<script setup lang="ts"></script>

<template>
  <main class="min-h-screen flex items-center justify-center p-6">
    <div class="w-full max-w-5xl grid grid-cols-1 md:grid-cols-3 gap-6">
      <RouterLink to="/register" class="bg-zinc-900 border border-zinc-800 rounded-2xl p-6 flex flex-col items-center text-center hover:bg-zinc-800 transition">
        <div class="text-3xl mb-3">📝</div>
        <h2 class="text-xl font-bold mb-2">Register Peserta</h2>
        <p class="text-zinc-400 text-sm">Daftarkan peserta dengan foto & UID NFC.</p>
      </RouterLink>
      <RouterLink to="/booth" class="bg-zinc-900 border border-zinc-800 rounded-2xl p-6 flex flex-col items-center text-center hover:bg-zinc-800 transition">
        <div class="text-3xl mb-3">🎯</div>
        <h2 class="text-xl font-bold mb-2">Booth Scanner</h2>
        <p class="text-zinc-400 text-sm">Tampilkan nama & foto saat tap NFC.</p>
      </RouterLink>
      <RouterLink to="/dashboard" class="bg-zinc-900 border border-zinc-800 rounded-2xl p-6 flex flex-col items-center text-center hover:bg-zinc-800 transition">
        <div class="text-3xl mb-3">📊</div>
        <h2 class="text-xl font-bold mb-2">Dashboard</h2>
        <p class="text-zinc-400 text-sm">Kelola data peserta (CRUD).</p>
      </RouterLink>
    </div>
  </main>
</template>
