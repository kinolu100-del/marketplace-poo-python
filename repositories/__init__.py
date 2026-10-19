"""Pacote de repositórios em memória para desacoplamento da camada de persistência."""

from repositories.usuario_repository import UsuarioRepository
from repositories.produto_repository import ProdutoRepository
from repositories.pedido_repository import PedidoRepository

__all__ = [
    "UsuarioRepository",
    "ProdutoRepository",
    "PedidoRepository",
]
