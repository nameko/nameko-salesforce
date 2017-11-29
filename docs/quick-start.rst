.. _quick-start:

Quick Start
-----------

Create a service which handles Salesforce Contact objects changes and also
has an RPC endpoint for creating new Contact objects in Salesforce.

.. code-block:: python

    # service.py

    from nameko.rpc import rpc
    from nameko_salesforce.streaming import handle_sobject_notification
    from nameko_salesforce.api import SalesforceAPI

    class Service:

        name = 'some-service'

        salesforce = SalesforceAPI()

        @handle_sobject_notification('Contact', exclude_current_user=False)
        def handle_contact_updates(
            self, sobject_type, record_type, notification
        ):
        """ Handle Salesforce contacts updates
        """
        print(notification)

        @rpc
        def create_contact(self, last_name, email_address):
        """ Create a contact in Salesforce
        """
        self.salesforce.Contact.create(
            {'LastName': last_name,'Email': email_address})


Create a config file with essential settings:

.. code-block:: yaml

    # config.yaml

    AMQP_URI: 'pyamqp://guest:guest@localhost'
    SALESFORCE:
        USERNAME: ${SALESFORCE_USERNAME}
        PASSWORD: ${SALESFORCE_PASSWORD}
        SECURITY_TOKEN: ${SALESFORCE_SECURITY_TOKEN}
        SANDBOX: False

Run the service providing your Salesforce credentials:

.. code-block:: console

    $ SALESFORCE_USERNAME=rocky \
      SALESFORCE_PASSWORD=*** \
      SALESFORCE_SECURITY_TOKEN=*** \
      nameko run --config config.yaml service

Finally, open another shell and call the RPC endpoint to create a new user:

.. code-block:: console

    $ nameko shell --config config.yaml
    In [1]: n.rpc['some-service'].create_contact('Yo', 'yo@yo.yo')

You should see a new contact created in Salesforce and your service should
get a notification. In the first shell you'll find the notification printed:

.. code-block:: console

    {'event': {'replayId': 1, 'type': 'created' ...
