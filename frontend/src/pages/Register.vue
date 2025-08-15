<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, computed } from 'vue';
import { io } from 'socket.io-client';

type ToastType = 'info' | 'success' | 'error';

const video = ref<HTMLVideoElement | null>(null);
const canvas = ref<HTMLCanvasElement | null>(null);
const streamRef = ref<MediaStream | null>(null);

const uid = ref('');
const name = ref('');
const dataURL = ref<string | null>(null);
const captured = ref(false);

const toast = ref('');
const toastType = ref<ToastType>('info');
let toastTimer: number | null = null;

// Socket.IO proxied di /socket.io -> Flask:5000
const socket = io({ path: '/socket.io' });
socket.on('nfc_tapped', (msg: { uid: string }) => {
  uid.value = msg.uid;
});

function showToast(msg: string, type: ToastType = 'info', ms = 2500) {
  toast.value = msg;
  toastType.value = type;
  if (toastTimer) window.clearTimeout(toastTimer);
  toastTimer = window.setTimeout(() => (toast.value = ''), ms);
}

async function startCamera() {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({
      video: { width: { ideal: 1280 }, height: { ideal: 720 } },
      audio: false,
    });
    streamRef.value = stream;
    if (video.value) video.value.srcObject = stream;
  } catch (e: unknown) {
    const msg = (e as any)?.message ?? String(e);
    showToast(`Gagal akses kamera: ${msg}`, 'error');
  }
}

function stopCamera() {
  streamRef.value?.getTracks().forEach((t) => t.stop());
  streamRef.value = null;
}

onMounted(startCamera);
onBeforeUnmount(() => {
  stopCamera();
  socket.removeAllListeners();
  socket.disconnect();
});

function capture() {
  if (!video.value || !canvas.value) return;
  const w = video.value.videoWidth || 1280;
  const h = video.value.videoHeight || 720;
  canvas.value.width = w;
  canvas.value.height = h;
  const ctx = canvas.value.getContext('2d');
  if (!ctx) return;
  ctx.drawImage(video.value, 0, 0, w, h);
  dataURL.value = canvas.value.toDataURL('image/jpeg', 0.9);
  captured.value = true;
  showToast('Foto diambil.', 'success');
}

function retake() {
  dataURL.value = null;
  captured.value = false;
  showToast('Silakan ambil ulang.', 'info');
}

const canSubmit = computed(() => Boolean(uid.value && name.value.trim() && dataURL.value));

async function submit() {
  if (!canSubmit.value) return;
  try {
    const res = await fetch('/api/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ uid: uid.value, name: name.value.trim(), photo: dataURL.value }),
    });
    const j = await res.json();
    if (!j.ok) throw new Error(j.error || 'Gagal menyimpan.');

    showToast('Registrasi berhasil! Gelang bisa dicabut.', 'success');
    name.value = '';
    uid.value = '';
    retake();
  } catch (e: any) {
    showToast(e?.message ?? String(e), 'error');
  }
}
</script>

<template>
  <div class="min-h-screen flex items-center justify-center p-4">
    <main class="w-full max-w-5xl">
      <header class="mb-6">
        <h1 class="text-2xl sm:text-3xl font-extrabold">Registrasi Peserta</h1>
        <p class="text-zinc-400 text-sm mt-1">Tap gelang NFC, isi nama, ambil foto.</p>
      </header>

      <section class="grid grid-cols-1 md:grid-cols-2 gap-6">
        <!-- Kamera -->
        <div class="rounded-2xl border border-zinc-800 bg-zinc-900/50 p-4">
          <div class="flex items-center justify-between mb-3">
            <div class="text-sm text-zinc-400">Kamera</div>
            <div :class="['text-xs px-2 py-1 rounded-lg border', uid ? 'bg-sky-900/30 border-sky-700 text-sky-200' : 'border-zinc-700 text-zinc-300']">
              UID: <span class="opacity-70">{{ uid || 'Belum tap' }}</span>
            </div>
          </div>

          <div class="relative aspect-video rounded-xl overflow-hidden bg-black border border-zinc-800">
            <video ref="video" autoplay playsinline class="w-full h-full object-cover" v-show="!captured" />
            <canvas ref="canvas" class="w-full h-full" v-show="captured" />
          </div>

          <div class="mt-4 flex gap-3">
            <button :disabled="captured" @click="capture" class="cursor-pointer px-4 py-2 rounded-xl bg-sky-600 hover:bg-sky-500 text-white disabled:opacity-50 disabled:cursor-not-allowed">
              Ambil Foto
            </button>
            <button
              :disabled="!captured"
              @click="retake"
              class="cursor-pointer px-4 py-2 rounded-xl bg-zinc-800 hover:bg-zinc-700 border border-zinc-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Ulangi
            </button>
          </div>

          <p class="text-xs text-zinc-400 mt-2">Pastikan wajah jelas & pencahayaan cukup.</p>
        </div>

        <!-- Form -->
        <div class="rounded-2xl border border-zinc-800 bg-zinc-900/50 p-4">
          <label class="block text-sm font-medium mb-1">Nama Peserta</label>
          <input v-model="name" type="text" placeholder="cth: Andi Pratama" class="w-full px-3 py-2 rounded-xl bg-zinc-800 border border-zinc-700 outline-none focus:ring-2 focus:ring-sky-500" />
          <p class="text-xs text-zinc-400 mt-1">Tersimpan ke CSV, foto ke folder <code>foto_peserta/</code>.</p>

          <div class="mt-6 flex items-center gap-3">
            <button :disabled="!canSubmit" @click="submit" class="cursor-pointer px-5 py-2 rounded-xl bg-sky-600 hover:bg-sky-500 text-white disabled:opacity-50 disabled:cursor-not-allowed">
              Simpan Registrasi
            </button>

            <RouterLink to="/" class="cursor-pointer inline-flex items-center justify-center px-4 py-2 rounded-xl bg-zinc-800 hover:bg-zinc-700 border border-zinc-700"> Kembali </RouterLink>
          </div>

          <div
            v-if="toast"
            :class="[
              'mt-4 px-3 py-2 text-sm rounded-xl border',
              toastType === 'error' ? 'bg-rose-900/30 border-rose-700 text-rose-200' : toastType === 'success' ? 'bg-sky-900/30 border-sky-700 text-sky-200' : 'bg-zinc-800 border-zinc-700',
            ]"
            role="status"
            aria-live="polite"
          >
            {{ toast }}
          </div>
        </div>
      </section>
    </main>
  </div>
</template>
