import logging
from csm_unit import CSMUnit
import meta_data
import CgtConstants
from csm_entity_version import CSMEntityVersion

class Function(CSMUnit):
    '''
    CSM Composition class
    '''

    def __init__(self) :
        super(Function, self).__init__()
        self.name = None
        self.uid = None
        self.version = CSMEntityVersion()
        self.description = ""
        self.services = []
        self.externalServices = []  # Services containing only external components
        self.functions = []
        self._meta_data = None
        self._input_yaml_dict = None

    def __eq__(self, other):
        if type(other) is not Function:
            return False
        return self._input_yaml_dict == other._input_yaml_dict

    def setValues(
            self,
            name = None,
            uid = None,
            version = None,
            description = None,
            services = [],
            functions = [],
            functionsMetaData = None,
            input_yaml_dict = None):
        ''' Constructor of Composition '''
        self.setName(name)
        self.setUid(uid)
        self.setVersion(version, uid)
        self.setDescription(description)
        self.setServices(services)
        self.setFunctions(functions)
        self.setMetaData(functionsMetaData, uid)
        self.set_input_yaml(input_yaml_dict)
        ''' List of services included in the Composition '''

    def getName(self) :
        return self.name

    def getVersion(self) :
        return self.version.getVersionString()

    def getVersionObject(self):
        return self.version

    def getUid(self):
        return self.uid

    def getDescription(self) :
        return self.description

    def getServices(self) :
        return self.services

    def getFunctions(self):
        return self.functions

    def getMetaData(self) :
        return self._meta_data

    def get_input_yaml_dict(self):
        return self._input_yaml_dict

    def setName(self, name = None) :
        self.name = name

    def setVersion(self, version, owner_uid) :
        self.version.setVersion(version, owner_uid)

    def setUid(self, uid = None):
        self.uid = uid

    def setDescription(self, description = "") :
        self.description = description

    def setServices(self, services = []) :
        self.services = list(services)

    def setServiceInstances(self, svInstances):
        self.services = list(svInstances)
        self.__expandContainerServicesInInputYml(svInstances)

    def setFunctions(self, functions = []):
        self.functions = functions

    def setMetaData(self, functionsMetaData, uid):
        try:
            self._meta_data = meta_data.FunctionsMetaData(functionsMetaData)
        except ValueError as e:
            logging.debug("Function: %s: %s" %(uid, e))

    def set_input_yaml(self, input_yaml_dict):
        self._input_yaml_dict = input_yaml_dict
        CSMUnit.sort_yaml_dict(self._input_yaml_dict)

    def validate(self):
       ''' validate function for CSM Composition'''

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
        function. It could be core services or container services. On the other
        hand, the service instances of the function are expanded and the
        container services are replaced by the children core services. We need
        to adjust the input yml to have a consistent model
        """
        svUids = [sv.getUid() for sv in svInstances]
        self._input_yaml_dict[CgtConstants.FUNCTION_SERVICES_TAG] = sorted(svUids)
