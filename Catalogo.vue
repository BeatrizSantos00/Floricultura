<script setup>
import { ref, onMounted, watch } from 'vue'
import { api, moeda, rotulosCategoria } from '../api'
import Modal from '../components/Modal.vue'

const produtos = ref([])
const categoria = ref('')
const busca = ref('')
const erro = ref('')
const modal = ref(false)
const editandoId = ref(null)

const vazio = () => ({ nome: '', descricao: '', categoria: 'buques', preco: 0, estoque: 0, emoji: '🌸', ativo: true })
const form = ref(vazio())

async function carregar() {
  try {
    erro.value = ''
    produtos.value = await api.produtos.listar({ categoria: categoria.value, q: busca.value })
  } catch (e) {
    erro.value = e.message
  }
}

function novo() {
  editandoId.value = null
  form.value = vazio()
  modal.value = true
}

function editar(p) {
  editandoId.value = p.id
  const { id, ...resto } = p
  form.value = { ...resto }
  modal.value = true
}

async function salvar() {
  try {
    erro.value = ''
    const corpo = { ...form.value, preco: Number(form.value.preco), estoque: Number(form.value.estoque) }
    if (editandoId.value) await api.produtos.atualizar(editandoId.value, corpo)
    else await api.produtos.criar(corpo)
    modal.value = false
    await carregar()
  } catch (e) {
    erro.value = e.message
  }
}

async function remover(p) {
  if (!confirm(`Remover "${p.nome}" do catálogo?`)) return
  try {
    await api.produtos.remover(p.id)
    await carregar()
  } catch (e) {
    erro.value = e.message
  }
}

onMounted(carregar)
watch([categoria, busca], carregar)
</script>

<template>
  <div class="topo">
    <div>
      <h1>Catálogo</h1>
      <p>Buquês, arranjos, plantas e presentes</p>
    </div>
    <button class="btn" @click="novo">+ Novo produto</button>
  </div>

  <div class="filtros">
    <button class="chip" :class="{ ativo: categoria === '' }" @click="categoria = ''">Todos</button>
    <button
      v-for="(rotulo, chave) in rotulosCategoria"
      :key="chave"
      class="chip"
      :class="{ ativo: categoria === chave }"
      @click="categoria = chave"
    >
      {{ rotulo }}
    </button>
    <input v-model="busca" placeholder="Buscar pelo nome..." />
  </div>

  <div v-if="erro" class="erro">{{ erro }}</div>
  <p v-if="!produtos.length" class="vazio">Nenhum produto encontrado 🌱</p>

  <div class="grid">
    <div v-for="p in produtos" :key="p.id" class="card prod" :class="{ inativo: !p.ativo }">
      <div class="emoji">{{ p.emoji }}</div>
      <h3>{{ p.nome }}</h3>
      <p class="desc">{{ p.descricao }}</p>
      <div class="meta">
        <strong class="preco">{{ moeda(p.preco) }}</strong>
        <span v-if="p.estoque === 0" class="badge zerado">Sem estoque</span>
        <span v-else-if="p.estoque <= 5" class="badge baixo">Restam {{ p.estoque }}</span>
        <span v-else class="badge entregue">{{ p.estoque }} em estoque</span>
      </div>
      <p v-if="!p.ativo" class="desc">Inativo</p>
      <div class="acoes">
        <button class="btn sec pq" @click="editar(p)">Editar</button>
        <button class="btn perigo pq" @click="remover(p)">Remover</button>
      </div>
    </div>
  </div>

  <Modal v-if="modal" :titulo="editandoId ? 'Editar produto' : 'Novo produto'" @fechar="modal = false">
    <form @submit.prevent="salvar">
      <label>Nome</label>
      <input v-model="form.nome" required minlength="2" />
      <label>Descrição</label>
      <textarea v-model="form.descricao" rows="2"></textarea>
      <div class="linha">
        <div>
          <label>Categoria</label>
          <select v-model="form.categoria">
            <option v-for="(rotulo, chave) in rotulosCategoria" :key="chave" :value="chave">{{ rotulo }}</option>
          </select>
        </div>
        <div>
          <label>Emoji</label>
          <input v-model="form.emoji" maxlength="8" />
        </div>
        <div>
          <label>Preço (R$)</label>
          <input v-model="form.preco" type="number" step="0.01" min="0.01" required />
        </div>
        <div>
          <label>Estoque</label>
          <input v-model="form.estoque" type="number" min="0" required />
        </div>
      </div>
      <label><input v-model="form.ativo" type="checkbox" style="width:auto" /> Produto ativo</label>
      <div v-if="erro" class="erro" style="margin-top:12px">{{ erro }}</div>
      <div class="acoes" style="margin-top:16px">
        <button class="btn" type="submit">Salvar</button>
        <button class="btn sec" type="button" @click="modal = false">Cancelar</button>
      </div>
    </form>
  </Modal>
</template>

<style scoped>
.prod { display: flex; flex-direction: column; gap: 6px; }
.prod.inativo { opacity: .6; }
.emoji { font-size: 2.6rem; background: var(--rosa-claro); width: 70px; height: 70px; border-radius: 50%; display: flex; align-items: center; justify-content: center; }
.prod h3 { font-size: 1.1rem; }
.desc { color: var(--suave); margin: 0; font-size: .88rem; flex: 1; }
.meta { display: flex; justify-content: space-between; align-items: center; }
.preco { color: var(--rosa-escuro); font-size: 1.15rem; }
</style>
