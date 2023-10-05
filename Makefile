.PHONY: list docs

list:
	@LC_ALL=C $(MAKE) -pRrq -f $(lastword $(MAKEFILE_LIST)) : 2>/dev/null | awk -v RS= -F: '/^# File/,/^# Finished Make data base/ {if ($$1 !~ "^[#.]") {print $$1}}' | sort | grep -E -v -e '^[^[:alnum:]]' -e '^$@$$'

init:
	poetry install --with dev --sync
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
	python -m pytest --cov=thalassa --cov-report term-missing --durations=10

clean_notebooks:
	pre-commit run nbstripout

exec_notebooks:
	set -e; \
	for file in $$(git -C notebooks ls-files); do \
		echo $$file; \
		timeout 600 papermill --start-timeout 1 --cwd notebooks notebooks/$$file --progress-bar /dev/null; \
	done

deps:
	pre-commit run poetry-lock -a
	pre-commit run poetry-export -a

docs:
	mkdocs serve
