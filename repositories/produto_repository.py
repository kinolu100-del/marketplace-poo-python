"""
=====================================================================
Repositório SQLite de Produtos (repositories/produto_repository.py)
=====================================================================
Implementação de persistência relacional em SQLite para Produtos Físicos
e Digitais. Mantém exatamente as mesmas assinaturas do repositório em
memória para garantir compatibilidade com as camadas de negócio e UI.
=====================================================================
"""

from __future__ import annotations
from decimal import Decimal
import sqlite3
from typing import Dict, List, Optional, Union
from database.connection import Database, obter_banco_padrao
from models.produto import Produto, ProdutoFisico, ProdutoDigital
from models.usuario import Vendedor
from repositories.usuario_repository import UsuarioRepository
from exceptions import BancoDeDadosError, OperacaoInvalidaError


class ProdutoFisicoPersistente(ProdutoFisico):
    """
    Subclasse de ProdutoFisico que sincroniza alterações de atributos
    e movimentações de estoque diretamente com o SQLite.
    """
    def __init__(self, *args, db: Optional[Database] = None, **kwargs):
        super().__init__(*args, **kwargs)
        self._db = db

    @Produto.preco.setter
    def preco(self, valor: Union[Decimal, float, int, str]) -> None:
        Produto.preco.fset(self, valor)
        if getattr(self, "_db", None):
            with self._db.transacao() as conn:
                conn.execute("UPDATE produtos SET preco = ? WHERE id = ?", (f"{self._preco:.2f}", self.id))

    @Produto.estoque.setter
    def estoque(self, valor: int) -> None:
        Produto.estoque.fset(self, valor)
        if getattr(self, "_db", None):
            with self._db.transacao() as conn:
                conn.execute("UPDATE produtos SET estoque = ? WHERE id = ?", (self._estoque, self.id))

    @ProdutoFisico.peso_kg.setter
    def peso_kg(self, valor: Union[Decimal, float, int, str]) -> None:
        ProdutoFisico.peso_kg.fset(self, valor)
        if getattr(self, "_db", None):
            with self._db.transacao() as conn:
                conn.execute("UPDATE produtos SET peso_kg = ? WHERE id = ?", (f"{self._peso_kg:.2f}", self.id))

    def baixar_estoque(self, quantidade: int) -> None:
        super().baixar_estoque(quantidade)
        if getattr(self, "_db", None):
            with self._db.transacao() as conn:
                conn.execute("UPDATE produtos SET estoque = ? WHERE id = ?", (self._estoque, self.id))

    def repor_estoque(self, quantidade: int) -> None:
        super().repor_estoque(quantidade)
        if getattr(self, "_db", None):
            with self._db.transacao() as conn:
                conn.execute("UPDATE produtos SET estoque = ? WHERE id = ?", (self._estoque, self.id))


class ProdutoDigitalPersistente(ProdutoDigital):
    """
    Subclasse de ProdutoDigital que sincroniza alterações de atributos
    e movimentações de estoque diretamente com o SQLite.
    """
    def __init__(self, *args, db: Optional[Database] = None, **kwargs):
        super().__init__(*args, **kwargs)
        self._db = db

    @Produto.preco.setter
    def preco(self, valor: Union[Decimal, float, int, str]) -> None:
        Produto.preco.fset(self, valor)
        if getattr(self, "_db", None):
            with self._db.transacao() as conn:
                conn.execute("UPDATE produtos SET preco = ? WHERE id = ?", (f"{self._preco:.2f}", self.id))

    @Produto.estoque.setter
    def estoque(self, valor: int) -> None:
        Produto.estoque.fset(self, valor)
        if getattr(self, "_db", None):
            with self._db.transacao() as conn:
                conn.execute("UPDATE produtos SET estoque = ? WHERE id = ?", (self._estoque, self.id))

    @ProdutoDigital.tamanho_mb.setter
    def tamanho_mb(self, valor: Union[Decimal, float, int, str]) -> None:
        ProdutoDigital.tamanho_mb.fset(self, valor)
        if getattr(self, "_db", None):
            with self._db.transacao() as conn:
                conn.execute("UPDATE produtos SET tamanho_mb = ? WHERE id = ?", (f"{self._tamanho_mb:.1f}", self.id))

    @ProdutoDigital.link_download.setter
    def link_download(self, valor: str) -> None:
        ProdutoDigital.link_download.fset(self, valor)
        if getattr(self, "_db", None):
            with self._db.transacao() as conn:
                conn.execute("UPDATE produtos SET link_download = ? WHERE id = ?", (self._link_download, self.id))

    def baixar_estoque(self, quantidade: int) -> None:
        super().baixar_estoque(quantidade)
        if getattr(self, "_db", None):
            with self._db.transacao() as conn:
                conn.execute("UPDATE produtos SET estoque = ? WHERE id = ?", (self._estoque, self.id))

    def repor_estoque(self, quantidade: int) -> None:
        super().repor_estoque(quantidade)
        if getattr(self, "_db", None):
            with self._db.transacao() as conn:
                conn.execute("UPDATE produtos SET estoque = ? WHERE id = ?", (self._estoque, self.id))


class ProdutoRepository:
    """Repositório responsável pela persistência de Produtos em SQLite."""

    def __init__(
        self,
        db: Optional[Database] = None,
        db_path: Optional[str] = None,
        usuario_repo: Optional[UsuarioRepository] = None,
    ):
        if db is not None:
            self._db = db
        elif db_path is not None:
            self._db = Database(db_path)
        else:
            self._db = obter_banco_padrao()

        self._usuario_repo = usuario_repo or UsuarioRepository(db=self._db)
        self._cache: Dict[int, Produto] = {}
        self._sincronizar_gerador_id()

    @property
    def db(self) -> Database:
        return self._db

    def _sincronizar_gerador_id(self) -> None:
        """Sincroniza o gerador de ID sequencial com o maior ID existente no banco."""
        conn = self._db.obter_conexao()
        cursor = conn.cursor()
        cursor.execute("SELECT COALESCE(MAX(id), 0) FROM produtos")
        max_id = cursor.fetchone()[0]
        Produto.resetar_gerador_id(max_id + 1)

    def adicionar(self, produto: Produto) -> Produto:
        """
        Insere ou atualiza um produto no SQLite.
        Valores monetários guardados como TEXT garantindo precisão Decimal.
        """
        conn = self._db.obter_conexao()
        tipo = produto.tipo()
        preco_str = f"{produto.preco:.2f}"
        peso_str = f"{produto.peso_kg:.2f}" if isinstance(produto, ProdutoFisico) else None
        mb_str = f"{produto.tamanho_mb:.1f}" if isinstance(produto, ProdutoDigital) else None
        link = getattr(produto, "link_download", None)

        try:
            with self._db.transacao():
                conn.execute(
                    """
                    INSERT INTO produtos (id, nome, preco, estoque, tipo, vendedor_id, peso_kg, tamanho_mb, link_download)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(id) DO UPDATE SET
                        nome = excluded.nome,
                        preco = excluded.preco,
                        estoque = excluded.estoque,
                        tipo = excluded.tipo,
                        vendedor_id = excluded.vendedor_id,
                        peso_kg = excluded.peso_kg,
                        tamanho_mb = excluded.tamanho_mb,
                        link_download = excluded.link_download
                    """,
                    (
                        produto.id,
                        produto.nome,
                        preco_str,
                        produto.estoque,
                        tipo,
                        produto.vendedor.id,
                        peso_str,
                        mb_str,
                        link,
                    ),
                )
        except sqlite3.IntegrityError as erro:
            raise OperacaoInvalidaError(f"Erro de integridade referencial ao salvar produto: {erro}")
        except sqlite3.Error as erro:
            raise BancoDeDadosError(f"Erro no banco ao salvar produto: {erro}", causa=erro)

        if isinstance(produto, (ProdutoFisicoPersistente, ProdutoDigitalPersistente)):
            produto._db = self._db

        self._cache[produto.id] = produto
        produto.vendedor.adicionar_produto(produto)
        self._sincronizar_gerador_id()
        return produto

    def _reconstruir_produto(self, row: sqlite3.Row) -> Produto:
        """Reidrata ProdutoFisico ou ProdutoDigital conectando com Vendedor correto."""
        pid = row["id"]
        if pid in self._cache:
            return self._cache[pid]

        vendedor_id = row["vendedor_id"]
        vendedor = self._usuario_repo.buscar_por_id(vendedor_id)
        if vendedor is None or not isinstance(vendedor, Vendedor):
            raise OperacaoInvalidaError(f"Vendedor de ID {vendedor_id} associado ao produto não existe.")

        tipo = row["tipo"]
        preco = Decimal(row["preco"])
        estoque = row["estoque"]

        if tipo == "Físico":
            produto = ProdutoFisicoPersistente(
                nome=row["nome"],
                preco=preco,
                estoque=estoque,
                vendedor=vendedor,
                peso_kg=Decimal(row["peso_kg"]),
                id_produto=pid,
                db=self._db,
            )
        elif tipo == "Digital":
            produto = ProdutoDigitalPersistente(
                nome=row["nome"],
                preco=preco,
                estoque=estoque,
                vendedor=vendedor,
                tamanho_mb=Decimal(row["tamanho_mb"]),
                link_download=row["link_download"],
                id_produto=pid,
                db=self._db,
            )
        else:
            raise BancoDeDadosError(f"Tipo desconhecido de produto no banco de dados: {tipo}")

        vendedor.adicionar_produto(produto)
        self._cache[pid] = produto
        return produto

    def buscar_por_id(self, id_produto: int) -> Optional[Produto]:
        """Busca um produto pelo seu ID."""
        if id_produto in self._cache:
            return self._cache[id_produto]

        conn = self._db.obter_conexao()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM produtos WHERE id = ?", (id_produto,))
        row = cursor.fetchone()
        if row is None:
            return None
        return self._reconstruir_produto(row)

    def listar(self) -> List[Produto]:
        """Retorna todos os produtos do catálogo."""
        conn = self._db.obter_conexao()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM produtos ORDER BY id ASC")
        return [self._reconstruir_produto(row) for row in cursor.fetchall()]

    def listar_por_vendedor(self, id_vendedor: int) -> List[Produto]:
        """Retorna todos os produtos ofertados por um determinado vendedor."""
        conn = self._db.obter_conexao()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM produtos WHERE vendedor_id = ? ORDER BY id ASC", (id_vendedor,))
        return [self._reconstruir_produto(row) for row in cursor.fetchall()]

    def remover(self, id_produto: int) -> bool:
        """Remove o produto pelo seu ID."""
        conn = self._db.obter_conexao()
        produto = self.buscar_por_id(id_produto)
        try:
            with self._db.transacao():
                cursor = conn.execute("DELETE FROM produtos WHERE id = ?", (id_produto,))
                removido = cursor.rowcount > 0
                if removido:
                    if id_produto in self._cache:
                        del self._cache[id_produto]
                    if produto and produto.vendedor:
                        produto.vendedor.remover_produto(produto)
                return removido
        except sqlite3.IntegrityError as erro:
            raise OperacaoInvalidaError(
                f"Não é permitido remover o produto ID {id_produto} devido a restrições no banco: {erro}"
            )
        except sqlite3.Error as erro:
            raise BancoDeDadosError(f"Erro ao remover produto: {erro}", causa=erro)

    def limpar(self) -> None:
        """Esvazia o repositório de produtos e limpa o cache."""
        self._cache.clear()
        conn = self._db.obter_conexao()
        try:
            with self._db.transacao():
                conn.execute("DELETE FROM produtos")
                conn.execute("DELETE FROM sqlite_sequence WHERE name = 'produtos'")
            self._sincronizar_gerador_id()
        except sqlite3.Error as erro:
            raise BancoDeDadosError(f"Erro ao limpar repositório de produtos: {erro}", causa=erro)
