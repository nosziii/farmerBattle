<script setup lang="ts">
import { computed, ref } from "vue";
import { useRouter } from "vue-router";
import { register as registerUser, useAuthState } from "../services/auth";
import { useI18n } from "../i18n";

const router = useRouter();

const form = ref({
  username: "",
  password: "",
  confirmPassword: "",
});

const submitting = ref(false);
const formError = ref<string | null>(null);

const { isLoading } = useAuthState();
const pending = computed(() => submitting.value || isLoading.value);
const { t } = useI18n();

const handleSubmit = async () => {
  if (pending.value) return;
  formError.value = null;

  if (form.value.password.length < 6) {
    formError.value = t("auth.register.validation.minLength");
    return;
  }

  if (form.value.password !== form.value.confirmPassword) {
    formError.value = t("auth.register.validation.mismatch");
    return;
  }

  submitting.value = true;
  try {
    await registerUser({
      username: form.value.username.trim(),
      password: form.value.password,
    });
    router.replace("/village");
  } catch (error: any) {
    formError.value = error?.response?.data?.detail ?? t("auth.register.errorGeneric");
  } finally {
    submitting.value = false;
  }
};
</script>

<template>
  <main class="flex flex-1 items-center justify-center overflow-y-auto px-4 py-12">
    <div class="w-full max-w-lg rounded-3xl border border-primary/30 bg-surface/80 p-8 shadow-2xl shadow-black/40 backdrop-blur">
      <div class="mb-6 text-center">
        <h2 class="text-3xl font-semibold text-text-primary">{{ t('auth.register.title') }}</h2>
        <p class="mt-2 text-sm text-text-secondary">
          {{ t('auth.register.subtitle') }}
        </p>
      </div>

      <form class="space-y-5" @submit.prevent="handleSubmit">
        <label class="block text-sm text-text-secondary">
          <span class="text-xs uppercase tracking-wide text-text-secondary/70">{{ t('auth.register.usernameLabel') }}</span>
          <input
            v-model="form.username"
            type="text"
            required
            minlength="3"
            class="mt-1 w-full rounded-xl border border-secondary-700/40 bg-secondary-800/60 px-3 py-2 text-sm text-text-primary shadow-inner shadow-black/20 focus:border-primary focus:outline-none"
            :placeholder="t('auth.register.usernamePlaceholder')"
          />
        </label>

        <div class="grid gap-4 md:grid-cols-2">
          <label class="block text-sm text-text-secondary">
            <span class="text-xs uppercase tracking-wide text-text-secondary/70">{{ t('auth.register.passwordLabel') }}</span>
            <input
              v-model="form.password"
              type="password"
              required
              minlength="6"
              class="mt-1 w-full rounded-xl border border-secondary-700/40 bg-secondary-800/60 px-3 py-2 text-sm text-text-primary shadow-inner shadow-black/20 focus:border-primary focus:outline-none"
              :placeholder="t('auth.register.passwordPlaceholder')"
            />
          </label>
          <label class="block text-sm text-text-secondary">
            <span class="text-xs uppercase tracking-wide text-text-secondary/70">{{ t('auth.register.confirmLabel') }}</span>
            <input
              v-model="form.confirmPassword"
              type="password"
              required
              class="mt-1 w-full rounded-xl border border-secondary-700/40 bg-secondary-800/60 px-3 py-2 text-sm text-text-primary shadow-inner shadow-black/20 focus:border-primary focus:outline-none"
              :placeholder="t('auth.register.confirmPlaceholder')"
            />
          </label>
        </div>

        <div
          v-if="formError"
          class="rounded-xl border border-red-500/40 bg-red-500/10 px-4 py-3 text-sm text-red-200"
        >
          {{ formError }}
        </div>

        <button
          type="submit"
          class="w-full rounded-xl border border-primary/40 bg-primary/80 px-4 py-2.5 text-sm font-semibold text-white shadow-lg shadow-primary/30 transition hover:bg-primary disabled:cursor-not-allowed disabled:opacity-60"
          :disabled="pending"
        >
          {{ pending ? t('auth.register.submitPending') : t('auth.register.submit') }}
        </button>
      </form>

      <p class="mt-6 text-center text-sm text-text-secondary">
        {{ t('auth.register.haveAccount') }}
        <router-link to="/login" class="text-primary-200 hover:text-primary-100">
          {{ t('auth.register.signInCta') }}
        </router-link>
      </p>
    </div>
  </main>
</template>
