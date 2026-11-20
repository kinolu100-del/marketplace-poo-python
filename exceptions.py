"""
=====================================================================
Módulo de Exceções de Domínio do Marketplace (exceptions.py)
=====================================================================
Define as exceções de negócio do sistema para desacoplar a camada de
regras de negócio de qualquer interface gráfica ou de console (I/O).
=====================================================================
"""


class MarketplaceError(Exception):
    """Classe base para todas as exceções de regra de negócio do Marketplace."""
    pass


class EstoqueInsuficienteError(MarketplaceError, ValueError):
    """
    Lançada quando uma operação tenta baixar mais estoque do que o disponível.
    Herda também de ValueError para compatibilidade com verificações padrão.
    """
    def __init__(self, produto_nome: str, disponivel: int, solicitado: int):
        self.produto_nome = produto_nome
        self.disponivel = disponivel
        self.solicitado = solicitado
        super().__init__(
            f"Estoque insuficiente para '{produto_nome}'. Disponível: {disponivel}, Solicitado: {solicitado}."
        )


class EntidadeNaoEncontradaError(MarketplaceError, LookupError):
    """Lançada quando um usuário, produto ou pedido com determinado ID não for localizado."""
    def __init__(self, tipo_entidade: str, identificador: object):
        self.tipo_entidade = tipo_entidade
        self.identificador = identificador
        super().__init__(f"{tipo_entidade} com identificador '{identificador}' não foi encontrado(a).")


class EmailDuplicadoError(MarketplaceError, ValueError):
    """Lançada na tentativa de cadastrar um usuário com e-mail já existente na base."""
    def __init__(self, email: str):
        self.email = email
        super().__init__(f"O endereço de e-mail '{email}' já está cadastrado no sistema.")


class OperacaoInvalidaError(MarketplaceError):
    """Lançada quando uma ação infringe uma invariante ou regra de negócio."""
    pass


class ValorInvalidoError(MarketplaceError, ValueError):
    """
    Lançada quando valores monetários, textuais ou quantidades violam os limites.
    Herda de ValueError para conformidade estrita com validações clássicas de tipos.
    """
    pass


class BancoDeDadosError(MarketplaceError):
    """
    Lançada em falhas operacionais ou de persistência do banco de dados relacional.
    Desacopla erros de sqlite3 da camada de aplicação e interface.
    """
    def __init__(self, mensagem: str, causa: object = None):
        self.causa = causa
        super().__init__(mensagem)
