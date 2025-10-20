<script setup lang="ts">
import { computed } from 'vue';

const props = defineProps<{
  modelValue: number;
  min: number;
  max: number;
  step?: number;
}>();

const emit = defineEmits<{
  (e: 'update:modelValue', value: number): void;
  (e: 'zoom-step', delta: number): void;
  (e: 'reset'): void;
}>();

const stepSize = computed(() => props.step ?? 4);

const clamp = (value: number) =>
  Math.min(props.max, Math.max(props.min, Math.round(value)));

const sliderValue = computed({
  get: () => clamp(props.modelValue),
  set: (value: number) => emit('update:modelValue', clamp(value)),
});

const handleZoomStep = (direction: 'in' | 'out') => {
  const delta = direction === 'in' ? stepSize.value : -stepSize.value;
  emit('zoom-step', delta);
};

const handleReset = () => {
  emit('reset');
};
</script>

<template>
  <div
    class="map-zoom-controls flex items-center gap-3 rounded-xl border border-secondary-700/40 bg-secondary-900/70 px-4 py-3 shadow-inner shadow-black/40"
  >
    <span class="uppercase text-[0.65rem] tracking-wider text-text-secondary select-none">
      Zoom
    </span>
    <button
      type="button"
      class="h-9 w-9 rounded-full border border-secondary-700/50 bg-secondary-900/80 text-lg text-text-secondary transition hover:-translate-y-[1px] hover:bg-secondary-800/70 active:translate-y-0"
      :title="'Zoom out'"
      @click="handleZoomStep('out')"
    >
      –
    </button>
    <input
      v-model.number="sliderValue"
      type="range"
      :min="min"
      :max="max"
      :step="stepSize"
      class="h-1.5 w-40 cursor-pointer rounded-full bg-secondary-800/80 accent-emerald-400"
    />
    <button
      type="button"
      class="h-9 w-9 rounded-full border border-secondary-700/50 bg-secondary-900/80 text-lg text-text-secondary transition hover:-translate-y-[1px] hover:bg-secondary-800/70 active:translate-y-0"
      :title="'Zoom in'"
      @click="handleZoomStep('in')"
    >
      +
    </button>
    <button
      type="button"
      class="ml-2 rounded-md border border-emerald-500/40 bg-emerald-500/10 px-3 py-1.5 text-xs font-semibold uppercase tracking-wide text-emerald-200 transition hover:bg-emerald-500/20"
      @click="handleReset"
    >
      Reset
    </button>
    <span class="font-mono text-[0.7rem] text-text-secondary/80">
      {{ sliderValue }} px
    </span>
  </div>
</template>

<style scoped>
.map-zoom-controls {
  backdrop-filter: blur(6px);
}
</style>
