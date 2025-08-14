import { createRouter, createWebHistory } from 'vue-router';
import Home from './pages/Home.vue';
import Register from './pages/Register.vue';
import Booth from './pages/Booth.vue';
import Analytics from './pages/Analytics.vue';
import Dashboard from './pages/Dashboard.vue';

const routes = [
  { path: '/', component: Home },
  { path: '/register', component: Register },
  { path: '/booth', component: Booth },
  { path: '/analytics', component: Analytics },
  { path: '/dashboard', component: Dashboard },
];

export default createRouter({
  history: createWebHistory(),
  routes,
});
