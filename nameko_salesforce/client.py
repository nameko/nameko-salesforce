from nameko.exceptions import ConfigurationError
from nameko_bayeux_client.client import BayeuxClient

from nameko_salesforce import constants


class SalesForceBayeuxClient(BayeuxClient):

    def setup(self):

        try:
            config = self.container.config[constants.CONFIG_KEY]
        except KeyError:
            raise ConfigurationError(
                '`{}` config key not found'.format(constants.CONFIG_KEY))

        self.version = config.get('BAYEUX_VERSION', '1.0')
        self.minimum_version = config.get('BAYEUX_MINIMUM_VERSION', '1.0')

        try:
            self.username = config['USERNAME']
            self.password = config['PASSWORD']
            self.security_token = config['SECURITY_TOKEN']
            self.sandbox = config['SANDBOX']
        except KeyError as exc:
            raise ConfigurationError(
                "`{}` configuration does not contain mandatory "
                "`{}` key".format(constants.CONFIG_KEY, exc.args[0])
            ) from exc
