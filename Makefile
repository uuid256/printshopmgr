.PHONY: dev test shell logs demo

dev:          ## Build and start all services (migrations run automatically)
	cp -n .env.example .env 2>/dev/null || true
	docker compose up --build

test:         ## Run the test suite
	docker compose exec web uv run pytest -v

shell:        ## Django shell
	docker compose exec web uv run python manage.py shell

logs:         ## Tail web logs
	docker compose logs -f web

demo:         ## Load demo data (optional, run after dev)
	docker compose exec web uv run python manage.py create_demo_data
