<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from "vue";
import axios from "axios";
import ResourcePill from "./ResourcePill.vue";
import ActionBtn from "./ActionBtn.vue";
import NavGroup from "./NavGroup.vue";
import NavItem from "./NavItem.vue";
import {
  API_BASE,
  activeVillageId,
  ensureActiveVillageId,
} from "../../services/villageState";
import { useI18n } from "../../i18n";

/** Compact mód tárolása */
const isCompact = ref(localStorage.getItem("fb_sidebar_compact") === "1");
const toggleCompact = () => {
  isCompact.value = !isCompact.value;
  localStorage.setItem("fb_sidebar_compact", isCompact.value ? "1" : "0");
};

const resourceSnapshot = ref({
  gold: 0,
  wood: 0,
  clay: 0,
  iron: 0,
});

let resourcePoller: number | null = null;

const fetchResourceSnapshot = async () => {
  if (!activeVillageId.value) {
    return;
  }
  try {
    const { data } = await axios.get(
      `${API_BASE}/villages/${activeVillageId.value}`
    );
    resourceSnapshot.value = {
      gold: data.gold ?? 0,
      wood: data.wood ?? 0,
      clay: data.clay ?? 0,
      iron: data.iron ?? 0,
    };
  } catch (error) {
    console.error("Error fetching village resources:", error);
  }
};

onMounted(async () => {
  try {
    await ensureActiveVillageId();
  } catch (error) {
    console.error("Failed to resolve active village:", error);
  }
  await fetchResourceSnapshot();
  resourcePoller = window.setInterval(fetchResourceSnapshot, 5000);
});

onUnmounted(() => {
  if (resourcePoller !== null) {
    window.clearInterval(resourcePoller);
    resourcePoller = null;
  }
});

watch(
  activeVillageId,
  () => {
    fetchResourceSnapshot();
  },
  { flush: "post" }
);

const { t } = useI18n();
</script>

<template>
  <aside
    :class="[
      'relative h-[calc(100vh+100)] bg-surface/95 border-r border-primary-800/30 p-4 transition-all duration-300 ease-out sticky',
      'overflow-hidden z-10 shrink-0', // <- fontos
      isCompact ? 'w-20' : 'w-72',
    ]"
  >
    <!-- Decorative glows -->
    <div
      class="pointer-events-none absolute -top-10 -left-10 h-40 w-40 rounded-full glow-primary"
    ></div>
    <div
      class="pointer-events-none absolute bottom-10 -right-10 h-40 w-40 rounded-full glow-amber"
    ></div>

    <!-- Header -->
    <div class="flex items-center gap-3 px-2 pb-4">
      <div class="relative">
        <div
          class="w-12 h-12 rounded-2xl bg-gradient-to-br from-primary to-primary-700 grid place-items-center shadow-neon"
        >
          <span class="text-2xl">🏰</span>
        </div>
        <span
          class="absolute -right-2 -bottom-2 text-xs px-2 py-0.5 rounded-full bg-primary-800/70 border border-primary-700 shadow-sm"
          >{{ t("sidebar.brand.badge") }}</span
        >
      </div>

      <div v-if="!isCompact" class="leading-tight">
        <h2 class="text-lg font-bold tracking-wide">
          {{ t("sidebar.brand.title") }}
        </h2>
        <p class="text-[11px] text-text-secondary">
          {{ t("sidebar.brand.subtitle") }}
        </p>
      </div>

      <!-- Compact toggle -->
      <button
        class="ml-auto rounded-lg px-2 py-2 hover:bg-secondary-800/70 border border-secondary/40 transition"
        :title="
          isCompact
            ? t('sidebar.toggle.expand')
            : t('sidebar.toggle.compact')
        "
        @click="toggleCompact"
      >
        <span v-if="isCompact">➡️</span>
        <span v-else>⬅️</span>
      </button>
    </div>

    <!-- Event / banner -->
    <div
      class="relative overflow-hidden rounded-xl border border-primary-800/40 mb-4 mx-0.5"
      :class="isCompact ? 'hidden' : ''"
    >
      <div class="absolute inset-0 shimmer pointer-events-none"></div>
      <div class="p-3 bg-gradient-to-br from-primary-900/30 to-primary-800/10">
        <div class="flex items-center gap-2 text-sm">
          <span>🎃</span>
          <span class="font-semibold">{{ t("sidebar.event.title") }}</span>
          <span class="text-text-secondary">{{
            t("sidebar.event.countdown")
          }}</span>
        </div>
        <p class="mt-1 text-xs text-text-secondary">
          {{ t("sidebar.event.description") }}
        </p>
        <div class="mt-3 flex gap-2">
          <router-link
            to="/quests"
            class="text-xs px-3 py-1.5 rounded-lg border border-primary-700/60 hover:bg-primary-800/30 transition"
            >{{ t("sidebar.event.viewQuests") }}</router-link
          >
          <router-link
            to="/shop"
            class="text-xs px-3 py-1.5 rounded-lg bg-primary-700/70 hover:bg-primary-600/70 border border-primary-600/60 transition"
            >{{ t("sidebar.event.eventShop") }}</router-link
          >
        </div>
      </div>
    </div>

    <!-- Resources -->
    <div
      class="grid gap-2 mb-5"
      :class="isCompact ? 'grid-cols-1' : 'grid-cols-2'"
    >
      <ResourcePill
        icon="🪙"
        :label="t('sidebar.resources.gold')"
        :value="resourceSnapshot.gold"
      />
      <ResourcePill
        icon="🪵"
        :label="t('sidebar.resources.wood')"
        :value="resourceSnapshot.wood"
      />
      <ResourcePill
        icon="🧱"
        :label="t('sidebar.resources.clay')"
        :value="resourceSnapshot.clay"
      />
      <ResourcePill
        icon="⛏️"
        :label="t('sidebar.resources.iron')"
        :value="resourceSnapshot.iron"
      />
    </div>

    <!-- Quick Actions -->
    <div
      class="mb-5 gap-2"
      :class="isCompact ? 'grid grid-cols-1' : 'grid grid-cols-3'"
    >
      <ActionBtn
        class="w-full"
        icon="🏗️"
        :label="t('sidebar.actions.build')"
        :tooltip="
          t('sidebar.actions.hotkey', {
            label: t('sidebar.actions.build'),
            key: 'B',
          })
        "
        k="B"
        to="/build"
        :compact="isCompact"
      />
      <ActionBtn
        class="w-full"
        icon="🛡️"
        :label="t('sidebar.actions.train')"
        :tooltip="
          t('sidebar.actions.hotkey', {
            label: t('sidebar.actions.train'),
            key: 'T',
          })
        "
        k="T"
        to="/barracks"
        :compact="isCompact"
      />
      <ActionBtn
        class="w-full"
        icon="🧠"
        :label="t('sidebar.actions.research')"
        :tooltip="
          t('sidebar.actions.hotkey', {
            label: t('sidebar.actions.research'),
            key: 'R',
          })
        "
        k="R"
        to="/research"
        :compact="isCompact"
      />
    </div>

    <!-- Nav groups -->
    <nav class="space-y-4 overflow-y-auto pr-1 sidebar-scroll pb-28">
      <NavGroup
        icon="🏡"
        :title="t('sidebar.nav.village.title')"
        :compact="isCompact"
      >
        <NavItem
          to="/village"
          icon="🏠"
          :label="t('sidebar.nav.village.townSquare')"
        />
        <NavItem
          to="/build"
          icon="🧱"
          :label="t('sidebar.nav.village.build')"
        />
        <NavItem
          to="/storage"
          icon="📦"
          :label="t('sidebar.nav.village.storage')"
        />
        <NavItem
          to="/market"
          icon="🛒"
          :label="t('sidebar.nav.village.market')"
          badge="2"
        />
      </NavGroup>

      <NavGroup
        icon="⚔️"
        :title="t('sidebar.nav.military.title')"
        :compact="isCompact"
      >
        <NavItem
          to="/barracks"
          icon="🗡️"
          :label="t('sidebar.nav.military.barracks')"
        />
        <NavItem
          to="/armory"
          icon="🛡️"
          :label="t('sidebar.nav.military.armory')"
        />
        <NavItem
          to="/battle"
          icon="🔥"
          :label="t('sidebar.nav.military.battle')"
        />
        <NavItem
          to="/defense"
          icon="🏹"
          :label="t('sidebar.nav.military.defense')"
        />
      </NavGroup>

      <NavGroup
        icon="🗺️"
        :title="t('sidebar.nav.world.title')"
        :compact="isCompact"
      >
        <NavItem
          to="/map"
          icon="🧭"
          :label="t('sidebar.nav.world.map')"
        />
        <NavItem
          to="/expeditions"
          icon="🧳"
          :label="t('sidebar.nav.world.expeditions')"
        />
        <NavItem
          to="/trade"
          icon="⚖️"
          :label="t('sidebar.nav.world.tradeRoutes')"
        />
      </NavGroup>

      <NavGroup
        icon="👥"
        :title="t('sidebar.nav.social.title')"
        :compact="isCompact"
      >
        <NavItem
          to="/leaderboard"
          icon="🏆"
          :label="t('sidebar.nav.social.leaderboard')"
        />
        <NavItem
          to="/clan"
          icon="🏳️"
          :label="t('sidebar.nav.social.clan')"
          badge="!"
        />
        <NavItem
          to="/mail"
          icon="✉️"
          :label="t('sidebar.nav.social.mail')"
          badge="5"
        />
      </NavGroup>
    </nav>

    <!-- Bottom Profile Card -->
    <div
      class="absolute left-0 right-0 bottom-0 p-4 border-t border-secondary/40 bg-surface/90 backdrop-blur-md"
    >
      <div class="flex items-center gap-3">
        <div
          class="w-10 h-10 rounded-xl bg-secondary-800 grid place-items-center text-lg"
        >
          🧑‍🌾
        </div>
        <div v-if="!isCompact" class="flex-1">
          <div class="flex items-center justify-between">
            <span class="text-sm font-medium">{{
              t("sidebar.profile.name")
            }}</span>
            <span class="text-[10px] text-text-secondary">{{
              t("sidebar.profile.level", { level: 7 })
            }}</span>
          </div>
          <div class="mt-1 h-2 bg-secondary/40 rounded-full overflow-hidden">
            <div
              class="h-full bg-gradient-to-r from-primary-600 to-primary-400 xp-bar"
            ></div>
          </div>
          <div class="mt-2 flex gap-2">
            <router-link to="/settings" class="btn-secondary text-[11px]">
              {{ t("sidebar.profile.settings") }}
            </router-link>
            <button class="btn-danger text-[11px]">
              {{ t("sidebar.profile.logout") }}
            </button>
          </div>
        </div>
        <router-link
          v-else
          to="/settings"
          class="ml-auto"
          :title="t('sidebar.profile.settings')"
          >⚙️</router-link
        >
      </div>
    </div>
  </aside>
</template>

<style scoped>
.before-hover::before,
.before-active::before {
  content: "";
  position: absolute;
  inset: 0;
  border-radius: 12px;
  box-shadow: 0 0 0 0 rgba(245, 158, 11, 0);
  transition: box-shadow 0.3s ease;
}
.before-hover:hover::before {
  box-shadow: 0 0 16px 2px rgba(245, 158, 11, 0.15);
}
.before-active::before {
  box-shadow: 0 0 18px 3px rgba(245, 158, 11, 0.18);
}
</style>
