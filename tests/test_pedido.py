"""
=====================================================================
Testes de Pedido e ItemPedido (test_pedido.py)
=====================================================================
Verifica composição entre Pedido e ItemPedido, congelamento histórico
de preços, cálculo de totais e regras de cancelamento com devolução de estoque.
=====================================================================
"""

from decimal import Decimal
import pytest
from models.usuario import Cliente, Vendedor
from models.produto import ProdutoFisico
from models.pedido import Pedido, StatusPedido
from exceptions import OperacaoInvalidaError


@pytest.fixture
def cenario():
    vendedor = Vendedor("Vendedor Um", "v1@loja.com", "Loja Um")
    cliente = Cliente("Cliente Um", "c1@email.com", "Rua Centro, 100")
    produto = ProdutoFisico("Monitor 24pol", Decimal("800.00"), estoque=5, vendedor=vendedor, peso_kg=Decimal("3.00"))
    return cliente, produto


def test_congelamento_de_preco_no_item_pedido(cenario):
    cliente, produto = cenario
    pedido = Pedido(cliente)
    pedido.adicionar_item(produto, quantidade=2)

    item = pedido.itens[0]
    assert item.preco_unitario == Decimal("800.00")
    # Frete unitário congelado = 3.50 * 3.00 * 2 = 21.00
    assert item.frete == Decimal("21.00")

    # Altera o preço e estoque do produto posteriormente
    produto.preco = Decimal("950.00")
    produto.baixar_estoque(2)

    # O pedido histórico deve permanecer inalterado (congelamento)
    assert item.preco_unitario == Decimal("800.00")
    assert item.subtotal == Decimal("1600.00")
    assert item.frete == Decimal("21.00")
    assert item.total == Decimal("1621.00")


def test_totais_do_pedido(cenario):
    cliente, produto = cenario
    pedido = Pedido(cliente)
    pedido.adicionar_item(produto, quantidade=1)

    # Subtotal = 800.00
    # Frete por peso = 3.50 * 3.00 * 1 = 10.50
    # Taxa fixa pedido físico = 10.00
    # Frete total = 20.50
    # Total = 820.50
    assert pedido.subtotal == Decimal("800.00")
    assert pedido.frete_itens == Decimal("10.50")
    assert pedido.taxa_pedido_fisico == Decimal("10.00")
    assert pedido.frete_total == Decimal("20.50")
    assert pedido.total == Decimal("820.50")
    assert pedido.status == StatusPedido.CONFIRMADO


def test_status_e_cancelamento_do_pedido(cenario):
    cliente, produto = cenario
    pedido = Pedido(cliente)
    pedido.adicionar_item(produto, quantidade=2)

    assert pedido.status == StatusPedido.CONFIRMADO
    pedido.cancelar()
    assert pedido.status == StatusPedido.CANCELADO


def test_resumo_sem_prints(cenario):
    cliente, produto = cenario
    pedido = Pedido(cliente)
    pedido.adicionar_item(produto, 1)

    resumo = pedido.resumo()
    assert isinstance(resumo, str)
    assert f"Pedido #{pedido.id:04d}" in resumo
    assert "Cliente Um" in resumo
    assert "Confirmado" in resumo
