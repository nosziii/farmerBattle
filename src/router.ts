import { createRouter, createWebHistory } from 'vue-router';

import Village from './views/Village.vue';
import Battle from './views/Battle.vue';
import Map from './views/Map.vue';
import Leaderboard from './views/Leaderboard.vue';
import Barracks from './views/Barracks.vue';
import Build from './views/Build.vue';
import Storage from './views/Storage.vue';
import Admin from './views/Admin.vue';
import Info from './views/Info.vue';

const routes = [
  { path: '/', component: Village },
  { path: '/battle', component: Battle },
  { path: '/build', component: Build },
  { path: '/map', component: Map },
  { path: '/leaderboard', component: Leaderboard },
  { path: '/barracks', component: Barracks },
  { path: '/storage', component: Storage },
  { path: '/admin', component: Admin },
  { path: '/info', component: Info },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

export default router;
