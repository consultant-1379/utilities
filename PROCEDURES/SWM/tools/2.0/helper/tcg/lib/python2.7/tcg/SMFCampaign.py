import xml.dom.minidom
from utils.logger_tcg import tcg_error
import logging
import AMFConstants
import AMFTools
import CampaignGenerator
import re
from collections import defaultdict
from tcg.plugin_api.SMFApiObjects import CsmApiComputeResource
import ImmHelper
import AMFModel


def campaign_writexml(self, writer, indent="", addindent="", newl=""):
    """A redefinition of the writexml function.
    This is here because the CMWGETDN macro in the campaign looks like this:
    bundleDN='CMW_GETDN("^safSmfBundle=ERIC-LpmsvAgent-CXC1731620.*$","^safSmfBundle=ERIC-LpmsvAgent-CXC1731620-R3A16$")'
    This function replaces the quote of attribute values to apostrophes and also makes sure that nothing(!) is rewritten in the value.
    This is necessary because the double quotes in the value would be written as &quot; by the default xml writer
    and the CoreMW campaign generator is written in bash(why would anyone do that???) and expects the quotes written as a real quote characters"""
    # indent = current indentation
    # addindent = indentation to add to higher levels
    # newl = newline string
    writer.write(indent+"<" + self.tagName)

    attrs = self._get_attributes()
    a_names = attrs.keys()
    a_names.sort()

    for a_name in a_names:
        writer.write(" %s='%s'" % (a_name, attrs[a_name].value))
    if self.childNodes:
        if len(self.childNodes) == 1 \
          and self.childNodes[0].nodeType == xml.dom.minidom.Node.TEXT_NODE:
            writer.write(">")
            self.childNodes[0].writexml(writer, "", "", "")
            writer.write("</%s>%s" % (self.tagName, newl))
            return
        writer.write(">%s"%(newl))
        for node in self.childNodes:
            node.writexml(writer,indent+addindent,addindent,newl)
        writer.write("%s</%s>%s" % (indent,self.tagName,newl))
    else:
        writer.write("/>%s"%(newl))


def getValueByName(name, object):
    return eval("object._" + name)


class SMFCampaign(object):

    def __init__(self, campaignName, baseAmfModel):
        self._doc = xml.dom.minidom.Document()
        self._rootElement = self._doc.createElement("upgradeCampaign")
        self._rootElement.setAttribute("xmlns:xsi", "http://www.w3.org/2001/XMLSchema-instance")
        self._rootElement.setAttribute("safSmfCampaign", "safSmfCampaign=" + campaignName)
        self._rootElement.setAttribute("xsi:noNamespaceSchemaLocation", "SAI-AIS-SMF-UCS-A.01.02_OpenSAF.xsd")
        self._doc.appendChild(self._rootElement)
        campaignInfoElement = self._doc.createElement("campaignInfo")
        campaignPeriodElement = self._doc.createElement("campaignPeriod")
        self._rootElement.appendChild(campaignInfoElement)
        campaignInfoElement.appendChild(campaignPeriodElement)
        self._elements = [self._rootElement]
        self._softwareBundles = defaultdict(set)  #Contains list of softwares to nodes map that are part of this campaign
        self._removedBundles = {}  # Contains list of softwares to nodes map that this campaign will remove
        self._baseAmfModel = baseAmfModel
        # Store the uid's for already been handled units
        # Precondition: UID is unique in model
        self._needOneStepUpgrade = False

    def beginElement(self, elementName):
        element = self._doc.createElement(elementName)
        self.getCurrentElement().appendChild(element)
        self._elements.append(element)

    def addSoftwareBundleToNodes(self, sdpName, nodes = set()) :
        if not sdpName :
            tcg_error('Error: Software name cannot be empty')

        self._softwareBundles[sdpName].update(nodes)

    def getAddedSoftwareBundlesToNodes(self):
        return self._softwareBundles

    def addRemovedBundle(self, bundleName, nodes):
        self._removedBundles[bundleName] = nodes

    def getRemovedBundles(self):
        return self._removedBundles

    def popElement(self):
        self._elements.pop()

    def getCurrentElement(self):
        return self._elements[-1]

    def finish(self, fileName):
        xmlfile = open(fileName, "w")

        # replace the xml writer method, see the implementation of the campaign_writexml
        # for details
        orig_writexml = xml.dom.minidom.Element.writexml
        xml.dom.minidom.Element.writexml = campaign_writexml

        xmlfile.write(self._doc.toprettyxml(indent="  "))
        #self._doc.writexml(xml)
        xmlfile.close()
        xml.dom.minidom.Element.writexml = orig_writexml

    def beginObject(self, objectClassName, parentObjectDN):
        self.beginElement("create")
        self.getCurrentElement().setAttribute("objectClassName", objectClassName)
        self.getCurrentElement().setAttribute("parentObjectDN", parentObjectDN)

    def endObject(self):
        self.popElement()

    def generateWaitToCommit(self):
        self.beginElement("waitToCommit")
        self.popElement()

    def generateWaitToAllowNewCampaign(self):
        self.beginElement("waitToAllowNewCampaign")
        self.popElement()

    def beginCampaignWrapup(self):
        self.beginElement("campaignWrapup")

    def endCampaignWrapup(self):
        self.popElement()

    def beginCampaignInitialization(self):
        self.beginElement("campaignInitialization")

    def endCampaignInitialization(self):
        self.popElement()

    def beginAddToImm(self):
        self.beginElement("addToImm")

    def endAddToImm(self):
        self.popElement()

    def beginAmfEntityTypes(self):
        self.beginElement("amfEntityTypes")

    def endAmfEntityTypes(self):
        self.popElement()

    def beginUpgradeProcedure(self, name, executionLevel):
        self.beginElement("upgradeProcedure")
        self.getCurrentElement().setAttribute("safSmfProcedure", "safSmfProc=" + name)
        self.getCurrentElement().setAttribute("saSmfExecLevel", str(executionLevel))
        self.beginElement("outageInfo")
        self.beginElement("acceptableServiceOutage")
        self.beginElement("none")
        self.popElement()
        self.popElement()
        self.beginElement("procedurePeriod")
        self.getCurrentElement().setAttribute("saSmfProcPeriod", "600000000000")
        self.popElement()
        self.popElement()

    def endUpgradeProcedure(self):
        self.popElement()

    def beginUpgradeMethod(self):
        self.beginElement("upgradeMethod")

    def endUpgradeMethod(self):
        self.popElement()

    def beginSingleStepUpgrade(self):
        self.beginElement("singleStepUpgrade")

    def endSingleStepUpgrade(self):
        self.popElement()

    def beginUpgradeScope(self):
        self.beginElement("upgradeScope")

    def endUpgradeScope(self):
        self.popElement()

    def beginForAddRemove(self):
        self.beginElement("forAddRemove")

    def endForAddRemove(self):
        self.popElement()

    def beginDeactivationUnit(self):
        self.beginElement("deactivationUnit")

    def endDeactivationUnit(self):
        self.popElement()

    def beginActivationUnit(self):
        self.beginElement("activationUnit")

    def endActivationUnit(self):
        self.popElement()

    def beginProcInitAction(self):
        self.beginElement("procInitAction")

    def endProcInitAction(self):
        self.popElement()

    def beginProcWrapupAction(self):
        self.beginElement("procWrapupAction")

    def endProcWrapupAction(self):
        self.popElement()

    def beginImmCCB(self):
        self.beginElement("immCCB")
        self.getCurrentElement().setAttribute("ccbFlags", "0")

    def endImmCCB(self):
        self.popElement()

    def beginCreate(self, className, parentDn):
        self.beginElement("create")
        self.getCurrentElement().setAttribute("objectClassName", className)
        self.getCurrentElement().setAttribute("parentObjectDN", parentDn)

    def endCreate(self):
        self.popElement()

    def beginDelete(self, objectDn):
        self.beginElement("delete")
        self.getCurrentElement().setAttribute("objectDN", objectDn)

    def endDelete(self):
        self.popElement()

    def addAttribute(self, name, type_, values):
        self.beginElement("attribute")
        self.getCurrentElement().setAttribute("name", name)
        self.getCurrentElement().setAttribute("type", type_)
        if not isinstance(values, list):
            values = [values]
        for value in values:
            self.beginElement("value")
            self.getCurrentElement().appendChild(self._doc.createTextNode(value))
            self.popElement()
        self.popElement()

    def beginSwAdd(self, bundle, prefix):
        self.beginElement("swAdd")
        self.getCurrentElement().setAttribute("bundleDN", bundle)
        self.getCurrentElement().setAttribute("pathnamePrefix", prefix)

    def endSwAdd(self):
        self.popElement()

    def beginSwRemove(self, bundle, prefix):
        self.beginElement("swRemove")
        self.getCurrentElement().setAttribute("bundleDN", bundle)
        self.getCurrentElement().setAttribute("pathnamePrefix", prefix)

    def endSwRemove(self):
        self.popElement()

    def beginRemoved(self):
        self.beginElement("removed")

    def endRemoved(self):
        self.popElement()

    def beginActedOn(self):
        self.beginElement("actedOn")

    def endActedOn(self):
        self.popElement()

    def beginUpgradeStep(self, reboot=False):
        self.beginElement("upgradeStep")
        if reboot:
            self.getCurrentElement().setAttribute("saSmfStepRestartOption", "1")

    def beginCustomizationTime(self):
        self.beginElement("customizationTime")

    def generateOnStep(self, on_step):
        self.beginElement("onStep")
        self.beginElement(on_step)
        self.popElement()
        self.popElement()

    def generateAtAction(self, at_action):
        self.beginElement("atAction")
        self.beginElement(at_action)
        self.popElement()
        self.popElement()

    def endCustomizationTime(self):
        self.popElement()

    def generateRollingUpgradeStepCallbacks(self, procedureCTs, plugins):
        # generating upgrade step callbacks for rolling procedure
        callbacks = {}
        for ct in [x for x in procedureCTs if x in plugins]:
            current_callbacks = plugins[ct].callbackAtRollingUpgradeStep()
            for (label, timeout, stringToPass, on_step, at_action) in current_callbacks:
                if stringToPass in callbacks:
                    if timeout != callbacks[stringToPass]['timeout'] or \
                       stringToPass != callbacks[stringToPass]['stringToPass'] or \
                       on_step != callbacks[stringToPass]['on_step'] or \
                       at_action != callbacks[stringToPass]['at_action']:
                        tcg_error("Conflicting definition for callback %s in CTs %s versus CT %s" % (stringToPass, callbacks[stringToPass]['cts'], ct))
                    callbacks[stringToPass]['cts'].append(ct)
                else:
                    callbacks[stringToPass] = {'timeout': timeout, 'label': label, 'on_step': on_step, 'at_action': at_action, 'cts': [ct]}
        for (stringToPass, callback) in callbacks.items():
            self.beginCustomizationTime()
            self.generateOnStep(callback['on_step'])
            self.generateAtAction(callback['at_action'])
            self.endCustomizationTime()
            self.generateRollingUpgradeStepCallback(callback['label'], callback['timeout'], stringToPass)

    def generateRollingUpgradeStepCallback(self, callback_label, time, string_to_pass):
        self.beginElement("callback")
        self.getCurrentElement().setAttribute("callbackLabel", callback_label)
        self.getCurrentElement().setAttribute("time", time)
        self.getCurrentElement().setAttribute("stringToPass", string_to_pass)
        self.popElement()

    def endUpgradeStep(self):
        self.popElement()

    def generateByName(self, obj):
        self.beginElement("byName")
        self.getCurrentElement().setAttribute("objectDN", obj)
        self.popElement()

    def generateDoAdminOperation(self, obj, operation):
        self.beginElement("doAdminOperation")
        self.getCurrentElement().setAttribute("objectDN", obj)
        self.getCurrentElement().setAttribute("operationID", operation)
        self.popElement()

    def generateUndoAdminOperation(self, obj, operation):
        self.beginElement("undoAdminOperation")
        self.getCurrentElement().setAttribute("objectDN", obj)
        self.getCurrentElement().setAttribute("operationID", operation)
        self.popElement()

    def generatePlmExecEnv(self, node):
        self.beginElement("plmExecEnv")
        self.getCurrentElement().setAttribute("amfNode", node)
        self.popElement()

    def beginRollingUpgrade(self):
        self.beginElement("rollingUpgrade")

    def endRollingUpgrade(self):
        self.popElement()

    def beginByTemplate(self):
        self.beginElement("byTemplate")

    def endByTemplate(self):
        self.popElement()

    def beginTargetNodeTemplate(self, obj):
        self.beginElement("targetNodeTemplate")
        self.getCurrentElement().setAttribute("objectDN", obj)

    def endTargetNodeTemplate(self):
        self.popElement()

    def beginActivationUnitTemplate(self):
        self.beginElement("activationUnitTemplate")

    def endActivationUnitTemplate(self):
        self.popElement()

    def generateParent(self, obj):
        self.beginElement("parent")
        self.getCurrentElement().setAttribute("objectDN", obj)
        self.popElement()

    def _generateCallback(self, name, label, time, stringToPass):
        self.beginElement(name)
        self.getCurrentElement().setAttribute("callbackLabel", label)
        if time is not None:
            self.getCurrentElement().setAttribute("time", time)
        if stringToPass is not None:
            self.getCurrentElement().setAttribute("stringToPass", stringToPass)
        self.popElement()

    def generateCallbackAtInit(self, label, time = None, stringToPass = None):
        self._generateCallback("callbackAtInit", label, time, stringToPass)

    def generateCallbackAtRollback(self, label, time = None, stringToPass = None):
        self._generateCallback("callbackAtRollback", label, time, stringToPass)

    def generateCallbackAtCommit(self, label, time = None, stringToPass = None):
        self._generateCallback("callbackAtCommit", label, time, stringToPass)

    def generateCallback(self, label, time = None, stringToPass = None):
        self._generateCallback("callback", label, time, stringToPass)

    def beginCampInitAction(self):
        self.beginElement("campInitAction")

    def endCampInitAction(self):
        self.popElement()

    def beginCampCompleteAction(self):
        self.beginElement("campCompleteAction")

    def endCampCompleteAction(self):
        self.popElement()

    def beginCampWrapupAction(self):
        self.beginElement("campWrapupAction")

    def endCampWrapupAction(self):
        self.popElement()

    def generateDoCliCommand(self, cmd, args = None):
        self.beginElement("doCliCommand")
        self.getCurrentElement().setAttribute("command", cmd)
        if (args != None):
            self.getCurrentElement().setAttribute("args", args)
        self.popElement()

    def generateUndoCliCommand(self, cmd, args = None):
        self.beginElement("undoCliCommand")
        self.getCurrentElement().setAttribute("command", cmd)
        if (args != None):
            self.getCurrentElement().setAttribute("args", args)
        self.popElement()

    def generateAttributesFromMap(self, attrMap, obj, mandatory = False):

        for (group, attrs) in attrMap:
            self.beginElement(group)
            for attr in attrs:
                n = attr
                # this piece of code here lies to show how horribly the SMF campaign was 'designed'
                if attr == "safAmfSgtDefAutoAdjust":
                    n = "saAmfSgtDefAutoAdjust"
                if attr == "safAmfSgtDefAutoRepair":
                    n = "saAmfSgtDefAutoRepair"
                value = getValueByName(n, obj)
                if value is None:
                    if mandatory:
                        tcg_error("Mandatory attribute %s does not have a value" % (n))
                else:
                    self.getCurrentElement().setAttribute(attr, value)
            self.popElement()

    def generateCompTypeDefaults(self, compType, mandatory = False):
        attributeList = [ "saAmfCtCompCategory",
                                             "saAmfCtDefClcCliTimeout",
                                             "saAmfCtDefCallbackTimeout",
                                             "saAmfCtDefInstantiationLevel",
                                             "saAmfCtDefQuiescingCompleteTimeout",
                                             "saAmfCtDefRecoveryOnError",
                                             "saAmfCtDefDisableRestart" ]

        self.beginElement("compTypeDefaults")
        for attr in attributeList :
            value = getValueByName(attr, compType)
            if value is None:
                if mandatory:
                    tcg_error("Mandatory attribute %s does not have a value" % (attr))
            else:
                self.getCurrentElement().setAttribute(attr, value)

        for cmdEnv in compType.getsaAmfCtDefCmdEnv() :
            self.beginElement("cmdEnv")
            text = self._doc.createTextNode(cmdEnv)
            self.getCurrentElement().appendChild(text)
            self.popElement()

        self.popElement()

    def generateAppBaseType(self, appType):
        self.beginElement("AppBaseType")
        self.getCurrentElement().setAttribute("safAppType", appType.getParentDn())
        self.beginElement("AppType")
        self.getCurrentElement().setAttribute("safVersion", appType.getRdn())
        for sgType in appType.getsaAmfApptSGTypes():
            self.beginElement("serviceGroupType")
            self.getCurrentElement().setAttribute("saAmfApptSGTypes", sgType)
            self.popElement()
        self.popElement()
        self.popElement()

    def generateSGBaseType(self, sgType):
        attrMap = [ ("redundancy", [ "saAmfSgtRedundancyModel" ]),
                    ("compRestart", [ "saAmfSgtDefCompRestartProb", "saAmfSgtDefCompRestartMax"]),
                    ("suRestart", [ "saAmfSgtDefSuRestartProb", "saAmfSgtDefSuRestartMax" ]),
                    ("autoAttrs", [ "safAmfSgtDefAutoAdjust", "safAmfSgtDefAutoRepair", "saAmfSgtDefAutoAdjustProb" ])
                  ]
        self.beginElement("SGBaseType")
        self.getCurrentElement().setAttribute("safSgType", sgType.getParentDn())
        self.beginElement("SGType")
        self.getCurrentElement().setAttribute("safVersion", sgType.getRdn())
        for suType in sgType.getsaAmfSgtValidSuTypes():
            self.beginElement("suType")
            self.getCurrentElement().setAttribute("saAmfSgtValidSuTypes", suType)
            self.popElement()
        self.generateAttributesFromMap(attrMap, sgType)
        self.popElement()
        self.popElement()

    def generateSUBaseType(self, suType, sutCompTypes):
        attrMap = [ ("mandatoryAttrs", [ "saAmfSutIsExternal", "saAmfSutDefSUFailover" ]) ]
        self.beginElement("SUBaseType")
        self.getCurrentElement().setAttribute("safSuType", suType.getParentDn())
        self.beginElement("SUType")
        self.getCurrentElement().setAttribute("safVersion", suType.getRdn())
        self.generateAttributesFromMap(attrMap, suType, mandatory = True)
        for sutCompType in sutCompTypes:
            self.beginElement("componentType")
            saAmfSutMinNumComponents = sutCompType.getsaAmfSutMinNumComponents_unsafe()
            if saAmfSutMinNumComponents is not None:
                self.getCurrentElement().setAttribute("saAmfSutMinNumComponents", saAmfSutMinNumComponents)
            saAmfSutMaxNumComponents = sutCompType.getsaAmfSutMaxNumComponents_unsafe()
            if saAmfSutMaxNumComponents is not None:
                self.getCurrentElement().setAttribute("saAmfSutMaxNumComponents", saAmfSutMaxNumComponents)
            self.getCurrentElement().setAttribute("safMemberCompType", sutCompType.getRdn())
            self.popElement()
        for svcType in suType.getsaAmfSutProvidesSvcTypes():
            self.beginElement("supportedSvcType")
            self.getCurrentElement().setAttribute("saAmfSutProvidesSvcType", svcType)
            self.popElement()
        self.popElement()
        self.popElement()

    def generateCompBaseType(self, compType, ctCsTypes, healthcheckTypes):
        '''
        attrMap = [ ("compTypeDefaults",   [ "saAmfCtCompCategory",
                                             "saAmfCtDefClcCliTimeout",
                                             "saAmfCtDefCallbackTimeout",
                                             "saAmfCtDefInstantiationLevel",
                                             "saAmfCtDefQuiescingCompleteTimeout",
                                             "saAmfCtDefRecoveryOnError",
                                             "saAmfCtDefDisableRestart" ])
                  ]
        '''
        self.beginElement("CompBaseType")
        self.getCurrentElement().setAttribute("safCompType", compType.getParentDn())
        self.beginElement("CompType")
        self.getCurrentElement().setAttribute("safVersion", compType.getRdn())
        for ctCsType in ctCsTypes:
            self.beginElement("providesCSType")
            self.getCurrentElement().setAttribute("safSupportedCsType", ctCsType.getRdn())
            self.getCurrentElement().setAttribute("saAmfCtCompCapability", ctCsType.getsaAmfCtCompCapability())
            self.popElement()

        #self.generateAttributesFromMap(attrMap, compType)   #This function is replaced by the below function call
        self.generateCompTypeDefaults(compType)

        instantiate_cmd = compType.getsaAmfCtRelPathInstantiateCmd_unsafe()
        if instantiate_cmd:
            self.beginElement("instantiateCmd")
            self.getCurrentElement().setAttribute("saAmfCtRelPathInstantiateCmd", instantiate_cmd)
            for arg in compType.getsaAmfCtDefInstantiateCmdArgv():
                self.beginElement("cmdArgv")
                text = self._doc.createTextNode(arg)
                self.getCurrentElement().appendChild(text)
                self.popElement()
            self.popElement()

        terminateCmd = compType.getsaAmfCtRelPathTerminateCmd_unsafe()
        if terminateCmd:
            self.beginElement("terminateCmd")
            self.getCurrentElement().setAttribute("saAmfCtRelPathTerminateCmd", terminateCmd)
            for arg in compType.getsaAmfCtDefTerminateCmdArgv():
                self.beginElement("cmdArgv")
                text = self._doc.createTextNode(arg)
                self.getCurrentElement().appendChild(text)
                self.popElement()
            self.popElement()

        self.beginElement("cleanupCmd")
        self.getCurrentElement().setAttribute("saAmfCtRelPathCleanupCmd", compType.getsaAmfCtRelPathCleanupCmd())
        for arg in compType.getsaAmfCtDefCleanupCmdArgv():
            self.beginElement("cmdArgv")
            text = self._doc.createTextNode(arg)
            self.getCurrentElement().appendChild(text)
            self.popElement()
        self.popElement()

        if int(compType.getsaAmfCtCompCategory()) & AMFConstants.SA_AMF_COMP_LOCAL:
            hcCmd = compType.getosafAmfCtRelPathHcCmd_unsafe()
            if hcCmd:
                self.beginElement("osafHcCmd")
                self.getCurrentElement().setAttribute("osafAmfCtRelPathHcCmd", hcCmd)
                for arg in compType.getosafAmfCtDefHcCmdArgv():
                    self.beginElement("cmdArgv")
                    text = self._doc.createTextNode(arg)
                    self.getCurrentElement().appendChild(text)
                    self.popElement()
                self.popElement()

        for hct in healthcheckTypes:
            self.beginElement("healthCheck")
            self.getCurrentElement().setAttribute("safHealthcheckKey", hct.getRdn())
            saAmfHealthcheckPeriod = hct.getsaAmfHctDefPeriod()
            if saAmfHealthcheckPeriod is not None:
                self.getCurrentElement().setAttribute("saAmfHealthcheckPeriod", saAmfHealthcheckPeriod)
            saAmfHealthcheckMaxDuration = hct.getsaAmfHctDefMaxDuration()
            if saAmfHealthcheckMaxDuration is not None:
                self.getCurrentElement().setAttribute("saAmfHealthcheckMaxDuration", saAmfHealthcheckMaxDuration)
            self.popElement()
        sw_bundle = compType.getsaAmfCtSwBundle_unsafe()
        if sw_bundle is not None and sw_bundle != '':
            self.beginElement("swBundle")
            self.getCurrentElement().setAttribute("saAmfCtSwBundle", sw_bundle)
            self.popElement()
        self.popElement()
        self.popElement()

    def generateCSBaseType(self, csType):
        self.beginElement("CSBaseType")
        self.getCurrentElement().setAttribute("safCSType", csType.getParentDn())
        self.beginElement("CSType")
        self.getCurrentElement().setAttribute("safVersion", csType.getRdn())
        for csAttribute in csType.getsaAmfCSAttrName():
            self.beginElement("csAttribute")
            self.getCurrentElement().setAttribute("saAmfCSAttrName", csAttribute)
            self.popElement()
        self.popElement()
        self.popElement()

    def generateServiceBaseType(self, svcType, svcTypeCsTypes):
        self.beginElement("ServiceBaseType")
        self.getCurrentElement().setAttribute("safSvcType", svcType.getParentDn())
        self.beginElement("ServiceType")
        self.getCurrentElement().setAttribute("safVersion", svcType.getRdn())
        for csType in svcTypeCsTypes:
            self.beginElement("csType")
            self.getCurrentElement().setAttribute("safMemberCSType", csType.getRdn())
            saAmfSvctMaxNumCSIs = csType.getsaAmfSvctMaxNumCSIs_unsafe()
            if saAmfSvctMaxNumCSIs is not None:
                self.getCurrentElement().setAttribute("saAmfSvctMaxNumCSIs", saAmfSvctMaxNumCSIs)
            self.popElement()
        self.popElement()
        self.popElement()

    def get_installed_nodes_for_bundle_name(self, bundleName):
        match_pattern = 'safInstalledSwBundle=safSmfBundle=' + bundleName + ','
        installed_nodes = set()
        for nodeSwBundle in self._baseAmfModel.getObjects(AMFModel.SaAmfNodeSwBundle).keys():
            if nodeSwBundle.startswith(match_pattern):
                installed_nodes.add(AMFTools.getNodeNameFromNodeDn(ImmHelper.getParentDn(nodeSwBundle)))
        return installed_nodes

    def skip_generate_markup_tag(self, matchDn):
        prog = re.compile(matchDn)
        for objDn in self._baseAmfModel.getObjects().keys():
            if prog.match(objDn):
                return True
        return False

    # Below interface is reverted for backward compatibility reason.
    # Will be removed soon when vDicos adapted with the new interface.
    def generateExcludeIf(self, pattern):
        # <!-- CMW_CAMPAIGN_XML_EXCLUDE_IF(<pattern>) -->
        comment = self._doc.createComment("CMW_CAMPAIGN_XML_EXCLUDE_IF(" + pattern + ")")
        self.getCurrentElement().appendChild(comment)

    def generateExcludeFi(self):
        # <!-- CMW_CAMPAIGN_XML_EXCLUDE_FI -->
        comment = self._doc.createComment("CMW_CAMPAIGN_XML_EXCLUDE_FI")
        self.getCurrentElement().appendChild(comment)

    def generateIncludeIf(self, pattern):
        # <!-- CMW_CAMPAIGN_XML_INCLUDE_IF(<pattern>) -->
        comment = self._doc.createComment("CMW_CAMPAIGN_XML_INCLUDE_IF(" + pattern + ")")
        self.getCurrentElement().appendChild(comment)

    def generateIncludeFi(self):
        # <!-- CMW_CAMPAIGN_XML_INCLUDE_FI -->
        comment = self._doc.createComment("CMW_CAMPAIGN_XML_INCLUDE_FI")
        self.getCurrentElement().appendChild(comment)

    def generateIncludeIfCmd(self, cmd):
        # <!-- CMW_CAMPAIGN_XML_INCLUDE_IF_CMD(<pattern>) -->
        comment = self._doc.createComment("CMW_CAMPAIGN_XML_INCLUDE_IF_CMD(" + cmd + ")")
        self.getCurrentElement().appendChild(comment)

    def generateIncludeFiCmd(self):
        # <!-- CMW_CAMPAIGN_XML_INCLUDE_FI_CMD -->
        comment = self._doc.createComment("CMW_CAMPAIGN_XML_INCLUDE_FI_CMD")
        self.getCurrentElement().appendChild(comment)

    def generateModifyObject(self, dn, changes, modify_value = False):
        # only REPLACE operation is supported
        self.beginElement("modify")
        self.getCurrentElement().setAttribute("objectDN", dn)
        self.getCurrentElement().setAttribute("operation", "SA_IMM_ATTR_VALUES_REPLACE")
        for (name, t, value) in changes:
            self.beginElement("attribute")
            self.getCurrentElement().setAttribute("name", name)
            self.getCurrentElement().setAttribute("type", t)
            if modify_value:
                self.beginElement("value")
                self.getCurrentElement().appendChild(self._doc.createTextNode(value))
                self.popElement()
            else:
                self.getCurrentElement().setAttribute("value", value)
            self.popElement()
        self.popElement()

    def generateDeleteObject(self, dn):
        self.beginElement("delete")
        self.getCurrentElement().setAttribute("objectDN", dn)
        self.popElement()

    def beginRemoveFromImm(self):
        self.beginElement("removeFromImm")

    def endRemoveFromImm(self):
        self.popElement()

    def generateAmfEntityTypeDN(self, object):
        self.beginElement("amfEntityTypeDN")
        self.getCurrentElement().setAttribute("objectDN", object)
        self.popElement()

    def beginTargetEntityTemplate(self, objDn):
        self.beginElement("targetEntityTemplate")
        self.beginElement("parent")
        self.getCurrentElement().setAttribute("objectDN", objDn)
        self.popElement()

    def generateCompTypeUpgrade(self, compRdn, compTypeDn):
        self.beginElement("modifyOperation")
        self.getCurrentElement().setAttribute("objectRDN", compRdn)
        self.getCurrentElement().setAttribute("operation", "SA_IMM_ATTR_VALUES_REPLACE")
        self.beginElement("attribute")
        self.getCurrentElement().setAttribute("name", "saAmfCompType")
        self.getCurrentElement().setAttribute("type", "SA_IMM_ATTR_SANAMET")
        self.beginElement("value")
        self.getCurrentElement().appendChild(self._doc.createTextNode(compTypeDn))
        self.popElement()
        self.popElement()
        self.popElement()

    def endTargetEntityTemplate(self):
        self.popElement()

    def __call_plugin_cli_action(self, func, begin, end, plugins, valid_uid = None):
        """
        Plugin will be execute on all component if valid_uid is None
        Otherwise valid_uid should be a list of valid UID to exec plugin
        """
        for (uid, plugin) in plugins.iteritems():
            if (valid_uid is not None) and (uid not in valid_uid):
                continue
            logging.debug("Invoke plugin function %s" % func)
            self.__generate_plugin_cli_commands(
                plugin, uid, func,
                begin, end
                )

    def __generate_plugin_cli_commands(self, plugin, unit, getterFunc, begin, end):
        logging.debug("Exec plugin function %s for unit %s" % (getterFunc, unit))
        cliactions = getattr(plugin, getterFunc)()
        if cliactions:
            self.__generate_cli_commands(unit, cliactions, begin, end)

    def __generate_cli_commands(self, unit, cliactions, begin, end):
        logging.debug("Get cli actions from plugin.")
        for (do, undo, node) in cliactions:
            if do is None:
                tcg_error("unit %s has SMFCampaignPlugin and returned None as a doCliCommand" % unit)
            begin()
            self.generateDoCliCommand(do[0], do[1])
            if undo is not None:
                self.generateUndoCliCommand(undo[0], undo[1])
            if node is None:
                node = CampaignGenerator.find_exec_node(unit)
            elif isinstance(node, CsmApiComputeResource):
                node = node.dn
            self.generatePlmExecEnv(node)
            end()

    def call_plugin_cli_action_at_camp_init(self, plugins):
        self.__call_plugin_cli_action(
            "cliAtCampInit",
            self.beginCampInitAction,
            self.endCampInitAction,
            plugins
            )

    def call_plugin_cli_action_at_camp_complete(self, plugins):
        self.__call_plugin_cli_action(
            "cliAtCampComplete",
            self.beginCampCompleteAction,
            self.endCampCompleteAction,
            plugins
            )

    def call_plugin_cli_action_at_camp_wrapup(self, plugins):
        self.__call_plugin_cli_action(
            "cliAtCampWrapup",
            self.beginCampWrapupAction,
            self.endCampWrapupAction,
            plugins
            )

    def create_cli_actions_at_proc_init(self, unit, clis):
        if clis is not None:
            self.__generate_cli_commands(unit,
                                         clis,
                                         self.beginProcInitAction,
                                         self.endProcInitAction)

    def create_cli_actions_at_proc_wrapup(self, unit, clis):
        if clis is not None:
            self.__generate_cli_commands(unit,
                                         clis,
                                         self.beginProcWrapupAction,
                                         self.endProcWrapupAction)

    def setOneStepUpgrade(self, flag):
        self._needOneStepUpgrade = flag

    def needOneStepUpgrade(self):
        return self._needOneStepUpgrade
