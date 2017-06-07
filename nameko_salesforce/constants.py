from enum import Enum


CONFIG_KEY = 'SALESFORCE'


DEFAULT_API_VERSION = '37.0'


DEFAULT_REPLAY_STORAGE_TTL = 60 * 60 * 12


class NotifyForFields(Enum):
    """ Specifies how the records are evaluated against the PushTopic query
    """

    all_ = 'All'
    """ All record field changes
    """

    referenced = 'Referenced'
    """ Changes to fields referenced in the SELECT and WHERE query clauses
    """

    select = 'Select'
    """ Changes to fields referenced in the SELECT clause of the query
    """

    where = 'Where'
    """ Changes to fields referenced in the WHERE clause of the query
    """
