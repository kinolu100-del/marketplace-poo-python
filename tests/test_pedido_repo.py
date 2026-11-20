"""
=====================================================================
Testes Unitários do Repositório SQLite de Pedidos e Carrinho (test_pedido_repo.py)
=====================================================================
Valida operações transacionais, rollback em falhas de estoque,
congelamento de preços históricos, reposição de estoque no cancelamento
e persistência do carrinho entre conexões.
=====================================================================
"""

from decimal import Decimal
import pytest
from database.connection import Database
from repositories.usuario_repository import UsuarioRepository
from repositories.produto_repository import ProdutoRepository
from repositories.pedido_repository import PedidoRepository
from models.usuario import Cliente, Vendedor
from models.produto import ProdutoFisico, ProdutoDigital
from models.pedido import Pedido, StatusPedido
from exceptions import EstoqueInsuficienteError


def test_crud_pedido_e_itens_sqlite(tmp_path):
    db_file = str(tmp_path / "test_pedidos.db")
    db = Database(db_file)
    u_repo = UsuarioRepository(db=db)
    p_repo = ProdutoRepository(db=db, usuario_repo=u_repo)
    ped_repo = PedidoRepository(db=db, usuario_repo=u_repo, produto_repo=p_repo)

    # Cria cliente, vendedor e produto
    v = Vendedor(nome="Loja A", email="loja@a.com", nome_loja="Loja A")
    c = Cliente(nome="Comprador", email="comp@a.com", endereco="Rua 1")
    p = ProdutoFisico(nome="Mouse", preco=Decimal("50.00"), estoque=10, vendedor=v, peso_kg=Decimal("0.20"))
    u_repo.adicionar(v)
    u_repo.adicionar(c)
    p_repo.adicionar(p)

    # Cria pedido e adiciona item
    pedido = Pedido(cliente=c)
    pedido.adicionar_item(p, quantidade=2)
    p.baixar_estoque(2)

    ped_repo.adicionar(pedido)
    assert pedido.id is not None

    # Busca por ID e confere dados
    buscado = ped_repo.buscar_por_id(pedido.id)
    assert buscado is not None
    assert buscado.cliente.id == c.id
    assert len(buscado.itens) == 1
    assert buscado.itens[0].produto.id == p.id
    assert buscado.itens[0].quantidade == 2
    assert buscado.status == StatusPedido.CONFIRMADO

    # Listar por cliente
    pedidos_c = ped_repo.listar_por_cliente(c.id)
    assert len(pedidos_c) == 1
    assert pedidos_c[0].id == pedido.id

    db.fechar()


def test_persistencia_pedido_entre_duas_conexoes(tmp_path):
    db_file = str(tmp_path / "persistencia_pedidos.db")

    # Primeira conexão: grava compra completa
    db1 = Database(db_file)
    u_repo1 = UsuarioRepository(db=db1)
    p_repo1 = ProdutoRepository(db=db1, usuario_repo=u_repo1)
    ped_repo1 = PedidoRepository(db=db1, usuario_repo=u_repo1, produto_repo=p_repo1)

    v = Vendedor(nome="Vendedor", email="v@v.com", nome_loja="V Loja")
    c = Cliente(nome="Cliente", email="c@c.com", endereco="Rua C")
    p = ProdutoDigital(nome="Curso", preco=Decimal("120.00"), estoque=5, vendedor=v, tamanho_mb=Decimal("100"), link_download="https://link.com")
    u_repo1.adicionar(v)
    u_repo1.adicionar(c)
    p_repo1.adicionar(p)

    pedido = Pedido(cliente=c)
    pedido.adicionar_item(p, quantidade=1)
    p.baixar_estoque(1)
    ped_repo1.adicionar(pedido)

    pid = pedido.id
    cid = c.id
    db1.fechar()

    # Segunda conexão: reabre e valida integridade e relações
    db2 = Database(db_file)
    u_repo2 = UsuarioRepository(db=db2)
    p_repo2 = ProdutoRepository(db=db2, usuario_repo=u_repo2)
    ped_repo2 = PedidoRepository(db=db2, usuario_repo=u_repo2, produto_repo=p_repo2)

    pedido_reaberto = ped_repo2.buscar_por_id(pid)
    assert pedido_reaberto is not None
    assert pedido_reaberto.cliente.id == cid
    assert pedido_reaberto.total == Decimal("120.00")
    assert len(pedido_reaberto.itens) == 1
    assert pedido_reaberto.itens[0].preco_unitario == Decimal("120.00")

    # O cliente reidratado deve ter o pedido em seu histórico
    cliente_reaberto = u_repo2.buscar_por_id(cid)
    assert len(cliente_reaberto.pedidos) == 1
    assert cliente_reaberto.pedidos[0].id == pid

    db2.fechar()


def test_preco_congelado_apos_alteracao_do_produto(tmp_path):
    """
    Garante que o preço no histórico do pedido permanece congelado
    mesmo após a alteração posterior do preço do produto no catálogo.
    """
    db_file = str(tmp_path / "preco_congelado.db")
    db = Database(db_file)
    u_repo = UsuarioRepository(db=db)
    p_repo = ProdutoRepository(db=db, usuario_repo=u_repo)
    ped_repo = PedidoRepository(db=db, usuario_repo=u_repo, produto_repo=p_repo)

    v = Vendedor(nome="Loja V", email="v@preco.com", nome_loja="Loja V")
    c = Cliente(nome="Cliente C", email="c@preco.com", endereco="Rua C")
    p = ProdutoFisico(nome="Mochila", preco=Decimal("100.00"), estoque=20, vendedor=v, peso_kg=Decimal("1.00"))
    u_repo.adicionar(v)
    u_repo.adicionar(c)
    p_repo.adicionar(p)

    # Compra a R$ 100.00 (Subtotal: 100.00, Frete: 3.50 + 10.00 = 13.50, Total: 113.50)
    pedido = Pedido(cliente=c)
    pedido.adicionar_item(p, quantidade=1)
    p.baixar_estoque(1)
    ped_repo.adicionar(pedido)

    # Altera o preço do produto para R$ 250.00
    p.preco = Decimal("250.00")
    p_repo.adicionar(p)
    assert p_repo.buscar_por_id(p.id).preco == Decimal("250.00")

    # Fecha e reabre o banco para garantir que a leitura do histórico vem do disco
    db.fechar()
    db2 = Database(db_file)
    u_repo2 = UsuarioRepository(db=db2)
    p_repo2 = ProdutoRepository(db=db2, usuario_repo=u_repo2)
    ped_repo2 = PedidoRepository(db=db2, usuario_repo=u_repo2, produto_repo=p_repo2)

    pedido_historico = ped_repo2.buscar_por_id(pedido.id)
    assert pedido_historico.itens[0].preco_unitario == Decimal("100.00")
    assert pedido_historico.subtotal == Decimal("100.00")
    assert pedido_historico.total == Decimal("113.50")
    db2.fechar()


def test_cancelamento_devolvendo_estoque_mesma_transacao(tmp_path):
    """
    Valida a transação atômica de cancelamento:
    atualiza o status para Cancelado e repõe o estoque do produto no banco.
    """
    db_file = str(tmp_path / "cancelamento.db")
    db = Database(db_file)
    u_repo = UsuarioRepository(db=db)
    p_repo = ProdutoRepository(db=db, usuario_repo=u_repo)
    ped_repo = PedidoRepository(db=db, usuario_repo=u_repo, produto_repo=p_repo)

    v = Vendedor(nome="Vendedor", email="v@cancela.com", nome_loja="Loja V")
    c = Cliente(nome="Cliente", email="c@cancela.com", endereco="Rua C")
    p = ProdutoFisico(nome="Cadeira", preco=Decimal("300.00"), estoque=10, vendedor=v, peso_kg=Decimal("5.00"))
    u_repo.adicionar(v)
    u_repo.adicionar(c)
    p_repo.adicionar(p)

    # Compra 3 unidades -> estoque vai para 7
    pedido = Pedido(cliente=c)
    pedido.adicionar_item(p, quantidade=3)
    p.baixar_estoque(3)
    ped_repo.adicionar(pedido)

    prod_no_banco = p_repo.buscar_por_id(p.id)
    assert prod_no_banco.estoque == 7

    # Cancela o pedido via serviço/entidade
    p.repor_estoque(3)
    pedido.cancelar()

    # Confere no banco se o status foi gravado e o estoque reposto
    db.fechar()
    db2 = Database(db_file)
    u_repo2 = UsuarioRepository(db=db2)
    p_repo2 = ProdutoRepository(db=db2, usuario_repo=u_repo2)
    ped_repo2 = PedidoRepository(db=db2, usuario_repo=u_repo2, produto_repo=p_repo2)

    pedido_consultado = ped_repo2.buscar_por_id(pedido.id)
    assert pedido_consultado.status == StatusPedido.CANCELADO
    prod_consultado = p_repo2.buscar_por_id(p.id)
    assert prod_consultado.estoque == 10
    db2.fechar()


def test_rollback_quando_finalizar_falha_por_estoque(tmp_path):
    """
    Valida rollback na transação composta de finalização de pedido:
    se a quantidade solicitada for maior que o saldo no banco,
    nenhum pedido/item é gravado e o estoque permanece intocado.
    """
    db_file = str(tmp_path / "rollback_estoque.db")
    db = Database(db_file)
    u_repo = UsuarioRepository(db=db)
    p_repo = ProdutoRepository(db=db, usuario_repo=u_repo)
    ped_repo = PedidoRepository(db=db, usuario_repo=u_repo, produto_repo=p_repo)

    v = Vendedor(nome="Vendedor", email="v@rb.com", nome_loja="Loja RB")
    c = Cliente(nome="Cliente", email="c@rb.com", endereco="Rua RB")
    p = ProdutoFisico(nome="Tablet", preco=Decimal("800.00"), estoque=2, vendedor=v, peso_kg=Decimal("0.50"))
    u_repo.adicionar(v)
    u_repo.adicionar(c)
    p_repo.adicionar(p)

    # Tenta salvar pedido pedindo 5 unidades (maior que o estoque 2)
    pedido_invalido = Pedido(cliente=c)
    pedido_invalido.adicionar_item(p, quantidade=5)

    with pytest.raises(EstoqueInsuficienteError):
        ped_repo.adicionar(pedido_invalido)

    # Confere que a transação sofreu rollback: nenhum pedido gravado e estoque mantido em 2
    conn = db.obter_conexao()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM pedidos")
    assert cursor.fetchone()[0] == 0
    cursor.execute("SELECT COUNT(*) FROM itens_pedido")
    assert cursor.fetchone()[0] == 0
    cursor.execute("SELECT estoque FROM produtos WHERE id = ?", (p.id,))
    assert cursor.fetchone()[0] == 2
    db.fechar()


def test_persistencia_carrinho_entre_duas_conexoes(tmp_path):
    """
    Valida que os itens adicionados ao carrinho do cliente são salvos
    em 'carrinho_itens' e restaurados integralmente ao reabrir o programa.
    """
    db_file = str(tmp_path / "carrinho.db")

    # Conexão 1: adiciona ao carrinho e fecha
    db1 = Database(db_file)
    u_repo1 = UsuarioRepository(db=db1)
    p_repo1 = ProdutoRepository(db=db1, usuario_repo=u_repo1)

    v = Vendedor(nome="Loja Car", email="v@car.com", nome_loja="Loja Car")
    c = Cliente(nome="Cliente Car", email="c@car.com", endereco="Rua Car")
    p1 = ProdutoFisico(nome="Item 1", preco=Decimal("10.00"), estoque=50, vendedor=v, peso_kg=Decimal("0.10"))
    p2 = ProdutoFisico(nome="Item 2", preco=Decimal("20.00"), estoque=50, vendedor=v, peso_kg=Decimal("0.20"))
    u_repo1.adicionar(v)
    u_repo1.adicionar(c)
    p_repo1.adicionar(p1)
    p_repo1.adicionar(p2)

    c.carrinho.adicionar(p1, quantidade=3)
    c.carrinho.adicionar(p2, quantidade=2)
    cid = c.id
    db1.fechar()

    # Conexão 2: reabre e valida se o carrinho mantém os itens
    db2 = Database(db_file)
    u_repo2 = UsuarioRepository(db=db2)
    p_repo2 = ProdutoRepository(db=db2, usuario_repo=u_repo2)

    cliente_reaberto = u_repo2.buscar_por_id(cid)
    assert cliente_reaberto is not None
    assert len(cliente_reaberto.carrinho.itens) == 2
    assert cliente_reaberto.carrinho.subtotal == Decimal("70.00")  # 10*3 + 20*2 = 70.00

    # Limpar carrinho e fechar
    cliente_reaberto.carrinho.limpar()
    assert cliente_reaberto.carrinho.esta_vazio()
    db2.fechar()

    # Conexão 3: reabre e valida se o carrinho continua vazio
    db3 = Database(db_file)
    u_repo3 = UsuarioRepository(db=db3)
    cliente_limpo = u_repo3.buscar_por_id(cid)
    assert cliente_limpo.carrinho.esta_vazio()
    db3.fechar()

