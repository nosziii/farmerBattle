<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue';
import axios from 'axios';
import type {
  AdminUser,
  AdminUserCreate,
  AdminVillageSummary,
  AdminVillageDetail,
  AdminVillageUpdate,
  AdminVillageCreate,
  AdminAssignTileRequest,
} from '../types/admin';
import type { MapOverview } from '../types/map';

const API_BASE = 'http://localhost:8000/api';

const sections = [
  { key: 'users', label: 'Players' },
  { key: 'villages', label: 'Villages' },
  { key: 'map', label: 'World Map' },
] as const;

type SectionKey = typeof sections[number]['key'];

const adminToken = ref(localStorage.getItem('fb_admin_token') ?? 'changeme');
const activeSection = ref<SectionKey>('users');
const errorMessage = ref<string | null>(null);
const successMessage = ref<string | null>(null);
const loadingSection = ref<SectionKey | null>(null);

const users = ref<AdminUser[]>([]);
const villages = ref<AdminVillageSummary[]>([]);
const villageDetail = ref<AdminVillageDetail | null>(null);
const mapOverview = ref<MapOverview | null>(null);

const selectedUserId = ref<number | null>(null);
const selectedVillageId = ref<number | null>(null);

const villageForm = ref({
  wood: 0,
  clay: 0,
  iron: 0,
  gold: 0,
  wood_mill_level: 1,
  clay_pit_level: 1,
  iron_mine_level: 1,
  town_hall_level: 1,
  warehouse_level: 1,
});

const assignForm = ref<{ x: number | null; y: number | null; force: boolean }>({ x: null, y: null, force: false });
const newUserForm = ref<AdminUserCreate>({ username: '', password: 'password' });
const newVillageForm = ref<AdminVillageCreate>({ user_id: 0, name: '' });

const sectionLoaded = ref<Record<SectionKey, boolean>>({ users: false, villages: false, map: false });

watch(adminToken, (value) => {
  localStorage.setItem('fb_admin_token', value ?? '');
  sectionLoaded.value = { users: false, villages: false, map: false };
});

const tokenNotice = computed(() => !adminToken.value || adminToken.value === 'changeme');

const requestConfig = computed(() => ({
  headers: { 'X-Admin-Token': (adminToken.value ?? '').trim() },
}));

const resourceFields = [
  { key: 'wood', label: 'Wood' },
  { key: 'clay', label: 'Clay' },
  { key: 'iron', label: 'Iron' },
  { key: 'gold', label: 'Gold' },
] as const;

const buildingFields = [
  { key: 'wood_mill_level', label: 'Wood Mill' },
  { key: 'clay_pit_level', label: 'Clay Pit' },
  { key: 'iron_mine_level', label: 'Iron Mine' },
  { key: 'town_hall_level', label: 'Town Hall' },
  { key: 'warehouse_level', label: 'Warehouse' },
] as const;

const filteredVillages = computed(() => {
  if (!selectedUserId.value) {
    return villages.value;
  }
  return villages.value.filter((village) => village.user_id === selectedUserId.value);
});

const mapStats = computed(() => {
  if (!mapOverview.value) {
    return null;
  }
  const total = mapOverview.value.tiles.length;
  const players = mapOverview.value.tiles.filter((tile) => tile.type === 'player').length;
  const barbarians = mapOverview.value.tiles.filter((tile) => tile.type === 'barbarian').length;
  const empty = total - players - barbarians;
  return { total, players, barbarians, empty };
});

const setError = (message: string | null) => {
  errorMessage.value = message;
  if (message) {
    console.error('[Admin]', message);
  }
};

const setSuccess = (message: string | null) => {
  successMessage.value = message;
  if (message) {
    window.setTimeout(() => {
      if (successMessage.value === message) {
        successMessage.value = null;
      }
    }, 3000);
  }
};

const ensureToken = () => {
  if (!adminToken.value) {
    setError('Admin token is required.');
    return false;
  }
  setError(null);
  return true;
};

const hydrateVillageForm = (detail: AdminVillageDetail) => {
  villageForm.value = {
    wood: detail.resources.wood,
    clay: detail.resources.clay,
    iron: detail.resources.iron,
    gold: detail.resources.gold,
    wood_mill_level: detail.building_levels.wood_mill ?? 1,
    clay_pit_level: detail.building_levels.clay_pit ?? 1,
    iron_mine_level: detail.building_levels.iron_mine ?? 1,
    town_hall_level: detail.building_levels.town_hall ?? 1,
    warehouse_level: detail.building_levels.warehouse ?? 1,
  };
};

const fetchUsers = async () => {
  if (!ensureToken()) return;
  loadingSection.value = 'users';
  try {
    const { data } = await axios.get<AdminUser[]>(`${API_BASE}/admin/users`, requestConfig.value);
    users.value = data;
    if (!selectedUserId.value && data.length) {
      selectedUserId.value = data[0].id;
    }
  } catch (err: any) {
    setError(err.response?.data?.detail ?? 'Failed to fetch users.');
  } finally {
    sectionLoaded.value.users = true;
    loadingSection.value = null;
  }
};

const fetchVillages = async (refreshDetail = false) => {
  if (!ensureToken()) return;
  loadingSection.value = 'villages';
  try {
    const { data } = await axios.get<AdminVillageSummary[]>(`${API_BASE}/admin/villages`, requestConfig.value);
    villages.value = data;
    if (!selectedVillageId.value && data.length) {
      selectedVillageId.value = data[0].id;
    }
    if (refreshDetail && selectedVillageId.value) {
      await fetchVillageDetail(selectedVillageId.value);
    }
  } catch (err: any) {
    setError(err.response?.data?.detail ?? 'Failed to fetch villages.');
  } finally {
    sectionLoaded.value.villages = true;
    loadingSection.value = null;
  }
};

const fetchVillageDetail = async (villageId: number | null) => {
  if (!villageId || !ensureToken()) return;
  try {
    const { data } = await axios.get<AdminVillageDetail>(`${API_BASE}/admin/villages/${villageId}`, requestConfig.value);
    villageDetail.value = data;
    hydrateVillageForm(data);
  } catch (err: any) {
    setError(err.response?.data?.detail ?? 'Failed to load village detail.');
  }
};

const fetchMapOverview = async () => {
  if (!ensureToken()) return;
  loadingSection.value = 'map';
  try {
    const { data } = await axios.get<MapOverview>(`${API_BASE}/admin/map`, requestConfig.value);
    mapOverview.value = data;
  } catch (err: any) {
    setError(err.response?.data?.detail ?? 'Failed to load map overview.');
  } finally {
    sectionLoaded.value.map = true;
    loadingSection.value = null;
  }
};

const ensureSectionData = async (section: SectionKey) => {
  if (sectionLoaded.value[section]) {
    if (section === 'villages' && selectedVillageId.value) {
      await fetchVillageDetail(selectedVillageId.value);
    }
    return;
  }
  switch (section) {
    case 'users':
      await fetchUsers();
      break;
    case 'villages':
      await fetchVillages(true);
      break;
    case 'map':
      await Promise.all([fetchVillages(), fetchMapOverview()]);
      break;
  }
};

const saveVillage = async () => {
  if (!selectedVillageId.value || !ensureToken()) return;
  const payload: AdminVillageUpdate = {
    wood: villageForm.value.wood,
    clay: villageForm.value.clay,
    iron: villageForm.value.iron,
    gold: villageForm.value.gold,
    wood_mill_level: villageForm.value.wood_mill_level,
    clay_pit_level: villageForm.value.clay_pit_level,
    iron_mine_level: villageForm.value.iron_mine_level,
    town_hall_level: villageForm.value.town_hall_level,
    warehouse_level: villageForm.value.warehouse_level,
  };
  try {
    const { data } = await axios.put<AdminVillageDetail>(
      `${API_BASE}/admin/villages/${selectedVillageId.value}`,
      payload,
      requestConfig.value
    );
    villageDetail.value = data;
    hydrateVillageForm(data);
    setSuccess('Village updated');
    await fetchVillages();
  } catch (err: any) {
    setError(err.response?.data?.detail ?? 'Failed to update village.');
  }
};

const assignVillageTile = async () => {
  if (!selectedVillageId.value || !ensureToken()) return;
  if (assignForm.value.x == null || assignForm.value.y == null) {
    setError('Please provide tile coordinates.');
    return;
  }
  const payload: AdminAssignTileRequest = {
    village_id: selectedVillageId.value,
    x: Number(assignForm.value.x),
    y: Number(assignForm.value.y),
    force: !!assignForm.value.force,
  };
  try {
    await axios.post(`${API_BASE}/admin/map/assign`, payload, requestConfig.value);
    setSuccess('Village assigned to tile');
    await Promise.all([fetchVillageDetail(selectedVillageId.value), fetchVillages(), fetchMapOverview()]);
  } catch (err: any) {
    setError(err.response?.data?.detail ?? 'Failed to assign tile.');
  }
};

const createUser = async () => {
  if (!newUserForm.value.username.trim() || !ensureToken()) {
    setError('Username is required.');
    return;
  }
  try {
    await axios.post(`${API_BASE}/admin/users`, newUserForm.value, requestConfig.value);
    setSuccess('Player created');
    newUserForm.value = { username: '', password: 'password' };
    sectionLoaded.value.users = false;
    await fetchUsers();
  } catch (err: any) {
    setError(err.response?.data?.detail ?? 'Failed to create user.');
  }
};

const createVillage = async () => {
  if (!newVillageForm.value.user_id || !newVillageForm.value.name.trim() || !ensureToken()) {
    setError('Owner and village name are required.');
    return;
  }
  try {
    await axios.post(`${API_BASE}/admin/villages`, newVillageForm.value, requestConfig.value);
    setSuccess('Village created');
    newVillageForm.value = { user_id: selectedUserId.value ?? 0, name: '' };
    sectionLoaded.value.villages = false;
    await fetchVillages(true);
  } catch (err: any) {
    setError(err.response?.data?.detail ?? 'Failed to create village.');
  }
};

watch(selectedVillageId, (villageId) => {
  if (activeSection.value === 'villages') {
    fetchVillageDetail(villageId);
  }
});

watch(selectedUserId, () => {
  newVillageForm.value.user_id = selectedUserId.value ?? 0;
  if (filteredVillages.value.length) {
    selectedVillageId.value = filteredVillages.value[0].id;
  }
});

watch(activeSection, (section) => {
  setError(null);
  loadingSection.value = section;
  ensureSectionData(section).finally(() => {
    loadingSection.value = null;
  });
});

onMounted(async () => {
  await ensureSectionData('users');
  await ensureSectionData('villages');
});
</script>

<template>
  <main class="flex-1 overflow-y-auto p-8 space-y-8">
    <section class="rounded-2xl border border-secondary-700/40 bg-secondary-900/70 px-6 py-5 shadow-lg shadow-black/30 space-y-4">
      <div class="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <h1 class="text-3xl font-semibold text-text-primary">Admin Console</h1>
          <p class="text-sm text-text-secondary">
            Manage players, villages, and the world map.
          </p>
        </div>
        <div class="flex flex-wrap gap-2 items-center">
          <input
            v-model="adminToken"
            type="password"
            placeholder="Admin token"
            class="rounded-lg border border-secondary-700/50 bg-secondary-800/60 px-3 py-2 text-sm text-text-primary focus:outline-none focus:border-primary"
          />
          <button
            type="button"
            class="rounded-lg border border-primary/40 bg-primary/70 px-4 py-2 text-sm font-semibold text-white shadow-lg shadow-primary/20 hover:bg-primary"
            @click="ensureSectionData(activeSection)"
          >
            Reload
          </button>
        </div>
      </div>
      <p v-if="tokenNotice" class="text-xs text-amber-200">
        Tip: configure <code>ADMIN_TOKEN</code> on the backend and update it here for secure access.
      </p>
      <div v-if="errorMessage" class="rounded-lg border border-red-500/40 bg-red-500/10 px-4 py-2 text-red-200 text-sm">
        {{ errorMessage }}
      </div>
      <div v-else-if="successMessage" class="rounded-lg border border-emerald-500/40 bg-emerald-500/10 px-4 py-2 text-emerald-200 text-sm">
        {{ successMessage }}
      </div>
      <div class="flex flex-wrap gap-2 pt-2">
        <button
          v-for="section in sections"
          :key="section.key"
          class="rounded-xl border px-4 py-2 text-sm font-semibold transition"
          :class="[
            activeSection === section.key
              ? 'border-primary/60 bg-primary/15 text-text-primary shadow shadow-primary/20'
              : 'border-secondary-700/50 bg-secondary-800/60 text-text-secondary hover:bg-secondary-800'
          ]"
          @click="activeSection = section.key"
        >
          {{ section.label }}
        </button>
      </div>
    </section>

    <section v-if="activeSection === 'users'" class="rounded-2xl border border-secondary-700/40 bg-secondary-900/60 px-6 py-5 space-y-5">
      <header class="flex items-center justify-between">
        <div>
          <h2 class="text-xl font-semibold text-text-primary">Players</h2>
          <p class="text-sm text-text-secondary">Create players and review their assigned villages.</p>
        </div>
        <span class="text-xs text-text-secondary/70">{{ users.length }} total</span>
      </header>

      <div v-if="loadingSection === 'users'" class="py-16 text-center text-text-secondary">
        Loading players...
      </div>

      <div v-else class="grid gap-6 lg:grid-cols-2">
        <div class="space-y-3">
          <div class="max-h-64 overflow-y-auto space-y-2">
            <button
              v-for="user in users"
              :key="user.id"
              class="w-full rounded-lg border px-3 py-2 text-left text-sm transition"
              :class="[
                user.id === selectedUserId
                  ? 'border-primary/60 bg-primary/10 text-text-primary'
                  : 'border-secondary-700/40 bg-secondary-800/60 text-text-secondary'
              ]"
              @click="selectedUserId = user.id"
            >
              <div class="flex justify-between">
                <span class="font-semibold text-text-primary">{{ user.username }}</span>
                <span class="text-xs text-text-secondary/70">ID {{ user.id }}</span>
              </div>
              <div class="text-xs text-text-secondary/70">Villages: {{ user.village_ids.length }}</div>
            </button>
          </div>
        </div>

        <form class="space-y-3" @submit.prevent="createUser">
          <h3 class="text-sm font-semibold text-text-primary uppercase tracking-wide">Create player</h3>
          <input
            v-model="newUserForm.username"
            type="text"
            placeholder="Username"
            class="w-full rounded-lg border border-secondary-700/40 bg-secondary-800/60 px-3 py-2 text-sm text-text-primary focus:outline-none focus:border-primary"
          />
          <input
            v-model="newUserForm.password"
            type="password"
            placeholder="Password"
            class="w-full rounded-lg border border-secondary-700/40 bg-secondary-800/60 px-3 py-2 text-sm text-text-primary focus:outline-none focus:border-primary"
          />
          <button
            type="submit"
            class="rounded-lg border border-emerald-500/40 bg-emerald-500/70 px-4 py-2 text-sm font-semibold text-white hover:bg-emerald-500"
          >
            Add player
          </button>
        </form>
      </div>
    </section>

    <section v-else-if="activeSection === 'villages'" class="space-y-6">
      <div class="grid gap-6 lg:grid-cols-2">
        <div class="rounded-2xl border border-secondary-700/40 bg-secondary-900/60 px-6 py-5 space-y-4">
          <header class="flex items-center justify-between">
            <h2 class="text-xl font-semibold text-text-primary">Villages</h2>
            <span class="text-xs text-text-secondary/70">{{ villages.length }} total</span>
          </header>

          <div v-if="loadingSection === 'villages'" class="py-10 text-center text-text-secondary">
            Loading villages...
          </div>

          <div v-else class="space-y-2 max-h-72 overflow-y-auto">
            <button
              v-for="village in filteredVillages"
              :key="village.id"
              class="w-full rounded-lg border px-3 py-2 text-left text-sm transition"
              :class="[
                village.id === selectedVillageId
                  ? 'border-emerald-500/60 bg-emerald-500/10 text-text-primary'
                  : 'border-secondary-700/40 bg-secondary-800/60 text-text-secondary'
              ]"
              @click="selectedVillageId = village.id"
            >
              <div class="flex justify-between">
                <span class="font-semibold text-text-primary">{{ village.name }}</span>
                <span class="text-xs text-text-secondary/70">ID {{ village.id }}</span>
              </div>
              <div class="text-xs text-text-secondary/70">Owner: {{ village.user_name }}</div>
              <div class="text-xs text-text-secondary/70">Tile: {{ village.tile ? `${village.tile.x}|${village.tile.y}` : 'Unassigned' }}</div>
            </button>
          </div>

          <form class="space-y-2" @submit.prevent="createVillage">
            <h3 class="text-sm font-semibold text-text-primary uppercase tracking-wide">Create village</h3>
            <input
              v-model.number="newVillageForm.user_id"
              type="number"
              min="1"
              placeholder="Owner user id"
              class="w-full rounded-lg border border-secondary-700/40 bg-secondary-800/60 px-3 py-2 text-sm text-text-primary focus:outline-none focus:border-primary"
            />
            <input
              v-model="newVillageForm.name"
              type="text"
              placeholder="Village name"
              class="w-full rounded-lg border border-secondary-700/40 bg-secondary-800/60 px-3 py-2 text-sm text-text-primary focus:outline-none focus:border-primary"
            />
            <button
              type="submit"
              class="rounded-lg border border-primary/40 bg-primary/70 px-4 py-2 text-sm font-semibold text-white hover:bg-primary"
            >
              Add village
            </button>
          </form>
        </div>

        <div v-if="villageDetail" class="rounded-2xl border border-secondary-700/40 bg-secondary-900/60 px-6 py-5 space-y-5">
          <header class="flex items-center justify-between">
            <div>
              <h2 class="text-xl font-semibold text-text-primary">{{ villageDetail.name }}</h2>
              <p class="text-xs text-text-secondary">Owner: {{ villageDetail.user_name }}</p>
            </div>
            <span class="text-xs text-text-secondary/70">Tile: {{ villageDetail.tile ? `${villageDetail.tile.x}|${villageDetail.tile.y}` : 'Unassigned' }}</span>
          </header>

          <div class="grid gap-6 md:grid-cols-2">
            <div class="space-y-3">
              <h3 class="text-sm font-semibold text-text-primary uppercase tracking-wide">Resources</h3>
              <div class="grid gap-3 sm:grid-cols-2">
                <label v-for="field in resourceFields" :key="field.key" class="text-sm text-text-secondary">
                  <span class="block text-xs uppercase tracking-wide text-text-secondary/70">{{ field.label }}</span>
                  <input
                    v-model.number="(villageForm as any)[field.key]"
                    type="number"
                    step="0.01"
                    class="mt-1 w-full rounded-lg border border-secondary-700/40 bg-secondary-800/60 px-3 py-2 text-sm text-text-primary focus:outline-none focus:border-primary"
                  />
                </label>
              </div>
            </div>

            <div class="space-y-3">
              <h3 class="text-sm font-semibold text-text-primary uppercase tracking-wide">Building levels</h3>
              <div class="grid gap-3 sm:grid-cols-2">
                <label v-for="field in buildingFields" :key="field.key" class="text-sm text-text-secondary">
                  <span class="block text-xs uppercase tracking-wide text-text-secondary/70">{{ field.label }}</span>
                  <input
                    v-model.number="(villageForm as any)[field.key]"
                    type="number"
                    min="1"
                    class="mt-1 w-full rounded-lg border border-secondary-700/40 bg-secondary-800/60 px-3 py-2 text-sm text-text-primary focus:outline-none focus:border-primary"
                  />
                </label>
              </div>
            </div>
          </div>

          <div class="flex flex-wrap gap-3 pt-1">
            <button
              type="button"
              class="rounded-lg border border-primary/40 bg-primary/70 px-4 py-2 text-sm font-semibold text-white hover:bg-primary"
              @click="saveVillage"
            >
              Save changes
            </button>
          </div>
        </div>
      </div>

      <section class="rounded-2xl border border-secondary-700/40 bg-secondary-900/60 px-6 py-5 space-y-4">
        <h3 class="text-sm font-semibold text-text-primary uppercase tracking-wide">Assign map tile</h3>
        <p class="text-sm text-text-secondary">Force override removes the previous occupant.</p>
        <form class="flex flex-wrap items-end gap-3" @submit.prevent="assignVillageTile">
          <label class="flex flex-col text-sm text-text-secondary">
            <span class="text-xs uppercase tracking-wide text-text-secondary/70">X</span>
            <input
              v-model.number="assignForm.x"
              type="number"
              class="rounded-lg border border-secondary-700/40 bg-secondary-800/60 px-3 py-2 text-sm text-text-primary focus:outline-none focus:border-primary"
            />
          </label>
          <label class="flex flex-col text-sm text-text-secondary">
            <span class="text-xs uppercase tracking-wide text-text-secondary/70">Y</span>
            <input
              v-model.number="assignForm.y"
              type="number"
              class="rounded-lg border border-secondary-700/40 bg-secondary-800/60 px-3 py-2 text-sm text-text-primary focus:outline-none focus:border-primary"
            />
          </label>
          <label class="flex items-center gap-2 text-sm text-text-secondary">
            <input type="checkbox" v-model="assignForm.force" />
            Force override
          </label>
          <button
            type="submit"
            class="rounded-lg border border-emerald-500/40 bg-emerald-500/70 px-4 py-2 text-sm font-semibold text-white hover:bg-emerald-500"
          >
            Assign tile
          </button>
        </form>
      </section>
    </section>

    <section v-else-if="activeSection === 'map'" class="rounded-2xl border border-secondary-700/40 bg-secondary-900/60 px-6 py-6 space-y-6">
      <header class="flex items-center justify-between">
        <div>
          <h2 class="text-xl font-semibold text-text-primary">World map overview</h2>
          <p class="text-sm text-text-secondary">Inspect occupancy and assign villages to coordinates.</p>
        </div>
        <button
          type="button"
          class="rounded-lg border border-primary/40 bg-primary/70 px-4 py-2 text-sm font-semibold text-white hover:bg-primary"
          @click="fetchMapOverview"
        >
          Refresh map
        </button>
      </header>

      <div v-if="loadingSection === 'map'" class="py-16 text-center text-text-secondary">
        Loading map data...
      </div>

      <div v-else class="space-y-5">
        <div v-if="mapStats" class="grid gap-3 sm:grid-cols-4">
          <div class="stat-card">
            <p class="stat-label">Tiles</p>
            <p class="stat-value">{{ mapStats.total }}</p>
          </div>
          <div class="stat-card">
            <p class="stat-label">Player villages</p>
            <p class="stat-value">{{ mapStats.players }}</p>
          </div>
          <div class="stat-card">
            <p class="stat-label">Barbarians</p>
            <p class="stat-value">{{ mapStats.barbarians }}</p>
          </div>
          <div class="stat-card">
            <p class="stat-label">Empty tiles</p>
            <p class="stat-value">{{ mapStats.empty }}</p>
          </div>
        </div>

        <div class="rounded-xl border border-secondary-700/40 bg-secondary-900/70 overflow-hidden">
          <table class="w-full text-sm">
            <thead class="bg-secondary-900/80 text-text-secondary uppercase tracking-wide text-xs">
              <tr>
                <th class="px-4 py-2 text-left">Coordinates</th>
                <th class="px-4 py-2 text-left">Type</th>
                <th class="px-4 py-2 text-left">Name</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="tile in mapOverview?.tiles.slice(0, 200) ?? []"
                :key="`${tile.x}-${tile.y}`"
                class="border-t border-secondary-800/40 text-text-secondary"
              >
                <td class="px-4 py-2 text-text-primary font-semibold">
                  {{ tile.x }} | {{ tile.y }}
                </td>
                <td class="px-4 py-2 capitalize">{{ tile.type }}</td>
                <td class="px-4 py-2">
                  <span v-if="tile.type === 'player' && tile.village">
                    {{ tile.village.name }} ({{ tile.village.owner.username }})
                  </span>
                  <span v-else-if="tile.type === 'barbarian' && tile.barbarian">
                    {{ tile.barbarian.name }}
                  </span>
                  <span v-else>—</span>
                </td>
              </tr>
            </tbody>
          </table>
          <p v-if="mapOverview && mapOverview.tiles.length > 200" class="px-4 py-2 text-xs text-text-secondary/70">
            Showing first 200 tiles. Use filters or the API for full exports.
          </p>
        </div>
      </div>
    </section>
  </main>
</template>

<style scoped>
.stat-card {
  border-radius: 1rem;
  border: 1px solid rgba(148, 163, 184, 0.25);
  background: rgba(15, 23, 42, 0.65);
  padding: 1rem;
  box-shadow: 0 12px 24px rgba(15, 23, 42, 0.35);
}
.stat-label {
  font-size: 0.75rem;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: rgba(203, 213, 225, 0.7);
}
.stat-value {
  font-size: 1.5rem;
  font-weight: 600;
  color: var(--color-text-primary);
}
</style>
