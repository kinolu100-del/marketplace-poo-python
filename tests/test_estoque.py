"""
=====================================================================
Testes de Encapsulamento de Estoque (test_estoque.py)
=====================================================================
Valida os métodos baixar_estoque e repor_estoque, garantindo integridade
de dados e tratamento de exceções para saldo insuficiente.
=====================================================================
"""

from decimal import Decimal
import pytest
from models.usuario import Vendedor
from models.produto import ProdutoFisico
from exceptions import EstoqueInsuficienteError, ValorInvalidoError


@pytest.fixture
def produto():
    vendedor = Vendedor("Tech Store", "tech@store.com", "Tech Store")
    return ProdutoFisico("Headset Gamer", Decimal("200.00"), estoque=10, vendedor=vendedor, peso_kg=Decimal("0.40"))


def test_baixa_de_estoque_com_sucesso(produto):
    produto.baixar_estoque(4)
    assert produto.estoque == 6


def test_baixa_de_estoque_zerando_saldo(produto):
    produto.baixar_estoque(10)
    assert produto.estoque == 0


def test_baixa_de_estoque_insuficiente_lanca_excecao(produto):
    # Deve lançar EstoqueInsuficienteError (e também ser capturável como ValueError)
    with pytest.raises(EstoqueInsuficienteError) as exc_info:
        produto.baixar_estoque(11)

    assert "Estoque insuficiente" in str(exc_info.value)
    assert exc_info.value.disponivel == 10
    assert exc_info.value.solicitado == 11

    # Garante que também é compatível com ValueError conforme requisito
    with pytest.raises(ValueError):
        produto.baixar_estoque(15)


def test_baixa_de_estoque_quantidade_invalida_lanca_erro(produto):
    with pytest.raises(ValorInvalidoError):
        produto.baixar_estoque(0)

    with pytest.raises(ValorInvalidoError):
        produto.baixar_estoque(-3)


def test_reposicao_de_estoque_com_sucesso(produto):
    produto.repor_estoque(5)
    assert produto.estoque == 15


def test_reposicao_de_estoque_quantidade_invalida_lanca_erro(produto):
    with pytest.raises(ValorInvalidoError):
        produto.repor_estoque(0)

    with pytest.raises(ValorInvalidoError):
        produto.repor_estoque(-2)
