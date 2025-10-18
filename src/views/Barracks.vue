<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue';
import axios from 'axios';
import { useWebSocket } from '../services/websocket';

const API_BASE = 'http://localhost:8000/api';

interface Troop {
  id: number;
  name: string;
  attack: number;
  defense: number;
  speed: number;
  carry_capacity: number;
  wood_cost: number;
  clay_cost: number;
  iron_cost: number;
  training_time: number;
}

interface QueueItem {
  id: number;
  village_id: number;
  troop_id: number;
  quantity: number;
  start_time: string | null;
  end_time: string;
  troop: Troop;
}

interface QueueItemWithProgress extends QueueItem {
  totalSeconds: number;
  remainingSeconds: number;
  progress: number;
}

interface VillageTroop {
  id: number;
  village_id: number;
  troop_id: number;
  quantity: number;
  troop: Troop;
}

interface ResourceBalances {
  wood: number;
  clay: number;
  iron: number;
  gold: number;
}

interface ResourceUpdatePayload {
  type: 'resources_updated';
  village_id: number;
  resources: ResourceBalances;
  capacities: ResourceBalances;
}

const RESOURCE_CAPACITY_BASE: ResourceBalances = { wood: 5000, clay: 5000, iron: 5000, gold: 50 };
const RESOURCE_CAPACITY_GROWTH = 1.3;
const GOLD_CAPACITY_GROWTH = 1.35;
const computeCapacity = (base: number, level: number, growth = RESOURCE_CAPACITY_GROWTH) =>
  base * Math.pow(growth, Math.max(level - 1, 0));

const parseServerDate = (value: string | null | undefined) => {
  if (!value) {
    return null;
  }
  const iso = value.endsWith('Z') ? value : `${value}Z`;
  const parsed = new Date(iso);
  return Number.isNaN(parsed.getTime()) ? null : parsed;
};

const troops = ref<Troop[]>([]);
const trainAmounts = ref<Record<number, number>>({});
const queue = ref<QueueItem[]>([]);
const trainedTroops = ref<VillageTroop[]>([]);
const resources = ref<ResourceBalances>({ wood: 0, clay: 0, iron: 0, gold: 0 });
const resourceCapacities = ref<ResourceBalances>({
  wood: RESOURCE_CAPACITY_BASE.wood,
  clay: RESOURCE_CAPACITY_BASE.clay,
  iron: RESOURCE_CAPACITY_BASE.iron,
  gold: RESOURCE_CAPACITY_BASE.gold,
});

const loadingTroops = ref(true);
const loadingQueue = ref(true);
const loadingTrained = ref(true);
const loadingResources = ref(true);

const villageId = ref<number | null>(null);
const isSubmitting = ref(false);
const trainError = ref<string | null>(null);
const trainErrorDetail = ref<Record<string, unknown> | null>(null);
const successMessage = ref<string | null>(null);

const now = ref(Date.now());
let ticker: number | null = null;
let poller: number | null = null;
let detachSocket: (() => void) | null = null;

const numberFormatter = new Intl.NumberFormat();

const totalSelected = computed(() =>
  Object.values(trainAmounts.value).reduce((sum, qty) => sum + (typeof qty === 'number' ? qty : 0), 0)
);

const trainedByTroopId = computed<Record<number, VillageTroop>>(() => {
  const lookup: Record<number, VillageTroop> = {};
  trainedTroops.value.forEach((item) => {
    lookup[item.troop_id] = item;
  });
  return lookup;
});

const queueWithProgress = computed<QueueItemWithProgress[]>(() =>
  queue.value.map((item) => {
    const endDate = parseServerDate(item.end_time);
    if (!endDate) {
      return {
        ...item,
        totalSeconds: 0,
        remainingSeconds: 0,
        progress: 100,
      };
    }
    const end = endDate.getTime();
    const fallbackDuration = item.troop.training_time * item.quantity * 1000;
    const startDate = item.start_time ? parseServerDate(item.start_time) : null;
    const start = startDate ? startDate.getTime() : end - fallbackDuration;
    const total = Math.max(end - start, 1000);
    const remaining = Math.max(end - now.value, 0);
    const progress = Math.min(100, ((total - remaining) / total) * 100);

    return {
      ...item,
      totalSeconds: Math.round(total / 1000),
      remainingSeconds: Math.ceil(remaining / 1000),
      progress,
    };
  })
);

const resourceCards = computed(() => [
  { key: 'wood', label: 'Wood', value: resources.value.wood, capacity: resourceCapacities.value.wood },
  { key: 'clay', label: 'Clay', value: resources.value.clay, capacity: resourceCapacities.value.clay },
  { key: 'iron', label: 'Iron', value: resources.value.iron, capacity: resourceCapacities.value.iron },
  { key: 'gold', label: 'Gold', value: resources.value.gold, capacity: resourceCapacities.value.gold },
]);

const formatNumber = (value: number) => numberFormatter.format(Math.max(0, Math.floor(value || 0)));

const formatDuration = (seconds: number) => {
  if (seconds <= 0 || Number.isNaN(seconds)) {
    return 'Done';
  }
  const mins = Math.floor(seconds / 60);
  const hrs = Math.floor(mins / 60);
  const remMins = mins % 60;
  const remSecs = seconds % 60;

  if (hrs > 0) {
    return `${hrs}h ${remMins}m`;
  }
  if (mins > 0) {
    return `${mins}m ${remSecs}s`;
  }
  return `${remSecs}s`;
};

const formatTimestamp = (value: string) => {
  const date = parseServerDate(value);
  if (!date) {
    return 'Unknown';
  }
  return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
};

const { connect, onMessage, offMessage } = useWebSocket();

const getVillageId = async () => {
  try {
    const response = await axios.get(`${API_BASE}/villages/?user_id=1`);
    if (Array.isArray(response.data) && response.data.length > 0) {
      villageId.value = response.data[0].id;
    }
  } catch (error) {
    console.error('Error fetching village id:', error);
  }
};

const fetchTroopDefinitions = async () => {
  loadingTroops.value = true;
  try {
    const response = await axios.get<Troop[]>(`${API_BASE}/troops/`);
    const sorted = [...response.data].sort((a, b) => a.id - b.id);
    troops.value = sorted;

    const nextAmounts: Record<number, number> = {};
    sorted.forEach((troop) => {
      const current = trainAmounts.value[troop.id] ?? 0;
      nextAmounts[troop.id] = current;
    });
    trainAmounts.value = nextAmounts;
  } catch (error) {
    console.error('Error fetching troops:', error);
  } finally {
    loadingTroops.value = false;
  }
};

const fetchQueue = async (showLoader = true) => {
  if (!villageId.value) return;
  if (showLoader) {
    loadingQueue.value = true;
  }
  try {
    const response = await axios.get<QueueItem[]>(`${API_BASE}/villages/${villageId.value}/training-queue`);
    queue.value = response.data ?? [];
  } catch (error) {
    console.error('Error fetching training queue:', error);
  } finally {
    if (showLoader) {
      loadingQueue.value = false;
    }
  }
};

const fetchTrainedTroops = async (showLoader = true) => {
  if (!villageId.value) return;
  if (showLoader) {
    loadingTrained.value = true;
  }
  try {
    const response = await axios.get<VillageTroop[]>(`${API_BASE}/villages/${villageId.value}/troops`);
    trainedTroops.value = response.data ?? [];
  } catch (error) {
    console.error('Error fetching trained troops:', error);
  } finally {
    if (showLoader) {
      loadingTrained.value = false;
    }
  }
};

const fetchResources = async (showLoader = true) => {
  if (!villageId.value) return;
  if (showLoader) {
    loadingResources.value = true;
  }
  try {
    const response = await axios.get(`${API_BASE}/villages/${villageId.value}`);
    const data = response.data ?? {};
    const capacities: ResourceBalances = {
      wood: computeCapacity(RESOURCE_CAPACITY_BASE.wood, data.wood_mill_level ?? 1),
      clay: computeCapacity(RESOURCE_CAPACITY_BASE.clay, data.clay_pit_level ?? 1),
      iron: computeCapacity(RESOURCE_CAPACITY_BASE.iron, data.iron_mine_level ?? 1),
      gold: computeCapacity(RESOURCE_CAPACITY_BASE.gold, data.town_hall_level ?? 1, GOLD_CAPACITY_GROWTH),
    };
    resources.value = {
      wood: data.wood ?? 0,
      clay: data.clay ?? 0,
      iron: data.iron ?? 0,
      gold: data.gold ?? 0,
    };
    resourceCapacities.value = capacities;
  } catch (error) {
    console.error('Error fetching village resources:', error);
  } finally {
    if (showLoader) {
      loadingResources.value = false;
    }
  }
};

const clearSelection = () => {
  const cleared: Record<number, number> = {};
  Object.keys(trainAmounts.value).forEach((key) => {
    const id = Number(key);
    cleared[id] = 0;
  });
  trainAmounts.value = cleared;
};

const applyResourceUpdate = (payload: ResourceUpdatePayload) => {
  resources.value = payload.resources;
  resourceCapacities.value = payload.capacities;
  loadingResources.value = false;
};

const refreshDynamicData = () => {
  fetchQueue(false);
  fetchTrainedTroops(false);
  fetchResources(false);
};

const handleSocketMessage = (event: MessageEvent) => {
  if (!villageId.value) return;
  if (event.data === `village:${villageId.value}:training_started`) {
    fetchQueue(false);
    fetchResources(false);
  } else if (event.data === `village:${villageId.value}:training_finished`) {
    refreshDynamicData();
  } else {
    try {
      const payload = JSON.parse(event.data) as ResourceUpdatePayload;
      if (payload.type === 'resources_updated' && payload.village_id === villageId.value) {
        applyResourceUpdate(payload);
      }
    } catch {
      // Ignore non-JSON payloads
    }
  }
};

const train = async () => {
  if (!villageId.value || isSubmitting.value) return;

  const orders = Object.entries(trainAmounts.value)
    .map(([troopId, quantity]) => ({ troop_id: Number(troopId), quantity: Number(quantity) || 0 }))
    .filter((order) => order.quantity > 0);

  if (orders.length === 0) {
    trainError.value = 'Select at least one unit to train.';
    trainErrorDetail.value = null;
    return;
  }

  isSubmitting.value = true;
  trainError.value = null;
  trainErrorDetail.value = null;
  successMessage.value = null;

  try {
    const response = await axios.post(`${API_BASE}/villages/${villageId.value}/train`, orders);
    queue.value = response.data?.queue ?? [];
    if (response.data?.resources) {
      resources.value = response.data.resources;
    }
    if (response.data?.capacities) {
      resourceCapacities.value = response.data.capacities;
    }
    successMessage.value = response.data?.message ?? 'Training queue updated.';
    window.setTimeout(() => {
      successMessage.value = null;
    }, 4000);
    clearSelection();
    fetchQueue(false);
    fetchResources(false);
  } catch (error: unknown) {
    successMessage.value = null;
    if (axios.isAxiosError(error)) {
      const detail = error.response?.data?.detail;
      if (typeof detail === 'string') {
        trainError.value = detail;
      } else if (detail && typeof detail === 'object') {
        trainError.value = (detail as Record<string, unknown>).message as string ?? 'Unable to train troops.';
        trainErrorDetail.value = detail as Record<string, unknown>;
      } else {
        trainError.value = 'Unable to train troops.';
      }
    } else {
      trainError.value = 'Unable to train troops.';
    }
  } finally {
    isSubmitting.value = false;
  }
};

onMounted(async () => {
  await getVillageId();
  if (!villageId.value) {
    return;
  }

  connect(villageId.value.toString());
  detachSocket = onMessage(handleSocketMessage);

  await Promise.all([
    fetchTroopDefinitions(),
    fetchQueue(),
    fetchTrainedTroops(),
    fetchResources(),
  ]);

  ticker = window.setInterval(() => {
    now.value = Date.now();
  }, 1000);

  poller = window.setInterval(() => {
    refreshDynamicData();
  }, 10000);
});

onUnmounted(() => {
  if (ticker !== null) {
    window.clearInterval(ticker);
    ticker = null;
  }
  if (poller !== null) {
    window.clearInterval(poller);
    poller = null;
  }
  if (detachSocket) {
    detachSocket();
    detachSocket = null;
  }
  if (typeof offMessage === 'function') {
    offMessage(handleSocketMessage);
  }
});
</script>

<template>
  <div class="space-y-8">
    <div>
      <h2 class="text-4xl font-bold mb-2">Barracks</h2>
      <p class="text-text-secondary">Manage your army production and keep track of every training queue.</p>
    </div>

    <section>
      <h3 class="text-2xl font-semibold mb-4">Resources</h3>
      <div class="grid gap-4 sm:grid-cols-3">
        <div
          v-for="card in resourceCards"
          :key="card.key"
          class="rounded-xl border border-secondary/40 bg-surface/70 p-4 backdrop-blur"
        >
          <p class="text-xs uppercase tracking-wide text-text-secondary">{{ card.label }}</p>
          <p class="mt-2 text-2xl font-semibold">
            <span v-if="loadingResources">...</span>
            <span v-else>
              {{ formatNumber(card.value) }} / {{ formatNumber(card.capacity) }}
            </span>
          </p>
        </div>
      </div>
    </section>

    <div class="grid gap-8 lg:grid-cols-3">
      <section class="lg:col-span-2 space-y-6">
        <div class="rounded-2xl border border-secondary/40 bg-surface/70 p-6 backdrop-blur">
          <header class="mb-4 flex items-center justify-between gap-2">
            <h3 class="text-2xl font-semibold">Train Troops</h3>
            <p class="text-sm text-text-secondary">Queue up new forces when you have the resources.</p>
          </header>

          <div v-if="loadingTroops" class="py-6 text-center text-text-secondary">
            Loading troops...
          </div>

          <div v-else class="space-y-5">
            <div class="space-y-4">
              <div
                v-for="troop in troops"
                :key="troop.id"
                class="rounded-xl border border-secondary/30 bg-background/60 p-4 shadow-sm"
              >
                <div class="flex flex-wrap items-center justify-between gap-4">
                  <div>
                    <p class="text-lg font-semibold">{{ troop.name }}</p>
                    <p class="text-xs text-text-secondary">
                      Cost: {{ troop.wood_cost }} wood · {{ troop.clay_cost }} clay · {{ troop.iron_cost }} iron
                    </p>
                    <p class="mt-1 text-xs text-text-secondary">
                      Training time per unit: {{ formatDuration(troop.training_time) }}
                    </p>
                    <p class="mt-1 text-xs text-text-secondary">
                      Ready units: {{ trainedByTroopId[troop.id]?.quantity ?? 0 }}
                    </p>
                  </div>
                  <div class="flex items-center gap-3">
                    <label class="text-sm text-text-secondary" :for="`train-${troop.id}`">Quantity</label>
                    <input
                      :id="`train-${troop.id}`"
                      v-model.number="trainAmounts[troop.id]"
                      type="number"
                      min="0"
                      class="w-24 rounded-lg border border-secondary/40 bg-surface/60 px-3 py-2 text-right"
                    />
                  </div>
                </div>
              </div>
            </div>

            <div class="flex flex-wrap items-center gap-3">
              <button
                class="rounded-lg bg-primary px-5 py-2 font-semibold text-white transition hover:bg-primary-600 disabled:cursor-not-allowed disabled:bg-secondary/40"
                @click="train"
                :disabled="isSubmitting || totalSelected === 0"
              >
                {{ isSubmitting ? 'Training...' : 'Train Selected' }}
              </button>
              <button
                class="rounded-lg border border-secondary/40 px-4 py-2 text-sm text-text-secondary hover:bg-secondary/20 disabled:cursor-not-allowed disabled:opacity-60"
                type="button"
                @click="clearSelection"
                :disabled="isSubmitting || totalSelected === 0"
              >
                Clear selection
              </button>
              <span class="text-sm text-text-secondary" v-if="totalSelected > 0">
                Total units queued: {{ totalSelected }}
              </span>
            </div>

            <div
              v-if="trainError"
              class="rounded-lg border border-red-500/40 bg-red-500/10 px-4 py-3 text-sm text-red-100"
            >
              <p class="font-semibold">{{ trainError }}</p>
              <ul v-if="trainErrorDetail?.shortage" class="mt-2 space-y-1">
                <li v-for="(value, resource) in trainErrorDetail.shortage as Record<string, number>" :key="resource">
                  <span class="capitalize">{{ resource }}</span> short by {{ formatNumber(value) }}
                </li>
              </ul>
            </div>
            <div
              v-else-if="successMessage"
              class="rounded-lg border border-primary/40 bg-primary/10 px-4 py-3 text-sm text-primary-100"
            >
              {{ successMessage }}
            </div>
          </div>
        </div>

        <div class="rounded-2xl border border-secondary/40 bg-surface/70 p-6 backdrop-blur">
          <h3 class="text-2xl font-semibold mb-4">Ready Troops</h3>
          <div v-if="loadingTrained" class="py-6 text-center text-text-secondary">
            Loading troop counts...
          </div>
          <div v-else-if="!trainedTroops.length" class="text-sm text-text-secondary">
            No trained troops are available yet.
          </div>
          <ul v-else class="space-y-3">
            <li
              v-for="troop in trainedTroops"
              :key="troop.id"
              class="flex items-center justify-between rounded-lg border border-secondary/30 bg-background/60 px-4 py-3"
            >
              <span class="font-medium">{{ troop.troop.name }}</span>
              <span class="text-lg font-semibold">{{ formatNumber(troop.quantity) }}</span>
            </li>
          </ul>
        </div>
      </section>

      <section class="rounded-2xl border border-secondary/40 bg-surface/70 p-6 backdrop-blur">
        <h3 class="text-2xl font-semibold mb-4">Training Queue</h3>
        <div v-if="loadingQueue" class="py-6 text-center text-text-secondary">
          Loading queue...
        </div>
        <div v-else-if="!queue.length" class="text-sm text-text-secondary">
          No units are currently in training.
        </div>
        <div v-else class="space-y-4">
          <div
            v-for="item in queueWithProgress"
            :key="item.id"
            class="rounded-xl border border-secondary/30 bg-background/60 p-4"
          >
            <div class="flex items-start justify-between gap-4">
              <div>
                <p class="font-semibold">{{ item.quantity }}x {{ item.troop.name }}</p>
                <p class="text-xs text-text-secondary">Finishes at {{ formatTimestamp(item.end_time) }}</p>
              </div>
              <div class="text-right">
                <p class="text-xs text-text-secondary">Remaining</p>
                <p class="text-base font-semibold">
                  {{ item.remainingSeconds <= 0 ? 'Completed' : formatDuration(item.remainingSeconds) }}
                </p>
              </div>
            </div>
            <div class="mt-3 h-2 w-full rounded-full bg-secondary/30">
              <div
                class="h-full rounded-full bg-primary transition-[width]"
                :style="{ width: `${item.progress}%` }"
              ></div>
            </div>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>
