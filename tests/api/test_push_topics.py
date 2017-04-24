from mock import patch
import pytest
import requests_mock
from simple_salesforce import SalesforceResourceNotFound

from nameko_salesforce.api.client import ClientProxy
from nameko_salesforce.api.push_topics import get_client


@pytest.fixture
def client(config):
    return get_client(config)


@pytest.fixture
def api_version(config):
    return config['SALESFORCE']['API_VERSION']


@pytest.fixture
def mock_salesforce_server():
    with requests_mock.Mocker() as mocked_requests:
        yield mocked_requests


@pytest.fixture(autouse=True)
def mock_salesforce_login():
    with patch('simple_salesforce.api.SalesforceLogin') as SalesforceLogin:
        SalesforceLogin.return_value = 'session_id', 'abc.salesforce.com'
        yield


def test_implements_client_proxy(client):
    assert isinstance(client, ClientProxy)


def test_get_push_topic_by_name_not_found(
    api_version, client, mock_salesforce_server
):
    response_data = {'totalSize': 0, 'records': []}
    mock_salesforce_server.get(requests_mock.ANY, json=response_data)

    with pytest.raises(client.NotFound) as exc:
        client.get_push_topic_by_name('ContactUpdates')

    assert str(exc.value) == "PushTopic 'ContactUpdates' does not exist"


def test_get_push_topic_by_name(api_version, client, mock_salesforce_server):

    name = 'ContactUpdates'
    response_data = {
        'totalSize': 1,
        'records': [{'Id': '00..A0', 'Name': name, 'Query': '...'}]
    }
    mock_salesforce_server.get(requests_mock.ANY, json=response_data)

    result = client.get_push_topic_by_name(name)

    assert result == {'Id': '00..A0', 'Name': name, 'Query': '...'}

    assert len(mock_salesforce_server.request_history) == 1
    request = mock_salesforce_server.request_history[0]
    assert request.path == '/services/data/v{}/query/'.format(api_version)
    assert request.query == (
        'q=select+id%2c+name%2c+query+from+pushtopic+where+name+%3d+%27'
        'contactupdates%27'
    )


def test_get_push_topic_by_name_cached(
    api_version, client, mock_salesforce_server
):
    name = 'ContactUpdates'
    response_data = {
        'totalSize': 1,
        'records': [{'Id': '00..A0', 'Name': name, 'Query': '...'}]
    }
    mock_salesforce_server.get(requests_mock.ANY, json=response_data)

    result = client.get_push_topic_by_name(name)
    assert result == {'Id': '00..A0', 'Name': name, 'Query': '...'}
    assert len(mock_salesforce_server.request_history) == 1

    result = client.get_push_topic_by_name(name)
    assert result == {'Id': '00..A0', 'Name': name, 'Query': '...'}
    assert len(mock_salesforce_server.request_history) == 1  # requested once


def test_get_user_id_by_name_not_found(
    api_version, client, mock_salesforce_server
):
    response_data = {'totalSize': 0, 'records': []}
    mock_salesforce_server.get(requests_mock.ANY, json=response_data)

    with pytest.raises(client.NotFound) as exc:
        client.get_user_id_by_name('smith')

    assert str(exc.value) == "User 'smith' does not exist"


def test_get_user_id_by_name(api_version, client, mock_salesforce_server):

    name = 'smith'
    response_data = {
        'totalSize': 1,
        'records': [{'Id': '00..A0', 'Username': name}]
    }
    mock_salesforce_server.get(requests_mock.ANY, json=response_data)

    result = client.get_user_id_by_name(name)

    assert result == '00..A0'

    assert len(mock_salesforce_server.request_history) == 1
    request = mock_salesforce_server.request_history[0]
    assert request.path == '/services/data/v{}/query/'.format(api_version)
    assert request.query == (
        'q=select+id+from+user+where+username+%3d+%27smith%27')


def test_get_user_id_by_name_cached(
    api_version, client, mock_salesforce_server
):
    name = 'ContactUpdates'
    response_data = {
        'totalSize': 1,
        'records': [{'Id': '00..A0', 'Username': name}]
    }
    mock_salesforce_server.get(requests_mock.ANY, json=response_data)

    result = client.get_user_id_by_name(name)
    assert result == '00..A0'
    assert len(mock_salesforce_server.request_history) == 1

    result = client.get_user_id_by_name(name)
    assert result == '00..A0'
    assert len(mock_salesforce_server.request_history) == 1  # requested once


def test_get_record_type_id_by_name_not_found(
    api_version, client, mock_salesforce_server
):
    response_data = {'totalSize': 0, 'records': []}
    mock_salesforce_server.get(requests_mock.ANY, json=response_data)

    with pytest.raises(client.NotFound) as exc:
        client.get_record_type_id_by_name('Student', 'Contact')

    assert (
        str(exc.value) == "RecordType 'Student' of 'Contact' does not exist")


def test_get_record_type_id_by_name(
    api_version, client, mock_salesforce_server
):

    sobject_type_name = 'Contact'
    record_typ_name = 'Student'
    response_data = {'totalSize': 1, 'records': [{'Id': '00..A0'}]}
    mock_salesforce_server.get(requests_mock.ANY, json=response_data)

    result = client.get_record_type_id_by_name(
        sobject_type_name, record_typ_name)

    assert result == '00..A0'

    assert len(mock_salesforce_server.request_history) == 1
    request = mock_salesforce_server.request_history[0]
    assert request.path == '/services/data/v{}/query/'.format(api_version)
    assert request.query == (
        'q=select+id%2c+developername%2c+sobjecttype+from+recordtype+where+'
        'sobjecttype+%3d+%27contact%27+and+developername+%3d+%27student%27'
    )


def test_get_record_type_id_by_name_cached(
    api_version, client, mock_salesforce_server
):
    sobject_type_name = 'Contact'
    record_typ_name = 'Student'
    response_data = {'totalSize': 1, 'records': [{'Id': '00..A0'}]}
    mock_salesforce_server.get(requests_mock.ANY, json=response_data)

    result = client.get_record_type_id_by_name(
        sobject_type_name, record_typ_name)
    assert result == '00..A0'
    assert len(mock_salesforce_server.request_history) == 1

    result = client.get_record_type_id_by_name(
        sobject_type_name, record_typ_name)
    assert result == '00..A0'
    assert len(mock_salesforce_server.request_history) == 1  # requested once
