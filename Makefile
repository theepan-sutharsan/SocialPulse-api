.PHONY: install run seed test lint worker beat snapshots

install:
	pip install -r requirements.txt

run:
	python run.py

seed:
	python seed.py

test:
	pytest -q

lint:
	ruff check app worker tests

format:
	ruff format app worker tests

worker:
	celery -A worker.celery_app.celery worker --loglevel=info

beat:
	celery -A worker.celery_app.celery beat --loglevel=info

snapshots:
	flask --app run.py run-snapshots
