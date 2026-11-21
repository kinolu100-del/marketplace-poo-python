"""
=====================================================================
Tela de Gestão do Carrinho e Checkout (ui/gui/carrinho_view.py)
=====================================================================
Permite gerenciar a cesta de compras por cliente em tempo real com
persistência relacional imediata e janela modal de checkout atômico.
=====================================================================
"""

from __future__ import annotations
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from typing import Optional, Any

from ui.gui.estilos import (
    BG_CARD,
    BG_SURFACE,
    BG_ROW_EVEN,
    BG_ROW_ODD,
    FONT_BOLD,
    FONT_SUBTITLE,
    FONT_SECTION,
    FONT_MAIN,
)
from ui.gui.formatters import formatar_item_carrinho_tabela
from ui.gui.validators import validar_quantidade_carrinho
from ui.gui.detalhes_pedido_modal import DetalhesPedidoModal
from ui.helpers import moeda, calcular_resumo_frete
from exceptions import MarketplaceError


class FinalizarCompraModal(tk.Toplevel):
    """Janela modal de prévia consolidada de frete e confirmação de compra."""

    def __init__(self, parent: tk.Widget, cliente: Any, pedido_service: Any, gui_app: Any, on_success: Any):
        super().__init__(parent)
        self.cliente = cliente
        self.pedido_service = pedido_service
        self.gui_app = gui_app
        self.on_success = on_success

        self.title("Revisão e Finalização do Pedido")
        self.geometry("640x520")
        self.minsize(580, 460)
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

        ttk.Label(container, text="Revisão Final da Compra", font=FONT_SUBTITLE).pack(anchor=tk.W, pady=(0, 6))

        # Dados do Destinatário
        frm_dest = ttk.Frame(container, style="Surface.TFrame", padding=10)
        frm_dest.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(
            frm_dest,
            text=f"Destinatário: {self.cliente.nome} | E-mail: {self.cliente.email}",
            font=FONT_BOLD,
        ).pack(anchor=tk.W)
        ttk.Label(
            frm_dest,
            text=f"Endereço de Entrega: {self.cliente.endereco}",
            style="Muted.TLabel",
        ).pack(anchor=tk.W, pady=(2, 0))

        # Tabela de Itens
        ttk.Label(container, text="Itens da Cesta:", font=FONT_SECTION).pack(anchor=tk.W, pady=(4, 2))

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
        tree.heading("frete", text="Frete Variável")

        tree.column("produto", width=200, anchor=tk.W)
        tree.column("tipo", width=70, anchor=tk.CENTER)
        tree.column("preco", width=90, anchor=tk.E)
        tree.column("qtd", width=50, anchor=tk.CENTER)
        tree.column("subtotal", width=90, anchor=tk.E)
        tree.column("frete", width=90, anchor=tk.E)

        tree.tag_configure("even", background=BG_ROW_EVEN)
        tree.tag_configure("odd", background=BG_ROW_ODD)

        resumo = calcular_resumo_frete(self.cliente.carrinho)
        for i, item_det in enumerate(resumo.itens):
            tag = "even" if i % 2 == 0 else "odd"
            tree.insert(
                "",
                tk.END,
                values=(
                    item_det.nome,
                    item_det.tipo,
                    moeda(item_det.preco_unitario),
                    f"{item_det.quantidade:02d}",
                    moeda(item_det.subtotal),
                    moeda(item_det.frete),
                ),
                tags=(tag,),
            )

        scroll = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scroll.set)
        tree.grid(row=0, column=0, sticky="nsew")
        scroll.grid(row=0, column=1, sticky="ns")

        # Resumo Financeiro Consolidado
        frm_financeiro = ttk.Frame(container, style="Surface.TFrame", padding=12)
        frm_financeiro.pack(fill=tk.X, pady=(0, 15))
        frm_financeiro.columnconfigure(0, weight=1)
        frm_financeiro.columnconfigure(1, weight=1)

        ttk.Label(frm_financeiro, text=f"Subtotal dos Produtos: {moeda(resumo.subtotal_produtos)}", font=FONT_BOLD).grid(
            row=0, column=0, sticky="w", pady=2
        )
        if resumo.tem_produto_fisico:
            lbl_frete_detalhe = (
                f"Frete Peso ({moeda(resumo.frete_variavel)}) + Taxa Única de Pedido Físico ({moeda(resumo.taxa_fixa_pedido)})"
            )
        else:
            lbl_frete_detalhe = "Produtos Digitais (Frete Zero)"
        ttk.Label(frm_financeiro, text=f"Frete Total: {moeda(resumo.frete_total)} ({lbl_frete_detalhe})", style="Muted.TLabel").grid(
            row=1, column=0, sticky="w", pady=2
        )

        ttk.Label(
            frm_financeiro,
            text=f"TOTAL: {moeda(resumo.total_estimado)}",
            style="ValueTotal.TLabel",
        ).grid(row=0, column=1, rowspan=2, sticky="e")

        # Botões
        frm_botoes = ttk.Frame(container)
        frm_botoes.pack(fill=tk.X, side=tk.BOTTOM)

        btn_cancelar = ttk.Button(frm_botoes, text="Cancelar", style="Secondary.TButton", command=self.destroy)
        btn_cancelar.pack(side=tk.RIGHT, padx=(8, 0))

        btn_confirmar = ttk.Button(
            frm_botoes, text="✅ Confirmar e Finalizar Pedido", style="Success.TButton", command=self._confirmar
        )
        btn_confirmar.pack(side=tk.RIGHT)

    def _confirmar(self) -> None:
        try:
            pedido = self.pedido_service.finalizar_pedido(self.cliente.id)
            self.destroy()

            # Notifica sucesso
            self.gui_app.definir_status(f"Pedido #{pedido.id:04d} finalizado com sucesso!")
            if self.on_success:
                self.on_success(pedido)

            # Abre automaticamente a tela com as instruções polimórficas de entrega
            DetalhesPedidoModal(self.master, pedido)

        except MarketplaceError as erro:
            messagebox.showerror("Erro na Finalização", str(erro), parent=self)
        except Exception as erro:
            messagebox.showerror("Erro Operacional", f"Falha ao concluir compra: {erro}", parent=self)


class CarrinhoView(ttk.Frame):
    """Painel principal da aba de Gestão de Carrinho de Compras."""

    def __init__(
        self,
        parent: tk.Widget,
        pedido_service: Any,
        usuario_service: Any,
        produto_service: Any,
        gui_app: Any,
    ):
        super().__init__(parent)
        self.pedido_service = pedido_service
        self.usuario_service = usuario_service
        self.produto_service = produto_service
        self.gui_app = gui_app

        self._cliente_selecionado_var = tk.StringVar()
        self._clientes_map: dict[str, int] = {}

        self._produto_adicionar_var = tk.StringVar()
        self._produtos_map: dict[str, int] = {}
        self._qtd_adicionar_var = tk.StringVar(value="1")

        # Labels de resumo
        self._lbl_subtotal_var = tk.StringVar(value="R$ 0,00")
        self._lbl_frete_var = tk.StringVar(value="R$ 0,00")
        self._lbl_taxa_var = tk.StringVar(value="R$ 0,00")
        self._lbl_total_var = tk.StringVar(value="R$ 0,00")

        self._construir_interface()
        self.carregar_dados()

    def _construir_interface(self) -> None:
        self.columnconfigure(0, weight=3)
        self.columnconfigure(1, weight=2)
        self.rowconfigure(1, weight=1)

        # 1. Seletor de Cliente no Topo
        top_bar = ttk.Frame(self, style="Surface.TFrame", padding=(12, 10))
        top_bar.grid(row=0, column=0, columnspan=2, sticky="ew", padx=12, pady=(10, 8))

        ttk.Label(top_bar, text="Cliente Ativo:*", font=FONT_SECTION).pack(side=tk.LEFT, padx=(0, 8))
        self.cb_cliente = ttk.Combobox(
            top_bar,
            textvariable=self._cliente_selecionado_var,
            state="readonly",
            width=36,
            font=("Segoe UI", 9),
        )
        self.cb_cliente.pack(side=tk.LEFT, padx=(0, 10))
        self.cb_cliente.bind("<<ComboboxSelected>>", lambda e: self._ao_mudar_cliente())

        btn_atualizar_clientes = ttk.Button(
            top_bar, text="🔄 Atualizar Lista", style="Secondary.TButton", command=self.carregar_dados
        )
        btn_atualizar_clientes.pack(side=tk.LEFT, padx=4)

        # 2. Painel Esquerdo: Tabela de Itens no Carrinho
        frm_esquerda = ttk.Frame(self, padding=(12, 0, 6, 10))
        frm_esquerda.grid(row=1, column=0, sticky="nsew")
        frm_esquerda.columnconfigure(0, weight=1)
        frm_esquerda.rowconfigure(1, weight=1)

        self.lbl_titulo_carrinho = ttk.Label(frm_esquerda, text="Itens no Carrinho:", font=FONT_SECTION)
        self.lbl_titulo_carrinho.grid(row=0, column=0, sticky="w", pady=(0, 6))

        tree_container = ttk.Frame(frm_esquerda)
        tree_container.grid(row=1, column=0, sticky="nsew")
        tree_container.columnconfigure(0, weight=1)
        tree_container.rowconfigure(0, weight=1)

        colunas = ("id", "nome", "tipo", "preco", "qtd", "subtotal", "estoque")
        self.tree = ttk.Treeview(tree_container, columns=colunas, show="headings", selectmode="browse")

        self.tree.heading("id", text="ID")
        self.tree.heading("nome", text="Produto")
        self.tree.heading("tipo", text="Tipo")
        self.tree.heading("preco", text="Preço Unit.")
        self.tree.heading("qtd", text="Qtd")
        self.tree.heading("subtotal", text="Subtotal")
        self.tree.heading("estoque", text="Estoque Disp.")

        self.tree.column("id", width=45, anchor=tk.CENTER)
        self.tree.column("nome", width=170, anchor=tk.W)
        self.tree.column("tipo", width=65, anchor=tk.CENTER)
        self.tree.column("preco", width=85, anchor=tk.E)
        self.tree.column("qtd", width=50, anchor=tk.CENTER)
        self.tree.column("subtotal", width=85, anchor=tk.E)
        self.tree.column("estoque", width=80, anchor=tk.CENTER)

        self.tree.tag_configure("even", background=BG_ROW_EVEN)
        self.tree.tag_configure("odd", background=BG_ROW_ODD)

        scroll_y = ttk.Scrollbar(tree_container, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll_y.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        scroll_y.grid(row=0, column=1, sticky="ns")

        # Botões de gestão de itens do carrinho
        toolbar_carrinho = ttk.Frame(frm_esquerda, padding=(0, 8))
        toolbar_carrinho.grid(row=2, column=0, sticky="ew")

        btn_alterar_qtd = ttk.Button(
            toolbar_carrinho, text="✏️ Alterar Quantidade", style="Secondary.TButton", command=self._alterar_quantidade
        )
        btn_alterar_qtd.pack(side=tk.LEFT, padx=(0, 6))

        btn_remover_item = ttk.Button(
            toolbar_carrinho, text="❌ Remover Item", style="Danger.TButton", command=self._remover_item
        )
        btn_remover_item.pack(side=tk.LEFT, padx=(0, 6))

        btn_limpar = ttk.Button(
            toolbar_carrinho, text="🗑️ Limpar Carrinho", style="Secondary.TButton", command=self._limpar_carrinho
        )
        btn_limpar.pack(side=tk.RIGHT)

        # 3. Painel Direito: Adição de Produtos e Resumo de Frete
        frm_direita = ttk.Frame(self, padding=(6, 0, 12, 10))
        frm_direita.grid(row=1, column=1, sticky="nsew")
        frm_direita.columnconfigure(0, weight=1)

        # Card: Adicionar Produto
        card_add = ttk.Frame(frm_direita, style="Card.TFrame", padding=12)
        card_add.pack(fill=tk.X, pady=(0, 12))

        ttk.Label(card_add, text="Adicionar Produto ao Carrinho", font=FONT_SECTION).pack(anchor=tk.W, pady=(0, 6))

        ttk.Label(card_add, text="Selecione o Produto do Catálogo:", font=FONT_BOLD).pack(anchor=tk.W, pady=(2, 2))
        self.cb_produtos = ttk.Combobox(
            card_add,
            textvariable=self._produto_adicionar_var,
            state="readonly",
            font=("Segoe UI", 9),
        )
        self.cb_produtos.pack(fill=tk.X, pady=(0, 6))

        frm_qtd_btn = ttk.Frame(card_add)
        frm_qtd_btn.pack(fill=tk.X, pady=(2, 0))

        ttk.Label(frm_qtd_btn, text="Qtd:", font=FONT_BOLD).pack(side=tk.LEFT, padx=(0, 4))
        self.sp_qtd = ttk.Spinbox(
            frm_qtd_btn,
            from_=1,
            to=999,
            textvariable=self._qtd_adicionar_var,
            width=6,
            font=("Segoe UI", 9),
        )
        self.sp_qtd.pack(side=tk.LEFT, padx=(0, 8))

        btn_adicionar = ttk.Button(
            frm_qtd_btn, text="➕ Adicionar", style="Primary.TButton", command=self._adicionar_ao_carrinho
        )
        btn_adicionar.pack(side=tk.RIGHT, fill=tk.X, expand=True)

        # Card: Resumo em Tempo Real e Botão Finalizar
        card_resumo = ttk.Frame(frm_direita, style="Card.TFrame", padding=14)
        card_resumo.pack(fill=tk.BOTH, expand=True)

        ttk.Label(card_resumo, text="Resumo da Compra (Tempo Real)", font=FONT_SECTION).pack(anchor=tk.W, pady=(0, 8))

        # Linhas de Valores
        self._criar_linha_resumo(card_resumo, "Subtotal Produtos:", self._lbl_subtotal_var)
        self._criar_linha_resumo(card_resumo, "Frete Variável (Peso):", self._lbl_frete_var)
        self._criar_linha_resumo(card_resumo, "Taxa Fixa Pedido Físico:", self._lbl_taxa_var)
        ttk.Separator(card_resumo, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=8)
        self._criar_linha_resumo(card_resumo, "TOTAL ESTIMADO:", self._lbl_total_var, destaque=True)

        self.btn_finalizar = ttk.Button(
            card_resumo,
            text="🚀 Finalizar Compra...",
            style="Success.TButton",
            command=self._abrir_finalizar_compra,
        )
        self.btn_finalizar.pack(fill=tk.X, side=tk.BOTTOM, pady=(15, 0))

    def _criar_linha_resumo(self, parent: tk.Widget, label: str, var: tk.StringVar, destaque: bool = False) -> None:
        frm = ttk.Frame(parent)
        frm.pack(fill=tk.X, pady=2)
        font_lbl = FONT_SUBTITLE if destaque else FONT_MAIN
        ttk.Label(frm, text=label, font=font_lbl).pack(side=tk.LEFT)
        style_val = "ValueTotal.TLabel" if destaque else "TLabel"
        ttk.Label(frm, textvariable=var, style=style_val).pack(side=tk.RIGHT)

    def _obter_cliente_atual(self) -> Optional[Any]:
        chave = self._cliente_selecionado_var.get()
        cid = self._clientes_map.get(chave)
        if cid is None:
            return None
        return self.usuario_service.buscar_por_id(cid)

    def _ao_mudar_cliente(self) -> None:
        cliente = self._obter_cliente_atual()
        if cliente:
            self.lbl_titulo_carrinho.configure(text=f"Itens no Carrinho de {cliente.nome}:")
        else:
            self.lbl_titulo_carrinho.configure(text="Itens no Carrinho:")
        self.atualizar_tabela_carrinho()

    def carregar_dados(self) -> None:
        """Carrega clientes e produtos disponíveis."""
        # Clientes
        clientes = self.usuario_service.listar_clientes()
        self._clientes_map = {f"{c.nome} (#{c.id}) - {c.email}": c.id for c in clientes}
        opcoes_clientes = list(self._clientes_map.keys())
        self.cb_cliente["values"] = opcoes_clientes

        if opcoes_clientes:
            if self._cliente_selecionado_var.get() not in opcoes_clientes:
                self._cliente_selecionado_var.set(opcoes_clientes[0])
        else:
            self._cliente_selecionado_var.set("")

        # Produtos
        produtos = self.produto_service.listar_produtos()
        self._produtos_map = {
            f"{p.nome} ({p.tipo()}) - {moeda(p.preco)} [Disp: {p.estoque}]": p.id
            for p in produtos
            if p.estoque > 0
        }
        opcoes_produtos = list(self._produtos_map.keys())
        self.cb_produtos["values"] = opcoes_produtos
        if opcoes_produtos:
            self._produto_adicionar_var.set(opcoes_produtos[0])
        else:
            self._produto_adicionar_var.set("")

        self._ao_mudar_cliente()

    def atualizar_tabela_carrinho(self) -> None:
        """Recarrega os itens do carrinho do cliente atual e recalcula o frete em tempo real."""
        cliente = self._obter_cliente_atual()

        for item in self.tree.get_children():
            self.tree.delete(item)

        if not cliente:
            self._lbl_subtotal_var.set("R$ 0,00")
            self._lbl_frete_var.set("R$ 0,00")
            self._lbl_taxa_var.set("R$ 0,00")
            self._lbl_total_var.set("R$ 0,00")
            self.btn_finalizar.configure(state="disabled")
            return

        carrinho = cliente.carrinho
        itens = carrinho.itens

        for i, item in enumerate(itens):
            tag = "even" if i % 2 == 0 else "odd"
            valores = formatar_item_carrinho_tabela(item)
            self.tree.insert("", tk.END, iid=str(item.produto.id), values=valores, tags=(tag,))

        if carrinho.esta_vazio():
            self._lbl_subtotal_var.set("R$ 0,00")
            self._lbl_frete_var.set("R$ 0,00")
            self._lbl_taxa_var.set("R$ 0,00")
            self._lbl_total_var.set("R$ 0,00")
            self.btn_finalizar.configure(state="disabled")
        else:
            resumo = calcular_resumo_frete(carrinho)
            self._lbl_subtotal_var.set(moeda(resumo.subtotal_produtos))
            self._lbl_frete_var.set(moeda(resumo.frete_variavel))
            self._lbl_taxa_var.set(moeda(resumo.taxa_fixa_pedido))
            self._lbl_total_var.set(moeda(resumo.total_estimado))
            self.btn_finalizar.configure(state="normal")

    def _obter_produto_id_selecionado(self) -> Optional[int]:
        sel = self.tree.selection()
        if not sel:
            return None
        try:
            return int(sel[0])
        except ValueError:
            return None

    def _adicionar_ao_carrinho(self) -> None:
        cliente = self._obter_cliente_atual()
        if not cliente:
            messagebox.showwarning("Atenção", "Selecione um cliente ativo para adicionar itens ao carrinho.", parent=self)
            return

        prod_txt = self._produto_adicionar_var.get()
        pid = self._produtos_map.get(prod_txt)
        if pid is None:
            messagebox.showwarning("Atenção", "Selecione um produto da lista para adicionar.", parent=self)
            return

        produto = self.produto_service.buscar_por_id(pid)
        if not produto:
            return

        valido, msg_erro, qtd = validar_quantidade_carrinho(self._qtd_adicionar_var.get(), produto.estoque)
        if not valido or qtd is None:
            messagebox.showwarning("Aviso de Validação", msg_erro, parent=self)
            return

        try:
            self.pedido_service.adicionar_ao_carrinho(cliente.id, pid, qtd)
            self.atualizar_tabela_carrinho()
            self.gui_app.definir_status(f"Item '{produto.nome}' x{qtd} adicionado ao carrinho de {cliente.nome}.")
        except MarketplaceError as erro:
            messagebox.showerror("Erro de Estoque / Negócio", str(erro), parent=self)

    def _alterar_quantidade(self) -> None:
        cliente = self._obter_cliente_atual()
        if not cliente:
            return

        pid = self._obter_produto_id_selecionado()
        if pid is None:
            messagebox.showinfo("Seleção", "Selecione um item no carrinho para alterar a quantidade.", parent=self)
            return

        produto = self.produto_service.buscar_por_id(pid)
        if not produto:
            return

        qtd_atual = cliente.carrinho.quantidade_de(produto)
        if qtd_atual <= 0:
            return

        nova_qtd_str = simpledialog.askstring(
            "Alterar Quantidade",
            f"Informe a nova quantidade para '{produto.nome}'\n(Estoque disponível no catálogo: {produto.estoque}):",
            initialvalue=str(qtd_atual),
            parent=self,
        )
        if nova_qtd_str is None:
            return

        valido, msg_erro, nova_qtd = validar_quantidade_carrinho(nova_qtd_str, produto.estoque)
        if not valido or nova_qtd is None:
            messagebox.showwarning("Validação", msg_erro, parent=self)
            return

        try:
            self.pedido_service.alterar_quantidade_carrinho(cliente.id, pid, nova_qtd)
            self.atualizar_tabela_carrinho()
            self.gui_app.definir_status(f"Quantidade de '{produto.nome}' alterada para {nova_qtd}.")
        except MarketplaceError as erro:
            messagebox.showerror("Erro", str(erro), parent=self)

    def _remover_item(self) -> None:
        cliente = self._obter_cliente_atual()
        if not cliente:
            return

        pid = self._obter_produto_id_selecionado()
        if pid is None:
            messagebox.showinfo("Seleção", "Selecione um item no carrinho para remover.", parent=self)
            return

        produto = self.produto_service.buscar_por_id(pid)
        if not produto:
            return

        confirma = messagebox.askyesno(
            "Confirmar Remoção", f"Remover '{produto.nome}' do carrinho de compras?", parent=self
        )
        if not confirma:
            return

        try:
            self.pedido_service.remover_do_carrinho(cliente.id, pid)
            self.atualizar_tabela_carrinho()
            self.gui_app.definir_status(f"'{produto.nome}' removido do carrinho.")
        except MarketplaceError as erro:
            messagebox.showerror("Erro", str(erro), parent=self)

    def _limpar_carrinho(self) -> None:
        cliente = self._obter_cliente_atual()
        if not cliente or cliente.carrinho.esta_vazio():
            messagebox.showinfo("Aviso", "O carrinho já está vazio.", parent=self)
            return

        confirma = messagebox.askyesno(
            "Esvaziar Carrinho",
            f"Deseja realmente esvaziar todos os itens do carrinho de '{cliente.nome}'?",
            parent=self,
        )
        if not confirma:
            return

        self.pedido_service.limpar_carrinho(cliente.id)
        self.atualizar_tabela_carrinho()
        self.gui_app.definir_status(f"Carrinho de {cliente.nome} esvaziado.")

    def _abrir_finalizar_compra(self) -> None:
        cliente = self._obter_cliente_atual()
        if not cliente or cliente.carrinho.esta_vazio():
            messagebox.showwarning("Aviso", "Não é possível finalizar uma compra com o carrinho vazio.", parent=self)
            return

        FinalizarCompraModal(
            parent=self,
            cliente=cliente,
            pedido_service=self.pedido_service,
            gui_app=self.gui_app,
            on_success=self._ao_concluir_pedido,
        )

    def _ao_concluir_pedido(self, pedido: Any) -> None:
        """Callback executado após checkout com sucesso."""
        self.atualizar_tabela_carrinho()
        self.gui_app.atualizar_todas_as_abas()
