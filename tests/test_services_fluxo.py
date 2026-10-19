"""
=====================================================================
Testes de Integração e Fluxo Completo de Negócio (test_services_fluxo.py)
=====================================================================
Testa o ciclo de vida completo via camadas de serviços:
  1. Cadastro de vendedores, clientes e produtos.
  2. Validação de e-mails duplicados.
  3. Adição ao carrinho e checkout (finalizar_pedido) com baixa de estoque.
  4. Cancelamento de pedido com reposição automática de estoque.
  5. Regras de integridade referencial na exclusão de usuários e produtos.
  6. Idempotência do DemonstracaoService.
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
from exceptions import (
    EmailDuplicadoError,
    EstoqueInsuficienteError,
    OperacaoInvalidaError,
)


@pytest.fixture
def servicos():
    u_repo = UsuarioRepository()
    prod_repo = ProdutoRepository()
    ped_repo = PedidoRepository()

    u_serv = UsuarioService(u_repo, prod_repo, ped_repo)
    prod_serv = ProdutoService(prod_repo, u_repo)
    ped_serv = PedidoService(ped_repo, u_repo, prod_repo)
    demo_serv = DemonstracaoService(u_serv, prod_serv, u_repo, prod_repo)

    return u_serv, prod_serv, ped_serv, demo_serv


def test_fluxo_completo_compra_e_cancelamento(servicos):
    u_serv, prod_serv, ped_serv, _ = servicos

    # 1. Cadastra vendedor e produtos
    vendedor = u_serv.cadastrar_vendedor("Loja Informática", "info@loja.com", "Info Store")
    prod_fisico = prod_serv.cadastrar_produto_fisico(
        nome="Teclado",
        preco=Decimal("150.00"),
        estoque=10,
        vendedor_id=vendedor.id,
        peso_kg=Decimal("0.50"),
    )
    prod_digital = prod_serv.cadastrar_produto_digital(
        nome="E-book Python",
        preco=Decimal("50.00"),
        estoque=20,
        vendedor_id=vendedor.id,
        tamanho_mb=Decimal("10.0"),
        link_download="https://ebook.com",
    )

    # 2. Cadastra cliente comprador
    cliente = u_serv.cadastrar_cliente("Lucas Silva", "lucas@email.com", "Av. Paulista, 100")

    # 3. Adiciona ao carrinho
    ped_serv.adicionar_ao_carrinho(cliente.id, prod_fisico.id, quantidade=2)
    ped_serv.adicionar_ao_carrinho(cliente.id, prod_digital.id, quantidade=1)

    assert len(cliente.carrinho.itens) == 2
    assert prod_fisico.estoque == 10
    assert prod_digital.estoque == 20

    # 4. Finaliza compra (checkout)
    pedido = ped_serv.finalizar_pedido(cliente.id)

    # Confere baixa de estoque
    assert prod_fisico.estoque == 8   # 10 - 2
    assert prod_digital.estoque == 19  # 20 - 1

    # Confere esvaziamento do carrinho e histórico do cliente
    assert cliente.carrinho.esta_vazio()
    assert len(cliente.pedidos) == 1
    assert cliente.pedidos[0].id == pedido.id

    # Confere totais do pedido
    # Subtotal = 150*2 + 50*1 = 350.00
    # Frete por peso = 3.50 * 0.50 * 2 = 3.50
    # Taxa fixa pedido físico = 10.00
    # Frete total = 13.50
    # Total pedido = 363.50
    assert pedido.subtotal == Decimal("350.00")
    assert pedido.frete_total == Decimal("13.50")
    assert pedido.total == Decimal("363.50")
    assert pedido.status == StatusPedido.CONFIRMADO

    # 5. Cancela pedido e confere devolução integral do estoque
    ped_serv.cancelar_pedido(pedido.id)
    assert pedido.status == StatusPedido.CANCELADO
    assert prod_fisico.estoque == 10
    assert prod_digital.estoque == 20

    # Tentativa de cancelar novamente lança OperacaoInvalidaError
    with pytest.raises(OperacaoInvalidaError):
        ped_serv.cancelar_pedido(pedido.id)


def test_validacao_email_duplicado(servicos):
    u_serv, _, _, _ = servicos
    u_serv.cadastrar_cliente("Maria", "maria@email.com", "Rua 1")

    with pytest.raises(EmailDuplicadoError):
        u_serv.cadastrar_cliente("Outra Maria", "maria@email.com", "Rua 2")

    with pytest.raises(EmailDuplicadoError):
        u_serv.cadastrar_vendedor("Loja Maria", "MARIA@EMAIL.COM", "Loja")


def test_tentativa_comprar_sem_estoque_lanca_erro(servicos):
    u_serv, prod_serv, ped_serv, _ = servicos
    vendedor = u_serv.cadastrar_vendedor("Vendedor", "v@email.com", "Loja V")
    produto = prod_serv.cadastrar_produto_fisico("Monitor", Decimal("500.00"), estoque=2, vendedor_id=vendedor.id, peso_kg=Decimal("2.0"))
    cliente = u_serv.cadastrar_cliente("Cliente", "c@email.com", "Rua C")

    # Tentativa de colocar mais do que o estoque disponível no carrinho
    with pytest.raises(EstoqueInsuficienteError):
        ped_serv.adicionar_ao_carrinho(cliente.id, produto.id, quantidade=5)


def test_regras_de_exclusao_protegida(servicos):
    u_serv, prod_serv, ped_serv, _ = servicos
    vendedor = u_serv.cadastrar_vendedor("Vendedor", "v_del@email.com", "Loja")
    produto = prod_serv.cadastrar_produto_fisico("Mouse", Decimal("50.00"), 5, vendedor.id, Decimal("0.2"))
    cliente = u_serv.cadastrar_cliente("Cliente", "c_del@email.com", "Rua")

    # Não permite remover vendedor com produtos
    with pytest.raises(OperacaoInvalidaError):
        u_serv.remover_usuario(vendedor.id)

    # Realiza compra com o cliente
    ped_serv.adicionar_ao_carrinho(cliente.id, produto.id, 1)
    ped_serv.finalizar_pedido(cliente.id)

    # Não permite remover cliente com pedidos realizados
    with pytest.raises(OperacaoInvalidaError):
        u_serv.remover_usuario(cliente.id)

    # Remove produto -> agora vendedor pode ser removido
    prod_serv.remover_produto(produto.id)
    u_serv.remover_usuario(vendedor.id)
    assert len(u_serv.listar_vendedores()) == 0


def test_idempotencia_dados_demonstracao(servicos):
    _, _, _, demo_serv = servicos

    # Executa a primeira vez
    res1 = demo_serv.carregar_dados_demo()
    assert res1["vendedores"] == 2
    assert res1["clientes"] == 2
    assert res1["produtos_novos"] == 4

    # Executa a segunda vez consecutiva (não pode lançar EmailDuplicadoError nem duplicar)
    res2 = demo_serv.carregar_dados_demo()
    assert res2["vendedores"] == 2
    assert res2["clientes"] == 2
    assert res2["produtos_novos"] == 0
    assert res2["total_produtos"] == 4


def test_edicao_de_usuarios_e_produtos(servicos):
    u_serv, prod_serv, _, _ = servicos

    v = u_serv.cadastrar_vendedor("Vendedor Original", "v_orig@loja.com", "Loja Original")
    c = u_serv.cadastrar_cliente("Cliente Original", "c_orig@email.com", "Endereço Original")
    p = prod_serv.cadastrar_produto_fisico("Produto Original", Decimal("100.00"), 10, v.id, Decimal("1.0"))

    # Edição de usuário
    u_serv.editar_usuario(v.id, nome="Vendedor Alterado", nome_loja="Loja Alterada")
    assert v.nome == "Vendedor Alterado"
    assert v.nome_loja == "Loja Alterada"

    u_serv.editar_usuario(c.id, endereco="Endereço Alterado")
    assert c.endereco == "Endereço Alterado"

    # Edição de produto
    prod_serv.editar_produto(p.id, novo_preco=Decimal("120.00"), novo_estoque=25)
    assert p.preco == Decimal("120.00")
    assert p.estoque == 25


def test_entidade_nao_encontrada(servicos):
    u_serv, prod_serv, ped_serv, _ = servicos
    from exceptions import EntidadeNaoEncontradaError

    with pytest.raises(EntidadeNaoEncontradaError):
        u_serv.buscar_por_id(9999)

    with pytest.raises(EntidadeNaoEncontradaError):
        prod_serv.buscar_por_id(9999)

    with pytest.raises(EntidadeNaoEncontradaError):
        ped_serv.buscar_por_id(9999)

