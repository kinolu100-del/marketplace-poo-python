"""
=====================================================================
Testes de Funções Auxiliares de UI e Formatação (test_helpers.py)
=====================================================================
Valida a formatação monetária em padrão brasileiro (R$ X.XXX,XX)
para float, int e Decimal.
=====================================================================
"""

from decimal import Decimal
from ui.helpers import moeda


def test_formatacao_moeda_padrao_brasileiro():
    assert moeda(Decimal("0.00")) == "R$ 0,00"
    assert moeda(Decimal("5.90")) == "R$ 5,90"
    assert moeda(Decimal("49.99")) == "R$ 49,99"
    assert moeda(Decimal("1250.50")) == "R$ 1.250,50"
    assert moeda(Decimal("1000000.00")) == "R$ 1.000.000,00"


def test_formatacao_moeda_com_float_e_int():
    assert moeda(10) == "R$ 10,00"
    assert moeda(149.5) == "R$ 149,50"
    assert moeda(1234.56) == "R$ 1.234,56"
