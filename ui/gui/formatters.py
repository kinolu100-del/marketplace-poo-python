"""
=====================================================================
Formatadores de Dados para Tabelas GUI (ui/gui/formatters.py)
=====================================================================
Funções puras desacopladas de qualquer widget visual, facilitando
testes unitários isolados da camada de apresentação.
=====================================================================
"""

from __future__ import annotations
from typing import Tuple, Any
from ui.helpers import moeda


def formatar_usuario_tabela(usuario: Any) -> Tuple[str, str, str, str, str]:
    """
    Formata um objeto Cliente ou Vendedor para linha de Treeview:
    Retorno: (ID, Tipo, Nome, E-mail, Detalhes de Endereço/Loja)
    """
    uid_str = f"#{usuario.id:03d}"
    tipo_str = usuario.tipo()
    nome_str = usuario.nome
    email_str = usuario.email

    if tipo_str == "Cliente":
        detalhe_str = f"Endereço: {getattr(usuario, 'endereco', '')}"
    else:
        detalhe_str = f"Loja: {getattr(usuario, 'nome_loja', '')}"

    return (uid_str, tipo_str, nome_str, email_str, detalhe_str)


def formatar_produto_tabela(produto: Any) -> Tuple[str, str, str, str, str, str, str]:
    """
    Formata um ProdutoFisico ou ProdutoDigital para linha de Treeview:
    Retorno: (ID, Nome, Tipo, Preço, Estoque, Vendedor, Detalhes Extras)
    """
    pid_str = f"#{produto.id:03d}"
    nome_str = produto.nome
    tipo_str = produto.tipo()
    preco_str = moeda(produto.preco)
    estoque_str = str(produto.estoque)
    vendedor_str = f"{produto.vendedor.nome} (#{produto.vendedor.id})"

    if tipo_str == "Físico":
        detalhe_str = f"Peso: {produto.peso_kg:.2f} kg"
    else:
        detalhe_str = f"{produto.tamanho_mb:.1f} MB | {produto.link_download}"

    return (pid_str, nome_str, tipo_str, preco_str, estoque_str, vendedor_str, detalhe_str)


def formatar_item_carrinho_tabela(item: Any) -> Tuple[str, str, str, str, str, str, str]:
    """
    Formata um ItemCarrinho para linha de Treeview:
    Retorno: (ID Produto, Nome, Tipo, Preço Unit., Quantidade, Subtotal, Estoque Disp.)
    """
    prod = item.produto
    pid_str = f"#{prod.id:03d}"
    nome_str = prod.nome
    tipo_str = prod.tipo()
    preco_str = moeda(prod.preco)
    qtd_str = str(item.quantidade)
    subtotal_str = moeda(item.subtotal)
    estoque_str = str(prod.estoque)

    return (pid_str, nome_str, tipo_str, preco_str, qtd_str, subtotal_str, estoque_str)


def formatar_pedido_tabela(pedido: Any) -> Tuple[str, str, str, str, str, str, str, str]:
    """
    Formata um Pedido para linha de Treeview:
    Retorno: (ID, Data/Hora, Cliente, Qtd Unidades, Subtotal, Frete Total, Total Geral, Status)
    """
    pid_str = f"#{pedido.id:04d}"
    data_str = pedido.data_criacao.strftime("%d/%m/%Y %H:%M")
    cliente_str = f"{pedido.cliente.nome} (#{pedido.cliente.id})"
    qtd_total = sum(i.quantidade for i in pedido.itens)
    itens_str = f"{qtd_total} unid. ({len(pedido.itens)} itens)"
    subtotal_str = moeda(pedido.subtotal)
    frete_str = moeda(pedido.frete_total)
    total_str = moeda(pedido.total)
    status_str = pedido.status.value

    return (
        pid_str,
        data_str,
        cliente_str,
        itens_str,
        subtotal_str,
        frete_str,
        total_str,
        status_str,
    )
