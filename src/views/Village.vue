<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed, watch, nextTick } from "vue";

import ResourceCard from "../components/ResourceCard.vue";
import BuildingCard from "../components/BuildingCard.vue";
import FarmScene from "../components/pixi/FarmScene.vue";
import type { StructureSnapshot as SceneStructureSnapshot } from "../components/pixi/usePixiFarmScene";
import axios from "axios";
import { useWebSocket } from "../services/websocket";
import { ensureAuthReady } from "../services/auth";
import { useI18n } from "../i18n";
import type {
  BuildingStatus,
  BuildingCost,
  BuildingQueueItem,
} from "../types/buildings";
import type { ExpeditionListResponse, ExpeditionSummary } from "../types/expeditions";
import { decorateExpedition, formatDuration as formatExpeditionDuration, type ExpeditionWithProgress } from "../utils/expeditions";
import {
  API_BASE,
  activeVillageId,
  ensureActiveVillageId,
  setActiveVillageId,
} from "../services/villageState";

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
const villageId = activeVillageId;
const notifications = ref<any[]>([]);
const trainedTroops = ref<VillageTroopEntry[]>([]);
const trainingQueue = ref<TrainingQueueItem[]>([]);
const expeditions = ref<ExpeditionSummary[]>([]);
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
const { t } = useI18n();
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
    return t("common.duration.done");
  }
  const mins = Math.floor(seconds / 60);
  const hrs = Math.floor(mins / 60);
  const remMins = mins % 60;
  const remSecs = seconds % 60;

  if (hrs > 0) {
    return t("common.duration.hoursMinutes", { hours: hrs, minutes: remMins });
  }
  if (mins > 0) {
    return t("common.duration.minutesSeconds", { minutes: mins, seconds: remSecs });
  }
  return t("common.duration.seconds", { seconds: remSecs });
};

const formatTimestamp = (value: string) => {
  const date = parseServerDate(value);
  if (!date) {
    return t("common.unknown");
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
      title: t("village.resources.gold.title"),
      subtitle: t("village.resources.gold.subtitle"),
      icon: "🪙",
      amount: resourceBalances.value.gold,
      capacity: resourceCapacities.value.gold,
      production: lastProductionRates.value.gold,
    },
    {
      title: t("village.resources.wood.title"),
      subtitle: t("village.resources.wood.subtitle"),
      icon: "🪵",
      amount: resourceBalances.value.wood,
      capacity: resourceCapacities.value.wood,
      production: lastProductionRates.value.wood,
    },
    {
      title: t("village.resources.clay.title"),
      subtitle: t("village.resources.clay.subtitle"),
      icon: "🧱",
      amount: resourceBalances.value.clay,
      capacity: resourceCapacities.value.clay,
      production: lastProductionRates.value.clay,
    },
    {
      title: t("village.resources.iron.title"),
      subtitle: t("village.resources.iron.subtitle"),
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

type ExpeditionProgressCard = ExpeditionWithProgress & {
  phaseLabel: string;
  etaLabel: string;
};

const getExpeditionTargetTime = (entry: ExpeditionWithProgress) => {
  if (entry.currentPhase === "outbound") {
    return parseServerDate(entry.arrive_at)?.getTime() ?? Number.POSITIVE_INFINITY;
  }
  if (entry.currentPhase === "returning") {
    return parseServerDate(entry.return_at)?.getTime() ?? Number.POSITIVE_INFINITY;
  }
  return Number.POSITIVE_INFINITY;
};

const activeExpeditionsWithProgress = computed<ExpeditionProgressCard[]>(() => {
  const nowMs = now.value;
  return expeditions.value
    .filter(
      (expedition) =>
        expedition.status === "outbound" || expedition.status === "returning"
    )
    .map((expedition) => {
      const decorated = decorateExpedition(expedition, nowMs);
      const phaseLabel =
        decorated.currentPhase === "outbound"
          ? t("expeditions.phases.outbound")
          : decorated.currentPhase === "returning"
          ? t("expeditions.phases.returning")
          : t("expeditions.phases.completed");
      const etaLabel =
        decorated.currentPhase === "completed"
          ? t("expeditions.labels.arrived")
          : formatExpeditionDuration(decorated.etaSeconds);
      return {
        ...decorated,
        phaseLabel,
        etaLabel,
      };
    })
    .sort((a, b) => getExpeditionTargetTime(a) - getExpeditionTargetTime(b))
    .slice(0, 3);
});

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

const SCENE_STRUCTURE_ORDER = [
  "town_hall",
  "warehouse",
  "barracks",
  "wood_mill",
  "clay_pit",
  "iron_mine",
  "market",
  "stable",
] as const;

const SCENE_STRUCTURE_INDEX = new Map<string, number>(
  SCENE_STRUCTURE_ORDER.map((name, index) => [name as string, index])
);

const computeUpgradeProgress = (status: BuildingStatus, nowMs: number) => {
  if (
    !status.is_upgrading ||
    !status.upgrade_duration ||
    !status.upgrade_end_time
  ) {
    return 0;
  }
  const endDate = parseServerDate(status.upgrade_end_time);
  if (!endDate) {
    return 0;
  }
  const totalMs = status.upgrade_duration * 1000;
  if (!totalMs) {
    return 0;
  }
  const startMs = endDate.getTime() - totalMs;
  const elapsed = nowMs - startMs;
  if (elapsed <= 0) {
    return 0;
  }
  return Math.min(1, Math.max(0, elapsed / totalMs));
};

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
    const progressRatio = computeUpgradeProgress(status, now.value);
    const progress = progressRatio * 100;

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

const sceneStructures = computed<SceneStructureSnapshot[]>(() => {
  const statuses = buildingStatuses.value;
  if (!statuses.length) {
    return [];
  }
  const nowMs = now.value;
  return statuses
    .filter((status) => SCENE_STRUCTURE_INDEX.has(status.internal_name))
    .map((status) => {
      const order = SCENE_STRUCTURE_INDEX.get(status.internal_name) ?? 99;
      return {
        internalName: status.internal_name,
        name: status.name,
        level: status.level,
        isUpgrading: status.is_upgrading,
        canUpgrade:
          status.available &&
          !status.is_upgrading &&
          status.level < status.max_level &&
          !!status.next_cost,
        progress: computeUpgradeProgress(status, nowMs),
        order,
      };
    })
    .sort((a, b) => a.order - b.order)
    .map(({ order, ...rest }) => rest);
});

const sceneLoading = computed(() => buildingStatuses.value.length === 0);

const highlightedStructureId = ref<string | null>(null);
let highlightClearHandle: number | null = null;

const handleStructureSelect = (internalName: string) => {
  highlightedStructureId.value = internalName;
  if (highlightClearHandle !== null) {
    window.clearTimeout(highlightClearHandle);
  }
  highlightClearHandle = window.setTimeout(() => {
    highlightedStructureId.value = null;
    highlightClearHandle = null;
  }, 4200);
  nextTick(() => {
    const target = document.querySelector<HTMLElement>(
      `[data-building-tile="${internalName}"]`
    );
    target?.scrollIntoView({ behavior: "smooth", block: "center" });
  });
};

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
  if (!villageId.value) {
    return;
  }
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
      addNotification(t("village.notifications.creatingVillage"), "info");
      try {
        const createResponse = await axios.post(`${API_BASE}/villages/`, {
          name: "My New Village",
        });
        const newId = createResponse.data.id;
        setActiveVillageId(newId);
        addNotification(t("village.notifications.created"), "success");
        await fetchVillageData();
      } catch (createError) {
        addNotification(t("village.notifications.createError"), "error");
        console.error("Error creating village:", createError);
      }
    } else {
      addNotification(t("village.notifications.fetchFailed"), "error");
      console.error("Full error object:", JSON.stringify(error, null, 2));
    }
  }
};

const fetchReadyTroops = async (showLoader = true) => {
  if (!villageId.value) {
    return;
  }
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
  if (!villageId.value) {
    return;
  }
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

const fetchExpeditionData = async () => {
  if (!villageId.value) return;
  try {
    const { data } = await axios.get<ExpeditionListResponse>(`${API_BASE}/villages/${villageId.value}/expeditions`);
    expeditions.value = [...data.active, ...data.completed];
  } catch (error) {
    console.error("Error fetching expeditions", error);
  }
};

const handleUpgrade = async (buildingInternalName: string) => {
  if (!villageId.value) {
    addNotification(t("common.notifications.noActiveVillage"), "error");
    return;
  }
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
      data.message ?? t("village.notifications.upgradeStartedCustom", { building: displayName }),
      "success"
    );
  } catch (error: any) {
    const detail = error.response?.data?.detail;
    if (typeof detail === "string") {
      addNotification(detail, "error");
    } else if (detail?.message) {
      addNotification(detail.message as string, "error");
    } else {
      addNotification(t("village.notifications.upgradeError", { building: displayName }), "error");
    }
    console.error(`Error upgrading ${buildingInternalName}:`, error);
  }
};

const { connect, onMessage, offMessage } = useWebSocket();

const handleSocketMessage = (event: MessageEvent) => {
  const currentId = villageId.value;
  if (!currentId) {
    return;
  }
  const message = event.data;

  if (
    message === `village:${currentId}:training_started` ||
    message === `village:${currentId}:training_finished`
  ) {
    fetchVillageData();
    refreshMilitaryData(false);
    return;
  }
  if (message === `village:${currentId}:expedition_updated`) {
    fetchExpeditionData();
    return;
  }

  try {
    const payload = JSON.parse(message) as
      | ResourceUpdatePayload
      | BuildingUpgradeFinishedPayload
      | {
          type: "expedition_update";
          village_id: number;
          expedition: ExpeditionSummary;
        };
    if (
      payload.type === "resources_updated" &&
      payload.village_id === currentId
    ) {
      applyResourceUpdate(payload.resources, payload.capacities);
      return;
    }
    if (
      payload.type === "building_upgrade_finished" &&
      payload.village_id === currentId
    ) {
      fetchVillageData();
      return;
    }
    if (
      payload.type === "expedition_update" &&
      payload.village_id === currentId &&
      payload.expedition
    ) {
      const summary = payload.expedition;
      expeditions.value = [
        summary,
        ...expeditions.value.filter((entry) => entry.id !== summary.id),
      ];
    }
  } catch {
    // Ignore non-JSON payloads
  }
};

updateResourceCards();

onMounted(async () => {
  await ensureAuthReady();
  try {
    await ensureActiveVillageId();
  } catch (error) {
    addNotification(t("village.notifications.ensureActiveFailed"), "error");
    console.error("Unable to ensure active village id:", error);
    return;
  }

  if (!villageId.value) {
    return;
  }

  await fetchVillageData();
  await refreshMilitaryData();
  await fetchExpeditionData();

  connect(villageId.value.toString());
  detachSocket = onMessage(handleSocketMessage);

  villagePoller = window.setInterval(() => {
    fetchVillageData();
    refreshMilitaryData(false);
    fetchExpeditionData();
  }, 10000);

  trainingTicker = window.setInterval(() => {
    now.value = Date.now();
  }, 1000);
});

watch(
  activeVillageId,
  async (newId, oldId) => {
    if (!newId || newId === oldId) {
    return;
  }
  await fetchVillageData();
  await refreshMilitaryData();
  await fetchExpeditionData();
  connect(newId.toString());
}
);

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
  if (highlightClearHandle !== null) {
    window.clearTimeout(highlightClearHandle);
    highlightClearHandle = null;
  }
  offMessage(handleSocketMessage);
});
</script>

<template>
  <main class="flex-1 p-8 overflow-y-auto">
    <!-- Header -->
    <header class="flex justify-between items-center mb-8">
      <div>
        <h2 class="text-4xl font-bold">{{ t('village.header.title') }}</h2>
        <p class="text-text-secondary">{{ t('village.header.subtitle') }}</p>
      </div>
      <div class="flex items-center gap-4">
        <div class="text-right">
          <p class="font-bold">{{ t('village.header.playerName') }}</p>
          <p class="text-sm text-text-secondary">{{ t('village.header.playerLevel') }}</p>
        </div>
        <div class="w-12 h-12 bg-surface rounded-full" :aria-label="t('village.header.avatarLabel')"></div>
      </div>
    </header>

    <section class="mb-12">
      <FarmScene
        :structures="sceneStructures"
        :resources="resourceBalances"
        :loading="sceneLoading"
        @structure-select="handleStructureSelect"
      />
    </section>

    <!-- Resources -->
    <section class="mb-12">
      <h3 class="text-2xl font-bold mb-4">{{ t('village.sections.resources') }}</h3>
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
      <h3 class="text-2xl font-bold mb-4">{{ t('village.sections.buildings') }}</h3>
      <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div
          v-for="card in buildingCards"
          :key="card.internalName"
          :data-building-tile="card.internalName"
          class="h-full transition-all duration-300"
          :class="{
            'ring-2 ring-primary/70 ring-offset-2 ring-offset-background shadow-[0_18px_40px_-24px_rgba(56,189,248,0.45)] scale-[1.02]':
              highlightedStructureId === card.internalName,
          }"
        >
          <BuildingCard
            v-bind="card"
            @upgrade="handleUpgrade"
          />
        </div>
      </div>
      <div
        class="mt-6 rounded-2xl border border-secondary/40 bg-surface/70 px-6 py-5 backdrop-blur"
      >
        <div class="flex items-center justify-between gap-4 mb-4">
          <h4 class="text-xl font-semibold">{{ t('village.buildingQueue.title') }}</h4>
          <span class="text-xs uppercase tracking-wide text-text-secondary/70">
            {{ t('village.buildingQueue.count', { count: buildingQueueEntries.length }) }}
          </span>
        </div>
        <p v-if="!buildingQueueEntries.length" class="text-sm text-text-secondary">
          {{ t('village.buildingQueue.empty') }}
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
                  {{ entry.displayName }} → {{ t('common.levelShort', { level: entry.targetLevel }) }}
                </p>
                <p class="text-xs text-text-secondary">
                  {{
                    entry.remainingSeconds <= 0
                      ? t('common.duration.anyMoment')
                      : t('common.duration.inDuration', { duration: formatDuration(entry.remainingSeconds) })
                  }}
                </p>
              </div>
              <div class="text-right">
                <p class="text-[11px] uppercase tracking-wide text-text-secondary/60">
                  {{ t('village.buildingQueue.finishesAt') }}
                </p>
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
      <h3 class="text-2xl font-bold mb-4">{{ t('village.sections.military') }}</h3>
      <div class="grid grid-cols-1 gap-6 md:grid-cols-2">
        <div
          class="rounded-2xl border border-secondary/40 bg-surface/70 p-6 backdrop-blur"
        >
          <h4 class="text-xl font-semibold mb-3">{{ t('village.military.readyTroops.title') }}</h4>
          <div
            v-if="loadingTroops"
            class="py-6 text-center text-text-secondary"
          >
            {{ t('village.military.readyTroops.loading') }}
          </div>
          <div
            v-else-if="!sortedReadyTroops.length"
            class="text-sm text-text-secondary"
          >
            {{ t('village.military.readyTroops.empty') }}
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
          <h4 class="text-xl font-semibold mb-3">{{ t('village.military.trainingQueue.title') }}</h4>
          <div
            v-if="loadingTrainingQueue"
            class="py-6 text-center text-text-secondary"
          >
            {{ t('village.military.trainingQueue.loading') }}
          </div>
          <div
            v-else-if="!queueWithProgress.length"
            class="text-sm text-text-secondary"
          >
            {{ t('village.military.trainingQueue.empty') }}
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
                    {{ t('common.quantity', { value: item.quantity }) }} {{ item.troop.name }}
                  </p>
                  <p class="text-xs text-text-secondary">
                    {{ t('village.military.trainingQueue.finishesAt', { time: formatTimestamp(item.end_time) }) }}
                  </p>
                </div>
                <div class="text-right">
                  <p class="text-xs text-text-secondary">{{ t('village.military.trainingQueue.remainingLabel') }}</p>
                  <p class="text-base font-semibold">
                    {{
                      item.remainingSeconds <= 0
                        ? t('village.military.trainingQueue.completed')
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
        <div
          class="rounded-2xl border border-secondary/40 bg-surface/70 p-6 backdrop-blur md:col-span-2"
        >
          <div class="mb-4 flex items-center justify-between gap-4">
            <h4 class="text-xl font-semibold">{{ t('village.expeditions.title') }}</h4>
            <RouterLink
              to="/expeditions"
              class="text-xs font-semibold uppercase tracking-wide text-primary hover:text-primary/80"
            >
              {{ t('village.expeditions.manageLink') }}
            </RouterLink>
          </div>
          <div
            v-if="!activeExpeditionsWithProgress.length"
            class="text-sm text-text-secondary"
          >
            {{ t('village.expeditions.empty') }}
          </div>
          <ul v-else class="space-y-4">
            <li
              v-for="entry in activeExpeditionsWithProgress"
              :key="entry.id"
              class="rounded-xl border border-secondary/30 bg-background/60 px-4 py-3"
            >
              <div class="flex items-start justify-between gap-4">
                <div>
                  <p class="text-base font-semibold text-text-primary">
                    {{ entry.barbarian_name }}
                  </p>
                  <p class="text-xs text-text-secondary">
                    {{ t('village.expeditions.distancePhase', {
                      distance: entry.distance,
                      phase: entry.phaseLabel,
                    }) }}
                    • {{ t('village.expeditions.eta', { eta: entry.etaLabel }) }}
                  </p>
                </div>
                <div class="text-right text-sm text-text-secondary">
                  <p class="text-[11px] uppercase tracking-wide text-text-secondary/60">
                    {{ t('village.expeditions.statusLabel') }}
                  </p>
                  <p class="font-semibold text-text-primary">
                    {{
                      entry.currentPhase === "returning"
                        ? t('village.expeditions.statusReturning')
                        : t('village.expeditions.statusTravelling')
                    }}
                  </p>
                </div>
              </div>
              <div class="mt-3 space-y-2">
                <div>
                  <div class="mb-1 flex items-center justify-between text-[11px] uppercase tracking-wide text-text-secondary/70">
                    <span>{{ t('village.expeditions.outboundLabel') }}</span>
                    <span>{{ Math.round(entry.outboundProgress * 100) }}%</span>
                  </div>
                  <div class="h-2 w-full rounded-full bg-secondary/30">
                    <div
                      class="h-full rounded-full bg-primary transition-[width]"
                      :style="{ width: `${Math.round(entry.outboundProgress * 100)}%` }"
                    ></div>
                  </div>
                </div>
                <div
                  v-if="entry.currentPhase !== 'outbound' || entry.returnProgress > 0"
                >
                  <div class="mb-1 flex items-center justify-between text-[11px] uppercase tracking-wide text-text-secondary/70">
                    <span>{{ t('village.expeditions.returnLabel') }}</span>
                    <span>{{ Math.round(entry.returnProgress * 100) }}%</span>
                  </div>
                  <div class="h-2 w-full rounded-full bg-secondary/30">
                    <div
                      class="h-full rounded-full bg-emerald-400 transition-[width]"
                      :style="{ width: `${Math.round(entry.returnProgress * 100)}%` }"
                    ></div>
                  </div>
                </div>
              </div>
              <div class="mt-3 grid gap-2 text-[11px] uppercase tracking-wide text-text-secondary/60 md:grid-cols-3">
                <span>{{ t('village.expeditions.departedAt', { time: formatTimestamp(entry.departed_at ?? "") }) }}</span>
                <span>{{ t('village.expeditions.arrivalAt', { time: formatTimestamp(entry.arrive_at ?? "") }) }}</span>
                <span>{{ t('village.expeditions.returnAt', { time: formatTimestamp(entry.return_at ?? "") }) }}</span>
              </div>
            </li>
          </ul>
        </div>
      </div>
    </section>
  </main>
</template>
