import ImmMerger
import ImmClassMerger
import Utils
from utils.logger_tcg import tcg_error
import shutil
import os
import sys
import re


class UniqueFileCollector():
    def __init__(self, pattern = None):
        if pattern:
            self._compiledRE = re.compile(pattern)
        else:
            self._compiledRE = None
        self._files = {}

    def addFile(self, f, path, unit, consumer):
        if self._compiledRE is None or self._compiledRE.match(f):
            if f in self._files.keys():
                tcg_error("%s data file %s is present in multiple directories (detected while processing unit %s)" % (consumer, f, unit.identity))
            self._files[f] = os.path.join(path, f)

    def writeConfig(self, campaignDirectory, consumer):
        d = os.path.join(campaignDirectory, consumer)
        Utils.mkdir_safe(d)
        modelFile = open(os.path.join(campaignDirectory, consumer + "-model.config"), "w")
        for (f, path) in self._files.items():
            modelFile.write(os.path.join(consumer, f) + "\n")
            shutil.copy2(path, d)
        modelFile.close()

    def isEmpty(self):
        return len(self._files) == 0

    def getCommand(self):
        return "cmw-model-modify"

class ImmConfigMerger():
    def __init__(self):
        self._merger = ImmMerger.ImmMerger()

    def addFile(self, f, path, unit, consumer):
        self._merger.mergeXML(os.path.join(path, f))

    def writeConfig(self, campaignDirectory, consumer):
        modelFile = open(os.path.join(campaignDirectory, consumer + "-model.config"), "w")
        d = os.path.join(campaignDirectory, consumer)
        Utils.mkdir_safe(d)
        instanceFile = "imm.xml"
        modelFile.write(os.path.join(consumer, instanceFile) + "\n")
        self._merger.writeXML(os.path.join(d, instanceFile))
        modelFile.close()

    def isEmpty(self):
        return self._merger.isEmpty()

    def getCommand(self):
        return "cmw-model-modify"

    def merge(self, merger):
        self._merger.merge(merger)

class ConfigMerger():
    def __init__(self, consumer, baseMerger):
        self._consumer = consumer
        self._baseMerger = baseMerger

    def addFile(self, f, path, unit):
        self._baseMerger.addFile(f, path, unit, self._consumer)

    def writeConfig(self, campaignDirectory):
        self._baseMerger.writeConfig(campaignDirectory, self._consumer)

    def isEmpty(self):
        return self._baseMerger.isEmpty()

    def getCommand(self):
        return self._baseMerger.getCommand()

    def getConsumer(self):
        return self._consumer

    def merge(self, merger):
        self._baseMerger.merge(merger)
