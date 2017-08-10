import operator

from cachetools import LRUCache, cachedmethod

from nameko_salesforce.api.client import ClientPool, ClientProxy
from nameko_salesforce import constants


cached = cachedmethod(operator.attrgetter('cache'))


class NotFound(LookupError):
    pass


def get_client(*args, **kwargs):
    pool = ClientPool(*args, **kwargs)
    return PushTopicsAPIClient(pool)


class PushTopicsAPIClient(ClientProxy):
    """
    Salesforce API client with helper method for managing PushTopic object

    """

    NotFound = NotFound

    def __init__(self, pool):
        self.cache = LRUCache(maxsize=100)
        super().__init__(pool)

    def declare_push_topic_for_sobject(
        self,
        sobject_type,
        record_type=None,
        exclude_current_user=False,
        notify_for_fields=constants.NotifyForFields.all_,
        notify_for_operation_create=True,
        notify_for_operation_update=True,
        notify_for_operation_delete=True,
        notify_for_operation_undelete=True,
    ):
        """
        Update or create Push Topic object notifying given sobject changes

        :sobject_type:
            Name of the Salesforce object (e.g. Contact, Task, ...)

        :record_type:
            Optional record type name filtering notifications for a subset
            of the given Salesforce object type.

        :exclude_current_user:
            Exclude changes done by the same user as this extension uses to
            connect to the Salesforce API. Defaults to ``False``.

        """

        if record_type:
            name = '{}{}'.format(sobject_type, record_type)
            record_type_id = self.get_record_type_id_by_name(
                sobject_type, record_type)
        else:
            name = sobject_type

        query = (
            "SELECT Id, Name, LastModifiedById, LastModifiedDate FROM {}"
            .format(sobject_type))

        conditions = []
        if record_type:
            conditions.append(
                "RecordTypeId = '{}'".format(record_type_id))
        if exclude_current_user:
            current_user_id = self.get_user_id_by_name(
                self.pool.username)
            conditions.append(
                "LastModifiedById != '{}'".format(current_user_id))

        if conditions:
            query = '{} WHERE {}'.format(
                query, ' AND '.join(conditions))

        return self.declare_push_topic(
            name=name,
            query=query,
            notify_for_fields=notify_for_fields,
            notify_for_operation_create=notify_for_operation_create,
            notify_for_operation_update=notify_for_operation_update,
            notify_for_operation_delete=notify_for_operation_delete,
            notify_for_operation_undelete=notify_for_operation_undelete)

    def declare_push_topic(
        self,
        name=None,
        query=None,
        notify_for_fields=constants.NotifyForFields.all_,
        notify_for_operation_create=True,
        notify_for_operation_update=True,
        notify_for_operation_delete=True,
        notify_for_operation_undelete=True,
    ):
        """
        Update or create Push Topic object

        Note that the update or create operation is not atomic and there
        is a race condition with multiple services trying to create the same
        topic at the same time.

        :params name:
            Descriptive name of the Push Topic object to create,
            such as `MyNewCases` or `TeamUpdatedContacts`. The maximum length
            is 25 characters. This value identifies the channel and must be
            unique.

        :param query:
            The SOQL query statement that determines which record changes
            trigger events to be sent to the channel.

        :params notify_for_fields:
            Specifies which fields are evaluated to generate a notification.
            See :class:`~.constants.NotifyForFields` for valid options.

        :params notify_for_operation_create:
            ``True`` if a create operation should generate a notification,
            otherwise, ``False``. Defaults to ``True``.

        :params notify_for_operation_update:
            ``True`` if an update operation should generate a notification,
            otherwise, ``False``. Defaults to ``True``.

        :params notify_for_operation_delete:
            ``True`` if a delete operation should generate a notification,
            otherwise, ``False``. Defaults to ``True``.

        :params notify_for_operation_undelete:
            ``True`` if an undelete operation should generate a notification,
            otherwise, ``False``. Defaults to ``True``.

        """

        if not isinstance(notify_for_fields, constants.NotifyForFields):
            notify_for_fields = constants.NotifyForFields(notify_for_fields)

        push_topic_data = {
            'Name': name,
            'Query': query,
            'ApiVersion': self.pool.api_version,
            'NotifyForOperationCreate': notify_for_operation_create,
            'NotifyForOperationUpdate': notify_for_operation_update,
            'NotifyForOperationDelete': notify_for_operation_delete,
            'NotifyForOperationUndelete': notify_for_operation_undelete,
            'NotifyForFields': notify_for_fields.value,
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
