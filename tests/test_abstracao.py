"""
=====================================================================
Testes de Abstração (test_abstracao.py)
=====================================================================
Garante que as classes abstratas 'Usuario' e 'Produto' não podem ser
instanciadas diretamente (lançam TypeError), comprovando o conceito de
Abstração com ABC e @abstractmethod.
=====================================================================
"""

import pytest
from models.usuario import Usuario, Cliente, Vendedor
from models.produto import Produto, ProdutoFisico, ProdutoDigital


def test_impossibilidade_de_instanciar_usuario_diretamente():
    # Usuario possui o método abstrato 'tipo()', logo o Python impede instanciação
    with pytest.raises(TypeError) as exc_info:
        Usuario("Usuario Base", "base@email.com")

    assert "Can't instantiate abstract class Usuario" in str(exc_info.value)


def test_impossibilidade_de_instanciar_produto_diretamente():
    vendedor = Vendedor("Loja Teste", "v@loja.com", "Loja")
    # Produto possui calcular_frete, exibir_detalhes e mensagem_entrega abstratos
    with pytest.raises(TypeError) as exc_info:
        Produto("Produto Base", 50.0, 10, vendedor)

    assert "Can't instantiate abstract class Produto" in str(exc_info.value)


def test_subclasses_concretas_instanciam_normalmente():
    # As classes filhas que implementam todos os métodos abstratos funcionam perfeitamente
    cliente = Cliente("Comprador", "comprador@email.com", "Rua X, 10")
    vendedor = Vendedor("Lojista", "lojista@email.com", "Loja Y")
    fisico = ProdutoFisico("Mouse", 50.0, 5, vendedor, 0.2)
    digital = ProdutoDigital("Ebook", 25.0, 10, vendedor, 2.0, "https://link.com")

    assert isinstance(cliente, Usuario)
    assert isinstance(vendedor, Usuario)
    assert isinstance(fisico, Produto)
    assert isinstance(digital, Produto)
