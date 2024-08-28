import logging
import meta_data

import tcg.CgtConstants as CgtConstants
from csm_unit import CSMUnit
from tcg.utils.logger_tcg import tcg_error
from csm_entity_version import CSMEntityVersion, VERSION_TYPE_DOTTED
from tcg import CSMConstants


class ComputeResource(CSMUnit):
    def __init__(self):
        self.name = None
        self.role = None

    def set(self, name, role):
        self.name = name
        self.role = role

    def getName(self):
        return self.name

    def getRole(self):
        return self.role


class SystemConstraints(CSMUnit):

    def __init__(self):
        self.upgrade_oldest_version = CSMEntityVersion()
        self.max_cluster_size = None
        self.is_set = False
        self.extended_system = None

    def set(self, inputDict, owner_uid):
        if inputDict:
            if (CgtConstants.SYSTEM_CONSTRAINTS_OLDEST_VERSION_TAG in inputDict):
                self.upgrade_oldest_version.setVersion(inputDict[CgtConstants.SYSTEM_CONSTRAINTS_OLDEST_VERSION_TAG], owner_uid, VERSION_TYPE_DOTTED)

            if (CgtConstants.SYSTEM_MAX_CLUSTER_SIZE_TAG in inputDict):
                self.max_cluster_size = inputDict[CgtConstants.SYSTEM_MAX_CLUSTER_SIZE_TAG]

            if (CgtConstants.SYSTEM_CONSTRAINTS_EXTEND_TAG in inputDict):
                self.extended_system = inputDict[CgtConstants.SYSTEM_CONSTRAINTS_EXTEND_TAG]

            self.is_set = True

    def getUpgradeOldestVersion(self):
        return self.upgrade_oldest_version

    def getMaxClusterSize(self):
        return self.max_cluster_size

    def getExtendedSystem(self):
        return self.extended_system

    def isSet(self):
        return self.is_set


class System(CSMUnit):
    '''
    CSM System class
    '''

    def __init__(self) :
        super(System, self).__init__()
        self.raw_uid = None
        self.raw_name = None
        self.raw_version = None
        self.raw_product_number = None
        self.raw_description = ""
        self.raw_functions = []
        self.raw_roles = []
        self.raw_system_constraints = None
        self.raw_meta_data = None

        self.uid = None
        self.name = None
        self.version = CSMEntityVersion()
        self.product_number = None
        self.description = ""
        self.functions = []
        self.services = []  # only csm native services (contain at least one non-external component)
        self.native_components = []
        self.native_plus_ext_components = []
        self.local_functions = set()
        self.roles = set()
        self.system_constraints = None
        self.computeResources = []

        self._meta_data = None

        self.roleToNodeMap = {}
        self.componentToNodeMap = {}
        self.systemComponentIds = []  # only csm native components
        self.fullSystemComponentIds = []  # csm native + external components
        self._input_yaml_dict = None
        self._hostname_amfnode_map = None
        self._isAccumulated = False
        self.role_allocations = None

    def clone_raw(self):
        systemInstance = System()
        systemInstance.raw_uid = self.raw_uid
        systemInstance.raw_name = self.raw_name
        systemInstance.raw_version = self.raw_version
        systemInstance.raw_product_number = self.raw_product_number
        systemInstance.raw_description = self.raw_description
        systemInstance.raw_functions = self.raw_functions
        systemInstance.raw_roles = self.raw_roles
        systemInstance.raw_system_constraints = self.raw_system_constraints
        systemInstance.raw_meta_data = self.raw_meta_data
        systemInstance.set_input_yaml(self._input_yaml_dict)
        return systemInstance

    def __eq__(self, other):
        if type(other) is not System:
            return False
        return self._input_yaml_dict == other._input_yaml_dict

    def setValues(
            self,
            hostname_amfnode_map,
            uid=None,
            name=None,
            version=None,
            product_number=None,
            description=None,
            functions=None,
            localFunctions=None,
            roles=[],
            system_constraints={},
            systemMetaData=None):
        ''' Constructor of System '''

        assert(hostname_amfnode_map is not None)
        self._hostname_amfnode_map = hostname_amfnode_map
        self.setUid(uid)
        self.setName(name)
        self.setVersion(version, uid)
        self.setProductNumber(product_number)
        self.setDescription(description)
        self.setFunctions(functions)
        self.setLocalFunctions(set(localFunctions))
        self.setRoles(roles)
        self.setSystemConstraints(system_constraints, uid)
        self.setMetaData(systemMetaData, uid)

    def getUid(self):
        return self.uid

    def getName(self):
        return self.name

    def getVersion(self):
        return self.version.getVersionString()

    def getVersionObject(self):
        return self.version

    def getProductNumber(self):
        return self.product_number

    def getDescription(self):
        return self.description

    def getFunctions(self):
        return self.functions

    def getServices(self):
        return self.services

    def getComponents(self):
        return self.native_components

    def getComponent(self, uid):
        for comp in self.native_components:
            if comp.getUid() == uid:
                return comp
        return None

    def getNonManagedComps(self):
        return self._getCompsByAvailMngr(CSMConstants.AVAILABILTY_MANAGER_NONE)

    def getCDSComps(self):
        return self._getCompsByAvailMngr(CSMConstants.AVAILABILTY_MANAGER_CDS)

    def _getCompsByAvailMngr(self, availabilty_manager):
        """
        returns the list of components with the received availability manager.
        """
        comps = []
        for comp in self.native_components:
            if comp.getAvailabilityManager().upper() == availabilty_manager:
                comps.append(comp)
        return comps

    def getRoles(self):
        return self.roles

    def getRoleAllocations(self):
        return self.role_allocations

    def getSystemConstraints(self):
        return self.system_constraints

    def getComputeResources(self):
        return self.computeResources

    def setComputeResources(self, computers):
        self.computeResources = computers

        # The new compute resourses invalidate the previously calculated role
        # to node map and services/components to node map
        self._recalculate_role_to_node_map()
        self.setServicesCompsToNodesMap()

    def getMetaData(self):
        return self._meta_data

    def getRolesToComputeResourcesMap(self):
        return self.roleToNodeMap

    def getComponentsToComputeResourcesMap(self):
        return self.componentToNodeMap

    def get_input_yaml_dict(self):
        return self._input_yaml_dict

    def isAccumulated(self):
        return self._isAccumulated

    def getLocalFunctions(self):
        return self.local_functions

    def setUid(self, uid=None):
        self.uid = uid

    def setName(self, name=None):
        self.name = name

    def setVersion(self, version=None, owner_uid=None):
        self.version.setVersion(version, owner_uid, VERSION_TYPE_DOTTED)

    def setProductNumber(self, product_number=None):
        self.product_number = product_number

    def setDescription(self, description=None):
        self.description = description

    def setFunctions(self, functions=None):
        self.functions = list(functions)

    def setFunctionInstances(self, ftInstances, localInstances=None):
        self.functions = list(ftInstances)
        self.__expandContainerFunctionsInInputYml(ftInstances if localInstances is None else localInstances)

    def setSystemConstraints(self, system_constraints, owner_uid):
        self.system_constraints = SystemConstraints()
        self.system_constraints.set(system_constraints, owner_uid)

    def setSystemServicesAndComponents(self):
        nativeServices = set()
        nativeComponents = set()
        externalServices = set()
        externalComponents = set()

        # Deployment service according to roles.
        # Partial service allocation will be done in validate
        for role in self.roles:
            nativeServices.update(role.getServices())
            externalServices.update(role.getExternalServices())

        for serv in nativeServices:
            nativeComponents.update(serv.getComponentTypes())
            # a native service could have external components also
            externalComponents.update(serv.getExternalComponentTypes())

        for serv in externalServices:
            externalComponents.update(serv.getExternalComponentTypes())

        self.services = list(nativeServices)
        self.native_components = list(nativeComponents)

        self.native_plus_ext_components = list(nativeComponents)
        self.native_plus_ext_components.extend(externalComponents)

        for component in self.native_components:
            self.systemComponentIds.append(component.getUid())

        for component in self.native_plus_ext_components:
            self.fullSystemComponentIds.append(component.getUid())

    def updateRoleInstance(self, role_role_instances):
        self.roles = role_role_instances

    def setRoles(self, roles=[]):
        self.role_allocations = roles
        self.roles = set(role['role'] for role in roles)

    def processRoles(self, role_map):
        roles = self.role_allocations
        self.roles = set()
        all_computer_resources = set()
        for allocation in roles:
            if CgtConstants.SYSTEM_ROLE_TAG not in allocation:
                tcg_error("Miss %s tag under system.roles" % CgtConstants.SYSTEM_ROLE_TAG)
            role = allocation[CgtConstants.SYSTEM_ROLE_TAG]
            if role_map[role].getExtendsFrom() is not None:
                continue
            if CgtConstants.SYSTEM_ROLE_ASSIGN_TO_TAG not in allocation:
                tcg_error("Miss %s tag under system.roles" % CgtConstants.SYSTEM_ROLE_ASSIGN_TO_TAG)
            assign_to = allocation[CgtConstants.SYSTEM_ROLE_ASSIGN_TO_TAG]
            assigned_amf_nodes = map(lambda x: self.__get_amfnode_from_hostname(x), assign_to)
            assert (len(assign_to) == len(assigned_amf_nodes))
            computer_resources = set(assigned_amf_nodes)
            if len(computer_resources) == 0:
                tcg_error("Role %s not assign to any computer resource." % role)
            if len(computer_resources) != len(assigned_amf_nodes):
                # Most possibly, there are duplicate computer resources for same role in assign_to
                tcg_error("Role %s have duplicate computer resource." % role)
            all_computer_resources.update(computer_resources)
            self.roles.add(role)
            for computer in computer_resources:
                computeResourceInstance = ComputeResource()
                computeResourceInstance.set(computer, role)
                self.computeResources.append(computeResourceInstance)
            self.roleToNodeMap[role] = computer_resources

    def setMetaData(self, systemMetaData, uid):
        try:
            self._meta_data = meta_data.SystemMetaData(systemMetaData)
        except ValueError as e:
            logging.debug("System: %s: %s" %(uid, e))

    def setServicesCompsToNodesMap(self):
        self.componentToNodeMap = dict.fromkeys(self.fullSystemComponentIds, [])

        for role in self.roles :
            full_services = list(role.getServices())
            full_services.extend(role.getExternalServices())
            for service in full_services:
                full_comp_types = service.getComponentTypes()
                full_comp_types.update(service.getExternalComponentTypes())
                for component in full_comp_types:
                    self.componentToNodeMap[component.getUid()] = list(set(self.componentToNodeMap[component.getUid()]) |
                                                                                self.roleToNodeMap[role.getUid()])

    def set_input_yaml(self, input_yaml_dict):
        self._input_yaml_dict = input_yaml_dict
        CSMUnit.sort_yaml_dict(self._input_yaml_dict)

    def setAccumulated(self, val):
        self._isAccumulated = val

    def setLocalFunctions(self, local_functions):
        self.local_functions = set(local_functions)

    def validate(self):
        ''' validate function for CSM System'''
        if not self.computeResources :
            tcg_error("There is no compute resource defined for the System Model. \
                                    \n Hint: There is no compute-resources \
                                    (node to role mapping) present under system tag")

        # Check if all the services that are part of the system are also part of the roles included
        missingServices = []

        if self.functions :
            for function in self.functions :
                for service in function.getServices() :
                    servicePresentFlag = False
                    for roleServ in self.services:
                        # self.services contains only the services from the roles
                        if service.getUid() == roleServ.getUid() :
                            servicePresentFlag = True
                            break
                    if not servicePresentFlag:
                        missingServices.append(service.getUid())

            if missingServices :
                if (len(missingServices) == 1):
                    tcg_error("Service '%s' is defined in the System functions but is not allocated to any of the system roles." % missingServices[0])
                else:
                    missingServices = sorted(missingServices)  # sorting makes the message deterministic
                    tcg_error("Services '%s' are defined in the System functions but are not allocated to any of the system roles." % (', '.join(missingServices)))

        '''
        Check the components which are dependent are also part of the System
        '''
        componentsToDepCompsMap = {}  # contains a map of the component to dependent components which are not present in the System
        for component in self.native_plus_ext_components:
            depCompsNotPresent = []
            for depComp in component.getDependsOnComponents():
                if depComp not in self.fullSystemComponentIds:
                    depCompsNotPresent.append(depComp)

            if depCompsNotPresent:
                componentsToDepCompsMap.update({component.getUid(): depCompsNotPresent})

        if componentsToDepCompsMap.keys():
            errorInfo = ""
            for key, value in componentsToDepCompsMap.iteritems() :
                errorInfo += 'Component %s depends on these components %s which are not part of the System' % (key, value)
                errorInfo += "\n"

            tcg_error("All the components dependencies are not satisfied.\n%s" % errorInfo)

        '''
        Check the components which are dependent are also part of the same compute resources or not
        '''
        for component in self.native_plus_ext_components:
            for depComp in component.getDependsOnComponents() :
                if not set(self.getComponentsToComputeResourcesMap()[component.getUid()]).issubset(
                                                            set(self.getComponentsToComputeResourcesMap()[depComp])) :
                    logging.warning("Component %s is allocated to compute resources %s whereas the component %s it depends on is allocated to %s.\
                    The dependent components should be present on the same node set"
                          % (component.getUid(), self.getComponentsToComputeResourcesMap()[component.getUid()], depComp,
                                              self.getComponentsToComputeResourcesMap()[depComp]))
        return

    def copy_site_dependent_info(self, other_system):
        """
        This method copies the site dependent information from the received
        system into this system.
        Site dependent information is the one related to the size of the
        particular cluster where the system is running
        """
        self.setComputeResources(other_system.getComputeResources())
        self._copy_role_to_compute_resource_allocation(other_system.get_input_yaml_dict())

    def _copy_role_to_compute_resource_allocation(self, other_yaml_dict):
        roles = self._input_yaml_dict[CgtConstants.SYSTEM_ROLES_TAG]
        other_roles = other_yaml_dict[CgtConstants.SYSTEM_ROLES_TAG]
        for role in roles:
            self._copy_cr_allocation(role, other_roles)

    def _copy_cr_allocation(self, role, other_roles):
        role_id = role[CgtConstants.SYSTEM_ROLE_TAG]
        for other_role in other_roles:
            other_role_id = other_role[CgtConstants.SYSTEM_ROLE_TAG]
            if role_id == other_role_id:
                if CgtConstants.SYSTEM_ROLE_ASSIGN_TO_TAG in other_role:
                    role[CgtConstants.SYSTEM_ROLE_ASSIGN_TO_TAG] = other_role[CgtConstants.SYSTEM_ROLE_ASSIGN_TO_TAG]
                break

    def _recalculate_role_to_node_map(self):
        self.roleToNodeMap.clear()
        for cr in self.computeResources:
            role = cr.getRole()
            if (role not in self.roleToNodeMap):
                self.roleToNodeMap[role] = set()
            self.roleToNodeMap[role].add(cr.getName())

    def __expandContainerFunctionsInInputYml(self, ftInstances):
        """
        The input yml contains the original function uids associated to the
        system. It could be core functions or container functions. On the other
        hand, the function instances of the system are expanded and the
        container functions are replaced by the children core functions. We
        need to adjust the input yml to have a consistent model
        """
        ftUids = [ft.getUid() for ft in ftInstances]
        self._input_yaml_dict[CgtConstants.SYSTEM_FUNCTIONS_TAG] = sorted(ftUids)

    def __get_amfnode_from_hostname(self, hostname):
        if self._hostname_amfnode_map == {}:
            return hostname
        elif hostname in self._hostname_amfnode_map:
            return self._hostname_amfnode_map[hostname]
        else:
            tcg_error("Unknown hostname {0}. Possible root cause is that "
                      "the computer resource {0} specified in the CSM model "
                      "is not a host in the cluster".format(hostname))
