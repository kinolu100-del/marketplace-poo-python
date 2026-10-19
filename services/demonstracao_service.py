"""
=====================================================================
Serviço de Dados de Demonstração (services/demonstracao_service.py)
=====================================================================
Carrega dados de teste de forma estritamente idempotente:
  - Não duplica e-mails mesmo se executado repetidas vezes.
  - Reutiliza entidades existentes caso já tenham sido inseridas.
  - Perfeito para a gravação dos vídeos de demonstração (Níveis 1 e 2).
=====================================================================
"""

from __future__ import annotations
from decimal import Decimal
from typing import Dict, Any
from services.usuario_service import UsuarioService
from services.produto_service import ProdutoService
from repositories.usuario_repository import UsuarioRepository
from repositories.produto_repository import ProdutoRepository


class DemonstracaoService:
    """Popula dados fictícios com segurança e idempotência."""

    def __init__(
        self,
        usuario_service: UsuarioService,
        produto_service: ProdutoService,
        usuario_repo: UsuarioRepository,
        produto_repo: ProdutoRepository,
    ):
        self.usuario_service = usuario_service
        self.produto_service = produto_service
        self.usuario_repo = usuario_repo
        self.produto_repo = produto_repo

    def carregar_dados_demo(self) -> Dict[str, Any]:
        """
        Popula a base em memória com dados ricos para testes e demonstração.
        Idempotente: ignora ou reutiliza registros cujos e-mails já existam.
        """
        # 1. Vendedores
        vendedor_dados = [
            ("Mariana Costa", "mariana@techprime.com", "Tech Prime Informática"),
            ("Rafael Souza", "rafael@livroscursos.com", "Livraria Saber Digital"),
        ]
        vendedores = []
        for nome, email, loja in vendedor_dados:
            v = self.usuario_repo.buscar_por_email(email)
            if v is None:
                v = self.usuario_service.cadastrar_vendedor(nome=nome, email=email, nome_loja=loja)
            vendedores.append(v)

        v1, v2 = vendedores[0], vendedores[1]

        # 2. Clientes
        cliente_dados = [
            ("Lucas Silva", "lucas@email.com", "Av. Paulista, 1000 - São Paulo/SP"),
            ("Beatriz Mendes", "beatriz@email.com", "Rua das Flores, 45 - Rio de Janeiro/RJ"),
        ]
        clientes = []
        for nome, email, endereco in cliente_dados:
            c = self.usuario_repo.buscar_por_email(email)
            if c is None:
                c = self.usuario_service.cadastrar_cliente(nome=nome, email=email, endereco=endereco)
            clientes.append(c)

        # 3. Produtos (adiciona se ainda não existirem com o mesmo nome para o vendedor)
        produtos_atuais = {p.nome for p in self.produto_repo.listar()}
        produtos_criados = []

        if "Teclado Mecânico RGB" not in produtos_atuais:
            p1 = self.produto_service.cadastrar_produto_fisico(
                nome="Teclado Mecânico RGB",
                preco=Decimal("299.90"),
                estoque=8,
                vendedor_id=v1.id,
                peso_kg=Decimal("0.95"),
            )
            produtos_criados.append(p1)

        if "Mouse Sem Fio Ergonômico" not in produtos_atuais:
            p2 = self.produto_service.cadastrar_produto_fisico(
                nome="Mouse Sem Fio Ergonômico",
                preco=Decimal("149.50"),
                estoque=15,
                vendedor_id=v1.id,
                peso_kg=Decimal("0.25"),
            )
            produtos_criados.append(p2)

        if "E-book Python Orientado a Objetos" not in produtos_atuais:
            p3 = self.produto_service.cadastrar_produto_digital(
                nome="E-book Python Orientado a Objetos",
                preco=Decimal("49.90"),
                estoque=100,
                vendedor_id=v2.id,
                tamanho_mb=Decimal("12.4"),
                link_download="https://marketplace.exemplo.com/download/ebook-poo.pdf",
            )
            produtos_criados.append(p3)

        if "Curso Completo de Python Desktop" not in produtos_atuais:
            p4 = self.produto_service.cadastrar_produto_digital(
                nome="Curso Completo de Python Desktop",
                preco=Decimal("129.00"),
                estoque=50,
                vendedor_id=v2.id,
                tamanho_mb=Decimal("450.0"),
                link_download="https://marketplace.exemplo.com/cursos/python-desktop",
            )
            produtos_criados.append(p4)

        return {
            "vendedores": len(vendedores),
            "clientes": len(clientes),
            "produtos_novos": len(produtos_criados),
            "total_produtos": len(self.produto_repo.listar()),
        }
