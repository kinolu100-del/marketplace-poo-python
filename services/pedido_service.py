"""
=====================================================================
Serviço de Gestão de Carrinho e Pedidos (services/pedido_service.py)
=====================================================================
Regra de negócio pura:
  - Operações de carrinho (adicionar, remover, alterar quantidade, limpar).
  - Finalização de compra com validação de estoque, congelamento de valores,
    aplicação de taxa única por pedido físico e baixa de estoque encapsulada.
  - Cancelamento de pedido com reposição automática de estoque.
  - Sem chamadas a 'print()' ou 'input()'. Lança exceções de domínio.
=====================================================================
"""

from __future__ import annotations
from typing import List
from models.usuario import Cliente
from models.produto import Produto
from models.pedido import Pedido, StatusPedido
from repositories.pedido_repository import PedidoRepository
from repositories.usuario_repository import UsuarioRepository
from repositories.produto_repository import ProdutoRepository
from exceptions import (
    EntidadeNaoEncontradaError,
    EstoqueInsuficienteError,
    OperacaoInvalidaError,
)


class PedidoService:
    """[DEPENDÊNCIA]: Orquestra as regras de negócio de carrinhos e compras."""

    def __init__(
        self,
        pedido_repo: PedidoRepository,
        usuario_repo: UsuarioRepository,
        produto_repo: ProdutoRepository,
    ):
        self.pedido_repo = pedido_repo
        self.usuario_repo = usuario_repo
        self.produto_repo = produto_repo

    # -----------------------------------------------------------------
    # GESTÃO DO CARRINHO (COMPOSIÇÃO CLIENTE -> CARRINHO)
    # -----------------------------------------------------------------
    def obter_cliente(self, cliente_id: int) -> Cliente:
        """Busca e valida se o usuário informado é um Cliente."""
        usuario = self.usuario_repo.buscar_por_id(cliente_id)
        if usuario is None:
            raise EntidadeNaoEncontradaError("Cliente", cliente_id)
        if not isinstance(usuario, Cliente):
            raise OperacaoInvalidaError(f"O usuário de ID {cliente_id} não é um Cliente.")
        return usuario

    def obter_produto(self, produto_id: int) -> Produto:
        """Busca e valida se o produto existe no catálogo."""
        produto = self.produto_repo.buscar_por_id(produto_id)
        if produto is None:
            raise EntidadeNaoEncontradaError("Produto", produto_id)
        return produto

    def adicionar_ao_carrinho(self, cliente_id: int, produto_id: int, quantidade: int) -> None:
        """
        Adiciona itens ao carrinho do cliente respeitando a disponibilidade de estoque.
        """
        cliente = self.obter_cliente(cliente_id)
        produto = self.obter_produto(produto_id)

        ja_no_carrinho = cliente.carrinho.quantidade_de(produto)
        disponivel = produto.estoque - ja_no_carrinho

        if quantidade > disponivel:
            raise EstoqueInsuficienteError(produto.nome, disponivel, quantidade)

        cliente.carrinho.adicionar(produto, quantidade)

    def remover_do_carrinho(self, cliente_id: int, produto_id: int) -> None:
        """Remove determinado produto do carrinho do cliente."""
        cliente = self.obter_cliente(cliente_id)
        produto = self.obter_produto(produto_id)
        cliente.carrinho.remover(produto)

    def alterar_quantidade_carrinho(self, cliente_id: int, produto_id: int, nova_quantidade: int) -> None:
        """
        Atualiza a quantidade de um item no carrinho.
        Se nova_quantidade for maior que o estoque, lança EstoqueInsuficienteError.
        """
        cliente = self.obter_cliente(cliente_id)
        produto = self.obter_produto(produto_id)

        if nova_quantidade > produto.estoque:
            raise EstoqueInsuficienteError(produto.nome, produto.estoque, nova_quantidade)

        cliente.carrinho.alterar_quantidade(produto, nova_quantidade)

    def limpar_carrinho(self, cliente_id: int) -> None:
        """Esvazia o carrinho do cliente."""
        cliente = self.obter_cliente(cliente_id)
        cliente.carrinho.limpar()

    # -----------------------------------------------------------------
    # PROCESSAMENTO E FINALIZAÇÃO DE PEDIDOS
    # -----------------------------------------------------------------
    def finalizar_pedido(self, cliente_id: int) -> Pedido:
        """
        Finaliza a compra transformando o carrinho em um Pedido:
          1. Valida se o carrinho não está vazio.
          2. Valida se todo item tem estoque suficiente.
          3. Instancia o Pedido com composição de ItemPedido.
          4. Baixa o estoque de cada produto via Produto.baixar_estoque().
          5. Registra o pedido no histórico e esvazia o carrinho.
        """
        cliente = self.obter_cliente(cliente_id)
        if cliente.carrinho.esta_vazio():
            raise OperacaoInvalidaError("Não é possível finalizar uma compra com o carrinho vazio.")

        # Validação preventiva de estoque de todos os itens
        for item in cliente.carrinho.itens:
            if item.quantidade > item.produto.estoque:
                raise EstoqueInsuficienteError(
                    item.produto.nome,
                    item.produto.estoque,
                    item.quantidade,
                )

        # [COMPOSIÇÃO]: O Pedido cria seus próprios ItemPedido
        pedido = Pedido(cliente=cliente)
        for item in cliente.carrinho.itens:
            pedido.adicionar_item(item.produto, item.quantidade)
            # [ENCAPSULAMENTO]: Baixa o estoque através do método do próprio produto
            item.produto.baixar_estoque(item.quantidade)

        # Salva no repositório e no histórico do cliente
        self.pedido_repo.adicionar(pedido)
        cliente.adicionar_pedido(pedido)  # [ASSOCIAÇÃO]: Registra histórico

        # Limpa o carrinho após o sucesso da compra
        cliente.carrinho.limpar()
        return pedido

    def cancelar_pedido(self, pedido_id: int) -> Pedido:
        """
        Cancela um pedido existente:
          1. Verifica se o pedido existe e não está já cancelado.
          2. Devolve o estoque de todos os produtos via Produto.repor_estoque().
          3. Altera o status do pedido para CANCELADO.
        """
        pedido = self.pedido_repo.buscar_por_id(pedido_id)
        if pedido is None:
            raise EntidadeNaoEncontradaError("Pedido", pedido_id)

        if pedido.status == StatusPedido.CANCELADO:
            raise OperacaoInvalidaError(f"O Pedido #{pedido.id:04d} já está cancelado.")

        # Repõe o estoque dos produtos
        for item in pedido.itens:
            item.produto.repor_estoque(item.quantidade)

        pedido.cancelar()
        return pedido

    def buscar_por_id(self, pedido_id: int) -> Pedido:
        """Busca pedido por ID ou lança EntidadeNaoEncontradaError."""
        pedido = self.pedido_repo.buscar_por_id(pedido_id)
        if pedido is None:
            raise EntidadeNaoEncontradaError("Pedido", pedido_id)
        return pedido

    def listar_pedidos(self) -> List[Pedido]:
        """Retorna todos os pedidos registrados."""
        return self.pedido_repo.listar()

    def listar_pedidos_cliente(self, cliente_id: int) -> List[Pedido]:
        """Retorna os pedidos de um cliente específico."""
        self.obter_cliente(cliente_id)
        return self.pedido_repo.listar_por_cliente(cliente_id)
