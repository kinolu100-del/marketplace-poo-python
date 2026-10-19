"""
=====================================================================
Repositório em Memória de Pedidos (repositories/pedido_repository.py)
=====================================================================
Abstrai a persistência e consulta do histórico de pedidos.
=====================================================================
"""

from __future__ import annotations
from typing import Dict, List, Optional
from models.pedido import Pedido


class PedidoRepository:
    """Repositório responsável pelo armazenamento em memória de Pedidos."""

    def __init__(self):
        self._dados: Dict[int, Pedido] = {}

    def adicionar(self, pedido: Pedido) -> Pedido:
        """Armazena ou atualiza um pedido no histórico."""
        self._dados[pedido.id] = pedido
        return pedido

    def buscar_por_id(self, id_pedido: int) -> Optional[Pedido]:
        """Busca um pedido pelo seu ID."""
        return self._dados.get(id_pedido)

    def listar(self) -> List[Pedido]:
        """Retorna todos os pedidos registrados."""
        return list(self._dados.values())

    def listar_por_cliente(self, id_cliente: int) -> List[Pedido]:
        """Retorna os pedidos realizados por um cliente específico."""
        return [p for p in self._dados.values() if p.cliente.id == id_cliente]

    def remover(self, id_pedido: int) -> bool:
        """Remove um pedido pelo seu ID."""
        if id_pedido in self._dados:
            del self._dados[id_pedido]
            return True
        return False

    def limpar(self) -> None:
        """Esvazia o histórico de pedidos."""
        self._dados.clear()
