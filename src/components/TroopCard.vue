<template>
  <div class="group relative overflow-hidden rounded-2xl bg-gradient-to-br from-dark-800/90 to-dark-900/80 p-6 border-2 border-primary-600/30 shadow-2xl hover:shadow-primary-500/20 hover:border-primary-500/50 transition-all duration-500 hover:scale-105">
    <div :class="`absolute -top-10 -right-10 w-40 h-40 ${bgColor} opacity-20 rounded-full blur-3xl group-hover:scale-150 transition-transform duration-700`"></div>

    <div class="relative z-10 flex items-start gap-5">
      <div :class="`w-20 h-20 rounded-2xl ${bgColor} flex items-center justify-center flex-shrink-0 shadow-xl border-2 border-white/10`">
        <span class="text-4xl drop-shadow-lg">{{ icon }}</span>
      </div>
      <div class="flex-1">
        <h3 class="text-2xl font-bold text-white mb-2">{{ name }}</h3>
        <div class="flex gap-3 mb-4">
          <div class="px-3 py-1 rounded-lg bg-red-500/20 border border-red-400/40">
            <span class="text-xs text-gray-400">ATK</span>
            <p class="text-sm font-bold text-red-300">{{ attack }}</p>
          </div>
          <div class="px-3 py-1 rounded-lg bg-blue-500/20 border border-blue-400/40">
            <span class="text-xs text-gray-400">DEF</span>
            <p class="text-sm font-bold text-blue-300">{{ defense }}</p>
          </div>
          <div class="px-3 py-1 rounded-lg bg-green-500/20 border border-green-400/40">
            <span class="text-xs text-gray-400">HP</span>
            <p class="text-sm font-bold text-green-300">{{ health }}</p>
          </div>
        </div>
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm text-gray-400 mb-1">Available</p>
            <p class="text-3xl font-bold text-white">{{ count }}</p>
          </div>
          <button class="px-6 py-3 bg-gradient-to-r from-primary-600 via-primary-500 to-secondary-600 text-white rounded-xl font-bold shadow-lg shadow-primary-600/30 hover:shadow-primary-500/50 hover:scale-105 transition-all border-2 border-primary-400/30">
            Train More
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
interface Props {
  name: string;
  icon: string;
  attack: number;
  defense: number;
  health: number;
  count: number;
  bgColor: string;
}

defineProps<Props>();
</script>
