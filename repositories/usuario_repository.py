"""
=====================================================================
Repositório em Memória de Usuários (repositories/usuario_repository.py)
=====================================================================
Abstrai a persistência dos usuários em memória. Prepara a arquitetura
para o Nível 3, onde a implementação será substituída por SQLite sem
alterar a camada de serviços ou modelos.
=====================================================================
"""

from __future__ import annotations
from typing import Dict, List, Optional
from models.usuario import Usuario, Cliente, Vendedor


class UsuarioRepository:
    """Repositório responsável pelo armazenamento em memória de Usuários."""

    def __init__(self):
        self._dados: Dict[int, Usuario] = {}

    def adicionar(self, usuario: Usuario) -> Usuario:
        """Armazena um novo usuário ou atualiza se já existir."""
        self._dados[usuario.id] = usuario
        return usuario

    def buscar_por_id(self, id_usuario: int) -> Optional[Usuario]:
        """Busca um usuário pelo seu ID."""
        return self._dados.get(id_usuario)

    def buscar_por_email(self, email: str) -> Optional[Usuario]:
        """Busca um usuário pelo seu endereço de e-mail (case-insensitive)."""
        email_limpo = email.strip().lower()
        for usuario in self._dados.values():
            if usuario.email.lower() == email_limpo:
                return usuario
        return None

    def listar(self) -> List[Usuario]:
        """Retorna todos os usuários cadastrados."""
        return list(self._dados.values())

    def listar_clientes(self) -> List[Cliente]:
        """Filtra e retorna apenas clientes cadastrados."""
        return [u for u in self._dados.values() if isinstance(u, Cliente)]

    def listar_vendedores(self) -> List[Vendedor]:
        """Filtra e retorna apenas vendedores cadastrados."""
        return [u for u in self._dados.values() if isinstance(u, Vendedor)]

    def remover(self, id_usuario: int) -> bool:
        """Remove o usuário da memória pelo seu ID."""
        if id_usuario in self._dados:
            del self._dados[id_usuario]
            return True
        return False

    def limpar(self) -> None:
        """Esvazia o repositório (útil para testes unitários)."""
        self._dados.clear()
