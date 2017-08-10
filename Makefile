test: flake8 pylint pytest

flake8:
	flake8 nameko_salesforce tests

pylint:
	pylint nameko_salesforce -E

pytest:
	coverage run --concurrency=eventlet --source nameko_salesforce --branch -m pytest tests
	coverage report --show-missing --fail-under=100
