<script setup lang="ts">
import { ref, onMounted } from 'vue';

import ResourceCard from '../components/ResourceCard.vue';
import BuildingCard from '../components/BuildingCard.vue';
import axios from 'axios';

const resources = ref<any[]>([]);
const buildings = ref<any[]>([]);
const villageId = ref(1); // Assuming a fixed village for now
const notifications = ref<any[]>([]);

const addNotification = (message: string, type: string = 'info') => {
  const id = Date.now();
  notifications.value.push({ id, message, type });
  setTimeout(() => {
    notifications.value = notifications.value.filter(n => n.id !== id);
  }, 5000);
};

const fetchVillageData = async () => {
  try {
    const response = await axios.get(`http://localhost:8000/api/villages/${villageId.value}`);
    const village = response.data;
    
    resources.value = [
      { title: 'Wood', subtitle: 'Resource', icon: '🪵', amount: village.wood, capacity: 50000, production: village.wood_production },
      { title: 'Clay', subtitle: 'Resource', icon: '🧱', amount: village.clay, capacity: 50000, production: village.clay_production },
      { title: 'Iron', subtitle: 'Resource', icon: '🔩', amount: village.iron, capacity: 50000, production: village.iron_production },
    ];

    const BASE_COST = {
        "wood_mill": {"wood": 60, "clay": 40, "iron": 20},
        "clay_pit": {"wood": 40, "clay": 60, "iron": 20},
        "iron_mine": {"wood": 80, "clay": 80, "iron": 40},
    };
    const COST_FACTOR = 1.5;

    buildings.value = [
        {
            name: 'Wood Mill', 
            internal_name: 'wood_mill', 
            description: 'Increases wood production', 
            icon: '🌲', 
            level: village.wood_mill_level, 
            isUpgrading: false,
            cost_wood: Math.round(BASE_COST["wood_mill"]["wood"] * (COST_FACTOR ** village.wood_mill_level)),
            cost_clay: Math.round(BASE_COST["wood_mill"]["clay"] * (COST_FACTOR ** village.wood_mill_level)),
            cost_iron: Math.round(BASE_COST["wood_mill"]["iron"] * (COST_FACTOR ** village.wood_mill_level)),
            canAfford: village.wood >= BASE_COST["wood_mill"]["wood"] * (COST_FACTOR ** village.wood_mill_level) &&
                       village.clay >= BASE_COST["wood_mill"]["clay"] * (COST_FACTOR ** village.wood_mill_level) &&
                       village.iron >= BASE_COST["wood_mill"]["iron"] * (COST_FACTOR ** village.wood_mill_level),
        },
        {
            name: 'Clay Pit', 
            internal_name: 'clay_pit', 
            description: 'Increases clay production', 
            icon: '🧱', 
            level: village.clay_pit_level, 
            isUpgrading: false,
            cost_wood: Math.round(BASE_COST["clay_pit"]["wood"] * (COST_FACTOR ** village.clay_pit_level)),
            cost_clay: Math.round(BASE_COST["clay_pit"]["clay"] * (COST_FACTOR ** village.clay_pit_level)),
            cost_iron: Math.round(BASE_COST["clay_pit"]["iron"] * (COST_FACTOR ** village.clay_pit_level)),
            canAfford: village.wood >= BASE_COST["clay_pit"]["wood"] * (COST_FACTOR ** village.clay_pit_level) &&
                       village.clay >= BASE_COST["clay_pit"]["clay"] * (COST_FACTOR ** village.clay_pit_level) &&
                       village.iron >= BASE_COST["clay_pit"]["iron"] * (COST_FACTOR ** village.clay_pit_level),
        },
        {
            name: 'Iron Mine', 
            internal_name: 'iron_mine', 
            description: 'Increases iron production', 
            icon: '⛏️', 
            level: village.iron_mine_level, 
            isUpgrading: false,
            cost_wood: Math.round(BASE_COST["iron_mine"]["wood"] * (COST_FACTOR ** village.iron_mine_level)),
            cost_clay: Math.round(BASE_COST["iron_mine"]["clay"] * (COST_FACTOR ** village.iron_mine_level)),
            cost_iron: Math.round(BASE_COST["iron_mine"]["iron"] * (COST_FACTOR ** village.iron_mine_level)),
            canAfford: village.wood >= BASE_COST["iron_mine"]["wood"] * (COST_FACTOR ** village.iron_mine_level) &&
                       village.clay >= BASE_COST["iron_mine"]["clay"] * (COST_FACTOR ** village.iron_mine_level) &&
                       village.iron >= BASE_COST["iron_mine"]["iron"] * (COST_FACTOR ** village.iron_mine_level),
        },
    ];

  } catch (error: any) {
    if (error.response && error.response.status === 404) {
      addNotification("Village not found, creating a new one...", "info");
      try {
        const createResponse = await axios.post('http://localhost:8000/api/villages/', { name: 'My New Village' });
        villageId.value = createResponse.data.id;
        addNotification("New village created!", "success");
        await fetchVillageData();
      } catch (createError) {
        addNotification("Error creating village!", "error");
        console.error('Error creating village:', createError);
      }
    } else {
      addNotification("Failed to fetch village data.", "error");
      console.error('Full error object:', JSON.stringify(error, null, 2));
    }
  }
};

const handleUpgrade = async (buildingName: string) => {
    const buildingToUpgrade = buildings.value.find(b => b.name === buildingName);
    if (!buildingToUpgrade) return;

    try {
        await axios.post(`http://localhost:8000/api/villages/${villageId.value}/upgrade/${buildingToUpgrade.internal_name}`);
        addNotification(`${buildingName} upgrade started!`, 'success');
        fetchVillageData(); // Refetch data to update the UI
    } catch (error: any) {
        if (error.response && error.response.data && error.response.data.detail) {
            addNotification(error.response.data.detail, 'error');
        } else {
            addNotification(`Error upgrading ${buildingName}.`, 'error');
        }
        console.error(`Error upgrading ${buildingName}:`, error);
    }
};

onMounted(async () => {
  await fetchVillageData();
  setInterval(fetchVillageData, 10000); // Fetch data every 10 seconds
});

</script>

<template>
  <main class="flex-1 p-8 overflow-y-auto">
    <!-- Header -->
    <header class="flex justify-between items-center mb-8">
      <div>
        <h2 class="text-4xl font-bold">Village Dashboard</h2>
        <p class="text-text-secondary">Welcome back, Commander!</p>
      </div>
      <div class="flex items-center gap-4">
        <div class="text-right">
          <p class="font-bold">Player Name</p>
          <p class="text-sm text-text-secondary">Level 1</p>
        </div>
        <div class="w-12 h-12 bg-surface rounded-full"></div>
      </div>
    </header>

    <!-- Resources -->
    <section class="mb-12">
      <h3 class="text-2xl font-bold mb-4">Resources</h3>
      <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
        <ResourceCard
          v-for="resource in resources"
          :key="resource.title"
          v-bind="resource"
        />
      </div>
    </section>

    <!-- Buildings -->
    <section>
      <h3 class="text-2xl font-bold mb-4">Buildings</h3>
      <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
        <BuildingCard
          v-for="building in buildings"
          :key="building.name"
          v-bind="building"
          @upgrade="handleUpgrade"
        />
      </div>
    </section>
  </main>
</template>