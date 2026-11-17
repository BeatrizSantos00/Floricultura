"""Popula o banco com dados de exemplo.

Uso:  python -m app.seed            (só insere se o banco estiver vazio)
      python -m app.seed --reset    (apaga tudo e insere de novo)
"""
import random
import sys
from datetime import datetime, timedelta, timezone

from .database import criar_indices, get_db

PRODUTOS = [
    ("Buquê Rosas Vermelhas", "12 rosas colombianas com folhagem", "buques", 129.90, 20, "🌹"),
    ("Buquê Campestre", "Flores do campo em tons pastel", "buques", 89.90, 15, "💐"),
    ("Buquê de Girassóis", "7 girassóis com papel kraft", "buques", 99.90, 12, "🌻"),
    ("Arranjo Peônias Rosa", "Arranjo em vaso de cerâmica", "arranjos", 189.90, 8, "🌸"),
    ("Arranjo Lírios Brancos", "Lírios com eucalipto", "arranjos", 159.90, 10, "🤍"),
    ("Orquídea Phalaenopsis", "Orquídea rosa no vaso decorado", "plantas", 139.90, 14, "🪷"),
    ("Suculentas Mini Trio", "Trio em vasinhos de cerâmica", "plantas", 59.90, 30, "🪴"),
    ("Violeta Africana", "Pequena violeta em cachepô", "plantas", 44.90, 25, "💜"),
    ("Cesta Café da Manhã Floral", "Cesta com flores, bolo e geleias", "cestas", 219.90, 6, "🧺"),
    ("Cesta Relax", "Flores, vela aromática e chocolates", "cestas", 179.90, 9, "🕯️"),
    ("Caixa de Bombons Artesanais", "12 bombons belgas", "presentes", 49.90, 40, "🍫"),
    ("Pelúcia Ursinho", "Ursinho 25 cm para acompanhar o buquê", "presentes", 39.90, 18, "🧸"),
]

CLIENTES = [
    ("Ana Beatriz Lima", "ana.lima@email.com", "(12) 99111-1111", ("Rua das Acácias, 120", "Jardim Esplanada", "São José dos Campos")),
    ("Camila Ferreira", "camila.f@email.com", "(12) 99222-2222", ("Av. Andrômeda, 800", "Jardim Satélite", "São José dos Campos")),
    ("Juliana Rocha", "ju.rocha@email.com", "(12) 99333-3333", ("Rua Ipê Amarelo, 45", "Vila Ema", "São José dos Campos")),
    ("Mariana Costa", "mari.costa@email.com", "(12) 99444-4444", ("Rua das Orquídeas, 310", "Urbanova", "São José dos Campos")),
    ("Fernanda Alves", "fe.alves@email.com", "(12) 99555-5555", ("Rua Rosa Branca, 77", "Centro", "Jacareí")),
]

MENSAGENS = [
    "Feliz aniversário!",
    "Com todo carinho 💕",
    "Parabéns pela conquista!",
    "Saudades de você",
    "",
]


def popular(reset: bool = False) -> None:
    db = get_db()
    if reset:
        for nome in ("produtos", "clientes", "pedidos"):
            db[nome].drop()
    criar_indices()

    if db.produtos.count_documents({}) or db.clientes.count_documents({}):
        print("Banco já possui dados. Use --reset para recriar.")
        return

    agora = datetime.now(timezone.utc)
    rng = random.Random(42)

    produtos = []
    for nome, desc, cat, preco, estoque, emoji in PRODUTOS:
        doc = {
            "nome": nome,
            "descricao": desc,
            "categoria": cat,
            "preco": preco,
            "estoque": estoque,
            "emoji": emoji,
            "ativo": True,
        }
        doc["_id"] = db.produtos.insert_one(doc).inserted_id
        produtos.append(doc)

    clientes = []
    for nome, email, tel, (rua, bairro, cidade) in CLIENTES:
        doc = {
            "nome": nome,
            "email": email,
            "telefone": tel,
            "endereco": {"rua": rua, "bairro": bairro, "cidade": cidade},
            "observacoes": "",
            "criado_em": agora - timedelta(days=rng.randint(30, 120)),
        }
        doc["_id"] = db.clientes.insert_one(doc).inserted_id
        clientes.append(doc)

    status_possiveis = ["entregue"] * 7 + ["em_preparo", "recebido", "saiu_para_entrega", "cancelado"]
    for _ in range(16):
        cliente = rng.choice(clientes)
        itens = []
        for produto in rng.sample(produtos, rng.randint(1, 3)):
            itens.append(
                {
                    "produto_id": produto["_id"],
                    "nome": produto["nome"],
                    "categoria": produto["categoria"],
                    "quantidade": rng.randint(1, 2),
                    "preco_unitario": produto["preco"],
                }
            )
        criado_em = agora - timedelta(days=rng.randint(0, 29), hours=rng.randint(0, 10))
        db.pedidos.insert_one(
            {
                "cliente_id": cliente["_id"],
                "cliente_nome": cliente["nome"],
                "itens": itens,
                "total": round(sum(i["quantidade"] * i["preco_unitario"] for i in itens), 2),
                "status": rng.choice(status_possiveis),
                "tipo_entrega": rng.choice(["entrega", "entrega", "retirada"]),
                "data_entrega": (criado_em + timedelta(days=1)).strftime("%Y-%m-%d"),
                "mensagem_cartao": rng.choice(MENSAGENS),
                "criado_em": criado_em,
            }
        )

    print(
        f"Pronto: {db.produtos.count_documents({})} produtos, "
        f"{db.clientes.count_documents({})} clientes, "
        f"{db.pedidos.count_documents({})} pedidos."
    )


if __name__ == "__main__":
    popular(reset="--reset" in sys.argv)
