<template>
  <div class="group flex items-center gap-4 p-5 rounded-xl bg-gradient-to-r from-dark-800/80 via-dark-700/60 to-dark-800/80 border border-primary-700/20 hover:border-primary-500/50 shadow-lg hover:shadow-primary-500/10 transition-all duration-300 hover:scale-[1.02]">
    <div :class="`relative flex items-center justify-center w-12 h-12 rounded-full font-bold text-lg ${rankColor} shadow-lg`">
      <span v-if="rank <= 3" class="text-2xl">{{ rankIcon }}</span>
      <span v-else class="text-white">{{ rank }}</span>
      <div :class="`absolute inset-0 rounded-full ${rankGlow} blur-xl opacity-50 group-hover:opacity-75 transition-opacity`"></div>
    </div>

    <div class="flex items-center gap-3 flex-1">
      <div class="w-14 h-14 rounded-xl bg-gradient-to-br from-primary-600 to-secondary-600 flex items-center justify-center shadow-md">
        <span class="text-2xl">{{ avatar }}</span>
      </div>
      <div class="flex-1">
        <h4 class="text-lg font-bold text-white mb-1">{{ playerName }}</h4>
        <p class="text-sm text-gray-400">Level {{ level }} • {{ clanName }}</p>
      </div>
    </div>

    <div class="text-right">
      <p class="text-2xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-yellow-400 to-yellow-600">
        {{ trophies.toLocaleString() }}
      </p>
      <p class="text-xs text-gray-400">Trophies</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';

interface Props {
  rank: number;
  playerName: string;
  level: number;
  clanName: string;
  trophies: number;
  avatar: string;
}

const props = defineProps<Props>();

const rankIcon = computed(() => {
  if (props.rank === 1) return '👑';
  if (props.rank === 2) return '🥈';
  if (props.rank === 3) return '🥉';
  return '';
});

const rankColor = computed(() => {
  if (props.rank === 1) return 'bg-gradient-to-br from-yellow-400 to-yellow-600';
  if (props.rank === 2) return 'bg-gradient-to-br from-gray-300 to-gray-500';
  if (props.rank === 3) return 'bg-gradient-to-br from-amber-600 to-amber-800';
  return 'bg-gradient-to-br from-primary-700 to-primary-900';
});

const rankGlow = computed(() => {
  if (props.rank === 1) return 'bg-yellow-400';
  if (props.rank === 2) return 'bg-gray-400';
  if (props.rank === 3) return 'bg-amber-600';
  return 'bg-primary-600';
});
</script>
