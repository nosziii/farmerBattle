<script setup lang="ts">
import { computed } from 'vue';
import type { MapTile } from '../types/map';

const props = defineProps<{
  tile: MapTile;
  selected?: boolean;
}>();

const emit = defineEmits<{
  (e: 'select', tile: MapTile): void;
}>();

const variantClasses = computed(() => {
  if (props.tile.type === 'player' && props.tile.village) {
    return 'border-emerald-500/60 bg-emerald-500/10 hover:bg-emerald-500/20';
  }
  if (props.tile.type === 'barbarian' && props.tile.barbarian) {
    return 'border-amber-500/60 bg-amber-500/10 hover:bg-amber-500/20';
  }
  return 'border-secondary-700/40 bg-secondary-900/40 hover:bg-secondary-800/50';
});

const selectionClasses = computed(() =>
  props.selected ? 'shadow-lg shadow-white/20 border-white/70' : ''
);

const badgeText = computed(() => {
  if (props.tile.type === 'player' && props.tile.village) {
    return props.tile.village.owner.username;
  }
  if (props.tile.type === 'barbarian' && props.tile.barbarian) {
    return `Lv.${props.tile.barbarian.level}`;
  }
  return '--';
});

const tooltip = computed(() => {
  if (props.tile.type === 'player' && props.tile.village) {
    return `${props.tile.village.name} (${props.tile.village.owner.username})`;
  }
  if (props.tile.type === 'barbarian' && props.tile.barbarian) {
    return `${props.tile.barbarian.name} - Level ${props.tile.barbarian.level} - ${props.tile.barbarian.warriors} warriors`;
  }
  return 'Empty tile';
});

const handleSelect = () => {
  emit('select', props.tile);
};
</script>

<template>
  <button
    type="button"
    class="relative aspect-square rounded-md border transition transform hover:scale-[1.03] focus-visible:outline focus-visible:outline-2 focus-visible:outline-emerald-300"
    :class="[variantClasses, selectionClasses]"
    :title="tooltip"
    @click="handleSelect"
  >
    <span class="absolute top-1 left-1 text-[0.65rem] font-mono text-text-secondary">
      {{ tile.x }}|{{ tile.y }}
    </span>

    <div class="flex h-full flex-col items-center justify-center gap-1 px-1 text-center">
      <template v-if="tile.type === 'player' && tile.village">
        <p class="text-sm font-semibold text-text-primary truncate w-full">{{ tile.village.name }}</p>
        <p class="text-xs text-text-secondary truncate w-full">{{ tile.village.owner.username }}</p>
        <p class="text-[0.65rem] text-text-secondary">Score {{ tile.village.score }}</p>
      </template>
      <template v-else-if="tile.type === 'barbarian' && tile.barbarian">
        <p class="text-sm font-semibold text-amber-100 truncate w-full">
          {{ tile.barbarian.name }}
        </p>
        <p class="text-xs text-text-secondary">Level {{ tile.barbarian.level }}</p>
        <p class="text-[0.65rem] text-text-secondary">{{ tile.barbarian.warriors }} warriors</p>
      </template>
      <template v-else>
        <p class="text-xs text-text-secondary italic">Empty</p>
      </template>
    </div>

    <span
      class="absolute bottom-1 right-1 rounded-sm px-1 py-0.5 text-[0.6rem] font-semibold uppercase tracking-wide text-text-primary bg-secondary-900/80"
    >
      {{ badgeText }}
    </span>
  </button>
</template>
