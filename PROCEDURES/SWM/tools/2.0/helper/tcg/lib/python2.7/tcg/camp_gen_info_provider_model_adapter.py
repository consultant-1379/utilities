from tcg.plugin_api.SMFCampaignGenerationInfoProvider import SMFCampaignGenerationInfoProvider
from tcg.utils.logger_tcg import tcg_error
from tcg.plugin_api import SMFConstants
from tcg import CSMConstants, CgtConstants, AMFTools
from tcg.plugin_api.SMFApiObjects import CsmApiComponent, CsmApiRole,\
    CsmApiComputeResource, CsmApiComponentConfigFile, CsmApiService,\
    CsmApiComponentInstance
import os


class InfoProviderModelAdapter():

    @staticmethod
    def failInfoRequestedBeforeCapaignStart():
        tcg_error("Trying to get information before the start of a campaign "
                  "or procedure. The requested information is not available "
                  "at this point in time.")

    def __init__(self, uid, model):
        self._uid = uid  # the uid of the component defining the plugin
        self._model = model

        self._current_campaign = None
        self._current_procedure = None
        self._csm_config_root_location = None

        self._comp_types_to_be_migrated = None

        self._api_comps_cache = {}
        self._api_svs_cache = {}
        self._api_roles_cache = {}
        self._api_compute_resources_cache = {}

    def setCurrentCampaign(self, camp):
        self._current_campaign = camp

    def setCurrentProcedure(self, proc):
        self._current_procedure = proc

    def setCompTypesToBeMigrated(self, compTypes):
        self._comp_types_to_be_migrated = compTypes

    def setCsmConfigRootLocation(self, configRootLocation):
        self._csm_config_root_location = configRootLocation

    def getComponentActionType(self):
        if self._current_campaign is None:
            InfoProviderModelAdapter.failInfoRequestedBeforeCapaignStart()

        comp_types = self._current_campaign.getComponentTypes()
        if (self._uid in comp_types):
            comp = self._model.getComponent(self._uid)
            if self._uid in self._comp_types_to_be_migrated:
                return SMFConstants.CT_MIGRATE
            elif comp.is_install():
                return SMFConstants.CT_INSTALL
            elif comp.is_upgrade():
                return SMFConstants.CT_UPGRADE
            elif comp.is_removed():
                return SMFConstants.CT_REMOVE
            else:
                # Unchanged is assumed. This MUST CHANGE when support for
                # removal of components is added.
                return SMFConstants.CT_NOOP
        else:
            # the component is not present in the campaign
            return SMFConstants.CT_NOOP

    def getComponents(self,
                      scope=SMFCampaignGenerationInfoProvider.ALL,
                      onlyCdsComponents=False):
        if scope == SMFCampaignGenerationInfoProvider.ALL:
            return self._getAllComponents(onlyCdsComponents)
        elif scope == SMFCampaignGenerationInfoProvider.CAMPAIGN:
            return self._getCampaignComponents(onlyCdsComponents)
        elif scope == SMFCampaignGenerationInfoProvider.PROCEDURE:
            return self._getProcedureComponents(onlyCdsComponents)
        else:
            tcg_error("Incorrect usage of plugin interface. Unknown scope %s" % scope)

    def getComponent(self, compUid):
        comp = self._model.getComponent(compUid)
        if comp is not None:
            return self._transformToAPIComponent(comp)
        else:
            return None

    def getServices(self):
        ret = set()
        for sv in self._model.services_in_system():
            ret.add(self._transformToAPIService(sv))
        return ret

    def getComputeResources(self, roleId=None):
        ret = set()
        api_roles = self.getRoles()
        for api_role in api_roles:
            if roleId is not None and roleId != api_role.uid:
                continue  # we don't want this one
            ret.update(api_role.computeResources)
        return ret

    def getRoles(self):
        ret = set()
        for role in self._model.roles_in_system():
            ret.add(self._transformToAPIRole(role))
        return ret

    def extractConfigFiles(self,
                           api_comps,
                           dataType=None,
                           dataCategory=None):
        ret = set()
        for api_comp in api_comps:
            comp = self._model.getComponent(api_comp.uid)
            for configFile in comp.getConfigurationFiles():
                if dataType is not None and dataType != configFile.get_data_type():
                    continue  # we don't want this one
                if dataCategory is not None and dataCategory != configFile.get_data_category():
                    continue  # we don't want this one
                api_conf_file = CsmApiComponentConfigFile()
                api_conf_file.name = os.path.join(self._csm_config_root_location,
                                                  configFile.get_name())
                api_conf_file.dataType = configFile.get_data_type()
                api_conf_file.dataCategory = configFile.get_data_category()
                ret.add(api_conf_file)

        return ret

    def getServiceAllocation(self, serviceUid):
        ret = set()
        for api_role in self.getRoles():
            sv_uids = [sv.uid for sv in api_role.services]
            if serviceUid in sv_uids:
                ret.add(api_role)
        return ret

    def getComponentAllocation(self, componentUid):
        ret = set()
        for api_role in self.getRoles():
            for api_service in api_role.services:
                for comp_inst in api_service.componentInstances:
                    if comp_inst.component.uid == componentUid:
                        ret.add(api_role)
        return ret

    ###########################################################################
    # "Private" methods
    ###########################################################################

    def _extractCompInstActionTypeFromProc(self, proc):
        """
        returns a set of the action types of the component instances
        in the received procedure that correspond to the component type of
        this plugin.
        """
        # TODO
        pass

    def _getAllComponents(self, onlyCds):
        ret = set()
        for comp in self._model.components_in_system():
            if (not comp) or (onlyCds and comp.getAvailabilityManager().upper() != CSMConstants.AVAILABILTY_MANAGER_CDS):
                continue  # we don't want this one
            api_comp = self._transformToAPIComponent(comp)
            ret.add(api_comp)
        return ret

    def _getProcedureComponents(self, onlyCds):
        if self._current_procedure is None:
            InfoProviderModelAdapter.failInfoRequestedBeforeCapaignStart()

        return self._extractComponentsInProcedure(self._current_procedure, onlyCds)

    def _getCampaignComponents(self, onlyCds):
        if self._current_campaign is None:
            InfoProviderModelAdapter.failInfoRequestedBeforeCapaignStart()
        ret = set()
        for proc in self._current_campaign.getProcedures():
            ret.update(self._extractComponentsInProcedure(proc, onlyCds))
        return ret

    def _extractComponentsInProcedure(self, proc, onlyCds):
        ret = set()
        comp_uids = proc.getComponentTypes()
        for uid in comp_uids:
            comp = self._model.getComponent(uid)
            if (not comp) or (onlyCds and comp.getAvailabilityManager().upper() != CSMConstants.AVAILABILTY_MANAGER_CDS):
                continue  # we don't want this one
            ret.add(self._transformToAPIComponent(comp))
        return ret

    def _transformToAPIComponent(self, comp):
        the_uid = comp.getUid()
        if the_uid in self._api_comps_cache:
            return self._api_comps_cache[the_uid]

        api_comp = CsmApiComponent()
        api_comp.uid = the_uid
        api_comp.version = comp.getVersion()
        if (comp.getPlugin() is not None):
            api_comp.plugin = os.path.join(comp.getPluginsBaseDir(),
                                           comp.getPlugin())
        if (comp.get_software_type() is not None):
            if comp.get_software_type() == CgtConstants.COMPONENT_SOFTWARE_RPM_TAG:
                api_comp.swType = CsmApiComponent.RPM
            elif comp.get_software_type() == CgtConstants.COMPONENT_SOFTWARE_SDP_TAG:
                api_comp.swType = CsmApiComponent.SDP
            else:
                tcg_error("Unknown software type")
            api_comp.swPackages = comp.get_software_name_without_version()
        for fileName, bundle in comp.getMetaData().softwares():
            api_comp.swBundles.append((fileName, bundle))

        self._api_comps_cache[the_uid] = api_comp
        return api_comp

    def _transformToAPIRole(self, role):
        the_uid = role.getUid()
        if the_uid in self._api_roles_cache:
            return self._api_roles_cache[the_uid]

        api_role = CsmApiRole()
        api_role.uid = the_uid
        api_role.canScale = role.getCanScale()

        for service in role.getServices():
            api_service = self._transformToAPIService(service)
            api_role.services.append(api_service)

        roleToCR = self._model.system.getRolesToComputeResourcesMap()
        for cr in roleToCR[the_uid]:
            api_cr = self._transformToAPIComputeResouce(cr, api_role)
            api_role.computeResources.append(api_cr)

        self._api_roles_cache[the_uid] = api_role
        return api_role

    def _transformToAPIComputeResouce(self, crName, apiRole):
        if crName in self._api_compute_resources_cache:
            return self._api_compute_resources_cache[crName]
        api_cr = CsmApiComputeResource()
        api_cr.name = crName
        api_cr.dn = AMFTools.getNodeDnFromName(crName)
        api_cr.role = apiRole

        self._api_compute_resources_cache[crName] = api_cr
        return api_cr

    def _transformToAPIService(self, service):
        the_uid = service.getUid()
        if the_uid in self._api_svs_cache:
            return self._api_svs_cache[the_uid]

        api_service = CsmApiService()
        api_service.uid = the_uid
        api_service.version = service.getVersion()

        comp_instances = service.getComponentInstances()
        for instance_name, comp in comp_instances.iteritems():
            api_comp_instance = CsmApiComponentInstance()
            api_comp_instance.instanceName = instance_name
            api_comp_instance.component = self._transformToAPIComponent(comp)
            api_service.componentInstances.append(api_comp_instance)

        self._api_svs_cache[the_uid] = api_service
        return api_service
