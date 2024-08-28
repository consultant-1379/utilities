class CSMModelExpansionPluginContext(object):
    def __init__(self,
                 configBasePath,
                 siteConfig,
                 csmModelLocation,
                 csmPluginsLocation,
                 configBaseTargetDirectory,
                 tcgScriptDir,
                 deliveryPackageDirs):
        self._config_base_path = configBasePath
        self._site_config = siteConfig
        self._csm_config_root_location = csmModelLocation
        self._csm_plugin_root_location = csmPluginsLocation
        self._config_base_target_directory = configBaseTargetDirectory
        self._tcg_script_dir = tcgScriptDir
        self._delivery_package_dirs = deliveryPackageDirs

    def getConfigBasePath(self):
        return self._config_base_path

    def getSiteConfig(self):
        return self._site_config

    def getCsmConfigRootLocation(self):
        return self._csm_config_root_location

    def getCsmPluginRootLocation(self):
        return self._csm_plugin_root_location

    def getConfigBaseTargetDirectory(self):
        return self._config_base_target_directory

    def getTcgScriptDir(self):
        return self._tcg_script_dir

    def getDeliveryPackageDirs(self):
        return self._delivery_package_dirs
