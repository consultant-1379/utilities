

class CsmApiComponent(object):

    """
    Constants to be used in swType attribute
    """
    SDP = 0
    RPM = 1

    def __init__(self):
        self.uid = None
        self.version = None
        self.plugin = None
        self.swType = None
        self.swPackages = []  # list of strings
        self.swBundles = []  # list of pairs (file name, bundle name) as defined in the meta-data section


class CsmApiComponentInstance(object):

    def __init__(self):
        self.component = None  # reference to CsmApiComponent
        self.instanceName = None


class CsmApiService(object):

    def __init__(self):
        self.uid = None
        self.version = None
        self.componentInstances = []  # list of CsmApiComponentInstance


class CsmApiComponentConfigFile(object):
    def __init__(self):
        self.name = None
        self.dataType = None
        self.dataCategory = None


class CsmApiComputeResource(object):

    def __init__(self):
        self.name = None  # example: "SC-1"
        self.dn = None  # example: "safAmfNode=SC-1,safAmfCluster=myAmfCluster"
        self.role = None  # reference to the CsmApiRole allocated in this compute resource


class CsmApiRole(object):

    def __init__(self):
        self.uid = None
        self.canScale = None
        self.services = []  # list of CsmApiService
        self.computeResources = []  # list of CsmApiComputeResource


class CsmApiPool(object):

    def __init__(self):
        self.name = None
        self.nodes = None  # list of CsmApiComputeResource objects
        self.services = []  # list of CsmApiService objects
