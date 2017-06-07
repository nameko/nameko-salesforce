=================
Nameko Salesforce
=================

This library contains a `Nameko`_ extension which acts as a client to `Salesforce Streaming API`_
and a `Nameko`_ dependency for easy communication with `Salesforce REST API`_.

The Streaming API extension is based on `Nameko Cometd Bayeux Client`_ and the REST API dependency
id based on `Simple Salesforce`.

.. _Nameko: http://nameko.readthedocs.org

.. _Salesforce Streaming API:
    https://developer.salesforce.com/docs/atlas.en-us.api_streaming.meta/api_streaming/intro_stream.htm

.. _Salesforce REST API:
    https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/intro_what_is_rest_api.htm

.. _Nameko Cometd Bayeux Client:
    https://github.com/Overseas-Student-Living/nameko-bayeux-client

.. _Simple Salesforce:
    https://github.com/simple-salesforce/simple-salesforce


Configuration
=============

TODO describe ...

.. code-block:: yaml

    # config.yaml

    SALESFORCE:
        USERNAME: ${SALESFORCE_USERNAME}
        PASSWORD: ${SALESFORCE_PASSWORD}
        SECURITY_TOKEN: ${SALESFORCE_SECURITY_TOKEN}
        SANDBOX: False


Salesforce Streaming API client
===============================

TODO describe ...

.. code-block:: python

    # service.py

    from nameko_salesforce.streaming import subscribe

    class Service:

        name = 'some-service'

        @subscribe('/topic/InvoiceStatementUpdates')
        def handle_event(self, topic, event):
            """ Handle Salesforce invoice statement updates
            """

TODO describe ...

.. code-block:: python

    # service.py

    from nameko_salesforce.streaming import handle_notification

    class Service:

        name = 'some-service'

        @handle_notification(
            name='ContactUpdates',
            query='SELECT ...'
        )
        def handle_contact_updates(self, name, notification):
            """ Handle Salesforce contacts updates
            """

TODO describe ...

.. code-block:: python

    # service.py

    from nameko_salesforce.streaming import handle_notification

    class Service:

        name = 'some-service'

        @handle_notification(
            name='ContactNameUpdated',
            query='SELECT firstName, lastName ...',
            notify_for_fields=NotifyForFields.select,
            notify_for_operation_update=True,
            notify_for_operation_create=False,
            notify_for_operation_undelete=False,
            notify_for_operation_delete=False)
        def handle_contact_updates(self, name, notification):
            """ Handle Salesforce contacts name changes
            
            Handles only first and last name changes of existing contacts.
            Ignores any other modification.

            """

TODO describe ...

.. code-block:: python

    # service.py

    from nameko_salesforce.streaming import handle_sobject_notification

    class Service:

        name = 'some-service'

        @handle_sobject_notification('Contact')
        def handle_contact_updates(
            self, sobject_type, record_type, notification
        ):
            """ Handle Salesforce contacts updates
            """

More notification options:

.. code-block:: python

    # service.py

    from nameko_salesforce.streaming import handle_sobject_notification

    class Service:

        name = 'some-service'

        @handle_sobject_notification(
            sobject_type='Contact',
            record_type='Student',
            exclude_current_user=True,
            notify_for_fields=NotifyForFields.select,
            notify_for_operation_update=True,
            notify_for_operation_create=False, 
            notify_for_operation_undelete=False,
            notify_for_operation_delete=False) 
        def handle_contact_updates(self, topic, event):
            """ Handle Salesforce student contacts name changes
            
            Handles only first and last name changes of existing contacts
            of type of student. Ignores any other modification.
            
            Also ignores changes done by this service (more precisely changes
            done by the same API user as this extension use for connection
            to Salesforce streaming API).

            """


Salesforce API Dependency
=========================

TODO describe ...

.. code-block:: python

    # service.py

    from nameko_salesforce.api import SalesforceAPI

    class Service:

        name = 'some-service'

        salesforce = SalesforceAPI()

        @rpc
        def create_contact(self, last_name, email_address):
            self.salesforce.Contact.create(
                {'LastName': last_name,'Email': email_address})
