<script setup lang="ts">
const props = defineProps<{
  icon: string;
  label: string;
  value: number;
}>();
</script>

<template>
  <div
    class="group flex items-center gap-2 rounded-xl border border-secondary/40 bg-secondary-800/40 px-3 py-2 hover:border-primary-700/60 hover:bg-secondary-800/60 transition min-w-0"
  >
    <span class="text-lg shrink-0">{{ props.icon }}</span>
    <div class="min-w-0 overflow-hidden">
      <div class="text-xs text-text-secondary">{{ props.label }}</div>
      <div class="text-sm font-semibold tracking-wide truncate">
        {{ props.value.toLocaleString() }}
      </div>
    </div>
  </div>
</template>
