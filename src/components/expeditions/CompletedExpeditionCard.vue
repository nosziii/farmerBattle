<script setup lang="ts">
import type { PropType } from 'vue';
import { useI18n } from '../../i18n';
import type { ExpeditionSummary } from '../../types/expeditions';

const props = defineProps({
  expedition: {
    type: Object as PropType<ExpeditionSummary>,
    required: true,
  },
});

defineEmits<{ (e: 'view-details', expedition: ExpeditionSummary): void }>();

const { t } = useI18n();

const normaliseIsoTimestamp = (value: string) => {
  return /(Z|z|[+-]\d{2}:?\d{2})$/.test(value) ? value : `${value}Z`;
};

const parseDate = (value: string | null | undefined) => {
  if (!value) return null;
  const date = new Date(normaliseIsoTimestamp(value));
  return Number.isNaN(date.getTime()) ? null : date;
};

const formatTimestamp = (date: Date | null) => {
  if (!date) return '—';
  return date.toLocaleString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
};

const formatResourceValue = (value: number | undefined) => {
  if (!value) return '0';
  return new Intl.NumberFormat().format(Math.floor(value));
};
</script>

<template>
  <article class="rounded-2xl border border-secondary-700/40 bg-secondary-900/60 px-5 py-4 space-y-2">
    <header class="flex items-center justify-between">
      <div>
        <h3 class="text-lg font-semibold text-text-primary">{{ expedition.barbarian_name }}</h3>
        <p class="text-xs text-text-secondary/70">{{ t('expeditions.completedAt', { time: formatTimestamp(parseDate(expedition.completed_at)) }) }}</p>
      </div>
      <span
        class="rounded-full border px-2 py-1 text-[11px] uppercase tracking-wide"
        :class="expedition.success
          ? 'border-emerald-500/40 bg-emerald-500/10 text-emerald-200'
          : 'border-red-500/40 bg-red-500/10 text-red-200'"
      >
        {{ expedition.success ? t('expeditions.success') : t('expeditions.failed') }}
      </span>
    </header>
    <div class="text-xs text-text-secondary">
      <span class="uppercase tracking-wide text-text-secondary/70">{{ t('expeditions.loot') }}</span>
      <p class="text-text-primary">
        Wood {{ formatResourceValue(expedition.loot.wood) }} • Clay {{ formatResourceValue(expedition.loot.clay) }} • Iron {{ formatResourceValue(expedition.loot.iron) }}
      </p>
    </div>
    <div class="text-xs text-text-secondary">
      <span class="uppercase tracking-wide text-text-secondary/70">{{ t('expeditions.battleReport') }}</span>
      <p class="line-clamp-2 text-text-primary/80">{{ expedition.battle_report ?? t('expeditions.noReportAvailable') }}</p>
    </div>
    <button
      type="button"
      class="rounded-lg border border-primary/40 bg-primary/20 px-3 py-1.5 text-xs text-primary-100 hover:bg-primary/30"
      @click="$emit('view-details', expedition)"
    >
      {{ t('expeditions.viewDetails') }}
    </button>
  </article>
</template>
