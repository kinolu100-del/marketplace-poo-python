"""
=====================================================================
Módulo de Modelos de Produtos (models/produto.py)
=====================================================================
CONCEITOS DE POO APLICADOS NESTE ARQUIVO:
  - [ABSTRAÇÃO / CLASSE ABSTRATA]: ABC e @abstractmethod definem a interface
    base de Produto (calcular_frete, exibir_detalhes, mensagem_entrega).
    Impede a instanciação direta da classe base abstrata.
  - [HERANÇA]: ProdutoFisico e ProdutoDigital herdam de Produto.
  - [ENCAPSULAMENTO]: Atributos privados (_id, _nome, _preco, _estoque,
    _vendedor, _peso_kg, etc.) acessados e modificados via @property e métodos
    com validação de integridade (baixar_estoque e repor_estoque).
  - [POLIMORFISMO DE SOBRESCRITA]: Cada subclasse implementa
    'calcular_frete()', 'exibir_detalhes()' e 'mensagem_entrega()'
    com comportamentos específicos sem necessidade de checagens com 'isinstance'.
  - [ASSOCIAÇÃO]: O Produto referencia o Vendedor responsável pelo anúncio.
=====================================================================
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from decimal import Decimal, ROUND_HALF_UP
import itertools
from typing import Optional, Union, TYPE_CHECKING
from exceptions import EstoqueInsuficienteError, ValorInvalidoError

if TYPE_CHECKING:
    from models.usuario import Vendedor


def _para_decimal(valor: Union[Decimal, float, int, str], casas: int = 2) -> Decimal:
    """Função utilitária interna para conversão precisa de valores para Decimal."""
    if isinstance(valor, Decimal):
        dec = valor
    elif isinstance(valor, (float, int)):
        dec = Decimal(str(valor))
    elif isinstance(valor, str):
        dec = Decimal(valor.strip().replace(",", "."))
    else:
        raise ValorInvalidoError(f"Tipo inválido para valor monetário ou numérico: {type(valor)}")
    mascara = Decimal("1." + "0" * casas) if casas > 0 else Decimal("1")
    return dec.quantize(mascara, rounding=ROUND_HALF_UP)


class Produto(ABC):
    """
    [ABSTRAÇÃO / HERANÇA - CLASSE BASE ABSTRATA]
    Classe abstrata que define os atributos e contratos comuns a todos os produtos.
    Não pode ser instanciada diretamente (lança TypeError se instanciada).
    """

    _gerador_id = itertools.count(1)

    def __init__(
        self,
        nome: str,
        preco: Union[Decimal, float, int, str],
        estoque: int,
        vendedor: Vendedor,
        id_produto: Optional[int] = None,
    ):
        self._id = id_produto if id_produto is not None else next(Produto._gerador_id)
        self.nome = nome
        self.preco = preco
        self.estoque = estoque
        self._vendedor = vendedor  # [ASSOCIAÇÃO]: Referência ao Vendedor ofertante

    @classmethod
    def resetar_gerador_id(cls, inicio: int = 1) -> None:
        """Reinicia o gerador sequencial de IDs (útil para testes isolados)."""
        cls._gerador_id = itertools.count(inicio)

    @property
    def id(self) -> int:
        """[ENCAPSULAMENTO]: Identificador único do produto (somente leitura)."""
        return self._id

    @property
    def nome(self) -> str:
        """[ENCAPSULAMENTO]: Nome do produto."""
        return self._nome

    @nome.setter
    def nome(self, valor: str) -> None:
        """[ENCAPSULAMENTO]: Validação de nome não vazio."""
        if not isinstance(valor, str) or not valor.strip():
            raise ValorInvalidoError("O nome do produto não pode ser vazio.")
        self._nome = valor.strip()

    @property
    def preco(self) -> Decimal:
        """[ENCAPSULAMENTO / DINHEIRO]: Preço unitário em Decimal com 2 casas."""
        return self._preco

    @preco.setter
    def preco(self, valor: Union[Decimal, float, int, str]) -> None:
        """[ENCAPSULAMENTO]: Validação de preço estritamente positivo (> 0)."""
        dec_valor = _para_decimal(valor, 2)
        if dec_valor <= Decimal("0.00"):
            raise ValorInvalidoError("O preço do produto deve ser estritamente maior que zero.")
        self._preco = dec_valor

    @property
    def estoque(self) -> int:
        """[ENCAPSULAMENTO]: Quantidade atual em estoque."""
        return self._estoque

    @estoque.setter
    def estoque(self, valor: int) -> None:
        """[ENCAPSULAMENTO]: Validação de estoque não negativo."""
        if not isinstance(valor, int) or valor < 0:
            raise ValorInvalidoError("A quantidade em estoque deve ser um número inteiro maior ou igual a zero.")
        self._estoque = valor

    @property
    def vendedor(self) -> Vendedor:
        """[ASSOCIAÇÃO / ENCAPSULAMENTO]: Vendedor responsável pelo produto."""
        return self._vendedor

    def baixar_estoque(self, quantidade: int) -> None:
        """
        [ENCAPSULAMENTO]: Decrementa o estoque de forma segura com validação de saldo.
        Lança EstoqueInsuficienteError (e ValueError) caso a quantidade solicitada exceda o estoque.
        """
        if not isinstance(quantidade, int) or quantidade <= 0:
            raise ValorInvalidoError("A quantidade a ser baixada do estoque deve ser maior que zero.")
        if quantidade > self._estoque:
            raise EstoqueInsuficienteError(self._nome, self._estoque, quantidade)
        self._estoque -= quantidade

    def repor_estoque(self, quantidade: int) -> None:
        """
        [ENCAPSULAMENTO]: Incrementa o estoque após cancelamento ou reposição de mercadoria.
        """
        if not isinstance(quantidade, int) or quantidade <= 0:
            raise ValorInvalidoError("A quantidade a ser reposta no estoque deve ser maior que zero.")
        self._estoque += quantidade

    @abstractmethod
    def calcular_frete(self, quantidade: int) -> Decimal:
        """
        [ABSTRAÇÃO / POLIMORFISMO]
        Calcula o frete variável do produto de acordo com suas características.
        """
        pass

    @abstractmethod
    def exibir_detalhes(self) -> str:
        """
        [ABSTRAÇÃO / POLIMORFISMO]
        Retorna uma representação em texto detalhada e especializada do produto.
        """
        pass

    @abstractmethod
    def mensagem_entrega(self) -> str:
        """
        [ABSTRAÇÃO / POLIMORFISMO]
        Retorna as instruções polimórficas de entrega do item após a confirmação da compra,
        eliminando a necessidade de 'isinstance' no controlador ou serviço.
        """
        pass

    def tipo(self) -> str:
        """Identificador textual do tipo do produto."""
        return "Produto"

    def cabecalho(self) -> str:
        """Retorna os dados gerais comuns do produto sem dependência de UI."""
        return (
            f"[{self.id:03d}] {self.nome} | R$ {self.preco:.2f} | "
            f"Estoque: {self.estoque:02d} un | Vendedor: {self.vendedor.nome_loja}"
        )


class ProdutoFisico(Produto):
    """
    [HERANÇA] Subclasse concreta de Produto para itens tangíveis que exigem transporte.
    Acrescenta o atributo 'peso_kg'.
    """

    # Valor variável por quilograma transportado (Decimal para precisão monetária)
    VALOR_POR_KG = Decimal("3.50")

    def __init__(
        self,
        nome: str,
        preco: Union[Decimal, float, int, str],
        estoque: int,
        vendedor: Vendedor,
        peso_kg: Union[Decimal, float, int, str],
        id_produto: Optional[int] = None,
    ):
        super().__init__(nome, preco, estoque, vendedor, id_produto)
        self.peso_kg = peso_kg

    @property
    def peso_kg(self) -> Decimal:
        """[ENCAPSULAMENTO]: Peso em quilogramas."""
        return self._peso_kg

    @peso_kg.setter
    def peso_kg(self, valor: Union[Decimal, float, int, str]) -> None:
        """[ENCAPSULAMENTO]: Valida peso positivo."""
        dec_peso = _para_decimal(valor, 2)
        if dec_peso <= Decimal("0.00"):
            raise ValorInvalidoError("O peso do produto físico deve ser maior que zero.")
        self._peso_kg = dec_peso

    def tipo(self) -> str:
        return "Físico"

    def calcular_frete(self, quantidade: int) -> Decimal:
        """
        [POLIMORFISMO DE SOBRESCRITA]
        Frete variável do produto físico baseado estritamente no peso e quantidade:
        Frete = VALOR_POR_KG * peso_kg * quantidade.
        (A taxa base por pedido é aplicada no Pedido, uma única vez para o conjunto).
        """
        if quantidade <= 0:
            return Decimal("0.00")
        total_frete = self.VALOR_POR_KG * self._peso_kg * Decimal(str(quantidade))
        return total_frete.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def exibir_detalhes(self) -> str:
        """[POLIMORFISMO DE SOBRESCRITA]: Detalhes especializados para produto físico."""
        return f"{self.cabecalho()} | FÍSICO | Peso: {self.peso_kg:.2f} kg"

    def mensagem_entrega(self) -> str:
        """
        [POLIMORFISMO DE SOBRESCRITA]
        Instruções de envio físico com peso e prazo estimado pela transportadora.
        """
        return f"Envio físico via transportadora. Peso: {self.peso_kg:.2f} kg. Prazo estimado: 5 a 10 dias úteis."


class ProdutoDigital(Produto):
    """
    [HERANÇA] Subclasse concreta de Produto para bens digitais (e-books, softwares, cursos).
    Acrescenta tamanho do arquivo (MB) e link de download.
    """

    def __init__(
        self,
        nome: str,
        preco: Union[Decimal, float, int, str],
        estoque: int,
        vendedor: Vendedor,
        tamanho_mb: Union[Decimal, float, int, str],
        link_download: str,
        id_produto: Optional[int] = None,
    ):
        super().__init__(nome, preco, estoque, vendedor, id_produto)
        self.tamanho_mb = tamanho_mb
        self.link_download = link_download

    @property
    def tamanho_mb(self) -> Decimal:
        """[ENCAPSULAMENTO]: Tamanho do arquivo digital em MB."""
        return self._tamanho_mb

    @tamanho_mb.setter
    def tamanho_mb(self, valor: Union[Decimal, float, int, str]) -> None:
        """[ENCAPSULAMENTO]: Valida tamanho em MB estritamente positivo."""
        dec_mb = _para_decimal(valor, 1)
        if dec_mb <= Decimal("0.0"):
            raise ValorInvalidoError("O tamanho do arquivo digital deve ser maior que zero.")
        self._tamanho_mb = dec_mb

    @property
    def link_download(self) -> str:
        """[ENCAPSULAMENTO]: Link ou URI para acesso ao produto."""
        return self._link_download

    @link_download.setter
    def link_download(self, valor: str) -> None:
        """[ENCAPSULAMENTO]: Valida link de download não vazio."""
        if not isinstance(valor, str) or not valor.strip():
            raise ValorInvalidoError("O link de download não pode ser vazio.")
        self._link_download = valor.strip()

    def tipo(self) -> str:
        return "Digital"

    def calcular_frete(self, quantidade: int) -> Decimal:
        """
        [POLIMORFISMO DE SOBRESCRITA]
        Produtos digitais são entregues pela internet, logo o frete é sempre zero (gratuito).
        """
        return Decimal("0.00")

    def exibir_detalhes(self) -> str:
        """[POLIMORFISMO DE SOBRESCRITA]: Detalhes especializados para produto digital."""
        return f"{self.cabecalho()} | DIGITAL | Arquivo: {self.tamanho_mb:.1f} MB | Entrega: Download"

    def mensagem_entrega(self) -> str:
        """
        [POLIMORFISMO DE SOBRESCRITA]
        Instruções de acesso imediato com liberação do link de download.
        """
        return f"Acesso digital liberado imediatamente. Link de download: {self.link_download}"
