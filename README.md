# 🌸 Flor Nova

Sistema de floricultura com **catálogo, pedidos, clientes e relatórios**.
Projeto de Banco de Dados (NoSQL) — Fatec.

| Camada    | Tecnologia                  |
|-----------|-----------------------------|
| Banco     | MongoDB                     |
| Backend   | FastAPI (Python) + PyMongo  |
| Frontend  | Vue 3 + Vite + Vue Router   |

## Funcionalidades

- **Catálogo**: CRUD de produtos (buquês, arranjos, plantas, cestas, presentes), filtro por categoria e busca por nome, alerta de estoque baixo.
- **Clientes**: CRUD com endereço, e-mail único e observações (datas especiais, flores preferidas).
- **Pedidos**: vários itens por pedido, entrega ou retirada, data e mensagem de cartão. Baixa de estoque automática e fluxo de status controlado.
- **Relatórios**: faturamento, ticket médio, produtos mais vendidos, receita por categoria, faturamento por dia e melhores clientes (Aggregation Framework).

## Como rodar

### 1. MongoDB

Com Docker:

```bash
docker compose up -d
```

Ou use um MongoDB já instalado em `localhost:27017`.

### 2. Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env             # Windows: copy .env.example .env

python -m app.seed               # dados de exemplo (use --reset para recriar)
uvicorn app.main:app --reload
```

- API: http://localhost:8000
- Documentação interativa (Swagger): http://localhost:8000/docs

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

Abra http://localhost:5173 (o Vite encaminha `/api` para o backend na porta 8000).

### Testes

```bash
cd backend
pytest
```

Os testes usam `mongomock` (MongoDB em memória), então não precisam do banco rodando.

## Modelagem (coleções)

```text
produtos  { _id, nome, descricao, categoria, preco, estoque, emoji, ativo }

clientes  { _id, nome, email (único), telefone,
            endereco: { rua, bairro, cidade }, observacoes, criado_em }

pedidos   { _id, cliente_id, cliente_nome,
            itens: [ { produto_id, nome, categoria, quantidade, preco_unitario } ],
            total, status, tipo_entrega, data_entrega, mensagem_cartao, criado_em }
```

**Decisões de modelagem**

- **Embutir** (`endereco` em clientes, `itens` em pedidos): os dados são sempre lidos juntos, então uma consulta só já traz tudo.
- **Referenciar** (`cliente_id`, `produto_id`): clientes e produtos existem e mudam por conta própria.
- **Desnormalizar** (`cliente_nome`, `nome`, `categoria` e `preco_unitario` dentro do pedido): o pedido guarda uma "foto" do que foi vendido. Se o preço do produto mudar depois, o histórico continua correto, e os relatórios dispensam `$lookup`.
- **Índices**: `clientes.email` (único), `produtos.categoria`, `pedidos.status`, `pedidos.cliente_id` e `pedidos.criado_em`.

## Regras de negócio

- A baixa de estoque é atômica por produto (`update_one` com filtro `estoque >= quantidade` e `$inc`). Se algum item não tiver estoque, as baixas já feitas são desfeitas e o pedido não é criado.
- Cancelar um pedido devolve o estoque.
- Fluxo de status:

```text
recebido → em_preparo → saiu_para_entrega → entregue
   └──────────┴──→ cancelado        (retirada pula "saiu_para_entrega")
```

- Pedido com entrega exige cliente com endereço cadastrado.
- Cliente que já tem pedidos não pode ser removida.
- Pedidos cancelados não entram nos relatórios de faturamento.

## Endpoints

| Método | Rota | Descrição |
|--------|------|-----------|
| GET/POST | `/api/produtos` | Lista (filtros `categoria`, `q`, `apenas_ativos`) / cria |
| GET/PUT/DELETE | `/api/produtos/{id}` | Detalhe / atualiza / remove |
| GET/POST | `/api/clientes` | Lista (filtro `q`) / cria |
| GET/PUT/DELETE | `/api/clientes/{id}` | Detalhe / atualiza / remove |
| GET | `/api/clientes/{id}/pedidos` | Pedidos da cliente |
| GET/POST | `/api/pedidos` | Lista (filtros `status`, `cliente_id`) / cria |
| GET | `/api/pedidos/{id}` | Detalhe |
| PATCH | `/api/pedidos/{id}/status` | Muda o status |
| GET | `/api/relatorios/resumo` | Faturamento, pedidos, ticket médio, por status |
| GET | `/api/relatorios/produtos-mais-vendidos` | Top produtos |
| GET | `/api/relatorios/vendas-por-categoria` | Receita por categoria |
| GET | `/api/relatorios/vendas-por-dia` | Faturamento diário |
| GET | `/api/relatorios/melhores-clientes` | Ranking de clientes |

## Estrutura

```text
flor-nova/
├── docker-compose.yml
├── backend/
│   ├── app/
│   │   ├── main.py          # app FastAPI, CORS, rotas
│   │   ├── database.py      # conexão e índices
│   │   ├── schemas.py       # validação (Pydantic)
│   │   ├── utils.py         # ObjectId <-> str
│   │   ├── seed.py          # dados de exemplo
│   │   └── routers/         # produtos, clientes, pedidos, relatorios
│   └── tests/test_api.py
└── frontend/
    └── src/
        ├── api.js           # chamadas HTTP e formatadores
        ├── views/           # Catalogo, Pedidos, Clientes, Relatorios
        └── components/Modal.vue
```
