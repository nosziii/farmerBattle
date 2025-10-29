<script setup lang="ts">
import type { PropType } from 'vue';
import { useI18n } from '../../i18n';

interface BarbarianTarget {
  id: number;
  name: string;
  level: number;
  warriors: number;
  x: number;
  y: number;
  distance: number;
}

const props = defineProps({
  target: {
    type: Object as PropType<BarbarianTarget>,
    required: true,
  },
});

defineEmits<{ (e: 'plan-expedition', targetId: number): void }>();

const { t } = useI18n();
</script>

<template>
  <article
    class="rounded-xl border border-secondary-700/40 bg-secondary-900/60 px-4 py-3 space-y-1"
  >
    <header class="flex items-center justify-between">
      <h3 class="text-base font-semibold text-text-primary">{{ target.name }}</h3>
      <span class="text-xs text-text-secondary/70">{{ t('expeditions.levelShort', { level: target.level }) }}</span>
    </header>
    <p class="text-xs text-text-secondary">{{ t('expeditions.warriors', { warriors: target.warriors }) }}</p>
    <p class="text-xs text-text-secondary">{{ t('expeditions.distanceTiles', { distance: target.distance }) }}</p>
    <button
      type="button"
      class="mt-2 w-full rounded-lg border border-primary/40 bg-primary/20 px-3 py-2 text-xs font-semibold text-primary-100 hover:bg-primary/30"
      @click="$emit('plan-expedition', target.id)"
    >
      {{ t('expeditions.planExpedition') }}
    </button>
  </article>
</template>
