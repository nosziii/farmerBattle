<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from "vue";

import ResourceCard from "../components/ResourceCard.vue";
import BuildingCard from "../components/BuildingCard.vue";
import axios from "axios";
import { useWebSocket } from "../services/websocket";
import type {
  BuildingStatus,
  BuildingCost,
  BuildingQueueItem,
} from "../types/buildings";

const API_BASE = "http://localhost:8000/api";

interface ResourceBalances {
  wood: number;
  clay: number;
  iron: number;
  gold: number;
}

interface ResourceUpdatePayload {
  type: "resources_updated";
  village_id: number;
  resources: ResourceBalances;
  capacities: ResourceBalances;
}

interface BuildingUpgradeFinishedPayload {
  type: "building_upgrade_finished";
  village_id: number;
  building: string;
  level: number;
}

interface TrainingQueueItem {
  id: number;
  village_id: number;
  troop_id: number;
  quantity: number;
  start_time: string | null;
  end_time: string;
  troop: {
    id: number;
    name: string;
    training_time: number;
  };
}

interface TrainingQueueItemWithProgress extends TrainingQueueItem {
  remainingSeconds: number;
  progress: number;
}

interface VillageTroopEntry {
  id: number;
  village_id: number;
  troop_id: number;
  quantity: number;
  troop: {
    id: number;
    name: string;
  };
}

interface BuildingUpgradeResponse {
  message: string;
  resources: ResourceBalances;
  queue: BuildingQueueItem[];
}

interface BuildingCardView {
  name: string;
  internalName: string;
  description: string;
  icon: string;
  level: number;
  maxLevel: number;
  production: number;
  storage: number | null;
  resourceField: string | null;
  isUpgrading: boolean;
  progress: number;
  remainingSeconds: number | null;
  canUpgrade: boolean;
  canAfford: boolean;
  nextCost: BuildingCost | null;
  durationSeconds: number | null;
  upgradeEndTime: string | null;
}

const parseServerDate = (value: string | null | undefined) => {
  if (!value) {
    return null;
  }
  const iso = value.endsWith("Z") ? value : `${value}Z`;
  const parsed = new Date(iso);
  return Number.isNaN(parsed.getTime()) ? null : parsed;
};

const resources = ref<any[]>([]);
const villageId = ref(1); // Assuming a fixed village for now
const notifications = ref<any[]>([]);
const trainedTroops = ref<VillageTroopEntry[]>([]);
const trainingQueue = ref<TrainingQueueItem[]>([]);
const loadingTroops = ref(true);
const loadingTrainingQueue = ref(true);
const now = ref(Date.now());
const resourceBalances = ref<ResourceBalances>({ wood: 0, clay: 0, iron: 0, gold: 0 });
const resourceCapacities = ref<ResourceBalances>({
  wood: 0,
  clay: 0,
  iron: 0,
  gold: 0,
});
const lastProductionRates = ref<ResourceBalances>({
  wood: 0,
  clay: 0,
  iron: 0,
  gold: 0,
});
const buildingStatuses = ref<BuildingStatus[]>([]);
const buildingQueue = ref<BuildingQueueItem[]>([]);

const numberFormatter = new Intl.NumberFormat();
let villagePoller: number | null = null;
let trainingTicker: number | null = null;
let detachSocket: (() => void) | null = null;

const addNotification = (message: string, type: string = "info") => {
  const id = Date.now();
  notifications.value.push({ id, message, type });
  setTimeout(() => {
    notifications.value = notifications.value.filter((n) => n.id !== id);
  }, 5000);
};

const formatNumber = (value: number) =>
  numberFormatter.format(Math.max(0, Math.floor(value || 0)));

const formatDuration = (seconds: number) => {
  if (seconds <= 0 || Number.isNaN(seconds)) {
    return "Done";
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
    return "Unknown";
  }
  return date.toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
};

const updateResourceCards = () => {
  resources.value = [
    {
      title: "Gold",
      subtitle: "Treasury",
      icon: "🪙",
      amount: resourceBalances.value.gold,
      capacity: resourceCapacities.value.gold,
      production: lastProductionRates.value.gold,
    },
    {
      title: "Wood",
      subtitle: "Resource",
      icon: "🪵",
      amount: resourceBalances.value.wood,
      capacity: resourceCapacities.value.wood,
      production: lastProductionRates.value.wood,
    },
    {
      title: "Clay",
      subtitle: "Resource",
      icon: "🧱",
      amount: resourceBalances.value.clay,
      capacity: resourceCapacities.value.clay,
      production: lastProductionRates.value.clay,
    },
    {
      title: "Iron",
      subtitle: "Resource",
      icon: "🔩",
      amount: resourceBalances.value.iron,
      capacity: resourceCapacities.value.iron,
      production: lastProductionRates.value.iron,
    },
  ];
};

const queueWithProgress = computed<TrainingQueueItemWithProgress[]>(() =>
  trainingQueue.value.map((item) => {
    const endDate = parseServerDate(item.end_time);
    if (!endDate) {
      return {
        ...item,
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

    return {
      ...item,
      remainingSeconds: Math.ceil(remaining / 1000),
      progress: Math.min(100, ((total - remaining) / total) * 100),
    };
  })
);

const sortedReadyTroops = computed(() =>
  [...trainedTroops.value].sort((a, b) =>
    a.troop.name.localeCompare(b.troop.name)
  )
);

const buildingQueueEntries = computed(() =>
  buildingQueue.value
    .slice()
    .sort((a, b) => new Date(a.end_time).getTime() - new Date(b.end_time).getTime())
    .map((entry) => {
      const status = buildingStatuses.value.find(
        (item) => item.internal_name === entry.building
      );

      const startTime = parseServerDate(entry.start_time)?.getTime() ?? 0;
      const endTime = parseServerDate(entry.end_time)?.getTime() ?? 0;
      const totalSeconds = Math.max(1, Math.floor((endTime - startTime) / 1000));
      const remainingSeconds = Math.max(0, Math.ceil((endTime - now.value) / 1000));
      const progress = Math.min(
        100,
        Math.max(0, ((totalSeconds - remainingSeconds) / totalSeconds) * 100)
      );

      return {
        id: entry.id,
        displayName: status?.name ?? entry.building,
        targetLevel: entry.target_level,
        remainingSeconds,
        finishAt: entry.end_time,
        progress,
      };
    })
);

const BUILDING_METADATA: Record<
  string,
  { icon: string; description: string; displayName?: string }
> = {
  wood_mill: {
    icon: "🌲",
    description: "Boosts hourly wood production.",
    displayName: "Wood Mill",
  },
  clay_pit: {
    icon: "🧱",
    description: "Boosts hourly clay production.",
    displayName: "Clay Pit",
  },
  iron_mine: {
    icon: "⛏️",
    description: "Boosts hourly iron production.",
    displayName: "Iron Mine",
  },
  town_hall: {
    icon: "🏛️",
    description: "Governance centre that mints gold and unlocks major upgrades.",
    displayName: "Town Hall",
  },
};

const RESOURCE_FIELDS = new Set(["wood", "clay", "iron", "gold"]);

const buildingCards = computed<BuildingCardView[]>(() =>
  buildingStatuses.value
    .filter((status) =>
      status.resource_field ? RESOURCE_FIELDS.has(status.resource_field) : false
    )
    .map((status) => {
      const endDate = status.upgrade_end_time
        ? parseServerDate(status.upgrade_end_time)
        : null;
      const durationSeconds = status.upgrade_duration ?? null;
      const totalMs = durationSeconds ? durationSeconds * 1000 : null;
    const endMs = endDate ? endDate.getTime() : null;
    const remainingMs =
      endMs !== null && totalMs !== null
        ? Math.max(endMs - now.value, 0)
        : null;
    const progress =
      endMs !== null && totalMs !== null && totalMs > 0
        ? Math.min(100, ((totalMs - (remainingMs ?? 0)) / totalMs) * 100)
        : 0;

    const metadata = BUILDING_METADATA[status.internal_name] ?? {
      icon: "???",
      description: "Structure upgrade.",
      displayName: status.name,
    };

    const nextCost = status.next_cost ?? null;
    const canAfford =
      !!nextCost &&
      resourceBalances.value.wood >= nextCost.wood &&
      resourceBalances.value.clay >= nextCost.clay &&
      resourceBalances.value.iron >= nextCost.iron;
    const canUpgrade =
      status.available && !status.is_upgrading && status.level < status.max_level && !!nextCost;

    return {
      name: metadata.displayName ?? status.name,
      internalName: status.internal_name,
      description: metadata.description,
      icon: metadata.icon,
      level: status.level,
      maxLevel: status.max_level,
      production: status.production,
      storage: status.storage ?? null,
      resourceField: status.resource_field ?? null,
      isUpgrading: status.is_upgrading,
      progress,
      remainingSeconds:
        remainingMs !== null ? Math.ceil(remainingMs / 1000) : null,
      canUpgrade,
      canAfford,
      nextCost,
      durationSeconds,
      upgradeEndTime: status.upgrade_end_time,
    };
  })
);

const updateProductionAndCapacitiesFromStatuses = () => {
  const woodStatus = buildingStatuses.value.find(
    (status) => status.internal_name === "wood_mill"
  );
  const clayStatus = buildingStatuses.value.find(
    (status) => status.internal_name === "clay_pit"
  );
  const ironStatus = buildingStatuses.value.find(
    (status) => status.internal_name === "iron_mine"
  );
  const warehouseStatus = buildingStatuses.value.find(
    (status) => status.internal_name === "warehouse"
  );
  const townHallStatus = buildingStatuses.value.find(
    (status) => status.internal_name === "town_hall"
  );
  const warehouseBonus = warehouseStatus?.storage ?? 0;

  if (woodStatus) {
    lastProductionRates.value.wood = woodStatus.production;
    if (woodStatus.storage != null) {
      resourceCapacities.value.wood = woodStatus.storage + warehouseBonus;
    }
  }
  if (clayStatus) {
    lastProductionRates.value.clay = clayStatus.production;
    if (clayStatus.storage != null) {
      resourceCapacities.value.clay = clayStatus.storage + warehouseBonus;
    }
  }
  if (ironStatus) {
    lastProductionRates.value.iron = ironStatus.production;
    if (ironStatus.storage != null) {
      resourceCapacities.value.iron = ironStatus.storage + warehouseBonus;
    }
  }
  if (townHallStatus) {
    lastProductionRates.value.gold = townHallStatus.production;
    if (townHallStatus.storage != null) {
      resourceCapacities.value.gold = townHallStatus.storage;
    }
  }

  updateResourceCards();
};

const fetchBuildingStatuses = async () => {
  if (!villageId.value) return;
  try {
    const [statusResponse, queueResponse] = await Promise.all([
      axios.get<BuildingStatus[]>(
        `${API_BASE}/villages/${villageId.value}/buildings`
      ),
      axios.get<BuildingQueueItem[]>(
        `${API_BASE}/villages/${villageId.value}/building-queue`
      ),
    ]);

    buildingStatuses.value = statusResponse.data ?? [];
    buildingQueue.value = queueResponse.data ?? [];

    updateProductionAndCapacitiesFromStatuses();
  } catch (error) {
    console.error("Error fetching building statuses:", error);
  }
};

const applyResourceUpdate = (
  resourcesPayload: ResourceBalances,
  capacitiesPayload: ResourceBalances
) => {
  resourceBalances.value = resourcesPayload;
  resourceCapacities.value = capacitiesPayload;
  updateResourceCards();
};

const fetchVillageData = async () => {
  try {
    const response = await axios.get(`${API_BASE}/villages/${villageId.value}`);
    const village = response.data;

    resourceBalances.value = {
      wood: village.wood ?? 0,
      clay: village.clay ?? 0,
      iron: village.iron ?? 0,
      gold: village.gold ?? 0,
    };
    updateResourceCards();

    await fetchBuildingStatuses();
  } catch (error: any) {
    if (error.response && error.response.status === 404) {
      addNotification("Village not found, creating a new one...", "info");
      try {
        const createResponse = await axios.post(`${API_BASE}/villages/`, {
          name: "My New Village",
        });
        villageId.value = createResponse.data.id;
        addNotification("New village created!", "success");
        await fetchVillageData();
      } catch (createError) {
        addNotification("Error creating village!", "error");
        console.error("Error creating village:", createError);
      }
    } else {
      addNotification("Failed to fetch village data.", "error");
      console.error("Full error object:", JSON.stringify(error, null, 2));
    }
  }
};

const fetchReadyTroops = async (showLoader = true) => {
  if (showLoader) {
    loadingTroops.value = true;
  }
  try {
    const response = await axios.get<VillageTroopEntry[]>(
      `${API_BASE}/villages/${villageId.value}/troops`
    );
    trainedTroops.value = response.data ?? [];
  } catch (error) {
    console.error("Error fetching trained troops:", error);
  } finally {
    if (showLoader) {
      loadingTroops.value = false;
    }
  }
};

const fetchTrainingQueueData = async (showLoader = true) => {
  if (showLoader) {
    loadingTrainingQueue.value = true;
  }
  try {
    const response = await axios.get<TrainingQueueItem[]>(
      `${API_BASE}/villages/${villageId.value}/training-queue`
    );
    trainingQueue.value = response.data ?? [];
  } catch (error) {
    console.error("Error fetching training queue:", error);
  } finally {
    if (showLoader) {
      loadingTrainingQueue.value = false;
    }
  }
};

const refreshMilitaryData = async (showLoader = true) => {
  await Promise.all([
    fetchReadyTroops(showLoader),
    fetchTrainingQueueData(showLoader),
  ]);
};

const handleUpgrade = async (buildingInternalName: string) => {
  const status = buildingStatuses.value.find(
    (entry) => entry.internal_name === buildingInternalName
  );
  const displayName = status?.name ?? buildingInternalName;

  try {
    const response = await axios.post<BuildingUpgradeResponse>(
      `${API_BASE}/villages/${villageId.value}/upgrade/${buildingInternalName}`
    );
    const data = response.data;
    resourceBalances.value = data.resources;
    buildingQueue.value = data.queue ?? [];
    updateResourceCards();
    await fetchBuildingStatuses();
    addNotification(
      data.message ?? `${displayName} upgrade started!`,
      "success"
    );
  } catch (error: any) {
    const detail = error.response?.data?.detail;
    if (typeof detail === "string") {
      addNotification(detail, "error");
    } else if (detail?.message) {
      addNotification(detail.message as string, "error");
    } else {
      addNotification(`Error upgrading ${displayName}.`, "error");
    }
    console.error(`Error upgrading ${buildingInternalName}:`, error);
  }
};

const { connect, onMessage, offMessage } = useWebSocket();

const handleSocketMessage = (event: MessageEvent) => {
  const message = event.data;

  if (
    message === `village:${villageId.value}:training_started` ||
    message === `village:${villageId.value}:training_finished`
  ) {
    fetchVillageData();
    refreshMilitaryData(false);
    return;
  }

  try {
    const payload = JSON.parse(message) as
      | ResourceUpdatePayload
      | BuildingUpgradeFinishedPayload;
    if (
      payload.type === "resources_updated" &&
      payload.village_id === villageId.value
    ) {
      applyResourceUpdate(payload.resources, payload.capacities);
      return;
    }
    if (
      payload.type === "building_upgrade_finished" &&
      payload.village_id === villageId.value
    ) {
      fetchVillageData();
    }
  } catch {
    // Ignore non-JSON payloads
  }
};

updateResourceCards();

onMounted(async () => {
  await fetchVillageData();
  await refreshMilitaryData();

  connect(villageId.value.toString());
  detachSocket = onMessage(handleSocketMessage);

  villagePoller = window.setInterval(() => {
    fetchVillageData();
    refreshMilitaryData(false);
  }, 10000);

  trainingTicker = window.setInterval(() => {
    now.value = Date.now();
  }, 1000);
});

onUnmounted(() => {
  if (villagePoller !== null) {
    window.clearInterval(villagePoller);
    villagePoller = null;
  }
  if (trainingTicker !== null) {
    window.clearInterval(trainingTicker);
    trainingTicker = null;
  }
  if (detachSocket) {
    detachSocket();
    detachSocket = null;
  }
  offMessage(handleSocketMessage);
});
</script>

<template>
  <main class="flex-1 p-8 overflow-y-auto">
    <!-- Header -->
    <header class="flex justify-between items-center mb-8">
      <div>
        <h2 class="text-4xl font-bold">Village Dashboard</h2>
        <p class="text-text-secondary">Welcome back, Commander!</p>
      </div>
      <div class="flex items-center gap-4">
        <div class="text-right">
          <p class="font-bold">Player Name</p>
          <p class="text-sm text-text-secondary">Level 1</p>
        </div>
        <div class="w-12 h-12 bg-surface rounded-full"></div>
      </div>
    </header>

    <!-- Resources -->
    <section class="mb-12">
      <h3 class="text-2xl font-bold mb-4">Resources</h3>
      <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
        <ResourceCard
          v-for="resource in resources"
          :key="resource.title"
          v-bind="resource"
        />
      </div>
    </section>

    <!-- Buildings -->
    <section>
      <h3 class="text-2xl font-bold mb-4">Buildings</h3>
      <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
        <BuildingCard
          v-for="card in buildingCards"
          :key="card.internalName"
          v-bind="card"
          @upgrade="handleUpgrade"
        />
      </div>
      <div
        class="mt-6 rounded-2xl border border-secondary/40 bg-surface/70 px-6 py-5 backdrop-blur"
      >
        <div class="flex items-center justify-between gap-4 mb-4">
          <h4 class="text-xl font-semibold">Construction Queue</h4>
          <span class="text-xs uppercase tracking-wide text-text-secondary/70">
            {{ buildingQueueEntries.length }} active
          </span>
        </div>
        <p v-if="!buildingQueueEntries.length" class="text-sm text-text-secondary">
          No buildings are currently being upgraded. Queue a project to keep your builders busy.
        </p>
        <ul v-else class="space-y-4">
          <li
            v-for="entry in buildingQueueEntries"
            :key="entry.id"
            class="rounded-xl border border-secondary/30 bg-background/60 px-4 py-3"
          >
            <div class="flex items-start justify-between gap-4">
              <div>
                <p class="text-base font-semibold text-text-primary">
                  {{ entry.displayName }} → Lv. {{ entry.targetLevel }}
                </p>
                <p class="text-xs text-text-secondary">
                  Ready {{ entry.remainingSeconds <= 0 ? 'any moment' : `in ${formatDuration(entry.remainingSeconds)}` }}
                </p>
              </div>
              <div class="text-right">
                <p class="text-[11px] uppercase tracking-wide text-text-secondary/60">Finishes at</p>
                <p class="text-sm font-medium text-text-primary">
                  {{ formatTimestamp(entry.finishAt) }}
                </p>
              </div>
            </div>
            <div class="mt-3 h-2 w-full rounded-full bg-secondary/30">
              <div
                class="h-full rounded-full bg-emerald-400 transition-[width] duration-300"
                :style="{ width: `${entry.progress}%` }"
              ></div>
            </div>
          </li>
        </ul>
      </div>
    </section>

    <!-- Military Overview -->
    <section class="mt-12">
      <h3 class="text-2xl font-bold mb-4">Military Overview</h3>
      <div class="grid grid-cols-1 gap-6 md:grid-cols-2">
        <div
          class="rounded-2xl border border-secondary/40 bg-surface/70 p-6 backdrop-blur"
        >
          <h4 class="text-xl font-semibold mb-3">Ready Troops</h4>
          <div
            v-if="loadingTroops"
            class="py-6 text-center text-text-secondary"
          >
            Loading troop counts...
          </div>
          <div
            v-else-if="!sortedReadyTroops.length"
            class="text-sm text-text-secondary"
          >
            No trained troops available. Visit the Barracks to start training
            your army.
          </div>
          <ul v-else class="space-y-3">
            <li
              v-for="troop in sortedReadyTroops"
              :key="troop.id"
              class="flex items-center justify-between rounded-lg border border-secondary/30 bg-background/60 px-4 py-3"
            >
              <span class="font-medium">{{ troop.troop.name }}</span>
              <span class="text-lg font-semibold">{{
                formatNumber(troop.quantity)
              }}</span>
            </li>
          </ul>
        </div>
        <div
          class="rounded-2xl border border-secondary/40 bg-surface/70 p-6 backdrop-blur"
        >
          <h4 class="text-xl font-semibold mb-3">Training Queue</h4>
          <div
            v-if="loadingTrainingQueue"
            class="py-6 text-center text-text-secondary"
          >
            Loading training queue...
          </div>
          <div
            v-else-if="!queueWithProgress.length"
            class="text-sm text-text-secondary"
          >
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
                  <p class="font-semibold">
                    {{ item.quantity }}x {{ item.troop.name }}
                  </p>
                  <p class="text-xs text-text-secondary">
                    Finishes at {{ formatTimestamp(item.end_time) }}
                  </p>
                </div>
                <div class="text-right">
                  <p class="text-xs text-text-secondary">Remaining</p>
                  <p class="text-base font-semibold">
                    {{
                      item.remainingSeconds <= 0
                        ? "Completed"
                        : formatDuration(item.remainingSeconds)
                    }}
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
        </div>
      </div>
    </section>
  </main>
</template>
