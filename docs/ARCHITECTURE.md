# Diagrama de Arquitetura por Camadas

```mermaid
flowchart TB
    subgraph Clientes["Clientes"]
        APP["App Mobile"]
        WEB["Web Browser"]
        TOTEM["Totem"]
    end

    subgraph API["API Layer - FastAPI"]
        direction LR
        ROUTERS["Routers\n(auth, unidades,\nprodutos, pedidos,\npagamentos, ...)"]
        MIDDLEWARE["Middleware\n(Auth JWT, CORS,\nLogging)"]
    end

    subgraph Application["Application Layer"]
        direction LR
        SERVICES["Services\n(UserService,\nOrderService,\nPaymentService, ...)"]
        SCHEMAS["Schemas / DTOs\n(Pydantic)"]
    end

    subgraph Domain["Domain Layer"]
        direction LR
        MODELS["Entities\n(User, Order,\nProduct, ...)"]
        ENUMS["Enums\n(Role, OrderStatus,\nOrderChannel, ...)"]
        EXCEPTIONS["Exceptions\n(Domain Errors)"]
    end

    subgraph Infrastructure["Infrastructure Layer"]
        direction LR
        DB["Database\nPostgreSQL + SQLModel\n(Alembic Migrations)"]
        SECURITY["Security\nbcrypt + JWT"]
        REDIS["Redis\nToken blocklist + Celery broker"]
        WORKER["Celery\nAsync tasks"]
        MAIL["MailDev / FastAPI Mail\nDevelopment email"]
        LOGS["Logging / Audit"]
    end

    Clientes -->|HTTP/REST| API
    API -->|"Dependency Injection"| Application
    Application --> Domain
    Application --> Infrastructure
    Infrastructure -->|"asyncpg"| DB[(PostgreSQL)]
    Infrastructure --> REDIS
    Infrastructure --> WORKER
    Infrastructure --> MAIL
```
