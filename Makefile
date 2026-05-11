.PHONY: build dev lint test check
VENV_BIN ?= .venv/bin

setup:
	@command -v uv >/dev/null 2>&1 || pip install uv --break-system-packages
	@[ -d .venv ] || uv venv .venv --python 3.11
	. .venv/bin/activate && uv pip install -r requirements.txt
	@command -v pnpm >/dev/null 2>&1 || npm i -g pnpm
	pnpm i

build:
	pnpm build

compile:
	$(VENV_BIN)/uv pip compile requirements.in -o requirements.txt

dev:
	$(VENV_BIN)/python run.py

deploy:
	sudo docker compose up -d --build

lint:
	pnpm lint
	$(VENV_BIN)/ruff check --fix
	$(VENV_BIN)/mypy .

test:
	$(VENV_BIN)/python -m pytest . -q

check: lint test
run: build dev
