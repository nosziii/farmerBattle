<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, reactive, ref, watch } from 'vue';
import MapTile from '../MapTile.vue';
import type { MapTile as MapTileSummary } from '../../types/map';

const props = defineProps<{
  tiles: MapTileSummary[];
  width: number;
  height: number;
  tileSize: number;
  gridGap?: number;
  selectedTile?: MapTileSummary | null;
}>();

const emit = defineEmits<{
  (e: 'tile-select', tile: MapTileSummary): void;
  (e: 'request-zoom', delta: number): void;
}>();

const wrapperRef = ref<HTMLElement | null>(null);

const gridGap = computed(() => props.gridGap ?? 4);

const surfaceDimensions = computed(() => {
  const widthPx =
    props.width * props.tileSize + Math.max(props.width - 1, 0) * gridGap.value;
  const heightPx =
    props.height * props.tileSize + Math.max(props.height - 1, 0) * gridGap.value;

  return {
    width: widthPx,
    height: heightPx,
  };
});

const gridTemplateStyle = computed(() => ({
  gridTemplateColumns: `repeat(${props.width}, ${props.tileSize}px)`,
  gridAutoRows: `${props.tileSize}px`,
  gap: `${gridGap.value}px`,
}));

const pan = reactive({ x: 0, y: 0 });

const dragState = ref<{
  pointerId: number;
  startX: number;
  startY: number;
  originX: number;
  originY: number;
  moved: boolean;
  hasCapture: boolean;
} | null>(null);

const suppressClick = ref(false);
const showHint = ref(true);
const pendingPan = reactive({ x: 0, y: 0 });
let panRafHandle = 0;

const surfaceStyle = computed(() => ({
  width: `${surfaceDimensions.value.width}px`,
  height: `${surfaceDimensions.value.height}px`,
  transform: `translate3d(${pan.x}px, ${pan.y}px, 0)`,
  '--tile-size': `${props.tileSize}px`,
}));

const isDragging = computed(() => dragState.value?.moved === true);

const clampPanToBounds = (nextX: number, nextY: number) => {
  const wrapper = wrapperRef.value;
  if (!wrapper) {
    return { x: nextX, y: nextY };
  }

  const containerWidth = wrapper.clientWidth;
  const containerHeight = wrapper.clientHeight;
  const { width: contentWidth, height: contentHeight } = surfaceDimensions.value;

  const getAxisBounds = (containerSize: number, contentSize: number) => {
    if (contentSize <= containerSize) {
      return { min: 0, max: 0 };
    }
    const halfOverflow = (contentSize - containerSize) / 2;
    const slack = Math.min(160, containerSize * 0.3);
    return {
      min: -(halfOverflow + slack),
      max: halfOverflow + slack,
    };
  };

  const horizontal = getAxisBounds(containerWidth, contentWidth);
  const vertical = getAxisBounds(containerHeight, contentHeight);

  return {
    x: Math.min(horizontal.max, Math.max(horizontal.min, nextX)),
    y: Math.min(vertical.max, Math.max(vertical.min, nextY)),
  };
};

const applyPan = (nextX: number, nextY: number) => {
  const bounded = clampPanToBounds(nextX, nextY);
  pendingPan.x = bounded.x;
  pendingPan.y = bounded.y;

  if (!panRafHandle) {
    panRafHandle = window.requestAnimationFrame(() => {
      pan.x = pendingPan.x;
      pan.y = pendingPan.y;
      panRafHandle = 0;
    });
  }
};

const handlePointerDown = (event: PointerEvent) => {
  if (event.button !== 0) {
    return;
  }

  suppressClick.value = false;

  dragState.value = {
    pointerId: event.pointerId,
    startX: event.clientX,
    startY: event.clientY,
    originX: pan.x,
    originY: pan.y,
    moved: false,
    hasCapture: false,
  };
};

const handlePointerMove = (event: PointerEvent) => {
  const state = dragState.value;
  if (!state) {
    return;
  }

  const deltaX = event.clientX - state.startX;
  const deltaY = event.clientY - state.startY;

  if (!state.moved && Math.abs(deltaX) + Math.abs(deltaY) > 6) {
    state.moved = true;
    showHint.value = false;

    if (!state.hasCapture) {
      const interactionLayer = event.currentTarget as HTMLElement | null;
      interactionLayer?.setPointerCapture(event.pointerId);
      state.hasCapture = true;
    }
  }

  if (!state.moved) {
    return;
  }

  event.preventDefault();
  suppressClick.value = true;
  applyPan(state.originX + deltaX, state.originY + deltaY);
};

const finishPointerInteraction = (event: PointerEvent) => {
  const state = dragState.value;
  if (!state) {
    return;
  }

  const target = event.currentTarget as HTMLElement | null;

  if (state.hasCapture && target?.hasPointerCapture(event.pointerId)) {
    target.releasePointerCapture(event.pointerId);
  }

  dragState.value = null;

  if (suppressClick.value) {
    window.setTimeout(() => {
      suppressClick.value = false;
    }, 0);
  }
};

const handlePointerUp = (event: PointerEvent) => {
  finishPointerInteraction(event);
};

const handlePointerCancel = (event: PointerEvent) => {
  finishPointerInteraction(event);
};

const handleWheel = (event: WheelEvent) => {
  event.preventDefault();

  const direction = event.deltaY === 0 ? 0 : event.deltaY > 0 ? -1 : 1;
  if (direction === 0) {
    return;
  }

  showHint.value = false;

  const baseStep = 4;
  const magnitude = Math.max(1, Math.round(Math.abs(event.deltaY) / 40));
  const multiplier = event.ctrlKey ? 2 : 1;
  const delta = direction * baseStep * magnitude * multiplier;

  emit('request-zoom', delta);
};

const handleClickCapture = (event: MouseEvent) => {
  if (!suppressClick.value) {
    return;
  }

  event.stopImmediatePropagation?.();
  event.stopPropagation();
  event.preventDefault();
  suppressClick.value = false;
};

const handleTileSelect = (tile: MapTileSummary) => {
  emit('tile-select', tile);
};

const handleResize = () => {
  applyPan(pan.x, pan.y);
};

watch(
  () => [props.tileSize, props.width, props.height] as const,
  () => {
    nextTick(() => applyPan(pan.x, pan.y));
  }
);

watch(
  () => props.tiles.length,
  () => {
    pan.x = 0;
    pan.y = 0;
    pendingPan.x = 0;
    pendingPan.y = 0;
    nextTick(() => applyPan(pan.x, pan.y));
  }
);

onMounted(() => {
  window.addEventListener('resize', handleResize, { passive: true });
  nextTick(() => applyPan(pan.x, pan.y));
});

onUnmounted(() => {
  window.removeEventListener('resize', handleResize);
  if (panRafHandle) {
    window.cancelAnimationFrame(panRafHandle);
    panRafHandle = 0;
  }
});
</script>

<template>
  <div class="map-viewport" ref="wrapperRef">
    <div class="map-viewport__glow"></div>
    <div
      class="map-viewport__content"
      @wheel.prevent="handleWheel"
      @pointerdown.capture="handlePointerDown"
      @pointermove="handlePointerMove"
      @pointerup="handlePointerUp"
      @pointerleave="handlePointerUp"
      @pointercancel="handlePointerCancel"
      @click.capture="handleClickCapture"
    >
      <div class="map-viewport__surface">
        <div
          class="map-viewport__grid"
          :class="{ 'is-dragging': isDragging }"
          :style="[surfaceStyle, gridTemplateStyle]"
        >
          <MapTile
            v-for="tile in tiles"
            :key="`${tile.x}-${tile.y}`"
            :tile="tile"
            :selected="selectedTile?.x === tile.x && selectedTile?.y === tile.y"
            :tile-size="tileSize"
            @select="handleTileSelect"
          />
        </div>
      </div>
      <transition name="map-hint">
        <div v-if="showHint" class="map-viewport__hint">
          Scroll to zoom · Drag to pan
        </div>
      </transition>
    </div>
  </div>
</template>

<style scoped>
.map-viewport {
  position: relative;
  width: min(100%, 48rem);
  max-width: 48rem;
  height: min(70vh, 42rem);
  max-height: 42rem;
  margin: 0 auto;
  border-radius: 1.5rem;
  background: radial-gradient(
      120% 120% at 50% 0%,
      rgba(16, 185, 129, 0.12),
      rgba(15, 23, 42, 0.06) 55%,
      rgba(15, 23, 42, 0.9) 100%
    ),
    rgba(15, 23, 42, 0.85);
  border: 1px solid rgba(148, 163, 184, 0.22);
  box-shadow:
    inset 0 0 0 1px rgba(148, 163, 184, 0.08),
    0 20px 40px -24px rgba(15, 23, 42, 0.75),
    0 0 45px rgba(16, 185, 129, 0.15);
  overflow: hidden;
  backdrop-filter: blur(12px);
}

.map-viewport__glow {
  position: absolute;
  inset: 0;
  pointer-events: none;
  background:
    radial-gradient(circle at 20% 20%, rgba(45, 212, 191, 0.16), transparent 60%),
    radial-gradient(circle at 80% 30%, rgba(251, 191, 36, 0.1), transparent 55%),
    radial-gradient(circle at 50% 80%, rgba(56, 189, 248, 0.12), transparent 60%);
  opacity: 0.8;
}

.map-viewport__content {
  position: relative;
  width: 100%;
  height: 100%;
  display: grid;
  place-items: center;
  padding: 1.75rem;
  box-sizing: border-box;
  overflow: hidden;
  touch-action: none;
}

.map-viewport__surface {
  width: 100%;
  height: 100%;
  display: grid;
  place-items: center;
  overflow: hidden;
  position: relative;
}

.map-viewport__grid {
  display: grid;
  position: relative;
  padding: 1.5rem;
  border-radius: 1.25rem;
  background:
    linear-gradient(135deg, rgba(15, 23, 42, 0.65), rgba(30, 41, 59, 0.85)),
    rgba(15, 23, 42, 0.75);
  box-shadow:
    inset 0 0 0 1px rgba(148, 163, 184, 0.18),
    inset 0 20px 40px -30px rgba(14, 116, 144, 0.4),
    0 20px 45px -30px rgba(15, 23, 42, 0.9);
  transition: box-shadow 0.3s ease;
  will-change: transform;
}

.map-viewport__grid::before {
  content: '';
  position: absolute;
  inset: 0;
  border-radius: inherit;
  mix-blend-mode: screen;
  pointer-events: none;
  background-image: linear-gradient(rgba(148, 163, 184, 0.08) 1px, transparent 1px),
    linear-gradient(90deg, rgba(148, 163, 184, 0.08) 1px, transparent 1px);
  background-size: calc(var(--tile-size, 64px) + 12px) calc(var(--tile-size, 64px) + 12px);
  opacity: 0.6;
}

.map-viewport__grid.is-dragging {
  cursor: grabbing;
}

.map-viewport__grid:not(.is-dragging) {
  cursor: grab;
}

.map-viewport__hint {
  position: absolute;
  bottom: 1.25rem;
  left: 50%;
  transform: translateX(-50%);
  padding: 0.6rem 1.2rem;
  border-radius: 9999px;
  background: rgba(15, 23, 42, 0.9);
  border: 1px solid rgba(148, 163, 184, 0.3);
  box-shadow: 0 12px 32px -18px rgba(15, 23, 42, 0.8);
  font-size: 0.75rem;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: rgba(226, 232, 240, 0.85);
  pointer-events: none;
}

.map-hint-enter-active,
.map-hint-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}

.map-hint-enter-from,
.map-hint-leave-to {
  opacity: 0;
  transform: translate(-50%, 10px);
}
</style>
