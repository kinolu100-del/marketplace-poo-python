"""
=====================================================================
Módulo de Pedidos e Carrinho (models/pedido.py)
=====================================================================
CONCEITOS DE POO APLICADOS NESTE ARQUIVO:
  - [COMPOSIÇÃO]:
      - 'Cliente' compõe 'Carrinho' (ciclo de vida vinculado).
      - 'Pedido' compõe 'ItemPedido' (instanciados exclusivamente dentro do Pedido).
  - [ASSOCIAÇÃO]:
      - 'ItemPedido' referencia 'Produto' (guarda a referência do produto comprado).
      - 'Pedido' referencia 'Cliente' (o cliente titular da compra).
  - [DEPENDÊNCIA]:
      - 'Pedido.adicionar_item(produto, qtd)' recebe 'Produto' como parâmetro.
      - 'Carrinho' recebe 'Produto' em seus métodos (adicionar, remover, etc.)
        como dependência temporal de operação, sem ser dono dos produtos.
  - [POLIMORFISMO]:
      - Ao instanciar 'ItemPedido', o frete por peso é calculado polimorficamente
        por 'produto.calcular_frete(quantidade)', sem distinção via if/else de tipo.
  - [ENCAPSULAMENTO]:
      - Itens do carrinho acessíveis via cópia/lista somente leitura.
      - Atributos monetários em Decimal com quantização rigorosa.
=====================================================================
"""

from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum
import itertools
from typing import Dict, List, Optional, TYPE_CHECKING
from exceptions import ValorInvalidoError

if TYPE_CHECKING:
    from models.produto import Produto
    from models.usuario import Cliente


class StatusPedido(str, Enum):
    """Enum com os estados possíveis do ciclo de vida de um Pedido."""
    CONFIRMADO = "Confirmado"
    CANCELADO = "Cancelado"


@dataclass
class ItemCarrinho:
    """
    [DATACLASS / ASSOCIAÇÃO]
    Estrutura que armazena a intenção de compra de um produto e sua quantidade no carrinho.
    """
    produto: Produto
    quantidade: int

    def __post_init__(self) -> None:
        if self.quantidade <= 0:
            raise ValorInvalidoError("A quantidade do item no carrinho deve ser maior que zero.")

    @property
    def subtotal(self) -> Decimal:
        """[ENCAPSULAMENTO]: Subtotal do item no carrinho (preço * quantidade)."""
        sub = self.produto.preco * Decimal(str(self.quantidade))
        return sub.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


class Carrinho:
    """
    [COMPOSIÇÃO / DEPENDÊNCIA]
    Representa a cesta de compras privativa de um Cliente.
    Recebe 'Produto' em seus métodos como [DEPENDÊNCIA].
    """

    def __init__(self):
        # Mapeamento interno {id_produto: ItemCarrinho}
        self._itens: Dict[int, ItemCarrinho] = {}

    @property
    def itens(self) -> List[ItemCarrinho]:
        """[ENCAPSULAMENTO]: Lista somente leitura com os itens presentes no carrinho."""
        return list(self._itens.values())

    def adicionar(self, produto: Produto, quantidade: int) -> None:
        """
        [DEPENDÊNCIA]: Recebe Produto como parâmetro.
        Adiciona o produto ou soma à quantidade já existente.
        """
        if not isinstance(quantidade, int) or quantidade <= 0:
            raise ValorInvalidoError("A quantidade a adicionar deve ser um número inteiro maior que zero.")
        if produto.id in self._itens:
            nova_qtd = self._itens[produto.id].quantidade + quantidade
            self._itens[produto.id].quantidade = nova_qtd
        else:
            self._itens[produto.id] = ItemCarrinho(produto=produto, quantidade=quantidade)

    def remover(self, produto: Produto) -> None:
        """[DEPENDÊNCIA]: Remove integralmente um produto do carrinho."""
        if produto.id in self._itens:
            del self._itens[produto.id]

    def alterar_quantidade(self, produto: Produto, nova_quantidade: int) -> None:
        """
        [DEPENDÊNCIA]: Atualiza a quantidade do item.
        Se a nova quantidade for menor ou igual a zero, remove o item.
        """
        if nova_quantidade <= 0:
            self.remover(produto)
        elif produto.id in self._itens:
            self._itens[produto.id].quantidade = nova_quantidade
        else:
            self._itens[produto.id] = ItemCarrinho(produto=produto, quantidade=nova_quantidade)

    def quantidade_de(self, produto: Produto) -> int:
        """Retorna a quantidade já colocada no carrinho para o produto informado."""
        item = self._itens.get(produto.id)
        return item.quantidade if item else 0

    def esta_vazio(self) -> bool:
        """Informa se o carrinho possui ao menos um item."""
        return len(self._itens) == 0

    def limpar(self) -> None:
        """Esvazia todos os itens do carrinho."""
        self._itens.clear()

    @property
    def subtotal(self) -> Decimal:
        """Calcula o valor acumulado de todos os itens do carrinho."""
        total = sum((item.subtotal for item in self._itens.values()), Decimal("0.00"))
        return total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


class ItemPedido:
    """
    [COMPOSIÇÃO + ASSOCIAÇÃO]
    Entidade que compõe o Pedido.
      - [ASSOCIAÇÃO]: Mantém referência ao 'Produto' comprado.
      - Congela o preço unitário e o frete no momento da compra para segurança histórica.
    """

    def __init__(self, produto: Produto, quantidade: int):
        if not isinstance(quantidade, int) or quantidade <= 0:
            raise ValorInvalidoError("A quantidade do item de pedido deve ser maior que zero.")
        self._produto = produto  # [ASSOCIAÇÃO]: Associação direta com o Produto
        self._quantidade = quantidade
        # Congela o valor unitário no ato da compra
        self._preco_unitario: Decimal = produto.preco
        # [POLIMORFISMO]: O produto calcula o seu próprio frete variável (peso ou zero)
        self._frete: Decimal = produto.calcular_frete(quantidade)

    @property
    def produto(self) -> Produto:
        """[ASSOCIAÇÃO / ENCAPSULAMENTO]: Produto associado ao item."""
        return self._produto

    @property
    def quantidade(self) -> int:
        return self._quantidade

    @property
    def preco_unitario(self) -> Decimal:
        return self._preco_unitario

    @property
    def frete(self) -> Decimal:
        return self._frete

    @property
    def subtotal(self) -> Decimal:
        """Subtotal dos produtos do item (preço unitário congelado * quantidade)."""
        sub = self._preco_unitario * Decimal(str(self._quantidade))
        return sub.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    @property
    def total(self) -> Decimal:
        """Total do item somando seu subtotal e o frete por peso."""
        tot = self.subtotal + self._frete
        return tot.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


class Pedido:
    """
    [COMPOSIÇÃO + ASSOCIAÇÃO + DEPENDÊNCIA]
    Representa uma transação finalizada de compra.
      - [COMPOSIÇÃO]: Instancia e gerencia os objetos 'ItemPedido' internamente.
      - [ASSOCIAÇÃO]: Associa-se ao 'Cliente' comprador.
      - [DEPENDÊNCIA]: Recebe 'Produto' como parâmetro em 'adicionar_item()'.
    """

    # Taxa fixa de frete cobrada UMA ÚNICA VEZ por pedido se houver ao menos um produto físico
    TAXA_PEDIDO_FISICO = Decimal("10.00")

    _gerador_id = itertools.count(1)

    def __init__(self, cliente: Cliente, id_pedido: Optional[int] = None):
        self._id = id_pedido if id_pedido is not None else next(Pedido._gerador_id)
        self._cliente = cliente            # [ASSOCIAÇÃO]: Cliente comprador
        self._itens: List[ItemPedido] = []  # [COMPOSIÇÃO]: Lista de itens exclusivos do pedido
        self._data_criacao = datetime.now()
        self._status = StatusPedido.CONFIRMADO

    @classmethod
    def resetar_gerador_id(cls, inicio: int = 1) -> None:
        """Reinicia o gerador sequencial de IDs (útil para testes isolados)."""
        cls._gerador_id = itertools.count(inicio)

    @property
    def id(self) -> int:
        return self._id

    @property
    def cliente(self) -> Cliente:
        return self._cliente

    @property
    def itens(self) -> List[ItemPedido]:
        """[COMPOSIÇÃO / ENCAPSULAMENTO]: Retorna a lista de itens do pedido."""
        return list(self._itens)

    @property
    def data_criacao(self) -> datetime:
        return self._data_criacao

    @property
    def status(self) -> StatusPedido:
        return self._status

    def cancelar(self) -> None:
        """Atualiza o estado do pedido para CANCELADO."""
        self._status = StatusPedido.CANCELADO

    def adicionar_item(self, produto: Produto, quantidade: int) -> None:
        """
        [COMPOSIÇÃO / DEPENDÊNCIA]
        Recebe Produto como parâmetro temporário e cria uma nova instância de
        ItemPedido, incorporando-a exclusivamente à sua coleção interna.
        """
        item = ItemPedido(produto, quantidade)
        self._itens.append(item)

    @property
    def tem_produto_fisico(self) -> bool:
        """Verifica se há pelo menos um item físico no pedido para aplicar a taxa base."""
        return any(item.produto.tipo() == "Físico" for item in self._itens)

    @property
    def subtotal(self) -> Decimal:
        """Soma o subtotal de todos os itens do pedido."""
        tot = sum((item.subtotal for item in self._itens), Decimal("0.00"))
        return tot.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    @property
    def frete_itens(self) -> Decimal:
        """Soma o frete variável (por peso) de todos os itens."""
        tot = sum((item.frete for item in self._itens), Decimal("0.00"))
        return tot.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    @property
    def taxa_pedido_fisico(self) -> Decimal:
        """Taxa base de R$ 10,00 cobrada uma única vez por pedido caso haja item físico."""
        if self.tem_produto_fisico:
            return self.TAXA_PEDIDO_FISICO
        return Decimal("0.00")

    @property
    def frete_total(self) -> Decimal:
        """Frete total do pedido = frete variável por peso + taxa única de pedido físico."""
        tot = self.frete_itens + self.taxa_pedido_fisico
        return tot.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    @property
    def total(self) -> Decimal:
        """Total consolidado do pedido: subtotal dos produtos + frete total."""
        tot = self.subtotal + self.frete_total
        return tot.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def resumo(self) -> str:
        """Retorna uma linha descritiva resumida do pedido sem acoplamento com prints."""
        data_str = self.data_criacao.strftime("%d/%m/%Y %H:%M")
        return (
            f"Pedido #{self.id:04d} | {data_str} | Cliente: {self.cliente.nome} | "
            f"Status: {self.status.value} | Total: R$ {self.total:.2f}"
        )
