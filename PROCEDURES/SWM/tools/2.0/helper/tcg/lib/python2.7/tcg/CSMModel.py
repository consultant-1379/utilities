import os
import re
import logging
import copy
import xml.dom.minidom
import shutil

from utils.yaml_parser import YamlParser
from csm_units import component
from csm_units import service
from csm_units import function
from csm_units import role
from csm_units import system
from csm_units import deployment_profile
import CgtConstants
from utils.logger_tcg import tcg_error
import CSMConstants
import AMFConstants
import CSMTools
import Utils
import AMFModel
import ImmHelper
import AMFTools
from CSMConstants import validateAndGetBool


def getValue(searchTag=None, input_dict_list=[], recursionFlag=False, parentTag=None, defaultValue=None):

    if not parentTag :
        queryResult = YamlParser.getInstance().getNodesByName2(name=searchTag,
                                                     inputDictList=input_dict_list,
                                                     recursionFlag=recursionFlag)
    else :
        queryResult = YamlParser.getInstance().getChildNodesInParentNodeFromDictionaries(
                                                   childNodeName=searchTag,
                                                   inputDictList=input_dict_list,
                                                   parentNodeName=parentTag,
                                                   recursionFlag=recursionFlag)

    if queryResult != [] :
        return queryResult[0][searchTag] if queryResult[0][searchTag] is not None else defaultValue

    return defaultValue

class CSMModel():
    '''
    class to create CSM units from CSM Yaml
    '''
    def __init__(self, model_context_data):
        self.components = []
        self.services = []
        self.functions = []
        self.roles = []
        self.role_map = {}
        self.system = None
        self.system_map = {}
        self.function_map = {}
        self.service_map = {}
        self.component_map = {}
        self.deployment_profile = None
        self.external_system_components = []
        self.external_system_services = []
        self.model_context_data = model_context_data
        self.csm_version = None
        self.original_system = None

    def parseInputYaml(self, inputYaml, unitType):
        returnList = []
        queryResult = YamlParser.getInstance().getNodesByName(name=unitType,
                                                              inputYaml=inputYaml,
                                                              recursionFlag=False)
        if queryResult == []:
            logging.debug("No %s found in %s" % (unitType, inputYaml))
        else:
            to_append = queryResult[0][unitType]
            if to_append is not None:
                if type(to_append) is list:
                    returnList.extend(to_append)
                else:
                    returnList.append(to_append)
        return returnList

    def __contains__(self, item):
        """
        Return True if the inputed item instance is in CSM model.
        """
        if not self.system:
            return False
        if type(item) is system.System:
            return (
                self.system.getName() == item.getName() and
                self.system.getVersion() == item.getVersion()
            )
        if type(item) is role.Role:
            return self.__isRoleInModel(item)
        if type(item) is service.Service:
            return self.__isServiceInModel(item)
        if type(item) is component.Component:
            return self.__isComponentInModel(item)
        if type(item) is function.Function:
            return self.__isFunctionInModel(item)
        return False

    def __isRoleInModel(self, role):
        """
        Return True if role instance is in CSM model.
        """
        for r in self.system.getRoles():
            if r.getUid() == role.getUid():
                return True
        return False

    def __isServiceInModel(self, service):
        """
        Return True if service instance is in CSM model.
        """
        for serv in self.system.getServices():
            if serv.getUid() == service.getUid():
                return True
        return False

    def __isComponentInModel(self, component):
        """
        Return True if component instance is in CSM model.
        """
        for comp in self.system.getComponents():
            if comp.getUid() == component.getUid():
                return True
        return False

    def __isFunctionInModel(self, function):
        """
        Return True if function instance is in CSM model.
        """
        for func in self.system.getFunctions():
            if func.getUid() == function.getUid():
                return True
        return False

    def roles_in_system(self):
        for r in self.system.getRoles():
            yield r

    def get_role_in_system(self, uid):
        for r in self.roles_in_system():
            if r.getUid() == uid:
                return r
        return None

    def functions_in_system(self):
        for func in self.system.getFunctions():
            yield func

    def get_function_in_system(self, uid):
        for func in self.functions_in_system():
            if func.getUid() == uid:
                return func
        return None

    def services_in_system(self):
        for serv in self.system.getServices():
            yield serv

    def get_service_in_system(self, uid):
        for serv in self.services_in_system():
            if serv.getUid() == uid:
                return serv
        return None

    def components_in_system(self):
        for comp in self.system.getComponents():
            yield comp

    def get_component_in_system(self, uid):
        for comp in self.components_in_system():
            if comp.getUid() == uid:
                return comp
        return None

    def _get_nodes_for_role(self, role, amfModel):
        nodes = set()
        if role.isExternal() and amfModel:
            for ngObj in amfModel.getObjects(AMFModel.SaAmfNodeGroup).values():
                if ngObj.getName() == role.getUid():
                    for nodeDn in ngObj.getsaAmfNGNodeList():
                        node = ImmHelper.getName(nodeDn)
                        nodes.add(node)
                    break
        else:
            for node in self.system.getComputeResources():
                if node.getRole() == role.getUid():
                    nodes.add(node.getName())
        return nodes

    def generate_component_allocations(self, amfModel = None):
        """
        Return component to node allocations.
        """
        allocations = {}
        for (comp, serv, ro) in (
            (comp, serv, ro)
            for ro in self.roles_in_system()
            for serv in ro.getServices()
            for comp in serv.getComponentTypes()
        ):
            role_uid = ro.getUid()
            nodes = self._get_nodes_for_role(ro, amfModel)

            if comp not in allocations:
                allocations[comp] = [(comp.getVersion(), serv, role_uid, nodes)]
            else:
                allocations[comp].append((comp.getVersion(), serv, role_uid, nodes))
        return allocations

    def get_component_allcated_services(self, comp):
        """
        Return a list of service UID which service contains the component
        Argument comp can be component UID string or Component object.
        """
        servs = []
        for serv in self.services_in_system():
            if comp in serv:
                servs.append(serv.getUid())
        return servs

    def copy_site_dependent_information(self, other_model):
        """
        This method copies the site dependent information from the received
        model into this model
        """
        if not other_model or not self.system:
            return
        self.system.copy_site_dependent_info(other_model.getSystem())

    def validate_csm_version(self, version):
        """
        Check if the provided version is in the allowed range.
        """
        ret = (False, 0)
        if "." not in version:
            tcg_error("Expected a csm-version in the format major.minor. Received %s" %version)
        major = version.split(".")[0]
        minor = version.split(".")[1]

        try:
            major = int(major)
        except ValueError:
            return ret
        try:
            minor = int(minor)
        except ValueError:
            return ret

        if major < CSMConstants.CSM_VER_MINUMUM_MAJOR or \
                    major > CSMConstants.CSM_VER_MAXIMUM_MAJOR:
            return ret
        if minor < CSMConstants.CSM_VER_MINUMUM_MINOR or \
                    minor > CSMConstants.CSM_VER_MAXIMUM_MINOR:
            return ret

        return (True, float("%d.%d"%(major, minor)))

    def generateCSMUnitInstances(self, modelFiles, config_base=None, online_adapter=None):

        #Check CSM version
        csm_ver_found = False
        csm_versions = []
        for inputYaml in modelFiles:
            ver = self.parseInputYaml(inputYaml, CgtConstants.CSM_VERSION_TAG)
            if len(ver) > 0:
                csm_ver_found = True
                # Only the first version will be taken, if there are multiple versions in CSM file
                str_version = ver[0]
                valid, float_version = self.validate_csm_version(str_version)
                if not valid:
                    tcg_error("csm-version is not correct for %s. Supported range: %d.%d - %d.%d."  \
                              %(inputYaml, \
                                CSMConstants.CSM_VER_MINUMUM_MAJOR, \
                                CSMConstants.CSM_VER_MINUMUM_MINOR, \
                                CSMConstants.CSM_VER_MAXIMUM_MAJOR, \
                                CSMConstants.CSM_VER_MAXIMUM_MINOR))
                else:
                    csm_versions.append((float_version, str_version))
            else:
                logging.warning("File %s does not have a csm-version." %inputYaml)
        if not csm_ver_found:
            if config_base is None:
                logging.debug("csm-version is mandatory but not contained in any of the provided model files. This can be OK older config-base directories.")
            else:
                tcg_error("csm-version is mandatory but not contained in any of the provided model files")
        else:
            self.csm_version = max(csm_versions, key=lambda version: version[0])[1]

        #Parse system
        for inputYaml in modelFiles:
            systemDict = self.parseInputYaml(inputYaml, CgtConstants.SYSTEM_TAG)
            self.parseSystem(systemDict)
        hostnameAmfnodeMap = self.model_context_data.get_hostname_amfnode_map()
        self.buildSystem(hostnameAmfnodeMap, config_base)

        #Parse deployment_profile
        for inputYaml in modelFiles:
            deployment_prof_dict = self.parseInputYaml(inputYaml, CgtConstants.DEPLOYMENT_PROFILE_TAG)
            self.parse_deployment_prof(deployment_prof_dict)

        #parse roles
        for inputYaml in modelFiles:
            rolesDict = self.parseInputYaml(inputYaml, CgtConstants.ROLES_TAG)
            self.parse_roles(rolesDict)
        self.build_roles(config_base)
        self.add_roles_to_system(config_base)

        #parse functions
        functionsDict = []
        for inputYaml in modelFiles:
            functionsDict.extend(self.parseInputYaml(inputYaml, CgtConstants.FUNCTIONS_TAG))
        self.parse_functions(functionsDict)
        self.build_functions(config_base)
        self.replace_uid_with_instance_function()
        self.add_function_to_system()

        #parse services
        serviceDict = []
        serviceSourceFileDict = {}
        for inputYaml in modelFiles:
            serviceDict.extend(self.parseInputYaml(inputYaml, CgtConstants.SERVICES_TAG))
            serviceSourceFileDict.update(self.build_source_file_dict(self.parseInputYaml(inputYaml, CgtConstants.SERVICES_TAG), inputYaml, CgtConstants.SERVICE_UID_TAG))

        sv_ids_to_parse = self.get_services_in_entities(self.roles) + self.get_services_in_entities(self.functions)
        self.parse_services(serviceDict, serviceSourceFileDict, sv_ids_to_parse)
        self.build_services(config_base)

        #parse components
        components_in_system = []
        for s in self.services:
            components_in_system.extend(s.getComponentTypesUid())

        componentDict = []
        componentSourceFileDict = {}
        for inputYaml in modelFiles:
            cts_in_yml = self.parseInputYaml(inputYaml, CgtConstants.COMPONENTS_TAG)
            componentDict.extend(cts_in_yml)
            componentSourceFileDict.update(self.build_source_file_dict(cts_in_yml, inputYaml, CgtConstants.COMPONENT_UID_TAG))
        self._componentDict = componentDict
        self._componentSourceFileDict = componentSourceFileDict
        self.parse_components(componentDict, componentSourceFileDict, components_in_system)
        self.build_components(config_base)

    def finalize_model(self, is_base, online_adapter=None):
        """
        The following function calls have a strict order, any modification has to be inspected
        for possible impacts before applying it.
        """
        self.generateMissingInfoForComponents()
        self.generateMissingInfoForServices()
        self.add_services_to_function()
        self.add_services_to_role()
        self.add_orphan_components(self._componentDict, self._componentSourceFileDict)
        self.filterExternalComponents()
        self.system.setSystemServicesAndComponents()

        '''
        Map roles,services, components to Nodes map of the System
        '''
        self.system.setServicesCompsToNodesMap()

        '''
        Correct reboot info between csm model and software bundle
        '''
        if online_adapter is not None:
            self._updateRebootInfoForSystemComponents(online_adapter, is_base)
        self.validateCSMModel()
        #self.displayCSMUnits()

    def _updateRebootInfoForSystemComponents(self, online_adapter, is_config_base):
        rebootInfoComponentDict = {}
        for component in self.system.getComponents():
            if component.getMetaData().getSoftwares() is not None and len(component.getMetaData().getSoftwares()) > 0:
                installConstraint = component.getInstallationConstraints()
                upgradeConstraint = component.getUpgradeConstraints()
                for software in component.getMetaData().getSoftwares():
                    bundleName = software[CgtConstants.META_BUNDLE_NAME_TAG]
                    bundleFileName = software[CgtConstants.META_FILE_NAME_TAG]
                    if bundleName in rebootInfoComponentDict:
                        if installConstraint.getReboot() and rebootInfoComponentDict[bundleName][CgtConstants.INSTALL_REBOOT_FLAG] is False:
                            rebootInfoComponentDict[bundleName][CgtConstants.INSTALL_REBOOT_FLAG] = True
                        if upgradeConstraint.getReboot() and rebootInfoComponentDict[bundleName][CgtConstants.UPGRDADE_REBOOT_FLAG] is False:
                            rebootInfoComponentDict[bundleName][CgtConstants.UPGRDADE_REBOOT_FLAG] = True
                        rebootInfoComponentDict[bundleName][CgtConstants.COMPONENTS_REBOOT_LIST].append(component)
                    else:
                        installReboot = True if installConstraint.getReboot() else False
                        upgradeReboot = True if  upgradeConstraint.getReboot() else False
                        rebootInfoComponentDict[bundleName] = {CgtConstants.COMPONENTS_BUNDLE_FILE_NAME:bundleFileName,
                                                              CgtConstants.INSTALL_REBOOT_FLAG:installReboot,
                                                              CgtConstants.UPGRDADE_REBOOT_FLAG:upgradeReboot,
                                                              CgtConstants.COMPONENTS_REBOOT_LIST:[component]}

        #we need to check reboot info between csm model and sofware bundle
        # and if there is differnce, we update info following by reboot priority
        for bundleName in rebootInfoComponentDict:
            rebootInfoComponent = rebootInfoComponentDict[bundleName]
            rebootInfo = online_adapter.get_reboot_info(bundleName, rebootInfoComponent[CgtConstants.COMPONENTS_BUNDLE_FILE_NAME])
            if rebootInfo != None:
                realBundleName = rebootInfo[CgtConstants.META_BUNDLE_NAME_TAG]
                needToUpdateRebootInfoIMM = False
                if rebootInfo[CgtConstants.INSTALL_REBOOT_FLAG] and rebootInfoComponent[CgtConstants.INSTALL_REBOOT_FLAG] is False:
                    rebootInfoComponent[CgtConstants.INSTALL_REBOOT_FLAG] = True
                if rebootInfo[CgtConstants.INSTALL_REBOOT_FLAG] is False and rebootInfoComponent[CgtConstants.INSTALL_REBOOT_FLAG]:
                    needToUpdateRebootInfoIMM = True
                    rebootInfo[CgtConstants.INSTALL_REBOOT_FLAG] = True

                if rebootInfoComponent[CgtConstants.UPGRDADE_REBOOT_FLAG] is False:
                    if rebootInfo[CgtConstants.UPGRDADE_REBOOT_FLAG]:
                        rebootInfoComponent[CgtConstants.UPGRDADE_REBOOT_FLAG] = True
                    else:
                        bundleNamePrefix = re.sub("-(.){1,6}$","", realBundleName)
                        rebootInfoUsedBundle = online_adapter.get_reboot_info_of_used_bundle_with_prefix(bundleNamePrefix)
                        if rebootInfoUsedBundle is not None and rebootInfoUsedBundle[CgtConstants.UPGRDADE_REBOOT_FLAG]:
                            rebootInfoComponent[CgtConstants.UPGRDADE_REBOOT_FLAG] = True
                            needToUpdateRebootInfoIMM = True
                            rebootInfo[CgtConstants.UPGRDADE_REBOOT_FLAG] = True

                if rebootInfo[CgtConstants.UPGRDADE_REBOOT_FLAG] is False and rebootInfoComponent[CgtConstants.UPGRDADE_REBOOT_FLAG]:
                    needToUpdateRebootInfoIMM = True
                    rebootInfo[CgtConstants.UPGRDADE_REBOOT_FLAG] = True

                if needToUpdateRebootInfoIMM:
                    online_adapter.set_reboot_info(realBundleName, rebootInfo)

                #Update and sync reboot info of all component with same bundle
                for compCSM in rebootInfoComponent[CgtConstants.COMPONENTS_REBOOT_LIST]:
                    inputYaml = compCSM.get_input_yaml_dict()
                    installConstraint = compCSM.getInstallationConstraints()
                    upgradeConstraint = compCSM.getUpgradeConstraints()
                    if rebootInfoComponent[CgtConstants.INSTALL_REBOOT_FLAG] and not installConstraint.getReboot():
                        logging.info("Component uses a bundle which seems need the reboot when installation.\
                                      Overwrite its installation constraint" + compCSM.getUid())
                        installConstraint.set({'reboot':'yes','scope':'COMPUTE-RESOURCE'})
                        if 'constraints' in inputYaml:
                            inputYaml['constraints']['installation'] = {'reboot':'yes','scope':CgtConstants.SCOPE_COMPUTE_RESOURCE}
                        else:
                            inputYaml['constraints'] = { 'installation':{'reboot':'yes','scope':CgtConstants.SCOPE_COMPUTE_RESOURCE}}
                    if rebootInfoComponent[CgtConstants.UPGRDADE_REBOOT_FLAG] and not upgradeConstraint.getReboot():
                        upgradeConstraint.set({'reboot':'yes','scope':'COMPUTE-RESOURCE'}, compCSM.getUid())
                        logging.info("Component uses a bundle which seems need the reboot when upgrade.\
                                      Overwrite its upgrade constraint" + compCSM.getUid())
                        if 'constraints' in inputYaml:
                            inputYaml['constraints']['upgrade'] = {'reboot':'yes','scope':CgtConstants.SCOPE_COMPUTE_RESOURCE}
                        else:
                            inputYaml['constraints'] = { 'upgrade':{'reboot':'yes','scope':CgtConstants.SCOPE_COMPUTE_RESOURCE}}
            else:
                for compCSM in rebootInfoComponent[CgtConstants.COMPONENTS_REBOOT_LIST]:
                    if compCSM.getAvailabilityManager().upper() != "CDS":
                        if online_adapter.is_running_online():
                            tcg_error("Failed to get reboot info of bundle :  " + bundleName)


    def build_source_file_dict(self, input_dict_list, input_yaml, search_tag):
        '''
        Generate a dictionary with service uid to source yaml file mapping.
        '''
        source_dict = {}
        for entity_dict in input_dict_list:
            uid = getValue(searchTag=search_tag,input_dict_list=[entity_dict])
            source_dict[uid]=input_yaml
        return source_dict

    def displayCSMUnits(self):
        logging.debug("System:")
        logging.debug(" " + self.system.getName())

        logging.debug("System Roles: ")
        for role in self.system.getRoles() :
            logging.debug(" -" + role.getUid())
            logging.debug("   Included services: ")
            for serv in role.getServices() :
                logging.debug("    -" + serv.getUid())

        logging.debug("System Compute Resources: ")
        for computeResource in self.system.getComputeResources() :
            logging.debug(" -" + computeResource.getName())
            logging.debug("  " + computeResource.getRole())

        logging.debug("System Core Functions: ")
        for func in self.system.getFunctions() :
            logging.debug(" -Function: " + func.getUid())
            logging.debug("    Included Services: ")
            for serv in func.getServices() :
                logging.debug("     -Service: " + serv.getUid())
                logging.debug("        Included Components: ")
                for comp in serv.getComponentTypes() :
                    logging.debug("         -Component: " + comp.getUid())

        logging.debug("System Services: ")
        for serv in self.system.getServices() :
            logging.debug("     -" + serv.getUid())
        '''
        logging.debug("---------------------------------------")
        logging.debug("System Functions:"))
        for func in self.system.getFunctions() :
            logging.debug("- "+func.getUid()))

        logging.debug("---------------------------------------")
        logging.debug("System Services:")
        for serv in self.system.getServices() :
            logging.debug("- "+serv.getUid())

        logging.debug("---------------------------------------")
        logging.debug("System Components:")
        for comp in self.system.getComponents() :
            logging.debug("- "+comp.getUid())

        logging.debug("Component to Node Mapping:")
            logging.debug("- "+comp.getUid())

        logging.debug("Component to Node Mapping:"
        for key,value in self.system.getComponentsToComputeResourcesMap().iteritems() :
            logging.debug("- " + key + " : "+ ', '.join(value))
        '''
    def parse_components(self, input_dict_list, uid_yaml_dict, components_to_parse):
        '''
        creates component instances from the input CSM Yaml
        '''
        for component_dict in input_dict_list:
            component_id = getValue(searchTag=CgtConstants.COMPONENT_UID_TAG,
                                    input_dict_list=[component_dict])

            self.validateUid(component_id, component.Component)

            if component_id in components_to_parse:
                component_external = getValue(searchTag=CgtConstants.COMPONENT_EXTERNAL_TAG,
                                     input_dict_list=[component_dict], recursionFlag=True,
                                     defaultValue=CSMConstants.EXTERNAL_DEFAULT)
                component_external = validateAndGetBool(component_external, CgtConstants.COMPONENT_EXTERNAL_TAG)

                component_name = getValue(searchTag=CgtConstants.COMPONENT_NAME_TAG,
                                       input_dict_list=[component_dict])


                component_version = getValue(searchTag=CgtConstants.META_COMPONENT_VERSION_TAG, parentTag=CgtConstants.META_METADATA_TAG,
                                      input_dict_list=[component_dict], recursionFlag=True)

                component_description = getValue(searchTag=CgtConstants.COMPONENT_DESCRIPTION_TAG,
                                      input_dict_list=[component_dict], defaultValue="")

                availability_manager = getValue(searchTag=CgtConstants.COMPONENT_AVAILABILITY_MANAGER_TAG,
                                      input_dict_list=[component_dict], defaultValue=CSMConstants.AVAILABILTY_MANAGER_NONE)

                component_install_prefix = getValue(searchTag=CgtConstants.COMPONENT_INSTALL_PREFIX_TAG,
                                      input_dict_list=[component_dict], recursionFlag=True, defaultValue="/")

                softwares = getValue(
                        searchTag=CgtConstants.COMPONENT_SOFTWARE_TAG,
                        input_dict_list=[component_dict],
                        recursionFlag=False
                        )

                component_instantiate_command = getValue(searchTag=CgtConstants.COMMANDS_START_TAG,
                                      input_dict_list=[component_dict], recursionFlag=True)

                component_cleanup_command = getValue(searchTag=CgtConstants.COMMANDS_STOP_TAG,
                                      input_dict_list=[component_dict], recursionFlag=True)

                component_terminate_command = getValue(searchTag=CgtConstants.COMMANDS_CONCLUDE_TAG,
                                      input_dict_list=[component_dict], recursionFlag=True,
                                      defaultValue=component_cleanup_command)

                component_monitor_command = getValue(searchTag=CgtConstants.COMMANDS_MONITOR_TAG,
                                      input_dict_list=[component_dict], recursionFlag=True)

                component_config_files = getValue(searchTag=CgtConstants.COMPONENT_CONFIGURATIONFILE_TAG,
                                      input_dict_list=[component_dict], defaultValue=[], recursionFlag=True)

                depends_on_components = getValue(searchTag=CgtConstants.COMPONENT_DEPENDS_ON_TAG,
                                      input_dict_list=[component_dict], defaultValue=[])

                health_check_keys = getValue(searchTag=CgtConstants.HEALTHCHECK_KEYS_TAG,
                                      input_dict_list=[component_dict], defaultValue=[], recursionFlag=True,)

                control_policy_type = getValue(searchTag=CgtConstants.COMPONENT_CONTROL_POLICY_TYPE_TAG,
                                    parentTag=CgtConstants.COMPONENT_CONTROL_POLICY_TAG,
                                    input_dict_list=[component_dict], recursionFlag=True,
                                    defaultValue="SIMPLE")

                control_policy_parent = getValue(searchTag=CgtConstants.COMPONENT_CONTROL_POLICY_PARENT_TAG,
                                    parentTag=CgtConstants.COMPONENT_CONTROL_POLICY_TAG,
                                    input_dict_list=[component_dict], recursionFlag=True,
                                    defaultValue=None)

                node_active = getValue(searchTag=CgtConstants.COMPONENT_NODE_ACTIVE_TAG,
                                    input_dict_list=[component_dict], recursionFlag=True, defaultValue="ONE")

                node_standby = getValue(searchTag=CgtConstants.COMPONENT_NODE_STANDBY_TAG,
                                    input_dict_list=[component_dict], recursionFlag=True, defaultValue="NONE")

                node_active_standby = getValue(searchTag=CgtConstants.COMPONENT_NODE_ACTIVE_STANDBY_TAG,
                                    input_dict_list=[component_dict], recursionFlag=True, defaultValue=CSMConstants.NODE_ACTIVE_STANDBY_NO)

                cluster_active = getValue(searchTag=CgtConstants.COMPONENT_CLUSTER_ACTIVE_TAG,
                                    input_dict_list=[component_dict], recursionFlag=True, defaultValue="MANY")

                cluster_standby = getValue(searchTag=CgtConstants.COMPONENT_CLUSTER_STANDBY_TAG,
                                    input_dict_list=[component_dict], recursionFlag=True, defaultValue="NONE")

                start_stop_timeout = getValue(searchTag=CgtConstants.COMPONENT_START_STOP_TIMEOUT_TAG,
                                    input_dict_list=[component_dict], recursionFlag=True, defaultValue="10 s")

                promote_demote_timeout = getValue(searchTag=CgtConstants.COMPONENT_PROMOTE_DEMOTE_TIMEOUT_TAG,
                                    input_dict_list=[component_dict], recursionFlag=True, defaultValue="10 s")


                migrate_timeout = getValue(searchTag=CgtConstants.COMPONENT_MIGRATE_TIMEOUT_TAG,
                                    input_dict_list=[component_dict], recursionFlag=True, defaultValue="60 s")

                recovery_policy = getValue(searchTag=CgtConstants.COMPONENT_RECOVERY_POLICY_TAG,
                                    input_dict_list=[component_dict], recursionFlag=True,
                                     defaultValue=CSMConstants.RECOVERY_POLICY_COMPONENT_RESTART)

                plugin = getValue(searchTag=CgtConstants.COMPONENT_PLUGIN_TAG,
                                    input_dict_list=[component_dict], recursionFlag=True)

                min_nodes = getValue(searchTag=CgtConstants.COMPONENT_SCALING_MIN_NODES_TAG,
                                      input_dict_list=[component_dict], recursionFlag=True)

                max_nodes = getValue(searchTag=CgtConstants.COMPONENT_SCALING_MAX_NODES_TAG,
                                      input_dict_list=[component_dict], recursionFlag=True)

                promotion_attributes = getValue(searchTag=CgtConstants.COMPONENT_PROMOTION_ATTRIBUTES_TAG,
                                            input_dict_list=[component_dict], defaultValue=[], recursionFlag=True)

                environment_attributes = getValue(searchTag=CgtConstants.COMPONENT_ENVIRONMENT_ATTRIBUTES_TAG,
                                             input_dict_list=[component_dict], defaultValue=[], recursionFlag=True)

                installation_constraints = getValue(searchTag=CgtConstants.COMPONENT_INSTALLATION_CONSTRAINTS,
                                               parentTag=CgtConstants.COMPONENT_CONSTRAINTS,
                                               input_dict_list=[component_dict],
                                               defaultValue={},
                                               recursionFlag=False)

                upgrade_constraints = getValue(searchTag=CgtConstants.COMPONENT_UPGRADE_CONTRAINTS,
                                          parentTag=CgtConstants.COMPONENT_CONSTRAINTS,
                                          input_dict_list=[component_dict],
                                          defaultValue={},
                                          recursionFlag=False)

                meta_data = getValue(
                        searchTag=CgtConstants.META_METADATA_TAG,
                        input_dict_list=[component_dict])

                supersedes = getValue(searchTag=CgtConstants.COMPONENT_SUPERSEDES_TAG,
                                                 input_dict_list=[component_dict],
                                                 defaultValue=[], recursionFlag=False)

                component_instance = component.Component()
                component_instance.setValues(
                        name=component_name,
                        componentVersion=component_version,
                        uid=component_id,
                        softwares=softwares,
                        installPrefix=component_install_prefix,
                        description=component_description,
                        instantiateCommand=component_instantiate_command,
                        terminateCommand=component_terminate_command,
                        monitorCommand=component_monitor_command,
                        cleanupCommand=component_cleanup_command,
                        dependsOnComponents=depends_on_components,
                        configurationFiles=component_config_files,
                        healthCheckKeys=health_check_keys,
                        minNodes=min_nodes,
                        maxNodes=max_nodes,
                        availabilityManager=availability_manager,
                        controlPolicyType=control_policy_type,
                        controlPolicyParent=control_policy_parent,
                        nodeActive=node_active,
                        nodeStandby=node_standby,
                        nodeActiveStandby=node_active_standby,
                        clusterActive=cluster_active,
                        clusterStandby=cluster_standby,
                        startStopTimeout=start_stop_timeout,
                        promoteDemoteTimeout=promote_demote_timeout,
                        migrateTimeout=migrate_timeout,
                        recoveryPolicy=recovery_policy,
                        external=component_external,
                        plugin=plugin,
                        installationConstraints=installation_constraints,
                        upgradeConstraints=upgrade_constraints,
                        promotion_attributes=promotion_attributes,
                        environment_attributes=environment_attributes,
                        sourceFile=uid_yaml_dict[component_id],
                        pluginsBaseDir=self.model_context_data.get_plugins_base_dir(),
                        componentsMetaData=meta_data,
                        input_yaml_dict=component_dict,
                        supersedes=supersedes)

                #component_instance.display()
                self.__add_component(component_instance)

    def build_components(self, config_base):
        if config_base is None:
            return
        for r in self.system.getRoles():
            for sv in r.getServices():
                sv = self.service_map[sv]
                for c in sv.getComponentTypesUid():
                    if c not in self.component_map:
                        if c in config_base.component_map:
                            self.__add_component(config_base.component_map[c])
                        else:
                            tcg_error("Component '{}' is used in system '{}' but not defined".format(c, self.system.getUid()))

    def generateMissingInfoForComponents(self):
        for component_type in self.components:
            componentCategoryType = None

            if component_type.getAvailabilityManager().upper() == 'AMF' :
                '''
                Set component category types
                '''
                hasParentFlag = False
                hasChildFlag = False

                if component_type.getControlPolicyParent() :
                    hasParentFlag = True

                for c in self.components :
                    if component_type.getUid() != c.getUid() :
                        if c.getControlPolicyParent() == component_type.getUid() :
                            hasChildFlag = True
                            break

                if hasParentFlag and hasChildFlag:
                    raise ValueError("Component %s is both parent and child, which is illegitimate in CSM." % (component_type.getUid()))

                if component_type.getControlPolicyType().upper() == CSMConstants.COMPONENT_CONTROL_POLICY_SIMPLE :
                    if not hasParentFlag and not hasChildFlag :
                        componentCategoryType = AMFConstants.SA_AMF_COMP_LOCAL
                    elif hasParentFlag :
                        componentCategoryType = AMFConstants.SA_AMF_COMP_LOCAL | AMFConstants.SA_AMF_COMP_PROXIED_NPI
                    else:  # hasChildFlag
                        raise ValueError("Component %s is SIMPLE control policy type but have child, which is illegitimate in CSM." % (component_type.getUid()))

                elif component_type.getControlPolicyType().upper() == CSMConstants.COMPONENT_CONTROL_POLICY_ADVANCED :
                    if not hasParentFlag and not hasChildFlag :
                        componentCategoryType = AMFConstants.SA_AMF_COMP_SA_AWARE
                    elif hasParentFlag :
                        componentCategoryType = AMFConstants.SA_AMF_COMP_PROXIED
                    else:
                        '''
                        When component has child, use SA_AWARE to replace PROXY for
                        OpenSAF do not support SA_AWARE category.
                        componentCategoryType = AMFConstants.SA_AMF_COMP_PROXY
                        '''
                        componentCategoryType = AMFConstants.SA_AMF_COMP_SA_AWARE

            """
            If component Availability Manager is 'NONE' or 'CDS':
            Let componentCategoryType be None
            """

            component_type.setType(componentCategoryType)

    def get_services_in_entities(self, entities):
        '''
        Calls getServices on objects in entities list.
        Requires that the object has getServices method.
        '''
        services = set()
        for instance in entities:
            services.update(instance.getServices())
        return list(services)

    def parse_services(self, input_dict_list, uid_yaml_dict, services_to_parse):
        for service_dict in input_dict_list:
            service_uid = getValue(searchTag=CgtConstants.SERVICE_UID_TAG,
                                   input_dict_list=[service_dict])
            self.validateUid(service_uid, service.Service)

            already_parsed_uid = [v.getUid() for v in self.services]
            if (service_uid in services_to_parse and service_uid not in already_parsed_uid):
                service_name = getValue(searchTag=CgtConstants.SERVICE_NAME_TAG,
                                       input_dict_list=[service_dict])

                service_version = getValue(searchTag=CgtConstants.META_SERVICE_VERSION_TAG,
                                           parentTag=CgtConstants.SERVICE_METADATA_TAG,
                                           input_dict_list=[service_dict], recursionFlag=True)

                service_description = getValue(searchTag=CgtConstants.SERVICE_DESCRIPTION_TAG,
                                              input_dict_list=[service_dict], defaultValue="")

                components = getValue(searchTag=CgtConstants.SERVICE_COMPONENTS_TAG,
                                              input_dict_list=[service_dict], defaultValue=[])

                services = getValue(searchTag=CgtConstants.SERVICE_SERVICES_TAG,
                                              input_dict_list=[service_dict], defaultValue=[])

                plugin = getValue(searchTag=CgtConstants.SERVICE_PLUGIN_TAG,
                                            input_dict_list=[service_dict], recursionFlag=True)

                redundancy_model = getValue(searchTag=CgtConstants.SERVICE_REDUNDANCY_TAG,
                                              input_dict_list=[service_dict], recursionFlag=True,
                                              defaultValue=None)

                max_promotions = getValue(searchTag=CgtConstants.SERVICE_MAX_PROMOTIONS_TAG,
                                              input_dict_list=[service_dict], recursionFlag=True,
                                              defaultValue=None)

                monitor_period = getValue(searchTag=CgtConstants.SERVICE_MONITOR_PERIOD_TAG,
                                              input_dict_list=[service_dict], recursionFlag=True,
                                              defaultValue="2000 ms")

                max_failure_nr = getValue(searchTag=CgtConstants.SERVICE_MAX_FAILURE_NR_TAG,
                                              input_dict_list=[service_dict], defaultValue=2, recursionFlag=True)

                depends_on_services = getValue(searchTag=CgtConstants.SERVICE_PROMOTION_DEPENDENCY_TAG,
                                              input_dict_list=[service_dict], recursionFlag=True, defaultValue=[])

                for dep in depends_on_services:
                    dep[CgtConstants.SERVICE_DEPENDS_ON_TAG] = dep[CgtConstants.SERVICE_DEPENDS_ON_TAG]

                meta_data = getValue(
                                searchTag=CgtConstants.META_METADATA_TAG,
                                input_dict_list=[service_dict])

                service_instance = service.Service()
                service_instance.setValues(name=service_name,
                                          version=service_version,
                                          description=service_description,
                                          uid=service_uid,
                                          dependsOnServices=depends_on_services,
                                          plugin=plugin,
                                          components=components,
                                          services=services,
                                          monitorPeriod=monitor_period,
                                          maxFailureNr=max_failure_nr,
                                          redundancyModel=redundancy_model,
                                          maxPromotions=max_promotions,
                                          serviceVersion=service_version,
                                          servicesMetaData=meta_data,
                                          sourceFile=uid_yaml_dict[service_uid],
                                          pluginsBaseDir=self.model_context_data.get_plugins_base_dir(),
                                          input_yaml_dict=service_dict)

                #service_instance.display()

                self.__add_service(service_instance)
                service_in_service = service_instance.getServices()
                if service_in_service:
                    self.parse_services(input_dict_list, uid_yaml_dict, service_in_service)

    def build_services(self, config_base):
        for r in self.system.getRoles():
            q = r.getServices()[:]
            while len(q) > 0:
                sv = q.pop(0)
                if sv not in self.service_map:
                    if config_base is not None and sv in config_base.service_map:
                        self.__add_service(copy.deepcopy(config_base.service_map[sv]))
                    else:
                        tcg_error("Service '{}' is used in role '{}' but not defined".format(sv, r.getUid()))
                q.extend(self.service_map[sv].getServices())

        ss = set(s.getUid() for s in self.services)
        for f in self.functions:
            for s_f in f.getServices():
                # Error if service is not defined but ignore if it is external because we didn't include external services
                if s_f not in ss and (config_base is None or s_f not in config_base.service_map):
                    tcg_error("Service '{}' is refered to in function '{}' but not defined".format(s_f, f.getUid()))

    def build_functions(self, config_base):
        if config_base is None:
            return
        q = self.system.getFunctions()[:]
        while len(q) > 0:
            f = q.pop(0)
            if f not in self.function_map:
                if f in config_base.function_map:
                    self.__add_function(config_base.function_map[f])
                else:
                    tcg_error("Function '{}' is used in system '{}' but not defined".format(f, self.system.getUid()))
            q.extend(self.function_map[f].getFunctions())

    def _check_if_all_entities_were_parsed(self,
                                           ids_to_check,
                                           parsed_entities,
                                           the_type):
        parsed_entities_ids = [e.getUid() for e in parsed_entities]
        for id in ids_to_check:
            if (id not in parsed_entities_ids):
                # uops here we need to abort the campaign generation
                tcg_error("The entity with type: {0} and uid: {1} was not found"
                          " in the system model.".format(the_type, id))
        # if the loop ended gracefully, the validation was successful

    def generateMissingInfoForServices(self):
        '''
        Checking if included components exists
        '''
        for serviceInst in self.services :

            componentRedundancyModels = []

            # Question: Should amfManagedComponents and nonAmfManagedComponents be list or set
            amfManagedComponents = []
            nonAmfManagedComponents = []

            # convert Raw component instance information to data struct.
            serviceInst.convertComponentsRawData(self.components)
            for compType in serviceInst.getComponentTypes():
                if compType.getAvailabilityManager().upper() == 'AMF':
                    amfManagedComponents.append(compType)
                    if compType.getComponentRedundancyModel():
                        componentRedundancyModels.append(compType.getComponentRedundancyModel())
                else:
                    nonAmfManagedComponents.append(compType)

            serviceInst.setAmfManagedComponents(amfManagedComponents)
            serviceInst.setNonAmfManagedComponents(nonAmfManagedComponents)

            #Set service getSaAmfSutDefSUFailover
            saAmfSutDefSUFailover = "SA_FALSE"
            for comp in serviceInst.getComponentTypes():
                if comp.getDisableRestart() == "SA_TRUE":
                    saAmfSutDefSUFailover = "SA_TRUE"

            serviceInst.setSaAmfSutDefSUFailover(saAmfSutDefSUFailover)

            serviceInstances = []
            for service in serviceInst.getServices() :
                servicePresentFlag = False
                for serviceInstance in self.services :
                    if serviceInstance.getUid() == service :
                        servicePresentFlag = True
                        serviceInstances.append(serviceInstance)
                if not servicePresentFlag :
                    tcg_error('No such service %s' % service)
            serviceInst.setServices(serviceInstances)

            '''
            Fetch the redundancy model if not specified in CSM Yaml Model
            '''
            redundancyModel = serviceInst.getRedundancyModel()

            if not redundancyModel :
                redundancyModel = CSMConstants.getServiceRedundancyModel(componentRedundancyModels, serviceInst.getUid())
                serviceInst.setRedundancyModel(redundancyModel)

            service_roles = []
            for role in self.roles:
                if serviceInst.getUid() in role.getServices():
                    service_roles.append(role)

            serviceInst.set_roles(service_roles)

    def add_services_to_function(self):
        '''
        Add service objects to function.
        '''
        for func_inst in self.functions:
            if len(func_inst.getServices()) == 0 or isinstance(func_inst.getServices()[0], service.Service):
                continue
            service_inst_in_function = [v for v in self.services if v.getUid() in func_inst.getServices()]
            core_services = set()
            for service_inst in service_inst_in_function:
                for elem in CSMTools.getCoreServices(service_inst):
                    core_services.add(elem)
            func_inst.setServiceInstances(core_services)

    def add_services_to_role(self):
        '''
        Only the services specified in the role's services list are considered:
        - The services that are not part of any functions (globally)
          will NOT be assigned to the role.
        - The services defined in the system functions will be assigned
          to the role.
        In both cases the the container relation is resolved and only core
        services are allocated.
        '''
        for role_inst in self.role_map.values():
            service_inst_in_role = [v for v in self.services if v.getUid() in role_inst.getServices()]
            core_services = set()
            local_core_services = set()

            for service_inst in service_inst_in_role:
                sv_to_update = CSMTools.getCoreServices(service_inst)
                core_services.update(sv_to_update)
                if service_inst.getUid() in role_inst.getLocalServices():
                    local_core_services.update(sv.getUid() for sv in sv_to_update)

            assigned_services = set()
            local_assigned_services = set()
            # add in services defined in system functions
            for func in self.system.getFunctions():
                for func_serv in func.getServices():
                    for service_inst in core_services:
                        if func_serv.getUid() == service_inst.getUid():
                            assigned_services.add(service_inst)
                            if service_inst.getUid() in local_core_services:
                                local_assigned_services.add(service_inst)
                            break

            role_inst.setServiceInstances(assigned_services, local_assigned_services)

    def add_orphan_components(self, component_dict, component_source_file_dict):
        '''
        Check component dependencies in role, if component is missing (orphan)
        create dummy service and add it to role.
        '''
        for role_inst in self.roles:
            component_instances = []
            for service_inst in role_inst.getServices():
                component_instances.extend(list(service_inst.getComponentTypes()))

            component_dependencies_uids = {}
            for component_instance in component_instances:
                for dep_on_comp_uid in component_instance.getDependsOnComponents():
                    if dep_on_comp_uid not in component_dependencies_uids.keys():
                        component_dependencies_uids[dep_on_comp_uid] = []
                    component_dependencies_uids[dep_on_comp_uid].append(component_instance.getUid())

            component_uids_in_role = [ c.getUid() for c in component_instances]
            orphan_components_uids = list(set(component_dependencies_uids.keys())-set(component_uids_in_role))

            if orphan_components_uids:
                orphan_components_instances = []
                self.parse_components(component_dict, component_source_file_dict, orphan_components_uids)
                for orphan_comp_uid in orphan_components_uids:
                    orphan_comp = self.getComponent(orphan_comp_uid)
                    if orphan_comp is None:
                        tcg_error("Could not find component {0} referenced in the following components dependencies: "
                                  "{1}.".format(orphan_comp_uid, component_dependencies_uids[orphan_comp_uid]))
                    if orphan_comp.getExternal():
                        tcg_error("Components %s depend on external component '%s' and they are not all allocated in the same role. "\
                                  "Dependent components must be allocated together or the dependency must be removed from the model." %
                                  (component_dependencies_uids[orphan_comp_uid], orphan_comp_uid))
                    if orphan_comp.getAvailabilityManager().upper() != CSMConstants.AVAILABILTY_MANAGER_NONE:
                        # orphan components must have no defined Availability Manager
                        tcg_error("Component '%s' with availability manager '%s' is an orphan (not allocated to a service) but is depended upon by component(s) %s."\
                            " Only components with no defined availability manager can be an orphan." % \
                            (orphan_comp_uid,orphan_comp.getAvailabilityManager(),component_dependencies_uids[orphan_comp_uid]))
                    orphan_components_instances.append(
                        {
                            CgtConstants.SERVICE_COMPONENT_INSTANCES_OF_TAG: orphan_comp_uid,
                            CgtConstants.SERVICE_COMPONENT_NAME_TAG: 'dummy_{uid}'.format(uid=orphan_comp_uid)
                        })
                dummy_service = service.Service()
                service_name = 'orphan-comp-service'
                service_description = 'service containing orphan components in role'
                service_uid = 'orphan.comp.service'
                #egercso FIXME: add the roles version instead of hardcoded value
                service_version = role_inst.getVersion()
                service_input_yaml = {CgtConstants.SERVICE_NAME_TAG: service_name,
                        CgtConstants.SERVICE_DESCRIPTION_TAG: service_description,
                        CgtConstants.SERVICE_COMPONENTS_TAG: orphan_components_instances,
                        CgtConstants.SERVICE_UID_TAG: service_uid,
                        CgtConstants.META_METADATA_TAG: {CgtConstants.META_SERVICE_VERSION_TAG: service_version}}
                dummy_service.setValues(name=service_name,
                                          description=service_description,
                                          uid=service_uid,
                                          components=orphan_components_instances,
                                          input_yaml_dict=service_input_yaml,
                                          version=service_version)
                dummy_service.convertComponentsRawData(self.components)
                services_in_role = role_inst.getServices()
                services_in_role.append(dummy_service)
                role_inst.setServices(services_in_role)

    def parse_functions(self, input_dict_list, functions_to_parse=None):
        '''
        Create function instances from CSM Yaml
        '''
        for function_dict in input_dict_list:
            uid = getValue(searchTag=CgtConstants.FUNCTION_UID_TAG,
                           input_dict_list=[function_dict])
            self.validateUid(uid, function.Function)
            if functions_to_parse is None or uid in functions_to_parse:

                name = getValue(searchTag=CgtConstants.FUNCTION_NAME_TAG,
                    input_dict_list=[function_dict])

                version = getValue(searchTag=CgtConstants.FUNCTION_VERSION_TAG,
                                      input_dict_list=[function_dict])

                description = getValue(searchTag=CgtConstants.FUNCTION_DESCRIPTION_TAG,
                                      input_dict_list=[function_dict], defaultValue="")

                services = getValue(searchTag=CgtConstants.FUNCTION_SERVICES_TAG,
                                      input_dict_list=[function_dict], defaultValue=[])

                functions = getValue(searchTag=CgtConstants.FUNCTION_FUNCTIONS_TAG,
                                      input_dict_list=[function_dict], defaultValue=[])

                meta_data = getValue(
                                    searchTag=CgtConstants.META_METADATA_TAG,
                                    input_dict_list=[function_dict])

                # functionInstance.display()
                function_instance = function.Function()
                function_instance.setValues(
                                            name=name,
                                            uid=uid,
                                            description=description,
                                            version=version,
                                            services=services,
                                            functions=functions,
                                            functionsMetaData=meta_data,
                                            input_yaml_dict=function_dict)

                self.__add_function(function_instance)
                function_in_function = function_instance.getFunctions()
                if function_in_function:
                    self.parse_functions(input_dict_list, function_in_function)

        if functions_to_parse is not None:
            self._check_if_all_entities_were_parsed(functions_to_parse,
                                                    self.functions,
                                                    function.Function.__name__)

    def replace_uid_with_instance_function(self):
        '''
        Replace the uid in function list in function with instances.
        '''
        for function_instance in self.functions:
            function_instance_list = []
            for functions_in_function in function_instance.getFunctions():
                for match_instance in self.functions:
                    if match_instance.getUid() == functions_in_function:
                        function_instance_list.append(match_instance)
            function_instance.setFunctions(function_instance_list)

    def add_function_to_system(self):
        '''
        Add function instances to system
        '''
        for st in self.system_map.values():
            core_functions = {}
            local_core_functions = {}
            for f in self.functions:
                if f.getUid() in st.getFunctions():
                    for elem in CSMTools.getCoreFunctions(f):
                        core_functions[elem.getUid()] = elem
                if f.getUid() in st.getLocalFunctions():
                    for elem in CSMTools.getCoreFunctions(f):
                        local_core_functions[elem.getUid()] = elem
            st.setFunctionInstances(core_functions.values(), local_core_functions.values())

    def parse_roles(self, input_dict_list):
        '''
        Create role instances for roles included in the system.
        '''
        for role_dict in input_dict_list:
            role_instance = role.Role()
            role_instance.raw_uid = getValue(searchTag=CgtConstants.ROLE_UID_TAG,
                                    input_dict_list=[role_dict])
            self.validateUid(role_instance.raw_uid, role.Role)
            if role_instance.raw_uid in self.system.getRoles():
                role_instance.raw_name = getValue(searchTag=CgtConstants.ROLE_NAME_TAG,input_dict_list=[role_dict])

                role_instance.raw_version = getValue(searchTag=CgtConstants.META_ROLE_VERSION_TAG,
                                            parentTag=CgtConstants.META_METADATA_TAG,
                                            input_dict_list=[role_dict], recursionFlag=True)

                role_instance.raw_description = getValue(searchTag=CgtConstants.ROLE_DESCRIPTION_TAG,
                                                input_dict_list=[role_dict], defaultValue="")
                role_instance.raw_services = getValue(searchTag=CgtConstants.ROLE_SERVICES_TAG,
                                             input_dict_list=[role_dict], defaultValue=[])
                role_instance.raw_minNodes = getValue(searchTag=CgtConstants.ROLE_MINNODES_TAG,
                                             input_dict_list=[role_dict],
                                             recursionFlag=True, defaultValue=[])
                role_instance.raw_canScale = getValue(searchTag=CgtConstants.ROLE_SCALING_TAG,
                                             input_dict_list=[role_dict],
                                             recursionFlag=True, defaultValue='NO')
                role_instance.raw_canScale = validateAndGetBool(role_instance.raw_canScale, CgtConstants.ROLE_SCALING_TAG)

                role_instance.raw_weight = getValue(searchTag=CgtConstants.ROLE_WEIGHT_TAG,
                                           recursionFlag=True,
                                           input_dict_list=[role_dict], defaultValue=0)

                role_instance.raw_rank = getValue(searchTag=CgtConstants.ROLE_RANK_TAG,
                                         recursionFlag=True,
                                         input_dict_list=[role_dict], defaultValue=0)

                role_instance.raw_external = getValue(searchTag=CgtConstants.ROLE_EXTERNAL_TAG,
                                             recursionFlag=True,
                                             input_dict_list=[role_dict], defaultValue='NO')
                role_instance.raw_external = validateAndGetBool(role_instance.raw_external, CgtConstants.ROLE_EXTERNAL_TAG)

                role_instance.raw_meta_data = getValue(
                    searchTag=CgtConstants.META_METADATA_TAG,
                    input_dict_list=[role_dict])

                role_instance.raw_role_constraints = getValue(searchTag=CgtConstants.ROLE_CONSTRAINTS_TAG,
                                                     input_dict_list=[role_dict])
                role_instance.set_input_yaml(role_dict)
                if role_instance.raw_uid in self.role_map:
                    tcg_error("Multiple definitions of role: {}".format(role_instance.raw_uid))
                self.role_map[role_instance.raw_uid] = role_instance

    def build_roles(self, config_base):
        for role in self.system.getRoles():
            if role not in self.role_map:
                if config_base is not None:
                    self.role_map[role] = config_base.role_map[role].clone_raw()
                else:
                    tcg_error("Role definition not found: '{}'".format(role))

        q = self.role_map.values()
        # pull in extended roles from config base if needed
        while len(q):
            r = q.pop(0)
            extends_from_role = self.get_extend_info(r.raw_role_constraints)
            if extends_from_role is not None and extends_from_role not in self.role_map:
                if config_base is not None and extends_from_role in config_base.role_map:
                    pull_in_role = config_base.role_map[extends_from_role].clone_raw()
                    self.role_map[extends_from_role] = pull_in_role
                    q.append(pull_in_role)
                else:
                    tcg_error("Extended role not found '{}'".format(extends_from_role))
            if extends_from_role is not None:
                if r.getExtendsFrom() is not None and r.getExtendsFrom().getUid() != extends_from_role:
                    tcg_error("Multiple extensions (nonlinear extension hierarchy tree) of role '{}' found".format(extends_from_role))
                r.setExtendsFrom(self.role_map[extends_from_role])
                self.role_map[extends_from_role].setExtendedBy(r)

        # only add root roles (that do not extend from any role)
        for role_instance in self.role_map.values():
            services = CSMModel.acc_roles(role_instance)
            services = list(set(services))
            role_instance.setValues(
                name=role_instance.raw_name,
                uid=role_instance.raw_uid,
                description=role_instance.raw_description,
                services=services,
                localServices=role_instance.raw_services,
                canScale=role_instance.raw_canScale,
                weight=role_instance.raw_weight,
                rank=role_instance.raw_rank,
                minNodes=role_instance.raw_minNodes,
                external=role_instance.raw_external,
                version=role_instance.raw_version,
                roleConstraints=role_instance.raw_role_constraints,
                rolesMetaData=role_instance.raw_meta_data)
            if role_instance.getExtendsFrom() is None:
                self.roles.append(role_instance)
        self.system.processRoles(self.role_map)

    def add_roles_to_system(self, config_base):
        '''
        Add role instances to system
        '''

        system_roles = [role for role in self.roles if role.getExtendsFrom() is None]
        self.system.updateRoleInstance(system_roles)

        all_crs = set()
        for r in self.system.getRoles():
            crs = self.system.roleToNodeMap[r.getUid()]
            if not all_crs.isdisjoint(crs):
                computer_str = ','.join(all_crs.intersection(crs))
                tcg_error("Duplicate computer resource %s" % computer_str)
            else:
                all_crs.update(crs)

    @staticmethod
    def get_extend_info(inputDict):
        if inputDict is not None and CgtConstants.SYSTEM_CONSTRAINTS_EXTEND_TAG in inputDict:
            return inputDict[CgtConstants.SYSTEM_CONSTRAINTS_EXTEND_TAG]
        return None

    @staticmethod
    def acc_roles(role):
        extended_by = role.getExtendedBy()
        if extended_by is None:
            return role.raw_services
        else:
            return role.raw_services + CSMModel.acc_roles(extended_by)

    @staticmethod
    def acc_systems(system_uid, system_map):
        the_system = system_map[system_uid]
        if the_system.isAccumulated():
            return the_system.getRoleAllocations(), the_system.getFunctions()
        else:
            extended_system_uid = CSMModel.get_extend_info(the_system.raw_system_constraints)
            if extended_system_uid is None:
                return the_system.raw_roles, the_system.raw_functions
            else:
                roles, functions = CSMModel.acc_systems(extended_system_uid, system_map)
                return roles + the_system.raw_roles, functions + the_system.raw_functions

    def parseSystem(self, inputDictList):
        '''
        creates system instance from the input CSM Yaml
        '''

        for systemDict in inputDictList:
            systemInstance = system.System()
            systemInstance.raw_uid = getValue(searchTag=CgtConstants.SYSTEM_UID_TAG,
                                      input_dict_list=[systemDict])
            if systemInstance.raw_uid in self.system_map:
                tcg_error("System is already defined: {}".format(systemInstance.raw_uid))
            self.validateUid(systemInstance.raw_uid, system.System)
            systemInstance.raw_name = getValue(searchTag=CgtConstants.SYSTEM_NAME_TAG,
                                      input_dict_list=[systemDict])
            systemInstance.raw_version = getValue(searchTag=CgtConstants.SYSTEM_VERSION_TAG,
                                      input_dict_list=[systemDict])
            systemInstance.raw_product_number = getValue(searchTag=CgtConstants.SYSTEM_PRODUCT_NUMBER_TAG,
                                      input_dict_list=[systemDict])
            systemInstance.raw_description = getValue(searchTag=CgtConstants.SYSTEM_DESCRIPTION_TAG,
                                      input_dict_list=[systemDict], defaultValue="")
            systemInstance.raw_functions = getValue(searchTag=CgtConstants.SYSTEM_FUNCTIONS_TAG,
                                      input_dict_list=[systemDict], defaultValue=[])
            systemInstance.raw_roles = getValue(searchTag=CgtConstants.SYSTEM_ROLES_TAG,
                                      input_dict_list=[systemDict], defaultValue=[])
            systemInstance.raw_system_constraints = getValue(searchTag=CgtConstants.SYSTEM_CONSTRAINTS_TAG,
                                          input_dict_list=[systemDict], defaultValue={})
            systemInstance.raw_meta_data = getValue(
                searchTag=CgtConstants.META_METADATA_TAG,
                input_dict_list=[systemDict])

            systemInstance.set_input_yaml(systemDict)
            # systemInstance.display()

            self.system_map[systemInstance.raw_uid] = systemInstance
            if self.original_system is None:
                self.original_system = systemInstance

    def buildSystem(self, hostnameAmfnodeMap, config_base):
        # replicate ALL systems in the base that do not exist in the target
        if config_base is not None:
            for base_system_uid, base_system in config_base.system_map.items():
                if base_system_uid not in self.system_map:
                    self.system_map[base_system_uid] = base_system.clone_raw()

        # build reverse extend (i.e. extended) and do some validations
        extended_map = {}  # 'key' is extended by 'value'
        for system_uid, the_system in self.system_map.items():
            extended_system = self.get_extend_info(the_system.raw_system_constraints)
            if extended_system is None:
                continue
            if extended_system not in self.system_map:
                tcg_error("Extended system not found: '{}'".format(extended_system))
            if extended_system in extended_map:
                tcg_error("Multiple extensions (nonlinear extension hierarchy tree) of system '{}' found".format(extended_system))

            extended_map[extended_system] = system_uid

        # accumulate all functions and roles of the extended systems
        for system_uid, the_system in self.system_map.items():
            if system_uid not in extended_map:
                if self.system is None:
                    self.system = the_system
                else:
                    tcg_error("More than ONE base system found")

            roles, functions = CSMModel.acc_systems(system_uid, self.system_map)
            the_system.setValues(
                hostnameAmfnodeMap,
                uid=the_system.raw_uid,
                name=the_system.raw_name,
                version=the_system.raw_version,
                product_number=the_system.raw_product_number,
                description=the_system.raw_description,
                functions=functions,
                localFunctions=the_system.raw_functions,
                roles=roles,
                system_constraints=the_system.raw_system_constraints,
                systemMetaData=the_system.raw_meta_data)
            the_system.setAccumulated(True)

        if self.system is None:
            tcg_error("No genesis system found, empty CSM model or cyclic dependencies detected")

    def parse_deployment_prof(self, inputDictList):
        '''
        creates deployment profile instance from the input CSM Yaml
        '''
        for deployment_prof_dict in inputDictList :
            instance_of = getValue(searchTag=CgtConstants.DEPLOYMENT_PROFILE_INSTANCE_OF_TAG,
                                      input_dict_list=[deployment_prof_dict])

            deployment_prof_instance = deployment_profile.DeploymentProfile()
            deployment_prof_instance.setValues(
                instance_of=instance_of,
                input_yaml_dict=deployment_prof_dict)

            if not self.deployment_profile :
                self.deployment_profile = deployment_prof_instance
            else :
                tcg_error("There can only be one deployment profile defined")

    def validateCSMModel(self):
        '''
        Check if the model has all the required information like roles
        '''
        self.system.validate()
        if not self.roles :
            tcg_error("No roles defined in the System model")
        '''
        for component in self.components :
            component.validate()
        '''
    def write_csm_config_base(self,target_config_base_path):
        '''
        Write configbase to file. Copy components' plugins and configuration files.
        '''
        base_config_path = os.path.join(
                            target_config_base_path,
                            CgtConstants.CDFCGT_CONFIG_BASE_CSM_PART)
        Utils.mkdir_safe(base_config_path)
        csm_base_file = os.path.join(base_config_path, CgtConstants.CDFCGT_CONFIG_BASE_CSM_MODEL_FILENAME)
        csm_model_dict = {}

        # We can assume that self.csm_version is defined because this method
        # is called only for the target model and not the config-base
        # where the csm-version is kept optional.
        csm_model_dict[CgtConstants.CSM_VERSION_TAG] = self.csm_version

        comp_dict_list = [c.get_input_yaml_dict() for c in self.system.getComponents()]
        comp_dict_list.extend([c.get_input_yaml_dict() for c in self.external_system_components])
        csm_model_dict[CgtConstants.COMPONENTS_TAG] = comp_dict_list

        service_dict_list = [s.get_input_yaml_dict() for s in self.system.getServices()]
        service_dict_list.extend([s.get_input_yaml_dict() for s in self.external_system_services])
        csm_model_dict[CgtConstants.SERVICES_TAG] = service_dict_list

        role_dict_list = []
        for role in self.system.getRoles():
            while role is not None:
                role_dict_list.append(role.get_input_yaml_dict())
                role = role.getExtendedBy()
        csm_model_dict[CgtConstants.ROLES_TAG] = role_dict_list

        func_dict_list = []
        for func in self.system.getFunctions():
            func_dict_list.append(func.get_input_yaml_dict())
        if func_dict_list:
            csm_model_dict[CgtConstants.FUNCTIONS_TAG] = func_dict_list

        system_dict_list = []
        my_system = self.system
        while my_system is not None:
            system_dict_list.append(my_system.get_input_yaml_dict())
            my_system = dict.get(self.system_map, my_system.getSystemConstraints().getExtendedSystem(), None)
        csm_model_dict[CgtConstants.SYSTEM_TAG] = system_dict_list
        YamlParser.getInstance().dump_yaml_dict_to_file(csm_model_dict, csm_base_file)

        # copy components' plugins and configuration files
        for comp in self.system.getComponents():
            if comp.getPlugin() is not None:
                src = os.path.join(comp.getPluginsBaseDir(), comp.getPlugin())
                if os.path.exists(src):
                    dest = os.path.join(base_config_path, comp.getPlugin())
                    try:
                        shutil.copytree(src, dest, symlinks=True, ignore=shutil.ignore_patterns('*.pyc'))
                    except shutil.Error as err:
                        tcg_error("Error while copying plugin directory for component {0}: {1}".format(comp.getUid(),
                                                                                                       err))
                else:
                    tcg_error("Could not find plugins dir for component {}".format(comp.getName()))

            for configFile in comp.getConfigurationFiles():
                # tcg ignores "OTHER" type
                if configFile.get_data_type() == CSMConstants.CONFIGURATION_DATA_TYPE_OTHER:
                    continue
                src = os.path.join(comp.getSourceFileLocation(), configFile.get_name())
                if os.path.exists(src):
                    dest = os.path.join(base_config_path, configFile.get_name())
                    try:
                        dest_dir = os.path.dirname(dest)
                        if not os.path.exists(dest_dir):
                            os.makedirs(dest_dir)
                        shutil.copy2(src, dest)
                    except OSError as err:
                        logging.warn("Error while copying configuration file for component {0}: {1}".format(
                            comp.getUid(), err))
                else:
                    logging.warn("Could not find configuration file {0} for component {1}".format(configFile.get_name(),
                                                                                               comp.getName()))

    def write_domain_mapping_file(self, domains_mapping_file, online_adapter=None):
        '''
        Write domain mapping to file.
        '''
        xml_doc = xml.dom.minidom.Document()
        xml_root = xml_doc.createElement("systems")

        my_system = self.system
        while my_system is not None:
            xml_system = xml_doc.createElement("system")
            xml_root.appendChild(xml_system)
            xml_system.setAttribute("name", my_system.getName())
            xml_system.setAttribute("productNumber", my_system.getProductNumber())
            xml_system.setAttribute("version", my_system.getVersion())
            xml_system.setAttribute("description", my_system.getDescription())
            sws = set()
            system_local_services = set()
            for e in my_system.raw_roles:
                r = self.role_map[e['role']]
                system_local_services |= set(r.getLocalAssignedServices())
            for sv in system_local_services:
                for core_sv in CSMTools.getCoreServices(self.service_map[sv]):
                    comps = core_sv.getComponentTypes() | core_sv.getExternalComponentTypes()
                    for c in comps:
                        for filename, bundle in c.getMetaData().softwares():
                            if c.get_software_type() == CgtConstants.COMPONENT_SOFTWARE_RPM_TAG:
                                if not (bundle.startswith(AMFTools.getProvider() + "-") or bundle.startswith("3PP-")) and online_adapter is not None:
                                    bundle = online_adapter.get_rpm_name(bundle, filename)
                            sws.update([bundle])
            for sw in sws:
                xml_software = xml_doc.createElement("software")
                xml_system.appendChild(xml_software)
                xml_software.setAttribute("bundle", sw)
            my_system = dict.get(self.system_map, my_system.getSystemConstraints().getExtendedSystem(), None)

        xml_contents = xml_root.toprettyxml()
        with open(domains_mapping_file, 'w') as xml_file:
            xml_file.write(xml_contents)

    def getFunction(self, function):
        for func in self.functions :
            if func.getUid() == function :
                return func
        return None

    def getComponent(self, compId):
        for comp in self.components:
            if comp.getUid() == compId:
                return comp
        # not a native component, maybe it is external
        for comp in self.external_system_components:
            if comp.getUid() == compId:
                return comp
        # not found (not native nor external)
        return None

    def getService(self, svId):
        for serv in self.services :
            if serv.getUid() == svId:
                return serv
        return None

    def getRole(self, roleId):
        for role in self.roles :
            if role.getUid() == roleId:
                return role
        return None

    def getSystem(self):
        return self.system

    def getNonManagedComps(self):
        # returns a list of non-amf (componentId, version) tuples
        nonManagedComps = []
        for comp in self.components :
            if comp.getAvailabilityManager().upper() == "NONE":
                nonManagedComps.append((comp.getUid(), comp.getName(), comp.getVersion()))
        return nonManagedComps

    def getNonAmfComps(self):
        # returns a list of non-amf (componentId, version) tuples
        nonAmfComps = []
        for comp in self.components :
            if comp.getAvailabilityManager().upper() != "AMF":
                nonAmfComps.append((comp.getUid(), comp.getName(), comp.getVersion()))
        return nonAmfComps

    def filterExternalComponents(self):
        """
        - Function for filtering the model from bottom to top
          based on model-compiler information.
        - We assume that generateMissingInfoForRoles() was
          already called and we don't have any service containing
          services.
        - The same goes for functions with generateMissingInfoForSystem().
        - Must follow the first call for setSystemServicesAndComponents()
        """
        self.external_system_components = []

        for comp in self.components:
            if comp.getExternal():
                self.external_system_components.append(comp)

        for comp in self.external_system_components:
            self.components.remove(comp)

        self.external_system_services = []
        container_services = []  # Container services should be remove from config_base
        for serv in self.services:
            if serv.is_container():
                container_services.append(serv)
            elif serv.filterExternalComponents(self.external_system_components):
                self.external_system_services.append(serv)

        for filtered_service in container_services:
            self.services.remove(filtered_service)
        for filtered_service in self.external_system_services:
            self.services.remove(filtered_service)

        """
        Empty functions don't have to be removed. If it is empty it
        means we don't have to install anything which is a strange
        thing to do, but it is what is specified.
        """
        for func in self.functions:
            func.filterExternalServices(self.external_system_services)

        """
        Same goes for roles.
        """
        for r in self.roles:
            r.filterExternalServices(self.external_system_services)

    def getExternalSDPs(self):
        SDPNames = []
        for CT in self.external_system_components:
            for sw, bundle in CT.software_bundle_names():
                SDPNames.append((CT.getUid(), sw, bundle))
        return SDPNames

    def validateUid(self, uid, unitType):
        if not re.match('^[a-zA-Z0-9\.]+$', uid):
            tcg_error("The %s uid: %s is invalid. It must be a sequence of ASCII "\
                      "alphanumeric ([a-zA-Z0-9]) and dot (.) characters." % (unitType.__name__, uid))

    def __add_function(self, f):
        self.function_map[f.getUid()] = f
        self.functions.append(f)

    def __add_service(self, sv):
        self.service_map[sv.getUid()] = sv
        self.services.append(sv)

    def __add_component(self, c):
        self.component_map[c.getUid()] = c
        self.components.append(c)
