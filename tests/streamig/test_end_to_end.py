import json

from eventlet import sleep
from eventlet.event import Event
from mock import call, Mock, patch
from nameko.testing.utils import find_free_port
from nameko.web.handlers import http
from nameko_bayeux_client.constants import Reconnection
import pytest
import requests_mock

from nameko_salesforce import constants
from nameko_salesforce.streaming import (
    handle_sobject_notification,
    handle_notification,
    subscribe,
)
from nameko_salesforce.streaming.client import StreamingClient


@pytest.fixture
def client_id():
    return '5b1jdngw1jz9g9w176s5z4jha0h8'


@pytest.fixture
def message_maker(config, client_id):

    # TODO - nameko_bayeux_client should make these fixtures available?

    class MessageMaker:

        def make_handshake_request(self, **fields):
            message = {
                'channel': '/meta/handshake',
                'id': 1,
                'version': config['SALESFORCE']['BAYEUX_VERSION'],
                'minimumVersion': (
                    config['SALESFORCE']['BAYEUX_MINIMUM_VERSION']),
                'supportedConnectionTypes': ['long-polling'],
            }
            message.update(**fields)
            return message

        def make_subscribe_request(self, **fields):
            message = {
                'clientId': client_id,
                'channel': '/meta/subscribe',
                'id': 2,
                'subscription': '/topic/example',
            }
            message.update(**fields)
            return message

        def make_connect_request(self, **fields):
            message = {
                'clientId': client_id,
                'id': 4,
                'channel': '/meta/connect',
                'connectionType': 'long-polling',
            }
            message.update(**fields)
            return message

        def make_disconnect_request(self, **fields):
            message = {
                'clientId': client_id,
                'id': 5,
                'channel': '/meta/disconnect',
            }
            message.update(**fields)
            return message

        def make_event_delivery_message(self, **fields):
            message = {
                'data': [],
                'channel': '/topic/example',
                'clientId': client_id,
            }
            message.update(**fields)
            return message

        def make_handshake_response(self, **fields):
            message = {
                'successful': True,
                'id': '1',
                'channel': '/meta/handshake',
                'version': '1.0',
                'minimumVersion': '1.0',
                'clientId': client_id,
                'supportedConnectionTypes': ['long-polling'],
                'ext': {'replay': True},
            }
            message.update(**fields)
            return message

        def make_subscribe_response(self, **fields):
            message = {
                    'successful': True,
                    'id': '1',
                    'channel': '/meta/subscribe',
                    'clientId': client_id,
                    'subscription': '/spam/ham',
            }
            message.update(**fields)
            return message

        def make_connect_response(self, **fields):
            message = {
                'successful': True,
                'id': '1',
                'channel': '/meta/connect',
                'clientId': client_id,
            }
            message.update(**fields)
            return message

        def make_disconnect_response(self, **fields):
            message = {
                'successful': True,
                'id': '1',
                'channel': '/meta/disconnect',
                'clientId': client_id,
            }
            message.update(**fields)
            return message

    return MessageMaker()


@pytest.fixture
def notifications(message_maker):
    return [
        {
            'event': {
                'createdDate': '2016-03-29T16:40:08.208Z',
                'replayId': 1,
                'type': 'created',
            },
            'sobject': {
                'Id': '001D000000KnaXjIAJ',
                'FirstName': 'Rocky',
                'LastName': 'Balboa',
            }
        },
        {
            'event': {
                'createdDate': '2016-03-29T16:40:08.208Z',
                'replayId': 2,
                'type': 'updated',
            },
            'sobject': {
                'Id': '006D000000KnaXjIAJ',
                'Name': 'TicTacToe'
            }
        },
        {
            'event': {
                'createdDate': '2016-03-29T16:40:08.208Z',
                'replayId': 3,
                'type': 'created',
            },
            'sobject': {
                'Id': '004D000000KnaXjIAJ',
                'FirstName': 'John',
                'LastName': 'Rambo',
            }
        },
    ]


@pytest.fixture
def salesforce_server_port():
    return find_free_port()


@pytest.fixture
def salesforce_server_uri(salesforce_server_port):
    return 'http://localhost:{}/cometd/37.0'.format(salesforce_server_port)


@pytest.fixture
def login(salesforce_server_uri):
    def patched_login(obj):
        obj.server_uri = salesforce_server_uri
    with patch.object(StreamingClient, 'login', patched_login) as login:
        yield login


@pytest.fixture
def tracker():
    return Mock()


@pytest.fixture
def waiter():
    return Event()


@pytest.fixture
def make_salesforce_server(
    container_factory, salesforce_server_port, message_maker, tracker, waiter
):
    """ Return a container to imitating Salesforce Streaming API server
    """

    def _make(responses):

        class CometdServer(object):

            name = "cometd"

            @http('POST', "/cometd/37.0")
            def handle(self, request):
                tracker.request(
                    json.loads(request.get_data().decode(encoding='UTF-8')))
                try:
                    return 200, json.dumps(responses.pop(0))
                except IndexError:
                    waiter.send()
                    sleep(0.1)
                    no_events_to_deliver = [
                        message_maker.make_connect_response()]
                    return (200, json.dumps(no_events_to_deliver))

        config = {
            'WEB_SERVER_ADDRESS': 'localhost:{}'.format(
                salesforce_server_port)
        }
        container = container_factory(CometdServer, config)

        return container

    return _make


@pytest.fixture
def run_services(
    container_factory, config, login, make_salesforce_server, waiter
):
    """ Returns services runner
    """

    def _run(service_class, responses):
        """
        Run testing salesforce server and the tested example service

        Before run, the Streaming API server server is preloaded with
        passed responses.

        """

        salesforce_server = make_salesforce_server(responses)
        container = container_factory(service_class, config)

        salesforce_server.start()
        container.start()

        waiter.wait()

        container.kill()
        salesforce_server.stop()

    return _run


@pytest.fixture
def salesforce_api_server(salesforce_server_uri):
    """
    Mocked Salesforce API server

    Notification entrypoints creates PushTopic objects using Salesforce API.
    Here the API is mocked to be able to preset responses simulating a simple
    PushTopic declaration scenario.

    """
    with patch('simple_salesforce.api.SalesforceLogin') as SalesforceLogin:
        SalesforceLogin.return_value = 'session', 'abc.salesforce.com'
        with requests_mock.Mocker() as mocked_requests:
            yield mocked_requests


def test_subscribe(message_maker, notifications, run_services, tracker):

    class Service:

        name = 'example-service'

        @subscribe('/topic/AccountUpdates')
        @subscribe('/topic/ContactUpdates')
        def handle_event(self, topic, event):
            tracker.handle_event(topic, event)

    notification_one, notification_two, notification_three = notifications

    responses = [
        [message_maker.make_handshake_response()],
        [
            message_maker.make_subscribe_response(
                subscription='/topic/AccountUpdates'),
            message_maker.make_subscribe_response(
                subscription='/topic/ContactUpdates'),
        ],
        [
            message_maker.make_connect_response(
                advice={'reconnect': Reconnection.retry.value}),
        ],
        # two events to deliver
        [
            message_maker.make_event_delivery_message(
                channel='/topic/ContactUpdates',
                data=notification_one,
            ),
            message_maker.make_event_delivery_message(
                channel='/topic/AccountUpdates',
                data=notification_two,
            ),
        ],
        # no event to deliver within server timeout
        [message_maker.make_connect_response()],
        # one event to deliver
        [
            message_maker.make_event_delivery_message(
                channel='/topic/ContactUpdates',
                data=notification_three,
            ),
        ],
    ]

    run_services(Service, responses)

    handshake, subscriptions = tracker.request.call_args_list[:2]
    connect = tracker.request.call_args_list[2:]

    assert handshake == call(
        [message_maker.make_handshake_request(id=1)])

    topics = [
        message.pop('subscription') for message in subscriptions[0][0]
    ]
    assert set(topics) == set(
        ['/topic/AccountUpdates', '/topic/ContactUpdates'])

    assert connect == [
        call([message_maker.make_connect_request(id=4)]),
        call([message_maker.make_connect_request(id=5)]),
        call([message_maker.make_connect_request(id=6)]),
        call([message_maker.make_connect_request(id=7)]),
        call([message_maker.make_connect_request(id=8)]),
    ]

    expected_event_handling = [
        call('/topic/ContactUpdates', notification_one),
        call('/topic/AccountUpdates', notification_two),
        call('/topic/ContactUpdates', notification_three),
    ]
    assert tracker.handle_event.call_args_list == expected_event_handling


def test_handle_notification(
    message_maker, notifications, run_services, tracker,
    salesforce_api_server, salesforce_server_uri
):

    salesforce_api_server.get(requests_mock.ANY, json={'totalSize': 0})
    salesforce_api_server.post(requests_mock.ANY, json={})
    # un-mock Salesforce Streaming API calls making the mocker to let
    # streaming requests reach the testing streaming API server:
    salesforce_api_server.post(salesforce_server_uri, real_http=True)

    class Service:

        name = 'example-service'

        @handle_notification('AccountUpdates')
        @handle_notification(
            'ContactUpdates',
            query='SELECT ...',
            notify_for_fields=constants.NotifyForFields.referenced,
            notify_for_operation_create=False,
            notify_for_operation_update=True,
            notify_for_operation_delete=False,
            notify_for_operation_undelete=False
        )
        def handle_notification(self, topic, notification):
            tracker.handle_notification(topic, notification)

    notification_one, notification_two, notification_three = notifications

    responses = [
        [message_maker.make_handshake_response()],
        [
            message_maker.make_subscribe_response(
                subscription='/topic/AccountUpdates'),
            message_maker.make_subscribe_response(
                subscription='/topic/ContactUpdates'),
        ],
        [
            message_maker.make_connect_response(
                advice={'reconnect': Reconnection.retry.value}),
        ],
        # two notifications to deliver
        [
            message_maker.make_event_delivery_message(
                channel='/topic/ContactUpdates',
                data=notification_one,
            ),
            message_maker.make_event_delivery_message(
                channel='/topic/AccountUpdates',
                data=notification_two,
            ),
        ],
        # no notification to deliver within server timeout
        [message_maker.make_connect_response()],
        # one notification to deliver
        [
            message_maker.make_event_delivery_message(
                channel='/topic/ContactUpdates',
                data=notification_three,
            ),
        ],
    ]

    run_services(Service, responses)

    handshake, subscriptions = tracker.request.call_args_list[:2]
    connect = tracker.request.call_args_list[2:]

    assert handshake == call(
        [message_maker.make_handshake_request(id=1)])

    topics = [
        message.pop('subscription') for message in subscriptions[0][0]
    ]
    assert set(topics) == set(
        ['/topic/AccountUpdates', '/topic/ContactUpdates'])

    assert connect == [
        call([message_maker.make_connect_request(id=4)]),
        call([message_maker.make_connect_request(id=5)]),
        call([message_maker.make_connect_request(id=6)]),
        call([message_maker.make_connect_request(id=7)]),
        call([message_maker.make_connect_request(id=8)]),
    ]

    expected_notification_handling = [
        call('ContactUpdates', notification_one),
        call('AccountUpdates', notification_two),
        call('ContactUpdates', notification_three),
    ]
    assert (
        tracker.handle_notification.call_args_list ==
        expected_notification_handling)

    get_push_topic, create_push_topic = (
        salesforce_api_server.request_history[:2])

    assert get_push_topic.method == 'GET'
    assert create_push_topic.method == 'POST'

    push_topic_definition = create_push_topic.json()

    assert push_topic_definition['Name'] == 'ContactUpdates'
    assert push_topic_definition['Query'] == 'SELECT ...'
    assert (
        push_topic_definition['NotifyForFields'] ==
        constants.NotifyForFields.referenced.value)
    assert push_topic_definition['NotifyForOperationCreate'] is False
    assert push_topic_definition['NotifyForOperationUpdate'] is True
    assert push_topic_definition['NotifyForOperationDelete'] is False
    assert push_topic_definition['NotifyForOperationUndelete'] is False


def test_handle_sobject_notification(
    message_maker, notifications, run_services, tracker,
    salesforce_api_server, salesforce_server_uri
):

    salesforce_api_server.get(
        requests_mock.ANY,
        [
            # getting current user ID
            {'json': {'totalSize': 1, 'records': [{'Id': '00..A0'}]}},
            # getting the PushTopic
            {'json': {'totalSize': 0}}
        ])
    salesforce_api_server.post(requests_mock.ANY, json={})
    # un-mock Salesforce Streaming API calls making the mocker to let
    # streaming requests reach the testing streaming API server:
    salesforce_api_server.post(salesforce_server_uri, real_http=True)

    class Service:

        name = 'example-service'

        @handle_sobject_notification('Contact', declare=False)
        @handle_sobject_notification(
            sobject_type='Contact',
            record_type='Student',
            exclude_current_user=False,
            notify_for_fields=constants.NotifyForFields.referenced,
            notify_for_operation_create=False,
            notify_for_operation_update=True,
            notify_for_operation_delete=False,
            notify_for_operation_undelete=False
        )
        def handle_notification(
            self, sobject_type, record_type, notification
        ):
            tracker.handle_notification(
                sobject_type, record_type, notification)

    notification_one, notification_two, notification_three = notifications

    responses = [
        [message_maker.make_handshake_response()],
        [
            message_maker.make_subscribe_response(
                subscription='/topic/Contact'),
            message_maker.make_subscribe_response(
                subscription='/topic/ContactStudent'),
        ],
        [
            message_maker.make_connect_response(
                advice={'reconnect': Reconnection.retry.value}),
        ],
        # two notifications to deliver
        [
            message_maker.make_event_delivery_message(
                channel='/topic/ContactStudent',
                data=notification_one,
            ),
            message_maker.make_event_delivery_message(
                channel='/topic/Contact',
                data=notification_two,
            ),
        ],
        # no notification to deliver within server timeout
        [message_maker.make_connect_response()],
        # one notification to deliver
        [
            message_maker.make_event_delivery_message(
                channel='/topic/ContactStudent',
                data=notification_three,
            ),
        ],
    ]

    run_services(Service, responses)

    handshake, subscriptions = tracker.request.call_args_list[:2]
    connect = tracker.request.call_args_list[2:]

    assert handshake == call(
        [message_maker.make_handshake_request(id=1)])

    topics = [
        message.pop('subscription') for message in subscriptions[0][0]
    ]
    assert set(topics) == set(
        ['/topic/Contact', '/topic/ContactStudent'])

    assert connect == [
        call([message_maker.make_connect_request(id=4)]),
        call([message_maker.make_connect_request(id=5)]),
        call([message_maker.make_connect_request(id=6)]),
        call([message_maker.make_connect_request(id=7)]),
        call([message_maker.make_connect_request(id=8)]),
    ]

    expected_notification_handling = [
        call('Contact', 'Student', notification_one),
        call('Contact', None, notification_two),
        call('Contact', 'Student', notification_three),
    ]
    assert (
        tracker.handle_notification.call_args_list ==
        expected_notification_handling)

    get_user_id, get_push_topic, create_push_topic = (
        salesforce_api_server.request_history[:3])

    assert get_user_id.method == 'GET'
    assert get_push_topic.method == 'GET'
    assert create_push_topic.method == 'POST'

    push_topic_definition = create_push_topic.json()

    assert push_topic_definition['Name'] == 'ContactStudent'
    assert push_topic_definition['Query'].startswith('SELECT')
    assert (
        push_topic_definition['NotifyForFields'] ==
        constants.NotifyForFields.referenced.value)
    assert push_topic_definition['NotifyForOperationCreate'] is False
    assert push_topic_definition['NotifyForOperationUpdate'] is True
    assert push_topic_definition['NotifyForOperationDelete'] is False
    assert push_topic_definition['NotifyForOperationUndelete'] is False
