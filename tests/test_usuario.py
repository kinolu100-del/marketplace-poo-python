"""
=====================================================================
Testes de Usuários (test_usuario.py)
=====================================================================
Valida construtores, encapsulamento (@property e validações),
composição do carrinho no Cliente, catálogo no Vendedor e unicidade de e-mail.
=====================================================================
"""

import pytest
from models.usuario import Cliente, Vendedor
from exceptions import ValorInvalidoError


def test_cliente_criacao_e_composicao_carrinho():
    cliente = Cliente("Fernanda Lima", "fernanda@email.com", "Rua das Acacias, 12")
    assert cliente.nome == "Fernanda Lima"
    assert cliente.email == "fernanda@email.com"
    assert cliente.endereco == "Rua das Acacias, 12"
    assert cliente.tipo() == "Cliente"

    # [COMPOSIÇÃO]: Carrinho é instanciado automaticamente e pertence ao cliente
    assert cliente.carrinho is not None
    assert cliente.carrinho.esta_vazio()
    assert len(cliente.pedidos) == 0


def test_vendedor_criacao_e_associacao_produtos():
    vendedor = Vendedor("Roberto Silva", "roberto@loja.com", "Silva Variedades")
    assert vendedor.nome == "Roberto Silva"
    assert vendedor.email == "roberto@loja.com"
    assert vendedor.nome_loja == "Silva Variedades"
    assert vendedor.tipo() == "Vendedor"
    assert len(vendedor.produtos) == 0


def test_validacao_nome_obrigatorio():
    with pytest.raises(ValorInvalidoError):
        Cliente("", "email@teste.com", "Endereco")

    with pytest.raises(ValorInvalidoError):
        Vendedor("   ", "email@teste.com", "Loja")


def test_validacao_email_obrigatorio_e_formato():
    with pytest.raises(ValorInvalidoError):
        Cliente("Nome", "", "Endereco")

    with pytest.raises(ValorInvalidoError):
        Cliente("Nome", "emailsemarroba.com", "Endereco")


def test_validacao_endereco_e_loja_obrigatorios():
    with pytest.raises(ValorInvalidoError):
        Cliente("Nome", "email@teste.com", "")

    with pytest.raises(ValorInvalidoError):
        Vendedor("Nome", "email@teste.com", "   ")
