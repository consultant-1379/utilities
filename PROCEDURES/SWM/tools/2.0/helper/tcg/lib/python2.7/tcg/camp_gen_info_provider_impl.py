from tcg.plugin_api.SMFCampaignGenerationInfoProvider import SMFCampaignGenerationInfoProvider
from tcg.SystemModels import SystemModels
from tcg.camp_gen_info_provider_model_adapter import InfoProviderModelAdapter


class CampGenInfoProviderImpl(SMFCampaignGenerationInfoProvider):

    def __init__(self, uid):
        self._current_campaign_dir = None
        self._config_base_path = None
        self._config_base_target_dir = None

        self._target_adapter = InfoProviderModelAdapter(uid, SystemModels.targetCSMModel)
        if (SystemModels.baseCSMModel is not None):
            self._base_adapter = InfoProviderModelAdapter(uid, SystemModels.baseCSMModel)
        else:
            self._base_adapter = None

    ###########################################################################
    # Setters:
    # these methods are not part of the interface and are used by TCG code to
    # define data that can be accessed later by the plugin authors using the
    # methods from the interface SMFCampaignGenerationInfoProvider
    ###########################################################################

    def setCurrentCampaign(self, camp):
        # Only the target adapter needs the current campaign.
        # "Current campaign" is not a concept related to the base system
        self._target_adapter.setCurrentCampaign(camp)

    def setCurrentCampaignDir(self, campDir):
        self._current_campaign_dir = campDir

    def setCurrentProcedure(self, proc):
        # Only the target adapter needs the current procedure.
        # "Current procedure" is not a concept related to the base system
        self._target_adapter.setCurrentProcedure(proc)

    def setCompTypesToBeMigrated(self, comTypes):
        # Only the target adapter needs the component types to be migrated
        self._target_adapter.setCompTypesToBeMigrated(comTypes)

    def setCsmConfigRootLocation(self, configRootLocation):
        # Only the target adapter needs the config root location.
        self._target_adapter.setCsmConfigRootLocation(configRootLocation)

    def setConfigBasePath(self, configBasePath):
        self._config_base_path = configBasePath

    def setConfigBaseTargetDirectory(self, configBaseTargetDir):
        self._config_base_target_dir = configBaseTargetDir

    ###########################################################################
    # Implementation of interface SMFCampaignGenerationInfoProvider
    ###########################################################################

    def getCampaignName(self):
        """
        the campaign name is obtained using `basename $OSAFCAMPAIGNROOT` to
        ensure that the commands in the generated campaign does not contain its
        own name (otherwise the campaign cannot be merged)
        """
        return "`basename $OSAFCAMPAIGNROOT`"

    def getComponentActionType(self):
        return self._target_adapter.getComponentActionType()

    def getConfigBasePath(self):
        return self._config_base_path

    def getConfigBaseTargetDirectory(self):
        return self._config_base_target_dir

    def getCampaignDirectory(self):
        if self._current_campaign_dir is None:
            InfoProviderModelAdapter.failInfoRequestedBeforeCapaignStart()
        else:
            return self._current_campaign_dir

    def getComponents(self,
                      scope=SMFCampaignGenerationInfoProvider.ALL,
                      onlyCdsComponents=False):
        return self._target_adapter.getComponents(scope, onlyCdsComponents)

    def getBaseComponents(self, onlyCdsComponents=False):
        if self._base_adapter is not None:
            # For base components the only valid scope is ALL. The campaign and
            # procedures are not concepts related to the base system.
            return self._base_adapter.getComponents(SMFCampaignGenerationInfoProvider.ALL,
                                                    onlyCdsComponents)
        else:
            return None  # Installation or migration (no base system)

    def getComponent(self, compUid):
        return self._target_adapter. getComponent(compUid)

    def getBaseComponent(self, compUid):
        if self._base_adapter is not None:
            return self._base_adapter. getComponent(compUid)
        else:
            return None  # Installation or migration (no base system)

    def getServices(self):
        return self._target_adapter.getServices()

    def getBaseServices(self):
        if self._base_adapter is not None:
            return self._base_adapter.getServices()
        else:
            return None  # Installation or migration (no base system)

    def getComputeResources(self, roleId=None):
        return self._target_adapter.getComputeResources(roleId)

    def getBaseComputeResources(self, roleId=None):
        if self._base_adapter is not None:
            return self._base_adapter.getComputeResources(roleId)
        else:
            return None  # Installation or migration (no base system)

    def getRoles(self):
        return self._target_adapter.getRoles()

    def getBaseRoles(self):
        if self._base_adapter is not None:
            return self._base_adapter.getRoles()
        else:
            return None  # Installation or migration (no base system)

    def extractConfigFiles(self,
                           api_comps,
                           dataType=None,
                           dataCategory=None):
        return self._target_adapter.extractConfigFiles(api_comps,
                                                       dataType,
                                                       dataCategory)

    def getServiceAllocation(self, serviceUid):
        return self._target_adapter.getServiceAllocation(serviceUid)

    def getBaseServiceAllocation(self, serviceUid):
        if self._base_adapter is not None:
            return self._base_adapter.getServiceAllocation(serviceUid)
        else:
            return None  # Installation or migration (no base system)

    def getComponentAllocation(self, componentUid):
        return self._target_adapter.getComponentAllocation(componentUid)

    def getBaseComponentAllocation(self, componentUid):
        if self._base_adapter is not None:
            return self._base_adapter.getComponentAllocation(componentUid)
        else:
            return None  # Installation or migration (no base system)
