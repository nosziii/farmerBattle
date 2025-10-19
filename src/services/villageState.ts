import { ref, watch } from "vue";
import axios from "axios";
import { authUser } from "./auth";

export const API_BASE = "http://localhost:8000/api";

const STORAGE_PREFIX = "fb_active_village_id";
const activeVillageId = ref<number | null>(null);

let ensurePromise: Promise<number> | null = null;

const storageKeyForUser = (userId: number | null | undefined) =>
  userId ? `${STORAGE_PREFIX}_${userId}` : STORAGE_PREFIX;

const loadStoredVillageId = (userId: number | null | undefined): number | null => {
  if (!userId || typeof window === "undefined") {
    return null;
  }
  const raw = window.localStorage.getItem(storageKeyForUser(userId));
  if (!raw) {
    return null;
  }
  const parsed = Number.parseInt(raw, 10);
  if (Number.isNaN(parsed) || parsed <= 0) {
    window.localStorage.removeItem(storageKeyForUser(userId));
    return null;
  }
  return parsed;
};

const storeVillageId = (userId: number | null | undefined, villageId: number | null) => {
  if (typeof window === "undefined") {
    return;
  }
  const storageKey = storageKeyForUser(userId ?? null);
  if (!villageId) {
    window.localStorage.removeItem(storageKey);
  } else {
    window.localStorage.setItem(storageKey, villageId.toString());
  }
};

export const setActiveVillageId = (id: number) => {
  activeVillageId.value = id;
  storeVillageId(authUser.value?.id ?? null, id);
};

export const clearActiveVillageId = () => {
  activeVillageId.value = null;
  storeVillageId(authUser.value?.id ?? null, null);
};

export const ensureActiveVillageId = async (): Promise<number> => {
  if (activeVillageId.value !== null) {
    return activeVillageId.value;
  }

  const currentUser = authUser.value;
  if (!currentUser) {
    throw new Error("Not authenticated");
  }

  if (ensurePromise) {
    return ensurePromise;
  }

  ensurePromise = (async () => {
    const stored = loadStoredVillageId(currentUser.id);
    if (stored) {
      activeVillageId.value = stored;
      return stored;
    }

    const listResponse = await axios.get(`${API_BASE}/villages/`);
    const villages = Array.isArray(listResponse.data) ? listResponse.data : [];
    if (villages.length > 0) {
      const first = villages[0];
      setActiveVillageId(first.id);
      return first.id;
    }

    const createResponse = await axios.post(`${API_BASE}/villages/`, {
      name: `${currentUser.username}'s Village`,
    });
    const createdId = createResponse.data?.id;
    if (!createdId) {
      throw new Error("Failed to initialise a default village");
    }
    setActiveVillageId(createdId);
    return createdId;
  })();

  try {
    return await ensurePromise;
  } finally {
    ensurePromise = null;
  }
};

export { activeVillageId };

watch(
  authUser,
  (newUser, oldUser) => {
    if (newUser?.id === oldUser?.id) {
      return;
    }
    ensurePromise = null;
    activeVillageId.value = null;
    if (newUser) {
      const stored = loadStoredVillageId(newUser.id);
      if (stored) {
        activeVillageId.value = stored;
      }
    }
  },
  { immediate: true }
);
