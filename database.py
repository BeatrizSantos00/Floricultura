"""Conexão com o MongoDB.

A conexão é criada só no primeiro uso. Nos testes, `set_db` troca o banco
real por um banco em memória (mongomock).
"""
import os

from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.database import Database

load_dotenv()

_db: Database | None = None


def get_db() -> Database:
    global _db
    if _db is None:
        url = os.getenv("MONGO_URL", "mongodb://localhost:27017")
        nome = os.getenv("MONGO_DB", "flor_nova")
        _db = MongoClient(url)[nome]
    return _db


def set_db(db: Database | None) -> None:
    global _db
    _db = db


def criar_indices() -> None:
    db = get_db()
    db.clientes.create_index("email", unique=True)
    db.produtos.create_index("categoria")
    db.pedidos.create_index("status")
    db.pedidos.create_index("cliente_id")
    db.pedidos.create_index("criado_em")
