.PHONY: list docs

list:
	@LC_ALL=C $(MAKE) -pRrq -f $(lastword $(MAKEFILE_LIST)) : 2>/dev/null | awk -v RS= -F: '/^# File/,/^# Finished Make data base/ {if ($$1 !~ "^[#.]") {print $$1}}' | sort | grep -E -v -e '^[^[:alnum:]]' -e '^$@$$'

dev:
	poetry install --with dev --with docs --sync
	pre-commit install

style:
	pre-commit run black -a

lint:
	pre-commit run ruff -a

mypy:
	dmypy run thalassa

test:
	python -m pytest -vlx --durations 10

cov:
	coverage erase
	python -m pytest \
		--numprocesses=auto \
		--durations=10 \
		--cov=thalassa \
		--cov-report term-missing

clean_notebooks:
	pre-commit run nbstripout

exec_notebooks:
	pytest -n auto --nbmake --nbmake-timeout=20 --nbmake-kernel=python3 $$(git ls-files | grep ipynb)

deps:
	pre-commit run poetry-lock -a
	pre-commit run poetry-export -a

docs:
	mkdocs serve
