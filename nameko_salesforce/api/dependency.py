from nameko.exceptions import ConfigurationError
from nameko.extensions import DependencyProvider

from nameko_salesforce import constants
from nameko_salesforce.api.client import get_client


class SalesforceAPI(DependencyProvider):

    def setup(self):

        try:
            config = self.container.config[constants.CONFIG_KEY]
        except KeyError:
            raise ConfigurationError(
                '`{}` config key not found'.format(constants.CONFIG_KEY))

        try:
            username = config['USERNAME']
            password = config['PASSWORD']
            security_token = config['SECURITY_TOKEN']
            sandbox = config['SANDBOX']
        except KeyError as exc:
            raise ConfigurationError(
                '`{}` configuration does not contain mandatory '
                '`{}` key'.format(constants.CONFIG_KEY, exc.args[0])
            ) from exc

        api_version = config.get('API_VERSION', constants.DEFAULT_API_VERSION)

        self.client = get_client(
            username, password, security_token,
            sandbox=sandbox, api_version=api_version)

    def get_dependency(self, worker_ctx):
        return self.client
