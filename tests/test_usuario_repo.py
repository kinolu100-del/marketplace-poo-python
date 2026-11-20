"""
=====================================================================
Testes Unitários do Repositório SQLite de Usuários (test_usuario_repo.py)
=====================================================================
Valida operações de CRUD, unicidade de e-mail e persistência entre
duas conexões distintas utilizando SQLite.
=====================================================================
"""

import pytest
from database.connection import Database
from repositories.usuario_repository import UsuarioRepository
from models.usuario import Cliente, Vendedor
from exceptions import EmailDuplicadoError


def test_crud_cliente_sqlite(tmp_path):
    db_file = str(tmp_path / "test_usuarios.db")
    db = Database(db_file)
    repo = UsuarioRepository(db=db)

    # 1. Adicionar cliente
    cliente = Cliente(nome="Carlos Souza", email="carlos@teste.com", endereco="Rua A, 123")
    salvo = repo.adicionar(cliente)
    assert salvo.id == cliente.id

    # 2. Buscar por ID
    buscado = repo.buscar_por_id(cliente.id)
    assert buscado is not None
    assert buscado.nome == "Carlos Souza"
    assert buscado.email == "carlos@teste.com"
    assert isinstance(buscado, Cliente)
    assert buscado.endereco == "Rua A, 123"

    # 3. Buscar por e-mail (case-insensitive)
    buscado_email = repo.buscar_por_email("CARLOS@TESTE.COM")
    assert buscado_email is not None
    assert buscado_email.id == cliente.id

    # 4. Atualizar atributos
    buscado.nome = "Carlos S. Souza"
    buscado.endereco = "Av. B, 456"
    repo.adicionar(buscado)

    atualizado = repo.buscar_por_id(cliente.id)
    assert atualizado.nome == "Carlos S. Souza"
    assert atualizado.endereco == "Av. B, 456"

    # 5. Listar
    clientes = repo.listar_clientes()
    assert len(clientes) == 1
    assert clientes[0].id == cliente.id

    # 6. Remover
    assert repo.remover(cliente.id) is True
    assert repo.buscar_por_id(cliente.id) is None
    assert len(repo.listar_clientes()) == 0


def test_crud_vendedor_sqlite(tmp_path):
    db_file = str(tmp_path / "test_vendedores.db")
    db = Database(db_file)
    repo = UsuarioRepository(db=db)

    # 1. Adicionar vendedor
    vendedor = Vendedor(nome="Fernanda Lima", email="fernanda@loja.com", nome_loja="Moda & Cia")
    repo.adicionar(vendedor)

    # 2. Buscar
    buscado = repo.buscar_por_id(vendedor.id)
    assert buscado is not None
    assert isinstance(buscado, Vendedor)
    assert buscado.nome_loja == "Moda & Cia"

    # 3. Listar
    vendedores = repo.listar_vendedores()
    assert len(vendedores) == 1
    assert vendedores[0].nome == "Fernanda Lima"

    # 4. Limpar
    repo.limpar()
    assert len(repo.listar_vendedores()) == 0


def test_unicidade_email_lanca_excecao(tmp_path):
    db_file = str(tmp_path / "test_email.db")
    db = Database(db_file)
    repo = UsuarioRepository(db=db)

    c1 = Cliente(nome="User 1", email="duplicado@teste.com", endereco="Rua 1")
    repo.adicionar(c1)

    c2 = Cliente(nome="User 2", email="duplicado@teste.com", endereco="Rua 2")
    with pytest.raises(EmailDuplicadoError):
        repo.adicionar(c2)


def test_persistencia_entre_duas_conexoes(tmp_path):
    db_file = str(tmp_path / "persistencia_usuarios.db")

    # Primeira conexão: salva dados e fecha
    db1 = Database(db_file)
    repo1 = UsuarioRepository(db=db1)
    cliente = Cliente(nome="Roberta Dias", email="roberta@email.com", endereco="Rua X, 789")
    vendedor = Vendedor(nome="Marcos Vale", email="marcos@loja.com", nome_loja="Games Store")
    repo1.adicionar(cliente)
    repo1.adicionar(vendedor)
    id_c = cliente.id
    id_v = vendedor.id
    db1.fechar()

    # Segunda conexão: reabre e confere se dados continuam presentes
    db2 = Database(db_file)
    repo2 = UsuarioRepository(db=db2)

    cliente_reaberto = repo2.buscar_por_id(id_c)
    assert cliente_reaberto is not None
    assert cliente_reaberto.nome == "Roberta Dias"
    assert cliente_reaberto.endereco == "Rua X, 789"
    assert isinstance(cliente_reaberto, Cliente)

    vendedor_reaberto = repo2.buscar_por_id(id_v)
    assert vendedor_reaberto is not None
    assert vendedor_reaberto.nome == "Marcos Vale"
    assert vendedor_reaberto.nome_loja == "Games Store"
    assert isinstance(vendedor_reaberto, Vendedor)

    assert len(repo2.listar()) == 2
    db2.fechar()

