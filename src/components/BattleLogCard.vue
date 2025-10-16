<template>
  <div class="bg-surface border-2 border-secondary-700/50 p-4 rounded-lg">
    <p class="text-sm text-text-secondary">{{ log.log }}</p>
  </div>
</template>

<script setup lang="ts">
import { defineProps } from 'vue';

defineProps({
  log: {
    type: Object,
    required: true,
  },
});
</script>
