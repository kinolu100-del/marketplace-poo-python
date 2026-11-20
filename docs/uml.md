# Diagrama de Classes UML - Marketplace POO

Este documento apresenta a modelagem completa da arquitetura orientada a objetos do Marketplace, cobrindo todas as cinco relações fundamentais exigidas no Nível 1: **Herança**, **Polimorfismo**, **Composição**, **Associação** e **Dependência**.

---

## Diagrama de Classes (Mermaid)

```mermaid
classDiagram
    direction TB

    %% Classes Abstratas e Enumerações
    class Usuario {
        <<abstract>>
        #int _id
        #str _nome
        #str _email
        +id() int
        +nome() str
        +nome(valor: str)
        +email() str
        +email(valor: str)
        +tipo()* str
        +resumo() str
    }

    class Produto {
        <<abstract>>
        #int _id
        #str _nome
        #Decimal _preco
        #int _estoque
        #Vendedor _vendedor
        +id() int
        +nome() str
        +preco() Decimal
        +estoque() int
        +vendedor() Vendedor
        +baixar_estoque(qtd: int)
        +repor_estoque(qtd: int)
        +calcular_frete(quantidade: int)* Decimal
        +exibir_detalhes()* str
        +mensagem_entrega()* str
        +tipo() str
        +cabecalho() str
    }

    class StatusPedido {
        <<enumeration>>
        CONFIRMADO
        CANCELADO
    }

    %% Subclasses de Usuario
    class Cliente {
        #str _endereco
        #Carrinho _carrinho
        #List~Pedido~ _pedidos
        +endereco() str
        +carrinho() Carrinho
        +pedidos() List~Pedido~
        +adicionar_pedido(pedido: Pedido)
        +tipo() str
        +resumo() str
    }

    class Vendedor {
        #str _nome_loja
        #List~Produto~ _produtos
        +nome_loja() str
        +produtos() List~Produto~
        +adicionar_produto(produto: Produto)
        +remover_produto(produto: Produto)
        +tipo() str
        +resumo() str
    }

    %% Subclasses de Produto
    class ProdutoFisico {
        -Decimal VALOR_POR_KG = 3.50
        #Decimal _peso_kg
        +peso_kg() Decimal
        +tipo() str
        +calcular_frete(quantidade: int) Decimal
        +exibir_detalhes() str
        +mensagem_entrega() str
    }

    class ProdutoDigital {
        #Decimal _tamanho_mb
        #str _link_download
        +tamanho_mb() Decimal
        +link_download() str
        +tipo() str
        +calcular_frete(quantidade: int) Decimal
        +exibir_detalhes() str
        +mensagem_entrega() str
    }

    %% Carrinho e Itens
    class ItemCarrinho {
        +Produto produto
        +int quantidade
        +subtotal() Decimal
    }

    class Carrinho {
        #dict _itens
        +itens() List~ItemCarrinho~
        +subtotal() Decimal
        +adicionar(produto: Produto, qtd: int)
        +remover(produto: Produto)
        +alterar_quantidade(produto: Produto, nova_qtd: int)
        +quantidade_de(produto: Produto) int
        +esta_vazio() bool
        +limpar()
    }

    %% Pedido e Itens
    class ItemPedido {
        #Produto _produto
        #int _quantidade
        #Decimal _preco_unitario
        #Decimal _frete
        +produto() Produto
        +quantidade() int
        +preco_unitario() Decimal
        +frete() Decimal
        +subtotal() Decimal
        +total() Decimal
    }

    class Pedido {
        -Decimal TAXA_PEDIDO_FISICO = 10.00
        #int _id
        #Cliente _cliente
        #List~ItemPedido~ _itens
        #datetime _data_criacao
        #StatusPedido _status
        +id() int
        +cliente() Cliente
        +itens() List~ItemPedido~
        +status() StatusPedido
        +subtotal() Decimal
        +frete_itens() Decimal
        +taxa_pedido_fisico() Decimal
        +frete_total() Decimal
        +total() Decimal
        +tem_produto_fisico() bool
        +adicionar_item(produto: Produto, qtd: int)
        +cancelar()
        +resumo() str
    }

    %% Camada de Serviços (Regras de Negócio)
    class UsuarioService {
        +cadastrar_cliente(...) Cliente
        +cadastrar_vendedor(...) Vendedor
        +editar_usuario(...) Usuario
        +remover_usuario(id: int)
        +listar_usuarios() List~Usuario~
    }

    class ProdutoService {
        +cadastrar_produto_fisico(...) ProdutoFisico
        +cadastrar_produto_digital(...) ProdutoDigital
        +editar_produto(...) Produto
        +remover_produto(id: int)
        +listar_produtos() List~Produto~
        +listar_por_vendedor(id: int) List~Produto~
    }

    class PedidoService {
        +adicionar_ao_carrinho(...)
        +remover_do_carrinho(...)
        +alterar_quantidade_carrinho(...)
        +limpar_carrinho(...)
        +finalizar_pedido(cliente_id: int) Pedido
        +cancelar_pedido(pedido_id: int) Pedido
        +listar_pedidos() List~Pedido~
    }

    %% RELAÇÕES DE POO:

    %% 1. Herança
    Usuario <|-- Cliente : Herança
    Usuario <|-- Vendedor : Herança
    Produto <|-- ProdutoFisico : Herança
    Produto <|-- ProdutoDigital : Herança

    %% 2. Composição (Losango preenchido: todo-parte com ciclo de vida acoplado)
    Cliente "1" *-- "1" Carrinho : [Composição] possui privativo
    Pedido "1" *-- "1..*" ItemPedido : [Composição] cria e gerencia
    Carrinho "1" *-- "0..*" ItemCarrinho : [Composição] contém

    %% 3. Associação (Linha contínua com multiplicidades)
    Vendedor "1" -- "0..*" Produto : [Associação] anuncia / catálogo
    Cliente "1" -- "0..*" Pedido : [Associação] histórico de compras
    ItemPedido "*" --> "1" Produto : [Associação] referencia
    ItemCarrinho "*" --> "1" Produto : [Associação] referencia
    Pedido --> "1" StatusPedido : [Associação] estado atual

    %% 4. Dependência (Setas tracejadas: uso em parâmetros / métodos sem reter estado forte)
    Pedido ..> Produto : [Dependência] adicionar_item(produto, qtd)
    Carrinho ..> Produto : [Dependência] adicionar/remover(produto)
    PedidoService ..> Pedido : [Dependência] orquestra fluxo
    PedidoService ..> Carrinho : [Dependência] manipula itens
    ProdutoService ..> Produto : [Dependência] gerencia catálogo
    UsuarioService ..> Usuario : [Dependência] gerencia perfis
```

---

## 🗄️ Diagrama Entidade-Relacionamento (ER - Nível 3 / SQLite)

Modelagem relacional implementada no banco de dados SQLite (`marketplace.db`) via `database/schema.py`:

```mermaid
erDiagram
    USUARIOS {
        INTEGER id PK "AUTOINCREMENT"
        TEXT nome "NOT NULL"
        TEXT email UK "NOT NULL, UNIQUE"
        TEXT tipo "NOT NULL (Cliente | Vendedor)"
        TEXT endereco "Exclusivo Cliente"
        TEXT nome_loja "Exclusivo Vendedor"
    }

    PRODUTOS {
        INTEGER id PK "AUTOINCREMENT"
        TEXT nome "NOT NULL"
        TEXT preco "NOT NULL (formato Decimal 0.00)"
        INTEGER estoque "NOT NULL, >= 0"
        TEXT tipo "NOT NULL (Físico | Digital)"
        INTEGER vendedor_id FK "REFERENCES usuarios(id)"
        TEXT peso_kg "Exclusivo Físico"
        TEXT tamanho_mb "Exclusivo Digital"
        TEXT link_download "Exclusivo Digital"
    }

    CARRINHO_ITENS {
        INTEGER cliente_id PK,FK "REFERENCES usuarios(id) ON DELETE CASCADE"
        INTEGER produto_id PK,FK "REFERENCES produtos(id) ON DELETE CASCADE"
        INTEGER quantidade "NOT NULL, > 0"
    }

    PEDIDOS {
        INTEGER id PK "AUTOINCREMENT"
        INTEGER cliente_id FK "REFERENCES usuarios(id)"
        TEXT status "NOT NULL (Confirmado | Cancelado)"
        TEXT data_criacao "NOT NULL (ISO 8601)"
    }

    ITENS_PEDIDO {
        INTEGER id PK "AUTOINCREMENT"
        INTEGER pedido_id FK "REFERENCES pedidos(id) ON DELETE CASCADE"
        INTEGER produto_id FK "REFERENCES produtos(id) ON DELETE CASCADE"
        INTEGER quantidade "NOT NULL, > 0"
        TEXT preco_unitario "NOT NULL (congelado)"
        TEXT frete "NOT NULL (congelado)"
    }

    USUARIOS ||--o{ PRODUTOS : "1:N anuncia (Vendedor)"
    USUARIOS ||--o{ PEDIDOS : "1:N realiza (Cliente)"
    USUARIOS ||--o{ CARRINHO_ITENS : "1:N compõe cesta (Cliente)"
    PRODUTOS ||--o{ CARRINHO_ITENS : "1:N presente em"
    PEDIDOS ||--|{ ITENS_PEDIDO : "1:N compõe"
    PRODUTOS ||--o{ ITENS_PEDIDO : "1:N comprado em"
```

---

## 🏛️ Camada de Persistência Relacional (Nível 3)

```mermaid
classDiagram
    direction TB

    class Database {
        -str db_path
        -Connection _conn
        +obter_conexao() Connection
        +transacao() Generator
        +limpar_tudo()
        +fechar()
    }

    class UsuarioRepository {
        -Database _db
        -Dict~int, Usuario~ _cache
        +adicionar(usuario: Usuario) Usuario
        +buscar_por_id(id: int) Usuario
        +buscar_por_email(email: str) Usuario
        +listar() List~Usuario~
        +listar_clientes() List~Cliente~
        +listar_vendedores() List~Vendedor~
        +remover(id: int) bool
        +limpar()
    }

    class ProdutoRepository {
        -Database _db
        -UsuarioRepository _usuario_repo
        -Dict~int, Produto~ _cache
        +adicionar(produto: Produto) Produto
        +buscar_por_id(id: int) Produto
        +listar() List~Produto~
        +listar_por_vendedor(id: int) List~Produto~
        +remover(id: int) bool
        +limpar()
    }

    class PedidoRepository {
        -Database _db
        -UsuarioRepository _usuario_repo
        -ProdutoRepository _produto_repo
        -Dict~int, Pedido~ _cache
        +adicionar(pedido: Pedido) Pedido
        +buscar_por_id(id: int) Pedido
        +listar() List~Pedido~
        +listar_por_cliente(id: int) List~Pedido~
        +remover(id: int) bool
        +limpar()
    }

    class CarrinhoPersistente {
        -int _cliente_id
        -Database _db
        +adicionar(produto: Produto, qtd: int)
        +remover(produto: Produto)
        +alterar_quantidade(produto: Produto, qtd: int)
        +limpar()
    }

    UsuarioRepository ..> Database : transações e conexão
    ProdutoRepository ..> Database : transações e conexão
    PedidoRepository ..> Database : transações e conexão
    CarrinhoPersistente ..> Database : sincronização direta
    ProdutoRepository ..> UsuarioRepository : resolve Vendedor
    PedidoRepository ..> UsuarioRepository : resolve Cliente
    PedidoRepository ..> ProdutoRepository : resolve Produto
```

---

## 📖 Legenda das Relações de POO no Projeto

| Conceito | Representação UML | Aplicação Prática no Código | Explicação Conceitual |
| :--- | :---: | :--- | :--- |
| **Herança** | `A <|-- B` | `Usuario <|-- Cliente, Vendedor`<br>`Produto <|-- ProdutoFisico, ProdutoDigital` | As subclasses herdam atributos e comportamentos da classe base abstrata e invocam `super().__init__()`. |
| **Polimorfismo** | Métodos sobrescritos | `calcular_frete()`, `exibir_detalhes()`, `mensagem_entrega()` | Métodos com a mesma assinatura que executam comportamentos distintos dependendo se o produto é Físico ou Digital. Elimina `isinstance`. |
| **Composição** | `A *-- B` | `Cliente *-- Carrinho`<br>`Pedido *-- ItemPedido`<br>`Carrinho *-- ItemCarrinho` | Relação todo-parte forte: `ItemPedido` e `Carrinho` são criados e destruídos junto com a entidade titular. |
| **Associação** | `A -- B` / `A --> B` | `Vendedor -- Produto`<br>`Cliente -- Pedido`<br>`ItemPedido --> Produto` | Vínculo entre duas classes autônomas: o `ItemPedido` guarda referência ao `Produto` associado; o `Vendedor` conhece seus produtos e o `Produto` conhece seu `Vendedor`. |
| **Dependência** | `A ..> B` | `Pedido ..> Produto`<br>`Carrinho ..> Produto`<br>`Services ..> Models` | Relação fraca/operacional: `Pedido.adicionar_item(produto, qtd)` e `Carrinho.adicionar(produto, qtd)` recebem `Produto` como parâmetro sem que o produto pertença a eles. |

---

## 💰 Regra de Cálculo de Frete

1. **Frete Variável por Produto Físico (Polimórfico):**
   - `ProdutoFisico`: `3.50 * peso_kg * quantidade`
   - `ProdutoDigital`: `R$ 0,00`
2. **Taxa Base por Pedido (Cobrança Única):**
   - Se o pedido contiver **pelo menos um** item físico: adiciona taxa única de **R$ 10,00**.
   - Se o pedido for composto **exclusivamente por itens digitais**: taxa adicional é **R$ 0,00**.
3. **Frete Total:**
   $$\text{Frete Total} = \sum (\text{frete dos itens}) + \text{taxa pedido físico}$$
