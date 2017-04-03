import collections

from mock import call, Mock, patch
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
            'API_VERSION': '37.0',
        }
        return config

    @pytest.fixture
    def access_token(self):
        return '*********'

    @pytest.fixture
    def server_host(self):
        return 'some.salesforce.server'

    @pytest.fixture
    def login(self, access_token, server_host):
        with patch('nameko_salesforce.client.SalesforceLogin') as login:
            login.return_value = (access_token, server_host)
            yield login

    @pytest.fixture
    def redis_uri(self):
        return 'redis://localhost:6379/11'

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
        assert client.api_version == config['SALESFORCE']['API_VERSION']
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
        ('attr', 'key', 'expected_default'),
        (
            ('version', 'BAYEUX_VERSION', '1.0'),
            ('minimum_version', 'BAYEUX_MINIMUM_VERSION', '1.0'),
            ('api_version', 'API_VERSION', '37.0'),
            ('replay_enabled', 'PUSHTOPIC_REPLAY_ENABLED', False),
            ('replay_storage_ttl', 'PUSHTOPIC_REPLAY_TTL', 60 * 60 * 12),
        ),
    )
    def test_setup_defaults(self, attr, key, expected_default, container):

        container.config[constants.CONFIG_KEY].pop(key, None)

        client = SalesForceBayeuxClient()
        client.container = container
        client.setup()

        assert getattr(client, attr) == expected_default

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

    def test_setup_replay_enabled(self, container, redis_uri):

        config = container.config[constants.CONFIG_KEY]
        config['PUSHTOPIC_REPLAY_ENABLED'] = True

        client = SalesForceBayeuxClient()
        client.container = container

        with pytest.raises(ConfigurationError) as exc:
            client.setup()

        expected_error = (
            '`{}` must have `PUSHTOPIC_REPLAY_REDIS_URI` defined if '
            '`PUSHTOPIC_REPLAY_ENABLED` is set to `True`'
            .format(constants.CONFIG_KEY))
        assert str(exc.value) == expected_error

        config['PUSHTOPIC_REPLAY_REDIS_URI'] = redis_uri
        config['PUSHTOPIC_REPLAY_TTL'] = 3600

        client.setup()

        assert client.replay_enabled == True
        assert client.replay_storage_ttl == 3600

    def test_login(self, access_token, client, config, login):

        client.login()

        assert access_token == client.access_token
        assert (
            'https://some.salesforce.server/cometd/37.0' ==
            client.server_uri
        )
        assert (
            login.call_args ==
            call(
                session=None,
                username=client.username,
                password=client.password,
                security_token=client.security_token,
                sandbox=client.sandbox,
                sf_version=client.api_version,
            )
        )

    def test_get_authorisation(self, client, access_token):
        client.access_token = access_token
        assert ('Bearer', access_token) == client.get_authorisation()
