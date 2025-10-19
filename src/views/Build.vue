<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue';
import axios from 'axios';

import ResourceCard from '../components/ResourceCard.vue';
import BuildingDetailCard from '../components/buildings/BuildingDetailCard.vue';

import type { BuildingStatus, BuildingQueueItem } from '../types/buildings';
import { ensureAuthReady } from '../services/auth';
import {
  API_BASE,
  activeVillageId,
  ensureActiveVillageId,
} from '../services/villageState';

interface ResourceBalances {
  wood: number;
  clay: number;
  iron: number;
  gold: number;
}

interface BuildingUpgradeResponse {
  message: string;
  resources: ResourceBalances;
  queue: BuildingQueueItem[];
}

const villageId = activeVillageId;

const buildingStatuses = ref<BuildingStatus[]>([]);
const buildingQueue = ref<BuildingQueueItem[]>([]);
const resourceBalances = ref<ResourceBalances>({ wood: 0, clay: 0, iron: 0, gold: 0 });
const resourceCapacities = ref<ResourceBalances>({ wood: 0, clay: 0, iron: 0, gold: 0 });
const productionRates = ref<ResourceBalances>({ wood: 0, clay: 0, iron: 0, gold: 0 });

const loading = ref(true);
const error = ref<string | null>(null);
const notifications = ref<{ id: number; message: string; type: 'success' | 'error' | 'info' }[]>([]);

const now = ref(Date.now());
let ticker: number | null = null;
let refreshHandle: number | null = null;
const REFRESH_INTERVAL_MS = 5000;

const parseServerDate = (value: string | null | undefined) => {
  if (!value) {
    return null;
  }
  const iso = value.endsWith('Z') ? value : `${value}Z`;
  const parsed = new Date(iso);
  return Number.isNaN(parsed.getTime()) ? null : parsed;
};

const formatDuration = (seconds: number) => {
  if (seconds <= 0 || Number.isNaN(seconds)) {
    return 'Soon';
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

const addNotification = (message: string, type: 'success' | 'error' | 'info' = 'info') => {
  const id = Date.now();
  notifications.value.push({ id, message, type });
  setTimeout(() => {
    notifications.value = notifications.value.filter((notification) => notification.id !== id);
  }, 5000);
};

const sortedBuildings = computed(() =>
  [...buildingStatuses.value].sort((a, b) => a.order - b.order)
);

const groupedBuildings = computed(() => {
  const groups = new Map<string, BuildingStatus[]>();
  for (const status of sortedBuildings.value) {
    const current = groups.get(status.category) ?? [];
    current.push(status);
    groups.set(status.category, current);
  }
  return Array.from(groups.entries()).map(([category, items]) => ({ category, items }));
});

const buildingLookup = computed(() => {
  const map = new Map<string, BuildingStatus>();
  for (const status of buildingStatuses.value) {
    map.set(status.internal_name, status);
  }
  return map;
});

const queueEntries = computed(() =>
  buildingQueue.value
    .slice()
    .sort((a, b) => new Date(a.end_time).getTime() - new Date(b.end_time).getTime())
    .map((entry) => {
      const status = buildingLookup.value.get(entry.building);
      const start = parseServerDate(entry.start_time)?.getTime() ?? 0;
      const end = parseServerDate(entry.end_time)?.getTime() ?? 0;
      const totalSeconds = start > 0 && end > start
        ? Math.max(1, Math.floor((end - start) / 1000))
        : Math.max(1, Math.floor(Math.max(end - now.value, 0) / 1000));
      const remainingSeconds = Math.max(0, Math.ceil((end - now.value) / 1000));
      const progress = Math.min(
        100,
        Math.max(0, ((totalSeconds - remainingSeconds) / totalSeconds) * 100)
      );
      return {
        id: entry.id,
        building: entry.building,
        displayName: status?.name ?? entry.building,
        targetLevel: entry.target_level,
        remainingSeconds,
        remainingLabel: formatDuration(remainingSeconds),
        progress,
      };
    })
);

const resourceCards = computed(() => [
  {
    title: 'Gold',
    subtitle: 'Treasury',
    icon: '🪙',
    amount: resourceBalances.value.gold,
    capacity: resourceCapacities.value.gold || 1,
    production: productionRates.value.gold,
  },
  {
    title: 'Wood',
    subtitle: 'Timber reserves',
    icon: '🪵',
    amount: resourceBalances.value.wood,
    capacity: resourceCapacities.value.wood || 1,
    production: productionRates.value.wood,
  },
  {
    title: 'Clay',
    subtitle: 'Quarry output',
    icon: '🧱',
    amount: resourceBalances.value.clay,
    capacity: resourceCapacities.value.clay || 1,
    production: productionRates.value.clay,
  },
  {
    title: 'Iron',
    subtitle: 'Mine stockpile',
    icon: '⛏️',
    amount: resourceBalances.value.iron,
    capacity: resourceCapacities.value.iron || 1,
    production: productionRates.value.iron,
  },
]);

const canAfford = (status: BuildingStatus) => {
  if (!status.next_cost) {
    return false;
  }
  const { wood, clay, iron } = status.next_cost;
  return (
    resourceBalances.value.wood >= wood &&
    resourceBalances.value.clay >= clay &&
    resourceBalances.value.iron >= iron
  );
};

const fetchVillageResources = async () => {
  if (!villageId.value) {
    return;
  }
  const response = await axios.get(`${API_BASE}/villages/${villageId.value}`);
  const village = response.data;
  resourceBalances.value = {
    wood: village.wood ?? 0,
    clay: village.clay ?? 0,
    iron: village.iron ?? 0,
    gold: village.gold ?? 0,
  };
  productionRates.value = {
    wood: village.wood_production ?? 0,
    clay: village.clay_production ?? 0,
    iron: village.iron_production ?? 0,
    gold: village.gold_production ?? 0,
  };
};

const updateResourceCapacitiesFromStatuses = () => {
  const wood = buildingStatuses.value.find((status) => status.internal_name === 'wood_mill');
  const clay = buildingStatuses.value.find((status) => status.internal_name === 'clay_pit');
  const iron = buildingStatuses.value.find((status) => status.internal_name === 'iron_mine');
  const townHall = buildingStatuses.value.find((status) => status.internal_name === 'town_hall');
  const warehouse = buildingStatuses.value.find((status) => status.internal_name === 'warehouse');

  const warehouseBonus = warehouse?.storage ?? 0;

  if (wood?.storage != null) {
    resourceCapacities.value.wood = wood.storage + warehouseBonus;
  }
  if (clay?.storage != null) {
    resourceCapacities.value.clay = clay.storage + warehouseBonus;
  }
  if (iron?.storage != null) {
    resourceCapacities.value.iron = iron.storage + warehouseBonus;
  }
  if (townHall?.storage != null) {
    resourceCapacities.value.gold = townHall.storage;
  }
};

const fetchBuildingStatuses = async () => {
  if (!villageId.value) {
    return;
  }
  const response = await axios.get<BuildingStatus[]>(
    `${API_BASE}/villages/${villageId.value}/buildings`
  );
  buildingStatuses.value = response.data ?? [];
  updateResourceCapacitiesFromStatuses();
};

const fetchBuildingQueue = async () => {
  if (!villageId.value) {
    return;
  }
  const response = await axios.get<BuildingQueueItem[]>(
    `${API_BASE}/villages/${villageId.value}/building-queue`
  );
  buildingQueue.value = response.data ?? [];
};

const fetchAll = async () => {
  loading.value = true;
  error.value = null;
  try {
    await ensureActiveVillageId();
    if (!villageId.value) {
      throw new Error('No active village available.');
    }
    await Promise.all([
      fetchVillageResources(),
      fetchBuildingStatuses(),
      fetchBuildingQueue(),
    ]);
  } catch (err: any) {
    console.error('Error loading building data:', err);
    error.value = err.response?.data?.detail ?? 'Failed to load building overview.';
  } finally {
    loading.value = false;
  }
};

const handleUpgrade = async (buildingKey: string) => {
  if (!villageId.value) {
    addNotification('No active village selected.', 'error');
    return;
  }
  try {
    const response = await axios.post<BuildingUpgradeResponse>(
      `${API_BASE}/villages/${villageId.value}/upgrade/${buildingKey}`
    );
    const data = response.data;
    resourceBalances.value = data.resources;
    buildingQueue.value = data.queue ?? [];
    await fetchBuildingStatuses();
    addNotification(data.message ?? 'Upgrade started!', 'success');
    startAutoRefresh();
  } catch (err: any) {
    console.error(`Error upgrading ${buildingKey}:`, err);
    const detail = err.response?.data?.detail;
    if (typeof detail === 'string') {
      addNotification(detail, 'error');
    } else {
      addNotification('Unable to start this upgrade.', 'error');
    }
  }
};

onMounted(async () => {
  await ensureAuthReady();
  await fetchAll();
  ticker = window.setInterval(() => {
    now.value = Date.now();
  }, 1000);
});

onUnmounted(() => {
  if (ticker) {
    clearInterval(ticker);
    ticker = null;
  }
  if (refreshHandle) {
    clearInterval(refreshHandle);
    refreshHandle = null;
  }
});

const hasActiveUpgrade = computed(
  () =>
    buildingStatuses.value.some((status) => status.is_upgrading) ||
    buildingQueue.value.length > 0
);

const startAutoRefresh = () => {
  if (refreshHandle !== null) {
    return;
  }
  refreshHandle = window.setInterval(async () => {
    await Promise.all([fetchBuildingStatuses(), fetchBuildingQueue()]);
  }, REFRESH_INTERVAL_MS);
};

const stopAutoRefresh = () => {
  if (refreshHandle !== null) {
    clearInterval(refreshHandle);
    refreshHandle = null;
  }
};

watch(
  activeVillageId,
  async (newId, oldId) => {
    if (!newId || newId === oldId) {
      return;
    }
    await fetchAll();
  }
);

watch(
  hasActiveUpgrade,
  (active) => {
    if (active) {
      startAutoRefresh();
    } else {
      stopAutoRefresh();
    }
  },
  { immediate: true }
);
</script>

<template>
  <main class="flex-1 overflow-y-auto p-8 space-y-8">
    <section class="grid gap-4 md:grid-cols-3" v-if="!loading">
      <ResourceCard
        v-for="card in resourceCards"
        :key="card.title"
        :title="card.title"
        :subtitle="card.subtitle"
        :icon="card.icon"
        :amount="card.amount"
        :capacity="card.capacity"
        :production="card.production"
      />
    </section>

    <div v-if="loading" class="py-16 text-center text-text-secondary">
      <p>Gathering blueprints...</p>
    </div>

    <div v-else-if="error" class="rounded-xl border border-red-500/40 bg-red-500/10 px-6 py-4 text-red-200">
      {{ error }}
    </div>

    <div v-else class="flex flex-col gap-6 lg:flex-row">
      <section class="flex-1 space-y-6">
        <div
          v-for="group in groupedBuildings"
          :key="group.category"
          class="space-y-4"
        >
          <div class="flex items-center justify-between">
            <h2 class="text-xl font-semibold text-text-primary">
              {{ group.category }}
            </h2>
            <span class="text-xs uppercase tracking-wide text-text-secondary/70">
              {{ group.items.length }} building{{ group.items.length === 1 ? '' : 's' }}
            </span>
          </div>
          <div class="grid gap-5 md:grid-cols-2">
            <BuildingDetailCard
              v-for="status in group.items"
              :key="status.internal_name"
              :status="status"
              :now="now"
              :can-afford="canAfford(status)"
              @upgrade="handleUpgrade"
            />
          </div>
        </div>
      </section>

      <aside class="w-full lg:w-80 space-y-6">
        <div class="rounded-2xl border border-secondary-700/40 bg-secondary-900/60 p-5">
          <h3 class="text-lg font-semibold text-text-primary mb-3">Queue</h3>
          <p v-if="!queueEntries.length" class="text-sm text-text-secondary">
            No ongoing upgrades. Your builders await orders.
          </p>
          <ul v-else class="space-y-3">
            <li
              v-for="entry in queueEntries"
              :key="entry.id"
              class="rounded-lg border border-secondary-700/40 bg-secondary-800/60 px-3 py-3 text-sm"
            >
              <div class="flex items-start justify-between gap-3">
                <div>
                  <p class="text-text-primary font-semibold">
                    {{ entry.displayName }} → Lv. {{ entry.targetLevel }}
                  </p>
                  <p class="text-xs text-text-secondary">
                    Ready {{ entry.remainingSeconds <= 0 ? 'any moment' : `in ${entry.remainingLabel}` }}
                  </p>
                </div>
                <p class="text-xs text-text-secondary">
                  {{ Math.round(entry.progress) }}%
                </p>
              </div>
              <div class="mt-2 h-1.5 rounded-full bg-secondary-700/50 overflow-hidden">
                <div
                  class="h-full rounded-full bg-emerald-400 transition-[width] duration-300"
                  :style="{ width: `${entry.progress}%` }"
                ></div>
              </div>
            </li>
          </ul>
        </div>

        <div
          v-if="notifications.length"
          class="space-y-3"
        >
          <div
            v-for="note in notifications"
            :key="note.id"
            :class="[
              'rounded-xl px-4 py-3 text-sm border',
              note.type === 'success'
                ? 'border-emerald-500/40 bg-emerald-500/10 text-emerald-200'
                : note.type === 'error'
                ? 'border-red-500/40 bg-red-500/10 text-red-200'
                : 'border-secondary-700/40 bg-secondary-800/60 text-text-secondary'
            ]"
          >
            {{ note.message }}
          </div>
        </div>
      </aside>
    </div>
  </main>
</template>
