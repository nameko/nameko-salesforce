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
