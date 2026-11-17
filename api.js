// Cliente HTTP simples para a API do Flor Nova.
// Em desenvolvimento o Vite faz proxy de /api para http://localhost:8000.
const BASE = import.meta.env.VITE_API_URL || '/api'

async function req(caminho, opcoes = {}) {
  const resp = await fetch(BASE + caminho, {
    headers: { 'Content-Type': 'application/json' },
    ...opcoes,
    body: opcoes.body ? JSON.stringify(opcoes.body) : undefined,
  })
  if (resp.status === 204) return null
  const dados = await resp.json().catch(() => null)
  if (!resp.ok) {
    let msg = dados?.detail
    if (Array.isArray(msg)) msg = msg.map((e) => `${e.loc?.slice(1).join('.')}: ${e.msg}`).join(' | ')
    throw new Error(msg || `Erro ${resp.status}`)
  }
  return dados
}

const qs = (params = {}) => {
  const limpo = Object.fromEntries(Object.entries(params).filter(([, v]) => v !== '' && v != null))
  const s = new URLSearchParams(limpo).toString()
  return s ? `?${s}` : ''
}

export const api = {
  produtos: {
    listar: (params) => req('/produtos' + qs(params)),
    criar: (body) => req('/produtos', { method: 'POST', body }),
    atualizar: (id, body) => req(`/produtos/${id}`, { method: 'PUT', body }),
    remover: (id) => req(`/produtos/${id}`, { method: 'DELETE' }),
  },
  clientes: {
    listar: (params) => req('/clientes' + qs(params)),
    criar: (body) => req('/clientes', { method: 'POST', body }),
    atualizar: (id, body) => req(`/clientes/${id}`, { method: 'PUT', body }),
    remover: (id) => req(`/clientes/${id}`, { method: 'DELETE' }),
  },
  pedidos: {
    listar: (params) => req('/pedidos' + qs(params)),
    criar: (body) => req('/pedidos', { method: 'POST', body }),
    mudarStatus: (id, status) => req(`/pedidos/${id}/status`, { method: 'PATCH', body: { status } }),
  },
  relatorios: {
    resumo: () => req('/relatorios/resumo'),
    maisVendidos: () => req('/relatorios/produtos-mais-vendidos'),
    porCategoria: () => req('/relatorios/vendas-por-categoria'),
    porDia: () => req('/relatorios/vendas-por-dia'),
    melhoresClientes: () => req('/relatorios/melhores-clientes'),
  },
}

export const moeda = (v) =>
  Number(v || 0).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })

export const rotulosStatus = {
  recebido: 'Recebido',
  em_preparo: 'Em preparo',
  saiu_para_entrega: 'Saiu para entrega',
  entregue: 'Entregue',
  cancelado: 'Cancelado',
}

export const rotulosCategoria = {
  buques: 'Buquês',
  arranjos: 'Arranjos',
  plantas: 'Plantas',
  cestas: 'Cestas',
  presentes: 'Presentes',
}
