from functools import partial
import operator

from cachetools import LRUCache, cachedmethod

from nameko_salesforce.api.client import ClientPool, ClientProxy


cached = cachedmethod(operator.attrgetter('cache'))


class NotFound(LookupError):
    pass


def get_client(config):
    pool = ClientPool(config)
    return PushTopicsAPIClient(config, pool)


class PushTopicsAPIClient(ClientProxy):
    """
    Salesforce API client with helper method for managing PushTopic object

    """

    NotFound = NotFound

    def __init__(self, config, pool):
        self.cache = LRUCache(maxsize=100)
        self.config = config
        super().__init__(pool)

    def declare_push_topic(
        self, sobject_type, record_type=None, exclude_current_user=False
    ):
        """
        Update or create Push Topic object

        Note that the update or create operation is not atomic and there
        is a race condition with multiple services trying to declare the topic
        at the same time.

        """

        if record_type:
            name = '{}{}'.format(sobject_type, record_type)
            record_type_id = self.get_record_type_id_by_name(
                sobject_type, record_type)
        else:
            name = sobject_type

        push_topic_query = (
            "SELECT Id, Name, LastModifiedById, LastModifiedDate FROM {}"
            .format(sobject_type))

        conditions = []
        if record_type:
            conditions.append(
                "RecordTypeId = '{}'".format(record_type_id))
        if exclude_current_user:
            current_user_id = self.get_user_id_by_name(
                self.config['SALESFORCE']['USERNAME'])
            conditions.append(
                "LastModifiedById != '{}'".format(current_user_id))

        if conditions:
            push_topic_query = '{} WHERE {}'.format(
                push_topic_query, ' AND '.join(conditions))

        push_topic_data = {
            'Name': name,
            'Query': push_topic_query,
            'ApiVersion': self.config['SALESFORCE']['API_VERSION'],
            'NotifyForOperationCreate': True,
            'NotifyForOperationUpdate': True,
            'NotifyForOperationUndelete': True,
            'NotifyForOperationDelete': True,
            'NotifyForFields': 'All',
        }

        try:
            record = self.get_push_topic_by_name(name)
        except NotFound:
            self.PushTopic.create(push_topic_data)
        else:
            self.PushTopic.update(record['Id'], push_topic_data)

    @cached
    def get_push_topic_by_name(self, name):
        query = (
            "SELECT Id, Name, Query "
            "FROM PushTopic WHERE Name = '{}'".format(name))
        response = self.query(query)
        if response['totalSize'] < 1:
            raise NotFound("PushTopic '{}' does not exist".format(name))
        return response['records'][0]

    @cached
    def get_user_id_by_name(self, username):
        query = (
            "SELECT Id FROM User WHERE Username = '{}'".format(username))
        response = self.query(query)
        if response['totalSize'] < 1:
            raise NotFound("User '{}' does not exist".format(username))
        return response['records'][0]['Id']

    @cached
    def get_record_type_id_by_name(self, sobject_type, record_type):
        query = (
            "SELECT Id, DeveloperName, SobjectType "
             "FROM RecordType WHERE SobjectType = '{}' "
             "AND DeveloperName = '{}'".format(sobject_type, record_type))
        response = self.query(query)
        if response['totalSize'] < 1:
            raise NotFound(
                "RecordType '{}' of '{}' does not exist"
                .format(sobject_type, record_type))
        return response['records'][0]['Id']
