from plugin_handler import loadPlugins, loadPluginsUsingVDicosHardcodedDependency
import CgtConstants
import CSMConstants
import tcg.plugin_api.SMFConstants as SMFConstants
import Utils
import SMFCampaign
import os
import sys
import imp
import re
import shutil
import distutils.dir_util
import time
import logging
import AMFModel
import AMFTools
import SDPTools
import AMFConstants
import ImmHelper
import AMFModelInstanceGenerator
import DependencyCalculator
import CoreMWCampaignGeneratorPlugin
from AMFModelPostScaleTransformation import AMFModelPostScaleTransformation
from sdk.plugin_contexts import CSMModelExpansionPluginContext
from SystemModels import SystemModels
from utils.logger_tcg import tcg_error
from amf_diff_and_model_change_detector import AMFModelDiffCalcResult
import copy
import inspect
from tcg.camp_gen_info_provider_impl import CampGenInfoProviderImpl
from tcg.plugin_utilities_provider_impl import PluginUtilitiesProviderImpl

from tcg.plugin_api.SMFCsmModelExpansionPlugin import CSMModelExpansionPlugin
from tcg.plugin_api.SMFCampaignPlugin import SMFCampaignPlugin as SMFCampaignPlugin

INTERNAL_CAMPAIGN_GENERATOR_PLUGIN_NAME = "INTERNAL_CAMPAIGN_GENERATOR_PLUGIN_NAME"
CDFCGT_CONFIG_BASE_AMF_PART = "AMF"
CDFCGT_CONFIG_BASE_AMF_MODEL_FILENAME = "model_objects.xml"
ONE_STEP_UPGRADE_MARKER = "ONE-STEP-UPGRADE_MARKER"


class Context(object):

    _instance = None

    @staticmethod
    def get():
        """Get the only instance of the context.

        If it does not exist yet, it will be created."""
        if Context._instance is None:
            Context._instance = Context()
        return Context._instance

    def __init__(self):
        self._contains = {}
        self._nodePoolAllocation = {}
        self._poolNodeAllocation = {}
        self._roleNodeAllocation = {}
        self._componentPoolAllocation = {}
        self._entityTypes = {}
        self._controllerNode = None

    def getControllerNode(self):
        if self._controllerNode is None:
            tcg_error("Controller node is not defined in the site configuration")
        return self._controllerNode

    def initNodePoolAllocation(self, siteConfig):
        nodeRoleAllocation = {}
        self._roleNodeAllocation = {}
        nodes = siteConfig[CgtConstants.SYSTEM_COMPUTE_RESOURCES_TAG]
        for node in nodes:
            nodeName = node.getName()
            nodeRole = node.getRole()

            if self._controllerNode is None:
                self._controllerNode = AMFTools.getNodeDnFromName(nodeName)
            nodeRoleAllocation[nodeName] = nodeRole
            if nodeRole not in self._roleNodeAllocation.keys():
                self._roleNodeAllocation[nodeRole] = set()
            self._roleNodeAllocation[nodeRole].add(nodeName)

        self._nodePoolAllocation = {}
        self._poolNodeAllocation = {}

        for (node, role) in nodeRoleAllocation.items():
            self._nodePoolAllocation[node] = []
            definedRole = None
            for t_role in siteConfig[CgtConstants.ROLES_TAG]:
                if t_role.getUid() == role:
                    definedRole = t_role
            if definedRole is None:
                tcg_error("ERROR: Siteconfig references role %s, but it is not defined under roles." % (role))

            for service in definedRole.getServices():
                self._nodePoolAllocation[node].append(service.getUid())
                if service.getUid() not in self._poolNodeAllocation.keys():
                    self._poolNodeAllocation[service.getUid()] = set()
                self._poolNodeAllocation[service.getUid()].add(node)

    def initComponentPoolAllocation(self, components, services):
        self._componentPoolAllocation = {}
        for component in components:
            ctId = component.getUid()
            if ctId not in self._componentPoolAllocation.keys():
                self._componentPoolAllocation[ctId] = set()
            for service in services:
                for containedComponent in service.getComponentTypes():
                    if ctId == containedComponent.getUid():
                        self._componentPoolAllocation[ctId].add(service.getUid())

    def getNodesForPool(self, pool):
        return self._poolNodeAllocation[pool]

    def getNodesForRole(self, role):
        return list(self._roleNodeAllocation[role])

    def getRoles(self):
        return self._roleNodeAllocation.keys()

    def getPoolsForComponent(self, ctId):
        if ctId in self._componentPoolAllocation:
            return self._componentPoolAllocation[ctId]
        return []

    def getNodesForComponent(self, ctId):
        nodes = set()
        for serviceId in self.getPoolsForComponent(ctId):
            if nodes is None:
                nodes = self.getNodesForPool(serviceId)
            else:
                nodes = nodes | self.getNodesForPool(serviceId)
        return nodes

    def hasCompOrService(self, role):
        for node in self._roleNodeAllocation[role]:
            for service in self._nodePoolAllocation[node]:
                return True
        return False

    def processEntityTypes(self, amfModel, appTypeDns):
        self._entityTypes = {}
        for appTypedn in appTypeDns:
            appType = amfModel.getObject(appTypedn)
            self._entityTypes[appTypedn] = {}
            for sgtdn in appType.getsaAmfApptSGTypes():
                sgt = amfModel.getObject(sgtdn)
                self._entityTypes[appTypedn][sgtdn] = {}
                # rule: validate that each SGT has supported redundancy model
                if sgt.getsaAmfSgtRedundancyModel().upper() != AMFConstants.SA_AMF_2N_REDUNDANCY_MODEL and \
                                sgt.getsaAmfSgtRedundancyModel().upper() != AMFConstants.SA_AMF_NWA_REDUNDANCY_MODEL and \
                                sgt.getsaAmfSgtRedundancyModel().upper() != AMFConstants.SA_AMF_NR_REDUNDANCY_MODEL:
                    tcg_error("ServiceGroupType: " + sgt.getDn() + " generated from unit " + AMFTools.getUnitIdFromDn(sgt.getDn()) + " has unsupported redundancy model: " + sgt.getsaAmfSgtRedundancyModel())
                    # rule: validate that each SUT is local scoped
                saAmfSgtValidSuTypedn = sgt.getsaAmfSgtValidSuTypes_single()
                self._entityTypes[appTypedn][sgtdn][saAmfSgtValidSuTypedn] = []
                sutype = amfModel.getObject(saAmfSgtValidSuTypedn)
                if sutype.getsaAmfSutIsExternal() != "0":
                    tcg_error("ServiceUnitTYpe: " + sutype.getDn() + " generated from unit " + AMFTools.getUnitIdFromDn(sutype.getDn()) + " is not local, only local scope is supported")
                    # rule: validate that category of CTs belonging to SUT matches the scope of the SUT (local only!) and category is SA-Aware
                for sutcomptypedn, sutcomptype in amfModel.getObjects(AMFModel.SaAmfSutCompType, saAmfSgtValidSuTypedn).items():
                    comptypedn = ImmHelper.getName(sutcomptypedn)
                    self._entityTypes[appTypedn][sgtdn][saAmfSgtValidSuTypedn].append(comptypedn)

    def getEntityTypes(self):
        return self._entityTypes


def updateGeneratorPlugin(plugin, siteConfig, svIdentity, sgRedMode):
    context = Context.get()
    plugin._svIdentity = svIdentity
    plugin._nodeList = map(AMFTools.getNodeDnFromName, context.getNodesForPool(svIdentity))
    plugin._numberOfSUs = len(plugin._nodeList)
    plugin._redundancyModel = sgRedMode

def generateInstancesForAMFModel(amfModel, siteConfig, amfModelPluginModules,
                                 configBaseTargetDirectory, generateOnlyImm, online_adapter):

    context = Context.get()

    context.initNodePoolAllocation(siteConfig)
    components = SystemModels.targetCSMModel.system.getComponents()
    services = SystemModels.targetCSMModel.system.getServices()

    context.initComponentPoolAllocation(components, services)

    # generate nodeSwBundle for non managed CTs
    for comp in SystemModels.targetCSMModel.system.getNonManagedComps():
        _addNodeSwBundle(comp, amfModel, context, online_adapter)

    # generate nodeSwBundle for CDS CTs
    """
    This is a special case where TCG takes care of CDS components. In the rest
    of the use cases, CDS component handling is delegated to plugins.
    This special case is required in OICVI flow to secure that the software for
    the CDS components appears as "Used" in the software repository after
    instantiation.
    An alternative solution could be to delegate this to the model expansion
    plugin, but since all the software from CDS objects present in the model
    is used, then, TCG does not really require any special logic to handle this.
    This is an exceptional use case but is simpler than handling it through
    plugins. This decision could be revisited in the future if needed.
    """
    for comp in SystemModels.targetCSMModel.system.getCDSComps():
        _addNodeSwBundle(comp, amfModel, context, online_adapter)

    # SaAmfNodeGroup
    for roleId in context.getRoles():
        role = SystemModels.targetCSMModel.getRole(roleId)
        if not role.isExternal():
            nodegroup = AMFModel.SaAmfNodeGroup()
            nodegroup._dn = AMFTools.getNodeGroupDnFromPGName(roleId)
            for node in context.getNodesForRole(roleId):
                nodegroup.addTosaAmfNGNodeList(AMFTools.getNodeDnFromName(node))
            amfModel.addObject(nodegroup)

    csmServiceToPluginSIMap = {}
    '''
    csmServiceToSIMap contains a map {csmService : (csmServicePlugin, {SI:Node})}

    csmService is the service Id

    csmServicePlugin is the AMFModelInstanceGenerator.AMFModelInstanceGenerator() plugin
    by default or the specific service plugin if provided in the model

    {SI:Node} is a map between each SI created and the node_info(applicable for NR, None for 2N and NWA)
                                                         for the service(generated below)
    csmServicePluginToSIMap is used to create SI dependencies between SIs generated
    '''
    # SaAmfSG
    for (sgDn, sg) in amfModel.getObjects(AMFModel.SaAmfSG).items():
        svIdentity = AMFTools.getUnitIdFromModelName(ImmHelper.getName(sg.getParentDn()))
        plugin = AMFModelInstanceGenerator.AMFModelInstanceGenerator()
        sgRedMode = AMFConstants.getRedundancyModelShortName(amfModel.getObject(sg.getsaAmfSGType()).getsaAmfSgtRedundancyModel())
        if svIdentity in amfModelPluginModules.keys():
            plugin = amfModelPluginModules[svIdentity].createModelGenerator()

        # update the plugin with information such as service name, redundancy model, nodes mapped to this service
        updateGeneratorPlugin(plugin, siteConfig, svIdentity, sgRedMode)

        sg.updateParams(plugin.processSaAmfSG(sgDn), ["saAmfSGType", "saAmfSGNumPrefInserviceSUs"])

        if sg.getsaAmfSGAutoAdjust_unsafe() and \
                not sg.getsaAmfSGAutoAdjustProb_unsafe():
            tcg_error("In SG %s saAmfSgtDefAutoAdjust is specified from plugin but saAmfSgtDefAutoAdjustProb is missing" % sgDn)

        if sgRedMode != AMFConstants.REDUNDANCY_MODEL_NAME_NM and \
                (sg.getsaAmfSGNumPrefActiveSUs_unsafe() or \
                         sg.getsaAmfSGNumPrefStandbySUs_unsafe()):
            tcg_error("In SG %s invalid attributes are specified fron plugin: saAmfSGNumPrefActiveSUs and saAmfSGNumPrefStandbySUs can only be used with N+M redundancy model" % sgDn)

        if (sgRedMode != AMFConstants.REDUNDANCY_MODEL_NAME_NW or \
                        sgRedMode != AMFConstants.REDUNDANCY_MODEL_NAME_NWA) and \
                sg.getsaAmfSGNumPrefAssignedSUs_unsafe():
            tcg_error("In SG %s saAmfSGNumPrefAssignedSUs is specified from plugin but it can only be used with NW or NWA redundancy model" % sgDn)

        if (sgRedMode != AMFConstants.REDUNDANCY_MODEL_NAME_NM or \
                        sgRedMode != AMFConstants.REDUNDANCY_MODEL_NAME_NW or \
                        sgRedMode != AMFConstants.REDUNDANCY_MODEL_NAME_NWA) and \
                sg.getsaAmfSGMaxActiveSIsperSU_unsafe():
            tcg_error("In SG %s saAmfSGMaxActiveSIsperSU is specified from plugin but it can only be used with N+M, NW or NWA redundancy model" % sgDn)

        if (sgRedMode != AMFConstants.REDUNDANCY_MODEL_NAME_NM or \
                        sgRedMode != AMFConstants.REDUNDANCY_MODEL_NAME_NW) and \
                sg.getsaAmfSGMaxStandbySIsperSU_unsafe():
            tcg_error("In SG %s saAmfSGMaxStandbySIsperSU is specified from plugin but it can only be used with N+M or NW redundancy model" % sgDn)

        if sgRedMode != AMFConstants.REDUNDANCY_MODEL_NAME_NR:
            nodeCount = len(plugin._nodeList)
            sg.setsaAmfSGNumPrefInserviceSUs(nodeCount)
        sgtdn = sg.getsaAmfSGType()
        svcTypeDn = None
        sut = None
        compTypes = None
        entities = context.getEntityTypes()
        for (app, sgts) in entities.items():
            for (sgt, suts) in sgts.items():
                if sgt == sgtdn:
                    sut = suts.keys()[0]
                    compTypes = suts.values()[0]
        svcTypeDn = amfModel.getObject(sut).getsaAmfSutProvidesSvcTypes()[0]

        # generate nodeSwBundle for AMF CTs
        for ctDn in compTypes:
            ctId = AMFTools.getUnitIdFromModelName(ImmHelper.getParentDn(ctDn))
            nodes = context.getNodesForPool(svIdentity)
            # logging.debug("CT %s of SV %s is allocated to pool %s, nodes [%s]" % (ctId, svIdentity, pool, nodes))
            component = SystemModels.targetCSMModel.getComponent(ctId)

            for node in nodes:
                sw = component.get_single_sdp_name(online_adapter)
                if sw:
                    nodeSwBundle = AMFModel.SaAmfNodeSwBundle()
                    nodeSwBundle._dn = AMFTools.getNodeSwBundleDnFromUnit(
                        sw,
                        AMFTools.getNodeDnFromName(node)
                    )
                    nodeSwBundle.setsaAmfNodeSwBundlePathPrefix(AMFConstants.AMFCOMPONENTTYPE_DEFAULT_PREFIX)
                    amfModel.addObject(nodeSwBundle)
        # SaAmfSU
        for node in plugin._nodeList:
            su = AMFModel.SaAmfSU()
            su._dn = AMFTools.generateSUDn(ImmHelper.getName(node), sgDn)
            amfModel.addObject(su)
            su.updateParams(plugin.processSaAmfSU(su.getDn(), node), ["saAmfSUType", "saAmfSUHostNodeOrNodeGroup"])

            su.setsaAmfSUAdminState(AMFConstants.SA_AMF_ADMIN_LOCKED_INSTANTIATION)

            su.setsaAmfSUType(sut)
            su.setsaAmfSUHostNodeOrNodeGroup(node)
            # SaAmfComp
            service = SystemModels.targetCSMModel.getService(svIdentity)
            for comp_ins in service.getAmfComponentInstances():
                ct = service.getComponentType(comp_ins)
                compType = AMFTools.getCompTypeDnFromUnit(ct.getUid(), ct.getVersion())
                compTypeObject = amfModel.getObject(compType)
                priorityLevel = service.getCompInstantiationLevel(comp_ins)
                comp = AMFModel.SaAmfComp()
                comp._dn = AMFTools.generateCompDn(comp_ins, su._dn)
                comp.setsaAmfCompType(compType)
                _fill_env_attrs_in_comp(comp, service.get_component_instance_env_attrs(comp_ins))

                amfModel.addObject(comp)
                comp.updateParams(plugin.processSaAmfComp(comp._dn, node, AMFTools.getUnitIdFromModelName(compType)), ["saAmfCompType", "saAmfCompInstantiationLevel", "osafAmfCompHcCmdArgv"])

                comp_category = compTypeObject.getsaAmfCtCompCategory()
                match_range = [
                    AMFConstants.SA_AMF_COMP_SA_AWARE,
                    AMFConstants.SA_AMF_COMP_PROXY,
                    AMFConstants.SA_AMF_COMP_PROXIED]

                if (AMFTools.compCategoryInRange(comp_category, match_range) and priorityLevel >= 0):
                    comp.setsaAmfCompInstantiationLevel(priorityLevel)

                match_range = [AMFConstants.SA_AMF_COMP_PROXIED, AMFConstants.SA_AMF_COMP_PROXIED_NPI]
                if (AMFTools.compCategoryOnlyInRange(comp_category, match_range) and
                        comp.getsaAmfCompInstantiateCmdArgv()):
                    tcg_error("In component %s saAmfCompInstantiateCmdArgv is specified from plugin but it can only be used with SA-AWARE, PROXY or LOCAL categories" % comp._dn)

                if (not AMFTools.isLocalComponent(comp_category)) and comp.getsaAmfCompTerminateCmdArgv():
                    tcg_error("In component %s saAmfCompTerminateCmdArgv can only be used with LOCAL category" % comp._dn)

                match_range = [AMFConstants.SA_AMF_COMP_LOCAL, AMFConstants.SA_AMF_COMP_PROXIED_NPI]
                if (AMFTools.compCategoryOnlyInRange(comp_category, match_range) and
                        comp.getsaAmfCompQuiescingCompleteTimeout_unsafe()):
                    tcg_error("In component %s saAmfCompQuiescingCompleteTimeout is specified from plugin but it can only be used with SA-AWARE, PROXY or PROXIED categories" % comp._dn)

                if AMFTools.isProxiedNpiComponent(comp_category) and comp.getsaAmfCompInstantiateTimeout_unsafe():
                    tcg_error("In component %s saAmfCompInstantiateTimeout  is specified from plugin but it can only be used with SA-AWARE, PROXY, PROXIED or LOCAL category" % comp._dn)

                match_range = [AMFConstants.SA_AMF_COMP_SA_AWARE, AMFConstants.SA_AMF_COMP_LOCAL]
                if (AMFTools.compCategoryNotInRange(comp_category, match_range) and
                        comp.getsaAmfCompNumMaxInstantiateWithoutDelay_unsafe()):
                    tcg_error("In component %s saAmfCompNumMaxInstantiateWithoutDelay is specified from plugin but it can only be used with SA-AWARE or LOCAL categories" % comp._dn)

                if (not AMFTools.isLocalComponent(comp_category)) and comp.getsaAmfCompTerminateTimeout_unsafe():
                    tcg_error("In component %s saAmfCompTerminateTimeout is specified from plugin but it can only be used with LOCAL category" % comp._dn)

                match_range = [AMFConstants.SA_AMF_COMP_SA_AWARE, AMFConstants.SA_AMF_COMP_PROXY]
                if (AMFTools.compCategoryNotInRange(comp_category, match_range) and
                        comp.getsaAmfCompCSISetCallbackTimeout_unsafe()):
                    tcg_error("In component %s saAmfCompCSISetCallbackTimeout is specified from plugin but it can only be used with SA-AWARE or PROXY categories" % comp._dn)

                match_range = [AMFConstants.SA_AMF_COMP_SA_AWARE, AMFConstants.SA_AMF_COMP_PROXY]
                if (AMFTools.compCategoryNotInRange(comp_category, match_range) and
                        comp.getsaAmfCompCSIRmvCallbackTimeout_unsafe()):
                    tcg_error("In component %s saAmfCompCSIRmvCallbackTimeout is specified from plugin but it can only be used with SA-AWARE or PROXY categories" % comp._dn)

                if comp.getsaAmfCompContainerCsi_unsafe():
                    tcg_error("In component %s saAmfCompContainerCsi is specified from plugin but it cannot be used with any supported categories" % comp._dn)

                if comp.getsaAmfCompProxyCsi_unsafe():
                    tcg_error("In component %s saAmfCompProxyCsi should not be set from plugin" % comp._dn)

                match_range = [AMFConstants.SA_AMF_COMP_PROXIED, AMFConstants.SA_AMF_COMP_PROXIED_NPI]
                if AMFTools.compCategoryInRange(comp_category, match_range):
                    represent_proxy_proxied_comp_relation(
                        ct, comp._dn, amfModel
                    )

                # saAmfCompInstantiationLevel still missing
                saAmfCtCsTypeDns = amfModel.getObjects(AMFModel.SaAmfCtCsType, compType).keys()
                saAmfCSTypeDns = map(ImmHelper.getName, saAmfCtCsTypeDns)
                for csType in saAmfCSTypeDns:
                    # SaAmfCompCsType
                    compCsType = AMFModel.SaAmfCompCsType()
                    compCsType._dn = AMFTools.generateCompCsTypeDn(csType, comp.getDn())
                    amfModel.addObject(compCsType)
                    compCsType.updateParams(plugin.processSaAmfCompCsType(compCsType._dn,
                                                                          AMFTools.getUnitIdFromModelName(compType),
                                                                          AMFTools.getUnitIdFromModelName(csType)), [])

        nodeList = [None]
        if sgRedMode == AMFConstants.REDUNDANCY_MODEL_NAME_NR:
            '''
            For NR Redundancy Model, as many SIs as the number of nodes should be created
            '''
            nodeList = []
            for nodeDn in plugin._nodeList:
                nodeList.append(AMFTools.getNodeNameFromNodeDn(nodeDn))
            if not nodeList:
                tcg_error("model generator plugin for SV %s generated empty node list" % (svIdentity))

        # SaAmfSI
        siToNodeMap = {}

        for node in nodeList:
            siList = plugin.generateSINameList()
            if len(siList) == 0:
                tcg_error("model generator plugin for SV %s generated empty si list" % (svIdentity))

            appDn = ImmHelper.getParentDn(sgDn)
            for siId in siList:
                si = AMFModel.SaAmfSI()
                si._dn = AMFTools.generateSIDn(svIdentity, sgRedMode, siId, appDn, node)
                amfModel.addObject(si)
                siToNodeMap[si] = node
                si.updateParams(plugin.processSaAmfSI(si._dn, siId), ["saAmfSvcType", "saAmfSIProtectedbySG"])
                si.setsaAmfSvcType(svcTypeDn)
                si.setsaAmfSIProtectedbySG(sgDn)
                if sgRedMode == AMFConstants.REDUNDANCY_MODEL_NAME_NWA:
                    service = SystemModels.targetCSMModel.getService(svIdentity)

                    # If the saAmfSgtRedundancyModel is NWA, and the associated
                    # service entity has defined a maxPromotions limit, tcg
                    # should update the saAmfSIPrefStandbyAssignments with the
                    # maxPromotions value.
                    max_promotions_limit = service.getMaxPromotions()
                    if max_promotions_limit is not None:
                        si.setsaAmfSIPrefActiveAssignments(max_promotions_limit)
                    else:
                        # Else, if the value for the saAmfSIPrefStandbyAssignments
                        # was not specified in the plugin for this service, tcg
                        # will fill out the saAmfSIPrefStandbyAssignments with
                        # a default value based on the number of payloads in
                        # the configuration.
                        if not si.getsaAmfSIPrefActiveAssignments_unsafe():
                            si.setsaAmfSIPrefActiveAssignments(str(len(plugin._nodeList)))

                if sgRedMode != AMFConstants.REDUNDANCY_MODEL_NAME_NW and \
                        si.getsaAmfSIPrefStandbyAssignments_unsafe():
                    tcg_error("In SI %s saAmfSIPrefStandbyAssignments is specified from plugin but it can only be used with NW redundancy model" % comp._dn)

                # SaAmfCSI
                service = SystemModels.targetCSMModel.getService(svIdentity)
                for comp_ins in service.getAmfComponentInstances():
                    ct = service.getComponentType(comp_ins)
                    compType = AMFTools.getCompTypeDnFromUnit(ct.getUid(), ct.getVersion())
                    saAmfCtCsTypeDns = amfModel.getObjects(AMFModel.SaAmfCtCsType, compType).keys()
                    saAmfCSTypeDns = map(ImmHelper.getName, saAmfCtCsTypeDns)
                    # Limitation: CSI <-> CSType should be 1:1
                    for csType in saAmfCSTypeDns:
                        csi = AMFModel.SaAmfCSI()
                        csi._dn = AMFTools.generateCSIDn(comp_ins, si._dn, node)
                        amfModel.addObject(csi)
                        csi.setsaAmfCSType(csType)

                        ctId = AMFTools.getUnitIdFromModelName(ImmHelper.getParentDn(compType))
                        component = SystemModels.targetCSMModel.getComponent(ctId)

                        # SaAmfCSIAttribute
                        comp_inst_prom_attr_dict = service.get_component_instance_prom_attrs(comp_ins)
                        comp_type_prom_attr_dict = dict(
                            (attr.get_name(), attr.get_default_value()) for attr in service.getComponentType(comp_ins).get_promotion_attributes()
                        )
                        _create_prom_attrs_for_csi(
                            amfModel,
                            csi._dn,
                            comp_type_prom_attr_dict,
                            comp_inst_prom_attr_dict
                        )

                for comp_ins in service.getAmfComponentInstances():
                    csi_dn = AMFTools.generateCSIDn(comp_ins, si._dn, node)
                    csi = amfModel.getObject(csi_dn)
                    if not csi:
                        tcg_error("AMF model contains no CSI entity named %s" % csi_dn)
                    for (depFrom, depTo) in service.getComponentInstPromDeps():
                        if comp_ins == depFrom:
                            to_csi_dn = AMFTools.generateCSIDn(depTo, si._dn, node)
                            to_csi = amfModel.getObject(csi_dn)
                            if not to_csi:
                                tcg_error("AMF model contains no CSI entity named %s" % to_csi_dn)
                            csi.addTosaAmfCSIDependencies(to_csi_dn)

            csmServiceToPluginSIMap[svIdentity] = (plugin, siToNodeMap)


    # SaAmfSIDependency
    for svIdentity, (plugin, siToNodeMap) in csmServiceToPluginSIMap.iteritems():
        # if svIdentity in amfModelPluginModules.keys():
        #    # This part has to be supported, need to check how this handling is to be done for plugins
        #    tcg_critical("Handling the SI dependencies through plugin is not implemented yet")
        # else :
        svRedModel = plugin.getRedundancyModel()
        csmServiceInstance = SystemModels.targetCSMModel.getService(svIdentity)

        for promDepInstance in csmServiceInstance.getDependsOnServices():
            depSvPlugin, depSvSINodeMap = csmServiceToPluginSIMap[promDepInstance.getDependsOnService()]
            for si, node in siToNodeMap.iteritems():
                for depSvSI, depSINode in depSvSINodeMap.iteritems():
                    if (node == depSINode) or (node is not None and depSINode is None):
                        '''
                        In the above if statement,
                        (node == depSINode)                        resembles NR to NR
                        (node is not None and depSINode is None)   resembles Nt to 2N/NWA
                        '''
                        depSIDn = depSvSI.getDn()
                        break

                siDep = AMFModel.SaAmfSIDependency()
                siDep._dn = AMFModel.SaAmfSIDependency.createDn(depSIDn, parentDn=si.getDn())
                siDep.setsaAmfToleranceTime(promDepInstance.getToleranceTimeout())
                amfModel.addObject(siDep)
    if generateOnlyImm:
        amfModelDir = os.path.join(configBaseTargetDirectory, CDFCGT_CONFIG_BASE_AMF_PART)
        Utils.mkdir_safe(amfModelDir)
        amfModel.writeXML(os.path.join(amfModelDir, CDFCGT_CONFIG_BASE_AMF_MODEL_FILENAME))


def _addNodeSwBundle(comp, amfModel, context, online_adapter):
    for node in context.getNodesForComponent(comp.getUid()):
        for _, sw in comp.software_bundle_names(online_adapter):
            nodeSwBundle = AMFModel.SaAmfNodeSwBundle()
            nodeSwBundle._dn = AMFTools.getNodeSwBundleDnFromUnit(
                sw,
                AMFTools.getNodeDnFromName(node)
            )
            nodeSwBundle.setsaAmfNodeSwBundlePathPrefix(AMFConstants.AMFCOMPONENTTYPE_DEFAULT_PREFIX)
            amfModel.addObject(nodeSwBundle)


def represent_proxy_proxied_comp_relation(proxied_comp, proxied_comp_dn, amfModel):
    proxy_csm_ct = SystemModels.targetCSMModel.get_component_in_system(
        proxied_comp.getControlPolicyParent()
    )
    proxy_ct_dn = AMFTools.getCompTypeDnFromUnit(
        proxy_csm_ct.getUid(), proxy_csm_ct.getVersion()
    )
    proxy_amf_ct_obj = amfModel.getObject(proxy_ct_dn)
    AMFTools.validateAndSetOptionalArg(
        proxy_amf_ct_obj.addTosaAmfCtDefCmdEnv,
        'PROXIED_COMP_DN_{0}={1}'.format(
            proxy_csm_ct.proxied_comp_counter(), proxied_comp_dn
        )
    )


def _fill_env_attrs_in_comp(comp, env_attrs_dict):
    for attr_name in env_attrs_dict:
        env_attr = attr_name + "=" + env_attrs_dict[attr_name]
        comp.addTosaAmfCompCmdEnv(env_attr)


def _create_prom_attrs_for_csi(amf_model, csi_dn, prom_attrs_in_comp_type, prom_sttrs_in_comp_inst):
    overwrited = set()
    for attr in prom_sttrs_in_comp_inst:
        csiattr = AMFModel.SaAmfCSIAttribute()
        csiattr._dn = AMFTools.generateCSIAttributeDn(attr, csi_dn)
        AMFTools.validateAndSetOptionalArg(
            csiattr.addTosaAmfCSIAttriValue,
            prom_sttrs_in_comp_inst[attr]
        )
        amf_model.addObject(csiattr)
        overwrited.add(attr)
    for attr in [k for k in prom_attrs_in_comp_type if k not in overwrited]:
        csiattr = AMFModel.SaAmfCSIAttribute()
        csiattr._dn = AMFTools.generateCSIAttributeDn(attr, csi_dn)
        AMFTools.validateAndSetOptionalArg(
            csiattr.addTosaAmfCSIAttriValue,
            prom_attrs_in_comp_type[attr]
        )
        amf_model.addObject(csiattr)


def extendAmfModelWithNonManagedComponents(system_model, amf_model):
    """
    This function creates dummy component types for non amf components in
    the amf model so they can be handled in the same way as amf managed
    components.
    Should only be called after target amf model is exported into file
    which is done in generateInstancesForAMFModel().
    """
    for comp in system_model.getNonManagedComps():
        ct_id = comp.getUid()
        ct_version = comp.getVersion()
        comp_base_type = AMFModel.SaAmfCompBaseType()
        comp_base_type._dn = AMFTools.getCompBaseTypeDnFromUnit(ct_id)
        amf_model.addObject(comp_base_type)
        comp_type = AMFModel.SaAmfCompType()
        comp_type._dn = AMFTools.getCompTypeDnFromUnit(ct_id, ct_version)
        amf_model.addObject(comp_type)
        comp_type.setsaAmfCtCompCategory(AMFConstants.SA_AMF_COMP_LOCAL | AMFConstants.SA_AMF_COMP_PROXIED_NPI)
        comp_type.setsaAmfCtDefRecoveryOnError(AMFConstants.SA_AMF_COMPONENT_FAILOVER)
        comp_type.addTosaAmfCtDefCmdEnv(Utils.NON_MANAGED_CT_IDENTIFIER)

def amfModelPluginFilter(module):
    """Filter for SV AMF Model generator plugin modules.

    An AMF Model generator plugin module should provide the following function:

    - createModelGenerator(): returns an instance of the model generator plugin."""

    return "createModelGenerator" in module.__dict__

def smfCampaignPluginFilter(module):
    """Filter for SV SMF Campaign plugin modules.

    An SMF Campaign plugin module should provide the following function:

    - createSMFCampaignPlugin(): returns an instance of the SMF campaign plugin."""

    return "createSMFCampaignPlugin" in module.__dict__

def campaignGeneratorPluginFilter(module):
    """Filter for SV Campaign generator plugin modules.

    A Campaign generator plugin module should provide the following function:

    - createCampaignGeneratorPlugin(): returns an instance of the campaign generator plugin."""

    return "createCampaignGeneratorPlugin" in module.__dict__


def csmModelExpansionPluginFilter(module):
    """
    Filter for CSM model expansion plugins.
    A CSM model expansion plugin module must provide the function
    'createCsmModelExpansionPlugin()' used to return an instance of the csm
    model expansion plugin which must be a subclass of CSMModelExpansionPlugin
    """

    return "createCsmModelExpansionPlugin" in module.__dict__


def collectNonManagedCTs(model):
    libsModel = AMFModel.AMFModel()
    for ct in model.getObjects(AMFModel.SaAmfCompType).values():
        # ctId = AMFTools.getUnitIdFromModelName(ct.getParentDn())
        # version = ImmHelper.getName(ct.getDn())
        if Utils.isNonManagedCT(ct):
            libsModel.addObject(ct)
    return libsModel


def fillPrelimNodeAlloc(config):
    # Fill preliminary node allocation info
    for pool in config.getPools():
        for sv in pool.getSVs().values():
            sv.setNodes(pool.getNodes())
            for ct in sv.getCTs():
                ct.setNodes(pool.getNodes())
        for ct in pool.getCTs():
            ct.setNodes(pool.getNodes())


def updateDependencies(config, forBase=False):
    svs = {}
    cts = {}

    for pool in config.getPools():
        for (svid, sv) in pool.getSVs().items():
            if pool.getName() not in svs:
                svs[pool.getName()] = {}
            svs[pool.getName()][svid] = sv
            for ct in sv.getCTs():
                if pool.getName() not in cts:
                    cts[pool.getName()] = {}
                if svid not in cts[pool.getName()]:
                    cts[pool.getName()][svid] = {}
                cts[pool.getName()][svid][ct.getName()] = ct

    # This is fetching the non AMF CTs information who does not have any services
    for pool in config.getPools():
        for ct in pool.getCTs():
            if pool.getName() not in cts:
                cts[pool.getName()] = {}
            if None not in cts[pool.getName()]:
                cts[pool.getName()][None] = {}
            cts[pool.getName()][None][ct.getName()] = ct

    for (pool, svInfo) in svs.items():
        for (svid, sv) in svInfo.items():
            """
            TODO: the expansion plugin does not have the getSVDependencies() method.
            we need to query the plugin type until we remove the old campaign
            generator plugin interface. At that time the SV / CT can have a member
            variable called expansionPlugin that will contain a reference to
            the expansion plugin that injected the entity or None if the entity
            was created by regular TCG flow. If the expansion plugin is None
            we now that is a regular entity. If the expansion plugin is
            different from None we know that the entity was injected by an
            extension plugin.
            """
            if isinstance(sv.getPlugin(), CSMModelExpansionPlugin):
                deps = sv.getPlugin().injectServiceDependencies(svid)
            elif isinstance(sv.getPlugin(), CoreMWCampaignGeneratorPlugin.CoreMWCampaignGeneratorPlugin):
                deps = sv.getPlugin().getSVDependencies(pool, svid, sv.isToBeRemoved())
            else:
                deps = sv.getPlugin().getSVDependencies(pool, svid)
            for (depSV, constraint) in deps:
                foundDependencySV = False
                for (depPool, depSVInfo) in svs.items():
                    if depSV in depSVInfo:
                        sv.usesSV(depSVInfo[depSV], constraint)
                        foundDependencySV = True
                        break
                assert (foundDependencySV)


    for (pool, svInfo) in cts.items():
        for (svid, ctInfo) in svInfo.items():
            for (ctId, ct) in ctInfo.items():
                # This is to deal with the backward compatibility issue.
                # Only add the additional argument for CoreMWCampaignGenerator plugin
                if isinstance(ct.getPlugin(), CSMModelExpansionPlugin):
                    deps = []  # there are no CT dependencies in new plugin interface
                elif isinstance(ct.getPlugin(), CoreMWCampaignGeneratorPlugin.CoreMWCampaignGeneratorPlugin):
                    deps = ct.getPlugin().getCTDependencies(pool, ctId, ct.isToBeMigrated(), ct.isToBeRemoved())
                else:
                    deps = ct.getPlugin().getCTDependencies(pool, ctId)
                for (depCT, constraint) in deps:
                    foundDepCT = False
                    if constraint == DependencyCalculator.CT.CONSTRAINT_TYPE_NONE:
                        for (depSV, depCTInfo) in svInfo.items():
                            if depCT not in depCTInfo:
                                continue
                            else:
                                ct.usesCT(depCTInfo[depCT], constraint)
                                foundDepCT = True
                                break
                    else:
                        for (depPool, depSVInfo) in cts.items():
                            for (depSV, depCTInfo) in depSVInfo.items():
                                if depCT not in depCTInfo:
                                    continue
                                else:
                                    ct.usesCT(depCTInfo[depCT], constraint)
                                    foundDepCT = True
                                    break
                    if not foundDepCT:
                        tcg_error("Missing dependency, component %s uses %s in role %s" % (ctId, depCT, pool))
    updateProxyCompDependencies(config)


def updateProxyCompDependencies(config):
    for csm_comp in (comp for
                     comp in SystemModels.targetCSMModel.components
                     if comp.getControlPolicyParent() is not None):
        proxy_comp = []
        proxied_comp = []
        proxied_comp_uid = csm_comp.getUid()
        proxy_comp_uid = csm_comp.getControlPolicyParent()
        for pool in config.getPools():
            for (svid, sv) in pool.getSVs().items():
                for ct in sv.getCTs():
                    if ct.getName() == proxied_comp_uid:
                        proxied_comp.append(ct)
                    elif ct.getName() == proxy_comp_uid:
                        proxy_comp.append(ct)
        for proxy, proxied in ((proxy, proxied) for proxy in proxy_comp for proxied in proxied_comp):
            proxy.usesCT(proxied, DependencyCalculator.CT.CONSTRAINT_TYPE_NONE)
            proxied.usesCT(proxy, DependencyCalculator.CT.CONSTRAINT_TYPE_NONE)



def getMergeableCampaignName():
    # TODO: this can be removed when the support for old campaign generation
    # plugin is removed

    # the campaign name is obtained using `basename $OSAFCAMPAIGNROOT` to ensure
    # that the commands in the generated campaign does not contain its own name (otherwise the campaign cannot be merged)
    return "`basename $OSAFCAMPAIGNROOT`"


def generatePluginCallbacks(plugins, genFunc, getterFunc):
    for (svid, svPlugin) in plugins.items():
        callbacks = getattr(svPlugin, getterFunc)()
        for (label, timeout, stringToPass) in callbacks:
            genFunc(label, timeout, stringToPass)

def find_exec_node(unit):
    """
    Find out a node with the following priority:
      1. Tread unit as a component UID and return any node that component located
      2. Tread unit as a service UID and return any node that service located
      3. Return a controller node by using Context.getControllerNode()
      4. Return None if all fail.
    """
    context = Context.get()
    exec_node = None
    try:
        exec_node = context.getNodesForComponent(unit).pop()
        logging.debug("Select node {0} with component UID {1}".format(exec_node, unit))
        exec_node = AMFTools.getNodeDnFromName(exec_node)
    except KeyError:
        logging.debug("Do not find any node with component UID {0}.".format(unit))
    except Exception as e:
        logging.error("Unexpected error when get node with component UID %s, exception info: %s." % (unit, str(e)))
        return None
    if exec_node is None:
        try:
            exec_node = context.getNodesForPool(unit).pop()
            logging.debug("Select node {0} with service UID {1}".format(exec_node, unit))
            exec_node = AMFTools.getNodeDnFromName(exec_node)
        except KeyError:
            logging.debug("Do not find any node with service UID {0}.".format(unit))
            exec_node = context.getControllerNode()
            logging.debug("Use controller node {0}".format(exec_node))
        except Exception as e:
            logging.error("Unexpected error when get node with service UID %s, exception info: %s." % (unit, str(e)))
            return None
    return exec_node

def checkTargetOldestVersionsAgainstBase():
    required_system_version = SystemModels.targetCSMModel.original_system.getSystemConstraints().getUpgradeOldestVersion()
    if SystemModels.targetCSMModel.original_system.getUid() in SystemModels.baseCSMModel.system_map:
        old_system_version = SystemModels.baseCSMModel.system_map[SystemModels.targetCSMModel.original_system.getUid()].getVersionObject()
        if required_system_version.isValid() and required_system_version.compare(old_system_version) > 0:
            tcg_error("Invalid system upgrade.    Old system version: %s     Minimum required system version: %s" % (old_system_version.getVersionString(), required_system_version.getVersionString()))
    for new_comp in SystemModels.targetCSMModel.system.getComponents():
        for old_comp in SystemModels.baseCSMModel.system.getComponents():
            if new_comp.getUid() == old_comp.getUid():
                required_component_version = new_comp.getUpgradeConstraints().getOldestVersionObject()
                old_component_version = old_comp.getVersionObject()
                if required_component_version.isValid() and required_component_version.compare(old_component_version) > 0:
                    tcg_error("Invalid component upgrade for component %s.    Old version: %s     Minimum required version: %s" % (new_comp.getUid(), old_component_version.getVersionString(), required_component_version.getVersionString()))
                break
    targetExtComps = SystemModels.targetCSMModel.external_system_components
    baseExtComps = SystemModels.baseCSMModel.external_system_components
    new_ext_comps = dict(zip([c.getUid() for c in targetExtComps], targetExtComps))
    old_ext_comps = dict(zip([c.getUid() for c in baseExtComps], baseExtComps))
    for uid in new_ext_comps:
        if uid in old_ext_comps:
            required_component_version = new_ext_comps[uid].getUpgradeConstraints().getOldestVersionObject()
            old_component_version = old_ext_comps[uid].getVersionObject()
            if required_component_version.isValid() and required_component_version.compare(old_component_version) > 0:
                tcg_error("Invalid component upgrade for component %s.    Old version: %s     Minimum required version: %s" % (new_comp.getUid(), old_component_version.getVersionString(), required_component_version.getVersionString()))


def generateCampaign(configBasePath,
                     modelContext,
                     online_adapter,
                     base_immdump,
                     cbAmfModel,
                     targetAmfModel,
                     siteConfig,
                     bundleSDPList,
                     configBaseTargetDir,
                     targetSDPDir,
                     tcgScriptDir,
                     deliveryPackageDirs,
                     migration_info,
                     generateOnlyImm,
                     generate_instantiation_campaign=False):

    if generateOnlyImm:
        logging.debug("Model generator started")
    else:
        logging.debug("Campaign generator started")
        if generate_instantiation_campaign:
            logging.debug("Generating an instantiation campaign")

    context = Context.get()
    # context.setYamlModel(yamlModelFiles)

    amfModelPluginModules = {}
    # Loading of amf plugins is intentionally disabled in CMW 4.2 CP2
    # This interface is deprecated and MUST not be used. The rest of the code
    # stays because there are some requirements being studied that may need
    # this interface again. The code should be clean in the future if the
    # conclusion is that the interface is not needed
    # FIXME: enabled again to make LCT/LUT pass until vDicos delivers their implementation of the new interface
    logging.debug("Loading amf model plugin modules")
    amfModelPluginModules.update(loadPluginsUsingVDicosHardcodedDependency(amfModelPluginFilter))

    csmModelExpansionPluginModules = {}
    logging.debug("Loading CSM model expansion plugin modules")
    csmModelExpansionPluginModules.update(loadPlugins(csmModelExpansionPluginFilter))

    csmModelExpansionPlugins = {}
    for uId, module in csmModelExpansionPluginModules.iteritems():
        plugin = module.createCsmModelExpansionPlugin()
        if isinstance(plugin, CSMModelExpansionPlugin):
            csmModelExpansionPlugins[uId] = plugin
        else:
            tcg_error("Error in plugin design for component '%s'. The CMS model "
                      "expansion plugin must be an instance of %s" % (uId, CSMModelExpansionPlugin))

    smfPluginModules = {}
    logging.debug("Loading SMF Campaign plugin modules")
    smfPluginModules.update(loadPlugins(smfCampaignPluginFilter))


    smfPlugins = {}
    for uId, module in smfPluginModules.iteritems():
        plugin = module.createSMFCampaignPlugin()
        smfPlugins[uId] = plugin
        if not isinstance(plugin, SMFCampaignPlugin):
            logging.warn("SMF plugin for component '%s' must be an instance of %s. "
                         "Base classes found: %s." % (uId, SMFCampaignPlugin, type(plugin).__bases__))

    extend_smf_plugins_with_model_expansion(smfPlugins,
                                            csmModelExpansionPlugins)

    plugin_info_providers = set()
    # once all the plugins are instantiated we can initialize them
    for uId, plugin in smfPlugins.iteritems():
        comp = SystemModels.targetCSMModel.getComponent(uId)
        plugin_info_prov = CampGenInfoProviderImpl(uId)
        plugin_info_prov.setCsmConfigRootLocation(comp.getSourceFileLocation())
        plugin_info_prov.setConfigBasePath(configBasePath)
        plugin_info_prov.setConfigBaseTargetDirectory(configBaseTargetDir)
        plugin_info_providers.add(plugin_info_prov)
        plugin_utilities_prov = PluginUtilitiesProviderImpl(uId)
        plugin.prepare(plugin_info_prov, plugin_utilities_prov)

    campaignGeneratorPluginModules = {}

    # Loading of campaign generator plugins is intentionally disabled in CMW 4.2 CP2
    # This interface is deprecated and MUST not be used. The rest of the code
    # stays just in case that an emergency correction is needed. When the new
    # is mature enough we should clean the code.
    # FIXME: enabled again to make LCT/LUT pass until vDicos delivers their implementation of the new interface
    logging.debug("Loading campaign generator plugin modules")
    campaignGeneratorPluginModules.update(loadPluginsUsingVDicosHardcodedDependency(campaignGeneratorPluginFilter))

    campaignGeneratorPlugins = {}
    for unitId, module in campaignGeneratorPluginModules.items():
        if unitId not in csmModelExpansionPlugins:
            modelLocation = SystemModels.targetCSMModel.getComponent(unitId).getSourceFileLocation()
            pluginLocation = SystemModels.targetCSMModel.getComponent(unitId).getPluginsBaseDir()
            pluginContext = CSMModelExpansionPluginContext(configBasePath, siteConfig,
                                                           modelLocation, pluginLocation,
                                                           configBaseTargetDir, tcgScriptDir, deliveryPackageDirs)

            campaignGeneratorPlugins[unitId] = module.createCampaignGeneratorPlugin(pluginContext)
            logging.debug("Campaign generator plugin for %s is loaded." % unitId)
        else:
            logging.info("Component: '%s' has a CSM model expansion plugin and"
                         " also has an old campaign generator plugin. The old "
                         "campaign generator plugin is ignored (not loaded)." % unitId)

    # instantiate internal campaign generator plugin
    campaignGeneratorPlugins[INTERNAL_CAMPAIGN_GENERATOR_PLUGIN_NAME] = CoreMWCampaignGeneratorPlugin.CoreMWCampaignGeneratorPlugin(generate_instantiation_campaign, online_adapter)

    installPrefixes = {}
    for comp in SystemModels.targetCSMModel.system.getComponents():
        if comp.getInstallPrefix() is not None:
            # installPrefixes[comp.getUid()] = comp.getInstallPrefix()
            installPrefixes[comp.getUid()] = AMFConstants.AMFCOMPONENTTYPE_DEFAULT_PREFIX

    validate_comp_uid_supersedes(migration_info)

    for plugin in campaignGeneratorPlugins.values():
        plugin.initialize(installPrefixes)
        if hasattr(plugin, 'setMigrationInfo'):
            plugin.setMigrationInfo(migration_info)

    # filter out not used apps and apptypes from the target model here, before doing anything else with it
    emptyAppBaseTypeDns = []
    for (appTypeDn, appType) in targetAmfModel.getObjects(AMFModel.SaAmfAppType).items():
        if len(appType.getsaAmfApptSGTypes()) == 0:
            emptyAppBaseTypeDns.append(appType.getParentDn())
            targetAmfModel.removeObject(appType.getParentDn())
            targetAmfModel.removeObject(appTypeDn)

    for appBaseType in emptyAppBaseTypeDns:
        targetAmfModel.removeObject(AMFModel.SaAmfApplication.createDn(ImmHelper.getName(appBaseType)))

    appTypes = targetAmfModel.getObjects(AMFModel.SaAmfAppType)
    appBaseTypeDNs = map(ImmHelper.getParentDn, appTypes.keys())

    context.processEntityTypes(targetAmfModel, appTypes)

    generateInstancesForAMFModel(targetAmfModel, siteConfig, amfModelPluginModules,
                                 configBaseTargetDir, generateOnlyImm, online_adapter)

    # If only imm model is required we are done for now
    if generateOnlyImm:
        logging.debug("Model generator finished")
        return (None, None)

    """
    We create an object for the base model, and read the model into it.
    """
    baseAmfModel = AMFModel.AMFModel()
    immdump_base = AMFModel.AMFModel()

    # the base model if there is one, was set earlier
    if SystemModels.baseCSMModel is not None:
        logging.debug("Base CSM model exists...check versions")
        checkTargetOldestVersionsAgainstBase()

    if not base_immdump:
        if not online_adapter.is_offline_instantiation():
            if configBasePath or migration_info:
                tcg_error("Missing immdump file")
    else:
        logging.debug("Parsing imm dump file: %s", base_immdump)
        try:
            immdump_base.parseXML(base_immdump)
        except Exception as e:
            tcg_error("error while parsing base imm dump: " + str(e))

        if configBasePath:
            baseAmfModel = copy.deepcopy(immdump_base)

    """
    Here we are running some checks on the nodes in the base model
    and the target model because role expansion is not supported yet
    """
    extNodeGroups = set()

    for role in siteConfig[CgtConstants.ROLES_TAG]:
        if role.isExternal() and context.hasCompOrService(role.getUid()):
            extNodeGroups.add(role.getUid())

    containedInModel = set()
    for dn, obj in immdump_base.getObjects(AMFModel.SaAmfNodeGroup).items():
        containedInModel.add(obj.getName())

    if containedInModel:
        remainderRoles = extNodeGroups.difference(containedInModel)
        if remainderRoles:
            tcg_error("The following roles are predefined but not found in base model: " + " ".join(remainderRoles))

    postScaleTransformation = AMFModelPostScaleTransformation(baseAmfModel,
                                                              targetAmfModel)
    postScaleTransformation.post_scale_transform()

    # collect all interested app base types
    cbAppTypes = cbAmfModel.getObjects(AMFModel.SaAmfAppType)
    cbAppBaseTypeDNs = map(ImmHelper.getParentDn, cbAppTypes.keys())
    mergedAppBaseTypeDns = list(set(appBaseTypeDNs + emptyAppBaseTypeDns + cbAppBaseTypeDNs))

    amf_diff_calc_result = AMFModelDiffCalcResult(baseAmfModel, targetAmfModel, mergedAppBaseTypeDns)
    sv_target_models = amf_diff_calc_result.get_sv_target_models()

    """
    Calculate the changes in non managed (library) components
    """

    if SystemModels.baseCSMModel:
        extendAmfModelWithNonManagedComponents(SystemModels.baseCSMModel.system, baseAmfModel)
    extendAmfModelWithNonManagedComponents(SystemModels.targetCSMModel.system, targetAmfModel)

    baseNonManagedCTModel = collectNonManagedCTs(baseAmfModel)
    targetNonManagedCTModel = collectNonManagedCTs(targetAmfModel)
    nonManagedCTChanges = targetNonManagedCTModel.diff(baseNonManagedCTModel)

    # get nodes for CTs from base model
    baseCTAllocations = SystemModels.generate_base_component_allocations(baseAmfModel)
    # get nodes for CTs from target model
    targetCTAllocations = SystemModels.generate_target_component_allocations()

    baseCTAllocations_str = {}
    targetCTAllocations_str = {}
    for ct in baseCTAllocations.keys():
        baseCTAllocations_str[ct.getUid()] = baseCTAllocations[ct]
    for ct in targetCTAllocations.keys():
        targetCTAllocations_str[ct.getUid()] = targetCTAllocations[ct]

    """
    Creating a dependency calculator config object. And filling it with data
    from the base model. This extra config object is needed because in the original
    model there are some informations missing like dependencies.
    """
    calcBase = DependencyCalculator.Config()
    calcTarget = DependencyCalculator.Config()

    cts_to_be_installed = set()
    for ct in targetCTAllocations_str.keys():
        if ct not in baseCTAllocations_str.keys():
            cts_to_be_installed.add(ct)

    campaignGeneratorPlugins[INTERNAL_CAMPAIGN_GENERATOR_PLUGIN_NAME].init(
        targetAmfModel, baseAmfModel, cts_to_be_installed, extNodeGroups, nonManagedCTChanges,
        immdump_base, amf_diff_calc_result)

    for key, plugin in campaignGeneratorPlugins.items():
        if key == INTERNAL_CAMPAIGN_GENERATOR_PLUGIN_NAME:
            plugin.fillConfig(calcBase, baseCTAllocations, True)
            plugin.fillConfig(calcTarget, targetCTAllocations, False)
        else:
            plugin.fillConfig(calcBase, baseCTAllocations_str, True)
            plugin.fillConfig(calcTarget, targetCTAllocations_str, False)

    for plugin in csmModelExpansionPlugins.itervalues():
        baseExtensionList = plugin.extendDependencyCalculation(True)
        extend_dependency_calculation(calcBase, baseExtensionList, plugin)

        targetExtensionList = plugin.extendDependencyCalculation(False)
        extend_dependency_calculation(calcTarget,
                                      targetExtensionList,
                                      plugin)

    # Here we set the allocated nodes to the units (CT and SV). This is only
    # required to suport the old CampaignGenerator interface where vDicos
    # creates the CT and SV without nodes. In the CTs and SVs handled by CMW
    # and in the new model expansion interface, we set the nodes at creation
    # time, so this is not required. Please remove when removing the support
    # for old CampaignGenerator plugin
    fillPrelimNodeAlloc(calcBase)
    fillPrelimNodeAlloc(calcTarget)

    """
    Here we calculate the campaigns and procedures required for the
    install and in what step what entities on which nodes should be
    installed.
    The result will contain a list of campaigns which contain a list
    of procedures which contain a map nodes to the amf entities they
    need to be installed with.
    """
    calculator = DependencyCalculator.Calculator(SystemModels.baseCSMModel is not None)

    calcBase.displayConfig("Dependency calculator base config:")
    calcTarget.displayConfig("Dependency calculator target config:")

    comp_types_to_be_migrated = getCompTypesToBeMigrated(migration_info, immdump_base)
    setCompTypesToBeMigratedInProviders(comp_types_to_be_migrated, plugin_info_providers)
    calculator.install(calcBase, calcTarget, comp_types_to_be_migrated)

    """
    This function call puts the dependencies that are in CSM model
    into the dependency calculator config object.
    """
    updateDependencies(calcTarget)

    mergedRolling = calculator.calculate_partition(calcBase, calcTarget)

    (install_cts, upgrade_cts, remove_cts, nochange_cts, migrate_cts) = \
        get_component_actions(calculator)

    campaignIndex = -1
    campaignCount = len(calculator.getCampaigns()) - 1
    campaignList = []

    """
    Find install/migration component type and update relative path cmd only
    """
    for comp in (install_cts | migrate_cts):
        compCSM = SystemModels.targetCSMModel.getComponent(comp)
        if compCSM.getAvailabilityManager().upper() != CSMConstants.AVAILABILTY_MANAGER_AMF:
            continue

        def get_prefix_path_for_comp_from_base(component, amfModel):
            sws = component.getMetaData().getSoftwares()
            if len(sws) == 0:
                return None
            targetswBundle = sws[0][CgtConstants.META_BUNDLE_NAME_TAG]
            for swInstalledDn, swInstalledObj in amfModel.getObjects(AMFModel.SaAmfNodeSwBundle).items():
                if re.match(r"safSmfBundle=(ERIC-|3PP-)?" + targetswBundle, ImmHelper.getName(swInstalledDn)):
                    return swInstalledObj.getsaAmfNodeSwBundlePathPrefix()
            else:
                return None

        def remove_common_dir(prefix, gen_cmd):
            if prefix[-1] != "/":
                prefix = prefix + "/"
            common = os.path.commonprefix([prefix, gen_cmd])
            common_index = len(os.path.dirname(common))
            return gen_cmd[common_index + 1:] if gen_cmd[common_index] == "/" else gen_cmd[common_index:]

        def adapt_gen_ref_path_to_prefix(prefix, gen_cmd):
            des_cmd = gen_cmd
            if prefix != "/" and gen_cmd != None:
                if len(gen_cmd) > 0 and gen_cmd[0] == "/":
                    # Reformat path in order to excute string
                    gen_cmd = os.path.realpath(gen_cmd)
                    prefix = os.path.realpath(prefix)
                    des_cmd = remove_common_dir(prefix, gen_cmd)
                    retry = 20
                    while retry > 0:
                        if gen_cmd == os.path.realpath(os.path.join(prefix, des_cmd)):
                            break
                        des_cmd = os.path.join("../", des_cmd)
                        retry = retry - 1
                    else:
                        tcg_error("Fail to adapt path %s" % gen_cmd)
            return des_cmd

        cur_prefix = get_prefix_path_for_comp_from_base(compCSM, immdump_base)
        if cur_prefix != None:
            targetCompTypeObj = targetAmfModel.getObjects(AMFModel.SaAmfCompType, AMFTools.getCompBaseTypeDnFromUnit(comp)).values()[0]
            targetCompTypeObj.setsaAmfCtRelPathInstantiateCmd(adapt_gen_ref_path_to_prefix(cur_prefix, targetCompTypeObj.getsaAmfCtRelPathInstantiateCmd_unsafe()))
            targetCompTypeObj.setsaAmfCtRelPathTerminateCmd(adapt_gen_ref_path_to_prefix(cur_prefix, targetCompTypeObj.getsaAmfCtRelPathTerminateCmd_unsafe()))
            targetCompTypeObj.setsaAmfCtRelPathCleanupCmd(adapt_gen_ref_path_to_prefix(cur_prefix, targetCompTypeObj.getsaAmfCtRelPathCleanupCmd_unsafe()))
            targetCompTypeObj.setosafAmfCtRelPathHcCmd(adapt_gen_ref_path_to_prefix(cur_prefix, targetCompTypeObj.getosafAmfCtRelPathHcCmd_unsafe()))

    for comp in list(install_cts | upgrade_cts | remove_cts):
        if comp in remove_cts:
            compCSM = SystemModels.baseCSMModel.getComponent(comp)
        else:
            compCSM = SystemModels.targetCSMModel.getComponent(comp)
        software_type = compCSM.get_software_type()

        if software_type == CgtConstants.COMPONENT_SOFTWARE_RPM_TAG:
            logging.debug('%s component contains RPM software, checking for its provider' % compCSM.getName())
            meta_data = compCSM.getMetaData()
            amfModel = baseAmfModel if configBasePath else immdump_base
            available_sw_bundles = amfModel.getObjects(AMFModel.SaSmfSwBundle).keys()
            default_provider = AMFTools.getProvider()

            software_names = compCSM.get_software_name_without_version()
            for filename, bundle in meta_data.softwares():
                # Find rpm bundle name missing prefix
                if not (bundle.startswith(default_provider + "-") or bundle.startswith("3PP-")):
                    new_bundle_name = online_adapter.get_rpm_name(bundle, filename)
                    logging.debug('Online adapter returned %s for %s' % (new_bundle_name, filename))
                    # update sofware in meta data of component
                    meta_data.updateSoftware(filename, new_bundle_name)

                    old_bundle_name = default_provider + "-" + bundle
                    if new_bundle_name != old_bundle_name:
                        logging.debug('Detect bundle name update, old name: %s, new name: %s'
                                      % (old_bundle_name, new_bundle_name))
                        # update service target model for generate campaign
                        ref_sw_bundle = AMFTools.getSaSmfSwBundleDnFromUnit(old_bundle_name)
                        for svId in SystemModels.targetCSMModel.get_component_allcated_services(comp):
                            if svId in sv_target_models.keys():
                                targetModel, _, _, added, _, _, _ = sv_target_models[svId]
                                for (compTypeDn, compType) in targetModel.getObjects(AMFModel.SaAmfCompType).items():
                                    if compTypeDn in added:
                                        # Get right bundle name and correct it in amf model if needed
                                        if compType.getsaAmfCtSwBundle() == ref_sw_bundle:
                                            logging.debug('Updating %s with new bundle' % compTypeDn)
                                            compType.setsaAmfCtSwBundle(AMFTools.getSaSmfSwBundleDnFromUnit(new_bundle_name))

                        # update target AMF model for generate AMF config base
                        tmp_SafAmfNodeSwBundle = copy.deepcopy(targetAmfModel.getObjects(AMFModel.SaAmfNodeSwBundle))
                        for dn, obj in tmp_SafAmfNodeSwBundle.iteritems():
                            if AMFTools.getNodeSwBundleDnFromUnit(old_bundle_name) in dn:
                                nodeSwBundle = AMFModel.SaAmfNodeSwBundle()
                                nodeSwBundle._dn = dn.replace(old_bundle_name, new_bundle_name)
                                nodeSwBundle.setsaAmfNodeSwBundlePathPrefix(obj.getsaAmfNodeSwBundlePathPrefix())
                                targetAmfModel.removeObject(dn)
                                targetAmfModel.addObject(nodeSwBundle)
                        del tmp_SafAmfNodeSwBundle

    # We need to keep track of the models already delivered because, in case
    # of generation of multiple campaigns, only one campaign has to deliver the
    # models. This used to prevent that two campaigns deliver the same models
    # when the same bundle is shared between components installed in different
    # campaigns
    delivered_models = set()

    # We need to keep track of the scripts that are already copied. This is
    # because in the case of generation of multiple campaigns, the same
    # component can be present in more than one campaign, but the scripts need
    # to be included only once (in the first campaign where the component is
    # present
    component_scripts_already_copied = set()

    usedBundleSDPList = []

    """
    The rest from here is the smf campaign generation
    """
    alreadyProcessedCampaigns = set()

    for campaign in calculator.getCampaigns():
        campaignIndex = campaignIndex + 1

        name = time.strftime("%Y_%m_%d-%H%M%S", time.gmtime())
        campaignName = "ERIC-TCG_CAMPAIGN" + str(campaignIndex) + "-" + name

        campaignDirectory = os.path.join(targetSDPDir, campaignName)

        setCurrentCampaignInProviders(campaign,
                                      campaignDirectory,
                                      plugin_info_providers)

        baseAmfModel = baseAmfModel if configBasePath else immdump_base
        smfCampaign = SMFCampaign.SMFCampaign(campaignName, baseAmfModel)

        for plugin in campaignGeneratorPlugins.values():
            plugin.startCampaign(campaign.getProcedures(), campaignName, smfCampaign, campaignDirectory)

        # skip processing campaign zero (campaign zero contains the already installed softwares)
        if campaignIndex == 0:
            for plugin in campaignGeneratorPlugins.values():
                plugin.endCampaign()
            continue

        assert (not campaign.isEmpty())

        logging.debug("Generating campaign: " + campaignName)

        campaignList.append(campaignName)

        smfPluginsInCampaign = filterActivePlugins(smfPlugins,
                                                   campaign,
                                                   alreadyProcessedCampaigns,
                                                   SystemModels.baseCSMModel)

        csmModelExpansionPluginsInCampaign = filterActivePlugins(csmModelExpansionPlugins,
                                                                 campaign,
                                                                 alreadyProcessedCampaigns,
                                                                 SystemModels.baseCSMModel)

        Utils.mkdir_safe(campaignDirectory)
        copy_scripts_in_camp_dir(smfPluginsInCampaign,
                                 component_scripts_already_copied,
                                 campaignDirectory)


        legacyInitializationOfSmfPlugin(smfPluginsInCampaign,
                                        campaignName,
                                        campaign.getComponentTypes(),
                                        install_cts,
                                        upgrade_cts,
                                        remove_cts,
                                        nochange_cts,
                                        migrate_cts)

        for smf_plugin in smfPluginsInCampaign.itervalues():
            smf_plugin.startCampaign()

        smfCampaign.beginCampaignInitialization()
        smfCampaign.beginAddToImm()

        if not generate_instantiation_campaign:
            for plugin in campaignGeneratorPlugins.values():
                plugin.addTypes()

        smfCampaign.endAddToImm()

        for key, plugin in campaignGeneratorPlugins.iteritems():
            try:
                plugin.generateCampInitActions(SMFConstants.CAMP_INIT_PHASE_ADD_TO_IMM, campaignDirectory, getMergeableCampaignName())
            except Exception as e:
                tcg_error("Unexpected error while calling generateCampInitActions with 'CAMP_INIT_PHASE_ADD_TO_IMM' for unit id: " + key + str(e))

        for key, plugin in campaignGeneratorPlugins.iteritems():
            try:
                plugin.generateCampInitActions(SMFConstants.CAMP_INIT_PHASE_CB_AT_INIT, campaignDirectory, getMergeableCampaignName())
            except Exception as e:
                tcg_error("Unexpected error while calling generateCampInitActions with 'CAMP_INIT_PHASE_CB_AT_INIT' for unit id: " + key + str(e))

        generatePluginCallbacks(smfPluginsInCampaign, smfCampaign.generateCallbackAtInit, "callbackAtCampaignInit")

        for key, plugin in campaignGeneratorPlugins.iteritems():
            try:
                plugin.generateCampInitActions(SMFConstants.CAMP_INIT_PHASE_CB_AT_BACKUP, campaignDirectory, getMergeableCampaignName())
            except Exception as e:
                tcg_error("Unexpected error while calling generateCampInitActions with 'CAMP_INIT_PHASE_CB_AT_BACKUP' for unit id: " + key + str(e))


        for key, plugin in campaignGeneratorPlugins.iteritems():
            try:
                plugin.generateCampInitActions(SMFConstants.CAMP_INIT_PHASE_CB_AT_ROLLBACK, campaignDirectory, getMergeableCampaignName())
            except Exception as e:
                tcg_error("Unexpected error while calling generateCampInitActions with 'CAMP_INIT_PHASE_CB_AT_ROLLBACK' for unit id: " + key + str(e))

        generatePluginCallbacks(smfPluginsInCampaign, smfCampaign.generateCallbackAtRollback, "callbackAtCampaignRollback")

        campaign_bundles = extract_bundles(campaignGeneratorPlugins,
                                           csmModelExpansionPluginsInCampaign,
                                           generate_instantiation_campaign)
        usedBundleSDPList += add_model_delivery_modify_operations(smfCampaign,
                                                                  campaign_bundles,
                                                                  smfPluginsInCampaign,
                                                                  delivered_models)
        add_model_delivery_done_operations(smfCampaign, campaign_bundles, smfPluginsInCampaign)

        smfCampaign.call_plugin_cli_action_at_camp_init(smfPluginsInCampaign)

        for plugin in campaignGeneratorPlugins.values():
            plugin.generateCampInitActions(SMFConstants.CAMP_INIT_PHASE_CAMP_INIT_ACTION, campaignDirectory, getMergeableCampaignName())

        #generate updating SwmBundle objs for rebooting
        def create_update_scope_object(rebootInfoSwBundle):
            updateAttributes = []
            if CgtConstants.INSTALL_REBOOT_FLAG in rebootInfoSwBundle and rebootInfoSwBundle[CgtConstants.INSTALL_REBOOT_FLAG]:
                updateAttributes.append(('saSmfBundleInstallOfflineScope','SA_IMM_ATTR_SAUINT32T','4'))
            if CgtConstants.UPGRDADE_REBOOT_FLAG in rebootInfoSwBundle and rebootInfoSwBundle[CgtConstants.UPGRDADE_REBOOT_FLAG]:
                updateAttributes.append(('saSmfBundleRemoveOfflineScope','SA_IMM_ATTR_SAUINT32T','4'))
            if updateAttributes is not None:
                return updateAttributes

        def generate_modify_scope_attr_swbundle_object():
            #build up update objects list
            rebootUpdateForSwBundles = online_adapter.get_reboot_update_for_sw_bundle_mapping()
            update_objs = {}
            for swBundleName in rebootUpdateForSwBundles:
                dn = "safSmfBundle=" + swBundleName
                rebootInfoSwBundle = rebootUpdateForSwBundles[swBundleName]
                update_objs[dn] = create_update_scope_object(rebootInfoSwBundle)

            if not generate_instantiation_campaign and update_objs:
                smfCampaign.beginCampInitAction()
                smfCampaign.beginImmCCB()

                for dn in update_objs:
                    smfCampaign.generateModifyObject(dn, update_objs[dn], True)

                smfCampaign.endImmCCB()
                smfCampaign.endCampInitAction()

        generate_modify_scope_attr_swbundle_object()

        smfCampaign.endCampaignInitialization()

        procedureIndex = 0

        numberOfProcedures = len(campaign.getProcedures())

        init_callbacks_mergedrolling = []
        added_init_callbacks = set()
        init_clis_mergedrolling = []
        added_init_clis = set()
        wrapup_callbacks_mergedrolling = []
        added_wrapup_callbacks = set()
        wrapup_clis_mergedrolling = []
        added_wrapup_clis = set()

        if mergedRolling:
            for proc in campaign.getProcedures():
                setCurrentProcedureInProviders(proc, plugin_info_providers)
                comp_types_for_plugin_in_proc_scope = proc.getComponentTypes()
                comp_types_for_plugin_in_proc_scope.update(csmModelExpansionPluginsInCampaign.iterkeys())

                for ct in [x for x in comp_types_for_plugin_in_proc_scope if x in smfPluginsInCampaign]:
                    if ct not in added_init_callbacks:
                        callback = smfPluginsInCampaign[ct].callbackAtProcInit()
                        if callback:
                            init_callbacks_mergedrolling.append(callback)
                            added_init_callbacks.add(ct)
                    if ct not in added_init_clis:
                        callback = smfPluginsInCampaign[ct].cliAtProcInit()
                        if callback:
                            init_clis_mergedrolling.append(callback)
                            added_init_clis.add(ct)
                    if ct not in added_wrapup_callbacks:
                        callback = smfPluginsInCampaign[ct].callbackAtProcWrapup()
                        if callback:
                            wrapup_callbacks_mergedrolling.append(callback)
                            added_wrapup_callbacks.add(ct)
                    if ct not in added_wrapup_clis:
                        callback = smfPluginsInCampaign[ct].cliAtProcWrapup()
                        if callback:
                            wrapup_clis_mergedrolling.append(callback)
                            added_wrapup_clis.add(ct)

        for proc in campaign.getProcedures():
            setCurrentProcedureInProviders(proc, plugin_info_providers)

            # This variable is the set of component types to be considered for
            # the SMF plugin operations at procedure level. The set is composed
            # by the component types that have an instance present in the
            # current procedure, plus the component types that contain a CSM
            # model expansion plugin (independent if they are present in the
            # procedure or not). This means that the plugin methods for CSM
            # model expansion plugins will be called in all the procedures. It
            # is up to the authors of the model expansion plugin to decide when
            # they return a callback/CLI. This behavior is required because
            # some implementations of CSM model expansion plugins need to
            # introduce callbacks/CLIs even in those procedures where their
            # components are not present.
            comp_types_for_plugin_in_proc_scope = proc.getComponentTypes()
            comp_types_for_plugin_in_proc_scope.update(csmModelExpansionPluginsInCampaign.iterkeys())
            if generate_instantiation_campaign:
                procedureName = "csminstantiation_proc_"
            elif len(comp_types_for_plugin_in_proc_scope) == 0:
                procedureName = "csm_proc_"
            elif any(ct in migrate_cts for ct in comp_types_for_plugin_in_proc_scope):
                procedureName = "csmmigration_proc_"
            elif all(ct in remove_cts for ct in comp_types_for_plugin_in_proc_scope):
                procedureName = "csmremove_proc_"
            elif SystemModels.baseCSMModel is not None:  # have config-base
                procedureName = "csmupgrade_proc_"
            else:
                procedureName = "csminstall_proc_"
            procedureName += str(procedureIndex)
            procedureIndex = procedureIndex + 1
            smfCampaign.beginUpgradeProcedure(procedureName, procedureIndex)

            for plugin in campaignGeneratorPlugins.values():
                plugin.startProcedure(proc)

            for plugin in campaignGeneratorPlugins.values():
                plugin.generateProcInit(None)
            # some optimization: generate all the procinits in the first procedure if possible
            if mergedRolling:
                if procedureIndex == 1:
                    campaignGeneratorPlugins[INTERNAL_CAMPAIGN_GENERATOR_PLUGIN_NAME].setMergedAndFirst()#mergedRolling, procedureIndex == 1
                    for clis_for_ct in init_clis_mergedrolling:
                        smfCampaign.create_cli_actions_at_proc_init(ct, clis_for_ct)

                    for callbacks_for_ct in init_callbacks_mergedrolling:
                        for (label, timeout, stringToPass) in callbacks_for_ct:
                            smfCampaign.beginProcInitAction()
                            smfCampaign.generateCallback(label, timeout, stringToPass)
                            smfCampaign.endProcInitAction()
            else:
                for ct in [x for x in comp_types_for_plugin_in_proc_scope if x in smfPluginsInCampaign]:
                    clis = smfPluginsInCampaign[ct].cliAtProcInit()
                    smfCampaign.create_cli_actions_at_proc_init(ct, clis)

                    callbacks = smfPluginsInCampaign[ct].callbackAtProcInit()
                    for (label, timeout, stringToPass) in callbacks:
                        smfCampaign.beginProcInitAction()
                        smfCampaign.generateCallback(label, timeout, stringToPass)
                        smfCampaign.endProcInitAction()

            if proc.getType() == DependencyCalculator.Procedure.PROCEDURE_TYPE_SINGLESTEP:
                for plugin in campaignGeneratorPlugins.values():
                    plugin.generateSingleStepProcedureInit()
                smfCampaign.beginUpgradeMethod()
                smfCampaign.beginSingleStepUpgrade()
                smfCampaign.beginUpgradeScope()
                smfCampaign.beginForAddRemove()
                smfCampaign.beginDeactivationUnit()
                for plugin in campaignGeneratorPlugins.values():
                    if hasattr(plugin, 'generateDeactivationUnit'):
                        plugin.generateDeactivationUnit()
                if not generate_instantiation_campaign:
                    for plugin in csmModelExpansionPluginsInCampaign.itervalues():
                        sw_to_remove = plugin.removeSoftwareInSingleStep()
                        remove_sws_in_nodes(smfCampaign, sw_to_remove)
                smfCampaign.endDeactivationUnit()
                smfCampaign.beginActivationUnit()
                for plugin in campaignGeneratorPlugins.values():
                    plugin.generateSingleStepProcedureBody()
                if not generate_instantiation_campaign:
                    for plugin in csmModelExpansionPluginsInCampaign.itervalues():
                        sw_to_add = plugin.addSoftwareInSingleStep()
                        add_sws_in_nodes(smfCampaign, sw_to_add)
                smfCampaign.endActivationUnit()
                smfCampaign.endForAddRemove()
                smfCampaign.endUpgradeScope()
                smfCampaign.beginUpgradeStep()
                smfCampaign.endUpgradeStep()
                smfCampaign.endSingleStepUpgrade()
                smfCampaign.endUpgradeMethod()
            elif proc.getType() == DependencyCalculator.Procedure.PROCEDURE_TYPE_ROLLING:
                for plugin in campaignGeneratorPlugins.values():
                    plugin.generateRollingProcedureInit()
                smfCampaign.beginUpgradeMethod()
                smfCampaign.beginRollingUpgrade()
                smfCampaign.beginUpgradeScope()
                smfCampaign.beginByTemplate()
                targetNG = None
                baseNGNameList = baseAmfModel.getObjects(AMFModel.SaAmfNodeGroup).keys()
                for role in context.getRoles():
                    nodes = sorted(context.getNodesForRole(role))
                    if nodes == proc.getNodes():
                        targetNG = AMFTools.getNodeGroupDnFromPGName(role)
                        if targetNG in baseNGNameList:
                            break
                        else:
                            targetNG = None
                if targetNG is None:
                    tcg_error("Could not find matching node group for nodes: " + str(proc.getNodes()))
                smfCampaign.beginTargetNodeTemplate(targetNG)

                # CoreMWCampaignGeneratorPlugin to add swRemove.
                campaignGeneratorPlugins[INTERNAL_CAMPAIGN_GENERATOR_PLUGIN_NAME].generateRollingProcedureAddSwRemove()
                if not generate_instantiation_campaign:
                    for plugin in csmModelExpansionPluginsInCampaign.itervalues():
                        sw_to_remove = plugin.removeSoftwareInRolling()
                        remove_sws(smfCampaign, sw_to_remove)
                for plugin in campaignGeneratorPlugins.values():
                    plugin.generateRollingProcedureBody()
                # CoreMWCampaignGeneratorPlugin to add swAdd.
                campaignGeneratorPlugins[INTERNAL_CAMPAIGN_GENERATOR_PLUGIN_NAME].generateRollingProcedureAddSwAdd()
                if not generate_instantiation_campaign:
                    for plugin in csmModelExpansionPluginsInCampaign.itervalues():
                        sw_to_add = plugin.addSoftwareInRolling()
                        add_sws(smfCampaign, sw_to_add)
                smfCampaign.endTargetNodeTemplate()
                for plugin in campaignGeneratorPlugins.values():
                    plugin.generateRollingProcedureTargetEntityTemplate()
                smfCampaign.endByTemplate()
                smfCampaign.endUpgradeScope()
                smfCampaign.beginUpgradeStep()
                smfCampaign.generateRollingUpgradeStepCallbacks(comp_types_for_plugin_in_proc_scope, smfPluginsInCampaign)
                smfCampaign.endUpgradeStep()
                smfCampaign.endRollingUpgrade()
                smfCampaign.endUpgradeMethod()

            else:
                assert (0)

            """
            There are two types of wrapups:
            1 - Procedure specific procWrapup actions. If someone wants to do
            a procWrapup action right after the procedure in which the component
            is installed this should be used.
            2 - Campaign specific procWrapup actions. These actions can be done
            at procWrapup section of the last procedure of the campaign.
            """

            """ 1 - Procedure specific """
            for plugin in campaignGeneratorPlugins.values():
                plugin.generateProcWrapup()

            """ 2 - Campaign specific """
            # some optimization: generate all the procwrapup in the last procedure if possible
            if mergedRolling:
                if procedureIndex == numberOfProcedures:
                    for clis_for_ct in wrapup_clis_mergedrolling:
                        smfCampaign.create_cli_actions_at_proc_wrapup(ct, clis_for_ct)

                    for callbacks_for_ct in wrapup_callbacks_mergedrolling:
                        for (label, timeout, stringToPass) in callbacks_for_ct:
                            smfCampaign.beginProcWrapupAction()
                            smfCampaign.generateCallback(label, timeout, stringToPass)
                            smfCampaign.endProcWrapupAction()
            else:
                for ct in [x for x in comp_types_for_plugin_in_proc_scope if x in smfPluginsInCampaign]:
                    clis = smfPluginsInCampaign[ct].cliAtProcWrapup()
                    smfCampaign.create_cli_actions_at_proc_wrapup(ct, clis)

                    callbacks = smfPluginsInCampaign[ct].callbackAtProcWrapup()
                    for (label, timeout, stringToPass) in callbacks:
                        smfCampaign.beginProcWrapupAction()
                        smfCampaign.generateCallback(label, timeout, stringToPass)
                        smfCampaign.endProcWrapupAction()

            smfCampaign.endUpgradeProcedure()

        smfCampaign.beginCampaignWrapup()

        smfCampaign.call_plugin_cli_action_at_camp_complete(smfPluginsInCampaign)

        smfCampaign.generateWaitToCommit()

        for plugin in campaignGeneratorPlugins.values():
            plugin.generateCommit()

        generatePluginCallbacks(smfPluginsInCampaign, smfCampaign.generateCallbackAtCommit, "callbackAtCampaignCommit")

        smfCampaign.call_plugin_cli_action_at_camp_wrapup(smfPluginsInCampaign)

        smfCampaign.generateWaitToAllowNewCampaign()
        smfCampaign.beginRemoveFromImm()

        if campaignIndex == campaignCount:  # last campaign
            for plugin in campaignGeneratorPlugins.values():
                plugin.generateRemoveFromImm()

        smfCampaign.endRemoveFromImm()
        smfCampaign.endCampaignWrapup()
        smfCampaign.finish(os.path.join(campaignDirectory, "campaign.template.xml"))

        for plugin in campaignGeneratorPlugins.values():
            plugin.endCampaign()
        for plugin in smfPluginsInCampaign.itervalues():
            plugin.endCampaign()

        SDPTools.generateSDPFromDirectory(campaignDirectory, targetSDPDir, campaignName, campaignSDP=True)
        shutil.rmtree(campaignDirectory)

        # Create the marker if needed so that the caller will know if the ONE-STEP upgrade should be activated
        # for this campaign or not.
        if smfCampaign.needOneStepUpgrade():
            logging.warn('Migration on COMPUTE RESOURCE scope is detected. ONE-STEP upgrade should be activated'
                         ' before running this campaign')
            marker = open(os.path.join(targetSDPDir, ONE_STEP_UPGRADE_MARKER), 'w')
            marker.close()

        alreadyProcessedCampaigns.add(campaign)

    for plugin in campaignGeneratorPlugins.values():
        plugin.generatePostCampaign()

    for plugin in smfPlugins.itervalues():
        plugin.finalize()

    logging.debug("Campaign generator finished")

    return (campaignList, usedBundleSDPList)


def getCompTypesToBeMigrated(migration_info, immdump_base):
    ret = set()
    for comp in SystemModels.targetCSMModel.components_in_system():
        uid = comp.getUid()
        if uid in migration_info and at_least_one_supersede_exists(immdump_base,
                                                                   migration_info[uid]):
            ret.add(uid)
    return ret


def at_least_one_supersede_exists(amf_base, supersedes):
    installed_bundles = map(ImmHelper.getName, amf_base.getObjects(AMFModel.SaAmfNodeSwBundle))
    for supersede in supersedes:
        if CgtConstants.COMPONENT_SUPERSEDES_BASE_COMPONENT_TAG in supersede:
            comp_base_type_name_dn = u"safCompType=" + supersede[CgtConstants.COMPONENT_SUPERSEDES_BASE_COMPONENT_TAG]
            if comp_base_type_name_dn in amf_base.getObjects():
                return True
        elif CgtConstants.COMPONENT_SUPERSEDES_SOFTWARE_TAG in supersede:
            superseded_sdp = SDPTools.get_bundle_name_with_provider_missing(installed_bundles,
                                supersede[CgtConstants.COMPONENT_SUPERSEDES_SOFTWARE_TAG])
            if superseded_sdp is None:
                continue
            for sdpName in installed_bundles:
                if sdpName.startswith("safSmfBundle=" + superseded_sdp):
                    return True
    return False


def copy_scripts_in_camp_dir(smf_plugins,
                             component_scripts_already_copied,
                             camp_dir):
    for uid in smf_plugins:
        if uid not in component_scripts_already_copied:
            comp = SystemModels.targetCSMModel.get_component_in_system(uid)
            campaignPluginDir = os.path.join(comp.getPluginsBaseDir(),
                                             comp.getPlugin())
            src = os.path.join(campaignPluginDir, "scripts")
            if os.path.exists(src):
                dest = os.path.join(camp_dir, uid.replace(os.sep, "_"), "scripts")
                if not os.path.exists(dest):
                    os.makedirs(dest)
                logging.debug("Copying scripts from %s to %s for unit %s" %
                              (src, dest, uid))
                distutils.dir_util.copy_tree(src, dest)
            else:
                logging.warning("Plugins path specified but could not find scripts"
                                " dir for component %s", uid)
            component_scripts_already_copied.add(uid)


def setCurrentProcedureInProviders(procedure, plugin_info_providers):
    for prov in plugin_info_providers:
        prov.setCurrentProcedure(procedure)


def setCompTypesToBeMigratedInProviders(compTypes, plugin_info_providers):
    for prov in plugin_info_providers:
        prov.setCompTypesToBeMigrated(compTypes)


def setCurrentCampaignInProviders(camp,
                                  camp_dir,
                                  plugin_info_providers):
    for prov in plugin_info_providers:
        prov.setCurrentCampaign(camp)
        prov.setCurrentCampaignDir(camp_dir)


def legacyInitializationOfSmfPlugin(smfPluginsInCampaign,
                                    campaignName,
                                    current_campaign_cts,
                                    install_cts,
                                    upgrade_cts,
                                    remove_cts,
                                    nochange_cts,
                                    migrate_cts):
    """
    This function performs the legacy initialization of SMF plugins. This is
    needed until the deprecated code is removed. The new SMF plugins are
    initialized through the prepare() function
    """
    for uid, plugin in smfPluginsInCampaign.iteritems():
        plugin._campaignName = campaignName
        plugin._ctRootDir = uid
        plugin._isCtToBeMigrated = uid in migrate_cts
        if uid in current_campaign_cts:
            # The different action groups are calculated for all the campaigns
            # but we only consider them when the component is in the current
            # campaign
            plugin._ctAction = findout_legacy_plugin_action(uid,
                                                            install_cts,
                                                            upgrade_cts,
                                                            remove_cts,
                                                            nochange_cts,
                                                            migrate_cts)
        else:
            plugin._ctAction = SMFCampaignPlugin.CT_ACTION_NOOP


def findout_legacy_plugin_action(uid,
                                 install_cts,
                                 upgrade_cts,
                                 remove_cts,
                                 nochange_cts,
                                 migrate_cts):
    if uid in migrate_cts:
        # handle the MIGRATION as sub-use-case of UPGRADE
        return SMFCampaignPlugin.CT_ACTION_UPGRADE
    if uid in install_cts:
        return SMFCampaignPlugin.CT_ACTION_INSTALL
    if uid in upgrade_cts:
        return SMFCampaignPlugin.CT_ACTION_UPGRADE
    if uid in nochange_cts:
        return SMFCampaignPlugin.CT_ACTION_NOOP
    if uid in remove_cts:
        tcg_error("Remove component is not supported yet.")


def filterActivePlugins(smfPlugins,
                        currentCampaign,
                        alreadyProcessedCampaigns,
                        base_model):
    """
    This function returns a dictionary of the form {uid, plugin} containing
    the plugins that must be considered in the received campaign. A plugin
    must be part of a campaign in the following situations:
    1- The corresponding component is already part of the system (base model)
    This means that the plugin for existing components will always be
    considered even if there is no software management operation for it (this
    is required by some components that need to inject callbacks/clis even when
    they are not upgraded).
    2- The corresponding component is not part of the base system but it is
    going to be installed in the received campaign
    3- The corresponding component is not part of the base system, the
    corresponding component is not part of the received campaign, but the
    corresponding component is part of one of the previously processed
    campaigns. That is, in case of multiple campaigns, the later campaigns
    include the components from the previous campaigns which are already part
    of the system.
    If a component is not part of the system yet and it is not going to be
    installed in the received campaign, then the component will be ignored.
    """
    ret = {}

    # collect comp types for current and previous campaigns
    comps_type_in_camp = currentCampaign.getComponentTypes()
    for camp in alreadyProcessedCampaigns:
        comps_type_in_camp.update(camp.getComponentTypes())

    for uid, plugin in smfPlugins.iteritems():
        if (base_model is not None) and \
                (base_model.system.getComponent(uid) is not None):
            ret[uid] = plugin
        elif uid in comps_type_in_camp:
            ret[uid] = plugin
    return ret


def add_sws_in_nodes(smf_campaign, sw_to_add):
    for bundle, nodes in sw_to_add.iteritems():
        add_sw(smf_campaign, bundle, nodes)


def add_sws(smf_campaign, sw_to_add):
    for bundle in sw_to_add:
        add_sw(smf_campaign, bundle)


def add_sw(smf_campaign, bundle, nodes=[]):
    if not smf_campaign.skip_generate_markup_tag(AMFTools.getNodeSwBundleTemplateDnFromSDP(bundle)):
        amf_bundle = AMFTools.getSaSmfSwBundleDnFromUnit(bundle)
        smf_campaign.beginSwAdd(amf_bundle, AMFConstants.AMFCOMPONENTTYPE_DEFAULT_PREFIX)
        for node in nodes:
            smf_campaign.generatePlmExecEnv(AMFTools.getNodeDnFromName(node))
        smf_campaign.endSwAdd()


def remove_sws_in_nodes(smf_campaign, sw_to_remove):
    for bundle, nodes in sw_to_remove.iteritems():
        remove_sw(smf_campaign, bundle, nodes)


def remove_sws(smf_campaign, sw_to_remove):
    for bundle in sw_to_remove:
        remove_sw(smf_campaign, bundle)


def remove_sw(smf_campaign, bundle, nodes=[]):
    if smf_campaign.skip_generate_markup_tag(AMFTools.getNodeSwBundleTemplateDnFromSDP(bundle)):
        amf_bundle = AMFTools.getSaSmfSwBundleDnFromUnit(bundle)
        smf_campaign.beginSwRemove(amf_bundle, AMFConstants.AMFCOMPONENTTYPE_DEFAULT_PREFIX)
        for node in nodes:
            smf_campaign.generatePlmExecEnv(AMFTools.getNodeDnFromName(node))
        smf_campaign.endSwRemove()


def extend_dependency_calculation(config, extension_list, extension_pugin):
    """
    Extends the received dependency calculator config object with the pools,
    services and components received through the plugin API.
    Creates the internal dependency calculator objects mapping the plugin API
    objects
    """
    for pool in extension_list:
        nodes = set([cr.name for cr in pool.nodes])
        new_pool = DependencyCalculator.Pool(pool.name, nodes)
        config.addPool(new_pool)
        for sv in pool.services:
            new_sv = DependencyCalculator.SV(sv.uid, sv.version, nodes)
            new_pool.addSV(new_sv)
            new_sv.setPlugin(extension_pugin)
            for ct_inst in sv.componentInstances:
                new_ct_inst = DependencyCalculator.CT(ct_inst.component.uid,
                                                      ct_inst.instanceName,
                                                      ct_inst.component.version,
                                                      nodes)
                new_sv.addCT(new_ct_inst)
                new_ct_inst.addSV(new_sv)
                new_ct_inst.setPlugin(extension_pugin)


def extend_smf_plugins_with_model_expansion(smf_plugins,
                                            csmModelExpansionPlugins):
    """
    This function add the model expansion plugin instances to the dictionary
    containing the SMF plugin instances. The csm model expansion instances
    are extensions to SMF plugin functionality and they need to be considerend
    when regular SMF plugins are considered
    """
    for uid in csmModelExpansionPlugins:
        if uid in smf_plugins:
            tcg_error("Error in plugin design for component: '%s'. "
                      "Only one plugin is allowed. "
                      "The component contains a CSM model extension plugin and a SMF plugin. "
                      "The former is a subclass of the later, so the SMF plugin "
                      "functionality has to be implemented in the CSM model extension." % uid)
        else:
            smf_plugins[uid] = csmModelExpansionPlugins[uid]


def extract_bundles(campaignGeneratorPlugins,
                    csmModelExpansionPlugins,
                    instantiation_campaign):
    """
    The bundles from the campaignGeneratorPlugins are only considered in the
    online flow. Instantiation campaigns should not consider campaign generator
    bundles. Bundles from CMS model expansion are always required.
    This is because the component implementing model expansion plugins (vDicos)
    can not deliver their models through MDF offline delivery and requires the
    instantiation campaign to deliver the models as it is done in the online
    flow.
    TODO: this method has to be refactored when we remove support for campaign
    generator plugins.
    """
    ret = []  # list of tuples (ctUid, sw, bundle)
    if not instantiation_campaign:
        for plugin in campaignGeneratorPlugins.itervalues():
            ret.extend(plugin.getSDPsInCampaign())

    for plugin in csmModelExpansionPlugins.itervalues():
        ret.extend(plugin.extendCampaignBundles())
    return ret


def add_model_delivery_modify_operations(smfCampaign,
                                         campaign_bundles,
                                         plugins,
                                         delivered_models):
    sdp_need_model_modify = build_model_modify_dict(campaign_bundles, plugins)

    for (bundleData, need_model_add) in sdp_need_model_modify.items():
        bundleSDP = bundleData[1]
        if need_model_add and bundleSDP not in delivered_models:
            bundleDn = AMFTools.getNodeSwBundleTemplateDnFromSDP(bundleSDP)
            if not smfCampaign.skip_generate_markup_tag(bundleDn):
                smfCampaign.beginCampInitAction()
                smfCampaign.generateDoCliCommand("cmw-model-modify", bundleSDP)
                smfCampaign.generateUndoCliCommand("/bin/true")
                smfCampaign.generatePlmExecEnv(Context.get().getControllerNode())
                smfCampaign.endCampInitAction()
                delivered_models.add(bundleSDP)
    return sdp_need_model_modify.keys()


def build_model_modify_dict(campaign_bundles, plugins):
    """
    It returns a dictionary of the form: key=(fileName, bundleName) value=bool
    for each of the pairs (fileName, bundleNane), it indicates if that software
    bundle requires MDF models deployment of not.
    When two or more components share the same bundle, if only one of them
    indicates the the models should NOT be deployed, then the models will not
    be deployed. That is, "not deploy" has precedence over "deploy" if two
    components indicate different information.
    """
    ret_dict = {}

    # info from the first plugin used to verify if another plugin tries to
    # change the value later.
    cts_plugin_info = {}

    for (compUid, sw, bundle) in campaign_bundles:
        the_key = (sw, bundle)
        if compUid not in plugins:
            # when there is no plugin the default is True
            if the_key not in ret_dict:
                ret_dict[the_key] = True
        else:
            plugin_info = plugins[compUid].deliverModels()
            if the_key not in ret_dict:
                # it is the first component containing this bundle
                ret_dict[the_key] = plugin_info
                cts_plugin_info[the_key] = plugin_info
            else:
                ret_dict[the_key] = ret_dict[the_key] and plugin_info
                if the_key in cts_plugin_info and \
                                cts_plugin_info[the_key] != plugin_info:
                    logging.warning("Two different plugins from components sharing the " \
                                    "software bundle %s are providing different information " \
                                    "for the MDF model delivery. Models will NOT be delivered." % bundle)
    return ret_dict


def add_model_delivery_done_operations(smfCampaign, campaign_bundles, plugins):
    need_cmw_model_done = get_need_cmw_model_done(campaign_bundles, plugins)
    if need_cmw_model_done:
        smfCampaign.beginCampInitAction()
        smfCampaign.generateDoCliCommand("cmw-model-done")
        smfCampaign.generateUndoCliCommand("/bin/true")
        smfCampaign.generatePlmExecEnv(Context.get().getControllerNode())
        smfCampaign.endCampInitAction()


def get_need_cmw_model_done(campaign_bundles, plugins):
    """
    returns a bool indicating if the campaign needs to call the cmw-model-done
    command. If the value is not provided by any plugin, the default is True.
    TCG will crash if two plugins provide different values
    """
    if len(campaign_bundles) == 0:
        # If there are no bundles there is nothing to deliver
        return False

    ret = None
    ct_init = None
    for (compUid, sw, bundle) in campaign_bundles:
        if compUid in plugins:
            the_value = plugins[compUid].finalizeModelDelivery()
            if the_value is not None:
                if ret is None:
                    ret = the_value
                    ct_init = compUid
                elif the_value != ret:
                    tcg_error("Components %s and %s in the same campaign are " \
                              "conflicting in cmw-model-done generation." % (ct_init, compUid))
    if ret is None:
        # No plugin defined the value before
        ret = True

    return ret


def get_component_actions(calculator):
    install_cts = set()
    upgrade_cts = set()
    remove_cts = set()
    nochange_cts = set()
    migrate_cts = set()
    referenceCTunit = DependencyCalculator.CT("dummy", "dummy", set(), [])
    for campaign in calculator.getCampaigns():
        for proc in campaign.getProcedures():
            for (node, entities) in proc.getResult().items():
                for entity in entities:
                    if type(entity) == type(referenceCTunit):
                        if entity.isToBeUpgraded():
                            upgrade_cts.add(entity.getName())
                        elif entity.isToBeRemoved():
                            remove_cts.add(entity.getName())
                        elif entity.is_to_be_deployed():
                            # Not upgrade, but need deploy, which means install
                            install_cts.add(entity.getName())
                            if entity.isToBeMigrated():
                                migrate_cts.add(entity.getName())
                        elif entity.isToBeMigrated():
                            # Not sure if we need it, keep this elif for get the
                            # same result as usual in migrate_cts set
                            migrate_cts.add(entity.getName())
    cts_in_base = SystemModels.baseCSMModel.system.getComponents() if SystemModels.baseCSMModel else []
    base_cts = set([c.getUid() for c in cts_in_base])
    affected_cts = install_cts.union(upgrade_cts, remove_cts)
    nochange_cts = base_cts.difference(affected_cts)
    return install_cts, upgrade_cts, remove_cts, nochange_cts, migrate_cts


def validate_comp_uid_supersedes(migration_info):
    for uid, supersedes in migration_info.items():
        gen_name = AMFTools.getCompBaseTypeDnFromUnit(uid)
        gen_name = gen_name[len('safCompType='):]
        for supersede in supersedes:
            for supersede_type, supersede_item in supersede.items():
                if (supersede_type == CgtConstants.COMPONENT_SUPERSEDES_BASE_COMPONENT_TAG and
                            gen_name == supersede_item):
                    tcg_error("Superseded component {0} has the same name with newly generated name.".format(gen_name))
