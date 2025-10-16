<script setup lang="ts">
import { ref, onMounted } from 'vue';
import axios from 'axios';
import OpponentCard from '../components/OpponentCard.vue';
import BattleLogCard from '../components/BattleLogCard.vue';

const opponents = ref<any[]>([]);
const battleLogs = ref<any[]>([]);
const loadingOpponents = ref(true);
const loadingLogs = ref(true);
const villageId = ref<number | null>(null);

const getVillageId = async () => {
  try {
    // I'm assuming user with id 1 for now
    const response = await axios.get('http://localhost:8000/api/villages/?user_id=1');
    if (response.data.length > 0) {
      villageId.value = response.data[0].id;
    }
  } catch (error) {
    console.error('Error fetching village id:', error);
  }
};

const fetchOpponents = async () => {
  if (!villageId.value) return;
  try {
    const response = await axios.get(`http://localhost:8000/api/battle/opponents/${villageId.value}`);
    opponents.value = response.data;
  } catch (error) {
    console.error('Error fetching opponents:', error);
  } finally {
    loadingOpponents.value = false;
  }
};

const handleAttack = async (defenderId: number) => {
  if (!villageId.value) return;
  try {
    await axios.post(`http://localhost:8000/api/battle/attack/${villageId.value}/${defenderId}`);
    fetchOpponents();
    fetchBattleLogs();
  } catch (error) {
    console.error('Error attacking village:', error);
  }
};

const fetchBattleLogs = async () => {
  if (!villageId.value) return;
  try {
    const villageResponse = await axios.get(`http://localhost:8000/api/villages/${villageId.value}`);
    const village = villageResponse.data;
    const offenseBattles = village.offense_battles || [];
    const defenseBattles = village.defense_battles || [];
    const allBattles = [...offenseBattles, ...defenseBattles];
    
    const logPromises = allBattles.map(battle => axios.get(`http://localhost:8000/api/battle/log/${battle.id}`));
    const logResponses = await Promise.all(logPromises);
    
    battleLogs.value = logResponses.map(response => response.data).flat();
  } catch (error) {
    console.error('Error fetching battle logs:', error);
  } finally {
    loadingLogs.value = false;
  }
};

onMounted(async () => {
  await getVillageId();
  fetchOpponents();
  fetchBattleLogs();
});
</script>

<template>
  <main class="flex-1 p-8 overflow-y-auto">
    <h2 class="text-4xl font-bold mb-8">Battle</h2>

    <div class="grid grid-cols-2 gap-8">
      <div>
        <h3 class="text-2xl font-bold mb-4">Opponents</h3>
        <div v-if="loadingOpponents" class="text-center">
          <p>Loading opponents...</p>
        </div>
        <div v-else class="space-y-4">
          <OpponentCard
            v-for="opponent in opponents"
            :key="opponent.id"
            :opponent="opponent"
            @attack="handleAttack"
          />
        </div>
      </div>
      <div>
        <h3 class="text-2xl font-bold mb-4">Battle History</h3>
        <div v-if="loadingLogs" class="text-center">
          <p>Loading battle history...</p>
        </div>
        <div v-else class="space-y-4">
          <BattleLogCard
            v-for="log in battleLogs"
            :key="log.id"
            :log="log"
          />
        </div>
      </div>
    </div>
  </main>
</template>
