<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, nextTick, computed } from 'vue';
import TheSidebar from '../components/TheSidebar.vue';
import { Chart, LineController, LineElement, PointElement, LinearScale, CategoryScale, Filler, Tooltip, Legend, DoughnutController, ArcElement, BarController, BarElement } from 'chart.js';

Chart.register(LineController, LineElement, PointElement, LinearScale, CategoryScale, Filler, Tooltip, Legend, DoughnutController, ArcElement, BarController, BarElement);

type Stats = {
  kpi: {
    total_peserta: number;
    dengan_foto: number;
    tanpa_foto: number;
    foto_storage_mb: number;
    foto_storage_bytes: number;
    foto_avg_kb: number;
    foto_max_kb: number;
    earliest_ts: string | null;
    latest_ts: string | null;
  };
  series: {
    labels_14d: string[];
    registrations_14d: number[];
    labels_weekday: string[];
    registrations_weekday: number[];
    labels_hour: string[];
    registrations_hour: number[];
  };
  recent: { uid: string; nama: string; foto: string; waktu: string | null }[];
};

const sidebarOpen = ref(false);
const isDesktop = ref(false);
const hasInteracted = ref(false);

function setupBreakpoint() {
  const mql = window.matchMedia('(min-width: 1024px)');
  const apply = () => {
    isDesktop.value = mql.matches;
    if (!hasInteracted.value) sidebarOpen.value = mql.matches;
  };
  mql.addEventListener('change', apply);
  apply();
  return () => mql.removeEventListener('change', apply);
}
function toggleSidebar() {
  hasInteracted.value = true;
  sidebarOpen.value = !sidebarOpen.value;
}

const stats = ref<Stats | null>(null);

const lineRef = ref<HTMLCanvasElement | null>(null);
const doughnutRef = ref<HTMLCanvasElement | null>(null);
const weekRef = ref<HTMLCanvasElement | null>(null);
const hourRef = ref<HTMLCanvasElement | null>(null);

function safeDestroy(c: HTMLCanvasElement | null) {
  if (!c) return;
  const inst = Chart.getChart(c);
  if (inst) inst.destroy();
}

const photoCounts = computed(() => {
  const w = Number(stats.value?.kpi?.dengan_foto ?? 0);
  const wo = Number(stats.value?.kpi?.tanpa_foto ?? 0);
  return { withPhoto: w, withoutPhoto: wo, total: w + wo };
});

const kpiCards = computed(() => [
  { label: 'Total Peserta', value: stats.value?.kpi?.total_peserta ?? '-' },
  { label: 'Dengan Foto', value: stats.value?.kpi?.dengan_foto ?? '-' },
  { label: 'Tanpa Foto', value: stats.value?.kpi?.tanpa_foto ?? '-' },
  { label: 'Foto Avg (KB)', value: stats.value?.kpi?.foto_avg_kb ?? '-' },
  { label: 'Foto Max (KB)', value: stats.value?.kpi?.foto_max_kb ?? '-' },
  { label: 'Storage (MB)', value: stats.value?.kpi?.foto_storage_mb ?? '-' },
]);

function renderCharts() {
  if (!stats.value) return;

  // Line
  if (lineRef.value) {
    safeDestroy(lineRef.value);
    const ctx = lineRef.value.getContext('2d');
    if (ctx) {
      const grad = ctx.createLinearGradient(0, 0, 0, 240);
      grad.addColorStop(0, 'rgba(2,132,199,0.35)');
      grad.addColorStop(1, 'rgba(2,132,199,0.04)');
      new Chart(ctx, {
        type: 'line',
        data: {
          labels: stats.value.series.labels_14d,
          datasets: [{ label: 'Registrasi (14 hari)', data: stats.value.series.registrations_14d, fill: true, backgroundColor: grad, borderColor: 'rgb(2,132,199)', pointRadius: 3, tension: 0.25 }],
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

  // Doughnut
  if (doughnutRef.value) {
    safeDestroy(doughnutRef.value);
    const ctx = doughnutRef.value.getContext('2d');
    if (ctx) {
      const w = photoCounts.value.withPhoto;
      const wo = photoCounts.value.withoutPhoto;
      const ds = w + wo > 0 ? [w, wo] : [1, 1];
      new Chart(ctx, {
        type: 'doughnut',
        data: {
          labels: ['Dengan Foto', 'Tanpa Foto'],
          datasets: [{ data: ds, backgroundColor: ['rgb(2,132,199)', 'rgb(63,63,70)'], hoverBackgroundColor: ['rgb(14,165,233)', 'rgb(82,82,91)'], borderWidth: 0 }],
        },
        options: { responsive: true, maintainAspectRatio: false, cutout: '66%', plugins: { legend: { position: 'bottom', labels: { color: '#E4E4E7' } } } },
      });
    }
  }

  // Bar Weekday
  if (weekRef.value) {
    safeDestroy(weekRef.value);
    const ctx = weekRef.value.getContext('2d');
    if (ctx) {
      new Chart(ctx, {
        type: 'bar',
        data: {
          labels: stats.value.series.labels_weekday,
          datasets: [{ label: 'By Weekday', data: stats.value.series.registrations_weekday, backgroundColor: 'rgba(2,132,199,0.6)' }],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: { legend: { display: false } },
          scales: {
            x: { grid: { color: 'rgba(255,255,255,0.06)' }, ticks: { color: '#A1A1AA' } },
            y: { grid: { color: 'rgba(255,255,255,0.06)' }, ticks: { color: '#A1A1AA' }, beginAtZero: true },
          },
        },
      });
    }
  }

  // Bar Hour
  if (hourRef.value) {
    safeDestroy(hourRef.value);
    const ctx = hourRef.value.getContext('2d');
    if (ctx) {
      new Chart(ctx, {
        type: 'bar',
        data: {
          labels: stats.value.series.labels_hour,
          datasets: [{ label: 'By Hour', data: stats.value.series.registrations_hour, backgroundColor: 'rgba(2,132,199,0.6)' }],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: { legend: { display: false } },
          scales: {
            x: { grid: { color: 'rgba(255,255,255,0.06)' }, ticks: { color: '#A1A1AA', maxRotation: 0, autoSkip: true } },
            y: { grid: { color: 'rgba(255,255,255,0.06)' }, ticks: { color: '#A1A1AA' }, beginAtZero: true },
          },
        },
      });
    }
  }
}

async function loadStats() {
  const r = await fetch('/api/stats');
  const j = await r.json();
  if (j.ok) {
    stats.value = j as Stats;
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
  [lineRef.value, doughnutRef.value, weekRef.value, hourRef.value].forEach(safeDestroy);
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
          <button aria-label="Toggle sidebar" @click="toggleSidebar" class="cursor-pointer inline-flex items-center justify-center size-9 rounded-lg border border-zinc-800 bg-zinc-900/80 hover:bg-zinc-800/70">
            <svg viewBox="0 0 24 24" class="size-5 stroke-current" fill="none" stroke-width="1.8">
              <path d="M4 7h16M4 12h16M4 17h16" />
            </svg>
          </button>

          <!-- Export buttons -->
          <div class="ml-auto flex items-center gap-2">
            <a href="/api/export/participants.csv" class="px-3 py-1.5 text-xs sm:text-sm rounded-lg bg-zinc-800 border border-zinc-700 hover:bg-zinc-700">Export CSV</a>
            <a href="/api/export/stats.json" class="px-3 py-1.5 text-xs sm:text-sm rounded-lg bg-zinc-800 border border-zinc-700 hover:bg-zinc-700">Export JSON</a>
            <a href="/api/export/photos.zip" class="px-3 py-1.5 text-xs sm:text-sm rounded-lg bg-zinc-800 border border-zinc-700 hover:bg-zinc-700">Download Photos ZIP</a>
          </div>
        </div>
      </header>

      <main class="px-3 sm:px-4 lg:px-6 py-5 space-y-4">
        <!-- KPI -->
        <section class="rounded-2xl bg-zinc-900/70 border border-zinc-800 p-4 sm:p-5">
          <h2 class="sr-only">Ringkasan</h2>
          <div class="grid grid-cols-2 sm:grid-cols-3 xl:grid-cols-6 gap-3 sm:gap-4">
            <div v-for="(card, i) in kpiCards" :key="i" class="rounded-xl border border-zinc-800 bg-zinc-900/60 p-3 sm:p-4">
              <div class="text-[11px] sm:text-xs text-zinc-400">{{ card.label }}</div>
              <div class="mt-1 text-xl sm:text-2xl font-bold truncate">{{ card.value }}</div>
            </div>
          </div>
          <div class="mt-3 text-[11px] sm:text-xs text-zinc-400">
            Rentang data: {{ stats?.kpi?.earliest_ts ? new Date(stats.kpi.earliest_ts).toLocaleString() : '-' }} — {{ stats?.kpi?.latest_ts ? new Date(stats.kpi.latest_ts).toLocaleString() : '-' }}
          </div>
        </section>

        <!-- Charts -->
        <section class="rounded-2xl bg-zinc-900/70 border border-zinc-800 p-4 sm:p-5">
          <h2 class="sr-only">Grafik</h2>
          <div class="grid grid-cols-1 lg:grid-cols-3 gap-4">
            <div class="lg:col-span-2 rounded-xl border border-zinc-800 bg-zinc-900/60 p-3 sm:p-4">
              <div class="text-xs text-zinc-400">Registrasi 14 hari</div>
              <div class="mt-2 h-[240px] sm:h-[300px]"><canvas ref="lineRef"></canvas></div>
            </div>
            <div class="relative rounded-xl border border-zinc-800 bg-zinc-900/60 p-3 sm:p-4">
              <div class="text-xs text-zinc-400">Kelengkapan Foto</div>
              <div class="mt-2 h-[240px] sm:h-[300px]"><canvas ref="doughnutRef"></canvas></div>
              <div v-if="photoCounts.total === 0" class="absolute inset-0 flex items-center justify-center pointer-events-none">
                <span class="text-xs text-zinc-400">Tidak ada data</span>
              </div>
            </div>
          </div>
        </section>

        <!-- Distribusi waktu -->
        <section class="rounded-2xl bg-zinc-900/70 border border-zinc-800 p-4 sm:p-5">
          <h2 class="sr-only">Distribusi Waktu</h2>
          <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <div class="rounded-xl border border-zinc-800 bg-zinc-900/60 p-3 sm:p-4">
              <div class="text-xs text-zinc-400">Distribusi per Hari (Sen–Min)</div>
              <div class="mt-2 h-[220px] sm:h-[260px]"><canvas ref="weekRef"></canvas></div>
            </div>
            <div class="rounded-xl border border-zinc-800 bg-zinc-900/60 p-3 sm:p-4">
              <div class="text-xs text-zinc-400">Distribusi per Jam (00–23)</div>
              <div class="mt-2 h-[220px] sm:h-[260px]"><canvas ref="hourRef"></canvas></div>
            </div>
          </div>
        </section>

        <!-- Recent -->
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
