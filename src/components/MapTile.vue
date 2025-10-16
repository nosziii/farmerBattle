<template>
  <div class="group relative w-24 h-24 bg-surface border-2 border-secondary-700/50 flex items-center justify-center transition-all duration-300 hover:scale-110 hover:bg-secondary-800">
    <div class="text-center">
      <p class="text-lg font-bold">{{ village.name }}</p>
      <p class="text-xs text-text-secondary">{{ village.owner.username }}</p>
      <p class="text-xs text-text-secondary">Score: {{ village.score }}</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { defineProps } from 'vue';

defineProps({
  village: {
    type: Object,
    required: true,
  },
});
</script>
