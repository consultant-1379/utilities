from abc import ABCMeta, abstractmethod


class SMFCampaignGenerationInfoProvider(object):
    """
    This class defines the interface that the plugin author can use to get
    information from the CMW about the system model and the campaign generation
    """

    __metaclass__ = ABCMeta

    """
    Constants to be used when defining the scope of a query
    """
    ALL = 0
    CAMPAIGN = 1
    PROCEDURE = 2

    @abstractmethod
    def getCampaignName(self):
        """
        Returns a string representing a macro that will resolve to the name of
        the campaign. If this macro is used as part of the campaign (for
        example as part of a CLI or callback) then, when the campaign template
        is instantiated during campaign execution, this macro will be resolved
        to the actual name of the campaign.
        """

    @abstractmethod
    def getComponentActionType(self):
        """
        Returns the action in the current campaign with respect to the
        Component type. If the component type is not present in the campaign
        a SMFConstants.CT_NOOP is returned. The possible return values are:

            SMFConstants.CT_INSTALL
            SMFConstants.CT_UPGRADE
            SMFConstants.CT_REMOVE
            SMFConstants.CT_NOOP
            SMFConstants.CT_MIGRATE
        """

    @abstractmethod
    def getConfigBasePath(self):
        """
        Provides the path to the base configuration in the system
        """

    @abstractmethod
    def getConfigBaseTargetDirectory(self):
        """
        Provides the path to the target base configuration in the system
        """

    @abstractmethod
    def getCampaignDirectory(self):
        """
        Provides the path to the directory containing where the campaigns' SDPs
        are generated
        """

    @abstractmethod
    def getComponents(self, scope=ALL, onlyCdsComponents=False):
        """
        Returns a list of the components that comply to the filter criteria
        defined by the parameters.

        Argument 'scope' must be one of the following values:
            ALL: selects all the components in the system
            CAMPAIGN: selects only the components in current campaign
            PROCEDURE: selects only the components in current procedure

        Argument 'onlyCdsComponents' must be one of the following values:
            True: only components with availability manager CDS are considered
            False: all components in the system are considered
        """

    @abstractmethod
    def getBaseComponents(self, onlyCdsComponents=False):
        """
        Returns a list of the components present in the base system that comply
        to the filter criteria defined by the parameters.

        Argument 'onlyCdsComponents' must be one of the following values:
            True: only components with availability manager CDS are considered
            False: all components in the system are considered

        In case of maiden installation or migrations, this method returns
        always 'None' because there is no ESM base system
        """

    @abstractmethod
    def getComponent(self, componentUid):
        """
        Returns component (CsmApiComponent object) for the corresponding uid
        """

    @abstractmethod
    def getBaseComponent(self, componentUid):
        """
        Returns component (CsmApiComponent object) in the base system for the
        corresponding uid

        In case of maiden installation or migrations, this method returns
        always 'None' because there is no ESM base system
        """

    @abstractmethod
    def getServices(self):
        """
        Returns the set of the services (CsmApiService objects) to be deployed
        in the system
        """

    @abstractmethod
    def getBaseServices(self):
        """
        Returns the set of the services (CsmApiService objects) already
        deployed in the base system.

        In case of maiden installation or migrations, this method returns
        always 'None' because there is no ESM base system
        """

    @abstractmethod
    def getComputeResources(self, roleUid=None):
        """
        returns the set of the compute resources of the system.
        If a role uid is specified, only the compute resources for that role
        are considered
        """

    @abstractmethod
    def getBaseComputeResources(self, roleUid=None):
        """
        returns the set of the compute resources of the base system.
        If a role uid is specified, only the compute resources for that role
        are considered.

        In case of maiden installation or migrations, this method returns
        always 'None' because there is no ESM base system
        """

    @abstractmethod
    def getRoles(self):
        """
        returns the set of the roles of the system
        """

    @abstractmethod
    def getBaseRoles(self):
        """
        returns the set of the roles of the base system

        In case of maiden installation or migrations, this method returns
        always 'None' because there is no ESM base system
        """

    @abstractmethod
    def extractConfigFiles(self,
                           components,
                           dataType=None,
                           dataCategory=None):
        """
        Return the list of the configuration files (CsmApiComponentConfigFile
        objects) corresponding to the received components.
        The resulting list comply to the filter criteria defined by the
        parameters.

        components -> iterator over CsmApiComponent objects
        dataType -> None: all values
                 -> not None: applies the argument filter
        dataCategory -> None: all values
                     -> not None: applies the argument filter
        """

    @abstractmethod
    def getServiceAllocation(self, serviceUid):
        """
        Returns the set of roles (CsmApiRole objects) where the service is
        allocated
        """

    @abstractmethod
    def getBaseServiceAllocation(self, serviceUid):
        """
        Returns the set of roles (CsmApiRole objects) where the service is
        allocated in the base system.

        In case of maiden installation or migrations, this method returns
        always 'None' because there is no ESM base system
        """

    @abstractmethod
    def getComponentAllocation(self, componentUid):
        """
        Returns the set of roles (CsmApiRole objects) where the component is
        allocated
        """

    @abstractmethod
    def getBaseComponentAllocation(self, componentUid):
        """
        Returns the set of roles (CsmApiRole objects) where the component is
        allocated in the base system.

        In case of maiden installation or migrations, this method returns
        always 'None' because there is no ESM base system
        """
