dev:
	uv run uvicorn backend.app.main:app --reload

worker:
	uv run celery -A backend.app.worker worker --loglevel=info --pool=solo

migrate:
	uv run alembic upgrade head