import { createApp } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'
import App from './App.vue'
import './style.css'

import Catalogo from './views/Catalogo.vue'
import Pedidos from './views/Pedidos.vue'
import Clientes from './views/Clientes.vue'
import Relatorios from './views/Relatorios.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', redirect: '/catalogo' },
    { path: '/catalogo', component: Catalogo },
    { path: '/pedidos', component: Pedidos },
    { path: '/clientes', component: Clientes },
    { path: '/relatorios', component: Relatorios },
  ],
})

createApp(App).use(router).mount('#app')
