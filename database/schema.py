"""
=====================================================================
Módulo de Definição de Esquema do Banco de Dados (database/schema.py)
=====================================================================
Define o schema relacional em SQLite3 com tipos estritos, chaves
estrangeiras ativas e restrições de integridade.
=====================================================================
"""

import sqlite3

DDL_USUARIOS = """
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    tipo TEXT NOT NULL CHECK(tipo IN ('Cliente', 'Vendedor')),
    endereco TEXT,
    nome_loja TEXT
);
"""

DDL_PRODUTOS = """
CREATE TABLE IF NOT EXISTS produtos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    preco TEXT NOT NULL,
    estoque INTEGER NOT NULL CHECK(estoque >= 0),
    tipo TEXT NOT NULL CHECK(tipo IN ('Físico', 'Digital')),
    vendedor_id INTEGER NOT NULL,
    peso_kg TEXT,
    tamanho_mb TEXT,
    link_download TEXT,
    FOREIGN KEY (vendedor_id) REFERENCES usuarios(id)
);
"""

DDL_CARRINHO_ITENS = """
CREATE TABLE IF NOT EXISTS carrinho_itens (
    cliente_id INTEGER NOT NULL,
    produto_id INTEGER NOT NULL,
    quantidade INTEGER NOT NULL CHECK(quantidade > 0),
    PRIMARY KEY (cliente_id, produto_id),
    FOREIGN KEY (cliente_id) REFERENCES usuarios(id) ON DELETE CASCADE,
    FOREIGN KEY (produto_id) REFERENCES produtos(id) ON DELETE CASCADE
);
"""

DDL_PEDIDOS = """
CREATE TABLE IF NOT EXISTS pedidos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cliente_id INTEGER NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('Confirmado', 'Cancelado')),
    data_criacao TEXT NOT NULL,
    FOREIGN KEY (cliente_id) REFERENCES usuarios(id)
);
"""

DDL_ITENS_PEDIDO = """
CREATE TABLE IF NOT EXISTS itens_pedido (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pedido_id INTEGER NOT NULL,
    produto_id INTEGER NOT NULL,
    quantidade INTEGER NOT NULL CHECK(quantidade > 0),
    preco_unitario TEXT NOT NULL,
    frete TEXT NOT NULL,
    FOREIGN KEY (pedido_id) REFERENCES pedidos(id) ON DELETE CASCADE,
    FOREIGN KEY (produto_id) REFERENCES produtos(id) ON DELETE RESTRICT
);
"""

DDL_INDICES = [
    "CREATE INDEX IF NOT EXISTS idx_produtos_vendedor ON produtos(vendedor_id);",
    "CREATE INDEX IF NOT EXISTS idx_pedidos_cliente ON pedidos(cliente_id);",
    "CREATE INDEX IF NOT EXISTS idx_itens_pedido_pedido ON itens_pedido(pedido_id);",
    "CREATE INDEX IF NOT EXISTS idx_carrinho_cliente ON carrinho_itens(cliente_id);",
]


def criar_tabelas(conn: sqlite3.Connection) -> None:
    """Cria todas as tabelas e índices necessários caso ainda não existam."""
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")
    cursor.execute(DDL_USUARIOS)
    cursor.execute(DDL_PRODUTOS)
    cursor.execute(DDL_CARRINHO_ITENS)
    cursor.execute(DDL_PEDIDOS)
    cursor.execute(DDL_ITENS_PEDIDO)
    for indice in DDL_INDICES:
        cursor.execute(indice)
    conn.commit()

