"""
=====================================================================
Modal de Detalhes do Pedido e Instruções de Entrega
(ui/gui/detalhes_pedido_modal.py)
=====================================================================
Exibe a nota de compra com preços e fretes históricos congelados e as
mensagens polimórficas de entrega (mensagem_entrega) de cada produto.
=====================================================================
"""

from __future__ import annotations
import tkinter as tk
from tkinter import ttk
from typing import Any

from ui.gui.estilos import (
    BG_CARD,
    BG_SURFACE,
    BG_ROW_EVEN,
    BG_ROW_ODD,
    TEXT_WHITE,
    TEXT_MUTED,
    ACCENT_SUCCESS,
    ACCENT_DANGER,
    FONT_TITLE,
    FONT_SUBTITLE,
    FONT_SECTION,
    FONT_BOLD,
    FONT_MONO,
)
from ui.helpers import moeda


class DetalhesPedidoModal(tk.Toplevel):
    """Janela modal para exibição dos dados históricos e instruções de entrega do pedido."""

    def __init__(self, parent: tk.Widget, pedido: Any):
        super().__init__(parent)
        self.pedido = pedido

        self.title(f"Detalhes do Pedido #{pedido.id:04d}")
        self.geometry("680x560")
        self.minsize(620, 500)
        self.configure(bg=BG_CARD)

        self.transient(parent.winfo_toplevel())
        self.grab_set()

        self._construir_interface()
        self.center_window()

    def center_window(self) -> None:
        self.update_idletasks()
        w = self.winfo_width()
        h = self.winfo_height()
        parent_x = self.master.winfo_rootx()
        parent_y = self.master.winfo_rooty()
        parent_w = self.master.winfo_width()
        parent_h = self.master.winfo_height()
        pos_x = parent_x + (parent_w - w) // 2
        pos_y = parent_y + (parent_h - h) // 2
        self.geometry(f"+{pos_x}+{pos_y}")

    def _construir_interface(self) -> None:
        container = ttk.Frame(self, padding=20)
        container.pack(fill=tk.BOTH, expand=True)

        # 1. Cabeçalho do Pedido
        frm_header = ttk.Frame(container)
        frm_header.pack(fill=tk.X, pady=(0, 10))

        cor_status = ACCENT_SUCCESS if self.pedido.status.value == "Confirmado" else ACCENT_DANGER
        lbl_id = ttk.Label(frm_header, text=f"PEDIDO #{self.pedido.id:04d}", font=FONT_TITLE)
        lbl_id.pack(side=tk.LEFT)

        lbl_status = tk.Label(
            frm_header,
            text=f"  ● {self.pedido.status.value.upper()}  ",
            bg=BG_SURFACE,
            fg=cor_status,
            font=FONT_BOLD,
            relief="flat",
            padx=8,
            pady=4,
        )
        lbl_status.pack(side=tk.RIGHT)

        data_str = self.pedido.data_criacao.strftime("%d/%m/%Y às %H:%M:%S")
        ttk.Label(
            container,
            text=f"Realizado em: {data_str} | Cliente: {self.pedido.cliente.nome} ({self.pedido.cliente.email})",
            font=FONT_BOLD,
        ).pack(anchor=tk.W, pady=(0, 2))

        ttk.Label(
            container,
            text=f"Endereço de Entrega Cadastrado: {self.pedido.cliente.endereco}",
            style="Muted.TLabel",
        ).pack(anchor=tk.W, pady=(0, 10))

        # 2. Tabela de Itens Comprados (Preço e Frete Congelados)
        ttk.Label(container, text="Itens Comprados (Preço e Frete Congelados):", font=FONT_SECTION).pack(
            anchor=tk.W, pady=(4, 4)
        )

        tree_frame = ttk.Frame(container)
        tree_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 8))
        tree_frame.columnconfigure(0, weight=1)
        tree_frame.rowconfigure(0, weight=1)

        colunas = ("produto", "tipo", "preco", "qtd", "subtotal", "frete")
        tree = ttk.Treeview(tree_frame, columns=colunas, show="headings", height=4)
        tree.heading("produto", text="Produto")
        tree.heading("tipo", text="Tipo")
        tree.heading("preco", text="Preço Unit.")
        tree.heading("qtd", text="Qtd")
        tree.heading("subtotal", text="Subtotal")
        tree.heading("frete", text="Frete Histórico")

        tree.column("produto", width=220, anchor=tk.W)
        tree.column("tipo", width=70, anchor=tk.CENTER)
        tree.column("preco", width=95, anchor=tk.E)
        tree.column("qtd", width=55, anchor=tk.CENTER)
        tree.column("subtotal", width=95, anchor=tk.E)
        tree.column("frete", width=95, anchor=tk.E)

        tree.tag_configure("even", background=BG_ROW_EVEN)
        tree.tag_configure("odd", background=BG_ROW_ODD)

        for i, item in enumerate(self.pedido.itens):
            tag = "even" if i % 2 == 0 else "odd"
            tree.insert(
                "",
                tk.END,
                values=(
                    item.produto.nome,
                    item.produto.tipo(),
                    moeda(item.preco_unitario),
                    f"{item.quantidade:02d}",
                    moeda(item.subtotal),
                    moeda(item.frete),
                ),
                tags=(tag,),
            )

        scroll = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scroll.set)
        tree.grid(row=0, column=0, sticky="nsew")
        scroll.grid(row=0, column=1, sticky="ns")

        # 3. Resumo Financeiro
        frm_totais = ttk.Frame(container, style="Surface.TFrame", padding=10)
        frm_totais.pack(fill=tk.X, pady=(0, 10))
        frm_totais.columnconfigure(0, weight=1)
        frm_totais.columnconfigure(1, weight=1)

        subtotal_txt = f"Subtotal Produtos: {moeda(self.pedido.subtotal)}"
        ttk.Label(frm_totais, text=subtotal_txt, font=FONT_BOLD).grid(row=0, column=0, sticky="w", pady=1)

        if self.pedido.tem_produto_fisico:
            frete_desc = f"Frete Peso ({moeda(self.pedido.frete_itens)}) + Taxa Única ({moeda(self.pedido.taxa_pedido_fisico)})"
        else:
            frete_desc = "Envio Digital (Isento de Frete)"
        frete_txt = f"Frete Total: {moeda(self.pedido.frete_total)} [{frete_desc}]"
        ttk.Label(frm_totais, text=frete_txt, style="Muted.TLabel").grid(row=1, column=0, sticky="w", pady=1)

        total_txt = f"VALOR TOTAL: {moeda(self.pedido.total)}"
        ttk.Label(frm_totais, text=total_txt, style="ValueTotal.TLabel").grid(row=0, column=1, rowspan=2, sticky="e")

        # 4. Polimorfismo: Instruções de Entrega (mensagem_entrega)
        ttk.Label(
            container,
            text="Instruções de Entrega (Polimorfismo Produto.mensagem_entrega()):",
            font=FONT_SECTION,
        ).pack(anchor=tk.W, pady=(4, 4))

        frm_entrega = ttk.Frame(container, style="Surface.TFrame", padding=10)
        frm_entrega.pack(fill=tk.X, pady=(0, 15))

        for item in self.pedido.itens:
            prod = item.produto
            msg_polimorfica = prod.mensagem_entrega()
            lbl_item = ttk.Label(
                frm_entrega,
                text=f"• [{prod.nome}] ({prod.tipo()}): {msg_polimorfica}",
                font=("Segoe UI", 9),
                wraplength=620,
                justify=tk.LEFT,
            )
            lbl_item.pack(anchor=tk.W, pady=2)

        # 5. Botão Fechar
        btn_fechar = ttk.Button(container, text="Fechar", style="Secondary.TButton", command=self.destroy)
        btn_fechar.pack(side=tk.RIGHT)
