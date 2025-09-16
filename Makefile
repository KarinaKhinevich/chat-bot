local_run:
	docker compose -f docker-compose.yaml up

local_build:
	docker compose -f docker-compose.yaml up --build

local_build_no_cache:
	docker compose -f docker-compose.yaml build --no-cache && docker compose -f docker-compose.yaml up

local_stop:
	docker compose -f docker-compose.yaml stop

