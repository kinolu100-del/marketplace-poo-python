"""
=====================================================================
Interface de Linha de Comando / Console (ui/cli.py)
=====================================================================
Responsável por toda a interação com o usuário (prints, menus, inputs).
Consome as regras de negócio puras através de serviços:
  - UsuarioService
  - ProdutoService
  - PedidoService
  - DemonstracaoService

Garante que as regras de negócio permaneçam desacopladas e prontas
para Nível 3 (banco de dados) e Nível 4 (interface gráfica).
=====================================================================
"""

from __future__ import annotations
from decimal import Decimal, InvalidOperation
from typing import Optional

from services.usuario_service import UsuarioService
from services.produto_service import ProdutoService
from services.pedido_service import PedidoService
from services.demonstracao_service import DemonstracaoService
from models.usuario import Cliente, Vendedor
from models.pedido import Pedido, StatusPedido
from exceptions import MarketplaceError
from ui.helpers import (
    moeda,
    linha,
    titulo,
    ler_texto,
    ler_inteiro,
    ler_inteiro_opcional,
    ler_decimal,
    ler_decimal_opcional,
    ler_email,
    confirmar,
    calcular_resumo_frete,
)


class MarketplaceCLI:
    """[DEPENDÊNCIA]: Camada de apresentação no terminal."""

    def __init__(
        self,
        usuario_service: UsuarioService,
        produto_service: ProdutoService,
        pedido_service: PedidoService,
        demonstracao_service: DemonstracaoService,
    ):
        self.usuario_service = usuario_service
        self.produto_service = produto_service
        self.pedido_service = pedido_service
        self.demonstracao_service = demonstracao_service

    # =================================================================
    # MENU PRINCIPAL
    # =================================================================
    def executar(self) -> None:
        """Loop de execução do menu principal."""
        opcoes = {
            1: ("Gestão de Usuários (Clientes e Vendedores)", self.menu_usuarios),
            2: ("Gestão de Produtos (Físicos e Digitais)", self.menu_produtos),
            3: ("Gestão de Carrinho de Compras", self.menu_carrinho),
            4: ("Gestão de Pedidos e Vendas", self.menu_pedidos),
            5: ("Carregar Dados de Demonstração (Vídeo)", self.acao_carregar_demo),
            6: ("Reiniciar / Zerar Banco de Dados (Vídeo)", self.acao_reiniciar_banco),
            0: ("Sair do Sistema", None),
        }

        while True:
            titulo("MARKETPLACE EM PYTHON - SISTEMA DE DOMÍNIO POO")
            for num, (rotulo, _) in opcoes.items():
                print(f"  [{num}] {rotulo}")
            linha("=")

            try:
                escolha = ler_inteiro("Informe a opção desejada: ", 0, 6)
            except (KeyboardInterrupt, EOFError):
                print("\nEncerrando sistema...")
                break

            if escolha == 0:
                print("\nEncerrando o Marketplace. Obrigado e até a próxima!")
                break

            acao = opcoes[escolha][1]
            try:
                acao()
            except (KeyboardInterrupt, EOFError):
                print("\n[!] Operação cancelada. Retornando ao menu principal...")
            except (MarketplaceError, ValueError, InvalidOperation) as erro:
                print(f"\n  [!] Erro: {erro}")
                input("\nPressione [Enter] para continuar...")

    # =================================================================
    # 1. GESTÃO DE USUÁRIOS
    # =================================================================
    def menu_usuarios(self) -> None:
        """Submenu com todas as operações de usuários."""
        while True:
            titulo("GESTÃO DE USUÁRIOS")
            print("  [1] Cadastrar Novo Usuário (Cliente ou Vendedor)")
            print("  [2] Listar Todos os Usuários")
            print("  [3] Editar Usuário Existente")
            print("  [4] Remover Usuário")
            print("  [0] Voltar ao Menu Principal")
            linha()

            opcao = ler_inteiro("Opção: ", 0, 4)
            if opcao == 0:
                break
            elif opcao == 1:
                self._cadastrar_usuario()
            elif opcao == 2:
                self._listar_usuarios()
            elif opcao == 3:
                self._editar_usuario()
            elif opcao == 4:
                self._remover_usuario()

            input("\nPressione [Enter] para continuar...")

    def _cadastrar_usuario(self) -> None:
        titulo("CADASTRAR USUÁRIO")
        print("  1 - Cliente (Comprador)")
        print("  2 - Vendedor (Loja Parceira)")
        tipo_escolha = ler_inteiro("Selecione o tipo: ", 1, 2)

        nome = ler_texto("Nome completo: ")
        email = ler_email("E-mail de contato: ")

        if tipo_escolha == 1:
            endereco = ler_texto("Endereço de entrega: ")
            usuario = self.usuario_service.cadastrar_cliente(nome, email, endereco)
        else:
            nome_loja = ler_texto("Nome fantasia da loja: ")
            usuario = self.usuario_service.cadastrar_vendedor(nome, email, nome_loja)

        print(f"\n  [OK] {usuario.tipo()} '{usuario.nome}' cadastrado com sucesso! ID: {usuario.id:03d}")

    def _listar_usuarios(self) -> None:
        titulo("USUÁRIOS CADASTRADOS")
        usuarios = self.usuario_service.listar_usuarios()
        if not usuarios:
            print("  Nenhum usuário cadastrado no sistema.")
            return

        for u in usuarios:
            # [POLIMORFISMO]: Cada subclasse gera seu resumo formatado
            print(f"  {u.resumo()}")

        linha()
        clientes = self.usuario_service.listar_clientes()
        vendedores = self.usuario_service.listar_vendedores()
        print(f"  Total: {len(clientes)} cliente(s) e {len(vendedores)} vendedor(es).")

    def _editar_usuario(self) -> None:
        titulo("EDITAR USUÁRIO")
        usuarios = self.usuario_service.listar_usuarios()
        if not usuarios:
            print("  Nenhum usuário cadastrado.")
            return

        for u in usuarios:
            print(f"  [{u.id:03d}] {u.nome} ({u.tipo()})")
        linha()

        uid = ler_inteiro("Informe o ID do usuário para editar (0 para cancelar): ", 0)
        if uid == 0:
            return

        usuario = self.usuario_service.buscar_por_id(uid)
        print(f"\nEditando: {usuario.resumo()}")
        print("(Deixe em branco pressionando [Enter] para manter o valor atual)")

        novo_nome = input(f"Novo nome [{usuario.nome}]: ").strip()
        novo_email = input(f"Novo e-mail [{usuario.email}]: ").strip()

        novo_end = None
        nova_loja = None

        if isinstance(usuario, Cliente):
            novo_end = input(f"Novo endereço [{usuario.endereco}]: ").strip()
        elif isinstance(usuario, Vendedor):
            nova_loja = input(f"Novo nome de loja [{usuario.nome_loja}]: ").strip()

        self.usuario_service.editar_usuario(
            id_usuario=uid,
            nome=novo_nome if novo_nome else None,
            email=novo_email if novo_email else None,
            endereco=novo_end if novo_end else None,
            nome_loja=nova_loja if nova_loja else None,
        )
        print(f"\n  [OK] Usuário ID {uid:03d} atualizado com sucesso!")

    def _remover_usuario(self) -> None:
        titulo("REMOVER USUÁRIO")
        usuarios = self.usuario_service.listar_usuarios()
        if not usuarios:
            print("  Nenhum usuário cadastrado.")
            return

        for u in usuarios:
            print(f"  [{u.id:03d}] {u.nome} ({u.tipo()})")
        linha()

        uid = ler_inteiro("Informe o ID do usuário para remover (0 para cancelar): ", 0)
        if uid == 0:
            return

        usuario = self.usuario_service.buscar_por_id(uid)
        if confirmar(f"Tem certeza que deseja remover {usuario.tipo()} '{usuario.nome}'?"):
            self.usuario_service.remover_usuario(uid)
            print(f"\n  [OK] Usuário ID {uid:03d} removido com sucesso!")
        else:
            print("\n  Operação cancelada.")

    # =================================================================
    # 2. GESTÃO DE PRODUTOS
    # =================================================================
    def menu_produtos(self) -> None:
        """Submenu com todas as operações de produtos."""
        while True:
            titulo("GESTÃO DE PRODUTOS")
            print("  [1] Cadastrar Novo Produto (Físico ou Digital)")
            print("  [2] Listar Catálogo Completo de Produtos")
            print("  [3] Listar Produtos por Vendedor")
            print("  [4] Editar Preço e Estoque do Produto")
            print("  [5] Remover Produto do Catálogo")
            print("  [0] Voltar ao Menu Principal")
            linha()

            opcao = ler_inteiro("Opção: ", 0, 5)
            if opcao == 0:
                break
            elif opcao == 1:
                self._cadastrar_produto()
            elif opcao == 2:
                self._listar_produtos()
            elif opcao == 3:
                self._listar_produtos_por_vendedor()
            elif opcao == 4:
                self._editar_produto()
            elif opcao == 5:
                self._remover_produto()

            input("\nPressione [Enter] para continuar...")

    def _cadastrar_produto(self) -> None:
        titulo("CADASTRAR PRODUTO")
        vendedores = self.usuario_service.listar_vendedores()
        if not vendedores:
            print("  [!] Nenhum Vendedor cadastrado. Cadastre um vendedor primeiro!")
            return

        print("Vendedores disponíveis:")
        for v in vendedores:
            print(f"  [{v.id:03d}] {v.nome} - Loja: {v.nome_loja}")
        linha()

        vid = ler_inteiro("Informe o ID do vendedor anunciante: ", 1)
        # Validação do vendedor
        self.usuario_service.buscar_por_id(vid)

        print("\nTipo de Produto:")
        print("  1 - Produto Físico (calcula frete com base no peso)")
        print("  2 - Produto Digital (download imediato com frete grátis)")
        tipo_prod = ler_inteiro("Opção: ", 1, 2)

        nome = ler_texto("Nome do produto: ")
        preco = ler_decimal("Preço unitário (R$): ", minimo=Decimal("0.01"))
        estoque = ler_inteiro("Estoque inicial: ", minimo=1)

        if tipo_prod == 1:
            peso_kg = ler_decimal("Peso em Kg (ex: 0.5): ", minimo=Decimal("0.01"))
            produto = self.produto_service.cadastrar_produto_fisico(
                nome=nome,
                preco=preco,
                estoque=estoque,
                vendedor_id=vid,
                peso_kg=peso_kg,
            )
        else:
            tamanho_mb = ler_decimal("Tamanho em Megabytes (MB): ", minimo=Decimal("0.1"))
            link = ler_texto("Link de download/acesso: ")
            produto = self.produto_service.cadastrar_produto_digital(
                nome=nome,
                preco=preco,
                estoque=estoque,
                vendedor_id=vid,
                tamanho_mb=tamanho_mb,
                link_download=link,
            )

        print(f"\n  [OK] Produto '{produto.nome}' ({produto.tipo()}) cadastrado! ID: {produto.id:03d}")

    def _listar_produtos(self) -> None:
        titulo("CATÁLOGO GERAL DE PRODUTOS")
        produtos = self.produto_service.listar_produtos()
        if not produtos:
            print("  Nenhum produto cadastrado no marketplace.")
            return

        for p in produtos:
            # [POLIMORFISMO]: Exibição especializada por subclasse
            print(f"  {p.exibir_detalhes()}")

    def _listar_produtos_por_vendedor(self) -> None:
        titulo("PRODUTOS POR VENDEDOR")
        vendedores = self.usuario_service.listar_vendedores()
        if not vendedores:
            print("  Nenhum vendedor cadastrado.")
            return

        for v in vendedores:
            print(f"  [{v.id:03d}] {v.nome} - Loja: {v.nome_loja}")
        linha()

        vid = ler_inteiro("Informe o ID do vendedor: ", 1)
        produtos = self.produto_service.listar_por_vendedor(vid)
        if not produtos:
            print("  Este vendedor não possui produtos anunciados.")
            return

        for p in produtos:
            print(f"  {p.exibir_detalhes()}")

    def _editar_produto(self) -> None:
        titulo("EDITAR PRODUTO")
        produtos = self.produto_service.listar_produtos()
        if not produtos:
            print("  Nenhum produto cadastrado.")
            return

        for p in produtos:
            print(f"  [{p.id:03d}] {p.nome} | Preço: {moeda(p.preco)} | Estoque: {p.estoque} un")
        linha()

        pid = ler_inteiro("Informe o ID do produto para editar (0 para cancelar): ", 0)
        if pid == 0:
            return

        produto = self.produto_service.buscar_por_id(pid)
        print(f"\nEditando: {produto.nome}")

        novo_preco = ler_decimal_opcional(
            f"Novo preço [{produto.preco}]: ", minimo=Decimal("0.01")
        )
        novo_estoque = ler_inteiro_opcional(
            f"Novo estoque [{produto.estoque}]: ", minimo=0
        )

        self.produto_service.editar_produto(
            id_produto=pid,
            novo_preco=novo_preco,
            novo_estoque=novo_estoque,
        )
        print(f"\n  [OK] Produto ID {pid:03d} atualizado com sucesso!")

    def _remover_produto(self) -> None:
        titulo("REMOVER PRODUTO")
        produtos = self.produto_service.listar_produtos()
        if not produtos:
            print("  Nenhum produto cadastrado.")
            return

        for p in produtos:
            print(f"  [{p.id:03d}] {p.nome} ({p.tipo()})")
        linha()

        pid = ler_inteiro("Informe o ID do produto para remover (0 para cancelar): ", 0)
        if pid == 0:
            return

        produto = self.produto_service.buscar_por_id(pid)
        if confirmar(f"Tem certeza que deseja remover o produto '{produto.nome}'?"):
            self.produto_service.remover_produto(pid)
            print(f"\n  [OK] Produto ID {pid:03d} removido com sucesso!")
        else:
            print("\n  Operação cancelada.")

    # =================================================================
    # 3. GESTÃO DO CARRINHO
    # =================================================================
    def _selecionar_cliente(self) -> Optional[Cliente]:
        """Auxiliar interativo para selecionar um cliente."""
        clientes = self.usuario_service.listar_clientes()
        if not clientes:
            print("  [!] Nenhum cliente cadastrado. Cadastre um cliente primeiro!")
            return None

        print("Clientes cadastrados:")
        for c in clientes:
            print(f"  [{c.id:03d}] {c.nome} - Endereço: {c.endereco}")
        linha()

        cid = ler_inteiro("Informe o ID do cliente (0 para cancelar): ", 0)
        if cid == 0:
            return None
        return self.pedido_service.obter_cliente(cid)

    def menu_carrinho(self) -> None:
        """Submenu com operações completas do carrinho."""
        while True:
            titulo("GESTÃO DE CARRINHO DE COMPRAS")
            print("  [1] Visualizar Itens do Carrinho de um Cliente")
            print("  [2] Adicionar Item ao Carrinho")
            print("  [3] Alterar Quantidade de um Item no Carrinho")
            print("  [4] Remover Item do Carrinho")
            print("  [5] Limpar Carrinho Integralmente")
            print("  [0] Voltar ao Menu Principal")
            linha()

            opcao = ler_inteiro("Opção: ", 0, 5)
            if opcao == 0:
                break
            elif opcao == 1:
                self._ver_carrinho()
            elif opcao == 2:
                self._adicionar_ao_carrinho()
            elif opcao == 3:
                self._alterar_qtd_carrinho()
            elif opcao == 4:
                self._remover_do_carrinho()
            elif opcao == 5:
                self._limpar_carrinho()

            input("\nPressione [Enter] para continuar...")

    def _ver_carrinho(self) -> None:
        titulo("CARRINHO DO CLIENTE")
        cliente = self._selecionar_cliente()
        if not cliente:
            return

        carrinho = cliente.carrinho
        if carrinho.esta_vazio():
            print(f"\n  O carrinho de '{cliente.nome}' está vazio.")
            return

        print(f"\nItens no carrinho de '{cliente.nome}':")
        linha("-")
        for item in carrinho.itens:
            prod = item.produto
            print(
                f"  • [{prod.id:03d}] {prod.nome:<30} | {item.quantidade:02d} un | "
                f"Unit: {moeda(prod.preco)} | Subtotal: {moeda(item.subtotal)}"
            )
        linha("-")
        print(f"  Subtotal acumulado dos produtos: {moeda(carrinho.subtotal)}")

    def _adicionar_ao_carrinho(self) -> None:
        titulo("ADICIONAR PRODUTO AO CARRINHO")
        cliente = self._selecionar_cliente()
        if not cliente:
            return

        produtos = self.produto_service.listar_produtos()
        if not produtos:
            print("  Nenhum produto cadastrado no sistema.")
            return

        print("\nProdutos disponíveis:")
        for p in produtos:
            print(f"  [{p.id:03d}] {p.nome:<28} | {moeda(p.preco):<10} | Estoque: {p.estoque:02d} un ({p.tipo()})")
        linha()

        pid = ler_inteiro("Informe o ID do produto para adicionar: ", 1)
        produto = self.produto_service.buscar_por_id(pid)

        ja_no_carrinho = cliente.carrinho.quantidade_de(produto)
        disponivel = produto.estoque - ja_no_carrinho

        if disponivel <= 0:
            print(f"  [!] Sem estoque disponível para adicionar mais unidades de '{produto.nome}'.")
            return

        qtd = ler_inteiro(
            f"Quantidade de '{produto.nome}' (Disponível: {disponivel}): ",
            minimo=1,
            maximo=disponivel,
        )

        self.pedido_service.adicionar_ao_carrinho(cliente.id, pid, qtd)
        print(f"\n  [OK] {qtd}x '{produto.nome}' adicionado(s) ao carrinho com sucesso!")

    def _alterar_qtd_carrinho(self) -> None:
        titulo("ALTERAR QUANTIDADE NO CARRINHO")
        cliente = self._selecionar_cliente()
        if not cliente:
            return

        carrinho = cliente.carrinho
        if carrinho.esta_vazio():
            print("  O carrinho está vazio.")
            return

        for item in carrinho.itens:
            print(f"  [{item.produto.id:03d}] {item.produto.nome} (Atual: {item.quantidade} un)")
        linha()

        pid = ler_inteiro("Informe o ID do produto: ", 1)
        produto = self.produto_service.buscar_por_id(pid)

        nova_qtd = ler_inteiro(
            f"Nova quantidade (0 para remover, Máx em estoque: {produto.estoque}): ",
            minimo=0,
            maximo=produto.estoque,
        )

        self.pedido_service.alterar_quantidade_carrinho(cliente.id, pid, nova_qtd)
        print(f"\n  [OK] Quantidade atualizada no carrinho com sucesso!")

    def _remover_do_carrinho(self) -> None:
        titulo("REMOVER ITEM DO CARRINHO")
        cliente = self._selecionar_cliente()
        if not cliente:
            return

        carrinho = cliente.carrinho
        if carrinho.esta_vazio():
            print("  O carrinho está vazio.")
            return

        for item in carrinho.itens:
            print(f"  [{item.produto.id:03d}] {item.produto.nome} (Quantidade: {item.quantidade} un)")
        linha()

        pid = ler_inteiro("Informe o ID do produto a remover: ", 1)
        self.pedido_service.remover_do_carrinho(cliente.id, pid)
        print(f"\n  [OK] Produto removido do carrinho com sucesso!")

    def _limpar_carrinho(self) -> None:
        titulo("LIMPAR CARRINHO")
        cliente = self._selecionar_cliente()
        if not cliente:
            return

        if confirmar(f"Deseja esvaziar o carrinho de '{cliente.nome}'?"):
            self.pedido_service.limpar_carrinho(cliente.id)
            print("\n  [OK] Carrinho esvaziado com sucesso!")
        else:
            print("\n  Operação cancelada.")

    # =================================================================
    # 4. GESTÃO DE PEDIDOS
    # =================================================================
    def menu_pedidos(self) -> None:
        """Submenu com operações completas de pedidos."""
        while True:
            titulo("GESTÃO DE PEDIDOS E VENDAS")
            print("  [1] Finalizar Compra do Carrinho")
            print("  [2] Listar Histórico Geral de Pedidos")
            print("  [3] Filtrar Pedidos por Cliente")
            print("  [4] Cancelar Pedido (Devolve Estoque)")
            print("  [0] Voltar ao Menu Principal")
            linha()

            opcao = ler_inteiro("Opção: ", 0, 4)
            if opcao == 0:
                break
            elif opcao == 1:
                self._finalizar_compra()
            elif opcao == 2:
                self._listar_historico_geral()
            elif opcao == 3:
                self._filtrar_pedidos_cliente()
            elif opcao == 4:
                self._cancelar_pedido()

            input("\nPressione [Enter] para continuar...")

    def _finalizar_compra(self) -> None:
        titulo("FINALIZAR COMPRA DO CARRINHO")
        cliente = self._selecionar_cliente()
        if not cliente:
            return

        carrinho = cliente.carrinho
        if carrinho.esta_vazio():
            print(f"  [!] O carrinho de '{cliente.nome}' está vazio.")
            return

        # Prévia do pedido antes da confirmação via função compartilhada de cálculo de frete
        print(f"\nResumo prévio da compra para {cliente.nome}:")
        linha("-")
        resumo = calcular_resumo_frete(carrinho)

        for item_det in resumo.itens:
            print(
                f"   • {item_det.nome} ({item_det.tipo}) x{item_det.quantidade:02d} | "
                f"Unitário: {moeda(item_det.preco_unitario)} | Subtotal: {moeda(item_det.subtotal)} | "
                f"Frete Variável: {moeda(item_det.frete)}"
            )

        print(f"\nSubtotal Produtos:          {moeda(resumo.subtotal_produtos)}")
        if resumo.tem_produto_fisico:
            print(f"Frete Variável (Peso):      {moeda(resumo.frete_variavel)}")
            print(f"Taxa Fixa do Pedido Físico: {moeda(resumo.taxa_fixa_pedido)} (Cobrada uma única vez por pedido)")
        print(f"Frete Total:                {moeda(resumo.frete_total)}")
        print(f"VALOR TOTAL ESTIMADO:       {moeda(resumo.total_estimado)}")
        linha()

        if not confirmar("Deseja confirmar e finalizar este pedido agora?"):
            print("\n  [i] Operação cancelada. Os itens continuam no carrinho.")
            return

        # Processamento pelo serviço
        pedido = self.pedido_service.finalizar_pedido(cliente.id)
        print(f"\n  [OK] Sucesso! Pedido #{pedido.id:04d} aprovado e registrado!")
        self._exibir_detalhes_pedido(pedido)

    def _exibir_detalhes_pedido(self, pedido: Pedido) -> None:
        """Exibe os dados detalhados e mensagens polimórficas de entrega do pedido."""
        linha("=")
        data_str = pedido.data_criacao.strftime("%d/%m/%Y às %H:%M:%S")
        print(f"PEDIDO #{pedido.id:04d} | Status: {pedido.status.value} | Data: {data_str}")
        print(f"Cliente: {pedido.cliente.nome} <{pedido.cliente.email}>")
        print(f"Endereço de Entrega: {pedido.cliente.endereco}")
        linha("-")
        print("Itens Comprados:")
        for item in pedido.itens:
            prod = item.produto
            print(
                f"   • {prod.nome} ({prod.tipo()}) x{item.quantidade:02d} | "
                f"Unitário: {moeda(item.preco_unitario)} | "
                f"Subtotal: {moeda(item.subtotal)} | "
                f"Frete: {moeda(item.frete)}"
            )
        linha("-")
        print(f"Subtotal Produtos:          {moeda(pedido.subtotal)}")
        if pedido.tem_produto_fisico:
            print(f"Frete Itens (Peso):         {moeda(pedido.frete_itens)}")
            print(f"Taxa Pedido Físico:         {moeda(pedido.taxa_pedido_fisico)} (Taxa única por pedido)")
        print(f"Frete Total:                {moeda(pedido.frete_total)}")
        print(f"TOTAL DO PEDIDO:            {moeda(pedido.total)}")
        linha("-")

        # [POLIMORFISMO EM AÇÃO]: O método 'mensagem_entrega()' é chamado em cada produto
        # sem checagem de tipo (sem 'isinstance'). Cada subclasse sabe como deve ser entregue!
        print("Instruções de Entrega dos Produtos:")
        for item in pedido.itens:
            print(f"   ► [{item.produto.nome}]: {item.produto.mensagem_entrega()}")
        linha("=")

    def _listar_historico_geral(self) -> None:
        titulo("HISTÓRICO GERAL DE PEDIDOS")
        pedidos = self.pedido_service.listar_pedidos()
        if not pedidos:
            print("  Nenhum pedido foi realizado ainda no sistema.")
            return

        for p in pedidos:
            self._exibir_detalhes_pedido(p)

        linha()
        pedidos_confirmados = [p for p in pedidos if p.status == StatusPedido.CONFIRMADO]
        total_faturado = sum((p.total for p in pedidos_confirmados), Decimal("0.00"))
        print(f"Total de {len(pedidos)} pedido(s) registrado(s) ({len(pedidos_confirmados)} confirmados).")
        print(f"Faturamento Total Líquido Confirmado: {moeda(total_faturado)}")

    def _filtrar_pedidos_cliente(self) -> None:
        titulo("PEDIDOS POR CLIENTE")
        cliente = self._selecionar_cliente()
        if not cliente:
            return

        pedidos = self.pedido_service.listar_pedidos_cliente(cliente.id)
        if not pedidos:
            print(f"  O cliente '{cliente.nome}' ainda não realizou compras.")
            return

        for p in pedidos:
            self._exibir_detalhes_pedido(p)

    def _cancelar_pedido(self) -> None:
        titulo("CANCELAR PEDIDO")
        pedidos = self.pedido_service.listar_pedidos()
        if not pedidos:
            print("  Nenhum pedido registrado para cancelamento.")
            return

        for p in pedidos:
            print(f"  {p.resumo()}")
        linha()

        pid = ler_inteiro("Informe o ID do pedido que deseja cancelar (0 para voltar): ", 0)
        if pid == 0:
            return

        pedido = self.pedido_service.buscar_por_id(pid)
        if pedido.status == StatusPedido.CANCELADO:
            print("  [!] Este pedido já se encontra cancelado.")
            return

        if confirmar(f"Confirma o cancelamento do Pedido #{pedido.id:04d} e a devolução do estoque?"):
            self.pedido_service.cancelar_pedido(pid)
            print(f"\n  [OK] Pedido #{pedido.id:04d} cancelado com sucesso!")
            print("  O estoque dos produtos foi integralmente reposto.")
        else:
            print("\n  Operação cancelada.")

    # =================================================================
    # 5. CARREGAR DADOS DE DEMONSTRAÇÃO
    # =================================================================
    def acao_carregar_demo(self) -> None:
        """Executa a carga de demonstração com proteção contra duplicidade."""
        titulo("CARREGAR DADOS DE EXEMPLO (DEMO)")
        resumo = self.demonstracao_service.carregar_dados_demo()
        print("  [OK] Dados de demonstração carregados com sucesso:")
        print(f"       • Vendedores disponíveis: {resumo['vendedores']}")
        print(f"       • Clientes disponíveis:   {resumo['clientes']}")
        print(f"       • Novos produtos criados: {resumo['produtos_novos']}")
        print(f"       • Total no catálogo:      {resumo['total_produtos']}")
        print("\n  Base pronta para a apresentação e testes!")
        input("\nPressione [Enter] para continuar...")

    # =================================================================
    # 6. REINICIAR / ZERAR BANCO DE DADOS
    # =================================================================
    def acao_reiniciar_banco(self) -> None:
        """Apaga todos os registros do banco de dados para nova gravação limpa."""
        titulo("REINICIAR / ZERAR BANCO DE DADOS")
        print("  [ATENÇÃO] Esta ação apagará permanentemente todos os usuários,")
        print("  produtos, pedidos e itens do carrinho no banco SQLite.")
        linha()
        if confirmar("Deseja realmente apagar todos os dados e reiniciar o banco?"):
            # Usa limpar_tudo() do Database que respeita a ordem de FKs em transação única
            db = self.pedido_service.pedido_repo.db
            db.limpar_tudo()
            # Reseta caches em memória e geradores de ID sequenciais
            for repo in (self.pedido_service.pedido_repo,
                         self.produto_service.produto_repo,
                         self.usuario_service.usuario_repo):
                repo._cache.clear()
                repo._sincronizar_gerador_id()
            print("\n  [OK] Banco de dados reiniciado com sucesso! Todos os dados foram apagados.")
        else:
            print("\n  Operação cancelada. Nenhum dado foi alterado.")
        input("\nPressione [Enter] para continuar...")
