<script setup lang="ts">
const props = defineProps<{
  icon: string;
  title: string;
  compact?: boolean;
}>();
</script>

<template>
  <div>
    <div
      v-if="!props.compact"
      class="flex items-center gap-2 px-2 mb-2 text-text-secondary uppercase tracking-wider text-[11px]"
    >
      <span>{{ props.icon }}</span>
      <span>{{ props.title }}</span>
      <div class="flex-1 h-px bg-secondary/40 ml-2"></div>
    </div>
    <div class="grid gap-1">
      <slot></slot>
    </div>
  </div>
</template>
