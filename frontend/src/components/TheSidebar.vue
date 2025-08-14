<script setup lang="ts">
import { h } from 'vue';

const topItems = [
  { key: 'dashboard', title: 'Dashboard', to: '/dashboard' },
  { key: 'analytics', title: 'Analytics', to: '/analytics' },
];

const bottomItems = [
  { key: 'home', title: 'Home', to: '/', newTab: true },
  { key: 'booth', title: 'Booth', to: '/booth', newTab: true },
  { key: 'register', title: 'Register', to: '/register', newTab: true },
];

function getIcon(name: string) {
  const base = { viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', 'stroke-width': 1.5, class: 'size-4' };
  switch (name) {
    case 'dashboard':
      return {
        render: () =>
          h('svg', base, [
            h('rect', { x: 3, y: 3, width: 7, height: 7, rx: 2 }),
            h('rect', { x: 14, y: 3, width: 7, height: 4, rx: 2 }),
            h('rect', { x: 14, y: 9, width: 7, height: 12, rx: 2 }),
            h('rect', { x: 3, y: 12, width: 7, height: 9, rx: 2 }),
          ]),
      };
    case 'analytics':
      return { render: () => h('svg', base, [h('path', { d: 'M4 20h16' }), h('path', { d: 'M6 15l5-6 3 3 4-6' })]) };
    case 'register':
      return { render: () => h('svg', base, [h('circle', { cx: 9, cy: 8, r: 2.5 }), h('path', { d: 'M5.5 18a5 5 0 0 1 7 0' }), h('path', { d: 'M16 8h4M18 6v4' })]) };
    case 'booth':
      return {
        render: () =>
          h('svg', base, [h('rect', { x: 3, y: 4, width: 18, height: 14, rx: 2 }), h('circle', { cx: 9, cy: 11, r: 2 }), h('path', { d: 'M7 15a4 4 0 0 1 4 0' }), h('path', { d: 'M14 9h5M14 12h5' })]),
      };
    case 'home':
    default:
      return { render: () => h('svg', base, [h('path', { d: 'M3 11.5L12 4l9 7.5' }), h('path', { d: 'M5 10v9a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1v-9' })]) };
  }
}

function ExternalIcon() {
  const base = { viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', 'stroke-width': 1.5, class: 'size-3_5' };
  return { render: () => h('svg', base, [h('path', { d: 'M14 5h5v5' }), h('path', { d: 'M10 14L19 5' }), h('path', { d: 'M19 13v5a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V7a2 2 0 0 1 2-2h5' })]) };
}
</script>

<template>
  <aside class="fixed inset-y-0 left-0 w-60 bg-zinc-900/95 border-r border-zinc-800 backdrop-blur flex flex-col">
    <div class="px-4 py-4 flex items-center gap-3 border-b border-zinc-800">
      <div class="grid place-items-center size-8 rounded-xl bg-sky-600 text-white text-sm font-bold">N</div>
      <div>
        <div class="text-[15px] font-extrabold tracking-tight leading-5">NFC Event</div>
        <div class="text-xs text-zinc-400">Check-in Dashboard</div>
      </div>
    </div>

    <nav class="px-3 py-4">
      <div class="space-y-1">
        <RouterLink v-for="item in topItems" :key="item.key" :to="item.to" custom v-slot="{ href, navigate, isActive }">
          <a
            :href="href"
            @click="navigate"
            :aria-current="isActive ? 'page' : undefined"
            class="group relative flex items-center gap-3 rounded-lg px-3 py-2.5 text-[14px] transition overflow-hidden"
            :class="isActive ? 'bg-zinc-800 text-white ring-1 ring-zinc-700' : 'text-zinc-300 hover:bg-zinc-800 hover:text-white'"
          >
            <span class="absolute left-0 top-0 bottom-0 w-[3px] bg-sky-500 transition-opacity" :class="isActive ? 'opacity-100' : 'opacity-0 group-hover:opacity-60'" />
            <span class="shrink-0">
              <component :is="getIcon(item.key)" class="opacity-90 group-hover:opacity-100" />
            </span>
            <span class="font-medium">{{ item.title }}</span>
          </a>
        </RouterLink>
      </div>

      <div class="my-5 mx-1 border-t border-zinc-800"></div>

      <div class="space-y-1">
        <RouterLink v-for="item in bottomItems" :key="item.key" :to="item.to" custom v-slot="{ href, isActive }">
          <a
            :href="href"
            target="_blank"
            rel="noopener"
            :aria-current="isActive ? 'page' : undefined"
            class="group relative flex items-center gap-2 rounded-lg px-3 py-2.5 text-[14px] transition overflow-hidden"
            :class="isActive ? 'bg-zinc-800 text-white ring-1 ring-zinc-700' : 'text-zinc-300 hover:bg-zinc-800 hover:text-white'"
          >
            <span class="absolute left-0 top-0 bottom-0 w-[2px] bg-sky-500 transition-opacity" :class="isActive ? 'opacity-100' : 'opacity-0 group-hover:opacity-60'" />
            <span class="shrink-0">
              <component :is="getIcon(item.key)" class="opacity-90 group-hover:opacity-100" />
            </span>
            <span class="font-medium">{{ item.title }}</span>
            <span class="opacity-60 group-hover:opacity-100">
              <component :is="ExternalIcon()" />
            </span>
          </a>
        </RouterLink>
      </div>
    </nav>

    <div class="mt-auto px-4 py-4 text-[11px] text-zinc-400">
      <div>© {{ new Date().getFullYear() }} • aptrocode</div>
    </div>
  </aside>
</template>

<style scoped>
.size-4 {
  width: 1rem;
  height: 1rem;
}
.size-3_5 {
  width: 0.875rem;
  height: 0.875rem;
}
.size-8 {
  width: 2rem;
  height: 2rem;
}
</style>
