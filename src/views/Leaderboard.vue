<script setup lang="ts">
import { ref, onMounted } from 'vue';
import axios from 'axios';
import LeaderboardItem from '../components/LeaderboardItem.vue';

const leaderboard = ref<any[]>([]);
const loading = ref(true);

const fetchLeaderboard = async () => {
  try {
    const response = await axios.get('http://localhost:8000/api/leaderboard/');
    leaderboard.value = response.data;
  } catch (error) {
    console.error('Error fetching leaderboard:', error);
  } finally {
    loading.value = false;
  }
};

onMounted(fetchLeaderboard);
</script>

<template>
  <main class="flex-1 p-8 overflow-y-auto">
    <h2 class="text-4xl font-bold mb-8">Leaderboard</h2>

    <div v-if="loading" class="text-center">
      <p>Loading...</p>
    </div>

    <div v-else class="space-y-4">
      <LeaderboardItem
        v-for="(village, index) in leaderboard"
        :key="village.id"
        :rank="index + 1"
        :playerName="village.owner.username"
        :level="village.wood_mill_level + village.clay_pit_level + village.iron_mine_level"
        :clanName="'No Clan'"
        :trophies="village.score"
        :avatar="'촌'"
      />
    </div>
  </main>
</template>
