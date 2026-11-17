<script setup>
import { ref, onMounted, watch } from 'vue'
import { api } from '../api'
import Modal from '../components/Modal.vue'

const clientes = ref([])
const busca = ref('')
const erro = ref('')
const modal = ref(false)
const editandoId = ref(null)

const vazio = () => ({ nome: '', email: '', telefone: '', endereco: { rua: '', bairro: '', cidade: '' }, observacoes: '' })
const form = ref(vazio())

async function carregar() {
  try {
    clientes.value = await api.clientes.listar({ q: busca.value })
  } catch (e) {
    erro.value = e.message
  }
}

function nova() {
  editandoId.value = null
  form.value = vazio()
  erro.value = ''
  modal.value = true
}

function editar(c) {
  editandoId.value = c.id
  form.value = {
    nome: c.nome,
    email: c.email,
    telefone: c.telefone,
    endereco: { ...c.endereco },
    observacoes: c.observacoes,
  }
  erro.value = ''
  modal.value = true
}

async function salvar() {
  try {
    erro.value = ''
    if (editandoId.value) await api.clientes.atualizar(editandoId.value, form.value)
    else await api.clientes.criar(form.value)
    modal.value = false
    await carregar()
  } catch (e) {
    erro.value = e.message
  }
}

async function remover(c) {
  if (!confirm(`Remover ${c.nome}?`)) return
  try {
    erro.value = ''
    await api.clientes.remover(c.id)
    await carregar()
  } catch (e) {
    erro.value = e.message
  }
}

onMounted(carregar)
watch(busca, carregar)
</script>

<template>
  <div class="topo">
    <div>
      <h1>Clientes</h1>
      <p>Quem leva flores para casa</p>
    </div>
    <button class="btn" @click="nova">+ Nova cliente</button>
  </div>

  <div class="filtros"><input v-model="busca" placeholder="Buscar por nome ou e-mail..." /></div>
  <div v-if="erro && !modal" class="erro">{{ erro }}</div>

  <div class="card" style="overflow-x:auto">
    <table>
      <thead>
        <tr><th>Nome</th><th>Contato</th><th>Endereço</th><th></th></tr>
      </thead>
      <tbody>
        <tr v-for="c in clientes" :key="c.id">
          <td><strong>{{ c.nome }}</strong></td>
          <td>{{ c.email }}<br /><small>{{ c.telefone }}</small></td>
          <td>
            <span v-if="c.endereco?.rua">{{ c.endereco.rua }}<br /><small>{{ c.endereco.bairro }} · {{ c.endereco.cidade }}</small></span>
            <small v-else>—</small>
          </td>
          <td class="acoes">
            <button class="btn sec pq" @click="editar(c)">Editar</button>
            <button class="btn perigo pq" @click="remover(c)">Remover</button>
          </td>
        </tr>
      </tbody>
    </table>
    <p v-if="!clientes.length" class="vazio">Nenhuma cliente cadastrada 🌱</p>
  </div>

  <Modal v-if="modal" :titulo="editandoId ? 'Editar cliente' : 'Nova cliente'" @fechar="modal = false">
    <form @submit.prevent="salvar">
      <label>Nome</label>
      <input v-model="form.nome" required minlength="2" />
      <div class="linha">
        <div><label>E-mail</label><input v-model="form.email" type="email" required /></div>
        <div><label>Telefone</label><input v-model="form.telefone" /></div>
      </div>
      <label>Rua e número</label>
      <input v-model="form.endereco.rua" />
      <div class="linha">
        <div><label>Bairro</label><input v-model="form.endereco.bairro" /></div>
        <div><label>Cidade</label><input v-model="form.endereco.cidade" /></div>
      </div>
      <label>Observações</label>
      <textarea v-model="form.observacoes" rows="2" placeholder="Ex.: datas especiais, flores preferidas"></textarea>
      <div v-if="erro" class="erro" style="margin-top:12px">{{ erro }}</div>
      <div class="acoes" style="margin-top:16px">
        <button class="btn" type="submit">Salvar</button>
        <button class="btn sec" type="button" @click="modal = false">Cancelar</button>
      </div>
    </form>
  </Modal>
</template>
