from tcg.plugin_api.SMFCampaignPlugin import SMFCampaignPlugin


class CSMModelExpansionPlugin(SMFCampaignPlugin):

    def __init__(self):
        super(CSMModelExpansionPlugin, self).__init__()

    def extendDependencyCalculation(self, baseModel):
        """
        Function to return the objects that will be used to extend the
        dependency calculation.
        If parameter baseModel is True, the plugin has to return the extensions
        to the base model. If parameter baseModel is false, the plugin has to
        return the extansions to the target model.
        The expected result is a list of CsmApiPool objects
        """
        return []

    def extendCampaignBundles(self):
        """
        Function to return the sw bundles for the components that
        the plugin adds to the campaign.
        The expected result is a list of tuples of the (componentUid, fileName,
        bundleName) with the values as present in the CSM model
        """
        return []

    def injectServiceDependencies(self, serviceUid):
        """
        Function to return the dependencies for the corresponding service
        that will be injected in the dependency calculation.

        The expected result is a list of pairs (serviceUid, dependencyType)
        where dependencyType must be one of the following:
            SmfConstants.NOT_BEFORE,
            SmfConstants.DIFFERENT_PROCEDURE
            SmfConstants.DIFFERENT_CAMPAIGN
        """
        return []

    def addSoftwareInSingleStep(self):
        """
        Function used to provide additional sw bundles that are not handled by
        CMW.

        The expected result is a map where the key is the bundle name (as it is
        present in the CSM model) and the value is the list of nodes where the
        sw needs to be installed
        """
        return {}

    def removeSoftwareInSingleStep(self):
        """
        Function used to provide sw bundles that have to be removed from the
        system and are not handled by CMW.

        The expected result is a map where the key is the bundle name (as it is
        present in the CSM model) and the value is the list of nodes from where
        the sw needs to be removed
        """
        return {}

    def addSoftwareInRolling(self):
        """
        Function used to provide additional sw bundles that are not handled by
        CMW.

        The expected result is a list of bundle names (as it is
        present in the CSM model)
        """
        return []

    def removeSoftwareInRolling(self):
        """
        Function used to provide sw bundles that have to be removed from the
        system and are not handled by CMW.

        The expected result is a list of bundle names (as it is
        present in the CSM model)
        """
        return []
