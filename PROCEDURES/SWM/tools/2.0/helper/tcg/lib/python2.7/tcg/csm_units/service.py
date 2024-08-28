import os
from csm_unit import CSMUnit
from tcg.common import convert_s_and_ms_to_number, Prioritize, validate_is_number

import CgtConstants
import AMFConstants
import CSMConstants

import meta_data
import logging
import AMFTools
from tcg.utils.logger_tcg import tcg_error
from csm_entity_version import CSMEntityVersion
from component import Component


class PromotionDependency():
    def __init__(self):
        self.dependsOn = None
        self._saAmfToleranceTime = "5 s"

    def set(self, dependsOnDict={}):
        if dependsOnDict is not None :
            dependsOnUid = dependsOnDict[CgtConstants.SERVICE_DEPENDS_ON_TAG] if dependsOnDict.has_key(
                            CgtConstants.SERVICE_DEPENDS_ON_TAG) else tcg_error(
                                "%s tag in %s tag cannot be empty" % (CgtConstants.SERVICE_DEPENDS_ON_TAG, CgtConstants.SERVICE_PROMOTION_DEPENDENCY_TAG))
            toleranceTimeout = dependsOnDict[CgtConstants.SERVICE_TOLERANCE_TIMEOUT_TAG] if dependsOnDict.has_key(
                            CgtConstants.SERVICE_TOLERANCE_TIMEOUT_TAG) else "5 s"

        self.setDependsOnService(dependsOnUid)
        self.setToleranceTimoeut(toleranceTimeout)

    def getDependsOnService(self):
        return self.dependsOn

    def getToleranceTimeout(self):
        return self._saAmfToleranceTime

    def setDependsOnService(self, dependsOnUid=None):
        self.dependsOn = dependsOnUid

    def setToleranceTimoeut(self, toleranceTimeout):
        self._saAmfToleranceTime = convert_s_and_ms_to_number(toleranceTimeout)

class Service(CSMUnit):
    '''
    CSM Service class
    '''
    def __init__(self) :
        ''' Constructor of Service '''
        super(Service, self).__init__()
        self.uid = None
        self.name = None
        self.description = None
        self.services = []
        self.__components = []
        self._componentInstances = {}
        self._comp_inst_prom_attr = {}
        self._comp_inst_env_attr = {}
        self._amfComponentInstances = {}
        self._componentTypes = set()
        self._externalComponentTypes = set()
        self.monitorPeriod = "2000 ms"
        self.maxFailureNr = 2

        self._saAmfSgtDefCompRestartMax = self.monitorPeriod
        self._saAmfSgtDefSuRestartMax = self.monitorPeriod

        self._saAmfSgtDefCompRestartProb = self.maxFailureNr
        self._saAmfSgtDefSuRestartProb = self.maxFailureNr

        self._saAmfSutDefSUFailover = 'SA_FALSE'     #SA_TRUE if anyone of the included components
                                                    #have saAmfCtDefDisableRestart=SA_TRUE else SA_FALSE

        self._saAmfSgtDefAutoRepair = 'SA_TRUE'    #will not be set or modified by TCG, default behavior used
        self._saAmfSgtDefAutoAdjust = 'SA_FALSE'   #will not be set or modified by TCG, default behavior used
        self._saAmfSgtDefAutoAdjustProb = 10000000 #default used

        '''
        TO BE SUPPORTED IN CSM 0.9b
        component-promotion-dependency (optional; cardinality=(0..*))
        service-promotion-dependency (optional; cardinality=(0..*))

        component-promotion-dependency:                       # O
         - from-component:       <from_component_id>          # M
           to-component:         <to_component_id>            # M

        service-promotion-dependency:                         # O
         - depends-on:           <dependent_service_id>       # M
           tolerance-timeout:    <outage_tolerance_timeout>   # O
        '''
        self.redundancyModel = None
        self.maxPromotions = None
        self.amfManagedComponents = []
        self.version = CSMEntityVersion()
        self._meta_data = None
        self.dependsOnServices = []
        self.sourceFile = None
        self._compInsLevel = Prioritize()  # generate from compPromoDependency
        self._componentInstPromDeps = []
        self._input_yaml_dict = None

        self._roles = []
        self._updated_component_instances = {}
        # self._md5ForSGVersion = None

    def __contains__(self, item):
        """
        Return True if the inputed item instance is in Service.
        """
        uid = None
        if type(item) is str:
            # string will be consider as component UID
            uid = item
        elif type(item) is Component:
            uid = item.getUid()
        if uid:
            for comp in self._componentTypes:
                if comp.getUid() == uid:
                    return True
        return False

    def __eq__(self, other):
        if type(other) is not Service:
            return False
        return self._input_yaml_dict == other._input_yaml_dict

    def setValues(self, name=None, version=None, uid=None, description=None,
                 category=None, dependsOnServices=[],
                 components=[],
                 services=[],
                 monitorPeriod="2000 ms",
                 maxFailureNr=2,
                 redundancyModel=None,
                 maxPromotions=None,
                 serviceVersion=None,
                 servicesMetaData=None,
                 plugin=None,
                 componentInstanceConfigList=[],
                 sourceFile=None,
                 pluginsBaseDir=None,
                 input_yaml_dict = None):
        ''' Sets values for a Service '''

        self.setName(name)
        self.setVersion(version, uid)
        self.setUid(uid)
        self.setDescription(description)
        self.setServices(services)
        self.__setComponents(components)
        self.setMonitorPeriod(monitorPeriod)
        self.setMaxFailureNr(maxFailureNr)
        self.setPlugin(plugin)
        self.setMetaData(servicesMetaData, uid)

        self.setCategory(category)
        self.setRedundancyModel(redundancyModel)
        self.setMaxPromotions(maxPromotions)

        self.setDependsOnServices(dependsOnServices)
        # self.setIncludedComponents(includedComponents)
        self.setSaAmfSutDefSUFailover()
        self.setSourceFile(sourceFile)
        self.setPluginsBaseDir(pluginsBaseDir)

        ''' List of service type/instance parameters (given values in the service context) '''

        self.componentInstanceConfig = componentInstanceConfigList
        '''
        List of component instance or csi attributes parameters (given values in the service context).
        These refer to csi attributes
        '''
        self.set_input_yaml(input_yaml_dict)

    def getName(self) :
        return self.name

    def getUid(self):
        return self.uid

    def getVersion(self) :
        return self.version.getVersionString()

    def getVersionObject(self):
        return self.version

    def getCategory(self) :
        return self.category

    def getDescription(self) :
        return self.description

    def getRedundancyModel(self) :
        return self.redundancyModel

    def getMaxPromotions(self) :
        return self.maxPromotions

    def getComponentInstances(self):
        return self._componentInstances

    def getAmfComponentInstances(self):
        return self._amfComponentInstances

    def getComponentTypes(self):
        return self._componentTypes

    def getExternalComponentTypes(self):
        return self._externalComponentTypes

    def getComponentType(self, component_instance_name):
        return self._componentInstances[component_instance_name]

    def getComponentTypesUid(self):
        uids = []
        for comp in self.__components:
            uids.append(comp[CgtConstants.SERVICE_COMPONENT_INSTANCES_OF_TAG])
        return uids

    def get_component_instance_prom_attrs(self, component_instance_name):
        if component_instance_name in self._comp_inst_prom_attr.keys():
            return self._comp_inst_prom_attr[component_instance_name]
        else:
            return {}

    def get_component_instance_env_attrs(self, component_instance_name):
        if component_instance_name in self._comp_inst_env_attr.keys():
            return self._comp_inst_env_attr[component_instance_name]
        else:
            return {}

    def getSaAmfSgtDefAutoRepair(self):
        return self._saAmfSgtDefAutoRepair

    def getSaAmfSgtDefAutoAdjust(self):
        return self._saAmfSgtDefAutoAdjust

    def getSaAmfSgtDefAutoAdjustProb(self):
        return self._saAmfSgtDefAutoAdjustProb

    def getServices(self):
        return self.services

    def get_roles(self):
        return self._roles

    def getMonitorPeriod(self) :
        return self.monitorPeriod

    def getMaxFailureNr(self) :
        return self.maxFailureNr

    def getMetaData(self) :
        return self._meta_data

    def getDependsOnServices(self):
        return self.dependsOnServices

    def getAmfManagedComponents(self) :
        return self.amfManagedComponents

    def getNonAmfManagedComponents(self) :
        return self.nonAmfManagedComponents

    def getPlugin(self) :
        return self.plugin

    def getSourceFile(self) :
        return self.sourceFile

    def getSourceFileLocation(self):
        if self.sourceFile:
            return os.path.abspath(os.path.join(self.sourceFile, os.pardir))

    '''
    def getMD5ForSGVersion(self):
        #Used to generate the safversion of the sgtype dn
        if not self._md5ForSGVersion :
            redundancyModelNumber = AMFConstants.getRedundancyModelNumber(self.redundancyModel)
            sgVersionStr = self.uid + redundancyModelNumber  #Specified in CSM 0.9 specification
            sgVersionMD5 = hashlib.md5()
            sgVersionMD5.update(sgVersionStr)
            self._md5ForSGVersion = sgVersionMD5.hexdigest()

        return self._md5ForSGVersion
    '''

    def setSourceFile(self, sourceFile=None) :
        self.sourceFile = sourceFile

    def setPluginsBaseDir(self, pluginsBaseDir):
        self.pluginsBaseDir = pluginsBaseDir

    def getPluginsBaseDir(self):
        if self.pluginsBaseDir:
            return self.pluginsBaseDir
        else:
            return self.getSourceFileLocation()

    def setPlugin(self, plugin=None) :
        self.plugin = plugin

    def setAmfManagedComponents(self, amfManagedComponents=[]) :
        self.amfManagedComponents = amfManagedComponents

    def setNonAmfManagedComponents(self, nonAmfManagedComponents=[]) :
        self.nonAmfManagedComponents = nonAmfManagedComponents

    def setDependsOnServices(self, dependsOnServices=[]):
        for dep in dependsOnServices :
            promotionDepInstance = PromotionDependency()
            promotionDepInstance.set(dep)
            self.dependsOnServices.append(promotionDepInstance)

    def __setComponents(self, components=[]):
        self.__components = components

    def convertComponentsRawData(self, components):
        promotion_order = set([])
        for comp in self.__components:
            instance_name = comp[CgtConstants.SERVICE_COMPONENT_NAME_TAG]
            if instance_name in self._componentInstances:
                logging.error("Component instance name [%s] have to be unique in service." % instance_name)
                continue
            instance_type = comp[CgtConstants.SERVICE_COMPONENT_INSTANCES_OF_TAG]
            component_type = None
            for compType in components:
                if compType.getUid() == instance_type:
                    component_type = compType
                    break
            if not component_type:
                tcg_error("Component type %s for instance %s not found! Aborting." % (instance_type, instance_name))
            self._componentInstances[instance_name] = component_type
            self._componentTypes.add(component_type)

            if CgtConstants.SERVICE_COMPONENT_INSTANCE_ATTRIBUTE in comp:
                comp_inst_attr_dict = comp[CgtConstants.SERVICE_COMPONENT_INSTANCE_ATTRIBUTE]
                promotion_attr_names = [attr.get_name() for attr in component_type.get_promotion_attributes()]
                environment_attr_names = [attr.get_name() for attr in component_type.get_environment_attributes()]

                for attr_name in comp_inst_attr_dict.iterkeys():
                    if (attr_name in promotion_attr_names):
                        if (instance_name not in self._comp_inst_prom_attr):
                            self._comp_inst_prom_attr[instance_name] = {}
                        self._comp_inst_prom_attr[instance_name][attr_name] = comp_inst_attr_dict[attr_name]
                    elif (attr_name in environment_attr_names):
                        if (instance_name not in self._comp_inst_env_attr):
                            self._comp_inst_env_attr[instance_name] = {}
                        self._comp_inst_env_attr[instance_name][attr_name] = comp_inst_attr_dict[attr_name]
                    else:
                        tcg_error("Attribute {the_attr} defined in component instance {the_inst} in service {the_sv} "
                                  "is not defined in the corresponding component type".format(the_attr=attr_name,
                                                                                              the_inst=instance_name,
                                                                                              the_sv=self.uid))

            if AMFTools.isCategoryAMFRelated(component_type.getType()):
                self._amfComponentInstances[instance_name] = component_type
            if "promotion-order" in comp:
                order = comp["promotion-order"]
                if CgtConstants.SERVICE_COMPONENT_PROMOTION_AFTER_TAG in order:
                    if type(order[CgtConstants.SERVICE_COMPONENT_PROMOTION_AFTER_TAG]) != list:
                        tcg_error("promotion-order constraint 'after:' in component instance {the_inst} in service {the_sv} "
                                  "is in format {the_format}, it should be <type \'list\'> - check CSM model".format(the_inst=instance_name,the_sv=self.uid,
                                                                                                              the_format = type(order[CgtConstants.SERVICE_COMPONENT_PROMOTION_AFTER_TAG])))
                    for depends_on in order[CgtConstants.SERVICE_COMPONENT_PROMOTION_AFTER_TAG]:
                        promotion_order.add((instance_name, depends_on))
                if CgtConstants.SERVICE_COMPONENT_PROMOTION_BEFORE_TAG in order:
                    if type(order[CgtConstants.SERVICE_COMPONENT_PROMOTION_BEFORE_TAG]) != list:
                        tcg_error("promotion-order constraint 'before:' in component instance {the_inst} in service {the_sv} "
                                  "is in format {the_format}, it should be <type \'list\'> - check CSM model".format(the_inst=instance_name,the_sv=self.uid,
                                                                                                              the_format = type(order[CgtConstants.SERVICE_COMPONENT_PROMOTION_BEFORE_TAG])))

                    for be_depends_on in order[CgtConstants.SERVICE_COMPONENT_PROMOTION_BEFORE_TAG]:
                        promotion_order.add((be_depends_on, instance_name))
            # TODO: saAmfCSIDependencies will also get from this promotion-order
            # TODO: set attributes is needed here
        if not self._compInsLevel.convertFrom(promotion_order):
            logging.warning("{0} in Service is wrong.".format(
                CgtConstants.SERVICE_COMPONENT_PROMOTION_ORDER_TAG))
            self._compInsLevel.reset()
        self._componentInstPromDeps = promotion_order

    def filterExternalComponents(self, ext_components):
        filtered_comp_instances = []

        for (comp_inst_name, comp_inst) in self._componentInstances.items():
            if comp_inst in ext_components:
                filtered_comp_instances.append(comp_inst_name)

        for comp_inst_name in filtered_comp_instances:
            component_type = self._componentInstances[comp_inst_name]
            self._componentTypes.remove(component_type)
            self._externalComponentTypes.add(component_type)
            del self._componentInstances[comp_inst_name]
            if comp_inst_name in self._comp_inst_prom_attr:
                del self._comp_inst_prom_attr[comp_inst_name]
            if comp_inst_name in self._comp_inst_env_attr:
                del self._comp_inst_env_attr[comp_inst_name]
            if comp_inst_name in self._amfComponentInstances:
                del self._amfComponentInstances[comp_inst_name]
            if self._meta_data:
                self._meta_data.removeComponent(component_type.getUid())

        if not self._componentInstances:
            return True

        return False

    def is_container(self):
        if not self._componentInstances:
            return True
        return False

    def setServices(self, services=[]):
        self.services = services[:]

    def set_roles(self, roles=[]):
        self._roles = roles[:]


    def setMetaData(self, servicesMetaData, uid):
        try:
            self._meta_data = meta_data.ServicesMetaData(servicesMetaData)
        except ValueError as e:
            logging.debug("Service: %s: %s" %(uid, e))

    def setMonitorPeriod(self, monitorPeriod) :
        monitorPeriod = convert_s_and_ms_to_number(monitorPeriod)
        self.monitorPeriod = monitorPeriod

        self._saAmfSgtDefCompRestartProb = self.monitorPeriod
        self._saAmfSgtDefSuRestartProb = self.monitorPeriod

    def setMaxFailureNr(self, maxFailureNr) :
        maxFailureNr = validate_is_number(maxFailureNr)
        self.maxFailureNr = maxFailureNr

        self._saAmfSgtDefCompRestartMax = self.maxFailureNr
        self._saAmfSgtDefSuRestartMax = self.maxFailureNr


    def setName(self, name=None) :
        self.name = name

    def setUid(self, uid=None):
        self.uid = uid

    def setVersion(self, version, owner_uid) :
        self.version.setVersion(version, owner_uid)

    def setCategory(self, category=None) :
        self.category = category

    def setDescription(self, description=None) :
        self.description = description

    def setRedundancyModel(self, redundancyModel=None) :
        if redundancyModel==None:
            self.redundancyModel = redundancyModel
        elif redundancyModel.upper() in AMFConstants.VALID_REDUNDANCY_MODEL_NAME:
            self.redundancyModel = redundancyModel
        else:
            tcg_error('{rm} is not a valid value for constraints:availability:redundancy-model in service {uid}'.format(rm=redundancyModel, uid=self.uid))

    def setMaxPromotions(self, maxPromotions):
        if maxPromotions is not None:
            self.maxPromotions = maxPromotions
            # The max-promotions attribute is only valid if the NWA redundancy model is used.
            # As of CSM schema 1.0 services->constraints->availability->redundancy-model can ONLY take the NR value in the CSM model.
            # The redundancy model is determined by TCG based on components: availability-properties: lifecycle-control attributes
            # When we consume this variable in CampaignGenerator TCG had already determined the redundancy model and will only consume
            # the variable if the redundancy-model is NWA.
            logging.debug("services->constraints->availability->max-promotions ({maxProm}) value will only be consumed if the determined redundancy-model is NWA".format(maxProm=maxPromotions))

    '''
    def setIncludedComponents(self, includedComponents = []) :
        self.includedComponents = includedComponents
    '''

    def setSaAmfSutDefSUFailover(self, saAmfSutDefSUFailover='SA_FALSE'):
        '''
        This value is set based on the included components' saAmfCtDefDisableRestart value
        If all of them are SA_FALSE, it is set to SA_TRUE if anyone of them is SA_TRUE
        '''
        self._saAmfSutDefSUFailover = saAmfSutDefSUFailover

    def set_input_yaml(self, input_yaml_dict):
            self._input_yaml_dict = input_yaml_dict
            CSMUnit.sort_yaml_dict(self._input_yaml_dict)

    def getCompInstantiationLevel(self, component_instance_name):
        return self._compInsLevel.getPrioritizeLevel(component_instance_name)

    def getComponentInstPromDeps(self):
        return self._componentInstPromDeps

    def getSaAmfSutDefSUFailover(self) :
        return self._saAmfSutDefSUFailover

    def get_input_yaml_dict(self):
        return self._input_yaml_dict

    def getAnyComponentInstance(self, comp_uid):
        """
        Return component_instance_name for the given comp_uid
        If comp_uid have multiple instance, it will randomly
        return one of the instances
        """
        for ins, typ in self._componentInstances.items():
            if typ.getUid() == comp_uid:
                return ins

    def validate(self):
        '''
        Does the schema validation and other conditional checks related to CSM
        '''
        #Check if the included components can colocate together, refer TABLE 2 in the CSM 0.9 wiki page

    def display(self):
        attrs = vars(self)
        print attrs.items()

    def upgrade_availability_check(self, base):
        # Only UID is not CAU in Service, no need to check
        return True

    def service_is_deletable(self):
        '''
        a service that contains only components that are deletable can be deleted
        '''
        for comp in self._componentTypes:
            if not comp.component_is_deletable():
                return False
        return True

    def check_for_upgrade(self, base_unit):
        '''
        service upgrade
        '''
        targetdep = self.dependsOnServices
        basedep = base_unit.dependsOnServices
        targetdeps = [i.getDependsOnService() for i in targetdep]
        basedeps = [i.getDependsOnService() for i in basedep]
        targettimeout = [i.getToleranceTimeout() for i in targetdep]
        basetimeout = [i.getToleranceTimeout() for i in basedep]


        base_comp_instances = base_unit._componentInstances

        # check for NON AMF MANAGED comps with an upgrade of the component uid
        for instname, csm_ct in [(instname,csm_ct) for (instname,csm_ct) in self._componentInstances.items() \
            if (csm_ct.getAvailabilityManager().upper() == CSMConstants.AVAILABILTY_MANAGER_NONE) \
            and (instname in base_comp_instances.keys())]:
                if csm_ct.getUid() != base_comp_instances[instname].getUid():
                    # the base and target service have a component with same instance name, but different uid.
                    # this is an allowed upgrade for comps with no availability manager.
                    self._updated_component_instances[instname] = tuple([csm_ct.getUid(), base_comp_instances[instname].getUid()])
                    logging.debug("Service component instance upgrade of uid (from %s to %s) of component instance %s in service %s:"\
                        % (base_comp_instances[instname].getUid(), csm_ct.getUid(), instname, self.getUid()))

       # check for change in component instance attributes
        if self._comp_inst_prom_attr != base_unit._comp_inst_prom_attr:
            for instname, valuedict in self._comp_inst_prom_attr.items():
                if instname not in base_unit._comp_inst_prom_attr.keys() or valuedict != base_unit._comp_inst_prom_attr[instname]:
                    self._updated_component_instances[instname] = None
            for instname, valuedict in base_unit._comp_inst_prom_attr.items():
                if instname not in self._comp_inst_prom_attr.keys() or valuedict != self._comp_inst_prom_attr[instname]:
                    self._updated_component_instances[instname] = None

        retvalue = False
        if basedeps != targetdeps or targettimeout != basetimeout:
            logging.debug("Service upgrade detected - promotion dependencies: %s:" %(self.getUid()))
            retvalue = True

        if self.maxPromotions != base_unit.maxPromotions:
            logging.debug("Service upgrade detected - constraint max-promotions: %s:" %(self.getUid()))
            retvalue = True

        if len(self.get_roles()) > len(base_unit.get_roles()):
            logging.debug("Service upgrade detected - the service is contained in more roles: %s:" %(self.getUid()))
            retvalue = True

        if self.maxFailureNr != base_unit.maxFailureNr:
            logging.debug("Service upgrade detected - max-failure-nr %s:" %(self.getUid()))
            retvalue = True

        if self.monitorPeriod != base_unit.monitorPeriod:
            logging.debug("Service upgrade detected - monitor-period %s:" %(self.getUid()))
            retvalue = True

        return retvalue

    def comp_inst_is_upgraded(self, instance_name, target_uid = None, base_uid = None):
        '''
        service upgrade
        '''
        if (target_uid == None and base_uid == None):
            return instance_name in self._updated_component_instances.keys()

        # check to see if there is an update of the uid for a comp
        for instname, uid_tuple in self._updated_component_instances.items():
            if uid_tuple is not None and instance_name == instname and uid_tuple[0] == target_uid and uid_tuple[1] == base_uid:
                return True
        return False

