.PHONY: list
list:
	@LC_ALL=C $(MAKE) -pRrq -f $(lastword $(MAKEFILE_LIST)) : 2>/dev/null | awk -v RS= -F: '/^# File/,/^# Finished Make data base/ {if ($$1 !~ "^[#.]") {print $$1}}' | sort | egrep -v -e '^[^[:alnum:]]' -e '^$@$$'

lock:
	poetry lock --no-update
	poetry export --without-hashes --output requirements/requirements.txt
	poetry export --without-hashes --dev --output requirements/requirements-dev.txt
