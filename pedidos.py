from collections import defaultdict
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException

from ..database import get_db
from ..schemas import PedidoIn, StatusIn, StatusPedido
from ..utils import serializar, to_object_id

router = APIRouter(prefix="/pedidos", tags=["Pedidos"])

# Fluxo permitido de status
TRANSICOES = {
    "recebido": {"em_preparo", "cancelado"},
    "em_preparo": {"saiu_para_entrega", "entregue", "cancelado"},
    "saiu_para_entrega": {"entregue"},
    "entregue": set(),
    "cancelado": set(),
}


def _devolver_estoque(itens: list[dict]) -> None:
    for item in itens:
        get_db().produtos.update_one(
            {"_id": item["produto_id"]}, {"$inc": {"estoque": item["quantidade"]}}
        )


@router.get("")
def listar(status: Optional[StatusPedido] = None, cliente_id: Optional[str] = None):
    filtro: dict = {}
    if status:
        filtro["status"] = status
    if cliente_id:
        filtro["cliente_id"] = to_object_id(cliente_id)
    docs = get_db().pedidos.find(filtro).sort("criado_em", -1)
    return serializar(list(docs))


@router.get("/{pedido_id}")
def obter(pedido_id: str):
    doc = get_db().pedidos.find_one({"_id": to_object_id(pedido_id)})
    if not doc:
        raise HTTPException(404, "Pedido não encontrado")
    return serializar(doc)


@router.post("", status_code=201)
def criar(pedido: PedidoIn):
    db = get_db()

    cliente = db.clientes.find_one({"_id": to_object_id(pedido.cliente_id)})
    if not cliente:
        raise HTTPException(404, "Cliente não encontrada")

    if pedido.tipo_entrega == "entrega" and not cliente.get("endereco", {}).get("rua"):
        raise HTTPException(422, "Cliente sem endereço cadastrado para entrega")

    # junta itens repetidos do mesmo produto
    quantidades: dict[str, int] = defaultdict(int)
    for item in pedido.itens:
        quantidades[item.produto_id] += item.quantidade

    itens: list[dict] = []
    baixados: list[dict] = []
    for produto_id, qtd in quantidades.items():
        oid = to_object_id(produto_id)
        produto = db.produtos.find_one({"_id": oid})
        if not produto:
            _devolver_estoque(baixados)
            raise HTTPException(404, f"Produto não encontrado: {produto_id}")

        # baixa atômica: só decrementa se ainda houver estoque suficiente
        res = db.produtos.update_one(
            {"_id": oid, "ativo": True, "estoque": {"$gte": qtd}},
            {"$inc": {"estoque": -qtd}},
        )
        if res.modified_count == 0:
            _devolver_estoque(baixados)
            raise HTTPException(
                409, f"Estoque insuficiente ou produto inativo: {produto['nome']}"
            )

        item = {
            "produto_id": oid,
            "nome": produto["nome"],
            "categoria": produto["categoria"],
            "quantidade": qtd,
            "preco_unitario": produto["preco"],
        }
        itens.append(item)
        baixados.append(item)

    total = round(sum(i["quantidade"] * i["preco_unitario"] for i in itens), 2)
    doc = {
        "cliente_id": cliente["_id"],
        "cliente_nome": cliente["nome"],  # desnormalizado de propósito (NoSQL)
        "itens": itens,  # documentos embutidos
        "total": total,
        "status": "recebido",
        "tipo_entrega": pedido.tipo_entrega,
        "data_entrega": pedido.data_entrega,
        "mensagem_cartao": pedido.mensagem_cartao,
        "criado_em": datetime.now(timezone.utc),
    }
    resultado = db.pedidos.insert_one(doc)
    return serializar(db.pedidos.find_one({"_id": resultado.inserted_id}))


@router.patch("/{pedido_id}/status")
def mudar_status(pedido_id: str, corpo: StatusIn):
    oid = to_object_id(pedido_id)
    pedido = get_db().pedidos.find_one({"_id": oid})
    if not pedido:
        raise HTTPException(404, "Pedido não encontrado")

    atual, novo = pedido["status"], corpo.status
    if novo not in TRANSICOES[atual]:
        raise HTTPException(409, f"Não é possível mudar de '{atual}' para '{novo}'")
    if novo == "saiu_para_entrega" and pedido["tipo_entrega"] == "retirada":
        raise HTTPException(409, "Pedido para retirada não sai para entrega")

    if novo == "cancelado":
        _devolver_estoque(pedido["itens"])

    get_db().pedidos.update_one({"_id": oid}, {"$set": {"status": novo}})
    return serializar(get_db().pedidos.find_one({"_id": oid}))
