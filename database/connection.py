"""
=====================================================================
Módulo de Conexão e Gerenciamento do SQLite (database/connection.py)
=====================================================================
Centraliza abertura de conexão, habilitação de chaves estrangeiras,
transações atômicas e controle de ciclo de vida do SQLite.
=====================================================================
"""

from __future__ import annotations
from contextlib import contextmanager
import sqlite3
from typing import Generator, Optional
from database.schema import criar_tabelas
from exceptions import BancoDeDadosError


class Database:
    """
    Gerenciador de conexões SQLite com suporte a arquivo físico ou memória (:memory:).
    Garante PRAGMA foreign_keys = ON e transações ACID.
    """

    def __init__(self, db_path: str = "marketplace.db"):
        self.db_path = db_path
        self._conn: Optional[sqlite3.Connection] = None
        self._inicializar()

    def _inicializar(self) -> None:
        """Abre a conexão inicial e garante a existência das tabelas."""
        conn = self.obter_conexao()
        criar_tabelas(conn)

    def obter_conexao(self) -> sqlite3.Connection:
        """
        Retorna a conexão ativa. Para :memory: mantém a mesma conexão aberta
        para que as tabelas e dados persistam entre chamadas.
        """
        if self._conn is None:
            try:
                self._conn = sqlite3.connect(
                    self.db_path,
                    check_same_thread=False,
                    timeout=30.0,
                )
                self._conn.row_factory = sqlite3.Row
                self._conn.execute("PRAGMA foreign_keys = ON;")
            except sqlite3.Error as erro:
                raise BancoDeDadosError(f"Falha ao conectar ao banco SQLite '{self.db_path}': {erro}", causa=erro)
        return self._conn

    @contextmanager
    def transacao(self) -> Generator[sqlite3.Connection, None, None]:
        """
        Context manager para transações atômicas:
        executa commit se concluir sem erros; rollback caso ocorra exceção.
        """
        conn = self.obter_conexao()
        try:
            yield conn
            conn.commit()
        except Exception as erro:
            conn.rollback()
            if isinstance(erro, sqlite3.IntegrityError):
                raise
            raise

    def limpar_tudo(self) -> None:
        """
        Remove todos os dados das tabelas na ordem inversa de dependência,
        reseta sequências auto-incrementais e comita.
        """
        conn = self.obter_conexao()
        try:
            with self.transacao():
                conn.execute("PRAGMA foreign_keys = OFF;")
                conn.execute("DELETE FROM itens_pedido;")
                conn.execute("DELETE FROM pedidos;")
                conn.execute("DELETE FROM carrinho_itens;")
                conn.execute("DELETE FROM produtos;")
                conn.execute("DELETE FROM usuarios;")
                conn.execute("DELETE FROM sqlite_sequence WHERE name IN ('usuarios', 'produtos', 'pedidos', 'itens_pedido');")
                conn.execute("PRAGMA foreign_keys = ON;")
        except sqlite3.Error as erro:
            raise BancoDeDadosError(f"Erro ao limpar banco de dados: {erro}", causa=erro)

    def fechar(self) -> None:
        """Fecha a conexão com o banco de dados."""
        if self._conn is not None:
            try:
                self._conn.close()
            finally:
                self._conn = None


# Instância global padrão utilizada em tempo de execução normal
_banco_padrao: Optional[Database] = None


def obter_banco_padrao(db_path: str = "marketplace.db") -> Database:
    """Retorna ou cria o singleton da base de dados padrão."""
    global _banco_padrao
    if _banco_padrao is None:
        _banco_padrao = Database(db_path=db_path)
    return _banco_padrao


def resetar_banco_padrao(novo_banco: Optional[Database] = None) -> None:
    """Redefine o banco padrão (útil para testes unitários)."""
    global _banco_padrao
    if _banco_padrao is not None and _banco_padrao is not novo_banco:
        _banco_padrao.fechar()
    _banco_padrao = novo_banco

