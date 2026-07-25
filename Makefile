install:
	uv sync

run:
	uv run python -m src

debug:
	uv run python -m pdb -m src

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	rm -rf .mypy_cache
	rm -rf .pytest_cache
	rm -rf data/output

lint:
	uv run flake8 . --exclude=.venv,llm_sdk
	uv run mypy src --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs

lint-strict:
	uv run flake8 . --exclude=.venv,llm_sdk
	uv run mypy src --strict --ignore-missing-imports


.PHONY: install run debug clean lint lint-strict
