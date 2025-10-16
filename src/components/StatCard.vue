<template>
  <div class="group relative overflow-hidden rounded-2xl bg-gradient-to-br from-dark-800/90 to-dark-900/80 p-6 border-2 border-primary-600/20 shadow-2xl hover:shadow-primary-500/20 hover:border-primary-500/40 transition-all duration-500 hover:scale-105">
    <div :class="`absolute top-0 right-0 w-32 h-32 ${gradientColor} rounded-full blur-3xl opacity-20 group-hover:opacity-40 group-hover:scale-150 transition-all duration-700`"></div>

    <div class="relative z-10">
      <div class="flex items-center justify-between mb-4">
        <div :class="`w-14 h-14 rounded-xl ${iconBg} flex items-center justify-center shadow-lg ${shadowColor}`">
          <span class="text-3xl">{{ icon }}</span>
        </div>
        <div :class="`px-3 py-1 rounded-full ${trendBg} border ${trendBorder}`">
          <span :class="`text-sm font-bold ${trendText}`">
            {{ trend > 0 ? '↑' : '↓' }} {{ Math.abs(trend) }}%
          </span>
        </div>
      </div>

      <h3 class="text-gray-400 text-sm font-medium mb-2">{{ label }}</h3>
      <p class="text-4xl font-bold text-white mb-1">{{ value }}</p>
      <p class="text-sm text-gray-500">{{ subtitle }}</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';

interface Props {
  icon: string;
  label: string;
  value: string | number;
  subtitle: string;
  trend: number;
  color: 'blue' | 'purple' | 'green' | 'yellow';
}

const props = defineProps<Props>();

const gradientColor = computed(() => {
  const colors = {
    blue: 'bg-gradient-to-br from-blue-500 to-cyan-500',
    purple: 'bg-gradient-to-br from-purple-500 to-pink-500',
    green: 'bg-gradient-to-br from-green-500 to-emerald-500',
    yellow: 'bg-gradient-to-br from-yellow-500 to-orange-500',
  };
  return colors[props.color];
});

const iconBg = computed(() => {
  const colors = {
    blue: 'bg-gradient-to-br from-blue-600 to-cyan-600',
    purple: 'bg-gradient-to-br from-purple-600 to-pink-600',
    green: 'bg-gradient-to-br from-green-600 to-emerald-600',
    yellow: 'bg-gradient-to-br from-yellow-600 to-orange-600',
  };
  return colors[props.color];
});

const shadowColor = computed(() => {
  const colors = {
    blue: 'shadow-blue-500/30',
    purple: 'shadow-purple-500/30',
    green: 'shadow-green-500/30',
    yellow: 'shadow-yellow-500/30',
  };
  return colors[props.color];
});

const trendBg = computed(() => props.trend > 0 ? 'bg-green-500/10' : 'bg-red-500/10');
const trendBorder = computed(() => props.trend > 0 ? 'border-green-400/30' : 'border-red-400/30');
const trendText = computed(() => props.trend > 0 ? 'text-green-400' : 'text-red-400');
</script>
