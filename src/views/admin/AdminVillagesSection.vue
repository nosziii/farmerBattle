<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue';
import axios from 'axios';
import type {
  AdminAssignTileRequest,
  AdminVillageCreate,
  AdminVillageDetail,
  AdminVillageSummary,
  AdminVillageTroop,
  AdminVillageTroopUpdatePayload,
  AdminVillageUpdate,
  AdminTroop,
} from '../../types/admin';

const props = defineProps<{
  apiBase: string;
  active: boolean;
  selectedUserId: number | null;
  ensureAdminAccess: () => boolean;
  setError: (message: string | null) => void;
  setSuccess: (message: string | null) => void;
  sectionLoaded: boolean;
  setSectionLoaded: (loaded: boolean) => void;
  troopCatalogue: AdminTroop[];
}>();

const villages = ref<AdminVillageSummary[]>([]);
const villageDetail = ref<AdminVillageDetail | null>(null);
const selectedVillageId = ref<number | null>(null);

const villageForm = ref({
  name: '',
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
const newVillageForm = ref<AdminVillageCreate>({ user_id: 0, name: '' });

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

type ResourceKey = (typeof resourceFields)[number]['key'];
type BuildingKey = (typeof buildingFields)[number]['key'];

const isListLoading = ref(false);
const isSavingVillage = ref(false);
const isAssigningTile = ref(false);
const isSavingTroops = ref(false);

const villageTroops = ref<AdminVillageTroop[]>([]);
const troopAssignments = ref<Record<number, number>>({});

const filteredVillages = computed(() => {
  if (!props.selectedUserId) {
    return villages.value;
  }
  return villages.value.filter((village) => village.user_id === props.selectedUserId);
});

const notifyError = (message: string | null) => {
  props.setError(message);
};

const notifySuccess = (message: string | null) => {
  props.setSuccess(message);
};

const adjustResource = (key: ResourceKey, delta: number) => {
  const current = Number((villageForm.value as any)[key] ?? 0);
  const next = Math.max(0, Math.round((current + delta) * 100) / 100);
  (villageForm.value as any)[key] = next;
};

const adjustBuildingLevel = (key: BuildingKey, delta: number) => {
  const current = Number((villageForm.value as any)[key] ?? 1);
  const next = Math.max(1, current + delta);
  (villageForm.value as any)[key] = next;
};

const hydrateVillageForm = (detail: AdminVillageDetail) => {
  villageForm.value = {
    name: detail.name,
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

const syncTroopAssignments = () => {
  const assignments: Record<number, number> = {};
  props.troopCatalogue.forEach((troop) => {
    const existing = villageTroops.value.find((entry) => entry.troop_id === troop.id);
    assignments[troop.id] = existing ? existing.quantity : 0;
  });
  troopAssignments.value = assignments;
};

const ensureAdmin = () => {
  if (!props.ensureAdminAccess()) {
    return false;
  }
  notifyError(null);
  return true;
};

const fetchVillageDetail = async (villageId: number | null) => {
  if (!villageId || !ensureAdmin()) return;
  try {
    const { data } = await axios.get<AdminVillageDetail>(`${props.apiBase}/admin/villages/${villageId}`);
    villageDetail.value = data;
    hydrateVillageForm(data);
    assignForm.value = {
      x: data.tile?.x ?? null,
      y: data.tile?.y ?? null,
      force: false,
    };
  } catch (err: any) {
    notifyError(err.response?.data?.detail ?? 'Failed to load village detail.');
  }
};

const fetchVillageTroops = async (villageId: number | null) => {
  if (!villageId || !ensureAdmin()) return;
  try {
    const { data } = await axios.get<AdminVillageTroop[]>(`${props.apiBase}/admin/villages/${villageId}/troops`);
    villageTroops.value = data;
    syncTroopAssignments();
  } catch (err: any) {
    notifyError(err.response?.data?.detail ?? 'Failed to load village troops.');
  }
};

const selectDefaultVillage = () => {
  const available = filteredVillages.value;
  if (!available.length) {
    selectedVillageId.value = null;
    villageDetail.value = null;
    villageTroops.value = [];
    troopAssignments.value = {};
    return;
  }
  if (!selectedVillageId.value || !available.some((village) => village.id === selectedVillageId.value)) {
    selectedVillageId.value = available[0].id;
  }
};

const fetchVillages = async (refreshDetail = false) => {
  if (!ensureAdmin()) return;
  isListLoading.value = true;
  try {
    const { data } = await axios.get<AdminVillageSummary[]>(`${props.apiBase}/admin/villages`);
    villages.value = data;
    selectDefaultVillage();
    if (refreshDetail && selectedVillageId.value) {
      await Promise.all([fetchVillageDetail(selectedVillageId.value), fetchVillageTroops(selectedVillageId.value)]);
    }
    props.setSectionLoaded(true);
  } catch (err: any) {
    notifyError(err.response?.data?.detail ?? 'Failed to fetch villages.');
  } finally {
    isListLoading.value = false;
  }
};

const saveVillage = async () => {
  if (!selectedVillageId.value || !ensureAdmin()) return;
  isSavingVillage.value = true;
  const payload: AdminVillageUpdate = {
    name: villageForm.value.name,
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
      `${props.apiBase}/admin/villages/${selectedVillageId.value}`,
      payload
    );
    villageDetail.value = data;
    hydrateVillageForm(data);
    notifySuccess('Village updated');
    await fetchVillages();
  } catch (err: any) {
    notifyError(err.response?.data?.detail ?? 'Failed to update village.');
  } finally {
    isSavingVillage.value = false;
  }
};

const assignVillageTile = async () => {
  if (!selectedVillageId.value || !ensureAdmin()) return;
  if (assignForm.value.x == null || assignForm.value.y == null) {
    notifyError('Please provide tile coordinates.');
    return;
  }
  isAssigningTile.value = true;
  const payload: AdminAssignTileRequest = {
    village_id: selectedVillageId.value,
    x: Number(assignForm.value.x),
    y: Number(assignForm.value.y),
    force: !!assignForm.value.force,
  };
  try {
    await axios.post(`${props.apiBase}/admin/map/assign`, payload);
    notifySuccess('Village assigned to tile');
    await Promise.all([
      fetchVillageDetail(selectedVillageId.value),
      fetchVillages(),
    ]);
  } catch (err: any) {
    notifyError(err.response?.data?.detail ?? 'Failed to assign tile.');
  } finally {
    isAssigningTile.value = false;
  }
};

const createVillage = async () => {
  if (!ensureAdmin()) return;
  if (!newVillageForm.value.user_id || !newVillageForm.value.name.trim()) {
    notifyError('Owner and village name are required.');
    return;
  }
  try {
    await axios.post(`${props.apiBase}/admin/villages`, newVillageForm.value);
    notifySuccess('Village created');
    newVillageForm.value = { user_id: props.selectedUserId ?? 0, name: '' };
    props.setSectionLoaded(false);
    await fetchVillages(true);
  } catch (err: any) {
    notifyError(err.response?.data?.detail ?? 'Failed to create village.');
  }
};

const saveTroopAssignments = async () => {
  if (!selectedVillageId.value || !ensureAdmin()) return;
  const entries = Object.entries(troopAssignments.value).map(([troopId, quantity]) => ({
    troop_id: Number(troopId),
    quantity: Math.max(0, Math.floor(Number(quantity) || 0)),
  }));
  const payload: AdminVillageTroopUpdatePayload = { troops: entries };
  isSavingTroops.value = true;
  try {
    const { data } = await axios.put<AdminVillageTroop[]>(
      `${props.apiBase}/admin/villages/${selectedVillageId.value}/troops`,
      payload
    );
    villageTroops.value = data;
    syncTroopAssignments();
    notifySuccess('Troop garrison updated');
  } catch (err: any) {
    notifyError(err.response?.data?.detail ?? 'Failed to update troops.');
  } finally {
    isSavingTroops.value = false;
  }
};

const ensureLoaded = async () => {
  if (!props.sectionLoaded) {
    await fetchVillages(true);
  } else if (selectedVillageId.value) {
    await Promise.all([
      fetchVillageDetail(selectedVillageId.value),
      fetchVillageTroops(selectedVillageId.value),
    ]);
  }
};

const reload = async () => {
  props.setSectionLoaded(false);
  await fetchVillages(true);
};

watch(
  () => props.selectedUserId,
  () => {
    newVillageForm.value.user_id = props.selectedUserId ?? 0;
    selectDefaultVillage();
  }
);

watch(selectedVillageId, async (villageId) => {
  if (!props.active || !villageId) {
    return;
  }
  await Promise.all([fetchVillageDetail(villageId), fetchVillageTroops(villageId)]);
});

watch(
  () => props.troopCatalogue,
  () => {
    if (villageDetail.value) {
      syncTroopAssignments();
    }
  },
  { deep: true }
);

watch(
  () => props.active,
  async (active) => {
    if (active) {
      await ensureLoaded();
    }
  }
);

onMounted(async () => {
  newVillageForm.value.user_id = props.selectedUserId ?? 0;
  if (props.active) {
    await ensureLoaded();
  }
});

defineExpose({ reload, ensureLoaded });
</script>

<template>
  <section v-if="active" class="space-y-6">
    <div class="grid gap-6 lg:grid-cols-2">
      <div class="rounded-2xl border border-secondary-700/40 bg-secondary-900/60 px-6 py-5 space-y-4">
        <header class="flex items-center justify-between">
          <h2 class="text-xl font-semibold text-text-primary">Villages</h2>
          <span class="text-xs text-text-secondary/70">{{ villages.length }} total</span>
        </header>

        <div v-if="isListLoading" class="py-10 text-center text-text-secondary">
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

      <div
        v-if="villageDetail"
        class="rounded-2xl border border-secondary-700/40 bg-secondary-900/60 px-6 py-5 space-y-5"
      >
        <header class="flex items-center justify-between">
          <div>
            <h2 class="text-xl font-semibold text-text-primary">{{ villageForm.name || villageDetail.name }}</h2>
            <p class="text-xs text-text-secondary">Owner: {{ villageDetail.user_name }}</p>
          </div>
          <span class="text-xs text-text-secondary/70">
            Tile: {{ villageDetail.tile ? `${villageDetail.tile.x}|${villageDetail.tile.y}` : 'Unassigned' }}
          </span>
        </header>

        <div class="space-y-6">
          <div class="grid gap-4 md:grid-cols-2">
            <label class="text-sm text-text-secondary md:col-span-2">
              <span class="text-xs uppercase tracking-wide text-text-secondary/70">Village name</span>
              <input
                v-model="villageForm.name"
                type="text"
                class="mt-1 w-full rounded-lg border border-secondary-700/40 bg-secondary-800/60 px-3 py-2 text-sm text-text-primary focus:outline-none focus:border-primary"
              />
            </label>
          </div>

          <div class="grid gap-6 md:grid-cols-2">
            <div class="space-y-3">
              <h3 class="text-sm font-semibold text-text-primary uppercase tracking-wide">Resources</h3>
              <div class="space-y-3">
                <div v-for="field in resourceFields" :key="field.key" class="text-sm text-text-secondary">
                  <span class="block text-xs uppercase tracking-wide text-text-secondary/70">{{ field.label }}</span>
                  <div class="mt-1 flex items-center gap-2">
                    <input
                      v-model.number="(villageForm as any)[field.key]"
                      type="number"
                      min="0"
                      class="h-9 flex-1 rounded-lg border border-secondary-700/40 bg-secondary-800/60 px-3 text-sm text-text-primary focus:outline-none focus:border-primary"
                    />
                    <div class="flex gap-1">
                      <button
                        v-for="preset in [100, 1000, 10000]"
                        :key="preset"
                        type="button"
                        class="rounded-md border border-secondary-700/40 bg-secondary-800/80 px-2 py-1 text-xs text-text-secondary hover:bg-secondary-800"
                        @click="adjustResource(field.key, preset)"
                      >
                        +{{ preset }}
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div class="space-y-3">
              <h3 class="text-sm font-semibold text-text-primary uppercase tracking-wide">Building levels</h3>
              <div class="space-y-3">
                <div v-for="field in buildingFields" :key="field.key" class="text-sm text-text-secondary">
                  <span class="block text-xs uppercase tracking-wide text-text-secondary/70">{{ field.label }}</span>
                  <div class="mt-1 flex items-center gap-2">
                    <input
                      v-model.number="(villageForm as any)[field.key]"
                      type="number"
                      min="1"
                      class="h-9 w-20 rounded-lg border border-secondary-700/40 bg-secondary-800/60 px-3 text-sm text-text-primary focus:outline-none focus:border-primary"
                    />
                    <div class="flex gap-1">
                      <button
                        v-for="preset in [1, 5]"
                        :key="preset"
                        type="button"
                        class="rounded-md border border-secondary-700/40 bg-secondary-800/80 px-2 py-1 text-xs text-text-secondary hover:bg-secondary-800"
                        @click="adjustBuildingLevel(field.key, preset)"
                      >
                        +{{ preset }}
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <footer class="flex flex-wrap justify-between gap-3 border-t border-secondary-700/40 pt-4">
            <button
              type="button"
              class="rounded-lg border border-primary/40 bg-primary/70 px-4 py-2 text-sm font-semibold text-white hover:bg-primary"
              :disabled="isSavingVillage"
              @click="saveVillage"
            >
              {{ isSavingVillage ? 'Saving...' : 'Save village' }}
            </button>
            <button
              type="button"
              class="rounded-lg border border-secondary-700/60 bg-secondary-800/60 px-4 py-2 text-sm text-text-secondary hover:bg-secondary-800"
              @click="() => hydrateVillageForm(villageDetail!)"
            >
              Reset changes
            </button>
          </footer>
        </div>
      </div>

      <div
        v-else
        class="rounded-2xl border border-secondary-700/40 bg-secondary-900/60 px-6 py-5 text-center text-sm text-text-secondary"
      >
        Select a village to view its details.
      </div>
    </div>

    <div
      v-if="villageDetail"
      class="grid gap-6 lg:grid-cols-2"
    >
      <section class="rounded-2xl border border-secondary-700/40 bg-secondary-900/60 px-6 py-5 space-y-4">
        <header>
          <h3 class="text-lg font-semibold text-text-primary">Assign to tile</h3>
          <p class="text-sm text-text-secondary">Set the map coordinates for this village.</p>
        </header>

        <form class="grid gap-4 md:grid-cols-2" @submit.prevent="assignVillageTile">
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
          <label class="flex items-center gap-2 text-sm text-text-secondary md:col-span-2">
            <input type="checkbox" v-model="assignForm.force" />
            Force override
          </label>
          <button
            type="submit"
            class="rounded-lg border border-emerald-500/40 bg-emerald-500/70 px-4 py-2 text-sm font-semibold text-white hover:bg-emerald-500 disabled:opacity-60"
            :disabled="isAssigningTile"
          >
            {{ isAssigningTile ? 'Assigning...' : 'Assign tile' }}
          </button>
        </form>
      </section>

      <section class="rounded-2xl border border-secondary-700/40 bg-secondary-900/60 px-6 py-5 space-y-4">
        <header>
          <h3 class="text-lg font-semibold text-text-primary">Troop garrison</h3>
          <p class="text-sm text-text-secondary">Directly manage troop quantities (instant assignment for testing).</p>
        </header>

        <div class="space-y-3 max-h-72 overflow-y-auto pr-1">
          <div
            v-for="troop in troopCatalogue"
            :key="troop.id"
            class="flex items-center justify-between gap-3 rounded-lg border border-secondary-700/40 bg-secondary-800/50 px-3 py-2 text-sm"
          >
            <div>
              <p class="font-semibold text-text-primary">{{ troop.name }}</p>
              <p class="text-xs text-text-secondary/70">
                Attack {{ troop.attack }} • Defense {{ troop.defense }} • Speed {{ troop.speed }}
              </p>
            </div>
            <input
              v-model.number="troopAssignments[troop.id]"
              type="number"
              min="0"
              class="h-9 w-24 rounded-lg border border-secondary-700/40 bg-secondary-900/60 px-3 text-sm text-text-primary focus:outline-none focus:border-primary"
            />
          </div>
        </div>

        <button
          type="button"
          class="rounded-lg border border-primary/40 bg-primary/70 px-4 py-2 text-sm font-semibold text-white hover:bg-primary disabled:opacity-60"
          :disabled="isSavingTroops"
          @click="saveTroopAssignments"
        >
          {{ isSavingTroops ? 'Saving troops...' : 'Apply troop changes' }}
        </button>
      </section>
    </div>
  </section>
</template>
