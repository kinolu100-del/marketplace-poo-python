"""
=====================================================================
Tela de Gestão de Pedidos e Vendas (ui/gui/pedidos_view.py)
=====================================================================
Permite visualização do histórico de pedidos, filtragem por cliente
e status, cancelamento atômico com reposição de estoque e inspeção de
instruções polimórficas de entrega.
=====================================================================
"""

from __future__ import annotations
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, Any

from ui.gui.estilos import (
    BG_CARD,
    BG_ROW_EVEN,
    BG_ROW_ODD,
    ACCENT_SUCCESS,
    ACCENT_DANGER,
    FONT_SECTION,
)
from ui.gui.formatters import formatar_pedido_tabela
from ui.gui.detalhes_pedido_modal import DetalhesPedidoModal
from exceptions import MarketplaceError


class PedidosView(ttk.Frame):
    """Painel principal da aba de Gestão de Pedidos e Vendas."""

    def __init__(
        self,
        parent: tk.Widget,
        pedido_service: Any,
        usuario_service: Any,
        gui_app: Any,
    ):
        super().__init__(parent)
        self.pedido_service = pedido_service
        self.usuario_service = usuario_service
        self.gui_app = gui_app

        self._filtro_cliente_var = tk.StringVar(value="Todos os Clientes")
        self._filtro_status_var = tk.StringVar(value="Todos")
        self._clientes_map: dict[str, int] = {}

        self._construir_interface()
        self.carregar_dados()

    def _construir_interface(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        # 1. Barra Superior de Ferramentas e Filtros
        toolbar = ttk.Frame(self, padding=(12, 10))
        toolbar.grid(row=0, column=0, sticky="ew")

        # Filtro de Clientes
        ttk.Label(toolbar, text="Cliente:", font=FONT_SECTION).pack(side=tk.LEFT, padx=(0, 4))
        self.cb_clientes = ttk.Combobox(
            toolbar,
            textvariable=self._filtro_cliente_var,
            state="readonly",
            width=24,
        )
        self.cb_clientes.pack(side=tk.LEFT, padx=(0, 10))
        self.cb_clientes.bind("<<ComboboxSelected>>", lambda e: self.carregar_dados())

        # Filtro de Status
        ttk.Label(toolbar, text="Status:", font=FONT_SECTION).pack(side=tk.LEFT, padx=(0, 4))
        cb_status = ttk.Combobox(
            toolbar,
            textvariable=self._filtro_status_var,
            values=["Todos", "Confirmado", "Cancelado"],
            state="readonly",
            width=12,
        )
        cb_status.pack(side=tk.LEFT, padx=(0, 16))
        cb_status.bind("<<ComboboxSelected>>", lambda e: self.carregar_dados())

        # Botões de Ação
        btn_detalhes = ttk.Button(
            toolbar, text="👁️ Ver Detalhes e Entrega", style="Primary.TButton", command=self._abrir_detalhes
        )
        btn_detalhes.pack(side=tk.LEFT, padx=4)

        btn_cancelar = ttk.Button(
            toolbar, text="⛔ Cancelar Pedido", style="Danger.TButton", command=self._cancelar_pedido
        )
        btn_cancelar.pack(side=tk.LEFT, padx=4)

        btn_atualizar = ttk.Button(
            toolbar, text="🔄 Atualizar", style="Secondary.TButton", command=self.carregar_dados
        )
        btn_atualizar.pack(side=tk.RIGHT, padx=4)

        # 2. Área Central com Treeview
        tree_container = ttk.Frame(self, padding=(12, 0, 12, 10))
        tree_container.grid(row=1, column=0, sticky="nsew")
        tree_container.columnconfigure(0, weight=1)
        tree_container.rowconfigure(0, weight=1)

        colunas = ("id", "data", "cliente", "itens", "subtotal", "frete", "total", "status")
        self.tree = ttk.Treeview(tree_container, columns=colunas, show="headings", selectmode="browse")

        self.tree.heading("id", text="ID Pedido")
        self.tree.heading("data", text="Data / Horário")
        self.tree.heading("cliente", text="Cliente Comprador")
        self.tree.heading("itens", text="Qtd Itens")
        self.tree.heading("subtotal", text="Subtotal")
        self.tree.heading("frete", text="Frete Total")
        self.tree.heading("total", text="Total Geral")
        self.tree.heading("status", text="Status")

        self.tree.column("id", width=70, anchor=tk.CENTER)
        self.tree.column("data", width=130, anchor=tk.CENTER)
        self.tree.column("cliente", width=180, anchor=tk.W)
        self.tree.column("itens", width=130, anchor=tk.CENTER)
        self.tree.column("subtotal", width=100, anchor=tk.E)
        self.tree.column("frete", width=95, anchor=tk.E)
        self.tree.column("total", width=110, anchor=tk.E)
        self.tree.column("status", width=95, anchor=tk.CENTER)

        self.tree.tag_configure("even", background=BG_ROW_EVEN)
        self.tree.tag_configure("odd", background=BG_ROW_ODD)
        self.tree.tag_configure("status_confirmado", foreground=ACCENT_SUCCESS)
        self.tree.tag_configure("status_cancelado", foreground=ACCENT_DANGER)

        scroll_y = ttk.Scrollbar(tree_container, orient=tk.VERTICAL, command=self.tree.yview)
        scroll_x = ttk.Scrollbar(tree_container, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        scroll_y.grid(row=0, column=1, sticky="ns")
        scroll_x.grid(row=1, column=0, sticky="ew")

        self.tree.bind("<Double-1>", lambda e: self._abrir_detalhes())

    def carregar_dados(self) -> None:
        """Carrega e filtra a listagem histórica de pedidos."""
        # Atualiza opções de clientes
        clientes = self.usuario_service.listar_clientes()
        self._clientes_map = {f"{c.nome} [#{c.id}]": c.id for c in clientes}
        opcoes_clientes = ["Todos os Clientes"] + list(self._clientes_map.keys())
        self.cb_clientes["values"] = opcoes_clientes
        if self._filtro_cliente_var.get() not in opcoes_clientes:
            self._filtro_cliente_var.set("Todos os Clientes")

        cliente_sel = self._filtro_cliente_var.get()
        if cliente_sel != "Todos os Clientes" and cliente_sel in self._clientes_map:
            cid = self._clientes_map[cliente_sel]
            pedidos = self.pedido_service.listar_pedidos_cliente(cid)
        else:
            pedidos = self.pedido_service.listar_pedidos()

        # Filtro de Status
        status_sel = self._filtro_status_var.get()
        if status_sel != "Todos":
            pedidos = [p for p in pedidos if p.status.value == status_sel]

        for item in self.tree.get_children():
            self.tree.delete(item)

        for i, ped in enumerate(pedidos):
            tag_zebra = "even" if i % 2 == 0 else "odd"
            tag_status = "status_confirmado" if ped.status.value == "Confirmado" else "status_cancelado"
            valores = formatar_pedido_tabela(ped)
            self.tree.insert("", tk.END, iid=str(ped.id), values=valores, tags=(tag_zebra, tag_status))

        self.gui_app.definir_status(f"Histórico de pedidos atualizado ({len(pedidos)} registros).")

    def _obter_id_selecionado(self) -> Optional[int]:
        sel = self.tree.selection()
        if not sel:
            return None
        try:
            return int(sel[0])
        except ValueError:
            return None

    def _abrir_detalhes(self) -> None:
        pid = self._obter_id_selecionado()
        if pid is None:
            messagebox.showinfo("Seleção", "Selecione um pedido na tabela para visualizar detalhes.", parent=self)
            return

        pedido = self.pedido_service.buscar_por_id(pid)
        if pedido:
            DetalhesPedidoModal(self, pedido)

    def _cancelar_pedido(self) -> None:
        pid = self._obter_id_selecionado()
        if pid is None:
            messagebox.showinfo("Seleção", "Selecione um pedido na tabela para cancelar.", parent=self)
            return

        pedido = self.pedido_service.buscar_por_id(pid)
        if not pedido:
            return

        if pedido.status.value == "Cancelado":
            messagebox.showinfo("Aviso", f"O Pedido #{pedido.id:04d} já se encontra cancelado.", parent=self)
            return

        confirma = messagebox.askyesno(
            "Confirmar Cancelamento",
            f"Deseja realmente cancelar o Pedido #{pedido.id:04d}?\n\n"
            "• O status será alterado para Cancelado.\n"
            "• O saldo em estoque de todos os produtos comprados será estornado no banco na mesma transação atômica.",
            parent=self,
        )
        if not confirma:
            return

        try:
            self.pedido_service.cancelar_pedido(pid)
            self.carregar_dados()
            self.gui_app.atualizar_todas_as_abas()
            self.gui_app.definir_status(f"Pedido #{pid:04d} cancelado e estoque estornado.")
            messagebox.showinfo(
                "Cancelamento Concluído",
                f"Pedido #{pid:04d} cancelado com sucesso!\nO estoque dos produtos comprados foi devolvido ao catálogo.",
                parent=self,
            )
        except MarketplaceError as erro:
            messagebox.showerror("Erro no Cancelamento", str(erro), parent=self)
        except Exception as erro:
            messagebox.showerror("Erro Operacional", f"Falha ao cancelar pedido: {erro}", parent=self)
