"""
=====================================================================
Testes de Correções do Nível 3 - Multi-Sessão (test_nivel3_correcoes.py)
=====================================================================
Valida os três bugs corrigidos de persistência SQLite com o padrão
obrigatório de abrir DUAS (ou mais) conexões/sessões consecutivas,
simulando o fechamento e reabertura do sistema:
  a) Carrinho persistido, reabrir, editar estoque via ProdutoService,
     finalizar compra: estoque final correto (10 -> 5 -> compra 2 = 3).
  b) Reabrir e comprar todo o estoque (2 de 2): pedido salvo e estoque 0.
  c) Checkout que falha: nada gravado no banco (rollback atômico).
  d) Cancelamento após reabertura devolve estoque correto na mesma transação.
  e) Tentativa de remover produto vendido é bloqueada com OperacaoInvalidaError
     e o produto permanece na lista do vendedor em memória e itens_pedido inalterado.
=====================================================================
"""

from decimal import Decimal
import pytest
from database.connection import Database
from models.pedido import StatusPedido
from repositories.usuario_repository import UsuarioRepository
from repositories.produto_repository import ProdutoRepository
from repositories.pedido_repository import PedidoRepository
from services.usuario_service import UsuarioService
from services.produto_service import ProdutoService
from services.pedido_service import PedidoService
from exceptions import EstoqueInsuficienteError, OperacaoInvalidaError


def test_a_carrinho_reabrir_editar_estoque_finalizar(tmp_path):
    """
    a) Carrinho salvo, reabrir, editar estoque pelo ProdutoService, finalizar:
       estoque final correto (10 -> editado para 5 -> compra de 2 = 3).
       Garante que o produto reidratado no carrinho compartilha a mesma instância
       do catálogo (BUG 1 corrigido).
    """
    db_file = str(tmp_path / "teste_a.db")

    # SESSÃO 1: Criação de dados e carrinho salvo
    db1 = Database(db_file)
    u_repo1 = UsuarioRepository(db=db1)
    p_repo1 = ProdutoRepository(db=db1, usuario_repo=u_repo1)
    ped_repo1 = PedidoRepository(db=db1, usuario_repo=u_repo1, produto_repo=p_repo1)

    u_serv1 = UsuarioService(u_repo1, p_repo1, ped_repo1)
    p_serv1 = ProdutoService(p_repo1, u_repo1)
    ped_serv1 = PedidoService(ped_repo1, u_repo1, p_repo1)

    vendedor = u_serv1.cadastrar_vendedor("Tech Store", "tech@loja.com", "Tech Store")
    produto = p_serv1.cadastrar_produto_fisico(
        "Monitor 27", Decimal("1200.00"), 10, vendedor.id, Decimal("4.5")
    )
    cliente = u_serv1.cadastrar_cliente("Lucas Silva", "lucas@email.com", "Rua das Flores, 100")

    # Cliente coloca 2 unidades no carrinho
    ped_serv1.adicionar_ao_carrinho(cliente.id, produto.id, quantidade=2)
    assert cliente.carrinho.quantidade_de(produto) == 2
    db1.fechar()

    # SESSÃO 2: Reabertura do sistema
    db2 = Database(db_file)
    u_repo2 = UsuarioRepository(db=db2)
    p_repo2 = ProdutoRepository(db=db2, usuario_repo=u_repo2)
    ped_repo2 = PedidoRepository(db=db2, usuario_repo=u_repo2, produto_repo=p_repo2)

    u_serv2 = UsuarioService(u_repo2, p_repo2, ped_repo2)
    p_serv2 = ProdutoService(p_repo2, u_repo2)
    ped_serv2 = PedidoService(ped_repo2, u_repo2, p_repo2)

    # Edita o estoque do produto de 10 para 5 via ProdutoService
    p_serv2.editar_produto(produto.id, novo_estoque=5)

    # Cliente reaberto finaliza compra de 2 unidades
    pedido = ped_serv2.finalizar_pedido(cliente.id)
    assert pedido.status == StatusPedido.CONFIRMADO

    # Validação do estoque final na sessão 2: 5 - 2 = 3
    prod_s2 = p_repo2.buscar_por_id(produto.id)
    assert prod_s2.estoque == 3
    db2.fechar()

    # SESSÃO 3: Confirmação da persistência em disco
    db3 = Database(db_file)
    p_repo3 = ProdutoRepository(db=db3)
    prod_s3 = p_repo3.buscar_por_id(produto.id)
    assert prod_s3.estoque == 3
    db3.fechar()


def test_b_reabrir_e_comprar_todo_o_estoque(tmp_path):
    """
    b) Reabrir e comprar todo o estoque (2 de 2):
       pedido gravado e estoque 0 (BUG 2 corrigido).
    """
    db_file = str(tmp_path / "teste_b.db")

    # SESSÃO 1: Cadastra produto com exatamente 2 unidades e põe 2 no carrinho
    db1 = Database(db_file)
    u_repo1 = UsuarioRepository(db=db1)
    p_repo1 = ProdutoRepository(db=db1, usuario_repo=u_repo1)
    ped_repo1 = PedidoRepository(db=db1, usuario_repo=u_repo1, produto_repo=p_repo1)

    u_serv1 = UsuarioService(u_repo1, p_repo1, ped_repo1)
    p_serv1 = ProdutoService(p_repo1, u_repo1)
    ped_serv1 = PedidoService(ped_repo1, u_repo1, p_repo1)

    vendedor = u_serv1.cadastrar_vendedor("Livros SA", "livros@loja.com", "Livros SA")
    livro = p_serv1.cadastrar_produto_digital(
        "Python Avançado", Decimal("80.00"), 2, vendedor.id, Decimal("15.0"), "https://dl.livro.com"
    )
    cliente = u_serv1.cadastrar_cliente("Carla Souza", "carla@email.com", "Av Central, 45")

    ped_serv1.adicionar_ao_carrinho(cliente.id, livro.id, quantidade=2)
    db1.fechar()

    # SESSÃO 2: Reabre e finaliza compra consumindo todo o estoque (2 de 2)
    db2 = Database(db_file)
    u_repo2 = UsuarioRepository(db=db2)
    p_repo2 = ProdutoRepository(db=db2, usuario_repo=u_repo2)
    ped_repo2 = PedidoRepository(db=db2, usuario_repo=u_repo2, produto_repo=p_repo2)

    ped_serv2 = PedidoService(ped_repo2, u_repo2, p_repo2)

    pedido = ped_serv2.finalizar_pedido(cliente.id)
    assert pedido.status == StatusPedido.CONFIRMADO

    # Estoque em memória e repositório zerado
    prod_s2 = p_repo2.buscar_por_id(livro.id)
    assert prod_s2.estoque == 0
    db2.fechar()

    # SESSÃO 3: Confirmação no banco em disco
    db3 = Database(db_file)
    p_repo3 = ProdutoRepository(db=db3)
    ped_repo3 = PedidoRepository(db=db3)
    assert p_repo3.buscar_por_id(livro.id).estoque == 0
    assert len(ped_repo3.listar()) == 1
    db3.fechar()


def test_c_checkout_que_falha_nada_gravado(tmp_path):
    """
    c) Checkout que falha: nada gravado no banco
       (estoque, pedidos e itens_pedido iguais ao início - rollback atômico).
    """
    db_file = str(tmp_path / "teste_c.db")

    # SESSÃO 1: Cadastra dados iniciais com estoque 5
    db1 = Database(db_file)
    u_repo1 = UsuarioRepository(db=db1)
    p_repo1 = ProdutoRepository(db=db1, usuario_repo=u_repo1)
    ped_repo1 = PedidoRepository(db=db1, usuario_repo=u_repo1, produto_repo=p_repo1)

    u_serv1 = UsuarioService(u_repo1, p_repo1, ped_repo1)
    p_serv1 = ProdutoService(p_repo1, u_repo1)
    ped_serv1 = PedidoService(ped_repo1, u_repo1, p_repo1)

    vendedor = u_serv1.cadastrar_vendedor("Game Shop", "game@loja.com", "Game Shop")
    produto = p_serv1.cadastrar_produto_fisico(
        "Controle Sem Fio", Decimal("250.00"), 5, vendedor.id, Decimal("0.4")
    )
    cliente = u_serv1.cadastrar_cliente("Marcio Lima", "marcio@email.com", "Rua do Jogo, 12")

    # Cliente adiciona 5 ao carrinho
    ped_serv1.adicionar_ao_carrinho(cliente.id, produto.id, 5)
    db1.fechar()

    # SESSÃO 2: Reabre e simula redução externa de estoque antes do checkout
    db2 = Database(db_file)
    conn2 = db2.obter_conexao()
    # Reduz o estoque no banco diretamente para 3 (simulando concorrência ou ajuste)
    conn2.execute("UPDATE produtos SET estoque = 3 WHERE id = ?", (produto.id,))
    conn2.commit()

    u_repo2 = UsuarioRepository(db=db2)
    p_repo2 = ProdutoRepository(db=db2, usuario_repo=u_repo2)
    ped_repo2 = PedidoRepository(db=db2, usuario_repo=u_repo2, produto_repo=p_repo2)
    ped_serv2 = PedidoService(ped_repo2, u_repo2, p_repo2)

    # Tentativa de checkout de 5 unidades deve falhar porque o banco tem apenas 3
    with pytest.raises(EstoqueInsuficienteError):
        ped_serv2.finalizar_pedido(cliente.id)

    # Confere que NADA foi gravado no banco
    cursor2 = conn2.cursor()
    cursor2.execute("SELECT COUNT(*) FROM pedidos")
    assert cursor2.fetchone()[0] == 0

    cursor2.execute("SELECT COUNT(*) FROM itens_pedido")
    assert cursor2.fetchone()[0] == 0

    # Estoque no banco continua 3 (não foi alterado pelo checkout falho)
    cursor2.execute("SELECT estoque FROM produtos WHERE id = ?", (produto.id,))
    assert cursor2.fetchone()[0] == 3
    db2.fechar()


def test_d_cancelar_depois_de_reabrir_devolve_estoque(tmp_path):
    """
    d) Cancelar depois de reabrir devolve o estoque correto
       em transação única atômica (BUG 2 corrigido).
    """
    db_file = str(tmp_path / "teste_d.db")

    # SESSÃO 1: Compra 4 unidades de um estoque de 10 -> estoque vai para 6
    db1 = Database(db_file)
    u_repo1 = UsuarioRepository(db=db1)
    p_repo1 = ProdutoRepository(db=db1, usuario_repo=u_repo1)
    ped_repo1 = PedidoRepository(db=db1, usuario_repo=u_repo1, produto_repo=p_repo1)

    u_serv1 = UsuarioService(u_repo1, p_repo1, ped_repo1)
    p_serv1 = ProdutoService(p_repo1, u_repo1)
    ped_serv1 = PedidoService(ped_repo1, u_repo1, p_repo1)

    vendedor = u_serv1.cadastrar_vendedor("Hardware BR", "hard@loja.com", "Hardware BR")
    produto = p_serv1.cadastrar_produto_fisico(
        "SSD 1TB", Decimal("400.00"), 10, vendedor.id, Decimal("0.1")
    )
    cliente = u_serv1.cadastrar_cliente("Ana Julia", "ana@email.com", "Rua Sul, 80")

    ped_serv1.adicionar_ao_carrinho(cliente.id, produto.id, 4)
    pedido = ped_serv1.finalizar_pedido(cliente.id)
    pedido_id = pedido.id

    assert p_repo1.buscar_por_id(produto.id).estoque == 6
    db1.fechar()

    # SESSÃO 2: Reabre o sistema e efetua o cancelamento
    db2 = Database(db_file)
    u_repo2 = UsuarioRepository(db=db2)
    p_repo2 = ProdutoRepository(db=db2, usuario_repo=u_repo2)
    ped_repo2 = PedidoRepository(db=db2, usuario_repo=u_repo2, produto_repo=p_repo2)
    ped_serv2 = PedidoService(ped_repo2, u_repo2, p_repo2)

    pedido_cancelado = ped_serv2.cancelar_pedido(pedido_id)
    assert pedido_cancelado.status == StatusPedido.CANCELADO

    # O estoque na sessão 2 deve ter retornado integralmente para 10
    prod_s2 = p_repo2.buscar_por_id(produto.id)
    assert prod_s2.estoque == 10
    db2.fechar()

    # SESSÃO 3: Confirmação definitiva no banco após novo fechamento
    db3 = Database(db_file)
    p_repo3 = ProdutoRepository(db=db3)
    ped_repo3 = PedidoRepository(db=db3)
    assert p_repo3.buscar_por_id(produto.id).estoque == 10
    ped_banco = ped_repo3.buscar_por_id(pedido_id)
    assert ped_banco.status == StatusPedido.CANCELADO
    db3.fechar()


def test_e_remover_produto_vendido_bloqueado_itens_pedido_intacto(tmp_path):
    """
    e) Remover produto vendido é bloqueado com OperacaoInvalidaError,
       o produto NÃO é removido da lista do vendedor em memória e
       itens_pedido permanece inalterado (BUG 3 corrigido).
    """
    db_file = str(tmp_path / "teste_e.db")

    # SESSÃO 1: Realiza compra gerando registro em itens_pedido
    db1 = Database(db_file)
    u_repo1 = UsuarioRepository(db=db1)
    p_repo1 = ProdutoRepository(db=db1, usuario_repo=u_repo1)
    ped_repo1 = PedidoRepository(db=db1, usuario_repo=u_repo1, produto_repo=p_repo1)

    u_serv1 = UsuarioService(u_repo1, p_repo1, ped_repo1)
    p_serv1 = ProdutoService(p_repo1, u_repo1)
    ped_serv1 = PedidoService(ped_repo1, u_repo1, p_repo1)

    vendedor = u_serv1.cadastrar_vendedor("Eletronicos SA", "eletro@loja.com", "Eletronicos SA")
    produto = p_serv1.cadastrar_produto_fisico(
        "Fone Bluetooth", Decimal("150.00"), 8, vendedor.id, Decimal("0.3")
    )
    cliente = u_serv1.cadastrar_cliente("Pedro Santos", "pedro@email.com", "Rua Norte, 55")

    ped_serv1.adicionar_ao_carrinho(cliente.id, produto.id, 2)
    ped_serv1.finalizar_pedido(cliente.id)

    # Confere que há 1 item registrado em itens_pedido
    conn1 = db1.obter_conexao()
    cursor1 = conn1.cursor()
    cursor1.execute("SELECT COUNT(*) FROM itens_pedido WHERE produto_id = ?", (produto.id,))
    assert cursor1.fetchone()[0] == 1
    db1.fechar()

    # SESSÃO 2: Reabre e tenta remover o produto vendido
    db2 = Database(db_file)
    u_repo2 = UsuarioRepository(db=db2)
    p_repo2 = ProdutoRepository(db=db2, usuario_repo=u_repo2)
    ped_repo2 = PedidoRepository(db=db2, usuario_repo=u_repo2, produto_repo=p_repo2)

    u_serv2 = UsuarioService(u_repo2, p_repo2, ped_repo2)
    p_serv2 = ProdutoService(p_repo2, u_repo2)

    # Tentativa de remover produto vendido DEVE lançar OperacaoInvalidaError
    with pytest.raises(OperacaoInvalidaError, match="produto possui pedidos"):
        p_serv2.remover_produto(produto.id)

    # Garante que o produto NÃO foi removido da lista do vendedor em memória
    vendedor_s2 = u_serv2.buscar_por_id(vendedor.id)
    assert any(p.id == produto.id for p in vendedor_s2.produtos)

    # Garante que no banco o produto e seu item_pedido permanecem intactos
    conn2 = db2.obter_conexao()
    cursor2 = conn2.cursor()
    cursor2.execute("SELECT COUNT(*) FROM produtos WHERE id = ?", (produto.id,))
    assert cursor2.fetchone()[0] == 1

    cursor2.execute("SELECT COUNT(*) FROM itens_pedido WHERE produto_id = ?", (produto.id,))
    assert cursor2.fetchone()[0] == 1
    db2.fechar()

