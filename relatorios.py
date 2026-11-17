"""Relatórios feitos com o Aggregation Framework do MongoDB.

Pedidos cancelados não entram no faturamento.
"""
from fastapi import APIRouter, Query

from ..database import get_db

router = APIRouter(prefix="/relatorios", tags=["Relatórios"])

SEM_CANCELADOS = {"$match": {"status": {"$ne": "cancelado"}}}


@router.get("/resumo")
def resumo():
    db = get_db()
    vendas = list(
        db.pedidos.aggregate(
            [
                SEM_CANCELADOS,
                {
                    "$group": {
                        "_id": None,
                        "faturamento": {"$sum": "$total"},
                        "pedidos": {"$sum": 1},
                    }
                },
            ]
        )
    )
    faturamento = round(vendas[0]["faturamento"], 2) if vendas else 0.0
    qtd = vendas[0]["pedidos"] if vendas else 0

    por_status = {
        r["_id"]: r["quantidade"]
        for r in db.pedidos.aggregate(
            [{"$group": {"_id": "$status", "quantidade": {"$sum": 1}}}]
        )
    }
    return {
        "faturamento": faturamento,
        "pedidos": qtd,
        "ticket_medio": round(faturamento / qtd, 2) if qtd else 0.0,
        "clientes": db.clientes.count_documents({}),
        "produtos": db.produtos.count_documents({}),
        "por_status": por_status,
    }


@router.get("/produtos-mais-vendidos")
def produtos_mais_vendidos(limite: int = Query(default=5, ge=1, le=50)):
    pipeline = [
        SEM_CANCELADOS,
        {"$unwind": "$itens"},
        {
            "$group": {
                "_id": "$itens.produto_id",
                "nome": {"$first": "$itens.nome"},
                "quantidade": {"$sum": "$itens.quantidade"},
                "receita": {
                    "$sum": {"$multiply": ["$itens.quantidade", "$itens.preco_unitario"]}
                },
            }
        },
        {"$sort": {"quantidade": -1, "receita": -1}},
        {"$limit": limite},
    ]
    return [
        {
            "produto_id": str(r["_id"]),
            "nome": r["nome"],
            "quantidade": r["quantidade"],
            "receita": round(r["receita"], 2),
        }
        for r in get_db().pedidos.aggregate(pipeline)
    ]


@router.get("/vendas-por-categoria")
def vendas_por_categoria():
    pipeline = [
        SEM_CANCELADOS,
        {"$unwind": "$itens"},
        {
            "$group": {
                "_id": "$itens.categoria",
                "quantidade": {"$sum": "$itens.quantidade"},
                "receita": {
                    "$sum": {"$multiply": ["$itens.quantidade", "$itens.preco_unitario"]}
                },
            }
        },
        {"$sort": {"receita": -1}},
    ]
    return [
        {
            "categoria": r["_id"],
            "quantidade": r["quantidade"],
            "receita": round(r["receita"], 2),
        }
        for r in get_db().pedidos.aggregate(pipeline)
    ]


@router.get("/vendas-por-dia")
def vendas_por_dia():
    pipeline = [
        SEM_CANCELADOS,
        {
            "$group": {
                "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$criado_em"}},
                "pedidos": {"$sum": 1},
                "faturamento": {"$sum": "$total"},
            }
        },
        {"$sort": {"_id": 1}},
    ]
    return [
        {
            "data": r["_id"],
            "pedidos": r["pedidos"],
            "faturamento": round(r["faturamento"], 2),
        }
        for r in get_db().pedidos.aggregate(pipeline)
    ]


@router.get("/melhores-clientes")
def melhores_clientes(limite: int = Query(default=5, ge=1, le=50)):
    pipeline = [
        SEM_CANCELADOS,
        {
            "$group": {
                "_id": "$cliente_id",
                "nome": {"$first": "$cliente_nome"},
                "pedidos": {"$sum": 1},
                "total_gasto": {"$sum": "$total"},
            }
        },
        {"$sort": {"total_gasto": -1}},
        {"$limit": limite},
    ]
    return [
        {
            "cliente_id": str(r["_id"]),
            "nome": r["nome"],
            "pedidos": r["pedidos"],
            "total_gasto": round(r["total_gasto"], 2),
        }
        for r in get_db().pedidos.aggregate(pipeline)
    ]
