"""
=====================================================================
Tela de Gestão de Usuários (ui/gui/usuarios_view.py)
=====================================================================
Permite visualização, filtragem, cadastro, edição e exclusão de
Clientes e Vendedores via Treeview e janelas modais dedicadas.
=====================================================================
"""

from __future__ import annotations
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, Callable, Any

from ui.gui.estilos import (
    BG_DARK,
    BG_CARD,
    BG_ROW_EVEN,
    BG_ROW_ODD,
    FONT_BOLD,
    FONT_SUBTITLE,
    FONT_SECTION,
)
from ui.gui.formatters import formatar_usuario_tabela
from ui.gui.validators import validar_dados_usuario
from exceptions import MarketplaceError


class UsuarioModal(tk.Toplevel):
    """Janela modal para cadastro ou edição de Cliente / Vendedor."""

    def __init__(
        self,
        parent: tk.Widget,
        usuario_service: Any,
        usuario_edicao: Optional[Any] = None,
        on_success: Optional[Callable[[], None]] = None,
    ):
        super().__init__(parent)
        self.usuario_service = usuario_service
        self.usuario_edicao = usuario_edicao
        self.on_success = on_success

        self.eh_edicao = usuario_edicao is not None
        titulo_janela = "Editar Usuário" if self.eh_edicao else "Novo Usuário"
        self.title(titulo_janela)
        self.geometry("480x420")
        self.minsize(440, 380)
        self.configure(bg=BG_CARD)

        # Configura comportamento modal
        self.transient(parent.winfo_toplevel())
        self.grab_set()

        self._tipo_var = tk.StringVar(value="Cliente")
        self._nome_var = tk.StringVar()
        self._email_var = tk.StringVar()
        self._endereco_var = tk.StringVar()
        self._loja_var = tk.StringVar()

        if self.eh_edicao:
            self._tipo_var.set(self.usuario_edicao.tipo())
            self._nome_var.set(self.usuario_edicao.nome)
            self._email_var.set(self.usuario_edicao.email)
            if self.usuario_edicao.tipo() == "Cliente":
                self._endereco_var.set(getattr(self.usuario_edicao, "endereco", ""))
            else:
                self._loja_var.set(getattr(self.usuario_edicao, "nome_loja", ""))

        self._construir_interface()
        self._alternar_campos_por_tipo()
        self.center_window()

    def center_window(self) -> None:
        """Centraliza o diálogo em relação à janela principal."""
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
            f"Editar Usuário #{self.usuario_edicao.id:03d}"
            if self.eh_edicao
            else "Cadastrar Novo Usuário"
        )
        lbl_titulo = ttk.Label(container, text=titulo_texto, font=FONT_SUBTITLE)
        lbl_titulo.pack(anchor=tk.W, pady=(0, 15))

        # Seleção de Tipo (Cliente / Vendedor)
        frm_tipo = ttk.Frame(container)
        frm_tipo.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(frm_tipo, text="Perfil de Usuário:", font=FONT_BOLD).pack(anchor=tk.W, pady=(0, 4))
        rb_cliente = ttk.Radiobutton(
            frm_tipo,
            text="Cliente (Consumidor / Compras)",
            value="Cliente",
            variable=self._tipo_var,
            command=self._alternar_campos_por_tipo,
        )
        rb_cliente.pack(anchor=tk.W, pady=2)

        rb_vendedor = ttk.Radiobutton(
            frm_tipo,
            text="Vendedor (Lojista / Catálogo)",
            value="Vendedor",
            variable=self._tipo_var,
            command=self._alternar_campos_por_tipo,
        )
        rb_vendedor.pack(anchor=tk.W, pady=2)

        if self.eh_edicao:
            rb_cliente.configure(state="disabled")
            rb_vendedor.configure(state="disabled")

        # Campo: Nome
        ttk.Label(container, text="Nome Completo:*", font=FONT_BOLD).pack(anchor=tk.W, pady=(8, 2))
        self.ent_nome = ttk.Entry(container, textvariable=self._nome_var, font=("Segoe UI", 9))
        self.ent_nome.pack(fill=tk.X, pady=(0, 6))

        # Campo: E-mail
        ttk.Label(container, text="E-mail Corporativo/Pessoal:*", font=FONT_BOLD).pack(anchor=tk.W, pady=(4, 2))
        self.ent_email = ttk.Entry(container, textvariable=self._email_var, font=("Segoe UI", 9))
        self.ent_email.pack(fill=tk.X, pady=(0, 6))

        # Frame dinâmico para campo específico
        self.frm_dinamico = ttk.Frame(container)
        self.frm_dinamico.pack(fill=tk.X, pady=(4, 15))

        self.lbl_especifico = ttk.Label(self.frm_dinamico, text="Endereço:*", font=FONT_BOLD)
        self.lbl_especifico.pack(anchor=tk.W, pady=(0, 2))
        self.ent_especifico = ttk.Entry(self.frm_dinamico, textvariable=self._endereco_var, font=("Segoe UI", 9))
        self.ent_especifico.pack(fill=tk.X)

        # Botões de Ação
        frm_botoes = ttk.Frame(container)
        frm_botoes.pack(fill=tk.X, side=tk.BOTTOM, pady=(15, 0))

        btn_cancelar = ttk.Button(frm_botoes, text="Cancelar", style="Secondary.TButton", command=self.destroy)
        btn_cancelar.pack(side=tk.RIGHT, padx=(8, 0))

        btn_salvar = ttk.Button(frm_botoes, text="Salvar", style="Primary.TButton", command=self._salvar)
        btn_salvar.pack(side=tk.RIGHT)

        self.ent_nome.focus_set()

    def _alternar_campos_por_tipo(self) -> None:
        """Alterna a exibição de 'Endereço' ou 'Nome da Loja'."""
        tipo = self._tipo_var.get()
        if tipo == "Cliente":
            self.lbl_especifico.configure(text="Endereço de Entrega:*")
            self.ent_especifico.configure(textvariable=self._endereco_var)
        else:
            self.lbl_especifico.configure(text="Nome da Loja / Razão Social:*")
            self.ent_especifico.configure(textvariable=self._loja_var)

    def _salvar(self) -> None:
        tipo = self._tipo_var.get()
        nome = self._nome_var.get()
        email = self._email_var.get()
        endereco = self._endereco_var.get()
        nome_loja = self._loja_var.get()

        valido, erro_msg = validar_dados_usuario(
            tipo=tipo,
            nome=nome,
            email=email,
            endereco=endereco,
            nome_loja=nome_loja,
        )
        if not valido:
            messagebox.showwarning("Aviso de Validação", erro_msg, parent=self)
            return

        try:
            if not self.eh_edicao:
                if tipo == "Cliente":
                    self.usuario_service.cadastrar_cliente(nome=nome, email=email, endereco=endereco)
                else:
                    self.usuario_service.cadastrar_vendedor(nome=nome, email=email, nome_loja=nome_loja)
            else:
                self.usuario_service.editar_usuario(
                    id_usuario=self.usuario_edicao.id,
                    nome=nome,
                    email=email,
                    endereco=endereco if tipo == "Cliente" else None,
                    nome_loja=nome_loja if tipo == "Vendedor" else None,
                )

            if self.on_success:
                self.on_success()
            self.destroy()
        except MarketplaceError as erro:
            messagebox.showerror("Erro de Negócio", str(erro), parent=self)
        except Exception as erro:
            messagebox.showerror("Erro Inesperado", f"Falha ao persistir usuário: {erro}", parent=self)


class UsuariosView(ttk.Frame):
    """Painel principal da aba de Gestão de Usuários."""

    def __init__(self, parent: tk.Widget, usuario_service: Any, gui_app: Any):
        super().__init__(parent)
        self.usuario_service = usuario_service
        self.gui_app = gui_app

        self._filtro_var = tk.StringVar(value="Todos")
        self._construir_interface()
        self.carregar_dados()

    def _construir_interface(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        # 1. Barra de Ferramentas Superior
        toolbar = ttk.Frame(self, padding=(12, 10))
        toolbar.grid(row=0, column=0, sticky="ew")

        ttk.Label(toolbar, text="Filtrar por Perfil:", font=FONT_SECTION).pack(side=tk.LEFT, padx=(0, 6))
        cb_filtro = ttk.Combobox(
            toolbar,
            textvariable=self._filtro_var,
            values=["Todos", "Clientes", "Vendedores"],
            state="readonly",
            width=14,
        )
        cb_filtro.pack(side=tk.LEFT, padx=(0, 15))
        cb_filtro.bind("<<ComboboxSelected>>", lambda e: self.carregar_dados())

        btn_novo = ttk.Button(toolbar, text="➕ Novo Usuário", style="Primary.TButton", command=self._abrir_cadastro)
        btn_novo.pack(side=tk.LEFT, padx=4)

        btn_editar = ttk.Button(toolbar, text="✏️ Editar", style="Secondary.TButton", command=self._abrir_edicao)
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

        colunas = ("id", "tipo", "nome", "email", "detalhes")
        self.tree = ttk.Treeview(tree_container, columns=colunas, show="headings", selectmode="browse")

        self.tree.heading("id", text="ID")
        self.tree.heading("tipo", text="Tipo")
        self.tree.heading("nome", text="Nome Completo")
        self.tree.heading("email", text="E-mail")
        self.tree.heading("detalhes", text="Endereço / Loja")

        self.tree.column("id", width=60, anchor=tk.CENTER)
        self.tree.column("tipo", width=90, anchor=tk.CENTER)
        self.tree.column("nome", width=200, anchor=tk.W)
        self.tree.column("email", width=220, anchor=tk.W)
        self.tree.column("detalhes", width=300, anchor=tk.W)

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
        """Recarrega a lista de usuários a partir do serviço."""
        filtro = self._filtro_var.get()
        if filtro == "Clientes":
            usuarios = self.usuario_service.listar_clientes()
        elif filtro == "Vendedores":
            usuarios = self.usuario_service.listar_vendedores()
        else:
            usuarios = self.usuario_service.listar_usuarios()

        for item in self.tree.get_children():
            self.tree.delete(item)

        for i, u in enumerate(usuarios):
            tag = "even" if i % 2 == 0 else "odd"
            valores = formatar_usuario_tabela(u)
            self.tree.insert("", tk.END, iid=str(u.id), values=valores, tags=(tag,))

        self.gui_app.definir_status(f"Listagem de usuários atualizada ({len(usuarios)} registros).")

    def _obter_id_selecionado(self) -> Optional[int]:
        selecao = self.tree.selection()
        if not selecao:
            return None
        try:
            return int(selecao[0])
        except ValueError:
            return None

    def _abrir_cadastro(self) -> None:
        UsuarioModal(self, self.usuario_service, usuario_edicao=None, on_success=self.carregar_dados)

    def _abrir_edicao(self) -> None:
        uid = self._obter_id_selecionado()
        if uid is None:
            messagebox.showinfo("Seleção", "Selecione um usuário na tabela para editar.", parent=self)
            return

        usuario = self.usuario_service.buscar_por_id(uid)
        if usuario:
            UsuarioModal(self, self.usuario_service, usuario_edicao=usuario, on_success=self.carregar_dados)

    def _remover_selecionado(self) -> None:
        uid = self._obter_id_selecionado()
        if uid is None:
            messagebox.showinfo("Seleção", "Selecione um usuário na tabela para remover.", parent=self)
            return

        usuario = self.usuario_service.buscar_por_id(uid)
        if not usuario:
            return

        confirma = messagebox.askyesno(
            "Confirmar Remoção",
            f"Deseja realmente remover o usuário #{usuario.id:03d} - '{usuario.nome}' ({usuario.tipo()})?\n\n"
            "Atenção: Clientes com histórico de pedidos ou Vendedores com produtos não podem ser removidos.",
            parent=self,
        )
        if not confirma:
            return

        try:
            self.usuario_service.remover_usuario(uid)
            self.tree.selection_remove(self.tree.selection())
            self.carregar_dados()
            self.gui_app.definir_status(f"Usuário #{uid:03d} removido com sucesso.")
            messagebox.showinfo("Sucesso", f"Usuário #{uid:03d} removido com sucesso.", parent=self)
        except MarketplaceError as erro:
            messagebox.showerror("Bloqueio de Regra de Negócio", str(erro), parent=self)
        except Exception as erro:
            messagebox.showerror("Erro Operacional", f"Falha ao remover usuário: {erro}", parent=self)
