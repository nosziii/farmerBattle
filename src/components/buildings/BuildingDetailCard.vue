<template>
  <article
    class="rounded-2xl border border-secondary-700/40 bg-secondary-900/60 shadow-lg shadow-black/10 transition hover:border-primary-500/40 hover:shadow-primary-500/20"
  >
    <header class="flex flex-wrap items-start justify-between gap-4 border-b border-secondary-700/30 px-6 py-5">
      <div class="flex items-start gap-4">
        <div
          class="grid h-14 w-14 place-items-center rounded-xl bg-secondary-800/80 text-3xl"
        >
          {{ status.icon || '🏛️' }}
        </div>
        <div class="space-y-1">
          <p class="text-[11px] uppercase tracking-wide text-text-secondary/70">
            {{ translateCategory(status.category) }}
          </p>
          <h3 class="text-lg font-semibold text-text-primary">
            {{ status.name }}
          </h3>
          <p class="text-sm text-text-secondary leading-relaxed">
            {{ status.description }}
          </p>
        </div>
      </div>
      <div class="text-right">
        <p class="text-xs uppercase tracking-wide text-text-secondary/70">
          {{ t('components.buildingDetail.levelHeading') }}
        </p>
        <p class="text-xl font-semibold text-text-primary">
          {{ status.level }} / {{ status.max_level }}
        </p>
      </div>
    </header>

    <section class="px-6 py-5 space-y-6">
      <div v-if="status.effects.length" class="space-y-2">
        <p class="text-[11px] uppercase tracking-wide text-text-secondary/70">
          {{ t('components.buildingDetail.effectsHeading') }}
        </p>
        <ul class="space-y-1 text-sm text-text-secondary">
          <li v-for="effect in status.effects" :key="effect" class="flex items-start gap-2">
            <span class="mt-[2px] text-primary">•</span>
            <span>{{ effect }}</span>
          </li>
        </ul>
      </div>

      <div v-if="status.requirements.length" class="space-y-2">
        <p class="text-[11px] uppercase tracking-wide text-text-secondary/70">
          {{ t('components.buildingDetail.requirementsHeading') }}
        </p>
        <ul class="space-y-1 text-sm">
          <li
            v-for="requirement in status.requirements"
            :key="requirement.building"
            class="flex items-center justify-between rounded-md border border-secondary-700/40 bg-secondary-900/70 px-3 py-2"
            :class="requirement.met ? 'border-emerald-500/40' : 'border-red-500/30'"
          >
            <span class="text-text-secondary">
              {{ requirement.display_name }}
              <span class="text-text-secondary/70">
                {{ t('components.buildingDetail.levelShort', { level: requirement.required_level }) }}
              </span>
            </span>
            <span
              :class="requirement.met ? 'text-emerald-300' : 'text-red-400'"
              class="text-sm font-semibold"
            >
              {{
                requirement.met
                  ? t('components.buildingDetail.requirementMet')
                  : t('components.buildingDetail.levelShort', { level: requirement.current_level })
              }}
            </span>
          </li>
        </ul>
      </div>

      <div v-if="status.unlocks.length" class="space-y-2">
        <p class="text-[11px] uppercase tracking-wide text-text-secondary/70">
          {{ t('components.buildingDetail.unlocksHeading') }}
        </p>
        <ul class="grid gap-1 text-sm text-text-secondary">
          <li v-for="unlock in status.unlocks" :key="unlock" class="flex items-start gap-2">
            <span class="text-primary">➤</span>
            <span>{{ unlock }}</span>
          </li>
        </ul>
      </div>

      <div class="space-y-2">
        <p class="text-[11px] uppercase tracking-wide text-text-secondary/70">
          {{ t('components.buildingDetail.detailsHeading') }}
        </p>
        <div class="flex flex-wrap items-center gap-3 text-sm text-text-secondary">
          <span v-if="nextCostLabel" class="rounded-md bg-secondary-800/70 px-3 py-1 border border-secondary-700/40">
            {{ nextCostLabel }}
          </span>
          <span v-if="upgradeDurationLabel" class="rounded-md bg-secondary-800/70 px-3 py-1 border border-secondary-700/40">
            {{ t('components.buildingDetail.duration', { duration: upgradeDurationLabel }) }}
          </span>
          <span v-if="status.is_upgrading" class="rounded-md bg-emerald-500/10 px-3 py-1 border border-emerald-500/30 text-emerald-200">
            {{ t('components.buildingDetail.readyIn', { duration: remainingLabel }) }}
          </span>
        </div>

        <div v-if="status.is_upgrading" class="h-2 rounded-full bg-secondary-800/70 overflow-hidden">
          <div
            class="h-full rounded-full bg-emerald-400 transition-[width] duration-500"
            :style="{ width: `${progress}%` }"
          ></div>
        </div>
      </div>

      <p v-if="!status.next_cost || isMaxLevel" class="text-sm text-text-secondary">
        {{ t('components.buildingDetail.messages.maxLevel') }}
      </p>
      <p v-else-if="isLocked" class="text-sm text-red-300">
        {{ t('components.buildingDetail.messages.requirementsMissing') }}
      </p>
      <p v-else-if="!canAfford" class="text-sm text-amber-300">
        {{ t('components.buildingDetail.messages.notEnoughResources') }}
      </p>

      <button
        type="button"
        class="w-full rounded-xl border-2 border-primary/60 bg-primary/80 py-3 text-base font-semibold text-white shadow-lg shadow-primary/30 transition hover:bg-primary"
        :disabled="isUpgradeDisabled"
        :class="{
          'opacity-50 cursor-not-allowed hover:bg-primary/80': isUpgradeDisabled
        }"
        @click="emitUpgrade"
      >
        {{ buttonLabel }}
      </button>
    </section>
  </article>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import type { BuildingStatus } from '../../types/buildings';
import { useI18n } from '../../i18n';

const numberFormatter = new Intl.NumberFormat();

const props = defineProps<{
  status: BuildingStatus;
  now: number;
  canAfford: boolean;
}>();

const emit = defineEmits<{
  (e: 'upgrade', building: string): void;
}>();

const { t } = useI18n();

const formatNumber = (value: number) =>
  numberFormatter.format(Math.max(0, Math.floor(value || 0)));

const translateCategory = (category: string) => {
  const key = `build.categories.${category}`;
  const translated = t(key, { category });
  return translated === key ? category : translated;
};

const formatDuration = (seconds: number | null | undefined) => {
  if (!seconds || seconds <= 0) {
    return t('common.duration.instant');
  }
  const mins = Math.floor(seconds / 60);
  const hrs = Math.floor(mins / 60);
  const remMins = mins % 60;
  const remSecs = seconds % 60;

  if (hrs > 0) {
    return t('common.duration.hoursMinutes', { hours: hrs, minutes: remMins });
  }
  if (mins > 0) {
    return t('common.duration.minutesSeconds', { minutes: mins, seconds: remSecs });
  }
  return t('common.duration.seconds', { seconds: remSecs });
};

const remainingSeconds = computed(() => {
  if (!props.status.upgrade_end_time) {
    return null;
  }
  const parsed = new Date(props.status.upgrade_end_time).getTime();
  if (Number.isNaN(parsed)) {
    return null;
  }
  return Math.max(0, Math.ceil((parsed - props.now) / 1000));
});

const progress = computed(() => {
  if (!props.status.is_upgrading || !props.status.upgrade_duration) {
    return 0;
  }
  const total = props.status.upgrade_duration;
  const remaining = remainingSeconds.value ?? total;
  const completed = Math.max(0, total - remaining);
  return Math.min(100, Math.round((completed / total) * 100));
});

const nextCostLabel = computed(() => {
  if (!props.status.next_cost) {
    return null;
  }
  const { wood, clay, iron } = props.status.next_cost;
  return t('components.buildingDetail.cost', {
    wood: formatNumber(wood),
    woodLabel: t('build.resources.wood.title'),
    clay: formatNumber(clay),
    clayLabel: t('build.resources.clay.title'),
    iron: formatNumber(iron),
    ironLabel: t('build.resources.iron.title'),
  });
});

const upgradeDurationLabel = computed(() =>
  formatDuration(props.status.upgrade_duration ?? null)
);

const remainingLabel = computed(() => {
  if (!props.status.is_upgrading) {
    return t('components.buildingDetail.queueing');
  }
  const value = remainingSeconds.value;
  return value === null ? t('common.duration.soon') : formatDuration(value);
});

const isLocked = computed(() => props.status.requirements.some((req) => !req.met));
const isMaxLevel = computed(() => props.status.level >= props.status.max_level);

const isUpgradeDisabled = computed(() =>
  !props.status.next_cost ||
  props.status.is_upgrading ||
  isMaxLevel.value ||
  isLocked.value ||
  !props.status.available ||
  !props.canAfford
);

const buttonLabel = computed(() => {
  if (!props.status.next_cost || isMaxLevel.value) {
    return t('components.buildingDetail.button.maxLevel');
  }
  if (props.status.is_upgrading) {
    return t('components.buildingDetail.button.inProgress');
  }
  if (isLocked.value) {
    return t('components.buildingDetail.button.requirementsMissing');
  }
  if (!props.canAfford) {
    return t('components.buildingDetail.button.notEnoughResources');
  }
  return t('components.buildingDetail.button.upgrade', {
    level: props.status.level + 1,
  });
});

function emitUpgrade() {
  if (isUpgradeDisabled.value) {
    return;
  }
  emit('upgrade', props.status.internal_name);
}
</script>
