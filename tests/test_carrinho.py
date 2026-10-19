"""
=====================================================================
Testes de Carrinho de Compras (test_carrinho.py)
=====================================================================
Valida a substituição do dicionário bruto por ItemCarrinho dataclass,
soma de quantidades, alteração, remoção, subtotal e imutabilidade da lista de itens.
=====================================================================
"""

from decimal import Decimal
import pytest
from models.usuario import Vendedor
from models.produto import ProdutoFisico, ProdutoDigital
from models.pedido import Carrinho, ItemCarrinho
from exceptions import ValorInvalidoError


@pytest.fixture
def produtos():
    vendedor = Vendedor("Mega Informática", "mega@info.com", "Mega Info")
    p1 = ProdutoFisico("Teclado Mecânico", Decimal("250.00"), 10, vendedor, peso_kg=Decimal("0.80"))
    p2 = ProdutoDigital("Curso Python", Decimal("100.00"), 50, vendedor, tamanho_mb=Decimal("200.0"), link_download="https://curso.com")
    return p1, p2


def test_adicionar_item_e_dataclass_item_carrinho(produtos):
    p1, _ = produtos
    carrinho = Carrinho()
    assert carrinho.esta_vazio()

    carrinho.adicionar(p1, 2)
    assert not carrinho.esta_vazio()
    assert len(carrinho.itens) == 1

    item = carrinho.itens[0]
    assert isinstance(item, ItemCarrinho)
    assert item.produto == p1
    assert item.quantidade == 2
    assert item.subtotal == Decimal("500.00")


def test_adicionar_mesmo_produto_incrementa_quantidade(produtos):
    p1, _ = produtos
    carrinho = Carrinho()
    carrinho.adicionar(p1, 2)
    carrinho.adicionar(p1, 3)

    assert len(carrinho.itens) == 1
    assert carrinho.quantidade_de(p1) == 5
    assert carrinho.subtotal == Decimal("1250.00")


def test_alterar_quantidade_carrinho(produtos):
    p1, p2 = produtos
    carrinho = Carrinho()
    carrinho.adicionar(p1, 2)
    carrinho.adicionar(p2, 1)

    carrinho.alterar_quantidade(p1, 4)
    assert carrinho.quantidade_de(p1) == 4

    # Alterar para zero remove o produto
    carrinho.alterar_quantidade(p2, 0)
    assert carrinho.quantidade_de(p2) == 0
    assert len(carrinho.itens) == 1


def test_remover_produto_do_carrinho(produtos):
    p1, p2 = produtos
    carrinho = Carrinho()
    carrinho.adicionar(p1, 1)
    carrinho.adicionar(p2, 2)

    carrinho.remover(p1)
    assert carrinho.quantidade_de(p1) == 0
    assert len(carrinho.itens) == 1
    assert carrinho.itens[0].produto == p2


def test_limpar_carrinho(produtos):
    p1, p2 = produtos
    carrinho = Carrinho()
    carrinho.adicionar(p1, 2)
    carrinho.adicionar(p2, 3)

    carrinho.limpar()
    assert carrinho.esta_vazio()
    assert len(carrinho.itens) == 0
    assert carrinho.subtotal == Decimal("0.00")


def test_adicionar_quantidade_invalida_lanca_erro(produtos):
    p1, _ = produtos
    carrinho = Carrinho()
    with pytest.raises(ValorInvalidoError):
        carrinho.adicionar(p1, 0)
    with pytest.raises(ValorInvalidoError):
        carrinho.adicionar(p1, -1)


def test_itens_propriedade_somente_leitura(produtos):
    p1, _ = produtos
    carrinho = Carrinho()
    carrinho.adicionar(p1, 1)

    itens = carrinho.itens
    itens.clear()  # Modificação na lista cópia não pode afetar o carrinho interno
    assert len(carrinho.itens) == 1
