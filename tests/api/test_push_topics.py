from mock import patch
import pytest
import requests_mock
from simple_salesforce import SalesforceResourceNotFound

from nameko_salesforce.api.client import ClientProxy
from nameko_salesforce.api.push_topics import get_client, PushTopicsAPIClient


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


class TestDeclarePushTopic:

    def test_push_topic_created(
        self, api_version, client, mock_salesforce_server
    ):
        """ Test creates push topic if it does not exist
        """
        sobject_type = 'Contact'

        # setup push topic lookup
        response_data = {'totalSize': 0, 'records': []}
        mock_salesforce_server.get(requests_mock.ANY, json=response_data)

        # setup push topic creation
        mock_salesforce_server.post(requests_mock.ANY, json={})

        client.declare_push_topic(sobject_type)

        get_request, post_request = mock_salesforce_server.request_history

        assert get_request.method == 'GET'
        assert get_request.path == '/services/data/v{}/query/'.format(api_version)

        assert post_request.method == 'POST'
        assert post_request.path == (
            '/services/data/v{}/sobjects/pushtopic/'.format(api_version))

    def test_push_topic_updated(
        self, api_version, client, mock_salesforce_server
    ):
        """ Test updates push topic if it exists
        """
        sobject_type = 'Contact'

        # push topic lookup response
        response_data = {'totalSize': 1, 'records': [{'Id': '00..A0'}]}
        mock_salesforce_server.get(requests_mock.ANY, json=response_data)

        # push topic update response
        mock_salesforce_server.patch(requests_mock.ANY, json={})

        client.declare_push_topic(sobject_type)

        get_request, post_request = mock_salesforce_server.request_history

        assert get_request.method == 'GET'
        assert get_request.path == '/services/data/v{}/query/'.format(api_version)

        assert post_request.method == 'PATCH'
        assert post_request.path == (
            '/services/data/v{}/sobjects/pushtopic/00..a0'.format(api_version))

    @pytest.fixture
    def get_record_type_id_by_name(self):
        with patch.object(
            PushTopicsAPIClient, 'get_record_type_id_by_name'
        ) as method:
            yield method

    @pytest.fixture
    def get_user_id_by_name(self):
        with patch.object(
            PushTopicsAPIClient, 'get_user_id_by_name'
        ) as method:
            yield method

    @pytest.fixture
    def get_push_topic_by_name(self):
        with patch.object(
            PushTopicsAPIClient, 'get_push_topic_by_name'
        ) as method:
            yield method

    @pytest.fixture(params=('create', 'update'))
    def write_push_topic(
        self, request, client, get_push_topic_by_name, mock_salesforce_server
    ):
        if request.param == 'create':
            get_push_topic_by_name.side_effect = client.NotFound
            create_push_topic = mock_salesforce_server.post(
                requests_mock.ANY, json={})
            return create_push_topic
        if request.param == 'update':
            get_push_topic_by_name.return_value = {'Id': '00..A0'}
            update_push_topic = mock_salesforce_server.patch(
                requests_mock.ANY, json={})
            return update_push_topic

    @pytest.mark.parametrize(
        ('sobject_type', 'record_type', 'expected_name'),
        (
            ('Contact', None, 'Contact'),
            ('Contact', 'Student', 'ContactStudent'),
        )
    )
    def test_push_topic_name(
        self, get_record_type_id_by_name, client, write_push_topic,
        sobject_type, record_type, expected_name
    ):
        """ Test push topic name definition

        Parameterised as a matrix testing the cases for creation of a new
        push topic object and for an update of existing one.

        """
        client.declare_push_topic(sobject_type, record_type)

        request = write_push_topic.request_history[0]
        assert request.json()['Name'] == expected_name

    @pytest.mark.parametrize(
        ('record_type', 'exclude_current_user', 'expected_query'),
        (
            (
                None, False,
                ("SELECT Id, Name, LastModifiedById, LastModifiedDate "
                 "FROM Contact"),
            ),
            (
                'Student', False,
                ("SELECT Id, Name, LastModifiedById, LastModifiedDate "
                 "FROM Contact WHERE RecordTypeId = '00..A0'"),
            ),
            (
                None, True,
                ("SELECT Id, Name, LastModifiedById, LastModifiedDate "
                 "FROM Contact WHERE LastModifiedById != '11..A1'"),
            ),
            (
                'Student', True,
                ("SELECT Id, Name, LastModifiedById, LastModifiedDate "
                 "FROM Contact WHERE RecordTypeId = '00..A0' "
                 "AND LastModifiedById != '11..A1'"),
            ),
        )
    )
    def test_push_topic_query(
        self, get_record_type_id_by_name, get_user_id_by_name, client,
        write_push_topic, record_type, exclude_current_user, expected_query
    ):
        """ Test push topic query definition

        Parameterised as a matrix testing the cases for creation of a new
        push topic object and for an update of existing one.

        """
        sobject_type = 'Contact'

        get_record_type_id_by_name.return_value = '00..A0'
        get_user_id_by_name.return_value = '11..A1'

        client.declare_push_topic(
            sobject_type, record_type,
            exclude_current_user=exclude_current_user)

        request = write_push_topic.request_history[0]
        assert request.json()['Query'] == expected_query
