import sys
import os
import logging
from csm_unit import CSMUnit
import AMFConstants
import CSMConstants
import CgtConstants
import meta_data
import AMFTools
from tcg.common import convert_s_and_ms_to_number
from tcg.utils.logger_tcg import tcg_error
from tcg.CSMConstants import validateAndGetBool
from csm_entity_version import CSMEntityVersion, VERSION_TYPE_DOTTED
import itertools

class ConfigurationFile(CSMUnit):
    '''
    Component ConfigurationFile class
    '''

    def __init__(self):
        '''
        ConfigurationFile Constructor
        '''
        self.name = None
        self.data_type = CSMConstants.CONFIGURATION_DATA_TYPE_INITIAL
        self.data_category = None

    def set(self, config_file_dict=None):
        if config_file_dict is not None :
            if config_file_dict.has_key(CgtConstants.COMPONENT_CONFIGURATIONFILE_NAME_TAG):
                self.name = config_file_dict[CgtConstants.COMPONENT_CONFIGURATIONFILE_NAME_TAG]
            else:
                logging.error("Configuration Attribute Name cannot be empty")

            if config_file_dict.has_key(CgtConstants.COMPONENT_CONFIGURATIONFILE_TYPE_TAG):
                self.data_type = config_file_dict[CgtConstants.COMPONENT_CONFIGURATIONFILE_TYPE_TAG]

            if config_file_dict.has_key(CgtConstants.COMPONENT_CONFIGURATIONFILE_CATEGORY_TAG):
                self.data_category = config_file_dict[CgtConstants.COMPONENT_CONFIGURATIONFILE_CATEGORY_TAG]


    def get_name(self):
        return self.name

    def get_data_type(self):
        return self.data_type

    def get_data_category(self):
        return self.data_category

    def set_name(self, name):
        self.name = name

    def set_data_type(self, data_type):
        self.data_type = data_type


class __ComponentConstraints(CSMUnit):

    def __init__(self):
        self.scope = None
        self.reboot = None
        self.afterComponents = []  # list of pairs (ct_uid, method)
        self.is_set = False
        self.bootstrap = False

    def set(self, inputDict):
        if inputDict:
            if (CgtConstants.COMPONENT_CONSTRAINTS_BOOTSTRAP in inputDict):
                logging.info("Component constraint 'bootstrap' is not yet supported.")

            if (CgtConstants.COMPONENT_CONSTRAINTS_SCOPE in inputDict):
                self.scope = inputDict[CgtConstants.COMPONENT_CONSTRAINTS_SCOPE]
            else:
                self.scope = None

            if (CgtConstants.COMPONENT_CONSTRAINTS_REBOOT in inputDict):
                self.reboot = validateAndGetBool(inputDict[CgtConstants.COMPONENT_CONSTRAINTS_REBOOT],
                                                 CgtConstants.COMPONENT_CONSTRAINTS_REBOOT)
            else:
                self.reboot = False

            del self.afterComponents[:]  # clear the list before assigning the new elements
            if (CgtConstants.COMPONENT_CONSTRAINTS_AFTER in inputDict):
                for afterCompDict in inputDict[CgtConstants.COMPONENT_CONSTRAINTS_AFTER]:
                    if (CgtConstants.COMPONENT_CONSTRAINTS_COMPONENT not in afterCompDict or
                            afterCompDict[CgtConstants.COMPONENT_CONSTRAINTS_COMPONENT] is None):
                        tcg_error("Constraint 'after' does not specify component uid. Component uid is mandatory in contraints 'after'")
                    method = afterCompDict.get(
                        CgtConstants.COMPONENT_CONSTRAINTS_METHOD,
                        GenericConstraints.METHOD_DEFAULT
                    )
                    self.afterComponents.append(
                        (afterCompDict[CgtConstants.COMPONENT_CONSTRAINTS_COMPONENT], method)
                    )
            self.is_set = True

    def getScope(self):
        return self.scope

    def getReboot(self):
        return self.reboot

    def getBootstrap(self):
        return self.bootstrap

    def getAfterComponents(self):
        """
        returns a dictionary with key 'component_uid' and value 'method' where method could be None.
        """
        return self.afterComponents

    def isSet(self):
        return self.is_set


class GenericConstraints(__ComponentConstraints):
    METHOD_DIFFERENT_PROCEDURE = 'DIFFERENT-STEP'
    METHOD_DIFFERENT_CAMPAIGN  = 'DIFFERENT-FLOW'
    METHOD_DEFAULT = METHOD_DIFFERENT_PROCEDURE

    def __init__(self):
        super(GenericConstraints, self).__init__()


class InstallationConstraints(GenericConstraints):
    def __init__(self):
        super(InstallationConstraints, self).__init__()


class UpgradeConstraints(GenericConstraints):
    def __init__(self):
        super(UpgradeConstraints, self).__init__()
        self.migrationScope = None
        self.oldest_version = CSMEntityVersion()

    def set(self, inputDict, owner_uid):
        super(UpgradeConstraints, self).set(inputDict)
        if (CgtConstants.COMPONENT_CONSTRAINTS_MIGRATION_SCOPE in inputDict):
            self.migrationScope = inputDict[CgtConstants.COMPONENT_CONSTRAINTS_MIGRATION_SCOPE]

        if (CgtConstants.COMPONENT_CONSTRAINTS_OLDEST_VERSION_TAG in inputDict):
            self.oldest_version.setVersion(inputDict[CgtConstants.COMPONENT_CONSTRAINTS_OLDEST_VERSION_TAG], owner_uid, VERSION_TYPE_DOTTED)

    def getMigrationScope(self):
        return self.migrationScope

    def getOldestVersion(self):
        return self.oldest_version.getVersionString()

    def getOldestVersionObject(self):
        return self.oldest_version


class ConfigurationAttribute():

    def __init__(self):
        self.name = None
        self.default_value = None
        self.description = ""
        self.format_rule = "string"

    def set(self, conf_attr_dict):
        if conf_attr_dict is not None:
            if conf_attr_dict.has_key(CgtConstants.COMPONENT_ATTRIBUTE_NAME_TAG):
                self.name = conf_attr_dict[CgtConstants.COMPONENT_ATTRIBUTE_NAME_TAG]
            else:
                logging.error("Configuration Attribute Name cannot be empty")

            if conf_attr_dict.has_key(CgtConstants.COMPONENT_ATTRIBUTE_DEFAULTVALUE_TAG):
                self.default_value = conf_attr_dict[CgtConstants.COMPONENT_ATTRIBUTE_DEFAULTVALUE_TAG]

            if conf_attr_dict.has_key(CgtConstants.COMPONENT_ATTRIBUTE_DESCRIPTION_TAG):
                self.description = conf_attr_dict[CgtConstants.COMPONENT_ATTRIBUTE_DESCRIPTION_TAG]

            if conf_attr_dict.has_key(CgtConstants.COMPONENT_ATTRIBUTE_FORMAT_TAG):
                self.format_rule = conf_attr_dict[CgtConstants.COMPONENT_ATTRIBUTE_FORMAT_TAG]
                if not self.format_rule in CSMConstants.FORMAT_RULE_VALID_OPTIONS:
                    logging.error("The format-rule attribute is allowed to take values only from the \
                    following list: %s" %str(CSMConstants.FORMAT_RULE_VALID_OPTIONS))

    def get_name(self):
        return self.name

    def get_default_value(self):
        return self.default_value

    def get_description(self):
        return self.description

    def get_format_fule(self):
        return self.format_rule

    def set_name(self, name):
        self.name = name

    def set_default_value(self, default_value):
        self.default_value = default_value

    def set_description(self, description):
        self.description = description

    def set_format_rule(self, format_rule):
        self.format_rule = format_rule

class HealthCheckKey(CSMUnit):

    def __init__(self):

        self._safHealthcheckKey = "osafHealthCheck"
        self._saAmfHctDefPeriod = convert_s_and_ms_to_number("1000 ms")
        self._saAmfHctDefMaxDuration = convert_s_and_ms_to_number("500 ms")

    def set(self, healthCheckKey = None):
        if healthCheckKey is not None :
            self._safHealthcheckKey = healthCheckKey[CgtConstants.HEALTHCHECK_KEY_TAG] if healthCheckKey.has_key(
                                                    CgtConstants.HEALTHCHECK_KEY_TAG) else "osafHealthCheck"
            self._saAmfHctDefPeriod = convert_s_and_ms_to_number(healthCheckKey[CgtConstants.HEALTHCHECK_PERIOD_TAG] if healthCheckKey.has_key(
                                                    CgtConstants.HEALTHCHECK_PERIOD_TAG) else "1000 ms")
            self._saAmfHctDefMaxDuration = convert_s_and_ms_to_number(healthCheckKey[CgtConstants.HEALTHCHECK_TIMEOUT_TAG] if healthCheckKey.has_key(
                                                    CgtConstants.HEALTHCHECK_TIMEOUT_TAG) else "500 ms")

    def getSaAmfHctDefPeriod(self):
        return self._saAmfHctDefPeriod

    def getSaAmfHctDefMaxDuration(self):
        return self._saAmfHctDefMaxDuration

    def getSafHealthcheckKey(self):
        return self._safHealthcheckKey

class Component(CSMUnit) :

    '''
    CSM Component class
    '''
    def __init__(self):

        '''
        Constructor for CSM Component class
        '''
        super(Component, self).__init__()
        self._proxied_comp_counter = itertools.count(1)
        self.uid = None
        self.name = None
        self.description = None
        self.availabilityManager = CSMConstants.AVAILABILTY_MANAGER_NONE  #availability-manager

        self.dependsOnComponents = []       #"depends-on" element are only checked when deployment
                                            #campaigns are constructed but not checked or used runtime.
                                            #That is, it is not translated for instance into a "CSI" dependency
                                            #information on "AMF" model level

        self.supersedes = []

        self.installationConstraints = None
        self.upgradeConstraints = None

        self.controlPolicyType = CSMConstants.COMPONENT_CONTROL_POLICY_SIMPLE   #control-policy/type
        self.controlPolicyParent = None     #control-policy/parent

        self.nodeActive = CSMConstants.NODE_ACTIVE_ONE             #active instances on node
        self.nodeStandby = CSMConstants.NODE_STANDBY_NONE           #standby instances on node
        self.nodeActiveStandby = CSMConstants.NODE_ACTIVE_STANDBY_NO                       #"NO"       #active standby on same_node
        self.clusterActive = CSMConstants.CLUSTER_ACTIVE_MANY         #active instances on cluster
        self.clusterStandby = CSMConstants.CLUSTER_STANDBY_NONE        #standby instances on cluster


        self._saAmfCtDefClcCliTimeout = "10 s"      #time period in which the configured availability management system (AMF)
                                            #should expect a response of the CLC-CLI commands used for
                                            #component life-cycle control

        self._saAmfCtDefCallbackTimeout = "10 s"   #time period in which the configured availability management
                                            #system should expect a response for the component active/standby
                                            #assignment handling operations

        self._saAmfCtDefQuiescingCompleteTimeout = "60 s"        #time period in which the configured availability management system
                                            #should expect a component to migrate service from one location
                                            #to the other

        self.recoveryPolicy             = "COMPONENT_FAILOVER" #recovery type the configured availability management system should
                                                               #take if the component is crashing or when the timeout on
                                                               #CLC-CLI and monitor commands expire

        self._saAmfCtDefRecoveryOnError = 3                    #refer AMFConstants.py file

        self.external = False               #specify if component is external, default is False (not external)

        self.plugin = None                  #A relative path pointing to a TCG plugin placed
                                            #in the deployment package.

                                            #The relative path is to be considered from
                                            #the YAML specification of the related component.

                                            #A TCG plugin is to be created for a component if custom items
                                            #are to be generated into the AMF model (eg: special instance
                                            #configurations) and the SMF campaign (eg: doCLI script references,
                                            #callbacks, special control on entity instance attribute and values, etc.).
        self.sourceFile = None

        self.minNodes = 1
        self.maxNodes = 100
        self.configurationFiles = []
        self.promotion_attributes = []
        self.environment_attributes = []
        self._softwares = []
        self._software_type = None
        self.installPrefix = "/"

        self.componentRedundancyModel = None

        self._saAmfCtDefRecoveryOnError = None
        self._saAmfCtCompCategory = None
        self._saAmfCtDefCmdEnv = []
        self._saAmfCtDefClcCliTimeout = None

        self._osafAmfCtRelPathHcCmd = None
        self._osafAmfCtRelPathHcCmdArgv = None
        self._saAmfCtRelPathInstantiateCmd = None
        self._saAmfCtDefInstantiateCmdArgv = None
        self._saAmfCtDefInstantiationLevel = 0 #set to 0 by default
        self._saAmfCtRelPathTerminateCmd = None
        self._saAmfCtDefTerminateCmdArgv = None
        self._saAmfCtRelPathCleanupCmd = None
        self._saAmfCtDefCleanupCmdArgv = None

        self._saAmfCtRelPathAmStartCmd = None
        self._saAmfCtDefAmStartCmdArgv = None
        self._saAmfCtRelPathAmStopCmd = None
        self._saAmfCtDefAmStopCmdArgv = None

        self._saAmfCtDefDisableRestart = None

        self.healthCheckKeys = []

        self.componentVersion = CSMEntityVersion()

        self._meta_data = None
        self._input_yaml_dict = None

    def __hash__(self):
        return hash((self.uid, self.getVersion()))

    def __eq__(self, other):
        if (not other) or (type(other) is not Component):
            return False
        return self.uid == other.uid and self.getVersion() == other.getVersion()

    def proxied_comp_counter(self):
        return next(self._proxied_comp_counter)

    def setValues(self, name=None, uid=None, description=None, componentVersion=None,
                softwares=None,
                installPrefix="/", configurationFiles=[],
                instantiateCommand='', cleanupCommand='', monitorCommand='',
                dependsOnComponents=[], terminateCommand='', healthCheckKeys=[],
                minNodes=1, maxNodes=100,
                installationConstraints = {},
                upgradeConstraints = {},
                controlPolicyType="SIMPLE",
                controlPolicyParent=None,
                nodeActive="ONE" ,
                nodeStandby="NONE",
                nodeActiveStandby='NO', #"NO"
                clusterActive="MANY",
                clusterStandby="NONE",
                startStopTimeout="10 s",
                promoteDemoteTimeout="10 s",
                migrateTimeout="60 s",
                recoveryPolicy="COMPONENT_FAILOVER",
                external=False,
                plugin=None,
                promotion_attributes=[],
                environment_attributes=[],
                availabilityManager=CSMConstants.AVAILABILTY_MANAGER_NONE,
                sourceFile=None,
                pluginsBaseDir=None,
                componentsMetaData=None,
                input_yaml_dict=None,
                supersedes=[]):
        self.setName(name)
        self.setUid(uid)
        self.setDescription(description)
        self.setComponentVersion(componentVersion, uid)
        self.set_softwares(softwares, availabilityManager)
        self.setInstallPrefix(installPrefix)
        self.setConfigurationFiles(configurationFiles)
        self.setInstantiateCommand(instantiateCommand)
        self.setCleanupCommand(cleanupCommand)
        self.setTerminateCommand(terminateCommand)
        self.setMonitorCommand(monitorCommand)
        self.setHealthCheckKeys(healthCheckKeys)
        self.setDependsOnComponents(dependsOnComponents)
        self.setInstallationConstraints(installationConstraints)
        self.setUpgradeConstraints(upgradeConstraints, uid)
        self.setAlreadyInstalledVersion(None)
        self.setMinNodes(minNodes)
        self.setMaxNodes(maxNodes)
        self.setRecoveryPolicy(recoveryPolicy)
        self.setAvailabilityManager(availabilityManager)
        self.setControlPolicyType(controlPolicyType)
        self.setControlPolicyParent(controlPolicyParent)
        self.setNodeActive(nodeActive)
        self.setNodeStandby(nodeStandby)
        self.setNodeActiveStandby(nodeActiveStandby)
        self.setClusterActive(clusterActive)
        self.setClusterStandby(clusterStandby)
        self.setComponentRedundancyModel()
        self.setComponentCapabilityModel()
        self.setStartStopTimeout(startStopTimeout)
        self.setPromoteDemoteTimeout(promoteDemoteTimeout)
        self.setMigrateTimeout(migrateTimeout)
        self.setExternal(external)
        self.setPlugin(plugin)
        self.set_promotion_attributes(promotion_attributes)
        self.set_environment_attributes(environment_attributes)
        self.setSourceFile(sourceFile)
        self.setPluginsBaseDir(pluginsBaseDir)
        self.setMetaData(componentsMetaData, uid)
        self.set_input_yaml(input_yaml_dict)
        self.set_supersedes(supersedes)

    def getName(self):
        return self.name

    def getUid(self):
        return self.uid

    def getType(self):
        return self._saAmfCtCompCategory

    def getVersion(self):
        return self.componentVersion.getVersionString()

    def getVersionObject(self):
        return self.componentVersion

    def getDescription(self):
        return self.description

    def getConfigurationFiles(self):
        return self.configurationFiles

    def getInstantiateCommand(self):
        if self._saAmfCtRelPathInstantiateCmd :
            return os.path.join(self.installPrefix, self._saAmfCtRelPathInstantiateCmd)
        else :
            return self._saAmfCtRelPathInstantiateCmd

    def getTerminateCommand(self):
        if self._saAmfCtRelPathTerminateCmd :
            return os.path.join(self.installPrefix, self._saAmfCtRelPathTerminateCmd)
        else :
            return self._saAmfCtRelPathTerminateCmd

    def getCleanupCommand(self):
        if self._saAmfCtRelPathCleanupCmd :
            return os.path.join(self.installPrefix, self._saAmfCtRelPathCleanupCmd)
        else :
            return self._saAmfCtRelPathCleanupCmd

    def getMonitorCommand(self):
        if self._osafAmfCtRelPathHcCmd :
            return os.path.join(self.installPrefix, self._osafAmfCtRelPathHcCmd)
        else :
            return self._osafAmfCtRelPathHcCmd

    def getInstantiateCommandArgs(self):
        return self._saAmfCtDefInstantiateCmdArgv

    def getMonitorCommandArgs(self):
        return self._osafAmfCtRelPathHcCmdArgv

    def getTerminateCommandArgs(self):
        return self._saAmfCtDefTerminateCmdArgv

    def getCleanupCommandArgs(self):
        return self._saAmfCtDefCleanupCmdArgv

    """FIXME: Backward compatibility reasons for this, should be removed after plugin is done"""
    def getSoftwareName(self):
        if self.get_software_name():
            return self.get_software_name()[0]
        return None

    def get_software_name(self):
        if self._softwares:
            return [sw+'_'+self.componentVersion.getVersionString() for sw in self._softwares]
        return None

    def get_software_name_without_version(self):
        return self._softwares

    def get_software_type(self):
        return self._software_type

    def getInstallPrefix(self):
        return self.installPrefix

    def getDependsOnComponents(self) :
        return self.dependsOnComponents

    def get_supersedes(self):
        return self.supersedes

    def getInstallationConstraints(self):
        return self.installationConstraints

    def hasUpgradeConstraints(self):
        return self.upgradeConstraints is not None

    def getUpgradeConstraints(self):
        return self.upgradeConstraints

    def getAlreadyInstalledVersion(self):
        return self.alreadyInstalledVersion

    def getHealthCheckKeys(self, healthCheckKeys = []) :
        return self.healthCheckKeys

    def getRecoveryPolicy(self):
        return self.recoveryPolicy

    def getMinNodes(self):
        return self.minNodes

    def getMaxNodes(self):
        return self.maxNodes

    def getControlPolicyType(self) :
        return self.controlPolicyType

    def getControlPolicyParent(self) :
        return self.controlPolicyParent

    def getNodeActive(self) :
        return self.nodeActive

    def getNodeStandby(self) :
        return self.nodeStandby

    def getNodeActiveStandby(self) :
        return self.nodeActiveStandby

    def getClusterActive(self) :
        return self.clusterActive

    def getClusterStandby(self) :
        return self.clusterStandby

    def getStartStopTimeout(self) :
        return self._saAmfCtDefClcCliTimeout

    def getPromoteDemoteTimeout(self) :
        return self._saAmfCtDefCallbackTimeout

    def getMigrateTimeout(self) :
        return self._saAmfCtDefQuiescingCompleteTimeout

    def getExternal(self) :
        return self.external

    def getPlugin(self) :
        return self.plugin

    def get_promotion_attributes(self):
        return self.promotion_attributes

    def get_promotion_attribute_instance(self, name):
        prom_attr_instance = None
        if name is not None:
            for prom_attr in self.promotion_attributes:
                if prom_attr.get_name() == name:
                    prom_attr_instance = prom_attr
                    break
        return prom_attr_instance

    def get_environment_attributes(self):
        return self.environment_attributes

    def get_environment_attribute_instance(self, name):
        env_attr_instance = None
        if name is not None:
            for env_attr in self.environment_attributes:
                if env_attr.get_name() == name:
                    env_attr_instance = env_attr
                    break
        return env_attr_instance

    def get_health_check_key_instance(self, health_check_key):
        for key in self.healthCheckKeys:
            if key.getSafHealthcheckKey() == health_check_key:
                return key
        return None

    def getComponentRedundancyModel(self):
        return self.componentRedundancyModel

    def getComponentCapabilityModel(self):
        return self.componentCapabilityModel

    def getAvailabilityManager(self) :
        return self.availabilityManager

    def getSourceFile(self) :
        return self.sourceFile

    def getSourceFileLocation(self):
        if self.sourceFile:
            return os.path.abspath(os.path.join(self.sourceFile, os.pardir))

    def setSourceFile(self, sourceFile = None) :
        self.sourceFile = sourceFile

    def setPluginsBaseDir(self, pluginsBaseDir):
        self.pluginsBaseDir = pluginsBaseDir

    def getPluginsBaseDir(self):
        if self.pluginsBaseDir:
            return self.pluginsBaseDir
        else:
            return self.getSourceFileLocation()

    def setMetaData(self, componentsMetaData, uid):
        try:
            self._meta_data = meta_data.ComponentsMetaData(componentsMetaData)
        except ValueError as e:
            tcg_error("Component: %s: %s" %(uid, e))

    def getMetaData(self) :
        return self._meta_data

    def setAvailabilityManager(self, availabilityManager = CSMConstants.AVAILABILTY_MANAGER_NONE) :
        if availabilityManager.upper() not in CSMConstants.AVAILABILTY_VALID_OPTONS:
            tcg_error('{am} is not a valid option for components:availability-manager for component {c}'.format(am=availabilityManager, c=self.uid))
        self.availabilityManager = availabilityManager

    def setComponentRedundancyModel(self):
        self.componentRedundancyModel = CSMConstants.getComponentRedundancyModel(
                                                nodeActive = self.nodeActive,
                                                nodeStandby = self.nodeStandby,
                                                nodeActiveStandby = self.nodeActiveStandby,
                                                clusterActive = self.clusterActive,
                                                clusterStandby = self.clusterStandby)

    def setComponentCapabilityModel(self):
        self.componentCapabilityModel = CSMConstants.getComponentCapabilityModel(
                                                nodeActive = self.nodeActive,
                                                nodeStandby = self.nodeStandby,
                                                nodeActiveStandby = self.nodeActiveStandby,
                                                controlPolicyType = self.controlPolicyType)

        currentMultiplicity = {'nodeActive' : self.nodeActive, 'nodeStandby' : self.nodeStandby,
                           'nodeActiveStandby' : self.nodeActiveStandby,
                           'controlPolicyType' : self.controlPolicyType
                          }
        if not self.componentCapabilityModel :
            tcg_error("Unsupported or invalid node multiplicity policy and control policy %s for component %s"%(currentMultiplicity, self.uid))

    def set_promotion_attributes(self, promotion_attributes):
        for prom_attr in promotion_attributes:
            prom_attr_instance = ConfigurationAttribute()
            prom_attr_instance.set(prom_attr)
            self.promotion_attributes.append(prom_attr_instance)

    def set_environment_attributes(self, environment_attributes):
        for env_attr in environment_attributes:
            env_attr_instance = ConfigurationAttribute()
            env_attr_instance.set(env_attr)
            self.environment_attributes.append(env_attr_instance)

    def setControlPolicyType(self, controlPolicyType = None) :
        if controlPolicyType is not None:
            if controlPolicyType.upper() not in CSMConstants.COMPONENT_CONTROL_POLICY_VALID_OPTIONS:
                tcg_error('{cp} Is not a valid option for components:availability-properties:control-policy:type in component {c}'.format(cp=controlPolicyType, c=self.uid))
        self.controlPolicyType = controlPolicyType

    def setControlPolicyParent(self, controlPolicyParent = None) :
        self.controlPolicyParent = controlPolicyParent

    def setNodeActive(self, nodeActive = None) :
        if nodeActive is not None:
            if nodeActive.upper() not in CSMConstants.NODE_ACTIVE_VALID_OPTIONS:
                tcg_error('{na} Is not a valid option for components:multiplicity-policy:node-active in component {c}'.format(na=nodeActive, c=self.uid))
        self.nodeActive = nodeActive

    def setNodeStandby(self, nodeStandby = None) :
        if nodeStandby is not None:
            if nodeStandby.upper() not in CSMConstants.NODE_STANDBY_VALID_OPTIONS:
                tcg_error('{ns} Is not a valid option for components:multiplicity-policy:node-standby in component {c}'.format(ns=nodeStandby, c=self.uid))
        self.nodeStandby = nodeStandby

    def setNodeActiveStandby(self, nodeActiveStandby = CSMConstants.NODE_ACTIVE_STANDBY_NO) :
        if not isinstance(nodeActiveStandby, basestring) or nodeActiveStandby not in CSMConstants.NODE_ACTIVE_STANDBY_VALID_OPTIONS:
            tcg_error('{nas} is not a valid option for component:multiplicity-policy:node-active-standby'.format(nas=nodeActiveStandby))
        else:
            self.nodeActiveStandby = nodeActiveStandby

    def setClusterActive(self, clusterActive = None) :
        if clusterActive is not None:
            if clusterActive.upper() not in CSMConstants.CLUSTER_ACTIVE_VALID_OPTIONS:
                tcg_error('{ca} Is not a valid option for components:multiplicity-policy:cluster-active in component {c}'.format(ca=clusterActive, c=self.uid))
        self.clusterActive = clusterActive

    def setClusterStandby(self, clusterStandby = None) :
        if clusterStandby is not None:
            if clusterStandby.upper() not in CSMConstants.CLUSTER_STANDBY_VALID_OPTIONS:
                tcg_error('{cs} Is not a valid option for components:multiplicity-policy:cluster-standby in component {c}'.format(cs=clusterStandby, c=self.uid))
        self.clusterStandby = clusterStandby

    def setStartStopTimeout(self, startStopTimeout):

        startStopTimeout = convert_s_and_ms_to_number(startStopTimeout)

        self._saAmfCtDefClcCliTimeout = startStopTimeout

    def setPromoteDemoteTimeout(self, promoteDemoteTimeout):
        promoteDemoteTimeout = convert_s_and_ms_to_number(promoteDemoteTimeout)
        self._saAmfCtDefCallbackTimeout = promoteDemoteTimeout

    def setMigrateTimeout(self, migrateTimeout):
        migrateTimeout = convert_s_and_ms_to_number(migrateTimeout)
        self._saAmfCtDefQuiescingCompleteTimeout = migrateTimeout

    def setExternal(self, external = False) :
        self.external = external

    def setPlugin(self, plugin = None) :
        self.plugin = plugin

    def setMaxNodes(self, maxNodes = 100) :
        self.maxNodes = maxNodes

    def setMinNodes(self, minNodes = 1) :
        self.minNodes = minNodes

    def setRecoveryPolicy(self, recoveryPolicy = CSMConstants.RECOVERY_POLICY_COMPONENT_FAILOVER):
        if recoveryPolicy.upper() not in CSMConstants.RECOVERY_POLICY_VALID_OPTIONS:
            tcg_error('{cs} Is not a valid option for components:availability-properties:recovery-policy in component {c}'.format(rp=recoveryPolicy, c=self.uid))

        self.recoveryPolicy = 'SA_AMF_' + recoveryPolicy.upper()
        if AMFConstants.isValidRecoveryOnErrorName(self.recoveryPolicy) :
            self._saAmfCtDefRecoveryOnError = AMFConstants.getRecoveryOnErrorNumber(self.recoveryPolicy)
        else :
            tcg_error("invalid RecoveryOnError value in unit %s" % (self.uid))

        #Setting ctdefdisablerestart
        if recoveryPolicy.upper() ==  CSMConstants.RECOVERY_POLICY_COMPONENT_RESTART:
            self._saAmfCtDefDisableRestart = AMFConstants.BOOLEAN_NAME_FALSE

        elif recoveryPolicy.upper() in [CSMConstants.RECOVERY_POLICY_COMPONENT_FAILOVER,
                                CSMConstants.RECOVERY_POLICY_NODE_SWITCHOVER,
                                CSMConstants.RECOVERY_POLICY_NODE_FAILOVER,
                                CSMConstants.RECOVERY_POLICY_NODE_FAILFAST] :
            self._saAmfCtDefDisableRestart = AMFConstants.BOOLEAN_NAME_TRUE

    def getDisableRestart(self) :
        return self._saAmfCtDefDisableRestart

    def get_input_yaml_dict(self):
        return self._input_yaml_dict

    def setDisableRestart(self, flag = None):
        if flag not in ["SA_TRUE", "SA_FALSE"] :
            tcg_error("Component Disable Restart only takes SA_TRUE or SA_FALSE")
        self._saAmfCtDefDisableRestart = flag

    def setAlreadyInstalledVersion(self, version):
        self.alreadyInstalledVersion = version

    def setDependsOnComponents(self, dependsOnComponents = []) :
        self.dependsOnComponents = dependsOnComponents

    def setInstallationConstraints(self, installConstrDic):
        self.installationConstraints = InstallationConstraints()
        self.installationConstraints.set(installConstrDic)

    def setUpgradeConstraints(self, upgradeConstrDic, owner_uid):
        self.upgradeConstraints = UpgradeConstraints()
        self.upgradeConstraints.set(upgradeConstrDic, owner_uid)

    def setName(self, name = None):
        self.name = name

    def setUid(self, uid = None):
        self.uid = uid

    def setType(self, type = None):
        self._saAmfCtCompCategory = type

    def setComponentVersion(self, componentVersion=None, owner_uid=None):
        self.componentVersion.setVersion(componentVersion, owner_uid, VERSION_TYPE_DOTTED)

    def setDescription(self, description = None):
        self.description = description

    def setConfigurationFiles(self, configurationFiles = []):
        for configFileDict in configurationFiles:
            configFileInstance = ConfigurationFile()
            configFileInstance.set(configFileDict)
            self.configurationFiles.append(configFileInstance)

    def setInstantiateCommand(self, command = None):
        if command != None :
            commandList = command.split(' ')
            self._saAmfCtRelPathInstantiateCmd = commandList[0]
            if len(commandList) > 1 :
                self._saAmfCtDefInstantiateCmdArgv = commandList[1:]

    def setMonitorCommand(self, command = None):
        if command != None :
            commandList = command.split(' ')
            self._osafAmfCtRelPathHcCmd = commandList[0]
            if len(commandList) > 1 :
                self._osafAmfCtRelPathHcCmdArgv = commandList[1:]

    def setTerminateCommand(self, command = None):
        if command != None :
            commandList = command.split(' ')
            self._saAmfCtRelPathTerminateCmd = commandList[0]
            if len(commandList) > 1 :
                self._saAmfCtDefTerminateCmdArgv = commandList[1:]

    def setCleanupCommand(self, command = None):
        if command != None :
            commandList = command.split(' ')
            self._saAmfCtRelPathCleanupCmd = commandList[0]
            if len(commandList) > 1 :
                self._saAmfCtDefCleanupCmdArgv = commandList[1:]

    def set_softwares(self, softwares, availabilityManager):
        rpm = CgtConstants.COMPONENT_SOFTWARE_RPM_TAG
        sdp = CgtConstants.COMPONENT_SOFTWARE_SDP_TAG
        if not softwares:
            return
        if type(softwares) is not dict:
            raise ValueError("software type error in component.")
        if len(softwares) != 1:
            raise ValueError("component {0} must have only one software type.".format(self.uid) )
        if rpm in softwares:
            rpms = softwares[rpm]
            if type(rpms) is not list:
                raise ValueError("rpms in software should be a list.")
            if len(rpms) > 1 and availabilityManager.upper() != CSMConstants.AVAILABILTY_MANAGER_NONE:
                raise ValueError("availability-manager have to be NONE for multiple SW bundle.")
            self._softwares = rpms
            self._software_type = rpm
        elif sdp in softwares:
            sdps = softwares[sdp]
            if type(sdps) is not str:
                raise ValueError("sdp in software should be string.")
            self._softwares.append(sdps)
            self._software_type = sdp

    def setInstallPrefix(self, installPrefix = "/"):
        self.installPrefix = installPrefix

    def setHealthCheckKeys(self, healthCheckKeys = []) :
        for healthCheckKey in healthCheckKeys :
            healthCheckKeyInstance = HealthCheckKey()
            healthCheckKeyInstance.set(healthCheckKey)
            # ensure that the key values in healthCheckKeys are unique
            if (self.get_health_check_key_instance(
                  healthCheckKeyInstance.getSafHealthcheckKey())) == None:
                self.healthCheckKeys.append(healthCheckKeyInstance)
            else:
                tcg_error('ERROR: attempting to set identical healthCheckKeys ({a}) in component {c}'.
                      format(a=healthCheckKeyInstance.getSafHealthcheckKey(),
                      c=self.uid))

    def set_supersedes(self, supersedes):
        self.supersedes = supersedes

    def set_input_yaml(self, input_yaml_dict):
        self._input_yaml_dict = input_yaml_dict
        CSMUnit.sort_yaml_dict(self._input_yaml_dict)

    def display(self):
        attrs = vars(self)
        print attrs.items()

    def validate(self):
        '''
        Does the schema validation and other conditional checks related to CSM

        '''

        CSMConstants.isValidMultiplicityPolicy(nodeActive = self.nodeActive,
                                               nodeStandby = self.nodeStandby,
                                               nodeActiveStandby = self.nodeActiveStandby,
                                               clusterActive = self.clusterActive,
                                               clusterStandby = self.clusterStandby)

    def upgrade_availability_check(self, base):
        # cau_tags defind cau status for component attributes.
        # It not must to list an attribute if it is CAU and all
        # it's leafs are CAU.
        cau_tags = {
            'uid': (False, None, None),
            'availability-manager': (False, 'NONE', None),
            # Question: availability-properties in component is marked as CAM
            # Which means it's for migration and not able to change in upgrade
            # But it's child element lifecycle-control is CAU.
            # Not make sense to say availability-properties is CAM.
            'availability-properties': (True, None, {
                'control-policy': (True, None, {
                    'type': (False, 'SIMPLE', None),
                    'parent': (False, None, None)
                }),
                'multiplicity-policy': (True, None, {
                    'node-active': (False, 'ONE', None),
                    'node-standby': (False, 'NONE', None),
                    'node-active-standby': (False, 'NO', None),
                    'cluster-active': (False, 'MANY', None),
                    'cluster-standby': (False, 'NONE', None)
                }),
                'lifecycle-control': (True, None, None)
            })
        }
        base_yml = base.get_input_yaml_dict()
        return CSMUnit.yaml_upgrade_availability_check('components', base_yml, self._input_yaml_dict, (True, None, cau_tags))

    def component_is_deletable(self):
        '''
        a component with availability manager other than AMF can be removed
        '''
        return (self.getAvailabilityManager().upper() != CSMConstants.AVAILABILTY_MANAGER_AMF)

    def software_bundle_names(self, online_adapter=None):
        if self._software_type is None:
            logging.info("Component %s has no software bundle." % self.uid)
        elif self._software_type not in [CgtConstants.COMPONENT_SOFTWARE_SDP_TAG, CgtConstants.COMPONENT_SOFTWARE_RPM_TAG]:
            logging.warning("Component %s has unsupported software type: %s " % (self.uid, self._software_type))
        else:
            for filename, bundle in self._meta_data.softwares():
                sw_bundle = None
                if self._software_type == CgtConstants.COMPONENT_SOFTWARE_SDP_TAG:
                    sw_bundle = bundle
                else:  # if self._software_type == "rpm":
                    # 3PP is only Workaround for 3pp softwares + code duplication
                    if bundle.startswith(AMFTools.getProvider() + "-") or bundle.startswith("3PP-"):
                        sw_bundle = bundle
                    elif not self.external and online_adapter:
                        sw_bundle = online_adapter.get_rpm_name(bundle, filename)
                    else:
                        sw_bundle = AMFTools.getProvider() + "-" + bundle
                if sw_bundle is None:
                    tcg_error("couldn't get bundle name of %s file of component %s" % (filename, self.uid))
                yield filename, sw_bundle

    def get_single_sdp_name(self, online_adapter):
        try:
            _, sw_bundle = next(self.software_bundle_names(online_adapter))
            return sw_bundle
        except StopIteration:
            return None
    def check_for_upgrade(self, base_unit):
        '''
        component upgrade only with a change in version number
        '''

        if self.getVersion() != base_unit.getVersion():
            return True
        return False
