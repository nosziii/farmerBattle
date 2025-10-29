<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from "vue";
import { createFarmScene, type FarmSceneHandle, type StructureSnapshot } from "./usePixiFarmScene";

type ResourceKey = "wood" | "clay" | "iron" | "gold";

const props = defineProps<{
  structures: StructureSnapshot[];
  resources: Record<ResourceKey, number>;
  loading?: boolean;
}>();

const emit = defineEmits<{
  (e: "structure-select", internalName: string): void;
}>();

const stageRef = ref<HTMLDivElement | null>(null);
const sceneHandle = ref<FarmSceneHandle | null>(null);
const sceneReady = ref(false);
const selectedStructureId = ref<string | null>(null);

const resourceEntries = computed(() => {
  const descriptors: Array<{ key: ResourceKey; label: string; accent: string }> = [
    { key: "wood", label: "Fa", accent: "#4ade80" },
    { key: "clay", label: "Agyag", accent: "#f97316" },
    { key: "iron", label: "Vas", accent: "#94a3b8" },
    { key: "gold", label: "Arany", accent: "#facc15" },
  ];

  return descriptors.map((item) => ({
    ...item,
    value: props.resources?.[item.key] ?? 0,
  }));
});

const selectedStructure = computed(() => {
  if (!selectedStructureId.value) {
    return null;
  }
  return props.structures.find((entry) => entry.internalName === selectedStructureId.value) ?? null;
});

const formatNumber = (value: number) =>
  new Intl.NumberFormat("hu-HU", {
    maximumFractionDigits: value >= 1000 ? 0 : 1,
  }).format(Math.max(0, Math.floor(value)));

const mountScene = async () => {
  if (!stageRef.value) {
    return;
  }

  const handle = await createFarmScene({
    container: stageRef.value,
    onStructureSelect: (internalName) => {
      selectedStructureId.value = internalName;
      emit("structure-select", internalName);
    },
  });
  sceneHandle.value = handle;
  sceneReady.value = true;
  await handle.syncStructures(props.structures);
};

const syncStructures = async (structures: StructureSnapshot[]) => {
  if (!sceneHandle.value) {
    return;
  }
  await sceneHandle.value.syncStructures(structures);
  if (selectedStructureId.value && !structures.find((entry) => entry.internalName === selectedStructureId.value)) {
    selectedStructureId.value = null;
  }
};

const handleResize = () => {
  sceneHandle.value?.resize();
};

onMounted(async () => {
  await mountScene();
  window.addEventListener("resize", handleResize);
});

onUnmounted(() => {
  window.removeEventListener("resize", handleResize);
  sceneHandle.value?.destroy();
  sceneHandle.value = null;
});

watch(
  () => props.structures,
  async (next) => {
    await syncStructures(next);
  },
  { deep: true },
);
</script>

<template>
  <div class="farm-scene">
    <div ref="stageRef" class="farm-scene__stage"></div>

    <div class="farm-scene__overlay">
      <transition name="farm-scene-fade" mode="out-in">
        <div
          v-if="loading || !sceneReady"
          key="scene-loading"
          class="farm-scene__loading"
        >
          Település betöltése...
        </div>
        <div
          v-else
          key="scene-resources"
          class="farm-scene__resources"
        >
          <div
            v-for="entry in resourceEntries"
            :key="entry.key"
            class="farm-scene__resource"
          >
            <span class="farm-scene__resource-label" :style="{ color: entry.accent }">
              {{ entry.label }}
            </span>
            <span class="farm-scene__resource-value">
              {{ formatNumber(entry.value) }}
            </span>
          </div>
        </div>
      </transition>

      <transition name="farm-scene-fade">
        <div
          v-if="selectedStructure"
          class="farm-scene__info"
        >
          <p class="farm-scene__info-title">
            {{ selectedStructure.name }} ({{ selectedStructure.level }}. szint)
          </p>
          <p class="farm-scene__info-sub">
            <span v-if="selectedStructure.isUpgrading">Fejlesztés alatt • {{ Math.round(selectedStructure.progress * 100) }}%</span>
            <span v-else-if="selectedStructure.canUpgrade">Fejleszthető</span>
            <span v-else>Aktív</span>
          </p>
        </div>
        <div
          v-else
          class="farm-scene__hint"
        >
          Forgasd a teret, és kattints egy épületre a részletekhez.
        </div>
      </transition>
    </div>
  </div>
</template>

<style scoped>
.farm-scene {
  position: relative;
  width: 100%;
  min-height: clamp(320px, 58vh, 560px);
  border-radius: 28px;
  border: 1px solid rgba(148, 163, 184, 0.35);
  background: radial-gradient(circle at 20% 20%, rgba(56, 189, 248, 0.12), transparent 65%),
    radial-gradient(circle at 80% 30%, rgba(251, 191, 36, 0.12), transparent 60%),
    linear-gradient(135deg, rgba(15, 23, 42, 0.92), rgba(30, 41, 59, 0.96));
  box-shadow:
    0 22px 48px -32px rgba(14, 116, 144, 0.65),
    inset 0 0 0 1px rgba(148, 163, 184, 0.12);
  overflow: hidden;
}

.farm-scene__stage {
  width: 100%;
  height: 100%;
}

.farm-scene__stage canvas {
  width: 100%;
  height: 100%;
  display: block;
}

.farm-scene__overlay {
  pointer-events: none;
  position: absolute;
  inset: 0;
  padding: 24px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

.farm-scene__loading {
  align-self: center;
  margin-top: clamp(80px, 18vh, 140px);
  padding: 16px 28px;
  border-radius: 999px;
  background: rgba(15, 23, 42, 0.88);
  border: 1px solid rgba(148, 163, 184, 0.3);
  font-size: 0.85rem;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: rgba(226, 232, 240, 0.85);
  text-align: center;
  box-shadow: 0 18px 36px -26px rgba(15, 23, 42, 0.8);
}

.farm-scene__resources {
  pointer-events: none;
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
  align-items: start;
  justify-items: center;
  margin-inline: auto;
  width: min(100%, 640px);
}

.farm-scene__resource {
  background: rgba(15, 23, 42, 0.72);
  border: 1px solid rgba(148, 163, 184, 0.22);
  border-radius: 16px;
  padding: 14px 18px 16px;
  text-align: center;
  backdrop-filter: blur(12px);
  box-shadow: 0 10px 30px -18px rgba(15, 23, 42, 0.8);
}

.farm-scene__resource-label {
  font-size: 0.7rem;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  display: block;
  margin-bottom: 6px;
}

.farm-scene__resource-value {
  font-size: 1.25rem;
  font-weight: 600;
  color: rgba(226, 232, 240, 0.95);
  text-shadow: 0 1px 2px rgba(15, 23, 42, 0.6);
}

.farm-scene__info {
  align-self: center;
  margin-bottom: 12px;
  padding: 16px 22px;
  border-radius: 18px;
  background: rgba(15, 23, 42, 0.9);
  border: 1px solid rgba(148, 163, 184, 0.35);
  text-align: center;
  box-shadow:
    0 18px 40px -28px rgba(56, 189, 248, 0.6),
    inset 0 0 0 1px rgba(148, 163, 184, 0.12);
}

.farm-scene__info-title {
  font-weight: 600;
  font-size: 1.05rem;
  color: rgba(226, 232, 240, 0.96);
}

.farm-scene__info-sub {
  margin-top: 4px;
  font-size: 0.85rem;
  color: rgba(148, 163, 184, 0.9);
  letter-spacing: 0.02em;
}

.farm-scene__hint {
  align-self: center;
  margin-bottom: 24px;
  padding: 14px 24px;
  border-radius: 999px;
  background: rgba(15, 23, 42, 0.8);
  border: 1px solid rgba(148, 163, 184, 0.25);
  font-size: 0.8rem;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: rgba(226, 232, 240, 0.7);
  box-shadow: 0 18px 36px -28px rgba(15, 23, 42, 0.8);
}

.farm-scene-fade-enter-active,
.farm-scene-fade-leave-active {
  transition: opacity 0.25s ease, transform 0.25s ease;
}

.farm-scene-fade-enter-from,
.farm-scene-fade-leave-to {
  opacity: 0;
  transform: translateY(6px);
}

@media (max-width: 900px) {
  .farm-scene__resources {
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 10px;
  }

  .farm-scene__resource {
    width: 100%;
  }
}
</style>
