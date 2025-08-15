<script setup lang="ts">
import { computed } from 'vue';

const props = defineProps<{
  icon: 'edit' | 'trash';
  variant?: 'ghost' | 'primary' | 'danger';
  size?: 'sm' | 'md';
  title?: string;
}>();

const emit = defineEmits<{ (e: 'click'): void }>();

const variantCls = computed(() => {
  switch (props.variant) {
    case 'primary':
      return 'bg-sky-600 text-white hover:bg-sky-500 border-transparent';
    case 'danger':
      return 'bg-rose-600 text-white hover:bg-rose-500 border-transparent';
    default:
      return 'bg-zinc-800 hover:bg-zinc-700 border border-zinc-700 text-zinc-100';
  }
});

const sizeCls = computed(() => (props.size === 'sm' ? 'size-8' : 'size-9'));
</script>

<template>
  <button
    :title="title"
    :aria-label="title"
    @click="$emit('click')"
    :class="['cursor-pointer inline-flex items-center justify-center rounded-lg transition focus:outline-none focus:ring-2 focus:ring-sky-500/40', variantCls, sizeCls]"
  >
    <svg v-if="icon === 'edit'" viewBox="0 0 24 24" class="size-4_5" fill="none" stroke="currentColor" stroke-width="1.8">
      <path d="M4 20h16" />
      <path d="M16.5 3.5l4 4L9 19H5v-4z" />
    </svg>
    <svg v-else-if="icon === 'trash'" viewBox="0 0 24 24" class="size-4_5" fill="none" stroke="currentColor" stroke-width="1.8">
      <path d="M3 6h18" />
      <path d="M8 6V4h8v2" />
      <path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6" />
    </svg>
  </button>
</template>

<style scoped>
.size-8 {
  width: 2rem;
  height: 2rem;
}
.size-9 {
  width: 2.25rem;
  height: 2.25rem;
}
.size-4_5 {
  width: 1.125rem;
  height: 1.125rem;
}
</style>
