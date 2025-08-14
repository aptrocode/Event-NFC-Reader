
<script setup lang="ts">
import { ref } from 'vue';
import { io } from 'socket.io-client';

const title = ref('Tempelkan gelang...');
const hint = ref('Menunggu tap berikutnya');
const photo = ref<string | null>(null);
const photoUrl = ref<string>('');

const socket = io({ path: '/socket.io' });

socket.on('nfc_tapped', async (msg: any) => {
  const uid = msg.uid;
  hint.value = 'Memproses...';
  try {
    const res = await fetch(`/api/participant/${uid}`);
    if (!res.ok) {
      title.value = 'Data tidak ditemukan';
      photo.value = null;
      photoUrl.value = '';
      hint.value = 'Menunggu tap berikutnya';
      return;
    }
    const j = await res.json();
    const { Nama, Foto } = j.data;
    title.value = Nama || '(Tanpa Nama)';
    photo.value = Foto || null;
    photoUrl.value = photo.value ? '/' + photo.value : '';
    hint.value = 'Menunggu tap berikutnya';
  } catch {
    title.value = 'Gagal memuat data';
    photo.value = null;
    photoUrl.value = '';
    hint.value = 'Menunggu tap berikutnya';
  }
});
</script>

<template>
  <main class="min-h-screen flex items-center justify-center p-4 text-center">
    <div class="w-full max-w-4xl">
      <h1 class="text-3xl sm:text-5xl font-extrabold mb-6">{{ title }}</h1>
      <div class="flex justify-center">
        <img v-if="photo" :src="photoUrl" class="max-h-[70vh] rounded-2xl shadow-lg border border-zinc-800 object-cover transition-opacity duration-300" />
      </div>
      <p class="mt-6 text-zinc-400 text-lg">{{ hint }}</p>
    </div>
  </main>
</template>
