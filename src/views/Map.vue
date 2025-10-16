<script setup lang="ts">
import { ref, onMounted } from 'vue';
import axios from 'axios';
import MapTile from '../components/MapTile.vue';

const mapData = ref<any[]>([]);
const loading = ref(true);

const fetchMapData = async () => {
  try {
    const response = await axios.get('http://localhost:8000/api/map/');
    mapData.value = response.data;
  } catch (error) {
    console.error('Error fetching map data:', error);
  } finally {
    loading.value = false;
  }
};

onMounted(fetchMapData);
</script>

<template>
  <main class="flex-1 p-8 overflow-y-auto">
    <h2 class="text-4xl font-bold mb-8">Map</h2>

    <div v-if="loading" class="text-center">
      <p>Loading...</p>
    </div>

    <div v-else class="grid grid-cols-10 gap-2">
      <MapTile
        v-for="village in mapData"
        :key="village.id"
        :village="village"
      />
    </div>
  </main>
</template>
