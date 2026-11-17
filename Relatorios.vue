<script setup>
import { ref, computed, onMounted } from 'vue'
import { api, moeda, rotulosStatus, rotulosCategoria } from '../api'

const resumo = ref(null)
const maisVendidos = ref([])
const porCategoria = ref([])
const porDia = ref([])
const melhores = ref([])
const erro = ref('')

onMounted(async () => {
  try {
    ;[resumo.value, maisVendidos.value, porCategoria.value, porDia.value, melhores.value] = await Promise.all([
      api.relatorios.resumo(),
      api.relatorios.maisVendidos(),
      api.relatorios.porCategoria(),
      api.relatorios.porDia(),
      api.relatorios.melhoresClientes(),
    ])
  } catch (e) {
    erro.value = e.message
  }
})

const maxQtd = computed(() => Math.max(1, ...maisVendidos.value.map((p) => p.quantidade)))
const maxCat = computed(() => Math.max(1, ...porCategoria.value.map((c) => c.receita)))
const maxDia = computed(() => Math.max(1, ...porDia.value.map((d) => d.faturamento)))
const pct = (v, max) => `${Math.max(4, (v / max) * 100)}%`
const diaBR = (s) => s.slice(8, 10) + '/' + s.slice(5, 7)
</script>

<template>
  <div class="topo">
    <div>
      <h1>Relatórios</h1>
      <p>Como está o jardim de vendas (pedidos cancelados não contam)</p>
    </div>
  </div>

  <div v-if="erro" class="erro">{{ erro }}</div>

  <template v-if="resumo">
    <div class="kpis">
      <div class="card kpi"><span>Faturamento</span><strong>{{ moeda(resumo.faturamento) }}</strong></div>
      <div class="card kpi"><span>Pedidos</span><strong>{{ resumo.pedidos }}</strong></div>
      <div class="card kpi"><span>Ticket médio</span><strong>{{ moeda(resumo.ticket_medio) }}</strong></div>
      <div class="card kpi"><span>Clientes</span><strong>{{ resumo.clientes }}</strong></div>
    </div>

    <div class="status-linha">
      <span v-for="(qtd, st) in resumo.por_status" :key="st" class="badge" :class="st">
        {{ rotulosStatus[st] }}: {{ qtd }}
      </span>
    </div>

    <div class="duas">
      <div class="card">
        <h3>🌹 Produtos mais vendidos</h3>
        <div v-for="p in maisVendidos" :key="p.produto_id" class="barra-linha">
          <div class="rotulo"><span>{{ p.nome }}</span><small>{{ p.quantidade }} un · {{ moeda(p.receita) }}</small></div>
          <div class="trilho"><div class="barra" :style="{ width: pct(p.quantidade, maxQtd) }"></div></div>
        </div>
        <p v-if="!maisVendidos.length" class="vazio">Sem vendas ainda</p>
      </div>

      <div class="card">
        <h3>🌿 Receita por categoria</h3>
        <div v-for="c in porCategoria" :key="c.categoria" class="barra-linha">
          <div class="rotulo"><span>{{ rotulosCategoria[c.categoria] || c.categoria }}</span><small>{{ moeda(c.receita) }}</small></div>
          <div class="trilho"><div class="barra verde" :style="{ width: pct(c.receita, maxCat) }"></div></div>
        </div>
        <p v-if="!porCategoria.length" class="vazio">Sem vendas ainda</p>
      </div>
    </div>

    <div class="card" style="margin-top:16px">
      <h3>📅 Faturamento por dia</h3>
      <div class="colunas">
        <div v-for="d in porDia" :key="d.data" class="coluna" :title="`${diaBR(d.data)} — ${moeda(d.faturamento)} (${d.pedidos} pedidos)`">
          <div class="pilar" :style="{ height: pct(d.faturamento, maxDia) }"></div>
          <small>{{ diaBR(d.data) }}</small>
        </div>
      </div>
      <p v-if="!porDia.length" class="vazio">Sem vendas ainda</p>
    </div>

    <div class="card" style="margin-top:16px; overflow-x:auto">
      <h3>💗 Melhores clientes</h3>
      <table>
        <thead><tr><th>#</th><th>Cliente</th><th>Pedidos</th><th>Total gasto</th></tr></thead>
        <tbody>
          <tr v-for="(c, i) in melhores" :key="c.cliente_id">
            <td>{{ i + 1 }}</td><td>{{ c.nome }}</td><td>{{ c.pedidos }}</td><td>{{ moeda(c.total_gasto) }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </template>
</template>

<style scoped>
.kpis { display: grid; gap: 14px; grid-template-columns: repeat(auto-fit, minmax(190px, 1fr)); margin-bottom: 14px; }
.kpi { display: flex; flex-direction: column; }
.kpi span { color: var(--suave); font-size: .85rem; font-weight: 700; }
.kpi strong { font-family: Georgia, serif; font-size: 1.7rem; color: var(--rosa-escuro); }
.status-linha { display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 18px; }
.duas { display: grid; gap: 16px; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); }
h3 { margin-bottom: 12px; font-size: 1.1rem; }
.barra-linha { margin-bottom: 11px; }
.rotulo { display: flex; justify-content: space-between; gap: 8px; font-size: .9rem; margin-bottom: 3px; }
.rotulo small { color: var(--suave); }
.trilho { background: var(--rosa-claro); border-radius: 999px; height: 10px; }
.barra { background: var(--rosa); height: 100%; border-radius: 999px; }
.barra.verde { background: var(--verde); }
.colunas { display: flex; align-items: flex-end; gap: 6px; height: 180px; overflow-x: auto; padding-bottom: 4px; }
.coluna { flex: 1; min-width: 28px; height: 100%; display: flex; flex-direction: column; justify-content: flex-end; align-items: center; gap: 4px; }
.pilar { width: 100%; max-width: 34px; background: linear-gradient(var(--rosa), #f783ac); border-radius: 8px 8px 0 0; }
.coluna small { font-size: .65rem; color: var(--suave); }
</style>
