<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue';
import { useRouter } from 'vue-router';
import axios from 'axios';
import MapViewport from '../components/map/MapViewport.vue';
import MapZoomControls from '../components/map/MapZoomControls.vue';
import MapLegend from '../components/map/MapLegend.vue';
import type { MapOverview, MapTile as MapTileSummary } from '../types/map';

const router = useRouter();
const loading = ref(true);
const error = ref<string | null>(null);
const overview = ref<MapOverview | null>(null);
const selectedTile = ref<MapTileSummary | null>(null);

const orderedTiles = computed(() => overview.value?.tiles ?? []);
const GRID_GAP_PX = 4;
const minTileSize = 44;
const maxTileSize = 128;
const defaultTileSize = 72;
const tileSize = ref(defaultTileSize);

const clampTileSize = (value: number) => Math.min(maxTileSize, Math.max(minTileSize, Math.round(value)));

watch(tileSize, (value, oldValue) => {
  if (value === oldValue) return;
  tileSize.value = clampTileSize(value);
});

const travelTimeFromOrigin = computed(() => {
  if (!selectedTile.value) {
    return 0;
  }
  return selectedTile.value.x + selectedTile.value.y;
});

const selectTile = (tile: MapTileSummary) => {
  selectedTile.value = tile;
};

const adjustTileSize = (delta: number) => {
  tileSize.value = clampTileSize(tileSize.value + delta);
};

const resetTileSize = () => {
  tileSize.value = defaultTileSize;
};

const openExpeditionPlanner = (barbarianId: number | undefined) => {
  if (!barbarianId) return;
  router.push({ path: '/expeditions', query: { target: String(barbarianId) } });
};

const fetchMapData = async () => {
  loading.value = true;
  error.value = null;
  try {
    const response = await axios.get<MapOverview>('http://localhost:8000/api/map/');
    overview.value = response.data;
    selectedTile.value =
      response.data.tiles.find((tile) => tile.type !== 'empty') ?? response.data.tiles[0] ?? null;
  } catch (err) {
    console.error('Error fetching map data:', err);
    error.value = 'Unable to load the world map. Please try again shortly.';
  } finally {
    loading.value = false;
  }
};

onMounted(fetchMapData);
</script>

<template>
  <main class="flex-1 overflow-y-auto p-8">
    <div class="mb-8 flex flex-wrap items-end justify-between gap-4">
      <div>
        <h2 class="text-4xl font-bold tracking-tight">Map</h2>
        <p v-if="overview" class="mt-1 text-sm text-text-secondary">
          {{ overview.width }} × {{ overview.height }} tiles · every step takes 1 minute of travel
        </p>
      </div>
      <div class="flex items-center gap-2">
        <button
          type="button"
          class="rounded-md border border-secondary-700/60 bg-secondary-900/40 px-3 py-1.5 text-sm text-text-secondary transition hover:bg-secondary-800/60"
          @click="fetchMapData"
        >
          Refresh
        </button>
      </div>
    </div>

    <div v-if="loading" class="py-16 text-center text-text-secondary">
      <p>Loading world data...</p>
    </div>

    <div v-else-if="error" class="py-16 text-center text-red-400">
      <p>{{ error }}</p>
    </div>

    <div
      v-else-if="overview"
      class="grid gap-8 lg:grid-cols-[minmax(0,1.7fr)_minmax(0,1fr)] xl:grid-cols-[minmax(0,2fr)_minmax(0,1fr)]"
    >
      <section class="flex min-w-0 flex-col gap-6">
        <div class="flex flex-wrap items-center justify-between gap-4">
          <MapZoomControls
            v-model="tileSize"
            :min="minTileSize"
            :max="maxTileSize"
            :step="4"
            @zoom-step="adjustTileSize"
            @reset="resetTileSize"
          />
          <div class="rounded-xl border border-secondary-700/30 bg-secondary-900/40 px-4 py-2 text-xs uppercase tracking-wide text-text-secondary/70">
            Scroll to zoom · Drag to pan · Click a tile to inspect
          </div>
        </div>

        <MapViewport
          :tiles="orderedTiles"
          :width="overview.width"
          :height="overview.height"
          :tile-size="tileSize"
          :grid-gap="GRID_GAP_PX"
          :selected-tile="selectedTile"
          @request-zoom="adjustTileSize"
          @tile-select="selectTile"
        />

        <MapLegend />
      </section>

      <aside class="h-fit w-full rounded-2xl border border-secondary-700/40 bg-secondary-900/40 p-5 backdrop-blur">
        <h3 class="mb-4 text-xl font-semibold tracking-tight text-text-primary/90">Tile details</h3>
        <div v-if="selectedTile" class="space-y-4 text-sm">
          <div class="flex items-center justify-between rounded-lg border border-secondary-700/40 bg-secondary-900/60 px-3 py-2 font-mono text-text-secondary">
            <span>Coords</span>
            <span>{{ selectedTile.x }} | {{ selectedTile.y }}</span>
          </div>
          <div class="flex items-center justify-between rounded-lg border border-secondary-700/30 bg-secondary-900/50 px-3 py-2 text-text-secondary">
            <span>Travel time to origin</span>
            <span class="font-semibold text-text-primary">{{ travelTimeFromOrigin }} min</span>
          </div>

          <div
            v-if="selectedTile.type === 'player' && selectedTile.village"
            class="rounded-xl border border-emerald-500/40 bg-emerald-500/10 p-4 text-text-secondary shadow-[0_18px_36px_-26px_rgba(16,185,129,0.85)]"
          >
            <div class="flex items-center justify-between">
              <p class="text-lg font-semibold text-text-primary">
                {{ selectedTile.village.name }}
              </p>
              <span class="rounded-full border border-emerald-400/40 bg-emerald-400/20 px-3 py-1 text-xs uppercase tracking-wide text-emerald-100">
                Player
              </span>
            </div>
            <p class="mt-2">
              Owner:
              <span class="font-semibold text-text-primary">{{ selectedTile.village.owner.username }}</span>
            </p>
            <p>Score: {{ selectedTile.village.score }}</p>
            <div class="mt-2 grid grid-cols-1 gap-1 text-xs text-text-secondary/80">
              <span>Wood Lv. {{ selectedTile.village.wood_mill_level }}</span>
              <span>Clay Lv. {{ selectedTile.village.clay_pit_level }}</span>
              <span>Iron Lv. {{ selectedTile.village.iron_mine_level }}</span>
            </div>
          </div>

          <div
            v-else-if="selectedTile.type === 'barbarian' && selectedTile.barbarian"
            class="rounded-xl border border-amber-500/40 bg-amber-500/10 p-4 text-text-secondary shadow-[0_18px_36px_-26px_rgba(251,191,36,0.85)]"
          >
            <div class="flex items-center justify-between">
              <p class="text-lg font-semibold text-amber-100">
                {{ selectedTile.barbarian.name }}
              </p>
              <span class="rounded-full border border-amber-400/40 bg-amber-400/20 px-3 py-1 text-xs uppercase tracking-wide text-amber-100">
                Barbarian
              </span>
            </div>
            <p class="mt-2">
              Level: <span class="font-semibold text-text-primary">{{ selectedTile.barbarian.level }}</span>
            </p>
            <p>
              Warriors:
              <span class="font-semibold text-text-primary">{{ selectedTile.barbarian.warriors }}</span>
            </p>
            <p class="mt-2 text-xs text-text-secondary/80">
              Barbarians grow following the global schedule. Expect tougher resistance over time.
            </p>
            <button
              type="button"
              class="mt-4 w-full rounded-lg border border-primary/40 bg-primary/20 px-3 py-2 text-sm font-semibold text-primary-100 transition hover:bg-primary/30"
              @click="openExpeditionPlanner(selectedTile.barbarian?.id)"
            >
              Prepare expedition
            </button>
          </div>

          <div
            v-else
            class="rounded-xl border border-secondary-700/40 bg-secondary-900/60 p-4 text-text-secondary italic"
          >
            Empty tile. No settlement spotted yet.
          </div>
        </div>
        <div v-else class="text-sm text-text-secondary">
          Select a tile from the map to inspect its details.
        </div>
      </aside>
    </div>

    <div v-else class="py-12 text-center text-text-secondary">
      <p>No map data available.</p>
    </div>
  </main>
</template>
