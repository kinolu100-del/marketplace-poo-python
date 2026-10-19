"""
=====================================================================
Testes de Polimorfismo (test_polimorfismo.py)
=====================================================================
Verifica se as subclasses de Produto e Usuario respondem aos mesmos
métodos de maneira especializada sem checagens condicionais (isinstance).
=====================================================================
"""

from decimal import Decimal
from models.usuario import Cliente, Vendedor
from models.produto import ProdutoFisico, ProdutoDigital


def test_polimorfismo_mensagem_entrega():
    vendedor = Vendedor("Loja Alpha", "alpha@loja.com", "Alpha Tech")
    prod_fisico = ProdutoFisico("Monitor LED", Decimal("900.00"), 5, vendedor, peso_kg=Decimal("4.50"))
    prod_digital = ProdutoDigital(
        "Software CAD",
        Decimal("1500.00"),
        20,
        vendedor,
        tamanho_mb=Decimal("850.0"),
        link_download="https://alpha.com/cad",
    )

    # Chamada uniforme ao método polimórfico sem 'isinstance'
    msg_fisico = prod_fisico.mensagem_entrega()
    msg_digital = prod_digital.mensagem_entrega()

    assert "transportadora" in msg_fisico.lower()
    assert "4.50 kg" in msg_fisico
    assert "prazo estimado" in msg_fisico.lower()

    assert "download" in msg_digital.lower()
    assert "https://alpha.com/cad" in msg_digital


def test_polimorfismo_exibir_detalhes():
    vendedor = Vendedor("Loja Livros", "livros@loja.com", "Mundo dos Livros")
    prod_fisico = ProdutoFisico("Livro Capa Dura", Decimal("80.00"), 10, vendedor, peso_kg=Decimal("0.80"))
    prod_digital = ProdutoDigital(
        "Livro Digital PDF",
        Decimal("30.00"),
        50,
        vendedor,
        tamanho_mb=Decimal("5.2"),
        link_download="https://livros.com/pdf",
    )

    detalhe_fisico = prod_fisico.exibir_detalhes()
    detalhe_digital = prod_digital.exibir_detalhes()

    assert "FÍSICO" in detalhe_fisico
    assert "0.80 kg" in detalhe_fisico

    assert "DIGITAL" in detalhe_digital
    assert "5.2 MB" in detalhe_digital


def test_polimorfismo_usuario_tipo_e_resumo():
    cliente = Cliente("Carlos Eduardo", "carlos@email.com", "Rua das Palmeiras, 50")
    vendedor = Vendedor("Ana Paula", "ana@loja.com", "Ana Decorações")

    assert cliente.tipo() == "Cliente"
    assert vendedor.tipo() == "Vendedor"

    assert "Endereço: Rua das Palmeiras, 50" in cliente.resumo()
    assert "Loja: Ana Decorações" in vendedor.resumo()
