<template>
  <div
    class="group relative overflow-hidden rounded-2xl bg-surface p-6 border-2 border-secondary-700/50 shadow-lg hover:shadow-secondary-500/10 hover:border-secondary-500/50 transition-all duration-300 hover:scale-105"
  >
    <div class="absolute -top-10 -right-10 w-40 h-40 bg-secondary-500/10 rounded-full blur-2xl group-hover:scale-150 transition-transform duration-700"></div>

    <div class="relative z-10">
      <div class="relative mb-5">
        <div class="relative w-full h-40 rounded-xl bg-secondary-900 flex items-center justify-center overflow-hidden shadow-xl border-2 border-white/10">
          <span class="text-7xl drop-shadow-2xl">{{ icon }}</span>
          <div class="absolute inset-0 bg-gradient-to-t from-black/40 to-transparent"></div>
          <div
            v-if="isUpgrading"
            class="absolute inset-0 bg-black/70 backdrop-blur-sm flex flex-col items-center justify-center px-4 text-center"
          >
            <p class="text-sm uppercase tracking-wide text-white/70 mb-2">Upgrading...</p>
            <div class="w-full h-2 rounded-full bg-white/10 overflow-hidden">
              <div
                class="h-full bg-primary transition-[width]"
                :style="{ width: `${progress}%` }"
              ></div>
            </div>
            <p class="mt-2 text-xs text-white/80 font-semibold">
              {{ remainingLabel }}
            </p>
          </div>
        </div>
        <div
          class="absolute -top-3 -right-3 bg-gradient-to-br from-primary to-primary-700 text-white rounded-xl w-14 h-14 flex flex-col items-center justify-center font-bold text-lg shadow-lg shadow-primary-500/50 border-2 border-white/20"
        >
          <span>{{ level }}</span>
          <span class="text-[10px] font-medium">/ {{ maxLevel }}</span>
        </div>
      </div>

      <h3 class="text-xl font-bold text-text-primary mb-1">{{ name }}</h3>
      <p class="text-sm text-text-secondary mb-4 leading-relaxed">{{ description }}</p>

      <div class="text-xs text-text-secondary mb-3 space-y-1">
        <p>Production: <span class="font-semibold text-text-primary">{{ formattedProduction }}/h</span></p>
        <p v-if="storage !== null">
          Storage: <span class="font-semibold text-text-primary">{{ formatNumber(storage) }}</span>
        </p>
      </div>

      <div v-if="nextCostLabel" class="text-sm text-text-secondary mb-4 space-y-1">
        <p>{{ nextCostLabel }}</p>
        <p v-if="upgradeDurationLabel" class="text-xs text-text-secondary/80">
          Duration: {{ upgradeDurationLabel }}
        </p>
      </div>
      <div v-else class="text-sm text-text-secondary mb-4">Maximum level reached.</div>

      <button
        @click="emitUpgrade"
        :disabled="isUpgradeDisabled"
        :class="[
          'w-full py-3 px-5 rounded-xl font-bold text-base shadow-lg transition-all duration-300 border-2',
          isUpgradeDisabled
            ? 'bg-gray-700/50 text-gray-500 cursor-not-allowed border-gray-600/30'
            : 'bg-primary text-white hover:bg-primary-600 hover:scale-105 hover:shadow-primary-500/50 border-primary-400/30'
        ]"
      >
        {{ buttonLabel }}
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';

interface BuildingCost {
  wood: number;
  clay: number;
  iron: number;
}

interface Props {
  name: string;
  internalName: string;
  description: string;
  icon: string;
  level: number;
  maxLevel: number;
  production: number;
  storage: number | null;
  isUpgrading: boolean;
  progress: number;
  remainingSeconds: number | null;
  durationSeconds: number | null;
  nextCost: BuildingCost | null;
  canUpgrade: boolean;
  canAfford: boolean;
}

const props = defineProps<Props>();
const emit = defineEmits<{
  (e: 'upgrade', buildingInternalName: string): void;
}>();

const numberFormatter = new Intl.NumberFormat();

const formatNumber = (value: number) => numberFormatter.format(Math.max(0, Math.floor(value || 0)));

const formatDuration = (seconds: number) => {
  if (!seconds || seconds <= 0) {
    return 'Done';
  }
  const minutes = Math.floor(seconds / 60);
  const hours = Math.floor(minutes / 60);
  const remMinutes = minutes % 60;
  const remSeconds = seconds % 60;

  if (hours > 0) {
    return `${hours}h ${remMinutes}m`;
  }
  if (minutes > 0) {
    return `${minutes}m ${remSeconds}s`;
  }
  return `${remSeconds}s`;
};

const remainingLabel = computed(() =>
  props.remainingSeconds !== null ? formatDuration(props.remainingSeconds) : 'In queue'
);

const formattedProduction = computed(() => formatNumber(props.production));

const nextCostLabel = computed(() => {
  if (!props.nextCost) {
    return null;
  }
  return `Cost: ${formatNumber(props.nextCost.wood)} Wood · ${formatNumber(props.nextCost.clay)} Clay · ${formatNumber(props.nextCost.iron)} Iron`;
});

const upgradeDurationLabel = computed(() => {
  if (!props.nextCost) {
    return null;
  }
  if (!props.durationSeconds || props.durationSeconds <= 0) {
    return 'Instant';
  }
  return formatDuration(props.durationSeconds);
});

const buttonLabel = computed(() => {
  if (!props.nextCost || props.level >= props.maxLevel) {
    return 'Max level reached';
  }
  if (props.isUpgrading) {
    return 'Upgrading...';
  }
  return `Upgrade to Level ${props.level + 1}`;
});

const isUpgradeDisabled = computed(
  () => props.isUpgrading || !props.canUpgrade || !props.nextCost || !props.canAfford
);

function emitUpgrade() {
  if (isUpgradeDisabled.value) {
    return;
  }
  emit('upgrade', props.internalName);
}
</script>
