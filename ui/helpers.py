"""
=====================================================================
Módulo de Utilitários de Interface e Terminal (ui/helpers.py)
=====================================================================
Responsável por formatações visuais, leitura defensiva de entradas
do usuário e tratamento de erros de digitação no console.
=====================================================================
"""

from __future__ import annotations
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
import re
from typing import Optional, Union, List, Any


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
    permitir_vazio: bool = False,
) -> Optional[int]:
    """
    Lê um número inteiro com validação defensiva contra erros de digitação
    e restrição opcional de valores mínimos e máximos.
    Se permitir_vazio for True e a entrada estiver em branco, retorna None.
    """
    while True:
        try:
            bruto = input(mensagem).strip()
        except (KeyboardInterrupt, EOFError):
            print("\nOperação cancelada.")
            raise
        if permitir_vazio and not bruto:
            return None
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


def ler_inteiro_opcional(
    mensagem: str,
    minimo: Optional[int] = None,
    maximo: Optional[int] = None,
) -> Optional[int]:
    """
    Variante de ler_inteiro que aceita entrada vazia (Enter), retornando None.
    """
    return ler_inteiro(mensagem, minimo=minimo, maximo=maximo, permitir_vazio=True)


def ler_decimal(
    mensagem: str,
    minimo: Optional[Union[Decimal, float, int]] = None,
    permitir_vazio: bool = False,
) -> Optional[Decimal]:
    """
    Lê um número monetário/fracionário, convertendo vírgula para ponto e retornando Decimal.
    Se permitir_vazio for True e a entrada estiver em branco, retorna None.
    """
    while True:
        try:
            bruto = input(mensagem).strip()
        except (KeyboardInterrupt, EOFError):
            print("\nOperação cancelada.")
            raise
        if permitir_vazio and not bruto:
            return None
        bruto = bruto.replace(",", ".")
        try:
            dec = Decimal(bruto).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        except (InvalidOperation, ValueError):
            print("  [!] Entrada inválida: Digite um número decimal válido (ex: 49.90 ou 49,90).")
            continue
        if minimo is not None:
            minimo_dec = minimo if isinstance(minimo, Decimal) else Decimal(str(minimo))
            if dec < minimo_dec:
                print(f"  [!] O valor mínimo permitido é {minimo_dec}.")
                continue
        return dec


def ler_decimal_opcional(
    mensagem: str,
    minimo: Optional[Union[Decimal, float, int]] = None,
) -> Optional[Decimal]:
    """
    Variante de ler_decimal que aceita entrada vazia (Enter), retornando None.
    """
    return ler_decimal(mensagem, minimo=minimo, permitir_vazio=True)


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


@dataclass
class DetalheItemResumo:
    """Estrutura imutável de detalhamento por item no resumo prévio de compra."""
    produto_id: int
    nome: str
    tipo: str
    preco_unitario: Decimal
    quantidade: int
    subtotal: Decimal
    frete: Decimal


@dataclass
class ResumoFreteCarrinho:
    """Consolidação dos cálculos de frete e totais estimados de um carrinho."""
    subtotal_produtos: Decimal
    tem_produto_fisico: bool
    frete_variavel: Decimal
    taxa_fixa_pedido: Decimal
    frete_total: Decimal
    total_estimado: Decimal
    itens: list[DetalheItemResumo]


def calcular_resumo_frete(carrinho: Any) -> ResumoFreteCarrinho:
    """
    Calcula o resumo consolidado de valores e frete para um carrinho de compras:
      - Subtotal dos produtos
      - Frete variável proporcional ao peso (polimórfico)
      - Taxa fixa única de R$ 10,00 se contiver ao menos um produto físico
      - Frete total e valor geral estimado
      - Detalhamento item a item
    """
    itens_detalhes: list[DetalheItemResumo] = []
    tem_fisico = False
    frete_variavel = Decimal("0.00")

    for item in carrinho.itens:
        prod = item.produto
        tipo_str = prod.tipo()
        if tipo_str == "Físico":
            tem_fisico = True
        frete_item = prod.calcular_frete(item.quantidade)
        frete_variavel += frete_item
        itens_detalhes.append(
            DetalheItemResumo(
                produto_id=prod.id,
                nome=prod.nome,
                tipo=tipo_str,
                preco_unitario=prod.preco,
                quantidade=item.quantidade,
                subtotal=item.subtotal,
                frete=frete_item,
            )
        )

    taxa_pedido = Decimal("10.00") if tem_fisico else Decimal("0.00")
    frete_total = (frete_variavel + taxa_pedido).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    subtotal = carrinho.subtotal
    total_estimado = (subtotal + frete_total).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    return ResumoFreteCarrinho(
        subtotal_produtos=subtotal,
        tem_produto_fisico=tem_fisico,
        frete_variavel=frete_variavel.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
        taxa_fixa_pedido=taxa_pedido.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
        frete_total=frete_total,
        total_estimado=total_estimado,
        itens=itens_detalhes,
    )
