<template>
  <div class="min-h-screen bg-background text-text-primary flex flex-col">
    <!-- Felső header (maradhat nálad így is) -->
    <header
      class="h-14 flex items-center justify-between px-4 border-b border-secondary/40 bg-surface/80 backdrop-blur"
    >
      <div class="flex items-center gap-3">
        <span class="text-xl">🌾</span>
        <h1 class="font-semibold">Farmer Battle</h1>
      </div>
      <nav class="flex items-center gap-4 text-sm text-text-secondary">
        <router-link
          to="/about"
          class="transition hover:text-text-primary"
          active-class="text-text-primary font-semibold"
        >
          About
        </router-link>
        <router-link
          to="/storage"
          class="transition hover:text-text-primary"
          active-class="text-text-primary font-semibold"
        >
          Storage
        </router-link>
        <router-link
          to="/info"
          class="transition hover:text-text-primary"
          active-class="text-text-primary font-semibold"
        >
          Info
        </router-link>
        <router-link
          to="/admin"
          class="transition hover:text-text-primary"
          active-class="text-text-primary font-semibold"
        >
          Admin
        </router-link>
      </nav>
    </header>

    <!-- Tartalom: bal oldalt a Sidebar, mellette a fő tartalom -->
    <div class="flex flex-1">
      <SidebarMenu />
      <main class="flex-1">
        <router-view />
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import SidebarMenu from "./components/sidebar/SidebarMenu.vue";
</script>
