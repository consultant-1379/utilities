import ImmHelper
from common import error
import xml.dom.minidom
import re


class AMFModel(object):
    def __init__(self):
        self._objects = {}
        self._objectsCreatedInCampaign = False

    def getObjects(self, _class = None, parentDn = None):
        if _class == None:
            return self._objects
        else:
            r = {}
            for k,v in self._objects.items():
                if v.__class__.__name__ == _class.__name__:
                    if parentDn is None or v.getParentDn() == parentDn:
                        r[v.getDn()] = v
            return r

    def getSubtree(self, rootDn):
        r = {}
        for k,v in self._objects.items():
            if k == rootDn or ImmHelper.isInSubtree(k, rootDn):
                r[k] = v
        return r

    def diff(self, base, fullCheck = False):
        added = []
        updated = {}
        removed = []
        unchanged = []
        for (k,v) in self._objects.items():
            if k in base._objects.keys():
                base_v = base._objects[k]
                v_diff = v.diff(base_v, fullCheck)
                if len(v_diff) > 0:
                    updated[v.getDn()] = v_diff
                else:
                    unchanged.append(v.getDn())
            else:
                added.append(k)
        for (k,v) in base._objects.items():
            if k not in self._objects.keys():
                removed.append(k)
        return (added, updated, removed, unchanged)

    def getObject(self, dn):
        return self._objects[dn]

    def getObjectUnsafe(self, dn):
        if dn in self._objects.keys():
            return self._objects[dn]

    def addObject(self, obj):
        self._objects[obj.getDn()] = obj

    def removeObject(self, dn):
        del self._objects[dn]

    def createObjectInCampaign(self, campaign, type):
        for o in self.getObjects(type).values():
            o.createObjectInCampaign(campaign)
        self._objectsCreatedInCampaign = True

    def parseXML(self, fileName):
        doc = xml.dom.minidom.parse(fileName)
        root = doc.documentElement
        for _obj in root.getElementsByTagName("object"):
            _class = _obj.getAttribute("class")
            obj = None
            if _class == "SaSmfSwBundle":
                obj = SaSmfSwBundle()
            elif _class == "SaAmfSvcTypeCSTypes":
                obj = SaAmfSvcTypeCSTypes()
            elif _class == "SaAmfSvcType":
                obj = SaAmfSvcType()
            elif _class == "SaAmfSvcBaseType":
                obj = SaAmfSvcBaseType()
            elif _class == "SaAmfSutCompType":
                obj = SaAmfSutCompType()
            elif _class == "SaAmfSUType":
                obj = SaAmfSUType()
            elif _class == "SaAmfSUBaseType":
                obj = SaAmfSUBaseType()
            elif _class == "SaAmfSU":
                obj = SaAmfSU()
            elif _class == "SaAmfSIRankedSU":
                obj = SaAmfSIRankedSU()
            elif _class == "SaAmfSIDependency":
                obj = SaAmfSIDependency()
            elif _class == "SaAmfSIAssignment":
                obj = SaAmfSIAssignment()
            elif _class == "SaAmfSI":
                obj = SaAmfSI()
            elif _class == "SaAmfSGType":
                obj = SaAmfSGType()
            elif _class == "SaAmfSGBaseType":
                obj = SaAmfSGBaseType()
            elif _class == "SaAmfSG":
                obj = SaAmfSG()
            elif _class == "SaAmfNodeSwBundle":
                obj = SaAmfNodeSwBundle()
            elif _class == "SaAmfNodeGroup":
                obj = SaAmfNodeGroup()
            elif _class == "SaAmfNode":
                obj = SaAmfNode()
            elif _class == "SaAmfHealthcheckType":
                obj = SaAmfHealthcheckType()
            elif _class == "SaAmfHealthcheck":
                obj = SaAmfHealthcheck()
            elif _class == "SaAmfCtCsType":
                obj = SaAmfCtCsType()
            elif _class == "SaAmfCompType":
                obj = SaAmfCompType()
            elif _class == "SaAmfCompGlobalAttributes":
                obj = SaAmfCompGlobalAttributes()
            elif _class == "SaAmfCompCsType":
                obj = SaAmfCompCsType()
            elif _class == "SaAmfCompBaseType":
                obj = SaAmfCompBaseType()
            elif _class == "SaAmfComp":
                obj = SaAmfComp()
            elif _class == "SaAmfCluster":
                obj = SaAmfCluster()
            elif _class == "SaAmfCSType":
                obj = SaAmfCSType()
            elif _class == "SaAmfCSIAttribute":
                obj = SaAmfCSIAttribute()
            elif _class == "SaAmfCSIAssignment":
                obj = SaAmfCSIAssignment()
            elif _class == "SaAmfCSI":
                obj = SaAmfCSI()
            elif _class == "SaAmfCSBaseType":
                obj = SaAmfCSBaseType()
            elif _class == "SaAmfApplication":
                obj = SaAmfApplication()
            elif _class == "SaAmfAppType":
                obj = SaAmfAppType()
            elif _class == "SaAmfAppBaseType":
                obj = SaAmfAppBaseType()
            else:
                continue
            obj.parseXML(_obj)
            self._objects[obj.getDn()] = obj

    def writeXML(self, fileName):
        doc = xml.dom.minidom.Document()
        root = doc.createElement("imm:IMM-contents")
        root.setAttribute("xmlns:imm", "http://www.saforum.org/IMMSchema")
        root.setAttribute("xmlns:xsi", "http://www.w3.org/2001/XMLSchema-instance")
        root.setAttribute("xsi:noNamespaceSchemaLocation", "SAI-AIS-IMM-XSD-A.01.01.xsd")
        doc.appendChild(root)
        for dn,obj in self._objects.items():
            obj.writeXML(root, doc)
        output = open(fileName, "w")
        doc.writexml(output, addindent = "  ", newl = "\n")
        output.close()

    def isObjectCreatedInCampaign(self):
        return self._objectsCreatedInCampaign

    @staticmethod
    def getInterestedAmfClasses():
        return ['SaSmfSwBundle', 'SaAmfSvcTypeCSTypes', 'SaAmfSvcType', 'SaAmfSvcBaseType', 'SaAmfSutCompType', 'SaAmfSUType', 'SaAmfSUBaseType', 'SaAmfSU', 'SaAmfSIRankedSU', 'SaAmfSIDependency', 'SaAmfSIAssignment', 'SaAmfSI', 'SaAmfSGType', 'SaAmfSGBaseType', 'SaAmfSG', 'SaAmfNodeSwBundle', 'SaAmfNodeGroup', 'SaAmfNode', 'SaAmfHealthcheckType', 'SaAmfHealthcheck', 'SaAmfCtCsType', 'SaAmfCompType', 'SaAmfCompGlobalAttributes', 'SaAmfCompCsType', 'SaAmfCompBaseType', 'SaAmfComp', 'SaAmfCluster', 'SaAmfCSType', 'SaAmfCSIAttribute', 'SaAmfCSIAssignment', 'SaAmfCSI', 'SaAmfCSBaseType', 'SaAmfApplication', 'SaAmfAppType', 'SaAmfAppBaseType']

class SaSmfSwBundle(object):
    def __init__(self):
        self._dn = None
        self._saSmfBundleRemoveOnlineCmdUri = None
        self._saSmfBundleRemoveOnlineCmdArgs = None
        self._saSmfBundleRemoveOfflineScope = None
        self._saSmfBundleRemoveOfflineCmdUri = None
        self._saSmfBundleRemoveOfflineCmdArgs = None
        self._saSmfBundleInstallOnlineCmdUri = None
        self._saSmfBundleInstallOnlineCmdArgs = None
        self._saSmfBundleInstallOfflineScope = None
        self._saSmfBundleInstallOfflineCmdUri = None
        self._saSmfBundleInstallOfflineCmdArgs = None
        self._saSmfBundleDefaultCmdTimeout = None
        self._SaImmAttrImplementerName = None
        self._SaImmAttrClassName = None
        self._SaImmAttrAdminOwnerName = None

    @staticmethod
    def createDn(name, parentDn = None):
        if parentDn == None:
            parentDn = ""
        else:
            parentDn = "," + parentDn
        return "safSmfBundle=" + ImmHelper.escapeName(name) + parentDn

    def getDn(self):
        return self._dn

    def getName(self):
        return ImmHelper.getName(self._dn)

    def getRdn(self):
        return ImmHelper.getRdn(self._dn)

    def getParentDn(self):
        return ImmHelper.getParentDn(self._dn)

    def createObjectInCampaign(self, campaign):
        parentDn = self.getParentDn()
        if parentDn == "":
            parentDn = "="
        campaign.beginCreate("SaSmfSwBundle", parentDn)
        campaign.addAttribute("safSmfBundle", "SA_IMM_ATTR_SASTRINGT", self.getRdn())
        if self._saSmfBundleRemoveOnlineCmdUri != None:
            campaign.addAttribute("saSmfBundleRemoveOnlineCmdUri", "SA_IMM_ATTR_SASTRINGT", self._saSmfBundleRemoveOnlineCmdUri)
        if self._saSmfBundleRemoveOnlineCmdArgs != None:
            campaign.addAttribute("saSmfBundleRemoveOnlineCmdArgs", "SA_IMM_ATTR_SASTRINGT", self._saSmfBundleRemoveOnlineCmdArgs)
        if self._saSmfBundleRemoveOfflineScope != None:
            campaign.addAttribute("saSmfBundleRemoveOfflineScope", "SA_IMM_ATTR_SAUINT32T", self._saSmfBundleRemoveOfflineScope)
        if self._saSmfBundleRemoveOfflineCmdUri != None:
            campaign.addAttribute("saSmfBundleRemoveOfflineCmdUri", "SA_IMM_ATTR_SASTRINGT", self._saSmfBundleRemoveOfflineCmdUri)
        if self._saSmfBundleRemoveOfflineCmdArgs != None:
            campaign.addAttribute("saSmfBundleRemoveOfflineCmdArgs", "SA_IMM_ATTR_SASTRINGT", self._saSmfBundleRemoveOfflineCmdArgs)
        if self._saSmfBundleInstallOnlineCmdUri != None:
            campaign.addAttribute("saSmfBundleInstallOnlineCmdUri", "SA_IMM_ATTR_SASTRINGT", self._saSmfBundleInstallOnlineCmdUri)
        if self._saSmfBundleInstallOnlineCmdArgs != None:
            campaign.addAttribute("saSmfBundleInstallOnlineCmdArgs", "SA_IMM_ATTR_SASTRINGT", self._saSmfBundleInstallOnlineCmdArgs)
        if self._saSmfBundleInstallOfflineScope != None:
            campaign.addAttribute("saSmfBundleInstallOfflineScope", "SA_IMM_ATTR_SAUINT32T", self._saSmfBundleInstallOfflineScope)
        if self._saSmfBundleInstallOfflineCmdUri != None:
            campaign.addAttribute("saSmfBundleInstallOfflineCmdUri", "SA_IMM_ATTR_SASTRINGT", self._saSmfBundleInstallOfflineCmdUri)
        if self._saSmfBundleInstallOfflineCmdArgs != None:
            campaign.addAttribute("saSmfBundleInstallOfflineCmdArgs", "SA_IMM_ATTR_SASTRINGT", self._saSmfBundleInstallOfflineCmdArgs)
        if self._saSmfBundleDefaultCmdTimeout != None:
            campaign.addAttribute("saSmfBundleDefaultCmdTimeout", "SA_IMM_ATTR_SATIMET", self._saSmfBundleDefaultCmdTimeout)
        if self._SaImmAttrImplementerName != None:
            campaign.addAttribute("SaImmAttrImplementerName", "SA_IMM_ATTR_SASTRINGT", self._SaImmAttrImplementerName)
        if self._SaImmAttrClassName != None:
            campaign.addAttribute("SaImmAttrClassName", "SA_IMM_ATTR_SASTRINGT", self._SaImmAttrClassName)
        if self._SaImmAttrAdminOwnerName != None:
            campaign.addAttribute("SaImmAttrAdminOwnerName", "SA_IMM_ATTR_SASTRINGT", self._SaImmAttrAdminOwnerName)
        campaign.endCreate()

    def getsaSmfBundleRemoveOnlineCmdUri(self):
        ImmHelper.validateSingle(self._saSmfBundleRemoveOnlineCmdUri, self._dn, "saSmfBundleRemoveOnlineCmdUri")
        return self._saSmfBundleRemoveOnlineCmdUri

    def getsaSmfBundleRemoveOnlineCmdArgs(self):
        ImmHelper.validateSingle(self._saSmfBundleRemoveOnlineCmdArgs, self._dn, "saSmfBundleRemoveOnlineCmdArgs")
        return self._saSmfBundleRemoveOnlineCmdArgs

    def getsaSmfBundleRemoveOfflineScope(self):
        if self._saSmfBundleRemoveOfflineScope is not None:
            ImmHelper.validateSingle(self._saSmfBundleRemoveOfflineScope, self._dn, "saSmfBundleRemoveOfflineScope")
        return self._saSmfBundleRemoveOfflineScope

    def getsaSmfBundleRemoveOfflineCmdUri(self):
        ImmHelper.validateSingle(self._saSmfBundleRemoveOfflineCmdUri, self._dn, "saSmfBundleRemoveOfflineCmdUri")
        return self._saSmfBundleRemoveOfflineCmdUri

    def getsaSmfBundleRemoveOfflineCmdArgs(self):
        ImmHelper.validateSingle(self._saSmfBundleRemoveOfflineCmdArgs, self._dn, "saSmfBundleRemoveOfflineCmdArgs")
        return self._saSmfBundleRemoveOfflineCmdArgs

    def getsaSmfBundleInstallOnlineCmdUri(self):
        ImmHelper.validateSingle(self._saSmfBundleInstallOnlineCmdUri, self._dn, "saSmfBundleInstallOnlineCmdUri")
        return self._saSmfBundleInstallOnlineCmdUri

    def getsaSmfBundleInstallOnlineCmdArgs(self):
        ImmHelper.validateSingle(self._saSmfBundleInstallOnlineCmdArgs, self._dn, "saSmfBundleInstallOnlineCmdArgs")
        return self._saSmfBundleInstallOnlineCmdArgs

    def getsaSmfBundleInstallOfflineScope(self):
        if self._saSmfBundleInstallOfflineScope is not None:
           ImmHelper.validateSingle(self._saSmfBundleInstallOfflineScope, self._dn, "saSmfBundleInstallOfflineScope")
        return self._saSmfBundleInstallOfflineScope

    def getsaSmfBundleInstallOfflineCmdUri(self):
        ImmHelper.validateSingle(self._saSmfBundleInstallOfflineCmdUri, self._dn, "saSmfBundleInstallOfflineCmdUri")
        return self._saSmfBundleInstallOfflineCmdUri

    def getsaSmfBundleInstallOfflineCmdArgs(self):
        ImmHelper.validateSingle(self._saSmfBundleInstallOfflineCmdArgs, self._dn, "saSmfBundleInstallOfflineCmdArgs")
        return self._saSmfBundleInstallOfflineCmdArgs

    def getsaSmfBundleDefaultCmdTimeout(self):
        ImmHelper.validateSingle(self._saSmfBundleDefaultCmdTimeout, self._dn, "saSmfBundleDefaultCmdTimeout")
        return self._saSmfBundleDefaultCmdTimeout

    def getSaImmAttrImplementerName(self):
        ImmHelper.validateSingle(self._SaImmAttrImplementerName, self._dn, "SaImmAttrImplementerName")
        return self._SaImmAttrImplementerName

    def getSaImmAttrClassName(self):
        ImmHelper.validateSingle(self._SaImmAttrClassName, self._dn, "SaImmAttrClassName")
        return self._SaImmAttrClassName

    def getSaImmAttrAdminOwnerName(self):
        ImmHelper.validateSingle(self._SaImmAttrAdminOwnerName, self._dn, "SaImmAttrAdminOwnerName")
        return self._SaImmAttrAdminOwnerName

    def getsaSmfBundleRemoveOnlineCmdUri_unsafe(self):
        return self._saSmfBundleRemoveOnlineCmdUri

    def getsaSmfBundleRemoveOnlineCmdArgs_unsafe(self):
        return self._saSmfBundleRemoveOnlineCmdArgs

    def getsaSmfBundleRemoveOfflineScope_unsafe(self):
        return self._saSmfBundleRemoveOfflineScope

    def getsaSmfBundleRemoveOfflineCmdUri_unsafe(self):
        return self._saSmfBundleRemoveOfflineCmdUri

    def getsaSmfBundleRemoveOfflineCmdArgs_unsafe(self):
        return self._saSmfBundleRemoveOfflineCmdArgs

    def getsaSmfBundleInstallOnlineCmdUri_unsafe(self):
        return self._saSmfBundleInstallOnlineCmdUri

    def getsaSmfBundleInstallOnlineCmdArgs_unsafe(self):
        return self._saSmfBundleInstallOnlineCmdArgs

    def getsaSmfBundleInstallOfflineScope_unsafe(self):
        return self._saSmfBundleInstallOfflineScope

    def getsaSmfBundleInstallOfflineCmdUri_unsafe(self):
        return self._saSmfBundleInstallOfflineCmdUri

    def getsaSmfBundleInstallOfflineCmdArgs_unsafe(self):
        return self._saSmfBundleInstallOfflineCmdArgs

    def getsaSmfBundleDefaultCmdTimeout_unsafe(self):
        return self._saSmfBundleDefaultCmdTimeout

    def getSaImmAttrImplementerName_unsafe(self):
        return self._SaImmAttrImplementerName

    def getSaImmAttrClassName_unsafe(self):
        return self._SaImmAttrClassName

    def getSaImmAttrAdminOwnerName_unsafe(self):
        return self._SaImmAttrAdminOwnerName

    def setsaSmfBundleRemoveOnlineCmdUri(self, value):
        ImmHelper.validateString(value, self._dn, "saSmfBundleRemoveOnlineCmdUri")
        self._saSmfBundleRemoveOnlineCmdUri = value

    def setsaSmfBundleRemoveOnlineCmdArgs(self, value):
        ImmHelper.validateString(value, self._dn, "saSmfBundleRemoveOnlineCmdArgs")
        self._saSmfBundleRemoveOnlineCmdArgs = value

    def setsaSmfBundleRemoveOfflineScope(self, value):
        if value is not None:
            ImmHelper.validateUint32(value, self._dn, "saSmfBundleRemoveOfflineScope")
            value = str(value)
            self._saSmfBundleRemoveOfflineScope = value

    def setsaSmfBundleRemoveOfflineCmdUri(self, value):
        ImmHelper.validateString(value, self._dn, "saSmfBundleRemoveOfflineCmdUri")
        self._saSmfBundleRemoveOfflineCmdUri = value

    def setsaSmfBundleRemoveOfflineCmdArgs(self, value):
        ImmHelper.validateString(value, self._dn, "saSmfBundleRemoveOfflineCmdArgs")
        self._saSmfBundleRemoveOfflineCmdArgs = value

    def setsaSmfBundleInstallOnlineCmdUri(self, value):
        ImmHelper.validateString(value, self._dn, "saSmfBundleInstallOnlineCmdUri")
        self._saSmfBundleInstallOnlineCmdUri = value

    def setsaSmfBundleInstallOnlineCmdArgs(self, value):
        ImmHelper.validateString(value, self._dn, "saSmfBundleInstallOnlineCmdArgs")
        self._saSmfBundleInstallOnlineCmdArgs = value

    def setsaSmfBundleInstallOfflineScope(self, value):
        if value is not None:
            ImmHelper.validateUint32(value, self._dn, "saSmfBundleInstallOfflineScope")
            value = str(value)
            self._saSmfBundleInstallOfflineScope = value

    def setsaSmfBundleInstallOfflineCmdUri(self, value):
        ImmHelper.validateString(value, self._dn, "saSmfBundleInstallOfflineCmdUri")
        self._saSmfBundleInstallOfflineCmdUri = value

    def setsaSmfBundleInstallOfflineCmdArgs(self, value):
        ImmHelper.validateString(value, self._dn, "saSmfBundleInstallOfflineCmdArgs")
        self._saSmfBundleInstallOfflineCmdArgs = value

    def setsaSmfBundleDefaultCmdTimeout(self, value):
        ImmHelper.validateTime(value, self._dn, "saSmfBundleDefaultCmdTimeout")
        value = str(value)
        self._saSmfBundleDefaultCmdTimeout = value

    def setSaImmAttrImplementerName(self, value):
        ImmHelper.validateString(value, self._dn, "SaImmAttrImplementerName")
        self._SaImmAttrImplementerName = value

    def setSaImmAttrClassName(self, value):
        ImmHelper.validateString(value, self._dn, "SaImmAttrClassName")
        self._SaImmAttrClassName = value

    def setSaImmAttrAdminOwnerName(self, value):
        ImmHelper.validateString(value, self._dn, "SaImmAttrAdminOwnerName")
        self._SaImmAttrAdminOwnerName = value

    def updateParams(self, params, canttouchthis):
        for (param, value) in params.items():
            if param in canttouchthis:
                error("Setting attribute " + param + " in object " + self.getDn() + " is not supported")
            if param == "saSmfBundleRemoveOnlineCmdUri":
                self.setsaSmfBundleRemoveOnlineCmdUri(value)
            elif param == "saSmfBundleRemoveOnlineCmdArgs":
                self.setsaSmfBundleRemoveOnlineCmdArgs(value)
            elif param == "saSmfBundleRemoveOfflineScope":
                self.setsaSmfBundleRemoveOfflineScope(value)
            elif param == "saSmfBundleRemoveOfflineCmdUri":
                self.setsaSmfBundleRemoveOfflineCmdUri(value)
            elif param == "saSmfBundleRemoveOfflineCmdArgs":
                self.setsaSmfBundleRemoveOfflineCmdArgs(value)
            elif param == "saSmfBundleInstallOnlineCmdUri":
                self.setsaSmfBundleInstallOnlineCmdUri(value)
            elif param == "saSmfBundleInstallOnlineCmdArgs":
                self.setsaSmfBundleInstallOnlineCmdArgs(value)
            elif param == "saSmfBundleInstallOfflineScope":
                self.setsaSmfBundleInstallOfflineScope(value)
            elif param == "saSmfBundleInstallOfflineCmdUri":
                self.setsaSmfBundleInstallOfflineCmdUri(value)
            elif param == "saSmfBundleInstallOfflineCmdArgs":
                self.setsaSmfBundleInstallOfflineCmdArgs(value)
            elif param == "saSmfBundleDefaultCmdTimeout":
                self.setsaSmfBundleDefaultCmdTimeout(value)
            else:
                error("Object " + self.getDn() + " has no attribute named " + param)

    def diff(self, other, fullCheck = False):
        changedAttrs = []
        if (fullCheck or self._saSmfBundleRemoveOnlineCmdUri != None) and other._saSmfBundleRemoveOnlineCmdUri != self._saSmfBundleRemoveOnlineCmdUri:
            changedAttrs.append("saSmfBundleRemoveOnlineCmdUri")
        if (fullCheck or self._saSmfBundleRemoveOnlineCmdArgs != None) and other._saSmfBundleRemoveOnlineCmdArgs != self._saSmfBundleRemoveOnlineCmdArgs:
            changedAttrs.append("saSmfBundleRemoveOnlineCmdArgs")
        if (fullCheck or self._saSmfBundleRemoveOfflineScope != None) and other._saSmfBundleRemoveOfflineScope != self._saSmfBundleRemoveOfflineScope:
            changedAttrs.append("saSmfBundleRemoveOfflineScope")
        if (fullCheck or self._saSmfBundleRemoveOfflineCmdUri != None) and other._saSmfBundleRemoveOfflineCmdUri != self._saSmfBundleRemoveOfflineCmdUri:
            changedAttrs.append("saSmfBundleRemoveOfflineCmdUri")
        if (fullCheck or self._saSmfBundleRemoveOfflineCmdArgs != None) and other._saSmfBundleRemoveOfflineCmdArgs != self._saSmfBundleRemoveOfflineCmdArgs:
            changedAttrs.append("saSmfBundleRemoveOfflineCmdArgs")
        if (fullCheck or self._saSmfBundleInstallOnlineCmdUri != None) and other._saSmfBundleInstallOnlineCmdUri != self._saSmfBundleInstallOnlineCmdUri:
            changedAttrs.append("saSmfBundleInstallOnlineCmdUri")
        if (fullCheck or self._saSmfBundleInstallOnlineCmdArgs != None) and other._saSmfBundleInstallOnlineCmdArgs != self._saSmfBundleInstallOnlineCmdArgs:
            changedAttrs.append("saSmfBundleInstallOnlineCmdArgs")
        if (fullCheck or self._saSmfBundleInstallOfflineScope != None) and other._saSmfBundleInstallOfflineScope != self._saSmfBundleInstallOfflineScope:
            changedAttrs.append("saSmfBundleInstallOfflineScope")
        if (fullCheck or self._saSmfBundleInstallOfflineCmdUri != None) and other._saSmfBundleInstallOfflineCmdUri != self._saSmfBundleInstallOfflineCmdUri:
            changedAttrs.append("saSmfBundleInstallOfflineCmdUri")
        if (fullCheck or self._saSmfBundleInstallOfflineCmdArgs != None) and other._saSmfBundleInstallOfflineCmdArgs != self._saSmfBundleInstallOfflineCmdArgs:
            changedAttrs.append("saSmfBundleInstallOfflineCmdArgs")
        if (fullCheck or self._saSmfBundleDefaultCmdTimeout != None) and other._saSmfBundleDefaultCmdTimeout != self._saSmfBundleDefaultCmdTimeout:
            changedAttrs.append("saSmfBundleDefaultCmdTimeout")
        if (fullCheck or self._SaImmAttrImplementerName != None) and other._SaImmAttrImplementerName != self._SaImmAttrImplementerName:
            changedAttrs.append("SaImmAttrImplementerName")
        if (fullCheck or self._SaImmAttrClassName != None) and other._SaImmAttrClassName != self._SaImmAttrClassName:
            changedAttrs.append("SaImmAttrClassName")
        if (fullCheck or self._SaImmAttrAdminOwnerName != None) and other._SaImmAttrAdminOwnerName != self._SaImmAttrAdminOwnerName:
            changedAttrs.append("SaImmAttrAdminOwnerName")
        return changedAttrs

    def parseXML(self, node):
        dns = node.getElementsByTagName("dn")
        if len(dns) != 1:
            error("object has " + str(len(dns)) + " dn(s) but it should have one")
        self._dn = dns[0].childNodes[0].nodeValue
        for attribute in node.getElementsByTagName("attr"):
            names = attribute.getElementsByTagName("name")
            if len(names) != 1:
                error("object attribute has " + str(len(names)) + " name(s) but it should have one")
            name = names[0].childNodes[0].nodeValue
            setFunc = None
            if name == "SaImmAttrImplementerName":
                continue
            elif name == "SaImmAttrAdminOwnerName":
                continue
            elif name == "SaImmAttrClassName":
                continue
            elif name == "saSmfBundleRemoveOnlineCmdUri":
                setFunc = self.setsaSmfBundleRemoveOnlineCmdUri
            elif name == "saSmfBundleRemoveOnlineCmdArgs":
                setFunc = self.setsaSmfBundleRemoveOnlineCmdArgs
            elif name == "saSmfBundleRemoveOfflineScope":
                setFunc = self.setsaSmfBundleRemoveOfflineScope
            elif name == "saSmfBundleRemoveOfflineCmdUri":
                setFunc = self.setsaSmfBundleRemoveOfflineCmdUri
            elif name == "saSmfBundleRemoveOfflineCmdArgs":
                setFunc = self.setsaSmfBundleRemoveOfflineCmdArgs
            elif name == "saSmfBundleInstallOnlineCmdUri":
                setFunc = self.setsaSmfBundleInstallOnlineCmdUri
            elif name == "saSmfBundleInstallOnlineCmdArgs":
                setFunc = self.setsaSmfBundleInstallOnlineCmdArgs
            elif name == "saSmfBundleInstallOfflineScope":
                setFunc = self.setsaSmfBundleInstallOfflineScope
            elif name == "saSmfBundleInstallOfflineCmdUri":
                setFunc = self.setsaSmfBundleInstallOfflineCmdUri
            elif name == "saSmfBundleInstallOfflineCmdArgs":
                setFunc = self.setsaSmfBundleInstallOfflineCmdArgs
            elif name == "saSmfBundleDefaultCmdTimeout":
                setFunc = self.setsaSmfBundleDefaultCmdTimeout
            elif name == "SaImmAttrImplementerName":
                setFunc = self.setSaImmAttrImplementerName
            elif name == "SaImmAttrClassName":
                setFunc = self.setSaImmAttrClassName
            elif name == "SaImmAttrAdminOwnerName":
                setFunc = self.setSaImmAttrAdminOwnerName
            elif name.startswith("osaf"):
                continue # ignore OpenSAF specific attributes
            else:
                error("unknown attribute called " + name + " defined in object " + self._dn)
            for value in attribute.getElementsByTagName("value"):
                setFunc(value.childNodes[0].nodeValue)

    def writeXML(self, parent, doc):
        obj = doc.createElement("object")
        parent.appendChild(obj)
        obj.setAttribute("class", "SaSmfSwBundle")
        dn = doc.createElement("dn")
        obj.appendChild(dn)
        dn.appendChild(doc.createTextNode(self._dn))
        ImmHelper.writeSingleAttribute("saSmfBundleRemoveOnlineCmdUri", self._saSmfBundleRemoveOnlineCmdUri, doc, obj)
        ImmHelper.writeSingleAttribute("saSmfBundleRemoveOnlineCmdArgs", self._saSmfBundleRemoveOnlineCmdArgs, doc, obj)
        ImmHelper.writeSingleAttribute("saSmfBundleRemoveOfflineScope", self._saSmfBundleRemoveOfflineScope, doc, obj)
        ImmHelper.writeSingleAttribute("saSmfBundleRemoveOfflineCmdUri", self._saSmfBundleRemoveOfflineCmdUri, doc, obj)
        ImmHelper.writeSingleAttribute("saSmfBundleRemoveOfflineCmdArgs", self._saSmfBundleRemoveOfflineCmdArgs, doc, obj)
        ImmHelper.writeSingleAttribute("saSmfBundleInstallOnlineCmdUri", self._saSmfBundleInstallOnlineCmdUri, doc, obj)
        ImmHelper.writeSingleAttribute("saSmfBundleInstallOnlineCmdArgs", self._saSmfBundleInstallOnlineCmdArgs, doc, obj)
        ImmHelper.writeSingleAttribute("saSmfBundleInstallOfflineScope", self._saSmfBundleInstallOfflineScope, doc, obj)
        ImmHelper.writeSingleAttribute("saSmfBundleInstallOfflineCmdUri", self._saSmfBundleInstallOfflineCmdUri, doc, obj)
        ImmHelper.writeSingleAttribute("saSmfBundleInstallOfflineCmdArgs", self._saSmfBundleInstallOfflineCmdArgs, doc, obj)
        ImmHelper.writeSingleAttribute("saSmfBundleDefaultCmdTimeout", self._saSmfBundleDefaultCmdTimeout, doc, obj)
        ImmHelper.writeSingleAttribute("SaImmAttrImplementerName", self._SaImmAttrImplementerName, doc, obj)
        ImmHelper.writeSingleAttribute("SaImmAttrClassName", self._SaImmAttrClassName, doc, obj)
        ImmHelper.writeSingleAttribute("SaImmAttrAdminOwnerName", self._SaImmAttrAdminOwnerName, doc, obj)


class SaAmfSvcTypeCSTypes(object):
    def __init__(self):
        self._dn = None
        self._saAmfSvctMaxNumCSIs = None
        self._SaImmAttrImplementerName = None
        self._SaImmAttrClassName = None
        self._SaImmAttrAdminOwnerName = None

    @staticmethod
    def createDn(name, parentDn = None):
        if parentDn == None:
            parentDn = ""
        else:
            parentDn = "," + parentDn
        return "safMemberCSType=" + ImmHelper.escapeName(name) + parentDn

    def getDn(self):
        return self._dn

    def getName(self):
        return ImmHelper.getName(self._dn)

    def getRdn(self):
        return ImmHelper.getRdn(self._dn)

    def getParentDn(self):
        return ImmHelper.getParentDn(self._dn)

    def createObjectInCampaign(self, campaign):
        parentDn = self.getParentDn()
        if parentDn == "":
            parentDn = "="
        campaign.beginCreate("SaAmfSvcTypeCSTypes", parentDn)
        campaign.addAttribute("safMemberCSType", "SA_IMM_ATTR_SANAMET", self.getRdn())
        if self._saAmfSvctMaxNumCSIs != None:
            campaign.addAttribute("saAmfSvctMaxNumCSIs", "SA_IMM_ATTR_SAUINT32T", self._saAmfSvctMaxNumCSIs)
        if self._SaImmAttrImplementerName != None:
            campaign.addAttribute("SaImmAttrImplementerName", "SA_IMM_ATTR_SASTRINGT", self._SaImmAttrImplementerName)
        if self._SaImmAttrClassName != None:
            campaign.addAttribute("SaImmAttrClassName", "SA_IMM_ATTR_SASTRINGT", self._SaImmAttrClassName)
        if self._SaImmAttrAdminOwnerName != None:
            campaign.addAttribute("SaImmAttrAdminOwnerName", "SA_IMM_ATTR_SASTRINGT", self._SaImmAttrAdminOwnerName)
        campaign.endCreate()

    def getsaAmfSvctMaxNumCSIs(self):
        ImmHelper.validateSingle(self._saAmfSvctMaxNumCSIs, self._dn, "saAmfSvctMaxNumCSIs")
        return self._saAmfSvctMaxNumCSIs

    def getSaImmAttrImplementerName(self):
        ImmHelper.validateSingle(self._SaImmAttrImplementerName, self._dn, "SaImmAttrImplementerName")
        return self._SaImmAttrImplementerName

    def getSaImmAttrClassName(self):
        ImmHelper.validateSingle(self._SaImmAttrClassName, self._dn, "SaImmAttrClassName")
        return self._SaImmAttrClassName

    def getSaImmAttrAdminOwnerName(self):
        ImmHelper.validateSingle(self._SaImmAttrAdminOwnerName, self._dn, "SaImmAttrAdminOwnerName")
        return self._SaImmAttrAdminOwnerName

    def getsaAmfSvctMaxNumCSIs_unsafe(self):
        return self._saAmfSvctMaxNumCSIs

    def getSaImmAttrImplementerName_unsafe(self):
        return self._SaImmAttrImplementerName

    def getSaImmAttrClassName_unsafe(self):
        return self._SaImmAttrClassName

    def getSaImmAttrAdminOwnerName_unsafe(self):
        return self._SaImmAttrAdminOwnerName

    def setsaAmfSvctMaxNumCSIs(self, value):
        ImmHelper.validateUint32(value, self._dn, "saAmfSvctMaxNumCSIs")
        value = str(value)
        self._saAmfSvctMaxNumCSIs = value

    def setSaImmAttrImplementerName(self, value):
        ImmHelper.validateString(value, self._dn, "SaImmAttrImplementerName")
        self._SaImmAttrImplementerName = value

    def setSaImmAttrClassName(self, value):
        ImmHelper.validateString(value, self._dn, "SaImmAttrClassName")
        self._SaImmAttrClassName = value

    def setSaImmAttrAdminOwnerName(self, value):
        ImmHelper.validateString(value, self._dn, "SaImmAttrAdminOwnerName")
        self._SaImmAttrAdminOwnerName = value

    def updateParams(self, params, canttouchthis):
        for (param, value) in params.items():
            if param in canttouchthis:
                error("Setting attribute " + param + " in object " + self.getDn() + " is not supported")
            if param == "saAmfSvctMaxNumCSIs":
                self.setsaAmfSvctMaxNumCSIs(value)
            else:
                error("Object " + self.getDn() + " has no attribute named " + param)

    def diff(self, other, fullCheck = False):
        changedAttrs = []
        if (fullCheck or self._saAmfSvctMaxNumCSIs != None) and other._saAmfSvctMaxNumCSIs != self._saAmfSvctMaxNumCSIs:
            changedAttrs.append("saAmfSvctMaxNumCSIs")
        if (fullCheck or self._SaImmAttrImplementerName != None) and other._SaImmAttrImplementerName != self._SaImmAttrImplementerName:
            changedAttrs.append("SaImmAttrImplementerName")
        if (fullCheck or self._SaImmAttrClassName != None) and other._SaImmAttrClassName != self._SaImmAttrClassName:
            changedAttrs.append("SaImmAttrClassName")
        if (fullCheck or self._SaImmAttrAdminOwnerName != None) and other._SaImmAttrAdminOwnerName != self._SaImmAttrAdminOwnerName:
            changedAttrs.append("SaImmAttrAdminOwnerName")
        return changedAttrs

    def parseXML(self, node):
        dns = node.getElementsByTagName("dn")
        if len(dns) != 1:
            error("object has " + str(len(dns)) + " dn(s) but it should have one")
        self._dn = dns[0].childNodes[0].nodeValue
        for attribute in node.getElementsByTagName("attr"):
            names = attribute.getElementsByTagName("name")
            if len(names) != 1:
                error("object attribute has " + str(len(names)) + " name(s) but it should have one")
            name = names[0].childNodes[0].nodeValue
            setFunc = None
            if name == "SaImmAttrImplementerName":
                continue
            elif name == "SaImmAttrAdminOwnerName":
                continue
            elif name == "SaImmAttrClassName":
                continue
            elif name == "saAmfSvctMaxNumCSIs":
                setFunc = self.setsaAmfSvctMaxNumCSIs
            elif name == "SaImmAttrImplementerName":
                setFunc = self.setSaImmAttrImplementerName
            elif name == "SaImmAttrClassName":
                setFunc = self.setSaImmAttrClassName
            elif name == "SaImmAttrAdminOwnerName":
                setFunc = self.setSaImmAttrAdminOwnerName
            elif name.startswith("osaf"):
                continue # ignore OpenSAF specific attributes
            else:
                error("unknown attribute called " + name + " defined in object " + self._dn)
            for value in attribute.getElementsByTagName("value"):
                setFunc(value.childNodes[0].nodeValue)

    def writeXML(self, parent, doc):
        obj = doc.createElement("object")
        parent.appendChild(obj)
        obj.setAttribute("class", "SaAmfSvcTypeCSTypes")
        dn = doc.createElement("dn")
        obj.appendChild(dn)
        dn.appendChild(doc.createTextNode(self._dn))
        ImmHelper.writeSingleAttribute("saAmfSvctMaxNumCSIs", self._saAmfSvctMaxNumCSIs, doc, obj)
        ImmHelper.writeSingleAttribute("SaImmAttrImplementerName", self._SaImmAttrImplementerName, doc, obj)
        ImmHelper.writeSingleAttribute("SaImmAttrClassName", self._SaImmAttrClassName, doc, obj)
        ImmHelper.writeSingleAttribute("SaImmAttrAdminOwnerName", self._SaImmAttrAdminOwnerName, doc, obj)


class SaAmfSvcType(object):
    def __init__(self):
        self._dn = None
        self._saAmfSvcDefStandbyWeight = []
        self._saAmfSvcDefActiveWeight = []
        self._SaImmAttrImplementerName = None
        self._SaImmAttrClassName = None
        self._SaImmAttrAdminOwnerName = None

    @staticmethod
    def createDn(name, parentDn = None):
        if parentDn == None:
            parentDn = ""
        else:
            parentDn = "," + parentDn
        return "safVersion=" + ImmHelper.escapeName(name) + parentDn

    def getDn(self):
        return self._dn

    def getName(self):
        return ImmHelper.getName(self._dn)

    def getRdn(self):
        return ImmHelper.getRdn(self._dn)

    def getParentDn(self):
        return ImmHelper.getParentDn(self._dn)

    def createObjectInCampaign(self, campaign):
        parentDn = self.getParentDn()
        if parentDn == "":
            parentDn = "="
        campaign.beginCreate("SaAmfSvcType", parentDn)
        campaign.addAttribute("safVersion", "SA_IMM_ATTR_SASTRINGT", self.getRdn())
        if len(self._saAmfSvcDefStandbyWeight) > 0:
            campaign.addAttribute("saAmfSvcDefStandbyWeight", "SA_IMM_ATTR_SASTRINGT", self._saAmfSvcDefStandbyWeight)
        if len(self._saAmfSvcDefActiveWeight) > 0:
            campaign.addAttribute("saAmfSvcDefActiveWeight", "SA_IMM_ATTR_SASTRINGT", self._saAmfSvcDefActiveWeight)
        if self._SaImmAttrImplementerName != None:
            campaign.addAttribute("SaImmAttrImplementerName", "SA_IMM_ATTR_SASTRINGT", self._SaImmAttrImplementerName)
        if self._SaImmAttrClassName != None:
            campaign.addAttribute("SaImmAttrClassName", "SA_IMM_ATTR_SASTRINGT", self._SaImmAttrClassName)
        if self._SaImmAttrAdminOwnerName != None:
            campaign.addAttribute("SaImmAttrAdminOwnerName", "SA_IMM_ATTR_SASTRINGT", self._SaImmAttrAdminOwnerName)
        campaign.endCreate()

    def getsaAmfSvcDefStandbyWeight(self):
        return self._saAmfSvcDefStandbyWeight

    def getsaAmfSvcDefActiveWeight(self):
        return self._saAmfSvcDefActiveWeight

    def getSaImmAttrImplementerName(self):
        ImmHelper.validateSingle(self._SaImmAttrImplementerName, self._dn, "SaImmAttrImplementerName")
        return self._SaImmAttrImplementerName

    def getSaImmAttrClassName(self):
        ImmHelper.validateSingle(self._SaImmAttrClassName, self._dn, "SaImmAttrClassName")
        return self._SaImmAttrClassName

    def getSaImmAttrAdminOwnerName(self):
        ImmHelper.validateSingle(self._SaImmAttrAdminOwnerName, self._dn, "SaImmAttrAdminOwnerName")
        return self._SaImmAttrAdminOwnerName

    def getsaAmfSvcDefStandbyWeight_single(self):
        ImmHelper.validateSingleInList(self._saAmfSvcDefStandbyWeight, self._dn, "saAmfSvcDefStandbyWeight")
        return self._saAmfSvcDefStandbyWeight[0]

    def getsaAmfSvcDefActiveWeight_single(self):
        ImmHelper.validateSingleInList(self._saAmfSvcDefActiveWeight, self._dn, "saAmfSvcDefActiveWeight")
        return self._saAmfSvcDefActiveWeight[0]

    def getSaImmAttrImplementerName_unsafe(self):
        return self._SaImmAttrImplementerName

    def getSaImmAttrClassName_unsafe(self):
        return self._SaImmAttrClassName

    def getSaImmAttrAdminOwnerName_unsafe(self):
        return self._SaImmAttrAdminOwnerName

    def addTosaAmfSvcDefStandbyWeight(self, value):
        ImmHelper.validateString(value, self._dn, "saAmfSvcDefStandbyWeight")
        self._saAmfSvcDefStandbyWeight.append(value)

    def addTosaAmfSvcDefActiveWeight(self, value):
        ImmHelper.validateString(value, self._dn, "saAmfSvcDefActiveWeight")
        self._saAmfSvcDefActiveWeight.append(value)

    def setSaImmAttrImplementerName(self, value):
        ImmHelper.validateString(value, self._dn, "SaImmAttrImplementerName")
        self._SaImmAttrImplementerName = value

    def setSaImmAttrClassName(self, value):
        ImmHelper.validateString(value, self._dn, "SaImmAttrClassName")
        self._SaImmAttrClassName = value

    def setSaImmAttrAdminOwnerName(self, value):
        ImmHelper.validateString(value, self._dn, "SaImmAttrAdminOwnerName")
        self._SaImmAttrAdminOwnerName = value

    def updateParams(self, params, canttouchthis):
        for (param, value) in params.items():
            if param in canttouchthis:
                error("Setting attribute " + param + " in object " + self.getDn() + " is not supported")
            if param == "saAmfSvcDefStandbyWeight":
                if not isinstance(value, list):
                    value = [value]
                self._saAmfSvcDefStandbyWeight = []
                for v in value:
                    self.addTosaAmfSvcDefStandbyWeight(v)
            elif param == "saAmfSvcDefActiveWeight":
                if not isinstance(value, list):
                    value = [value]
                self._saAmfSvcDefActiveWeight = []
                for v in value:
                    self.addTosaAmfSvcDefActiveWeight(v)
            else:
                error("Object " + self.getDn() + " has no attribute named " + param)

    def diff(self, other, fullCheck = False):
        changedAttrs = []
        if fullCheck or (len(self._saAmfSvcDefStandbyWeight) != 0):
            if len(self._saAmfSvcDefStandbyWeight) != len(other._saAmfSvcDefStandbyWeight):
                changedAttrs.append("saAmfSvcDefStandbyWeight")
            else:
                difflist = list(set(self._saAmfSvcDefStandbyWeight) ^ set(other._saAmfSvcDefStandbyWeight))
                if len(difflist) > 0:
                    changedAttrs.append("saAmfSvcDefStandbyWeight")
        if fullCheck or (len(self._saAmfSvcDefActiveWeight) != 0):
            if len(self._saAmfSvcDefActiveWeight) != len(other._saAmfSvcDefActiveWeight):
                changedAttrs.append("saAmfSvcDefActiveWeight")
            else:
                difflist = list(set(self._saAmfSvcDefActiveWeight) ^ set(other._saAmfSvcDefActiveWeight))
                if len(difflist) > 0:
                    changedAttrs.append("saAmfSvcDefActiveWeight")
        if (fullCheck or self._SaImmAttrImplementerName != None) and other._SaImmAttrImplementerName != self._SaImmAttrImplementerName:
            changedAttrs.append("SaImmAttrImplementerName")
        if (fullCheck or self._SaImmAttrClassName != None) and other._SaImmAttrClassName != self._SaImmAttrClassName:
            changedAttrs.append("SaImmAttrClassName")
        if (fullCheck or self._SaImmAttrAdminOwnerName != None) and other._SaImmAttrAdminOwnerName != self._SaImmAttrAdminOwnerName:
            changedAttrs.append("SaImmAttrAdminOwnerName")
        return changedAttrs

    def parseXML(self, node):
        dns = node.getElementsByTagName("dn")
        if len(dns) != 1:
            error("object has " + str(len(dns)) + " dn(s) but it should have one")
        self._dn = dns[0].childNodes[0].nodeValue
        for attribute in node.getElementsByTagName("attr"):
            names = attribute.getElementsByTagName("name")
            if len(names) != 1:
                error("object attribute has " + str(len(names)) + " name(s) but it should have one")
            name = names[0].childNodes[0].nodeValue
            setFunc = None
            if name == "SaImmAttrImplementerName":
                continue
            elif name == "SaImmAttrAdminOwnerName":
                continue
            elif name == "SaImmAttrClassName":
                continue
            elif name == "saAmfSvcDefStandbyWeight":
                setFunc = self.addTosaAmfSvcDefStandbyWeight
            elif name == "saAmfSvcDefActiveWeight":
                setFunc = self.addTosaAmfSvcDefActiveWeight
            elif name == "SaImmAttrImplementerName":
                setFunc = self.setSaImmAttrImplementerName
            elif name == "SaImmAttrClassName":
                setFunc = self.setSaImmAttrClassName
            elif name == "SaImmAttrAdminOwnerName":
                setFunc = self.setSaImmAttrAdminOwnerName
            elif name.startswith("osaf"):
                continue # ignore OpenSAF specific attributes
            else:
                error("unknown attribute called " + name + " defined in object " + self._dn)
            for value in attribute.getElementsByTagName("value"):
                setFunc(value.childNodes[0].nodeValue)

    def writeXML(self, parent, doc):
        obj = doc.createElement("object")
        parent.appendChild(obj)
        obj.setAttribute("class", "SaAmfSvcType")
        dn = doc.createElement("dn")
        obj.appendChild(dn)
        dn.appendChild(doc.createTextNode(self._dn))
        ImmHelper.writeMultiAttributes("saAmfSvcDefStandbyWeight", self._saAmfSvcDefStandbyWeight, doc, obj)
        ImmHelper.writeMultiAttributes("saAmfSvcDefActiveWeight", self._saAmfSvcDefActiveWeight, doc, obj)
        ImmHelper.writeSingleAttribute("SaImmAttrImplementerName", self._SaImmAttrImplementerName, doc, obj)
        ImmHelper.writeSingleAttribute("SaImmAttrClassName", self._SaImmAttrClassName, doc, obj)
        ImmHelper.writeSingleAttribute("SaImmAttrAdminOwnerName", self._SaImmAttrAdminOwnerName, doc, obj)


class SaAmfSvcBaseType(object):
    def __init__(self):
        self._dn = None
        self._SaImmAttrImplementerName = None
        self._SaImmAttrClassName = None
        self._SaImmAttrAdminOwnerName = None

    @staticmethod
    def createDn(name, parentDn = None):
        if parentDn == None:
            parentDn = ""
        else:
            parentDn = "," + parentDn
        return "safSvcType=" + ImmHelper.escapeName(name) + parentDn

    def getDn(self):
        return self._dn

    def getName(self):
        return ImmHelper.getName(self._dn)

    def getRdn(self):
        return ImmHelper.getRdn(self._dn)

    def getParentDn(self):
        return ImmHelper.getParentDn(self._dn)

    def createObjectInCampaign(self, campaign):
        parentDn = self.getParentDn()
        if parentDn == "":
            parentDn = "="
        campaign.beginCreate("SaAmfSvcBaseType", parentDn)
        campaign.addAttribute("safSvcType", "SA_IMM_ATTR_SASTRINGT", self.getRdn())
        if self._SaImmAttrImplementerName != None:
            campaign.addAttribute("SaImmAttrImplementerName", "SA_IMM_ATTR_SASTRINGT", self._SaImmAttrImplementerName)
        if self._SaImmAttrClassName != None:
            campaign.addAttribute("SaImmAttrClassName", "SA_IMM_ATTR_SASTRINGT", self._SaImmAttrClassName)
        if self._SaImmAttrAdminOwnerName != None:
            campaign.addAttribute("SaImmAttrAdminOwnerName", "SA_IMM_ATTR_SASTRINGT", self._SaImmAttrAdminOwnerName)
        campaign.endCreate()

    def getSaImmAttrImplementerName(self):
        ImmHelper.validateSingle(self._SaImmAttrImplementerName, self._dn, "SaImmAttrImplementerName")
        return self._SaImmAttrImplementerName

    def getSaImmAttrClassName(self):
        ImmHelper.validateSingle(self._SaImmAttrClassName, self._dn, "SaImmAttrClassName")
        return self._SaImmAttrClassName

    def getSaImmAttrAdminOwnerName(self):
        ImmHelper.validateSingle(self._SaImmAttrAdminOwnerName, self._dn, "SaImmAttrAdminOwnerName")
        return self._SaImmAttrAdminOwnerName

    def getSaImmAttrImplementerName_unsafe(self):
        return self._SaImmAttrImplementerName

    def getSaImmAttrClassName_unsafe(self):
        return self._SaImmAttrClassName

    def getSaImmAttrAdminOwnerName_unsafe(self):
        return self._SaImmAttrAdminOwnerName

    def setSaImmAttrImplementerName(self, value):
        ImmHelper.validateString(value, self._dn, "SaImmAttrImplementerName")
        self._SaImmAttrImplementerName = value

    def setSaImmAttrClassName(self, value):
        ImmHelper.validateString(value, self._dn, "SaImmAttrClassName")
        self._SaImmAttrClassName = value

    def setSaImmAttrAdminOwnerName(self, value):
        ImmHelper.validateString(value, self._dn, "SaImmAttrAdminOwnerName")
        self._SaImmAttrAdminOwnerName = value

    def updateParams(self, params, canttouchthis):
        for (param, value) in params.items():
            if param in canttouchthis:
                error("Setting attribute " + param + " in object " + self.getDn() + " is not supported")
            else:
                error("Object " + self.getDn() + " has no attribute named " + param)

    def diff(self, other, fullCheck = False):
        changedAttrs = []
        if (fullCheck or self._SaImmAttrImplementerName != None) and other._SaImmAttrImplementerName != self._SaImmAttrImplementerName:
            changedAttrs.append("SaImmAttrImplementerName")
        if (fullCheck or self._SaImmAttrClassName != None) and other._SaImmAttrClassName != self._SaImmAttrClassName:
            changedAttrs.append("SaImmAttrClassName")
        if (fullCheck or self._SaImmAttrAdminOwnerName != None) and other._SaImmAttrAdminOwnerName != self._SaImmAttrAdminOwnerName:
            changedAttrs.append("SaImmAttrAdminOwnerName")
        return changedAttrs

    def parseXML(self, node):
        dns = node.getElementsByTagName("dn")
        if len(dns) != 1:
            error("object has " + str(len(dns)) + " dn(s) but it should have one")
        self._dn = dns[0].childNodes[0].nodeValue
        for attribute in node.getElementsByTagName("attr"):
            names = attribute.getElementsByTagName("name")
            if len(names) != 1:
                error("object attribute has " + str(len(names)) + " name(s) but it should have one")
            name = names[0].childNodes[0].nodeValue
            setFunc = None
            if name == "SaImmAttrImplementerName":
                continue
            elif name == "SaImmAttrAdminOwnerName":
                continue
            elif name == "SaImmAttrClassName":
                continue
            elif name == "SaImmAttrImplementerName":
                setFunc = self.setSaImmAttrImplementerName
            elif name == "SaImmAttrClassName":
                setFunc = self.setSaImmAttrClassName
            elif name == "SaImmAttrAdminOwnerName":
                setFunc = self.setSaImmAttrAdminOwnerName
            elif name.startswith("osaf"):
                continue # ignore OpenSAF specific attributes
            else:
                error("unknown attribute called " + name + " defined in object " + self._dn)
            for value in attribute.getElementsByTagName("value"):
                setFunc(value.childNodes[0].nodeValue)

    def writeXML(self, parent, doc):
        obj = doc.createElement("object")
        parent.appendChild(obj)
        obj.setAttribute("class", "SaAmfSvcBaseType")
        dn = doc.createElement("dn")
        obj.appendChild(dn)
        dn.appendChild(doc.createTextNode(self._dn))
        ImmHelper.writeSingleAttribute("SaImmAttrImplementerName", self._SaImmAttrImplementerName, doc, obj)
        ImmHelper.writeSingleAttribute("SaImmAttrClassName", self._SaImmAttrClassName, doc, obj)
        ImmHelper.writeSingleAttribute("SaImmAttrAdminOwnerName", self._SaImmAttrAdminOwnerName, doc, obj)


class SaAmfSutCompType(object):
    def __init__(self):
        self._dn = None
        self._saAmfSutMinNumComponents = None
        self._saAmfSutMaxNumComponents = None
        self._SaImmAttrImplementerName = None
        self._SaImmAttrClassName = None
        self._SaImmAttrAdminOwnerName = None

    @staticmethod
    def createDn(name, parentDn = None):
        if parentDn == None:
            parentDn = ""
        else:
            parentDn = "," + parentDn
        return "safMemberCompType=" + ImmHelper.escapeName(name) + parentDn

    def getDn(self):
        return self._dn

    def getName(self):
        return ImmHelper.getName(self._dn)

    def getRdn(self):
        return ImmHelper.getRdn(self._dn)

    def getParentDn(self):
        return ImmHelper.getParentDn(self._dn)

    def getCompType(self):
        comp_type = re.sub(r'safMemberCompType=','',ImmHelper.getRdn(self._dn))
        return re.sub(r'\\','',comp_type)

    def createObjectInCampaign(self, campaign):
        parentDn = self.getParentDn()
        if parentDn == "":
            parentDn = "="
        campaign.beginCreate("SaAmfSutCompType", parentDn)
        campaign.addAttribute("safMemberCompType", "SA_IMM_ATTR_SANAMET", self.getRdn())
        if self._saAmfSutMinNumComponents != None:
            campaign.addAttribute("saAmfSutMinNumComponents", "SA_IMM_ATTR_SAUINT32T", self._saAmfSutMinNumComponents)
        if self._saAmfSutMaxNumComponents != None:
            campaign.addAttribute("saAmfSutMaxNumComponents", "SA_IMM_ATTR_SAUINT32T", self._saAmfSutMaxNumComponents)
        if self._SaImmAttrImplementerName != None:
            campaign.addAttribute("SaImmAttrImplementerName", "SA_IMM_ATTR_SASTRINGT", self._SaImmAttrImplementerName)
        if self._SaImmAttrClassName != None:
            campaign.addAttribute("SaImmAttrClassName", "SA_IMM_ATTR_SASTRINGT", self._SaImmAttrClassName)
        if self._SaImmAttrAdminOwnerName != None:
            campaign.addAttribute("SaImmAttrAdminOwnerName", "SA_IMM_ATTR_SASTRINGT", self._SaImmAttrAdminOwnerName)
        campaign.endCreate()

    def getsaAmfSutMinNumComponents(self):
        ImmHelper.validateSingle(self._saAmfSutMinNumComponents, self._dn, "saAmfSutMinNumComponents")
        return self._saAmfSutMinNumComponents

    def getsaAmfSutMaxNumComponents(self):
        ImmHelper.validateSingle(self._saAmfSutMaxNumComponents, self._dn, "saAmfSutMaxNumComponents")
        return self._saAmfSutMaxNumComponents

    def getSaImmAttrImplementerName(self):
        ImmHelper.validateSingle(self._SaImmAttrImplementerName, self._dn, "SaImmAttrImplementerName")
        return self._SaImmAttrImplementerName

    def getSaImmAttrClassName(self):
        ImmHelper.validateSingle(self._SaImmAttrClassName, self._dn, "SaImmAttrClassName")
        return self._SaImmAttrClassName

    def getSaImmAttrAdminOwnerName(self):
        ImmHelper.validateSingle(self._SaImmAttrAdminOwnerName, self._dn, "SaImmAttrAdminOwnerName")
        return self._SaImmAttrAdminOwnerName

    def getsaAmfSutMinNumComponents_unsafe(self):
        return self._saAmfSutMinNumComponents

    def getsaAmfSutMaxNumComponents_unsafe(self):
        return self._saAmfSutMaxNumComponents

    def getSaImmAttrImplementerName_unsafe(self):
        return self._SaImmAttrImplementerName

    def getSaImmAttrClassName_unsafe(self):
        return self._SaImmAttrClassName

    def getSaImmAttrAdminOwnerName_unsafe(self):
        return self._SaImmAttrAdminOwnerName

    def setsaAmfSutMinNumComponents(self, value):
        ImmHelper.validateUint32(value, self._dn, "saAmfSutMinNumComponents")
        value = str(value)
        self._saAmfSutMinNumComponents = value

    def setsaAmfSutMaxNumComponents(self, value):
        ImmHelper.validateUint32(value, self._dn, "saAmfSutMaxNumComponents")
        value = str(value)
        self._saAmfSutMaxNumComponents = value

    def setSaImmAttrImplementerName(self, value):
        ImmHelper.validateString(value, self._dn, "SaImmAttrImplementerName")
        self._SaImmAttrImplementerName = value

    def setSaImmAttrClassName(self, value):
        ImmHelper.validateString(value, self._dn, "SaImmAttrClassName")
        self._SaImmAttrClassName = value

    def setSaImmAttrAdminOwnerName(self, value):
        ImmHelper.validateString(value, self._dn, "SaImmAttrAdminOwnerName")
        self._SaImmAttrAdminOwnerName = value

    def updateParams(self, params, canttouchthis):
        for (param, value) in params.items():
            if param in canttouchthis:
                error("Setting attribute " + param + " in object " + self.getDn() + " is not supported")
            else:
                error("Object " + self.getDn() + " has no attribute named " + param)

    def diff(self, other, fullCheck = False):
        changedAttrs = []
        if (fullCheck or self._saAmfSutMinNumComponents != None) and other._saAmfSutMinNumComponents != self._saAmfSutMinNumComponents:
            changedAttrs.append("saAmfSutMinNumComponents")
        if (fullCheck or self._saAmfSutMaxNumComponents != None) and other._saAmfSutMaxNumComponents != self._saAmfSutMaxNumComponents:
            changedAttrs.append("saAmfSutMaxNumComponents")
        if (fullCheck or self._SaImmAttrImplementerName != None) and other._SaImmAttrImplementerName != self._SaImmAttrImplementerName:
            changedAttrs.append("SaImmAttrImplementerName")
        if (fullCheck or self._SaImmAttrClassName != None) and other._SaImmAttrClassName != self._SaImmAttrClassName:
            changedAttrs.append("SaImmAttrClassName")
        if (fullCheck or self._SaImmAttrAdminOwnerName != None) and other._SaImmAttrAdminOwnerName != self._SaImmAttrAdminOwnerName:
            changedAttrs.append("SaImmAttrAdminOwnerName")
        return changedAttrs

    def parseXML(self, node):
        dns = node.getElementsByTagName("dn")
        if len(dns) != 1:
            error("object has " + str(len(dns)) + " dn(s) but it should have one")
        self._dn = dns[0].childNodes[0].nodeValue
        for attribute in node.getElementsByTagName("attr"):
            names = attribute.getElementsByTagName("name")
            if len(names) != 1:
                error("object attribute has " + str(len(names)) + " name(s) but it should have one")
            name = names[0].childNodes[0].nodeValue
            setFunc = None
            if name == "SaImmAttrImplementerName":
                continue
            elif name == "SaImmAttrAdminOwnerName":
                continue
            elif name == "SaImmAttrClassName":
                continue
            elif name == "saAmfSutMinNumComponents":
                setFunc = self.setsaAmfSutMinNumComponents
            elif name == "saAmfSutMaxNumComponents":
                setFunc = self.setsaAmfSutMaxNumComponents
            elif name == "SaImmAttrImplementerName":
                setFunc = self.setSaImmAttrImplementerName
            elif name == "SaImmAttrClassName":
                setFunc = self.setSaImmAttrClassName
            elif name == "SaImmAttrAdminOwnerName":
                setFunc = self.setSaImmAttrAdminOwnerName
            elif name.startswith("osaf"):
                continue # ignore OpenSAF specific attributes
            else:
                error("unknown attribute called " + name + " defined in object " + self._dn)
            for value in attribute.getElementsByTagName("value"):
                setFunc(value.childNodes[0].nodeValue)

    def writeXML(self, parent, doc):
        obj = doc.createElement("object")
        parent.appendChild(obj)
        obj.setAttribute("class", "SaAmfSutCompType")
        dn = doc.createElement("dn")
        obj.appendChild(dn)
        dn.appendChild(doc.createTextNode(self._dn))
        ImmHelper.writeSingleAttribute("saAmfSutMinNumComponents", self._saAmfSutMinNumComponents, doc, obj)
        ImmHelper.writeSingleAttribute("saAmfSutMaxNumComponents", self._saAmfSutMaxNumComponents, doc, obj)
        ImmHelper.writeSingleAttribute("SaImmAttrImplementerName", self._SaImmAttrImplementerName, doc, obj)
        ImmHelper.writeSingleAttribute("SaImmAttrClassName", self._SaImmAttrClassName, doc, obj)
        ImmHelper.writeSingleAttribute("SaImmAttrAdminOwnerName", self._SaImmAttrAdminOwnerName, doc, obj)


class SaAmfSUType(object):
    def __init__(self):
        self._dn = None
        self._saAmfSutProvidesSvcTypes = []
        self._saAmfSutIsExternal = None
        self._saAmfSutDefSUFailover = None
        self._SaImmAttrImplementerName = None
        self._SaImmAttrClassName = None
        self._SaImmAttrAdminOwnerName = None

    @staticmethod
    def createDn(name, parentDn = None):
        if parentDn == None:
            parentDn = ""
        else:
            parentDn = "," + parentDn
        return "safVersion=" + ImmHelper.escapeName(name) + parentDn

    def getDn(self):
        return self._dn

    def getName(self):
        return ImmHelper.getName(self._dn)

    def getRdn(self):
        return ImmHelper.getRdn(self._dn)

    def getParentDn(self):
        return ImmHelper.getParentDn(self._dn)

    def createObjectInCampaign(self, campaign):
        parentDn = self.getParentDn()
        if parentDn == "":
            parentDn = "="
        campaign.beginCreate("SaAmfSUType", parentDn)
        campaign.addAttribute("safVersion", "SA_IMM_ATTR_SASTRINGT", self.getRdn())
        if len(self._saAmfSutProvidesSvcTypes) > 0:
            campaign.addAttribute("saAmfSutProvidesSvcTypes", "SA_IMM_ATTR_SANAMET", self._saAmfSutProvidesSvcTypes)
        if self._saAmfSutIsExternal != None:
            campaign.addAttribute("saAmfSutIsExternal", "SA_IMM_ATTR_SAUINT32T", self._saAmfSutIsExternal)
        if self._saAmfSutDefSUFailover != None:
            campaign.addAttribute("saAmfSutDefSUFailover", "SA_IMM_ATTR_SAUINT32T", self._saAmfSutDefSUFailover)
        if self._SaImmAttrImplementerName != None:
            campaign.addAttribute("SaImmAttrImplementerName", "SA_IMM_ATTR_SASTRINGT", self._SaImmAttrImplementerName)
        if self._SaImmAttrClassName != None:
            campaign.addAttribute("SaImmAttrClassName", "SA_IMM_ATTR_SASTRINGT", self._SaImmAttrClassName)
        if self._SaImmAttrAdminOwnerName != None:
            campaign.addAttribute("SaImmAttrAdminOwnerName", "SA_IMM_ATTR_SASTRINGT", self._SaImmAttrAdminOwnerName)
        campaign.endCreate()

    def getsaAmfSutProvidesSvcTypes(self):
        return self._saAmfSutProvidesSvcTypes

    def getsaAmfSutIsExternal(self):
        ImmHelper.validateSingle(self._saAmfSutIsExternal, self._dn, "saAmfSutIsExternal")
        return self._saAmfSutIsExternal

    def getsaAmfSutDefSUFailover(self):
        ImmHelper.validateSingle(self._saAmfSutDefSUFailover, self._dn, "saAmfSutDefSUFailover")
        return self._saAmfSutDefSUFailover

    def getSaImmAttrImplementerName(self):
        ImmHelper.validateSingle(self._SaImmAttrImplementerName, self._dn, "SaImmAttrImplementerName")
        return self._SaImmAttrImplementerName

    def getSaImmAttrClassName(self):
        ImmHelper.validateSingle(self._SaImmAttrClassName, self._dn, "SaImmAttrClassName")
        return self._SaImmAttrClassName

    def getSaImmAttrAdminOwnerName(self):
        ImmHelper.validateSingle(self._SaImmAttrAdminOwnerName, self._dn, "SaImmAttrAdminOwnerName")
        return self._SaImmAttrAdminOwnerName

    def getsaAmfSutProvidesSvcTypes_single(self):
        ImmHelper.validateSingleInList(self._saAmfSutProvidesSvcTypes, self._dn, "saAmfSutProvidesSvcTypes")
        return self._saAmfSutProvidesSvcTypes[0]

    def getsaAmfSutIsExternal_unsafe(self):
        return self._saAmfSutIsExternal

    def getsaAmfSutDefSUFailover_unsafe(self):
        return self._saAmfSutDefSUFailover

    def getSaImmAttrImplementerName_unsafe(self):
        return self._SaImmAttrImplementerName

    def getSaImmAttrClassName_unsafe(self):
        return self._SaImmAttrClassName

    def getSaImmAttrAdminOwnerName_unsafe(self):
        return self._SaImmAttrAdminOwnerName

    def addTosaAmfSutProvidesSvcTypes(self, value):
        ImmHelper.validateName(value, self._dn, "saAmfSutProvidesSvcTypes")
        self._saAmfSutProvidesSvcTypes.append(value)

    def setsaAmfSutIsExternal(self, value):
        ImmHelper.validateUint32(value, self._dn, "saAmfSutIsExternal")
        value = str(value)
        self._saAmfSutIsExternal = value

    def setsaAmfSutDefSUFailover(self, value):
        ImmHelper.validateUint32(value, self._dn, "saAmfSutDefSUFailover")
        value = str(value)
        self._saAmfSutDefSUFailover = value

    def setSaImmAttrImplementerName(self, value):
        ImmHelper.validateString(value, self._dn, "SaImmAttrImplementerName")
        self._SaImmAttrImplementerName = value

    def setSaImmAttrClassName(self, value):
        ImmHelper.validateString(value, self._dn, "SaImmAttrClassName")
        self._SaImmAttrClassName = value

    def setSaImmAttrAdminOwnerName(self, value):
        ImmHelper.validateString(value, self._dn, "SaImmAttrAdminOwnerName")
        self._SaImmAttrAdminOwnerName = value

    def updateParams(self, params, canttouchthis):
        for (param, value) in params.items():
            if param in canttouchthis:
                error("Setting attribute " + param + " in object " + self.getDn() + " is not supported")
            if param == "saAmfSutProvidesSvcTypes":
                if not isinstance(value, list):
                    value = [value]
                self._saAmfSutProvidesSvcTypes = []
                for v in value:
                    self.addTosaAmfSutProvidesSvcTypes(v)
            elif param == "saAmfSutDefSUFailover":
                self.setsaAmfSutDefSUFailover(value)
            else:
                error("Object " + self.getDn() + " has no attribute named " + param)

    def diff(self, other, fullCheck = False):
        changedAttrs = []
        if fullCheck or (len(self._saAmfSutProvidesSvcTypes) != 0):
            if len(self._saAmfSutProvidesSvcTypes) != len(other._saAmfSutProvidesSvcTypes):
                changedAttrs.append("saAmfSutProvidesSvcTypes")
            else:
                difflist = list(set(self._saAmfSutProvidesSvcTypes) ^ set(other._saAmfSutProvidesSvcTypes))
                if len(difflist) > 0:
                    changedAttrs.append("saAmfSutProvidesSvcTypes")
        if (fullCheck or self._saAmfSutIsExternal != None) and other._saAmfSutIsExternal != self._saAmfSutIsExternal:
            changedAttrs.append("saAmfSutIsExternal")
        if (fullCheck or self._saAmfSutDefSUFailover != None) and other._saAmfSutDefSUFailover != self._saAmfSutDefSUFailover:
            changedAttrs.append("saAmfSutDefSUFailover")
        if (fullCheck or self._SaImmAttrImplementerName != None) and other._SaImmAttrImplementerName != self._SaImmAttrImplementerName:
            changedAttrs.append("SaImmAttrImplementerName")
        if (fullCheck or self._SaImmAttrClassName != None) and other._SaImmAttrClassName != self._SaImmAttrClassName:
            changedAttrs.append("SaImmAttrClassName")
        if (fullCheck or self._SaImmAttrAdminOwnerName != None) and other._SaImmAttrAdminOwnerName != self._SaImmAttrAdminOwnerName:
            changedAttrs.append("SaImmAttrAdminOwnerName")
        return changedAttrs

    def parseXML(self, node):
        dns = node.getElementsByTagName("dn")
        if len(dns) != 1:
            error("object has " + str(len(dns)) + " dn(s) but it should have one")
        self._dn = dns[0].childNodes[0].nodeValue
        for attribute in node.getElementsByTagName("attr"):
            names = attribute.getElementsByTagName("name")
            if len(names) != 1:
                error("object attribute has " + str(len(names)) + " name(s) but it should have one")
            name = names[0].childNodes[0].nodeValue
            setFunc = None
            if name == "SaImmAttrImplementerName":
                continue
            elif name == "SaImmAttrAdminOwnerName":
                continue
            elif name == "SaImmAttrClassName":
                continue
            elif name == "saAmfSutProvidesSvcTypes":
                setFunc = self.addTosaAmfSutProvidesSvcTypes
            elif name == "saAmfSutIsExternal":
                setFunc = self.setsaAmfSutIsExternal
            elif name == "saAmfSutDefSUFailover":
                setFunc = self.setsaAmfSutDefSUFailover
            elif name == "SaImmAttrImplementerName":
                setFunc = self.setSaImmAttrImplementerName
            elif name == "SaImmAttrClassName":
                setFunc = self.setSaImmAttrClassName
            elif name == "SaImmAttrAdminOwnerName":
                setFunc = self.setSaImmAttrAdminOwnerName
            elif name.startswith("osaf"):
                continue # ignore OpenSAF specific attributes
            else:
                error("unknown attribute called " + name + " defined in object " + self._dn)
            for value in attribute.getElementsByTagName("value"):
                setFunc(value.childNodes[0].nodeValue)

    def writeXML(self, parent, doc):
        obj = doc.createElement("object")
        parent.appendChild(obj)
        obj.setAttribute("class", "SaAmfSUType")
        dn = doc.createElement("dn")
        obj.appendChild(dn)
        dn.appendChild(doc.createTextNode(self._dn))
        ImmHelper.writeMultiAttributes("saAmfSutProvidesSvcTypes", self._saAmfSutProvidesSvcTypes, doc, obj)
        ImmHelper.writeSingleAttribute("saAmfSutIsExternal", self._saAmfSutIsExternal, doc, obj)
        ImmHelper.writeSingleAttribute("saAmfSutDefSUFailover", self._saAmfSutDefSUFailover, doc, obj)
        ImmHelper.writeSingleAttribute("SaImmAttrImplementerName", self._SaImmAttrImplementerName, doc, obj)
        ImmHelper.writeSingleAttribute("SaImmAttrClassName", self._SaImmAttrClassName, doc, obj)
        ImmHelper.writeSingleAttribute("SaImmAttrAdminOwnerName", self._SaImmAttrAdminOwnerName, doc, obj)


class SaAmfSUBaseType(object):
    def __init__(self):
        self._dn = None
        self._SaImmAttrImplementerName = None
        self._SaImmAttrClassName = None
        self._SaImmAttrAdminOwnerName = None

    @staticmethod
    def createDn(name, parentDn = None):
        if parentDn == None:
            parentDn = ""
        else:
            parentDn = "," + parentDn
        return "safSuType=" + ImmHelper.escapeName(name) + parentDn

    def getDn(self):
        return self._dn

    def getName(self):
        return ImmHelper.getName(self._dn)

    def getRdn(self):
        return ImmHelper.getRdn(self._dn)

    def getParentDn(self):
        return ImmHelper.getParentDn(self._dn)

    def createObjectInCampaign(self, campaign):
        parentDn = self.getParentDn()
        if parentDn == "":
            parentDn = "="
        campaign.beginCreate("SaAmfSUBaseType", parentDn)
        campaign.addAttribute("safSuType", "SA_IMM_ATTR_SASTRINGT", self.getRdn())
        if self._SaImmAttrImplementerName != None:
            campaign.addAttribute("SaImmAttrImplementerName", "SA_IMM_ATTR_SASTRINGT", self._SaImmAttrImplementerName)
        if self._SaImmAttrClassName != None:
            campaign.addAttribute("SaImmAttrClassName", "SA_IMM_ATTR_SASTRINGT", self._SaImmAttrClassName)
        if self._SaImmAttrAdminOwnerName != None:
            campaign.addAttribute("SaImmAttrAdminOwnerName", "SA_IMM_ATTR_SASTRINGT", self._SaImmAttrAdminOwnerName)
        campaign.endCreate()

    def getSaImmAttrImplementerName(self):
        ImmHelper.validateSingle(self._SaImmAttrImplementerName, self._dn, "SaImmAttrImplementerName")
        return self._SaImmAttrImplementerName

    def getSaImmAttrClassName(self):
        ImmHelper.validateSingle(self._SaImmAttrClassName, self._dn, "SaImmAttrClassName")
        return self._SaImmAttrClassName

    def getSaImmAttrAdminOwnerName(self):
        ImmHelper.validateSingle(self._SaImmAttrAdminOwnerName, self._dn, "SaImmAttrAdminOwnerName")
        return self._SaImmAttrAdminOwnerName

    def getSaImmAttrImplementerName_unsafe(self):
        return self._SaImmAttrImplementerName

    def getSaImmAttrClassName_unsafe(self):
        return self._SaImmAttrClassName

    def getSaImmAttrAdminOwnerName_unsafe(self):
        return self._SaImmAttrAdminOwnerName

    def setSaImmAttrImplementerName(self, value):
        ImmHelper.validateString(value, self._dn, "SaImmAttrImplementerName")
        self._SaImmAttrImplementerName = value

    def setSaImmAttrClassName(self, value):
        ImmHelper.validateString(value, self._dn, "SaImmAttrClassName")
        self._SaImmAttrClassName = value

    def setSaImmAttrAdminOwnerName(self, value):
        ImmHelper.validateString(value, self._dn, "SaImmAttrAdminOwnerName")
        self._SaImmAttrAdminOwnerName = value

    def updateParams(self, params, canttouchthis):
        for (param, value) in params.items():
            if param in canttouchthis:
                error("Setting attribute " + param + " in object " + self.getDn() + " is not supported")
            else:
                error("Object " + self.getDn() + " has no attribute named " + param)

    def diff(self, other, fullCheck = False):
        changedAttrs = []
        if (fullCheck or self._SaImmAttrImplementerName != None) and other._SaImmAttrImplementerName != self._SaImmAttrImplementerName:
            changedAttrs.append("SaImmAttrImplementerName")
        if (fullCheck or self._SaImmAttrClassName != None) and other._SaImmAttrClassName != self._SaImmAttrClassName:
            changedAttrs.append("SaImmAttrClassName")
        if (fullCheck or self._SaImmAttrAdminOwnerName != None) and other._SaImmAttrAdminOwnerName != self._SaImmAttrAdminOwnerName:
            changedAttrs.append("SaImmAttrAdminOwnerName")
        return changedAttrs

    def parseXML(self, node):
        dns = node.getElementsByTagName("dn")
        if len(dns) != 1:
            error("object has " + str(len(dns)) + " dn(s) but it should have one")
        self._dn = dns[0].childNodes[0].nodeValue
        for attribute in node.getElementsByTagName("attr"):
            names = attribute.getElementsByTagName("name")
            if len(names) != 1:
                error("object attribute has " + str(len(names)) + " name(s) but it should have one")
            name = names[0].childNodes[0].nodeValue
            setFunc = None
            if name == "SaImmAttrImplementerName":
                continue
            elif name == "SaImmAttrAdminOwnerName":
                continue
            elif name == "SaImmAttrClassName":
                continue
            elif name == "SaImmAttrImplementerName":
                setFunc = self.setSaImmAttrImplementerName
            elif name == "SaImmAttrClassName":
                setFunc = self.setSaImmAttrClassName
            elif name == "SaImmAttrAdminOwnerName":
                setFunc = self.setSaImmAttrAdminOwnerName
            elif name.startswith("osaf"):
                continue # ignore OpenSAF specific attributes
            else:
                error("unknown attribute called " + name + " defined in object " + self._dn)
            for value in attribute.getElementsByTagName("value"):
                setFunc(value.childNodes[0].nodeValue)

    def writeXML(self, parent, doc):
        obj = doc.createElement("object")
        parent.appendChild(obj)
        obj.setAttribute("class", "SaAmfSUBaseType")
        dn = doc.createElement("dn")
        obj.appendChild(dn)
        dn.appendChild(doc.createTextNode(self._dn))
        ImmHelper.writeSingleAttribute("SaImmAttrImplementerName", self._SaImmAttrImplementerName, doc, obj)
        ImmHelper.writeSingleAttribute("SaImmAttrClassName", self._SaImmAttrClassName, doc, obj)
        ImmHelper.writeSingleAttribute("SaImmAttrAdminOwnerName", self._SaImmAttrAdminOwnerName, doc, obj)


class SaAmfSU(object):
    def __init__(self):
        self._dn = None
        self._saAmfSUType = None
        self._saAmfSURestartCount = None
        self._saAmfSUReadinessState = None
        self._saAmfSURank = None
        self._saAmfSUPresenceState = None
        self._saAmfSUPreInstantiable = None
        self._saAmfSUOperState = None
        self._saAmfSUNumCurrStandbySIs = None
        self._saAmfSUNumCurrActiveSIs = None
        self._saAmfSUMaintenanceCampaign = None
        self._saAmfSUHostedByNode = None
        self._saAmfSUHostNodeOrNodeGroup = None
        self._saAmfSUFailover = None
        self._saAmfSUAssignedSIs = []
        self._saAmfSUAdminState = None
        self._SaImmAttrImplementerName = None
        self._SaImmAttrClassName = None
        self._SaImmAttrAdminOwnerName = None

    @staticmethod
    def createDn(name, parentDn = None):
        if parentDn == None:
            parentDn = ""
        else:
            parentDn = "," + parentDn
        return "safSu=" + ImmHelper.escapeName(name) + parentDn

    def getDn(self):
        return self._dn

    def getName(self):
        return ImmHelper.getName(self._dn)

    def getRdn(self):
        return ImmHelper.getRdn(self._dn)

    def getParentDn(self):
        return ImmHelper.getParentDn(self._dn)

    def createObjectInCampaign(self, campaign):
        parentDn = self.getParentDn()
        if parentDn == "":
            parentDn = "="
        campaign.beginCreate("SaAmfSU", parentDn)
        campaign.addAttribute("safSu", "SA_IMM_ATTR_SASTRINGT", self.getRdn())
        if self._saAmfSUType != None:
            campaign.addAttribute("saAmfSUType", "SA_IMM_ATTR_SANAMET", self._saAmfSUType)
        if self._saAmfSURank != None:
            campaign.addAttribute("saAmfSURank", "SA_IMM_ATTR_SAUINT32T", self._saAmfSURank)
        if self._saAmfSUMaintenanceCampaign != None:
            campaign.addAttribute("saAmfSUMaintenanceCampaign", "SA_IMM_ATTR_SANAMET", self._saAmfSUMaintenanceCampaign)
        if self._saAmfSUHostNodeOrNodeGroup != None:
            campaign.addAttribute("saAmfSUHostNodeOrNodeGroup", "SA_IMM_ATTR_SANAMET", self._saAmfSUHostNodeOrNodeGroup)
        if self._saAmfSUFailover != None:
            campaign.addAttribute("saAmfSUFailover", "SA_IMM_ATTR_SAUINT32T", self._saAmfSUFailover)
        if self._saAmfSUAdminState != None:
            campaign.addAttribute("saAmfSUAdminState", "SA_IMM_ATTR_SAUINT32T", self._saAmfSUAdminState)
        if self._SaImmAttrImplementerName != None:
            campaign.addAttribute("SaImmAttrImplementerName", "SA_IMM_ATTR_SASTRINGT", self._SaImmAttrImplementerName)
        if self._SaImmAttrClassName != None:
            campaign.addAttribute("SaImmAttrClassName", "SA_IMM_ATTR_SASTRINGT", self._SaImmAttrClassName)
        if self._SaImmAttrAdminOwnerName != None:
            campaign.addAttribute("SaImmAttrAdminOwnerName", "SA_IMM_ATTR_SASTRINGT", self._SaImmAttrAdminOwnerName)
        campaign.endCreate()

    def getsaAmfSUType(self):
        ImmHelper.validateSingle(self._saAmfSUType, self._dn, "saAmfSUType")
        return self._saAmfSUType

    def getsaAmfSURestartCount(self):
        ImmHelper.validateSingle(self._saAmfSURestartCount, self._dn, "saAmfSURestartCount")
        return self._saAmfSURestartCount

    def getsaAmfSUReadinessState(self):
        ImmHelper.validateSingle(self._saAmfSUReadinessState, self._dn, "saAmfSUReadinessState")
        return self._saAmfSUReadinessState

    def getsaAmfSURank(self):
        ImmHelper.validateSingle(self._saAmfSURank, self._dn, "saAmfSURank")
        return self._saAmfSURank

    def getsaAmfSUPresenceState(self):
        ImmHelper.validateSingle(self._saAmfSUPresenceState, self._dn, "saAmfSUPresenceState")
        return self._saAmfSUPresenceState

    def getsaAmfSUPreInstantiable(self):
        ImmHelper.validateSingle(self._saAmfSUPreInstantiable, self._dn, "saAmfSUPreInstantiable")
        return self._saAmfSUPreInstantiable

    def getsaAmfSUOperState(self):
        ImmHelper.validateSingle(self._saAmfSUOperState, self._dn, "saAmfSUOperState")
        return self._saAmfSUOperState

    def getsaAmfSUNumCurrStandbySIs(self):
        ImmHelper.validateSingle(self._saAmfSUNumCurrStandbySIs, self._dn, "saAmfSUNumCurrStandbySIs")
        return self._saAmfSUNumCurrStandbySIs

    def getsaAmfSUNumCurrActiveSIs(self):
        ImmHelper.validateSingle(self._saAmfSUNumCurrActiveSIs, self._dn, "saAmfSUNumCurrActiveSIs")
        return self._saAmfSUNumCurrActiveSIs

    def getsaAmfSUMaintenanceCampaign(self):
        ImmHelper.validateSingle(self._saAmfSUMaintenanceCampaign, self._dn, "saAmfSUMaintenanceCampaign")
        return self._saAmfSUMaintenanceCampaign

    def getsaAmfSUHostedByNode(self):
        ImmHelper.validateSingle(self._saAmfSUHostedByNode, self._dn, "saAmfSUHostedByNode")
        return self._saAmfSUHostedByNode

    def getsaAmfSUHostNodeOrNodeGroup(self):
        if self._saAmfSUHostNodeOrNodeGroup is not None:
            ImmHelper.validateSingle(self._saAmfSUHostNodeOrNodeGroup, self._dn, "saAmfSUHostNodeOrNodeGroup")
        return self._saAmfSUHostNodeOrNodeGroup

    def getsaAmfSUFailover(self):
        ImmHelper.validateSingle(self._saAmfSUFailover, self._dn, "saAmfSUFailover")
        return self._saAmfSUFailover

    def getsaAmfSUAssignedSIs(self):
        return self._saAmfSUAssignedSIs

    def getsaAmfSUAdminState(self):
        ImmHelper.validateSingle(self._saAmfSUAdminState, self._dn, "saAmfSUAdminState")
        return self._saAmfSUAdminState

    def getSaImmAttrImplementerName(self):
        ImmHelper.validateSingle(self._SaImmAttrImplementerName, self._dn, "SaImmAttrImplementerName")
        return self._SaImmAttrImplementerName

    def getSaImmAttrClassName(self):
        ImmHelper.validateSingle(self._SaImmAttrClassName, self._dn, "SaImmAttrClassName")
        return self._SaImmAttrClassName

    def getSaImmAttrAdminOwnerName(self):
        ImmHelper.validateSingle(self._SaImmAttrAdminOwnerName, self._dn, "SaImmAttrAdminOwnerName")
        return self._SaImmAttrAdminOwnerName

    def getsaAmfSUType_unsafe(self):
        return self._saAmfSUType

    def getsaAmfSURestartCount_unsafe(self):
        return self._saAmfSURestartCount

    def getsaAmfSUReadinessState_unsafe(self):
        return self._saAmfSUReadinessState

    def getsaAmfSURank_unsafe(self):
        return self._saAmfSURank

    def getsaAmfSUPresenceState_unsafe(self):
        return self._saAmfSUPresenceState

    def getsaAmfSUPreInstantiable_unsafe(self):
        return self._saAmfSUPreInstantiable

    def getsaAmfSUOperState_unsafe(self):
        return self._saAmfSUOperState

    def getsaAmfSUNumCurrStandbySIs_unsafe(self):
        return self._saAmfSUNumCurrStandbySIs

    def getsaAmfSUNumCurrActiveSIs_unsafe(self):
        return self._saAmfSUNumCurrActiveSIs

    def getsaAmfSUMaintenanceCampaign_unsafe(self):
        return self._saAmfSUMaintenanceCampaign

    def getsaAmfSUHostedByNode_unsafe(self):
        return self._saAmfSUHostedByNode

    def getsaAmfSUHostNodeOrNodeGroup_unsafe(self):
        return self._saAmfSUHostNodeOrNodeGroup

    def getsaAmfSUFailover_unsafe(self):
        return self._saAmfSUFailover

    def getsaAmfSUAssignedSIs_single(self):
        ImmHelper.validateSingleInList(self._saAmfSUAssignedSIs, self._dn, "saAmfSUAssignedSIs")
        return self._saAmfSUAssignedSIs[0]

    def getsaAmfSUAdminState_unsafe(self):
        return self._saAmfSUAdminState

    def getSaImmAttrImplementerName_unsafe(self):
        return self._SaImmAttrImplementerName

    def getSaImmAttrClassName_unsafe(self):
        return self._SaImmAttrClassName

    def getSaImmAttrAdminOwnerName_unsafe(self):
        return self._SaImmAttrAdminOwnerName

    def setsaAmfSUType(self, value):
        ImmHelper.validateName(value, self._dn, "saAmfSUType")
        self._saAmfSUType = value

    def setsaAmfSURestartCount(self, value):
        ImmHelper.validateUint32(value, self._dn, "saAmfSURestartCount")
        value = str(value)
        self._saAmfSURestartCount = value

    def setsaAmfSUReadinessState(self, value):
        ImmHelper.validateUint32(value, self._dn, "saAmfSUReadinessState")
        value = str(value)
        self._saAmfSUReadinessState = value

    def setsaAmfSURank(self, value):
        ImmHelper.validateUint32(value, self._dn, "saAmfSURank")
        value = str(value)
        self._saAmfSURank = value

    def setsaAmfSUPresenceState(self, value):
        ImmHelper.validateUint32(value, self._dn, "saAmfSUPresenceState")
        value = str(value)
        self._saAmfSUPresenceState = value

    def setsaAmfSUPreInstantiable(self, value):
        ImmHelper.validateUint32(value, self._dn, "saAmfSUPreInstantiable")
        value = str(value)
        self._saAmfSUPreInstantiable = value

    def setsaAmfSUOperState(self, value):
        ImmHelper.validateUint32(value, self._dn, "saAmfSUOperState")
        value = str(value)
        self._saAmfSUOperState = value

    def setsaAmfSUNumCurrStandbySIs(self, value):
        ImmHelper.validateUint32(value, self._dn, "saAmfSUNumCurrStandbySIs")
        value = str(value)
        self._saAmfSUNumCurrStandbySIs = value

    def setsaAmfSUNumCurrActiveSIs(self, value):
        ImmHelper.validateUint32(value, self._dn, "saAmfSUNumCurrActiveSIs")
        value = str(value)
        self._saAmfSUNumCurrActiveSIs = value

    def setsaAmfSUMaintenanceCampaign(self, value):
        ImmHelper.validateName(value, self._dn, "saAmfSUMaintenanceCampaign")
        self._saAmfSUMaintenanceCampaign = value

    def setsaAmfSUHostedByNode(self, value):
        ImmHelper.validateName(value, self._dn, "saAmfSUHostedByNode")
        self._saAmfSUHostedByNode = value

    def setsaAmfSUHostNodeOrNodeGroup(self, value):
        if value is not None:
            ImmHelper.validateName(value, self._dn, "saAmfSUHostNodeOrNodeGroup")
        self._saAmfSUHostNodeOrNodeGroup = value

    def setsaAmfSUFailover(self, value):
        ImmHelper.validateUint32(value, self._dn, "saAmfSUFailover")
        value = str(value)
        self._saAmfSUFailover = value

    def addTosaAmfSUAssignedSIs(self, value):
        ImmHelper.validateName(value, self._dn, "saAmfSUAssignedSIs")
        self._saAmfSUAssignedSIs.append(value)

    def setsaAmfSUAdminState(self, value):
        ImmHelper.validateUint32(value, self._dn, "saAmfSUAdminState")
        value = str(value)
        self._saAmfSUAdminState = value

    def setSaImmAttrImplementerName(self, value):
        ImmHelper.validateString(value, self._dn, "SaImmAttrImplementerName")
        self._SaImmAttrImplementerName = value

    def setSaImmAttrClassName(self, value):
        ImmHelper.validateString(value, self._dn, "SaImmAttrClassName")
        self._SaImmAttrClassName = value

    def setSaImmAttrAdminOwnerName(self, value):
        ImmHelper.validateString(value, self._dn, "SaImmAttrAdminOwnerName")
        self._SaImmAttrAdminOwnerName = value

    def updateParams(self, params, canttouchthis):
        for (param, value) in params.items():
            if param in canttouchthis:
                error("Setting attribute " + param + " in object " + self.getDn() + " is not supported")
            if param == "saAmfSUType":
                self.setsaAmfSUType(value)
            elif param == "saAmfSURank":
                self.setsaAmfSURank(value)
            elif param == "saAmfSUMaintenanceCampaign":
                self.setsaAmfSUMaintenanceCampaign(value)
            elif param == "saAmfSUHostNodeOrNodeGroup":
                self.setsaAmfSUHostNodeOrNodeGroup(value)
            elif param == "saAmfSUFailover":
                self.setsaAmfSUFailover(value)
            else:
                error("Object " + self.getDn() + " has no attribute named " + param)

    def diff(self, other, fullCheck = False):
        changedAttrs = []
        if (fullCheck or self._saAmfSUType != None) and other._saAmfSUType != self._saAmfSUType:
            changedAttrs.append("saAmfSUType")
        if (fullCheck or self._saAmfSURank != None) and other._saAmfSURank != self._saAmfSURank:
            changedAttrs.append("saAmfSURank")
        if (fullCheck or self._saAmfSUMaintenanceCampaign != None) and other._saAmfSUMaintenanceCampaign != self._saAmfSUMaintenanceCampaign:
            changedAttrs.append("saAmfSUMaintenanceCampaign")
        if (fullCheck or self._saAmfSUHostNodeOrNodeGroup != None) and other._saAmfSUHostNodeOrNodeGroup != self._saAmfSUHostNodeOrNodeGroup:
            changedAttrs.append("saAmfSUHostNodeOrNodeGroup")
        if (fullCheck or self._saAmfSUFailover != None) and other._saAmfSUFailover != self._saAmfSUFailover:
            changedAttrs.append("saAmfSUFailover")
        if (fullCheck or self._SaImmAttrImplementerName != None) and other._SaImmAttrImplementerName != self._SaImmAttrImplementerName:
            changedAttrs.append("SaImmAttrImplementerName")
        if (fullCheck or self._SaImmAttrClassName != None) and other._SaImmAttrClassName != self._SaImmAttrClassName:
            changedAttrs.append("SaImmAttrClassName")
        if (fullCheck or self._SaImmAttrAdminOwnerName != None) and other._SaImmAttrAdminOwnerName != self._SaImmAttrAdminOwnerName:
            changedAttrs.append("SaImmAttrAdminOwnerName")
        return changedAttrs

    def parseXML(self, node):
        dns = node.getElementsByTagName("dn")
        if len(dns) != 1:
            error("object has " + str(len(dns)) + " dn(s) but it should have one")
        self._dn = dns[0].childNodes[0].nodeValue
        for attribute in node.getElementsByTagName("attr"):
            names = attribute.getElementsByTagName("name")
            if len(names) != 1:
                error("object attribute has " + str(len(names)) + " name(s) but it should have one")
            name = names[0].childNodes[0].nodeValue
            setFunc = None
            if name == "SaImmAttrImplementerName":
                continue
            elif name == "SaImmAttrAdminOwnerName":
                continue
            elif name == "SaImmAttrClassName":
                continue
            elif name == "saAmfSUType":
                setFunc = self.setsaAmfSUType
            elif name == "saAmfSURestartCount":
                setFunc = self.setsaAmfSURestartCount
            elif name == "saAmfSUReadinessState":
                setFunc = self.setsaAmfSUReadinessState
            elif name == "saAmfSURank":
                setFunc = self.setsaAmfSURank
            elif name == "saAmfSUPresenceState":
                setFunc = self.setsaAmfSUPresenceState
            elif name == "saAmfSUPreInstantiable":
                setFunc = self.setsaAmfSUPreInstantiable
            elif name == "saAmfSUOperState":
                setFunc = self.setsaAmfSUOperState
            elif name == "saAmfSUNumCurrStandbySIs":
                setFunc = self.setsaAmfSUNumCurrStandbySIs
            elif name == "saAmfSUNumCurrActiveSIs":
                setFunc = self.setsaAmfSUNumCurrActiveSIs
            elif name == "saAmfSUMaintenanceCampaign":
                setFunc = self.setsaAmfSUMaintenanceCampaign
            elif name == "saAmfSUHostedByNode":
                setFunc = self.setsaAmfSUHostedByNode
            elif name == "saAmfSUHostNodeOrNodeGroup":
                setFunc = self.setsaAmfSUHostNodeOrNodeGroup
            elif name == "saAmfSUFailover":
                setFunc = self.setsaAmfSUFailover
            elif name == "saAmfSUAssignedSIs":
                setFunc = self.addTosaAmfSUAssignedSIs
            elif name == "saAmfSUAdminState":
                setFunc = self.setsaAmfSUAdminState
            elif name == "SaImmAttrImplementerName":
                setFunc = self.setSaImmAttrImplementerName
            elif name == "SaImmAttrClassName":
                setFunc = self.setSaImmAttrClassName
            elif name == "SaImmAttrAdminOwnerName":
                setFunc = self.setSaImmAttrAdminOwnerName
            elif name.startswith("osaf"):
                continue # ignore OpenSAF specific attributes
            else:
                error("unknown attribute called " + name + " defined in object " + self._dn)
            for value in attribute.getElementsByTagName("value"):
                if value.childNodes:
                    setFunc(value.childNodes[0].nodeValue)
                else:
                    setFunc(None)

    def writeXML(self, parent, doc):
        obj = doc.createElement("object")
        parent.appendChild(obj)
        obj.setAttribute("class", "SaAmfSU")
        dn = doc.createElement("dn")
        obj.appendChild(dn)
        dn.appendChild(doc.createTextNode(self._dn))
        ImmHelper.writeSingleAttribute("saAmfSUType", self._saAmfSUType, doc, obj)
        ImmHelper.writeSingleAttribute("saAmfSURestartCount", self._saAmfSURestartCount, doc, obj)
        ImmHelper.writeSingleAttribute("saAmfSUReadinessState", self._saAmfSUReadinessState, doc, obj)
        ImmHelper.writeSingleAttribute("saAmfSURank", self._saAmfSURank, doc, obj)
        ImmHelper.writeSingleAttribute("saAmfSUPresenceState", self._saAmfSUPresenceState, doc, obj)
        ImmHelper.writeSingleAttribute("saAmfSUPreInstantiable", self._saAmfSUPreInstantiable, doc, obj)
        ImmHelper.writeSingleAttribute("saAmfSUOperState", self._saAmfSUOperState, doc, obj)
        ImmHelper.writeSingleAttribute("saAmfSUNumCurrStandbySIs", self._saAmfSUNumCurrStandbySIs, doc, obj)
        ImmHelper.writeSingleAttribute("saAmfSUNumCurrActiveSIs", self._saAmfSUNumCurrActiveSIs, doc, obj)
        ImmHelper.writeSingleAttribute("saAmfSUMaintenanceCampaign", self._saAmfSUMaintenanceCampaign, doc, obj)
        ImmHelper.writeSingleAttribute("saAmfSUHostedByNode", self._saAmfSUHostedByNode, doc, obj)
        ImmHelper.writeSingleAttribute("saAmfSUHostNodeOrNodeGroup", self._saAmfSUHostNodeOrNodeGroup, doc, obj)
        ImmHelper.writeSingleAttribute("saAmfSUFailover", self._saAmfSUFailover, doc, obj)
        ImmHelper.writeMultiAttributes("saAmfSUAssignedSIs", self._saAmfSUAssignedSIs, doc, obj)
        ImmHelper.writeSingleAttribute("saAmfSUAdminState", self._saAmfSUAdminState, doc, obj)
        ImmHelper.writeSingleAttribute("SaImmAttrImplementerName", self._SaImmAttrImplementerName, doc, obj)
        ImmHelper.writeSingleAttribute("SaImmAttrClassName", self._SaImmAttrClassName, doc, obj)
        ImmHelper.writeSingleAttribute("SaImmAttrAdminOwnerName", self._SaImmAttrAdminOwnerName, doc, obj)


class SaAmfSIRankedSU(object):
    def __init__(self):
        self._dn = None
        self._saAmfRank = None
        self._SaImmAttrImplementerName = None
        self._SaImmAttrClassName = None
        self._SaImmAttrAdminOwnerName = None

    @staticmethod
    def createDn(name, parentDn = None):
        if parentDn == None:
            parentDn = ""
        else:
            parentDn = "," + parentDn
        return "safRankedSu=" + ImmHelper.escapeName(name) + parentDn

    def getDn(self):
        return self._dn

    def getName(self):
        return ImmHelper.getName(self._dn)

    def getRdn(self):
        return ImmHelper.getRdn(self._dn)

    def getParentDn(self):
        return ImmHelper.getParentDn(self._dn)

    def createObjectInCampaign(self, campaign):
        parentDn = self.getParentDn()
        if parentDn == "":
            parentDn = "="
        campaign.beginCreate("SaAmfSIRankedSU", parentDn)
        campaign.addAttribute("safRankedSu", "SA_IMM_ATTR_SANAMET", self.getRdn())
        if self._saAmfRank != None:
            campaign.addAttribute("saAmfRank", "SA_IMM_ATTR_SAUINT32T", self._saAmfRank)
        if self._SaImmAttrImplementerName != None:
            campaign.addAttribute("SaImmAttrImplementerName", "SA_IMM_ATTR_SASTRINGT", self._SaImmAttrImplementerName)
        if self._SaImmAttrClassName != None:
            campaign.addAttribute("SaImmAttrClassName", "SA_IMM_ATTR_SASTRINGT", self._SaImmAttrClassName)
        if self._SaImmAttrAdminOwnerName != None:
            campaign.addAttribute("SaImmAttrAdminOwnerName", "SA_IMM_ATTR_SASTRINGT", self._SaImmAttrAdminOwnerName)
        campaign.endCreate()

    def getsaAmfRank(self):
        ImmHelper.validateSingle(self._saAmfRank, self._dn, "saAmfRank")
        return self._saAmfRank

    def getSaImmAttrImplementerName(self):
        ImmHelper.validateSingle(self._SaImmAttrImplementerName, self._dn, "SaImmAttrImplementerName")
        return self._SaImmAttrImplementerName

    def getSaImmAttrClassName(self):
        ImmHelper.validateSingle(self._SaImmAttrClassName, self._dn, "SaImmAttrClassName")
        return self._SaImmAttrClassName

    def getSaImmAttrAdminOwnerName(self):
        ImmHelper.validateSingle(self._SaImmAttrAdminOwnerName, self._dn, "SaImmAttrAdminOwnerName")
        return self._SaImmAttrAdminOwnerName

    def getsaAmfRank_unsafe(self):
        return self._saAmfRank

    def getSaImmAttrImplementerName_unsafe(self):
        return self._SaImmAttrImplementerName

    def getSaImmAttrClassName_unsafe(self):
        return self._SaImmAttrClassName

    def getSaImmAttrAdminOwnerName_unsafe(self):
        return self._SaImmAttrAdminOwnerName

    def setsaAmfRank(self, value):
        ImmHelper.validateUint32(value, self._dn, "saAmfRank")
        value = str(value)
        self._saAmfRank = value

    def setSaImmAttrImplementerName(self, value):
        ImmHelper.validateString(value, self._dn, "SaImmAttrImplementerName")
        self._SaImmAttrImplementerName = value

    def setSaImmAttrClassName(self, value):
        ImmHelper.validateString(value, self._dn, "SaImmAttrClassName")
        self._SaImmAttrClassName = value

    def setSaImmAttrAdminOwnerName(self, value):
        ImmHelper.validateString(value, self._dn, "SaImmAttrAdminOwnerName")
        self._SaImmAttrAdminOwnerName = value

    def updateParams(self, params, canttouchthis):
        for (param, value) in params.items():
            if param in canttouchthis:
                error("Setting attribute " + param + " in object " + self.getDn() + " is not supported")
            if param == "saAmfRank":
                self.setsaAmfRank(value)
            else:
                error("Object " + self.getDn() + " has no attribute named " + param)

    def diff(self, other, fullCheck = False):
        changedAttrs = []
        if (fullCheck or self._saAmfRank != None) and other._saAmfRank != self._saAmfRank:
            changedAttrs.append("saAmfRank")
        if (fullCheck or self._SaImmAttrImplementerName != None) and other._SaImmAttrImplementerName != self._SaImmAttrImplementerName:
            changedAttrs.append("SaImmAttrImplementerName")
        if (fullCheck or self._SaImmAttrClassName != None) and other._SaImmAttrClassName != self._SaImmAttrClassName:
            changedAttrs.append("SaImmAttrClassName")
        if (fullCheck or self._SaImmAttrAdminOwnerName != None) and other._SaImmAttrAdminOwnerName != self._SaImmAttrAdminOwnerName:
            changedAttrs.append("SaImmAttrAdminOwnerName")
        return changedAttrs

    def parseXML(self, node):
        dns = node.getElementsByTagName("dn")
        if len(dns) != 1:
            error("object has " + str(len(dns)) + " dn(s) but it should have one")
        self._dn = dns[0].childNodes[0].nodeValue
        for attribute in node.getElementsByTagName("attr"):
            names = attribute.getElementsByTagName("name")
            if len(names) != 1:
                error("object attribute has " + str(len(names)) + " name(s) but it should have one")
            name = names[0].childNodes[0].nodeValue
            setFunc = None
            if name == "SaImmAttrImplementerName":
                continue
            elif name == "SaImmAttrAdminOwnerName":
                continue
            elif name == "SaImmAttrClassName":
                continue
            elif name == "saAmfRank":
                setFunc = self.setsaAmfRank
            elif name == "SaImmAttrImplementerName":
                setFunc = self.setSaImmAttrImplementerName
            elif name == "SaImmAttrClassName":
                setFunc = self.setSaImmAttrClassName
            elif name == "SaImmAttrAdminOwnerName":
                setFunc = self.setSaImmAttrAdminOwnerName
            elif name.startswith("osaf"):
                continue # ignore OpenSAF specific attributes
            else:
                error("unknown attribute called " + name + " defined in object " + self._dn)
            for value in attribute.getElementsByTagName("value"):
                setFunc(value.childNodes[0].nodeValue)

    def writeXML(self, parent, doc):
        obj = doc.createElement("object")
        parent.appendChild(obj)
        obj.setAttribute("class", "SaAmfSIRankedSU")
        dn = doc.createElement("dn")
        obj.appendChild(dn)
        dn.appendChild(doc.createTextNode(self._dn))
        ImmHelper.writeSingleAttribute("saAmfRank", self._saAmfRank, doc, obj)
        ImmHelper.writeSingleAttribute("SaImmAttrImplementerName", self._SaImmAttrImplementerName, doc, obj)
        ImmHelper.writeSingleAttribute("SaImmAttrClassName", self._SaImmAttrClassName, doc, obj)
        ImmHelper.writeSingleAttribute("SaImmAttrAdminOwnerName", self._SaImmAttrAdminOwnerName, doc, obj)


class SaAmfSIDependency(object):
    def __init__(self):
        self._dn = None
        self._saAmfToleranceTime = None
        self._SaImmAttrImplementerName = None
        self._SaImmAttrClassName = None
        self._SaImmAttrAdminOwnerName = None

    @staticmethod
    def createDn(name, parentDn = None):
        if parentDn == None:
            parentDn = ""
        else:
            parentDn = "," + parentDn
        return "safDepend=" + ImmHelper.escapeName(name) + parentDn

    def getDn(self):
        return self._dn

    def getName(self):
        return ImmHelper.getName(self._dn)

    def getRdn(self):
        return ImmHelper.getRdn(self._dn)

    def getParentDn(self):
        return ImmHelper.getParentDn(self._dn)

    def createObjectInCampaign(self, campaign):
        parentDn = self.getParentDn()
        if parentDn == "":
            parentDn = "="
        campaign.beginCreate("SaAmfSIDependency", parentDn)
        campaign.addAttribute("safDepend", "SA_IMM_ATTR_SANAMET", self.getRdn())
        if self._saAmfToleranceTime != None:
            campaign.addAttribute("saAmfToleranceTime", "SA_IMM_ATTR_SATIMET", self._saAmfToleranceTime)
        if self._SaImmAttrImplementerName != None:
            campaign.addAttribute("SaImmAttrImplementerName", "SA_IMM_ATTR_SASTRINGT", self._SaImmAttrImplementerName)
        if self._SaImmAttrClassName != None:
            campaign.addAttribute("SaImmAttrClassName", "SA_IMM_ATTR_SASTRINGT", self._SaImmAttrClassName)
        if self._SaImmAttrAdminOwnerName != None:
            campaign.addAttribute("SaImmAttrAdminOwnerName", "SA_IMM_ATTR_SASTRINGT", self._SaImmAttrAdminOwnerName)
        campaign.endCreate()

    def getsaAmfToleranceTime(self):
        ImmHelper.validateSingle(self._saAmfToleranceTime, self._dn, "saAmfToleranceTime")
        return self._saAmfToleranceTime

    def getSaImmAttrImplementerName(self):
        ImmHelper.validateSingle(self._SaImmAttrImplementerName, self._dn, "SaImmAttrImplementerName")
        return self._SaImmAttrImplementerName

    def getSaImmAttrClassName(self):
        ImmHelper.validateSingle(self._SaImmAttrClassName, self._dn, "SaImmAttrClassName")
        return self._SaImmAttrClassName

    def getSaImmAttrAdminOwnerName(self):
        ImmHelper.validateSingle(self._SaImmAttrAdminOwnerName, self._dn, "SaImmAttrAdminOwnerName")
        return self._SaImmAttrAdminOwnerName

    def getsaAmfToleranceTime_unsafe(self):
        return self._saAmfToleranceTime

    def getSaImmAttrImplementerName_unsafe(self):
        return self._SaImmAttrImplementerName

    def getSaImmAttrClassName_unsafe(self):
        return self._SaImmAttrClassName

    def getSaImmAttrAdminOwnerName_unsafe(self):
        return self._SaImmAttrAdminOwnerName

    def setsaAmfToleranceTime(self, value):
        ImmHelper.validateTime(value, self._dn, "saAmfToleranceTime")
        value = str(value)
        self._saAmfToleranceTime = value

    def setSaImmAttrImplementerName(self, value):
        ImmHelper.validateString(value, self._dn, "SaImmAttrImplementerName")
        self._SaImmAttrImplementerName = value

    def setSaImmAttrClassName(self, value):
        ImmHelper.validateString(value, self._dn, "SaImmAttrClassName")
        self._SaImmAttrClassName = value

    def setSaImmAttrAdminOwnerName(self, value):
        ImmHelper.validateString(value, self._dn, "SaImmAttrAdminOwnerName")
        self._SaImmAttrAdminOwnerName = value

    def updateParams(self, params, canttouchthis):
        for (param, value) in params.items():
            if param in canttouchthis:
                error("Setting attribute " + param + " in object " + self.getDn() + " is not supported")
            if param == "saAmfToleranceTime":
                self.setsaAmfToleranceTime(value)
            else:
                error("Object " + self.getDn() + " has no attribute named " + param)

    def diff(self, other, fullCheck = False):
        changedAttrs = []
        if (fullCheck or self._saAmfToleranceTime != None) and other._saAmfToleranceTime != self._saAmfToleranceTime:
            changedAttrs.append("saAmfToleranceTime")
        if (fullCheck or self._SaImmAttrImplementerName != None) and other._SaImmAttrImplementerName != self._SaImmAttrImplementerName:
            changedAttrs.append("SaImmAttrImplementerName")
        if (fullCheck or self._SaImmAttrClassName != None) and other._SaImmAttrClassName != self._SaImmAttrClassName:
            changedAttrs.append("SaImmAttrClassName")
        if (fullCheck or self._SaImmAttrAdminOwnerName != None) and other._SaImmAttrAdminOwnerName != self._SaImmAttrAdminOwnerName:
            changedAttrs.append("SaImmAttrAdminOwnerName")
        return changedAttrs

    def parseXML(self, node):
        dns = node.getElementsByTagName("dn")
        if len(dns) != 1:
            error("object has " + str(len(dns)) + " dn(s) but it should have one")
        self._dn = dns[0].childNodes[0].nodeValue
        for attribute in node.getElementsByTagName("attr"):
            names = attribute.getElementsByTagName("name")
            if len(names) != 1:
                error("object attribute has " + str(len(names)) + " name(s) but it should have one")
            name = names[0].childNodes[0].nodeValue
            setFunc = None
            if name == "SaImmAttrImplementerName":
                continue
            elif name == "SaImmAttrAdminOwnerName":
                continue
            elif name == "SaImmAttrClassName":
                continue
            elif name == "saAmfToleranceTime":
                setFunc = self.setsaAmfToleranceTime
            elif name == "SaImmAttrImplementerName":
                setFunc = self.setSaImmAttrImplementerName
            elif name == "SaImmAttrClassName":
                setFunc = self.setSaImmAttrClassName
            elif name == "SaImmAttrAdminOwnerName":
                setFunc = self.setSaImmAttrAdminOwnerName
            elif name.startswith("osaf"):
                continue # ignore OpenSAF specific attributes
            else:
                error("unknown attribute called " + name + " defined in object " + self._dn)
            for value in attribute.getElementsByTagName("value"):
                setFunc(value.childNodes[0].nodeValue)

    def writeXML(self, parent, doc):
        obj = doc.createElement("object")
        parent.appendChild(obj)
        obj.setAttribute("class", "SaAmfSIDependency")
        dn = doc.createElement("dn")
        obj.appendChild(dn)
        dn.appendChild(doc.createTextNode(self._dn))
        ImmHelper.writeSingleAttribute("saAmfToleranceTime", self._saAmfToleranceTime, doc, obj)
        ImmHelper.writeSingleAttribute("SaImmAttrImplementerName", self._SaImmAttrImplementerName, doc, obj)
        ImmHelper.writeSingleAttribute("SaImmAttrClassName", self._SaImmAttrClassName, doc, obj)
        ImmHelper.writeSingleAttribute("SaImmAttrAdminOwnerName", self._SaImmAttrAdminOwnerName, doc, obj)


class SaAmfSIAssignment(object):
    def __init__(self):
        self._dn = None
        self._saAmfSISUHAState = None
        self._saAmfSISUHAReadinessState = None
        self._SaImmAttrImplementerName = None
        self._SaImmAttrClassName = None
        self._SaImmAttrAdminOwnerName = None

    @staticmethod
    def createDn(name, parentDn = None):
        if parentDn == None:
            parentDn = ""
        else:
            parentDn = "," + parentDn
        return "safSISU=" + ImmHelper.escapeName(name) + parentDn

    def getDn(self):
        return self._dn

    def getName(self):
        return ImmHelper.getName(self._dn)

    def getRdn(self):
        return ImmHelper.getRdn(self._dn)

    def getParentDn(self):
        return ImmHelper.getParentDn(self._dn)

    def createObjectInCampaign(self, campaign):
        parentDn = self.getParentDn()
        if parentDn == "":
            parentDn = "="
        campaign.beginCreate("SaAmfSIAssignment", parentDn)
        campaign.addAttribute("safSISU", "SA_IMM_ATTR_SANAMET", self.getRdn())
        campaign.endCreate()

    def getsaAmfSISUHAState(self):
        ImmHelper.validateSingle(self._saAmfSISUHAState, self._dn, "saAmfSISUHAState")
        return self._saAmfSISUHAState

    def getsaAmfSISUHAReadinessState(self):
        ImmHelper.validateSingle(self._saAmfSISUHAReadinessState, self._dn, "saAmfSISUHAReadinessState")
        return self._saAmfSISUHAReadinessState

    def getSaImmAttrImplementerName(self):
        ImmHelper.validateSingle(self._SaImmAttrImplementerName, self._dn, "SaImmAttrImplementerName")
        return self._SaImmAttrImplementerName

    def getSaImmAttrClassName(self):
        ImmHelper.validateSingle(self._SaImmAttrClassName, self._dn, "SaImmAttrClassName")
        return self._SaImmAttrClassName

    def getSaImmAttrAdminOwnerName(self):
        ImmHelper.validateSingle(self._SaImmAttrAdminOwnerName, self._dn, "SaImmAttrAdminOwnerName")
        return self._SaImmAttrAdminOwnerName

    def getsaAmfSISUHAState_unsafe(self):
        return self._saAmfSISUHAState

    def getsaAmfSISUHAReadinessState_unsafe(self):
        return self._saAmfSISUHAReadinessState

    def getSaImmAttrImplementerName_unsafe(self):
        return self._SaImmAttrImplementerName

    def getSaImmAttrClassName_unsafe(self):
        return self._SaImmAttrClassName

    def getSaImmAttrAdminOwnerName_unsafe(self):
        return self._SaImmAttrAdminOwnerName

    def setsaAmfSISUHAState(self, value):
        ImmHelper.validateUint32(value, self._dn, "saAmfSISUHAState")
        value = str(value)
        self._saAmfSISUHAState = value

    def setsaAmfSISUHAReadinessState(self, value):
        ImmHelper.validateUint32(value, self._dn, "saAmfSISUHAReadinessState")
        value = str(value)
        self._saAmfSISUHAReadinessState = value

    def setSaImmAttrImplementerName(self, value):
        ImmHelper.validateString(value, self._dn, "SaImmAttrImplementerName")
        self._SaImmAttrImplementerName = value

    def setSaImmAttrClassName(self, value):
        ImmHelper.validateString(value, self._dn, "SaImmAttrClassName")
        self._SaImmAttrClassName = value

    def setSaImmAttrAdminOwnerName(self, value):
        ImmHelper.validateString(value, self._dn, "SaImmAttrAdminOwnerName")
        self._SaImmAttrAdminOwnerName = value

    def updateParams(self, params, canttouchthis):
        for (param, value) in params.items():
            if param in canttouchthis:
                error("Setting attribute " + param + " in object " + self.getDn() + " is not supported")
            else:
                error("Object " + self.getDn() + " has no attribute named " + param)

    def diff(self, other, fullCheck = False):
        changedAttrs = []
        return changedAttrs

    def parseXML(self, node):
        dns = node.getElementsByTagName("dn")
        if len(dns) != 1:
            error("object has " + str(len(dns)) + " dn(s) but it should have one")
        self._dn = dns[0].childNodes[0].nodeValue
        for attribute in node.getElementsByTagName("attr"):
            names = attribute.getElementsByTagName("name")
            if len(names) != 1:
                error("object attribute has " + str(len(names)) + " name(s) but it should have one")
            name = names[0].childNodes[0].nodeValue
            setFunc = None
            if name == "SaImmAttrImplementerName":
                continue
            elif name == "SaImmAttrAdminOwnerName":
                continue
            elif name == "SaImmAttrClassName":
                continue
            elif name == "saAmfSISUHAState":
                setFunc = self.setsaAmfSISUHAState
            elif name == "saAmfSISUHAReadinessState":
                setFunc = self.setsaAmfSISUHAReadinessState
            elif name == "SaImmAttrImplementerName":
                setFunc = self.setSaImmAttrImplementerName
            elif name == "SaImmAttrClassName":
                setFunc = self.setSaImmAttrClassName
            elif name == "SaImmAttrAdminOwnerName":
                setFunc = self.setSaImmAttrAdminOwnerName
            elif name.startswith("osaf"):
                continue # ignore OpenSAF specific attributes
            else:
                error("unknown attribute called " + name + " defined in object " + self._dn)
            for value in attribute.getElementsByTagName("value"):
                setFunc(value.childNodes[0].nodeValue)

    def writeXML(self, parent, doc):
        obj = doc.createElement("object")
        parent.appendChild(obj)
        obj.setAttribute("class", "SaAmfSIAssignment")
        dn = doc.createElement("dn")
        obj.appendChild(dn)
        dn.appendChild(doc.createTextNode(self._dn))
        ImmHelper.writeSingleAttribute("saAmfSISUHAState", self._saAmfSISUHAState, doc, obj)
        ImmHelper.writeSingleAttribute("saAmfSISUHAReadinessState", self._saAmfSISUHAReadinessState, doc, obj)
        ImmHelper.writeSingleAttribute("SaImmAttrImplementerName", self._SaImmAttrImplementerName, doc, obj)
        ImmHelper.writeSingleAttribute("SaImmAttrClassName", self._SaImmAttrClassName, doc, obj)
        ImmHelper.writeSingleAttribute("SaImmAttrAdminOwnerName", self._SaImmAttrAdminOwnerName, doc, obj)


class SaAmfSI(object):
    def __init__(self):
        self._dn = None
        self._saAmfUnassignedAlarmStatus = None
        self._saAmfSvcType = None
        self._saAmfSIStandbyWeight = []
        self._saAmfSIRank = None
        self._saAmfSIProtectedbySG = None
        self._saAmfSIPrefStandbyAssignments = None
        self._saAmfSIPrefActiveAssignments = None
        self._saAmfSINumCurrStandbyAssignments = None
        self._saAmfSINumCurrActiveAssignments = None
        self._saAmfSIAssignmentState = None
        self._saAmfSIAdminState = None
        self._saAmfSIActiveWeight = []
        self._SaImmAttrImplementerName = None
        self._SaImmAttrClassName = None
        self._SaImmAttrAdminOwnerName = None

    @staticmethod
    def createDn(name, parentDn = None):
        if parentDn == None:
            parentDn = ""
        else:
            parentDn = "," + parentDn
        return "safSi=" + ImmHelper.escapeName(name) + parentDn

    def getDn(self):
        return self._dn

    def getName(self):
        return ImmHelper.getName(self._dn)

    def getRdn(self):
        return ImmHelper.getRdn(self._dn)

    def getParentDn(self):
        return ImmHelper.getParentDn(self._dn)

    def createObjectInCampaign(self, campaign):
        parentDn = self.getParentDn()
        if parentDn == "":
            parentDn = "="
        campaign.beginCreate("SaAmfSI", parentDn)
        campaign.addAttribute("safSi", "SA_IMM_ATTR_SASTRINGT", self.getRdn())
        if self._saAmfSvcType != None:
            campaign.addAttribute("saAmfSvcType", "SA_IMM_ATTR_SANAMET", self._saAmfSvcType)
        if len(self._saAmfSIStandbyWeight) > 0:
            campaign.addAttribute("saAmfSIStandbyWeight", "SA_IMM_ATTR_SASTRINGT", self._saAmfSIStandbyWeight)
        if self._saAmfSIRank != None:
            campaign.addAttribute("saAmfSIRank", "SA_IMM_ATTR_SAUINT32T", self._saAmfSIRank)
        if self._saAmfSIProtectedbySG != None:
            campaign.addAttribute("saAmfSIProtectedbySG", "SA_IMM_ATTR_SANAMET", self._saAmfSIProtectedbySG)
        if self._saAmfSIPrefStandbyAssignments != None:
            campaign.addAttribute("saAmfSIPrefStandbyAssignments", "SA_IMM_ATTR_SAUINT32T", self._saAmfSIPrefStandbyAssignments)
        if self._saAmfSIPrefActiveAssignments != None:
            campaign.addAttribute("saAmfSIPrefActiveAssignments", "SA_IMM_ATTR_SAUINT32T", self._saAmfSIPrefActiveAssignments)
        if len(self._saAmfSIActiveWeight) > 0:
            campaign.addAttribute("saAmfSIActiveWeight", "SA_IMM_ATTR_SASTRINGT", self._saAmfSIActiveWeight)
        if self._SaImmAttrImplementerName != None:
            campaign.addAttribute("SaImmAttrImplementerName", "SA_IMM_ATTR_SASTRINGT", self._SaImmAttrImplementerName)
        if self._SaImmAttrClassName != None:
            campaign.addAttribute("SaImmAttrClassName", "SA_IMM_ATTR_SASTRINGT", self._SaImmAttrClassName)
        if self._SaImmAttrAdminOwnerName != None:
            campaign.addAttribute("SaImmAttrAdminOwnerName", "SA_IMM_ATTR_SASTRINGT", self._SaImmAttrAdminOwnerName)
        campaign.endCreate()

    def getsaAmfUnassignedAlarmStatus(self):
        ImmHelper.validateSingle(self._saAmfUnassignedAlarmStatus, self._dn, "saAmfUnassignedAlarmStatus")
        return self._saAmfUnassignedAlarmStatus

    def getsaAmfSvcType(self):
        ImmHelper.validateSingle(self._saAmfSvcType, self._dn, "saAmfSvcType")
        return self._saAmfSvcType

    def getsaAmfSIStandbyWeight(self):
        return self._saAmfSIStandbyWeight

    def getsaAmfSIRank(self):
        ImmHelper.validateSingle(self._saAmfSIRank, self._dn, "saAmfSIRank")
        return self._saAmfSIRank

    def getsaAmfSIProtectedbySG(self):
        ImmHelper.validateSingle(self._saAmfSIProtectedbySG, self._dn, "saAmfSIProtectedbySG")
        return self._saAmfSIProtectedbySG

    def getsaAmfSIPrefStandbyAssignments(self):
        ImmHelper.validateSingle(self._saAmfSIPrefStandbyAssignments, self._dn, "saAmfSIPrefStandbyAssignments")
        return self._saAmfSIPrefStandbyAssignments

    def getsaAmfSIPrefActiveAssignments(self):
        ImmHelper.validateSingle(self._saAmfSIPrefActiveAssignments, self._dn, "saAmfSIPrefActiveAssignments")
        return self._saAmfSIPrefActiveAssignments

    def getsaAmfSINumCurrStandbyAssignments(self):
        ImmHelper.validateSingle(self._saAmfSINumCurrStandbyAssignments, self._dn, "saAmfSINumCurrStandbyAssignments")
        return self._saAmfSINumCurrStandbyAssignments

    def getsaAmfSINumCurrActiveAssignments(self):
        ImmHelper.validateSingle(self._saAmfSINumCurrActiveAssignments, self._dn, "saAmfSINumCurrActiveAssignments")
        return self._saAmfSINumCurrActiveAssignments

    def getsaAmfSIAssignmentState(self):
        ImmHelper.validateSingle(self._saAmfSIAssignmentState, self._dn, "saAmfSIAssignmentState")
        return self._saAmfSIAssignmentState

    def getsaAmfSIAdminState(self):
        ImmHelper.validateSingle(self._saAmfSIAdminState, self._dn, "saAmfSIAdminState")
        return self._saAmfSIAdminState

    def getsaAmfSIActiveWeight(self):
        return self._saAmfSIActiveWeight

    def getSaImmAttrImplementerName(self):
        ImmHelper.validateSingle(self._SaImmAttrImplementerName, self._dn, "SaImmAttrImplementerName")
        return self._SaImmAttrImplementerName

    def getSaImmAttrClassName(self):
        ImmHelper.validateSingle(self._SaImmAttrClassName, self._dn, "SaImmAttrClassName")
        return self._SaImmAttrClassName

    def getSaImmAttrAdminOwnerName(self):
        ImmHelper.validateSingle(self._SaImmAttrAdminOwnerName, self._dn, "SaImmAttrAdminOwnerName")
        return self._SaImmAttrAdminOwnerName

    def getsaAmfUnassignedAlarmStatus_unsafe(self):
        return self._saAmfUnassignedAlarmStatus

    def getsaAmfSvcType_unsafe(self):
        return self._saAmfSvcType

    def getsaAmfSIStandbyWeight_single(self):
        ImmHelper.validateSingleInList(self._saAmfSIStandbyWeight, self._dn, "saAmfSIStandbyWeight")
        return self._saAmfSIStandbyWeight[0]

    def getsaAmfSIRank_unsafe(self):
        return self._saAmfSIRank

    def getsaAmfSIProtectedbySG_unsafe(self):
        return self._saAmfSIProtectedbySG

    def getsaAmfSIPrefStandbyAssignments_unsafe(self):
        return self._saAmfSIPrefStandbyAssignments

    def getsaAmfSIPrefActiveAssignments_unsafe(self):
        return self._saAmfSIPrefActiveAssignments

    def getsaAmfSINumCurrStandbyAssignments_unsafe(self):
        return self._saAmfSINumCurrStandbyAssignments

    def getsaAmfSINumCurrActiveAssignments_unsafe(self):
        return self._saAmfSINumCurrActiveAssignments

    def getsaAmfSIAssignmentState_unsafe(self):
        return self._saAmfSIAssignmentState

    def getsaAmfSIAdminState_unsafe(self):
        return self._saAmfSIAdminState

    def getsaAmfSIActiveWeight_single(self):
        ImmHelper.validateSingleInList(self._saAmfSIActiveWeight, self._dn, "saAmfSIActiveWeight")
        return self._saAmfSIActiveWeight[0]

    def getSaImmAttrImplementerName_unsafe(self):
        return self._SaImmAttrImplementerName

    def getSaImmAttrClassName_unsafe(self):
        return self._SaImmAttrClassName

    def getSaImmAttrAdminOwnerName_unsafe(self):
        return self._SaImmAttrAdminOwnerName

    def setsaAmfUnassignedAlarmStatus(self, value):
        ImmHelper.validateUint32(value, self._dn, "saAmfUnassignedAlarmStatus")
        value = str(value)
        self._saAmfUnassignedAlarmStatus = value

    def setsaAmfSvcType(self, value):
        ImmHelper.validateName(value, self._dn, "saAmfSvcType")
        self._saAmfSvcType = value

    def addTosaAmfSIStandbyWeight(self, value):
        ImmHelper.validateString(value, self._dn, "saAmfSIStandbyWeight")
        self._saAmfSIStandbyWeight.append(value)

    def setsaAmfSIRank(self, value):
        ImmHelper.validateUint32(value, self._dn, "saAmfSIRank")
        value = str(value)
        self._saAmfSIRank = value

    def setsaAmfSIProtectedbySG(self, value):
        ImmHelper.validateName(value, self._dn, "saAmfSIProtectedbySG")
        self._saAmfSIProtectedbySG = value

    def setsaAmfSIPrefStandbyAssignments(self, value):
        ImmHelper.validateUint32(value, self._dn, "saAmfSIPrefStandbyAssignments")
        value = str(value)
        self._saAmfSIPrefStandbyAssignments = value

    def setsaAmfSIPrefActiveAssignments(self, value):
        ImmHelper.validateUint32(value, self._dn, "saAmfSIPrefActiveAssignments")
        value = str(value)
        self._saAmfSIPrefActiveAssignments = value

    def setsaAmfSINumCurrStandbyAssignments(self, value):
        ImmHelper.validateUint32(value, self._dn, "saAmfSINumCurrStandbyAssignments")
        value = str(value)
        self._saAmfSINumCurrStandbyAssignments = value

    def setsaAmfSINumCurrActiveAssignments(self, value):
        ImmHelper.validateUint32(value, self._dn, "saAmfSINumCurrActiveAssignments")
        value = str(value)
        self._saAmfSINumCurrActiveAssignments = value

    def setsaAmfSIAssignmentState(self, value):
        ImmHelper.validateUint32(value, self._dn, "saAmfSIAssignmentState")
        value = str(value)
        self._saAmfSIAssignmentState = value

    def setsaAmfSIAdminState(self, value):
        ImmHelper.validateUint32(value, self._dn, "saAmfSIAdminState")
        value = str(value)
        self._saAmfSIAdminState = value

    def addTosaAmfSIActiveWeight(self, value):
        ImmHelper.validateString(value, self._dn, "saAmfSIActiveWeight")
        self._saAmfSIActiveWeight.append(value)

    def setSaImmAttrImplementerName(self, value):
        ImmHelper.validateString(value, self._dn, "SaImmAttrImplementerName")
        self._SaImmAttrImplementerName = value

    def setSaImmAttrClassName(self, value):
        ImmHelper.validateString(value, self._dn, "SaImmAttrClassName")
        self._SaImmAttrClassName = value

    def setSaImmAttrAdminOwnerName(self, value):
        ImmHelper.validateString(value, self._dn, "SaImmAttrAdminOwnerName")
        self._SaImmAttrAdminOwnerName = value

    def updateParams(self, params, canttouchthis):
        for (param, value) in params.items():
            if param in canttouchthis:
                error("Setting attribute " + param + " in object " + self.getDn() + " is not supported")
            if param == "saAmfSvcType":
                self.setsaAmfSvcType(value)
            elif param == "saAmfSIStandbyWeight":
                if not isinstance(value, list):
                    value = [value]
                self._saAmfSIStandbyWeight = []
                for v in value:
                    self.addTosaAmfSIStandbyWeight(v)
            elif param == "saAmfSIRank":
                self.setsaAmfSIRank(value)
            elif param == "saAmfSIProtectedbySG":
                self.setsaAmfSIProtectedbySG(value)
            elif param == "saAmfSIPrefStandbyAssignments":
                self.setsaAmfSIPrefStandbyAssignments(value)
            elif param == "saAmfSIPrefActiveAssignments":
                self.setsaAmfSIPrefActiveAssignments(value)
            elif param == "saAmfSIActiveWeight":
                if not isinstance(value, list):
                    value = [value]
                self._saAmfSIActiveWeight = []
                for v in value:
                    self.addTosaAmfSIActiveWeight(v)
            else:
                error("Object " + self.getDn() + " has no attribute named " + param)

    def diff(self, other, fullCheck = False):
        changedAttrs = []
        if (fullCheck or self._saAmfSvcType != None) and other._saAmfSvcType != self._saAmfSvcType:
            changedAttrs.append("saAmfSvcType")
        if fullCheck or (len(self._saAmfSIStandbyWeight) != 0):
            if len(self._saAmfSIStandbyWeight) != len(other._saAmfSIStandbyWeight):
                changedAttrs.append("saAmfSIStandbyWeight")
            else:
                difflist = list(set(self._saAmfSIStandbyWeight) ^ set(other._saAmfSIStandbyWeight))
                if len(difflist) > 0:
                    changedAttrs.append("saAmfSIStandbyWeight")
        if (fullCheck or self._saAmfSIRank != None) and other._saAmfSIRank != self._saAmfSIRank:
            changedAttrs.append("saAmfSIRank")
        if (fullCheck or self._saAmfSIProtectedbySG != None) and other._saAmfSIProtectedbySG != self._saAmfSIProtectedbySG:
            changedAttrs.append("saAmfSIProtectedbySG")
        if (fullCheck or self._saAmfSIPrefStandbyAssignments != None) and other._saAmfSIPrefStandbyAssignments != self._saAmfSIPrefStandbyAssignments:
            changedAttrs.append("saAmfSIPrefStandbyAssignments")
        if (fullCheck or self._saAmfSIPrefActiveAssignments != None) and other._saAmfSIPrefActiveAssignments != self._saAmfSIPrefActiveAssignments:
            changedAttrs.append("saAmfSIPrefActiveAssignments")
        if fullCheck or (len(self._saAmfSIActiveWeight) != 0):
            if len(self._saAmfSIActiveWeight) != len(other._saAmfSIActiveWeight):
                changedAttrs.append("saAmfSIActiveWeight")
            else:
                difflist = list(set(self._saAmfSIActiveWeight) ^ set(other._saAmfSIActiveWeight))
                if len(difflist) > 0:
                    changedAttrs.append("saAmfSIActiveWeight")
        if (fullCheck or self._SaImmAttrImplementerName != None) and other._SaImmAttrImplementerName != self._SaImmAttrImplementerName:
            changedAttrs.append("SaImmAttrImplementerName")
        if (fullCheck or self._SaImmAttrClassName != None) and other._SaImmAttrClassName != self._SaImmAttrClassName:
            changedAttrs.append("SaImmAttrClassName")
        if (fullCheck or self._SaImmAttrAdminOwnerName != None) and other._SaImmAttrAdminOwnerName != self._SaImmAttrAdminOwnerName:
            changedAttrs.append("SaImmAttrAdminOwnerName")
        return changedAttrs

    def parseXML(self, node):
        dns = node.getElementsByTagName("dn")
        if len(dns) != 1:
            error("object has " + str(len(dns)) + " dn(s) but it should have one")
        self._dn = dns[0].childNodes[0].nodeValue
        for attribute in node.getElementsByTagName("attr"):
            names = attribute.getElementsByTagName("name")
            if len(names) != 1:
                error("object attribute has " + str(len(names)) + " name(s) but it should have one")
            name = names[0].childNodes[0].nodeValue
            setFunc = None
            if name == "SaImmAttrImplementerName":
                continue
            elif name == "SaImmAttrAdminOwnerName":
                continue
            elif name == "SaImmAttrClassName":
                continue
            elif name == "saAmfUnassignedAlarmStatus":
                setFunc = self.setsaAmfUnassignedAlarmStatus
            elif name == "saAmfSvcType":
                setFunc = self.setsaAmfSvcType
            elif name == "saAmfSIStandbyWeight":
                setFunc = self.addTosaAmfSIStandbyWeight
            elif name == "saAmfSIRank":
                setFunc = self.setsaAmfSIRank
            elif name == "saAmfSIProtectedbySG":
                setFunc = self.setsaAmfSIProtectedbySG
            elif name == "saAmfSIPrefStandbyAssignments":
                setFunc = self.setsaAmfSIPrefStandbyAssignments
            elif name == "saAmfSIPrefActiveAssignments":
                setFunc = self.setsaAmfSIPrefActiveAssignments
            elif name == "saAmfSINumCurrStandbyAssignments":
                setFunc = self.setsaAmfSINumCurrStandbyAssignments
            elif name == "saAmfSINumCurrActiveAssignments":
                setFunc = self.setsaAmfSINumCurrActiveAssignments
            elif name == "saAmfSIAssignmentState":
                setFunc = self.setsaAmfSIAssignmentState
            elif name == "saAmfSIAdminState":
                setFunc = self.setsaAmfSIAdminState
            elif name == "saAmfSIActiveWeight":
                setFunc = self.addTosaAmfSIActiveWeight
            elif name == "SaImmAttrImplementerName":
                setFunc = self.setSaImmAttrImplementerName
            elif name == "SaImmAttrClassName":
                setFunc = self.setSaImmAttrClassName
            elif name == "SaImmAttrAdminOwnerName":
                setFunc = self.setSaImmAttrAdminOwnerName
            elif name.startswith("osaf"):
                continue # ignore OpenSAF specific attributes
            else:
                error("unknown attribute called " + name + " defined in object " + self._dn)
            for value in attribute.getElementsByTagName("value"):
                setFunc(value.childNodes[0].nodeValue)

    def writeXML(self, parent, doc):
        obj = doc.createElement("object")
        parent.appendChild(obj)
        obj.setAttribute("class", "SaAmfSI")
        dn = doc.createElement("dn")
        obj.appendChild(dn)
        dn.appendChild(doc.createTextNode(self._dn))
        ImmHelper.writeSingleAttribute("saAmfUnassignedAlarmStatus", self._saAmfUnassignedAlarmStatus, doc, obj)
        ImmHelper.writeSingleAttribute("saAmfSvcType", self._saAmfSvcType, doc, obj)
        ImmHelper.writeMultiAttributes("saAmfSIStandbyWeight", self._saAmfSIStandbyWeight, doc, obj)
        ImmHelper.writeSingleAttribute("saAmfSIRank", self._saAmfSIRank, doc, obj)
        ImmHelper.writeSingleAttribute("saAmfSIProtectedbySG", self._saAmfSIProtectedbySG, doc, obj)
        ImmHelper.writeSingleAttribute("saAmfSIPrefStandbyAssignments", self._saAmfSIPrefStandbyAssignments, doc, obj)
        ImmHelper.writeSingleAttribute("saAmfSIPrefActiveAssignments", self._saAmfSIPrefActiveAssignments, doc, obj)
        ImmHelper.writeSingleAttribute("saAmfSINumCurrStandbyAssignments", self._saAmfSINumCurrStandbyAssignments, doc, obj)
        ImmHelper.writeSingleAttribute("saAmfSINumCurrActiveAssignments", self._saAmfSINumCurrActiveAssignments, doc, obj)
        ImmHelper.writeSingleAttribute("saAmfSIAssignmentState", self._saAmfSIAssignmentState, doc, obj)
        ImmHelper.writeSingleAttribute("saAmfSIAdminState", self._saAmfSIAdminState, doc, obj)
        ImmHelper.writeMultiAttributes("saAmfSIActiveWeight", self._saAmfSIActiveWeight, doc, obj)
        ImmHelper.writeSingleAttribute("SaImmAttrImplementerName", self._SaImmAttrImplementerName, doc, obj)
        ImmHelper.writeSingleAttribute("SaImmAttrClassName", self._SaImmAttrClassName, doc, obj)
        ImmHelper.writeSingleAttribute("SaImmAttrAdminOwnerName", self._SaImmAttrAdminOwnerName, doc, obj)


class SaAmfSGType(object):
    def __init__(self):
        self._dn = None
        self._saAmfSgtValidSuTypes = []
        self._saAmfSgtRedundancyModel = None
        self._saAmfSgtDefSuRestartProb = None
        self._saAmfSgtDefSuRestartMax = None
        self._saAmfSgtDefCompRestartProb = None
        self._saAmfSgtDefCompRestartMax = None
        self._saAmfSgtDefAutoRepair = None
        self._saAmfSgtDefAutoAdjustProb = None
        self._saAmfSgtDefAutoAdjust = None
        self._SaImmAttrImplementerName = None
        self._SaImmAttrClassName = None
        self._SaImmAttrAdminOwnerName = None

    @staticmethod
    def createDn(name, parentDn = None):
        if parentDn == None:
            parentDn = ""
        else:
            parentDn = "," + parentDn
        return "safVersion=" + ImmHelper.escapeName(name) + parentDn

    def getDn(self):
        return self._dn

    def getName(self):
        return ImmHelper.getName(self._dn)

    def getRdn(self):
        return ImmHelper.getRdn(self._dn)

    def getParentDn(self):
        return ImmHelper.getParentDn(self._dn)

    def createObjectInCampaign(self, campaign):
        parentDn = self.getParentDn()
        if parentDn == "":
            parentDn = "="
        campaign.beginCreate("SaAmfSGType", parentDn)
        campaign.addAttribute("safVersion", "SA_IMM_ATTR_SASTRINGT", self.getRdn())
        if len(self._saAmfSgtValidSuTypes) > 0:
            campaign.addAttribute("saAmfSgtValidSuTypes", "SA_IMM_ATTR_SANAMET", self._saAmfSgtValidSuTypes)
        if self._saAmfSgtRedundancyModel != None:
            campaign.addAttribute("saAmfSgtRedundancyModel", "SA_IMM_ATTR_SAUINT32T", self._saAmfSgtRedundancyModel)
        if self._saAmfSgtDefSuRestartProb != None:
            campaign.addAttribute("saAmfSgtDefSuRestartProb", "SA_IMM_ATTR_SATIMET", self._saAmfSgtDefSuRestartProb)
        if self._saAmfSgtDefSuRestartMax != None:
            campaign.addAttribute("saAmfSgtDefSuRestartMax", "SA_IMM_ATTR_SAUINT32T", self._saAmfSgtDefSuRestartMax)
        if self._saAmfSgtDefCompRestartProb != None:
            campaign.addAttribute("saAmfSgtDefCompRestartProb", "SA_IMM_ATTR_SATIMET", self._saAmfSgtDefCompRestartProb)
        if self._saAmfSgtDefCompRestartMax != None:
            campaign.addAttribute("saAmfSgtDefCompRestartMax", "SA_IMM_ATTR_SAUINT32T", self._saAmfSgtDefCompRestartMax)
        if self._saAmfSgtDefAutoRepair != None:
            campaign.addAttribute("saAmfSgtDefAutoRepair", "SA_IMM_ATTR_SAUINT32T", self._saAmfSgtDefAutoRepair)
        if self._saAmfSgtDefAutoAdjustProb != None:
            campaign.addAttribute("saAmfSgtDefAutoAdjustProb", "SA_IMM_ATTR_SATIMET", self._saAmfSgtDefAutoAdjustProb)
        if self._saAmfSgtDefAutoAdjust != None:
            campaign.addAttribute("saAmfSgtDefAutoAdjust", "SA_IMM_ATTR_SAUINT32T", self._saAmfSgtDefAutoAdjust)
        if self._SaImmAttrImplementerName != None:
            campaign.addAttribute("SaImmAttrImplementerName", "SA_IMM_ATTR_SASTRINGT", self._SaImmAttrImplementerName)
        if self._SaImmAttrClassName != None:
            campaign.addAttribute("SaImmAttrClassName", "SA_IMM_ATTR_SASTRINGT", self._SaImmAttrClassName)
        if self._SaImmAttrAdminOwnerName != None:
            campaign.addAttribute("SaImmAttrAdminOwnerName", "SA_IMM_ATTR_SASTRINGT", self._SaImmAttrAdminOwnerName)
        campaign.endCreate()

    def getsaAmfSgtValidSuTypes(self):
        return self._saAmfSgtValidSuTypes

    def getsaAmfSgtRedundancyModel(self):
        ImmHelper.validateSingle(self._saAmfSgtRedundancyModel, self._dn, "saAmfSgtRedundancyModel")
        return self._saAmfSgtRedundancyModel

    def getsaAmfSgtDefSuRestartProb(self):
        ImmHelper.validateSingle(self._saAmfSgtDefSuRestartProb, self._dn, "saAmfSgtDefSuRestartProb")
        return self._saAmfSgtDefSuRestartProb

    def getsaAmfSgtDefSuRestartMax(self):
        ImmHelper.validateSingle(self._saAmfSgtDefSuRestartMax, self._dn, "saAmfSgtDefSuRestartMax")
        return self._saAmfSgtDefSuRestartMax

    def getsaAmfSgtDefCompRestartProb(self):
        ImmHelper.validateSingle(self._saAmfSgtDefCompRestartProb, self._dn, "saAmfSgtDefCompRestartProb")
        return self._saAmfSgtDefCompRestartProb

    def getsaAmfSgtDefCompRestartMax(self):
        ImmHelper.validateSingle(self._saAmfSgtDefCompRestartMax, self._dn, "saAmfSgtDefCompRestartMax")
        return self._saAmfSgtDefCompRestartMax

    def getsaAmfSgtDefAutoRepair(self):
        ImmHelper.validateSingle(self._saAmfSgtDefAutoRepair, self._dn, "saAmfSgtDefAutoRepair")
        return self._saAmfSgtDefAutoRepair

    def getsaAmfSgtDefAutoAdjustProb(self):
        ImmHelper.validateSingle(self._saAmfSgtDefAutoAdjustProb, self._dn, "saAmfSgtDefAutoAdjustProb")
        return self._saAmfSgtDefAutoAdjustProb

    def getsaAmfSgtDefAutoAdjust(self):
        ImmHelper.validateSingle(self._saAmfSgtDefAutoAdjust, self._dn, "saAmfSgtDefAutoAdjust")
        return self._saAmfSgtDefAutoAdjust

    def getSaImmAttrImplementerName(self):
        ImmHelper.validateSingle(self._SaImmAttrImplementerName, self._dn, "SaImmAttrImplementerName")
        return self._SaImmAttrImplementerName

    def getSaImmAttrClassName(self):
        ImmHelper.validateSingle(self._SaImmAttrClassName, self._dn, "SaImmAttrClassName")
        return self._SaImmAttrClassName

    def getSaImmAttrAdminOwnerName(self):
        ImmHelper.validateSingle(self._SaImmAttrAdminOwnerName, self._dn, "SaImmAttrAdminOwnerName")
        return self._SaImmAttrAdminOwnerName

    def getsaAmfSgtValidSuTypes_single(self):
        ImmHelper.validateSingleInList(self._saAmfSgtValidSuTypes, self._dn, "saAmfSgtValidSuTypes")
        return self._saAmfSgtValidSuTypes[0]

    def getsaAmfSgtRedundancyModel_unsafe(self):
        return self._saAmfSgtRedundancyModel

    def getsaAmfSgtDefSuRestartProb_unsafe(self):
        return self._saAmfSgtDefSuRestartProb

    def getsaAmfSgtDefSuRestartMax_unsafe(self):
        return self._saAmfSgtDefSuRestartMax

    def getsaAmfSgtDefCompRestartProb_unsafe(self):
        return self._saAmfSgtDefCompRestartProb

    def getsaAmfSgtDefCompRestartMax_unsafe(self):
        return self._saAmfSgtDefCompRestartMax

    def getsaAmfSgtDefAutoRepair_unsafe(self):
        return self._saAmfSgtDefAutoRepair

    def getsaAmfSgtDefAutoAdjustProb_unsafe(self):
        return self._saAmfSgtDefAutoAdjustProb

    def getsaAmfSgtDefAutoAdjust_unsafe(self):
        return self._saAmfSgtDefAutoAdjust

    def getSaImmAttrImplementerName_unsafe(self):
        return self._SaImmAttrImplementerName

    def getSaImmAttrClassName_unsafe(self):
        return self._SaImmAttrClassName

    def getSaImmAttrAdminOwnerName_unsafe(self):
        return self._SaImmAttrAdminOwnerName

    def addTosaAmfSgtValidSuTypes(self, value):
        ImmHelper.validateName(value, self._dn, "saAmfSgtValidSuTypes")
        self._saAmfSgtValidSuTypes.append(value)

    def setsaAmfSgtRedundancyModel(self, value):
        ImmHelper.validateUint32(value, self._dn, "saAmfSgtRedundancyModel")
        value = str(value)
        self._saAmfSgtRedundancyModel = value

    def setsaAmfSgtDefSuRestartProb(self, value):
        ImmHelper.validateTime(value, self._dn, "saAmfSgtDefSuRestartProb")
        value = str(value)
        self._saAmfSgtDefSuRestartProb = value

    def setsaAmfSgtDefSuRestartMax(self, value):
        ImmHelper.validateUint32(value, self._dn, "saAmfSgtDefSuRestartMax")
        value = str(value)
        self._saAmfSgtDefSuRestartMax = value

    def setsaAmfSgtDefCompRestartProb(self, value):
        ImmHelper.validateTime(value, self._dn, "saAmfSgtDefCompRestartProb")
        value = str(value)
        self._saAmfSgtDefCompRestartProb = value

    def setsaAmfSgtDefCompRestartMax(self, value):
        ImmHelper.validateUint32(value, self._dn, "saAmfSgtDefCompRestartMax")
        value = str(value)
        self._saAmfSgtDefCompRestartMax = value

    def setsaAmfSgtDefAutoRepair(self, value):
        ImmHelper.validateUint32(value, self._dn, "saAmfSgtDefAutoRepair")
        value = str(value)
        self._saAmfSgtDefAutoRepair = value

    def setsaAmfSgtDefAutoAdjustProb(self, value):
        ImmHelper.validateTime(value, self._dn, "saAmfSgtDefAutoAdjustProb")
        value = str(value)
        self._saAmfSgtDefAutoAdjustProb = value

    def setsaAmfSgtDefAutoAdjust(self, value):
        ImmHelper.validateUint32(value, self._dn, "saAmfSgtDefAutoAdjust")
        value = str(value)
        self._saAmfSgtDefAutoAdjust = value

    def setSaImmAttrImplementerName(self, value):
        ImmHelper.validateString(value, self._dn, "SaImmAttrImplementerName")
        self._SaImmAttrImplementerName = value

    def setSaImmAttrClassName(self, value):
        ImmHelper.validateString(value, self._dn, "SaImmAttrClassName")
        self._SaImmAttrClassName = value

    def setSaImmAttrAdminOwnerName(self, value):
        ImmHelper.validateString(value, self._dn, "SaImmAttrAdminOwnerName")
        self._SaImmAttrAdminOwnerName = value

    def updateParams(self, params, canttouchthis):
        for (param, value) in params.items():
            if param in canttouchthis:
                error("Setting attribute " + param + " in object " + self.getDn() + " is not supported")
            if param == "saAmfSgtValidSuTypes":
                if not isinstance(value, list):
                    value = [value]
                self._saAmfSgtValidSuTypes = []
                for v in value:
                    self.addTosaAmfSgtValidSuTypes(v)
            elif param == "saAmfSgtDefSuRestartProb":
                self.setsaAmfSgtDefSuRestartProb(value)
            elif param == "saAmfSgtDefSuRestartMax":
                self.setsaAmfSgtDefSuRestartMax(value)
            elif param == "saAmfSgtDefCompRestartProb":
                self.setsaAmfSgtDefCompRestartProb(value)
            elif param == "saAmfSgtDefCompRestartMax":
                self.setsaAmfSgtDefCompRestartMax(value)
            elif param == "saAmfSgtDefAutoRepair":
                self.setsaAmfSgtDefAutoRepair(value)
            elif param == "saAmfSgtDefAutoAdjustProb":
                self.setsaAmfSgtDefAutoAdjustProb(value)
            elif param == "saAmfSgtDefAutoAdjust":
                self.setsaAmfSgtDefAutoAdjust(value)
            else:
                error("Object " + self.getDn() + " has no attribute named " + param)

    def diff(self, other, fullCheck = False):
        changedAttrs = []
        if fullCheck or (len(self._saAmfSgtValidSuTypes) != 0):
            if len(self._saAmfSgtValidSuTypes) != len(other._saAmfSgtValidSuTypes):
                changedAttrs.append("saAmfSgtValidSuTypes")
            else:
                difflist = list(set(self._saAmfSgtValidSuTypes) ^ set(other._saAmfSgtValidSuTypes))
                if len(difflist) > 0:
                    changedAttrs.append("saAmfSgtValidSuTypes")
        if (fullCheck or self._saAmfSgtRedundancyModel != None) and other._saAmfSgtRedundancyModel != self._saAmfSgtRedundancyModel:
            changedAttrs.append("saAmfSgtRedundancyModel")
        if (fullCheck or self._saAmfSgtDefSuRestartProb != None) and other._saAmfSgtDefSuRestartProb != self._saAmfSgtDefSuRestartProb:
            changedAttrs.append("saAmfSgtDefSuRestartProb")
        if (fullCheck or self._saAmfSgtDefSuRestartMax != None) and other._saAmfSgtDefSuRestartMax != self._saAmfSgtDefSuRestartMax:
            changedAttrs.append("saAmfSgtDefSuRestartMax")
        if (fullCheck or self._saAmfSgtDefCompRestartProb != None) and other._saAmfSgtDefCompRestartProb != self._saAmfSgtDefCompRestartProb:
            changedAttrs.append("saAmfSgtDefCompRestartProb")
        if (fullCheck or self._saAmfSgtDefCompRestartMax != None) and other._saAmfSgtDefCompRestartMax != self._saAmfSgtDefCompRestartMax:
            changedAttrs.append("saAmfSgtDefCompRestartMax")
        if (fullCheck or self._saAmfSgtDefAutoRepair != None) and other._saAmfSgtDefAutoRepair != self._saAmfSgtDefAutoRepair:
            changedAttrs.append("saAmfSgtDefAutoRepair")
        if (fullCheck or self._saAmfSgtDefAutoAdjustProb != None) and other._saAmfSgtDefAutoAdjustProb != self._saAmfSgtDefAutoAdjustProb:
            changedAttrs.append("saAmfSgtDefAutoAdjustProb")
        if (fullCheck or self._saAmfSgtDefAutoAdjust != None) and other._saAmfSgtDefAutoAdjust != self._saAmfSgtDefAutoAdjust:
            changedAttrs.append("saAmfSgtDefAutoAdjust")
        if (fullCheck or self._SaImmAttrImplementerName != None) and other._SaImmAttrImplementerName != self._SaImmAttrImplementerName:
            changedAttrs.append("SaImmAttrImplementerName")
        if (fullCheck or self._SaImmAttrClassName != None) and other._SaImmAttrClassName != self._SaImmAttrClassName:
            changedAttrs.append("SaImmAttrClassName")
        if (fullCheck or self._SaImmAttrAdminOwnerName != None) and other._SaImmAttrAdminOwnerName != self._SaImmAttrAdminOwnerName:
            changedAttrs.append("SaImmAttrAdminOwnerName")
        return changedAttrs

    def parseXML(self, node):
        dns = node.getElementsByTagName("dn")
        if len(dns) != 1:
            error("object has " + str(len(dns)) + " dn(s) but it should have one")
        self._dn = dns[0].childNodes[0].nodeValue
        for attribute in node.getElementsByTagName("attr"):
            names = attribute.getElementsByTagName("name")
            if len(names) != 1:
                error("object attribute has " + str(len(names)) + " name(s) but it should have one")
            name = names[0].childNodes[0].nodeValue
            setFunc = None
            if name == "SaImmAttrImplementerName":
                continue
            elif name == "SaImmAttrAdminOwnerName":
                continue
            elif name == "SaImmAttrClassName":
                continue
            elif name == "saAmfSgtValidSuTypes":
                setFunc = self.addTosaAmfSgtValidSuTypes
            elif name == "saAmfSgtRedundancyModel":
                setFunc = self.setsaAmfSgtRedundancyModel
            elif name == "saAmfSgtDefSuRestartProb":
                setFunc = self.setsaAmfSgtDefSuRestartProb
            elif name == "saAmfSgtDefSuRestartMax":
                setFunc = self.setsaAmfSgtDefSuRestartMax
            elif name == "saAmfSgtDefCompRestartProb":
                setFunc = self.setsaAmfSgtDefCompRestartProb
            elif name == "saAmfSgtDefCompRestartMax":
                setFunc = self.setsaAmfSgtDefCompRestartMax
            elif name == "saAmfSgtDefAutoRepair":
                setFunc = self.setsaAmfSgtDefAutoRepair
            elif name == "saAmfSgtDefAutoAdjustProb":
                setFunc = self.setsaAmfSgtDefAutoAdjustProb
            elif name == "saAmfSgtDefAutoAdjust":
                setFunc = self.setsaAmfSgtDefAutoAdjust
            elif name == "SaImmAttrImplementerName":
                setFunc = self.setSaImmAttrImplementerName
            elif name == "SaImmAttrClassName":
                setFunc = self.setSaImmAttrClassName
            elif name == "SaImmAttrAdminOwnerName":
                setFunc = self.setSaImmAttrAdminOwnerName
            elif name.startswith("osaf"):
                continue # ignore OpenSAF specific attributes
            else:
                error("unknown attribute called " + name + " defined in object " + self._dn)
            for value in attribute.getElementsByTagName("value"):
                setFunc(value.childNodes[0].nodeValue)

    def writeXML(self, parent, doc):
        obj = doc.createElement("object")
        parent.appendChild(obj)
        obj.setAttribute("class", "SaAmfSGType")
        dn = doc.createElement("dn")
        obj.appendChild(dn)
        dn.appendChild(doc.createTextNode(self._dn))
        ImmHelper.writeMultiAttributes("saAmfSgtValidSuTypes", self._saAmfSgtValidSuTypes, doc, obj)
        ImmHelper.writeSingleAttribute("saAmfSgtRedundancyModel", self._saAmfSgtRedundancyModel, doc, obj)
        ImmHelper.writeSingleAttribute("saAmfSgtDefSuRestartProb", self._saAmfSgtDefSuRestartProb, doc, obj)
        ImmHelper.writeSingleAttribute("saAmfSgtDefSuRestartMax", self._saAmfSgtDefSuRestartMax, doc, obj)
        ImmHelper.writeSingleAttribute("saAmfSgtDefCompRestartProb", self._saAmfSgtDefCompRestartProb, doc, obj)
        ImmHelper.writeSingleAttribute("saAmfSgtDefCompRestartMax", self._saAmfSgtDefCompRestartMax, doc, obj)
        ImmHelper.writeSingleAttribute("saAmfSgtDefAutoRepair", self._saAmfSgtDefAutoRepair, doc, obj)
        ImmHelper.writeSingleAttribute("saAmfSgtDefAutoAdjustProb", self._saAmfSgtDefAutoAdjustProb, doc, obj)
        ImmHelper.writeSingleAttribute("saAmfSgtDefAutoAdjust", self._saAmfSgtDefAutoAdjust, doc, obj)
        ImmHelper.writeSingleAttribute("SaImmAttrImplementerName", self._SaImmAttrImplementerName, doc, obj)
        ImmHelper.writeSingleAttribute("SaImmAttrClassName", self._SaImmAttrClassName, doc, obj)
        ImmHelper.writeSingleAttribute("SaImmAttrAdminOwnerName", self._SaImmAttrAdminOwnerName, doc, obj)


class SaAmfSGBaseType(object):
    def __init__(self):
        self._dn = None
        self._SaImmAttrImplementerName = None
        self._SaImmAttrClassName = None
        self._SaImmAttrAdminOwnerName = None

    @staticmethod
    def createDn(name, parentDn = None):
        if parentDn == None:
            parentDn = ""
        else:
            parentDn = "," + parentDn
        return "safSgType=" + ImmHelper.escapeName(name) + parentDn

    def getDn(self):
        return self._dn

    def getName(self):
        return ImmHelper.getName(self._dn)

    def getRdn(self):
        return ImmHelper.getRdn(self._dn)

    def getParentDn(self):
        return ImmHelper.getParentDn(self._dn)

    def createObjectInCampaign(self, campaign):
        parentDn = self.getParentDn()
        if parentDn == "":
            parentDn = "="
        campaign.beginCreate("SaAmfSGBaseType", parentDn)
        campaign.addAttribute("safSgType", "SA_IMM_ATTR_SASTRINGT", self.getRdn())
        if self._SaImmAttrImplementerName != None:
            campaign.addAttribute("SaImmAttrImplementerName", "SA_IMM_ATTR_SASTRINGT", self._SaImmAttrImplementerName)
        if self._SaImmAttrClassName != None:
            campaign.addAttribute("SaImmAttrClassName", "SA_IMM_ATTR_SASTRINGT", self._SaImmAttrClassName)
        if self._SaImmAttrAdminOwnerName != None:
            campaign.addAttribute("SaImmAttrAdminOwnerName", "SA_IMM_ATTR_SASTRINGT", self._SaImmAttrAdminOwnerName)
        campaign.endCreate()

    def getSaImmAttrImplementerName(self):
        ImmHelper.validateSingle(self._SaImmAttrImplementerName, self._dn, "SaImmAttrImplementerName")
        return self._SaImmAttrImplementerName

    def getSaImmAttrClassName(self):
        ImmHelper.validateSingle(self._SaImmAttrClassName, self._dn, "SaImmAttrClassName")
        return self._SaImmAttrClassName

    def getSaImmAttrAdminOwnerName(self):
        ImmHelper.validateSingle(self._SaImmAttrAdminOwnerName, self._dn, "SaImmAttrAdminOwnerName")
        return self._SaImmAttrAdminOwnerName

    def getSaImmAttrImplementerName_unsafe(self):
        return self._SaImmAttrImplementerName

    def getSaImmAttrClassName_unsafe(self):
        return self._SaImmAttrClassName

    def getSaImmAttrAdminOwnerName_unsafe(self):
        return self._SaImmAttrAdminOwnerName

    def setSaImmAttrImplementerName(self, value):
        ImmHelper.validateString(value, self._dn, "SaImmAttrImplementerName")
        self._SaImmAttrImplementerName = value

    def setSaImmAttrClassName(self, value):
        ImmHelper.validateString(value, self._dn, "SaImmAttrClassName")
        self._SaImmAttrClassName = value

    def setSaImmAttrAdminOwnerName(self, value):
        ImmHelper.validateString(value, self._dn, "SaImmAttrAdminOwnerName")
        self._SaImmAttrAdminOwnerName = value

    def updateParams(self, params, canttouchthis):
        for (param, value) in params.items():
            if param in canttouchthis:
                error("Setting attribute " + param + " in object " + self.getDn() + " is not supported")
            else:
                error("Object " + self.getDn() + " has no attribute named " + param)

    def diff(self, other, fullCheck = False):
        changedAttrs = []
        if (fullCheck or self._SaImmAttrImplementerName != None) and other._SaImmAttrImplementerName != self._SaImmAttrImplementerName:
            changedAttrs.append("SaImmAttrImplementerName")
        if (fullCheck or self._SaImmAttrClassName != None) and other._SaImmAttrClassName != self._SaImmAttrClassName:
            changedAttrs.append("SaImmAttrClassName")
        if (fullCheck or self._SaImmAttrAdminOwnerName != None) and other._SaImmAttrAdminOwnerName != self._SaImmAttrAdminOwnerName:
            changedAttrs.append("SaImmAttrAdminOwnerName")
        return changedAttrs

    def parseXML(self, node):
        dns = node.getElementsByTagName("dn")
        if len(dns) != 1:
            error("object has " + str(len(dns)) + " dn(s) but it should have one")
        self._dn = dns[0].childNodes[0].nodeValue
        for attribute in node.getElementsByTagName("attr"):
            names = attribute.getElementsByTagName("name")
            if len(names) != 1:
                error("object attribute has " + str(len(names)) + " name(s) but it should have one")
            name = names[0].childNodes[0].nodeValue
            setFunc = None
            if name == "SaImmAttrImplementerName":
                continue
            elif name == "SaImmAttrAdminOwnerName":
                continue
            elif name == "SaImmAttrClassName":
                continue
            elif name == "SaImmAttrImplementerName":
                setFunc = self.setSaImmAttrImplementerName
            elif name == "SaImmAttrClassName":
                setFunc = self.setSaImmAttrClassName
            elif name == "SaImmAttrAdminOwnerName":
                setFunc = self.setSaImmAttrAdminOwnerName
            elif name.startswith("osaf"):
                continue # ignore OpenSAF specific attributes
            else:
                error("unknown attribute called " + name + " defined in object " + self._dn)
            for value in attribute.getElementsByTagName("value"):
                setFunc(value.childNodes[0].nodeValue)

    def writeXML(self, parent, doc):
        obj = doc.createElement("object")
        parent.appendChild(obj)
        obj.setAttribute("class", "SaAmfSGBaseType")
        dn = doc.createElement("dn")
        obj.appendChild(dn)
        dn.appendChild(doc.createTextNode(self._dn))
        ImmHelper.writeSingleAttribute("SaImmAttrImplementerName", self._SaImmAttrImplementerName, doc, obj)
        ImmHelper.writeSingleAttribute("SaImmAttrClassName", self._SaImmAttrClassName, doc, obj)
        ImmHelper.writeSingleAttribute("SaImmAttrAdminOwnerName", self._SaImmAttrAdminOwnerName, doc, obj)


class SaAmfSG(object):
    def __init__(self):
        self._dn = None
        self._saAmfSGType = None
        self._saAmfSGSuRestartProb = None
        self._saAmfSGSuRestartMax = None
        self._saAmfSGSuHostNodeGroup = None
        self._saAmfSGNumPrefStandbySUs = None
        self._saAmfSGNumPrefInserviceSUs = None
        self._saAmfSGNumPrefAssignedSUs = None
        self._saAmfSGNumPrefActiveSUs = None
        self._saAmfSGNumCurrNonInstantiatedSpareSUs = None
        self._saAmfSGNumCurrInstantiatedSpareSUs = None
        self._saAmfSGNumCurrAssignedSUs = None
        self._saAmfSGMaxStandbySIsperSU = None
        self._saAmfSGMaxActiveSIsperSU = None
        self._saAmfSGCompRestartProb = None
        self._saAmfSGCompRestartMax = None
        self._saAmfSGAutoRepair = None
        self._saAmfSGAutoAdjustProb = None
        self._saAmfSGAutoAdjust = None
        self._saAmfSGAdminState = None
        self._SaImmAttrImplementerName = None
        self._SaImmAttrClassName = None
        self._SaImmAttrAdminOwnerName = None

    @staticmethod
    def createDn(name, parentDn = None):
        if parentDn == None:
            parentDn = ""
        else:
            parentDn = "," + parentDn
        return "safSg=" + ImmHelper.escapeName(name) + parentDn

    def getDn(self):
        return self._dn

    def getName(self):
        return ImmHelper.getName(self._dn)

    def getRdn(self):
        return ImmHelper.getRdn(self._dn)

    def getParentDn(self):
        return ImmHelper.getParentDn(self._dn)

    def createObjectInCampaign(self, campaign):
        parentDn = self.getParentDn()
        if parentDn == "":
            parentDn = "="
        campaign.beginCreate("SaAmfSG", parentDn)
        campaign.addAttribute("safSg", "SA_IMM_ATTR_SASTRINGT", self.getRdn())
        if self._saAmfSGType != None:
            campaign.addAttribute("saAmfSGType", "SA_IMM_ATTR_SANAMET", self._saAmfSGType)
        if self._saAmfSGSuRestartProb != None:
            campaign.addAttribute("saAmfSGSuRestartProb", "SA_IMM_ATTR_SATIMET", self._saAmfSGSuRestartProb)
        if self._saAmfSGSuRestartMax != None:
            campaign.addAttribute("saAmfSGSuRestartMax", "SA_IMM_ATTR_SAUINT32T", self._saAmfSGSuRestartMax)
        if self._saAmfSGSuHostNodeGroup != None:
            campaign.addAttribute("saAmfSGSuHostNodeGroup", "SA_IMM_ATTR_SANAMET", self._saAmfSGSuHostNodeGroup)
        if self._saAmfSGNumPrefStandbySUs != None:
            campaign.addAttribute("saAmfSGNumPrefStandbySUs", "SA_IMM_ATTR_SAUINT32T", self._saAmfSGNumPrefStandbySUs)
        if self._saAmfSGNumPrefInserviceSUs != None:
            campaign.addAttribute("saAmfSGNumPrefInserviceSUs", "SA_IMM_ATTR_SAUINT32T", self._saAmfSGNumPrefInserviceSUs)
        if self._saAmfSGNumPrefAssignedSUs != None:
            campaign.addAttribute("saAmfSGNumPrefAssignedSUs", "SA_IMM_ATTR_SAUINT32T", self._saAmfSGNumPrefAssignedSUs)
        if self._saAmfSGNumPrefActiveSUs != None:
            campaign.addAttribute("saAmfSGNumPrefActiveSUs", "SA_IMM_ATTR_SAUINT32T", self._saAmfSGNumPrefActiveSUs)
        if self._saAmfSGMaxStandbySIsperSU != None:
            campaign.addAttribute("saAmfSGMaxStandbySIsperSU", "SA_IMM_ATTR_SAUINT32T", self._saAmfSGMaxStandbySIsperSU)
        if self._saAmfSGMaxActiveSIsperSU != None:
            campaign.addAttribute("saAmfSGMaxActiveSIsperSU", "SA_IMM_ATTR_SAUINT32T", self._saAmfSGMaxActiveSIsperSU)
        if self._saAmfSGCompRestartProb != None:
            campaign.addAttribute("saAmfSGCompRestartProb", "SA_IMM_ATTR_SATIMET", self._saAmfSGCompRestartProb)
        if self._saAmfSGCompRestartMax != None:
            campaign.addAttribute("saAmfSGCompRestartMax", "SA_IMM_ATTR_SAUINT32T", self._saAmfSGCompRestartMax)
        if self._saAmfSGAutoRepair != None:
            campaign.addAttribute("saAmfSGAutoRepair", "SA_IMM_ATTR_SAUINT32T", self._saAmfSGAutoRepair)
        if self._saAmfSGAutoAdjustProb != None:
            campaign.addAttribute("saAmfSGAutoAdjustProb", "SA_IMM_ATTR_SATIMET", self._saAmfSGAutoAdjustProb)
        if self._saAmfSGAutoAdjust != None:
            campaign.addAttribute("saAmfSGAutoAdjust", "SA_IMM_ATTR_SAUINT32T", self._saAmfSGAutoAdjust)
        if self._saAmfSGAdminState != None:
            campaign.addAttribute("saAmfSGAdminState", "SA_IMM_ATTR_SAUINT32T", self._saAmfSGAdminState)
        if self._SaImmAttrImplementerName != None:
            campaign.addAttribute("SaImmAttrImplementerName", "SA_IMM_ATTR_SASTRINGT", self._SaImmAttrImplementerName)
        if self._SaImmAttrClassName != None:
            campaign.addAttribute("SaImmAttrClassName", "SA_IMM_ATTR_SASTRINGT", self._SaImmAttrClassName)
        if self._SaImmAttrAdminOwnerName != None:
            campaign.addAttribute("SaImmAttrAdminOwnerName", "SA_IMM_ATTR_SASTRINGT", self._SaImmAttrAdminOwnerName)
        campaign.endCreate()

    def getsaAmfSGType(self):
        ImmHelper.validateSingle(self._saAmfSGType, self._dn, "saAmfSGType")
        return self._saAmfSGType

    def getsaAmfSGSuRestartProb(self):
        ImmHelper.validateSingle(self._saAmfSGSuRestartProb, self._dn, "saAmfSGSuRestartProb")
        return self._saAmfSGSuRestartProb

    def getsaAmfSGSuRestartMax(self):
        ImmHelper.validateSingle(self._saAmfSGSuRestartMax, self._dn, "saAmfSGSuRestartMax")
        return self._saAmfSGSuRestartMax

    def getsaAmfSGSuHostNodeGroup(self):
        ImmHelper.validateSingle(self._saAmfSGSuHostNodeGroup, self._dn, "saAmfSGSuHostNodeGroup")
        return self._saAmfSGSuHostNodeGroup

    def getsaAmfSGNumPrefStandbySUs(self):
        ImmHelper.validateSingle(self._saAmfSGNumPrefStandbySUs, self._dn, "saAmfSGNumPrefStandbySUs")
        return self._saAmfSGNumPrefStandbySUs

    def getsaAmfSGNumPrefInserviceSUs(self):
        ImmHelper.validateSingle(self._saAmfSGNumPrefInserviceSUs, self._dn, "saAmfSGNumPrefInserviceSUs")
        return self._saAmfSGNumPrefInserviceSUs

    def getsaAmfSGNumPrefAssignedSUs(self):
        ImmHelper.validateSingle(self._saAmfSGNumPrefAssignedSUs, self._dn, "saAmfSGNumPrefAssignedSUs")
        return self._saAmfSGNumPrefAssignedSUs

    def getsaAmfSGNumPrefActiveSUs(self):
        ImmHelper.validateSingle(self._saAmfSGNumPrefActiveSUs, self._dn, "saAmfSGNumPrefActiveSUs")
        return self._saAmfSGNumPrefActiveSUs

    def getsaAmfSGNumCurrNonInstantiatedSpareSUs(self):
        ImmHelper.validateSingle(self._saAmfSGNumCurrNonInstantiatedSpareSUs, self._dn, "saAmfSGNumCurrNonInstantiatedSpareSUs")
        return self._saAmfSGNumCurrNonInstantiatedSpareSUs

    def getsaAmfSGNumCurrInstantiatedSpareSUs(self):
        ImmHelper.validateSingle(self._saAmfSGNumCurrInstantiatedSpareSUs, self._dn, "saAmfSGNumCurrInstantiatedSpareSUs")
        return self._saAmfSGNumCurrInstantiatedSpareSUs

    def getsaAmfSGNumCurrAssignedSUs(self):
        ImmHelper.validateSingle(self._saAmfSGNumCurrAssignedSUs, self._dn, "saAmfSGNumCurrAssignedSUs")
        return self._saAmfSGNumCurrAssignedSUs

    def getsaAmfSGMaxStandbySIsperSU(self):
        ImmHelper.validateSingle(self._saAmfSGMaxStandbySIsperSU, self._dn, "saAmfSGMaxStandbySIsperSU")
        return self._saAmfSGMaxStandbySIsperSU

    def getsaAmfSGMaxActiveSIsperSU(self):
        ImmHelper.validateSingle(self._saAmfSGMaxActiveSIsperSU, self._dn, "saAmfSGMaxActiveSIsperSU")
        return self._saAmfSGMaxActiveSIsperSU

    def getsaAmfSGCompRestartProb(self):
        ImmHelper.validateSingle(self._saAmfSGCompRestartProb, self._dn, "saAmfSGCompRestartProb")
        return self._saAmfSGCompRestartProb

    def getsaAmfSGCompRestartMax(self):
        ImmHelper.validateSingle(self._saAmfSGCompRestartMax, self._dn, "saAmfSGCompRestartMax")
        return self._saAmfSGCompRestartMax

    def getsaAmfSGAutoRepair(self):
        ImmHelper.validateSingle(self._saAmfSGAutoRepair, self._dn, "saAmfSGAutoRepair")
        return self._saAmfSGAutoRepair

    def getsaAmfSGAutoAdjustProb(self):
        ImmHelper.validateSingle(self._saAmfSGAutoAdjustProb, self._dn, "saAmfSGAutoAdjustProb")
        return self._saAmfSGAutoAdjustProb

    def getsaAmfSGAutoAdjust(self):
        ImmHelper.validateSingle(self._saAmfSGAutoAdjust, self._dn, "saAmfSGAutoAdjust")
        return self._saAmfSGAutoAdjust

    def getsaAmfSGAdminState(self):
        ImmHelper.validateSingle(self._saAmfSGAdminState, self._dn, "saAmfSGAdminState")
        return self._saAmfSGAdminState

    def getSaImmAttrImplementerName(self):
        ImmHelper.validateSingle(self._SaImmAttrImplementerName, self._dn, "SaImmAttrImplementerName")
        return self._SaImmAttrImplementerName

    def getSaImmAttrClassName(self):
        ImmHelper.validateSingle(self._SaImmAttrClassName, self._dn, "SaImmAttrClassName")
        return self._SaImmAttrClassName

    def getSaImmAttrAdminOwnerName(self):
        ImmHelper.validateSingle(self._SaImmAttrAdminOwnerName, self._dn, "SaImmAttrAdminOwnerName")
        return self._SaImmAttrAdminOwnerName

    def getsaAmfSGType_unsafe(self):
        return self._saAmfSGType

    def getsaAmfSGSuRestartProb_unsafe(self):
        return self._saAmfSGSuRestartProb

    def getsaAmfSGSuRestartMax_unsafe(self):
        return self._saAmfSGSuRestartMax

    def getsaAmfSGSuHostNodeGroup_unsafe(self):
        return self._saAmfSGSuHostNodeGroup

    def getsaAmfSGNumPrefStandbySUs_unsafe(self):
        return self._saAmfSGNumPrefStandbySUs

    def getsaAmfSGNumPrefInserviceSUs_unsafe(self):
        return self._saAmfSGNumPrefInserviceSUs

    def getsaAmfSGNumPrefAssignedSUs_unsafe(self):
        return self._saAmfSGNumPrefAssignedSUs

    def getsaAmfSGNumPrefActiveSUs_unsafe(self):
        return self._saAmfSGNumPrefActiveSUs

    def getsaAmfSGNumCurrNonInstantiatedSpareSUs_unsafe(self):
        return self._saAmfSGNumCurrNonInstantiatedSpareSUs

    def getsaAmfSGNumCurrInstantiatedSpareSUs_unsafe(self):
        return self._saAmfSGNumCurrInstantiatedSpareSUs

    def getsaAmfSGNumCurrAssignedSUs_unsafe(self):
        return self._saAmfSGNumCurrAssignedSUs

    def getsaAmfSGMaxStandbySIsperSU_unsafe(self):
        return self._saAmfSGMaxStandbySIsperSU

    def getsaAmfSGMaxActiveSIsperSU_unsafe(self):
        return self._saAmfSGMaxActiveSIsperSU

    def getsaAmfSGCompRestartProb_unsafe(self):
        return self._saAmfSGCompRestartProb

    def getsaAmfSGCompRestartMax_unsafe(self):
        return self._saAmfSGCompRestartMax

    def getsaAmfSGAutoRepair_unsafe(self):
        return self._saAmfSGAutoRepair

    def getsaAmfSGAutoAdjustProb_unsafe(self):
        return self._saAmfSGAutoAdjustProb

    def getsaAmfSGAutoAdjust_unsafe(self):
        return self._saAmfSGAutoAdjust

    def getsaAmfSGAdminState_unsafe(self):
        return self._saAmfSGAdminState

    def getSaImmAttrImplementerName_unsafe(self):
        return self._SaImmAttrImplementerName

    def getSaImmAttrClassName_unsafe(self):
        return self._SaImmAttrClassName

    def getSaImmAttrAdminOwnerName_unsafe(self):
        return self._SaImmAttrAdminOwnerName

    def setsaAmfSGType(self, value):
        ImmHelper.validateName(value, self._dn, "saAmfSGType")
        self._saAmfSGType = value

    def setsaAmfSGSuRestartProb(self, value):
        ImmHelper.validateTime(value, self._dn, "saAmfSGSuRestartProb")
        value = str(value)
        self._saAmfSGSuRestartProb = value

    def setsaAmfSGSuRestartMax(self, value):
        ImmHelper.validateUint32(value, self._dn, "saAmfSGSuRestartMax")
        value = str(value)
        self._saAmfSGSuRestartMax = value

    def setsaAmfSGSuHostNodeGroup(self, value):
        ImmHelper.validateName(value, self._dn, "saAmfSGSuHostNodeGroup")
        self._saAmfSGSuHostNodeGroup = value

    def setsaAmfSGNumPrefStandbySUs(self, value):
        ImmHelper.validateUint32(value, self._dn, "saAmfSGNumPrefStandbySUs")
        value = str(value)
        self._saAmfSGNumPrefStandbySUs = value

    def setsaAmfSGNumPrefInserviceSUs(self, value):
        ImmHelper.validateUint32(value, self._dn, "saAmfSGNumPrefInserviceSUs")
        value = str(value)
        self._saAmfSGNumPrefInserviceSUs = value

    def setsaAmfSGNumPrefAssignedSUs(self, value):
        ImmHelper.validateUint32(value, self._dn, "saAmfSGNumPrefAssignedSUs")
        value = str(value)
        self._saAmfSGNumPrefAssignedSUs = value

    def setsaAmfSGNumPrefActiveSUs(self, value):
        ImmHelper.validateUint32(value, self._dn, "saAmfSGNumPrefActiveSUs")
        value = str(value)
        self._saAmfSGNumPrefActiveSUs = value

    def setsaAmfSGNumCurrNonInstantiatedSpareSUs(self, value):
        ImmHelper.validateUint32(value, self._dn, "saAmfSGNumCurrNonInstantiatedSpareSUs")
        value = str(value)
        self._saAmfSGNumCurrNonInstantiatedSpareSUs = value

    def setsaAmfSGNumCurrInstantiatedSpareSUs(self, value):
        ImmHelper.validateUint32(value, self._dn, "saAmfSGNumCurrInstantiatedSpareSUs")
        value = str(value)
        self._saAmfSGNumCurrInstantiatedSpareSUs = value

    def setsaAmfSGNumCurrAssignedSUs(self, value):
        ImmHelper.validateUint32(value, self._dn, "saAmfSGNumCurrAssignedSUs")
        value = str(value)
        self._saAmfSGNumCurrAssignedSUs = value

    def setsaAmfSGMaxStandbySIsperSU(self, value):
        ImmHelper.validateUint32(value, self._dn, "saAmfSGMaxStandbySIsperSU")
        value = str(value)
        self._saAmfSGMaxStandbySIsperSU = value

    def setsaAmfSGMaxActiveSIsperSU(self, value):
        ImmHelper.validateUint32(value, self._dn, "saAmfSGMaxActiveSIsperSU")
        value = str(value)
        self._saAmfSGMaxActiveSIsperSU = value

    def setsaAmfSGCompRestartProb(self, value):
        ImmHelper.validateTime(value, self._dn, "saAmfSGCompRestartProb")
        value = str(value)
        self._saAmfSGCompRestartProb = value

    def setsaAmfSGCompRestartMax(self, value):
        ImmHelper.validateUint32(value, self._dn, "saAmfSGCompRestartMax")
        value = str(value)
        self._saAmfSGCompRestartMax = value

    def setsaAmfSGAutoRepair(self, value):
        ImmHelper.validateUint32(value, self._dn, "saAmfSGAutoRepair")
        value = str(value)
        self._saAmfSGAutoRepair = value

    def setsaAmfSGAutoAdjustProb(self, value):
        ImmHelper.validateTime(value, self._dn, "saAmfSGAutoAdjustProb")
        value = str(value)
        self._saAmfSGAutoAdjustProb = value

    def setsaAmfSGAutoAdjust(self, value):
        ImmHelper.validateUint32(value, self._dn, "saAmfSGAutoAdjust")
        value = str(value)
        self._saAmfSGAutoAdjust = value

    def setsaAmfSGAdminState(self, value):
        ImmHelper.validateUint32(value, self._dn, "saAmfSGAdminState")
        value = str(value)
        self._saAmfSGAdminState = value

    def setSaImmAttrImplementerName(self, value):
        ImmHelper.validateString(value, self._dn, "SaImmAttrImplementerName")
        self._SaImmAttrImplementerName = value

    def setSaImmAttrClassName(self, value):
        ImmHelper.validateString(value, self._dn, "SaImmAttrClassName")
        self._SaImmAttrClassName = value

    def setSaImmAttrAdminOwnerName(self, value):
        ImmHelper.validateString(value, self._dn, "SaImmAttrAdminOwnerName")
        self._SaImmAttrAdminOwnerName = value

    def updateParams(self, params, canttouchthis):
        for (param, value) in params.items():
            if param in canttouchthis:
                error("Setting attribute " + param + " in object " + self.getDn() + " is not supported")
            if param == "saAmfSGType":
                self.setsaAmfSGType(value)
            elif param == "saAmfSGSuRestartProb":
                self.setsaAmfSGSuRestartProb(value)
            elif param == "saAmfSGSuRestartMax":
                self.setsaAmfSGSuRestartMax(value)
            elif param == "saAmfSGSuHostNodeGroup":
                self.setsaAmfSGSuHostNodeGroup(value)
            elif param == "saAmfSGNumPrefStandbySUs":
                self.setsaAmfSGNumPrefStandbySUs(value)
            elif param == "saAmfSGNumPrefInserviceSUs":
                self.setsaAmfSGNumPrefInserviceSUs(value)
            elif param == "saAmfSGNumPrefAssignedSUs":
                self.setsaAmfSGNumPrefAssignedSUs(value)
            elif param == "saAmfSGNumPrefActiveSUs":
                self.setsaAmfSGNumPrefActiveSUs(value)
            elif param == "saAmfSGMaxStandbySIsperSU":
                self.setsaAmfSGMaxStandbySIsperSU(value)
            elif param == "saAmfSGMaxActiveSIsperSU":
                self.setsaAmfSGMaxActiveSIsperSU(value)
            elif param == "saAmfSGCompRestartProb":
                self.setsaAmfSGCompRestartProb(value)
            elif param == "saAmfSGCompRestartMax":
                self.setsaAmfSGCompRestartMax(value)
            elif param == "saAmfSGAutoRepair":
                self.setsaAmfSGAutoRepair(value)
            elif param == "saAmfSGAutoAdjustProb":
                self.setsaAmfSGAutoAdjustProb(value)
            elif param == "saAmfSGAutoAdjust":
                self.setsaAmfSGAutoAdjust(value)
            else:
                error("Object " + self.getDn() + " has no attribute named " + param)

    def diff(self, other, fullCheck = False):
        changedAttrs = []
        if (fullCheck or self._saAmfSGType != None) and other._saAmfSGType != self._saAmfSGType:
            changedAttrs.append("saAmfSGType")
        if (fullCheck or self._saAmfSGSuRestartProb != None) and other._saAmfSGSuRestartProb != self._saAmfSGSuRestartProb:
            changedAttrs.append("saAmfSGSuRestartProb")
        if (fullCheck or self._saAmfSGSuRestartMax != None) and other._saAmfSGSuRestartMax != self._saAmfSGSuRestartMax:
            changedAttrs.append("saAmfSGSuRestartMax")
        if (fullCheck or self._saAmfSGSuHostNodeGroup != None) and other._saAmfSGSuHostNodeGroup != self._saAmfSGSuHostNodeGroup:
            changedAttrs.append("saAmfSGSuHostNodeGroup")
        if (fullCheck or self._saAmfSGNumPrefStandbySUs != None) and other._saAmfSGNumPrefStandbySUs != self._saAmfSGNumPrefStandbySUs:
            changedAttrs.append("saAmfSGNumPrefStandbySUs")
        if (fullCheck or self._saAmfSGNumPrefInserviceSUs != None) and other._saAmfSGNumPrefInserviceSUs != self._saAmfSGNumPrefInserviceSUs:
            changedAttrs.append("saAmfSGNumPrefInserviceSUs")
        if (fullCheck or self._saAmfSGNumPrefAssignedSUs != None) and other._saAmfSGNumPrefAssignedSUs != self._saAmfSGNumPrefAssignedSUs:
            changedAttrs.append("saAmfSGNumPrefAssignedSUs")
        if (fullCheck or self._saAmfSGNumPrefActiveSUs != None) and other._saAmfSGNumPrefActiveSUs != self._saAmfSGNumPrefActiveSUs:
            changedAttrs.append("saAmfSGNumPrefActiveSUs")
        if (fullCheck or self._saAmfSGMaxStandbySIsperSU != None) and other._saAmfSGMaxStandbySIsperSU != self._saAmfSGMaxStandbySIsperSU:
            changedAttrs.append("saAmfSGMaxStandbySIsperSU")
        if (fullCheck or self._saAmfSGMaxActiveSIsperSU != None) and other._saAmfSGMaxActiveSIsperSU != self._saAmfSGMaxActiveSIsperSU:
            changedAttrs.append("saAmfSGMaxActiveSIsperSU")
        if (fullCheck or self._saAmfSGCompRestartProb != None) and other._saAmfSGCompRestartProb != self._saAmfSGCompRestartProb:
            changedAttrs.append("saAmfSGCompRestartProb")
        if (fullCheck or self._saAmfSGCompRestartMax != None) and other._saAmfSGCompRestartMax != self._saAmfSGCompRestartMax:
            changedAttrs.append("saAmfSGCompRestartMax")
        if (fullCheck or self._saAmfSGAutoRepair != None) and other._saAmfSGAutoRepair != self._saAmfSGAutoRepair:
            changedAttrs.append("saAmfSGAutoRepair")
        if (fullCheck or self._saAmfSGAutoAdjustProb != None) and other._saAmfSGAutoAdjustProb != self._saAmfSGAutoAdjustProb:
            changedAttrs.append("saAmfSGAutoAdjustProb")
        if (fullCheck or self._saAmfSGAutoAdjust != None) and other._saAmfSGAutoAdjust != self._saAmfSGAutoAdjust:
            changedAttrs.append("saAmfSGAutoAdjust")
        if (fullCheck or self._SaImmAttrImplementerName != None) and other._SaImmAttrImplementerName != self._SaImmAttrImplementerName:
            changedAttrs.append("SaImmAttrImplementerName")
        if (fullCheck or self._SaImmAttrClassName != None) and other._SaImmAttrClassName != self._SaImmAttrClassName:
            changedAttrs.append("SaImmAttrClassName")
        if (fullCheck or self._SaImmAttrAdminOwnerName != None) and other._SaImmAttrAdminOwnerName != self._SaImmAttrAdminOwnerName:
            changedAttrs.append("SaImmAttrAdminOwnerName")
        return changedAttrs

    def parseXML(self, node):
        dns = node.getElementsByTagName("dn")
        if len(dns) != 1:
            error("object has " + str(len(dns)) + " dn(s) but it should have one")
        self._dn = dns[0].childNodes[0].nodeValue
        for attribute in node.getElementsByTagName("attr"):
            names = attribute.getElementsByTagName("name")
            if len(names) != 1:
                error("object attribute has " + str(len(names)) + " name(s) but it should have one")
            name = names[0].childNodes[0].nodeValue
            setFunc = None
            if name == "SaImmAttrImplementerName":
                continue
            elif name == "SaImmAttrAdminOwnerName":
                continue
            elif name == "SaImmAttrClassName":
                continue
            elif name == "saAmfSGType":
                setFunc = self.setsaAmfSGType
            elif name == "saAmfSGSuRestartProb":
                setFunc = self.setsaAmfSGSuRestartProb
            elif name == "saAmfSGSuRestartMax":
                setFunc = self.setsaAmfSGSuRestartMax
            elif name == "saAmfSGSuHostNodeGroup":
                setFunc = self.setsaAmfSGSuHostNodeGroup
            elif name == "saAmfSGNumPrefStandbySUs":
                setFunc = self.setsaAmfSGNumPrefStandbySUs
            elif name == "saAmfSGNumPrefInserviceSUs":
                setFunc = self.setsaAmfSGNumPrefInserviceSUs
            elif name == "saAmfSGNumPrefAssignedSUs":
                setFunc = self.setsaAmfSGNumPrefAssignedSUs
            elif name == "saAmfSGNumPrefActiveSUs":
                setFunc = self.setsaAmfSGNumPrefActiveSUs
            elif name == "saAmfSGNumCurrNonInstantiatedSpareSUs":
                setFunc = self.setsaAmfSGNumCurrNonInstantiatedSpareSUs
            elif name == "saAmfSGNumCurrInstantiatedSpareSUs":
                setFunc = self.setsaAmfSGNumCurrInstantiatedSpareSUs
            elif name == "saAmfSGNumCurrAssignedSUs":
                setFunc = self.setsaAmfSGNumCurrAssignedSUs
            elif name == "saAmfSGMaxStandbySIsperSU":
                setFunc = self.setsaAmfSGMaxStandbySIsperSU
            elif name == "saAmfSGMaxActiveSIsperSU":
                setFunc = self.setsaAmfSGMaxActiveSIsperSU
            elif name == "saAmfSGCompRestartProb":
                setFunc = self.setsaAmfSGCompRestartProb
            elif name == "saAmfSGCompRestartMax":
                setFunc = self.setsaAmfSGCompRestartMax
            elif name == "saAmfSGAutoRepair":
                setFunc = self.setsaAmfSGAutoRepair
            elif name == "saAmfSGAutoAdjustProb":
                setFunc = self.setsaAmfSGAutoAdjustProb
            elif name == "saAmfSGAutoAdjust":
                setFunc = self.setsaAmfSGAutoAdjust
            elif name == "saAmfSGAdminState":
                setFunc = self.setsaAmfSGAdminState
            elif name == "SaImmAttrImplementerName":
                setFunc = self.setSaImmAttrImplementerName
            elif name == "SaImmAttrClassName":
                setFunc = self.setSaImmAttrClassName
            elif name == "SaImmAttrAdminOwnerName":
                setFunc = self.setSaImmAttrAdminOwnerName
            elif name.startswith("osaf"):
                continue # ignore OpenSAF specific attributes
            else:
                error("unknown attribute called " + name + " defined in object " + self._dn)
            for value in attribute.getElementsByTagName("value"):
                setFunc(value.childNodes[0].nodeValue)

    def writeXML(self, parent, doc):
        obj = doc.createElement("object")
        parent.appendChild(obj)
        obj.setAttribute("class", "SaAmfSG")
        dn = doc.createElement("dn")
        obj.appendChild(dn)
        dn.appendChild(doc.createTextNode(self._dn))
        ImmHelper.writeSingleAttribute("saAmfSGType", self._saAmfSGType, doc, obj)
        ImmHelper.writeSingleAttribute("saAmfSGSuRestartProb", self._saAmfSGSuRestartProb, doc, obj)
        ImmHelper.writeSingleAttribute("saAmfSGSuRestartMax", self._saAmfSGSuRestartMax, doc, obj)
        ImmHelper.writeSingleAttribute("saAmfSGSuHostNodeGroup", self._saAmfSGSuHostNodeGroup, doc, obj)
        ImmHelper.writeSingleAttribute("saAmfSGNumPrefStandbySUs", self._saAmfSGNumPrefStandbySUs, doc, obj)
        ImmHelper.writeSingleAttribute("saAmfSGNumPrefInserviceSUs", self._saAmfSGNumPrefInserviceSUs, doc, obj)
        ImmHelper.writeSingleAttribute("saAmfSGNumPrefAssignedSUs", self._saAmfSGNumPrefAssignedSUs, doc, obj)
        ImmHelper.writeSingleAttribute("saAmfSGNumPrefActiveSUs", self._saAmfSGNumPrefActiveSUs, doc, obj)
        ImmHelper.writeSingleAttribute("saAmfSGNumCurrNonInstantiatedSpareSUs", self._saAmfSGNumCurrNonInstantiatedSpareSUs, doc, obj)
        ImmHelper.writeSingleAttribute("saAmfSGNumCurrInstantiatedSpareSUs", self._saAmfSGNumCurrInstantiatedSpareSUs, doc, obj)
        ImmHelper.writeSingleAttribute("saAmfSGNumCurrAssignedSUs", self._saAmfSGNumCurrAssignedSUs, doc, obj)
        ImmHelper.writeSingleAttribute("saAmfSGMaxStandbySIsperSU", self._saAmfSGMaxStandbySIsperSU, doc, obj)
        ImmHelper.writeSingleAttribute("saAmfSGMaxActiveSIsperSU", self._saAmfSGMaxActiveSIsperSU, doc, obj)
        ImmHelper.writeSingleAttribute("saAmfSGCompRestartProb", self._saAmfSGCompRestartProb, doc, obj)
        ImmHelper.writeSingleAttribute("saAmfSGCompRestartMax", self._saAmfSGCompRestartMax, doc, obj)
        ImmHelper.writeSingleAttribute("saAmfSGAutoRepair", self._saAmfSGAutoRepair, doc, obj)
        ImmHelper.writeSingleAttribute("saAmfSGAutoAdjustProb", self._saAmfSGAutoAdjustProb, doc, obj)
        ImmHelper.writeSingleAttribute("saAmfSGAutoAdjust", self._saAmfSGAutoAdjust, doc, obj)
        ImmHelper.writeSingleAttribute("saAmfSGAdminState", self._saAmfSGAdminState, doc, obj)
        ImmHelper.writeSingleAttribute("SaImmAttrImplementerName", self._SaImmAttrImplementerName, doc, obj)
        ImmHelper.writeSingleAttribute("SaImmAttrClassName", self._SaImmAttrClassName, doc, obj)
        ImmHelper.writeSingleAttribute("SaImmAttrAdminOwnerName", self._SaImmAttrAdminOwnerName, doc, obj)


class SaAmfNodeSwBundle(object):
    def __init__(self):
        self._dn = None
        self._saAmfNodeSwBundlePathPrefix = None
        self._SaImmAttrImplementerName = None
        self._SaImmAttrClassName = None
        self._SaImmAttrAdminOwnerName = None

    @staticmethod
    def createDn(name, parentDn = None):
        if parentDn == None:
            parentDn = ""
        else:
            parentDn = "," + parentDn
        return "safInstalledSwBundle=" + ImmHelper.escapeName(name) + parentDn

    def getDn(self):
        return self._dn

    def getName(self):
        return ImmHelper.getName(self._dn)

    def getRdn(self):
        return ImmHelper.getRdn(self._dn)

    def getParentDn(self):
        return ImmHelper.getParentDn(self._dn)

    def createObjectInCampaign(self, campaign):
        parentDn = self.getParentDn()
        if parentDn == "":
            parentDn = "="
        campaign.beginCreate("SaAmfNodeSwBundle", parentDn)
        campaign.addAttribute("safInstalledSwBundle", "SA_IMM_ATTR_SANAMET", self.getRdn())
        if self._saAmfNodeSwBundlePathPrefix != None:
            campaign.addAttribute("saAmfNodeSwBundlePathPrefix", "SA_IMM_ATTR_SASTRINGT", self._saAmfNodeSwBundlePathPrefix)
        if self._SaImmAttrImplementerName != None:
            campaign.addAttribute("SaImmAttrImplementerName", "SA_IMM_ATTR_SASTRINGT", self._SaImmAttrImplementerName)
        if self._SaImmAttrClassName != None:
            campaign.addAttribute("SaImmAttrClassName", "SA_IMM_ATTR_SASTRINGT", self._SaImmAttrClassName)
        if self._SaImmAttrAdminOwnerName != None:
            campaign.addAttribute("SaImmAttrAdminOwnerName", "SA_IMM_ATTR_SASTRINGT", self._SaImmAttrAdminOwnerName)
        campaign.endCreate()

    def getsaAmfNodeSwBundlePathPrefix(self):
        ImmHelper.validateSingle(self._saAmfNodeSwBundlePathPrefix, self._dn, "saAmfNodeSwBundlePathPrefix")
        return self._saAmfNodeSwBundlePathPrefix

    def getSaImmAttrImplementerName(self):
        ImmHelper.validateSingle(self._SaImmAttrImplementerName, self._dn, "SaImmAttrImplementerName")
        return self._SaImmAttrImplementerName

    def getSaImmAttrClassName(self):
        ImmHelper.validateSingle(self._SaImmAttrClassName, self._dn, "SaImmAttrClassName")
        return self._SaImmAttrClassName

    def getSaImmAttrAdminOwnerName(self):
        ImmHelper.validateSingle(self._SaImmAttrAdminOwnerName, self._dn, "SaImmAttrAdminOwnerName")
        return self._SaImmAttrAdminOwnerName

    def getsaAmfNodeSwBundlePathPrefix_unsafe(self):
        return self._saAmfNodeSwBundlePathPrefix

    def getSaImmAttrImplementerName_unsafe(self):
        return self._SaImmAttrImplementerName

    def getSaImmAttrClassName_unsafe(self):
        return self._SaImmAttrClassName

    def getSaImmAttrAdminOwnerName_unsafe(self):
        return self._SaImmAttrAdminOwnerName

    def setsaAmfNodeSwBundlePathPrefix(self, value):
        ImmHelper.validateString(value, self._dn, "saAmfNodeSwBundlePathPrefix")
        self._saAmfNodeSwBundlePathPrefix = value

    def setSaImmAttrImplementerName(self, value):
        ImmHelper.validateString(value, self._dn, "SaImmAttrImplementerName")
        self._SaImmAttrImplementerName = value

    def setSaImmAttrClassName(self, value):
        ImmHelper.validateString(value, self._dn, "SaImmAttrClassName")
        self._SaImmAttrClassName = value

    def setSaImmAttrAdminOwnerName(self, value):
        ImmHelper.validateString(value, self._dn, "SaImmAttrAdminOwnerName")
        self._SaImmAttrAdminOwnerName = value

    def updateParams(self, params, canttouchthis):
        for (param, value) in params.items():
            if param in canttouchthis:
                error("Setting attribute " + param + " in object " + self.getDn() + " is not supported")
            else:
                error("Object " + self.getDn() + " has no attribute named " + param)

    def diff(self, other, fullCheck = False):
        changedAttrs = []
        if (fullCheck or self._saAmfNodeSwBundlePathPrefix != None) and other._saAmfNodeSwBundlePathPrefix != self._saAmfNodeSwBundlePathPrefix:
            changedAttrs.append("saAmfNodeSwBundlePathPrefix")
        if (fullCheck or self._SaImmAttrImplementerName != None) and other._SaImmAttrImplementerName != self._SaImmAttrImplementerName:
            changedAttrs.append("SaImmAttrImplementerName")
        if (fullCheck or self._SaImmAttrClassName != None) and other._SaImmAttrClassName != self._SaImmAttrClassName:
            changedAttrs.append("SaImmAttrClassName")
        if (fullCheck or self._SaImmAttrAdminOwnerName != None) and other._SaImmAttrAdminOwnerName != self._SaImmAttrAdminOwnerName:
            changedAttrs.append("SaImmAttrAdminOwnerName")
        return changedAttrs

    def parseXML(self, node):
        dns = node.getElementsByTagName("dn")
        if len(dns) != 1:
            error("object has " + str(len(dns)) + " dn(s) but it should have one")
        self._dn = dns[0].childNodes[0].nodeValue
        for attribute in node.getElementsByTagName("attr"):
            names = attribute.getElementsByTagName("name")
            if len(names) != 1:
                error("object attribute has " + str(len(names)) + " name(s) but it should have one")
            name = names[0].childNodes[0].nodeValue
            setFunc = None
            if name == "SaImmAttrImplementerName":
                continue
            elif name == "SaImmAttrAdminOwnerName":
                continue
            elif name == "SaImmAttrClassName":
                continue
            elif name == "saAmfNodeSwBundlePathPrefix":
                setFunc = self.setsaAmfNodeSwBundlePathPrefix
            elif name == "SaImmAttrImplementerName":
                setFunc = self.setSaImmAttrImplementerName
            elif name == "SaImmAttrClassName":
                setFunc = self.setSaImmAttrClassName
            elif name == "SaImmAttrAdminOwnerName":
                setFunc = self.setSaImmAttrAdminOwnerName
            elif name.startswith("osaf"):
                continue # ignore OpenSAF specific attributes
            else:
                error("unknown attribute called " + name + " defined in object " + self._dn)
            for value in attribute.getElementsByTagName("value"):
                setFunc(value.childNodes[0].nodeValue)

    def writeXML(self, parent, doc):
        obj = doc.createElement("object")
        parent.appendChild(obj)
        obj.setAttribute("class", "SaAmfNodeSwBundle")
        dn = doc.createElement("dn")
        obj.appendChild(dn)
        dn.appendChild(doc.createTextNode(self._dn))
        ImmHelper.writeSingleAttribute("saAmfNodeSwBundlePathPrefix", self._saAmfNodeSwBundlePathPrefix, doc, obj)
        ImmHelper.writeSingleAttribute("SaImmAttrImplementerName", self._SaImmAttrImplementerName, doc, obj)
        ImmHelper.writeSingleAttribute("SaImmAttrClassName", self._SaImmAttrClassName, doc, obj)
        ImmHelper.writeSingleAttribute("SaImmAttrAdminOwnerName", self._SaImmAttrAdminOwnerName, doc, obj)


class SaAmfNodeGroup(object):
    def __init__(self):
        self._dn = None
        self._saAmfNGNodeList = []
        self._saAmfNGAdminState = None
        self._SaImmAttrImplementerName = None
        self._SaImmAttrClassName = None
        self._SaImmAttrAdminOwnerName = None

    @staticmethod
    def createDn(name, parentDn = None):
        if parentDn == None:
            parentDn = ""
        else:
            parentDn = "," + parentDn
        return "safAmfNodeGroup=" + ImmHelper.escapeName(name) + parentDn

    def getDn(self):
        return self._dn

    def getName(self):
        return ImmHelper.getName(self._dn)

    def getRdn(self):
        return ImmHelper.getRdn(self._dn)

    def getParentDn(self):
        return ImmHelper.getParentDn(self._dn)

    def createObjectInCampaign(self, campaign):
        parentDn = self.getParentDn()
        if parentDn == "":
            parentDn = "="
        campaign.beginCreate("SaAmfNodeGroup", parentDn)
        campaign.addAttribute("safAmfNodeGroup", "SA_IMM_ATTR_SASTRINGT", self.getRdn())
        if len(self._saAmfNGNodeList) > 0:
            campaign.addAttribute("saAmfNGNodeList", "SA_IMM_ATTR_SANAMET", self._saAmfNGNodeList)
        if self._SaImmAttrImplementerName != None:
            campaign.addAttribute("SaImmAttrImplementerName", "SA_IMM_ATTR_SASTRINGT", self._SaImmAttrImplementerName)
        if self._SaImmAttrClassName != None:
            campaign.addAttribute("SaImmAttrClassName", "SA_IMM_ATTR_SASTRINGT", self._SaImmAttrClassName)
        if self._SaImmAttrAdminOwnerName != None:
            campaign.addAttribute("SaImmAttrAdminOwnerName", "SA_IMM_ATTR_SASTRINGT", self._SaImmAttrAdminOwnerName)
        campaign.endCreate()

    def getsaAmfNGNodeList(self):
        return self._saAmfNGNodeList

    def getsaAmfNGAdminState(self):
        ImmHelper.validateSingle(self._saAmfNGAdminState, self._dn, "saAmfNGAdminState")
        return self._saAmfNGAdminState

    def getSaImmAttrImplementerName(self):
        ImmHelper.validateSingle(self._SaImmAttrImplementerName, self._dn, "SaImmAttrImplementerName")
        return self._SaImmAttrImplementerName

    def getSaImmAttrClassName(self):
        ImmHelper.validateSingle(self._SaImmAttrClassName, self._dn, "SaImmAttrClassName")
        return self._SaImmAttrClassName

    def getSaImmAttrAdminOwnerName(self):
        ImmHelper.validateSingle(self._SaImmAttrAdminOwnerName, self._dn, "SaImmAttrAdminOwnerName")
        return self._SaImmAttrAdminOwnerName

    def getsaAmfNGNodeList_single(self):
        ImmHelper.validateSingleInList(self._saAmfNGNodeList, self._dn, "saAmfNGNodeList")
        return self._saAmfNGNodeList[0]

    def getsaAmfNGAdminState_unsafe(self):
        return self._saAmfNGAdminState

    def getSaImmAttrImplementerName_unsafe(self):
        return self._SaImmAttrImplementerName

    def getSaImmAttrClassName_unsafe(self):
        return self._SaImmAttrClassName

    def getSaImmAttrAdminOwnerName_unsafe(self):
        return self._SaImmAttrAdminOwnerName

    def addTosaAmfNGNodeList(self, value):
        ImmHelper.validateName(value, self._dn, "saAmfNGNodeList")
        self._saAmfNGNodeList.append(value)

    def setsaAmfNGAdminState(self, value):
        ImmHelper.validateUint32(value, self._dn, "saAmfNGAdminState")
        value = str(value)
        self._saAmfNGAdminState = value

    def setSaImmAttrImplementerName(self, value):
        ImmHelper.validateString(value, self._dn, "SaImmAttrImplementerName")
        self._SaImmAttrImplementerName = value

    def setSaImmAttrClassName(self, value):
        ImmHelper.validateString(value, self._dn, "SaImmAttrClassName")
        self._SaImmAttrClassName = value

    def setSaImmAttrAdminOwnerName(self, value):
        ImmHelper.validateString(value, self._dn, "SaImmAttrAdminOwnerName")
        self._SaImmAttrAdminOwnerName = value

    def updateParams(self, params, canttouchthis):
        for (param, value) in params.items():
            if param in canttouchthis:
                error("Setting attribute " + param + " in object " + self.getDn() + " is not supported")
            if param == "saAmfNGNodeList":
                if not isinstance(value, list):
                    value = [value]
                self._saAmfNGNodeList = []
                for v in value:
                    self.addTosaAmfNGNodeList(v)
            else:
                error("Object " + self.getDn() + " has no attribute named " + param)

    def diff(self, other, fullCheck = False):
        changedAttrs = []
        if fullCheck or (len(self._saAmfNGNodeList) != 0):
            if len(self._saAmfNGNodeList) != len(other._saAmfNGNodeList):
                changedAttrs.append("saAmfNGNodeList")
            else:
                difflist = list(set(self._saAmfNGNodeList) ^ set(other._saAmfNGNodeList))
                if len(difflist) > 0:
                    changedAttrs.append("saAmfNGNodeList")
        if (fullCheck or self._SaImmAttrImplementerName != None) and other._SaImmAttrImplementerName != self._SaImmAttrImplementerName:
            changedAttrs.append("SaImmAttrImplementerName")
        if (fullCheck or self._SaImmAttrClassName != None) and other._SaImmAttrClassName != self._SaImmAttrClassName:
            changedAttrs.append("SaImmAttrClassName")
        if (fullCheck or self._SaImmAttrAdminOwnerName != None) and other._SaImmAttrAdminOwnerName != self._SaImmAttrAdminOwnerName:
            changedAttrs.append("SaImmAttrAdminOwnerName")
        return changedAttrs

    def parseXML(self, node):
        dns = node.getElementsByTagName("dn")
        if len(dns) != 1:
            error("object has " + str(len(dns)) + " dn(s) but it should have one")
        self._dn = dns[0].childNodes[0].nodeValue
        for attribute in node.getElementsByTagName("attr"):
            names = attribute.getElementsByTagName("name")
            if len(names) != 1:
                error("object attribute has " + str(len(names)) + " name(s) but it should have one")
            name = names[0].childNodes[0].nodeValue
            setFunc = None
            if name == "SaImmAttrImplementerName":
                continue
            elif name == "SaImmAttrAdminOwnerName":
                continue
            elif name == "SaImmAttrClassName":
                continue
            elif name == "saAmfNGNodeList":
                setFunc = self.addTosaAmfNGNodeList
            elif name == "saAmfNGAdminState":
                setFunc = self.setsaAmfNGAdminState
            elif name == "SaImmAttrImplementerName":
                setFunc = self.setSaImmAttrImplementerName
            elif name == "SaImmAttrClassName":
                setFunc = self.setSaImmAttrClassName
            elif name == "SaImmAttrAdminOwnerName":
                setFunc = self.setSaImmAttrAdminOwnerName
            elif name.startswith("osaf"):
                continue # ignore OpenSAF specific attributes
            else:
                error("unknown attribute called " + name + " defined in object " + self._dn)
            for value in attribute.getElementsByTagName("value"):
                setFunc(value.childNodes[0].nodeValue)

    def writeXML(self, parent, doc):
        obj = doc.createElement("object")
        parent.appendChild(obj)
        obj.setAttribute("class", "SaAmfNodeGroup")
        dn = doc.createElement("dn")
        obj.appendChild(dn)
        dn.appendChild(doc.createTextNode(self._dn))
        ImmHelper.writeMultiAttributes("saAmfNGNodeList", self._saAmfNGNodeList, doc, obj)
        ImmHelper.writeSingleAttribute("saAmfNGAdminState", self._saAmfNGAdminState, doc, obj)
        ImmHelper.writeSingleAttribute("SaImmAttrImplementerName", self._SaImmAttrImplementerName, doc, obj)
        ImmHelper.writeSingleAttribute("SaImmAttrClassName", self._SaImmAttrClassName, doc, obj)
        ImmHelper.writeSingleAttribute("SaImmAttrAdminOwnerName", self._SaImmAttrAdminOwnerName, doc, obj)


class SaAmfNode(object):
    def __init__(self):
        self._dn = None
        self._saAmfNodeSuFailoverMax = None
        self._saAmfNodeSuFailOverProb = None
        self._saAmfNodeOperState = None
        self._saAmfNodeFailfastOnTerminationFailure = None
        self._saAmfNodeFailfastOnInstantiationFailure = None
        self._saAmfNodeClmNode = None
        self._saAmfNodeCapacity = []
        self._saAmfNodeAutoRepair = None
        self._saAmfNodeAdminState = None
        self._SaImmAttrImplementerName = None
        self._SaImmAttrClassName = None
        self._SaImmAttrAdminOwnerName = None

    @staticmethod
    def createDn(name, parentDn = None):
        if parentDn == None:
            parentDn = ""
        else:
            parentDn = "," + parentDn
        return "safAmfNode=" + ImmHelper.escapeName(name) + parentDn

    def getDn(self):
        return self._dn

    def getName(self):
        return ImmHelper.getName(self._dn)

    def getRdn(self):
        return ImmHelper.getRdn(self._dn)

    def getParentDn(self):
        return ImmHelper.getParentDn(self._dn)

    def createObjectInCampaign(self, campaign):
        parentDn = self.getParentDn()
        if parentDn == "":
            parentDn = "="
        campaign.beginCreate("SaAmfNode", parentDn)
        campaign.addAttribute("safAmfNode", "SA_IMM_ATTR_SASTRINGT", self.getRdn())
        if self._saAmfNodeSuFailoverMax != None:
            campaign.addAttribute("saAmfNodeSuFailoverMax", "SA_IMM_ATTR_SAUINT32T", self._saAmfNodeSuFailoverMax)
        if self._saAmfNodeSuFailOverProb != None:
            campaign.addAttribute("saAmfNodeSuFailOverProb", "SA_IMM_ATTR_SATIMET", self._saAmfNodeSuFailOverProb)
        if self._saAmfNodeFailfastOnTerminationFailure != None:
            campaign.addAttribute("saAmfNodeFailfastOnTerminationFailure", "SA_IMM_ATTR_SAUINT32T", self._saAmfNodeFailfastOnTerminationFailure)
        if self._saAmfNodeFailfastOnInstantiationFailure != None:
            campaign.addAttribute("saAmfNodeFailfastOnInstantiationFailure", "SA_IMM_ATTR_SAUINT32T", self._saAmfNodeFailfastOnInstantiationFailure)
        if self._saAmfNodeClmNode != None:
            campaign.addAttribute("saAmfNodeClmNode", "SA_IMM_ATTR_SANAMET", self._saAmfNodeClmNode)
        if len(self._saAmfNodeCapacity) > 0:
            campaign.addAttribute("saAmfNodeCapacity", "SA_IMM_ATTR_SASTRINGT", self._saAmfNodeCapacity)
        if self._saAmfNodeAutoRepair != None:
            campaign.addAttribute("saAmfNodeAutoRepair", "SA_IMM_ATTR_SAUINT32T", self._saAmfNodeAutoRepair)
        if self._SaImmAttrImplementerName != None:
            campaign.addAttribute("SaImmAttrImplementerName", "SA_IMM_ATTR_SASTRINGT", self._SaImmAttrImplementerName)
        if self._SaImmAttrClassName != None:
            campaign.addAttribute("SaImmAttrClassName", "SA_IMM_ATTR_SASTRINGT", self._SaImmAttrClassName)
        if self._SaImmAttrAdminOwnerName != None:
            campaign.addAttribute("SaImmAttrAdminOwnerName", "SA_IMM_ATTR_SASTRINGT", self._SaImmAttrAdminOwnerName)
        campaign.endCreate()

    def getsaAmfNodeSuFailoverMax(self):
        ImmHelper.validateSingle(self._saAmfNodeSuFailoverMax, self._dn, "saAmfNodeSuFailoverMax")
        return self._saAmfNodeSuFailoverMax

    def getsaAmfNodeSuFailOverProb(self):
        ImmHelper.validateSingle(self._saAmfNodeSuFailOverProb, self._dn, "saAmfNodeSuFailOverProb")
        return self._saAmfNodeSuFailOverProb

    def getsaAmfNodeOperState(self):
        ImmHelper.validateSingle(self._saAmfNodeOperState, self._dn, "saAmfNodeOperState")
        return self._saAmfNodeOperState

    def getsaAmfNodeFailfastOnTerminationFailure(self):
        ImmHelper.validateSingle(self._saAmfNodeFailfastOnTerminationFailure, self._dn, "saAmfNodeFailfastOnTerminationFailure")
        return self._saAmfNodeFailfastOnTerminationFailure

    def getsaAmfNodeFailfastOnInstantiationFailure(self):
        ImmHelper.validateSingle(self._saAmfNodeFailfastOnInstantiationFailure, self._dn, "saAmfNodeFailfastOnInstantiationFailure")
        return self._saAmfNodeFailfastOnInstantiationFailure

    def getsaAmfNodeClmNode(self):
        ImmHelper.validateSingle(self._saAmfNodeClmNode, self._dn, "saAmfNodeClmNode")
        return self._saAmfNodeClmNode

    def getsaAmfNodeCapacity(self):
        return self._saAmfNodeCapacity

    def getsaAmfNodeAutoRepair(self):
        ImmHelper.validateSingle(self._saAmfNodeAutoRepair, self._dn, "saAmfNodeAutoRepair")
        return self._saAmfNodeAutoRepair

    def getsaAmfNodeAdminState(self):
        ImmHelper.validateSingle(self._saAmfNodeAdminState, self._dn, "saAmfNodeAdminState")
        return self._saAmfNodeAdminState

    def getSaImmAttrImplementerName(self):
        ImmHelper.validateSingle(self._SaImmAttrImplementerName, self._dn, "SaImmAttrImplementerName")
        return self._SaImmAttrImplementerName

    def getSaImmAttrClassName(self):
        ImmHelper.validateSingle(self._SaImmAttrClassName, self._dn, "SaImmAttrClassName")
        return self._SaImmAttrClassName

    def getSaImmAttrAdminOwnerName(self):
        ImmHelper.validateSingle(self._SaImmAttrAdminOwnerName, self._dn, "SaImmAttrAdminOwnerName")
        return self._SaImmAttrAdminOwnerName

    def getsaAmfNodeSuFailoverMax_unsafe(self):
        return self._saAmfNodeSuFailoverMax

    def getsaAmfNodeSuFailOverProb_unsafe(self):
        return self._saAmfNodeSuFailOverProb

    def getsaAmfNodeOperState_unsafe(self):
        return self._saAmfNodeOperState

    def getsaAmfNodeFailfastOnTerminationFailure_unsafe(self):
        return self._saAmfNodeFailfastOnTerminationFailure

    def getsaAmfNodeFailfastOnInstantiationFailure_unsafe(self):
        return self._saAmfNodeFailfastOnInstantiationFailure

    def getsaAmfNodeClmNode_unsafe(self):
        return self._saAmfNodeClmNode

    def getsaAmfNodeCapacity_single(self):
        ImmHelper.validateSingleInList(self._saAmfNodeCapacity, self._dn, "saAmfNodeCapacity")
        return self._saAmfNodeCapacity[0]

    def getsaAmfNodeAutoRepair_unsafe(self):
        return self._saAmfNodeAutoRepair

    def getsaAmfNodeAdminState_unsafe(self):
        return self._saAmfNodeAdminState

    def getSaImmAttrImplementerName_unsafe(self):
        return self._SaImmAttrImplementerName

    def getSaImmAttrClassName_unsafe(self):
        return self._SaImmAttrClassName

    def getSaImmAttrAdminOwnerName_unsafe(self):
        return self._SaImmAttrAdminOwnerName

    def setsaAmfNodeSuFailoverMax(self, value):
        ImmHelper.validateUint32(value, self._dn, "saAmfNodeSuFailoverMax")
        value = str(value)
        self._saAmfNodeSuFailoverMax = value

    def setsaAmfNodeSuFailOverProb(self, value):
        ImmHelper.validateTime(value, self._dn, "saAmfNodeSuFailOverProb")
        value = str(value)
        self._saAmfNodeSuFailOverProb = value

    def setsaAmfNodeOperState(self, value):
        ImmHelper.validateUint32(value, self._dn, "saAmfNodeOperState")
        value = str(value)
        self._saAmfNodeOperState = value

    def setsaAmfNodeFailfastOnTerminationFailure(self, value):
        ImmHelper.validateUint32(value, self._dn, "saAmfNodeFailfastOnTerminationFailure")
        value = str(value)
        self._saAmfNodeFailfastOnTerminationFailure = value

    def setsaAmfNodeFailfastOnInstantiationFailure(self, value):
        ImmHelper.validateUint32(value, self._dn, "saAmfNodeFailfastOnInstantiationFailure")
        value = str(value)
        self._saAmfNodeFailfastOnInstantiationFailure = value

    def setsaAmfNodeClmNode(self, value):
        ImmHelper.validateName(value, self._dn, "saAmfNodeClmNode")
        self._saAmfNodeClmNode = value

    def addTosaAmfNodeCapacity(self, value):
        ImmHelper.validateString(value, self._dn, "saAmfNodeCapacity")
        self._saAmfNodeCapacity.append(value)

    def setsaAmfNodeAutoRepair(self, value):
        ImmHelper.validateUint32(value, self._dn, "saAmfNodeAutoRepair")
        value = str(value)
        self._saAmfNodeAutoRepair = value

    def setsaAmfNodeAdminState(self, value):
        ImmHelper.validateUint32(value, self._dn, "saAmfNodeAdminState")
        value = str(value)
        self._saAmfNodeAdminState = value

    def setSaImmAttrImplementerName(self, value):
        ImmHelper.validateString(value, self._dn, "SaImmAttrImplementerName")
        self._SaImmAttrImplementerName = value

    def setSaImmAttrClassName(self, value):
        ImmHelper.validateString(value, self._dn, "SaImmAttrClassName")
        self._SaImmAttrClassName = value

    def setSaImmAttrAdminOwnerName(self, value):
        ImmHelper.validateString(value, self._dn, "SaImmAttrAdminOwnerName")
        self._SaImmAttrAdminOwnerName = value

    def updateParams(self, params, canttouchthis):
        for (param, value) in params.items():
            if param in canttouchthis:
                error("Setting attribute " + param + " in object " + self.getDn() + " is not supported")
            if param == "saAmfNodeSuFailoverMax":
                self.setsaAmfNodeSuFailoverMax(value)
            elif param == "saAmfNodeSuFailOverProb":
                self.setsaAmfNodeSuFailOverProb(value)
            elif param == "saAmfNodeFailfastOnTerminationFailure":
                self.setsaAmfNodeFailfastOnTerminationFailure(value)
            elif param == "saAmfNodeFailfastOnInstantiationFailure":
                self.setsaAmfNodeFailfastOnInstantiationFailure(value)
            elif param == "saAmfNodeClmNode":
                self.setsaAmfNodeClmNode(value)
            elif param == "saAmfNodeCapacity":
                if not isinstance(value, list):
                    value = [value]
                self._saAmfNodeCapacity = []
                for v in value:
                    self.addTosaAmfNodeCapacity(v)
            elif param == "saAmfNodeAutoRepair":
                self.setsaAmfNodeAutoRepair(value)
            else:
                error("Object " + self.getDn() + " has no attribute named " + param)

    def diff(self, other, fullCheck = False):
        changedAttrs = []
        if (fullCheck or self._saAmfNodeSuFailoverMax != None) and other._saAmfNodeSuFailoverMax != self._saAmfNodeSuFailoverMax:
            changedAttrs.append("saAmfNodeSuFailoverMax")
        if (fullCheck or self._saAmfNodeSuFailOverProb != None) and other._saAmfNodeSuFailOverProb != self._saAmfNodeSuFailOverProb:
            changedAttrs.append("saAmfNodeSuFailOverProb")
        if (fullCheck or self._saAmfNodeFailfastOnTerminationFailure != None) and other._saAmfNodeFailfastOnTerminationFailure != self._saAmfNodeFailfastOnTerminationFailure:
            changedAttrs.append("saAmfNodeFailfastOnTerminationFailure")
        if (fullCheck or self._saAmfNodeFailfastOnInstantiationFailure != None) and other._saAmfNodeFailfastOnInstantiationFailure != self._saAmfNodeFailfastOnInstantiationFailure:
            changedAttrs.append("saAmfNodeFailfastOnInstantiationFailure")
        if (fullCheck or self._saAmfNodeClmNode != None) and other._saAmfNodeClmNode != self._saAmfNodeClmNode:
            changedAttrs.append("saAmfNodeClmNode")
        if fullCheck or (len(self._saAmfNodeCapacity) != 0):
            if len(self._saAmfNodeCapacity) != len(other._saAmfNodeCapacity):
                changedAttrs.append("saAmfNodeCapacity")
            else:
                difflist = list(set(self._saAmfNodeCapacity) ^ set(other._saAmfNodeCapacity))
                if len(difflist) > 0:
                    changedAttrs.append("saAmfNodeCapacity")
        if (fullCheck or self._saAmfNodeAutoRepair != None) and other._saAmfNodeAutoRepair != self._saAmfNodeAutoRepair:
            changedAttrs.append("saAmfNodeAutoRepair")
        if (fullCheck or self._SaImmAttrImplementerName != None) and other._SaImmAttrImplementerName != self._SaImmAttrImplementerName:
            changedAttrs.append("SaImmAttrImplementerName")
        if (fullCheck or self._SaImmAttrClassName != None) and other._SaImmAttrClassName != self._SaImmAttrClassName:
            changedAttrs.append("SaImmAttrClassName")
        if (fullCheck or self._SaImmAttrAdminOwnerName != None) and other._SaImmAttrAdminOwnerName != self._SaImmAttrAdminOwnerName:
            changedAttrs.append("SaImmAttrAdminOwnerName")
        return changedAttrs

    def parseXML(self, node):
        dns = node.getElementsByTagName("dn")
        if len(dns) != 1:
            error("object has " + str(len(dns)) + " dn(s) but it should have one")
        self._dn = dns[0].childNodes[0].nodeValue
        for attribute in node.getElementsByTagName("attr"):
            names = attribute.getElementsByTagName("name")
            if len(names) != 1:
                error("object attribute has " + str(len(names)) + " name(s) but it should have one")
            name = names[0].childNodes[0].nodeValue
            setFunc = None
            if name == "SaImmAttrImplementerName":
                continue
            elif name == "SaImmAttrAdminOwnerName":
                continue
            elif name == "SaImmAttrClassName":
                continue
            elif name == "saAmfNodeSuFailoverMax":
                setFunc = self.setsaAmfNodeSuFailoverMax
            elif name == "saAmfNodeSuFailOverProb":
                setFunc = self.setsaAmfNodeSuFailOverProb
            elif name == "saAmfNodeOperState":
                setFunc = self.setsaAmfNodeOperState
            elif name == "saAmfNodeFailfastOnTerminationFailure":
                setFunc = self.setsaAmfNodeFailfastOnTerminationFailure
            elif name == "saAmfNodeFailfastOnInstantiationFailure":
                setFunc = self.setsaAmfNodeFailfastOnInstantiationFailure
            elif name == "saAmfNodeClmNode":
                setFunc = self.setsaAmfNodeClmNode
            elif name == "saAmfNodeCapacity":
                setFunc = self.addTosaAmfNodeCapacity
            elif name == "saAmfNodeAutoRepair":
                setFunc = self.setsaAmfNodeAutoRepair
            elif name == "saAmfNodeAdminState":
                setFunc = self.setsaAmfNodeAdminState
            elif name == "SaImmAttrImplementerName":
                setFunc = self.setSaImmAttrImplementerName
            elif name == "SaImmAttrClassName":
                setFunc = self.setSaImmAttrClassName
            elif name == "SaImmAttrAdminOwnerName":
                setFunc = self.setSaImmAttrAdminOwnerName
            elif name.startswith("osaf"):
                continue # ignore OpenSAF specific attributes
            else:
                error("unknown attribute called " + name + " defined in object " + self._dn)
            for value in attribute.getElementsByTagName("value"):
                setFunc(value.childNodes[0].nodeValue)

    def writeXML(self, parent, doc):
        obj = doc.createElement("object")
        parent.appendChild(obj)
        obj.setAttribute("class", "SaAmfNode")
        dn = doc.createElement("dn")
        obj.appendChild(dn)
        dn.appendChild(doc.createTextNode(self._dn))
        ImmHelper.writeSingleAttribute("saAmfNodeSuFailoverMax", self._saAmfNodeSuFailoverMax, doc, obj)
        ImmHelper.writeSingleAttribute("saAmfNodeSuFailOverProb", self._saAmfNodeSuFailOverProb, doc, obj)
        ImmHelper.writeSingleAttribute("saAmfNodeOperState", self._saAmfNodeOperState, doc, obj)
        ImmHelper.writeSingleAttribute("saAmfNodeFailfastOnTerminationFailure", self._saAmfNodeFailfastOnTerminationFailure, doc, obj)
        ImmHelper.writeSingleAttribute("saAmfNodeFailfastOnInstantiationFailure", self._saAmfNodeFailfastOnInstantiationFailure, doc, obj)
        ImmHelper.writeSingleAttribute("saAmfNodeClmNode", self._saAmfNodeClmNode, doc, obj)
        ImmHelper.writeMultiAttributes("saAmfNodeCapacity", self._saAmfNodeCapacity, doc, obj)
        ImmHelper.writeSingleAttribute("saAmfNodeAutoRepair", self._saAmfNodeAutoRepair, doc, obj)
        ImmHelper.writeSingleAttribute("saAmfNodeAdminState", self._saAmfNodeAdminState, doc, obj)
        ImmHelper.writeSingleAttribute("SaImmAttrImplementerName", self._SaImmAttrImplementerName, doc, obj)
        ImmHelper.writeSingleAttribute("SaImmAttrClassName", self._SaImmAttrClassName, doc, obj)
        ImmHelper.writeSingleAttribute("SaImmAttrAdminOwnerName", self._SaImmAttrAdminOwnerName, doc, obj)


class SaAmfHealthcheckType(object):
    def __init__(self):
        self._dn = None
        self._saAmfHctDefPeriod = None
        self._saAmfHctDefMaxDuration = None
        self._SaImmAttrImplementerName = None
        self._SaImmAttrClassName = None
        self._SaImmAttrAdminOwnerName = None

    @staticmethod
    def createDn(name, parentDn = None):
        if parentDn == None:
            parentDn = ""
        else:
            parentDn = "," + parentDn
        return "safHealthcheckKey=" + ImmHelper.escapeName(name) + parentDn

    def getDn(self):
        return self._dn

    def getName(self):
        return ImmHelper.getName(self._dn)

    def getRdn(self):
        return ImmHelper.getRdn(self._dn)

    def getParentDn(self):
        return ImmHelper.getParentDn(self._dn)

    def createObjectInCampaign(self, campaign):
        parentDn = self.getParentDn()
        if parentDn == "":
            parentDn = "="
        campaign.beginCreate("SaAmfHealthcheckType", parentDn)
        campaign.addAttribute("safHealthcheckKey", "SA_IMM_ATTR_SASTRINGT", self.getRdn())
        if self._saAmfHctDefPeriod != None:
            campaign.addAttribute("saAmfHctDefPeriod", "SA_IMM_ATTR_SATIMET", self._saAmfHctDefPeriod)
        if self._saAmfHctDefMaxDuration != None:
            campaign.addAttribute("saAmfHctDefMaxDuration", "SA_IMM_ATTR_SATIMET", self._saAmfHctDefMaxDuration)
        if self._SaImmAttrImplementerName != None:
            campaign.addAttribute("SaImmAttrImplementerName", "SA_IMM_ATTR_SASTRINGT", self._SaImmAttrImplementerName)
        if self._SaImmAttrClassName != None:
            campaign.addAttribute("SaImmAttrClassName", "SA_IMM_ATTR_SASTRINGT", self._SaImmAttrClassName)
        if self._SaImmAttrAdminOwnerName != None:
            campaign.addAttribute("SaImmAttrAdminOwnerName", "SA_IMM_ATTR_SASTRINGT", self._SaImmAttrAdminOwnerName)
        campaign.endCreate()

    def getsaAmfHctDefPeriod(self):
        ImmHelper.validateSingle(self._saAmfHctDefPeriod, self._dn, "saAmfHctDefPeriod")
        return self._saAmfHctDefPeriod

    def getsaAmfHctDefMaxDuration(self):
        ImmHelper.validateSingle(self._saAmfHctDefMaxDuration, self._dn, "saAmfHctDefMaxDuration")
        return self._saAmfHctDefMaxDuration

    def getSaImmAttrImplementerName(self):
        ImmHelper.validateSingle(self._SaImmAttrImplementerName, self._dn, "SaImmAttrImplementerName")
        return self._SaImmAttrImplementerName

    def getSaImmAttrClassName(self):
        ImmHelper.validateSingle(self._SaImmAttrClassName, self._dn, "SaImmAttrClassName")
        return self._SaImmAttrClassName

    def getSaImmAttrAdminOwnerName(self):
        ImmHelper.validateSingle(self._SaImmAttrAdminOwnerName, self._dn, "SaImmAttrAdminOwnerName")
        return self._SaImmAttrAdminOwnerName

    def getsaAmfHctDefPeriod_unsafe(self):
        return self._saAmfHctDefPeriod

    def getsaAmfHctDefMaxDuration_unsafe(self):
        return self._saAmfHctDefMaxDuration

    def getSaImmAttrImplementerName_unsafe(self):
        return self._SaImmAttrImplementerName

    def getSaImmAttrClassName_unsafe(self):
        return self._SaImmAttrClassName

    def getSaImmAttrAdminOwnerName_unsafe(self):
        return self._SaImmAttrAdminOwnerName

    def setsaAmfHctDefPeriod(self, value):
        ImmHelper.validateTime(value, self._dn, "saAmfHctDefPeriod")
        value = str(value)
        self._saAmfHctDefPeriod = value

    def setsaAmfHctDefMaxDuration(self, value):
        ImmHelper.validateTime(value, self._dn, "saAmfHctDefMaxDuration")
        value = str(value)
        self._saAmfHctDefMaxDuration = value

    def setSaImmAttrImplementerName(self, value):
        ImmHelper.validateString(value, self._dn, "SaImmAttrImplementerName")
        self._SaImmAttrImplementerName = value

    def setSaImmAttrClassName(self, value):
        ImmHelper.validateString(value, self._dn, "SaImmAttrClassName")
        self._SaImmAttrClassName = value

    def setSaImmAttrAdminOwnerName(self, value):
        ImmHelper.validateString(value, self._dn, "SaImmAttrAdminOwnerName")
        self._SaImmAttrAdminOwnerName = value

    def updateParams(self, params, canttouchthis):
        for (param, value) in params.items():
            if param in canttouchthis:
                error("Setting attribute " + param + " in object " + self.getDn() + " is not supported")
            if param == "saAmfHctDefPeriod":
                self.setsaAmfHctDefPeriod(value)
            elif param == "saAmfHctDefMaxDuration":
                self.setsaAmfHctDefMaxDuration(value)
            else:
                error("Object " + self.getDn() + " has no attribute named " + param)

    def diff(self, other, fullCheck = False):
        changedAttrs = []
        if (fullCheck or self._saAmfHctDefPeriod != None) and other._saAmfHctDefPeriod != self._saAmfHctDefPeriod:
            changedAttrs.append("saAmfHctDefPeriod")
        if (fullCheck or self._saAmfHctDefMaxDuration != None) and other._saAmfHctDefMaxDuration != self._saAmfHctDefMaxDuration:
            changedAttrs.append("saAmfHctDefMaxDuration")
        if (fullCheck or self._SaImmAttrImplementerName != None) and other._SaImmAttrImplementerName != self._SaImmAttrImplementerName:
            changedAttrs.append("SaImmAttrImplementerName")
        if (fullCheck or self._SaImmAttrClassName != None) and other._SaImmAttrClassName != self._SaImmAttrClassName:
            changedAttrs.append("SaImmAttrClassName")
        if (fullCheck or self._SaImmAttrAdminOwnerName != None) and other._SaImmAttrAdminOwnerName != self._SaImmAttrAdminOwnerName:
            changedAttrs.append("SaImmAttrAdminOwnerName")
        return changedAttrs

    def parseXML(self, node):
        dns = node.getElementsByTagName("dn")
        if len(dns) != 1:
            error("object has " + str(len(dns)) + " dn(s) but it should have one")
        self._dn = dns[0].childNodes[0].nodeValue
        for attribute in node.getElementsByTagName("attr"):
            names = attribute.getElementsByTagName("name")
            if len(names) != 1:
                error("object attribute has " + str(len(names)) + " name(s) but it should have one")
            name = names[0].childNodes[0].nodeValue
            setFunc = None
            if name == "SaImmAttrImplementerName":
                continue
            elif name == "SaImmAttrAdminOwnerName":
                continue
            elif name == "SaImmAttrClassName":
                continue
            elif name == "saAmfHctDefPeriod":
                setFunc = self.setsaAmfHctDefPeriod
            elif name == "saAmfHctDefMaxDuration":
                setFunc = self.setsaAmfHctDefMaxDuration
            elif name == "SaImmAttrImplementerName":
                setFunc = self.setSaImmAttrImplementerName
            elif name == "SaImmAttrClassName":
                setFunc = self.setSaImmAttrClassName
            elif name == "SaImmAttrAdminOwnerName":
                setFunc = self.setSaImmAttrAdminOwnerName
            elif name.startswith("osaf"):
                continue # ignore OpenSAF specific attributes
            else:
                error("unknown attribute called " + name + " defined in object " + self._dn)
            for value in attribute.getElementsByTagName("value"):
                setFunc(value.childNodes[0].nodeValue)

    def writeXML(self, parent, doc):
        obj = doc.createElement("object")
        parent.appendChild(obj)
        obj.setAttribute("class", "SaAmfHealthcheckType")
        dn = doc.createElement("dn")
        obj.appendChild(dn)
        dn.appendChild(doc.createTextNode(self._dn))
        ImmHelper.writeSingleAttribute("saAmfHctDefPeriod", self._saAmfHctDefPeriod, doc, obj)
        ImmHelper.writeSingleAttribute("saAmfHctDefMaxDuration", self._saAmfHctDefMaxDuration, doc, obj)
        ImmHelper.writeSingleAttribute("SaImmAttrImplementerName", self._SaImmAttrImplementerName, doc, obj)
        ImmHelper.writeSingleAttribute("SaImmAttrClassName", self._SaImmAttrClassName, doc, obj)
        ImmHelper.writeSingleAttribute("SaImmAttrAdminOwnerName", self._SaImmAttrAdminOwnerName, doc, obj)


class SaAmfHealthcheck(object):
    def __init__(self):
        self._dn = None
        self._saAmfHealthcheckPeriod = None
        self._saAmfHealthcheckMaxDuration = None
        self._SaImmAttrImplementerName = None
        self._SaImmAttrClassName = None
        self._SaImmAttrAdminOwnerName = None

    @staticmethod
    def createDn(name, parentDn = None):
        if parentDn == None:
            parentDn = ""
        else:
            parentDn = "," + parentDn
        return "safHealthcheckKey=" + ImmHelper.escapeName(name) + parentDn

    def getDn(self):
        return self._dn

    def getName(self):
        return ImmHelper.getName(self._dn)

    def getRdn(self):
        return ImmHelper.getRdn(self._dn)

    def getParentDn(self):
        return ImmHelper.getParentDn(self._dn)

    def createObjectInCampaign(self, campaign):
        parentDn = self.getParentDn()
        if parentDn == "":
            parentDn = "="
        campaign.beginCreate("SaAmfHealthcheck", parentDn)
        campaign.addAttribute("safHealthcheckKey", "SA_IMM_ATTR_SASTRINGT", self.getRdn())
        if self._saAmfHealthcheckPeriod != None:
            campaign.addAttribute("saAmfHealthcheckPeriod", "SA_IMM_ATTR_SATIMET", self._saAmfHealthcheckPeriod)
        if self._saAmfHealthcheckMaxDuration != None:
            campaign.addAttribute("saAmfHealthcheckMaxDuration", "SA_IMM_ATTR_SATIMET", self._saAmfHealthcheckMaxDuration)
        if self._SaImmAttrImplementerName != None:
            campaign.addAttribute("SaImmAttrImplementerName", "SA_IMM_ATTR_SASTRINGT", self._SaImmAttrImplementerName)
        if self._SaImmAttrClassName != None:
            campaign.addAttribute("SaImmAttrClassName", "SA_IMM_ATTR_SASTRINGT", self._SaImmAttrClassName)
        if self._SaImmAttrAdminOwnerName != None:
            campaign.addAttribute("SaImmAttrAdminOwnerName", "SA_IMM_ATTR_SASTRINGT", self._SaImmAttrAdminOwnerName)
        campaign.endCreate()

    def getsaAmfHealthcheckPeriod(self):
        ImmHelper.validateSingle(self._saAmfHealthcheckPeriod, self._dn, "saAmfHealthcheckPeriod")
        return self._saAmfHealthcheckPeriod

    def getsaAmfHealthcheckMaxDuration(self):
        ImmHelper.validateSingle(self._saAmfHealthcheckMaxDuration, self._dn, "saAmfHealthcheckMaxDuration")
        return self._saAmfHealthcheckMaxDuration

    def getSaImmAttrImplementerName(self):
        ImmHelper.validateSingle(self._SaImmAttrImplementerName, self._dn, "SaImmAttrImplementerName")
        return self._SaImmAttrImplementerName

    def getSaImmAttrClassName(self):
        ImmHelper.validateSingle(self._SaImmAttrClassName, self._dn, "SaImmAttrClassName")
        return self._SaImmAttrClassName

    def getSaImmAttrAdminOwnerName(self):
        ImmHelper.validateSingle(self._SaImmAttrAdminOwnerName, self._dn, "SaImmAttrAdminOwnerName")
        return self._SaImmAttrAdminOwnerName

    def getsaAmfHealthcheckPeriod_unsafe(self):
        return self._saAmfHealthcheckPeriod

    def getsaAmfHealthcheckMaxDuration_unsafe(self):
        return self._saAmfHealthcheckMaxDuration

    def getSaImmAttrImplementerName_unsafe(self):
        return self._SaImmAttrImplementerName

    def getSaImmAttrClassName_unsafe(self):
        return self._SaImmAttrClassName

    def getSaImmAttrAdminOwnerName_unsafe(self):
        return self._SaImmAttrAdminOwnerName

    def setsaAmfHealthcheckPeriod(self, value):
        ImmHelper.validateTime(value, self._dn, "saAmfHealthcheckPeriod")
        value = str(value)
        self._saAmfHealthcheckPeriod = value

    def setsaAmfHealthcheckMaxDuration(self, value):
        ImmHelper.validateTime(value, self._dn, "saAmfHealthcheckMaxDuration")
        value = str(value)
        self._saAmfHealthcheckMaxDuration = value

    def setSaImmAttrImplementerName(self, value):
        ImmHelper.validateString(value, self._dn, "SaImmAttrImplementerName")
        self._SaImmAttrImplementerName = value

    def setSaImmAttrClassName(self, value):
        ImmHelper.validateString(value, self._dn, "SaImmAttrClassName")
        self._SaImmAttrClassName = value

    def setSaImmAttrAdminOwnerName(self, value):
        ImmHelper.validateString(value, self._dn, "SaImmAttrAdminOwnerName")
        self._SaImmAttrAdminOwnerName = value

    def updateParams(self, params, canttouchthis):
        for (param, value) in params.items():
            if param in canttouchthis:
                error("Setting attribute " + param + " in object " + self.getDn() + " is not supported")
            if param == "saAmfHealthcheckPeriod":
                self.setsaAmfHealthcheckPeriod(value)
            elif param == "saAmfHealthcheckMaxDuration":
                self.setsaAmfHealthcheckMaxDuration(value)
            else:
                error("Object " + self.getDn() + " has no attribute named " + param)

    def diff(self, other, fullCheck = False):
        changedAttrs = []
        if (fullCheck or self._saAmfHealthcheckPeriod != None) and other._saAmfHealthcheckPeriod != self._saAmfHealthcheckPeriod:
            changedAttrs.append("saAmfHealthcheckPeriod")
        if (fullCheck or self._saAmfHealthcheckMaxDuration != None) and other._saAmfHealthcheckMaxDuration != self._saAmfHealthcheckMaxDuration:
            changedAttrs.append("saAmfHealthcheckMaxDuration")
        if (fullCheck or self._SaImmAttrImplementerName != None) and other._SaImmAttrImplementerName != self._SaImmAttrImplementerName:
            changedAttrs.append("SaImmAttrImplementerName")
        if (fullCheck or self._SaImmAttrClassName != None) and other._SaImmAttrClassName != self._SaImmAttrClassName:
            changedAttrs.append("SaImmAttrClassName")
        if (fullCheck or self._SaImmAttrAdminOwnerName != None) and other._SaImmAttrAdminOwnerName != self._SaImmAttrAdminOwnerName:
            changedAttrs.append("SaImmAttrAdminOwnerName")
        return changedAttrs

    def parseXML(self, node):
        dns = node.getElementsByTagName("dn")
        if len(dns) != 1:
            error("object has " + str(len(dns)) + " dn(s) but it should have one")
        self._dn = dns[0].childNodes[0].nodeValue
        for attribute in node.getElementsByTagName("attr"):
            names = attribute.getElementsByTagName("name")
            if len(names) != 1:
                error("object attribute has " + str(len(names)) + " name(s) but it should have one")
            name = names[0].childNodes[0].nodeValue
            setFunc = None
            if name == "SaImmAttrImplementerName":
                continue
            elif name == "SaImmAttrAdminOwnerName":
                continue
            elif name == "SaImmAttrClassName":
                continue
            elif name == "saAmfHealthcheckPeriod":
                setFunc = self.setsaAmfHealthcheckPeriod
            elif name == "saAmfHealthcheckMaxDuration":
                setFunc = self.setsaAmfHealthcheckMaxDuration
            elif name == "SaImmAttrImplementerName":
                setFunc = self.setSaImmAttrImplementerName
            elif name == "SaImmAttrClassName":
                setFunc = self.setSaImmAttrClassName
            elif name == "SaImmAttrAdminOwnerName":
                setFunc = self.setSaImmAttrAdminOwnerName
            elif name.startswith("osaf"):
                continue # ignore OpenSAF specific attributes
            else:
                error("unknown attribute called " + name + " defined in object " + self._dn)
            for value in attribute.getElementsByTagName("value"):
                setFunc(value.childNodes[0].nodeValue)

    def writeXML(self, parent, doc):
        obj = doc.createElement("object")
        parent.appendChild(obj)
        obj.setAttribute("class", "SaAmfHealthcheck")
        dn = doc.createElement("dn")
        obj.appendChild(dn)
        dn.appendChild(doc.createTextNode(self._dn))
        ImmHelper.writeSingleAttribute("saAmfHealthcheckPeriod", self._saAmfHealthcheckPeriod, doc, obj)
        ImmHelper.writeSingleAttribute("saAmfHealthcheckMaxDuration", self._saAmfHealthcheckMaxDuration, doc, obj)
        ImmHelper.writeSingleAttribute("SaImmAttrImplementerName", self._SaImmAttrImplementerName, doc, obj)
        ImmHelper.writeSingleAttribute("SaImmAttrClassName", self._SaImmAttrClassName, doc, obj)
        ImmHelper.writeSingleAttribute("SaImmAttrAdminOwnerName", self._SaImmAttrAdminOwnerName, doc, obj)


class SaAmfCtCsType(object):
    def __init__(self):
        self._dn = None
        self._saAmfCtDefNumMaxStandbyCSIs = None
        self._saAmfCtDefNumMaxActiveCSIs = None
        self._saAmfCtCompCapability = None
        self._SaImmAttrImplementerName = None
        self._SaImmAttrClassName = None
        self._SaImmAttrAdminOwnerName = None

    @staticmethod
    def createDn(name, parentDn = None):
        if parentDn == None:
            parentDn = ""
        else:
            parentDn = "," + parentDn
        return "safSupportedCsType=" + ImmHelper.escapeName(name) + parentDn

    def getDn(self):
        return self._dn

    def getName(self):
        return ImmHelper.getName(self._dn)

    def getRdn(self):
        return ImmHelper.getRdn(self._dn)

    def getParentDn(self):
        return ImmHelper.getParentDn(self._dn)

    def createObjectInCampaign(self, campaign):
        parentDn = self.getParentDn()
        if parentDn == "":
            parentDn = "="
        campaign.beginCreate("SaAmfCtCsType", parentDn)
        campaign.addAttribute("safSupportedCsType", "SA_IMM_ATTR_SANAMET", self.getRdn())
        if self._saAmfCtDefNumMaxStandbyCSIs != None:
            campaign.addAttribute("saAmfCtDefNumMaxStandbyCSIs", "SA_IMM_ATTR_SAUINT32T", self._saAmfCtDefNumMaxStandbyCSIs)
        if self._saAmfCtDefNumMaxActiveCSIs != None:
            campaign.addAttribute("saAmfCtDefNumMaxActiveCSIs", "SA_IMM_ATTR_SAUINT32T", self._saAmfCtDefNumMaxActiveCSIs)
        if self._saAmfCtCompCapability != None:
            campaign.addAttribute("saAmfCtCompCapability", "SA_IMM_ATTR_SAUINT32T", self._saAmfCtCompCapability)
        if self._SaImmAttrImplementerName != None:
            campaign.addAttribute("SaImmAttrImplementerName", "SA_IMM_ATTR_SASTRINGT", self._SaImmAttrImplementerName)
        if self._SaImmAttrClassName != None:
            campaign.addAttribute("SaImmAttrClassName", "SA_IMM_ATTR_SASTRINGT", self._SaImmAttrClassName)
        if self._SaImmAttrAdminOwnerName != None:
            campaign.addAttribute("SaImmAttrAdminOwnerName", "SA_IMM_ATTR_SASTRINGT", self._SaImmAttrAdminOwnerName)
        campaign.endCreate()

    def getsaAmfCtDefNumMaxStandbyCSIs(self):
        ImmHelper.validateSingle(self._saAmfCtDefNumMaxStandbyCSIs, self._dn, "saAmfCtDefNumMaxStandbyCSIs")
        return self._saAmfCtDefNumMaxStandbyCSIs

    def getsaAmfCtDefNumMaxActiveCSIs(self):
        ImmHelper.validateSingle(self._saAmfCtDefNumMaxActiveCSIs, self._dn, "saAmfCtDefNumMaxActiveCSIs")
        return self._saAmfCtDefNumMaxActiveCSIs

    def getsaAmfCtCompCapability(self):
        ImmHelper.validateSingle(self._saAmfCtCompCapability, self._dn, "saAmfCtCompCapability")
        return self._saAmfCtCompCapability

    def getSaImmAttrImplementerName(self):
        ImmHelper.validateSingle(self._SaImmAttrImplementerName, self._dn, "SaImmAttrImplementerName")
        return self._SaImmAttrImplementerName

    def getSaImmAttrClassName(self):
        ImmHelper.validateSingle(self._SaImmAttrClassName, self._dn, "SaImmAttrClassName")
        return self._SaImmAttrClassName

    def getSaImmAttrAdminOwnerName(self):
        ImmHelper.validateSingle(self._SaImmAttrAdminOwnerName, self._dn, "SaImmAttrAdminOwnerName")
        return self._SaImmAttrAdminOwnerName

    def getsaAmfCtDefNumMaxStandbyCSIs_unsafe(self):
        return self._saAmfCtDefNumMaxStandbyCSIs

    def getsaAmfCtDefNumMaxActiveCSIs_unsafe(self):
        return self._saAmfCtDefNumMaxActiveCSIs

    def getsaAmfCtCompCapability_unsafe(self):
        return self._saAmfCtCompCapability

    def getSaImmAttrImplementerName_unsafe(self):
        return self._SaImmAttrImplementerName

    def getSaImmAttrClassName_unsafe(self):
        return self._SaImmAttrClassName

    def getSaImmAttrAdminOwnerName_unsafe(self):
        return self._SaImmAttrAdminOwnerName

    def setsaAmfCtDefNumMaxStandbyCSIs(self, value):
        ImmHelper.validateUint32(value, self._dn, "saAmfCtDefNumMaxStandbyCSIs")
        value = str(value)
        self._saAmfCtDefNumMaxStandbyCSIs = value

    def setsaAmfCtDefNumMaxActiveCSIs(self, value):
        ImmHelper.validateUint32(value, self._dn, "saAmfCtDefNumMaxActiveCSIs")
        value = str(value)
        self._saAmfCtDefNumMaxActiveCSIs = value

    def setsaAmfCtCompCapability(self, value):
        ImmHelper.validateUint32(value, self._dn, "saAmfCtCompCapability")
        value = str(value)
        self._saAmfCtCompCapability = value

    def setSaImmAttrImplementerName(self, value):
        ImmHelper.validateString(value, self._dn, "SaImmAttrImplementerName")
        self._SaImmAttrImplementerName = value

    def setSaImmAttrClassName(self, value):
        ImmHelper.validateString(value, self._dn, "SaImmAttrClassName")
        self._SaImmAttrClassName = value

    def setSaImmAttrAdminOwnerName(self, value):
        ImmHelper.validateString(value, self._dn, "SaImmAttrAdminOwnerName")
        self._SaImmAttrAdminOwnerName = value

    def updateParams(self, params, canttouchthis):
        for (param, value) in params.items():
            if param in canttouchthis:
                error("Setting attribute " + param + " in object " + self.getDn() + " is not supported")
            else:
                error("Object " + self.getDn() + " has no attribute named " + param)

    def diff(self, other, fullCheck = False):
        changedAttrs = []
        if (fullCheck or self._saAmfCtDefNumMaxStandbyCSIs != None) and other._saAmfCtDefNumMaxStandbyCSIs != self._saAmfCtDefNumMaxStandbyCSIs:
            changedAttrs.append("saAmfCtDefNumMaxStandbyCSIs")
        if (fullCheck or self._saAmfCtDefNumMaxActiveCSIs != None) and other._saAmfCtDefNumMaxActiveCSIs != self._saAmfCtDefNumMaxActiveCSIs:
            changedAttrs.append("saAmfCtDefNumMaxActiveCSIs")
        if (fullCheck or self._saAmfCtCompCapability != None) and other._saAmfCtCompCapability != self._saAmfCtCompCapability:
            changedAttrs.append("saAmfCtCompCapability")
        if (fullCheck or self._SaImmAttrImplementerName != None) and other._SaImmAttrImplementerName != self._SaImmAttrImplementerName:
            changedAttrs.append("SaImmAttrImplementerName")
        if (fullCheck or self._SaImmAttrClassName != None) and other._SaImmAttrClassName != self._SaImmAttrClassName:
            changedAttrs.append("SaImmAttrClassName")
        if (fullCheck or self._SaImmAttrAdminOwnerName != None) and other._SaImmAttrAdminOwnerName != self._SaImmAttrAdminOwnerName:
            changedAttrs.append("SaImmAttrAdminOwnerName")
        return changedAttrs

    def parseXML(self, node):
        dns = node.getElementsByTagName("dn")
        if len(dns) != 1:
            error("object has " + str(len(dns)) + " dn(s) but it should have one")
        self._dn = dns[0].childNodes[0].nodeValue
        for attribute in node.getElementsByTagName("attr"):
            names = attribute.getElementsByTagName("name")
            if len(names) != 1:
                error("object attribute has " + str(len(names)) + " name(s) but it should have one")
            name = names[0].childNodes[0].nodeValue
            setFunc = None
            if name == "SaImmAttrImplementerName":
                continue
            elif name == "SaImmAttrAdminOwnerName":
                continue
            elif name == "SaImmAttrClassName":
                continue
            elif name == "saAmfCtDefNumMaxStandbyCSIs":
                setFunc = self.setsaAmfCtDefNumMaxStandbyCSIs
            elif name == "saAmfCtDefNumMaxActiveCSIs":
                setFunc = self.setsaAmfCtDefNumMaxActiveCSIs
            elif name == "saAmfCtCompCapability":
                setFunc = self.setsaAmfCtCompCapability
            elif name == "SaImmAttrImplementerName":
                setFunc = self.setSaImmAttrImplementerName
            elif name == "SaImmAttrClassName":
                setFunc = self.setSaImmAttrClassName
            elif name == "SaImmAttrAdminOwnerName":
                setFunc = self.setSaImmAttrAdminOwnerName
            elif name.startswith("osaf"):
                continue # ignore OpenSAF specific attributes
            else:
                error("unknown attribute called " + name + " defined in object " + self._dn)
            for value in attribute.getElementsByTagName("value"):
                setFunc(value.childNodes[0].nodeValue)

    def writeXML(self, parent, doc):
        obj = doc.createElement("object")
        parent.appendChild(obj)
        obj.setAttribute("class", "SaAmfCtCsType")
        dn = doc.createElement("dn")
        obj.appendChild(dn)
        dn.appendChild(doc.createTextNode(self._dn))
        ImmHelper.writeSingleAttribute("saAmfCtDefNumMaxStandbyCSIs", self._saAmfCtDefNumMaxStandbyCSIs, doc, obj)
        ImmHelper.writeSingleAttribute("saAmfCtDefNumMaxActiveCSIs", self._saAmfCtDefNumMaxActiveCSIs, doc, obj)
        ImmHelper.writeSingleAttribute("saAmfCtCompCapability", self._saAmfCtCompCapability, doc, obj)
        ImmHelper.writeSingleAttribute("SaImmAttrImplementerName", self._SaImmAttrImplementerName, doc, obj)
        ImmHelper.writeSingleAttribute("SaImmAttrClassName", self._SaImmAttrClassName, doc, obj)
        ImmHelper.writeSingleAttribute("SaImmAttrAdminOwnerName", self._SaImmAttrAdminOwnerName, doc, obj)


class SaAmfCompType(object):
    def __init__(self):
        self._dn = None
        self._saAmfCtSwBundle = None
        self._saAmfCtRelPathTerminateCmd = None
        self._saAmfCtRelPathInstantiateCmd = None
        self._saAmfCtRelPathCleanupCmd = None
        self._saAmfCtRelPathAmStopCmd = None
        self._saAmfCtRelPathAmStartCmd = None
        self._saAmfCtDefTerminateCmdArgv = []
        self._saAmfCtDefRecoveryOnError = None
        self._saAmfCtDefQuiescingCompleteTimeout = None
        self._saAmfCtDefInstantiationLevel = None
        self._saAmfCtDefInstantiateCmdArgv = []
        self._saAmfCtDefDisableRestart = None
        self._saAmfCtDefCmdEnv = []
        self._saAmfCtDefCleanupCmdArgv = []
        self._saAmfCtDefClcCliTimeout = None
        self._saAmfCtDefCallbackTimeout = None
        self._saAmfCtDefAmStopCmdArgv = []
        self._saAmfCtDefAmStartCmdArgv = []
        self._saAmfCtCompCategory = None
        self._osafAmfCtRelPathHcCmd = None
        self._osafAmfCtDefHcCmdArgv = []
        self._SaImmAttrImplementerName = None
        self._SaImmAttrClassName = None
        self._SaImmAttrAdminOwnerName = None

    @staticmethod
    def createDn(name, parentDn = None):
        if parentDn == None:
            parentDn = ""
        else:
            parentDn = "," + parentDn
        return "safVersion=" + ImmHelper.escapeName(name) + parentDn

    def getDn(self):
        return self._dn

    def getName(self):
        return ImmHelper.getName(self._dn)

    def getRdn(self):
        return ImmHelper.getRdn(self._dn)

    def getParentDn(self):
        return ImmHelper.getParentDn(self._dn)

    def createObjectInCampaign(self, campaign):
        parentDn = self.getParentDn()
        if parentDn == "":
            parentDn = "="
        campaign.beginCreate("SaAmfCompType", parentDn)
        campaign.addAttribute("safVersion", "SA_IMM_ATTR_SASTRINGT", self.getRdn())
        if self._saAmfCtSwBundle != None:
            campaign.addAttribute("saAmfCtSwBundle", "SA_IMM_ATTR_SANAMET", self._saAmfCtSwBundle)
        if self._saAmfCtRelPathTerminateCmd != None:
            campaign.addAttribute("saAmfCtRelPathTerminateCmd", "SA_IMM_ATTR_SASTRINGT", self._saAmfCtRelPathTerminateCmd)
        if self._saAmfCtRelPathInstantiateCmd != None:
            campaign.addAttribute("saAmfCtRelPathInstantiateCmd", "SA_IMM_ATTR_SASTRINGT", self._saAmfCtRelPathInstantiateCmd)
        if self._saAmfCtRelPathCleanupCmd != None:
            campaign.addAttribute("saAmfCtRelPathCleanupCmd", "SA_IMM_ATTR_SASTRINGT", self._saAmfCtRelPathCleanupCmd)
        if self._saAmfCtRelPathAmStopCmd != None:
            campaign.addAttribute("saAmfCtRelPathAmStopCmd", "SA_IMM_ATTR_SASTRINGT", self._saAmfCtRelPathAmStopCmd)
        if self._saAmfCtRelPathAmStartCmd != None:
            campaign.addAttribute("saAmfCtRelPathAmStartCmd", "SA_IMM_ATTR_SASTRINGT", self._saAmfCtRelPathAmStartCmd)
        if len(self._saAmfCtDefTerminateCmdArgv) > 0:
            campaign.addAttribute("saAmfCtDefTerminateCmdArgv", "SA_IMM_ATTR_SASTRINGT", self._saAmfCtDefTerminateCmdArgv)
        if self._saAmfCtDefRecoveryOnError != None:
            campaign.addAttribute("saAmfCtDefRecoveryOnError", "SA_IMM_ATTR_SAUINT32T", self._saAmfCtDefRecoveryOnError)
        if self._saAmfCtDefQuiescingCompleteTimeout != None:
            campaign.addAttribute("saAmfCtDefQuiescingCompleteTimeout", "SA_IMM_ATTR_SATIMET", self._saAmfCtDefQuiescingCompleteTimeout)
        if self._saAmfCtDefInstantiationLevel != None:
            campaign.addAttribute("saAmfCtDefInstantiationLevel", "SA_IMM_ATTR_SAUINT32T", self._saAmfCtDefInstantiationLevel)
        if len(self._saAmfCtDefInstantiateCmdArgv) > 0:
            campaign.addAttribute("saAmfCtDefInstantiateCmdArgv", "SA_IMM_ATTR_SASTRINGT", self._saAmfCtDefInstantiateCmdArgv)
        if self._saAmfCtDefDisableRestart != None:
            campaign.addAttribute("saAmfCtDefDisableRestart", "SA_IMM_ATTR_SAUINT32T", self._saAmfCtDefDisableRestart)
        if len(self._saAmfCtDefCmdEnv) > 0:
            campaign.addAttribute("saAmfCtDefCmdEnv", "SA_IMM_ATTR_SASTRINGT", self._saAmfCtDefCmdEnv)
        if len(self._saAmfCtDefCleanupCmdArgv) > 0:
            campaign.addAttribute("saAmfCtDefCleanupCmdArgv", "SA_IMM_ATTR_SASTRINGT", self._saAmfCtDefCleanupCmdArgv)
        if self._saAmfCtDefClcCliTimeout != None:
            campaign.addAttribute("saAmfCtDefClcCliTimeout", "SA_IMM_ATTR_SATIMET", self._saAmfCtDefClcCliTimeout)
        if self._saAmfCtDefCallbackTimeout != None:
            campaign.addAttribute("saAmfCtDefCallbackTimeout", "SA_IMM_ATTR_SATIMET", self._saAmfCtDefCallbackTimeout)
        if len(self._saAmfCtDefAmStopCmdArgv) > 0:
            campaign.addAttribute("saAmfCtDefAmStopCmdArgv", "SA_IMM_ATTR_SASTRINGT", self._saAmfCtDefAmStopCmdArgv)
        if len(self._saAmfCtDefAmStartCmdArgv) > 0:
            campaign.addAttribute("saAmfCtDefAmStartCmdArgv", "SA_IMM_ATTR_SASTRINGT", self._saAmfCtDefAmStartCmdArgv)
        if self._saAmfCtCompCategory != None:
            campaign.addAttribute("saAmfCtCompCategory", "SA_IMM_ATTR_SAUINT32T", self._saAmfCtCompCategory)
        if self._osafAmfCtRelPathHcCmd != None:
            campaign.addAttribute("osafAmfCtRelPathHcCmd", "SA_IMM_ATTR_SASTRINGT", self._osafAmfCtRelPathHcCmd)
        if len(self._osafAmfCtDefHcCmdArgv) > 0:
            campaign.addAttribute("osafAmfCtDefHcCmdArgv", "SA_IMM_ATTR_SASTRINGT", self._osafAmfCtDefHcCmdArgv)
        if self._SaImmAttrImplementerName != None:
            campaign.addAttribute("SaImmAttrImplementerName", "SA_IMM_ATTR_SASTRINGT", self._SaImmAttrImplementerName)
        if self._SaImmAttrClassName != None:
            campaign.addAttribute("SaImmAttrClassName", "SA_IMM_ATTR_SASTRINGT", self._SaImmAttrClassName)
        if self._SaImmAttrAdminOwnerName != None:
            campaign.addAttribute("SaImmAttrAdminOwnerName", "SA_IMM_ATTR_SASTRINGT", self._SaImmAttrAdminOwnerName)
        campaign.endCreate()

    def getsaAmfCtSwBundle(self):
        ImmHelper.validateSingle(self._saAmfCtSwBundle, self._dn, "saAmfCtSwBundle")
        return self._saAmfCtSwBundle

    def getsaAmfCtRelPathTerminateCmd(self):
        ImmHelper.validateSingle(self._saAmfCtRelPathTerminateCmd, self._dn, "saAmfCtRelPathTerminateCmd")
        return self._saAmfCtRelPathTerminateCmd

    def getsaAmfCtRelPathInstantiateCmd(self):
        ImmHelper.validateSingle(self._saAmfCtRelPathInstantiateCmd, self._dn, "saAmfCtRelPathInstantiateCmd")
        return self._saAmfCtRelPathInstantiateCmd

    def getsaAmfCtRelPathCleanupCmd(self):
        ImmHelper.validateSingle(self._saAmfCtRelPathCleanupCmd, self._dn, "saAmfCtRelPathCleanupCmd")
        return self._saAmfCtRelPathCleanupCmd

    def getsaAmfCtRelPathAmStopCmd(self):
        ImmHelper.validateSingle(self._saAmfCtRelPathAmStopCmd, self._dn, "saAmfCtRelPathAmStopCmd")
        return self._saAmfCtRelPathAmStopCmd

    def getsaAmfCtRelPathAmStartCmd(self):
        ImmHelper.validateSingle(self._saAmfCtRelPathAmStartCmd, self._dn, "saAmfCtRelPathAmStartCmd")
        return self._saAmfCtRelPathAmStartCmd

    def getsaAmfCtDefTerminateCmdArgv(self):
        return self._saAmfCtDefTerminateCmdArgv

    def getsaAmfCtDefRecoveryOnError(self):
        ImmHelper.validateSingle(self._saAmfCtDefRecoveryOnError, self._dn, "saAmfCtDefRecoveryOnError")
        return self._saAmfCtDefRecoveryOnError

    def getsaAmfCtDefQuiescingCompleteTimeout(self):
        ImmHelper.validateSingle(self._saAmfCtDefQuiescingCompleteTimeout, self._dn, "saAmfCtDefQuiescingCompleteTimeout")
        return self._saAmfCtDefQuiescingCompleteTimeout

    def getsaAmfCtDefInstantiationLevel(self):
        ImmHelper.validateSingle(self._saAmfCtDefInstantiationLevel, self._dn, "saAmfCtDefInstantiationLevel")
        return self._saAmfCtDefInstantiationLevel

    def getsaAmfCtDefInstantiateCmdArgv(self):
        return self._saAmfCtDefInstantiateCmdArgv

    def getsaAmfCtDefDisableRestart(self):
        ImmHelper.validateSingle(self._saAmfCtDefDisableRestart, self._dn, "saAmfCtDefDisableRestart")
        return self._saAmfCtDefDisableRestart

    def getsaAmfCtDefCmdEnv(self):
        return self._saAmfCtDefCmdEnv

    def getsaAmfCtDefCleanupCmdArgv(self):
        return self._saAmfCtDefCleanupCmdArgv

    def getsaAmfCtDefClcCliTimeout(self):
        ImmHelper.validateSingle(self._saAmfCtDefClcCliTimeout, self._dn, "saAmfCtDefClcCliTimeout")
        return self._saAmfCtDefClcCliTimeout

    def getsaAmfCtDefCallbackTimeout(self):
        ImmHelper.validateSingle(self._saAmfCtDefCallbackTimeout, self._dn, "saAmfCtDefCallbackTimeout")
        return self._saAmfCtDefCallbackTimeout

    def getsaAmfCtDefAmStopCmdArgv(self):
        return self._saAmfCtDefAmStopCmdArgv

    def getsaAmfCtDefAmStartCmdArgv(self):
        return self._saAmfCtDefAmStartCmdArgv

    def getsaAmfCtCompCategory(self):
        ImmHelper.validateSingle(self._saAmfCtCompCategory, self._dn, "saAmfCtCompCategory")
        return self._saAmfCtCompCategory

    def getosafAmfCtRelPathHcCmd(self):
        ImmHelper.validateSingle(self._osafAmfCtRelPathHcCmd, self._dn, "osafAmfCtRelPathHcCmd")
        return self._osafAmfCtRelPathHcCmd

    def getosafAmfCtDefHcCmdArgv(self):
        return self._osafAmfCtDefHcCmdArgv

    def getSaImmAttrImplementerName(self):
        ImmHelper.validateSingle(self._SaImmAttrImplementerName, self._dn, "SaImmAttrImplementerName")
        return self._SaImmAttrImplementerName

    def getSaImmAttrClassName(self):
        ImmHelper.validateSingle(self._SaImmAttrClassName, self._dn, "SaImmAttrClassName")
        return self._SaImmAttrClassName

    def getSaImmAttrAdminOwnerName(self):
        ImmHelper.validateSingle(self._SaImmAttrAdminOwnerName, self._dn, "SaImmAttrAdminOwnerName")
        return self._SaImmAttrAdminOwnerName

    def getsaAmfCtSwBundle_unsafe(self):
        return self._saAmfCtSwBundle

    def getsaAmfCtRelPathTerminateCmd_unsafe(self):
        return self._saAmfCtRelPathTerminateCmd

    def getsaAmfCtRelPathInstantiateCmd_unsafe(self):
        return self._saAmfCtRelPathInstantiateCmd

    def getsaAmfCtRelPathCleanupCmd_unsafe(self):
        return self._saAmfCtRelPathCleanupCmd

    def getsaAmfCtRelPathAmStopCmd_unsafe(self):
        return self._saAmfCtRelPathAmStopCmd

    def getsaAmfCtRelPathAmStartCmd_unsafe(self):
        return self._saAmfCtRelPathAmStartCmd

    def getsaAmfCtDefTerminateCmdArgv_single(self):
        ImmHelper.validateSingleInList(self._saAmfCtDefTerminateCmdArgv, self._dn, "saAmfCtDefTerminateCmdArgv")
        return self._saAmfCtDefTerminateCmdArgv[0]

    def getsaAmfCtDefRecoveryOnError_unsafe(self):
        return self._saAmfCtDefRecoveryOnError

    def getsaAmfCtDefQuiescingCompleteTimeout_unsafe(self):
        return self._saAmfCtDefQuiescingCompleteTimeout

    def getsaAmfCtDefInstantiationLevel_unsafe(self):
        return self._saAmfCtDefInstantiationLevel

    def getsaAmfCtDefInstantiateCmdArgv_single(self):
        ImmHelper.validateSingleInList(self._saAmfCtDefInstantiateCmdArgv, self._dn, "saAmfCtDefInstantiateCmdArgv")
        return self._saAmfCtDefInstantiateCmdArgv[0]

    def getsaAmfCtDefDisableRestart_unsafe(self):
        return self._saAmfCtDefDisableRestart

    def getsaAmfCtDefCmdEnv_single(self):
        ImmHelper.validateSingleInList(self._saAmfCtDefCmdEnv, self._dn, "saAmfCtDefCmdEnv")
        return self._saAmfCtDefCmdEnv[0]

    def getsaAmfCtDefCleanupCmdArgv_single(self):
        ImmHelper.validateSingleInList(self._saAmfCtDefCleanupCmdArgv, self._dn, "saAmfCtDefCleanupCmdArgv")
        return self._saAmfCtDefCleanupCmdArgv[0]

    def getsaAmfCtDefClcCliTimeout_unsafe(self):
        return self._saAmfCtDefClcCliTimeout

    def getsaAmfCtDefCallbackTimeout_unsafe(self):
        return self._saAmfCtDefCallbackTimeout

    def getsaAmfCtDefAmStopCmdArgv_single(self):
        ImmHelper.validateSingleInList(self._saAmfCtDefAmStopCmdArgv, self._dn, "saAmfCtDefAmStopCmdArgv")
        return self._saAmfCtDefAmStopCmdArgv[0]

    def getsaAmfCtDefAmStartCmdArgv_single(self):
        ImmHelper.validateSingleInList(self._saAmfCtDefAmStartCmdArgv, self._dn, "saAmfCtDefAmStartCmdArgv")
        return self._saAmfCtDefAmStartCmdArgv[0]

    def getsaAmfCtCompCategory_unsafe(self):
        return self._saAmfCtCompCategory

    def getosafAmfCtRelPathHcCmd_unsafe(self):
        return self._osafAmfCtRelPathHcCmd

    def getosafAmfCtDefHcCmdArgv_single(self):
        ImmHelper.validateSingleInList(self._osafAmfCtDefHcCmdArgv, self._dn, "osafAmfCtDefHcCmdArgv")
        return self._osafAmfCtDefHcCmdArgv[0]

    def getSaImmAttrImplementerName_unsafe(self):
        return self._SaImmAttrImplementerName

    def getSaImmAttrClassName_unsafe(self):
        return self._SaImmAttrClassName

    def getSaImmAttrAdminOwnerName_unsafe(self):
        return self._SaImmAttrAdminOwnerName

    def setsaAmfCtSwBundle(self, value):
        ImmHelper.validateName(value, self._dn, "saAmfCtSwBundle")
        self._saAmfCtSwBundle = value

    def setsaAmfCtRelPathTerminateCmd(self, value):
        ImmHelper.validateString(value, self._dn, "saAmfCtRelPathTerminateCmd")
        self._saAmfCtRelPathTerminateCmd = value

    def setsaAmfCtRelPathInstantiateCmd(self, value):
        ImmHelper.validateString(value, self._dn, "saAmfCtRelPathInstantiateCmd")
        self._saAmfCtRelPathInstantiateCmd = value

    def setsaAmfCtRelPathCleanupCmd(self, value):
        ImmHelper.validateString(value, self._dn, "saAmfCtRelPathCleanupCmd")
        self._saAmfCtRelPathCleanupCmd = value

    def setsaAmfCtRelPathAmStopCmd(self, value):
        ImmHelper.validateString(value, self._dn, "saAmfCtRelPathAmStopCmd")
        self._saAmfCtRelPathAmStopCmd = value

    def setsaAmfCtRelPathAmStartCmd(self, value):
        ImmHelper.validateString(value, self._dn, "saAmfCtRelPathAmStartCmd")
        self._saAmfCtRelPathAmStartCmd = value

    def addTosaAmfCtDefTerminateCmdArgv(self, value):
        ImmHelper.validateString(value, self._dn, "saAmfCtDefTerminateCmdArgv")
        self._saAmfCtDefTerminateCmdArgv.append(value)

    def setsaAmfCtDefRecoveryOnError(self, value):
        ImmHelper.validateUint32(value, self._dn, "saAmfCtDefRecoveryOnError")
        value = str(value)
        self._saAmfCtDefRecoveryOnError = value

    def setsaAmfCtDefQuiescingCompleteTimeout(self, value):
        ImmHelper.validateTime(value, self._dn, "saAmfCtDefQuiescingCompleteTimeout")
        value = str(value)
        self._saAmfCtDefQuiescingCompleteTimeout = value

    def setsaAmfCtDefInstantiationLevel(self, value):
        ImmHelper.validateUint32(value, self._dn, "saAmfCtDefInstantiationLevel")
        value = str(value)
        self._saAmfCtDefInstantiationLevel = value

    def addTosaAmfCtDefInstantiateCmdArgv(self, value):
        ImmHelper.validateString(value, self._dn, "saAmfCtDefInstantiateCmdArgv")
        self._saAmfCtDefInstantiateCmdArgv.append(value)

    def setsaAmfCtDefDisableRestart(self, value):
        ImmHelper.validateUint32(value, self._dn, "saAmfCtDefDisableRestart")
        value = str(value)
        self._saAmfCtDefDisableRestart = value

    def addTosaAmfCtDefCmdEnv(self, value):
        ImmHelper.validateString(value, self._dn, "saAmfCtDefCmdEnv")
        self._saAmfCtDefCmdEnv.append(value)

    def addTosaAmfCtDefCleanupCmdArgv(self, value):
        ImmHelper.validateString(value, self._dn, "saAmfCtDefCleanupCmdArgv")
        self._saAmfCtDefCleanupCmdArgv.append(value)

    def setsaAmfCtDefClcCliTimeout(self, value):
        ImmHelper.validateTime(value, self._dn, "saAmfCtDefClcCliTimeout")
        value = str(value)
        self._saAmfCtDefClcCliTimeout = value

    def setsaAmfCtDefCallbackTimeout(self, value):
        ImmHelper.validateTime(value, self._dn, "saAmfCtDefCallbackTimeout")
        value = str(value)
        self._saAmfCtDefCallbackTimeout = value

    def addTosaAmfCtDefAmStopCmdArgv(self, value):
        ImmHelper.validateString(value, self._dn, "saAmfCtDefAmStopCmdArgv")
        self._saAmfCtDefAmStopCmdArgv.append(value)

    def addTosaAmfCtDefAmStartCmdArgv(self, value):
        ImmHelper.validateString(value, self._dn, "saAmfCtDefAmStartCmdArgv")
        self._saAmfCtDefAmStartCmdArgv.append(value)

    def setsaAmfCtCompCategory(self, value):
        ImmHelper.validateUint32(value, self._dn, "saAmfCtCompCategory")
        value = str(value)
        self._saAmfCtCompCategory = value

    def setosafAmfCtRelPathHcCmd(self, value):
        ImmHelper.validateString(value, self._dn, "osafAmfCtRelPathHcCmd")
        self._osafAmfCtRelPathHcCmd = value

    def addToosafAmfCtDefHcCmdArgv(self, value):
        ImmHelper.validateString(value, self._dn, "osafAmfCtDefHcCmdArgv")
        self._osafAmfCtDefHcCmdArgv.append(value)

    def setSaImmAttrImplementerName(self, value):
        ImmHelper.validateString(value, self._dn, "SaImmAttrImplementerName")
        self._SaImmAttrImplementerName = value

    def setSaImmAttrClassName(self, value):
        ImmHelper.validateString(value, self._dn, "SaImmAttrClassName")
        self._SaImmAttrClassName = value

    def setSaImmAttrAdminOwnerName(self, value):
        ImmHelper.validateString(value, self._dn, "SaImmAttrAdminOwnerName")
        self._SaImmAttrAdminOwnerName = value

    def updateParams(self, params, canttouchthis):
        for (param, value) in params.items():
            if param in canttouchthis:
                error("Setting attribute " + param + " in object " + self.getDn() + " is not supported")
            if param == "saAmfCtDefTerminateCmdArgv":
                if not isinstance(value, list):
                    value = [value]
                self._saAmfCtDefTerminateCmdArgv = []
                for v in value:
                    self.addTosaAmfCtDefTerminateCmdArgv(v)
            elif param == "saAmfCtDefRecoveryOnError":
                self.setsaAmfCtDefRecoveryOnError(value)
            elif param == "saAmfCtDefQuiescingCompleteTimeout":
                self.setsaAmfCtDefQuiescingCompleteTimeout(value)
            elif param == "saAmfCtDefInstantiationLevel":
                self.setsaAmfCtDefInstantiationLevel(value)
            elif param == "saAmfCtDefInstantiateCmdArgv":
                if not isinstance(value, list):
                    value = [value]
                self._saAmfCtDefInstantiateCmdArgv = []
                for v in value:
                    self.addTosaAmfCtDefInstantiateCmdArgv(v)
            elif param == "saAmfCtDefDisableRestart":
                self.setsaAmfCtDefDisableRestart(value)
            elif param == "saAmfCtDefCleanupCmdArgv":
                if not isinstance(value, list):
                    value = [value]
                self._saAmfCtDefCleanupCmdArgv = []
                for v in value:
                    self.addTosaAmfCtDefCleanupCmdArgv(v)
            elif param == "saAmfCtDefClcCliTimeout":
                self.setsaAmfCtDefClcCliTimeout(value)
            elif param == "saAmfCtDefCallbackTimeout":
                self.setsaAmfCtDefCallbackTimeout(value)
            elif param == "saAmfCtDefAmStopCmdArgv":
                if not isinstance(value, list):
                    value = [value]
                self._saAmfCtDefAmStopCmdArgv = []
                for v in value:
                    self.addTosaAmfCtDefAmStopCmdArgv(v)
            elif param == "saAmfCtDefAmStartCmdArgv":
                if not isinstance(value, list):
                    value = [value]
                self._saAmfCtDefAmStartCmdArgv = []
                for v in value:
                    self.addTosaAmfCtDefAmStartCmdArgv(v)
            elif param == "osafAmfCtDefHcCmdArgv":
                if not isinstance(value, list):
                    value = [value]
                self._osafAmfCtDefHcCmdArgv = []
                for v in value:
                    self.addToosafAmfCtDefHcCmdArgv(v)
            else:
                error("Object " + self.getDn() + " has no attribute named " + param)

    def diff(self, other, fullCheck = False):
        changedAttrs = []
        if (fullCheck or self._saAmfCtSwBundle != None) and other._saAmfCtSwBundle != self._saAmfCtSwBundle:
            changedAttrs.append("saAmfCtSwBundle")
        if (fullCheck or self._saAmfCtRelPathTerminateCmd != None) and other._saAmfCtRelPathTerminateCmd != self._saAmfCtRelPathTerminateCmd:
            if other._dn != self._dn:
                changedAttrs.append("saAmfCtRelPathTerminateCmd")
        if (fullCheck or self._saAmfCtRelPathInstantiateCmd != None) and other._saAmfCtRelPathInstantiateCmd != self._saAmfCtRelPathInstantiateCmd:
            if other._dn != self._dn:
                changedAttrs.append("saAmfCtRelPathInstantiateCmd")
        if (fullCheck or self._saAmfCtRelPathCleanupCmd != None) and other._saAmfCtRelPathCleanupCmd != self._saAmfCtRelPathCleanupCmd:
            if other._dn != self._dn:
                changedAttrs.append("saAmfCtRelPathCleanupCmd")
        if (fullCheck or self._saAmfCtRelPathAmStopCmd != None) and other._saAmfCtRelPathAmStopCmd != self._saAmfCtRelPathAmStopCmd:
            changedAttrs.append("saAmfCtRelPathAmStopCmd")
        if (fullCheck or self._saAmfCtRelPathAmStartCmd != None) and other._saAmfCtRelPathAmStartCmd != self._saAmfCtRelPathAmStartCmd:
            changedAttrs.append("saAmfCtRelPathAmStartCmd")
        if fullCheck or (len(self._saAmfCtDefTerminateCmdArgv) != 0):
            if len(self._saAmfCtDefTerminateCmdArgv) != len(other._saAmfCtDefTerminateCmdArgv):
                changedAttrs.append("saAmfCtDefTerminateCmdArgv")
            else:
                difflist = list(set(self._saAmfCtDefTerminateCmdArgv) ^ set(other._saAmfCtDefTerminateCmdArgv))
                if len(difflist) > 0:
                    changedAttrs.append("saAmfCtDefTerminateCmdArgv")
        if (fullCheck or self._saAmfCtDefRecoveryOnError != None) and other._saAmfCtDefRecoveryOnError != self._saAmfCtDefRecoveryOnError:
            changedAttrs.append("saAmfCtDefRecoveryOnError")
        if (fullCheck or self._saAmfCtDefQuiescingCompleteTimeout != None) and other._saAmfCtDefQuiescingCompleteTimeout != self._saAmfCtDefQuiescingCompleteTimeout:
            changedAttrs.append("saAmfCtDefQuiescingCompleteTimeout")
        if (fullCheck or self._saAmfCtDefInstantiationLevel != None) and other._saAmfCtDefInstantiationLevel != self._saAmfCtDefInstantiationLevel:
            changedAttrs.append("saAmfCtDefInstantiationLevel")
        if fullCheck or (len(self._saAmfCtDefInstantiateCmdArgv) != 0):
            if len(self._saAmfCtDefInstantiateCmdArgv) != len(other._saAmfCtDefInstantiateCmdArgv):
                changedAttrs.append("saAmfCtDefInstantiateCmdArgv")
            else:
                difflist = list(set(self._saAmfCtDefInstantiateCmdArgv) ^ set(other._saAmfCtDefInstantiateCmdArgv))
                if len(difflist) > 0:
                    changedAttrs.append("saAmfCtDefInstantiateCmdArgv")
        if (fullCheck or self._saAmfCtDefDisableRestart != None) and other._saAmfCtDefDisableRestart != self._saAmfCtDefDisableRestart:
            changedAttrs.append("saAmfCtDefDisableRestart")
        if fullCheck or (len(self._saAmfCtDefCmdEnv) != 0):
            if len(self._saAmfCtDefCmdEnv) != len(other._saAmfCtDefCmdEnv):
                changedAttrs.append("saAmfCtDefCmdEnv")
            else:
                difflist = list(set(self._saAmfCtDefCmdEnv) ^ set(other._saAmfCtDefCmdEnv))
                if len(difflist) > 0:
                    changedAttrs.append("saAmfCtDefCmdEnv")
        if fullCheck or (len(self._saAmfCtDefCleanupCmdArgv) != 0):
            if len(self._saAmfCtDefCleanupCmdArgv) != len(other._saAmfCtDefCleanupCmdArgv):
                changedAttrs.append("saAmfCtDefCleanupCmdArgv")
            else:
                difflist = list(set(self._saAmfCtDefCleanupCmdArgv) ^ set(other._saAmfCtDefCleanupCmdArgv))
                if len(difflist) > 0:
                    changedAttrs.append("saAmfCtDefCleanupCmdArgv")
        if (fullCheck or self._saAmfCtDefClcCliTimeout != None) and other._saAmfCtDefClcCliTimeout != self._saAmfCtDefClcCliTimeout:
            changedAttrs.append("saAmfCtDefClcCliTimeout")
        if (fullCheck or self._saAmfCtDefCallbackTimeout != None) and other._saAmfCtDefCallbackTimeout != self._saAmfCtDefCallbackTimeout:
            changedAttrs.append("saAmfCtDefCallbackTimeout")
        if fullCheck or (len(self._saAmfCtDefAmStopCmdArgv) != 0):
            if len(self._saAmfCtDefAmStopCmdArgv) != len(other._saAmfCtDefAmStopCmdArgv):
                changedAttrs.append("saAmfCtDefAmStopCmdArgv")
            else:
                difflist = list(set(self._saAmfCtDefAmStopCmdArgv) ^ set(other._saAmfCtDefAmStopCmdArgv))
                if len(difflist) > 0:
                    changedAttrs.append("saAmfCtDefAmStopCmdArgv")
        if fullCheck or (len(self._saAmfCtDefAmStartCmdArgv) != 0):
            if len(self._saAmfCtDefAmStartCmdArgv) != len(other._saAmfCtDefAmStartCmdArgv):
                changedAttrs.append("saAmfCtDefAmStartCmdArgv")
            else:
                difflist = list(set(self._saAmfCtDefAmStartCmdArgv) ^ set(other._saAmfCtDefAmStartCmdArgv))
                if len(difflist) > 0:
                    changedAttrs.append("saAmfCtDefAmStartCmdArgv")
        if (fullCheck or self._saAmfCtCompCategory != None) and other._saAmfCtCompCategory != self._saAmfCtCompCategory:
            changedAttrs.append("saAmfCtCompCategory")
        if (fullCheck or self._osafAmfCtRelPathHcCmd != None) and other._osafAmfCtRelPathHcCmd != self._osafAmfCtRelPathHcCmd:
            if other._dn != self._dn:
                changedAttrs.append("osafAmfCtRelPathHcCmd")
        if fullCheck or (len(self._osafAmfCtDefHcCmdArgv) != 0):
            if len(self._osafAmfCtDefHcCmdArgv) != len(other._osafAmfCtDefHcCmdArgv):
                changedAttrs.append("osafAmfCtDefHcCmdArgv")
            else:
                difflist = list(set(self._osafAmfCtDefHcCmdArgv) ^ set(other._osafAmfCtDefHcCmdArgv))
                if len(difflist) > 0:
                    changedAttrs.append("osafAmfCtDefHcCmdArgv")
        if (fullCheck or self._SaImmAttrImplementerName != None) and other._SaImmAttrImplementerName != self._SaImmAttrImplementerName:
            changedAttrs.append("SaImmAttrImplementerName")
        if (fullCheck or self._SaImmAttrClassName != None) and other._SaImmAttrClassName != self._SaImmAttrClassName:
            changedAttrs.append("SaImmAttrClassName")
        if (fullCheck or self._SaImmAttrAdminOwnerName != None) and other._SaImmAttrAdminOwnerName != self._SaImmAttrAdminOwnerName:
            changedAttrs.append("SaImmAttrAdminOwnerName")
        return changedAttrs

    def parseXML(self, node):
        dns = node.getElementsByTagName("dn")
        if len(dns) != 1:
            error("object has " + str(len(dns)) + " dn(s) but it should have one")
        self._dn = dns[0].childNodes[0].nodeValue
        for attribute in node.getElementsByTagName("attr"):
            names = attribute.getElementsByTagName("name")
            if len(names) != 1:
                error("object attribute has " + str(len(names)) + " name(s) but it should have one")
            name = names[0].childNodes[0].nodeValue
            setFunc = None
            if name == "SaImmAttrImplementerName":
                continue
            elif name == "SaImmAttrAdminOwnerName":
                continue
            elif name == "SaImmAttrClassName":
                continue
            elif name == "saAmfCtSwBundle":
                setFunc = self.setsaAmfCtSwBundle
            elif name == "saAmfCtRelPathTerminateCmd":
                setFunc = self.setsaAmfCtRelPathTerminateCmd
            elif name == "saAmfCtRelPathInstantiateCmd":
                setFunc = self.setsaAmfCtRelPathInstantiateCmd
            elif name == "saAmfCtRelPathCleanupCmd":
                setFunc = self.setsaAmfCtRelPathCleanupCmd
            elif name == "saAmfCtRelPathAmStopCmd":
                setFunc = self.setsaAmfCtRelPathAmStopCmd
            elif name == "saAmfCtRelPathAmStartCmd":
                setFunc = self.setsaAmfCtRelPathAmStartCmd
            elif name == "saAmfCtDefTerminateCmdArgv":
                setFunc = self.addTosaAmfCtDefTerminateCmdArgv
            elif name == "saAmfCtDefRecoveryOnError":
                setFunc = self.setsaAmfCtDefRecoveryOnError
            elif name == "saAmfCtDefQuiescingCompleteTimeout":
                setFunc = self.setsaAmfCtDefQuiescingCompleteTimeout
            elif name == "saAmfCtDefInstantiationLevel":
                setFunc = self.setsaAmfCtDefInstantiationLevel
            elif name == "saAmfCtDefInstantiateCmdArgv":
                setFunc = self.addTosaAmfCtDefInstantiateCmdArgv
            elif name == "saAmfCtDefDisableRestart":
                setFunc = self.setsaAmfCtDefDisableRestart
            elif name == "saAmfCtDefCmdEnv":
                setFunc = self.addTosaAmfCtDefCmdEnv
            elif name == "saAmfCtDefCleanupCmdArgv":
                setFunc = self.addTosaAmfCtDefCleanupCmdArgv
            elif name == "saAmfCtDefClcCliTimeout":
                setFunc = self.setsaAmfCtDefClcCliTimeout
            elif name == "saAmfCtDefCallbackTimeout":
                setFunc = self.setsaAmfCtDefCallbackTimeout
            elif name == "saAmfCtDefAmStopCmdArgv":
                setFunc = self.addTosaAmfCtDefAmStopCmdArgv
            elif name == "saAmfCtDefAmStartCmdArgv":
                setFunc = self.addTosaAmfCtDefAmStartCmdArgv
            elif name == "saAmfCtCompCategory":
                setFunc = self.setsaAmfCtCompCategory
            elif name == "osafAmfCtRelPathHcCmd":
                setFunc = self.setosafAmfCtRelPathHcCmd
            elif name == "osafAmfCtDefHcCmdArgv":
                setFunc = self.addToosafAmfCtDefHcCmdArgv
            elif name == "SaImmAttrImplementerName":
                setFunc = self.setSaImmAttrImplementerName
            elif name == "SaImmAttrClassName":
                setFunc = self.setSaImmAttrClassName
            elif name == "SaImmAttrAdminOwnerName":
                setFunc = self.setSaImmAttrAdminOwnerName
            elif name.startswith("osaf"):
                continue # ignore OpenSAF specific attributes
            else:
                error("unknown attribute called " + name + " defined in object " + self._dn)
            for value in attribute.getElementsByTagName("value"):
                setFunc(value.childNodes[0].nodeValue)

    def writeXML(self, parent, doc):
        obj = doc.createElement("object")
        parent.appendChild(obj)
        obj.setAttribute("class", "SaAmfCompType")
        dn = doc.createElement("dn")
        obj.appendChild(dn)
        dn.appendChild(doc.createTextNode(self._dn))
        ImmHelper.writeSingleAttribute("saAmfCtSwBundle", self._saAmfCtSwBundle, doc, obj)
        ImmHelper.writeSingleAttribute("saAmfCtRelPathTerminateCmd", self._saAmfCtRelPathTerminateCmd, doc, obj)
        ImmHelper.writeSingleAttribute("saAmfCtRelPathInstantiateCmd", self._saAmfCtRelPathInstantiateCmd, doc, obj)
        ImmHelper.writeSingleAttribute("saAmfCtRelPathCleanupCmd", self._saAmfCtRelPathCleanupCmd, doc, obj)
        ImmHelper.writeSingleAttribute("saAmfCtRelPathAmStopCmd", self._saAmfCtRelPathAmStopCmd, doc, obj)
        ImmHelper.writeSingleAttribute("saAmfCtRelPathAmStartCmd", self._saAmfCtRelPathAmStartCmd, doc, obj)
        ImmHelper.writeMultiAttributes("saAmfCtDefTerminateCmdArgv", self._saAmfCtDefTerminateCmdArgv, doc, obj)
        ImmHelper.writeSingleAttribute("saAmfCtDefRecoveryOnError", self._saAmfCtDefRecoveryOnError, doc, obj)
        ImmHelper.writeSingleAttribute("saAmfCtDefQuiescingCompleteTimeout", self._saAmfCtDefQuiescingCompleteTimeout, doc, obj)
        ImmHelper.writeSingleAttribute("saAmfCtDefInstantiationLevel", self._saAmfCtDefInstantiationLevel, doc, obj)
        ImmHelper.writeMultiAttributes("saAmfCtDefInstantiateCmdArgv", self._saAmfCtDefInstantiateCmdArgv, doc, obj)
        ImmHelper.writeSingleAttribute("saAmfCtDefDisableRestart", self._saAmfCtDefDisableRestart, doc, obj)
        ImmHelper.writeMultiAttributes("saAmfCtDefCmdEnv", self._saAmfCtDefCmdEnv, doc, obj)
        ImmHelper.writeMultiAttributes("saAmfCtDefCleanupCmdArgv", self._saAmfCtDefCleanupCmdArgv, doc, obj)
        ImmHelper.writeSingleAttribute("saAmfCtDefClcCliTimeout", self._saAmfCtDefClcCliTimeout, doc, obj)
        ImmHelper.writeSingleAttribute("saAmfCtDefCallbackTimeout", self._saAmfCtDefCallbackTimeout, doc, obj)
        ImmHelper.writeMultiAttributes("saAmfCtDefAmStopCmdArgv", self._saAmfCtDefAmStopCmdArgv, doc, obj)
        ImmHelper.writeMultiAttributes("saAmfCtDefAmStartCmdArgv", self._saAmfCtDefAmStartCmdArgv, doc, obj)
        ImmHelper.writeSingleAttribute("saAmfCtCompCategory", self._saAmfCtCompCategory, doc, obj)
        ImmHelper.writeSingleAttribute("osafAmfCtRelPathHcCmd", self._osafAmfCtRelPathHcCmd, doc, obj)
        ImmHelper.writeMultiAttributes("osafAmfCtDefHcCmdArgv", self._osafAmfCtDefHcCmdArgv, doc, obj)
        ImmHelper.writeSingleAttribute("SaImmAttrImplementerName", self._SaImmAttrImplementerName, doc, obj)
        ImmHelper.writeSingleAttribute("SaImmAttrClassName", self._SaImmAttrClassName, doc, obj)
        ImmHelper.writeSingleAttribute("SaImmAttrAdminOwnerName", self._SaImmAttrAdminOwnerName, doc, obj)


class SaAmfCompGlobalAttributes(object):
    def __init__(self):
        self._dn = None
        self._saAmfNumMaxInstantiateWithoutDelay = None
        self._saAmfNumMaxInstantiateWithDelay = None
        self._saAmfNumMaxAmStopAttempts = None
        self._saAmfNumMaxAmStartAttempts = None
        self._saAmfDelayBetweenInstantiateAttempts = None
        self._SaImmAttrImplementerName = None
        self._SaImmAttrClassName = None
        self._SaImmAttrAdminOwnerName = None

    @staticmethod
    def createDn(name, parentDn = None):
        if parentDn == None:
            parentDn = ""
        else:
            parentDn = "," + parentDn
        return "safRdn=" + ImmHelper.escapeName(name) + parentDn

    def getDn(self):
        return self._dn

    def getName(self):
        return ImmHelper.getName(self._dn)

    def getRdn(self):
        return ImmHelper.getRdn(self._dn)

    def getParentDn(self):
        return ImmHelper.getParentDn(self._dn)

    def createObjectInCampaign(self, campaign):
        parentDn = self.getParentDn()
        if parentDn == "":
            parentDn = "="
        campaign.beginCreate("SaAmfCompGlobalAttributes", parentDn)
        campaign.addAttribute("safRdn", "SA_IMM_ATTR_SASTRINGT", self.getRdn())
        if self._saAmfNumMaxInstantiateWithoutDelay != None:
            campaign.addAttribute("saAmfNumMaxInstantiateWithoutDelay", "SA_IMM_ATTR_SAUINT32T", self._saAmfNumMaxInstantiateWithoutDelay)
        if self._saAmfNumMaxInstantiateWithDelay != None:
            campaign.addAttribute("saAmfNumMaxInstantiateWithDelay", "SA_IMM_ATTR_SAUINT32T", self._saAmfNumMaxInstantiateWithDelay)
        if self._saAmfNumMaxAmStopAttempts != None:
            campaign.addAttribute("saAmfNumMaxAmStopAttempts", "SA_IMM_ATTR_SAUINT32T", self._saAmfNumMaxAmStopAttempts)
        if self._saAmfNumMaxAmStartAttempts != None:
            campaign.addAttribute("saAmfNumMaxAmStartAttempts", "SA_IMM_ATTR_SAUINT32T", self._saAmfNumMaxAmStartAttempts)
        if self._saAmfDelayBetweenInstantiateAttempts != None:
            campaign.addAttribute("saAmfDelayBetweenInstantiateAttempts", "SA_IMM_ATTR_SATIMET", self._saAmfDelayBetweenInstantiateAttempts)
        if self._SaImmAttrImplementerName != None:
            campaign.addAttribute("SaImmAttrImplementerName", "SA_IMM_ATTR_SASTRINGT", self._SaImmAttrImplementerName)
        if self._SaImmAttrClassName != None:
            campaign.addAttribute("SaImmAttrClassName", "SA_IMM_ATTR_SASTRINGT", self._SaImmAttrClassName)
        if self._SaImmAttrAdminOwnerName != None:
            campaign.addAttribute("SaImmAttrAdminOwnerName", "SA_IMM_ATTR_SASTRINGT", self._SaImmAttrAdminOwnerName)
        campaign.endCreate()

    def getsaAmfNumMaxInstantiateWithoutDelay(self):
        ImmHelper.validateSingle(self._saAmfNumMaxInstantiateWithoutDelay, self._dn, "saAmfNumMaxInstantiateWithoutDelay")
        return self._saAmfNumMaxInstantiateWithoutDelay

    def getsaAmfNumMaxInstantiateWithDelay(self):
        ImmHelper.validateSingle(self._saAmfNumMaxInstantiateWithDelay, self._dn, "saAmfNumMaxInstantiateWithDelay")
        return self._saAmfNumMaxInstantiateWithDelay

    def getsaAmfNumMaxAmStopAttempts(self):
        ImmHelper.validateSingle(self._saAmfNumMaxAmStopAttempts, self._dn, "saAmfNumMaxAmStopAttempts")
        return self._saAmfNumMaxAmStopAttempts

    def getsaAmfNumMaxAmStartAttempts(self):
        ImmHelper.validateSingle(self._saAmfNumMaxAmStartAttempts, self._dn, "saAmfNumMaxAmStartAttempts")
        return self._saAmfNumMaxAmStartAttempts

    def getsaAmfDelayBetweenInstantiateAttempts(self):
        ImmHelper.validateSingle(self._saAmfDelayBetweenInstantiateAttempts, self._dn, "saAmfDelayBetweenInstantiateAttempts")
        return self._saAmfDelayBetweenInstantiateAttempts

    def getSaImmAttrImplementerName(self):
        ImmHelper.validateSingle(self._SaImmAttrImplementerName, self._dn, "SaImmAttrImplementerName")
        return self._SaImmAttrImplementerName

    def getSaImmAttrClassName(self):
        ImmHelper.validateSingle(self._SaImmAttrClassName, self._dn, "SaImmAttrClassName")
        return self._SaImmAttrClassName

    def getSaImmAttrAdminOwnerName(self):
        ImmHelper.validateSingle(self._SaImmAttrAdminOwnerName, self._dn, "SaImmAttrAdminOwnerName")
        return self._SaImmAttrAdminOwnerName

    def getsaAmfNumMaxInstantiateWithoutDelay_unsafe(self):
        return self._saAmfNumMaxInstantiateWithoutDelay

    def getsaAmfNumMaxInstantiateWithDelay_unsafe(self):
        return self._saAmfNumMaxInstantiateWithDelay

    def getsaAmfNumMaxAmStopAttempts_unsafe(self):
        return self._saAmfNumMaxAmStopAttempts

    def getsaAmfNumMaxAmStartAttempts_unsafe(self):
        return self._saAmfNumMaxAmStartAttempts

    def getsaAmfDelayBetweenInstantiateAttempts_unsafe(self):
        return self._saAmfDelayBetweenInstantiateAttempts

    def getSaImmAttrImplementerName_unsafe(self):
        return self._SaImmAttrImplementerName

    def getSaImmAttrClassName_unsafe(self):
        return self._SaImmAttrClassName

    def getSaImmAttrAdminOwnerName_unsafe(self):
        return self._SaImmAttrAdminOwnerName

    def setsaAmfNumMaxInstantiateWithoutDelay(self, value):
        ImmHelper.validateUint32(value, self._dn, "saAmfNumMaxInstantiateWithoutDelay")
        value = str(value)
        self._saAmfNumMaxInstantiateWithoutDelay = value

    def setsaAmfNumMaxInstantiateWithDelay(self, value):
        ImmHelper.validateUint32(value, self._dn, "saAmfNumMaxInstantiateWithDelay")
        value = str(value)
        self._saAmfNumMaxInstantiateWithDelay = value

    def setsaAmfNumMaxAmStopAttempts(self, value):
        ImmHelper.validateUint32(value, self._dn, "saAmfNumMaxAmStopAttempts")
        value = str(value)
        self._saAmfNumMaxAmStopAttempts = value

    def setsaAmfNumMaxAmStartAttempts(self, value):
        ImmHelper.validateUint32(value, self._dn, "saAmfNumMaxAmStartAttempts")
        value = str(value)
        self._saAmfNumMaxAmStartAttempts = value

    def setsaAmfDelayBetweenInstantiateAttempts(self, value):
        ImmHelper.validateTime(value, self._dn, "saAmfDelayBetweenInstantiateAttempts")
        value = str(value)
        self._saAmfDelayBetweenInstantiateAttempts = value

    def setSaImmAttrImplementerName(self, value):
        ImmHelper.validateString(value, self._dn, "SaImmAttrImplementerName")
        self._SaImmAttrImplementerName = value

    def setSaImmAttrClassName(self, value):
        ImmHelper.validateString(value, self._dn, "SaImmAttrClassName")
        self._SaImmAttrClassName = value

    def setSaImmAttrAdminOwnerName(self, value):
        ImmHelper.validateString(value, self._dn, "SaImmAttrAdminOwnerName")
        self._SaImmAttrAdminOwnerName = value

    def updateParams(self, params, canttouchthis):
        for (param, value) in params.items():
            if param in canttouchthis:
                error("Setting attribute " + param + " in object " + self.getDn() + " is not supported")
            if param == "saAmfNumMaxInstantiateWithoutDelay":
                self.setsaAmfNumMaxInstantiateWithoutDelay(value)
            elif param == "saAmfNumMaxInstantiateWithDelay":
                self.setsaAmfNumMaxInstantiateWithDelay(value)
            elif param == "saAmfNumMaxAmStopAttempts":
                self.setsaAmfNumMaxAmStopAttempts(value)
            elif param == "saAmfNumMaxAmStartAttempts":
                self.setsaAmfNumMaxAmStartAttempts(value)
            elif param == "saAmfDelayBetweenInstantiateAttempts":
                self.setsaAmfDelayBetweenInstantiateAttempts(value)
            else:
                error("Object " + self.getDn() + " has no attribute named " + param)

    def diff(self, other, fullCheck = False):
        changedAttrs = []
        if (fullCheck or self._saAmfNumMaxInstantiateWithoutDelay != None) and other._saAmfNumMaxInstantiateWithoutDelay != self._saAmfNumMaxInstantiateWithoutDelay:
            changedAttrs.append("saAmfNumMaxInstantiateWithoutDelay")
        if (fullCheck or self._saAmfNumMaxInstantiateWithDelay != None) and other._saAmfNumMaxInstantiateWithDelay != self._saAmfNumMaxInstantiateWithDelay:
            changedAttrs.append("saAmfNumMaxInstantiateWithDelay")
        if (fullCheck or self._saAmfNumMaxAmStopAttempts != None) and other._saAmfNumMaxAmStopAttempts != self._saAmfNumMaxAmStopAttempts:
            changedAttrs.append("saAmfNumMaxAmStopAttempts")
        if (fullCheck or self._saAmfNumMaxAmStartAttempts != None) and other._saAmfNumMaxAmStartAttempts != self._saAmfNumMaxAmStartAttempts:
            changedAttrs.append("saAmfNumMaxAmStartAttempts")
        if (fullCheck or self._saAmfDelayBetweenInstantiateAttempts != None) and other._saAmfDelayBetweenInstantiateAttempts != self._saAmfDelayBetweenInstantiateAttempts:
            changedAttrs.append("saAmfDelayBetweenInstantiateAttempts")
        if (fullCheck or self._SaImmAttrImplementerName != None) and other._SaImmAttrImplementerName != self._SaImmAttrImplementerName:
            changedAttrs.append("SaImmAttrImplementerName")
        if (fullCheck or self._SaImmAttrClassName != None) and other._SaImmAttrClassName != self._SaImmAttrClassName:
            changedAttrs.append("SaImmAttrClassName")
        if (fullCheck or self._SaImmAttrAdminOwnerName != None) and other._SaImmAttrAdminOwnerName != self._SaImmAttrAdminOwnerName:
            changedAttrs.append("SaImmAttrAdminOwnerName")
        return changedAttrs

    def parseXML(self, node):
        dns = node.getElementsByTagName("dn")
        if len(dns) != 1:
            error("object has " + str(len(dns)) + " dn(s) but it should have one")
        self._dn = dns[0].childNodes[0].nodeValue
        for attribute in node.getElementsByTagName("attr"):
            names = attribute.getElementsByTagName("name")
            if len(names) != 1:
                error("object attribute has " + str(len(names)) + " name(s) but it should have one")
            name = names[0].childNodes[0].nodeValue
            setFunc = None
            if name == "SaImmAttrImplementerName":
                continue
            elif name == "SaImmAttrAdminOwnerName":
                continue
            elif name == "SaImmAttrClassName":
                continue
            elif name == "saAmfNumMaxInstantiateWithoutDelay":
                setFunc = self.setsaAmfNumMaxInstantiateWithoutDelay
            elif name == "saAmfNumMaxInstantiateWithDelay":
                setFunc = self.setsaAmfNumMaxInstantiateWithDelay
            elif name == "saAmfNumMaxAmStopAttempts":
                setFunc = self.setsaAmfNumMaxAmStopAttempts
            elif name == "saAmfNumMaxAmStartAttempts":
                setFunc = self.setsaAmfNumMaxAmStartAttempts
            elif name == "saAmfDelayBetweenInstantiateAttempts":
                setFunc = self.setsaAmfDelayBetweenInstantiateAttempts
            elif name == "SaImmAttrImplementerName":
                setFunc = self.setSaImmAttrImplementerName
            elif name == "SaImmAttrClassName":
                setFunc = self.setSaImmAttrClassName
            elif name == "SaImmAttrAdminOwnerName":
                setFunc = self.setSaImmAttrAdminOwnerName
            elif name.startswith("osaf"):
                continue # ignore OpenSAF specific attributes
            else:
                error("unknown attribute called " + name + " defined in object " + self._dn)
            for value in attribute.getElementsByTagName("value"):
                setFunc(value.childNodes[0].nodeValue)

    def writeXML(self, parent, doc):
        obj = doc.createElement("object")
        parent.appendChild(obj)
        obj.setAttribute("class", "SaAmfCompGlobalAttributes")
        dn = doc.createElement("dn")
        obj.appendChild(dn)
        dn.appendChild(doc.createTextNode(self._dn))
        ImmHelper.writeSingleAttribute("saAmfNumMaxInstantiateWithoutDelay", self._saAmfNumMaxInstantiateWithoutDelay, doc, obj)
        ImmHelper.writeSingleAttribute("saAmfNumMaxInstantiateWithDelay", self._saAmfNumMaxInstantiateWithDelay, doc, obj)
        ImmHelper.writeSingleAttribute("saAmfNumMaxAmStopAttempts", self._saAmfNumMaxAmStopAttempts, doc, obj)
        ImmHelper.writeSingleAttribute("saAmfNumMaxAmStartAttempts", self._saAmfNumMaxAmStartAttempts, doc, obj)
        ImmHelper.writeSingleAttribute("saAmfDelayBetweenInstantiateAttempts", self._saAmfDelayBetweenInstantiateAttempts, doc, obj)
        ImmHelper.writeSingleAttribute("SaImmAttrImplementerName", self._SaImmAttrImplementerName, doc, obj)
        ImmHelper.writeSingleAttribute("SaImmAttrClassName", self._SaImmAttrClassName, doc, obj)
        ImmHelper.writeSingleAttribute("SaImmAttrAdminOwnerName", self._SaImmAttrAdminOwnerName, doc, obj)


class SaAmfCompCsType(object):
    def __init__(self):
        self._dn = None
        self._saAmfCompNumMaxStandbyCSIs = None
        self._saAmfCompNumMaxActiveCSIs = None
        self._saAmfCompNumCurrStandbyCSIs = None
        self._saAmfCompNumCurrActiveCSIs = None
        self._saAmfCompAssignedCsi = None
        self._SaImmAttrImplementerName = None
        self._SaImmAttrClassName = None
        self._SaImmAttrAdminOwnerName = None

    @staticmethod
    def createDn(name, parentDn = None):
        if parentDn == None:
            parentDn = ""
        else:
            parentDn = "," + parentDn
        return "safSupportedCsType=" + ImmHelper.escapeName(name) + parentDn

    def getDn(self):
        return self._dn

    def getName(self):
        return ImmHelper.getName(self._dn)

    def getRdn(self):
        return ImmHelper.getRdn(self._dn)

    def getParentDn(self):
        return ImmHelper.getParentDn(self._dn)

    def createObjectInCampaign(self, campaign):
        parentDn = self.getParentDn()
        if parentDn == "":
            parentDn = "="
        campaign.beginCreate("SaAmfCompCsType", parentDn)
        campaign.addAttribute("safSupportedCsType", "SA_IMM_ATTR_SANAMET", self.getRdn())
        if self._saAmfCompNumMaxStandbyCSIs != None:
            campaign.addAttribute("saAmfCompNumMaxStandbyCSIs", "SA_IMM_ATTR_SAUINT32T", self._saAmfCompNumMaxStandbyCSIs)
        if self._saAmfCompNumMaxActiveCSIs != None:
            campaign.addAttribute("saAmfCompNumMaxActiveCSIs", "SA_IMM_ATTR_SAUINT32T", self._saAmfCompNumMaxActiveCSIs)
        if self._SaImmAttrImplementerName != None:
            campaign.addAttribute("SaImmAttrImplementerName", "SA_IMM_ATTR_SASTRINGT", self._SaImmAttrImplementerName)
        if self._SaImmAttrClassName != None:
            campaign.addAttribute("SaImmAttrClassName", "SA_IMM_ATTR_SASTRINGT", self._SaImmAttrClassName)
        if self._SaImmAttrAdminOwnerName != None:
            campaign.addAttribute("SaImmAttrAdminOwnerName", "SA_IMM_ATTR_SASTRINGT", self._SaImmAttrAdminOwnerName)
        campaign.endCreate()

    def getsaAmfCompNumMaxStandbyCSIs(self):
        ImmHelper.validateSingle(self._saAmfCompNumMaxStandbyCSIs, self._dn, "saAmfCompNumMaxStandbyCSIs")
        return self._saAmfCompNumMaxStandbyCSIs

    def getsaAmfCompNumMaxActiveCSIs(self):
        ImmHelper.validateSingle(self._saAmfCompNumMaxActiveCSIs, self._dn, "saAmfCompNumMaxActiveCSIs")
        return self._saAmfCompNumMaxActiveCSIs

    def getsaAmfCompNumCurrStandbyCSIs(self):
        ImmHelper.validateSingle(self._saAmfCompNumCurrStandbyCSIs, self._dn, "saAmfCompNumCurrStandbyCSIs")
        return self._saAmfCompNumCurrStandbyCSIs

    def getsaAmfCompNumCurrActiveCSIs(self):
        ImmHelper.validateSingle(self._saAmfCompNumCurrActiveCSIs, self._dn, "saAmfCompNumCurrActiveCSIs")
        return self._saAmfCompNumCurrActiveCSIs

    def getsaAmfCompAssignedCsi(self):
        ImmHelper.validateSingle(self._saAmfCompAssignedCsi, self._dn, "saAmfCompAssignedCsi")
        return self._saAmfCompAssignedCsi

    def getSaImmAttrImplementerName(self):
        ImmHelper.validateSingle(self._SaImmAttrImplementerName, self._dn, "SaImmAttrImplementerName")
        return self._SaImmAttrImplementerName

    def getSaImmAttrClassName(self):
        ImmHelper.validateSingle(self._SaImmAttrClassName, self._dn, "SaImmAttrClassName")
        return self._SaImmAttrClassName

    def getSaImmAttrAdminOwnerName(self):
        ImmHelper.validateSingle(self._SaImmAttrAdminOwnerName, self._dn, "SaImmAttrAdminOwnerName")
        return self._SaImmAttrAdminOwnerName

    def getsaAmfCompNumMaxStandbyCSIs_unsafe(self):
        return self._saAmfCompNumMaxStandbyCSIs

    def getsaAmfCompNumMaxActiveCSIs_unsafe(self):
        return self._saAmfCompNumMaxActiveCSIs

    def getsaAmfCompNumCurrStandbyCSIs_unsafe(self):
        return self._saAmfCompNumCurrStandbyCSIs

    def getsaAmfCompNumCurrActiveCSIs_unsafe(self):
        return self._saAmfCompNumCurrActiveCSIs

    def getsaAmfCompAssignedCsi_unsafe(self):
        return self._saAmfCompAssignedCsi

    def getSaImmAttrImplementerName_unsafe(self):
        return self._SaImmAttrImplementerName

    def getSaImmAttrClassName_unsafe(self):
        return self._SaImmAttrClassName

    def getSaImmAttrAdminOwnerName_unsafe(self):
        return self._SaImmAttrAdminOwnerName

    def setsaAmfCompNumMaxStandbyCSIs(self, value):
        ImmHelper.validateUint32(value, self._dn, "saAmfCompNumMaxStandbyCSIs")
        value = str(value)
        self._saAmfCompNumMaxStandbyCSIs = value

    def setsaAmfCompNumMaxActiveCSIs(self, value):
        ImmHelper.validateUint32(value, self._dn, "saAmfCompNumMaxActiveCSIs")
        value = str(value)
        self._saAmfCompNumMaxActiveCSIs = value

    def setsaAmfCompNumCurrStandbyCSIs(self, value):
        ImmHelper.validateUint32(value, self._dn, "saAmfCompNumCurrStandbyCSIs")
        value = str(value)
        self._saAmfCompNumCurrStandbyCSIs = value

    def setsaAmfCompNumCurrActiveCSIs(self, value):
        ImmHelper.validateUint32(value, self._dn, "saAmfCompNumCurrActiveCSIs")
        value = str(value)
        self._saAmfCompNumCurrActiveCSIs = value

    def setsaAmfCompAssignedCsi(self, value):
        ImmHelper.validateName(value, self._dn, "saAmfCompAssignedCsi")
        self._saAmfCompAssignedCsi = value

    def setSaImmAttrImplementerName(self, value):
        ImmHelper.validateString(value, self._dn, "SaImmAttrImplementerName")
        self._SaImmAttrImplementerName = value

    def setSaImmAttrClassName(self, value):
        ImmHelper.validateString(value, self._dn, "SaImmAttrClassName")
        self._SaImmAttrClassName = value

    def setSaImmAttrAdminOwnerName(self, value):
        ImmHelper.validateString(value, self._dn, "SaImmAttrAdminOwnerName")
        self._SaImmAttrAdminOwnerName = value

    def updateParams(self, params, canttouchthis):
        for (param, value) in params.items():
            if param in canttouchthis:
                error("Setting attribute " + param + " in object " + self.getDn() + " is not supported")
            if param == "saAmfCompNumMaxStandbyCSIs":
                self.setsaAmfCompNumMaxStandbyCSIs(value)
            elif param == "saAmfCompNumMaxActiveCSIs":
                self.setsaAmfCompNumMaxActiveCSIs(value)
            else:
                error("Object " + self.getDn() + " has no attribute named " + param)

    def diff(self, other, fullCheck = False):
        changedAttrs = []
        if (fullCheck or self._saAmfCompNumMaxStandbyCSIs != None) and other._saAmfCompNumMaxStandbyCSIs != self._saAmfCompNumMaxStandbyCSIs:
            changedAttrs.append("saAmfCompNumMaxStandbyCSIs")
        if (fullCheck or self._saAmfCompNumMaxActiveCSIs != None) and other._saAmfCompNumMaxActiveCSIs != self._saAmfCompNumMaxActiveCSIs:
            changedAttrs.append("saAmfCompNumMaxActiveCSIs")
        if (fullCheck or self._SaImmAttrImplementerName != None) and other._SaImmAttrImplementerName != self._SaImmAttrImplementerName:
            changedAttrs.append("SaImmAttrImplementerName")
        if (fullCheck or self._SaImmAttrClassName != None) and other._SaImmAttrClassName != self._SaImmAttrClassName:
            changedAttrs.append("SaImmAttrClassName")
        if (fullCheck or self._SaImmAttrAdminOwnerName != None) and other._SaImmAttrAdminOwnerName != self._SaImmAttrAdminOwnerName:
            changedAttrs.append("SaImmAttrAdminOwnerName")
        return changedAttrs

    def parseXML(self, node):
        dns = node.getElementsByTagName("dn")
        if len(dns) != 1:
            error("object has " + str(len(dns)) + " dn(s) but it should have one")
        self._dn = dns[0].childNodes[0].nodeValue
        for attribute in node.getElementsByTagName("attr"):
            names = attribute.getElementsByTagName("name")
            if len(names) != 1:
                error("object attribute has " + str(len(names)) + " name(s) but it should have one")
            name = names[0].childNodes[0].nodeValue
            setFunc = None
            if name == "SaImmAttrImplementerName":
                continue
            elif name == "SaImmAttrAdminOwnerName":
                continue
            elif name == "SaImmAttrClassName":
                continue
            elif name == "saAmfCompNumMaxStandbyCSIs":
                setFunc = self.setsaAmfCompNumMaxStandbyCSIs
            elif name == "saAmfCompNumMaxActiveCSIs":
                setFunc = self.setsaAmfCompNumMaxActiveCSIs
            elif name == "saAmfCompNumCurrStandbyCSIs":
                setFunc = self.setsaAmfCompNumCurrStandbyCSIs
            elif name == "saAmfCompNumCurrActiveCSIs":
                setFunc = self.setsaAmfCompNumCurrActiveCSIs
            elif name == "saAmfCompAssignedCsi":
                setFunc = self.setsaAmfCompAssignedCsi
            elif name == "SaImmAttrImplementerName":
                setFunc = self.setSaImmAttrImplementerName
            elif name == "SaImmAttrClassName":
                setFunc = self.setSaImmAttrClassName
            elif name == "SaImmAttrAdminOwnerName":
                setFunc = self.setSaImmAttrAdminOwnerName
            elif name.startswith("osaf"):
                continue # ignore OpenSAF specific attributes
            else:
                error("unknown attribute called " + name + " defined in object " + self._dn)
            for value in attribute.getElementsByTagName("value"):
                setFunc(value.childNodes[0].nodeValue)

    def writeXML(self, parent, doc):
        obj = doc.createElement("object")
        parent.appendChild(obj)
        obj.setAttribute("class", "SaAmfCompCsType")
        dn = doc.createElement("dn")
        obj.appendChild(dn)
        dn.appendChild(doc.createTextNode(self._dn))
        ImmHelper.writeSingleAttribute("saAmfCompNumMaxStandbyCSIs", self._saAmfCompNumMaxStandbyCSIs, doc, obj)
        ImmHelper.writeSingleAttribute("saAmfCompNumMaxActiveCSIs", self._saAmfCompNumMaxActiveCSIs, doc, obj)
        ImmHelper.writeSingleAttribute("saAmfCompNumCurrStandbyCSIs", self._saAmfCompNumCurrStandbyCSIs, doc, obj)
        ImmHelper.writeSingleAttribute("saAmfCompNumCurrActiveCSIs", self._saAmfCompNumCurrActiveCSIs, doc, obj)
        ImmHelper.writeSingleAttribute("saAmfCompAssignedCsi", self._saAmfCompAssignedCsi, doc, obj)
        ImmHelper.writeSingleAttribute("SaImmAttrImplementerName", self._SaImmAttrImplementerName, doc, obj)
        ImmHelper.writeSingleAttribute("SaImmAttrClassName", self._SaImmAttrClassName, doc, obj)
        ImmHelper.writeSingleAttribute("SaImmAttrAdminOwnerName", self._SaImmAttrAdminOwnerName, doc, obj)


class SaAmfCompBaseType(object):
    def __init__(self):
        self._dn = None
        self._SaImmAttrImplementerName = None
        self._SaImmAttrClassName = None
        self._SaImmAttrAdminOwnerName = None

    @staticmethod
    def createDn(name, parentDn = None):
        if parentDn == None:
            parentDn = ""
        else:
            parentDn = "," + parentDn
        return "safCompType=" + ImmHelper.escapeName(name) + parentDn

    def getDn(self):
        return self._dn

    def getName(self):
        return ImmHelper.getName(self._dn)

    def getRdn(self):
        return ImmHelper.getRdn(self._dn)

    def getParentDn(self):
        return ImmHelper.getParentDn(self._dn)

    def createObjectInCampaign(self, campaign):
        parentDn = self.getParentDn()
        if parentDn == "":
            parentDn = "="
        campaign.beginCreate("SaAmfCompBaseType", parentDn)
        campaign.addAttribute("safCompType", "SA_IMM_ATTR_SASTRINGT", self.getRdn())
        if self._SaImmAttrImplementerName != None:
            campaign.addAttribute("SaImmAttrImplementerName", "SA_IMM_ATTR_SASTRINGT", self._SaImmAttrImplementerName)
        if self._SaImmAttrClassName != None:
            campaign.addAttribute("SaImmAttrClassName", "SA_IMM_ATTR_SASTRINGT", self._SaImmAttrClassName)
        if self._SaImmAttrAdminOwnerName != None:
            campaign.addAttribute("SaImmAttrAdminOwnerName", "SA_IMM_ATTR_SASTRINGT", self._SaImmAttrAdminOwnerName)
        campaign.endCreate()

    def getSaImmAttrImplementerName(self):
        ImmHelper.validateSingle(self._SaImmAttrImplementerName, self._dn, "SaImmAttrImplementerName")
        return self._SaImmAttrImplementerName

    def getSaImmAttrClassName(self):
        ImmHelper.validateSingle(self._SaImmAttrClassName, self._dn, "SaImmAttrClassName")
        return self._SaImmAttrClassName

    def getSaImmAttrAdminOwnerName(self):
        ImmHelper.validateSingle(self._SaImmAttrAdminOwnerName, self._dn, "SaImmAttrAdminOwnerName")
        return self._SaImmAttrAdminOwnerName

    def getSaImmAttrImplementerName_unsafe(self):
        return self._SaImmAttrImplementerName

    def getSaImmAttrClassName_unsafe(self):
        return self._SaImmAttrClassName

    def getSaImmAttrAdminOwnerName_unsafe(self):
        return self._SaImmAttrAdminOwnerName

    def setSaImmAttrImplementerName(self, value):
        ImmHelper.validateString(value, self._dn, "SaImmAttrImplementerName")
        self._SaImmAttrImplementerName = value

    def setSaImmAttrClassName(self, value):
        ImmHelper.validateString(value, self._dn, "SaImmAttrClassName")
        self._SaImmAttrClassName = value

    def setSaImmAttrAdminOwnerName(self, value):
        ImmHelper.validateString(value, self._dn, "SaImmAttrAdminOwnerName")
        self._SaImmAttrAdminOwnerName = value

    def updateParams(self, params, canttouchthis):
        for (param, value) in params.items():
            if param in canttouchthis:
                error("Setting attribute " + param + " in object " + self.getDn() + " is not supported")
            else:
                error("Object " + self.getDn() + " has no attribute named " + param)

    def diff(self, other, fullCheck = False):
        changedAttrs = []
        if (fullCheck or self._SaImmAttrImplementerName != None) and other._SaImmAttrImplementerName != self._SaImmAttrImplementerName:
            changedAttrs.append("SaImmAttrImplementerName")
        if (fullCheck or self._SaImmAttrClassName != None) and other._SaImmAttrClassName != self._SaImmAttrClassName:
            changedAttrs.append("SaImmAttrClassName")
        if (fullCheck or self._SaImmAttrAdminOwnerName != None) and other._SaImmAttrAdminOwnerName != self._SaImmAttrAdminOwnerName:
            changedAttrs.append("SaImmAttrAdminOwnerName")
        return changedAttrs

    def parseXML(self, node):
        dns = node.getElementsByTagName("dn")
        if len(dns) != 1:
            error("object has " + str(len(dns)) + " dn(s) but it should have one")
        self._dn = dns[0].childNodes[0].nodeValue
        for attribute in node.getElementsByTagName("attr"):
            names = attribute.getElementsByTagName("name")
            if len(names) != 1:
                error("object attribute has " + str(len(names)) + " name(s) but it should have one")
            name = names[0].childNodes[0].nodeValue
            setFunc = None
            if name == "SaImmAttrImplementerName":
                continue
            elif name == "SaImmAttrAdminOwnerName":
                continue
            elif name == "SaImmAttrClassName":
                continue
            elif name == "SaImmAttrImplementerName":
                setFunc = self.setSaImmAttrImplementerName
            elif name == "SaImmAttrClassName":
                setFunc = self.setSaImmAttrClassName
            elif name == "SaImmAttrAdminOwnerName":
                setFunc = self.setSaImmAttrAdminOwnerName
            elif name.startswith("osaf"):
                continue # ignore OpenSAF specific attributes
            else:
                error("unknown attribute called " + name + " defined in object " + self._dn)
            for value in attribute.getElementsByTagName("value"):
                setFunc(value.childNodes[0].nodeValue)

    def writeXML(self, parent, doc):
        obj = doc.createElement("object")
        parent.appendChild(obj)
        obj.setAttribute("class", "SaAmfCompBaseType")
        dn = doc.createElement("dn")
        obj.appendChild(dn)
        dn.appendChild(doc.createTextNode(self._dn))
        ImmHelper.writeSingleAttribute("SaImmAttrImplementerName", self._SaImmAttrImplementerName, doc, obj)
        ImmHelper.writeSingleAttribute("SaImmAttrClassName", self._SaImmAttrClassName, doc, obj)
        ImmHelper.writeSingleAttribute("SaImmAttrAdminOwnerName", self._SaImmAttrAdminOwnerName, doc, obj)


class SaAmfComp(object):
    def __init__(self):
        self._dn = None
        self._saAmfCompType = None
        self._saAmfCompTerminateTimeout = None
        self._saAmfCompTerminateCmdArgv = []
        self._saAmfCompRestartCount = None
        self._saAmfCompRecoveryOnError = None
        self._saAmfCompReadinessState = None
        self._saAmfCompQuiescingCompleteTimeout = None
        self._saAmfCompProxyCsi = None
        self._saAmfCompPresenceState = None
        self._saAmfCompOperState = None
        self._saAmfCompNumMaxInstantiateWithoutDelay = None
        self._saAmfCompNumMaxInstantiateWithDelay = None
        self._saAmfCompNumMaxAmStopAttempts = None
        self._saAmfCompNumMaxAmStartAttempts = None
        self._saAmfCompInstantiationLevel = None
        self._saAmfCompInstantiateTimeout = None
        self._saAmfCompInstantiateCmdArgv = []
        self._saAmfCompDisableRestart = None
        self._saAmfCompDelayBetweenInstantiateAttempts = None
        self._saAmfCompCurrProxyName = None
        self._saAmfCompCurrProxiedNames = []
        self._saAmfCompContainerCsi = None
        self._saAmfCompCmdEnv = []
        self._saAmfCompCleanupTimeout = None
        self._saAmfCompCleanupCmdArgv = []
        self._saAmfCompCSISetCallbackTimeout = None
        self._saAmfCompCSIRmvCallbackTimeout = None
        self._saAmfCompAmStopTimeout = None
        self._saAmfCompAmStopCmdArgv = []
        self._saAmfCompAmStartTimeout = None
        self._saAmfCompAmStartCmdArgv = []
        self._osafAmfCompHcCmdArgv = []
        self._SaImmAttrImplementerName = None
        self._SaImmAttrClassName = None
        self._SaImmAttrAdminOwnerName = None

    @staticmethod
    def createDn(name, parentDn = None):
        if parentDn == None:
            parentDn = ""
        else:
            parentDn = "," + parentDn
        return "safComp=" + ImmHelper.escapeName(name) + parentDn

    def getDn(self):
        return self._dn

    def getName(self):
        return ImmHelper.getName(self._dn)

    def getRdn(self):
        return ImmHelper.getRdn(self._dn)

    def getParentDn(self):
        return ImmHelper.getParentDn(self._dn)

    def createObjectInCampaign(self, campaign):
        parentDn = self.getParentDn()
        if parentDn == "":
            parentDn = "="
        campaign.beginCreate("SaAmfComp", parentDn)
        campaign.addAttribute("safComp", "SA_IMM_ATTR_SASTRINGT", self.getRdn())
        if self._saAmfCompType != None:
            campaign.addAttribute("saAmfCompType", "SA_IMM_ATTR_SANAMET", self._saAmfCompType)
        if self._saAmfCompTerminateTimeout != None:
            campaign.addAttribute("saAmfCompTerminateTimeout", "SA_IMM_ATTR_SATIMET", self._saAmfCompTerminateTimeout)
        if len(self._saAmfCompTerminateCmdArgv) > 0:
            campaign.addAttribute("saAmfCompTerminateCmdArgv", "SA_IMM_ATTR_SASTRINGT", self._saAmfCompTerminateCmdArgv)
        if self._saAmfCompRecoveryOnError != None:
            campaign.addAttribute("saAmfCompRecoveryOnError", "SA_IMM_ATTR_SAUINT32T", self._saAmfCompRecoveryOnError)
        if self._saAmfCompQuiescingCompleteTimeout != None:
            campaign.addAttribute("saAmfCompQuiescingCompleteTimeout", "SA_IMM_ATTR_SATIMET", self._saAmfCompQuiescingCompleteTimeout)
        if self._saAmfCompProxyCsi != None:
            campaign.addAttribute("saAmfCompProxyCsi", "SA_IMM_ATTR_SANAMET", self._saAmfCompProxyCsi)
        if self._saAmfCompNumMaxInstantiateWithoutDelay != None:
            campaign.addAttribute("saAmfCompNumMaxInstantiateWithoutDelay", "SA_IMM_ATTR_SAUINT32T", self._saAmfCompNumMaxInstantiateWithoutDelay)
        if self._saAmfCompNumMaxInstantiateWithDelay != None:
            campaign.addAttribute("saAmfCompNumMaxInstantiateWithDelay", "SA_IMM_ATTR_SAUINT32T", self._saAmfCompNumMaxInstantiateWithDelay)
        if self._saAmfCompNumMaxAmStopAttempts != None:
            campaign.addAttribute("saAmfCompNumMaxAmStopAttempts", "SA_IMM_ATTR_SAUINT32T", self._saAmfCompNumMaxAmStopAttempts)
        if self._saAmfCompNumMaxAmStartAttempts != None:
            campaign.addAttribute("saAmfCompNumMaxAmStartAttempts", "SA_IMM_ATTR_SAUINT32T", self._saAmfCompNumMaxAmStartAttempts)
        if self._saAmfCompInstantiationLevel != None:
            campaign.addAttribute("saAmfCompInstantiationLevel", "SA_IMM_ATTR_SAUINT32T", self._saAmfCompInstantiationLevel)
        if self._saAmfCompInstantiateTimeout != None:
            campaign.addAttribute("saAmfCompInstantiateTimeout", "SA_IMM_ATTR_SATIMET", self._saAmfCompInstantiateTimeout)
        if len(self._saAmfCompInstantiateCmdArgv) > 0:
            campaign.addAttribute("saAmfCompInstantiateCmdArgv", "SA_IMM_ATTR_SASTRINGT", self._saAmfCompInstantiateCmdArgv)
        if self._saAmfCompDisableRestart != None:
            campaign.addAttribute("saAmfCompDisableRestart", "SA_IMM_ATTR_SAUINT32T", self._saAmfCompDisableRestart)
        if self._saAmfCompDelayBetweenInstantiateAttempts != None:
            campaign.addAttribute("saAmfCompDelayBetweenInstantiateAttempts", "SA_IMM_ATTR_SATIMET", self._saAmfCompDelayBetweenInstantiateAttempts)
        if self._saAmfCompContainerCsi != None:
            campaign.addAttribute("saAmfCompContainerCsi", "SA_IMM_ATTR_SANAMET", self._saAmfCompContainerCsi)
        if len(self._saAmfCompCmdEnv) > 0:
            campaign.addAttribute("saAmfCompCmdEnv", "SA_IMM_ATTR_SASTRINGT", self._saAmfCompCmdEnv)
        if self._saAmfCompCleanupTimeout != None:
            campaign.addAttribute("saAmfCompCleanupTimeout", "SA_IMM_ATTR_SATIMET", self._saAmfCompCleanupTimeout)
        if len(self._saAmfCompCleanupCmdArgv) > 0:
            campaign.addAttribute("saAmfCompCleanupCmdArgv", "SA_IMM_ATTR_SASTRINGT", self._saAmfCompCleanupCmdArgv)
        if self._saAmfCompCSISetCallbackTimeout != None:
            campaign.addAttribute("saAmfCompCSISetCallbackTimeout", "SA_IMM_ATTR_SATIMET", self._saAmfCompCSISetCallbackTimeout)
        if self._saAmfCompCSIRmvCallbackTimeout != None:
            campaign.addAttribute("saAmfCompCSIRmvCallbackTimeout", "SA_IMM_ATTR_SATIMET", self._saAmfCompCSIRmvCallbackTimeout)
        if self._saAmfCompAmStopTimeout != None:
            campaign.addAttribute("saAmfCompAmStopTimeout", "SA_IMM_ATTR_SATIMET", self._saAmfCompAmStopTimeout)
        if len(self._saAmfCompAmStopCmdArgv) > 0:
            campaign.addAttribute("saAmfCompAmStopCmdArgv", "SA_IMM_ATTR_SASTRINGT", self._saAmfCompAmStopCmdArgv)
        if self._saAmfCompAmStartTimeout != None:
            campaign.addAttribute("saAmfCompAmStartTimeout", "SA_IMM_ATTR_SATIMET", self._saAmfCompAmStartTimeout)
        if len(self._saAmfCompAmStartCmdArgv) > 0:
            campaign.addAttribute("saAmfCompAmStartCmdArgv", "SA_IMM_ATTR_SASTRINGT", self._saAmfCompAmStartCmdArgv)
        if len(self._osafAmfCompHcCmdArgv) > 0:
            campaign.addAttribute("osafAmfCompHcCmdArgv", "SA_IMM_ATTR_SASTRINGT", self._osafAmfCompHcCmdArgv)
        if self._SaImmAttrImplementerName != None:
            campaign.addAttribute("SaImmAttrImplementerName", "SA_IMM_ATTR_SASTRINGT", self._SaImmAttrImplementerName)
        if self._SaImmAttrClassName != None:
            campaign.addAttribute("SaImmAttrClassName", "SA_IMM_ATTR_SASTRINGT", self._SaImmAttrClassName)
        if self._SaImmAttrAdminOwnerName != None:
            campaign.addAttribute("SaImmAttrAdminOwnerName", "SA_IMM_ATTR_SASTRINGT", self._SaImmAttrAdminOwnerName)
        campaign.endCreate()

    def getsaAmfCompType(self):
        ImmHelper.validateSingle(self._saAmfCompType, self._dn, "saAmfCompType")
        return self._saAmfCompType

    def getsaAmfCompTerminateTimeout(self):
        ImmHelper.validateSingle(self._saAmfCompTerminateTimeout, self._dn, "saAmfCompTerminateTimeout")
        return self._saAmfCompTerminateTimeout

    def getsaAmfCompTerminateCmdArgv(self):
        return self._saAmfCompTerminateCmdArgv

    def getsaAmfCompRestartCount(self):
        ImmHelper.validateSingle(self._saAmfCompRestartCount, self._dn, "saAmfCompRestartCount")
        return self._saAmfCompRestartCount

    def getsaAmfCompRecoveryOnError(self):
        ImmHelper.validateSingle(self._saAmfCompRecoveryOnError, self._dn, "saAmfCompRecoveryOnError")
        return self._saAmfCompRecoveryOnError

    def getsaAmfCompReadinessState(self):
        ImmHelper.validateSingle(self._saAmfCompReadinessState, self._dn, "saAmfCompReadinessState")
        return self._saAmfCompReadinessState

    def getsaAmfCompQuiescingCompleteTimeout(self):
        ImmHelper.validateSingle(self._saAmfCompQuiescingCompleteTimeout, self._dn, "saAmfCompQuiescingCompleteTimeout")
        return self._saAmfCompQuiescingCompleteTimeout

    def getsaAmfCompProxyCsi(self):
        ImmHelper.validateSingle(self._saAmfCompProxyCsi, self._dn, "saAmfCompProxyCsi")
        return self._saAmfCompProxyCsi

    def getsaAmfCompPresenceState(self):
        ImmHelper.validateSingle(self._saAmfCompPresenceState, self._dn, "saAmfCompPresenceState")
        return self._saAmfCompPresenceState

    def getsaAmfCompOperState(self):
        ImmHelper.validateSingle(self._saAmfCompOperState, self._dn, "saAmfCompOperState")
        return self._saAmfCompOperState

    def getsaAmfCompNumMaxInstantiateWithoutDelay(self):
        ImmHelper.validateSingle(self._saAmfCompNumMaxInstantiateWithoutDelay, self._dn, "saAmfCompNumMaxInstantiateWithoutDelay")
        return self._saAmfCompNumMaxInstantiateWithoutDelay

    def getsaAmfCompNumMaxInstantiateWithDelay(self):
        ImmHelper.validateSingle(self._saAmfCompNumMaxInstantiateWithDelay, self._dn, "saAmfCompNumMaxInstantiateWithDelay")
        return self._saAmfCompNumMaxInstantiateWithDelay

    def getsaAmfCompNumMaxAmStopAttempts(self):
        ImmHelper.validateSingle(self._saAmfCompNumMaxAmStopAttempts, self._dn, "saAmfCompNumMaxAmStopAttempts")
        return self._saAmfCompNumMaxAmStopAttempts

    def getsaAmfCompNumMaxAmStartAttempts(self):
        ImmHelper.validateSingle(self._saAmfCompNumMaxAmStartAttempts, self._dn, "saAmfCompNumMaxAmStartAttempts")
        return self._saAmfCompNumMaxAmStartAttempts

    def getsaAmfCompInstantiationLevel(self):
        ImmHelper.validateSingle(self._saAmfCompInstantiationLevel, self._dn, "saAmfCompInstantiationLevel")
        return self._saAmfCompInstantiationLevel

    def getsaAmfCompInstantiateTimeout(self):
        ImmHelper.validateSingle(self._saAmfCompInstantiateTimeout, self._dn, "saAmfCompInstantiateTimeout")
        return self._saAmfCompInstantiateTimeout

    def getsaAmfCompInstantiateCmdArgv(self):
        return self._saAmfCompInstantiateCmdArgv

    def getsaAmfCompDisableRestart(self):
        ImmHelper.validateSingle(self._saAmfCompDisableRestart, self._dn, "saAmfCompDisableRestart")
        return self._saAmfCompDisableRestart

    def getsaAmfCompDelayBetweenInstantiateAttempts(self):
        ImmHelper.validateSingle(self._saAmfCompDelayBetweenInstantiateAttempts, self._dn, "saAmfCompDelayBetweenInstantiateAttempts")
        return self._saAmfCompDelayBetweenInstantiateAttempts

    def getsaAmfCompCurrProxyName(self):
        ImmHelper.validateSingle(self._saAmfCompCurrProxyName, self._dn, "saAmfCompCurrProxyName")
        return self._saAmfCompCurrProxyName

    def getsaAmfCompCurrProxiedNames(self):
        return self._saAmfCompCurrProxiedNames

    def getsaAmfCompContainerCsi(self):
        ImmHelper.validateSingle(self._saAmfCompContainerCsi, self._dn, "saAmfCompContainerCsi")
        return self._saAmfCompContainerCsi

    def getsaAmfCompCmdEnv(self):
        return self._saAmfCompCmdEnv

    def getsaAmfCompCleanupTimeout(self):
        ImmHelper.validateSingle(self._saAmfCompCleanupTimeout, self._dn, "saAmfCompCleanupTimeout")
        return self._saAmfCompCleanupTimeout

    def getsaAmfCompCleanupCmdArgv(self):
        return self._saAmfCompCleanupCmdArgv

    def getsaAmfCompCSISetCallbackTimeout(self):
        ImmHelper.validateSingle(self._saAmfCompCSISetCallbackTimeout, self._dn, "saAmfCompCSISetCallbackTimeout")
        return self._saAmfCompCSISetCallbackTimeout

    def getsaAmfCompCSIRmvCallbackTimeout(self):
        ImmHelper.validateSingle(self._saAmfCompCSIRmvCallbackTimeout, self._dn, "saAmfCompCSIRmvCallbackTimeout")
        return self._saAmfCompCSIRmvCallbackTimeout

    def getsaAmfCompAmStopTimeout(self):
        ImmHelper.validateSingle(self._saAmfCompAmStopTimeout, self._dn, "saAmfCompAmStopTimeout")
        return self._saAmfCompAmStopTimeout

    def getsaAmfCompAmStopCmdArgv(self):
        return self._saAmfCompAmStopCmdArgv

    def getsaAmfCompAmStartTimeout(self):
        ImmHelper.validateSingle(self._saAmfCompAmStartTimeout, self._dn, "saAmfCompAmStartTimeout")
        return self._saAmfCompAmStartTimeout

    def getsaAmfCompAmStartCmdArgv(self):
        return self._saAmfCompAmStartCmdArgv

    def getosafAmfCompHcCmdArgv(self):
        return self._osafAmfCompHcCmdArgv

    def getSaImmAttrImplementerName(self):
        ImmHelper.validateSingle(self._SaImmAttrImplementerName, self._dn, "SaImmAttrImplementerName")
        return self._SaImmAttrImplementerName

    def getSaImmAttrClassName(self):
        ImmHelper.validateSingle(self._SaImmAttrClassName, self._dn, "SaImmAttrClassName")
        return self._SaImmAttrClassName

    def getSaImmAttrAdminOwnerName(self):
        ImmHelper.validateSingle(self._SaImmAttrAdminOwnerName, self._dn, "SaImmAttrAdminOwnerName")
        return self._SaImmAttrAdminOwnerName

    def getsaAmfCompType_unsafe(self):
        return self._saAmfCompType

    def getsaAmfCompTerminateTimeout_unsafe(self):
        return self._saAmfCompTerminateTimeout

    def getsaAmfCompTerminateCmdArgv_single(self):
        ImmHelper.validateSingleInList(self._saAmfCompTerminateCmdArgv, self._dn, "saAmfCompTerminateCmdArgv")
        return self._saAmfCompTerminateCmdArgv[0]

    def getsaAmfCompRestartCount_unsafe(self):
        return self._saAmfCompRestartCount

    def getsaAmfCompRecoveryOnError_unsafe(self):
        return self._saAmfCompRecoveryOnError

    def getsaAmfCompReadinessState_unsafe(self):
        return self._saAmfCompReadinessState

    def getsaAmfCompQuiescingCompleteTimeout_unsafe(self):
        return self._saAmfCompQuiescingCompleteTimeout

    def getsaAmfCompProxyCsi_unsafe(self):
        return self._saAmfCompProxyCsi

    def getsaAmfCompPresenceState_unsafe(self):
        return self._saAmfCompPresenceState

    def getsaAmfCompOperState_unsafe(self):
        return self._saAmfCompOperState

    def getsaAmfCompNumMaxInstantiateWithoutDelay_unsafe(self):
        return self._saAmfCompNumMaxInstantiateWithoutDelay

    def getsaAmfCompNumMaxInstantiateWithDelay_unsafe(self):
        return self._saAmfCompNumMaxInstantiateWithDelay

    def getsaAmfCompNumMaxAmStopAttempts_unsafe(self):
        return self._saAmfCompNumMaxAmStopAttempts

    def getsaAmfCompNumMaxAmStartAttempts_unsafe(self):
        return self._saAmfCompNumMaxAmStartAttempts

    def getsaAmfCompInstantiationLevel_unsafe(self):
        return self._saAmfCompInstantiationLevel

    def getsaAmfCompInstantiateTimeout_unsafe(self):
        return self._saAmfCompInstantiateTimeout

    def getsaAmfCompInstantiateCmdArgv_single(self):
        ImmHelper.validateSingleInList(self._saAmfCompInstantiateCmdArgv, self._dn, "saAmfCompInstantiateCmdArgv")
        return self._saAmfCompInstantiateCmdArgv[0]

    def getsaAmfCompDisableRestart_unsafe(self):
        return self._saAmfCompDisableRestart

    def getsaAmfCompDelayBetweenInstantiateAttempts_unsafe(self):
        return self._saAmfCompDelayBetweenInstantiateAttempts

    def getsaAmfCompCurrProxyName_unsafe(self):
        return self._saAmfCompCurrProxyName

    def getsaAmfCompCurrProxiedNames_single(self):
        ImmHelper.validateSingleInList(self._saAmfCompCurrProxiedNames, self._dn, "saAmfCompCurrProxiedNames")
        return self._saAmfCompCurrProxiedNames[0]

    def getsaAmfCompContainerCsi_unsafe(self):
        return self._saAmfCompContainerCsi

    def getsaAmfCompCmdEnv_single(self):
        ImmHelper.validateSingleInList(self._saAmfCompCmdEnv, self._dn, "saAmfCompCmdEnv")
        return self._saAmfCompCmdEnv[0]

    def getsaAmfCompCleanupTimeout_unsafe(self):
        return self._saAmfCompCleanupTimeout

    def getsaAmfCompCleanupCmdArgv_single(self):
        ImmHelper.validateSingleInList(self._saAmfCompCleanupCmdArgv, self._dn, "saAmfCompCleanupCmdArgv")
        return self._saAmfCompCleanupCmdArgv[0]

    def getsaAmfCompCSISetCallbackTimeout_unsafe(self):
        return self._saAmfCompCSISetCallbackTimeout

    def getsaAmfCompCSIRmvCallbackTimeout_unsafe(self):
        return self._saAmfCompCSIRmvCallbackTimeout

    def getsaAmfCompAmStopTimeout_unsafe(self):
        return self._saAmfCompAmStopTimeout

    def getsaAmfCompAmStopCmdArgv_single(self):
        ImmHelper.validateSingleInList(self._saAmfCompAmStopCmdArgv, self._dn, "saAmfCompAmStopCmdArgv")
        return self._saAmfCompAmStopCmdArgv[0]

    def getsaAmfCompAmStartTimeout_unsafe(self):
        return self._saAmfCompAmStartTimeout

    def getsaAmfCompAmStartCmdArgv_single(self):
        ImmHelper.validateSingleInList(self._saAmfCompAmStartCmdArgv, self._dn, "saAmfCompAmStartCmdArgv")
        return self._saAmfCompAmStartCmdArgv[0]

    def getosafAmfCompHcCmdArgv_single(self):
        ImmHelper.validateSingleInList(self._osafAmfCompHcCmdArgv, self._dn, "osafAmfCompHcCmdArgv")
        return self._osafAmfCompHcCmdArgv[0]

    def getSaImmAttrImplementerName_unsafe(self):
        return self._SaImmAttrImplementerName

    def getSaImmAttrClassName_unsafe(self):
        return self._SaImmAttrClassName

    def getSaImmAttrAdminOwnerName_unsafe(self):
        return self._SaImmAttrAdminOwnerName

    def setsaAmfCompType(self, value):
        ImmHelper.validateName(value, self._dn, "saAmfCompType")
        self._saAmfCompType = value

    def setsaAmfCompTerminateTimeout(self, value):
        ImmHelper.validateTime(value, self._dn, "saAmfCompTerminateTimeout")
        value = str(value)
        self._saAmfCompTerminateTimeout = value

    def addTosaAmfCompTerminateCmdArgv(self, value):
        ImmHelper.validateString(value, self._dn, "saAmfCompTerminateCmdArgv")
        self._saAmfCompTerminateCmdArgv.append(value)

    def setsaAmfCompRestartCount(self, value):
        ImmHelper.validateUint32(value, self._dn, "saAmfCompRestartCount")
        value = str(value)
        self._saAmfCompRestartCount = value

    def setsaAmfCompRecoveryOnError(self, value):
        ImmHelper.validateUint32(value, self._dn, "saAmfCompRecoveryOnError")
        value = str(value)
        self._saAmfCompRecoveryOnError = value

    def setsaAmfCompReadinessState(self, value):
        ImmHelper.validateUint32(value, self._dn, "saAmfCompReadinessState")
        value = str(value)
        self._saAmfCompReadinessState = value

    def setsaAmfCompQuiescingCompleteTimeout(self, value):
        ImmHelper.validateTime(value, self._dn, "saAmfCompQuiescingCompleteTimeout")
        value = str(value)
        self._saAmfCompQuiescingCompleteTimeout = value

    def setsaAmfCompProxyCsi(self, value):
        ImmHelper.validateName(value, self._dn, "saAmfCompProxyCsi")
        self._saAmfCompProxyCsi = value

    def setsaAmfCompPresenceState(self, value):
        ImmHelper.validateUint32(value, self._dn, "saAmfCompPresenceState")
        value = str(value)
        self._saAmfCompPresenceState = value

    def setsaAmfCompOperState(self, value):
        ImmHelper.validateUint32(value, self._dn, "saAmfCompOperState")
        value = str(value)
        self._saAmfCompOperState = value

    def setsaAmfCompNumMaxInstantiateWithoutDelay(self, value):
        ImmHelper.validateUint32(value, self._dn, "saAmfCompNumMaxInstantiateWithoutDelay")
        value = str(value)
        self._saAmfCompNumMaxInstantiateWithoutDelay = value

    def setsaAmfCompNumMaxInstantiateWithDelay(self, value):
        ImmHelper.validateUint32(value, self._dn, "saAmfCompNumMaxInstantiateWithDelay")
        value = str(value)
        self._saAmfCompNumMaxInstantiateWithDelay = value

    def setsaAmfCompNumMaxAmStopAttempts(self, value):
        ImmHelper.validateUint32(value, self._dn, "saAmfCompNumMaxAmStopAttempts")
        value = str(value)
        self._saAmfCompNumMaxAmStopAttempts = value

    def setsaAmfCompNumMaxAmStartAttempts(self, value):
        ImmHelper.validateUint32(value, self._dn, "saAmfCompNumMaxAmStartAttempts")
        value = str(value)
        self._saAmfCompNumMaxAmStartAttempts = value

    def setsaAmfCompInstantiationLevel(self, value):
        ImmHelper.validateUint32(value, self._dn, "saAmfCompInstantiationLevel")
        value = str(value)
        self._saAmfCompInstantiationLevel = value

    def setsaAmfCompInstantiateTimeout(self, value):
        ImmHelper.validateTime(value, self._dn, "saAmfCompInstantiateTimeout")
        value = str(value)
        self._saAmfCompInstantiateTimeout = value

    def addTosaAmfCompInstantiateCmdArgv(self, value):
        ImmHelper.validateString(value, self._dn, "saAmfCompInstantiateCmdArgv")
        self._saAmfCompInstantiateCmdArgv.append(value)

    def setsaAmfCompDisableRestart(self, value):
        ImmHelper.validateUint32(value, self._dn, "saAmfCompDisableRestart")
        value = str(value)
        self._saAmfCompDisableRestart = value

    def setsaAmfCompDelayBetweenInstantiateAttempts(self, value):
        ImmHelper.validateTime(value, self._dn, "saAmfCompDelayBetweenInstantiateAttempts")
        value = str(value)
        self._saAmfCompDelayBetweenInstantiateAttempts = value

    def setsaAmfCompCurrProxyName(self, value):
        ImmHelper.validateName(value, self._dn, "saAmfCompCurrProxyName")
        self._saAmfCompCurrProxyName = value

    def addTosaAmfCompCurrProxiedNames(self, value):
        ImmHelper.validateName(value, self._dn, "saAmfCompCurrProxiedNames")
        self._saAmfCompCurrProxiedNames.append(value)

    def setsaAmfCompContainerCsi(self, value):
        ImmHelper.validateName(value, self._dn, "saAmfCompContainerCsi")
        self._saAmfCompContainerCsi = value

    def addTosaAmfCompCmdEnv(self, value):
        ImmHelper.validateString(value, self._dn, "saAmfCompCmdEnv")
        self._saAmfCompCmdEnv.append(value)

    def setsaAmfCompCleanupTimeout(self, value):
        ImmHelper.validateTime(value, self._dn, "saAmfCompCleanupTimeout")
        value = str(value)
        self._saAmfCompCleanupTimeout = value

    def addTosaAmfCompCleanupCmdArgv(self, value):
        ImmHelper.validateString(value, self._dn, "saAmfCompCleanupCmdArgv")
        self._saAmfCompCleanupCmdArgv.append(value)

    def setsaAmfCompCSISetCallbackTimeout(self, value):
        ImmHelper.validateTime(value, self._dn, "saAmfCompCSISetCallbackTimeout")
        value = str(value)
        self._saAmfCompCSISetCallbackTimeout = value

    def setsaAmfCompCSIRmvCallbackTimeout(self, value):
        ImmHelper.validateTime(value, self._dn, "saAmfCompCSIRmvCallbackTimeout")
        value = str(value)
        self._saAmfCompCSIRmvCallbackTimeout = value

    def setsaAmfCompAmStopTimeout(self, value):
        ImmHelper.validateTime(value, self._dn, "saAmfCompAmStopTimeout")
        value = str(value)
        self._saAmfCompAmStopTimeout = value

    def addTosaAmfCompAmStopCmdArgv(self, value):
        ImmHelper.validateString(value, self._dn, "saAmfCompAmStopCmdArgv")
        self._saAmfCompAmStopCmdArgv.append(value)

    def setsaAmfCompAmStartTimeout(self, value):
        ImmHelper.validateTime(value, self._dn, "saAmfCompAmStartTimeout")
        value = str(value)
        self._saAmfCompAmStartTimeout = value

    def addTosaAmfCompAmStartCmdArgv(self, value):
        ImmHelper.validateString(value, self._dn, "saAmfCompAmStartCmdArgv")
        self._saAmfCompAmStartCmdArgv.append(value)

    def addToosafAmfCompHcCmdArgv(self, value):
        ImmHelper.validateString(value, self._dn, "osafAmfCompHcCmdArgv")
        self._osafAmfCompHcCmdArgv.append(value)

    def setSaImmAttrImplementerName(self, value):
        ImmHelper.validateString(value, self._dn, "SaImmAttrImplementerName")
        self._SaImmAttrImplementerName = value

    def setSaImmAttrClassName(self, value):
        ImmHelper.validateString(value, self._dn, "SaImmAttrClassName")
        self._SaImmAttrClassName = value

    def setSaImmAttrAdminOwnerName(self, value):
        ImmHelper.validateString(value, self._dn, "SaImmAttrAdminOwnerName")
        self._SaImmAttrAdminOwnerName = value

    def updateParams(self, params, canttouchthis):
        for (param, value) in params.items():
            if param in canttouchthis:
                error("Setting attribute " + param + " in object " + self.getDn() + " is not supported")
            if param == "saAmfCompType":
                self.setsaAmfCompType(value)
            elif param == "saAmfCompTerminateTimeout":
                self.setsaAmfCompTerminateTimeout(value)
            elif param == "saAmfCompTerminateCmdArgv":
                if not isinstance(value, list):
                    value = [value]
                self._saAmfCompTerminateCmdArgv = []
                for v in value:
                    self.addTosaAmfCompTerminateCmdArgv(v)
            elif param == "saAmfCompRecoveryOnError":
                self.setsaAmfCompRecoveryOnError(value)
            elif param == "saAmfCompQuiescingCompleteTimeout":
                self.setsaAmfCompQuiescingCompleteTimeout(value)
            elif param == "saAmfCompProxyCsi":
                self.setsaAmfCompProxyCsi(value)
            elif param == "saAmfCompNumMaxInstantiateWithoutDelay":
                self.setsaAmfCompNumMaxInstantiateWithoutDelay(value)
            elif param == "saAmfCompNumMaxInstantiateWithDelay":
                self.setsaAmfCompNumMaxInstantiateWithDelay(value)
            elif param == "saAmfCompNumMaxAmStopAttempts":
                self.setsaAmfCompNumMaxAmStopAttempts(value)
            elif param == "saAmfCompNumMaxAmStartAttempts":
                self.setsaAmfCompNumMaxAmStartAttempts(value)
            elif param == "saAmfCompInstantiationLevel":
                self.setsaAmfCompInstantiationLevel(value)
            elif param == "saAmfCompInstantiateTimeout":
                self.setsaAmfCompInstantiateTimeout(value)
            elif param == "saAmfCompInstantiateCmdArgv":
                if not isinstance(value, list):
                    value = [value]
                self._saAmfCompInstantiateCmdArgv = []
                for v in value:
                    self.addTosaAmfCompInstantiateCmdArgv(v)
            elif param == "saAmfCompDisableRestart":
                self.setsaAmfCompDisableRestart(value)
            elif param == "saAmfCompDelayBetweenInstantiateAttempts":
                self.setsaAmfCompDelayBetweenInstantiateAttempts(value)
            elif param == "saAmfCompContainerCsi":
                self.setsaAmfCompContainerCsi(value)
            elif param == "saAmfCompCleanupTimeout":
                self.setsaAmfCompCleanupTimeout(value)
            elif param == "saAmfCompCleanupCmdArgv":
                if not isinstance(value, list):
                    value = [value]
                self._saAmfCompCleanupCmdArgv = []
                for v in value:
                    self.addTosaAmfCompCleanupCmdArgv(v)
            elif param == "saAmfCompCSISetCallbackTimeout":
                self.setsaAmfCompCSISetCallbackTimeout(value)
            elif param == "saAmfCompCSIRmvCallbackTimeout":
                self.setsaAmfCompCSIRmvCallbackTimeout(value)
            elif param == "saAmfCompAmStopTimeout":
                self.setsaAmfCompAmStopTimeout(value)
            elif param == "saAmfCompAmStopCmdArgv":
                if not isinstance(value, list):
                    value = [value]
                self._saAmfCompAmStopCmdArgv = []
                for v in value:
                    self.addTosaAmfCompAmStopCmdArgv(v)
            elif param == "saAmfCompAmStartTimeout":
                self.setsaAmfCompAmStartTimeout(value)
            elif param == "saAmfCompAmStartCmdArgv":
                if not isinstance(value, list):
                    value = [value]
                self._saAmfCompAmStartCmdArgv = []
                for v in value:
                    self.addTosaAmfCompAmStartCmdArgv(v)
            elif param == "osafAmfCompHcCmdArgv":
                if not isinstance(value, list):
                    value = [value]
                self._osafAmfCompHcCmdArgv = []
                for v in value:
                    self.addToosafAmfCompHcCmdArgv(v)
            else:
                error("Object " + self.getDn() + " has no attribute named " + param)

    def diff(self, other, fullCheck = False):
        changedAttrs = []
        if (fullCheck or self._saAmfCompType != None) and other._saAmfCompType != self._saAmfCompType:
            changedAttrs.append("saAmfCompType")
        if (fullCheck or self._saAmfCompTerminateTimeout != None) and other._saAmfCompTerminateTimeout != self._saAmfCompTerminateTimeout:
            changedAttrs.append("saAmfCompTerminateTimeout")
        if fullCheck or (len(self._saAmfCompTerminateCmdArgv) != 0):
            if len(self._saAmfCompTerminateCmdArgv) != len(other._saAmfCompTerminateCmdArgv):
                changedAttrs.append("saAmfCompTerminateCmdArgv")
            else:
                difflist = list(set(self._saAmfCompTerminateCmdArgv) ^ set(other._saAmfCompTerminateCmdArgv))
                if len(difflist) > 0:
                    changedAttrs.append("saAmfCompTerminateCmdArgv")
        if (fullCheck or self._saAmfCompRecoveryOnError != None) and other._saAmfCompRecoveryOnError != self._saAmfCompRecoveryOnError:
            changedAttrs.append("saAmfCompRecoveryOnError")
        if (fullCheck or self._saAmfCompQuiescingCompleteTimeout != None) and other._saAmfCompQuiescingCompleteTimeout != self._saAmfCompQuiescingCompleteTimeout:
            changedAttrs.append("saAmfCompQuiescingCompleteTimeout")
        if (fullCheck or self._saAmfCompProxyCsi != None) and other._saAmfCompProxyCsi != self._saAmfCompProxyCsi:
            changedAttrs.append("saAmfCompProxyCsi")
        if (fullCheck or self._saAmfCompNumMaxInstantiateWithoutDelay != None) and other._saAmfCompNumMaxInstantiateWithoutDelay != self._saAmfCompNumMaxInstantiateWithoutDelay:
            changedAttrs.append("saAmfCompNumMaxInstantiateWithoutDelay")
        if (fullCheck or self._saAmfCompNumMaxInstantiateWithDelay != None) and other._saAmfCompNumMaxInstantiateWithDelay != self._saAmfCompNumMaxInstantiateWithDelay:
            changedAttrs.append("saAmfCompNumMaxInstantiateWithDelay")
        if (fullCheck or self._saAmfCompNumMaxAmStopAttempts != None) and other._saAmfCompNumMaxAmStopAttempts != self._saAmfCompNumMaxAmStopAttempts:
            changedAttrs.append("saAmfCompNumMaxAmStopAttempts")
        if (fullCheck or self._saAmfCompNumMaxAmStartAttempts != None) and other._saAmfCompNumMaxAmStartAttempts != self._saAmfCompNumMaxAmStartAttempts:
            changedAttrs.append("saAmfCompNumMaxAmStartAttempts")
        if (fullCheck or self._saAmfCompInstantiationLevel != None) and other._saAmfCompInstantiationLevel != self._saAmfCompInstantiationLevel:
            changedAttrs.append("saAmfCompInstantiationLevel")
        if (fullCheck or self._saAmfCompInstantiateTimeout != None) and other._saAmfCompInstantiateTimeout != self._saAmfCompInstantiateTimeout:
            changedAttrs.append("saAmfCompInstantiateTimeout")
        if fullCheck or (len(self._saAmfCompInstantiateCmdArgv) != 0):
            if len(self._saAmfCompInstantiateCmdArgv) != len(other._saAmfCompInstantiateCmdArgv):
                changedAttrs.append("saAmfCompInstantiateCmdArgv")
            else:
                difflist = list(set(self._saAmfCompInstantiateCmdArgv) ^ set(other._saAmfCompInstantiateCmdArgv))
                if len(difflist) > 0:
                    changedAttrs.append("saAmfCompInstantiateCmdArgv")
        if (fullCheck or self._saAmfCompDisableRestart != None) and other._saAmfCompDisableRestart != self._saAmfCompDisableRestart:
            changedAttrs.append("saAmfCompDisableRestart")
        if (fullCheck or self._saAmfCompDelayBetweenInstantiateAttempts != None) and other._saAmfCompDelayBetweenInstantiateAttempts != self._saAmfCompDelayBetweenInstantiateAttempts:
            changedAttrs.append("saAmfCompDelayBetweenInstantiateAttempts")
        if (fullCheck or self._saAmfCompContainerCsi != None) and other._saAmfCompContainerCsi != self._saAmfCompContainerCsi:
            changedAttrs.append("saAmfCompContainerCsi")
        if fullCheck or (len(self._saAmfCompCmdEnv) != 0):
            if len(self._saAmfCompCmdEnv) != len(other._saAmfCompCmdEnv):
                changedAttrs.append("saAmfCompCmdEnv")
            else:
                difflist = list(set(self._saAmfCompCmdEnv) ^ set(other._saAmfCompCmdEnv))
                if len(difflist) > 0:
                    changedAttrs.append("saAmfCompCmdEnv")
        if (fullCheck or self._saAmfCompCleanupTimeout != None) and other._saAmfCompCleanupTimeout != self._saAmfCompCleanupTimeout:
            changedAttrs.append("saAmfCompCleanupTimeout")
        if fullCheck or (len(self._saAmfCompCleanupCmdArgv) != 0):
            if len(self._saAmfCompCleanupCmdArgv) != len(other._saAmfCompCleanupCmdArgv):
                changedAttrs.append("saAmfCompCleanupCmdArgv")
            else:
                difflist = list(set(self._saAmfCompCleanupCmdArgv) ^ set(other._saAmfCompCleanupCmdArgv))
                if len(difflist) > 0:
                    changedAttrs.append("saAmfCompCleanupCmdArgv")
        if (fullCheck or self._saAmfCompCSISetCallbackTimeout != None) and other._saAmfCompCSISetCallbackTimeout != self._saAmfCompCSISetCallbackTimeout:
            changedAttrs.append("saAmfCompCSISetCallbackTimeout")
        if (fullCheck or self._saAmfCompCSIRmvCallbackTimeout != None) and other._saAmfCompCSIRmvCallbackTimeout != self._saAmfCompCSIRmvCallbackTimeout:
            changedAttrs.append("saAmfCompCSIRmvCallbackTimeout")
        if (fullCheck or self._saAmfCompAmStopTimeout != None) and other._saAmfCompAmStopTimeout != self._saAmfCompAmStopTimeout:
            changedAttrs.append("saAmfCompAmStopTimeout")
        if fullCheck or (len(self._saAmfCompAmStopCmdArgv) != 0):
            if len(self._saAmfCompAmStopCmdArgv) != len(other._saAmfCompAmStopCmdArgv):
                changedAttrs.append("saAmfCompAmStopCmdArgv")
            else:
                difflist = list(set(self._saAmfCompAmStopCmdArgv) ^ set(other._saAmfCompAmStopCmdArgv))
                if len(difflist) > 0:
                    changedAttrs.append("saAmfCompAmStopCmdArgv")
        if (fullCheck or self._saAmfCompAmStartTimeout != None) and other._saAmfCompAmStartTimeout != self._saAmfCompAmStartTimeout:
            changedAttrs.append("saAmfCompAmStartTimeout")
        if fullCheck or (len(self._saAmfCompAmStartCmdArgv) != 0):
            if len(self._saAmfCompAmStartCmdArgv) != len(other._saAmfCompAmStartCmdArgv):
                changedAttrs.append("saAmfCompAmStartCmdArgv")
            else:
                difflist = list(set(self._saAmfCompAmStartCmdArgv) ^ set(other._saAmfCompAmStartCmdArgv))
                if len(difflist) > 0:
                    changedAttrs.append("saAmfCompAmStartCmdArgv")
        if fullCheck or (len(self._osafAmfCompHcCmdArgv) != 0):
            if len(self._osafAmfCompHcCmdArgv) != len(other._osafAmfCompHcCmdArgv):
                changedAttrs.append("osafAmfCompHcCmdArgv")
            else:
                difflist = list(set(self._osafAmfCompHcCmdArgv) ^ set(other._osafAmfCompHcCmdArgv))
                if len(difflist) > 0:
                    changedAttrs.append("osafAmfCompHcCmdArgv")
        if (fullCheck or self._SaImmAttrImplementerName != None) and other._SaImmAttrImplementerName != self._SaImmAttrImplementerName:
            changedAttrs.append("SaImmAttrImplementerName")
        if (fullCheck or self._SaImmAttrClassName != None) and other._SaImmAttrClassName != self._SaImmAttrClassName:
            changedAttrs.append("SaImmAttrClassName")
        if (fullCheck or self._SaImmAttrAdminOwnerName != None) and other._SaImmAttrAdminOwnerName != self._SaImmAttrAdminOwnerName:
            changedAttrs.append("SaImmAttrAdminOwnerName")
        return changedAttrs

    def parseXML(self, node):
        dns = node.getElementsByTagName("dn")
        if len(dns) != 1:
            error("object has " + str(len(dns)) + " dn(s) but it should have one")
        self._dn = dns[0].childNodes[0].nodeValue
        for attribute in node.getElementsByTagName("attr"):
            names = attribute.getElementsByTagName("name")
            if len(names) != 1:
                error("object attribute has " + str(len(names)) + " name(s) but it should have one")
            name = names[0].childNodes[0].nodeValue
            setFunc = None
            if name == "SaImmAttrImplementerName":
                continue
            elif name == "SaImmAttrAdminOwnerName":
                continue
            elif name == "SaImmAttrClassName":
                continue
            elif name == "saAmfCompType":
                setFunc = self.setsaAmfCompType
            elif name == "saAmfCompTerminateTimeout":
                setFunc = self.setsaAmfCompTerminateTimeout
            elif name == "saAmfCompTerminateCmdArgv":
                setFunc = self.addTosaAmfCompTerminateCmdArgv
            elif name == "saAmfCompRestartCount":
                setFunc = self.setsaAmfCompRestartCount
            elif name == "saAmfCompRecoveryOnError":
                setFunc = self.setsaAmfCompRecoveryOnError
            elif name == "saAmfCompReadinessState":
                setFunc = self.setsaAmfCompReadinessState
            elif name == "saAmfCompQuiescingCompleteTimeout":
                setFunc = self.setsaAmfCompQuiescingCompleteTimeout
            elif name == "saAmfCompProxyCsi":
                setFunc = self.setsaAmfCompProxyCsi
            elif name == "saAmfCompPresenceState":
                setFunc = self.setsaAmfCompPresenceState
            elif name == "saAmfCompOperState":
                setFunc = self.setsaAmfCompOperState
            elif name == "saAmfCompNumMaxInstantiateWithoutDelay":
                setFunc = self.setsaAmfCompNumMaxInstantiateWithoutDelay
            elif name == "saAmfCompNumMaxInstantiateWithDelay":
                setFunc = self.setsaAmfCompNumMaxInstantiateWithDelay
            elif name == "saAmfCompNumMaxAmStopAttempts":
                setFunc = self.setsaAmfCompNumMaxAmStopAttempts
            elif name == "saAmfCompNumMaxAmStartAttempts":
                setFunc = self.setsaAmfCompNumMaxAmStartAttempts
            elif name == "saAmfCompInstantiationLevel":
                setFunc = self.setsaAmfCompInstantiationLevel
            elif name == "saAmfCompInstantiateTimeout":
                setFunc = self.setsaAmfCompInstantiateTimeout
            elif name == "saAmfCompInstantiateCmdArgv":
                setFunc = self.addTosaAmfCompInstantiateCmdArgv
            elif name == "saAmfCompDisableRestart":
                setFunc = self.setsaAmfCompDisableRestart
            elif name == "saAmfCompDelayBetweenInstantiateAttempts":
                setFunc = self.setsaAmfCompDelayBetweenInstantiateAttempts
            elif name == "saAmfCompCurrProxyName":
                setFunc = self.setsaAmfCompCurrProxyName
            elif name == "saAmfCompCurrProxiedNames":
                setFunc = self.addTosaAmfCompCurrProxiedNames
            elif name == "saAmfCompContainerCsi":
                setFunc = self.setsaAmfCompContainerCsi
            elif name == "saAmfCompCmdEnv":
                setFunc = self.addTosaAmfCompCmdEnv
            elif name == "saAmfCompCleanupTimeout":
                setFunc = self.setsaAmfCompCleanupTimeout
            elif name == "saAmfCompCleanupCmdArgv":
                setFunc = self.addTosaAmfCompCleanupCmdArgv
            elif name == "saAmfCompCSISetCallbackTimeout":
                setFunc = self.setsaAmfCompCSISetCallbackTimeout
            elif name == "saAmfCompCSIRmvCallbackTimeout":
                setFunc = self.setsaAmfCompCSIRmvCallbackTimeout
            elif name == "saAmfCompAmStopTimeout":
                setFunc = self.setsaAmfCompAmStopTimeout
            elif name == "saAmfCompAmStopCmdArgv":
                setFunc = self.addTosaAmfCompAmStopCmdArgv
            elif name == "saAmfCompAmStartTimeout":
                setFunc = self.setsaAmfCompAmStartTimeout
            elif name == "saAmfCompAmStartCmdArgv":
                setFunc = self.addTosaAmfCompAmStartCmdArgv
            elif name == "osafAmfCompHcCmdArgv":
                setFunc = self.addToosafAmfCompHcCmdArgv
            elif name == "SaImmAttrImplementerName":
                setFunc = self.setSaImmAttrImplementerName
            elif name == "SaImmAttrClassName":
                setFunc = self.setSaImmAttrClassName
            elif name == "SaImmAttrAdminOwnerName":
                setFunc = self.setSaImmAttrAdminOwnerName
            elif name.startswith("osaf"):
                continue # ignore OpenSAF specific attributes
            else:
                error("unknown attribute called " + name + " defined in object " + self._dn)
            for value in attribute.getElementsByTagName("value"):
                setFunc(value.childNodes[0].nodeValue)

    def writeXML(self, parent, doc):
        obj = doc.createElement("object")
        parent.appendChild(obj)
        obj.setAttribute("class", "SaAmfComp")
        dn = doc.createElement("dn")
        obj.appendChild(dn)
        dn.appendChild(doc.createTextNode(self._dn))
        ImmHelper.writeSingleAttribute("saAmfCompType", self._saAmfCompType, doc, obj)
        ImmHelper.writeSingleAttribute("saAmfCompTerminateTimeout", self._saAmfCompTerminateTimeout, doc, obj)
        ImmHelper.writeMultiAttributes("saAmfCompTerminateCmdArgv", self._saAmfCompTerminateCmdArgv, doc, obj)
        ImmHelper.writeSingleAttribute("saAmfCompRestartCount", self._saAmfCompRestartCount, doc, obj)
        ImmHelper.writeSingleAttribute("saAmfCompRecoveryOnError", self._saAmfCompRecoveryOnError, doc, obj)
        ImmHelper.writeSingleAttribute("saAmfCompReadinessState", self._saAmfCompReadinessState, doc, obj)
        ImmHelper.writeSingleAttribute("saAmfCompQuiescingCompleteTimeout", self._saAmfCompQuiescingCompleteTimeout, doc, obj)
        ImmHelper.writeSingleAttribute("saAmfCompProxyCsi", self._saAmfCompProxyCsi, doc, obj)
        ImmHelper.writeSingleAttribute("saAmfCompPresenceState", self._saAmfCompPresenceState, doc, obj)
        ImmHelper.writeSingleAttribute("saAmfCompOperState", self._saAmfCompOperState, doc, obj)
        ImmHelper.writeSingleAttribute("saAmfCompNumMaxInstantiateWithoutDelay", self._saAmfCompNumMaxInstantiateWithoutDelay, doc, obj)
        ImmHelper.writeSingleAttribute("saAmfCompNumMaxInstantiateWithDelay", self._saAmfCompNumMaxInstantiateWithDelay, doc, obj)
        ImmHelper.writeSingleAttribute("saAmfCompNumMaxAmStopAttempts", self._saAmfCompNumMaxAmStopAttempts, doc, obj)
        ImmHelper.writeSingleAttribute("saAmfCompNumMaxAmStartAttempts", self._saAmfCompNumMaxAmStartAttempts, doc, obj)
        ImmHelper.writeSingleAttribute("saAmfCompInstantiationLevel", self._saAmfCompInstantiationLevel, doc, obj)
        ImmHelper.writeSingleAttribute("saAmfCompInstantiateTimeout", self._saAmfCompInstantiateTimeout, doc, obj)
        ImmHelper.writeMultiAttributes("saAmfCompInstantiateCmdArgv", self._saAmfCompInstantiateCmdArgv, doc, obj)
        ImmHelper.writeSingleAttribute("saAmfCompDisableRestart", self._saAmfCompDisableRestart, doc, obj)
        ImmHelper.writeSingleAttribute("saAmfCompDelayBetweenInstantiateAttempts", self._saAmfCompDelayBetweenInstantiateAttempts, doc, obj)
        ImmHelper.writeSingleAttribute("saAmfCompCurrProxyName", self._saAmfCompCurrProxyName, doc, obj)
        ImmHelper.writeMultiAttributes("saAmfCompCurrProxiedNames", self._saAmfCompCurrProxiedNames, doc, obj)
        ImmHelper.writeSingleAttribute("saAmfCompContainerCsi", self._saAmfCompContainerCsi, doc, obj)
        ImmHelper.writeMultiAttributes("saAmfCompCmdEnv", self._saAmfCompCmdEnv, doc, obj)
        ImmHelper.writeSingleAttribute("saAmfCompCleanupTimeout", self._saAmfCompCleanupTimeout, doc, obj)
        ImmHelper.writeMultiAttributes("saAmfCompCleanupCmdArgv", self._saAmfCompCleanupCmdArgv, doc, obj)
        ImmHelper.writeSingleAttribute("saAmfCompCSISetCallbackTimeout", self._saAmfCompCSISetCallbackTimeout, doc, obj)
        ImmHelper.writeSingleAttribute("saAmfCompCSIRmvCallbackTimeout", self._saAmfCompCSIRmvCallbackTimeout, doc, obj)
        ImmHelper.writeSingleAttribute("saAmfCompAmStopTimeout", self._saAmfCompAmStopTimeout, doc, obj)
        ImmHelper.writeMultiAttributes("saAmfCompAmStopCmdArgv", self._saAmfCompAmStopCmdArgv, doc, obj)
        ImmHelper.writeSingleAttribute("saAmfCompAmStartTimeout", self._saAmfCompAmStartTimeout, doc, obj)
        ImmHelper.writeMultiAttributes("saAmfCompAmStartCmdArgv", self._saAmfCompAmStartCmdArgv, doc, obj)
        ImmHelper.writeMultiAttributes("osafAmfCompHcCmdArgv", self._osafAmfCompHcCmdArgv, doc, obj)
        ImmHelper.writeSingleAttribute("SaImmAttrImplementerName", self._SaImmAttrImplementerName, doc, obj)
        ImmHelper.writeSingleAttribute("SaImmAttrClassName", self._SaImmAttrClassName, doc, obj)
        ImmHelper.writeSingleAttribute("SaImmAttrAdminOwnerName", self._SaImmAttrAdminOwnerName, doc, obj)


class SaAmfCluster(object):
    def __init__(self):
        self._dn = None
        self._saAmfClusterStartupTimeout = None
        self._saAmfClusterClmCluster = None
        self._saAmfClusterAdminState = None
        self._SaImmAttrImplementerName = None
        self._SaImmAttrClassName = None
        self._SaImmAttrAdminOwnerName = None

    @staticmethod
    def createDn(name, parentDn = None):
        if parentDn == None:
            parentDn = ""
        else:
            parentDn = "," + parentDn
        return "safAmfCluster=" + ImmHelper.escapeName(name) + parentDn

    def getDn(self):
        return self._dn

    def getName(self):
        return ImmHelper.getName(self._dn)

    def getRdn(self):
        return ImmHelper.getRdn(self._dn)

    def getParentDn(self):
        return ImmHelper.getParentDn(self._dn)

    def createObjectInCampaign(self, campaign):
        parentDn = self.getParentDn()
        if parentDn == "":
            parentDn = "="
        campaign.beginCreate("SaAmfCluster", parentDn)
        campaign.addAttribute("safAmfCluster", "SA_IMM_ATTR_SASTRINGT", self.getRdn())
        if self._saAmfClusterStartupTimeout != None:
            campaign.addAttribute("saAmfClusterStartupTimeout", "SA_IMM_ATTR_SATIMET", self._saAmfClusterStartupTimeout)
        if self._saAmfClusterClmCluster != None:
            campaign.addAttribute("saAmfClusterClmCluster", "SA_IMM_ATTR_SANAMET", self._saAmfClusterClmCluster)
        if self._SaImmAttrImplementerName != None:
            campaign.addAttribute("SaImmAttrImplementerName", "SA_IMM_ATTR_SASTRINGT", self._SaImmAttrImplementerName)
        if self._SaImmAttrClassName != None:
            campaign.addAttribute("SaImmAttrClassName", "SA_IMM_ATTR_SASTRINGT", self._SaImmAttrClassName)
        if self._SaImmAttrAdminOwnerName != None:
            campaign.addAttribute("SaImmAttrAdminOwnerName", "SA_IMM_ATTR_SASTRINGT", self._SaImmAttrAdminOwnerName)
        campaign.endCreate()

    def getsaAmfClusterStartupTimeout(self):
        ImmHelper.validateSingle(self._saAmfClusterStartupTimeout, self._dn, "saAmfClusterStartupTimeout")
        return self._saAmfClusterStartupTimeout

    def getsaAmfClusterClmCluster(self):
        ImmHelper.validateSingle(self._saAmfClusterClmCluster, self._dn, "saAmfClusterClmCluster")
        return self._saAmfClusterClmCluster

    def getsaAmfClusterAdminState(self):
        ImmHelper.validateSingle(self._saAmfClusterAdminState, self._dn, "saAmfClusterAdminState")
        return self._saAmfClusterAdminState

    def getSaImmAttrImplementerName(self):
        ImmHelper.validateSingle(self._SaImmAttrImplementerName, self._dn, "SaImmAttrImplementerName")
        return self._SaImmAttrImplementerName

    def getSaImmAttrClassName(self):
        ImmHelper.validateSingle(self._SaImmAttrClassName, self._dn, "SaImmAttrClassName")
        return self._SaImmAttrClassName

    def getSaImmAttrAdminOwnerName(self):
        ImmHelper.validateSingle(self._SaImmAttrAdminOwnerName, self._dn, "SaImmAttrAdminOwnerName")
        return self._SaImmAttrAdminOwnerName

    def getsaAmfClusterStartupTimeout_unsafe(self):
        return self._saAmfClusterStartupTimeout

    def getsaAmfClusterClmCluster_unsafe(self):
        return self._saAmfClusterClmCluster

    def getsaAmfClusterAdminState_unsafe(self):
        return self._saAmfClusterAdminState

    def getSaImmAttrImplementerName_unsafe(self):
        return self._SaImmAttrImplementerName

    def getSaImmAttrClassName_unsafe(self):
        return self._SaImmAttrClassName

    def getSaImmAttrAdminOwnerName_unsafe(self):
        return self._SaImmAttrAdminOwnerName

    def setsaAmfClusterStartupTimeout(self, value):
        ImmHelper.validateTime(value, self._dn, "saAmfClusterStartupTimeout")
        value = str(value)
        self._saAmfClusterStartupTimeout = value

    def setsaAmfClusterClmCluster(self, value):
        ImmHelper.validateName(value, self._dn, "saAmfClusterClmCluster")
        self._saAmfClusterClmCluster = value

    def setsaAmfClusterAdminState(self, value):
        ImmHelper.validateUint32(value, self._dn, "saAmfClusterAdminState")
        value = str(value)
        self._saAmfClusterAdminState = value

    def setSaImmAttrImplementerName(self, value):
        ImmHelper.validateString(value, self._dn, "SaImmAttrImplementerName")
        self._SaImmAttrImplementerName = value

    def setSaImmAttrClassName(self, value):
        ImmHelper.validateString(value, self._dn, "SaImmAttrClassName")
        self._SaImmAttrClassName = value

    def setSaImmAttrAdminOwnerName(self, value):
        ImmHelper.validateString(value, self._dn, "SaImmAttrAdminOwnerName")
        self._SaImmAttrAdminOwnerName = value

    def updateParams(self, params, canttouchthis):
        for (param, value) in params.items():
            if param in canttouchthis:
                error("Setting attribute " + param + " in object " + self.getDn() + " is not supported")
            if param == "saAmfClusterStartupTimeout":
                self.setsaAmfClusterStartupTimeout(value)
            elif param == "saAmfClusterClmCluster":
                self.setsaAmfClusterClmCluster(value)
            else:
                error("Object " + self.getDn() + " has no attribute named " + param)

    def diff(self, other, fullCheck = False):
        changedAttrs = []
        if (fullCheck or self._saAmfClusterStartupTimeout != None) and other._saAmfClusterStartupTimeout != self._saAmfClusterStartupTimeout:
            changedAttrs.append("saAmfClusterStartupTimeout")
        if (fullCheck or self._saAmfClusterClmCluster != None) and other._saAmfClusterClmCluster != self._saAmfClusterClmCluster:
            changedAttrs.append("saAmfClusterClmCluster")
        if (fullCheck or self._SaImmAttrImplementerName != None) and other._SaImmAttrImplementerName != self._SaImmAttrImplementerName:
            changedAttrs.append("SaImmAttrImplementerName")
        if (fullCheck or self._SaImmAttrClassName != None) and other._SaImmAttrClassName != self._SaImmAttrClassName:
            changedAttrs.append("SaImmAttrClassName")
        if (fullCheck or self._SaImmAttrAdminOwnerName != None) and other._SaImmAttrAdminOwnerName != self._SaImmAttrAdminOwnerName:
            changedAttrs.append("SaImmAttrAdminOwnerName")
        return changedAttrs

    def parseXML(self, node):
        dns = node.getElementsByTagName("dn")
        if len(dns) != 1:
            error("object has " + str(len(dns)) + " dn(s) but it should have one")
        self._dn = dns[0].childNodes[0].nodeValue
        for attribute in node.getElementsByTagName("attr"):
            names = attribute.getElementsByTagName("name")
            if len(names) != 1:
                error("object attribute has " + str(len(names)) + " name(s) but it should have one")
            name = names[0].childNodes[0].nodeValue
            setFunc = None
            if name == "SaImmAttrImplementerName":
                continue
            elif name == "SaImmAttrAdminOwnerName":
                continue
            elif name == "SaImmAttrClassName":
                continue
            elif name == "saAmfClusterStartupTimeout":
                setFunc = self.setsaAmfClusterStartupTimeout
            elif name == "saAmfClusterClmCluster":
                setFunc = self.setsaAmfClusterClmCluster
            elif name == "saAmfClusterAdminState":
                setFunc = self.setsaAmfClusterAdminState
            elif name == "SaImmAttrImplementerName":
                setFunc = self.setSaImmAttrImplementerName
            elif name == "SaImmAttrClassName":
                setFunc = self.setSaImmAttrClassName
            elif name == "SaImmAttrAdminOwnerName":
                setFunc = self.setSaImmAttrAdminOwnerName
            elif name.startswith("osaf"):
                continue # ignore OpenSAF specific attributes
            else:
                error("unknown attribute called " + name + " defined in object " + self._dn)
            for value in attribute.getElementsByTagName("value"):
                setFunc(value.childNodes[0].nodeValue)

    def writeXML(self, parent, doc):
        obj = doc.createElement("object")
        parent.appendChild(obj)
        obj.setAttribute("class", "SaAmfCluster")
        dn = doc.createElement("dn")
        obj.appendChild(dn)
        dn.appendChild(doc.createTextNode(self._dn))
        ImmHelper.writeSingleAttribute("saAmfClusterStartupTimeout", self._saAmfClusterStartupTimeout, doc, obj)
        ImmHelper.writeSingleAttribute("saAmfClusterClmCluster", self._saAmfClusterClmCluster, doc, obj)
        ImmHelper.writeSingleAttribute("saAmfClusterAdminState", self._saAmfClusterAdminState, doc, obj)
        ImmHelper.writeSingleAttribute("SaImmAttrImplementerName", self._SaImmAttrImplementerName, doc, obj)
        ImmHelper.writeSingleAttribute("SaImmAttrClassName", self._SaImmAttrClassName, doc, obj)
        ImmHelper.writeSingleAttribute("SaImmAttrAdminOwnerName", self._SaImmAttrAdminOwnerName, doc, obj)


class SaAmfCSType(object):
    def __init__(self):
        self._dn = None
        self._saAmfCSAttrName = []
        self._SaImmAttrImplementerName = None
        self._SaImmAttrClassName = None
        self._SaImmAttrAdminOwnerName = None

    @staticmethod
    def createDn(name, parentDn = None):
        if parentDn == None:
            parentDn = ""
        else:
            parentDn = "," + parentDn
        return "safVersion=" + ImmHelper.escapeName(name) + parentDn

    def getDn(self):
        return self._dn

    def getName(self):
        return ImmHelper.getName(self._dn)

    def getRdn(self):
        return ImmHelper.getRdn(self._dn)

    def getParentDn(self):
        return ImmHelper.getParentDn(self._dn)

    def createObjectInCampaign(self, campaign):
        parentDn = self.getParentDn()
        if parentDn == "":
            parentDn = "="
        campaign.beginCreate("SaAmfCSType", parentDn)
        campaign.addAttribute("safVersion", "SA_IMM_ATTR_SASTRINGT", self.getRdn())
        if len(self._saAmfCSAttrName) > 0:
            campaign.addAttribute("saAmfCSAttrName", "SA_IMM_ATTR_SASTRINGT", self._saAmfCSAttrName)
        if self._SaImmAttrImplementerName != None:
            campaign.addAttribute("SaImmAttrImplementerName", "SA_IMM_ATTR_SASTRINGT", self._SaImmAttrImplementerName)
        if self._SaImmAttrClassName != None:
            campaign.addAttribute("SaImmAttrClassName", "SA_IMM_ATTR_SASTRINGT", self._SaImmAttrClassName)
        if self._SaImmAttrAdminOwnerName != None:
            campaign.addAttribute("SaImmAttrAdminOwnerName", "SA_IMM_ATTR_SASTRINGT", self._SaImmAttrAdminOwnerName)
        campaign.endCreate()

    def getsaAmfCSAttrName(self):
        return self._saAmfCSAttrName

    def getSaImmAttrImplementerName(self):
        ImmHelper.validateSingle(self._SaImmAttrImplementerName, self._dn, "SaImmAttrImplementerName")
        return self._SaImmAttrImplementerName

    def getSaImmAttrClassName(self):
        ImmHelper.validateSingle(self._SaImmAttrClassName, self._dn, "SaImmAttrClassName")
        return self._SaImmAttrClassName

    def getSaImmAttrAdminOwnerName(self):
        ImmHelper.validateSingle(self._SaImmAttrAdminOwnerName, self._dn, "SaImmAttrAdminOwnerName")
        return self._SaImmAttrAdminOwnerName

    def getsaAmfCSAttrName_single(self):
        ImmHelper.validateSingleInList(self._saAmfCSAttrName, self._dn, "saAmfCSAttrName")
        return self._saAmfCSAttrName[0]

    def getSaImmAttrImplementerName_unsafe(self):
        return self._SaImmAttrImplementerName

    def getSaImmAttrClassName_unsafe(self):
        return self._SaImmAttrClassName

    def getSaImmAttrAdminOwnerName_unsafe(self):
        return self._SaImmAttrAdminOwnerName

    def addTosaAmfCSAttrName(self, value):
        ImmHelper.validateString(value, self._dn, "saAmfCSAttrName")
        self._saAmfCSAttrName.append(value)

    def setSaImmAttrImplementerName(self, value):
        ImmHelper.validateString(value, self._dn, "SaImmAttrImplementerName")
        self._SaImmAttrImplementerName = value

    def setSaImmAttrClassName(self, value):
        ImmHelper.validateString(value, self._dn, "SaImmAttrClassName")
        self._SaImmAttrClassName = value

    def setSaImmAttrAdminOwnerName(self, value):
        ImmHelper.validateString(value, self._dn, "SaImmAttrAdminOwnerName")
        self._SaImmAttrAdminOwnerName = value

    def updateParams(self, params, canttouchthis):
        for (param, value) in params.items():
            if param in canttouchthis:
                error("Setting attribute " + param + " in object " + self.getDn() + " is not supported")
            if param == "saAmfCSAttrName":
                if not isinstance(value, list):
                    value = [value]
                self._saAmfCSAttrName = []
                for v in value:
                    self.addTosaAmfCSAttrName(v)
            else:
                error("Object " + self.getDn() + " has no attribute named " + param)

    def diff(self, other, fullCheck = False):
        changedAttrs = []
        if fullCheck or (len(self._saAmfCSAttrName) != 0):
            if len(self._saAmfCSAttrName) != len(other._saAmfCSAttrName):
                changedAttrs.append("saAmfCSAttrName")
            else:
                difflist = list(set(self._saAmfCSAttrName) ^ set(other._saAmfCSAttrName))
                if len(difflist) > 0:
                    changedAttrs.append("saAmfCSAttrName")
        if (fullCheck or self._SaImmAttrImplementerName != None) and other._SaImmAttrImplementerName != self._SaImmAttrImplementerName:
            changedAttrs.append("SaImmAttrImplementerName")
        if (fullCheck or self._SaImmAttrClassName != None) and other._SaImmAttrClassName != self._SaImmAttrClassName:
            changedAttrs.append("SaImmAttrClassName")
        if (fullCheck or self._SaImmAttrAdminOwnerName != None) and other._SaImmAttrAdminOwnerName != self._SaImmAttrAdminOwnerName:
            changedAttrs.append("SaImmAttrAdminOwnerName")
        return changedAttrs

    def parseXML(self, node):
        dns = node.getElementsByTagName("dn")
        if len(dns) != 1:
            error("object has " + str(len(dns)) + " dn(s) but it should have one")
        self._dn = dns[0].childNodes[0].nodeValue
        for attribute in node.getElementsByTagName("attr"):
            names = attribute.getElementsByTagName("name")
            if len(names) != 1:
                error("object attribute has " + str(len(names)) + " name(s) but it should have one")
            name = names[0].childNodes[0].nodeValue
            setFunc = None
            if name == "SaImmAttrImplementerName":
                continue
            elif name == "SaImmAttrAdminOwnerName":
                continue
            elif name == "SaImmAttrClassName":
                continue
            elif name == "saAmfCSAttrName":
                setFunc = self.addTosaAmfCSAttrName
            elif name == "SaImmAttrImplementerName":
                setFunc = self.setSaImmAttrImplementerName
            elif name == "SaImmAttrClassName":
                setFunc = self.setSaImmAttrClassName
            elif name == "SaImmAttrAdminOwnerName":
                setFunc = self.setSaImmAttrAdminOwnerName
            elif name.startswith("osaf"):
                continue # ignore OpenSAF specific attributes
            else:
                error("unknown attribute called " + name + " defined in object " + self._dn)
            for value in attribute.getElementsByTagName("value"):
                setFunc(value.childNodes[0].nodeValue)

    def writeXML(self, parent, doc):
        obj = doc.createElement("object")
        parent.appendChild(obj)
        obj.setAttribute("class", "SaAmfCSType")
        dn = doc.createElement("dn")
        obj.appendChild(dn)
        dn.appendChild(doc.createTextNode(self._dn))
        ImmHelper.writeMultiAttributes("saAmfCSAttrName", self._saAmfCSAttrName, doc, obj)
        ImmHelper.writeSingleAttribute("SaImmAttrImplementerName", self._SaImmAttrImplementerName, doc, obj)
        ImmHelper.writeSingleAttribute("SaImmAttrClassName", self._SaImmAttrClassName, doc, obj)
        ImmHelper.writeSingleAttribute("SaImmAttrAdminOwnerName", self._SaImmAttrAdminOwnerName, doc, obj)


class SaAmfCSIAttribute(object):
    def __init__(self):
        self._dn = None
        self._saAmfCSIAttriValue = []
        self._SaImmAttrImplementerName = None
        self._SaImmAttrClassName = None
        self._SaImmAttrAdminOwnerName = None

    @staticmethod
    def createDn(name, parentDn = None):
        if parentDn == None:
            parentDn = ""
        else:
            parentDn = "," + parentDn
        return "safCsiAttr=" + ImmHelper.escapeName(name) + parentDn

    def getDn(self):
        return self._dn

    def getName(self):
        return ImmHelper.getName(self._dn)

    def getRdn(self):
        return ImmHelper.getRdn(self._dn)

    def getParentDn(self):
        return ImmHelper.getParentDn(self._dn)

    def createObjectInCampaign(self, campaign):
        parentDn = self.getParentDn()
        if parentDn == "":
            parentDn = "="
        campaign.beginCreate("SaAmfCSIAttribute", parentDn)
        campaign.addAttribute("safCsiAttr", "SA_IMM_ATTR_SASTRINGT", self.getRdn())
        if len(self._saAmfCSIAttriValue) > 0:
            campaign.addAttribute("saAmfCSIAttriValue", "SA_IMM_ATTR_SASTRINGT", self._saAmfCSIAttriValue)
        if self._SaImmAttrImplementerName != None:
            campaign.addAttribute("SaImmAttrImplementerName", "SA_IMM_ATTR_SASTRINGT", self._SaImmAttrImplementerName)
        if self._SaImmAttrClassName != None:
            campaign.addAttribute("SaImmAttrClassName", "SA_IMM_ATTR_SASTRINGT", self._SaImmAttrClassName)
        if self._SaImmAttrAdminOwnerName != None:
            campaign.addAttribute("SaImmAttrAdminOwnerName", "SA_IMM_ATTR_SASTRINGT", self._SaImmAttrAdminOwnerName)
        campaign.endCreate()

    def getsaAmfCSIAttriValue(self):
        return self._saAmfCSIAttriValue

    def getSaImmAttrImplementerName(self):
        ImmHelper.validateSingle(self._SaImmAttrImplementerName, self._dn, "SaImmAttrImplementerName")
        return self._SaImmAttrImplementerName

    def getSaImmAttrClassName(self):
        ImmHelper.validateSingle(self._SaImmAttrClassName, self._dn, "SaImmAttrClassName")
        return self._SaImmAttrClassName

    def getSaImmAttrAdminOwnerName(self):
        ImmHelper.validateSingle(self._SaImmAttrAdminOwnerName, self._dn, "SaImmAttrAdminOwnerName")
        return self._SaImmAttrAdminOwnerName

    def getsaAmfCSIAttriValue_single(self):
        ImmHelper.validateSingleInList(self._saAmfCSIAttriValue, self._dn, "saAmfCSIAttriValue")
        return self._saAmfCSIAttriValue[0]

    def getSaImmAttrImplementerName_unsafe(self):
        return self._SaImmAttrImplementerName

    def getSaImmAttrClassName_unsafe(self):
        return self._SaImmAttrClassName

    def getSaImmAttrAdminOwnerName_unsafe(self):
        return self._SaImmAttrAdminOwnerName

    def addTosaAmfCSIAttriValue(self, value):
        ImmHelper.validateString(value, self._dn, "saAmfCSIAttriValue")
        self._saAmfCSIAttriValue.append(value)

    def setSaImmAttrImplementerName(self, value):
        ImmHelper.validateString(value, self._dn, "SaImmAttrImplementerName")
        self._SaImmAttrImplementerName = value

    def setSaImmAttrClassName(self, value):
        ImmHelper.validateString(value, self._dn, "SaImmAttrClassName")
        self._SaImmAttrClassName = value

    def setSaImmAttrAdminOwnerName(self, value):
        ImmHelper.validateString(value, self._dn, "SaImmAttrAdminOwnerName")
        self._SaImmAttrAdminOwnerName = value

    def updateParams(self, params, canttouchthis):
        for (param, value) in params.items():
            if param in canttouchthis:
                error("Setting attribute " + param + " in object " + self.getDn() + " is not supported")
            if param == "saAmfCSIAttriValue":
                if not isinstance(value, list):
                    value = [value]
                self._saAmfCSIAttriValue = []
                for v in value:
                    self.addTosaAmfCSIAttriValue(v)
            else:
                error("Object " + self.getDn() + " has no attribute named " + param)

    def diff(self, other, fullCheck = False):
        changedAttrs = []
        if fullCheck or (len(self._saAmfCSIAttriValue) != 0):
            if len(self._saAmfCSIAttriValue) != len(other._saAmfCSIAttriValue):
                changedAttrs.append("saAmfCSIAttriValue")
            else:
                difflist = list(set(self._saAmfCSIAttriValue) ^ set(other._saAmfCSIAttriValue))
                if len(difflist) > 0:
                    changedAttrs.append("saAmfCSIAttriValue")
        if (fullCheck or self._SaImmAttrImplementerName != None) and other._SaImmAttrImplementerName != self._SaImmAttrImplementerName:
            changedAttrs.append("SaImmAttrImplementerName")
        if (fullCheck or self._SaImmAttrClassName != None) and other._SaImmAttrClassName != self._SaImmAttrClassName:
            changedAttrs.append("SaImmAttrClassName")
        if (fullCheck or self._SaImmAttrAdminOwnerName != None) and other._SaImmAttrAdminOwnerName != self._SaImmAttrAdminOwnerName:
            changedAttrs.append("SaImmAttrAdminOwnerName")
        return changedAttrs

    def parseXML(self, node):
        dns = node.getElementsByTagName("dn")
        if len(dns) != 1:
            error("object has " + str(len(dns)) + " dn(s) but it should have one")
        self._dn = dns[0].childNodes[0].nodeValue
        for attribute in node.getElementsByTagName("attr"):
            names = attribute.getElementsByTagName("name")
            if len(names) != 1:
                error("object attribute has " + str(len(names)) + " name(s) but it should have one")
            name = names[0].childNodes[0].nodeValue
            setFunc = None
            if name == "SaImmAttrImplementerName":
                continue
            elif name == "SaImmAttrAdminOwnerName":
                continue
            elif name == "SaImmAttrClassName":
                continue
            elif name == "saAmfCSIAttriValue":
                setFunc = self.addTosaAmfCSIAttriValue
            elif name == "SaImmAttrImplementerName":
                setFunc = self.setSaImmAttrImplementerName
            elif name == "SaImmAttrClassName":
                setFunc = self.setSaImmAttrClassName
            elif name == "SaImmAttrAdminOwnerName":
                setFunc = self.setSaImmAttrAdminOwnerName
            elif name.startswith("osaf"):
                continue # ignore OpenSAF specific attributes
            else:
                error("unknown attribute called " + name + " defined in object " + self._dn)
            for value in attribute.getElementsByTagName("value"):
                setFunc(value.childNodes[0].nodeValue)

    def writeXML(self, parent, doc):
        obj = doc.createElement("object")
        parent.appendChild(obj)
        obj.setAttribute("class", "SaAmfCSIAttribute")
        dn = doc.createElement("dn")
        obj.appendChild(dn)
        dn.appendChild(doc.createTextNode(self._dn))
        ImmHelper.writeMultiAttributes("saAmfCSIAttriValue", self._saAmfCSIAttriValue, doc, obj)
        ImmHelper.writeSingleAttribute("SaImmAttrImplementerName", self._SaImmAttrImplementerName, doc, obj)
        ImmHelper.writeSingleAttribute("SaImmAttrClassName", self._SaImmAttrClassName, doc, obj)
        ImmHelper.writeSingleAttribute("SaImmAttrAdminOwnerName", self._SaImmAttrAdminOwnerName, doc, obj)


class SaAmfCSIAssignment(object):
    def __init__(self):
        self._dn = None
        self._saAmfCSICompHAState = None
        self._saAmfCSICompHAReadinessState = None
        self._SaImmAttrImplementerName = None
        self._SaImmAttrClassName = None
        self._SaImmAttrAdminOwnerName = None

    @staticmethod
    def createDn(name, parentDn = None):
        if parentDn == None:
            parentDn = ""
        else:
            parentDn = "," + parentDn
        return "safCSIComp=" + ImmHelper.escapeName(name) + parentDn

    def getDn(self):
        return self._dn

    def getName(self):
        return ImmHelper.getName(self._dn)

    def getRdn(self):
        return ImmHelper.getRdn(self._dn)

    def getParentDn(self):
        return ImmHelper.getParentDn(self._dn)

    def createObjectInCampaign(self, campaign):
        parentDn = self.getParentDn()
        if parentDn == "":
            parentDn = "="
        campaign.beginCreate("SaAmfCSIAssignment", parentDn)
        campaign.addAttribute("safCSIComp", "SA_IMM_ATTR_SANAMET", self.getRdn())
        campaign.endCreate()

    def getsaAmfCSICompHAState(self):
        ImmHelper.validateSingle(self._saAmfCSICompHAState, self._dn, "saAmfCSICompHAState")
        return self._saAmfCSICompHAState

    def getsaAmfCSICompHAReadinessState(self):
        ImmHelper.validateSingle(self._saAmfCSICompHAReadinessState, self._dn, "saAmfCSICompHAReadinessState")
        return self._saAmfCSICompHAReadinessState

    def getSaImmAttrImplementerName(self):
        ImmHelper.validateSingle(self._SaImmAttrImplementerName, self._dn, "SaImmAttrImplementerName")
        return self._SaImmAttrImplementerName

    def getSaImmAttrClassName(self):
        ImmHelper.validateSingle(self._SaImmAttrClassName, self._dn, "SaImmAttrClassName")
        return self._SaImmAttrClassName

    def getSaImmAttrAdminOwnerName(self):
        ImmHelper.validateSingle(self._SaImmAttrAdminOwnerName, self._dn, "SaImmAttrAdminOwnerName")
        return self._SaImmAttrAdminOwnerName

    def getsaAmfCSICompHAState_unsafe(self):
        return self._saAmfCSICompHAState

    def getsaAmfCSICompHAReadinessState_unsafe(self):
        return self._saAmfCSICompHAReadinessState

    def getSaImmAttrImplementerName_unsafe(self):
        return self._SaImmAttrImplementerName

    def getSaImmAttrClassName_unsafe(self):
        return self._SaImmAttrClassName

    def getSaImmAttrAdminOwnerName_unsafe(self):
        return self._SaImmAttrAdminOwnerName

    def setsaAmfCSICompHAState(self, value):
        ImmHelper.validateUint32(value, self._dn, "saAmfCSICompHAState")
        value = str(value)
        self._saAmfCSICompHAState = value

    def setsaAmfCSICompHAReadinessState(self, value):
        ImmHelper.validateUint32(value, self._dn, "saAmfCSICompHAReadinessState")
        value = str(value)
        self._saAmfCSICompHAReadinessState = value

    def setSaImmAttrImplementerName(self, value):
        ImmHelper.validateString(value, self._dn, "SaImmAttrImplementerName")
        self._SaImmAttrImplementerName = value

    def setSaImmAttrClassName(self, value):
        ImmHelper.validateString(value, self._dn, "SaImmAttrClassName")
        self._SaImmAttrClassName = value

    def setSaImmAttrAdminOwnerName(self, value):
        ImmHelper.validateString(value, self._dn, "SaImmAttrAdminOwnerName")
        self._SaImmAttrAdminOwnerName = value

    def updateParams(self, params, canttouchthis):
        for (param, value) in params.items():
            if param in canttouchthis:
                error("Setting attribute " + param + " in object " + self.getDn() + " is not supported")
            else:
                error("Object " + self.getDn() + " has no attribute named " + param)

    def diff(self, other, fullCheck = False):
        changedAttrs = []
        return changedAttrs

    def parseXML(self, node):
        dns = node.getElementsByTagName("dn")
        if len(dns) != 1:
            error("object has " + str(len(dns)) + " dn(s) but it should have one")
        self._dn = dns[0].childNodes[0].nodeValue
        for attribute in node.getElementsByTagName("attr"):
            names = attribute.getElementsByTagName("name")
            if len(names) != 1:
                error("object attribute has " + str(len(names)) + " name(s) but it should have one")
            name = names[0].childNodes[0].nodeValue
            setFunc = None
            if name == "SaImmAttrImplementerName":
                continue
            elif name == "SaImmAttrAdminOwnerName":
                continue
            elif name == "SaImmAttrClassName":
                continue
            elif name == "saAmfCSICompHAState":
                setFunc = self.setsaAmfCSICompHAState
            elif name == "saAmfCSICompHAReadinessState":
                setFunc = self.setsaAmfCSICompHAReadinessState
            elif name == "SaImmAttrImplementerName":
                setFunc = self.setSaImmAttrImplementerName
            elif name == "SaImmAttrClassName":
                setFunc = self.setSaImmAttrClassName
            elif name == "SaImmAttrAdminOwnerName":
                setFunc = self.setSaImmAttrAdminOwnerName
            elif name.startswith("osaf"):
                continue # ignore OpenSAF specific attributes
            else:
                error("unknown attribute called " + name + " defined in object " + self._dn)
            for value in attribute.getElementsByTagName("value"):
                setFunc(value.childNodes[0].nodeValue)

    def writeXML(self, parent, doc):
        obj = doc.createElement("object")
        parent.appendChild(obj)
        obj.setAttribute("class", "SaAmfCSIAssignment")
        dn = doc.createElement("dn")
        obj.appendChild(dn)
        dn.appendChild(doc.createTextNode(self._dn))
        ImmHelper.writeSingleAttribute("saAmfCSICompHAState", self._saAmfCSICompHAState, doc, obj)
        ImmHelper.writeSingleAttribute("saAmfCSICompHAReadinessState", self._saAmfCSICompHAReadinessState, doc, obj)
        ImmHelper.writeSingleAttribute("SaImmAttrImplementerName", self._SaImmAttrImplementerName, doc, obj)
        ImmHelper.writeSingleAttribute("SaImmAttrClassName", self._SaImmAttrClassName, doc, obj)
        ImmHelper.writeSingleAttribute("SaImmAttrAdminOwnerName", self._SaImmAttrAdminOwnerName, doc, obj)


class SaAmfCSI(object):
    def __init__(self):
        self._dn = None
        self._saAmfCSType = None
        self._saAmfCSIDependencies = []
        self._SaImmAttrImplementerName = None
        self._SaImmAttrClassName = None
        self._SaImmAttrAdminOwnerName = None

    @staticmethod
    def createDn(name, parentDn = None):
        if parentDn == None:
            parentDn = ""
        else:
            parentDn = "," + parentDn
        return "safCsi=" + ImmHelper.escapeName(name) + parentDn

    def getDn(self):
        return self._dn

    def getName(self):
        return ImmHelper.getName(self._dn)

    def getRdn(self):
        return ImmHelper.getRdn(self._dn)

    def getParentDn(self):
        return ImmHelper.getParentDn(self._dn)

    def createObjectInCampaign(self, campaign):
        parentDn = self.getParentDn()
        if parentDn == "":
            parentDn = "="
        campaign.beginCreate("SaAmfCSI", parentDn)
        campaign.addAttribute("safCsi", "SA_IMM_ATTR_SASTRINGT", self.getRdn())
        if self._saAmfCSType != None:
            campaign.addAttribute("saAmfCSType", "SA_IMM_ATTR_SANAMET", self._saAmfCSType)
        if len(self._saAmfCSIDependencies) > 0:
            campaign.addAttribute("saAmfCSIDependencies", "SA_IMM_ATTR_SANAMET", self._saAmfCSIDependencies)
        if self._SaImmAttrImplementerName != None:
            campaign.addAttribute("SaImmAttrImplementerName", "SA_IMM_ATTR_SASTRINGT", self._SaImmAttrImplementerName)
        if self._SaImmAttrClassName != None:
            campaign.addAttribute("SaImmAttrClassName", "SA_IMM_ATTR_SASTRINGT", self._SaImmAttrClassName)
        if self._SaImmAttrAdminOwnerName != None:
            campaign.addAttribute("SaImmAttrAdminOwnerName", "SA_IMM_ATTR_SASTRINGT", self._SaImmAttrAdminOwnerName)
        campaign.endCreate()

    def getsaAmfCSType(self):
        ImmHelper.validateSingle(self._saAmfCSType, self._dn, "saAmfCSType")
        return self._saAmfCSType

    def getsaAmfCSIDependencies(self):
        return self._saAmfCSIDependencies

    def getSaImmAttrImplementerName(self):
        ImmHelper.validateSingle(self._SaImmAttrImplementerName, self._dn, "SaImmAttrImplementerName")
        return self._SaImmAttrImplementerName

    def getSaImmAttrClassName(self):
        ImmHelper.validateSingle(self._SaImmAttrClassName, self._dn, "SaImmAttrClassName")
        return self._SaImmAttrClassName

    def getSaImmAttrAdminOwnerName(self):
        ImmHelper.validateSingle(self._SaImmAttrAdminOwnerName, self._dn, "SaImmAttrAdminOwnerName")
        return self._SaImmAttrAdminOwnerName

    def getsaAmfCSType_unsafe(self):
        return self._saAmfCSType

    def getsaAmfCSIDependencies_single(self):
        ImmHelper.validateSingleInList(self._saAmfCSIDependencies, self._dn, "saAmfCSIDependencies")
        return self._saAmfCSIDependencies[0]

    def getSaImmAttrImplementerName_unsafe(self):
        return self._SaImmAttrImplementerName

    def getSaImmAttrClassName_unsafe(self):
        return self._SaImmAttrClassName

    def getSaImmAttrAdminOwnerName_unsafe(self):
        return self._SaImmAttrAdminOwnerName

    def setsaAmfCSType(self, value):
        ImmHelper.validateName(value, self._dn, "saAmfCSType")
        self._saAmfCSType = value

    def addTosaAmfCSIDependencies(self, value):
        ImmHelper.validateName(value, self._dn, "saAmfCSIDependencies")
        self._saAmfCSIDependencies.append(value)

    def setSaImmAttrImplementerName(self, value):
        ImmHelper.validateString(value, self._dn, "SaImmAttrImplementerName")
        self._SaImmAttrImplementerName = value

    def setSaImmAttrClassName(self, value):
        ImmHelper.validateString(value, self._dn, "SaImmAttrClassName")
        self._SaImmAttrClassName = value

    def setSaImmAttrAdminOwnerName(self, value):
        ImmHelper.validateString(value, self._dn, "SaImmAttrAdminOwnerName")
        self._SaImmAttrAdminOwnerName = value

    def updateParams(self, params, canttouchthis):
        for (param, value) in params.items():
            if param in canttouchthis:
                error("Setting attribute " + param + " in object " + self.getDn() + " is not supported")
            if param == "saAmfCSType":
                self.setsaAmfCSType(value)
            elif param == "saAmfCSIDependencies":
                if not isinstance(value, list):
                    value = [value]
                self._saAmfCSIDependencies = []
                for v in value:
                    self.addTosaAmfCSIDependencies(v)
            else:
                error("Object " + self.getDn() + " has no attribute named " + param)

    def diff(self, other, fullCheck = False):
        changedAttrs = []
        if (fullCheck or self._saAmfCSType != None) and other._saAmfCSType != self._saAmfCSType:
            changedAttrs.append("saAmfCSType")
        if fullCheck or (len(self._saAmfCSIDependencies) != 0):
            if len(self._saAmfCSIDependencies) != len(other._saAmfCSIDependencies):
                changedAttrs.append("saAmfCSIDependencies")
            else:
                difflist = list(set(self._saAmfCSIDependencies) ^ set(other._saAmfCSIDependencies))
                if len(difflist) > 0:
                    changedAttrs.append("saAmfCSIDependencies")
        if (fullCheck or self._SaImmAttrImplementerName != None) and other._SaImmAttrImplementerName != self._SaImmAttrImplementerName:
            changedAttrs.append("SaImmAttrImplementerName")
        if (fullCheck or self._SaImmAttrClassName != None) and other._SaImmAttrClassName != self._SaImmAttrClassName:
            changedAttrs.append("SaImmAttrClassName")
        if (fullCheck or self._SaImmAttrAdminOwnerName != None) and other._SaImmAttrAdminOwnerName != self._SaImmAttrAdminOwnerName:
            changedAttrs.append("SaImmAttrAdminOwnerName")
        return changedAttrs

    def parseXML(self, node):
        dns = node.getElementsByTagName("dn")
        if len(dns) != 1:
            error("object has " + str(len(dns)) + " dn(s) but it should have one")
        self._dn = dns[0].childNodes[0].nodeValue
        for attribute in node.getElementsByTagName("attr"):
            names = attribute.getElementsByTagName("name")
            if len(names) != 1:
                error("object attribute has " + str(len(names)) + " name(s) but it should have one")
            name = names[0].childNodes[0].nodeValue
            setFunc = None
            if name == "SaImmAttrImplementerName":
                continue
            elif name == "SaImmAttrAdminOwnerName":
                continue
            elif name == "SaImmAttrClassName":
                continue
            elif name == "saAmfCSType":
                setFunc = self.setsaAmfCSType
            elif name == "saAmfCSIDependencies":
                setFunc = self.addTosaAmfCSIDependencies
            elif name == "SaImmAttrImplementerName":
                setFunc = self.setSaImmAttrImplementerName
            elif name == "SaImmAttrClassName":
                setFunc = self.setSaImmAttrClassName
            elif name == "SaImmAttrAdminOwnerName":
                setFunc = self.setSaImmAttrAdminOwnerName
            elif name.startswith("osaf"):
                continue # ignore OpenSAF specific attributes
            else:
                error("unknown attribute called " + name + " defined in object " + self._dn)
            for value in attribute.getElementsByTagName("value"):
                setFunc(value.childNodes[0].nodeValue)

    def writeXML(self, parent, doc):
        obj = doc.createElement("object")
        parent.appendChild(obj)
        obj.setAttribute("class", "SaAmfCSI")
        dn = doc.createElement("dn")
        obj.appendChild(dn)
        dn.appendChild(doc.createTextNode(self._dn))
        ImmHelper.writeSingleAttribute("saAmfCSType", self._saAmfCSType, doc, obj)
        ImmHelper.writeMultiAttributes("saAmfCSIDependencies", self._saAmfCSIDependencies, doc, obj)
        ImmHelper.writeSingleAttribute("SaImmAttrImplementerName", self._SaImmAttrImplementerName, doc, obj)
        ImmHelper.writeSingleAttribute("SaImmAttrClassName", self._SaImmAttrClassName, doc, obj)
        ImmHelper.writeSingleAttribute("SaImmAttrAdminOwnerName", self._SaImmAttrAdminOwnerName, doc, obj)


class SaAmfCSBaseType(object):
    def __init__(self):
        self._dn = None
        self._SaImmAttrImplementerName = None
        self._SaImmAttrClassName = None
        self._SaImmAttrAdminOwnerName = None

    @staticmethod
    def createDn(name, parentDn = None):
        if parentDn == None:
            parentDn = ""
        else:
            parentDn = "," + parentDn
        return "safCSType=" + ImmHelper.escapeName(name) + parentDn

    def getDn(self):
        return self._dn

    def getName(self):
        return ImmHelper.getName(self._dn)

    def getRdn(self):
        return ImmHelper.getRdn(self._dn)

    def getParentDn(self):
        return ImmHelper.getParentDn(self._dn)

    def createObjectInCampaign(self, campaign):
        parentDn = self.getParentDn()
        if parentDn == "":
            parentDn = "="
        campaign.beginCreate("SaAmfCSBaseType", parentDn)
        campaign.addAttribute("safCSType", "SA_IMM_ATTR_SASTRINGT", self.getRdn())
        if self._SaImmAttrImplementerName != None:
            campaign.addAttribute("SaImmAttrImplementerName", "SA_IMM_ATTR_SASTRINGT", self._SaImmAttrImplementerName)
        if self._SaImmAttrClassName != None:
            campaign.addAttribute("SaImmAttrClassName", "SA_IMM_ATTR_SASTRINGT", self._SaImmAttrClassName)
        if self._SaImmAttrAdminOwnerName != None:
            campaign.addAttribute("SaImmAttrAdminOwnerName", "SA_IMM_ATTR_SASTRINGT", self._SaImmAttrAdminOwnerName)
        campaign.endCreate()

    def getSaImmAttrImplementerName(self):
        ImmHelper.validateSingle(self._SaImmAttrImplementerName, self._dn, "SaImmAttrImplementerName")
        return self._SaImmAttrImplementerName

    def getSaImmAttrClassName(self):
        ImmHelper.validateSingle(self._SaImmAttrClassName, self._dn, "SaImmAttrClassName")
        return self._SaImmAttrClassName

    def getSaImmAttrAdminOwnerName(self):
        ImmHelper.validateSingle(self._SaImmAttrAdminOwnerName, self._dn, "SaImmAttrAdminOwnerName")
        return self._SaImmAttrAdminOwnerName

    def getSaImmAttrImplementerName_unsafe(self):
        return self._SaImmAttrImplementerName

    def getSaImmAttrClassName_unsafe(self):
        return self._SaImmAttrClassName

    def getSaImmAttrAdminOwnerName_unsafe(self):
        return self._SaImmAttrAdminOwnerName

    def setSaImmAttrImplementerName(self, value):
        ImmHelper.validateString(value, self._dn, "SaImmAttrImplementerName")
        self._SaImmAttrImplementerName = value

    def setSaImmAttrClassName(self, value):
        ImmHelper.validateString(value, self._dn, "SaImmAttrClassName")
        self._SaImmAttrClassName = value

    def setSaImmAttrAdminOwnerName(self, value):
        ImmHelper.validateString(value, self._dn, "SaImmAttrAdminOwnerName")
        self._SaImmAttrAdminOwnerName = value

    def updateParams(self, params, canttouchthis):
        for (param, value) in params.items():
            if param in canttouchthis:
                error("Setting attribute " + param + " in object " + self.getDn() + " is not supported")
            else:
                error("Object " + self.getDn() + " has no attribute named " + param)

    def diff(self, other, fullCheck = False):
        changedAttrs = []
        if (fullCheck or self._SaImmAttrImplementerName != None) and other._SaImmAttrImplementerName != self._SaImmAttrImplementerName:
            changedAttrs.append("SaImmAttrImplementerName")
        if (fullCheck or self._SaImmAttrClassName != None) and other._SaImmAttrClassName != self._SaImmAttrClassName:
            changedAttrs.append("SaImmAttrClassName")
        if (fullCheck or self._SaImmAttrAdminOwnerName != None) and other._SaImmAttrAdminOwnerName != self._SaImmAttrAdminOwnerName:
            changedAttrs.append("SaImmAttrAdminOwnerName")
        return changedAttrs

    def parseXML(self, node):
        dns = node.getElementsByTagName("dn")
        if len(dns) != 1:
            error("object has " + str(len(dns)) + " dn(s) but it should have one")
        self._dn = dns[0].childNodes[0].nodeValue
        for attribute in node.getElementsByTagName("attr"):
            names = attribute.getElementsByTagName("name")
            if len(names) != 1:
                error("object attribute has " + str(len(names)) + " name(s) but it should have one")
            name = names[0].childNodes[0].nodeValue
            setFunc = None
            if name == "SaImmAttrImplementerName":
                continue
            elif name == "SaImmAttrAdminOwnerName":
                continue
            elif name == "SaImmAttrClassName":
                continue
            elif name == "SaImmAttrImplementerName":
                setFunc = self.setSaImmAttrImplementerName
            elif name == "SaImmAttrClassName":
                setFunc = self.setSaImmAttrClassName
            elif name == "SaImmAttrAdminOwnerName":
                setFunc = self.setSaImmAttrAdminOwnerName
            elif name.startswith("osaf"):
                continue # ignore OpenSAF specific attributes
            else:
                error("unknown attribute called " + name + " defined in object " + self._dn)
            for value in attribute.getElementsByTagName("value"):
                setFunc(value.childNodes[0].nodeValue)

    def writeXML(self, parent, doc):
        obj = doc.createElement("object")
        parent.appendChild(obj)
        obj.setAttribute("class", "SaAmfCSBaseType")
        dn = doc.createElement("dn")
        obj.appendChild(dn)
        dn.appendChild(doc.createTextNode(self._dn))
        ImmHelper.writeSingleAttribute("SaImmAttrImplementerName", self._SaImmAttrImplementerName, doc, obj)
        ImmHelper.writeSingleAttribute("SaImmAttrClassName", self._SaImmAttrClassName, doc, obj)
        ImmHelper.writeSingleAttribute("SaImmAttrAdminOwnerName", self._SaImmAttrAdminOwnerName, doc, obj)


class SaAmfApplication(object):
    def __init__(self):
        self._dn = None
        self._saAmfApplicationCurrNumSGs = None
        self._saAmfApplicationAdminState = None
        self._saAmfAppType = None
        self._SaImmAttrImplementerName = None
        self._SaImmAttrClassName = None
        self._SaImmAttrAdminOwnerName = None

    @staticmethod
    def createDn(name, parentDn = None):
        if parentDn == None:
            parentDn = ""
        else:
            parentDn = "," + parentDn
        return "safApp=" + ImmHelper.escapeName(name) + parentDn

    def getDn(self):
        return self._dn

    def getName(self):
        return ImmHelper.getName(self._dn)

    def getRdn(self):
        return ImmHelper.getRdn(self._dn)

    def getParentDn(self):
        return ImmHelper.getParentDn(self._dn)

    def createObjectInCampaign(self, campaign):
        parentDn = self.getParentDn()
        if parentDn == "":
            parentDn = "="
        campaign.beginCreate("SaAmfApplication", parentDn)
        campaign.addAttribute("safApp", "SA_IMM_ATTR_SASTRINGT", self.getRdn())
        if self._saAmfAppType != None:
            campaign.addAttribute("saAmfAppType", "SA_IMM_ATTR_SANAMET", self._saAmfAppType)
        if self._SaImmAttrImplementerName != None:
            campaign.addAttribute("SaImmAttrImplementerName", "SA_IMM_ATTR_SASTRINGT", self._SaImmAttrImplementerName)
        if self._SaImmAttrClassName != None:
            campaign.addAttribute("SaImmAttrClassName", "SA_IMM_ATTR_SASTRINGT", self._SaImmAttrClassName)
        if self._SaImmAttrAdminOwnerName != None:
            campaign.addAttribute("SaImmAttrAdminOwnerName", "SA_IMM_ATTR_SASTRINGT", self._SaImmAttrAdminOwnerName)
        campaign.endCreate()

    def getsaAmfApplicationCurrNumSGs(self):
        ImmHelper.validateSingle(self._saAmfApplicationCurrNumSGs, self._dn, "saAmfApplicationCurrNumSGs")
        return self._saAmfApplicationCurrNumSGs

    def getsaAmfApplicationAdminState(self):
        ImmHelper.validateSingle(self._saAmfApplicationAdminState, self._dn, "saAmfApplicationAdminState")
        return self._saAmfApplicationAdminState

    def getsaAmfAppType(self):
        ImmHelper.validateSingle(self._saAmfAppType, self._dn, "saAmfAppType")
        return self._saAmfAppType

    def getSaImmAttrImplementerName(self):
        ImmHelper.validateSingle(self._SaImmAttrImplementerName, self._dn, "SaImmAttrImplementerName")
        return self._SaImmAttrImplementerName

    def getSaImmAttrClassName(self):
        ImmHelper.validateSingle(self._SaImmAttrClassName, self._dn, "SaImmAttrClassName")
        return self._SaImmAttrClassName

    def getSaImmAttrAdminOwnerName(self):
        ImmHelper.validateSingle(self._SaImmAttrAdminOwnerName, self._dn, "SaImmAttrAdminOwnerName")
        return self._SaImmAttrAdminOwnerName

    def getsaAmfApplicationCurrNumSGs_unsafe(self):
        return self._saAmfApplicationCurrNumSGs

    def getsaAmfApplicationAdminState_unsafe(self):
        return self._saAmfApplicationAdminState

    def getsaAmfAppType_unsafe(self):
        return self._saAmfAppType

    def getSaImmAttrImplementerName_unsafe(self):
        return self._SaImmAttrImplementerName

    def getSaImmAttrClassName_unsafe(self):
        return self._SaImmAttrClassName

    def getSaImmAttrAdminOwnerName_unsafe(self):
        return self._SaImmAttrAdminOwnerName

    def setsaAmfApplicationCurrNumSGs(self, value):
        ImmHelper.validateUint32(value, self._dn, "saAmfApplicationCurrNumSGs")
        value = str(value)
        self._saAmfApplicationCurrNumSGs = value

    def setsaAmfApplicationAdminState(self, value):
        ImmHelper.validateUint32(value, self._dn, "saAmfApplicationAdminState")
        value = str(value)
        self._saAmfApplicationAdminState = value

    def setsaAmfAppType(self, value):
        ImmHelper.validateName(value, self._dn, "saAmfAppType")
        self._saAmfAppType = value

    def setSaImmAttrImplementerName(self, value):
        ImmHelper.validateString(value, self._dn, "SaImmAttrImplementerName")
        self._SaImmAttrImplementerName = value

    def setSaImmAttrClassName(self, value):
        ImmHelper.validateString(value, self._dn, "SaImmAttrClassName")
        self._SaImmAttrClassName = value

    def setSaImmAttrAdminOwnerName(self, value):
        ImmHelper.validateString(value, self._dn, "SaImmAttrAdminOwnerName")
        self._SaImmAttrAdminOwnerName = value

    def updateParams(self, params, canttouchthis):
        for (param, value) in params.items():
            if param in canttouchthis:
                error("Setting attribute " + param + " in object " + self.getDn() + " is not supported")
            if param == "saAmfAppType":
                self.setsaAmfAppType(value)
            else:
                error("Object " + self.getDn() + " has no attribute named " + param)

    def diff(self, other, fullCheck = False):
        changedAttrs = []
        if (fullCheck or self._saAmfAppType != None) and other._saAmfAppType != self._saAmfAppType:
            changedAttrs.append("saAmfAppType")
        if (fullCheck or self._SaImmAttrImplementerName != None) and other._SaImmAttrImplementerName != self._SaImmAttrImplementerName:
            changedAttrs.append("SaImmAttrImplementerName")
        if (fullCheck or self._SaImmAttrClassName != None) and other._SaImmAttrClassName != self._SaImmAttrClassName:
            changedAttrs.append("SaImmAttrClassName")
        if (fullCheck or self._SaImmAttrAdminOwnerName != None) and other._SaImmAttrAdminOwnerName != self._SaImmAttrAdminOwnerName:
            changedAttrs.append("SaImmAttrAdminOwnerName")
        return changedAttrs

    def parseXML(self, node):
        dns = node.getElementsByTagName("dn")
        if len(dns) != 1:
            error("object has " + str(len(dns)) + " dn(s) but it should have one")
        self._dn = dns[0].childNodes[0].nodeValue
        for attribute in node.getElementsByTagName("attr"):
            names = attribute.getElementsByTagName("name")
            if len(names) != 1:
                error("object attribute has " + str(len(names)) + " name(s) but it should have one")
            name = names[0].childNodes[0].nodeValue
            setFunc = None
            if name == "SaImmAttrImplementerName":
                continue
            elif name == "SaImmAttrAdminOwnerName":
                continue
            elif name == "SaImmAttrClassName":
                continue
            elif name == "saAmfApplicationCurrNumSGs":
                setFunc = self.setsaAmfApplicationCurrNumSGs
            elif name == "saAmfApplicationAdminState":
                setFunc = self.setsaAmfApplicationAdminState
            elif name == "saAmfAppType":
                setFunc = self.setsaAmfAppType
            elif name == "SaImmAttrImplementerName":
                setFunc = self.setSaImmAttrImplementerName
            elif name == "SaImmAttrClassName":
                setFunc = self.setSaImmAttrClassName
            elif name == "SaImmAttrAdminOwnerName":
                setFunc = self.setSaImmAttrAdminOwnerName
            elif name.startswith("osaf"):
                continue # ignore OpenSAF specific attributes
            else:
                error("unknown attribute called " + name + " defined in object " + self._dn)
            for value in attribute.getElementsByTagName("value"):
                setFunc(value.childNodes[0].nodeValue)

    def writeXML(self, parent, doc):
        obj = doc.createElement("object")
        parent.appendChild(obj)
        obj.setAttribute("class", "SaAmfApplication")
        dn = doc.createElement("dn")
        obj.appendChild(dn)
        dn.appendChild(doc.createTextNode(self._dn))
        ImmHelper.writeSingleAttribute("saAmfApplicationCurrNumSGs", self._saAmfApplicationCurrNumSGs, doc, obj)
        ImmHelper.writeSingleAttribute("saAmfApplicationAdminState", self._saAmfApplicationAdminState, doc, obj)
        ImmHelper.writeSingleAttribute("saAmfAppType", self._saAmfAppType, doc, obj)
        ImmHelper.writeSingleAttribute("SaImmAttrImplementerName", self._SaImmAttrImplementerName, doc, obj)
        ImmHelper.writeSingleAttribute("SaImmAttrClassName", self._SaImmAttrClassName, doc, obj)
        ImmHelper.writeSingleAttribute("SaImmAttrAdminOwnerName", self._SaImmAttrAdminOwnerName, doc, obj)


class SaAmfAppType(object):
    def __init__(self):
        self._dn = None
        self._saAmfApptSGTypes = []
        self._SaImmAttrImplementerName = None
        self._SaImmAttrClassName = None
        self._SaImmAttrAdminOwnerName = None

    @staticmethod
    def createDn(name, parentDn = None):
        if parentDn == None:
            parentDn = ""
        else:
            parentDn = "," + parentDn
        return "safVersion=" + ImmHelper.escapeName(name) + parentDn

    def getDn(self):
        return self._dn

    def getName(self):
        return ImmHelper.getName(self._dn)

    def getRdn(self):
        return ImmHelper.getRdn(self._dn)

    def getParentDn(self):
        return ImmHelper.getParentDn(self._dn)

    def createObjectInCampaign(self, campaign):
        parentDn = self.getParentDn()
        if parentDn == "":
            parentDn = "="
        campaign.beginCreate("SaAmfAppType", parentDn)
        campaign.addAttribute("safVersion", "SA_IMM_ATTR_SASTRINGT", self.getRdn())
        if len(self._saAmfApptSGTypes) > 0:
            campaign.addAttribute("saAmfApptSGTypes", "SA_IMM_ATTR_SANAMET", self._saAmfApptSGTypes)
        if self._SaImmAttrImplementerName != None:
            campaign.addAttribute("SaImmAttrImplementerName", "SA_IMM_ATTR_SASTRINGT", self._SaImmAttrImplementerName)
        if self._SaImmAttrClassName != None:
            campaign.addAttribute("SaImmAttrClassName", "SA_IMM_ATTR_SASTRINGT", self._SaImmAttrClassName)
        if self._SaImmAttrAdminOwnerName != None:
            campaign.addAttribute("SaImmAttrAdminOwnerName", "SA_IMM_ATTR_SASTRINGT", self._SaImmAttrAdminOwnerName)
        campaign.endCreate()

    def getsaAmfApptSGTypes(self):
        return self._saAmfApptSGTypes

    def getSaImmAttrImplementerName(self):
        ImmHelper.validateSingle(self._SaImmAttrImplementerName, self._dn, "SaImmAttrImplementerName")
        return self._SaImmAttrImplementerName

    def getSaImmAttrClassName(self):
        ImmHelper.validateSingle(self._SaImmAttrClassName, self._dn, "SaImmAttrClassName")
        return self._SaImmAttrClassName

    def getSaImmAttrAdminOwnerName(self):
        ImmHelper.validateSingle(self._SaImmAttrAdminOwnerName, self._dn, "SaImmAttrAdminOwnerName")
        return self._SaImmAttrAdminOwnerName

    def getsaAmfApptSGTypes_single(self):
        ImmHelper.validateSingleInList(self._saAmfApptSGTypes, self._dn, "saAmfApptSGTypes")
        return self._saAmfApptSGTypes[0]

    def getSaImmAttrImplementerName_unsafe(self):
        return self._SaImmAttrImplementerName

    def getSaImmAttrClassName_unsafe(self):
        return self._SaImmAttrClassName

    def getSaImmAttrAdminOwnerName_unsafe(self):
        return self._SaImmAttrAdminOwnerName

    def addTosaAmfApptSGTypes(self, value):
        ImmHelper.validateName(value, self._dn, "saAmfApptSGTypes")
        self._saAmfApptSGTypes.append(value)

    def setSaImmAttrImplementerName(self, value):
        ImmHelper.validateString(value, self._dn, "SaImmAttrImplementerName")
        self._SaImmAttrImplementerName = value

    def setSaImmAttrClassName(self, value):
        ImmHelper.validateString(value, self._dn, "SaImmAttrClassName")
        self._SaImmAttrClassName = value

    def setSaImmAttrAdminOwnerName(self, value):
        ImmHelper.validateString(value, self._dn, "SaImmAttrAdminOwnerName")
        self._SaImmAttrAdminOwnerName = value

    def updateParams(self, params, canttouchthis):
        for (param, value) in params.items():
            if param in canttouchthis:
                error("Setting attribute " + param + " in object " + self.getDn() + " is not supported")
            if param == "saAmfApptSGTypes":
                if not isinstance(value, list):
                    value = [value]
                self._saAmfApptSGTypes = []
                for v in value:
                    self.addTosaAmfApptSGTypes(v)
            else:
                error("Object " + self.getDn() + " has no attribute named " + param)

    def diff(self, other, fullCheck = False):
        changedAttrs = []
        if fullCheck or (len(self._saAmfApptSGTypes) != 0):
            if len(self._saAmfApptSGTypes) != len(other._saAmfApptSGTypes):
                changedAttrs.append("saAmfApptSGTypes")
            else:
                difflist = list(set(self._saAmfApptSGTypes) ^ set(other._saAmfApptSGTypes))
                if len(difflist) > 0:
                    changedAttrs.append("saAmfApptSGTypes")
        if (fullCheck or self._SaImmAttrImplementerName != None) and other._SaImmAttrImplementerName != self._SaImmAttrImplementerName:
            changedAttrs.append("SaImmAttrImplementerName")
        if (fullCheck or self._SaImmAttrClassName != None) and other._SaImmAttrClassName != self._SaImmAttrClassName:
            changedAttrs.append("SaImmAttrClassName")
        if (fullCheck or self._SaImmAttrAdminOwnerName != None) and other._SaImmAttrAdminOwnerName != self._SaImmAttrAdminOwnerName:
            changedAttrs.append("SaImmAttrAdminOwnerName")
        return changedAttrs

    def parseXML(self, node):
        dns = node.getElementsByTagName("dn")
        if len(dns) != 1:
            error("object has " + str(len(dns)) + " dn(s) but it should have one")
        self._dn = dns[0].childNodes[0].nodeValue
        for attribute in node.getElementsByTagName("attr"):
            names = attribute.getElementsByTagName("name")
            if len(names) != 1:
                error("object attribute has " + str(len(names)) + " name(s) but it should have one")
            name = names[0].childNodes[0].nodeValue
            setFunc = None
            if name == "SaImmAttrImplementerName":
                continue
            elif name == "SaImmAttrAdminOwnerName":
                continue
            elif name == "SaImmAttrClassName":
                continue
            elif name == "saAmfApptSGTypes":
                setFunc = self.addTosaAmfApptSGTypes
            elif name == "SaImmAttrImplementerName":
                setFunc = self.setSaImmAttrImplementerName
            elif name == "SaImmAttrClassName":
                setFunc = self.setSaImmAttrClassName
            elif name == "SaImmAttrAdminOwnerName":
                setFunc = self.setSaImmAttrAdminOwnerName
            elif name.startswith("osaf"):
                continue # ignore OpenSAF specific attributes
            else:
                error("unknown attribute called " + name + " defined in object " + self._dn)
            for value in attribute.getElementsByTagName("value"):
                setFunc(value.childNodes[0].nodeValue)

    def writeXML(self, parent, doc):
        obj = doc.createElement("object")
        parent.appendChild(obj)
        obj.setAttribute("class", "SaAmfAppType")
        dn = doc.createElement("dn")
        obj.appendChild(dn)
        dn.appendChild(doc.createTextNode(self._dn))
        ImmHelper.writeMultiAttributes("saAmfApptSGTypes", self._saAmfApptSGTypes, doc, obj)
        ImmHelper.writeSingleAttribute("SaImmAttrImplementerName", self._SaImmAttrImplementerName, doc, obj)
        ImmHelper.writeSingleAttribute("SaImmAttrClassName", self._SaImmAttrClassName, doc, obj)
        ImmHelper.writeSingleAttribute("SaImmAttrAdminOwnerName", self._SaImmAttrAdminOwnerName, doc, obj)


class SaAmfAppBaseType(object):
    def __init__(self):
        self._dn = None
        self._SaImmAttrImplementerName = None
        self._SaImmAttrClassName = None
        self._SaImmAttrAdminOwnerName = None

    @staticmethod
    def createDn(name, parentDn = None):
        if parentDn == None:
            parentDn = ""
        else:
            parentDn = "," + parentDn
        return "safAppType=" + ImmHelper.escapeName(name) + parentDn

    def getDn(self):
        return self._dn

    def getName(self):
        return ImmHelper.getName(self._dn)

    def getRdn(self):
        return ImmHelper.getRdn(self._dn)

    def getParentDn(self):
        return ImmHelper.getParentDn(self._dn)

    def createObjectInCampaign(self, campaign):
        parentDn = self.getParentDn()
        if parentDn == "":
            parentDn = "="
        campaign.beginCreate("SaAmfAppBaseType", parentDn)
        campaign.addAttribute("safAppType", "SA_IMM_ATTR_SASTRINGT", self.getRdn())
        if self._SaImmAttrImplementerName != None:
            campaign.addAttribute("SaImmAttrImplementerName", "SA_IMM_ATTR_SASTRINGT", self._SaImmAttrImplementerName)
        if self._SaImmAttrClassName != None:
            campaign.addAttribute("SaImmAttrClassName", "SA_IMM_ATTR_SASTRINGT", self._SaImmAttrClassName)
        if self._SaImmAttrAdminOwnerName != None:
            campaign.addAttribute("SaImmAttrAdminOwnerName", "SA_IMM_ATTR_SASTRINGT", self._SaImmAttrAdminOwnerName)
        campaign.endCreate()

    def getSaImmAttrImplementerName(self):
        ImmHelper.validateSingle(self._SaImmAttrImplementerName, self._dn, "SaImmAttrImplementerName")
        return self._SaImmAttrImplementerName

    def getSaImmAttrClassName(self):
        ImmHelper.validateSingle(self._SaImmAttrClassName, self._dn, "SaImmAttrClassName")
        return self._SaImmAttrClassName

    def getSaImmAttrAdminOwnerName(self):
        ImmHelper.validateSingle(self._SaImmAttrAdminOwnerName, self._dn, "SaImmAttrAdminOwnerName")
        return self._SaImmAttrAdminOwnerName

    def getSaImmAttrImplementerName_unsafe(self):
        return self._SaImmAttrImplementerName

    def getSaImmAttrClassName_unsafe(self):
        return self._SaImmAttrClassName

    def getSaImmAttrAdminOwnerName_unsafe(self):
        return self._SaImmAttrAdminOwnerName

    def setSaImmAttrImplementerName(self, value):
        ImmHelper.validateString(value, self._dn, "SaImmAttrImplementerName")
        self._SaImmAttrImplementerName = value

    def setSaImmAttrClassName(self, value):
        ImmHelper.validateString(value, self._dn, "SaImmAttrClassName")
        self._SaImmAttrClassName = value

    def setSaImmAttrAdminOwnerName(self, value):
        ImmHelper.validateString(value, self._dn, "SaImmAttrAdminOwnerName")
        self._SaImmAttrAdminOwnerName = value

    def updateParams(self, params, canttouchthis):
        for (param, value) in params.items():
            if param in canttouchthis:
                error("Setting attribute " + param + " in object " + self.getDn() + " is not supported")
            else:
                error("Object " + self.getDn() + " has no attribute named " + param)

    def diff(self, other, fullCheck = False):
        changedAttrs = []
        if (fullCheck or self._SaImmAttrImplementerName != None) and other._SaImmAttrImplementerName != self._SaImmAttrImplementerName:
            changedAttrs.append("SaImmAttrImplementerName")
        if (fullCheck or self._SaImmAttrClassName != None) and other._SaImmAttrClassName != self._SaImmAttrClassName:
            changedAttrs.append("SaImmAttrClassName")
        if (fullCheck or self._SaImmAttrAdminOwnerName != None) and other._SaImmAttrAdminOwnerName != self._SaImmAttrAdminOwnerName:
            changedAttrs.append("SaImmAttrAdminOwnerName")
        return changedAttrs

    def parseXML(self, node):
        dns = node.getElementsByTagName("dn")
        if len(dns) != 1:
            error("object has " + str(len(dns)) + " dn(s) but it should have one")
        self._dn = dns[0].childNodes[0].nodeValue
        for attribute in node.getElementsByTagName("attr"):
            names = attribute.getElementsByTagName("name")
            if len(names) != 1:
                error("object attribute has " + str(len(names)) + " name(s) but it should have one")
            name = names[0].childNodes[0].nodeValue
            setFunc = None
            if name == "SaImmAttrImplementerName":
                continue
            elif name == "SaImmAttrAdminOwnerName":
                continue
            elif name == "SaImmAttrClassName":
                continue
            elif name == "SaImmAttrImplementerName":
                setFunc = self.setSaImmAttrImplementerName
            elif name == "SaImmAttrClassName":
                setFunc = self.setSaImmAttrClassName
            elif name == "SaImmAttrAdminOwnerName":
                setFunc = self.setSaImmAttrAdminOwnerName
            elif name.startswith("osaf"):
                continue # ignore OpenSAF specific attributes
            else:
                error("unknown attribute called " + name + " defined in object " + self._dn)
            for value in attribute.getElementsByTagName("value"):
                setFunc(value.childNodes[0].nodeValue)

    def writeXML(self, parent, doc):
        obj = doc.createElement("object")
        parent.appendChild(obj)
        obj.setAttribute("class", "SaAmfAppBaseType")
        dn = doc.createElement("dn")
        obj.appendChild(dn)
        dn.appendChild(doc.createTextNode(self._dn))
        ImmHelper.writeSingleAttribute("SaImmAttrImplementerName", self._SaImmAttrImplementerName, doc, obj)
        ImmHelper.writeSingleAttribute("SaImmAttrClassName", self._SaImmAttrClassName, doc, obj)
        ImmHelper.writeSingleAttribute("SaImmAttrAdminOwnerName", self._SaImmAttrAdminOwnerName, doc, obj)
