<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { api, moeda, rotulosStatus } from '../api'
import Modal from '../components/Modal.vue'

const pedidos = ref([])
const clientes = ref([])
const produtos = ref([])
const filtroStatus = ref('')
const erro = ref('')
const modal = ref(false)

const vazio = () => ({
  cliente_id: '',
  tipo_entrega: 'entrega',
  data_entrega: '',
  mensagem_cartao: '',
  itens: [{ produto_id: '', quantidade: 1 }],
})
const form = ref(vazio())

async function carregar() {
  try {
    pedidos.value = await api.pedidos.listar({ status: filtroStatus.value })
  } catch (e) {
    erro.value = e.message
  }
}

async function abrirModal() {
  erro.value = ''
  form.value = vazio()
  ;[clientes.value, produtos.value] = await Promise.all([
    api.clientes.listar(),
    api.produtos.listar({ apenas_ativos: true }),
  ])
  modal.value = true
}

const totalPrevisto = computed(() =>
  form.value.itens.reduce((soma, item) => {
    const p = produtos.value.find((x) => x.id === item.produto_id)
    return soma + (p ? p.preco * (Number(item.quantidade) || 0) : 0)
  }, 0),
)

const addItem = () => form.value.itens.push({ produto_id: '', quantidade: 1 })
const removerItem = (i) => form.value.itens.splice(i, 1)

async function salvar() {
  try {
    erro.value = ''
    const corpo = {
      cliente_id: form.value.cliente_id,
      tipo_entrega: form.value.tipo_entrega,
      mensagem_cartao: form.value.mensagem_cartao,
      data_entrega: form.value.data_entrega || null,
      itens: form.value.itens.map((i) => ({ produto_id: i.produto_id, quantidade: Number(i.quantidade) })),
    }
    await api.pedidos.criar(corpo)
    modal.value = false
    await carregar()
  } catch (e) {
    erro.value = e.message
  }
}

// próximo passo do fluxo para cada pedido
function proximo(p) {
  if (p.status === 'recebido') return { status: 'em_preparo', texto: 'Iniciar preparo' }
  if (p.status === 'em_preparo')
    return p.tipo_entrega === 'entrega'
      ? { status: 'saiu_para_entrega', texto: 'Saiu para entrega' }
      : { status: 'entregue', texto: 'Marcar retirado' }
  if (p.status === 'saiu_para_entrega') return { status: 'entregue', texto: 'Marcar entregue' }
  return null
}
const podeCancelar = (p) => ['recebido', 'em_preparo'].includes(p.status)

async function mudar(p, status) {
  try {
    erro.value = ''
    await api.pedidos.mudarStatus(p.id, status)
    await carregar()
  } catch (e) {
    erro.value = e.message
  }
}

const dataBR = (iso) => new Date(iso).toLocaleDateString('pt-BR')
const dataEntregaBR = (s) => (s ? s.split('-').reverse().join('/') : '—')

onMounted(carregar)
watch(filtroStatus, carregar)
</script>

<template>
  <div class="topo">
    <div>
      <h1>Pedidos</h1>
      <p>Acompanhe cada buquê, da encomenda à entrega</p>
    </div>
    <button class="btn" @click="abrirModal">+ Novo pedido</button>
  </div>

  <div class="filtros">
    <button class="chip" :class="{ ativo: filtroStatus === '' }" @click="filtroStatus = ''">Todos</button>
    <button
      v-for="(rotulo, chave) in rotulosStatus"
      :key="chave"
      class="chip"
      :class="{ ativo: filtroStatus === chave }"
      @click="filtroStatus = chave"
    >
      {{ rotulo }}
    </button>
  </div>

  <div v-if="erro && !modal" class="erro">{{ erro }}</div>
  <p v-if="!pedidos.length" class="vazio">Nenhum pedido por aqui 🌱</p>

  <div class="lista">
    <div v-for="p in pedidos" :key="p.id" class="card pedido">
      <div class="linha-topo">
        <div>
          <strong>{{ p.cliente_nome }}</strong>
          <small> · pedido de {{ dataBR(p.criado_em) }}</small>
        </div>
        <span class="badge" :class="p.status">{{ rotulosStatus[p.status] }}</span>
      </div>

      <ul class="itens">
        <li v-for="i in p.itens" :key="i.produto_id">
          {{ i.quantidade }}× {{ i.nome }} <span class="suave">({{ moeda(i.preco_unitario) }})</span>
        </li>
      </ul>

      <p v-if="p.mensagem_cartao" class="cartao">💌 “{{ p.mensagem_cartao }}”</p>

      <div class="rodape-card">
        <div class="suave">
          {{ p.tipo_entrega === 'entrega' ? '🚚 Entrega' : '🛍️ Retirada' }} em {{ dataEntregaBR(p.data_entrega) }}
        </div>
        <strong class="total">{{ moeda(p.total) }}</strong>
      </div>

      <div class="acoes" v-if="proximo(p) || podeCancelar(p)">
        <button v-if="proximo(p)" class="btn verde pq" @click="mudar(p, proximo(p).status)">
          {{ proximo(p).texto }}
        </button>
        <button v-if="podeCancelar(p)" class="btn perigo pq" @click="mudar(p, 'cancelado')">Cancelar</button>
      </div>
    </div>
  </div>

  <Modal v-if="modal" titulo="Novo pedido" @fechar="modal = false">
    <form @submit.prevent="salvar">
      <label>Cliente</label>
      <select v-model="form.cliente_id" required>
        <option disabled value="">Selecione...</option>
        <option v-for="c in clientes" :key="c.id" :value="c.id">{{ c.nome }}</option>
      </select>

      <label>Itens</label>
      <div v-for="(item, i) in form.itens" :key="i" class="item-linha">
        <select v-model="item.produto_id" required>
          <option disabled value="">Produto...</option>
          <option v-for="p in produtos" :key="p.id" :value="p.id" :disabled="p.estoque === 0">
            {{ p.emoji }} {{ p.nome }} — {{ moeda(p.preco) }} ({{ p.estoque }})
          </option>
        </select>
        <input v-model="item.quantidade" type="number" min="1" max="100" required style="max-width:80px" />
        <button type="button" class="btn perigo pq" :disabled="form.itens.length === 1" @click="removerItem(i)">✕</button>
      </div>
      <button type="button" class="btn sec pq" @click="addItem">+ adicionar item</button>

      <div class="linha">
        <div>
          <label>Tipo</label>
          <select v-model="form.tipo_entrega">
            <option value="entrega">Entrega</option>
            <option value="retirada">Retirada</option>
          </select>
        </div>
        <div>
          <label>Data</label>
          <input v-model="form.data_entrega" type="date" />
        </div>
      </div>
      <label>Mensagem do cartão</label>
      <textarea v-model="form.mensagem_cartao" rows="2" maxlength="200"></textarea>

      <p class="total-prev">Total: <strong>{{ moeda(totalPrevisto) }}</strong></p>
      <div v-if="erro" class="erro">{{ erro }}</div>
      <div class="acoes">
        <button class="btn" type="submit">Registrar pedido</button>
        <button class="btn sec" type="button" @click="modal = false">Cancelar</button>
      </div>
    </form>
  </Modal>
</template>

<style scoped>
.lista { display: grid; gap: 14px; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); }
.pedido { display: flex; flex-direction: column; gap: 8px; }
.linha-topo { display: flex; justify-content: space-between; align-items: center; gap: 8px; }
.itens { margin: 0; padding-left: 18px; }
.suave { color: var(--suave); font-size: .85rem; }
.cartao { margin: 0; background: var(--rosa-claro); border-radius: 12px; padding: 8px 12px; font-style: italic; }
.rodape-card { display: flex; justify-content: space-between; align-items: center; border-top: 1px dashed var(--borda); padding-top: 8px; }
.total { color: var(--rosa-escuro); font-size: 1.15rem; }
.item-linha { display: flex; gap: 8px; margin-bottom: 8px; align-items: center; }
.total-prev { font-size: 1.1rem; margin: 14px 0 8px; }
</style>
