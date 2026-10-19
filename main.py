"""
=====================================================================
Ponto de Entrada Principal (main.py)
Projeto: Marketplace Simples em Python (Paradigma POO)
=====================================================================
Instancia as camadas de persistência (repositórios), regras de negócio
puras (serviços) e a interface com o usuário (CLI de console),
desencadeando o fluxo interativo do sistema.
=====================================================================
"""

import sys
from repositories.usuario_repository import UsuarioRepository
from repositories.produto_repository import ProdutoRepository
from repositories.pedido_repository import PedidoRepository
from services.usuario_service import UsuarioService
from services.produto_service import ProdutoService
from services.pedido_service import PedidoService
from services.demonstracao_service import DemonstracaoService
from ui.cli import MarketplaceCLI


def main() -> None:
    """Função de inicialização e injeção de dependências do sistema."""
    # 1. Camada de Repositórios (Em memória - pronta para Nível 3 / SQLite)
    usuario_repo = UsuarioRepository()
    produto_repo = ProdutoRepository()
    pedido_repo = PedidoRepository()

    # 2. Camada de Serviços de Negócio (Regras puras sem input/print)
    usuario_service = UsuarioService(
        usuario_repo=usuario_repo,
        produto_repo=produto_repo,
        pedido_repo=pedido_repo,
    )
    produto_service = ProdutoService(
        produto_repo=produto_repo,
        usuario_repo=usuario_repo,
    )
    pedido_service = PedidoService(
        pedido_repo=pedido_repo,
        usuario_repo=usuario_repo,
        produto_repo=produto_repo,
    )
    demonstracao_service = DemonstracaoService(
        usuario_service=usuario_service,
        produto_service=produto_service,
        usuario_repo=usuario_repo,
        produto_repo=produto_repo,
    )

    # 3. Camada de Apresentação (Console CLI)
    cli = MarketplaceCLI(
        usuario_service=usuario_service,
        produto_service=produto_service,
        pedido_service=pedido_service,
        demonstracao_service=demonstracao_service,
    )

    # 4. Início da execução
    cli.executar()


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print("\n\nSessão encerrada pelo usuário.")
    except Exception as erro:
        print(f"\n[ERRO FATAL]: Ocorreu um erro inesperado: {erro}", file=sys.stderr)
