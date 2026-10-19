"""
=====================================================================
Serviço de Gestão de Usuários (services/usuario_service.py)
=====================================================================
Regra de negócio pura:
  - Cadastros com validação de e-mail único.
  - Edição de perfil.
  - Exclusão protegida (não permite remover vendedor com produtos ou
    cliente com pedidos vinculados).
  - Sem chamadas a 'print()' ou 'input()'. Lança exceções de domínio.
=====================================================================
"""

from __future__ import annotations
from typing import List, Optional
from models.usuario import Usuario, Cliente, Vendedor
from repositories.usuario_repository import UsuarioRepository
from repositories.produto_repository import ProdutoRepository
from repositories.pedido_repository import PedidoRepository
from exceptions import (
    EmailDuplicadoError,
    EntidadeNaoEncontradaError,
    OperacaoInvalidaError,
)


class UsuarioService:
    """[DEPENDÊNCIA]: Orquestra as regras de negócio de usuários."""

    def __init__(
        self,
        usuario_repo: UsuarioRepository,
        produto_repo: ProdutoRepository,
        pedido_repo: PedidoRepository,
    ):
        self.usuario_repo = usuario_repo
        self.produto_repo = produto_repo
        self.pedido_repo = pedido_repo

    def cadastrar_cliente(self, nome: str, email: str, endereco: str) -> Cliente:
        """Cadastra um novo cliente garantindo unicidade de e-mail."""
        if self.usuario_repo.buscar_por_email(email) is not None:
            raise EmailDuplicadoError(email)
        cliente = Cliente(nome=nome, email=email, endereco=endereco)
        self.usuario_repo.adicionar(cliente)
        return cliente

    def cadastrar_vendedor(self, nome: str, email: str, nome_loja: str) -> Vendedor:
        """Cadastra um novo vendedor garantindo unicidade de e-mail."""
        if self.usuario_repo.buscar_por_email(email) is not None:
            raise EmailDuplicadoError(email)
        vendedor = Vendedor(nome=nome, email=email, nome_loja=nome_loja)
        self.usuario_repo.adicionar(vendedor)
        return vendedor

    def buscar_por_id(self, id_usuario: int) -> Usuario:
        """Busca usuário por ID ou lança EntidadeNaoEncontradaError."""
        usuario = self.usuario_repo.buscar_por_id(id_usuario)
        if usuario is None:
            raise EntidadeNaoEncontradaError("Usuário", id_usuario)
        return usuario

    def listar_usuarios(self) -> List[Usuario]:
        """Retorna todos os usuários cadastrados."""
        return self.usuario_repo.listar()

    def listar_clientes(self) -> List[Cliente]:
        """Retorna todos os clientes compradores."""
        return self.usuario_repo.listar_clientes()

    def listar_vendedores(self) -> List[Vendedor]:
        """Retorna todos os vendedores cadastrados."""
        return self.usuario_repo.listar_vendedores()

    def editar_usuario(
        self,
        id_usuario: int,
        nome: Optional[str] = None,
        email: Optional[str] = None,
        endereco: Optional[str] = None,
        nome_loja: Optional[str] = None,
    ) -> Usuario:
        """Edita atributos de um usuário existente."""
        usuario = self.buscar_por_id(id_usuario)

        if email is not None and email.strip().lower() != usuario.email.lower():
            existente = self.usuario_repo.buscar_por_email(email)
            if existente is not None and existente.id != id_usuario:
                raise EmailDuplicadoError(email)
            usuario.email = email

        if nome is not None:
            usuario.nome = nome

        if isinstance(usuario, Cliente) and endereco is not None:
            usuario.endereco = endereco

        if isinstance(usuario, Vendedor) and nome_loja is not None:
            usuario.nome_loja = nome_loja

        return usuario

    def remover_usuario(self, id_usuario: int) -> None:
        """
        Remove um usuário com proteção de integridade referencial:
          - Vendedor não pode ser removido se possuir produtos no catálogo.
          - Cliente não pode ser removido se possuir pedidos no histórico.
        """
        usuario = self.buscar_por_id(id_usuario)

        if isinstance(usuario, Vendedor):
            produtos = self.produto_repo.listar_por_vendedor(id_usuario)
            if len(produtos) > 0:
                raise OperacaoInvalidaError(
                    f"Não é permitido remover o vendedor '{usuario.nome}' pois ele possui "
                    f"{len(produtos)} produto(s) vinculado(s) ao seu catálogo."
                )

        if isinstance(usuario, Cliente):
            pedidos = self.pedido_repo.listar_por_cliente(id_usuario)
            if len(pedidos) > 0:
                raise OperacaoInvalidaError(
                    f"Não é permitido remover o cliente '{usuario.nome}' pois ele possui "
                    f"{len(pedidos)} pedido(s) associado(s) ao seu histórico."
                )

        self.usuario_repo.remover(id_usuario)
