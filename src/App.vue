<template>
  <div class="flex min-h-screen flex-col bg-background text-text-primary">
    <header
      class="sticky top-0 z-50 h-16 border-b border-secondary/40 bg-surface/80 backdrop-blur-md"
    >
      <div class="mx-auto flex h-full w-full max-w-7xl items-center justify-between px-4">
        <div class="flex items-center gap-3">
          <span class="text-2xl">🌾</span>
          <div>
            <h1 class="text-lg font-semibold">Farmer Battle</h1>
            <p class="text-xs text-text-secondary/80">Build. Train. Conquer.</p>
          </div>
        </div>
        <nav class="hidden items-center gap-4 text-sm text-text-secondary md:flex">
          <router-link
            to="/"
            class="transition hover:text-text-primary"
            active-class="text-text-primary font-semibold"
          >
            Home
          </router-link>
          <router-link
            to="/village"
            v-if="isAuthenticated"
            class="transition hover:text-text-primary"
            active-class="text-text-primary font-semibold"
          >
            My Village
          </router-link>
          <router-link
            to="/leaderboard"
            class="transition hover:text-text-primary"
            active-class="text-text-primary font-semibold"
          >
            Leaderboard
          </router-link>
          <router-link
            to="/info"
            class="transition hover:text-text-primary"
            active-class="text-text-primary font-semibold"
          >
            Info
          </router-link>
          <router-link
            v-if="isAdmin"
            to="/admin"
            class="transition hover:text-text-primary"
            active-class="text-text-primary font-semibold"
          >
            Admin
          </router-link>
        </nav>
        <div class="flex items-center gap-3 text-sm">
          <template v-if="isAuthenticated">
            <div class="hidden flex-col text-right md:flex">
              <span class="font-semibold text-text-primary">{{ currentUser?.username }}</span>
              <span class="text-xs text-text-secondary/70">Commander</span>
            </div>
            <button
              type="button"
              class="rounded-lg border border-secondary/40 bg-secondary-800/60 px-3 py-2 text-sm font-medium hover:bg-secondary-800"
              @click="handleSignOut"
            >
              Sign out
            </button>
          </template>
          <template v-else>
            <router-link
              to="/login"
              class="rounded-lg border border-primary/50 bg-primary/70 px-3 py-2 text-sm font-semibold text-white shadow hover:bg-primary"
            >
              Sign in
            </router-link>
            <router-link
              to="/register"
              class="hidden rounded-lg border border-secondary/40 px-3 py-2 text-sm text-text-secondary transition hover:text-text-primary md:inline-block"
            >
              Create account
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

const router = useRouter();
const { currentUser, isAuthenticated, isAdmin } = useAuthState();

onMounted(async () => {
  await ensureAuthReady();
});

const handleSignOut = () => {
  signOut();
  router.push("/login");
};

</script>
