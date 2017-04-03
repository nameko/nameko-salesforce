import logging

from nameko.exceptions import ConfigurationError
from nameko_bayeux_client.client import BayeuxClient, BayeuxMessageHandler
import redis
from simple_salesforce.login import SalesforceLogin

from nameko_salesforce import constants


logger = logging.getLogger(__name__)


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

        The underlying Simplesalesforce uses TODO describe ...
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

        self.replay_enabled = False
        """
        """

        self.replay_storage = None
        """
        """

        self.replay_storage_ttl = constants.DEFAULT_REPLAY_STORAGE_TTL
        """
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
                '`{}` configuration does not contain mandatory '
                '`{}` key'.format(constants.CONFIG_KEY, exc.args[0])
            ) from exc

        self.replay_enabled = config.get('PUSHTOPIC_REPLAY_ENABLED', False)
        if self.replay_enabled:
            self._setup_replay_storage(config)

    def _setup_replay_storage(self, config):
        try:
            redis_uri = config['PUSHTOPIC_REPLAY_REDIS_URI']
        except KeyError:
            raise ConfigurationError(
                '`{}` must have `PUSHTOPIC_REPLAY_REDIS_URI` defined if '
                '`PUSHTOPIC_REPLAY_ENABLED` is set to `True`'
                .format(constants.CONFIG_KEY)
            )
        self.replay_storage = redis.StrictRedis.from_url(redis_uri)
        self.replay_storage_ttl = config.get(
            'PUSHTOPIC_REPLAY_TTL', self.replay_storage_ttl)

    def login(self):

        config = self.container.config['SALESFORCE']

        access_token, host = SalesforceLogin(
            session=None,
            username=self.username,
            password=self.password,
            security_token=self.security_token,
            sandbox=self.sandbox,
            sf_version=self.api_version,
        )

        self.access_token = access_token

        self.server_uri = 'https://{}/cometd/{}'.format(host, self.api_version)

        logger.info('Logged in to salesforce as %s', config['USERNAME'])

    def get_authorisation(self):
        return 'Bearer', self.access_token



class SalesforceMessageHandler(BayeuxMessageHandler):
    pass


subscribe = SalesforceMessageHandler.decorator
