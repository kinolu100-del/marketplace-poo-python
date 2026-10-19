"""
=====================================================================
Testes de Regras de Frete e Polimorfismo de Transporte (test_frete.py)
=====================================================================
Regras testadas:
  - ProdutoFisico calcula frete por peso: 3.50 * peso_kg * quantidade.
  - ProdutoDigital possui frete zero: Decimal("0.00").
  - Pedido aplica taxa de frete base (R$ 10.00) uma única vez se houver
    pelo menos um item físico, independentemente da quantidade de itens.
  - Pedido exclusivamente digital tem frete total zero.
=====================================================================
"""

from decimal import Decimal
import pytest
from models.usuario import Cliente, Vendedor
from models.produto import ProdutoFisico, ProdutoDigital
from models.pedido import Pedido


@pytest.fixture
def vendedor():
    return Vendedor("Loja Teste", "loja@teste.com", "Mega Loja")


@pytest.fixture
def cliente():
    return Cliente("Cliente Teste", "cliente@teste.com", "Rua A, 123")


def test_frete_produto_fisico_calculado_por_peso(vendedor):
    # Peso = 2.0 kg. Valor por kg = 3.50. Quantidade = 3.
    # Frete esperado = 3.50 * 2.0 * 3 = 21.00
    prod_fisico = ProdutoFisico("Cadeira Gamer", Decimal("500.00"), 10, vendedor, peso_kg=Decimal("2.00"))
    frete = prod_fisico.calcular_frete(quantidade=3)
    assert frete == Decimal("21.00")


def test_frete_produto_digital_sempre_zero(vendedor):
    prod_digital = ProdutoDigital(
        "Curso Online",
        Decimal("100.00"),
        50,
        vendedor,
        tamanho_mb=Decimal("500.0"),
        link_download="https://curso.com/download",
    )
    assert prod_digital.calcular_frete(quantidade=1) == Decimal("0.00")
    assert prod_digital.calcular_frete(quantidade=10) == Decimal("0.00")


def test_pedido_apenas_produtos_digitais_frete_total_zero(cliente, vendedor):
    prod_digital = ProdutoDigital(
        "E-book Python",
        Decimal("50.00"),
        20,
        vendedor,
        tamanho_mb=Decimal("15.0"),
        link_download="https://livro.com/ebook",
    )
    pedido = Pedido(cliente)
    pedido.adicionar_item(prod_digital, 2)

    assert not pedido.tem_produto_fisico
    assert pedido.frete_itens == Decimal("0.00")
    assert pedido.taxa_pedido_fisico == Decimal("0.00")
    assert pedido.frete_total == Decimal("0.00")
    assert pedido.subtotal == Decimal("100.00")
    assert pedido.total == Decimal("100.00")


def test_pedido_com_produto_fisico_aplica_taxa_unica_de_dez_reais(cliente, vendedor):
    # Produto físico de 1.0 kg -> Frete peso = 3.50 * 1.0 * 2 = 7.00
    # Taxa fixa por pedido = 10.00
    # Frete total esperado = 7.00 + 10.00 = 17.00
    prod_fisico = ProdutoFisico("Mousepad", Decimal("30.00"), 10, vendedor, peso_kg=Decimal("1.00"))
    pedido = Pedido(cliente)
    pedido.adicionar_item(prod_fisico, 2)

    assert pedido.tem_produto_fisico
    assert pedido.frete_itens == Decimal("7.00")
    assert pedido.taxa_pedido_fisico == Decimal("10.00")
    assert pedido.frete_total == Decimal("17.00")
    assert pedido.subtotal == Decimal("60.00")
    assert pedido.total == Decimal("77.00")


def test_pedido_misto_cobra_taxa_fixa_uma_unica_vez(cliente, vendedor):
    # 2 produtos físicos diferentes + 1 digital
    # Fisico 1: 0.5 kg x 2 = 1.0 kg * 3.50 = 3.50
    # Fisico 2: 1.0 kg x 1 = 1.0 kg * 3.50 = 3.50
    # Digital: frete = 0.00
    # Frete itens = 7.00
    # Taxa fixa pedido físico = 10.00 (cobrada uma única vez!)
    # Frete total = 17.00
    p_fisico1 = ProdutoFisico("Pen Drive", Decimal("40.00"), 10, vendedor, peso_kg=Decimal("0.50"))
    p_fisico2 = ProdutoFisico("Hub USB", Decimal("60.00"), 10, vendedor, peso_kg=Decimal("1.00"))
    p_digital = ProdutoDigital("Antivírus", Decimal("80.00"), 10, vendedor, tamanho_mb=Decimal("20.0"), link_download="https://av.com/dl")

    pedido = Pedido(cliente)
    pedido.adicionar_item(p_fisico1, 2)  # subtotal = 80.00, frete = 3.50
    pedido.adicionar_item(p_fisico2, 1)  # subtotal = 60.00, frete = 3.50
    pedido.adicionar_item(p_digital, 1)  # subtotal = 80.00, frete = 0.00

    assert pedido.tem_produto_fisico
    assert pedido.subtotal == Decimal("220.00")
    assert pedido.frete_itens == Decimal("7.00")
    assert pedido.taxa_pedido_fisico == Decimal("10.00")
    assert pedido.frete_total == Decimal("17.00")
    assert pedido.total == Decimal("237.00")
