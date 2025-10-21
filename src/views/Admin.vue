<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue';
import { useRouter } from 'vue-router';
import axios from 'axios';
import { ensureAuthReady, signOut as authSignOut, useAuthState } from '../services/auth';
import AdminVillagesSection from './admin/AdminVillagesSection.vue';
import type {
  AdminUser,
  AdminUserCreate,
  AdminTroop,
  AdminTroopCreate,
  AdminTroopUpdate,
} from '../types/admin';
import type { MapOverview } from '../types/map';

const API_BASE = 'http://localhost:8000/api';

const sections = [
  { key: 'users', label: 'Players' },
  { key: 'villages', label: 'Villages' },
  { key: 'map', label: 'World Map' },
  { key: 'troops', label: 'Troops' },
] as const;

type SectionKey = typeof sections[number]['key'];

interface AdminTroopForm {
  name: string;
  attack: number;
  defense: number;
  speed: number;
  carry_capacity: number;
  wood_cost: number;
  clay_cost: number;
  iron_cost: number;
  training_time: number;
  requirements: string;
}

const { currentUser, isAdmin } = useAuthState();
const router = useRouter();

const isAuthenticated = computed(() => isAdmin.value);

const activeSection = ref<SectionKey>('users');
const errorMessage = ref<string | null>(null);
const successMessage = ref<string | null>(null);
const loadingSection = ref<SectionKey | null>(null);

const users = ref<AdminUser[]>([]);
const mapOverview = ref<MapOverview | null>(null);
const troops = ref<AdminTroop[]>([]);
const villagesSectionRef = ref<InstanceType<typeof AdminVillagesSection> | null>(null);

const troopForms = ref<Record<number, AdminTroopForm>>({});

const createEmptyTroopForm = (): AdminTroopForm => ({
  name: '',
  attack: 10,
  defense: 10,
  speed: 10,
  carry_capacity: 40,
  wood_cost: 60,
  clay_cost: 50,
  iron_cost: 40,
  training_time: 6,
  requirements: 'barracks:1',
});

const newTroopForm = ref<AdminTroopForm>(createEmptyTroopForm());
const troopRequirementHint = 'Format: building:level (e.g. barracks:1, smithy:2)';

const selectedUserId = ref<number | null>(null);

const selectedUser = computed(() => users.value.find((user) => user.id === selectedUserId.value) ?? null);

const userEditForm = ref({
  username: '',
  password: '',
  is_active: true,
});

const userUpdatePending = ref(false);

const newUserForm = ref<AdminUserCreate>({ username: '', password: 'password' });

const sectionLoaded = ref<Record<SectionKey, boolean>>({ users: false, villages: false, map: false, troops: false });
const villagesLoaded = computed(() => sectionLoaded.value.villages);
const setVillagesLoaded = (loaded: boolean) => {
  sectionLoaded.value.villages = loaded;
};

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
  if (message) console.error('[Admin]', message);
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

const knownTroopBuildings = ['barracks', 'smithy', 'stable', 'training_ground', 'workshop', 'forge'];

const formatRequirementsString = (requirements: AdminTroop['requirements']) =>
  [...requirements]
    .sort((a, b) => a.building.localeCompare(b.building))
    .map((req) => `${req.building}:${req.level}`)
    .join(', ');

const parseRequirementsString = (input: string): Record<string, number> => {
  const result: Record<string, number> = {};
  if (!input || !input.trim()) {
    return result;
  }

  const segments = input
    .split(',')
    .map((segment) => segment.trim())
    .filter(Boolean);

  for (const segment of segments) {
    const [buildingRaw, levelRaw] = segment.split(':').map((part) => part.trim());
    if (!buildingRaw || levelRaw === undefined) {
      throw new Error(`Invalid requirement segment "${segment}". Use building:level format.`);
    }
    const building = buildingRaw.toLowerCase();
    const levelValue = Number(levelRaw);
    if (!Number.isFinite(levelValue) || levelValue < 1) {
      throw new Error(`Invalid level for requirement "${building}". Use positive integers.`);
    }
    result[building] = Math.max(1, Math.floor(levelValue));
  }

  return result;
};

const buildTroopForm = (troop: AdminTroop): AdminTroopForm => ({
  name: troop.name,
  attack: troop.attack,
  defense: troop.defense,
  speed: troop.speed,
  carry_capacity: troop.carry_capacity,
  wood_cost: troop.wood_cost,
  clay_cost: troop.clay_cost,
  iron_cost: troop.iron_cost,
  training_time: troop.training_time,
  requirements: formatRequirementsString(troop.requirements),
});

const populateTroopForms = (data: AdminTroop[]) => {
  const forms: Record<number, AdminTroopForm> = {};
  data.forEach((troop) => {
    forms[troop.id] = buildTroopForm(troop);
  });
  troopForms.value = forms;
};

const resetTroopForm = (troopId: number) => {
  const troop = troops.value.find((entry) => entry.id === troopId);
  if (!troop) {
    return;
  }
  troopForms.value = {
    ...troopForms.value,
    [troopId]: buildTroopForm(troop),
  };
};

const resetNewTroopForm = () => {
  newTroopForm.value = createEmptyTroopForm();
};

const ensureAdminAccess = () => {
  if (!isAuthenticated.value) {
    setError('Admin privileges required.');
    return false;
  }
  setError(null);
  return true;
};

const fetchUsers = async () => {
  if (!ensureAdminAccess()) return;
  loadingSection.value = 'users';
  try {
    const { data } = await axios.get<AdminUser[]>(`${API_BASE}/admin/users`);
    users.value = data;
    if (selectedUserId.value && !data.some((user) => user.id === selectedUserId.value)) {
      selectedUserId.value = data.length ? data[0].id : null;
    }
    if (!selectedUserId.value && data.length) selectedUserId.value = data[0].id;
  } catch (err: any) {
    setError(err.response?.data?.detail ?? 'Failed to fetch users.');
  } finally {
    sectionLoaded.value.users = true;
    loadingSection.value = null;
  }
};

const fetchMapOverview = async () => {
  if (!ensureAdminAccess()) return;
  loadingSection.value = 'map';
  try {
    const { data } = await axios.get<MapOverview>(`${API_BASE}/admin/map`);
    mapOverview.value = data;
  } catch (err: any) {
    setError(err.response?.data?.detail ?? 'Failed to load map overview.');
  } finally {
    sectionLoaded.value.map = true;
    loadingSection.value = null;
  }
};

const fetchTroops = async () => {
  if (!ensureAdminAccess()) return;
  loadingSection.value = 'troops';
  try {
    const { data } = await axios.get<AdminTroop[]>(`${API_BASE}/admin/troops`);
    troops.value = data;
    populateTroopForms(data);
    setError(null);
  } catch (err: any) {
    setError(err.response?.data?.detail ?? 'Failed to fetch troop definitions.');
  } finally {
    sectionLoaded.value.troops = true;
    loadingSection.value = null;
  }
};

const ensureSectionData = async (section: SectionKey) => {
  if (!isAuthenticated.value) return;
  switch (section) {
    case 'users':
      if (!sectionLoaded.value.users) {
        await fetchUsers();
      }
      break;
    case 'villages':
      if (villagesSectionRef.value) {
        await villagesSectionRef.value.ensureLoaded();
      }
      break;
    case 'map': {
      const tasks: Promise<unknown>[] = [fetchMapOverview()];
      if (villagesSectionRef.value) {
        tasks.push(villagesSectionRef.value.ensureLoaded());
      }
      await Promise.all(tasks);
      break;
    }
    case 'troops':
      if (!sectionLoaded.value.troops) {
        await fetchTroops();
      }
      break;
  }
};

const updateUser = async () => {
  if (!selectedUser.value || !ensureAdminAccess()) {
    setError('Select a player to update.');
    return;
  }

  const payload: Record<string, unknown> = {};
  const trimmedUsername = userEditForm.value.username.trim();
  if (trimmedUsername && trimmedUsername !== selectedUser.value.username) {
    payload.username = trimmedUsername;
  }
  if (userEditForm.value.password) {
    payload.password = userEditForm.value.password;
  }
  if (userEditForm.value.is_active !== selectedUser.value.is_active) {
    payload.is_active = userEditForm.value.is_active;
  }

  if (Object.keys(payload).length === 0) {
    setError('No changes to apply for this player.');
    return;
  }

  try {
    userUpdatePending.value = true;
    await axios.put(`${API_BASE}/admin/users/${selectedUser.value.id}`, payload);
    setSuccess('Player updated');
    userEditForm.value.password = '';
    const previousSelection = selectedUser.value.id;
    await fetchUsers();
    selectedUserId.value = previousSelection;
  } catch (err: any) {
    setError(err.response?.data?.detail ?? 'Failed to update player.');
  } finally {
    userUpdatePending.value = false;
  }
};

const createUser = async () => {
  if (!newUserForm.value.username.trim() || !ensureAdminAccess()) {
    setError('Username is required.');
    return;
  }
  try {
    await axios.post(`${API_BASE}/admin/users`, newUserForm.value);
    setSuccess('Player created');
    newUserForm.value = { username: '', password: 'password' };
    sectionLoaded.value.users = false;
    await fetchUsers();
  } catch (err: any) {
    setError(err.response?.data?.detail ?? 'Failed to create user.');
  }
};

const updateTroopDefinition = async (troopId: number) => {
  if (!ensureAdminAccess()) return;
  const form = troopForms.value[troopId];
  if (!form) {
    setError('Unable to edit this troop.');
    return;
  }

  if (!form.name.trim()) {
    setError('Troop name is required.');
    return;
  }

  let requirements: Record<string, number>;
  try {
    requirements = parseRequirementsString(form.requirements);
  } catch (error: any) {
    setError(error instanceof Error ? error.message : 'Invalid requirements format.');
    return;
  }

  setError(null);

  const payload: AdminTroopUpdate = {
    name: form.name.trim(),
    attack: form.attack,
    defense: form.defense,
    speed: form.speed,
    carry_capacity: form.carry_capacity,
    wood_cost: form.wood_cost,
    clay_cost: form.clay_cost,
    iron_cost: form.iron_cost,
    training_time: form.training_time,
    requirements,
  };

  try {
    await axios.put(`${API_BASE}/admin/troops/${troopId}`, payload);
    setSuccess('Troop updated');
    await fetchTroops();
  } catch (err: any) {
    setError(err.response?.data?.detail ?? 'Failed to update troop.');
  }
};

const createTroopDefinition = async () => {
  if (!ensureAdminAccess()) return;
  const form = newTroopForm.value;

  if (!form.name.trim()) {
    setError('Troop name is required.');
    return;
  }

  let requirements: Record<string, number>;
  try {
    requirements = parseRequirementsString(form.requirements);
  } catch (error: any) {
    setError(error instanceof Error ? error.message : 'Invalid requirements format.');
    return;
  }

  setError(null);

  const payload: AdminTroopCreate = {
    name: form.name.trim(),
    attack: form.attack,
    defense: form.defense,
    speed: form.speed,
    carry_capacity: form.carry_capacity,
    wood_cost: form.wood_cost,
    clay_cost: form.clay_cost,
    iron_cost: form.iron_cost,
    training_time: form.training_time,
    requirements,
  };

  try {
    await axios.post(`${API_BASE}/admin/troops`, payload);
    setSuccess('Troop created');
    resetNewTroopForm();
    sectionLoaded.value.troops = false;
    await fetchTroops();
  } catch (err: any) {
    setError(err.response?.data?.detail ?? 'Failed to create troop.');
  }
};

watch(selectedUser, (user) => {
  if (!user) {
    userEditForm.value = { username: '', password: '', is_active: true };
    return;
  }
  userEditForm.value = {
    username: user.username,
    password: '',
    is_active: user.is_active,
  };
});

watch(activeSection, (section) => {
  setError(null);
  if (!isAuthenticated.value) {
    loadingSection.value = null;
    return;
  }
  loadingSection.value = section;
  ensureSectionData(section).finally(() => {
    loadingSection.value = null;
  });
});

onMounted(async () => {
  await ensureAuthReady();
  if (isAuthenticated.value) {
    await ensureSectionData('users');
    await ensureSectionData('villages');
    await ensureSectionData('troops');
  } else {
    setError('Admin privileges required.');
  }
});

const signOut = () => {
  authSignOut();
  sectionLoaded.value = { users: false, villages: false, map: false, troops: false };
  users.value = [];
  mapOverview.value = null;
  troops.value = [];
  troopForms.value = {};
  resetNewTroopForm();
  router.push('/login');
};
</script>

<template>
  <main class="flex-1 overflow-y-auto p-8 space-y-8">
    <section class="rounded-2xl border border-secondary-700/40 bg-secondary-900/70 px-6 py-5 shadow-lg shadow-black/30 space-y-4">
      <div class="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <h1 class="text-3xl font-semibold text-text-primary">Admin Console</h1>
          <p class="text-sm text-text-secondary">Manage players, villages, and the world map.</p>
        </div>
        <div class="flex flex-wrap gap-2 items-center" v-if="isAuthenticated">
          <button
            type="button"
            class="rounded-lg border border-primary/40 bg-primary/70 px-4 py-2 text-sm font-semibold text-white shadow-lg shadow-primary/20 hover:bg-primary"
            @click="ensureSectionData(activeSection)"
          >
            Reload
          </button>
          <button
            type="button"
            class="rounded-lg border border-secondary-700/60 bg-secondary-800/60 px-4 py-2 text-sm text-text-secondary hover:bg-secondary-800"
            @click="signOut"
          >
            Sign out
          </button>
        </div>
      </div>
      <p v-if="isAuthenticated" class="text-xs text-text-secondary/70">
        Signed in as <strong>{{ currentUser?.username }}</strong>. Only administrators can access this console.
      </p>
      <div v-if="errorMessage" class="rounded-lg border border-red-500/40 bg-red-500/10 px-4 py-2 text-red-200 text-sm">
        {{ errorMessage }}
      </div>
      <div v-else-if="successMessage" class="rounded-lg border border-emerald-500/40 bg-emerald-500/10 px-4 py-2 text-emerald-200 text-sm">
        {{ successMessage }}
      </div>
      <div class="flex flex-wrap gap-2 pt-2" v-if="isAuthenticated">
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

    <section
      v-if="!isAuthenticated"
      class="rounded-2xl border border-secondary-700/40 bg-secondary-900/60 px-6 py-6 text-center text-sm text-text-secondary"
    >
      Admin privileges required. Please sign in with an administrator account.
    </section>

    <section v-else-if="activeSection === 'users'" class="rounded-2xl border border-secondary-700/40 bg-secondary-900/60 px-6 py-5 space-y-5">
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
                  ? 'border-primary/60 bg-primary/15 text-text-primary'
                  : 'border-secondary-700/40 bg-secondary-800/60 text-text-secondary hover:border-primary/40',
                !user.is_active ? 'opacity-70' : ''
              ]"
              @click="selectedUserId = user.id"
            >
              <div class="flex justify-between">
                <span class="font-semibold text-text-primary">{{ user.username }}</span>
                <span class="text-xs text-text-secondary/70">ID {{ user.id }}</span>
              </div>
              <div class="mt-1 flex items-center justify-between text-xs text-text-secondary/70">
                <span>Villages: {{ user.village_ids.length }}</span>
                <span v-if="!user.is_active" class="rounded-full border border-amber-400/40 bg-amber-500/10 px-2 py-0.5 text-[10px] uppercase tracking-wide text-amber-200">
                  Inactive
                </span>
              </div>
            </button>
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

        <div class="space-y-4">
          <div v-if="selectedUser" class="space-y-3 rounded-2xl border border-secondary-700/40 bg-secondary-900/60 px-5 py-5">
            <header class="flex items-center justify-between">
              <div>
                <h3 class="text-sm font-semibold text-text-primary uppercase tracking-wide">Manage player</h3>
                <p class="text-xs text-text-secondary/70">Villages: {{ selectedUser.village_ids.length }}</p>
              </div>
              <span
                class="rounded-full border px-2 py-0.5 text-[11px] uppercase tracking-wide"
                :class="selectedUser.is_active
                  ? 'border-emerald-500/40 bg-emerald-500/10 text-emerald-200'
                  : 'border-amber-500/40 bg-amber-500/10 text-amber-200'"
              >
                {{ selectedUser.is_active ? 'Active' : 'Inactive' }}
              </span>
            </header>

            <form class="space-y-3" @submit.prevent="updateUser">
              <label class="block text-sm text-text-secondary">
                <span class="text-xs uppercase tracking-wide text-text-secondary/70">Username</span>
                <input
                  v-model="userEditForm.username"
                  type="text"
                  required
                  class="mt-1 w-full rounded-lg border border-secondary-700/40 bg-secondary-800/60 px-3 py-2 text-sm text-text-primary focus:outline-none focus:border-primary"
                />
              </label>
              <label class="block text-sm text-text-secondary">
                <span class="text-xs uppercase tracking-wide text-text-secondary/70">New password</span>
                <input
                  v-model="userEditForm.password"
                  type="password"
                  placeholder="Leave blank to keep current"
                  class="mt-1 w-full rounded-lg border border-secondary-700/40 bg-secondary-800/60 px-3 py-2 text-sm text-text-primary focus:outline-none focus:border-primary"
                />
              </label>
              <label class="flex items-center gap-2 text-sm text-text-secondary">
                <input type="checkbox" v-model="userEditForm.is_active" />
                Active account
              </label>
              <button
                type="submit"
                class="w-full rounded-lg border border-primary/40 bg-primary/70 px-4 py-2 text-sm font-semibold text-white hover:bg-primary disabled:cursor-not-allowed disabled:opacity-60"
                :disabled="userUpdatePending"
              >
                {{ userUpdatePending ? 'Saving...' : 'Save player' }}
              </button>
            </form>

            <div v-if="selectedUser.village_ids.length" class="rounded-xl border border-secondary-700/40 bg-secondary-900/70 px-4 py-3 text-xs text-text-secondary">
              <p class="mb-1 font-semibold text-text-primary">Village IDs</p>
              <div class="flex flex-wrap gap-2">
                <span
                  v-for="villageId in selectedUser.village_ids"
                  :key="villageId"
                  class="rounded-lg border border-secondary-600/40 bg-secondary-800/60 px-2 py-1"
                >
                  #{{ villageId }}
                </span>
              </div>
            </div>
          </div>
          <div v-else class="rounded-2xl border border-secondary-700/40 bg-secondary-900/50 px-5 py-6 text-center text-sm text-text-secondary">
            Select a player from the list to manage their account.
          </div>
        </div>
      </div>
    </section>

    <AdminVillagesSection
      v-else-if="activeSection === 'villages'"
      ref="villagesSectionRef"
      :api-base="API_BASE"
      :active="activeSection === 'villages'"
      :selected-user-id="selectedUserId"
      :ensure-admin-access="ensureAdminAccess"
      :set-error="setError"
      :set-success="setSuccess"
      :section-loaded="villagesLoaded"
      :set-section-loaded="setVillagesLoaded"
      :troop-catalogue="troops"
    />

    <section
      v-else-if="activeSection === 'troops'"
      class="space-y-6 rounded-2xl border border-secondary-700/40 bg-secondary-900/60 px-6 py-6"
    >
      <header class="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
        <div>
          <h2 class="text-xl font-semibold text-text-primary">Troop Catalogue</h2>
          <p class="text-sm text-text-secondary">Adjust unit stats and building requirements.</p>
        </div>
        <span class="text-xs uppercase tracking-wide text-text-secondary/70">{{ troops.length }} defined</span>
      </header>

      <p class="text-xs text-text-secondary/70">{{ troopRequirementHint }}</p>

      <div v-if="loadingSection === 'troops' && !troops.length" class="py-10 text-center text-text-secondary">
        Loading troop definitions...
      </div>

      <div v-else class="space-y-6">
        <p v-if="!troops.length" class="text-sm text-text-secondary">
          No troops are defined yet. Use the form below to introduce a new unit.
        </p>
        <article
          v-for="troop in troops"
          :key="troop.id"
          class="rounded-2xl border border-secondary-700/40 bg-secondary-900/70 px-5 py-5 space-y-4"
        >
          <header class="flex items-center justify-between">
            <div>
              <h3 class="text-lg font-semibold text-text-primary">{{ troopForms[troop.id]?.name ?? troop.name }}</h3>
              <p class="text-xs text-text-secondary/70">Troop ID {{ troop.id }}</p>
            </div>
            <span class="text-xs text-text-secondary/70">
              Requirements: {{ troopForms[troop.id]?.requirements || formatRequirementsString(troop.requirements) || 'None' }}
            </span>
          </header>

          <template v-if="troopForms[troop.id]">
            <div class="grid gap-3 md:grid-cols-2">
              <label class="text-sm text-text-secondary">
                <span class="text-xs uppercase tracking-wide text-text-secondary/70">Name</span>
                <input
                  v-model="troopForms[troop.id].name"
                  type="text"
                  class="mt-1 w-full rounded-lg border border-secondary-700/40 bg-secondary-800/60 px-3 py-2 text-sm text-text-primary focus:border-primary focus:outline-none"
                />
              </label>
              <label class="text-sm text-text-secondary">
                <span class="text-xs uppercase tracking-wide text-text-secondary/70">Attack</span>
                <input
                  v-model.number="troopForms[troop.id].attack"
                  type="number"
                  min="1"
                  class="mt-1 w-full rounded-lg border border-secondary-700/40 bg-secondary-800/60 px-3 py-2 text-sm text-text-primary focus:border-primary focus:outline-none"
                />
              </label>
              <label class="text-sm text-text-secondary">
                <span class="text-xs uppercase tracking-wide text-text-secondary/70">Defense</span>
                <input
                  v-model.number="troopForms[troop.id].defense"
                  type="number"
                  min="1"
                  class="mt-1 w-full rounded-lg border border-secondary-700/40 bg-secondary-800/60 px-3 py-2 text-sm text-text-primary focus:border-primary focus:outline-none"
                />
              </label>
              <label class="text-sm text-text-secondary">
                <span class="text-xs uppercase tracking-wide text-text-secondary/70">Speed</span>
                <input
                  v-model.number="troopForms[troop.id].speed"
                  type="number"
                  min="1"
                  class="mt-1 w-full rounded-lg border border-secondary-700/40 bg-secondary-800/60 px-3 py-2 text-sm text-text-primary focus:border-primary focus:outline-none"
                />
              </label>
              <label class="text-sm text-text-secondary">
                <span class="text-xs uppercase tracking-wide text-text-secondary/70">Carry capacity</span>
                <input
                  v-model.number="troopForms[troop.id].carry_capacity"
                  type="number"
                  min="0"
                  class="mt-1 w-full rounded-lg border border-secondary-700/40 bg-secondary-800/60 px-3 py-2 text-sm text-text-primary focus:border-primary focus:outline-none"
                />
              </label>
              <label class="text-sm text-text-secondary">
                <span class="text-xs uppercase tracking-wide text-text-secondary/70">Training time (s)</span>
                <input
                  v-model.number="troopForms[troop.id].training_time"
                  type="number"
                  min="1"
                  class="mt-1 w-full rounded-lg border border-secondary-700/40 bg-secondary-800/60 px-3 py-2 text-sm text-text-primary focus:border-primary focus:outline-none"
                />
              </label>
              <label class="text-sm text-text-secondary">
                <span class="text-xs uppercase tracking-wide text-text-secondary/70">Wood cost</span>
                <input
                  v-model.number="troopForms[troop.id].wood_cost"
                  type="number"
                  min="0"
                  class="mt-1 w-full rounded-lg border border-secondary-700/40 bg-secondary-800/60 px-3 py-2 text-sm text-text-primary focus:border-primary focus:outline-none"
                />
              </label>
              <label class="text-sm text-text-secondary">
                <span class="text-xs uppercase tracking-wide text-text-secondary/70">Clay cost</span>
                <input
                  v-model.number="troopForms[troop.id].clay_cost"
                  type="number"
                  min="0"
                  class="mt-1 w-full rounded-lg border border-secondary-700/40 bg-secondary-800/60 px-3 py-2 text-sm text-text-primary focus:border-primary focus:outline-none"
                />
              </label>
              <label class="text-sm text-text-secondary">
                <span class="text-xs uppercase tracking-wide text-text-secondary/70">Iron cost</span>
                <input
                  v-model.number="troopForms[troop.id].iron_cost"
                  type="number"
                  min="0"
                  class="mt-1 w-full rounded-lg border border-secondary-700/40 bg-secondary-800/60 px-3 py-2 text-sm text-text-primary focus:border-primary focus:outline-none"
                />
              </label>
              <label class="text-sm text-text-secondary md:col-span-2">
                <span class="text-xs uppercase tracking-wide text-text-secondary/70">Requirements</span>
                <input
                  v-model="troopForms[troop.id].requirements"
                  type="text"
                  class="mt-1 w-full rounded-lg border border-secondary-700/40 bg-secondary-800/60 px-3 py-2 text-sm text-text-primary focus:border-primary focus:outline-none"
                  placeholder="barracks:1, smithy:2"
                />
              </label>
            </div>
            <div class="flex flex-wrap gap-2 pt-3">
              <button
                type="button"
                class="rounded-lg border border-primary/40 bg-primary/70 px-4 py-2 text-sm font-semibold text-white hover:bg-primary"
                @click="updateTroopDefinition(troop.id)"
              >
                Save troop
              </button>
              <button
                type="button"
                class="rounded-lg border border-secondary-700/40 bg-secondary-800/60 px-4 py-2 text-sm text-text-secondary hover:bg-secondary-700"
                @click="resetTroopForm(troop.id)"
              >
                Reset changes
              </button>
            </div>
          </template>
        </article>

        <article class="rounded-2xl border border-secondary-700/40 bg-secondary-900/70 px-5 py-5 space-y-4">
          <header>
            <h3 class="text-lg font-semibold text-text-primary">Create a new troop</h3>
            <p class="text-xs text-text-secondary/70">Define stats and requirements to introduce new unit types.</p>
          </header>
          <form class="grid gap-3 md:grid-cols-2" @submit.prevent="createTroopDefinition">
            <label class="text-sm text-text-secondary md:col-span-2">
              <span class="text-xs uppercase tracking-wide text-text-secondary/70">Name</span>
              <input
                v-model="newTroopForm.name"
                type="text"
                required
                class="mt-1 w-full rounded-lg border border-secondary-700/40 bg-secondary-800/60 px-3 py-2 text-sm text-text-primary focus:border-primary focus:outline-none"
              />
            </label>
            <label class="text-sm text-text-secondary">
              <span class="text-xs uppercase tracking-wide text-text-secondary/70">Attack</span>
              <input
                v-model.number="newTroopForm.attack"
                type="number"
                min="1"
                class="mt-1 w-full rounded-lg border border-secondary-700/40 bg-secondary-800/60 px-3 py-2 text-sm text-text-primary focus:border-primary focus:outline-none"
              />
            </label>
            <label class="text-sm text-text-secondary">
              <span class="text-xs uppercase tracking-wide text-text-secondary/70">Defense</span>
              <input
                v-model.number="newTroopForm.defense"
                type="number"
                min="1"
                class="mt-1 w-full rounded-lg border border-secondary-700/40 bg-secondary-800/60 px-3 py-2 text-sm text-text-primary focus:border-primary focus:outline-none"
              />
            </label>
            <label class="text-sm text-text-secondary">
              <span class="text-xs uppercase tracking-wide text-text-secondary/70">Speed</span>
              <input
                v-model.number="newTroopForm.speed"
                type="number"
                min="1"
                class="mt-1 w-full rounded-lg border border-secondary-700/40 bg-secondary-800/60 px-3 py-2 text-sm text-text-primary focus:border-primary focus:outline-none"
              />
            </label>
            <label class="text-sm text-text-secondary">
              <span class="text-xs uppercase tracking-wide text-text-secondary/70">Carry capacity</span>
              <input
                v-model.number="newTroopForm.carry_capacity"
                type="number"
                min="0"
                class="mt-1 w-full rounded-lg border border-secondary-700/40 bg-secondary-800/60 px-3 py-2 text-sm text-text-primary focus:border-primary focus:outline-none"
              />
            </label>
            <label class="text-sm text-text-secondary">
              <span class="text-xs uppercase tracking-wide text-text-secondary/70">Training time (s)</span>
              <input
                v-model.number="newTroopForm.training_time"
                type="number"
                min="1"
                class="mt-1 w-full rounded-lg border border-secondary-700/40 bg-secondary-800/60 px-3 py-2 text-sm text-text-primary focus:border-primary focus:outline-none"
              />
            </label>
            <label class="text-sm text-text-secondary">
              <span class="text-xs uppercase tracking-wide text-text-secondary/70">Wood cost</span>
              <input
                v-model.number="newTroopForm.wood_cost"
                type="number"
                min="0"
                class="mt-1 w-full rounded-lg border border-secondary-700/40 bg-secondary-800/60 px-3 py-2 text-sm text-text-primary focus:border-primary focus:outline-none"
              />
            </label>
            <label class="text-sm text-text-secondary">
              <span class="text-xs uppercase tracking-wide text-text-secondary/70">Clay cost</span>
              <input
                v-model.number="newTroopForm.clay_cost"
                type="number"
                min="0"
                class="mt-1 w-full rounded-lg border border-secondary-700/40 bg-secondary-800/60 px-3 py-2 text-sm text-text-primary focus:border-primary focus:outline-none"
              />
            </label>
            <label class="text-sm text-text-secondary">
              <span class="text-xs uppercase tracking-wide text-text-secondary/70">Iron cost</span>
              <input
                v-model.number="newTroopForm.iron_cost"
                type="number"
                min="0"
                class="mt-1 w-full rounded-lg border border-secondary-700/40 bg-secondary-800/60 px-3 py-2 text-sm text-text-primary focus:border-primary focus:outline-none"
              />
            </label>
            <label class="text-sm text-text-secondary md:col-span-2">
              <span class="text-xs uppercase tracking-wide text-text-secondary/70">Requirements</span>
              <input
                v-model="newTroopForm.requirements"
                type="text"
                class="mt-1 w-full rounded-lg border border-secondary-700/40 bg-secondary-800/60 px-3 py-2 text-sm text-text-primary focus:border-primary focus:outline-none"
                placeholder="barracks:1, smithy:2"
              />
            </label>
            <div class="flex flex-wrap gap-2 pt-3 md:col-span-2">
              <button
                type="submit"
                class="rounded-lg border border-primary/40 bg-primary/70 px-4 py-2 text-sm font-semibold text-white hover:bg-primary"
              >
                Create troop
              </button>
              <button
                type="button"
                class="rounded-lg border border-secondary-700/40 bg-secondary-800/60 px-4 py-2 text-sm text-text-secondary hover:bg-secondary-700"
                @click="resetNewTroopForm()"
              >
                Reset form
              </button>
            </div>
          </form>
          <p class="text-[11px] text-text-secondary/60">Common buildings: {{ knownTroopBuildings.join(', ') }}</p>
        </article>
      </div>
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
