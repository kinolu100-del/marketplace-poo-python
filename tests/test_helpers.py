"""
=====================================================================
Testes de Funções Auxiliares de UI e Formatação (test_helpers.py)
=====================================================================
Valida a formatação monetária em padrão brasileiro (R$ X.XXX,XX)
para float, int e Decimal.
=====================================================================
"""

from decimal import Decimal
from ui.helpers import (
    moeda,
    ler_decimal,
    ler_decimal_opcional,
    ler_inteiro,
    ler_inteiro_opcional,
)


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


def test_ler_decimal_opcional_entradas(monkeypatch, capsys):
    """
    Testa a função de leitura decimal opcional com os 4 casos:
      1. Vazio -> Retorna None (mantém valor atual)
      2. "12,50" -> Converte vírgula e retorna Decimal("12.50")
      3. "abc" -> Exibe [!] Entrada inválida e solicita nova entrada
      4. "-1" -> Exibe erro de valor mínimo e solicita nova entrada
    """
    # 1. Entrada vazia (Enter)
    monkeypatch.setattr("builtins.input", lambda _: "")
    assert ler_decimal_opcional("Novo preço: ") is None

    # 2. Entrada com vírgula "12,50"
    monkeypatch.setattr("builtins.input", lambda _: "12,50")
    assert ler_decimal_opcional("Novo preço: ") == Decimal("12.50")

    # 3. Entrada com texto inválido "abc", seguido de entrada válida "12,50"
    entradas_abc = iter(["abc", "12,50"])
    monkeypatch.setattr("builtins.input", lambda _: next(entradas_abc))
    assert ler_decimal_opcional("Novo preço: ") == Decimal("12.50")
    saida_abc = capsys.readouterr().out
    assert "[!] Entrada inválida" in saida_abc

    # 4. Entrada negativa "-1", seguida de entrada válida "12,50"
    entradas_neg = iter(["-1", "12,50"])
    monkeypatch.setattr("builtins.input", lambda _: next(entradas_neg))
    assert ler_decimal_opcional("Novo preço: ", minimo=Decimal("0.01")) == Decimal("12.50")
    saida_neg = capsys.readouterr().out
    assert "[!] O valor mínimo permitido" in saida_neg


def test_ler_inteiro_opcional_entradas(monkeypatch, capsys):
    """
    Testa a função de leitura inteira opcional:
      1. Vazio -> Retorna None (mantém valor atual)
      2. "25" -> Retorna int 25
      3. "xyz" -> Exibe [!] Entrada inválida e solicita nova entrada
      4. "-1" com mínimo 0 -> Exibe erro de valor mínimo e solicita nova entrada
    """
    # 1. Entrada vazia (Enter)
    monkeypatch.setattr("builtins.input", lambda _: "")
    assert ler_inteiro_opcional("Novo estoque: ") is None

    # 2. Entrada válida "25"
    monkeypatch.setattr("builtins.input", lambda _: "25")
    assert ler_inteiro_opcional("Novo estoque: ") == 25

    # 3. Entrada com texto inválido "xyz", seguido de entrada válida "25"
    entradas_xyz = iter(["xyz", "25"])
    monkeypatch.setattr("builtins.input", lambda _: next(entradas_xyz))
    assert ler_inteiro_opcional("Novo estoque: ") == 25
    saida_xyz = capsys.readouterr().out
    assert "[!] Entrada inválida" in saida_xyz

    # 4. Entrada negativa "-1" com mínimo 0, seguida de entrada válida "0"
    entradas_neg = iter(["-1", "0"])
    monkeypatch.setattr("builtins.input", lambda _: next(entradas_neg))
    assert ler_inteiro_opcional("Novo estoque: ", minimo=0) == 0
    saida_neg = capsys.readouterr().out
    assert "mínimo" in saida_neg


def test_compatibilidade_funcoes_existentes(monkeypatch, capsys):
    """Garante que ler_decimal e ler_inteiro sem permitir_vazio mantêm o comportamento original."""
    # ler_decimal com vazio deve rejeitar se permitir_vazio=False (padrão)
    entradas_dec = iter(["", "9.99"])
    monkeypatch.setattr("builtins.input", lambda _: next(entradas_dec))
    assert ler_decimal("Preço: ") == Decimal("9.99")
    assert "[!] Entrada inválida" in capsys.readouterr().out

    # ler_inteiro com vazio deve rejeitar se permitir_vazio=False (padrão)
    entradas_int = iter(["", "10"])
    monkeypatch.setattr("builtins.input", lambda _: next(entradas_int))
    assert ler_inteiro("Estoque: ") == 10
    assert "[!] Entrada inválida" in capsys.readouterr().out


def test_executar_rede_de_seguranca_value_error_e_invalid_operation(monkeypatch, capsys):
    """
    Testa a rede de segurança em MarketplaceCLI.executar:
    Garante que InvalidOperation e ValueError são capturados sem encerrar o sistema.
    """
    from unittest.mock import MagicMock
    from decimal import InvalidOperation
    from ui.cli import MarketplaceCLI

    cli = MarketplaceCLI(
        usuario_service=MagicMock(),
        produto_service=MagicMock(),
        pedido_service=MagicMock(),
        demonstracao_service=MagicMock(),
    )

    chamadas = [0]
    def acao_com_erro():
        chamadas[0] += 1
        if chamadas[0] == 1:
            raise InvalidOperation("operacao decimal invalida simulada")
        raise ValueError("valor invalido simulado")

    monkeypatch.setattr(cli, "menu_usuarios", acao_com_erro)

    # Fluxo: escolhe 1 (InvalidOperation) -> Enter -> escolhe 1 (ValueError) -> Enter -> escolhe 0 (sair)
    entradas = iter(["1", "", "1", "", "0"])
    monkeypatch.setattr("builtins.input", lambda _: next(entradas))

    cli.executar()

    saida = capsys.readouterr().out
    assert "operacao decimal invalida simulada" in saida
    assert "valor invalido simulado" in saida
    assert "Encerrando o Marketplace" in saida


