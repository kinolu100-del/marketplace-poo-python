"""
=====================================================================
Repositório SQLite de Pedidos (repositories/pedido_repository.py)
=====================================================================
Implementação de persistência relacional em SQLite para Pedidos e
seus itens compostos. Garante transações atômicas para baixa/devolução
de estoque e congelamento histórico de preços e fretes.
=====================================================================
"""

from __future__ import annotations
from datetime import datetime
from decimal import Decimal
import sqlite3
from typing import Dict, List, Optional
from database.connection import Database, obter_banco_padrao
from models.pedido import Pedido, ItemPedido, StatusPedido
from models.usuario import Cliente
from repositories.usuario_repository import UsuarioRepository
from repositories.produto_repository import ProdutoRepository
from exceptions import BancoDeDadosError, EstoqueInsuficienteError, OperacaoInvalidaError


class PedidoPersistente(Pedido):
    """
    Subclasse de Pedido que sincroniza operações de cancelamento
    em transação composta atômica com reposição de estoque.
    """
    def __init__(self, *args, db: Optional[Database] = None, **kwargs):
        super().__init__(*args, **kwargs)
        self._db = db

    def cancelar(self) -> None:
        super().cancelar()
        if getattr(self, "_db", None):
            with self._db.transacao() as conn:
                conn.execute(
                    "UPDATE pedidos SET status = ? WHERE id = ?",
                    (StatusPedido.CANCELADO.value, self.id),
                )
                for item in self._itens:
                    conn.execute(
                        "UPDATE produtos SET estoque = ? WHERE id = ?",
                        (item.produto.estoque, item.produto.id),
                    )


class PedidoRepository:
    """Repositório responsável pela persistência de Pedidos em SQLite."""

    def __init__(
        self,
        db: Optional[Database] = None,
        db_path: Optional[str] = None,
        usuario_repo: Optional[UsuarioRepository] = None,
        produto_repo: Optional[ProdutoRepository] = None,
    ):
        if db is not None:
            self._db = db
        elif db_path is not None:
            self._db = Database(db_path)
        else:
            self._db = obter_banco_padrao()

        self._usuario_repo = usuario_repo or UsuarioRepository(db=self._db)
        self._produto_repo = produto_repo or ProdutoRepository(db=self._db, usuario_repo=self._usuario_repo)
        self._usuario_repo.vincular_produto_repo(self._produto_repo)
        self._cache: Dict[int, Pedido] = {}
        self._sincronizar_gerador_id()

    @property
    def db(self) -> Database:
        return self._db

    def _sincronizar_gerador_id(self) -> None:
        """Sincroniza o gerador sequencial de IDs com o banco."""
        conn = self._db.obter_conexao()
        cursor = conn.cursor()
        cursor.execute("SELECT COALESCE(MAX(id), 0) FROM pedidos")
        max_id = cursor.fetchone()[0]
        Pedido.resetar_gerador_id(max_id + 1)

    def adicionar(self, pedido: Pedido) -> Pedido:
        """
        Salva ou atualiza um pedido no banco.
        Se novo: grava pedido, itens congelados e baixa de estoque na MESMA transação.
        Se falhar por estoque insuficiente, aciona rollback automático.
        """
        conn = self._db.obter_conexao()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM pedidos WHERE id = ?", (pedido.id,))
        existe = cursor.fetchone() is not None

        try:
            with self._db.transacao():
                if not existe:
                    # 1. Validação de estoque preventiva dentro da transação atômica
                    for item in pedido.itens:
                        cursor.execute("SELECT estoque, nome FROM produtos WHERE id = ?", (item.produto.id,))
                        row_prod = cursor.fetchone()
                        if row_prod is None:
                            raise OperacaoInvalidaError(f"Produto ID {item.produto.id} não localizado no catálogo.")
                        estoque_banco = row_prod["estoque"]
                        if item.quantidade > estoque_banco:
                            raise EstoqueInsuficienteError(row_prod["nome"], estoque_banco, item.quantidade)

                    # 2. Inserção do pedido
                    conn.execute(
                        """
                        INSERT INTO pedidos (id, cliente_id, status, data_criacao)
                        VALUES (?, ?, ?, ?)
                        """,
                        (
                            pedido.id,
                            pedido.cliente.id,
                            pedido.status.value,
                            pedido.data_criacao.isoformat(),
                        ),
                    )

                    # 3. Inserção dos itens com preço e frete congelados e baixa de estoque
                    for item in pedido.itens:
                        preco_congelado = f"{item.preco_unitario:.2f}"
                        frete_congelado = f"{item.frete:.2f}"
                        conn.execute(
                            """
                            INSERT INTO itens_pedido (pedido_id, produto_id, quantidade, preco_unitario, frete)
                            VALUES (?, ?, ?, ?, ?)
                            """,
                            (
                                pedido.id,
                                item.produto.id,
                                item.quantidade,
                                preco_congelado,
                                frete_congelado,
                            ),
                        )
                        conn.execute(
                            "UPDATE produtos SET estoque = ? WHERE id = ?",
                            (item.produto.estoque, item.produto.id),
                        )
                else:
                    # Atualização de status (ex: confirmação ou cancelamento)
                    conn.execute(
                        "UPDATE pedidos SET status = ? WHERE id = ?",
                        (pedido.status.value, pedido.id),
                    )
        except (EstoqueInsuficienteError, OperacaoInvalidaError, sqlite3.Error, Exception) as erro:
            if not existe:
                # Restaura em memória o estoque que havia sido baixado preventivamente pelo PedidoService
                for item in pedido.itens:
                    try:
                        cursor_res = self._db.obter_conexao().cursor()
                        cursor_res.execute("SELECT estoque FROM produtos WHERE id = ?", (item.produto.id,))
                        r = cursor_res.fetchone()
                        if r is not None:
                            item.produto._estoque = r["estoque"]
                        else:
                            item.produto._estoque += item.quantidade
                    except Exception:
                        item.produto._estoque += item.quantidade
            if isinstance(erro, (EstoqueInsuficienteError, OperacaoInvalidaError)):
                raise
            if isinstance(erro, sqlite3.IntegrityError):
                raise OperacaoInvalidaError(f"Erro de integridade ao salvar pedido: {erro}")
            if isinstance(erro, sqlite3.Error):
                raise BancoDeDadosError(f"Erro no banco ao salvar pedido: {erro}", causa=erro)
            raise

        pedido.__class__ = PedidoPersistente
        pedido._db = self._db

        self._cache[pedido.id] = pedido
        self._sincronizar_gerador_id()
        return pedido

    def _reconstruir_pedido(self, row: sqlite3.Row) -> Pedido:
        """Reidrata um Pedido completo a partir do banco mantendo valores congelados."""
        pid = row["id"]
        if pid in self._cache:
            return self._cache[pid]

        cliente_id = row["cliente_id"]
        cliente = self._usuario_repo.buscar_por_id(cliente_id)
        if cliente is None or not isinstance(cliente, Cliente):
            raise OperacaoInvalidaError(f"Cliente de ID {cliente_id} associado ao pedido não existe.")

        pedido = PedidoPersistente(cliente=cliente, id_pedido=pid, db=self._db)
        pedido._status = StatusPedido(row["status"])
        pedido._data_criacao = datetime.fromisoformat(row["data_criacao"])

        conn = self._db.obter_conexao()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM itens_pedido WHERE pedido_id = ? ORDER BY id ASC", (pid,))
        itens_rows = cursor.fetchall()

        for item_row in itens_rows:
            prod_id = item_row["produto_id"]
            produto = self._produto_repo.buscar_por_id(prod_id)
            if produto is not None:
                item = ItemPedido(produto=produto, quantidade=item_row["quantidade"])
                # Restaura os valores monetários congelados no momento da compra
                item._preco_unitario = Decimal(item_row["preco_unitario"])
                item._frete = Decimal(item_row["frete"])
                pedido._itens.append(item)

        self._cache[pid] = pedido
        if not any(p.id == pedido.id for p in cliente.pedidos):
            cliente.adicionar_pedido(pedido)
        return pedido

    def buscar_por_id(self, id_pedido: int) -> Optional[Pedido]:
        """Busca um pedido pelo seu ID."""
        if id_pedido in self._cache:
            return self._cache[id_pedido]

        conn = self._db.obter_conexao()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM pedidos WHERE id = ?", (id_pedido,))
        row = cursor.fetchone()
        if row is None:
            return None
        return self._reconstruir_pedido(row)

    def listar(self) -> List[Pedido]:
        """Retorna todos os pedidos registrados."""
        conn = self._db.obter_conexao()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM pedidos ORDER BY id ASC")
        return [self._reconstruir_pedido(row) for row in cursor.fetchall()]

    def listar_por_cliente(self, id_cliente: int) -> List[Pedido]:
        """Retorna os pedidos realizados por um cliente específico."""
        conn = self._db.obter_conexao()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM pedidos WHERE cliente_id = ? ORDER BY id ASC", (id_cliente,))
        return [self._reconstruir_pedido(row) for row in cursor.fetchall()]

    def remover(self, id_pedido: int) -> bool:
        """Remove um pedido pelo seu ID."""
        conn = self._db.obter_conexao()
        pedido = self.buscar_por_id(id_pedido)
        try:
            with self._db.transacao():
                cursor = conn.execute("DELETE FROM pedidos WHERE id = ?", (id_pedido,))
                removido = cursor.rowcount > 0
                if removido:
                    if id_pedido in self._cache:
                        del self._cache[id_pedido]
                    if pedido and pedido in pedido.cliente.pedidos:
                        pedido.cliente.pedidos.remove(pedido)
                return removido
        except sqlite3.IntegrityError as erro:
            raise OperacaoInvalidaError(f"Não é permitido remover o pedido ID {id_pedido}: {erro}")
        except sqlite3.Error as erro:
            raise BancoDeDadosError(f"Erro ao remover pedido: {erro}", causa=erro)

    def limpar(self) -> None:
        """Esvazia o histórico de pedidos e limpa o cache."""
        self._cache.clear()
        conn = self._db.obter_conexao()
        try:
            with self._db.transacao():
                conn.execute("DELETE FROM itens_pedido")
                conn.execute("DELETE FROM pedidos")
                conn.execute("DELETE FROM sqlite_sequence WHERE name IN ('pedidos', 'itens_pedido')")
            self._sincronizar_gerador_id()
        except sqlite3.Error as erro:
            raise BancoDeDadosError(f"Erro ao limpar repositório de pedidos: {erro}", causa=erro)
