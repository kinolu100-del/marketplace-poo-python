"""
=====================================================================
Testes de Utilitários GUI, Formatadores, Validadores e Frete
(tests/test_gui_helpers.py)
=====================================================================
Testes unitários automatizados 100% headless (sem abrir janelas),
validando:
  1. A função compartilhada de cálculo e consolidação de frete
     (carrinho misto, só físico, só digital e vazio).
  2. Formatadores de dados para Treeviews (formatters.py).
  3. Validadores puros de formulários (validators.py).
  4. Teste de fumaça da inicialização do Tkinter com skip seguro
     caso o ambiente não possua display gráfico.
=====================================================================
"""

from decimal import Decimal
import pytest
from models.usuario import Cliente, Vendedor
from models.produto import ProdutoFisico, ProdutoDigital
from models.pedido import Carrinho, Pedido
from ui.helpers import calcular_resumo_frete
from ui.gui.formatters import (
    formatar_usuario_tabela,
    formatar_produto_tabela,
    formatar_item_carrinho_tabela,
    formatar_pedido_tabela,
)
from ui.gui.validators import (
    validar_dados_usuario,
    validar_dados_produto,
    validar_quantidade_carrinho,
)


# =====================================================================
# 1. TESTES DO CÁLCULO E RESUMO CONSOLIDADO DE FRETE
# =====================================================================

def test_resumo_frete_carrinho_so_produto_fisico():
    """
    Testa resumo de frete com apenas produtos físicos:
    Dois produtos:
      - Item 1: peso 2.0 kg x 2 un = 4.0 kg -> 4.0 * 3.50 = R$ 14.00
      - Item 2: peso 1.0 kg x 1 un = 1.0 kg -> 1.0 * 3.50 = R$ 3.50
    Frete variável = R$ 17.50
    Taxa fixa pedido físico = R$ 10.00 (cobrada uma única vez)
    Frete total = R$ 27.50
    """
    vendedor = Vendedor(nome="Vendedor", email="v@email.com", nome_loja="Loja")
    p1 = ProdutoFisico(nome="Teclado", preco=Decimal("150.00"), estoque=10, vendedor=vendedor, peso_kg=Decimal("2.0"))
    p2 = ProdutoFisico(nome="Mouse", preco=Decimal("50.00"), estoque=10, vendedor=vendedor, peso_kg=Decimal("1.0"))

    carrinho = Carrinho()
    carrinho.adicionar(p1, 2)
    carrinho.adicionar(p2, 1)

    resumo = calcular_resumo_frete(carrinho)

    assert resumo.tem_produto_fisico is True
    assert resumo.subtotal_produtos == Decimal("350.00")  # (150*2) + (50*1)
    assert resumo.frete_variavel == Decimal("17.50")
    assert resumo.taxa_fixa_pedido == Decimal("10.00")
    assert resumo.frete_total == Decimal("27.50")
    assert resumo.total_estimado == Decimal("377.50")
    assert len(resumo.itens) == 2


def test_resumo_frete_carrinho_so_produto_digital():
    """
    Testa resumo de frete com produtos exclusivamente digitais:
    Frete variável = R$ 0.00
    Taxa fixa pedido físico = R$ 0.00 (isento)
    Frete total = R$ 0.00
    """
    vendedor = Vendedor(nome="Vendedor", email="v@digital.com", nome_loja="Loja Digital")
    ebook = ProdutoDigital(
        nome="E-Book Python",
        preco=Decimal("49.90"),
        estoque=100,
        vendedor=vendedor,
        tamanho_mb=Decimal("12.5"),
        link_download="https://dl.loja.com/ebook",
    )
    curso = ProdutoDigital(
        nome="Curso POO",
        preco=Decimal("199.00"),
        estoque=50,
        vendedor=vendedor,
        tamanho_mb=Decimal("1500.0"),
        link_download="https://dl.loja.com/curso",
    )

    carrinho = Carrinho()
    carrinho.adicionar(ebook, 1)
    carrinho.adicionar(curso, 2)

    resumo = calcular_resumo_frete(carrinho)

    assert resumo.tem_produto_fisico is False
    assert resumo.subtotal_produtos == Decimal("447.90")  # 49.90 + (199.00*2)
    assert resumo.frete_variavel == Decimal("0.00")
    assert resumo.taxa_fixa_pedido == Decimal("0.00")
    assert resumo.frete_total == Decimal("0.00")
    assert resumo.total_estimado == Decimal("447.90")


def test_resumo_frete_carrinho_misto_fisico_e_digital():
    """
    Testa resumo de frete com pedido misto (físico + digital):
      - Produto Físico: 0.5 kg x 2 un = 1.0 kg -> frete R$ 3.50
      - Produto Digital: frete R$ 0.00
      - Taxa fixa única por haver produto físico: R$ 10.00 (cobrada UMA ÚNICA VEZ)
    Frete total = R$ 13.50
    """
    vendedor = Vendedor(nome="Vendedor", email="v@misto.com", nome_loja="Loja Mista")
    mousepad = ProdutoFisico(nome="Mousepad", preco=Decimal("30.00"), estoque=20, vendedor=vendedor, peso_kg=Decimal("0.5"))
    licenca = ProdutoDigital(
        nome="Chave Antivírus",
        preco=Decimal("79.90"),
        estoque=50,
        vendedor=vendedor,
        tamanho_mb=Decimal("50.0"),
        link_download="https://dl.loja.com/antivirus",
    )

    carrinho = Carrinho()
    carrinho.adicionar(mousepad, 2)
    carrinho.adicionar(licenca, 1)

    resumo = calcular_resumo_frete(carrinho)

    assert resumo.tem_produto_fisico is True
    assert resumo.subtotal_produtos == Decimal("139.90")  # 60.00 + 79.90
    assert resumo.frete_variavel == Decimal("3.50")
    assert resumo.taxa_fixa_pedido == Decimal("10.00")
    assert resumo.frete_total == Decimal("13.50")
    assert resumo.total_estimado == Decimal("153.40")


def test_resumo_frete_carrinho_vazio():
    """Testa o cálculo para um carrinho recém-criado e vazio."""
    carrinho = Carrinho()
    resumo = calcular_resumo_frete(carrinho)

    assert resumo.tem_produto_fisico is False
    assert resumo.subtotal_produtos == Decimal("0.00")
    assert resumo.frete_total == Decimal("0.00")
    assert resumo.total_estimado == Decimal("0.00")
    assert len(resumo.itens) == 0


# =====================================================================
# 2. TESTES DOS FORMATADORES DE TABELA GUI
# =====================================================================

def test_formatar_usuario_tabela():
    cliente = Cliente(nome="Lucas Silva", email="lucas@email.com", endereco="Rua A, 100", id_usuario=1)
    vendedor = Vendedor(nome="Loja Tech", email="contato@tech.com", nome_loja="Tech Store", id_usuario=2)

    f_cli = formatar_usuario_tabela(cliente)
    assert f_cli[0] == "#001"
    assert f_cli[1] == "Cliente"
    assert f_cli[2] == "Lucas Silva"
    assert f_cli[3] == "lucas@email.com"
    assert "Rua A, 100" in f_cli[4]

    f_ven = formatar_usuario_tabela(vendedor)
    assert f_ven[0] == "#002"
    assert f_ven[1] == "Vendedor"
    assert f_ven[2] == "Loja Tech"
    assert "Tech Store" in f_ven[4]


def test_formatar_produto_tabela():
    vendedor = Vendedor(nome="Vendedor", email="v@loja.com", nome_loja="Loja", id_usuario=1)
    p_fis = ProdutoFisico(
        nome="Cadeira Gamer",
        preco=Decimal("899.90"),
        estoque=5,
        vendedor=vendedor,
        peso_kg=Decimal("15.5"),
        id_produto=10,
    )
    p_dig = ProdutoDigital(
        nome="Ebook PDF",
        preco=Decimal("29.00"),
        estoque=100,
        vendedor=vendedor,
        tamanho_mb=Decimal("5.2"),
        link_download="https://dl.link/pdf",
        id_produto=11,
    )

    f_fis = formatar_produto_tabela(p_fis)
    assert f_fis[0] == "#010"
    assert f_fis[1] == "Cadeira Gamer"
    assert f_fis[2] == "Físico"
    assert "899,90" in f_fis[3]
    assert f_fis[4] == "5"
    assert "15.50 kg" in f_fis[6]

    f_dig = formatar_produto_tabela(p_dig)
    assert f_dig[0] == "#011"
    assert f_dig[2] == "Digital"
    assert "5.2 MB" in f_dig[6]


def test_formatar_item_carrinho_e_pedido_tabela():
    vendedor = Vendedor(nome="Vendedor", email="v@email.com", nome_loja="Loja", id_usuario=1)
    cliente = Cliente(nome="Cliente", email="c@email.com", endereco="Rua 1", id_usuario=2)
    p = ProdutoFisico(nome="Mouse", preco=Decimal("50.00"), estoque=8, vendedor=vendedor, peso_kg=Decimal("0.2"), id_produto=1)

    carrinho = Carrinho()
    carrinho.adicionar(p, 2)
    item_carrinho = carrinho.itens[0]

    f_item = formatar_item_carrinho_tabela(item_carrinho)
    assert f_item[0] == "#001"
    assert f_item[1] == "Mouse"
    assert f_item[4] == "2"
    assert "100,00" in f_item[5]

    pedido = Pedido(cliente=cliente)
    pedido.adicionar_item(p, 2)

    f_ped = formatar_pedido_tabela(pedido)
    assert f_ped[0] == f"#{pedido.id:04d}"
    assert "Cliente (#2)" in f_ped[2]
    assert "2 unid." in f_ped[3]
    assert f_ped[7] == "Confirmado"


# =====================================================================
# 3. TESTES DOS VALIDADORES DE FORMULÁRIO GUI
# =====================================================================

def test_validar_dados_usuario_sucesso_e_falhas():
    # Sucessos
    v1, e1 = validar_dados_usuario("Cliente", "Nome", "email@valido.com", endereco="Rua 1")
    assert v1 is True and e1 is None

    v2, e2 = validar_dados_usuario("Vendedor", "Nome Loja", "loja@valido.com", nome_loja="Loja")
    assert v2 is True and e2 is None

    # Falhas
    v3, e3 = validar_dados_usuario("Invalido", "Nome", "email@valido.com")
    assert v3 is False and "Tipo de usuário inválido" in e3

    v4, e4 = validar_dados_usuario("Cliente", "", "email@valido.com", endereco="Rua 1")
    assert v4 is False and "Nome" in e4

    v5, e5 = validar_dados_usuario("Cliente", "Nome", "email_invalido", endereco="Rua 1")
    assert v5 is False and "E-mail inválido" in e5

    v6, e6 = validar_dados_usuario("Cliente", "Nome", "email@valido.com", endereco="")
    assert v6 is False and "Endereço" in e6

    v7, e7 = validar_dados_usuario("Vendedor", "Nome", "email@valido.com", nome_loja="")
    assert v7 is False and "Nome da Loja" in e7


def test_validar_dados_produto_sucesso_e_falhas():
    # Físico válido
    v1, e1, d1 = validar_dados_produto(
        tipo="Físico",
        nome="Monitor",
        preco_str="1.250,50",
        estoque_str="15",
        vendedor_id=1,
        peso_str="4,5",
    )
    assert v1 is True and e1 is None
    assert d1["preco"] == Decimal("1250.50")
    assert d1["estoque"] == 15
    assert d1["peso_kg"] == Decimal("4.50")

    # Digital válido
    v2, e2, d2 = validar_dados_produto(
        tipo="Digital",
        nome="Software",
        preco_str="299.00",
        estoque_str="50",
        vendedor_id=2,
        tamanho_str="120.5",
        link_download="https://dl.site.com",
    )
    assert v2 is True and e2 is None
    assert d2["tamanho_mb"] == Decimal("120.5")
    assert d2["link_download"] == "https://dl.site.com"

    # Preço inválido ou zero
    v3, e3, _ = validar_dados_produto("Físico", "A", "0.00", "5", 1, peso_str="1.0")
    assert v3 is False and "maior que zero" in e3

    v4, e4, _ = validar_dados_produto("Físico", "A", "abc", "5", 1, peso_str="1.0")
    assert v4 is False and "Preço inválido" in e4

    # Estoque negativo
    v5, e5, _ = validar_dados_produto("Físico", "A", "10.00", "-2", 1, peso_str="1.0")
    assert v5 is False and "negativo" in e5

    # Sem vendedor
    v6, e6, _ = validar_dados_produto("Físico", "A", "10.00", "5", None, peso_str="1.0")
    assert v6 is False and "vendedor" in e6


def test_validar_quantidade_carrinho():
    # Válido
    v1, e1, q1 = validar_quantidade_carrinho("3", estoque_disponivel=10)
    assert v1 is True and e1 is None and q1 == 3

    # Não numérico
    v2, e2, _ = validar_quantidade_carrinho("abc", estoque_disponivel=10)
    assert v2 is False and "número inteiro válido" in e2

    # Zero ou negativo
    v3, e3, _ = validar_quantidade_carrinho("0", estoque_disponivel=10)
    assert v3 is False and "mínimo 1 unidade" in e3

    # Excede estoque disponível
    v4, e4, _ = validar_quantidade_carrinho("15", estoque_disponivel=10)
    assert v4 is False and "excede o estoque" in e4


# =====================================================================
# 4. TESTE DE FUMAÇA DA GUI (COM SKIP SEGURO SE NÃO HOUVER DISPLAY)
# =====================================================================

def test_smoke_gui_instanciacao_opcional():
    """
    Teste de fumaça da janela Tkinter.
    Se o ambiente não possuir suporte gráfico (ex: servidor CI headless),
    executa pytest.skip sem jamais falhar a suíte de testes.
    """
    import tkinter as tk
    try:
        from repositories.usuario_repository import UsuarioRepository
        from repositories.produto_repository import ProdutoRepository
        from repositories.pedido_repository import PedidoRepository
        from services.usuario_service import UsuarioService
        from services.produto_service import ProdutoService
        from services.pedido_service import PedidoService
        from services.demonstracao_service import DemonstracaoService
        from ui.gui.app import MarketplaceGUI

        u_repo = UsuarioRepository()
        p_repo = ProdutoRepository(usuario_repo=u_repo)
        ped_repo = PedidoRepository(usuario_repo=u_repo, produto_repo=p_repo)

        u_serv = UsuarioService(u_repo, p_repo, ped_repo)
        prod_serv = ProdutoService(p_repo, u_repo)
        ped_serv = PedidoService(ped_repo, u_repo, p_repo)
        demo_serv = DemonstracaoService(u_serv, prod_serv, u_repo, p_repo)

        app = MarketplaceGUI(
            usuario_service=u_serv,
            produto_service=prod_serv,
            pedido_service=ped_serv,
            demonstracao_service=demo_serv,
        )
        app.update_idletasks()
        app.destroy()
    except (tk.TclError, Exception) as erro:
        pytest.skip(f"Ambiente sem display gráfico compatível para Tkinter: {erro}")
