<script setup lang="ts">
import { computed } from "vue";
import type { MapTile } from "../types/map";

const props = defineProps<{
  tile: MapTile;
  selected?: boolean;
  tileSize?: number;
}>();

const emit = defineEmits<{
  (e: "select", tile: MapTile): void;
}>();

const baseTileSize = computed(() => props.tileSize ?? 64);

const variantClasses = computed(() => {
  if (props.tile.type === "player" && props.tile.village) {
    return "border-emerald-400/50 hover:border-emerald-300/60 focus-visible:outline-emerald-200";
  }
  if (props.tile.type === "barbarian" && props.tile.barbarian) {
    return "border-amber-400/50 hover:border-amber-300/60 focus-visible:outline-amber-200";
  }
  return "border-secondary-600/40 hover:border-secondary-400/60 focus-visible:outline-slate-200";
});

const selectionClasses = computed(() =>
  props.selected
    ? "border-white/70 shadow-[0_0_0_1px_rgba(255,255,255,0.65),0_12px_28px_-18px_rgba(226,232,240,0.75)]"
    : "shadow-[0_12px_28px_-24px_rgba(15,23,42,0.65)]"
);

const tileBackground = computed(() => {
  if (props.tile.type === "player") {
    return `linear-gradient(135deg, rgba(34,197,94,0.2) 0%, rgba(13,148,136,0.08) 45%, rgba(15,23,42,0.85) 100%)`;
  }
  if (props.tile.type === "barbarian") {
    return `linear-gradient(135deg, rgba(250,204,21,0.18) 0%, rgba(202,138,4,0.08) 45%, rgba(15,23,42,0.85) 100%)`;
  }
  return `linear-gradient(135deg, rgba(148,163,184,0.16) 0%, rgba(71,85,105,0.08) 45%, rgba(15,23,42,0.8) 100%)`;
});

const tileShadow = computed(() => {
  if (props.tile.type === "player") {
    return "inset 0 1px 0 rgba(255,255,255,0.05), 0 16px 32px -28px rgba(16,185,129,0.75)";
  }
  if (props.tile.type === "barbarian") {
    return "inset 0 1px 0 rgba(255,255,255,0.05), 0 16px 32px -28px rgba(251,191,36,0.7)";
  }
  return "inset 0 1px 0 rgba(255,255,255,0.04), 0 16px 32px -28px rgba(148,163,184,0.6)";
});

const rootStyle = computed(() => {
  const size = baseTileSize.value;
  const background = tileBackground.value;
  const shadow = tileShadow.value;
  return {
    padding: `${Math.max(6, Math.round(size * 0.16))}px`,
    borderRadius: `${Math.max(6, Math.round(size * 0.22))}px`,
    fontSize: `${Math.max(11, Math.round(size * 0.22))}px`,
    background,
    boxShadow: shadow,
  };
});

const coordinateStyle = computed(() => {
  const size = baseTileSize.value;
  return {
    fontSize: `${Math.max(9, Math.round(size * 0.18))}px`,
  };
});

const contentStyle = computed(() => {
  const size = baseTileSize.value;
  const horizontalPadding = Math.max(4, Math.round(size * 0.14));
  const gap = Math.max(4, Math.round(size * 0.12));
  return {
    gap: `${gap}px`,
    paddingLeft: `${horizontalPadding}px`,
    paddingRight: `${horizontalPadding}px`,
  };
});

const badgeStyle = computed(() => {
  const size = baseTileSize.value;
  const verticalPadding = Math.max(2, Math.round(size * 0.08));
  const horizontalPadding = Math.max(4, Math.round(size * 0.14));
  return {
    fontSize: `${Math.max(8, Math.round(size * 0.18))}px`,
    padding: `${verticalPadding}px ${horizontalPadding}px`,
    borderRadius: `${Math.max(4, Math.round(size * 0.16))}px`,
  };
});

const occupantBadge = computed(() => {
  if (props.tile.type === "player") {
    return "🏰";
  }
  if (props.tile.type === "barbarian") {
    return "⚔️";
  }
  return "·";
});

const occupantClasses = computed(() => {
  if (props.tile.type === "player") {
    return "bg-emerald-500/30 border border-emerald-400/40 text-emerald-100";
  }
  if (props.tile.type === "barbarian") {
    return "bg-amber-500/20 border border-amber-300/40 text-amber-100";
  }
  return "bg-secondary-800/60 border border-secondary-700/40 text-text-secondary/80";
});

const badgeText = computed(() => {
  if (props.tile.type === "player" && props.tile.village) {
    return props.tile.village.owner.username;
  }
  if (props.tile.type === "barbarian" && props.tile.barbarian) {
    return `Lv.${props.tile.barbarian.level}`;
  }
  return "--";
});

const tooltip = computed(() => {
  if (props.tile.type === "player" && props.tile.village) {
    return `${props.tile.village.name} (${props.tile.village.owner.username})`;
  }
  if (props.tile.type === "barbarian" && props.tile.barbarian) {
    return `${props.tile.barbarian.name} - Level ${props.tile.barbarian.level} - ${props.tile.barbarian.warriors} warriors`;
  }
  return "Empty tile";
});

const handleSelect = () => {
  emit("select", props.tile);
};
</script>

<template>
  <button
    type="button"
    class="relative w-full h-full border transition transform hover:scale-[1.03] focus-visible:outline focus-visible:outline-2 focus-visible:outline-emerald-300 flex flex-col shadow-[inset_0_1px_0_rgba(255,255,255,0.04)]"
    :class="[variantClasses, selectionClasses]"
    :title="tooltip"
    @click="handleSelect"
    :style="rootStyle"
  >
    <span
      class="absolute font-mono text-text-secondary"
      :style="[
        { top: '6px', left: '8px' },
        { fontSize: coordinateStyle.fontSize },
      ]"
    >
      {{ tile.x }}|{{ tile.y }}
    </span>
    <span
      class="absolute top-2 right-2 inline-flex h-6 w-6 items-center justify-center rounded-md text-sm backdrop-blur-sm"
      :class="occupantClasses"
    >
      {{ occupantBadge }}
    </span>

    <div
      class="flex flex-1 flex-col items-center justify-center text-center"
      :style="contentStyle"
    >
      <template v-if="tile.type === 'player' && tile.village">
        <p class="font-semibold text-text-primary truncate w-full">
          {{ tile.village.name }}
        </p>
        <p class="text-text-secondary truncate w-full">
          {{ tile.village.owner.username }}
        </p>
        <p class="text-text-secondary text-[0.8em]">
          Score {{ tile.village.score }}
        </p>
      </template>
      <template v-else-if="tile.type === 'barbarian' && tile.barbarian">
        <p class="font-semibold text-amber-100 truncate w-full">
          {{ tile.barbarian.name }}
        </p>
        <p class="text-text-secondary">Level {{ tile.barbarian.level }}</p>
        <p class="text-text-secondary text-[0.8em]">
          {{ tile.barbarian.warriors }} warriors
        </p>
      </template>
      <template v-else>
        <p class="text-text-secondary italic"></p>
      </template>
    </div>

    <span
      class="absolute bottom-1 right-1 font-semibold uppercase tracking-wide text-text-primary bg-secondary-900/80"
      :style="badgeStyle"
    >
      {{ badgeText }}
    </span>
  </button>
</template>
