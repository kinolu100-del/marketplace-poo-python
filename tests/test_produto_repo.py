"""
=====================================================================
Testes Unitários do Repositório SQLite de Produtos (test_produto_repo.py)
=====================================================================
Valida operações de CRUD, integridade referencial com vendedor,
precisão Decimal e persistência entre duas conexões distintas.
=====================================================================
"""

from decimal import Decimal
import pytest
from database.connection import Database
from repositories.usuario_repository import UsuarioRepository
from repositories.produto_repository import ProdutoRepository
from models.usuario import Vendedor
from models.produto import ProdutoFisico, ProdutoDigital
from exceptions import OperacaoInvalidaError


def test_crud_produtos_fisico_e_digital_sqlite(tmp_path):
    db_file = str(tmp_path / "test_produtos.db")
    db = Database(db_file)
    u_repo = UsuarioRepository(db=db)
    p_repo = ProdutoRepository(db=db, usuario_repo=u_repo)

    # 1. Cadastra vendedor
    vendedor = Vendedor(nome="Tech Store", email="contato@tech.com", nome_loja="Tech Store")
    u_repo.adicionar(vendedor)

    # 2. Cadastra produto físico
    pf = ProdutoFisico(
        nome="Teclado Gamer",
        preco=Decimal("250.75"),
        estoque=10,
        vendedor=vendedor,
        peso_kg=Decimal("0.85"),
    )
    p_repo.adicionar(pf)

    # 3. Cadastra produto digital
    pd = ProdutoDigital(
        nome="Curso POO",
        preco=Decimal("89.90"),
        estoque=50,
        vendedor=vendedor,
        tamanho_mb=Decimal("500.5"),
        link_download="https://download.curso.com/poo.zip",
    )
    p_repo.adicionar(pd)

    # 4. Busca por ID e confere tipos e valores
    bf = p_repo.buscar_por_id(pf.id)
    assert bf is not None
    assert isinstance(bf, ProdutoFisico)
    assert bf.preco == Decimal("250.75")
    assert bf.peso_kg == Decimal("0.85")
    assert bf.vendedor.id == vendedor.id

    bd = p_repo.buscar_por_id(pd.id)
    assert bd is not None
    assert isinstance(bd, ProdutoDigital)
    assert bd.preco == Decimal("89.90")
    assert bd.tamanho_mb == Decimal("500.5")
    assert bd.link_download == "https://download.curso.com/poo.zip"

    # 5. Listar geral e por vendedor
    todos = p_repo.listar()
    assert len(todos) == 2

    do_vendedor = p_repo.listar_por_vendedor(vendedor.id)
    assert len(do_vendedor) == 2
    assert len(vendedor.produtos) == 2

    # 6. Remover
    assert p_repo.remover(pf.id) is True
    assert p_repo.buscar_por_id(pf.id) is None
    assert len(p_repo.listar()) == 1


def test_persistencia_produtos_entre_duas_conexoes(tmp_path):
    db_file = str(tmp_path / "persistencia_produtos.db")

    # Primeira conexão: grava vendedor e produto
    db1 = Database(db_file)
    u_repo1 = UsuarioRepository(db=db1)
    p_repo1 = ProdutoRepository(db=db1, usuario_repo=u_repo1)

    v = Vendedor(nome="Livraria", email="livros@loja.com", nome_loja="Livraria Central")
    u_repo1.adicionar(v)
    prod = ProdutoDigital(
        nome="E-book Arquitetura Limpa",
        preco=Decimal("39.99"),
        estoque=100,
        vendedor=v,
        tamanho_mb=Decimal("15.2"),
        link_download="https://link.com/clean.pdf",
    )
    p_repo1.adicionar(prod)
    pid = prod.id
    vid = v.id
    db1.fechar()

    # Segunda conexão: reabre do arquivo e valida reidratação das relações
    db2 = Database(db_file)
    u_repo2 = UsuarioRepository(db=db2)
    p_repo2 = ProdutoRepository(db=db2, usuario_repo=u_repo2)

    prod_reaberto = p_repo2.buscar_por_id(pid)
    assert prod_reaberto is not None
    assert prod_reaberto.nome == "E-book Arquitetura Limpa"
    assert prod_reaberto.preco == Decimal("39.99")
    assert prod_reaberto.estoque == 100
    assert isinstance(prod_reaberto, ProdutoDigital)
    assert prod_reaberto.tamanho_mb == Decimal("15.2")

    # Vendedor deve ter o produto vinculado no catálogo
    vendedor_reaberto = u_repo2.buscar_por_id(vid)
    assert vendedor_reaberto is not None
    assert len(vendedor_reaberto.produtos) == 1
    assert vendedor_reaberto.produtos[0].id == pid
    assert prod_reaberto.vendedor.id == vid

    db2.fechar()


def test_integridade_fk_vendedor_inexistente(tmp_path):
    db_file = str(tmp_path / "fk_produtos.db")
    db = Database(db_file)
    p_repo = ProdutoRepository(db=db)

    # Vendedor fictício com ID que não existe na tabela usuarios
    v_fantasma = Vendedor(nome="Fantasma", email="ghost@loja.com", nome_loja="Fantasma", id_usuario=9999)
    p = ProdutoFisico(nome="Item", preco=Decimal("10.00"), estoque=5, vendedor=v_fantasma, peso_kg=Decimal("1.0"))

    with pytest.raises(OperacaoInvalidaError):
        p_repo.adicionar(p)

