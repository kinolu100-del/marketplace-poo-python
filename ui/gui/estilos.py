"""
=====================================================================
Módulo de Estilos Visuais e Tema Escuro (ui/gui/estilos.py)
=====================================================================
Define a paleta de cores moderna, tipografia e personalização completa
de widgets via ttk.Style (botões coloridos, Treeview alternada, abas,
cabeçalho e barra de status).
=====================================================================
"""

from __future__ import annotations
import tkinter as tk
from tkinter import ttk
from typing import Any

# =====================================================================
# PALETA DE CORES (DARK THEME MODERNO)
# =====================================================================
BG_DARK = "#12131D"            # Fundo base da janela principal
BG_CARD = "#1A1B2A"            # Fundo dos cartões, abas e painéis
BG_SURFACE = "#25273C"         # Superfícies elevadas (headers de tabela, inputs)
BG_HOVER = "#31344F"           # Efeito hover em listas e botões
BG_SELECTED = "#3E436D"        # Linha/item selecionado

BG_ROW_EVEN = "#1A1B2A"        # Linha par da Treeview
BG_ROW_ODD = "#151623"         # Linha ímpar da Treeview

TEXT_WHITE = "#FFFFFF"         # Títulos de alto destaque
TEXT_MAIN = "#E2E8F0"          # Texto padrão legível
TEXT_MUTED = "#94A3B8"         # Legendas e rótulos secundários

ACCENT_PRIMARY = "#6366F1"     # Azul / Índigo para botões de ação principal
ACCENT_PRIMARY_HOVER = "#4F46E5"

ACCENT_SUCCESS = "#10B981"     # Verde esmeralda para confirmações e checkout
ACCENT_SUCCESS_HOVER = "#059669"

ACCENT_DANGER = "#EF4444"      # Vermelho para cancelamento e deleção
ACCENT_DANGER_HOVER = "#DC2626"

ACCENT_SECONDARY = "#334155"   # Slate para botões neutros/atualizar
ACCENT_SECONDARY_HOVER = "#475569"

BORDER_COLOR = "#2A2D45"       # Bordas sutis


# =====================================================================
# FONTES PADRONIZADAS
# =====================================================================
FONT_TITLE = ("Segoe UI", 14, "bold")
FONT_SUBTITLE = ("Segoe UI", 11, "bold")
FONT_SECTION = ("Segoe UI", 10, "bold")
FONT_BOLD = ("Segoe UI", 9, "bold")
FONT_MAIN = ("Segoe UI", 9)
FONT_SMALL = ("Segoe UI", 8)
FONT_MONO = ("Consolas", 9)
FONT_MONO_BOLD = ("Consolas", 10, "bold")


def aplicar_tema(root: Any) -> ttk.Style:
    """
    Aplica o tema escuro customizado a todos os widgets ttk da aplicação,
    garantindo compatibilidade visual entre plataformas.
    """
    style = ttk.Style(root)
    temas = style.theme_names()
    if "clam" in temas:
        style.theme_use("clam")
    elif "default" in temas:
        style.theme_use("default")

    # Configuração da janela raiz
    try:
        root.configure(bg=BG_DARK)
    except Exception:
        pass

    # Padrão Global
    style.configure(
        ".",
        background=BG_CARD,
        foreground=TEXT_MAIN,
        font=FONT_MAIN,
    )

    # -----------------------------------------------------------------
    # FRAMES
    # -----------------------------------------------------------------
    style.configure("TFrame", background=BG_CARD)
    style.configure("Dark.TFrame", background=BG_DARK)
    style.configure("Surface.TFrame", background=BG_SURFACE)
    style.configure("Header.TFrame", background=BG_DARK)
    style.configure("Footer.TFrame", background=BG_DARK)
    style.configure("Card.TFrame", background=BG_CARD, relief="solid", borderwidth=1)

    # -----------------------------------------------------------------
    # LABELS
    # -----------------------------------------------------------------
    style.configure("TLabel", background=BG_CARD, foreground=TEXT_MAIN, font=FONT_MAIN)
    style.configure("Dark.TLabel", background=BG_DARK, foreground=TEXT_MAIN, font=FONT_MAIN)
    style.configure("HeaderTitle.TLabel", background=BG_DARK, foreground=TEXT_WHITE, font=FONT_TITLE)
    style.configure("HeaderSubtitle.TLabel", background=BG_DARK, foreground=TEXT_MUTED, font=FONT_SMALL)
    style.configure("CardTitle.TLabel", background=BG_CARD, foreground=TEXT_WHITE, font=FONT_SUBTITLE)
    style.configure("Section.TLabel", background=BG_CARD, foreground=TEXT_WHITE, font=FONT_SECTION)
    style.configure("Muted.TLabel", background=BG_CARD, foreground=TEXT_MUTED, font=FONT_SMALL)
    style.configure("Status.TLabel", background=BG_DARK, foreground=TEXT_MAIN, font=FONT_SMALL)
    style.configure("ValueTotal.TLabel", background=BG_CARD, foreground=ACCENT_SUCCESS, font=("Segoe UI", 13, "bold"))

    # -----------------------------------------------------------------
    # BOTÕES PERSONALIZADOS
    # -----------------------------------------------------------------
    style.configure(
        "TButton",
        background=ACCENT_SECONDARY,
        foreground=TEXT_WHITE,
        font=FONT_BOLD,
        borderwidth=0,
        focusthickness=0,
        focuscolor="none",
        padding=(10, 6),
    )
    style.map(
        "TButton",
        background=[("active", ACCENT_SECONDARY_HOVER), ("pressed", ACCENT_SECONDARY)],
    )

    # Botão Primário (Ações de criação / inclusão)
    style.configure(
        "Primary.TButton",
        background=ACCENT_PRIMARY,
        foreground=TEXT_WHITE,
        font=FONT_BOLD,
        padding=(12, 6),
    )
    style.map(
        "Primary.TButton",
        background=[("active", ACCENT_PRIMARY_HOVER), ("pressed", ACCENT_PRIMARY)],
    )

    # Botão de Sucesso / Checkout
    style.configure(
        "Success.TButton",
        background=ACCENT_SUCCESS,
        foreground=TEXT_WHITE,
        font=FONT_BOLD,
        padding=(14, 7),
    )
    style.map(
        "Success.TButton",
        background=[("active", ACCENT_SUCCESS_HOVER), ("pressed", ACCENT_SUCCESS)],
    )

    # Botão de Perigo / Exclusão (Vermelho)
    style.configure(
        "Danger.TButton",
        background=ACCENT_DANGER,
        foreground=TEXT_WHITE,
        font=FONT_BOLD,
        padding=(10, 6),
    )
    style.map(
        "Danger.TButton",
        background=[("active", ACCENT_DANGER_HOVER), ("pressed", ACCENT_DANGER)],
    )

    # Botão Secundário / Neutro
    style.configure(
        "Secondary.TButton",
        background=BG_SURFACE,
        foreground=TEXT_MAIN,
        font=FONT_BOLD,
        padding=(10, 6),
    )
    style.map(
        "Secondary.TButton",
        background=[("active", BG_HOVER), ("pressed", BG_SURFACE)],
    )

    # -----------------------------------------------------------------
    # NOTEBOOK / ABAS
    # -----------------------------------------------------------------
    style.configure("TNotebook", background=BG_DARK, borderwidth=0)
    style.configure(
        "TNotebook.Tab",
        background=BG_CARD,
        foreground=TEXT_MUTED,
        font=FONT_BOLD,
        padding=[14, 8],
        borderwidth=0,
    )
    style.map(
        "TNotebook.Tab",
        background=[("selected", BG_SURFACE), ("active", BG_HOVER)],
        foreground=[("selected", TEXT_WHITE), ("active", TEXT_WHITE)],
    )

    # -----------------------------------------------------------------
    # TREEVIEW (TABELAS DE DADOS)
    # -----------------------------------------------------------------
    style.configure(
        "Treeview",
        background=BG_ROW_EVEN,
        foreground=TEXT_MAIN,
        fieldbackground=BG_ROW_EVEN,
        font=FONT_MAIN,
        rowheight=26,
        borderwidth=0,
    )
    style.map(
        "Treeview",
        background=[("selected", BG_SELECTED)],
        foreground=[("selected", TEXT_WHITE)],
    )

    style.configure(
        "Treeview.Heading",
        background=BG_SURFACE,
        foreground=TEXT_WHITE,
        font=FONT_BOLD,
        relief="flat",
        padding=[6, 6],
    )
    style.map(
        "Treeview.Heading",
        background=[("active", BG_HOVER)],
    )

    # -----------------------------------------------------------------
    # ENTRADAS E COMBOBOX
    # -----------------------------------------------------------------
    style.configure(
        "TEntry",
        fieldbackground=BG_SURFACE,
        foreground=TEXT_MAIN,
        insertcolor=TEXT_WHITE,
        padding=6,
    )

    style.configure(
        "TCombobox",
        fieldbackground=BG_SURFACE,
        background=BG_SURFACE,
        foreground=TEXT_MAIN,
        arrowcolor=TEXT_MAIN,
        padding=5,
    )
    style.map(
        "TCombobox",
        fieldbackground=[("readonly", BG_SURFACE)],
        selectbackground=[("readonly", BG_SELECTED)],
        selectforeground=[("readonly", TEXT_WHITE)],
    )

    style.configure(
        "TSpinbox",
        fieldbackground=BG_SURFACE,
        background=BG_SURFACE,
        foreground=TEXT_MAIN,
        arrowcolor=TEXT_MAIN,
    )

    # -----------------------------------------------------------------
    # SCROLLBAR
    # -----------------------------------------------------------------
    style.configure(
        "TScrollbar",
        background=BG_SURFACE,
        troughcolor=BG_DARK,
        borderwidth=0,
        arrowcolor=TEXT_MUTED,
    )

    return style
