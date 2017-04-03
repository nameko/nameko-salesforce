from nameko.exceptions import ConfigurationError
from nameko_bayeux_client.client import BayeuxClient

from nameko_salesforce import constants


class SalesForceBayeuxClient(BayeuxClient):

    def __init__(self):

        super().__init__()

        self.version = '1.0'
        """ Bayeux protocol version
        """

        self.minimum_version = '1.0'
        """
        Minimum Bayeux protocol version

        Indicates the oldest protocol version that can be handled
        by the client/server

        """

        self.api_version = '37.0'
        """ Salesforce server API version
        """

        self.username = None
        """ Salesforce API username
        """

        self.password = None
        """ Salesforce API password
        """

        self.security_token = None
        """ Salesforce SOAP Authentication Security Token

        The underlying Simplesalesforce uses ...
        """

        self.sandbox = None
        """ If True, the client connects to testing Salesforce account
        """

        self.server_uri = None
        """ Salesforce server URI obtained upon login
        """

        self.access_token = None
        """ Access token for the session obtained upon login
        """

    def setup(self):

        try:
            config = self.container.config[constants.CONFIG_KEY]
        except KeyError:
            raise ConfigurationError(
                '`{}` config key not found'.format(constants.CONFIG_KEY))

        self.version = config.get('BAYEUX_VERSION', self.version)
        self.minimum_version = config.get(
            'BAYEUX_MINIMUM_VERSION', self.minimum_version)
        self.api_version = config.get('API_VERSION', self.api_version)

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

        self.server_uri = None  # will be filled on login
        self.access_token = None  # will be filled on login
