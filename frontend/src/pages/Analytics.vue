<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, nextTick, computed } from 'vue';
import TheSidebar from '../components/TheSidebar.vue';
import { Chart, LineController, LineElement, PointElement, LinearScale, CategoryScale, Filler, Tooltip, Legend, ArcElement, DoughnutController } from 'chart.js';

Chart.register(LineController, LineElement, PointElement, LinearScale, CategoryScale, Filler, Tooltip, Legend, DoughnutController, ArcElement);

const sidebarOpen = ref(false);
const isDesktop = ref(false);
const hasInteracted = ref(false);

function setupBreakpoint() {
  const mql = window.matchMedia('(min-width: 1024px)');
  const apply = () => {
    isDesktop.value = mql.matches;
    if (!hasInteracted.value) {
      sidebarOpen.value = mql.matches ? true : false;
    }
  };
  mql.addEventListener('change', apply);
  apply();
  return () => mql.removeEventListener('change', apply);
}

function toggleSidebar() {
  hasInteracted.value = true;
  sidebarOpen.value = !sidebarOpen.value;
}

const stats = ref<any>(null);

const lineRef = ref<HTMLCanvasElement | null>(null);
const doughnutRef = ref<HTMLCanvasElement | null>(null);

function safeDestroy(canvas: HTMLCanvasElement | null) {
  if (!canvas) return;
  const existing = Chart.getChart(canvas);
  if (existing) existing.destroy();
}

function makeGradient(ctx: CanvasRenderingContext2D) {
  const g = ctx.createLinearGradient(0, 0, 0, 240);
  g.addColorStop(0, 'rgba(2, 132, 199, 0.35)'); // sky-600
  g.addColorStop(1, 'rgba(2, 132, 199, 0.04)');
  return g;
}

const photoCounts = computed(() => {
  const withPhoto = Number(stats.value?.kpi?.dengan_foto ?? 0);
  const withoutPhoto = Number(stats.value?.kpi?.tanpa_foto ?? 0);
  return { withPhoto, withoutPhoto, total: withPhoto + withoutPhoto };
});

function renderCharts() {
  if (!stats.value) return;

  // LINE
  {
    const c = lineRef.value;
    if (c) {
      safeDestroy(c);
      const ctx = c.getContext('2d');
      if (ctx) {
        new Chart(ctx, {
          type: 'line',
          data: {
            labels: stats.value.series.labels_14d,
            datasets: [
              {
                label: 'Registrasi (14 hari)',
                data: (stats.value.series.registrations_14d ?? []).map((n: any) => Number(n) || 0),
                fill: true,
                backgroundColor: makeGradient(ctx),
                borderColor: 'rgb(2, 132, 199)',
                pointRadius: 3,
                tension: 0.25,
              },
            ],
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false }, tooltip: { mode: 'index', intersect: false } },
            scales: {
              x: { grid: { color: 'rgba(255,255,255,0.06)' }, ticks: { color: '#A1A1AA' } },
              y: { grid: { color: 'rgba(255,255,255,0.06)' }, ticks: { color: '#A1A1AA' }, beginAtZero: true },
            },
          },
        });
      }
    }
  }

  // DOUGHNUT
  {
    const c = doughnutRef.value;
    if (c) {
      safeDestroy(c);
      const ctx = c.getContext('2d');
      if (ctx) {
        const w = photoCounts.value.withPhoto;
        const wo = photoCounts.value.withoutPhoto;
        const total = w + wo;
        const dataValues = total > 0 ? [w, wo] : [1, 1]; // dummy agar terlihat

        new Chart(ctx, {
          type: 'doughnut',
          data: {
            labels: ['Dengan Foto', 'Tanpa Foto'],
            datasets: [
              {
                data: dataValues,
                backgroundColor: ['rgb(2, 132, 199)', 'rgb(63, 63, 70)'],
                hoverBackgroundColor: ['rgb(14, 165, 233)', 'rgb(82, 82, 91)'],
                borderWidth: 0,
              },
            ],
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '66%',
            plugins: {
              legend: { position: 'bottom', labels: { color: '#E4E4E7' } },
              tooltip: {
                callbacks: {
                  label: (ctx) => {
                    const i = ctx.dataIndex;
                    const original = i === 0 ? w : wo;
                    return `${ctx.label}: ${original}`;
                  },
                },
              },
            },
          },
        });
      }
    }
  }
}

async function loadStats() {
  const r = await fetch('/api/stats');
  const j = await r.json();
  if (j.ok) {
    stats.value = j;
    await nextTick();
    renderCharts();
  }
}

let disposeBreakpoint: (() => void) | null = null;
function onResize() {
  renderCharts();
}

onMounted(() => {
  disposeBreakpoint = setupBreakpoint();
  loadStats();
  window.addEventListener('resize', onResize);
});

onBeforeUnmount(() => {
  window.removeEventListener('resize', onResize);
  disposeBreakpoint?.();
  safeDestroy(lineRef.value);
  safeDestroy(doughnutRef.value);
});
</script>

<template>
  <div class="flex">
    <TheSidebar
      :class="[
        'fixed inset-y-0 left-0 w-60 z-50 transition-transform duration-300 will-change-transform',
        sidebarOpen ? 'translate-x-0' : '-translate-x-full',
        isDesktop ? 'shadow-none' : 'shadow-2xl',
      ]"
    />

    <div :class="['min-h-screen flex-1 transition-[margin] duration-300', isDesktop && sidebarOpen ? 'ml-60' : 'ml-0']">
      <header class="sticky top-0 z-40 bg-zinc-900/70 backdrop-blur border-b border-zinc-800">
        <div class="px-3 sm:px-4 py-2.5 flex items-center gap-2">
          <button aria-label="Toggle sidebar" @click="toggleSidebar" class="inline-flex items-center justify-center size-9 rounded-lg border border-zinc-800 bg-zinc-900/80 hover:bg-zinc-800/70">
            <svg viewBox="0 0 24 24" class="size-5 stroke-current" fill="none" stroke-width="1.8">
              <path d="M4 7h16M4 12h16M4 17h16" />
            </svg>
          </button>
        </div>
      </header>

      <main class="px-3 sm:px-4 lg:px-6 py-5 space-y-4">
        <section class="rounded-2xl bg-zinc-900/70 border border-zinc-800 p-4 sm:p-5">
          <h2 class="sr-only">Ringkasan</h2>
          <div class="grid grid-cols-2 sm:grid-cols-4 xl:grid-cols-6 gap-3 sm:gap-4">
            <div class="rounded-xl border border-zinc-800 bg-zinc-900/60 p-3 sm:p-4">
              <div class="text-[11px] sm:text-xs text-zinc-400">Total Peserta</div>
              <div class="mt-1 text-xl sm:text-2xl font-bold">{{ stats?.kpi?.total_peserta ?? '-' }}</div>
            </div>
            <div class="rounded-xl border border-zinc-800 bg-zinc-900/60 p-3 sm:p-4">
              <div class="text-[11px] sm:text-xs text-zinc-400">Dengan Foto</div>
              <div class="mt-1 text-xl sm:text-2xl font-bold">{{ stats?.kpi?.dengan_foto ?? '-' }}</div>
            </div>
            <div class="rounded-xl border border-zinc-800 bg-zinc-900/60 p-3 sm:p-4">
              <div class="text-[11px] sm:text-xs text-zinc-400">Tanpa Foto</div>
              <div class="mt-1 text-xl sm:text-2xl font-bold">{{ stats?.kpi?.tanpa_foto ?? '-' }}</div>
            </div>
            <div class="rounded-xl border border-zinc-800 bg-zinc-900/60 p-3 sm:p-4">
              <div class="text-[11px] sm:text-xs text-zinc-400">Storage Foto (MB)</div>
              <div class="mt-1 text-xl sm:text-2xl font-bold">{{ stats?.kpi?.foto_storage_mb ?? '-' }}</div>
            </div>
            <div class="rounded-xl border border-zinc-800 bg-zinc-900/60 p-3 sm:p-4 xl:col-span-2">
              <div class="text-[11px] sm:text-xs text-zinc-400">Storage (Bytes)</div>
              <div class="mt-1 text-xl sm:text-2xl font-bold truncate">{{ stats?.kpi?.foto_storage_bytes ?? '-' }}</div>
            </div>
          </div>
        </section>

        <section class="rounded-2xl bg-zinc-900/70 border border-zinc-800 p-4 sm:p-5">
          <h2 class="sr-only">Grafik</h2>
          <div class="grid grid-cols-1 lg:grid-cols-3 gap-4">
            <div class="lg:col-span-2 rounded-xl border border-zinc-800 bg-zinc-900/60 p-3 sm:p-4">
              <div class="text-xs text-zinc-400">Registrasi 14 hari</div>
              <div class="mt-2 h-[240px] sm:h-[300px]">
                <canvas ref="lineRef"></canvas>
              </div>
            </div>

            <div class="relative rounded-xl border border-zinc-800 bg-zinc-900/60 p-3 sm:p-4">
              <div class="text-xs text-zinc-400">Kelengkapan Foto</div>
              <div class="mt-2 h-[240px] sm:h-[300px]">
                <canvas ref="doughnutRef"></canvas>
              </div>
              <div v-if="photoCounts.total === 0" class="absolute inset-0 flex items-center justify-center pointer-events-none">
                <span class="text-xs text-zinc-400">Tidak ada data</span>
              </div>
            </div>
          </div>
        </section>

        <section class="rounded-2xl bg-zinc-900/70 border border-zinc-800 p-4 sm:p-5">
          <h2 class="sr-only">Aktivitas Terbaru</h2>
          <div class="space-y-2">
            <div v-for="r in stats?.recent ?? []" :key="r.uid" class="flex items-center gap-3 rounded-xl border border-zinc-800 bg-zinc-900/60 p-3">
              <img v-if="r.foto" :src="r.foto" class="size-10 sm:size-12 rounded-lg object-cover border border-zinc-800" />
              <div class="flex-1 min-w-0">
                <div class="font-medium truncate">{{ r.nama }}</div>
                <div class="text-[11px] sm:text-xs text-zinc-400 truncate">{{ r.uid }} • {{ r.waktu ? new Date(r.waktu).toLocaleString() : '-' }}</div>
              </div>
            </div>
          </div>
        </section>
      </main>
    </div>

    <div v-if="sidebarOpen && !isDesktop" @click="sidebarOpen = false" class="fixed inset-0 bg-black/40 backdrop-blur-sm z-40" />
  </div>
</template>

<style>
/* none */
</style>
