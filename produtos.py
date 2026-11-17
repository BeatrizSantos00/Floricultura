import re
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from ..database import get_db
from ..schemas import Categoria, ProdutoIn
from ..utils import serializar, to_object_id

router = APIRouter(prefix="/produtos", tags=["Catálogo"])


@router.get("")
def listar(
    categoria: Optional[Categoria] = None,
    q: Optional[str] = Query(default=None, description="busca pelo nome"),
    apenas_ativos: bool = False,
):
    filtro: dict = {}
    if categoria:
        filtro["categoria"] = categoria
    if q:
        filtro["nome"] = {"$regex": re.escape(q), "$options": "i"}
    if apenas_ativos:
        filtro["ativo"] = True
    docs = get_db().produtos.find(filtro).sort("nome", 1)
    return serializar(list(docs))


@router.get("/{produto_id}")
def obter(produto_id: str):
    doc = get_db().produtos.find_one({"_id": to_object_id(produto_id)})
    if not doc:
        raise HTTPException(404, "Produto não encontrado")
    return serializar(doc)


@router.post("", status_code=201)
def criar(produto: ProdutoIn):
    dados = produto.model_dump()
    resultado = get_db().produtos.insert_one(dados)
    return serializar(get_db().produtos.find_one({"_id": resultado.inserted_id}))


@router.put("/{produto_id}")
def atualizar(produto_id: str, produto: ProdutoIn):
    oid = to_object_id(produto_id)
    resultado = get_db().produtos.update_one({"_id": oid}, {"$set": produto.model_dump()})
    if resultado.matched_count == 0:
        raise HTTPException(404, "Produto não encontrado")
    return serializar(get_db().produtos.find_one({"_id": oid}))


@router.delete("/{produto_id}", status_code=204)
def remover(produto_id: str):
    resultado = get_db().produtos.delete_one({"_id": to_object_id(produto_id)})
    if resultado.deleted_count == 0:
        raise HTTPException(404, "Produto não encontrado")
