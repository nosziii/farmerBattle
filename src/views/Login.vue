<script setup lang="ts">
import { computed, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { login, useAuthState } from "../services/auth";
import { useI18n } from "../i18n";

const router = useRouter();
const route = useRoute();
const credentials = ref({ username: "", password: "" });
const submitting = ref(false);
const formError = ref<string | null>(null);

const { authError, isLoading } = useAuthState();
const { t } = useI18n();

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
    formError.value = error?.response?.data?.detail ?? t("auth.login.errorInvalid");
  } finally {
    submitting.value = false;
  }
};
</script>

<template>
  <main class="flex flex-1 items-center justify-center overflow-y-auto px-4 py-12">
    <div class="w-full max-w-md rounded-3xl border border-secondary-700/40 bg-secondary-900/70 p-8 shadow-2xl shadow-black/40 backdrop-blur">
      <div class="mb-6 text-center">
        <h2 class="text-3xl font-semibold text-text-primary">{{ t('auth.login.title') }}</h2>
        <p class="mt-2 text-sm text-text-secondary">{{ t('auth.login.subtitle') }}</p>
      </div>
      <form class="space-y-5" @submit.prevent="handleSubmit">
        <label class="block text-sm text-text-secondary">
          <span class="text-xs uppercase tracking-wide text-text-secondary/70">{{ t('auth.login.usernameLabel') }}</span>
          <input
            v-model="credentials.username"
            type="text"
            required
            class="mt-1 w-full rounded-xl border border-secondary-700/40 bg-secondary-800/60 px-3 py-2 text-sm text-text-primary shadow-inner shadow-black/20 focus:border-primary focus:outline-none"
            :placeholder="t('auth.login.usernamePlaceholder')"
          />
        </label>
        <label class="block text-sm text-text-secondary">
          <span class="text-xs uppercase tracking-wide text-text-secondary/70">{{ t('auth.login.passwordLabel') }}</span>
          <input
            v-model="credentials.password"
            type="password"
            required
            class="mt-1 w-full rounded-xl border border-secondary-700/40 bg-secondary-800/60 px-3 py-2 text-sm text-text-primary shadow-inner shadow-black/20 focus:border-primary focus:outline-none"
            :placeholder="t('auth.login.passwordPlaceholder')"
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
          {{ pending ? t('auth.login.submitPending') : t('auth.login.submit') }}
        </button>
      </form>
      <p class="mt-6 text-center text-sm text-text-secondary">
        {{ t('auth.login.newHere') }}
        <router-link to="/register" class="text-primary-200 hover:text-primary-100">
          {{ t('auth.login.registerCta') }}
        </router-link>
      </p>
    </div>
  </main>
</template>
