from typing import Literal, Optional

from pydantic import BaseModel, Field

Categoria = Literal["buques", "arranjos", "plantas", "cestas", "presentes"]
StatusPedido = Literal[
    "recebido", "em_preparo", "saiu_para_entrega", "entregue", "cancelado"
]
TipoEntrega = Literal["entrega", "retirada"]


# ---------- Produtos (catálogo) ----------
class ProdutoIn(BaseModel):
    nome: str = Field(min_length=2, max_length=80)
    descricao: str = Field(default="", max_length=300)
    categoria: Categoria
    preco: float = Field(gt=0)
    estoque: int = Field(ge=0)
    emoji: str = Field(default="🌸", max_length=8)
    ativo: bool = True


# ---------- Clientes ----------
class Endereco(BaseModel):
    rua: str = ""
    bairro: str = ""
    cidade: str = ""


class ClienteIn(BaseModel):
    nome: str = Field(min_length=2, max_length=80)
    email: str = Field(pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    telefone: str = Field(default="", max_length=20)
    endereco: Endereco = Field(default_factory=Endereco)
    observacoes: str = Field(default="", max_length=300)


# ---------- Pedidos ----------
class ItemPedidoIn(BaseModel):
    produto_id: str
    quantidade: int = Field(ge=1, le=100)


class PedidoIn(BaseModel):
    cliente_id: str
    itens: list[ItemPedidoIn] = Field(min_length=1)
    tipo_entrega: TipoEntrega = "entrega"
    data_entrega: Optional[str] = Field(
        default=None, pattern=r"^\d{4}-\d{2}-\d{2}$", description="AAAA-MM-DD"
    )
    mensagem_cartao: str = Field(default="", max_length=200)


class StatusIn(BaseModel):
    status: StatusPedido
