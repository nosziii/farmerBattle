<script setup lang="ts">
import { RouterLink } from "vue-router";

const props = defineProps<{
  icon: string;
  label: string;
  k: string;
  to: string;
  compact?: boolean;
}>();
</script>

<template>
  <RouterLink
    :to="props.to"
    class="relative inline-flex items-center gap-2 rounded-xl border px-3 py-2 transition group border-primary-800/50 bg-primary-900/20 hover:bg-primary-800/30 active:scale-[0.98] w-full min-w-0 overflow-hidden"
    :title="`${props.label} (hotkey ${props.k})`"
  >
    <span class="text-lg shrink-0">{{ props.icon }}</span>
    <span
      v-if="!props.compact"
      class="text-sm font-semibold truncate min-w-0"
      >{{ props.label }}</span
    >
    <kbd v-if="!props.compact" class="kbd-badge shrink-0">{{ props.k }}</kbd>
    <span
      class="absolute inset-0 rounded-xl ring-0 group-hover:ring-2 ring-primary-700/40 pointer-events-none"
    ></span>
  </RouterLink>
</template>
