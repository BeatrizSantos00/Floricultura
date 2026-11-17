import mongomock
import pytest
from fastapi.testclient import TestClient

from app import database
from app.main import app


@pytest.fixture()
def client():
    database.set_db(mongomock.MongoClient()["flor_nova_test"])
    with TestClient(app) as c:
        yield c
    database.set_db(None)


def novo_produto(client, **extra):
    corpo = {
        "nome": "Buquê Teste",
        "categoria": "buques",
        "preco": 100.0,
        "estoque": 5,
        **extra,
    }
    r = client.post("/api/produtos", json=corpo)
    assert r.status_code == 201, r.text
    return r.json()


def nova_cliente(client, email="ana@email.com", rua="Rua A, 1"):
    r = client.post(
        "/api/clientes",
        json={
            "nome": "Ana Teste",
            "email": email,
            "endereco": {"rua": rua, "bairro": "Centro", "cidade": "SJC"},
        },
    )
    assert r.status_code == 201, r.text
    return r.json()


def novo_pedido(client, cliente, itens, **extra):
    return client.post(
        "/api/pedidos",
        json={"cliente_id": cliente["id"], "itens": itens, **extra},
    )


def test_health(client):
    assert client.get("/api/health").json() == {"status": "ok"}


def test_crud_produto(client):
    p = novo_produto(client)
    assert "id" in p and "_id" not in p

    r = client.put(f"/api/produtos/{p['id']}", json={**p, "preco": 120.0})
    assert r.json()["preco"] == 120.0

    assert len(client.get("/api/produtos", params={"categoria": "buques"}).json()) == 1
    assert client.get("/api/produtos", params={"q": "teste"}).json()[0]["id"] == p["id"]

    assert client.delete(f"/api/produtos/{p['id']}").status_code == 204
    assert client.get(f"/api/produtos/{p['id']}").status_code == 404


def test_validacoes_produto(client):
    r = client.post("/api/produtos", json={"nome": "X", "categoria": "carros", "preco": -1, "estoque": 1})
    assert r.status_code == 422
    assert client.get("/api/produtos/abc").status_code == 422


def test_email_duplicado(client):
    nova_cliente(client)
    r = client.post("/api/clientes", json={"nome": "Outra", "email": "ana@email.com"})
    assert r.status_code == 409


def test_pedido_baixa_estoque_e_calcula_total(client):
    p = novo_produto(client, estoque=5, preco=100.0)
    c = nova_cliente(client)

    r = novo_pedido(client, c, [{"produto_id": p["id"], "quantidade": 2}])
    assert r.status_code == 201
    pedido = r.json()
    assert pedido["total"] == 200.0
    assert pedido["status"] == "recebido"
    assert pedido["cliente_nome"] == "Ana Teste"
    assert client.get(f"/api/produtos/{p['id']}").json()["estoque"] == 3


def test_pedido_estoque_insuficiente_nao_baixa_nada(client):
    a = novo_produto(client, nome="Produto A", estoque=5)
    b = novo_produto(client, nome="Produto B", estoque=1)
    c = nova_cliente(client)

    r = novo_pedido(
        client,
        c,
        [{"produto_id": a["id"], "quantidade": 2}, {"produto_id": b["id"], "quantidade": 3}],
    )
    assert r.status_code == 409
    # rollback: A continua com 5
    assert client.get(f"/api/produtos/{a['id']}").json()["estoque"] == 5


def test_pedido_entrega_exige_endereco(client):
    p = novo_produto(client)
    c = nova_cliente(client, rua="")
    r = novo_pedido(client, c, [{"produto_id": p["id"], "quantidade": 1}])
    assert r.status_code == 422
    r = novo_pedido(client, c, [{"produto_id": p["id"], "quantidade": 1}], tipo_entrega="retirada")
    assert r.status_code == 201


def test_fluxo_de_status_e_cancelamento_devolve_estoque(client):
    p = novo_produto(client, estoque=5)
    c = nova_cliente(client)
    pedido = novo_pedido(client, c, [{"produto_id": p["id"], "quantidade": 2}]).json()
    url = f"/api/pedidos/{pedido['id']}/status"

    # não pode pular direto para entregue
    assert client.patch(url, json={"status": "entregue"}).status_code == 409

    assert client.patch(url, json={"status": "cancelado"}).status_code == 200
    assert client.get(f"/api/produtos/{p['id']}").json()["estoque"] == 5
    # cancelado é final
    assert client.patch(url, json={"status": "em_preparo"}).status_code == 409


def test_retirada_nao_sai_para_entrega(client):
    p = novo_produto(client)
    c = nova_cliente(client)
    pedido = novo_pedido(
        client, c, [{"produto_id": p["id"], "quantidade": 1}], tipo_entrega="retirada"
    ).json()
    url = f"/api/pedidos/{pedido['id']}/status"
    client.patch(url, json={"status": "em_preparo"})
    assert client.patch(url, json={"status": "saiu_para_entrega"}).status_code == 409
    assert client.patch(url, json={"status": "entregue"}).status_code == 200


def test_cliente_com_pedido_nao_pode_ser_removida(client):
    p = novo_produto(client)
    c = nova_cliente(client)
    novo_pedido(client, c, [{"produto_id": p["id"], "quantidade": 1}])
    assert client.delete(f"/api/clientes/{c['id']}").status_code == 409
    assert len(client.get(f"/api/clientes/{c['id']}/pedidos").json()) == 1


def test_relatorios(client):
    a = novo_produto(client, nome="Rosa A", preco=100.0, estoque=20)
    b = novo_produto(client, nome="Planta B", categoria="plantas", preco=50.0, estoque=20)
    c = nova_cliente(client)

    novo_pedido(client, c, [{"produto_id": a["id"], "quantidade": 2}, {"produto_id": b["id"], "quantidade": 1}])
    cancelado = novo_pedido(client, c, [{"produto_id": a["id"], "quantidade": 5}]).json()
    client.patch(f"/api/pedidos/{cancelado['id']}/status", json={"status": "cancelado"})

    resumo = client.get("/api/relatorios/resumo").json()
    assert resumo["faturamento"] == 250.0  # cancelado fica de fora
    assert resumo["pedidos"] == 1
    assert resumo["ticket_medio"] == 250.0
    assert resumo["por_status"] == {"recebido": 1, "cancelado": 1}

    top = client.get("/api/relatorios/produtos-mais-vendidos").json()
    assert top[0]["nome"] == "Rosa A" and top[0]["quantidade"] == 2

    cats = {x["categoria"]: x["receita"] for x in client.get("/api/relatorios/vendas-por-categoria").json()}
    assert cats == {"buques": 200.0, "plantas": 50.0}

    dias = client.get("/api/relatorios/vendas-por-dia").json()
    assert len(dias) == 1 and dias[0]["faturamento"] == 250.0

    melhores = client.get("/api/relatorios/melhores-clientes").json()
    assert melhores[0]["nome"] == "Ana Teste" and melhores[0]["total_gasto"] == 250.0


def test_seed(client):
    from app.seed import popular

    popular()
    assert len(client.get("/api/produtos").json()) == 12
    assert client.get("/api/relatorios/resumo").json()["pedidos"] > 0
