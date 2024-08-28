from plugin_contexts import CSMModelExpansionPluginContext

class CSMModelExpansionPluginBase(object):
    def __init__(self, pluginContext):
        self._configBasePath = pluginContext.getConfigBasePath()
        self._siteConfig = pluginContext.getSiteConfig()
        self._configBaseTargetDirectory = pluginContext.getConfigBaseTargetDirectory()
        self._csm_config_root_location = pluginContext.getCsmConfigRootLocation()
        self._csm_plugin_root_location = pluginContext.getCsmPluginRootLocation()
        self._tcgScriptDir = pluginContext.getTcgScriptDir()
        self._deliveryPackageDirs = pluginContext.getDeliveryPackageDirs()

    def initialize(self, installPrefixes):
        pass

    def setMigrationInfo(self, migrationInfo):
        pass

    def fillConfig(self, config, ctAllocations, isBaseConfig):
        pass

    def isProcWrapupCallbackNeeded(self):
        return False

    def getSVDependencies(self, pool, svId, isToBeMigrated = False):
        constraintList = []
        return constraintList

    def getCTDependencies(self, pool, ctId, isToBeMigrated = False):
        constraintList = []
        return constraintList

    def startCampaign(self, procedures, campaignName, smfCampaign, campaignDirectory):
        pass

    def addTypes(self):
        pass

    def generateCampInitActions(self, phase, campaignDirectory, mergeableCampaignName):
        pass

    def startProcedure(self, proc):
        pass

    def generateProcInit(self, updatedSVs):
        pass

    def generateSingleStepProcedureInit(self):
        pass

    def generateSingleStepProcedureBody(self):
        pass

    def generateRollingProcedureInit(self):
        pass

    def generateRollingProcedureBody(self):
        pass

    def generateRollingProcedureTargetEntityTemplate(self):
        pass

    def generateProcWrapup(self):
        pass

    def generateCommit(self):
        pass

    def generateRemoveFromImm(self):
        pass

    def endCampaign(self):
        pass

    def generatePostCampaign(self):
        pass

    def getCampaignSVs(self):
        return {}

    def getCampaignCTs(self):
        return {}

    def getSDPsInCampaign(self):
        return []

    def getCsmConfigRootLocation(self):
        return self._csm_config_root_location

    def getCsmPluginRootLocation(self):
        return self._csm_plugin_root_location
