<template>
  <div class="flex min-h-screen flex-col bg-background text-text-primary">
    <header
      class="sticky top-0 z-50 h-16 border-b border-secondary/40 bg-surface/80 backdrop-blur-md"
    >
      <div class="mx-auto flex h-full w-full max-w-7xl items-center justify-between px-4">
        <div class="flex items-center gap-3">
          <span class="text-2xl">🌾</span>
          <div>
            <h1 class="text-lg font-semibold">{{ t('header.appName') }}</h1>
            <p class="text-xs text-text-secondary/80">{{ t('header.tagline') }}</p>
          </div>
        </div>
        <nav class="hidden items-center gap-4 text-sm text-text-secondary md:flex">
          <router-link
            to="/"
            class="transition hover:text-text-primary"
            active-class="text-text-primary font-semibold"
          >
            {{ t('nav.home') }}
          </router-link>
          <router-link
            to="/village"
            v-if="isAuthenticated"
            class="transition hover:text-text-primary"
            active-class="text-text-primary font-semibold"
          >
            {{ t('nav.village') }}
          </router-link>
          <router-link
            to="/leaderboard"
            class="transition hover:text-text-primary"
            active-class="text-text-primary font-semibold"
          >
            {{ t('nav.leaderboard') }}
          </router-link>
          <router-link
            to="/info"
            class="transition hover:text-text-primary"
            active-class="text-text-primary font-semibold"
          >
            {{ t('nav.info') }}
          </router-link>
          <router-link
            v-if="isAdmin"
            to="/admin"
            class="transition hover:text-text-primary"
            active-class="text-text-primary font-semibold"
          >
            {{ t('nav.admin') }}
          </router-link>
        </nav>
        <div class="hidden items-center gap-2 md:flex">
          <label class="text-xs uppercase tracking-wide text-text-secondary/70" :for="languageSelectId">
            {{ t('header.languageLabel') }}
          </label>
          <select
            :id="languageSelectId"
            class="rounded border border-secondary/40 bg-secondary-900/80 px-2 py-1 text-sm text-text-primary focus:border-primary focus:outline-none"
            :value="locale"
            @change="setLocale(($event.target as HTMLSelectElement).value as Locale)"
          >
            <option v-for="available in availableLocales" :key="available" :value="available">
              {{ t(`header.languages.${available}`) }}
            </option>
          </select>
        </div>
        <div class="flex items-center gap-3 text-sm">
          <template v-if="isAuthenticated">
            <div class="hidden flex-col text-right md:flex">
              <span class="font-semibold text-text-primary">{{ currentUser?.username }}</span>
              <span class="text-xs text-text-secondary/70">{{ t('header.roleCommander') }}</span>
            </div>
            <button
              type="button"
              class="rounded-lg border border-secondary/40 bg-secondary-800/60 px-3 py-2 text-sm font-medium hover:bg-secondary-800"
              @click="handleSignOut"
            >
              {{ t('header.signOut') }}
            </button>
          </template>
          <template v-else>
            <router-link
              to="/login"
              class="rounded-lg border border-primary/50 bg-primary/70 px-3 py-2 text-sm font-semibold text-white shadow hover:bg-primary"
            >
              {{ t('header.signIn') }}
            </router-link>
            <router-link
              to="/register"
              class="hidden rounded-lg border border-secondary/40 px-3 py-2 text-sm text-text-secondary transition hover:text-text-primary md:inline-block"
            >
              {{ t('header.createAccount') }}
            </router-link>
          </template>
        </div>
      </div>
    </header>

    <div class="flex flex-1">
      <SidebarMenu v-if="isAuthenticated" />
      <main class="flex-1">
        <router-view />
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from "vue";
import { useRouter } from "vue-router";
import SidebarMenu from "./components/sidebar/SidebarMenu.vue";
import { ensureAuthReady, signOut, useAuthState } from "./services/auth";
import { useI18n, type Locale } from "./i18n";

const router = useRouter();
const { currentUser, isAuthenticated, isAdmin } = useAuthState();
const { t, locale, setLocale, availableLocales } = useI18n();

const languageSelectId = `language-select-${Math.random().toString(36).slice(2)}`;

onMounted(async () => {
  await ensureAuthReady();
});

const handleSignOut = () => {
  signOut();
  router.push("/login");
};

</script>
