<script setup lang="ts">
import { computed } from "vue";
import { useRoute, RouterLink } from "vue-router";

const props = defineProps<{
  to: string;
  icon: string;
  label: string;
  badge?: string;
}>();

const route = useRoute();
const isActive = computed(
  () => route.path === props.to || route.path.startsWith(props.to + "/")
);
</script>

<template>
  <RouterLink
    :to="props.to"
    class="group flex items-center gap-3 px-3 py-2 rounded-lg transition relative hover:bg-secondary-800/70 border border-transparent min-w-0"
    :class="
      isActive
        ? 'bg-secondary-800/70 border-primary-700/40 shadow-neon-soft before-active'
        : 'before-hover'
    "
    :title="props.label"
  >
    <span class="text-xl shrink-0">{{ props.icon }}</span>
    <span class="text-sm font-medium truncate min-w-0">{{ props.label }}</span>
    <span
      v-if="props.badge"
      class="ml-auto text-[10px] px-1.5 py-0.5 rounded-md bg-primary-700/70 border border-primary-600/70 shrink-0"
      >{{ props.badge }}</span
    >
  </RouterLink>
</template>
