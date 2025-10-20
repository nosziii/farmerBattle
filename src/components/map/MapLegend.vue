<script setup lang="ts">
const legendItems = [
  {
    label: 'Player village',
    description: 'Allied stronghold. Grants access to production stats and owner details.',
    accentClass: 'from-emerald-500/80 to-emerald-400/70 text-emerald-50',
    bulletClass: 'bg-emerald-400/80 shadow-[0_0_8px_rgba(16,185,129,0.6)]',
  },
  {
    label: 'Barbarian village',
    description: 'Hostile settlement. Scout their strength and plan expeditions wisely.',
    accentClass: 'from-amber-500/80 to-amber-400/70 text-amber-50',
    bulletClass: 'bg-amber-400/80 shadow-[0_0_8px_rgba(251,191,36,0.6)]',
  },
  {
    label: 'Empty tile',
    description: 'Unclaimed farmland. Keep an eye out for future expansion opportunities.',
    accentClass: 'from-secondary-700/70 to-secondary-600/60 text-text-secondary',
    bulletClass: 'bg-secondary-600/70 shadow-[0_0_8px_rgba(148,163,184,0.4)]',
  },
];
</script>

<template>
  <div
    class="grid w-full gap-3 rounded-xl border border-secondary-700/40 bg-secondary-900/60 p-4 text-xs text-text-secondary shadow-lg shadow-black/30 md:grid-cols-3"
  >
    <div
      v-for="item in legendItems"
      :key="item.label"
      class="flex items-center gap-3 rounded-lg border border-secondary-700/40 bg-secondary-800/50 px-3 py-2 transition hover:-translate-y-0.5 hover:border-secondary-500/50 hover:bg-secondary-700/50"
    >
      <span class="h-4 w-4 shrink-0 rounded-md" :class="item.bulletClass"></span>
      <div class="flex flex-col">
        <span class="font-semibold uppercase tracking-wide" :class="item.accentClass">
          {{ item.label }}
        </span>
        <span class="text-[0.65rem] text-text-secondary/70">
          {{ item.description }}
        </span>
      </div>
    </div>
  </div>
</template>
