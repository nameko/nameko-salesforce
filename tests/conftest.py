import pytest


@pytest.fixture
def config():
    config = {}
    config['SALESFORCE'] = {
        'USERNAME': 'Rocky',
        'PASSWORD': 'Balboa',
        'SECURITY_TOKEN': 'ABCD1234',
        'SANDBOX': False,
        'API_VERSION': '37.0',
    }
    return config
