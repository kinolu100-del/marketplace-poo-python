"""
=====================================================================
Testes de Conformidade das Chamadas de Serviço da Interface Gráfica
(tests/test_gui_service_calls.py)
=====================================================================
Garante que todas as chamadas aos serviços (UsuarioService,
ProdutoService, PedidoService e DemonstracaoService) realizadas pelas
views da GUI (ui/gui/) utilizem assinaturas, nomes de parâmetros e
tipos perfeitamente compatíveis com as implementações reais em services/,
sem necessidade de abrir janelas Tkinter.
=====================================================================
"""

from decimal import Decimal
import pytest

from repositories.usuario_repository import UsuarioRepository
from repositories.produto_repository import ProdutoRepository
from repositories.pedido_repository import PedidoRepository
from services.usuario_service import UsuarioService
from services.produto_service import ProdutoService
from services.pedido_service import PedidoService
from services.demonstracao_service import DemonstracaoService
from models.pedido import StatusPedido
from exceptions import EntidadeNaoEncontradaError


@pytest.fixture
def servicos_gui():
    """Instancia repositórios e serviços conectados ao banco isolado da fixture conftest."""
    u_repo = UsuarioRepository()
    prod_repo = ProdutoRepository()
    ped_repo = PedidoRepository()

    u_serv = UsuarioService(u_repo, prod_repo, ped_repo)
    prod_serv = ProdutoService(prod_repo, u_repo)
    ped_serv = PedidoService(ped_repo, u_repo, prod_repo)
    demo_serv = DemonstracaoService(u_serv, prod_serv, u_repo, prod_repo)

    return {
        "usuario_service": u_serv,
        "produto_service": prod_serv,
        "pedido_service": ped_serv,
        "demonstracao_service": demo_serv,
    }


def test_gui_calls_usuario_service(servicos_gui):
    """Testa todas as chamadas de UsuarioService utilizadas em ui/gui/usuarios_view.py."""
    usuario_service = servicos_gui["usuario_service"]

    # 1. Cadastrar Cliente (como em _salvar na modal)
    cliente = usuario_service.cadastrar_cliente(
        nome="Cliente Teste GUI",
        email="cliente.gui@email.com",
        endereco="Rua das Flores, 123",
    )
    assert cliente.id is not None
    assert cliente.nome == "Cliente Teste GUI"

    # 2. Cadastrar Vendedor (como em _salvar na modal)
    vendedor = usuario_service.cadastrar_vendedor(
        nome="Vendedor Teste GUI",
        email="vendedor.gui@email.com",
        nome_loja="Loja Virtual GUI",
    )
    assert vendedor.id is not None
    assert vendedor.nome_loja == "Loja Virtual GUI"

    # 3. Listagens da toolbar e comboboxes
    todos = usuario_service.listar_usuarios()
    assert len(todos) >= 2

    clientes = usuario_service.listar_clientes()
    assert any(c.id == cliente.id for c in clientes)

    vendedores = usuario_service.listar_vendedores()
    assert any(v.id == vendedor.id for v in vendedores)

    # 4. Buscar por ID (ao abrir edição ou remover)
    u_buscado = usuario_service.buscar_por_id(cliente.id)
    assert u_buscado is not None
    assert u_buscado.email == "cliente.gui@email.com"

    # 5. Editar Usuário (Cliente) - exatamente como corrigido no UsuarioModal._salvar
    u_editado_cliente = usuario_service.editar_usuario(
        id_usuario=cliente.id,
        nome="Cliente Teste Editado",
        email="cliente.editado@email.com",
        endereco="Av. Nova, 456",
        nome_loja=None,
    )
    assert u_editado_cliente.nome == "Cliente Teste Editado"
    assert u_editado_cliente.endereco == "Av. Nova, 456"

    # 6. Editar Usuário (Vendedor) - exatamente como corrigido no UsuarioModal._salvar
    u_editado_vendedor = usuario_service.editar_usuario(
        id_usuario=vendedor.id,
        nome="Vendedor Teste Editado",
        email="vendedor.editado@email.com",
        endereco=None,
        nome_loja="Loja Mega Editada",
    )
    assert u_editado_vendedor.nome == "Vendedor Teste Editado"
    assert u_editado_vendedor.nome_loja == "Loja Mega Editada"

    # 7. Remover Usuário (como em _remover_selecionado)
    usuario_service.remover_usuario(cliente.id)
    with pytest.raises(EntidadeNaoEncontradaError):
        usuario_service.buscar_por_id(cliente.id)


def test_gui_calls_produto_service(servicos_gui):
    """Testa todas as chamadas de ProdutoService utilizadas em ui/gui/produtos_view.py."""
    usuario_service = servicos_gui["usuario_service"]
    produto_service = servicos_gui["produto_service"]

    vendedor = usuario_service.cadastrar_vendedor(
        nome="Vendedor Tech",
        email="tech@store.com",
        nome_loja="Tech Store",
    )

    # 1. Cadastrar Produto Físico (como em ProdutoModal._salvar)
    prod_fisico = produto_service.cadastrar_produto_fisico(
        nome="Mouse Gamer GUI",
        preco=Decimal("150.00"),
        estoque=10,
        vendedor_id=vendedor.id,
        peso_kg=Decimal("0.350"),
    )
    assert prod_fisico.id is not None
    assert prod_fisico.preco == Decimal("150.00")

    # 2. Cadastrar Produto Digital (como em ProdutoModal._salvar)
    prod_digital = produto_service.cadastrar_produto_digital(
        nome="E-book Python GUI",
        preco=Decimal("49.90"),
        estoque=25,
        vendedor_id=vendedor.id,
        tamanho_mb=Decimal("12.5"),
        link_download="https://dl.example.com/ebook-gui.pdf",
    )
    assert prod_digital.id is not None
    assert prod_digital.link_download == "https://dl.example.com/ebook-gui.pdf"

    # 3. Listagens
    todos_prods = produto_service.listar_produtos()
    assert len(todos_prods) == 2

    prods_vendedor = produto_service.listar_por_vendedor(vendedor.id)
    assert len(prods_vendedor) == 2

    # 4. Buscar por ID
    p_buscado = produto_service.buscar_por_id(prod_fisico.id)
    assert p_buscado is not None
    assert p_buscado.nome == "Mouse Gamer GUI"

    # 5. Editar Produto (Preço e Estoque) - como em ProdutoModal._salvar
    p_editado = produto_service.editar_produto(
        id_produto=prod_fisico.id,
        novo_preco=Decimal("179.90"),
        novo_estoque=15,
    )
    assert p_editado.preco == Decimal("179.90")
    assert p_editado.estoque == 15

    # 6. Remover Produto (como em _remover_selecionado)
    produto_service.remover_produto(prod_digital.id)
    with pytest.raises(EntidadeNaoEncontradaError):
        produto_service.buscar_por_id(prod_digital.id)


def test_gui_calls_pedido_service_e_carrinho(servicos_gui):
    """Testa todas as chamadas de PedidoService utilizadas em ui/gui/carrinho_view.py e pedidos_view.py."""
    usuario_service = servicos_gui["usuario_service"]
    produto_service = servicos_gui["produto_service"]
    pedido_service = servicos_gui["pedido_service"]

    vendedor = usuario_service.cadastrar_vendedor("Vendedor Car", "v@car.com", "Auto Loja")
    cliente = usuario_service.cadastrar_cliente("Cliente Car", "c@car.com", "Rua A, 100")

    p1 = produto_service.cadastrar_produto_fisico(
        nome="Peça Auto",
        preco=Decimal("200.00"),
        estoque=10,
        vendedor_id=vendedor.id,
        peso_kg=Decimal("2.0"),
    )
    p2 = produto_service.cadastrar_produto_digital(
        nome="Manual PDF",
        preco=Decimal("30.00"),
        estoque=5,
        vendedor_id=vendedor.id,
        tamanho_mb=Decimal("5.0"),
        link_download="https://auto.com/manual.pdf",
    )

    # 1. Adicionar ao carrinho (como em CarrinhoView._adicionar_item)
    pedido_service.adicionar_ao_carrinho(cliente.id, p1.id, 2)
    pedido_service.adicionar_ao_carrinho(cliente.id, p2.id, 1)

    c_atualizado = usuario_service.buscar_por_id(cliente.id)
    assert c_atualizado.carrinho.quantidade_de(p1) == 2
    assert c_atualizado.carrinho.quantidade_de(p2) == 1

    # 2. Alterar quantidade no carrinho (como em CarrinhoView._alterar_quantidade)
    pedido_service.alterar_quantidade_carrinho(cliente.id, p1.id, 3)
    c_atualizado = usuario_service.buscar_por_id(cliente.id)
    assert c_atualizado.carrinho.quantidade_de(p1) == 3

    # 3. Remover item do carrinho (como em CarrinhoView._remover_item)
    pedido_service.remover_do_carrinho(cliente.id, p2.id)
    c_atualizado = usuario_service.buscar_por_id(cliente.id)
    assert c_atualizado.carrinho.quantidade_de(p2) == 0

    # 4. Limpar carrinho (como em CarrinhoView._limpar_carrinho)
    pedido_service.limpar_carrinho(cliente.id)
    c_atualizado = usuario_service.buscar_por_id(cliente.id)
    assert c_atualizado.carrinho.esta_vazio()

    # 5. Finalizar pedido (como em FinalizarCompraModal._confirmar)
    pedido_service.adicionar_ao_carrinho(cliente.id, p1.id, 2)
    pedido = pedido_service.finalizar_pedido(cliente.id)
    assert pedido.id is not None
    assert pedido.status == StatusPedido.CONFIRMADO

    # 6. Listagens de pedidos (como em PedidosView.carregar_dados)
    todos_pedidos = pedido_service.listar_pedidos()
    assert len(todos_pedidos) == 1

    pedidos_cli = pedido_service.listar_pedidos_cliente(cliente.id)
    assert len(pedidos_cli) == 1

    # 7. Buscar pedido por ID (como em PedidosView._abrir_detalhes)
    ped_buscado = pedido_service.buscar_por_id(pedido.id)
    assert ped_buscado is not None
    assert ped_buscado.id == pedido.id

    # 8. Cancelar pedido com estorno de estoque (como em PedidosView._cancelar_pedido)
    p1_antes_cancelamento = produto_service.buscar_por_id(p1.id)
    assert p1_antes_cancelamento.estoque == 8  # 10 - 2

    pedido_cancelado = pedido_service.cancelar_pedido(pedido.id)
    assert pedido_cancelado.status == StatusPedido.CANCELADO

    p1_apos_cancelamento = produto_service.buscar_por_id(p1.id)
    assert p1_apos_cancelamento.estoque == 10  # 8 + 2 estornado


def test_gui_calls_demonstracao_service(servicos_gui):
    """Testa a chamada de DemonstracaoService utilizada em ui/gui/ferramentas_view.py."""
    demonstracao_service = servicos_gui["demonstracao_service"]
    res = demonstracao_service.carregar_dados_demo()
    assert "vendedores" in res
    assert "clientes" in res
    assert "produtos_novos" in res
    assert res["vendedores"] == 2
    assert res["clientes"] == 2
