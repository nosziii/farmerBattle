<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import type { LocationQueryRaw } from 'vue-router';
import axios from 'axios';

import { ensureAuthReady, useAuthState } from '../services/auth';
import { API_BASE, activeVillageId, ensureActiveVillageId } from '../services/villageState';
import { useWebSocket } from '../services/websocket';

import type { ExpeditionListResponse, ExpeditionSummary, ExpeditionCreateRequest } from '../types/expeditions';
import type { MapOverview, MapTile } from '../types/map';
import type { AvailableTroop } from '../types/troops';
import { decorateExpedition, formatDuration, type ExpeditionWithProgress } from '../utils/expeditions';

const route = useRoute();
const router = useRouter();
const { isAuthenticated } = useAuthState();
const villageId = activeVillageId;

const loading = ref(true);
const loadingPlannerData = ref(false);
const activeExpeditions = ref<ExpeditionSummary[]>([]);
const completedExpeditions = ref<ExpeditionSummary[]>([]);
const availableTroops = ref<AvailableTroop[]>([]);
const mapOverview = ref<MapOverview | null>(null);
const garrisonCounts = ref<Map<number, number>>(new Map());
const errorMessage = ref<string | null>(null);
const successMessage = ref<string | null>(null);

const now = ref(Date.now());
let ticker: number | null = null;

const isPlannerOpen = ref(false);
const plannerTargetId = ref<number | null>(null);
const plannerError = ref<string | null>(null);
const plannerSubmitting = ref(false);
const troopSelections = ref<Record<number, number>>({});

const selectedExpedition = ref<ExpeditionSummary | null>(null);

const { connect, onMessage, offMessage } = useWebSocket();
let detachSocket: (() => void) | null = null;

const TRAVEL_SECONDS_PER_TILE = 60;
const BASE_TRAVEL_SPEED = 12;

interface VillageTroopEntry {
  troop_id: number;
  quantity: number;
}

interface BarbarianTarget {
  id: number;
  name: string;
  level: number;
  warriors: number;
  x: number;
  y: number;
  distance: number;
}

const playerTile = computed<MapTile | null>(() => {
  if (!mapOverview.value || !villageId.value) return null;
  return (
    mapOverview.value.tiles.find(
      (tile) => tile.type === 'player' && tile.village && tile.village.id === villageId.value
    ) ?? null
  );
});

const barbarianTargets = computed<BarbarianTarget[]>(() => {
  if (!mapOverview.value || !playerTile.value) return [];
  return mapOverview.value.tiles
    .filter((tile) => tile.type === 'barbarian' && tile.barbarian)
    .map((tile) => ({
      id: tile.barbarian!.id,
      name: tile.barbarian!.name,
      level: tile.barbarian!.level,
      warriors: tile.barbarian!.warriors,
      x: tile.x,
      y: tile.y,
      distance: Math.abs(playerTile.value!.x - tile.x) + Math.abs(playerTile.value!.y - tile.y),
    }))
    .sort((a, b) => a.distance - b.distance);
});

const plannerTarget = computed<BarbarianTarget | null>(() => {
  if (!plannerTargetId.value) return null;
  return barbarianTargets.value.find((target) => target.id === plannerTargetId.value) ?? null;
});

const initialiseTroopSelections = () => {
  const next: Record<number, number> = {};
  availableTroops.value.forEach((troop) => {
    next[troop.id] = 0;
  });
  troopSelections.value = next;
};

watch(availableTroops, initialiseTroopSelections, { immediate: true });

const normaliseIsoTimestamp = (value: string) => {
  return /(Z|z|[+-]\d{2}:?\d{2})$/.test(value) ? value : `${value}Z`;
};

const parseDate = (value: string | null | undefined) => {
  if (!value) return null;
  const date = new Date(normaliseIsoTimestamp(value));
  return Number.isNaN(date.getTime()) ? null : date;
};

const calculateTravelSeconds = (distance: number, selectedTroopIds: number[]) => {
  if (distance <= 0) distance = 1;
  const speeds = selectedTroopIds.length
    ? selectedTroopIds
        .map((id) => availableTroops.value.find((troop) => troop.id === id)?.speed ?? BASE_TRAVEL_SPEED)
        .map((speed) => Math.max(1, speed))
    : [BASE_TRAVEL_SPEED];
  const slowest = Math.min(...speeds);
  const modifier = BASE_TRAVEL_SPEED / slowest;
  return Math.max(60, Math.ceil(distance * TRAVEL_SECONDS_PER_TILE * modifier));
};

type DecoratedExpedition = ExpeditionWithProgress & {
  phaseLabel: string;
  etaLabel: string;
};

const activeExpeditionsWithProgress = computed<DecoratedExpedition[]>(() => {
  const nowMs = now.value;
  return activeExpeditions.value.map((expedition) => {
    const decorated = decorateExpedition(expedition, nowMs);
    const phaseLabel =
      decorated.currentPhase === 'outbound'
        ? 'Outbound'
        : decorated.currentPhase === 'returning'
        ? 'Returning'
        : 'Completed';

    return {
      ...decorated,
      phaseLabel,
      etaLabel: decorated.currentPhase === 'completed' ? 'Arrived' : formatDuration(decorated.etaSeconds),
    };
  });
});

const totalSelectedTroops = computed(() =>
  Object.values(troopSelections.value).reduce((sum, qty) => sum + (Number.isFinite(qty) ? Number(qty) : 0), 0)
);

const plannerTravelSeconds = computed(() => {
  if (!plannerTarget.value) return 0;
  const selectedIds = Object.entries(troopSelections.value)
    .filter(([, qty]) => qty > 0)
    .map(([id]) => Number(id));
  return calculateTravelSeconds(plannerTarget.value.distance, selectedIds);
});

const plannerArrivalTime = computed(() => {
  if (!plannerTarget.value || plannerTravelSeconds.value <= 0) return null;
  return new Date(Date.now() + plannerTravelSeconds.value * 1000);
});

const plannerReturnTime = computed(() => {
  if (!plannerArrivalTime.value) return null;
  return new Date(plannerArrivalTime.value.getTime() + plannerTravelSeconds.value * 1000);
});

const formatTimestamp = (date: Date | null) => {
  if (!date) return '—';
  return date.toLocaleString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
};

const maxSendable = (troop: AvailableTroop) => {
  if (!troop.available) return 0;
  return garrisonCounts.value.get(troop.id) ?? 0;
};

const fetchExpeditions = async (showLoader = true) => {
  if (!villageId.value) return;
  if (showLoader) {
    loading.value = true;
  }
  try {
    const { data } = await axios.get<ExpeditionListResponse>(
      `${API_BASE}/villages/${villageId.value}/expeditions`
    );
    activeExpeditions.value = data.active;
    completedExpeditions.value = data.completed;
    errorMessage.value = null;
  } catch (error: any) {
    errorMessage.value = error?.response?.data?.detail ?? 'Unable to load expeditions right now.';
  } finally {
    if (showLoader) {
      loading.value = false;
    }
  }
};

const fetchAvailableTroops = async () => {
  if (!villageId.value) return;
  try {
    const { data } = await axios.get<AvailableTroop[]>(
      `${API_BASE}/villages/${villageId.value}/available-troops`
    );
    availableTroops.value = data;
  } catch (error) {
    console.error('Failed to fetch troop availability', error);
  }
};

const fetchGarrison = async () => {
  if (!villageId.value) return;
  try {
    const { data } = await axios.get<VillageTroopEntry[]>(`${API_BASE}/villages/${villageId.value}/troops`);
    const map = new Map<number, number>();
    data.forEach((entry) => {
      map.set(entry.troop_id, entry.quantity);
    });
    garrisonCounts.value = map;
  } catch (error) {
    console.error('Failed to fetch garrison troops', error);
  }
};

const fetchMapData = async () => {
  try {
    const { data } = await axios.get<MapOverview>(`${API_BASE}/map/`);
    mapOverview.value = data;
  } catch (error) {
    console.error('Failed to fetch map overview', error);
  }
};

const openPlanner = async (targetId?: number) => {
  if (!villageId.value) return;
  plannerError.value = null;
  plannerTargetId.value = targetId ?? plannerTargetId.value;
  if (!mapOverview.value || availableTroops.value.length === 0) {
    loadingPlannerData.value = true;
    await Promise.all([fetchMapData(), fetchAvailableTroops(), fetchGarrison()]);
    loadingPlannerData.value = false;
  }
  initialiseTroopSelections();
  if (targetId) {
    plannerTargetId.value = targetId;
  }
  isPlannerOpen.value = true;
};

const closePlanner = () => {
  isPlannerOpen.value = false;
  plannerTargetId.value = null;
  plannerError.value = null;
  plannerSubmitting.value = false;
  const newQuery: LocationQueryRaw = { ...route.query };
  delete newQuery.target;
  router.replace({ query: newQuery });
};

const sendExpedition = async () => {
  if (!villageId.value || !plannerTarget.value) {
    plannerError.value = 'Select a target barbarian village.';
    return;
  }
  const orders = Object.entries(troopSelections.value)
    .map(([troopId, quantity]) => ({ troop_id: Number(troopId), quantity: Number(quantity) || 0 }))
    .filter((order) => order.quantity > 0);

  if (!orders.length) {
    plannerError.value = 'Select at least one unit for this expedition.';
    return;
  }

  plannerSubmitting.value = true;
  plannerError.value = null;
  try {
    const payload: ExpeditionCreateRequest = {
      barbarian_village_id: plannerTarget.value.id,
      troops: orders,
    };
    await axios.post(`${API_BASE}/villages/${villageId.value}/expeditions`, payload);
    const successText = `Expedition to ${plannerTarget.value.name} launched!`;
    successMessage.value = successText;
    window.setTimeout(() => {
      if (successMessage.value === successText) {
        successMessage.value = null;
      }
    }, 4000);
    await Promise.all([fetchExpeditions(false), fetchGarrison(), fetchAvailableTroops()]);
    closePlanner();
  } catch (error: any) {
    const detail = error?.response?.data?.detail;
    if (typeof detail === 'string') {
      plannerError.value = detail;
    } else if (detail?.message) {
      plannerError.value = detail.message as string;
    } else {
      plannerError.value = 'Unable to launch expedition.';
    }
  } finally {
    plannerSubmitting.value = false;
  }
};

const formatResourceValue = (value: number | undefined) => {
  if (!value) return '0';
  return new Intl.NumberFormat().format(Math.floor(value));
};

const openReport = (expedition: ExpeditionSummary) => {
  selectedExpedition.value = expedition;
};

const closeReport = () => {
  selectedExpedition.value = null;
};

const handleSocketMessage = (event: MessageEvent) => {
  if (!villageId.value) return;
  const message = event.data;

  if (message === `village:${villageId.value}:expedition_updated`) {
    fetchExpeditions(false);
    fetchGarrison();
    fetchAvailableTroops();
    return;
  }

  try {
    const payload = JSON.parse(message) as {
      type?: string;
      village_id?: number;
      expedition?: ExpeditionSummary;
    };

    if (payload.type !== 'expedition_update' || payload.village_id !== villageId.value || !payload.expedition) {
      return;
    }

    const expedition = payload.expedition;

    // Update active expeditions
    activeExpeditions.value = activeExpeditions.value.filter((entry) => entry.id !== expedition.id);
    completedExpeditions.value = completedExpeditions.value.filter((entry) => entry.id !== expedition.id);

    if (expedition.status === 'completed') {
      completedExpeditions.value = [expedition, ...completedExpeditions.value];
    } else {
      activeExpeditions.value = [expedition, ...activeExpeditions.value];
    }

    // Refresh related state in the background
    fetchGarrison();
    fetchAvailableTroops();
  } catch {
    // Ignore non-JSON payloads
  }
};

watch(
  () => route.query.target,
  (value) => {
    if (value) {
      const targetId = Number(value);
      if (Number.isFinite(targetId)) {
        openPlanner(targetId);
      }
    }
  },
  { immediate: true }
);

watch(
  villageId,
  async (newId, oldId) => {
    if (newId && newId !== oldId) {
      await Promise.all([fetchExpeditions(), fetchAvailableTroops(), fetchGarrison(), fetchMapData()]);
      if (detachSocket) detachSocket();
      connect(newId.toString());
      detachSocket = onMessage(handleSocketMessage);
      const targetParam = route.query.target;
      if (targetParam && !isPlannerOpen.value) {
        const targetId = Number(targetParam);
        if (Number.isFinite(targetId)) {
          openPlanner(targetId);
        }
      }
    }
  }
);

onMounted(async () => {
  await ensureAuthReady();
  if (!isAuthenticated.value) {
    errorMessage.value = 'Sign in to manage expeditions.';
    return;
  }
  await ensureActiveVillageId();
  if (!villageId.value) {
    errorMessage.value = 'Create a village to launch expeditions.';
    return;
  }

  await Promise.all([fetchExpeditions(), fetchAvailableTroops(), fetchGarrison(), fetchMapData()]);

  connect(villageId.value.toString());
  detachSocket = onMessage(handleSocketMessage);

  ticker = window.setInterval(() => {
    now.value = Date.now();
  }, 1000);
});

onUnmounted(() => {
  if (ticker !== null) {
    window.clearInterval(ticker);
    ticker = null;
  }
  if (detachSocket) {
    detachSocket();
    detachSocket = null;
  }
  offMessage(handleSocketMessage);
});
</script>

<template>
  <main class="flex-1 overflow-y-auto p-8 space-y-8">
    <header class="flex flex-wrap items-center justify-between gap-4">
      <div>
        <h1 class="text-3xl font-semibold text-text-primary">Expeditions</h1>
        <p class="text-sm text-text-secondary">Send troops to raid nearby barbarian villages for resources.</p>
      </div>
      <div class="flex gap-2">
        <button
          v-if="barbarianTargets.length"
          type="button"
          class="rounded-lg border border-primary/40 bg-primary/70 px-4 py-2 text-sm font-semibold text-white hover:bg-primary"
          @click="openPlanner()"
        >
          Launch Expedition
        </button>
        <button
          type="button"
          class="rounded-lg border border-secondary-700/40 bg-secondary-800/60 px-4 py-2 text-sm text-text-secondary hover:bg-secondary-800"
          @click="fetchExpeditions()"
        >
          Refresh
        </button>
      </div>
    </header>

    <div v-if="errorMessage" class="rounded-lg border border-red-500/40 bg-red-500/10 px-4 py-3 text-sm text-red-200">
      {{ errorMessage }}
    </div>
    <div v-else-if="successMessage" class="rounded-lg border border-emerald-500/40 bg-emerald-500/10 px-4 py-3 text-sm text-emerald-200">
      {{ successMessage }}
    </div>

    <section class="space-y-4">
      <header class="flex items-center justify-between">
        <h2 class="text-xl font-semibold text-text-primary">Active expeditions</h2>
        <span class="text-xs uppercase tracking-wide text-text-secondary/70">
          {{ activeExpeditions.length }} active
        </span>
      </header>
      <div v-if="loading" class="py-8 text-center text-text-secondary">Loading expeditions...</div>
      <div v-else-if="!activeExpeditions.length" class="rounded-lg border border-secondary-700/40 bg-secondary-900/60 px-4 py-6 text-sm text-text-secondary">
        No troops are currently travelling. Launch a new expedition to start raiding barbarians.
      </div>
      <div v-else class="space-y-4">
        <article
          v-for="expedition in activeExpeditionsWithProgress"
          :key="expedition.id"
          class="rounded-2xl border border-secondary-700/40 bg-secondary-900/60 px-5 py-4 space-y-3"
        >
          <header class="flex flex-wrap items-center justify-between gap-2">
            <div>
              <h3 class="text-lg font-semibold text-text-primary">
                {{ expedition.barbarian_name }}
              </h3>
              <p class="text-xs text-text-secondary/70">
                Level {{ expedition.barbarian_level }} • Distance {{ expedition.distance }} tiles • Phase: {{ expedition.phaseLabel }}
              </p>
            </div>
            <div class="text-right text-sm text-text-secondary">
              <p>ETA: <span class="font-semibold text-text-primary">{{ expedition.etaLabel }}</span></p>
            </div>
          </header>
          <div class="space-y-2 w-full">
            <div>
              <div class="mb-1 flex items-center justify-between text-[11px] uppercase tracking-wide text-text-secondary/70">
                <span>Outbound</span>
                <span>{{ Math.round(expedition.outboundProgress * 100) }}%</span>
              </div>
              <div class="h-2 w-full rounded-full bg-secondary/30">
                <div
                  class="h-full rounded-full bg-primary transition-[width]"
                  :style="{ width: `${Math.round(expedition.outboundProgress * 100)}%` }"
                ></div>
              </div>
            </div>
            <div v-if="expedition.currentPhase !== 'outbound' || expedition.returnProgress > 0">
              <div class="mb-1 flex items-center justify-between text-[11px] uppercase tracking-wide text-text-secondary/70">
                <span>Return</span>
                <span>{{ Math.round(expedition.returnProgress * 100) }}%</span>
              </div>
              <div class="h-2 w-full rounded-full bg-secondary/30">
                <div
                  class="h-full rounded-full bg-emerald-400/80 transition-[width]"
                  :style="{ width: `${Math.round(expedition.returnProgress * 100)}%` }"
                ></div>
              </div>
            </div>
          </div>
          <div class="grid gap-2 text-xs text-text-secondary md:grid-cols-3">
            <div>
              <span class="uppercase tracking-wide text-text-secondary/70">Departed</span>
              <p class="text-text-primary">{{ formatTimestamp(parseDate(expedition.departed_at)) }}</p>
            </div>
            <div>
              <span class="uppercase tracking-wide text-text-secondary/70">Arrival</span>
              <p class="text-text-primary">{{ formatTimestamp(parseDate(expedition.arrive_at)) }}</p>
            </div>
            <div>
              <span class="uppercase tracking-wide text-text-secondary/70">Return</span>
              <p class="text-text-primary">{{ formatTimestamp(parseDate(expedition.return_at)) }}</p>
            </div>
          </div>
          <div class="text-xs text-text-secondary">
            <span class="uppercase tracking-wide text-text-secondary/70">Units</span>
            <ul class="mt-1 flex flex-wrap gap-3">
              <li v-for="troop in expedition.troops" :key="troop.troop_id" class="rounded border border-secondary-600/40 bg-secondary-800/60 px-2 py-1">
                <span class="text-text-primary font-semibold">{{ troop.name }}</span>
                <span class="ml-1 text-text-secondary/80">{{ troop.sent }} sent • {{ troop.returning }} returning</span>
              </li>
            </ul>
          </div>
        </article>
      </div>
    </section>

    <section class="space-y-4">
      <header class="flex items-center justify-between">
        <h2 class="text-xl font-semibold text-text-primary">Completed expeditions</h2>
        <span class="text-xs uppercase tracking-wide text-text-secondary/70">
          {{ completedExpeditions.length }} total
        </span>
      </header>
      <div v-if="!completedExpeditions.length" class="rounded-lg border border-secondary-700/40 bg-secondary-900/60 px-4 py-6 text-sm text-text-secondary">
        Completed expeditions will appear here with their loot and battle reports.
      </div>
      <div v-else class="grid gap-4 md:grid-cols-2">
        <article
          v-for="expedition in completedExpeditions"
          :key="expedition.id"
          class="rounded-2xl border border-secondary-700/40 bg-secondary-900/60 px-5 py-4 space-y-2"
        >
          <header class="flex items-center justify-between">
            <div>
              <h3 class="text-lg font-semibold text-text-primary">{{ expedition.barbarian_name }}</h3>
              <p class="text-xs text-text-secondary/70">Completed {{ formatTimestamp(parseDate(expedition.completed_at)) }}</p>
            </div>
            <span
              class="rounded-full border px-2 py-1 text-[11px] uppercase tracking-wide"
              :class="expedition.success
                ? 'border-emerald-500/40 bg-emerald-500/10 text-emerald-200'
                : 'border-red-500/40 bg-red-500/10 text-red-200'"
            >
              {{ expedition.success ? 'Success' : 'Failed' }}
            </span>
          </header>
          <div class="text-xs text-text-secondary">
            <span class="uppercase tracking-wide text-text-secondary/70">Loot</span>
            <p class="text-text-primary">
              Wood {{ formatResourceValue(expedition.loot.wood) }} • Clay {{ formatResourceValue(expedition.loot.clay) }} • Iron {{ formatResourceValue(expedition.loot.iron) }}
            </p>
          </div>
          <div class="text-xs text-text-secondary">
            <span class="uppercase tracking-wide text-text-secondary/70">Report</span>
            <p class="line-clamp-2 text-text-primary/80">{{ expedition.battle_report ?? 'No report available.' }}</p>
          </div>
          <button
            type="button"
            class="rounded-lg border border-primary/40 bg-primary/20 px-3 py-1.5 text-xs text-primary-100 hover:bg-primary/30"
            @click="openReport(expedition)"
          >
            View details
          </button>
        </article>
      </div>
    </section>

    <section class="space-y-4">
      <header class="flex items-center justify-between">
        <h2 class="text-xl font-semibold text-text-primary">Nearby barbarian villages</h2>
        <span class="text-xs uppercase tracking-wide text-text-secondary/70">{{ barbarianTargets.length }} found</span>
      </header>
      <div v-if="!barbarianTargets.length" class="rounded-lg border border-secondary-700/40 bg-secondary-900/60 px-4 py-6 text-sm text-text-secondary">
        No barbarian villages were discovered on the map yet.
      </div>
      <div v-else class="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
        <article
          v-for="target in barbarianTargets"
          :key="target.id"
          class="rounded-xl border border-secondary-700/40 bg-secondary-900/60 px-4 py-3 space-y-1"
        >
          <header class="flex items-center justify-between">
            <h3 class="text-base font-semibold text-text-primary">{{ target.name }}</h3>
            <span class="text-xs text-text-secondary/70">Lv. {{ target.level }}</span>
          </header>
          <p class="text-xs text-text-secondary">Warriors: {{ target.warriors }}</p>
          <p class="text-xs text-text-secondary">Distance: {{ target.distance }} tiles</p>
          <button
            type="button"
            class="mt-2 w-full rounded-lg border border-primary/40 bg-primary/20 px-3 py-2 text-xs font-semibold text-primary-100 hover:bg-primary/30"
            @click="openPlanner(target.id)"
          >
            Plan expedition
          </button>
        </article>
      </div>
    </section>

    <transition name="fade">
      <div
        v-if="isPlannerOpen"
        class="fixed inset-0 z-50 flex items-center justify-center bg-black/70 px-4"
      >
        <div class="w-full max-w-3xl rounded-3xl border border-secondary-700/40 bg-secondary-900/90 px-6 py-6 shadow-2xl shadow-black/60 backdrop-blur-lg">
          <header class="mb-4 flex items-start justify-between gap-4">
            <div>
              <h3 class="text-2xl font-semibold text-text-primary">Prepare expedition</h3>
              <p class="text-sm text-text-secondary">
                Choose a barbarian target and allocate troops. Travel time depends on the distance and your slowest unit.
              </p>
            </div>
            <button
              type="button"
              class="rounded-lg border border-secondary-700/50 bg-secondary-800/60 px-3 py-1 text-sm text-text-secondary hover:bg-secondary-800"
              @click="closePlanner"
            >
              Close
            </button>
          </header>

          <div v-if="loadingPlannerData" class="py-10 text-center text-text-secondary">
            Loading planner data...
          </div>
          <div v-else class="space-y-5">
            <div class="grid gap-4 md:grid-cols-2">
              <label class="text-sm text-text-secondary">
                <span class="text-xs uppercase tracking-wide text-text-secondary/70">Target village</span>
                <select
                  v-model.number="plannerTargetId"
                  class="mt-1 w-full rounded-lg border border-secondary-700/40 bg-secondary-800/60 px-3 py-2 text-sm text-text-primary focus:border-primary focus:outline-none"
                >
                  <option v-if="!plannerTargetId" value="" disabled>Select a target</option>
                  <option v-for="target in barbarianTargets" :key="target.id" :value="target.id">
                    {{ target.name }} — Lv. {{ target.level }} ({{ target.distance }} tiles)
                  </option>
                </select>
              </label>
              <div class="rounded-lg border border-secondary-700/40 bg-secondary-900/60 px-3 py-2 text-xs text-text-secondary">
                <p class="uppercase tracking-wide text-text-secondary/70">Estimated travel</p>
                <p class="text-text-primary">{{ formatDuration(plannerTravelSeconds) }} each way</p>
                <p class="uppercase tracking-wide text-text-secondary/70 mt-2">Estimated arrival</p>
                <p class="text-text-primary">{{ formatTimestamp(plannerArrivalTime) }}</p>
                <p class="uppercase tracking-wide text-text-secondary/70 mt-2">Estimated return</p>
                <p class="text-text-primary">{{ formatTimestamp(plannerReturnTime) }}</p>
              </div>
            </div>

            <div class="space-y-3">
              <h4 class="text-sm font-semibold uppercase tracking-wide text-text-primary">Troop allocation</h4>
              <div v-if="!availableTroops.length" class="rounded-lg border border-secondary-700/40 bg-secondary-900/60 px-4 py-3 text-xs text-text-secondary">
                No troops available. Train units in the barracks first.
              </div>
              <div v-else class="space-y-3 max-h-60 overflow-y-auto pr-2">
                <div
                  v-for="troop in availableTroops"
                  :key="troop.id"
                  :class="[
                    'rounded-lg border px-3 py-3 text-sm transition',
                    troop.available ? 'border-secondary-700/40 bg-secondary-800/60' : 'border-secondary-700/20 bg-secondary-900/60 opacity-60'
                  ]"
                >
                  <div class="flex flex-wrap items-center justify-between gap-3">
                    <div>
                      <p class="text-text-primary font-semibold">{{ troop.name }}</p>
                      <p class="text-xs text-text-secondary/70">
                        Cost {{ troop.wood_cost }}/{{ troop.clay_cost }}/{{ troop.iron_cost }} • Speed {{ troop.speed }} • Carry {{ troop.carry_capacity }} • Available {{ maxSendable(troop) }}
                      </p>
                      <p v-if="troop.missing_requirements.length" class="text-[11px] text-amber-300">
                        Requires
                        <span
                          v-for="req in troop.missing_requirements"
                          :key="req.building"
                          class="mr-2"
                        >
                          {{ req.display_name }} Lv. {{ req.required_level }} ({{ req.current_level }})
                        </span>
                      </p>
                    </div>
                    <div class="flex items-center gap-2">
                      <input
                        v-model.number="troopSelections[troop.id]"
                        type="number"
                        min="0"
                        :max="maxSendable(troop)"
                        :disabled="!troop.available"
                        class="w-24 rounded-lg border border-secondary-700/40 bg-secondary-900/60 px-2 py-1 text-right text-sm text-text-primary focus:border-primary focus:outline-none"
                      />
                      <button
                        type="button"
                        class="rounded border border-primary/40 bg-primary/20 px-2 py-1 text-xs text-primary-100 hover:bg-primary/30 disabled:opacity-50"
                        @click="troopSelections[troop.id] = maxSendable(troop)"
                        :disabled="!troop.available || maxSendable(troop) === 0"
                      >
                        Max
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div v-if="plannerError" class="rounded-lg border border-red-500/40 bg-red-500/10 px-4 py-2 text-sm text-red-200">
              {{ plannerError }}
            </div>

            <div class="flex flex-wrap items-center justify-between gap-3">
              <span class="text-sm text-text-secondary">Total units selected: <span class="font-semibold text-text-primary">{{ totalSelectedTroops }}</span></span>
              <div class="flex gap-2">
                <button
                  type="button"
                  class="rounded-lg border border-secondary-700/40 bg-secondary-800/60 px-3 py-2 text-sm text-text-secondary hover:bg-secondary-700"
                  @click="initialiseTroopSelections"
                  :disabled="plannerSubmitting"
                >
                  Reset
                </button>
                <button
                  type="button"
                  class="rounded-lg border border-primary/40 bg-primary/70 px-4 py-2 text-sm font-semibold text-white hover:bg-primary disabled:opacity-60"
                  @click="sendExpedition"
                  :disabled="plannerSubmitting"
                >
                  {{ plannerSubmitting ? 'Launching...' : 'Launch expedition' }}
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </transition>

    <transition name="fade">
      <div
        v-if="selectedExpedition"
        class="fixed inset-0 z-50 flex items-center justify-center bg-black/70 px-4"
      >
        <div class="w-full max-w-2xl rounded-3xl border border-secondary-700/40 bg-secondary-900/95 px-6 py-6 shadow-2xl shadow-black/60 backdrop-blur">
          <header class="mb-4 flex items-start justify-between gap-4">
            <div>
              <h3 class="text-2xl font-semibold text-text-primary">{{ selectedExpedition.barbarian_name }}</h3>
              <p class="text-xs text-text-secondary/70">
                Completed {{ formatTimestamp(parseDate(selectedExpedition.completed_at)) }} • Distance {{ selectedExpedition.distance }} tiles
              </p>
            </div>
            <button
              type="button"
              class="rounded-lg border border-secondary-700/50 bg-secondary-800/60 px-3 py-1 text-sm text-text-secondary hover:bg-secondary-800"
              @click="closeReport"
            >
              Close
            </button>
          </header>
          <div class="space-y-4 text-sm text-text-secondary">
            <div class="rounded-lg border border-secondary-700/40 bg-secondary-900/60 px-4 py-3">
              <span class="uppercase tracking-wide text-text-secondary/70">Outcome</span>
              <p class="text-text-primary">{{ selectedExpedition.success ? 'Success' : 'Failed' }}</p>
            </div>
            <div class="rounded-lg border border-secondary-700/40 bg-secondary-900/60 px-4 py-3">
              <span class="uppercase tracking-wide text-text-secondary/70">Loot</span>
              <p class="text-text-primary">
                Wood {{ formatResourceValue(selectedExpedition.loot.wood) }} • Clay {{ formatResourceValue(selectedExpedition.loot.clay) }} • Iron {{ formatResourceValue(selectedExpedition.loot.iron) }}
              </p>
            </div>
            <div class="rounded-lg border border-secondary-700/40 bg-secondary-900/60 px-4 py-3 space-y-2">
              <span class="uppercase tracking-wide text-text-secondary/70">Troops</span>
              <ul class="space-y-1">
                <li v-for="troop in selectedExpedition.troops" :key="troop.troop_id" class="flex items-center justify-between">
                  <span class="text-text-primary font-semibold">{{ troop.name }}</span>
                  <span class="text-text-secondary">
                    Sent {{ troop.sent }} • Returned {{ troop.returning }} • Lost {{ troop.casualties }}
                  </span>
                </li>
              </ul>
            </div>
            <div class="rounded-lg border border-secondary-700/40 bg-secondary-900/60 px-4 py-3">
              <span class="uppercase tracking-wide text-text-secondary/70">Battle report</span>
              <p class="text-text-primary/80">{{ selectedExpedition.battle_report ?? 'No report available.' }}</p>
            </div>
          </div>
        </div>
      </div>
    </transition>
  </main>
</template>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
