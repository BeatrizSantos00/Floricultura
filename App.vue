<script setup>
const links = [
  { to: '/catalogo', texto: 'Catálogo' },
  { to: '/pedidos', texto: 'Pedidos' },
  { to: '/clientes', texto: 'Clientes' },
  { to: '/relatorios', texto: 'Relatórios' },
]
</script>

<template>
  <header class="nav">
    <div class="nav-in">
      <span class="logo">🌸 Flor Nova</span>
      <nav>
        <RouterLink v-for="l in links" :key="l.to" :to="l.to">{{ l.texto }}</RouterLink>
      </nav>
    </div>
  </header>
  <main class="container">
    <RouterView />
  </main>
  <footer class="rodape">Flor Nova · floricultura · feito com 💗</footer>
</template>

<style scoped>
.nav { background: #fff; border-bottom: 1px solid var(--borda); position: sticky; top: 0; z-index: 10; }
.nav-in { max-width: 1100px; margin: 0 auto; padding: 12px 20px; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px; }
.logo { font-size: 1.5rem; font-weight: 700; }
nav { display: flex; gap: 6px; flex-wrap: wrap; }
nav a { text-decoration: none; color: var(--suave); font-weight: 700; padding: 7px 16px; border-radius: 999px; }
nav a:hover { background: var(--rosa-claro); }
nav a.router-link-active { background: var(--rosa); color: #fff; }
.rodape { text-align: center; color: var(--suave); font-size: .85rem; padding: 20px; }
</style>
