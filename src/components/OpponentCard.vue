<template>
  <div class="group relative bg-surface border-2 border-secondary-700/50 p-4 rounded-lg flex items-center justify-between transition-all duration-300 hover:scale-105 hover:bg-secondary-800">
    <div>
      <p class="text-lg font-bold">{{ opponent.name }}</p>
      <p class="text-xs text-text-secondary">{{ opponent.owner.username }}</p>
      <p class="text-xs text-text-secondary">Score: {{ opponent.score }}</p>
    </div>
    <button @click="emitAttack" class="bg-primary text-white px-4 py-2 rounded-lg hover:bg-primary-600">Attack</button>
  </div>
</template>

<script setup lang="ts">
import { defineProps, defineEmits } from 'vue';

const props = defineProps({
  opponent: {
    type: Object,
    required: true,
  },
});

const emit = defineEmits(['attack']);

function emitAttack() {
  emit('attack', props.opponent.id);
}
</script>
