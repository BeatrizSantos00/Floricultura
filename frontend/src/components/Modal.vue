<script setup>
defineProps({ titulo: String })
const emit = defineEmits(['fechar'])
</script>

<template>
  <div class="fundo" @click.self="emit('fechar')">
    <div class="janela card">
      <div class="cab">
        <h2>{{ titulo }}</h2>
        <button class="x" @click="emit('fechar')" aria-label="Fechar">✕</button>
      </div>
      <slot />
    </div>
  </div>
</template>

<style scoped>
.fundo { position: fixed; inset: 0; background: rgba(74, 44, 58, .45); display: flex; align-items: center; justify-content: center; padding: 16px; z-index: 50; }
.janela { width: 100%; max-width: 560px; max-height: 90vh; overflow-y: auto; }
.cab { display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; }
.x { border: none; background: none; font-size: 1.1rem; cursor: pointer; color: var(--suave); }
</style>
