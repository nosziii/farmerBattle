<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import axios from "axios";
import {
  API_BASE,
  activeVillageId,
  ensureActiveVillageId,
  refreshVillages,
  setActiveVillageId,
  villages,
  villagesLoading,
} from "../../services/villageState";
import { useAuthState } from "../../services/auth";

const isRefreshing = ref(false);
const isCreating = ref(false);
const creationName = ref("");
const feedback = ref<string | null>(null);
const feedbackType = ref<"success" | "error" | "info">("info");
const { isAdmin } = useAuthState();

const sortedVillages = computed(() => {
  return [...villages.value].sort((a, b) => a.id - b.id);
});

const activeVillageName = computed(() => {
  const match = villages.value.find((entry) => entry.id === activeVillageId.value);
  return match?.name ?? "—";
});

const showFeedback = (message: string | null, type: "success" | "error" | "info" = "info") => {
  feedback.value = message;
  feedbackType.value = type;
  if (message) {
    window.setTimeout(() => {
      if (feedback.value === message) {
        feedback.value = null;
      }
    }, 2500);
  }
};

const handleSelect = (event: Event) => {
  const target = event.target as HTMLSelectElement | null;
  if (!target) return;
  const value = Number(target.value);
  if (!Number.isFinite(value)) return;
  setActiveVillageId(value);
};

const reload = async () => {
  if (isRefreshing.value) return;
  isRefreshing.value = true;
  try {
    await refreshVillages(activeVillageId.value);
    showFeedback("Villages refreshed", "success");
  } catch (error) {
    console.error("[VillageSwitcher] Failed to refresh villages", error);
    showFeedback("Could not refresh villages", "error");
  } finally {
    isRefreshing.value = false;
  }
};

const createVillage = async () => {
  if (!isAdmin.value) {
    showFeedback("Only admins can create villages", "error");
    return;
  }
  if (isCreating.value) return;
  const name = creationName.value.trim() || `New Village #${sortedVillages.value.length + 1}`;
  isCreating.value = true;
  showFeedback(null);
  try {
    const { data } = await axios.post(`${API_BASE}/villages/`, { name });
    const createdId = Number(data?.id);
    await refreshVillages(createdId);
    if (Number.isFinite(createdId)) {
      setActiveVillageId(createdId);
    }
    creationName.value = "";
    showFeedback("Village created", "success");
  } catch (error) {
    console.error("[VillageSwitcher] Failed to create village", error);
    showFeedback("Could not create village", "error");
  } finally {
    isCreating.value = false;
  }
};

onMounted(async () => {
  try {
    await ensureActiveVillageId();
  } catch (error) {
    console.warn("[VillageSwitcher] Failed to resolve active village", error);
  }
});
</script>

<template>
  <section class="rounded-xl border border-secondary-700/40 bg-secondary-900/60 px-4 py-3 space-y-3">
    <header class="flex items-center justify-between gap-2">
      <div>
        <p class="text-xs uppercase tracking-wide text-text-secondary/70">Active village</p>
        <p class="text-sm font-semibold text-text-primary">{{ activeVillageName }}</p>
      </div>
      <button
        type="button"
        class="rounded-md border border-secondary-700/40 bg-secondary-800/60 px-3 py-1 text-xs text-text-secondary hover:bg-secondary-800 disabled:opacity-60"
        :disabled="isRefreshing || villagesLoading"
        @click="reload"
      >
        {{ isRefreshing || villagesLoading ? 'Refreshing…' : 'Refresh list' }}
      </button>
    </header>

    <div class="space-y-2">
      <select
        class="w-full rounded-lg border border-secondary-700/40 bg-secondary-800/60 px-3 py-2 text-sm text-text-primary focus:outline-none focus:border-primary disabled:opacity-60"
        :value="activeVillageId ?? ''"
        :disabled="villagesLoading || !sortedVillages.length"
        @change="handleSelect"
      >
        <option value="" disabled>Select a village</option>
        <option
          v-for="village in sortedVillages"
          :key="village.id"
          :value="village.id"
        >
          {{ village.name }} (#{{ village.id }})
        </option>
      </select>

      <div
        v-if="isAdmin"
        class="flex flex-col gap-2 sm:flex-row sm:items-center"
      >
        <input
          v-model="creationName"
          type="text"
          placeholder="Village name"
          class="flex-1 rounded-lg border border-secondary-700/40 bg-secondary-800/60 px-3 py-2 text-sm text-text-primary focus:outline-none focus:border-primary"
        />
        <button
          type="button"
          class="rounded-lg border border-primary/40 bg-primary/70 px-4 py-2 text-sm font-semibold text-white hover:bg-primary disabled:opacity-60"
          :disabled="isCreating"
          @click="createVillage"
        >
          {{ isCreating ? 'Creating...' : 'Add village' }}
        </button>
      </div>
    </div>

    <p
      v-if="feedback"
      class="text-xs"
      :class="{
        'text-emerald-300': feedbackType === 'success',
        'text-red-300': feedbackType === 'error',
        'text-text-secondary': feedbackType === 'info',
      }"
    >
      {{ feedback }}
    </p>
  </section>
</template>
