<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount } from 'vue';
import { io, Socket } from 'socket.io-client';
import TheSidebar from '../components/TheSidebar.vue';
import ButtonTable from '../components/atoms/ButtonTable.vue';

type Participant = { UID: string; Nama?: string; Foto?: string };

const q = ref('');
const rows = ref<Participant[]>([]);
const cols = [
  { key: 'photo', label: 'Foto' },
  { key: 'nama', label: 'Nama' },
  { key: 'uid', label: 'UID' },
  { key: 'waktu', label: 'Waktu' },
  { key: 'aksi', label: 'Aksi' },
];

const dlg = ref<HTMLDialogElement | null>(null);
const editUID = ref('');
const editName = ref('');
const fileInp = ref<HTMLInputElement | null>(null);
const currentPhotoUrl = ref<string | null>(null);
const preview = ref<string | null>(null);

const delDlg = ref<HTMLDialogElement | null>(null);
const delUid = ref<string | null>(null);
const delName = ref<string | null>(null);

const sidebarOpen = ref(false);
const isDesktop = ref(false);
const hasInteracted = ref(false);
let disposeBreakpoint: (() => void) | null = null;

// --- Realtime ---
let socket: Socket | null = null;
const liveConnected = ref(false);
let pollTimer: number | null = null;
let refreshTimer: number | null = null;

function scheduleRefresh(ms = 350) {
  if (refreshTimer) window.clearTimeout(refreshTimer);
  refreshTimer = window.setTimeout(() => void loadList(), ms);
}

function initSocket() {
  socket = io({ path: '/socket.io', transports: ['websocket', 'polling'] });
  socket.on('connect', () => {
    liveConnected.value = true;
  });
  socket.on('disconnect', () => {
    liveConnected.value = false;
  });

  const events = ['participant_added', 'participant_updated', 'participant_deleted', 'participants_changed', 'nfc_tapped'];
  events.forEach((ev) => socket!.on(ev, () => scheduleRefresh()));
}

function startPollFallback() {
  // Fallback ringan kalau socket gagal/di-block proxy
  if (pollTimer) window.clearInterval(pollTimer);
  pollTimer = window.setInterval(() => {
    if (!liveConnected.value) void loadList();
  }, 5000);
}

// --- Layout ---
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

// --- Helpers ---
function tsDisplay(path?: string) {
  if (!path) return '-';
  const base = path.split('/').pop() || '';
  const ts = Number(base.split('.')[0].split('_').pop());
  if (!Number.isFinite(ts)) return '-';
  return new Date(ts * 1000).toLocaleString();
}
async function loadList() {
  const res = await fetch('/api/participants' + (q.value ? `?q=${encodeURIComponent(q.value)}` : ''));
  const j = await res.json();
  if (j.ok) rows.value = j.data;
}

function openEdit(r: Participant) {
  editUID.value = r.UID;
  editName.value = r.Nama || '';
  currentPhotoUrl.value = r.Foto ? '/' + r.Foto : null;
  preview.value = null;
  if (fileInp.value) fileInp.value.value = '';
  dlg.value?.showModal();
}
function clearPreview() {
  preview.value = null;
  if (fileInp.value) fileInp.value.value = '';
}
function onFileChange(e: Event) {
  const f = (e.target as HTMLInputElement)?.files?.[0];
  if (!f) {
    preview.value = null;
    return;
  }
  const fr = new FileReader();
  fr.onload = () => {
    preview.value = fr.result as string;
  };
  fr.readAsDataURL(f);
}
function readFileAsDataURL(file: File) {
  return new Promise<string>((resolve, reject) => {
    const fr = new FileReader();
    fr.onload = () => resolve(fr.result as string);
    fr.onerror = reject;
    fr.readAsDataURL(file);
  });
}

async function saveEdit() {
  const payload: Record<string, unknown> = { name: editName.value };
  const f = fileInp.value?.files?.[0];
  if (f) payload.photoDataURL = await readFileAsDataURL(f);

  const res = await fetch(`/api/participant/${encodeURIComponent(editUID.value)}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  const j = await res.json();
  if (!j.ok) {
    alert('Gagal menyimpan: ' + (j.error || 'unknown'));
    return;
  }
  dlg.value?.close();
  await loadList();
}
function cancelEdit() {
  dlg.value?.close();
}

function openDelete(r: Participant) {
  delUid.value = r.UID;
  delName.value = r.Nama || '(Tanpa Nama)';
  delDlg.value?.showModal();
}
async function confirmDelete() {
  if (!delUid.value) return;
  const res = await fetch(`/api/participant/${encodeURIComponent(delUid.value)}?deletePhoto=1`, { method: 'DELETE' });
  const j = await res.json();
  if (!j.ok) {
    alert('Gagal menghapus: ' + (j.error || 'unknown'));
    return;
  }
  delDlg.value?.close();
  delUid.value = null;
  delName.value = null;
  await loadList();
}
function cancelDelete() {
  delDlg.value?.close();
  delUid.value = null;
  delName.value = null;
}

// --- Lifecycle ---
onMounted(() => {
  disposeBreakpoint = setupBreakpoint();
  initSocket();
  startPollFallback();
  loadList();

  document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'visible') scheduleRefresh(0);
  });
});
onBeforeUnmount(() => {
  disposeBreakpoint?.();
  if (socket) {
    socket.removeAllListeners();
    socket.disconnect();
  }
  if (pollTimer) window.clearInterval(pollTimer);
  if (refreshTimer) window.clearTimeout(refreshTimer);
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
          <button
            aria-label="Toggle sidebar"
            @click="toggleSidebar"
            class="cursor-pointer inline-flex items-center justify-center size-9 rounded-lg border border-zinc-800 bg-zinc-900/80 hover:bg-zinc-800/70"
          >
            <svg viewBox="0 0 24 24" class="size-5 stroke-current" fill="none" stroke-width="1.8">
              <path d="M4 7h16M4 12h16M4 17h16" />
            </svg>
          </button>

          <!-- Live indicator -->
          <div class="ml-2 flex items-center gap-2 text-xs">
            <span class="inline-flex items-center gap-1 rounded-full px-2 py-1 border" :class="liveConnected ? 'border-sky-700 text-sky-200 bg-sky-900/30' : 'border-zinc-700 text-zinc-300'">
              <span :class="['size-2 rounded-full', liveConnected ? 'bg-sky-400' : 'bg-zinc-500']"></span>
              {{ liveConnected ? 'Live' : 'Offline' }}
            </span>
          </div>

          <div class="ml-auto flex items-center gap-2">
            <input v-model="q" placeholder="Cari nama/UID..." class="px-3 py-2 text-sm rounded-lg bg-zinc-800 border border-zinc-700 outline-none focus:ring-2 focus:ring-sky-500" />
            <button @click="loadList" class="cursor-pointer px-3 py-2 text-sm rounded-lg bg-zinc-800 border border-zinc-700 hover:bg-zinc-700">Search</button>
            <button
              @click="
                q = '';
                loadList();
              "
              class="cursor-pointer px-3 py-2 text-sm rounded-lg bg-zinc-800 border border-zinc-700 hover:bg-zinc-700"
            >
              Reset
            </button>
          </div>
        </div>
      </header>

      <main class="px-3 sm:px-4 lg:px-6 py-5 space-y-4">
        <!-- Table (md+) -->
        <section class="rounded-2xl bg-zinc-900/70 border border-zinc-800 p-4 sm:p-5 hidden md:block">
          <div class="overflow-x-auto">
            <table class="min-w-full text-sm">
              <thead class="text-left text-zinc-300 border-b border-zinc-800">
                <tr>
                  <th v-for="c in cols" :key="c.key" class="py-2 pr-4">{{ c.label }}</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="r in rows" :key="r.UID" class="align-middle">
                  <td v-for="c in cols" :key="c.key" class="py-3 pr-4">
                    <template v-if="c.key === 'photo'">
                      <img v-if="r.Foto" :src="'/' + r.Foto" class="size-12 rounded-xl object-cover" />
                      <div v-else class="size-12 rounded-xl bg-zinc-800 grid place-items-center text-xs text-zinc-400">N/A</div>
                    </template>
                    <template v-else-if="c.key === 'nama'">
                      <span class="font-medium max-w-[280px] inline-block truncate">{{ r.Nama || '(Tanpa Nama)' }}</span>
                    </template>
                    <template v-else-if="c.key === 'uid'">
                      <span class="text-zinc-300 whitespace-nowrap">{{ r.UID }}</span>
                    </template>
                    <template v-else-if="c.key === 'waktu'">
                      <span class="text-zinc-300 whitespace-nowrap">{{ tsDisplay(r.Foto) }}</span>
                    </template>
                    <template v-else-if="c.key === 'aksi'">
                      <div class="flex gap-2">
                        <ButtonTable icon="edit" variant="ghost" title="Edit" @click="openEdit(r)" />
                        <ButtonTable icon="trash" variant="danger" title="Delete" @click="openDelete(r)" />
                      </div>
                    </template>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>

        <!-- Cards (< md) -->
        <section class="rounded-2xl bg-zinc-900/70 border border-zinc-800 p-4 sm:p-5 md:hidden">
          <ul class="space-y-3">
            <li v-for="r in rows" :key="r.UID" class="flex items-center gap-3 rounded-xl border border-zinc-800 bg-zinc-900/60 p-3">
              <img v-if="r.Foto" :src="'/' + r.Foto" class="size-12 rounded-lg object-cover border border-zinc-800" />
              <div v-else class="size-12 rounded-lg bg-zinc-800 grid place-items-center text-[10px] text-zinc-400">N/A</div>
              <div class="flex-1 min-w-0">
                <div class="font-medium truncate">{{ r.Nama || '(Tanpa Nama)' }}</div>
                <div class="text-xs text-zinc-400 truncate">{{ r.UID }}</div>
                <div class="text-xs text-zinc-500">{{ tsDisplay(r.Foto) }}</div>
              </div>
              <div class="flex gap-2 shrink-0">
                <ButtonTable icon="edit" size="sm" variant="ghost" title="Edit" @click="openEdit(r)" />
                <ButtonTable icon="trash" size="sm" variant="danger" title="Delete" @click="openDelete(r)" />
              </div>
            </li>
          </ul>
        </section>
      </main>
    </div>

    <!-- Edit Modal -->
    <dialog ref="dlg" class="modal fixed z-50 left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-[min(640px,95vw)] rounded-2xl bg-zinc-900 text-zinc-100 border border-zinc-700 shadow-2xl p-0">
      <div class="divide-y divide-zinc-800 rounded-2xl overflow-hidden">
        <header class="px-4 sm:px-5 py-3 flex items-center">
          <h3 class="font-semibold">Edit Peserta</h3>
          <button @click="cancelEdit" class="ml-auto inline-flex items-center justify-center size-8 rounded-lg hover:bg-zinc-800 text-zinc-300 hover:text-white cursor-pointer">✕</button>
        </header>

        <div class="p-4 sm:p-5 space-y-5">
          <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div class="sm:col-span-2">
              <label class="text-sm">Nama</label>
              <input v-model="editName" class="mt-1 w-full px-3 py-2 rounded-lg bg-zinc-800 border border-zinc-700 outline-none focus:ring-2 focus:ring-sky-500" />
            </div>
            <div>
              <label class="text-sm">UID</label>
              <input :value="editUID" disabled class="mt-1 w-full px-3 py-2 rounded-lg bg-zinc-800 border border-zinc-700 opacity-70" />
            </div>
          </div>

          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div class="space-y-4">
              <div class="text-sm mb-2">Foto saat ini</div>
              <img v-if="currentPhotoUrl" :src="currentPhotoUrl" class="size-[220px] object-cover rounded-xl border border-zinc-700 bg-zinc-800" />
              <div v-else class="size-[220px] rounded-xl border border-dashed border-zinc-700 grid place-items-center text-xs text-zinc-400">Tidak ada</div>
              <div>
                <label class="text-sm">Ganti Foto (opsional)</label>
                <input
                  ref="fileInp"
                  type="file"
                  accept="image/*"
                  @change="onFileChange"
                  class="cursor-pointer mt-1 w-full text-sm file:mr-3 file:px-3 file:py-2 file:rounded-lg file:border-0 file:bg-zinc-700 file:text-white hover:file:bg-zinc-600"
                />
                <p class="text-xs text-zinc-400 mt-1">Jika tidak dipilih, foto lama tetap dipakai.</p>
              </div>
            </div>
            <div class="space-y-4">
              <div class="text-sm mb-2">Preview foto baru</div>
              <img v-if="preview" :src="preview" class="size-[220px] object-cover rounded-xl border border-zinc-700 bg-zinc-800" />
              <div v-else class="size-[220px] rounded-xl border border-dashed border-zinc-700 grid place-items-center text-xs text-zinc-400">Belum dipilih</div>
              <button @click.prevent="clearPreview" class="cursor-pointer px-3 py-2 rounded-lg bg-zinc-800 border border-zinc-700 text-xs hover:bg-zinc-700">Bersihkan</button>
            </div>
          </div>
        </div>

        <footer class="px-4 sm:px-5 py-3 flex justify-end gap-2">
          <button @click="cancelEdit" class="cursor-pointer px-4 py-2 rounded-lg bg-zinc-800 border border-zinc-700 hover:bg-zinc-700">Batal</button>
          <button @click="saveEdit" class="cursor-pointer px-4 py-2 rounded-lg bg-sky-600 hover:bg-sky-500 text-white">Simpan</button>
        </footer>
      </div>
    </dialog>

    <!-- Delete Modal -->
    <dialog ref="delDlg" class="modal fixed z-50 left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-[min(420px,92vw)] rounded-2xl bg-zinc-900 text-zinc-100 border border-zinc-700 shadow-2xl p-0">
      <div class="divide-y divide-zinc-800 rounded-2xl overflow-hidden">
        <header class="px-4 py-3 font-semibold">Konfirmasi</header>
        <div class="px-4 py-4 text-sm">
          <p>Hapus peserta ini? Foto terkait juga akan dihapus.</p>
          <p v-if="delName" class="mt-2 text-zinc-400"><span class="text-zinc-300">Target:</span> {{ delName }} ({{ delUid }})</p>
        </div>
        <footer class="px-4 py-3 flex justify-end gap-2">
          <button @click="cancelDelete" class="cursor-pointer px-3 py-2 rounded-lg bg-zinc-800 border border-zinc-700 hover:bg-zinc-700">Batal</button>
          <button @click="confirmDelete" class="cursor-pointer px-3 py-2 rounded-lg bg-rose-600 hover:bg-rose-500 text-white">Hapus</button>
        </footer>
      </div>
    </dialog>

    <div v-if="sidebarOpen && !isDesktop" @click="sidebarOpen = false" class="fixed inset-0 bg-black/40 backdrop-blur-sm z-40" />
  </div>
</template>

<style>
.modal::backdrop {
  background: rgba(24, 24, 27, 0.6);
  backdrop-filter: blur(2px);
}
</style>
