<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue';
import { useRouter } from 'vue-router';
import axios from 'axios';
import MapTile from '../components/MapTile.vue';
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

const gridStyle = computed(() => {
  if (!overview.value) {
    return {};
  }
  const size = `${tileSize.value}px`;
  return {
    gridTemplateColumns: `repeat(${overview.value.width}, ${size})`,
    gridAutoRows: size,
  };
});

const viewportStyle = computed(() => ({
  height: 'min(70vh, 38rem)',
  width: 'min(100%, 42rem)',
  maxWidth: '42rem',
  maxHeight: '38rem',
}));

const gridMetrics = computed(() => {
  if (!overview.value) {
    return {};
  }
  const mapWidth =
    overview.value.width * tileSize.value +
    Math.max(overview.value.width - 1, 0) * GRID_GAP_PX;
  const mapHeight =
    overview.value.height * tileSize.value +
    Math.max(overview.value.height - 1, 0) * GRID_GAP_PX;
  return {
    width: `${mapWidth}px`,
    height: `${mapHeight}px`,
  };
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
  <main class="flex-1 p-8 overflow-y-auto">
    <div class="flex flex-wrap items-end justify-between gap-4 mb-8">
      <div>
        <h2 class="text-4xl font-bold">Map</h2>
        <p v-if="overview" class="text-sm text-text-secondary mt-1">
          {{ overview.width }} x {{ overview.height }} tiles - each step = 1 minute of travel
        </p>
      </div>
      <div class="flex items-center gap-2">
        <button
          type="button"
          class="px-3 py-1.5 rounded-md border border-secondary-700/60 bg-secondary-900/40 text-sm text-text-secondary hover:bg-secondary-800/60 transition"
          @click="fetchMapData"
        >
          Refresh
        </button>
      </div>
    </div>
    <div
      v-if="overview"
      class="flex flex-wrap items-center gap-4 mb-6 text-sm text-text-secondary"
    >
      <div class="flex items-center gap-3 rounded-md border border-secondary-700/40 bg-secondary-900/60 px-4 py-2">
        <span class="uppercase tracking-wide text-[0.65rem] text-text-secondary">Zoom</span>
        <button
          type="button"
          class="h-8 w-8 grid place-items-center rounded-md border border-secondary-700/50 bg-secondary-900/70 text-text-secondary hover:bg-secondary-800/70 transition"
          @click="adjustTileSize(-8)"
          title="Zoom out"
        >
          –
        </button>
        <input
          v-model.number="tileSize"
          type="range"
          :min="minTileSize"
          :max="maxTileSize"
          :step="4"
          class="w-36 accent-emerald-400"
        />
        <button
          type="button"
          class="h-8 w-8 grid place-items-center rounded-md border border-secondary-700/50 bg-secondary-900/70 text-text-secondary hover:bg-secondary-800/70 transition"
          @click="adjustTileSize(8)"
          title="Zoom in"
        >
          +
        </button>
        <button
          type="button"
          class="h-8 px-3 rounded-md border border-secondary-700/50 bg-secondary-900/70 text-text-secondary hover:bg-secondary-800/70 transition"
          @click="resetTileSize"
        >
          Reset
        </button>
        <span class="font-mono text-text-primary text-xs">
          {{ tileSize }} px
        </span>
      </div>
    </div>

    <div v-if="loading" class="text-center text-text-secondary py-16">
      <p>Loading world data...</p>
    </div>

    <div v-else-if="error" class="text-center text-red-400 py-16">
      <p>{{ error }}</p>
    </div>

    <div v-else-if="overview" class="flex flex-col lg:flex-row gap-6">
      <section class="flex-1 min-w-0 space-y-4">
        <div
          class="relative rounded-2xl border border-secondary-700/40 bg-gradient-to-br from-secondary-900/80 to-secondary-800/60 shadow-lg shadow-black/10 min-h-0"
        >
          <div class="absolute inset-x-0 top-0 h-10 rounded-t-2xl bg-secondary-900/60 backdrop-blur pointer-events-none"></div>
          <div
            class="relative overflow-x-auto overflow-y-auto rounded-2xl px-4 pb-4 pt-10 w-full min-h-0 max-w-full"
            :style="viewportStyle"
          >
            <div class="grid gap-1" :style="[gridStyle, gridMetrics]">
              <MapTile
                v-for="tile in orderedTiles"
                :key="`${tile.x}-${tile.y}`"
                :tile="tile"
                :selected="selectedTile?.x === tile.x && selectedTile?.y === tile.y"
                :tile-size="tileSize"
                @select="selectTile"
              />
            </div>
          </div>
        </div>

        <div class="flex flex-wrap gap-4 text-xs text-text-secondary">
          <div class="flex items-center gap-2">
            <span class="inline-block h-3 w-3 rounded-sm bg-emerald-400/80"></span>
            Player village
          </div>
          <div class="flex items-center gap-2">
            <span class="inline-block h-3 w-3 rounded-sm bg-amber-400/80"></span>
            Barbarian village
          </div>
          <div class="flex items-center gap-2">
            <span class="inline-block h-3 w-3 rounded-sm bg-secondary-700/60"></span>
            Empty tile
          </div>
        </div>
      </section>

      <aside class="w-full lg:w-72 border border-secondary-700/40 bg-secondary-900/40 rounded-lg p-4">
        <h3 class="text-xl font-semibold mb-3">Tile details</h3>
        <div v-if="selectedTile" class="space-y-3 text-sm">
          <div class="flex justify-between font-mono text-text-secondary">
            <span>Coords</span>
            <span>{{ selectedTile.x }} | {{ selectedTile.y }}</span>
          </div>
          <div class="flex justify-between text-text-secondary">
            <span>Travel time to origin</span>
            <span>{{ travelTimeFromOrigin }} min</span>
          </div>

          <div
            v-if="selectedTile.type === 'player' && selectedTile.village"
            class="rounded-md bg-emerald-500/5 border border-emerald-500/30 p-3 space-y-2"
          >
            <div class="flex items-center justify-between">
              <p class="text-lg font-semibold text-text-primary">
                {{ selectedTile.village.name }}
              </p>
              <span class="text-xs uppercase tracking-wide text-emerald-300">Player</span>
            </div>
            <p class="text-text-secondary">
              Owner:
              <span class="text-text-primary">{{ selectedTile.village.owner.username }}</span>
            </p>
            <p class="text-text-secondary">Score: {{ selectedTile.village.score }}</p>
            <p class="text-xs text-text-secondary">
              Wood Lv. {{ selectedTile.village.wood_mill_level }} | Clay Lv.
              {{ selectedTile.village.clay_pit_level }} | Iron Lv.
              {{ selectedTile.village.iron_mine_level }}
            </p>
          </div>

          <div
            v-else-if="selectedTile.type === 'barbarian' && selectedTile.barbarian"
            class="rounded-md bg-amber-500/5 border border-amber-500/40 p-3 space-y-2"
          >
            <div class="flex items-center justify-between">
              <p class="text-lg font-semibold text-amber-100">
                {{ selectedTile.barbarian.name }}
              </p>
              <span class="text-xs uppercase tracking-wide text-amber-300">Barbarian</span>
            </div>
            <p class="text-text-secondary">
              Level: <span class="text-text-primary">{{ selectedTile.barbarian.level }}</span>
            </p>
            <p class="text-text-secondary">
              Warriors:
              <span class="text-text-primary">{{ selectedTile.barbarian.warriors }}</span>
            </p>
            <p class="text-xs text-text-secondary">
              Barbarians grow based on the global growth schedule. Expect tougher battles over time.
            </p>
            <button
              type="button"
              class="mt-3 w-full rounded-lg border border-primary/40 bg-primary/20 px-3 py-2 text-sm font-semibold text-primary-100 hover:bg-primary/30"
              @click="openExpeditionPlanner(selectedTile.barbarian?.id)"
            >
              Prepare expedition
            </button>
          </div>

          <div
            v-else
            class="rounded-md border border-secondary-700/40 bg-secondary-900/60 p-3 text-text-secondary italic"
          >
            Empty tile. No settlement spotted yet.
          </div>
        </div>
        <div v-else class="text-text-secondary text-sm">
          Select a tile from the map to inspect its details.
        </div>
      </aside>
    </div>

    <div v-else class="text-center text-text-secondary py-12">
      <p>No map data available.</p>
    </div>
  </main>
</template>
