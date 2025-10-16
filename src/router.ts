import { createRouter, createWebHistory } from 'vue-router';

import Village from './views/Village.vue';
import Battle from './views/Battle.vue';
import Map from './views/Map.vue';
import Leaderboard from './views/Leaderboard.vue';
import Barracks from './views/Barracks.vue';

const routes = [
  { path: '/', component: Village },
  { path: '/battle', component: Battle },
  { path: '/map', component: Map },
  { path: '/leaderboard', component: Leaderboard },
  { path: '/barracks', component: Barracks },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

export default router;
