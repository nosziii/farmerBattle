<template>
  <div class="group relative overflow-hidden rounded-2xl bg-surface p-6 border-2 border-primary-600/30 shadow-lg hover:shadow-primary-500/10 hover:border-primary-500/50 transition-all duration-300 hover:scale-105">
    <div class="absolute top-0 right-0 w-32 h-32 bg-primary rounded-full blur-3xl opacity-10 group-hover:opacity-20 group-hover:scale-150 transition-all duration-700"></div>

    <div class="relative z-10">
      <div class="flex items-center justify-between mb-4">
        <div class="flex items-center gap-3">
          <div class="w-14 h-14 rounded-xl bg-secondary-800 flex items-center justify-center shadow-lg shadow-primary-500/10">
            <span class="text-3xl">{{ icon }}</span>
          </div>
          <div>
            <h3 class="text-xl font-bold text-text-primary">{{ title }}</h3>
            <p class="text-sm text-text-secondary">{{ subtitle }}</p>
          </div>
        </div>
      </div>
      <div class="space-y-3">
        <div class="flex justify-between items-end">
          <span class="text-4xl font-bold text-text-primary drop-shadow-lg">{{ amount.toLocaleString() }}</span>
          <span :class="`text-sm font-bold px-2 py-1 rounded-lg ${production >= 0 ? 'bg-green-500/20 text-green-300 border border-green-400/40' : 'bg-red-500/20 text-red-300 border border-red-400/40'}`">
            {{ production >= 0 ? '+' : '' }}{{ production }}{{ t('components.resourceCard.perHour') }}
          </span>
        </div>
        <div class="relative w-full bg-secondary-800 rounded-full h-3 overflow-hidden border border-secondary-700">
          <div
            class="h-full bg-primary transition-all duration-1000 shadow-lg"
            :style="{ width: `${percentage}%` }"
          >
            <div class="absolute inset-0 bg-white/20"></div>
          </div>
        </div>
        <p class="text-sm text-text-secondary font-medium">
          {{ t('components.resourceCard.max', { value: capacity.toLocaleString() }) }}
        </p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useI18n } from '../i18n';

interface Props {
  title: string;
  subtitle: string;
  icon: string;
  amount: number;
  capacity: number;
  production: number;
}

const props = defineProps<Props>();
const { t } = useI18n();

const percentage = computed(() => {
  const capacity = props.capacity && props.capacity > 0 ? props.capacity : 1;
  return Math.min((props.amount / capacity) * 100, 100);
});
</script>
