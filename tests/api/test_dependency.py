from mock import Mock, patch
from nameko.containers import ServiceContainer
from nameko.exceptions import ConfigurationError
from nameko.testing.services import dummy
from nameko.testing.utils import get_extension
import pytest
import requests_mock

from nameko_salesforce import constants
from nameko_salesforce.api import SalesforceAPI


@pytest.fixture
def make_salesforce_api_provider(config):

    containers = []
    default_config = config

    def factory(config=None):

        class Service(object):

            name = "service"

            salesforce_api = SalesforceAPI()

            @dummy
            def dummy(self):
                pass

        container = ServiceContainer(Service, config or default_config)
        containers.append(container)

        return get_extension(container, SalesforceAPI)

    yield factory

    del containers[:]


class TestSalesforceAPIUnit:

    def test_setup(self, config, make_salesforce_api_provider):

        salesforce_api_provider = make_salesforce_api_provider()
        salesforce_api_provider.setup()

        salesforce_config = config[constants.CONFIG_KEY]

        assert (
            salesforce_api_provider.client.pool.username ==
            salesforce_config['USERNAME'])
        assert (
            salesforce_api_provider.client.pool.password ==
            salesforce_config['PASSWORD'])
        assert (
            salesforce_api_provider.client.pool.security_token ==
            salesforce_config['SECURITY_TOKEN'])
        assert (
            salesforce_api_provider.client.pool.sandbox ==
            salesforce_config['SANDBOX'])
        assert (
            salesforce_api_provider.client.pool.api_version ==
            salesforce_config['API_VERSION'])

    def test_setup_default_api_version(
        self, config, make_salesforce_api_provider
    ):
        config[constants.CONFIG_KEY].pop('API_VERSION')

        salesforce_api_provider = make_salesforce_api_provider()
        salesforce_api_provider.setup()

        assert (
            salesforce_api_provider.client.pool.api_version ==
            constants.DEFAULT_API_VERSION)

    def test_setup_main_config_key_missing(
        self, config, make_salesforce_api_provider
    ):

        config.pop('SALESFORCE')

        salesforce_api_provider = make_salesforce_api_provider()

        with pytest.raises(ConfigurationError) as exc:
            salesforce_api_provider.setup()

        assert str(exc.value) == '`SALESFORCE` config key not found'

    @pytest.mark.parametrize(
        'key', ('USERNAME', 'PASSWORD', 'SECURITY_TOKEN', 'SANDBOX')
    )
    def test_setup_config_keys_missing(
        self, config, make_salesforce_api_provider, key
    ):

        config[constants.CONFIG_KEY].pop(key)

        salesforce_api_provider = make_salesforce_api_provider()

        with pytest.raises(ConfigurationError) as exc:
            salesforce_api_provider.setup()

        expected_error = (
            '`{}` configuration does not contain mandatory `{}` key'
            .format(constants.CONFIG_KEY, key))
        assert str(exc.value) == expected_error

    def test_get_dependency(self, config, make_salesforce_api_provider):
        salesforce_api_provider = make_salesforce_api_provider()
        salesforce_api_provider.setup()
        worker_ctx = Mock()
        assert (
            salesforce_api_provider.get_dependency(worker_ctx) ==
            salesforce_api_provider.client)


class TestSalesforceAPIEndToEnd:

    @pytest.fixture
    def mock_salesforce_server(self):
        with requests_mock.Mocker() as mocked_requests:
            yield mocked_requests

    @pytest.fixture(autouse=True)
    def mock_salesforce_login(self):
        with patch('simple_salesforce.api.SalesforceLogin') as SalesforceLogin:
            SalesforceLogin.return_value = 'session_id', 'abc.salesforce.com'
            yield

    def test_end_to_end(
        self, config, make_salesforce_api_provider, mock_salesforce_server
    ):

        requests_data = {'LastName': 'Smith', 'Email': 'example@example.com'}
        response_data = {
            'errors': [],
            'id': '003e0000003GuNXAA0',
            'success': True
        }
        mock_salesforce_server.post(requests_mock.ANY, json=response_data)

        salesforce_api_provider = make_salesforce_api_provider()
        salesforce_api_provider.setup()

        worker_ctx = {}

        salesforce_api = salesforce_api_provider.get_dependency(worker_ctx)

        result = salesforce_api.Contact.create(requests_data)

        assert result == response_data

        assert (
            mock_salesforce_server.request_history[0].json() ==
            requests_data)
