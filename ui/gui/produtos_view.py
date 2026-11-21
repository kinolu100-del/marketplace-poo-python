"""
=====================================================================
Tela de Gestão de Catálogo de Produtos (ui/gui/produtos_view.py)
=====================================================================
Permite visualização, filtragem, cadastro polimórfico (Físico/Digital),
edição de preços/estoque e exclusão protegida de produtos.
=====================================================================
"""

from __future__ import annotations
from decimal import Decimal
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, Callable, Any, List

from ui.gui.estilos import (
    BG_DARK,
    BG_CARD,
    BG_ROW_EVEN,
    BG_ROW_ODD,
    FONT_BOLD,
    FONT_SUBTITLE,
    FONT_SECTION,
)
from ui.gui.formatters import formatar_produto_tabela
from ui.gui.validators import validar_dados_produto
from exceptions import MarketplaceError


class ProdutoModal(tk.Toplevel):
    """Janela modal para cadastro polimórfico ou edição de produto."""

    def __init__(
        self,
        parent: tk.Widget,
        produto_service: Any,
        usuario_service: Any,
        produto_edicao: Optional[Any] = None,
        on_success: Optional[Callable[[], None]] = None,
    ):
        super().__init__(parent)
        self.produto_service = produto_service
        self.usuario_service = usuario_service
        self.produto_edicao = produto_edicao
        self.on_success = on_success

        self.eh_edicao = produto_edicao is not None
        titulo_janela = "Editar Produto" if self.eh_edicao else "Novo Produto"
        self.title(titulo_janela)
        self.geometry("520x490")
        self.minsize(480, 440)
        self.configure(bg=BG_CARD)

        self.transient(parent.winfo_toplevel())
        self.grab_set()

        self._tipo_var = tk.StringVar(value="Físico")
        self._vendedor_var = tk.StringVar()
        self._vendedores_map: dict[str, int] = {}

        self._nome_var = tk.StringVar()
        self._preco_var = tk.StringVar()
        self._estoque_var = tk.StringVar()
        self._peso_var = tk.StringVar()
        self._tamanho_var = tk.StringVar()
        self._link_var = tk.StringVar()

        if self.eh_edicao:
            self._tipo_var.set(self.produto_edicao.tipo())
            self._nome_var.set(self.produto_edicao.nome)
            self._preco_var.set(f"{self.produto_edicao.preco:.2f}")
            self._estoque_var.set(str(self.produto_edicao.estoque))
            if self.produto_edicao.tipo() == "Físico":
                self._peso_var.set(f"{self.produto_edicao.peso_kg:.2f}")
            else:
                self._tamanho_var.set(f"{self.produto_edicao.tamanho_mb:.1f}")
                self._link_var.set(self.produto_edicao.link_download)

        self._construir_interface()
        self._alternar_campos_por_tipo()
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

        titulo_texto = (
            f"Editar Produto #{self.produto_edicao.id:03d} - {self.produto_edicao.nome}"
            if self.eh_edicao
            else "Cadastrar Novo Produto"
        )
        ttk.Label(container, text=titulo_texto, font=FONT_SUBTITLE).pack(anchor=tk.W, pady=(0, 12))

        # Se for cadastro, seleciona vendedor e tipo
        if not self.eh_edicao:
            # Vendedor
            ttk.Label(container, text="Vendedor Responsável:*", font=FONT_BOLD).pack(anchor=tk.W, pady=(2, 2))
            vendedores = self.usuario_service.listar_vendedores()
            self._vendedores_map = {f"{v.nome} ({getattr(v, 'nome_loja', 'Loja')}) [#{v.id}]": v.id for v in vendedores}
            valores_vendedores = list(self._vendedores_map.keys())
            if valores_vendedores:
                self._vendedor_var.set(valores_vendedores[0])

            cb_vendedor = ttk.Combobox(
                container,
                textvariable=self._vendedor_var,
                values=valores_vendedores,
                state="readonly",
                font=("Segoe UI", 9),
            )
            cb_vendedor.pack(fill=tk.X, pady=(0, 8))

            # Tipo Polimórfico
            frm_tipo = ttk.Frame(container)
            frm_tipo.pack(fill=tk.X, pady=(2, 8))
            ttk.Label(frm_tipo, text="Tipo de Produto:*", font=FONT_BOLD).pack(side=tk.LEFT, padx=(0, 10))
            ttk.Radiobutton(
                frm_tipo,
                text="Físico (com frete por peso)",
                value="Físico",
                variable=self._tipo_var,
                command=self._alternar_campos_por_tipo,
            ).pack(side=tk.LEFT, padx=6)
            ttk.Radiobutton(
                frm_tipo,
                text="Digital (download imediato)",
                value="Digital",
                variable=self._tipo_var,
                command=self._alternar_campos_por_tipo,
            ).pack(side=tk.LEFT, padx=6)

            # Nome
            ttk.Label(container, text="Nome do Produto:*", font=FONT_BOLD).pack(anchor=tk.W, pady=(4, 2))
            self.ent_nome = ttk.Entry(container, textvariable=self._nome_var, font=("Segoe UI", 9))
            self.ent_nome.pack(fill=tk.X, pady=(0, 6))
        else:
            # Em edição, mostra dados fixos
            info_txt = (
                f"Vendedor: {self.produto_edicao.vendedor.nome} | "
                f"Tipo: {self.produto_edicao.tipo()}"
            )
            ttk.Label(container, text=info_txt, font=FONT_SECTION).pack(anchor=tk.W, pady=(0, 10))

        # Preço e Estoque lado a lado
        frm_duplo = ttk.Frame(container)
        frm_duplo.pack(fill=tk.X, pady=(4, 6))
        frm_duplo.columnconfigure(0, weight=1)
        frm_duplo.columnconfigure(1, weight=1)

        frm_esq = ttk.Frame(frm_duplo)
        frm_esq.grid(row=0, column=0, sticky="ew", padx=(0, 6))
        ttk.Label(frm_esq, text="Preço Unitário (R$):*", font=FONT_BOLD).pack(anchor=tk.W, pady=(0, 2))
        self.ent_preco = ttk.Entry(frm_esq, textvariable=self._preco_var, font=("Segoe UI", 9))
        self.ent_preco.pack(fill=tk.X)

        frm_dir = ttk.Frame(frm_duplo)
        frm_dir.grid(row=0, column=1, sticky="ew", padx=(6, 0))
        ttk.Label(frm_dir, text="Saldo em Estoque (unid.):*", font=FONT_BOLD).pack(anchor=tk.W, pady=(0, 2))
        self.ent_estoque = ttk.Entry(frm_dir, textvariable=self._estoque_var, font=("Segoe UI", 9))
        self.ent_estoque.pack(fill=tk.X)

        # Frame dinâmico para atributos polimórficos
        self.frm_especifico = ttk.Frame(container)
        self.frm_especifico.pack(fill=tk.X, pady=(6, 12))

        # Botões
        frm_botoes = ttk.Frame(container)
        frm_botoes.pack(fill=tk.X, side=tk.BOTTOM, pady=(10, 0))

        btn_cancelar = ttk.Button(frm_botoes, text="Cancelar", style="Secondary.TButton", command=self.destroy)
        btn_cancelar.pack(side=tk.RIGHT, padx=(8, 0))

        btn_salvar = ttk.Button(frm_botoes, text="Salvar", style="Primary.TButton", command=self._salvar)
        btn_salvar.pack(side=tk.RIGHT)

        if hasattr(self, "ent_nome"):
            self.ent_nome.focus_set()
        else:
            self.ent_preco.focus_set()

    def _alternar_campos_por_tipo(self) -> None:
        """Renderiza campos específicos de acordo com Físico ou Digital."""
        for widget in self.frm_especifico.winfo_children():
            widget.destroy()

        if self.eh_edicao:
            # Em edição, detalhes de peso/link não mudam
            return

        tipo = self._tipo_var.get()
        if tipo == "Físico":
            ttk.Label(self.frm_especifico, text="Peso Unitário em Kg (para cálculo de frete):*", font=FONT_BOLD).pack(
                anchor=tk.W, pady=(2, 2)
            )
            ent_peso = ttk.Entry(self.frm_especifico, textvariable=self._peso_var, font=("Segoe UI", 9))
            ent_peso.pack(fill=tk.X)
        else:
            ttk.Label(self.frm_especifico, text="Tamanho do Arquivo em Megabytes (MB):*", font=FONT_BOLD).pack(
                anchor=tk.W, pady=(2, 2)
            )
            ent_tam = ttk.Entry(self.frm_especifico, textvariable=self._tamanho_var, font=("Segoe UI", 9))
            ent_tam.pack(fill=tk.X, pady=(0, 4))

            ttk.Label(self.frm_especifico, text="Link Seguro para Download:*", font=FONT_BOLD).pack(
                anchor=tk.W, pady=(2, 2)
            )
            ent_link = ttk.Entry(self.frm_especifico, textvariable=self._link_var, font=("Segoe UI", 9))
            ent_link.pack(fill=tk.X)

    def _salvar(self) -> None:
        if self.eh_edicao:
            # Validação apenas de preço e estoque
            preco_str = self._preco_var.get().strip().replace(",", ".")
            estoque_str = self._estoque_var.get().strip()

            try:
                novo_preco = Decimal(preco_str)
                if novo_preco <= Decimal("0.00"):
                    messagebox.showwarning("Validação", "O preço deve ser maior que zero.", parent=self)
                    return
            except Exception:
                messagebox.showwarning("Validação", "Digite um valor numérico válido para o preço.", parent=self)
                return

            try:
                novo_estoque = int(estoque_str)
                if novo_estoque < 0:
                    messagebox.showwarning("Validação", "O estoque não pode ser negativo.", parent=self)
                    return
            except Exception:
                messagebox.showwarning("Validação", "Digite um número inteiro válido para o estoque.", parent=self)
                return

            try:
                self.produto_service.editar_produto(
                    id_produto=self.produto_edicao.id,
                    novo_preco=novo_preco,
                    novo_estoque=novo_estoque,
                )
                if self.on_success:
                    self.on_success()
                self.destroy()
            except MarketplaceError as erro:
                messagebox.showerror("Erro de Negócio", str(erro), parent=self)
            except Exception as erro:
                messagebox.showerror("Erro Inesperado", f"Falha ao salvar produto: {erro}", parent=self)
            return

        # Cadastro novo
        tipo = self._tipo_var.get()
        nome = self._nome_var.get()
        preco_str = self._preco_var.get()
        estoque_str = self._estoque_var.get()
        peso_str = self._peso_var.get()
        tam_str = self._tamanho_var.get()
        link = self._link_var.get()

        vendedor_texto = self._vendedor_var.get()
        vendedor_id = self._vendedores_map.get(vendedor_texto)

        valido, erro_msg, dados = validar_dados_produto(
            tipo=tipo,
            nome=nome,
            preco_str=preco_str,
            estoque_str=estoque_str,
            vendedor_id=vendedor_id,
            peso_str=peso_str,
            tamanho_str=tam_str,
            link_download=link,
        )

        if not valido:
            messagebox.showwarning("Aviso de Validação", erro_msg, parent=self)
            return

        try:
            if tipo == "Físico":
                self.produto_service.cadastrar_produto_fisico(
                    nome=dados["nome"],
                    preco=dados["preco"],
                    estoque=dados["estoque"],
                    vendedor_id=dados["vendedor_id"],
                    peso_kg=dados["peso_kg"],
                )
            else:
                self.produto_service.cadastrar_produto_digital(
                    nome=dados["nome"],
                    preco=dados["preco"],
                    estoque=dados["estoque"],
                    vendedor_id=dados["vendedor_id"],
                    tamanho_mb=dados["tamanho_mb"],
                    link_download=dados["link_download"],
                )

            if self.on_success:
                self.on_success()
            self.destroy()
        except MarketplaceError as erro:
            messagebox.showerror("Erro de Negócio", str(erro), parent=self)
        except Exception as erro:
            messagebox.showerror("Erro Inesperado", f"Falha ao cadastrar produto: {erro}", parent=self)


class ProdutosView(ttk.Frame):
    """Painel principal da aba de Gestão de Produtos."""

    def __init__(self, parent: tk.Widget, produto_service: Any, usuario_service: Any, gui_app: Any):
        super().__init__(parent)
        self.produto_service = produto_service
        self.usuario_service = usuario_service
        self.gui_app = gui_app

        self._filtro_tipo_var = tk.StringVar(value="Todos")
        self._filtro_vendedor_var = tk.StringVar(value="Todos os Vendedores")
        self._vendedores_map: dict[str, int] = {}

        self._construir_interface()
        self.carregar_dados()

    def _construir_interface(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        # 1. Barra de Ferramentas Superior
        toolbar = ttk.Frame(self, padding=(12, 10))
        toolbar.grid(row=0, column=0, sticky="ew")

        # Filtro de Tipo
        ttk.Label(toolbar, text="Tipo:", font=FONT_SECTION).pack(side=tk.LEFT, padx=(0, 4))
        cb_tipo = ttk.Combobox(
            toolbar,
            textvariable=self._filtro_tipo_var,
            values=["Todos", "Físicos", "Digitais"],
            state="readonly",
            width=10,
        )
        cb_tipo.pack(side=tk.LEFT, padx=(0, 12))
        cb_tipo.bind("<<ComboboxSelected>>", lambda e: self.carregar_dados())

        # Filtro de Vendedor
        ttk.Label(toolbar, text="Vendedor:", font=FONT_SECTION).pack(side=tk.LEFT, padx=(0, 4))
        self.cb_vendedor_filtro = ttk.Combobox(
            toolbar,
            textvariable=self._filtro_vendedor_var,
            state="readonly",
            width=22,
        )
        self.cb_vendedor_filtro.pack(side=tk.LEFT, padx=(0, 16))
        self.cb_vendedor_filtro.bind("<<ComboboxSelected>>", lambda e: self.carregar_dados())

        # Ações
        btn_novo = ttk.Button(toolbar, text="➕ Novo Produto", style="Primary.TButton", command=self._abrir_cadastro)
        btn_novo.pack(side=tk.LEFT, padx=4)

        btn_editar = ttk.Button(toolbar, text="✏️ Editar Preço/Estoque", style="Secondary.TButton", command=self._abrir_edicao)
        btn_editar.pack(side=tk.LEFT, padx=4)

        btn_remover = ttk.Button(toolbar, text="🗑️ Remover", style="Danger.TButton", command=self._remover_selecionado)
        btn_remover.pack(side=tk.LEFT, padx=4)

        btn_atualizar = ttk.Button(toolbar, text="🔄 Atualizar", style="Secondary.TButton", command=self.carregar_dados)
        btn_atualizar.pack(side=tk.RIGHT, padx=4)

        # 2. Área Central com Treeview
        tree_container = ttk.Frame(self, padding=(12, 0, 12, 10))
        tree_container.grid(row=1, column=0, sticky="nsew")
        tree_container.columnconfigure(0, weight=1)
        tree_container.rowconfigure(0, weight=1)

        colunas = ("id", "nome", "tipo", "preco", "estoque", "vendedor", "detalhes")
        self.tree = ttk.Treeview(tree_container, columns=colunas, show="headings", selectmode="browse")

        self.tree.heading("id", text="ID")
        self.tree.heading("nome", text="Nome do Produto")
        self.tree.heading("tipo", text="Tipo")
        self.tree.heading("preco", text="Preço Unitário")
        self.tree.heading("estoque", text="Estoque")
        self.tree.heading("vendedor", text="Vendedor")
        self.tree.heading("detalhes", text="Especificações (Peso / Download)")

        self.tree.column("id", width=55, anchor=tk.CENTER)
        self.tree.column("nome", width=220, anchor=tk.W)
        self.tree.column("tipo", width=80, anchor=tk.CENTER)
        self.tree.column("preco", width=110, anchor=tk.E)
        self.tree.column("estoque", width=80, anchor=tk.CENTER)
        self.tree.column("vendedor", width=180, anchor=tk.W)
        self.tree.column("detalhes", width=240, anchor=tk.W)

        self.tree.tag_configure("even", background=BG_ROW_EVEN)
        self.tree.tag_configure("odd", background=BG_ROW_ODD)

        scroll_y = ttk.Scrollbar(tree_container, orient=tk.VERTICAL, command=self.tree.yview)
        scroll_x = ttk.Scrollbar(tree_container, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        scroll_y.grid(row=0, column=1, sticky="ns")
        scroll_x.grid(row=1, column=0, sticky="ew")

        self.tree.bind("<Double-1>", lambda e: self._abrir_edicao())

    def carregar_dados(self) -> None:
        """Carrega e filtra a lista de produtos."""
        # Atualiza opções de vendedores no combobox
        vendedores = self.usuario_service.listar_vendedores()
        self._vendedores_map = {f"{v.nome} [#{v.id}]": v.id for v in vendedores}
        opcoes_vendedores = ["Todos os Vendedores"] + list(self._vendedores_map.keys())
        self.cb_vendedor_filtro["values"] = opcoes_vendedores
        if self._filtro_vendedor_var.get() not in opcoes_vendedores:
            self._filtro_vendedor_var.set("Todos os Vendedores")

        # Busca produtos
        vendedor_sel = self._filtro_vendedor_var.get()
        if vendedor_sel != "Todos os Vendedores" and vendedor_sel in self._vendedores_map:
            vid = self._vendedores_map[vendedor_sel]
            produtos = self.produto_service.listar_por_vendedor(vid)
        else:
            produtos = self.produto_service.listar_produtos()

        # Filtro por tipo
        tipo_sel = self._filtro_tipo_var.get()
        if tipo_sel == "Físicos":
            produtos = [p for p in produtos if p.tipo() == "Físico"]
        elif tipo_sel == "Digitais":
            produtos = [p for p in produtos if p.tipo() == "Digital"]

        for item in self.tree.get_children():
            self.tree.delete(item)

        for i, p in enumerate(produtos):
            tag = "even" if i % 2 == 0 else "odd"
            valores = formatar_produto_tabela(p)
            self.tree.insert("", tk.END, iid=str(p.id), values=valores, tags=(tag,))

        self.gui_app.definir_status(f"Catálogo de produtos atualizado ({len(produtos)} itens exibidos).")

    def _obter_id_selecionado(self) -> Optional[int]:
        selecao = self.tree.selection()
        if not selecao:
            return None
        try:
            return int(selecao[0])
        except ValueError:
            return None

    def _abrir_cadastro(self) -> None:
        vendedores = self.usuario_service.listar_vendedores()
        if not vendedores:
            messagebox.showwarning(
                "Atenção",
                "Nenhum vendedor cadastrado no sistema!\nCadastre ao menos um vendedor na aba 'Usuários' antes de cadastrar produtos.",
                parent=self,
            )
            return
        ProdutoModal(self, self.produto_service, self.usuario_service, produto_edicao=None, on_success=self.carregar_dados)

    def _abrir_edicao(self) -> None:
        pid = self._obter_id_selecionado()
        if pid is None:
            messagebox.showinfo("Seleção", "Selecione um produto na tabela para editar.", parent=self)
            return

        produto = self.produto_service.buscar_por_id(pid)
        if produto:
            ProdutoModal(self, self.produto_service, self.usuario_service, produto_edicao=produto, on_success=self.carregar_dados)

    def _remover_selecionado(self) -> None:
        pid = self._obter_id_selecionado()
        if pid is None:
            messagebox.showinfo("Seleção", "Selecione um produto na tabela para remover.", parent=self)
            return

        produto = self.produto_service.buscar_por_id(pid)
        if not produto:
            return

        confirma = messagebox.askyesno(
            "Confirmar Remoção",
            f"Deseja realmente remover o produto #{produto.id:03d} - '{produto.nome}'?\n\n"
            "Atenção: Produtos que já foram vendidos em pedidos concluídos não podem ser removidos (ON DELETE RESTRICT).",
            parent=self,
        )
        if not confirma:
            return

        try:
            self.produto_service.remover_produto(pid)
            self.tree.selection_remove(self.tree.selection())
            self.carregar_dados()
            self.gui_app.definir_status(f"Produto #{pid:03d} removido com sucesso.")
            messagebox.showinfo("Sucesso", f"Produto #{pid:03d} removido com sucesso.", parent=self)
        except MarketplaceError as erro:
            messagebox.showerror("Bloqueio de Regra de Negócio", str(erro), parent=self)
        except Exception as erro:
            messagebox.showerror("Erro Operacional", f"Falha ao remover produto: {erro}", parent=self)
