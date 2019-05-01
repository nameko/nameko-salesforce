import pytest
import requests_mock
from mock import Mock, patch
from nameko.containers import ServiceContainer
from nameko.exceptions import ConfigurationError
from nameko.testing.services import dummy, entrypoint_hook

from nameko_salesforce import constants
from nameko_salesforce.api import SalesforceAPI


class TestSalesforceAPIUnit:
    @pytest.fixture
    def container(self, config):
        return Mock(spec=ServiceContainer, config=config, service_name="exampleservice")

    @pytest.fixture
    def dependency_provider(self, container):
        return SalesforceAPI().bind(container, "salesforce_api")

    @pytest.fixture
    def salesforce_api(self, dependency_provider):
        dependency_provider.setup()
        return dependency_provider.get_dependency({})

    def test_setup(self, config, salesforce_api):

        salesforce_config = config[constants.CONFIG_KEY]

        assert salesforce_api.client.pool.username == salesforce_config["USERNAME"]
        assert salesforce_api.client.pool.password == salesforce_config["PASSWORD"]
        assert (
            salesforce_api.client.pool.security_token
            == salesforce_config["SECURITY_TOKEN"]
        )
        assert salesforce_api.client.pool.sandbox == salesforce_config["SANDBOX"]
        assert (
            salesforce_api.client.pool.api_version == salesforce_config["API_VERSION"]
        )

    def test_setup_default_api_version(self, config, salesforce_api):
        config[constants.CONFIG_KEY].pop("API_VERSION")

        assert salesforce_api.client.pool.api_version == constants.DEFAULT_API_VERSION

    def test_setup_main_config_key_missing(self, config, dependency_provider):

        config.pop("SALESFORCE")

        with pytest.raises(ConfigurationError) as exc:
            dependency_provider.setup()

        assert str(exc.value) == "`SALESFORCE` config key not found"

    @pytest.mark.parametrize(
        "key", ("USERNAME", "PASSWORD", "SECURITY_TOKEN", "SANDBOX")
    )
    def test_setup_config_keys_missing(self, config, dependency_provider, key):

        config[constants.CONFIG_KEY].pop(key)

        with pytest.raises(ConfigurationError) as exc:
            dependency_provider.setup()

        expected_error = "`{}` configuration does not contain mandatory `{}` key"
        assert str(exc.value) == expected_error.format(constants.CONFIG_KEY, key)

    def test_get_dependency(self, config, dependency_provider):
        dependency_provider.setup()
        worker_ctx = Mock()
        assert (
            dependency_provider.get_dependency(worker_ctx) == dependency_provider.client
        )


class TestSalesforceAPIEndToEnd:
    @pytest.fixture
    def mock_salesforce_server(self):
        with requests_mock.Mocker() as mocked_requests:
            yield mocked_requests

    @pytest.fixture(autouse=True)
    def mock_salesforce_login(self):
        with patch("simple_salesforce.api.SalesforceLogin") as SalesforceLogin:
            SalesforceLogin.return_value = "session_id", "abc.salesforce.com"
            yield

    def test_end_to_end(self, config, container_factory, mock_salesforce_server):

        requests_data = {"LastName": "Smith", "Email": "example@example.com"}
        response_data = {"errors": [], "id": "003e0000003GuNXAA0", "success": True}
        mock_salesforce_server.post(requests_mock.ANY, json=response_data)

        class Service(object):

            name = "service"

            salesforce_api = SalesforceAPI()

            @dummy
            def create(self, requests_data):
                return self.salesforce_api.Contact.create(requests_data)

        container = container_factory(Service, config)
        container.start()

        with entrypoint_hook(container, "create") as create:
            assert create(requests_data) == response_data

        assert mock_salesforce_server.request_history[0].json() == requests_data
