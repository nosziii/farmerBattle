<script setup lang="ts">
import { computed, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { login, useAuthState } from "../services/auth";

const router = useRouter();
const route = useRoute();
const credentials = ref({ username: "", password: "" });
const submitting = ref(false);
const formError = ref<string | null>(null);

const { authError, isLoading } = useAuthState();

const pending = computed(() => submitting.value || isLoading.value);

const handleSubmit = async () => {
  if (pending.value) return;
  submitting.value = true;
  formError.value = null;
  try {
    await login({
      username: credentials.value.username.trim(),
      password: credentials.value.password,
    });
    const redirect = typeof route.query.redirect === "string" ? route.query.redirect : "/village";
    router.replace(redirect);
  } catch (error: any) {
    formError.value = error?.response?.data?.detail ?? "Unable to sign in with those credentials.";
  } finally {
    submitting.value = false;
  }
};
</script>

<template>
  <main class="flex flex-1 items-center justify-center overflow-y-auto px-4 py-12">
    <div class="w-full max-w-md rounded-3xl border border-secondary-700/40 bg-secondary-900/70 p-8 shadow-2xl shadow-black/40 backdrop-blur">
      <div class="mb-6 text-center">
        <h2 class="text-3xl font-semibold text-text-primary">Welcome back, Commander</h2>
        <p class="mt-2 text-sm text-text-secondary">Log in to continue building your dominion.</p>
      </div>
      <form class="space-y-5" @submit.prevent="handleSubmit">
        <label class="block text-sm text-text-secondary">
          <span class="text-xs uppercase tracking-wide text-text-secondary/70">Username</span>
          <input
            v-model="credentials.username"
            type="text"
            required
            class="mt-1 w-full rounded-xl border border-secondary-700/40 bg-secondary-800/60 px-3 py-2 text-sm text-text-primary shadow-inner shadow-black/20 focus:border-primary focus:outline-none"
            placeholder="Your commander name"
          />
        </label>
        <label class="block text-sm text-text-secondary">
          <span class="text-xs uppercase tracking-wide text-text-secondary/70">Password</span>
          <input
            v-model="credentials.password"
            type="password"
            required
            class="mt-1 w-full rounded-xl border border-secondary-700/40 bg-secondary-800/60 px-3 py-2 text-sm text-text-primary shadow-inner shadow-black/20 focus:border-primary focus:outline-none"
            placeholder="••••••••"
          />
        </label>
        <div
          v-if="formError || authError"
          class="rounded-xl border border-red-500/40 bg-red-500/10 px-4 py-3 text-sm text-red-200"
        >
          {{ formError ?? authError }}
        </div>
        <button
          type="submit"
          class="w-full rounded-xl border border-primary/40 bg-primary/80 px-4 py-2.5 text-sm font-semibold text-white shadow-lg shadow-primary/30 transition hover:bg-primary disabled:cursor-not-allowed disabled:opacity-60"
          :disabled="pending"
        >
          {{ pending ? "Signing in..." : "Sign in" }}
        </button>
      </form>
      <p class="mt-6 text-center text-sm text-text-secondary">
        New here?
        <router-link to="/register" class="text-primary-200 hover:text-primary-100">
          Create a village
        </router-link>
      </p>
    </div>
  </main>
</template>
