# Diagrama de Casos de Uso

```mermaid
flowchart LR
    %% Atores
    Cliente(["Cliente\nApp / Web / Totem"])
    Atendente(["Atendente\nBalcão"])
    Cozinha(["Cozinha"])
    Gerente(["Gerente / Admin"])
    Gateway(["Gateway de Pagamento\nMock"])

    %% Autenticação
    subgraph AUTH["Autenticação"]
        UC1["UC1 - Realizar Cadastro"]
        UC2["UC2 - Autenticar (Login)"]
    end

    %% Cardápio
    subgraph CARD["Cardápio"]
        UC3["UC3 - Visualizar Cardápio por Unidade"]
    end

    %% Pedido
    subgraph PEDIDO["Pedido"]
        UC4["UC4 - Realizar Pedido (canalPedido)"]
        UC5["UC5 - Cancelar Pedido"]
        UC6["UC6 - Consultar Pedidos"]
    end

    %% Cozinha
    subgraph COZ["Cozinha"]
        UC7["UC7 - Atualizar Status do Pedido"]
    end

    %% Pagamento
    subgraph PAG["Pagamento"]
        UC8["UC8 - Solicitar Pagamento (Mock)"]
        UC9["UC9 - Confirmar Retorno do Pagamento"]
    end

    %% Fidelidade
    subgraph FID["Fidelidade"]
        UC10["UC10 - Consultar Pontos"]
        UC11["UC11 - Resgatar Pontos"]
    end

    %% Estoque
    subgraph EST["Estoque"]
        UC12["UC12 - Gerenciar Estoque"]
        UC13["UC13 - Consultar Saldo por Unidade"]
    end

    %% Administração
    subgraph ADM["Administração"]
        UC14["UC14 - Gerenciar Unidades"]
        UC15["UC15 - Gerenciar Produtos"]
        UC16["UC16 - Gerenciar Promoções"]
        UC17["UC17 - Gerenciar Usuários"]
    end

    %% LGPD
    subgraph LGPD["LGPD"]
        UC18["UC18 - Registrar Consentimento"]
        UC19["UC19 - Consultar Logs de Auditoria"]
    end

    %% Relacionamentos - Cliente
    Cliente --> UC1 & UC2 & UC3 & UC4 & UC5 & UC6 & UC10 & UC11 & UC18

    %% Relacionamentos - Atendente
    Atendente --> UC2 & UC4 & UC6

    %% Relacionamentos - Cozinha
    Cozinha --> UC2 & UC7 & UC6

    %% Relacionamentos - Gerente
    Gerente --> UC2 & UC12 & UC13 & UC14 & UC15 & UC16 & UC17 & UC19

    %% Include / Extend / Comunicação
    UC4 -.->|«include»| UC8
    UC8 -->|«comunica»| Gateway
    UC9 -->|«retorno»| Gateway
    UC5 -.->|«extend»| UC7
```
