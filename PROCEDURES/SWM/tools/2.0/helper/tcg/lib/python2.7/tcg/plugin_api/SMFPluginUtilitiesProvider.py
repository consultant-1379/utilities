from abc import ABCMeta, abstractmethod


class SMFPluginUtilitiesProvider(object):
    """
    This class defines the interface that the plugin author can use to access
    utilities to help the development and troubleshooting of SMF Campaign
    Plugins
    """

    __metaclass__ = ABCMeta

    """
    Constants to be used when logging
    """
    CRITICAL = 0
    ERROR = 1
    WARNING = 2
    INFO = 4
    DEBUG = 5

    @abstractmethod
    def log(self, msg, severity):
        """
        Used to define a logging point with a particular level.
        Supported levels are 'DEBUG', 'INFO', 'WARNING', 'ERROR',
        'CRITICAL':
        """

    @abstractmethod
    def reportUnrecoverableError(self, msg):
        """
        Used to report that the plugin has found an error from which it can not
        recover and the campaign generation must be aborted.
        """
