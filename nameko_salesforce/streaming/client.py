from functools import partial
import logging

from nameko.exceptions import ConfigurationError
from nameko_bayeux_client.client import BayeuxClient, BayeuxMessageHandler
import redis
from simple_salesforce.login import SalesforceLogin

from nameko_salesforce import constants
from nameko_salesforce.streaming import channels


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
        """ PushTopic Events tracking enabled

        If set to ``True``, the client will persist last event Reply ID for
        each channel and use it when subscribing to immediately receive events
        missed during the retention window.

        """

        self.replay_storage = None
        """ Redis client instance for persisting PushTopic Replay IDs

        Initialized only if ``replay_enabled`` is set.

        """

        self.replay_storage_ttl = constants.DEFAULT_REPLAY_STORAGE_TTL
        """ Time to live for persisted PushTopic Reply IDs

        Salesforce promises to keep events for 24 hours, therefore the TTL
        value must not exceed it.

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

    def subscribe(self):
        channel = channels.Subscribe(self)
        subscriptions = []
        for channel_name in self._subscriptions:
            if self.replay_enabled:
                replay_id = self.get_replay_id(channel_name)
            else:
                replay_id = None
            subscriptions.append(channel.compose(channel_name, replay_id))
        self.send_and_handle(subscriptions)

    def get_authorisation(self):
        return 'Bearer', self.access_token

    def _format_replay_key(self, channel_name):
        return 'salesforce:replay_id:{}'.format(channel_name)

    def get_replay_id(self, channel_name):
        replay_id = self.replay_storage.get(
            self._format_replay_key(channel_name))
        if replay_id:
            return int(replay_id)

    def set_replay_id(self, channel_name, replay_id):
        key = self._format_replay_key(channel_name)
        pipe = self.replay_storage.pipeline()
        pipe.set(key, replay_id)
        pipe.expire(key, self.replay_storage_ttl)
        pipe.execute()


class SalesforceMessageHandler(BayeuxMessageHandler):

    client = SalesForceBayeuxClient()

    def handle_message(self, message):
        args = (self.channel_name, message)
        kwargs = {}
        context_data = {}

        replay_id = message['event']['replayId']

        self.container.spawn_worker(
            self, args, kwargs, context_data=context_data,
            handle_result=partial(self.handle_result, replay_id))

    def handle_result(self, replay_id, worker_ctx, result, exc_info):
        if not exc_info and self.client.replay_enabled:
            self.client.set_replay_id(self.channel_name, replay_id)
        return result, exc_info


subscribe = SalesforceMessageHandler.decorator
