include .env
export

.PHONY: build up down logs psql run-bot create-bot

build:
	docker compose build

up:
	docker compose up -d

down:
	docker compose down

logs:
	docker compose logs -f app

psql:
	docker exec -it $$(docker compose ps -q db) psql -U $(POSTGRES_USER) -d $(POSTGRES_DB)

apply-migrations:
	docker compose run --rm app \
	  uv run alembic upgrade head

# run your bot:
# make run-bot BOT_NAME=<name> [MAX_TWEETS=<n>]
run-bot:
ifndef BOT_NAME
	$(error BOT_NAME is required)
endif
	docker compose run --rm app \
	  uv run -m src.run_bot \
	    --bot-name $(BOT_NAME) \
	    $(if $(MAX_TWEETS),--max-tweets $(MAX_TWEETS))

# create a bot:
# make create-bot BOT_NAME=<name> USERNAME=<user> LOGIN=<login> [PASSWORD=<pw>]
create-bot:
ifndef BOT_NAME
	$(error BOT_NAME is required)
endif
ifndef USERNAME
	$(error USERNAME is required)
endif
ifndef LOGIN
	$(error LOGIN is required)
endif
	docker compose run --rm -e PASSWORD="$(PASSWORD)" app \
	  uv run python3 -m src.bots.create_bot \
	    --bot-name "$(BOT_NAME)" \
	    --username "$(USERNAME)" \
	    --login "$(LOGIN)" \
	    $(if $(PASSWORD),--password "$(PASSWORD)")
