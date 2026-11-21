"""
=====================================================================
Validadores Puros de Formulário GUI (ui/gui/validators.py)
=====================================================================
Funções puras de validação de dados digitados em formulários da GUI,
desacopladas de Tkinter para permitir testes unitários headless com pytest.
=====================================================================
"""

from __future__ import annotations
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import re
from typing import Tuple, Optional, Dict, Any

PADRAO_EMAIL = re.compile(r"^[\w.+-]+@[\w-]+\.[\w.-]+$")


def validar_dados_usuario(
    tipo: str,
    nome: str,
    email: str,
    endereco: str = "",
    nome_loja: str = "",
) -> Tuple[bool, Optional[str]]:
    """
    Valida os campos de entrada para cadastro/edição de usuário:
      - Tipo deve ser 'Cliente' ou 'Vendedor'
      - Nome não pode ser vazio
      - E-mail deve seguir formato válido
      - Cliente exige endereço não vazio
      - Vendedor exige nome da loja não vazio
    Retorno: (valido: bool, mensagem_erro: Optional[str])
    """
    if tipo not in ("Cliente", "Vendedor"):
        return False, "Tipo de usuário inválido. Selecione 'Cliente' ou 'Vendedor'."

    nome_limpo = (nome or "").strip()
    if not nome_limpo:
        return False, "O campo 'Nome' é obrigatório e não pode ficar em branco."

    email_limpo = (email or "").strip().lower()
    if not email_limpo or not PADRAO_EMAIL.match(email_limpo):
        return False, "E-mail inválido. Utilize o formato 'usuario@dominio.com'."

    if tipo == "Cliente":
        endereco_limpo = (endereco or "").strip()
        if not endereco_limpo:
            return False, "O campo 'Endereço' é obrigatório para clientes."
    elif tipo == "Vendedor":
        loja_limpo = (nome_loja or "").strip()
        if not loja_limpo:
            return False, "O campo 'Nome da Loja' é obrigatório para vendedores."

    return True, None


def validar_dados_produto(
    tipo: str,
    nome: str,
    preco_str: str,
    estoque_str: str,
    vendedor_id: Optional[int],
    peso_str: str = "",
    tamanho_str: str = "",
    link_download: str = "",
) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
    """
    Valida e converte dados para criação/edição de produtos.
    Aceita vírgula ou ponto no preço e pesos.
    Retorno: (valido: bool, mensagem_erro: Optional[str], dados_convertidos: Optional[dict])
    """
    if tipo not in ("Físico", "Digital"):
        return False, "Tipo de produto inválido. Selecione 'Físico' ou 'Digital'.", None

    nome_limpo = (nome or "").strip()
    if not nome_limpo:
        return False, "O nome do produto é obrigatório.", None

    # Validação do Preço (aceita 49.90, 49,90 e 1.250,50)
    preco_tratado = (preco_str or "").strip()
    if "." in preco_tratado and "," in preco_tratado:
        preco_tratado = preco_tratado.replace(".", "").replace(",", ".")
    else:
        preco_tratado = preco_tratado.replace(",", ".")
    try:
        preco_dec = Decimal(preco_tratado).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        if preco_dec <= Decimal("0.00"):
            return False, "O preço do produto deve ser maior que zero (R$ 0,00).", None
    except (InvalidOperation, ValueError):
        return False, "Preço inválido. Digite um valor numérico válido (ex: 49,90 ou 49.90).", None

    # Validação do Estoque
    estoque_tratado = (estoque_str or "").strip()
    try:
        estoque_int = int(estoque_tratado)
        if estoque_int < 0:
            return False, "O estoque do produto não pode ser negativo.", None
    except ValueError:
        return False, "Estoque inválido. Digite um número inteiro maior ou igual a zero.", None

    if vendedor_id is None or vendedor_id <= 0:
        return False, "Selecione um vendedor responsável pelo produto.", None

    dados_convertidos: Dict[str, Any] = {
        "tipo": tipo,
        "nome": nome_limpo,
        "preco": preco_dec,
        "estoque": estoque_int,
        "vendedor_id": vendedor_id,
    }

    if tipo == "Físico":
        peso_tratado = (peso_str or "").strip()
        if "." in peso_tratado and "," in peso_tratado:
            peso_tratado = peso_tratado.replace(".", "").replace(",", ".")
        else:
            peso_tratado = peso_tratado.replace(",", ".")
        try:
            peso_dec = Decimal(peso_tratado).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            if peso_dec <= Decimal("0.00"):
                return False, "O peso do produto físico deve ser estritamente maior que zero.", None
            dados_convertidos["peso_kg"] = peso_dec
        except (InvalidOperation, ValueError):
            return False, "Peso inválido. Digite um número decimal em kg (ex: 0,5 ou 1.2).", None
    else:
        tam_tratado = (tamanho_str or "").strip()
        if "." in tam_tratado and "," in tam_tratado:
            tam_tratado = tam_tratado.replace(".", "").replace(",", ".")
        else:
            tam_tratado = tam_tratado.replace(",", ".")
        try:
            tam_dec = Decimal(tam_tratado).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
            if tam_dec <= Decimal("0.0"):
                return False, "O tamanho do arquivo digital deve ser maior que zero MB.", None
            dados_convertidos["tamanho_mb"] = tam_dec
        except (InvalidOperation, ValueError):
            return False, "Tamanho em MB inválido. Digite um número (ex: 15.5).", None

        link_limpo = (link_download or "").strip()
        if not link_limpo:
            return False, "O link para download é obrigatório para produtos digitais.", None
        dados_convertidos["link_download"] = link_limpo

    return True, None, dados_convertidos


def validar_quantidade_carrinho(
    quantidade_str: str,
    estoque_disponivel: int,
) -> Tuple[bool, Optional[str], Optional[int]]:
    """
    Valida a quantidade digitada para inclusão ou alteração no carrinho.
    Retorno: (valido: bool, mensagem_erro: Optional[str], quantidade_int: Optional[int])
    """
    qtd_limpa = (quantidade_str or "").strip()
    try:
        qtd = int(qtd_limpa)
    except ValueError:
        return False, "Digite um número inteiro válido para a quantidade.", None

    if qtd <= 0:
        return False, "A quantidade deve ser de no mínimo 1 unidade.", None

    if qtd > estoque_disponivel:
        return (
            False,
            f"Quantidade solicitada ({qtd}) excede o estoque disponível ({estoque_disponivel}).",
            None,
        )

    return True, None, qtd
