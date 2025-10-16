<template>
  <div class="group relative overflow-hidden rounded-2xl bg-gradient-to-br from-dark-800/90 via-dark-700/80 to-primary-900/40 p-6 border-2 border-primary-600/30 shadow-2xl hover:shadow-primary-500/20 hover:border-primary-500/50 transition-all duration-500 hover:scale-[1.02]">
    <div class="absolute top-0 right-0 w-32 h-32 bg-gradient-to-br from-primary-500/20 to-transparent rounded-full blur-2xl group-hover:scale-150 transition-transform duration-700"></div>

    <div class="relative z-10">
      <div class="flex items-start justify-between mb-4">
        <div class="flex items-center gap-3">
          <div class="w-14 h-14 rounded-xl bg-gradient-to-br from-primary-500 to-secondary-600 flex items-center justify-center shadow-lg shadow-primary-500/30 group-hover:shadow-primary-500/50 transition-all">
            <span class="text-3xl">{{ icon }}</span>
          </div>
          <div>
            <h3 class="text-xl font-bold text-white mb-1">{{ title }}</h3>
            <p class="text-sm text-primary-300 font-semibold">{{ category }}</p>
          </div>
        </div>
        <div class="px-3 py-1 rounded-full bg-yellow-500/20 border border-yellow-400/40">
          <span class="text-yellow-300 font-bold text-sm">+{{ reward }} XP</span>
        </div>
      </div>

      <p class="text-gray-300 mb-4 leading-relaxed">{{ description }}</p>

      <div class="space-y-2 mb-5">
        <div class="flex justify-between text-sm mb-1">
          <span class="text-gray-400">Progress</span>
          <span class="text-white font-semibold">{{ current }}/{{ total }}</span>
        </div>
        <div class="relative w-full h-3 bg-dark-900/60 rounded-full overflow-hidden border border-primary-800/30">
          <div
            class="absolute top-0 left-0 h-full bg-gradient-to-r from-primary-500 via-secondary-500 to-primary-600 rounded-full transition-all duration-1000 shadow-lg shadow-primary-500/50"
            :style="{ width: `${(current / total) * 100}%` }"
          >
            <div class="absolute inset-0 bg-white/20 animate-pulse"></div>
          </div>
        </div>
      </div>

      <div class="flex gap-3">
        <button
          v-if="current < total"
          class="flex-1 py-3 px-4 rounded-xl bg-gradient-to-r from-primary-600 via-primary-500 to-secondary-600 text-white font-bold shadow-lg shadow-primary-600/30 hover:shadow-primary-500/50 hover:scale-105 transition-all duration-300 border border-primary-400/30"
        >
          Continue Quest
        </button>
        <button
          v-else
          class="flex-1 py-3 px-4 rounded-xl bg-gradient-to-r from-green-600 via-emerald-500 to-green-600 text-white font-bold shadow-lg shadow-green-600/30 hover:shadow-green-500/50 hover:scale-105 transition-all duration-300 border border-green-400/30 animate-pulse"
        >
          Claim Reward
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
interface Props {
  title: string;
  description: string;
  category: string;
  icon: string;
  reward: number;
  current: number;
  total: number;
}

defineProps<Props>();
</script>
