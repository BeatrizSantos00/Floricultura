import re
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException
from pymongo.errors import DuplicateKeyError

from ..database import get_db
from ..schemas import ClienteIn
from ..utils import serializar, to_object_id

router = APIRouter(prefix="/clientes", tags=["Clientes"])


@router.get("")
def listar(q: Optional[str] = None):
    filtro: dict = {}
    if q:
        padrao = {"$regex": re.escape(q), "$options": "i"}
        filtro["$or"] = [{"nome": padrao}, {"email": padrao}]
    return serializar(list(get_db().clientes.find(filtro).sort("nome", 1)))


@router.get("/{cliente_id}")
def obter(cliente_id: str):
    doc = get_db().clientes.find_one({"_id": to_object_id(cliente_id)})
    if not doc:
        raise HTTPException(404, "Cliente não encontrado")
    return serializar(doc)


@router.get("/{cliente_id}/pedidos")
def pedidos_do_cliente(cliente_id: str):
    oid = to_object_id(cliente_id)
    docs = get_db().pedidos.find({"cliente_id": oid}).sort("criado_em", -1)
    return serializar(list(docs))


@router.post("", status_code=201)
def criar(cliente: ClienteIn):
    dados = cliente.model_dump()
    dados["criado_em"] = datetime.now(timezone.utc)
    try:
        resultado = get_db().clientes.insert_one(dados)
    except DuplicateKeyError:
        raise HTTPException(409, "Já existe uma cliente com esse e-mail")
    return serializar(get_db().clientes.find_one({"_id": resultado.inserted_id}))


@router.put("/{cliente_id}")
def atualizar(cliente_id: str, cliente: ClienteIn):
    oid = to_object_id(cliente_id)
    try:
        resultado = get_db().clientes.update_one({"_id": oid}, {"$set": cliente.model_dump()})
    except DuplicateKeyError:
        raise HTTPException(409, "Já existe uma cliente com esse e-mail")
    if resultado.matched_count == 0:
        raise HTTPException(404, "Cliente não encontrado")
    return serializar(get_db().clientes.find_one({"_id": oid}))


@router.delete("/{cliente_id}", status_code=204)
def remover(cliente_id: str):
    oid = to_object_id(cliente_id)
    if get_db().pedidos.count_documents({"cliente_id": oid}, limit=1):
        raise HTTPException(409, "Cliente possui pedidos e não pode ser removida")
    resultado = get_db().clientes.delete_one({"_id": oid})
    if resultado.deleted_count == 0:
        raise HTTPException(404, "Cliente não encontrado")
