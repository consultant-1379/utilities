import SimpleAMFModelGenerator
import AMFConstants

class CommonAMFModelGenerator(SimpleAMFModelGenerator.SimpleAMFModelGenerator):
    def __init__(self, configGeneratorFunc = None):
        self._configGeneratorFunc = configGeneratorFunc
        SimpleAMFModelGenerator.SimpleAMFModelGenerator.__init__( self )

    def processSaAmfComp(self, dn, node, ctIdentity):
        return {"saAmfCompDelayBetweenInstantiateAttempts" : "10000000000",
                "saAmfCompNumMaxInstantiateWithDelay" : "2000000"}

    def processSaAmfSI(self, dn, name):
        if self.getRedundancyModel().upper() == AMFConstants.REDUNDANCY_MODEL_NAME_NWA:
            return {"saAmfSIPrefActiveAssignments" : self.getNumberOfSUs()}
        return {}

    def getConsumerList(self):
        if self._configGeneratorFunc != None:
            return ["IMM"]
        return []

    def generateConfig(self, consumer, targetDirectory):
        assert(consumer == "IMM")
        if self._configGeneratorFunc != None:
            self._configGeneratorFunc(targetDirectory, self)
