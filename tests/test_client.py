import collections

from mock import Mock
from nameko.exceptions import ConfigurationError
import pytest

from nameko_salesforce import constants
from nameko_salesforce.client import SalesForceBayeuxClient


class TestSalesForceBayeuxClient:

    @pytest.fixture
    def config(self):
        config = {}
        config['SALESFORCE'] = {
            'BAYEUX_VERSION': '1.0',
            'BAYEUX_MINIMUM_VERSION': '1.0',
            'USERNAME': 'Rocky',
            'PASSWORD': 'Balboa',
            'SECURITY_TOKEN': 'ABCD1234',
            'SANDBOX': False,
        }
        return config

    @pytest.fixture
    def container(self, config):
        container = collections.namedtuple('container', ('config',))
        container.config = config
        return container

    @pytest.fixture
    def client(self, container):
        client = SalesForceBayeuxClient()
        client.container = container
        client.setup()
        return client

    def test_setup(self, client, config):
        assert client.version == config['SALESFORCE']['BAYEUX_VERSION']
        assert client.minimum_version == (
            config['SALESFORCE']['BAYEUX_MINIMUM_VERSION'])
        assert client.username == config['SALESFORCE']['USERNAME']
        assert client.password == config['SALESFORCE']['PASSWORD']
        assert client.security_token == config['SALESFORCE']['SECURITY_TOKEN']
        assert client.sandbox == config['SALESFORCE']['SANDBOX']

    def test_setup_main_config_key_failure(self, container):

        container.config.pop('SALESFORCE')

        client = SalesForceBayeuxClient()
        client.container = container

        with pytest.raises(ConfigurationError) as exc:
            client.setup()

        assert str(exc.value) == '`SALESFORCE` config key not found'

    @pytest.mark.parametrize(
        'key', ('USERNAME', 'PASSWORD', 'SECURITY_TOKEN', 'SANDBOX')
    )
    def test_setup_main_config_key_failures(self, container, key):

        container.config[constants.CONFIG_KEY].pop(key)

        client = SalesForceBayeuxClient()
        client.container = container

        with pytest.raises(ConfigurationError) as exc:
            client.setup()

        expected_error = (
            '`{}` configuration does not contain mandatory `{}` key'
            .format(constants.CONFIG_KEY, key))
        assert str(exc.value) == expected_error

