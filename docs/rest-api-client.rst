.. _rest-api-client:

Salesforce Rest API Client
==========================

.. _dependencies:

Nameko Dependency
-----------------

The ``SalesforceAPI`` dependency provider wraps Simple Salesforce client plus
brings additional benefits of **client pooling** and :ref:`connection setup <configuration>`
using standard Nameko config.

Usage:

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
