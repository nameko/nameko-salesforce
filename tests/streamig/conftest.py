import pytest
import redis


@pytest.fixture
def config():
    config = {}
    config['SALESFORCE'] = {
        'BAYEUX_VERSION': '1.0',
        'BAYEUX_MINIMUM_VERSION': '1.0',
        'USERNAME': 'Rocky',
        'PASSWORD': 'Balboa',
        'SECURITY_TOKEN': 'ABCD1234',
        'SANDBOX': False,
        'API_VERSION': '37.0',
    }
    return config


@pytest.fixture
def redis_uri():
    return 'redis://localhost:6379/11'


@pytest.yield_fixture
def redis_client(redis_uri):
    client = redis.StrictRedis.from_url(redis_uri)
    yield client
    client.flushdb()
