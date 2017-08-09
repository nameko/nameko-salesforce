from functools import partial
import logging

from nameko.exceptions import ConfigurationError
from nameko_bayeux_client.client import BayeuxClient, BayeuxMessageHandler
import redis
from simple_salesforce.login import SalesforceLogin

from nameko_salesforce import constants
from nameko_salesforce.api import push_topics
from nameko_salesforce.streaming import channels


logger = logging.getLogger(__name__)


class StreamingClient(BayeuxClient):

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

        self.api_version = constants.DEFAULT_API_VERSION
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

        If set to ``True``, the client will persist last event Replay ID for
        each channel and use it when subscribing to immediately receive events
        missed during the retention window.

        """

        self.replay_storage = None
        """ Redis client instance for persisting PushTopic Replay IDs

        Initialized only if ``replay_enabled`` is set.

        """

        self.replay_storage_ttl = constants.DEFAULT_REPLAY_STORAGE_TTL
        """ Time to live for persisted PushTopic Replay IDs

        Salesforce promises to keep events for 24 hours, therefore the TTL
        value must not exceed it. Subscription will fail on Replay IDs older
        than 24 hours.

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


class MessageHandler(BayeuxMessageHandler):

    client = StreamingClient()

    def handle_message(self, message):

        args, kwargs = self.get_worker_args(message)

        replay_id = message['event']['replayId']

        context_data = {
            constants.CLIENT_ID_CONTEXT_KEY: self.client.client_id,
            constants.REPLAY_ID_CONTEXT_KEY: replay_id,
        }

        self.container.spawn_worker(
            self, args, kwargs, context_data=context_data,
            handle_result=partial(self.handle_result, replay_id))

    def handle_result(self, replay_id, worker_ctx, result, exc_info):
        if not exc_info and self.client.replay_enabled:
            self.client.set_replay_id(self.channel_name, replay_id)
        return result, exc_info

    def get_worker_args(self, message):
        args = (self.channel_name, message)
        kwargs = {}
        return args, kwargs


subscribe = MessageHandler.decorator


class NotificationsClient(StreamingClient):

    def setup(self):
        super().setup()
        self.api_client = push_topics.get_client(
            self.username, self.password, self.security_token,
            sandbox=self.sandbox, api_version=self.api_version
        )

    def start(self):
        self._declare_push_topics()
        super().start()

    def _declare_push_topics(self):
        for provider in self._providers:
            provider.declare_push_topic(self.api_client)


class NotificationHandler(MessageHandler):

    client = NotificationsClient()

    def __init__(
        self,
        name,
        query=None,
        notify_for_fields=constants.NotifyForFields.all_,
        notify_for_operation_create=True,
        notify_for_operation_update=True,
        notify_for_operation_delete=True,
        notify_for_operation_undelete=True,
    ):
        self.name = name
        self.query = query
        self.notify_for_fields = notify_for_fields
        self.notify_for_operation_create = notify_for_operation_create
        self.notify_for_operation_update = notify_for_operation_update
        self.notify_for_operation_delete = notify_for_operation_delete
        self.notify_for_operation_undelete = notify_for_operation_undelete

        self.declare = True if self.query else False

        channel_name = '/topic/{}'.format(name)
        super().__init__(channel_name)

    def get_worker_args(self, message):
        args = (self.name, message)
        kwargs = {}
        return args, kwargs

    def declare_push_topic(self, api_client):
        if not self.declare:
            return
        api_client.declare_push_topic(
            self.name,
            self.query,
            notify_for_fields=self.notify_for_fields,
            notify_for_operation_create=self.notify_for_operation_create,
            notify_for_operation_update=self.notify_for_operation_update,
            notify_for_operation_delete=self.notify_for_operation_delete,
            notify_for_operation_undelete=self.notify_for_operation_undelete)


handle_notification = NotificationHandler.decorator


class SobjectNotificationHandler(MessageHandler):

    client = NotificationsClient()

    def __init__(
        self,
        sobject_type,
        record_type=None,
        declare=True,
        exclude_current_user=True,
        notify_for_fields=constants.NotifyForFields.all_,
        notify_for_operation_create=True,
        notify_for_operation_update=True,
        notify_for_operation_delete=True,
        notify_for_operation_undelete=True,
    ):

        self.sobject_type = sobject_type
        self.record_type = record_type
        self.exclude_current_user = exclude_current_user

        self.notify_for_fields = notify_for_fields
        self.notify_for_operation_create = notify_for_operation_create
        self.notify_for_operation_update = notify_for_operation_update
        self.notify_for_operation_delete = notify_for_operation_delete
        self.notify_for_operation_undelete = notify_for_operation_undelete

        self.declare = declare

        if self.record_type:
            topic = '{}{}'.format(sobject_type, record_type)
        else:
            topic = sobject_type
        channel_name = '/topic/{}'.format(topic)

        super().__init__(channel_name)

    def get_worker_args(self, message):
        args = (self.sobject_type, self.record_type, message)
        kwargs = {}
        return args, kwargs

    def declare_push_topic(self, api_client):
        if not self.declare:
            return
        api_client.declare_push_topic_for_sobject(
            self.sobject_type,
            self.record_type,
            exclude_current_user=self.exclude_current_user,
            notify_for_fields=self.notify_for_fields,
            notify_for_operation_create=self.notify_for_operation_create,
            notify_for_operation_update=self.notify_for_operation_update,
            notify_for_operation_delete=self.notify_for_operation_delete,
            notify_for_operation_undelete=self.notify_for_operation_undelete)


handle_sobject_notification = SobjectNotificationHandler.decorator
