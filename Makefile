COMPOSE_FILE = docker-compose.development.yml

.PHONY: help docker-up docker-down docker-down-clean api-migration api-dev api-worker api-worker-beat api-worker-ui

help:
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

docker-up:  						## Sobe os containers de desenvolvimento
	docker compose -f $(COMPOSE_FILE) up -d

docker-down:  					## Para os containers de desenvolvimento
	docker compose -f $(COMPOSE_FILE) down

docker-down-clean:  		## Para os containers de desenvolvimento e exclui os volumes
	docker compose -f $(COMPOSE_FILE) down -v --remove-orphans

docker-logs: 						## Mostra os logs dos containers em tempo real
	docker compose -f $(COMPOSE_FILE) logs -f

api-create-migration:		## Cria uma nova migration com base nas mudanças do modelo. Ex.: make api-create-migration m="commit message"
	uv run alembic revision --autogenerate -m "$(m)"

api-migration:  				## Executa as migrations pendentes no banco
	uv run alembic upgrade head

api-dev:								## Roda as migrations e sobe a aplicação (API) em modo desenvolvimento
	make api-migration && uv run uvicorn src.app:app --reload --host 0.0.0.0 --port 8000

api-worker:							## Roda o worker do Celery para processar tarefas assíncronas
	uv run celery -A src.worker.celery_app worker --loglevel=info

api-worker-beat:				## Roda o Celery Beat para agendamento de tarefas periódicas
	uv run celery -A src.worker.celery_app beat --loglevel=info

api-worker-ui:					## Roda a interface do Celery Flower para monitoramento dos workers
	uv run celery -A src.worker.celery_app flower --port=5555
