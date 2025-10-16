<template>
  <div :class="`flex items-center gap-4 p-5 rounded-xl border-2 ${resultBorder} ${resultBg} shadow-lg hover:scale-[1.02] transition-all duration-300`">
    <div :class="`w-16 h-16 rounded-xl ${resultIconBg} flex items-center justify-center shadow-lg`">
      <span class="text-3xl">{{ resultIcon }}</span>
    </div>

    <div class="flex-1">
      <div class="flex items-center gap-2 mb-2">
        <h4 class="text-lg font-bold text-white">vs {{ opponentName }}</h4>
        <span :class="`px-2 py-1 rounded-full text-xs font-bold ${resultBadge}`">
          {{ result.toUpperCase() }}
        </span>
      </div>
      <div class="flex gap-4 text-sm text-gray-400">
        <span>Trophies: {{ result === 'victory' ? '+' : '' }}{{ trophyChange }}</span>
        <span>{{ timeAgo }}</span>
        <span>{{ battleType }}</span>
      </div>
    </div>

    <div class="text-right">
      <p class="text-sm text-gray-400 mb-1">Damage</p>
      <p class="text-2xl font-bold text-white">{{ damagePercent }}%</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';

interface Props {
  result: 'victory' | 'defeat' | 'draw';
  opponentName: string;
  trophyChange: number;
  damagePercent: number;
  timeAgo: string;
  battleType: string;
}

const props = defineProps<Props>();

const resultIcon = computed(() => {
  if (props.result === 'victory') return '🏆';
  if (props.result === 'defeat') return '💀';
  return '🤝';
});

const resultBorder = computed(() => {
  if (props.result === 'victory') return 'border-green-500/50';
  if (props.result === 'defeat') return 'border-red-500/50';
  return 'border-yellow-500/50';
});

const resultBg = computed(() => {
  if (props.result === 'victory') return 'bg-gradient-to-r from-green-900/20 to-dark-800/80';
  if (props.result === 'defeat') return 'bg-gradient-to-r from-red-900/20 to-dark-800/80';
  return 'bg-gradient-to-r from-yellow-900/20 to-dark-800/80';
});

const resultIconBg = computed(() => {
  if (props.result === 'victory') return 'bg-gradient-to-br from-green-600 to-green-800';
  if (props.result === 'defeat') return 'bg-gradient-to-br from-red-600 to-red-800';
  return 'bg-gradient-to-br from-yellow-600 to-yellow-800';
});

const resultBadge = computed(() => {
  if (props.result === 'victory') return 'bg-green-500/20 text-green-300 border border-green-400/40';
  if (props.result === 'defeat') return 'bg-red-500/20 text-red-300 border border-red-400/40';
  return 'bg-yellow-500/20 text-yellow-300 border border-yellow-400/40';
});
</script>
