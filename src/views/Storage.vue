<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import axios from 'axios';
import ResourceCard from '../components/ResourceCard.vue';
import type { BuildingStatus } from '../types/buildings';

const API_BASE = 'http://localhost:8000/api';
const villageId = 1;

interface ResourceBalances {
  wood: number;
  clay: number;
  iron: number;
  gold: number;
}

const loading = ref(true);
const error = ref<string | null>(null);
const resourceBalances = ref<ResourceBalances>({ wood: 0, clay: 0, iron: 0, gold: 0 });
const resourceCapacities = ref<ResourceBalances>({ wood: 0, clay: 0, iron: 0, gold: 0 });
const productionRates = ref<ResourceBalances>({ wood: 0, clay: 0, iron: 0, gold: 0 });
const buildingStatuses = ref<BuildingStatus[]>([]);

const numberFormatter = new Intl.NumberFormat();

const resourceCards = computed(() => [
  {
    title: 'Gold',
    subtitle: 'Minted by Town Hall',
    icon: '🪙',
    amount: resourceBalances.value.gold,
    capacity: resourceCapacities.value.gold || 1,
    production: productionRates.value.gold,
  },
  {
    title: 'Wood',
    subtitle: 'Stored timber',
    icon: '🪵',
    amount: resourceBalances.value.wood,
    capacity: resourceCapacities.value.wood || 1,
    production: productionRates.value.wood,
  },
  {
    title: 'Clay',
    subtitle: 'Molded bricks',
    icon: '🧱',
    amount: resourceBalances.value.clay,
    capacity: resourceCapacities.value.clay || 1,
    production: productionRates.value.clay,
  },
  {
    title: 'Iron',
    subtitle: 'Smelted ore',
    icon: '⛏️',
    amount: resourceBalances.value.iron,
    capacity: resourceCapacities.value.iron || 1,
    production: productionRates.value.iron,
  },
]);

const producers = computed(() => {
  return buildingStatuses.value
    .filter((status) => status.resource_field)
    .map((status) => ({
      key: status.internal_name,
      name: status.name,
      icon: status.icon || '🏗️',
      level: status.level,
      production: status.production,
      storage: status.storage,
      resource: status.resource_field ?? '—',
      nextLevel: status.level + 1,
      hasNext: status.next_cost !== null,
    }))
    .sort((a, b) => a.resource.localeCompare(b.resource));
});

const upcomingBoosts = computed(() => {
  return buildingStatuses.value
    .filter((status) => status.resource_field && status.next_cost)
    .map((status) => ({
      key: status.internal_name,
      name: status.name,
      icon: status.icon || '⚙️',
      currentLevel: status.level,
      nextLevel: status.level + 1,
      duration: status.upgrade_duration,
      nextCost: status.next_cost,
      effects: status.effects,
      resource: status.resource_field,
      production: status.production,
    }));
});

const formatNumber = (value: number) => numberFormatter.format(Math.max(0, Math.floor(value || 0)));

const updateFromStatuses = () => {
  const findStatus = (key: string) => buildingStatuses.value.find((status) => status.internal_name === key);
  const wood = findStatus('wood_mill');
  const clay = findStatus('clay_pit');
  const iron = findStatus('iron_mine');
  const townHall = findStatus('town_hall');
  const warehouse = findStatus('warehouse');

  const warehouseBonus = warehouse?.storage ?? 0;

  if (wood) {
    productionRates.value.wood = wood.production;
    if (wood.storage != null) {
      resourceCapacities.value.wood = wood.storage + warehouseBonus;
    }
  }
  if (clay) {
    productionRates.value.clay = clay.production;
    if (clay.storage != null) {
      resourceCapacities.value.clay = clay.storage + warehouseBonus;
    }
  }
  if (iron) {
    productionRates.value.iron = iron.production;
    if (iron.storage != null) {
      resourceCapacities.value.iron = iron.storage + warehouseBonus;
    }
  }
  if (townHall) {
    productionRates.value.gold = townHall.production;
    if (townHall.storage != null) {
      resourceCapacities.value.gold = townHall.storage;
    }
  }
};

const fetchAll = async () => {
  loading.value = true;
  error.value = null;
  try {
    const [villageResponse, statusResponse] = await Promise.all([
      axios.get(`${API_BASE}/villages/${villageId}`),
      axios.get<BuildingStatus[]>(`${API_BASE}/villages/${villageId}/buildings`),
    ]);

    const village = villageResponse.data ?? {};
    buildingStatuses.value = statusResponse.data ?? [];

    resourceBalances.value = {
      wood: village.wood ?? 0,
      clay: village.clay ?? 0,
      iron: village.iron ?? 0,
      gold: village.gold ?? 0,
    };

    productionRates.value = {
      wood: village.wood_production ?? 0,
      clay: village.clay_production ?? 0,
      iron: village.iron_production ?? 0,
      gold: village.gold_production ?? 0,
    };

    updateFromStatuses();
  } catch (err: any) {
    console.error('Failed to load storage overview:', err);
    error.value = err.response?.data?.detail ?? 'Could not load storage overview.';
  } finally {
    loading.value = false;
  }
};

onMounted(fetchAll);

const formatDuration = (seconds: number | null | undefined) => {
  if (!seconds || seconds <= 0) {
    return 'Instant';
  }
  const mins = Math.floor(seconds / 60);
  const hrs = Math.floor(mins / 60);
  const remMins = mins % 60;
  const remSecs = seconds % 60;

  if (hrs > 0) {
    return `${hrs}h ${remMins}m`;
  }
  if (mins > 0) {
    return `${mins}m ${remSecs}s`;
  }
  return `${remSecs}s`;
};
</script>

<template>
  <main class="flex-1 overflow-y-auto p-8 md:p-12 space-y-10">
    <section
      class="relative overflow-hidden rounded-3xl border border-secondary-700/40 bg-secondary-900/70 px-8 py-10 shadow-xl shadow-black/30"
    >
      <div class="absolute inset-0 bg-gradient-to-tr from-primary-900/20 via-secondary-900/40 to-secondary-900/80"></div>
      <div class="relative z-10 space-y-3 max-w-3xl">
        <p class="text-xs uppercase tracking-[0.35em] text-primary-200/80">Stockpiles</p>
        <h1 class="text-4xl font-semibold text-text-primary">Storage & Treasury</h1>
        <p class="text-base text-text-secondary leading-relaxed">
          Monitor your resources, storage limits and production pace. Upgrade stockpile structures to keep the
          forges burning and the coffers filled.
        </p>
      </div>
    </section>

    <section v-if="loading" class="py-20 text-center text-text-secondary">
      <p>Surveying storehouses...</p>
    </section>

    <section
      v-else-if="error"
      class="rounded-2xl border border-red-500/40 bg-red-500/10 px-6 py-5 text-red-100"
    >
      {{ error }}
    </section>

    <section v-else class="space-y-8">
      <div class="grid gap-5 md:grid-cols-2 xl:grid-cols-4">
        <ResourceCard
          v-for="card in resourceCards"
          :key="card.title"
          :title="card.title"
          :subtitle="card.subtitle"
          :icon="card.icon"
          :amount="card.amount"
          :capacity="card.capacity"
          :production="card.production"
        />
      </div>

      <div class="grid gap-6 lg:grid-cols-2">
        <section class="rounded-2xl border border-secondary-700/40 bg-secondary-900/60 px-6 py-6 space-y-4">
          <header class="flex items-center justify-between">
            <h2 class="text-xl font-semibold text-text-primary">Production Buildings</h2>
            <span class="text-xs uppercase tracking-wide text-text-secondary/70">Live output</span>
          </header>
          <ul class="space-y-4">
            <li
              v-for="producer in producers"
              :key="producer.key"
              class="rounded-xl border border-secondary-700/30 bg-secondary-900/70 px-4 py-3"
            >
              <div class="flex items-start justify-between gap-4">
                <div>
                  <p class="flex items-center gap-2 text-text-primary font-semibold">
                    <span class="text-lg">{{ producer.icon }}</span>
                    {{ producer.name }}
                    <span class="text-xs uppercase tracking-wide text-text-secondary/70">Lv. {{ producer.level }}</span>
                  </p>
                  <p class="text-xs text-text-secondary">
                    {{ producer.resource.toUpperCase() }} production · {{ formatNumber(producer.production) }}/h
                  </p>
                  <p v-if="producer.storage != null" class="text-xs text-text-secondary/80">
                    Storage cap: {{ formatNumber(producer.storage) }}
                  </p>
                </div>
                <div class="text-right text-xs text-text-secondary">
                  <p v-if="producer.hasNext">Next Lv. {{ producer.nextLevel }}</p>
                  <p v-if="producer.hasNext">Potential boost pending upgrade</p>
                  <p v-else>Maxed</p>
                </div>
              </div>
            </li>
          </ul>
        </section>

        <section class="rounded-2xl border border-secondary-700/40 bg-secondary-900/60 px-6 py-6 space-y-4">
          <header class="flex items-center justify-between">
            <h2 class="text-xl font-semibold text-text-primary">Upcoming Boosts</h2>
            <span class="text-xs uppercase tracking-wide text-text-secondary/70">
              {{ upcomingBoosts.length ? `${upcomingBoosts.length} options` : 'No upgrades queued' }}
            </span>
          </header>
          <p v-if="!upcomingBoosts.length" class="text-sm text-text-secondary">
            Queue building upgrades to see projected increases in capacity and production.
          </p>
          <ul v-else class="space-y-4">
            <li
              v-for="boost in upcomingBoosts"
              :key="boost.key"
              class="rounded-xl border border-primary-700/30 bg-primary-900/10 px-4 py-3"
            >
              <div class="flex items-start justify-between gap-4">
                <div>
                  <p class="flex items-center gap-2 text-text-primary font-semibold">
                    <span class="text-lg">{{ boost.icon }}</span>
                    {{ boost.name }}
                  </p>
                  <p class="text-xs text-text-secondary">
                    Currently Lv. {{ boost.currentLevel }} · Next Lv. {{ boost.nextLevel }}
                  </p>
                  <p class="text-xs text-text-secondary/80">
                    Upgrade duration: {{ formatDuration(boost.duration) }}
                  </p>
                </div>
                <div class="text-right text-xs text-text-secondary">
                  <p>Costs:</p>
                  <p>
                    {{ formatNumber(boost.nextCost?.wood ?? 0) }} wood ·
                    {{ formatNumber(boost.nextCost?.clay ?? 0) }} clay ·
                    {{ formatNumber(boost.nextCost?.iron ?? 0) }} iron
                  </p>
                </div>
              </div>
            </li>
          </ul>
        </section>
      </div>
    </section>
  </main>
</template>
