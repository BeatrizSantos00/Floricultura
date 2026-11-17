from typing import Any

from bson import ObjectId
from bson.errors import InvalidId
from fastapi import HTTPException


def to_object_id(valor: str) -> ObjectId:
    try:
        return ObjectId(valor)
    except (InvalidId, TypeError):
        raise HTTPException(status_code=422, detail=f"ID inválido: {valor}")


def serializar(doc: Any) -> Any:
    """Converte ObjectId em str e renomeia `_id` para `id` (recursivo)."""
    if isinstance(doc, list):
        return [serializar(d) for d in doc]
    if isinstance(doc, dict):
        saida = {}
        for chave, valor in doc.items():
            nova = "id" if chave == "_id" else chave
            saida[nova] = serializar(valor)
        return saida
    if isinstance(doc, ObjectId):
        return str(doc)
    return doc
