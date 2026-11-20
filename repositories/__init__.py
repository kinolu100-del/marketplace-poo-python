"""Pacote de repositórios SQLite para a camada de persistência relacional (Nível 3)."""

from repositories.usuario_repository import UsuarioRepository
from repositories.produto_repository import ProdutoRepository
from repositories.pedido_repository import PedidoRepository
from repositories.carrinho_persistente import CarrinhoPersistente

__all__ = [
    "UsuarioRepository",
    "ProdutoRepository",
    "PedidoRepository",
    "CarrinhoPersistente",
]
