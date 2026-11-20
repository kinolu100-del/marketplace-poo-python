"""
Configurações globais e fixtures para a suíte de testes (tests/conftest.py).
Garante que cada teste execute com uma instância SQLite isolada e limpa.
"""

import pytest
from database.connection import Database, resetar_banco_padrao


@pytest.fixture(autouse=True)
def _isolamento_banco_testes(tmp_path):
    """
    Garante que cada teste execute com um arquivo SQLite exclusivo e limpo,
    desacoplando a execução dos testes do arquivo 'marketplace.db' de produção.
    """
    db_file = str(tmp_path / "test_suite.db")
    db = Database(db_file)
    resetar_banco_padrao(db)
    yield db
    db.fechar()
    resetar_banco_padrao(None)

