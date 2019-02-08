.. Nameko Salesforce documentation master file, created by
   sphinx-quickstart on Wed Jun  7 22:48:11 2017.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Nameko Salesforce
=================

A `Nameko`_ extension with entrypoints for handling `Salesforce Streaming API`_ events
and a dependency provider for easy communication with `Salesforce REST API`_.

The Streaming API extension is based on `Nameko Cometd Bayeux Client`_ and the REST API dependency
id based on `Simple Salesforce`_.

.. _Nameko: http://nameko.readthedocs.org

.. _Salesforce Streaming API:
    https://developer.salesforce.com/docs/atlas.en-us.api_streaming.meta/api_streaming/intro_stream.htm

.. _Salesforce REST API:
    https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/intro_what_is_rest_api.htm

.. _Nameko Cometd Bayeux Client:
    https://github.com/nameko/nameko-bayeux-client

.. _Simple Salesforce:
    https://github.com/simple-salesforce/simple-salesforce


.. toctree::
   :maxdepth: 3
   :caption: Contents:

   quick-start
   streaming-api-client
   rest-api-client
   configuration
