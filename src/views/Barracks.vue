<script setup lang="ts">
import { ref, onMounted } from 'vue';
import axios from 'axios';
import { useWebSocket } from '../services/websocket';

const troops = ref<any[]>([]);
const trainAmounts = ref<any>({});
const queue = ref<any[]>([]);
const loadingTroops = ref(true);
const loadingQueue = ref(true);
const villageId = ref<number | null>(null);

const { connect, onMessage } = useWebSocket();

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

const fetchTroops = async () => {
  try {
    const response = await axios.get('http://localhost:8000/api/troops/');
    troops.value = response.data;
    response.data.forEach((troop: any) => {
      trainAmounts.value[troop.id] = 0;
    });
  } catch (error) {
    console.error('Error fetching troops:', error);
  } finally {
    loadingTroops.value = false;
  }
};

const fetchQueue = async () => {
  if (!villageId.value) return;
  try {
    const response = await axios.get(`http://localhost:8000/api/villages/${villageId.value}/training-queue`);
    queue.value = response.data;
  } catch (error) {
    console.error('Error fetching training queue:', error);
  } finally {
    loadingQueue.value = false;
  }
};

const train = async () => {
  if (!villageId.value) return;
  const orders = Object.keys(trainAmounts.value)
    .filter(troopId => trainAmounts.value[troopId] > 0)
    .map(troopId => ({
      troop_id: parseInt(troopId),
      quantity: trainAmounts.value[troopId],
    }));

  if (orders.length === 0) return;

  try {
    await axios.post(`http://localhost:8000/api/villages/${villageId.value}/train`, orders);
    fetchQueue();
  } catch (error) {
    console.error('Error training troops:', error);
  }
};

onMounted(async () => {
  await getVillageId();
  if (villageId.value) {
    connect(villageId.value.toString());
    onMessage((event: MessageEvent) => {
      if (event.data === `village:${villageId.value}:training_started`) {
        fetchQueue();
      }
    });
  }
  fetchTroops();
  fetchQueue();
});
</script>

<template>
  <div>
    <h2 class="text-4xl font-bold mb-8">Barracks</h2>

    <div class="grid grid-cols-3 gap-8">
      <div>
        <h3 class="text-2xl font-bold mb-4">Train Troops</h3>
        <div v-if="loadingTroops" class="text-center">
          <p>Loading troops...</p>
        </div>
        <div v-else class="space-y-4">
          <div v-for="troop in troops" :key="troop.id">
            <p>{{ troop.name }}</p>
            <input type="number" v-model="trainAmounts[troop.id]" min="0" class="bg-surface border-2 border-secondary-700/50 p-2 rounded-lg w-24">
          </div>
          <button @click="train" class="bg-primary text-white px-4 py-2 rounded-lg hover:bg-primary-600">Train</button>
        </div>
      </div>
      <div>
        <h3 class="text-2xl font-bold mb-4">Training Queue</h3>
        <div v-if="loadingQueue" class="text-center">
          <p>Loading queue...</p>
        </div>
        <div v-else class="space-y-4">
          <div v-for="item in queue" :key="item.id">
            <p>{{ item.quantity }}x {{ item.troop.name }} - {{ item.end_time }}</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
