"""
=====================================================================
Serviço de Gestão de Produtos (services/produto_service.py)
=====================================================================
Regra de negócio pura:
  - Cadastro de produtos físicos e digitais com vínculo obrigatório a Vendedor.
  - Edição de preço e estoque com validação de limites.
  - Remoção de produtos mantendo a integridade com o catálogo do vendedor.
  - Sem chamadas a 'print()' ou 'input()'. Lança exceções de domínio.
=====================================================================
"""

from __future__ import annotations
from decimal import Decimal
from typing import List, Optional, Union
from models.produto import Produto, ProdutoFisico, ProdutoDigital
from models.usuario import Vendedor
from repositories.produto_repository import ProdutoRepository
from repositories.usuario_repository import UsuarioRepository
from exceptions import EntidadeNaoEncontradaError, OperacaoInvalidaError


class ProdutoService:
    """[DEPENDÊNCIA]: Orquestra as regras de negócio de produtos."""

    def __init__(self, produto_repo: ProdutoRepository, usuario_repo: UsuarioRepository):
        self.produto_repo = produto_repo
        self.usuario_repo = usuario_repo

    def cadastrar_produto_fisico(
        self,
        nome: str,
        preco: Union[Decimal, float, int, str],
        estoque: int,
        vendedor_id: int,
        peso_kg: Union[Decimal, float, int, str],
    ) -> ProdutoFisico:
        """Cadastra produto físico e associa ao vendedor."""
        usuario = self.usuario_repo.buscar_por_id(vendedor_id)
        if usuario is None:
            raise EntidadeNaoEncontradaError("Vendedor", vendedor_id)
        if not isinstance(usuario, Vendedor):
            raise OperacaoInvalidaError(f"O usuário de ID {vendedor_id} não é um Vendedor.")

        produto = ProdutoFisico(
            nome=nome,
            preco=preco,
            estoque=estoque,
            vendedor=usuario,
            peso_kg=peso_kg,
        )
        self.produto_repo.adicionar(produto)
        usuario.adicionar_produto(produto)  # [ASSOCIAÇÃO]: Registra na loja
        return produto

    def cadastrar_produto_digital(
        self,
        nome: str,
        preco: Union[Decimal, float, int, str],
        estoque: int,
        vendedor_id: int,
        tamanho_mb: Union[Decimal, float, int, str],
        link_download: str,
    ) -> ProdutoDigital:
        """Cadastra produto digital e associa ao vendedor."""
        usuario = self.usuario_repo.buscar_por_id(vendedor_id)
        if usuario is None:
            raise EntidadeNaoEncontradaError("Vendedor", vendedor_id)
        if not isinstance(usuario, Vendedor):
            raise OperacaoInvalidaError(f"O usuário de ID {vendedor_id} não é um Vendedor.")

        produto = ProdutoDigital(
            nome=nome,
            preco=preco,
            estoque=estoque,
            vendedor=usuario,
            tamanho_mb=tamanho_mb,
            link_download=link_download,
        )
        self.produto_repo.adicionar(produto)
        usuario.adicionar_produto(produto)  # [ASSOCIAÇÃO]: Registra na loja
        return produto

    def buscar_por_id(self, id_produto: int) -> Produto:
        """Busca produto por ID ou lança EntidadeNaoEncontradaError."""
        produto = self.produto_repo.buscar_por_id(id_produto)
        if produto is None:
            raise EntidadeNaoEncontradaError("Produto", id_produto)
        return produto

    def listar_produtos(self) -> List[Produto]:
        """Retorna todos os produtos disponíveis."""
        return self.produto_repo.listar()

    def listar_por_vendedor(self, id_vendedor: int) -> List[Produto]:
        """Retorna os produtos de um vendedor específico."""
        usuario = self.usuario_repo.buscar_por_id(id_vendedor)
        if usuario is None:
            raise EntidadeNaoEncontradaError("Vendedor", id_vendedor)
        return self.produto_repo.listar_por_vendedor(id_vendedor)

    def editar_produto(
        self,
        id_produto: int,
        novo_preco: Optional[Union[Decimal, float, int, str]] = None,
        novo_estoque: Optional[int] = None,
    ) -> Produto:
        """Atualiza preço e/ou estoque do produto."""
        produto = self.buscar_por_id(id_produto)
        if novo_preco is not None:
            produto.preco = novo_preco
        if novo_estoque is not None:
            produto.estoque = novo_estoque
        return produto

    def remover_produto(self, id_produto: int) -> None:
        """Remove produto do catálogo geral e do vendedor."""
        produto = self.buscar_por_id(id_produto)
        produto.vendedor.remover_produto(produto)  # [ASSOCIAÇÃO]: Remove da lista do vendedor
        self.produto_repo.remover(id_produto)
