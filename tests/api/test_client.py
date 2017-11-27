import eventlet
from eventlet.event import Event
from mock import patch
import pytest
import requests_mock
from simple_salesforce import SalesforceResourceNotFound

from nameko_salesforce.api.client import get_client, READ_RETRIES


@pytest.fixture
def client(config):
    return get_client(
        username=config['SALESFORCE']['USERNAME'],
        password=config['SALESFORCE']['PASSWORD'],
        security_token=config['SALESFORCE']['SECURITY_TOKEN'],
        sandbox=config['SALESFORCE']['SANDBOX'],
        api_version=config['SALESFORCE']['SANDBOX'],
    )


@pytest.fixture
def mock_salesforce_server():
    with requests_mock.Mocker() as mocked_requests:
        yield mocked_requests


@pytest.fixture(autouse=True)
def mock_salesforce_login():
    with patch('simple_salesforce.api.SalesforceLogin') as SalesforceLogin:
        SalesforceLogin.return_value = 'session_id', 'abc.salesforce.com'
        yield


@pytest.fixture(autouse=True)
def fast_retry():
    def no_sleep(period):
        eventlet.sleep(0)
    with patch('nameko.utils.retry.sleep', new=no_sleep):
        yield


def test_retry_adapter(client):
    # verify retry adapter is applied to session
    reads = READ_RETRIES
    assert client.session.get_adapter('http://foo').max_retries.read == reads
    assert client.session.get_adapter('https://bar').max_retries.read == reads


def test_proxy(client, mock_salesforce_server):
    requests_data = {'LastName': 'Smith', 'Email': 'example@example.com'}
    response_data = {
        'errors': [],
        'id': '003e0000003GuNXAA0',
        'success': True
    }
    mock_salesforce_server.post(requests_mock.ANY, json=response_data)

    result = client.Contact.create(requests_data)

    assert result == response_data

    assert mock_salesforce_server.request_history[0].json() == requests_data


def test_concurrency(client, mock_salesforce_server):

    requests_data = {'LastName': 'Smith', 'Email': 'example@example.com'}
    response_data = {
        'errors': [],
        'id': '003e0000003GuNXAA0',
        'success': True
    }

    class Pact:
        def __init__(self, threshold=2):
            self.count = 0
            self.event = Event()
            self.threshold = threshold

        def wait(self):
            self.count += 1
            if self.count == self.threshold:
                self.event.send()
            return self.event.wait()

    pact = Pact()

    def callback(*args, **kwargs):
        pact.wait()
        return response_data

    mock_salesforce_server.post(requests_mock.ANY, json=callback)

    def create_contact():
        assert client.Contact.create(requests_data) == response_data

    gt1 = eventlet.spawn(create_contact)
    gt2 = eventlet.spawn(create_contact)
    gt1.wait()
    gt2.wait()

    # expect two clients to have been created
    assert len(client.pool.busy) == 0
    assert len(client.pool.free) == 2


def test_pool_reuses_clients(client, mock_salesforce_server):

    requests_data = {'LastName': 'Smith', 'Email': 'example@example.com'}
    response_data = {
        'errors': [],
        'id': '003e0000003GuNXAA0',
        'success': True
    }
    mock_salesforce_server.post(requests_mock.ANY, json=response_data)

    assert client.Contact.create(requests_data) == response_data
    assert client.Contact.create(requests_data) == response_data

    # only one client should have been created
    assert len(client.pool.busy) == 0
    assert len(client.pool.free) == 1


@pytest.mark.usefixtures('fast_retry')
def test_bad_clients_are_discarded(client, mock_salesforce_server):

    # first call is successful; second is session expired; third is successful
    requests_data = {'LastName': 'Smith', 'Email': 'example@example.com'}
    response_data = {
        'errors': [],
        'id': '003e0000003GuNXAA0',
        'success': True
    }
    mock_salesforce_server.post(
        requests_mock.ANY,
        [
            {'json': response_data},
            {'status_code': 401, 'text': 'session expired'},
            {'json': response_data},
        ]
    )

    assert client.Contact.create(requests_data) == response_data

    assert len(client.pool.busy) == 0
    assert len(client.pool.free) == 1
    _first_client = list(client.pool.free)[0]

    assert client.Contact.create(requests_data) == response_data  # retries

    # first client is discarded from the pool
    assert _first_client not in client.pool.free
    assert len(client.pool.busy) == 0
    assert len(client.pool.free) == 1


@pytest.mark.usefixtures('fast_retry')
def test_proxy_retries_on_session_expired(client, mock_salesforce_server):

    # first call is session expired; second is success
    requests_data = {'LastName': 'Smith', 'Email': 'example@example.com'}
    response_data = {
        'errors': [],
        'id': '003e0000003GuNXAA0',
        'success': True
    }
    mock_salesforce_server.post(
        requests_mock.ANY,
        [
            {'status_code': 401, 'text': 'session expired'},
            {'json': response_data},
        ]
    )

    # retry succeeds
    assert client.Contact.create(requests_data) == response_data

    # second client is put back in the pool
    assert len(client.pool.busy) == 0
    assert len(client.pool.free) == 1


@pytest.mark.usefixtures('fast_retry')
def test_other_salesforce_errors_are_raised(client, mock_salesforce_server):

    # first call is session expired; second is a 404
    requests_data = {'LastName': 'Smith', 'Email': 'example@example.com'}
    mock_salesforce_server.post(
        requests_mock.ANY,
        [
            {'status_code': 401, 'text': 'session expired'},
            {'status_code': 404, 'text': 'not found'},
        ]
    )

    with pytest.raises(SalesforceResourceNotFound):
        assert client.Contact.create(requests_data)

    # client is still put back in the pool
    assert len(client.pool.busy) == 0
    assert len(client.pool.free) == 1
