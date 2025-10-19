import { computed, ref } from "vue";
import axios from "axios";
import type { AuthCredentials, AuthResponse, AuthUser } from "../types/auth";

const API_BASE = "http://localhost:8000";
const TOKEN_STORAGE_KEY = "fb_auth_token";

const storedToken = typeof window !== "undefined" ? window.localStorage.getItem(TOKEN_STORAGE_KEY) : null;
const accessToken = ref<string | null>(storedToken);
const currentUser = ref<AuthUser | null>(null);
const isReady = ref(false);
const isLoading = ref(false);
const authError = ref<string | null>(null);

const applyAuthHeader = (token: string | null) => {
  if (token) {
    axios.defaults.headers.common.Authorization = `Bearer ${token}`;
  } else {
    delete axios.defaults.headers.common.Authorization;
  }
};

applyAuthHeader(accessToken.value);

const persistToken = (token: string | null) => {
  accessToken.value = token;
  if (typeof window === "undefined") {
    return;
  }
  if (token) {
    window.localStorage.setItem(TOKEN_STORAGE_KEY, token);
  } else {
    window.localStorage.removeItem(TOKEN_STORAGE_KEY);
  }
};

const fetchCurrentUser = async () => {
  if (!accessToken.value) {
    currentUser.value = null;
    return;
  }
  try {
    const { data } = await axios.get<AuthUser>(`${API_BASE}/auth/me`);
    currentUser.value = data;
  } catch (error: any) {
    currentUser.value = null;
    persistToken(null);
    applyAuthHeader(null);
    authError.value = error?.response?.data?.detail ?? "Session expired. Please sign in again.";
  }
};

export const ensureAuthReady = async () => {
  if (isReady.value) {
    return;
  }
  isLoading.value = true;
  await fetchCurrentUser();
  isReady.value = true;
  isLoading.value = false;
};

const handleAuthSuccess = (response: AuthResponse) => {
  persistToken(response.access_token);
  applyAuthHeader(response.access_token);
  currentUser.value = response.user;
  authError.value = null;
};

export const login = async (credentials: AuthCredentials) => {
  isLoading.value = true;
  authError.value = null;
  try {
    const { data } = await axios.post<AuthResponse>(`${API_BASE}/auth/login`, {
      username: credentials.username,
      password: credentials.password,
    });
    handleAuthSuccess(data);
    return data.user;
  } catch (error: any) {
    authError.value = error?.response?.data?.detail ?? "Invalid credentials.";
    throw error;
  } finally {
    isLoading.value = false;
  }
};

export const register = async (credentials: AuthCredentials) => {
  isLoading.value = true;
  authError.value = null;
  try {
    const { data } = await axios.post<AuthResponse>(`${API_BASE}/auth/register`, {
      username: credentials.username,
      password: credentials.password,
    });
    handleAuthSuccess(data);
    return data.user;
  } catch (error: any) {
    authError.value = error?.response?.data?.detail ?? "Registration failed.";
    throw error;
  } finally {
    isLoading.value = false;
  }
};

export const signOut = () => {
  persistToken(null);
  applyAuthHeader(null);
  currentUser.value = null;
};

export const useAuthState = () => ({
  accessToken,
  currentUser,
  isReady,
  isLoading,
  authError,
  isAuthenticated: computed(() => !!currentUser.value),
  isAdmin: computed(() => !!currentUser.value?.is_admin),
});

export { currentUser as authUser, accessToken as authToken };
