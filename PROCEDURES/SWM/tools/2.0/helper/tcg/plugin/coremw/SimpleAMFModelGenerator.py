class SimpleAMFModelGenerator(object):
    def __init__(self):
        self._numberOfSUs = 0
        self._svIdentity = None
        self._parameters = {}
        self._nodeList = []
        self._redundancyModel = "Unknown"

    def getServiceIdentity(self):
        return self._svIdentity

    def getNumberOfSUs(self):
        return self._numberOfSUs

    def getNodeList(self):
        return self._nodeList

    def getRedundancyModel(self):
        return self._redundancyModel

    def getParameters(self, domain):
        if domain in self._parameters:
            return self._parameters[domain].keys()
        return None

    def getParameterValues(self, domain, name):
        if domain in self._parameters:
            if name in self._parameters[domain]:
                return self._parameters[domain][name]
        return None

    def getParameterValue(self, domain, name):
        if domain in self._parameters:
            if name in self._parameters[domain]:
                return self._parameters[domain][name][0]
        return None

    def processSaAmfSG(self, dn):
        return {}

    def processSaAmfSU(self, dn, node):
        return {}

    def processSaAmfComp(self, dn, node, ctIdentity):
        return {}

    def processSaAmfCompCsType(self, dn, ctIdentity, cstIdentity):
        return {}

    def generateSINameList(self):
        return ["1"]

    def processSaAmfSI(self, dn, name):
        return {}

    def processSaAmfCSIAttribute(self, dn, name, cstIdentity):
        return None

    def getConsumerList(self):
        return []

    def generateConfig(self, consumer, targetDirectory):
        pass
