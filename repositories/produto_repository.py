"""
=====================================================================
Repositório em Memória de Produtos (repositories/produto_repository.py)
=====================================================================
Abstrai a persistência dos produtos em memória. Permite consultas
gerais ou filtradas por vendedor.
=====================================================================
"""

from __future__ import annotations
from typing import Dict, List, Optional
from models.produto import Produto


class ProdutoRepository:
    """Repositório responsável pelo armazenamento em memória de Produtos."""

    def __init__(self):
        self._dados: Dict[int, Produto] = {}

    def adicionar(self, produto: Produto) -> Produto:
        """Armazena ou atualiza um produto."""
        self._dados[produto.id] = produto
        return produto

    def buscar_por_id(self, id_produto: int) -> Optional[Produto]:
        """Busca um produto pelo seu ID."""
        return self._dados.get(id_produto)

    def listar(self) -> List[Produto]:
        """Retorna todos os produtos do catálogo."""
        return list(self._dados.values())

    def listar_por_vendedor(self, id_vendedor: int) -> List[Produto]:
        """Retorna todos os produtos ofertados por um determinado vendedor."""
        return [p for p in self._dados.values() if p.vendedor.id == id_vendedor]

    def remover(self, id_produto: int) -> bool:
        """Remove o produto pelo seu ID."""
        if id_produto in self._dados:
            del self._dados[id_produto]
            return True
        return False

    def limpar(self) -> None:
        """Esvazia o repositório de produtos."""
        self._dados.clear()
