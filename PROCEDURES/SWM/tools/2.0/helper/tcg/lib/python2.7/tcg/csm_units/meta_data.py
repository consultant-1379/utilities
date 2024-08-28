import CgtConstants


class MetaData(object):
    def _which_metadata(self):
        return 'BASE'

    def _check_metadata_not_none(self, metadata):
        if metadata is None:
            raise ValueError("meta-data not exist in %s." % self._which_metadata())

    def _check_value_exist(self, dictionary, tag):
        if tag not in dictionary:
            raise ValueError("%s not exist in %s." % (tag, self._which_metadata()))

    def _check_dict_type(self, dictionary):
        if type(dictionary) is not dict:
            raise ValueError("meta-data type error in %s." % self._which_metadata())

    def _check_list_type(self, dictionary):
        if type(dictionary) is not list:
            raise ValueError("meta-data type error in %s." % self._which_metadata())


class ComponentsMetaData(MetaData):
    def __init__(self, metadata):
        self._check_metadata_not_none(metadata)
        self._check_dict_type(metadata)

        self._check_value_exist(metadata, CgtConstants.META_COMPONENT_VERSION_TAG)
        self.__component_version = metadata[CgtConstants.META_COMPONENT_VERSION_TAG]

        self._check_value_exist(metadata, CgtConstants.META_DELIVERABLE_TAG)
        self.__deliverable = metadata[CgtConstants.META_DELIVERABLE_TAG]
        self._check_dict_type(self.__deliverable)
        self._check_value_exist(self.__deliverable, CgtConstants.META_DEPLOYMENT_PACKAGE_TAG)
        self._check_value_exist(self.__deliverable, CgtConstants.META_RUNTIME_PACKAGE_TAG)

        if CgtConstants.META_SOFTWARE_TAG in metadata:
            self.__software = metadata[CgtConstants.META_SOFTWARE_TAG]
            self._check_list_type(self.__software)
            for sw in self.__software:
                self._check_dict_type(sw)
                self._check_value_exist(sw, CgtConstants.META_FILE_NAME_TAG)
                self._check_value_exist(sw, CgtConstants.META_BUNDLE_NAME_TAG)
        else:
            self.__software = []

    def _which_metadata(self):
        return 'components meta-data'

    def getComponentVersion(self):
        return self.__component_version

    def getDeploymentPackage(self):
        return self.__deliverable[CgtConstants.META_DEPLOYMENT_PACKAGE_TAG]

    def getRuntimePackage(self):
        return self.__deliverable[CgtConstants.META_RUNTIME_PACKAGE_TAG]

    def getSoftwares(self):
        """
        Return all softwares, but the better way is use traversal 'softwares'
        """
        return self.__software

    def updateSoftware(self, filename, bundle):
        for sw in self.__software:
            if filename == sw[CgtConstants.META_FILE_NAME_TAG]:
                sw[CgtConstants.META_BUNDLE_NAME_TAG] = bundle
                break

    def softwares(self):
        """Generator for traversal software in component meta-data"""
        for sw in self.__software:
            filename = sw[CgtConstants.META_FILE_NAME_TAG]
            bundle = sw[CgtConstants.META_BUNDLE_NAME_TAG]
            yield filename, bundle

    # def getSoftwareFilename(self):
    #     return self.__software[CgtConstants.META_FILE_NAME_TAG]

    # def getSoftwareBundleName(self):
    #     return self.__software[CgtConstants.META_BUNDLE_NAME_TAG]


class ServicesMetaData(MetaData):
    def __init__(self, metadata):
        self._check_metadata_not_none(metadata)
        self._check_dict_type(metadata)

        self._check_value_exist(metadata, CgtConstants.META_SERVICE_VERSION_TAG)
        self.__service_version = metadata[CgtConstants.META_SERVICE_VERSION_TAG]

        self.__components = []
        if CgtConstants.META_COMPONENTS_TAG in metadata:
            self.__components = metadata[CgtConstants.META_COMPONENTS_TAG]
            self._check_list_type(self.__components)
            for comp in self.__components:
                self._check_dict_type(comp)
                self._check_value_exist(comp, CgtConstants.META_COMPONENT_TAG)
                self._check_value_exist(comp, CgtConstants.META_VERSION_TAG)

        self.__services = []
        if CgtConstants.META_SERVICES_TAG in metadata:
            self.__services = metadata[CgtConstants.META_SERVICES_TAG]
            self._check_list_type(self.__services)
            for serv in self.__services:
                self._check_dict_type(serv)
                self._check_value_exist(serv, CgtConstants.META_SERVICE_TAG)
                self._check_value_exist(serv, CgtConstants.META_VERSION_TAG)

    def _which_metadata(self):
        return 'services meta-data'

    def getServiceVersion(self):
        return self.__service_version

    def num_of_components(self):
        return len(self.__components)

    def components(self):
        """Generator for traversal components in services meta-data"""
        for comp in self.__components:
            component = comp[CgtConstants.META_COMPONENT_TAG]
            version = comp[CgtConstants.META_VERSION_TAG]
            yield component, version

    def removeComponent(self, comp_id):
        components_to_remove = []
        for comp in self.__components:
            if comp[CgtConstants.META_COMPONENT_TAG] == comp_id:
                components_to_remove.append(comp)

        for comp in components_to_remove:
            self.__components.remove(comp)

    def num_of_services(self):
        return len(self.__services)

    def services(self):
        """Generator for traversal services in services meta-data"""
        for serv in self.__services:
            service = serv[CgtConstants.META_SERVICE_TAG]
            version = serv[CgtConstants.META_VERSION_TAG]
            yield service, version

    def removeService(self, serv_id):
        services_to_remove = []
        for serv in self.__services:
            if serv[CgtConstants.META_SERVICE_TAG] == serv_id:
                services_to_remove.append(serv)

        for serv in services_to_remove:
            self.__services.remove(serv)


class FunctionsMetaData(MetaData):
    def __init__(self, metadata):
        self._check_metadata_not_none(metadata)
        self._check_dict_type(metadata)

        self.__services = []
        if CgtConstants.META_SERVICES_TAG in metadata:
            self.__services = metadata[CgtConstants.META_SERVICES_TAG]
            self._check_list_type(self.__services)
            for serv in self.__services:
                self._check_dict_type(serv)
                self._check_value_exist(serv, CgtConstants.META_SERVICE_TAG)
                self._check_value_exist(serv, CgtConstants.META_VERSION_TAG)

        self.__functions = []
        if CgtConstants.META_FUNCTIONS_TAG in metadata:
            self.__functions = metadata[CgtConstants.META_FUNCTIONS_TAG]
            self._check_list_type(self.__functions)
            for func in self.__functions:
                self._check_dict_type(func)
                self._check_value_exist(func, CgtConstants.META_FUNCTION_TAG)
                self._check_value_exist(func, CgtConstants.META_VERSION_TAG)

    def _which_metadata(self):
        return 'functions meta-data'

    def num_of_services(self):
        return len(self.__services)

    def services(self):
        """Generator for traversal services in functions meta-data"""
        for serv in self.__services:
            service = serv[CgtConstants.META_SERVICE_TAG]
            version = serv[CgtConstants.META_VERSION_TAG]
            yield service, version

    def removeService(self, serv_id):
        services_to_remove = []
        for serv in self.__services:
            if serv[CgtConstants.META_SERVICE_TAG] == serv_id:
                services_to_remove.append(serv)

        for serv in services_to_remove:
            self.__services.remove(serv)

    def num_of_functions(self):
        return len(self.__functions)

    def functions(self):
        """Generator for traversal functions in functions meta-data"""
        for func in self.__functions:
            function = func[CgtConstants.META_FUNCTION_TAG]
            version = func[CgtConstants.META_VERSION_TAG]
            yield function, version

    def removeFunction(self, func_id):
        functions_to_remove = []
        for func in self.__functions:
            if func[CgtConstants.META_FUNCTION_TAG] == func_id:
                functions_to_remove.append(func)

        for func in functions_to_remove:
            self.__functions.remove(func)


class RolesMetaData(MetaData):
    def __init__(self, metadata):
        self._check_metadata_not_none(metadata)
        self._check_dict_type(metadata)

        self._check_value_exist(metadata, CgtConstants.META_ROLE_VERSION_TAG)
        self.__role_version = metadata[CgtConstants.META_ROLE_VERSION_TAG]

        self._check_value_exist(metadata, CgtConstants.META_SERVICES_TAG)
        self.__services = metadata[CgtConstants.META_SERVICES_TAG]
        self._check_list_type(self.__services)
        for serv in self.__services:
            self._check_dict_type(serv)
            self._check_value_exist(serv, CgtConstants.META_SERVICE_TAG)
            self._check_value_exist(serv, CgtConstants.META_VERSION_TAG)

    def _which_metadata(self):
        return 'roles meta-data'

    def getRoleVersion(self):
        return self.__role_version

    def removeService(self, serv_id):
        services_to_remove = []
        for serv in self.__services:
            if serv[CgtConstants.META_SERVICE_TAG] == serv_id:
                services_to_remove.append(serv)

        for serv in services_to_remove:
            self.__services.remove(serv)

    def num_of_services(self):
        return len(self.__services)

    def services(self):
        """Generator for traversal services in roles meta-data"""
        for serv in self.__services:
            service = serv[CgtConstants.META_SERVICE_TAG]
            version = serv[CgtConstants.META_VERSION_TAG]
            yield service, version


class SystemMetaData(MetaData):
    def __init__(self, metadata):
        self._check_metadata_not_none(metadata)
        self._check_dict_type(metadata)

        self._check_value_exist(metadata, CgtConstants.META_FUNCTIONS_TAG)
        self.__functions = metadata[CgtConstants.META_FUNCTIONS_TAG]
        self._check_list_type(self.__functions)
        for func in self.__functions:
            self._check_dict_type(func)
            self._check_value_exist(func, CgtConstants.META_FUNCTION_TAG)
            self._check_value_exist(func, CgtConstants.META_VERSION_TAG)

        self._check_value_exist(metadata, CgtConstants.META_ROLES_TAG)
        self.__roles = metadata[CgtConstants.META_ROLES_TAG]
        self._check_list_type(self.__roles)
        for role in self.__roles:
            self._check_dict_type(role)
            self._check_value_exist(role, CgtConstants.META_ROLE_TAG)
            self._check_value_exist(role, CgtConstants.META_VERSION_TAG)

    def _which_metadata(self):
        return 'system meta-data'

    def num_of_functions(self):
        return len(self.__functions)

    def functions(self):
        """Generator for traversal functions in system meta-data"""
        for func in self.__functions:
            function = func[CgtConstants.META_FUNCTION_TAG]
            version = func[CgtConstants.META_VERSION_TAG]
            yield function, version

    def num_of_roles(self):
        return len(self.__roles)

    def roles(self):
        """Generator for traversal roles in system meta-data"""
        for role in self.__roles:
            r = role[CgtConstants.META_ROLE_TAG]
            version = role[CgtConstants.META_VERSION_TAG]
            yield r, version
