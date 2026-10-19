"""
=====================================================================
Módulo de Utilitários de Interface e Terminal (ui/helpers.py)
=====================================================================
Responsável por formatações visuais, leitura defensiva de entradas
do usuário e tratamento de erros de digitação no console.
=====================================================================
"""

from __future__ import annotations
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
import re
from typing import Optional, Union


def moeda(valor: Union[Decimal, float, int]) -> str:
    """
    Formata um valor numérico ou Decimal para o padrão monetário brasileiro:
    Exemplo: R$ 1.250,50
    """
    if not isinstance(valor, Decimal):
        dec = Decimal(str(valor))
    else:
        dec = valor
    dec = dec.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    # Formatação com separadores
    partes = f"{dec:,.2f}".split(".")
    inteiro = partes[0].replace(",", ".")
    centavos = partes[1]
    return f"R$ {inteiro},{centavos}"


def linha(char: str = "-", tamanho: int = 70) -> None:
    """Imprime uma linha separadora formatada no terminal."""
    print(char * tamanho)


def titulo(texto: str) -> None:
    """Imprime um cabeçalho de destaque centralizado no console."""
    print()
    linha("=")
    print(texto.center(70))
    linha("=")


def ler_texto(mensagem: str) -> str:
    """Lê um texto garantindo que não seja composto apenas por espaços vazios."""
    while True:
        try:
            valor = input(mensagem).strip()
        except (KeyboardInterrupt, EOFError):
            print("\nOperação cancelada.")
            raise
        if valor:
            return valor
        print("  [!] Atenção: O campo não pode ficar vazio. Digite novamente.")


def ler_inteiro(
    mensagem: str,
    minimo: Optional[int] = None,
    maximo: Optional[int] = None,
) -> int:
    """
    Lê um número inteiro com validação defensiva contra erros de digitação
    e restrição opcional de valores mínimos e máximos.
    """
    while True:
        try:
            bruto = input(mensagem).strip()
        except (KeyboardInterrupt, EOFError):
            print("\nOperação cancelada.")
            raise
        try:
            numero = int(bruto)
        except ValueError:
            print("  [!] Entrada inválida: Digite um número inteiro.")
            continue
        if minimo is not None and numero < minimo:
            print(f"  [!] Valor abaixo do permitido. O valor mínimo é {minimo}.")
            continue
        if maximo is not None and numero > maximo:
            print(f"  [!] Valor acima do permitido. O valor máximo é {maximo}.")
            continue
        return numero


def ler_decimal(
    mensagem: str,
    minimo: Optional[Decimal] = None,
) -> Decimal:
    """
    Lê um número monetário/fracionário, convertendo vírgula para ponto e retornando Decimal.
    """
    while True:
        try:
            bruto = input(mensagem).strip().replace(",", ".")
        except (KeyboardInterrupt, EOFError):
            print("\nOperação cancelada.")
            raise
        try:
            dec = Decimal(bruto).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        except (InvalidOperation, ValueError):
            print("  [!] Entrada inválida: Digite um número decimal válido (ex: 49.90 ou 49,90).")
            continue
        if minimo is not None and dec < minimo:
            print(f"  [!] O valor mínimo permitido é {minimo}.")
            continue
        return dec


def ler_email(mensagem: str) -> str:
    """Lê e valida o formato básico de um endereço de e-mail via regex."""
    padrao = re.compile(r"^[\w.+-]+@[\w-]+\.[\w.-]+$")
    while True:
        try:
            email = input(mensagem).strip().lower()
        except (KeyboardInterrupt, EOFError):
            print("\nOperação cancelada.")
            raise
        if padrao.match(email):
            return email
        print("  [!] E-mail inválido. Formato esperado: usuario@dominio.com")


def confirmar(mensagem: str) -> bool:
    """Solicita confirmação binária ao usuário (sim/não)."""
    while True:
        try:
            resposta = input(f"{mensagem} (s/n): ").strip().lower()
        except (KeyboardInterrupt, EOFError):
            print("\nOperação cancelada.")
            raise
        if resposta in ("s", "sim"):
            return True
        if resposta in ("n", "nao", "não"):
            return False
        print("  [!] Responda apenas com 's' para sim ou 'n' para não.")
