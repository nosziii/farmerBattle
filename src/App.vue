<script setup lang="ts">
import { onMounted } from 'vue';
import axios from 'axios';

onMounted(async () => {
  try {
    await axios.post('http://localhost:8000/api/init/');
  } catch (error) {
    console.error('Error initializing data:', error);
  }
});
</script>

<template>
  <div class="min-h-screen bg-background text-text-primary flex">
    <!-- Sidebar -->
    <aside class="w-64 bg-surface p-6 flex flex-col justify-between">
      <div>
        <div class="flex items-center gap-4 mb-10">
          <div class="w-12 h-12 bg-gradient-to-br from-primary to-primary-700 rounded-xl flex items-center justify-center shadow-lg">
            <span class="text-3xl">🏰</span>
          </div>
          <div>
            <h1 class="text-xl font-bold">Farmer Battle</h1>
            <p class="text-xs text-text-secondary">alpha v0.1</p>
          </div>
        </div>
        <nav class="flex flex-col gap-4">
          <router-link to="/" class="flex items-center gap-3 px-4 py-3 text-text-secondary hover:bg-secondary-800 rounded-lg font-medium">
            <span class="text-xl">🏠</span> Village
          </router-link>
          <router-link to="/barracks" class="flex items-center gap-3 px-4 py-3 text-text-secondary hover:bg-secondary-800 rounded-lg font-medium">
            <span class="text-xl">⚔️</span> Barracks
          </router-link>
          <router-link to="/battle" class="flex items-center gap-3 px-4 py-3 text-text-secondary hover:bg-secondary-800 rounded-lg font-medium">
            <span class="text-xl">⚔️</span> Battle
          </router-link>
          <router-link to="/map" class="flex items-center gap-3 px-4 py-3 text-text-secondary hover:bg-secondary-800 rounded-lg font-medium">
            <span class="text-xl">🗺️</span> Map
          </router-link>
          <router-link to="/leaderboard" class="flex items-center gap-3 px-4 py-3 text-text-secondary hover:bg-secondary-800 rounded-lg font-medium">
            <span class="text-xl">🏆</span> Leaderboard
          </router-link>
        </nav>
      </div>
      <div class="text-center text-xs text-text-secondary">
        <p>&copy; 2025 Farmer Battle</p>
      </div>
    </aside>

    <!-- Main Content -->
    <router-view />

  </div>
</template>

