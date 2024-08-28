from tcg.plugin_api.SMFPluginUtilitiesProvider import SMFPluginUtilitiesProvider

import logging
from tcg.utils.logger_tcg import tcg_error


class PluginUtilitiesProviderImpl(SMFPluginUtilitiesProvider):

    def __init__(self, uid):
        self._uid = uid  # the uid of the entity defining the plugin

    def log(self, msg, severity):
        if severity == SMFPluginUtilitiesProvider.CRITICAL:
            logging.critical(msg)
        elif severity == SMFPluginUtilitiesProvider.ERROR:
            logging.error(msg)
        elif severity == SMFPluginUtilitiesProvider.WARNING:
            logging.warn(msg)
        elif severity == SMFPluginUtilitiesProvider.INFO:
            logging.info(msg)
        elif severity == SMFPluginUtilitiesProvider.DEBUG:
            logging.debug(msg)
        else:
            #  unexpected severity
            logging.error("TCG plugin for component '%s' is trying to log a "
                          "message with unknown severity. Message is: %s" % (self._uid, msg))

    def reportUnrecoverableError(self, msg):
        tcg_error(msg)
