from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import criar_indices
from .routers import clientes, pedidos, produtos, relatorios


@asynccontextmanager
async def lifespan(app: FastAPI):
    criar_indices()
    yield


app = FastAPI(
    title="Flor Nova — API",
    description="Sistema de floricultura com catálogo, pedidos, clientes e relatórios.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

api = APIRouter(prefix="/api")
api.include_router(produtos.router)
api.include_router(clientes.router)
api.include_router(pedidos.router)
api.include_router(relatorios.router)


@api.get("/health", tags=["Sistema"])
def health():
    return {"status": "ok"}


app.include_router(api)
