"""
=====================================================================
Tela de Ferramentas Administrativas (ui/gui/ferramentas_view.py)
=====================================================================
Permite carga idempotente de dados de demonstração para gravação do vídeo
e reinicialização completa/segura do banco SQLite com confirmação modal.
=====================================================================
"""

from __future__ import annotations
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Any

from ui.gui.estilos import (
    BG_CARD,
    FONT_TITLE,
    FONT_SUBTITLE,
    FONT_SECTION,
    FONT_BOLD,
)


class FerramentasView(ttk.Frame):
    """Painel da aba Ferramentas (Demonstração e Reinicialização de Banco)."""

    def __init__(
        self,
        parent: tk.Widget,
        demonstracao_service: Any,
        pedido_service: Any,
        produto_service: Any,
        usuario_service: Any,
        gui_app: Any,
    ):
        super().__init__(parent)
        self.demonstracao_service = demonstracao_service
        self.pedido_service = pedido_service
        self.produto_service = produto_service
        self.usuario_service = usuario_service
        self.gui_app = gui_app

        self._construir_interface()

    def _construir_interface(self) -> None:
        container = ttk.Frame(self, padding=25)
        container.pack(fill=tk.BOTH, expand=True)

        ttk.Label(container, text="Ferramentas Administrativas e de Demonstração", font=FONT_TITLE).pack(
            anchor=tk.W, pady=(0, 6)
        )
        ttk.Label(
            container,
            text="Utilitários desenvolvidos para apoiar testes de integração, auditoria e a gravação do vídeo de avaliação.",
            style="Muted.TLabel",
        ).pack(anchor=tk.W, pady=(0, 20))

        # -------------------------------------------------------------
        # CARD 1: CARGA DE DEMONSTRAÇÃO
        # -------------------------------------------------------------
        card_demo = ttk.Frame(container, style="Card.TFrame", padding=18)
        card_demo.pack(fill=tk.X, pady=(0, 16))

        ttk.Label(card_demo, text="📦 Carga de Dados de Exemplo (Demonstração)", font=FONT_SUBTITLE).pack(
            anchor=tk.W, pady=(0, 4)
        )
        ttk.Label(
            card_demo,
            text=(
                "Popula o banco de dados relacional com 2 vendedores (Tech Store e Livros BR), 2 clientes "
                "(Lucas Silva e Ana Souza) e 4 produtos de exemplo (físicos com cálculo de frete por peso "
                "e digitais com download imediato).\n\n"
                "✓ Operação 100% Idempotente: pode ser executada repetidas vezes sem duplicar registros."
            ),
            wraplength=800,
            justify=tk.LEFT,
        ).pack(anchor=tk.W, pady=(0, 12))

        btn_demo = ttk.Button(
            card_demo,
            text="🚀 Carregar Dados de Demonstração",
            style="Primary.TButton",
            command=self._executar_carga_demo,
        )
        btn_demo.pack(anchor=tk.W)

        # -------------------------------------------------------------
        # CARD 2: ZERAR / REINICIAR BANCO DE DADOS
        # -------------------------------------------------------------
        card_zerar = ttk.Frame(container, style="Card.TFrame", padding=18)
        card_zerar.pack(fill=tk.X)

        ttk.Label(card_zerar, text="⚠️ Reiniciar / Zerar Banco de Dados", font=FONT_SUBTITLE).pack(
            anchor=tk.W, pady=(0, 4)
        )
        ttk.Label(
            card_zerar,
            text=(
                "Exclui permanentemente todos os registros de todas as tabelas (pedidos, itens de pedidos, "
                "itens de carrinho, produtos do catálogo e usuários) e reinicia os geradores de chave "
                "primária auto-incremental no SQLite.\n\n"
                "✓ Respeita a ordem correta da árvore de integridade referencial com transação atômica."
            ),
            wraplength=800,
            justify=tk.LEFT,
        ).pack(anchor=tk.W, pady=(0, 12))

        btn_zerar = ttk.Button(
            card_zerar,
            text="💣 Apagar Tudo e Zerar Banco...",
            style="Danger.TButton",
            command=self._executar_zerar_banco,
        )
        btn_zerar.pack(anchor=tk.W)

    def _executar_carga_demo(self) -> None:
        try:
            res = self.demonstracao_service.carregar_dados_demo()
            self.gui_app.atualizar_todas_as_abas()
            self.gui_app.definir_status("Carga de demonstração executada com sucesso.")

            msg = (
                "Carga de demonstração concluída com sucesso!\n\n"
                f"• Vendedores na base: {res['vendedores']}\n"
                f"• Clientes na base: {res['clientes']}\n"
                f"• Novos produtos adicionados: {res['produtos_novos']}\n\n"
                "Os dados já estão visíveis nas abas 'Usuários' e 'Produtos'."
            )
            messagebox.showinfo("Carga Demo Idempotente", msg, parent=self)
        except Exception as erro:
            messagebox.showerror("Erro na Carga Demo", f"Falha ao carregar dados de demonstração: {erro}", parent=self)

    def _executar_zerar_banco(self) -> None:
        confirma = messagebox.askyesno(
            "ATENÇÃO - Zerar Banco de Dados",
            "Deseja realmente apagar TODOS os dados do sistema?\n\n"
            "Esta ação excluirá permanentemente todos os usuários, produtos, cestas e pedidos históricos do SQLite.",
            parent=self,
        )
        if not confirma:
            return

        try:
            db = self.pedido_service.pedido_repo.db
            db.limpar_tudo()

            # Reseta os caches e geradores de ID sequenciais de cada repositório
            for repo in (
                self.pedido_service.pedido_repo,
                self.produto_service.produto_repo,
                self.usuario_service.usuario_repo,
            ):
                repo._cache.clear()
                repo._sincronizar_gerador_id()

            self.gui_app.atualizar_todas_as_abas()
            self.gui_app.definir_status("Banco de dados SQLite reiniciado com sucesso. Todas as tabelas foram esvaziadas.")
            messagebox.showinfo(
                "Banco Zerado",
                "O banco de dados SQLite foi esvaziado com sucesso!\nTodas as tabelas foram limpas e os geradores de ID resetados.",
                parent=self,
            )
        except Exception as erro:
            messagebox.showerror("Erro ao Zerar Banco", f"Falha na reinicialização do banco: {erro}", parent=self)
