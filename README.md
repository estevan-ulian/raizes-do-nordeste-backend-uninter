# Raizes do Nordeste - Backend

## Requisitos

- Python 3.13+
- [uv](https://docs.astral.sh/uv/)
- [Docker](https://www.docker.com/products/docker-desktop)
- [Make](https://www.gnu.org/software/make/manual)

## Stack

- **FastAPI:** framework web usado para expor a API HTTP.
- **FastAPI Mail:** envio de e-mails da aplicação.
- **SQLModel:** modelagem das entidades e integração com SQLAlchemy.
- **PostgreSQL:** banco de dados relacional da aplicação.
- **Alembic:** controle e execução de migrations do banco.
- **Redis:** backend usado para blocklist de tokens e broker/result backend do Celery.
- **Celery:** processamento de tarefas em segundo plano.
- **Flower:** painel web opcional para monitorar workers e tarefas do Celery.
- **Pydantic Settings:** carregamento e validação das variáveis de ambiente.
- **Ruff:** lint e formatação de código.

## Instalação

1. Clone este repositório
```bash
git clone https://github.com/estevan-ulian/raizes-do-nordeste-backend-uninter.git
cd raizes-do-nordeste-backend-uninter
```

2. Crie/copie o arquivo de variáveis de ambiente
```bash
cp .env.example .env
```

Revise o `.env` antes de subir o projeto, especialmente as portas de PostgreSQL e Redis. O `.env.example` sugere e usa `POSTGRES_PORT=5444` e `REDIS_PORT=6380` para evitar conflito com serviços locais.

## Comandos

### Principais

Sobe os containers de desenvolvimento (PostgreSQL, Redis, MailDev, Adminer):
```bash
make docker-up
```

Roda as migrations e inicia a API:
```bash
make api-dev
```

Worker para executar tarefas em segundo plano:
```bash
make api-worker
```

### Outros comandos úteis

```bash
make help                               # Lista todos os comandos disponíveis
make api-create-migration m="descricao" # Cria uma nova migration
make api-migration                      # Executa migrations pendentes
make api-worker-beat                    # Inicializa o Celery Beat
make api-worker-ui                      # Inicializa o Celery UI
make docker-logs                        # Mostra logs dos containers
make docker-down                        # Para todos containers
make docker-down-clean                  # Para containers e remove volumes
```

> O comando `make docker-down-clean` remove os volumes do Docker, apagando todos os dados salvos no PostgreSQL e Redis.

## Acesso

- **API:** http://localhost:8000/api
- **Swagger:** http://localhost:8000/api/docs
- **ReDoc:** http://localhost:8000/api/redoc
- **MailDev:** http://localhost:1080
- **Adminer:** http://localhost:9192

### Worker UI
Para visualizar os agendamentos e execução das tarefas em segundo plano, rode o comando:
```bash
make api-worker-ui
```
- **Worker UI:** http://localhost:5555

### Adminer

Use os dados do `.env` para acessar o PostgreSQL pelo Adminer:

- **Sistema:** PostgreSQL
- **Servidor:** `database`
- **Usuário:** `POSTGRES_USER`
- **Senha:** `POSTGRES_PASSWORD`
- **Base:** `POSTGRES_DB`


## ToDo

### Infraestrutura e Configuração
- [x] Setup inicial do projeto (FastAPI, SQLModel, Alembic)
- [x] Configuração Docker Compose para ambiente de desenvolvimento (PostgreSQL, Redis, MailDev, Adminer)
- [x] Sistema de variáveis de ambiente (.env e .env.example)
- [x] Configuração Ruff (linting e formatação)
- [x] Makefile com comandos de execução do projeto
- [x] Seeder do primeiro usuário administrador
- [ ] Seeds de desenvolvimento para unidade, produtos, estoque e usuários de teste

### Autenticação e Segurança
- [x] Sistema de autenticação JWT (access + refresh tokens)
- [x] Registro e login de usuários
- [x] Verificação de e-mail com token
- [x] Recuperação de senha
- [x] Hash de senha com bcrypt
- [x] Token blocklist com Redis
- [x] Sistema de roles (ADMIN, MANAGER, KITCHEN, SERVER, CUSTOMER)
- [x] Dependência para autorização por perfil (`RoleChecker`)
- [x] Middleware CORS
- [x] Tratamento padronizado de erros globais e de autenticação
- [ ] Rate limiting

### Modelagem e Arquitetura
- [x] [Diagrama Entidade-Relacionamento](docs/DER.md)
- [x] [Diagrama de Casos de Uso](docs/USE_CASES.md)
- [x] [Diagrama de Classes](docs/CLASSES.md)
- [x] [Diagrama de sequência do fluxo](docs/FLOW.md)
- [x] [Diagrama de arquitetura por camadas](docs/ARCHITECTURE.md)
- [x] Models de domínio criados com SQLModel
- [x] Relationships dos models implementados conforme DER
- [x] Migration dos models de negócio criada
- [ ] Revisar coerência final entre diagramas, enums, migrations, endpoints e regras implementadas
- [ ] Descrever feature crítica com pré-condições, pós-condições, exceções e regras de negócio

### Módulo de Unidades
- [x] Model `Unit`
- [x] CRUD endpoints em `/units`
- [x] Permissões de gerenciamento para ADMIN/MANAGER

### Módulo de Produtos/Cardápio
- [x] Model `Product`
- [x] CRUD endpoints em `/products`
- [x] Listagem de cardápio por unidade
- [x] Paginação e filtros aplicáveis
- [x] Upload local de imagem via `multipart/form-data` e persistência em `image_url`

### Módulo de Estoque
- [x] Model `Inventory`
- [x] Migration da tabela `inventory`
- [x] Restrição única por unidade/produto
- [x] Entrada e saída de estoque por unidade
- [x] Consulta de saldo por unidade
- [x] Bloqueio de venda por estoque insuficiente

### Módulo de Pedidos
- [x] Models `Order` e `OrderItem`
- [x] Campo `order_channel` com ENUM APP, TOTEM, COUNTER, PICKUP e WEB
- [x] Campo `status` alinhado ao DER: WAITING_FOR_PAYMENT, PAID, IN_THE_KITCHEN, READY, DELIVERED, CANCELED
- [x] Criar pedido com `canalPedido`
- [x] Validar itens do pedido e existência de produto/unidade
- [x] Listar/filtrar pedidos por `canalPedido` e `status`
- [x] Atualizar status do pedido com transições válidas
- [x] Cancelar pedido conforme regra de negócio
- [x] CRUD endpoints em `/orders`
- [x] Validação de transições de status

### Módulo de Pagamento (Mock)
- [x] Model `Payment`
- [x] Relacionamento 1:1 entre pedido e pagamento
- [x] Campo `status` alinhado ao DER: PENDING, APPROVED, REJECTED
- [x] Mock gateway de pagamento
- [x] Endpoint `POST /payments`
- [x] Aprovar/recusar pagamento mock e atualizar status do pedido
- [x] Retornar payload de status ao cliente
- [x] Integração com OrderService para marcar pedido como pago

### Módulo de Fidelidade
- [x] Models `LoyaltyAccount` e `LoyaltyRedemption`
- [x] Conta de fidelidade 1:1 por cliente
- [ ] Documentar regra de pontos, saldo, resgate simples e consentimento
- [ ] Endpoints

### Módulo de Promoções
- [x] Models `Promotion` e `OrderPromotion`
- [x] Relacionamento de promoções aplicadas ao pedido
- [x] Regra percentual com período de vigência, ativação e impacto no valor final
- [x] CRUD de promoções e aplicação opcional na criação do pedido

### Logs e Auditoria
- [x] Model `AuditLog`
- [ ] Registrar ações sensíveis: criação de pedido, mudança de status e pagamento
- [ ] Definir política para logs sem usuário autenticado
- [ ] Documentar formato e consulta de logs

### LGPD e Privacidade
- [x] Model `LGPDConsent`
- [ ] Consentimento no cadastro de cliente
- [ ] Documentar finalidade e base legal
- [ ] Documentar minimização de dados pessoais
- [ ] Documentar retenção, exclusão ou anonimização

### API, Contratos e Testes
- [ ] Documentar endpoints
- [ ] Definir contrato por endpoint: método, path, auth/permissões, params, body, response, status codes e exemplo JSON
- [ ] Padronizar paginação com `page` e `limit` nas listagens
- [ ] Criar coleção Postman/Insomnia com fluxo principal
- [x] [Criar plano de testes com pelo menos 10 cenários](docs/TEST_PLAN.md)
- [ ] Documentar ordem de execução dos testes e evidências
