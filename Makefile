test: static pylint pytest

static:
	pre-commit run --all-files

pylint:
	pylint nameko_salesforce --disable=R,C,W0221

pytest:
	coverage run --concurrency=eventlet --source nameko_salesforce --branch -m pytest tests
	coverage report --show-missing --fail-under=100

doc:
	$(MAKE) -C docs clean html
