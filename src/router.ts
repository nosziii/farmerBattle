import { createRouter, createWebHistory } from "vue-router";
import { ensureAuthReady, useAuthState } from "./services/auth";

import Landing from "./views/Landing.vue";
import Login from "./views/Login.vue";
import Register from "./views/Register.vue";
import Village from "./views/Village.vue";
import Battle from "./views/Battle.vue";
import Map from "./views/Map.vue";
import Leaderboard from "./views/Leaderboard.vue";
import Barracks from "./views/Barracks.vue";
import Build from "./views/Build.vue";
import Storage from "./views/Storage.vue";
import Admin from "./views/Admin.vue";
import Info from "./views/Info.vue";
import Placeholder from "./views/Placeholder.vue";

const routes = [
  { path: "/", component: Landing },
  { path: "/login", component: Login, meta: { guestOnly: true } },
  { path: "/register", component: Register, meta: { guestOnly: true } },
  { path: "/village", component: Village, meta: { requiresAuth: true } },
  { path: "/battle", component: Battle, meta: { requiresAuth: true } },
  { path: "/build", component: Build, meta: { requiresAuth: true } },
  { path: "/map", component: Map, meta: { requiresAuth: true } },
  { path: "/leaderboard", component: Leaderboard },
  { path: "/barracks", component: Barracks, meta: { requiresAuth: true } },
  { path: "/storage", component: Storage, meta: { requiresAuth: true } },
  { path: "/admin", component: Admin, meta: { requiresAdmin: true } },
  { path: "/info", component: Info },
  { path: "/quests", component: Placeholder, props: { title: "Quests Board" }, meta: { requiresAuth: true } },
  { path: "/shop", component: Placeholder, props: { title: "Event Shop" }, meta: { requiresAuth: true } },
  { path: "/market", component: Placeholder, props: { title: "Market" }, meta: { requiresAuth: true } },
  { path: "/research", component: Placeholder, props: { title: "Research Lab" }, meta: { requiresAuth: true } },
  { path: "/armory", component: Placeholder, props: { title: "Armory" }, meta: { requiresAuth: true } },
  { path: "/defense", component: Placeholder, props: { title: "Defense Overview" }, meta: { requiresAuth: true } },
  { path: "/clan", component: Placeholder, props: { title: "Clan Hub" }, meta: { requiresAuth: true } },
  { path: "/mail", component: Placeholder, props: { title: "Mail Center" }, meta: { requiresAuth: true } },
  { path: "/settings", component: Placeholder, props: { title: "Settings" }, meta: { requiresAuth: true } },
  { path: "/expeditions", component: Placeholder, props: { title: "Expeditions" }, meta: { requiresAuth: true } },
  { path: "/trade", component: Placeholder, props: { title: "Trade Routes" }, meta: { requiresAuth: true } },
  { path: "/:pathMatch(.*)*", redirect: "/" },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

router.beforeEach(async (to) => {
  const { isAuthenticated, isAdmin } = useAuthState();
  await ensureAuthReady();

  if (to.meta?.requiresAuth && !isAuthenticated.value) {
    return { path: "/login", query: { redirect: to.fullPath } };
  }

  if (to.meta?.guestOnly && isAuthenticated.value) {
    return { path: "/village" };
  }

  if (to.meta?.requiresAdmin && !isAdmin.value) {
    return { path: "/" };
  }

  return true;
});

export default router;
