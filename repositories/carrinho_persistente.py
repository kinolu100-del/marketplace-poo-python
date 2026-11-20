"""
=====================================================================
Módulo de Carrinho Persistente (repositories/carrinho_persistente.py)
=====================================================================
Especializa o modelo 'Carrinho' para sincronizar operações de adição,
alteração de quantidade, remoção e esvaziamento diretamente com a tabela
'carrinho_itens' do SQLite, preservando a interface de domínio pura.
=====================================================================
"""

from __future__ import annotations
from typing import Dict
from database.connection import Database
from models.pedido import Carrinho, ItemCarrinho
from models.produto import Produto


class CarrinhoPersistente(Carrinho):
    """
    Subclasse de Carrinho transparente para a camada de serviços e modelos.
    Cada ação executada reflete imediatamente na persistência relacional.
    """

    def __init__(self, cliente_id: int, db: Database):
        super().__init__()
        self._cliente_id = cliente_id
        self._db = db

    def adicionar(self, produto: Produto, quantidade: int) -> None:
        super().adicionar(produto, quantidade)
        nova_qtd = self._itens[produto.id].quantidade
        with self._db.transacao() as conn:
            conn.execute(
                """
                INSERT INTO carrinho_itens (cliente_id, produto_id, quantidade)
                VALUES (?, ?, ?)
                ON CONFLICT(cliente_id, produto_id) DO UPDATE SET quantidade = ?
                """,
                (self._cliente_id, produto.id, nova_qtd, nova_qtd),
            )

    def remover(self, produto: Produto) -> None:
        super().remover(produto)
        with self._db.transacao() as conn:
            conn.execute(
                "DELETE FROM carrinho_itens WHERE cliente_id = ? AND produto_id = ?",
                (self._cliente_id, produto.id),
            )

    def alterar_quantidade(self, produto: Produto, nova_quantidade: int) -> None:
        super().alterar_quantidade(produto, nova_quantidade)
        with self._db.transacao() as conn:
            if nova_quantidade <= 0:
                conn.execute(
                    "DELETE FROM carrinho_itens WHERE cliente_id = ? AND produto_id = ?",
                    (self._cliente_id, produto.id),
                )
            else:
                conn.execute(
                    """
                    INSERT INTO carrinho_itens (cliente_id, produto_id, quantidade)
                    VALUES (?, ?, ?)
                    ON CONFLICT(cliente_id, produto_id) DO UPDATE SET quantidade = ?
                    """,
                    (self._cliente_id, produto.id, nova_quantidade, nova_quantidade),
                )

    def limpar(self) -> None:
        super().limpar()
        with self._db.transacao() as conn:
            conn.execute(
                "DELETE FROM carrinho_itens WHERE cliente_id = ?",
                (self._cliente_id,),
            )

    def carregar_itens_banco(self, itens: Dict[int, ItemCarrinho]) -> None:
        """Carrega dados existentes do banco em memória sem reescrever no SQLite."""
        self._itens = dict(itens)

