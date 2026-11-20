"""
=====================================================================
Repositório SQLite de Usuários (repositories/usuario_repository.py)
=====================================================================
Implementação de persistência relacional em SQLite para Clientes e
Vendedores. Mantém exatamente as mesmas assinaturas do repositório
em memória para garantir compatibilidade com as camadas de domínio,
serviços e interface.
=====================================================================
"""

from __future__ import annotations
import sqlite3
from typing import Dict, List, Optional, TYPE_CHECKING
from database.connection import Database, obter_banco_padrao
from models.usuario import Usuario, Cliente, Vendedor
from models.pedido import ItemCarrinho
from repositories.carrinho_persistente import CarrinhoPersistente
from exceptions import BancoDeDadosError, EmailDuplicadoError, OperacaoInvalidaError

if TYPE_CHECKING:
    from repositories.produto_repository import ProdutoRepository


class ClientePersistente(Cliente):
    """
    Subclasse de Cliente que sincroniza mutações de atributos em memória
    imediatamente com o banco de dados relacional.
    """
    def __init__(self, *args, db: Optional[Database] = None, **kwargs):
        super().__init__(*args, **kwargs)
        self._db = db

    @Cliente.nome.setter
    def nome(self, valor: str) -> None:
        Usuario.nome.fset(self, valor)
        if getattr(self, "_db", None):
            with self._db.transacao() as conn:
                conn.execute("UPDATE usuarios SET nome = ? WHERE id = ?", (self._nome, self.id))

    @Cliente.email.setter
    def email(self, valor: str) -> None:
        Usuario.email.fset(self, valor)
        if getattr(self, "_db", None):
            with self._db.transacao() as conn:
                conn.execute("UPDATE usuarios SET email = ? WHERE id = ?", (self._email, self.id))

    @Cliente.endereco.setter
    def endereco(self, valor: str) -> None:
        Cliente.endereco.fset(self, valor)
        if getattr(self, "_db", None):
            with self._db.transacao() as conn:
                conn.execute("UPDATE usuarios SET endereco = ? WHERE id = ?", (self._endereco, self.id))


class VendedorPersistente(Vendedor):
    """
    Subclasse de Vendedor que sincroniza mutações de atributos em memória
    imediatamente com o banco de dados relacional.
    """
    def __init__(self, *args, db: Optional[Database] = None, **kwargs):
        super().__init__(*args, **kwargs)
        self._db = db

    @Vendedor.nome.setter
    def nome(self, valor: str) -> None:
        Usuario.nome.fset(self, valor)
        if getattr(self, "_db", None):
            with self._db.transacao() as conn:
                conn.execute("UPDATE usuarios SET nome = ? WHERE id = ?", (self._nome, self.id))

    @Vendedor.email.setter
    def email(self, valor: str) -> None:
        Usuario.email.fset(self, valor)
        if getattr(self, "_db", None):
            with self._db.transacao() as conn:
                conn.execute("UPDATE usuarios SET email = ? WHERE id = ?", (self._email, self.id))

    @Vendedor.nome_loja.setter
    def nome_loja(self, valor: str) -> None:
        Vendedor.nome_loja.fset(self, valor)
        if getattr(self, "_db", None):
            with self._db.transacao() as conn:
                conn.execute("UPDATE usuarios SET nome_loja = ? WHERE id = ?", (self._nome_loja, self.id))


class UsuarioRepository:
    """Repositório responsável pela persistência de Usuários em SQLite."""

    def __init__(self, db: Optional[Database] = None, db_path: Optional[str] = None):
        if db is not None:
            self._db = db
        elif db_path is not None:
            self._db = Database(db_path)
        else:
            self._db = obter_banco_padrao()

        # Cache de identidade {id_usuario: Usuario} para evitar objetos duplicados em memória
        self._cache: Dict[int, Usuario] = {}
        self._produto_repo: Optional[Any] = None
        self._sincronizar_gerador_id()

    def vincular_produto_repo(self, produto_repo: Any) -> None:
        """Vincula a instância única compartilhada de ProdutoRepository para reidratação de carrinhos."""
        self._produto_repo = produto_repo

    @property
    def db(self) -> Database:
        return self._db

    def _sincronizar_gerador_id(self) -> None:
        """Sincroniza o gerador de ID sequencial com o maior ID existente na base."""
        conn = self._db.obter_conexao()
        cursor = conn.cursor()
        cursor.execute("SELECT COALESCE(MAX(id), 0) FROM usuarios")
        max_id = cursor.fetchone()[0]
        Usuario.resetar_gerador_id(max_id + 1)

    def adicionar(self, usuario: Usuario) -> Usuario:
        """
        Armazena um novo usuário ou atualiza se já existir no banco.
        Trata conflitos de unicidade de e-mail.
        """
        conn = self._db.obter_conexao()
        tipo = usuario.tipo()
        endereco = getattr(usuario, "endereco", None)
        nome_loja = getattr(usuario, "nome_loja", None)

        try:
            with self._db.transacao():
                conn.execute(
                    """
                    INSERT INTO usuarios (id, nome, email, tipo, endereco, nome_loja)
                    VALUES (?, ?, ?, ?, ?, ?)
                    ON CONFLICT(id) DO UPDATE SET
                        nome = excluded.nome,
                        email = excluded.email,
                        tipo = excluded.tipo,
                        endereco = excluded.endereco,
                        nome_loja = excluded.nome_loja
                    """,
                    (usuario.id, usuario.nome, usuario.email, tipo, endereco, nome_loja),
                )
        except sqlite3.IntegrityError as erro:
            msg = str(erro).lower()
            if "unique constraint failed: usuarios.email" in msg or "usuarios.email" in msg:
                raise EmailDuplicadoError(usuario.email)
            raise OperacaoInvalidaError(f"Erro de integridade ao salvar usuário: {erro}")
        except sqlite3.Error as erro:
            raise BancoDeDadosError(f"Erro no banco ao adicionar usuário: {erro}", causa=erro)

        # Associa referência do banco ao objeto para atualizações automáticas via setter
        if isinstance(usuario, (ClientePersistente, VendedorPersistente)):
            usuario._db = self._db

        if isinstance(usuario, Cliente):
            if not isinstance(usuario.carrinho, CarrinhoPersistente):
                carrinho = CarrinhoPersistente(usuario.id, self._db)
                carrinho.carregar_itens_banco(usuario.carrinho._itens)
                usuario._carrinho = carrinho
                # Persiste itens que já estavam no carrinho
                for item in usuario.carrinho.itens:
                    with self._db.transacao() as conn_carrinho:
                        conn_carrinho.execute(
                            """
                            INSERT INTO carrinho_itens (cliente_id, produto_id, quantidade)
                            VALUES (?, ?, ?)
                            ON CONFLICT(cliente_id, produto_id) DO UPDATE SET quantidade = ?
                            """,
                            (usuario.id, item.produto.id, item.quantidade, item.quantidade),
                        )

        self._cache[usuario.id] = usuario
        self._sincronizar_gerador_id()
        return usuario

    def _reconstruir_usuario(self, row: sqlite3.Row) -> Usuario:
        """Reidrata um objeto de domínio a partir de uma linha do SQLite."""
        uid = row["id"]
        if uid in self._cache:
            return self._cache[uid]

        tipo = row["tipo"]
        if tipo == "Cliente":
            usuario = ClientePersistente(
                nome=row["nome"],
                email=row["email"],
                endereco=row["endereco"],
                id_usuario=uid,
                db=self._db,
            )
            # Reidrata carrinho persistente a partir do banco
            carrinho = CarrinhoPersistente(uid, self._db)
            conn = self._db.obter_conexao()
            cursor = conn.cursor()
            cursor.execute("SELECT produto_id, quantidade FROM carrinho_itens WHERE cliente_id = ?", (uid,))
            itens_banco = cursor.fetchall()
            if itens_banco:
                p_repo = self._produto_repo
                if p_repo is None:
                    from repositories.produto_repository import ProdutoRepository
                    p_repo = ProdutoRepository(db=self._db, usuario_repo=self)
                    self._produto_repo = p_repo
                itens_dict = {}
                for item_row in itens_banco:
                    prod = p_repo.buscar_por_id(item_row["produto_id"])
                    if prod:
                        itens_dict[prod.id] = ItemCarrinho(produto=prod, quantidade=item_row["quantidade"])
                carrinho.carregar_itens_banco(itens_dict)
            usuario._carrinho = carrinho
        elif tipo == "Vendedor":
            usuario = VendedorPersistente(
                nome=row["nome"],
                email=row["email"],
                nome_loja=row["nome_loja"],
                id_usuario=uid,
                db=self._db,
            )
        else:
            raise BancoDeDadosError(f"Tipo desconhecido de usuário no banco de dados: {tipo}")

        self._cache[uid] = usuario
        return usuario

    def buscar_por_id(self, id_usuario: int) -> Optional[Usuario]:
        """Busca um usuário pelo seu ID."""
        if id_usuario in self._cache:
            return self._cache[id_usuario]

        conn = self._db.obter_conexao()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM usuarios WHERE id = ?", (id_usuario,))
        row = cursor.fetchone()
        if row is None:
            return None
        return self._reconstruir_usuario(row)

    def buscar_por_email(self, email: str) -> Optional[Usuario]:
        """Busca um usuário pelo seu endereço de e-mail (case-insensitive)."""
        email_limpo = email.strip().lower()
        # Primeiro confere no cache
        for u in self._cache.values():
            if u.email.lower() == email_limpo:
                return u

        conn = self._db.obter_conexao()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM usuarios WHERE LOWER(email) = ?", (email_limpo,))
        row = cursor.fetchone()
        if row is None:
            return None
        return self._reconstruir_usuario(row)

    def listar(self) -> List[Usuario]:
        """Retorna todos os usuários cadastrados."""
        conn = self._db.obter_conexao()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM usuarios ORDER BY id ASC")
        return [self._reconstruir_usuario(row) for row in cursor.fetchall()]

    def listar_clientes(self) -> List[Cliente]:
        """Filtra e retorna apenas clientes cadastrados."""
        conn = self._db.obter_conexao()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM usuarios WHERE tipo = 'Cliente' ORDER BY id ASC")
        return [self._reconstruir_usuario(row) for row in cursor.fetchall()]  # type: ignore

    def listar_vendedores(self) -> List[Vendedor]:
        """Filtra e retorna apenas vendedores cadastrados."""
        conn = self._db.obter_conexao()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM usuarios WHERE tipo = 'Vendedor' ORDER BY id ASC")
        return [self._reconstruir_usuario(row) for row in cursor.fetchall()]  # type: ignore

    def remover(self, id_usuario: int) -> bool:
        """Remove o usuário do banco pelo seu ID."""
        conn = self._db.obter_conexao()
        try:
            with self._db.transacao():
                cursor = conn.execute("DELETE FROM usuarios WHERE id = ?", (id_usuario,))
                removido = cursor.rowcount > 0
                if removido and id_usuario in self._cache:
                    del self._cache[id_usuario]
                return removido
        except sqlite3.IntegrityError as erro:
            raise OperacaoInvalidaError(
                f"Não é permitido remover o usuário ID {id_usuario} devido a vínculos ativos no banco: {erro}"
            )
        except sqlite3.Error as erro:
            raise BancoDeDadosError(f"Erro ao remover usuário: {erro}", causa=erro)

    def limpar(self) -> None:
        """Esvazia a tabela de usuários e limpa o cache."""
        self._cache.clear()
        conn = self._db.obter_conexao()
        try:
            with self._db.transacao():
                conn.execute("DELETE FROM usuarios")
                conn.execute("DELETE FROM sqlite_sequence WHERE name = 'usuarios'")
            self._sincronizar_gerador_id()
        except sqlite3.Error as erro:
            raise BancoDeDadosError(f"Erro ao limpar repositório de usuários: {erro}", causa=erro)
