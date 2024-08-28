import logging
import meta_data
from csm_unit import CSMUnit
import CSMConstants
import CgtConstants
from csm_entity_version import CSMEntityVersion


class RoleConstraints(CSMUnit):

    def __init__(self):
        self.is_set = False
        self.extended_role = None

    def set(self, inputDict):
        if inputDict:
            if (CgtConstants.ROLE_CONSTRAINTS_EXTEND_TAG in inputDict):
                self.extended_role = inputDict[CgtConstants.ROLE_CONSTRAINTS_EXTEND_TAG]

            self.is_set = True

    def getExtendedRole(self):
        return self.extended_role

    def isSet(self):
        return self.is_set


class Role(CSMUnit):
    '''
    CSM Role class
    '''

    def __init__(self):
        super(Role, self).__init__()
        self.raw_name = None
        self.raw_uid = None
        self.raw_description = ""
        self.raw_services = []
        self.raw_canScale = False
        self.raw_minNodes = None
        self.raw_weight = 0
        self.raw_rank = 0
        self.raw_external = False
        self.raw_version = None
        self.raw_meta_data = None
        self.raw_role_constraints = None

        self.name = None
        self.uid = None
        self.description = ""
        self.services = []
        self.externalServices = []  # Services containing only external components
        self.local_services = set()
        self.canScale = False
        self.minNodes = None
        self.weight = 0
        self.rank = 0
        self.external = False
        self.version = CSMEntityVersion()
        self._meta_data = None
        self.role_constraints = None
        self._input_yaml_dict = None

        self._extended_by = None
        self._extends_from = None

    def clone_raw(self):
        role_instance = Role()
        role_instance.raw_uid = self.raw_uid
        role_instance.raw_name = self.raw_name
        role_instance.raw_version = self.raw_version
        role_instance.raw_description = self.raw_description
        role_instance.raw_services = self.raw_services
        role_instance.raw_minNodes = self.raw_minNodes
        role_instance.raw_canScale = self.raw_canScale
        role_instance.raw_weight = self.raw_weight
        role_instance.raw_rank = self.raw_rank
        role_instance.raw_external = self.raw_external
        role_instance.raw_meta_data = self.raw_meta_data
        role_instance.raw_role_constraints = self.raw_role_constraints
        role_instance.set_input_yaml(self._input_yaml_dict)
        return role_instance

    def __eq__(self, other):
        if type(other) is not Role:
            return False
        return self._input_yaml_dict == other._input_yaml_dict

    def setValues(
            self,
            name=None,
            uid=None,
            services=[],
            localServices=[],
            description="",
            canScale=False,
            minNodes=None,
            weight=0,
            rank=1,
            external=False,
            version=None,
            rolesMetaData=None,
            roleConstraints={}):
        ''' Constructor of Role '''
        self.setName(name)
        self.setUid(uid)
        self.setDescription(description)
        self.setServices(services)
        self.setLocalServices(localServices)
        self.setCanScale(canScale)
        self.setMinNodes(minNodes)
        self.setWeight(weight)
        self.setRank(rank)
        self.setExternal(external)
        self.setVersion(version, uid)
        self.setMetaData(rolesMetaData, uid)
        self.setRoleConstraints(roleConstraints)

    def getName(self):
        return self.name

    def getUid(self):
        return self.uid

    def getDescription(self):
        return self.description

    def getServices(self):
        return self.services

    def getExternalServices(self):
        return self.externalServices

    def getLocalServices(self):
        return self.local_services

    def getLocalAssignedServices(self):
        return list(set(self.local_services) & set([sv.getUid() for sv in self.services]))

    def getComponents(self):
        components = set()
        for service in self.services:
            components.update(service.getComponentTypes())
        return components

    def getFullComponents(self):
        """
        Returns the csm native components plus the external components
        """
        components = set()
        for service in self.services:
            components.update(service.getComponentTypes())
            components.update(service.getExternalComponentTypes())

        for service in self.externalServices:
            components.update(service.getExternalComponentTypes())

        return components

    def getCanScale(self):
        return self.canScale

    def getMinNodes(self):
        return self.minNodes

    def getWeight(self):
        return self.weight

    def getRank(self):
        return self.rank

    def getMetaData(self):
        return self._meta_data

    def get_input_yaml_dict(self):
        return self._input_yaml_dict

    def isExternal(self):
        return self.external

    def getVersion(self):
        return self.version.getVersionString()

    def getVersionObject(self):
        return self.version

    def getRoleConstraints(self):
        return self.role_constraints

    def getExtendedBy(self):
        return self._extended_by

    def getExtendsFrom(self):
        return self._extends_from

    def setExternal(self, external):
        self.external = external

    def setVersion(self, version, owner_uid):
        self.version.setVersion(version, owner_uid)

    def setName(self, name=None):
        self.name = name

    def setUid(self, uid=None):
        self.uid = uid

    def setDescription(self, description=""):
        self.description = description

    def setServices(self, services=[]):
        self.services = list(services)

    def setLocalServices(self, services=set()):
        self.local_services = set(services)

    def setServiceInstances(self, svInstances, localServices=None):
        self.services = list(svInstances)
        self.__expandContainerServicesInInputYml(svInstances if localServices is None else localServices)

    def setCanScale(self, scaling):
        self.canScale = scaling

    def setMinNodes(self, minNodes=None):
        self.minNodes = minNodes

    def setWeight(self, weight=0):
        self.weight = weight

    def setRank(self, rank=0):
        self.rank = rank

    def setMetaData(self, rolesMetaData, uid):
        try:
            self._meta_data = meta_data.RolesMetaData(rolesMetaData)
        except ValueError as e:
            logging.debug("Role: %s: %s" %(uid, e))

    def setRoleConstraints(self, roleConstraints):
        self.role_constraints = RoleConstraints()
        self.role_constraints.set(roleConstraints)

    def set_input_yaml(self, input_yaml_dict):
        self._input_yaml_dict = input_yaml_dict
        CSMUnit.sort_yaml_dict(self._input_yaml_dict)

    def setExtendedBy(self, role):
        assert self._extended_by is None or self._extended_by == role
        self._extended_by = role

    def setExtendsFrom(self, role):
        assert self._extends_from is None or self._extends_from == role
        self._extends_from = role

    def validate(self):
        ''' validate function for CSM Role'''

    def display(self):
        attrs = vars(self)
        logging.debug(attrs.items())

    def filterExternalServices(self, filtered_services):
        contained_filtered_services = []

        for service in self.services:
            if service in filtered_services:
                contained_filtered_services.append(service)

        for service in contained_filtered_services:
            self.services.remove(service)
            self.externalServices.append(service)
            if self._meta_data:
                self._meta_data.removeService(service.getUid())

    def __expandContainerServicesInInputYml(self, svInstances):
        """
        The input yml contains the original service uids associated to the
        role. It could be core services or container services. On the other
        hand, the service instances of the role are expanded and the container
        services are replaced by the children core services. We need to adjust
        the input yml to have a consistent model
        """
        svUids = [sv.getUid() for sv in svInstances]
        self._input_yaml_dict[CgtConstants.ROLE_SERVICES_TAG] = sorted(svUids)

    def upgrade_availability_check(self, base):
        # cau_tags defind cau status for role attributes.
        # It not must to list an attribute if it is CAU and all
        # it's leafs are CAU.
        cau_tags = {
            'uid': (False, None, None),
            'name': (False, None, None),
            # 'services': (False, None) Question: service in roles is marked as CAM
            # Which means it's for migration and not able to change in upgrade
            # Is it correct?
            'services': (True, None, None)
        }
        base_yml = base.get_input_yaml_dict()
        return CSMUnit.yaml_upgrade_availability_check('roles', base_yml, self._input_yaml_dict, (True, None, cau_tags))


    def check_for_upgrade(self, base_unit):
        '''
        service upgrade
        '''
        if len(self.services) !=  len(base_unit.services):
            return True

        return False
