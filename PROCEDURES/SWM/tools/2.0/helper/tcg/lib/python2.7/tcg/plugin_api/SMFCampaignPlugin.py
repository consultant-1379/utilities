import inspect
import logging

"""
###########################################################################
For deprecated methods

Three decorators and one function for give warning when Plugin keep using
deprecated methods.
Should delete this part when TCG stop supporting the deprecated methods.
###########################################################################
"""


def deprecated(func):
    """
    Decorator for deprecated interface function.
    This decorators adds a flag to the function definition to mark it as
    deprecated.
    """
    def wrapper(*args, **kw):
        return func(*args, **kw)
    setattr(wrapper, 'deprecated', True)
    return wrapper


def inspect_deprecated(deprecated_func_name):
    """
    Decorator used for inspecting if a deprecated method is being implemented
    by a plugin instance (subclass of this class). A warning will be logged
    when a plugin instance implements a deprecated method.
    Node: deprecated_func_name is the name of the deprecated method which wants
    to be inspected. Replacement function is the name of the method that should
    be used instead of the deprecated method.
    """
    def inspect_func(replacement_func):
        def wrapper(*args, **kw):
            if len(args) > 0:
                deprecated_func = getattr(args[0], deprecated_func_name, None)
                if deprecated_func:
                    if hasattr(deprecated_func, 'deprecated') and deprecated_func.deprecated:
                        # The deprecated flag is present. This means that the function is the
                        # original deprecated function defined in this class and the plugin
                        # instance (subclass) has not overwritten the method.
                        # There is nothing to do here.
                        pass
                    else:
                        # The inspected function does not contain the 'deprecated' flag,
                        # which means the plugin instance (subclass) has overwritten the default
                        # method. TCG will log a warning message.
                        logging.warn(
                            "SMF plugin {plugin_class} implements method {old_func}, which is not part of the supported CMW API and will be removed in future releases. Please use {new_func} method instead.".format(
                                plugin_class=get_class_that_defined_method(deprecated_func),
                                old_func=deprecated_func.__name__,
                                new_func=replacement_func.__name__
                            )
                        )
            return replacement_func(*args, **kw)
        return wrapper
    return inspect_func


def deprecated_getter(func):
    """
    Decorator for deprecated getter interface function.
    """
    def wrapper(*args, **kw):
        if len(args) > 0:
            logging.warn(
                "SMF plugin {plugin_class} is using method {old_func}, which is not part of the supported CMW API and will be removed in future releases.".format(
                    plugin_class=type(args[0]).__name__,
                    old_func=func.__name__
                )
            )
        return func(*args, **kw)
    setattr(wrapper, 'deprecated', True)
    return wrapper


def get_class_that_defined_method(meth):
    """
    Get the class name string which defined the method.
    Note: Be careful that it only works for class method.
    If the input is a function which not in any class, a
    empty string will be return.
    """
    if not hasattr(meth, 'im_class'):
        return ''
    for cls in inspect.getmro(meth.im_class):
        if meth.__name__ in cls.__dict__:
            return cls.__name__
    return ''


"""
###########################################################################
END of temporary codes for deprecated methods
###########################################################################
"""


class SMFCampaignPlugin(object):
    """
    The SMFCampaignPlugin class is the base class of a component level SMF
    campaign plugin.
    """

    def __init__(self):
        """
        DEPRECATED PRIVATE ATTRIBUTES!!! Plugin implementations must not rely
        on these variables
        """
        self._ctAction = None
        self._ctRootDir = None
        self._campaignName = None
        self._needCmwModelAdd = True
        self._needCmwModelDone = None
        self._isCtToBeMigrated = False

    """
    DEPRECATED CONSTANTS!!! Use constants from SMFConstants module
    """
    CT_ACTION_INSTALL = 1
    CT_ACTION_UPGRADE = 2
    CT_ACTION_REMOVE = 3
    CT_ACTION_NOOP = 4
    CT_ACTION_MIGRATE = 5

    """
    ###########################################################################

    GETTERS

    These functions were deprecated. The plugin author should get information
    through the instance of SMFCampaignGenerationInfoProvider class that
    is is received as argument in the 'prepare' function.
    Subclasses (i.e. plugin instances) should not overwrite the getters
    functions in this section.
    If you need any extra information not provided by the following getters,
    please contact Core MW team to discuss the requirement.

    ###########################################################################
    """

    @deprecated_getter
    def getActionType(self):
        """
        DEPRECATED!!!
        Use SMFCampaignGenerationInfoProvider.getComponentActionType() instead.
        """
        return self._ctAction

    @deprecated_getter
    def getCampaignName(self):
        """
        DEPRECATED!!!
        Use SMFCampaignGenerationInfoProvider.getCampaignName() instead.
        """
        return self._campaignName

    """
    ###########################################################################
    END of GETTERS
    ###########################################################################
    """
    """
    ###########################################################################

    PLUGIN LIFE CYCLE MANAGEMENT

    This section contains functions to let the plugin author perform actions
    in certain situations during the life cycle of the campaign generation.
    CoreMW will signal the particular life cycle event through the
    corresponding life cycle function and the plugin should implement the
    intended behavior in that situation.
    The plugin author can overwrite this functions if any action is required.

    ###########################################################################
    """

    def prepare(self, csmModelInformationProvider, pluginUtilitiesProvider):
        """
        It will be called to let the plugin implementation prepare for the
        campaign generation.
        Implementations for the interfaces SMFModelInformationProvider and
        SMFPluginUtilitiesProvider will be received as arguments. The plugin
        author should keep references to those implementations for further
        reuse during the life cycle of the plugin implementation.
        This function will be called when all the information available for the
        plugin author is ready to be used. In particular, it will be called
        after all the python modules from plugins of all the components in the
        system are loaded. This can be used by the plugin author to, for
        example, dynamically create dependencies towards other plugin's
        implementations. Note that static dependencies between plugin's
        implementations are not allowed since the order of the plugin loading
        is undefined.
        Return values will be ignored by CMW.
        """
        pass

    def startCampaign(self):
        """
        It will be called when a new campaign is stated to be created.
        This method will be called once for each of the generated campaigns.
        """
        pass

    def endCampaign(self):
        """
        It will be called when the all the data for the campaign is defined,
        and the campaign is ready to be created. When multiple campaigns are
        required, this method will be called once for each of the generated
        campaigns.
        """
        pass

    def finalize(self):
        """
        It will be called when all the required campaigns have been generated.
        This method will be called only once per software management operation
        """
        pass

    """
    ###########################################################################
    END of PLUGIN LIFE CYCLE MANAGEMENT
    ###########################################################################
    """
    """
    ###########################################################################

    MDF MODEL DELIVERY

    ###########################################################################
    """

    @inspect_deprecated('getNeedCmwModelAdd')
    def deliverModels(self):
        """
        Set the return of this function to false if models should not be
        delivered from the SDP in this component (ex: it will be done in a
        different component): default: True
        """
        return self.getNeedCmwModelAdd()

    @inspect_deprecated('getNeedCmwModelDone')
    def finalizeModelDelivery(self):
        """
        This method can be used to indicate to Core MW if the delivery of the
        models has to be finalized of not (cmw-model-done is invoked or not).
        It must be taken into account that it is not allowed that two
        components in the same campaign provide contradicting information. That
        is, if one of the components in the campaign explicitly requires
        finalization of the models delivery (returns True) and another
        component in the campaign explicitly requires that the model delivery
        is not finalized (returns False), then the campaign generation is
        aborted. Default None
        """
        return self.getNeedCmwModelDone()

    """
    ###########################################################################
    END of MDF MODEL DELIVERY
    ###########################################################################
    """

    """
    ###########################################################################

    CALLBACKS

    The callback functions return a list of 3-tuples with the following
    meaning:
    [(callbackLabel, callbackTimeout, stringToPass)].

    Since the callbackTimeout and stringToPass are optional in the campaign, it
    is possible to skip them if 'None' is provided as value.
    Example 1:
    [("my_special_callbackAtInit", 3600000000000, "abrakadabra")]
    Example 2:
    [("my_special_callbackAtInit", 3600000000000, None)]
    Example 3:
    [("my_special_callbackAtInit", 3600000000000, "abrakadabra"),
     ("this_one_is_even_better_callbackAtInit", 4, "topsecret")]

    If no callback is needed by the component, an empty list should be returned
    (this is the default implementation for each function).

    ###########################################################################
    """

    """
    ---------------------------------------------------------------------------
    Campaign level callbacks:
    The following campaign level callbacks are supported:
     - callbackAtInit
     - callbackAtRollback
     - callbackAtCommit
    Note: callbackAtBackup is not supported
    ---------------------------------------------------------------------------
    """

    @inspect_deprecated('getCallbacksAtInit')
    def callbackAtCampaignInit(self):
        """
        This function is called when TCG is generating the campaign init
        callbacks (callbackAtInit).
        """
        return self.getCallbacksAtInit()

    @inspect_deprecated('getCallbacksAtRollback')
    def callbackAtCampaignRollback(self):
        """
        This function is called when TCG is generating the campaign rollback
        callbacks (callbackAtRollback).
        """
        return self.getCallbacksAtRollback()

    @inspect_deprecated('getCallbacksAtCommit')
    def callbackAtCampaignCommit(self):
        """
        This function is called when TCG is generating the campaign commit
        callbacks (callbackAtCommit).
        """
        return self.getCallbacksAtCommit()

    """
    ---------------------------------------------------------------------------
    Procedure level callbacks:
    The following procedure level callbacks are supported:
     - callback at procedure initialization
     - callback at procedure wrapup
     - callback at rolling upgrade step
     ---------------------------------------------------------------------------
    """
    @inspect_deprecated('getCallbacksAtProcInit')
    def callbackAtProcInit(self):
        """
        This function is called when TCG is generating the procedure
        initialization callbacks in procInitAction. The callbacks at
        procInit are called after all the CLIs at procInit are completed.
        """
        return self.getCallbacksAtProcInit()

    @inspect_deprecated('getCallbacksAtProcWrapup')
    def callbackAtProcWrapup(self):
        """
        This function is called when TCG is generating the procedure wrapup
        callbacks in procWrapupAction. The callbacks at procWrapup are
        called after all the CLIs at procWrapup are completed.
        """
        return self.getCallbacksAtProcWrapup()

    @inspect_deprecated('getCallbacksAtRollingUpgradeStep')
    def callbackAtRollingUpgradeStep(self):
        """
        This function is an exception among the callbacks since it is returning
        a list of 5-tuples instead of 3-tuples. This is because these callbacks
        have a different structure and cannot exist without an "on step" and an
        "at action" parameter (see the schema definition e.g. the campaign.xsd
        for more information).
        The elements of the tuples are as the following:

        (label, timeout, stringToPass, on_step, at_action),

        where label 'on_step' and 'at_action' should take a valid value
        specified in SMFConstants.py. Example for the return value:

        [(SMFConstants.CALLBACK_LABEL_UPGRADE_CMD, '100000000000', dummy_script_1, SMFConstants.CALLBACK_ON_STEP_EVERY_STEP, SMFConstants.CALLBACK_AT_ACTION_BEFORE_LOCK),
         (SMFConstants.CALLBACK_LABEL_UPGRADE_CMD, '100000000000', dummy_script_2, SMFConstants.CALLBACK_ON_STEP_LAST_STEP, SMFConstants.CALLBACK_AT_ACTION_AFTER_UNLOCK)]

        Also note that the specified scripts must have group execution
        permissions.
        """
        return self.getCallbacksAtRollingUpgradeStep()

    """
    ###########################################################################

    CLIS

    The Cli commands are represented as a 2-tuple: (command, args) where
    command and args are strings (args is optional and is not defined in the
    campaign if its value is 'None')

    The action functions return a list of 3-tuples with the following meaning:
    [(do_cli_command_tuple, undo_cli_command_tuple, node)]

    The do_cli_command_tuple are undo_cli_command_tuple are Cli command
    2-tuples and the node is the target node where the commands needs to be
    issued. If the value of node is 'None' a controller node is chosen by TCG
    automatically.

    Example 1:
    [(("/bin/echo", "abrakadabra"),
      ("/bin/echo", "abradakabra"),
      "safAmfNode=SC-1,safAmfCluster=myAmfCluster")]

    If no cli command is needed by the component, an empty list should be
    returned (this is the default implementation for each function).

    ###########################################################################
    """

    """
    ---------------------------------------------------------------------------
    Campaign level Cli actions
    ---------------------------------------------------------------------------
    """

    @inspect_deprecated('getCliActionAtCampInit')
    def cliAtCampInit(self):
        """
        This function is called when TCG is generating the campaign init
        actions (campInitAction).
        """
        return self.getCliActionAtCampInit()

    @inspect_deprecated('getCliActionAtCampComplete')
    def cliAtCampComplete(self):
        """
        This function is called when TCG is generating the campaign complete
        actions (campCompleteAction).
        """
        return self.getCliActionAtCampComplete()

    @inspect_deprecated('getCliActionAtCampWrapup')
    def cliAtCampWrapup(self):
        """
        This function is called when TCG is generating the campaign wrapup
        actions (campWrapupAction).
        """
        return self.getCliActionAtCampWrapup()

    """
    ---------------------------------------------------------------------------
    Procedure level Cli actions
    ---------------------------------------------------------------------------
    """
    @inspect_deprecated('getCliActionAtProcInit')
    def cliAtProcInit(self):
        """
        This function is called when TCG is generating the procedure init
        actions (procInitAction). The procInit CLIs are executed before
        calling the callbacks at procInit.
        """
        return self.getCliActionAtProcInit()

    @inspect_deprecated('getCliActionAtProcWrapup')
    def cliAtProcWrapup(self):
        """
        This function is called when TCG is generating the procedure wrapup
        actions (procWrapupAction). The procWrapup CLIs are executed before
        calling the callbacks at procWrapup.
        """
        return self.getCliActionAtProcWrapup()

    """
    ###########################################################################
    # Reserved for future use
    ###########################################################################
    """
    def setSupportedInterfaceVersions(self):
        """
        Supported version for the plugin
        TODO: This feature in not implemented yet
        """
        return []

    """
    ###########################################################################
    # Everything below this line is deprecated.
    # If starting a new plugin only use methods above this line
    ###########################################################################
    """

    @deprecated
    def getNeedCmwModelAdd(self):
        """
        DEPRECATED!!! Use deliverModels(self) instead
        """
        return self._needCmwModelAdd

    @deprecated
    def getNeedCmwModelDone(self):
        """
        DEPRECATED!!! Use finalizeModelDelivery(self) instead
        """
        return self._needCmwModelDone

    @deprecated_getter
    def getCTAction(self):
        """
        DEPRECATED!!! Use getActionType(self) instead
        """
        return self._ctAction

    @deprecated_getter
    def isCTToBeMigrated(self):
        """
        DEPRECATED!!!
        Use SMFCampaignGenerationInfoProvider.getComponentActionType() to know
        if the component is being migrated.
        """
        return self._isCtToBeMigrated

    @deprecated_getter
    def getCTRootDirectory(self):
        """
        DEPRECATED!!! The CT root directory is the uid of the component.
        This is well known by the plugin designer and it does not really need
        to be provided by CMW.
        """
        return self._ctRootDir

    @deprecated
    def getCallbacksAtInit(self):
        """
        DEPRECATED!!! Use callbackAtCampaignInit(self) instead.
        """
        return []

    @deprecated
    def getCallbacksAtRollback(self):
        """
        DEPRECATED!!! Use callbackAtCampaignRollback(self) instead
        """
        return []

    @deprecated
    def getCallbacksAtCommit(self):
        """
        DEPRECATED!!! Use callbackAtCampaignCommit(self) instead
        """
        return []

    @deprecated
    def getCallbacksAtProcInit(self):
        """
        DEPRECATED!!! Use callbackAtProcInit(self) instead
        """
        return []

    @deprecated
    def getCallbacksAtProcWrapup(self):
        """
        DEPRECATED!!! Use callbackAtProcWrapup(self) instead
        """
        return []

    @deprecated
    def getCallbacksAtRollingUpgradeStep(self):
        """
        DEPRECATED!!! Use callbackAtRollingUpgradeStep(self) instead
        """
        return []

    @deprecated
    def getCliActionAtCampInit(self):
        """
        DEPRECATED!!! Use cliAtCampInit(self) instead
        """
        return []

    @deprecated
    def getCliActionAtCampComplete(self):
        """
        DEPRECATED!!! Use cliAtCampComplete(self) instead
        """
        return []

    @deprecated
    def getCliActionAtCampWrapup(self):
        """
        DEPRECATED!!! Use cliAtCampWrapup(self) instead
        """
        return []

    @deprecated
    def getCliActionAtProcInit(self):
        """
        DEPRECATED!!! Use cliAtProcInit(self) instead
        """
        return []

    @deprecated
    def getCliActionAtProcWrapup(self):
        """
        DEPRECATED!!! Use cliAtProcWrapup(self) instead
        """
        return []
