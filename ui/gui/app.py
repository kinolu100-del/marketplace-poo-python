"""
=====================================================================
Janela Principal da Aplicação GUI (ui/gui/app.py)
=====================================================================
Orquestra a interface gráfica desktop (Tkinter/ttk - Desk App IV),
aplicando o tema escuro, cabeçalho de destaque, abas de módulos,
barra de status e vinculação aos serviços de domínio.
=====================================================================
"""

from __future__ import annotations
import tkinter as tk
from tkinter import ttk
from typing import Any

from ui.gui.estilos import (
    BG_DARK,
    BG_SURFACE,
    TEXT_WHITE,
    TEXT_MUTED,
    ACCENT_PRIMARY,
    FONT_TITLE,
    FONT_SMALL,
    aplicar_tema,
)
from ui.gui.usuarios_view import UsuariosView
from ui.gui.produtos_view import ProdutosView
from ui.gui.carrinho_view import CarrinhoView
from ui.gui.pedidos_view import PedidosView
from ui.gui.ferramentas_view import FerramentasView


class MarketplaceGUI(tk.Tk):
    """
    Janela Principal do Sistema Marketplace POO (Desk App IV).
    Integra as cinco abas do sistema através de um Notebook responsivo.
    """

    def __init__(
        self,
        usuario_service: Any,
        produto_service: Any,
        pedido_service: Any,
        demonstracao_service: Any,
    ):
        super().__init__()
        self.usuario_service = usuario_service
        self.produto_service = produto_service
        self.pedido_service = pedido_service
        self.demonstracao_service = demonstracao_service

        self.title("Marketplace POO - Gestão & E-Commerce (Desk App IV)")
        self.geometry("1060x700")
        self.minsize(960, 620)
        self.configure(bg=BG_DARK)

        # Aplica estilos e tema escuro
        aplicar_tema(self)

        self._status_var = tk.StringVar(value="Sistema pronto. Conectado ao banco SQLite.")
        self._construir_interface()

    def _construir_interface(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        # -------------------------------------------------------------
        # 1. CABEÇALHO SUPERIOR (BRANDING & BADGES)
        # -------------------------------------------------------------
        header = ttk.Frame(self, style="Header.TFrame", padding=(18, 12))
        header.grid(row=0, column=0, sticky="ew")
        header.columnconfigure(0, weight=1)
        header.columnconfigure(1, weight=0)

        frm_titulos = ttk.Frame(header, style="Header.TFrame")
        frm_titulos.grid(row=0, column=0, sticky="w")

        lbl_marca = ttk.Label(
            frm_titulos,
            text="🛒 MARKETPLACE POO  |  DESK APP IV",
            style="HeaderTitle.TLabel",
        )
        lbl_marca.pack(anchor=tk.W)

        lbl_sub = ttk.Label(
            frm_titulos,
            text="Sistema Desktop Orientado a Objetos com Persistência SQLite Relacional e Interface Gráfica Tkinter/ttk",
            style="HeaderSubtitle.TLabel",
        )
        lbl_sub.pack(anchor=tk.W, pady=(2, 0))

        # Badges no canto direito
        frm_badges = ttk.Frame(header, style="Header.TFrame")
        frm_badges.grid(row=0, column=1, sticky="e")

        lbl_badge_db = tk.Label(
            frm_badges,
            text="● SQLite 3 (ACID)",
            bg=BG_SURFACE,
            fg="#10B981",
            font=("Segoe UI", 8, "bold"),
            padx=8,
            pady=4,
            relief="flat",
        )
        lbl_badge_db.pack(side=tk.LEFT, padx=(0, 6))

        lbl_badge_poo = tk.Label(
            frm_badges,
            text="POO Completo",
            bg=BG_SURFACE,
            fg=ACCENT_PRIMARY,
            font=("Segoe UI", 8, "bold"),
            padx=8,
            pady=4,
            relief="flat",
        )
        lbl_badge_poo.pack(side=tk.LEFT)

        # -------------------------------------------------------------
        # 2. ÁREA CENTRAL DE ABAS (NOTEBOOK)
        # -------------------------------------------------------------
        self.notebook = ttk.Notebook(self)
        self.notebook.grid(row=1, column=0, sticky="nsew", padx=10, pady=(4, 0))

        # Instanciação das 5 visualizações
        self.view_usuarios = UsuariosView(self.notebook, self.usuario_service, gui_app=self)
        self.view_produtos = ProdutosView(self.notebook, self.produto_service, self.usuario_service, gui_app=self)
        self.view_carrinho = CarrinhoView(
            self.notebook,
            self.pedido_service,
            self.usuario_service,
            self.produto_service,
            gui_app=self,
        )
        self.view_pedidos = PedidosView(self.notebook, self.pedido_service, self.usuario_service, gui_app=self)
        self.view_ferramentas = FerramentasView(
            self.notebook,
            self.demonstracao_service,
            self.pedido_service,
            self.produto_service,
            self.usuario_service,
            gui_app=self,
        )

        self.notebook.add(self.view_usuarios, text="  👥  Usuários  ")
        self.notebook.add(self.view_produtos, text="  📦  Produtos  ")
        self.notebook.add(self.view_carrinho, text="  🛒  Carrinho  ")
        self.notebook.add(self.view_pedidos, text="  📋  Pedidos  ")
        self.notebook.add(self.view_ferramentas, text="  ⚙️  Ferramentas  ")

        # Sincroniza dados ao alternar abas
        self.notebook.bind("<<NotebookTabChanged>>", self._ao_mudar_aba)

        # -------------------------------------------------------------
        # 3. RODAPÉ / STATUS BAR
        # -------------------------------------------------------------
        footer = ttk.Frame(self, style="Footer.TFrame", padding=(14, 6))
        footer.grid(row=2, column=0, sticky="ew")
        footer.columnconfigure(0, weight=1)
        footer.columnconfigure(1, weight=0)

        lbl_status = ttk.Label(footer, textvariable=self._status_var, style="Status.TLabel")
        lbl_status.grid(row=0, column=0, sticky="w")

        lbl_info = ttk.Label(
            footer,
            text="Base: marketplace.db  |  Python 3.10+  |  Disciplina de POO",
            style="Muted.TLabel",
        )
        lbl_info.grid(row=0, column=1, sticky="e")

    def _ao_mudar_aba(self, event: Any = None) -> None:
        """Disparado quando o usuário troca de aba para manter dados sincronizados."""
        aba_idx = self.notebook.index(self.notebook.select())
        if aba_idx == 0:
            self.view_usuarios.carregar_dados()
        elif aba_idx == 1:
            self.view_produtos.carregar_dados()
        elif aba_idx == 2:
            self.view_carrinho.carregar_dados()
        elif aba_idx == 3:
            self.view_pedidos.carregar_dados()

    def definir_status(self, mensagem: str) -> None:
        """Atualiza a mensagem na barra de status inferior."""
        self._status_var.set(f"● {mensagem}")

    def atualizar_todas_as_abas(self) -> None:
        """Força atualização de dados em todas as abas filhas."""
        self.view_usuarios.carregar_dados()
        self.view_produtos.carregar_dados()
        self.view_carrinho.carregar_dados()
        self.view_pedidos.carregar_dados()
