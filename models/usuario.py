"""
=====================================================================
Módulo de Modelos de Usuários (models/usuario.py)
=====================================================================
CONCEITOS DE POO APLICADOS NESTE ARQUIVO:
  - [ABSTRAÇÃO / CLASSE ABSTRATA]: 'Usuario' herda de ABC e define o
    método abstrato 'tipo()', impedindo a instanciação direta da classe base.
  - [HERANÇA]: 'Cliente' e 'Vendedor' herdam de 'Usuario', reaproveitando
    atributos e validações comuns (id, nome, email) via 'super().__init__()'.
  - [ENCAPSULAMENTO]: Atributos privados (_nome, _email, _endereco, etc.)
    protegidos por propriedades (@property) e métodos com validação defensiva.
  - [COMPOSIÇÃO]: 'Cliente' cria e detém uma instância exclusiva de
    'Carrinho' durante sua construção.
  - [ASSOCIAÇÃO]:
      - 'Cliente' mantém associação com a lista de 'pedidos' efetuados.
      - 'Vendedor' mantém associação bidirecional com os 'produtos' ofertados.
  - [POLIMORFISMO DE SOBRESCRITA]: Subclasses sobrescrevem 'tipo()' e
    'resumo()' para fornecer representações textuais especializadas.
=====================================================================
"""

from __future__ import annotations
from abc import ABC, abstractmethod
import itertools
from typing import List, Optional, TYPE_CHECKING
from models.pedido import Carrinho
from exceptions import ValorInvalidoError

if TYPE_CHECKING:
    from models.produto import Produto
    from models.pedido import Pedido


class Usuario(ABC):
    """
    [ABSTRAÇÃO / HERANÇA - CLASSE BASE ABSTRATA]
    Define o contrato e os atributos fundamentais comuns a qualquer usuário.
    Não pode ser instanciada diretamente por possuir o método abstrato 'tipo()'.
    """

    _gerador_id = itertools.count(1)

    def __init__(self, nome: str, email: str, id_usuario: Optional[int] = None):
        self._id = id_usuario if id_usuario is not None else next(Usuario._gerador_id)
        self.nome = nome    # Validação executada via setter (@property)
        self.email = email  # Validação executada via setter (@property)

    @classmethod
    def resetar_gerador_id(cls, inicio: int = 1) -> None:
        """Reinicia o gerador sequencial de IDs (útil para testes isolados)."""
        cls._gerador_id = itertools.count(inicio)

    @property
    def id(self) -> int:
        """[ENCAPSULAMENTO]: Identificador numérico único (somente leitura)."""
        return self._id

    @property
    def nome(self) -> str:
        """[ENCAPSULAMENTO]: Nome do usuário."""
        return self._nome

    @nome.setter
    def nome(self, valor: str) -> None:
        """[ENCAPSULAMENTO]: Valida e atualiza o nome do usuário."""
        if not isinstance(valor, str) or not valor.strip():
            raise ValorInvalidoError("O nome do usuário não pode ser vazio.")
        self._nome = valor.strip()

    @property
    def email(self) -> str:
        """[ENCAPSULAMENTO]: E-mail do usuário."""
        return self._email

    @email.setter
    def email(self, valor: str) -> None:
        """[ENCAPSULAMENTO]: Valida e normaliza o e-mail do usuário."""
        if not isinstance(valor, str) or "@" not in valor or not valor.strip():
            raise ValorInvalidoError("Formato de e-mail inválido. Deve conter '@' e não ser vazio.")
        self._email = valor.strip().lower()

    @abstractmethod
    def tipo(self) -> str:
        """
        [ABSTRAÇÃO / POLIMORFISMO]
        Método abstrato obrigatório que retorna a identificação do tipo de perfil.
        """
        pass

    def resumo(self) -> str:
        """[POLIMORFISMO]: Retorna descrição textual dos dados do usuário."""
        return f"[{self.id:03d}] {self.tipo():<8} | {self.nome} <{self.email}>"


class Cliente(Usuario):
    """
    [HERANÇA] Subclasse concreta de Usuario representando compradores.
      - [COMPOSIÇÃO]: Instancia e possui com exclusividade o seu 'Carrinho'.
      - [ASSOCIAÇÃO]: Mantém referência ao histórico de 'pedidos' que realizou.
    """

    def __init__(self, nome: str, email: str, endereco: str, id_usuario: Optional[int] = None):
        super().__init__(nome, email, id_usuario)
        self.endereco = endereco
        self._carrinho = Carrinho()      # [COMPOSIÇÃO]: Carrinho privativo do cliente
        self._pedidos: List[Pedido] = []  # [ASSOCIAÇÃO]: Histórico de pedidos realizados

    @property
    def endereco(self) -> str:
        """[ENCAPSULAMENTO]: Endereço de entrega."""
        return self._endereco

    @endereco.setter
    def endereco(self, valor: str) -> None:
        """[ENCAPSULAMENTO]: Validação do endereço do cliente."""
        if not isinstance(valor, str) or not valor.strip():
            raise ValorInvalidoError("O endereço de entrega não pode ser vazio.")
        self._endereco = valor.strip()

    @property
    def carrinho(self) -> Carrinho:
        """[COMPOSIÇÃO / ENCAPSULAMENTO]: Acesso ao carrinho privativo do cliente."""
        return self._carrinho

    @property
    def pedidos(self) -> List[Pedido]:
        """[ASSOCIAÇÃO / ENCAPSULAMENTO]: Lista de pedidos realizados pelo cliente."""
        return self._pedidos

    def adicionar_pedido(self, pedido: Pedido) -> None:
        """[ASSOCIAÇÃO]: Registra um novo pedido no histórico do cliente."""
        self._pedidos.append(pedido)

    def tipo(self) -> str:
        """[POLIMORFISMO DE SOBRESCRITA]: Identificador do perfil de comprador."""
        return "Cliente"

    def resumo(self) -> str:
        """[POLIMORFISMO DE SOBRESCRITA]: Resumo especializado com endereço de entrega."""
        return f"{super().resumo()} | Endereço: {self.endereco}"


class Vendedor(Usuario):
    """
    [HERANÇA] Subclasse concreta de Usuario representando lojas parceiras.
      - [ASSOCIAÇÃO]: Mantém a lista de 'produtos' anunciados pela sua loja.
    """

    def __init__(self, nome: str, email: str, nome_loja: str, id_usuario: Optional[int] = None):
        super().__init__(nome, email, id_usuario)
        self.nome_loja = nome_loja
        self._produtos: List[Produto] = []  # [ASSOCIAÇÃO]: Catálogo de produtos da loja

    @property
    def nome_loja(self) -> str:
        """[ENCAPSULAMENTO]: Nome fantasia da loja do vendedor."""
        return self._nome_loja

    @nome_loja.setter
    def nome_loja(self, valor: str) -> None:
        """[ENCAPSULAMENTO]: Valida o nome fantasia da loja."""
        if not isinstance(valor, str) or not valor.strip():
            raise ValorInvalidoError("O nome da loja não pode ser vazio.")
        self._nome_loja = valor.strip()

    @property
    def produtos(self) -> List[Produto]:
        """[ASSOCIAÇÃO / ENCAPSULAMENTO]: Catálogo de produtos anunciados pelo vendedor."""
        return self._produtos

    def adicionar_produto(self, produto: Produto) -> None:
        """[ASSOCIAÇÃO]: Vincula um produto ao catálogo do vendedor."""
        if produto not in self._produtos:
            self._produtos.append(produto)

    def remover_produto(self, produto: Produto) -> None:
        """[ASSOCIAÇÃO]: Desvincula um produto do catálogo do vendedor."""
        if produto in self._produtos:
            self._produtos.remove(produto)

    def tipo(self) -> str:
        """[POLIMORFISMO DE SOBRESCRITA]: Identificador do perfil de parceiro comercial."""
        return "Vendedor"

    def resumo(self) -> str:
        """[POLIMORFISMO DE SOBRESCRITA]: Resumo especializado com dados da loja."""
        return f"{super().resumo()} | Loja: {self.nome_loja} | Produtos: {len(self._produtos)}"
