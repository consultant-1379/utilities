from common import printNice
from utils.logger_tcg import tcg_error
import CgtConstants

import logging
import AMFModel
import SDPTools
import ImmHelper
from csm_units import csm_unit
from tcg.plugin_api.SMFCsmModelExpansionPlugin import CSMModelExpansionPlugin

class _UNIT(object):
    CONSTRAINT_TYPE_NONE = 1
    CONSTRAINT_TYPE_DIFFERENT_PROCEDURE = 2
    CONSTRAINT_TYPE_DIFFERENT_CAMPAIGN = 3

    def __init__(self, name, version, nodes, install_scope, upgrade_scope):
        self._name = name
        self._version = version
        self._nodes = nodes
        self._isInstalled = set()
        self._to_be_deployed = set()
        self._to_be_upgraded = False
        self._force_upgrade = False
        self._to_be_removed = False
        self._is_movable = True
        self._install_scope = install_scope.lower()
        self._upgrade_scope = upgrade_scope.lower()
        self._csm_unit = None

    def getName(self):
        return self._name

    def getVersion(self):
        return self._version

    def isInstalled(self, nodes=None):
        if nodes is None:
            return self._isInstalled
        else:
            nodeset = set(nodes)
            return self._isInstalled.intersection(nodeset) == nodeset

    def installed(self, nodes):
        """
        to indicate that the unit is already installed in the base system
        """
        self._isInstalled = self._isInstalled.union(set(nodes))

    def is_to_be_deployed(self, nodes=None):
        if nodes is None:
            return self._to_be_deployed
        else:
            nodeset = set(nodes)
            return self._to_be_deployed.intersection(nodeset) == nodeset

    def to_be_deployed(self, nodes):
        """
        to indicate that the unit is going to be deployed (initial installation
        or upgrade) in the current campaign
        """
        self._to_be_deployed = self._to_be_deployed.union(set(nodes))

    def isToBeUpgraded(self):
        return self._to_be_upgraded

    def setToBeUpgraded(self):
        self._to_be_upgraded = True

    def isToBeRemoved(self):
        return self._to_be_removed

    def setToBeRemoved(self):
        self._to_be_removed = True

    def getNodes(self):
        return self._nodes

    def setNodes(self, nodes):
        if self._nodes != set() and self._nodes != nodes:
            tcg_error("%s: nodes are being set with different values %s %s %s." % (type(self), self.getName(), self._nodes, nodes))
        self._nodes = nodes

    def isMovable(self):
        return self._is_movable

    def setMovable(self, movable):
        self._is_movable = movable

    def set_csm_unit(self, csm_unit):
        self._csm_unit = csm_unit

    def get_csm_unit(self):
        return self._csm_unit

    def entity_needs_upgrade(self, otherunit):
       return False

class SV(_UNIT):
    def __init__(self, name, version, nodes=set(), install_scope=CgtConstants.SCOPE_SERVICE,
                 upgrade_scope=CgtConstants.SCOPE_COMPUTE_RESOURCE):
        super(SV, self).__init__(name, version, nodes, install_scope, upgrade_scope)
        self._usedSV = []
        self._cts = []
        self._plugin = None

    def toString(self):
        return "SV " + self._name +\
               " upgd: " + str(self._to_be_upgraded) +\
               " inst: " + str(self._isInstalled) + \
               " nodes: " + str(self._nodes) +\
               " id: " + str(id(self))

    def __str__(self):
        return self.toString()

    def __repr__(self):
        return '\n\t' + str(self) + '\n'

    def __hash__(self):
        myKey = self.getName()
        for node in sorted(list(self.getNodes())):
            myKey = myKey + node
        return hash(myKey)

    def __eq__(self, other):
        if other is None:
            return False
        if type(other) != SV:
            return False
        return self.getName() == other.getName() and self.getNodes() == other.getNodes()

    def __ne__(self, other):
        return not self.__eq__(other)

    def equal_except_nodes(self, other):
        '''Return True when two SV objects have
        same component UID.
        '''
        return type(self) == type(other) and \
            self.getName() == other.getName()

    def satisfies_dependency(self, unit):
        return self == unit

    def getPlugin(self):
        return self._plugin

    def setPlugin(self, plugin):
        self._plugin = plugin

    def dependsOn(self, other):
        for (sv, constr) in self._usedSV:
            if other == sv:
                return constr
        if other in self._cts:
            return self.CONSTRAINT_TYPE_NONE
        return None

    def getAllDeps(self):
        ret = list(self._usedSV)
        if self.isToBeUpgraded():
            # when the sv is upgraded it depends only on the component
            # instances being upgraded too. That is, the sv and its previously
            # existing cts will belong to the same campaign procedure. While it
            # is being upgraded, the sv does not need the new cts that are
            # going to be installed (the new cts can be installed in another
            # procedure later)
            for ct in self._cts:
                if ct.isToBeUpgraded():
                    ret.append((ct, SV.CONSTRAINT_TYPE_NONE))
        elif self.isToBeRemoved():
            return []
        else:
            # when the sv is installed, it depends on all the component
            # instances it will have. That is, the sv and its cts will belong
            # to the same campaign procedure
            ret = ret + [(elem, SV.CONSTRAINT_TYPE_NONE) for elem in self._cts]
        return ret

    def usesSV(self, sv, constraint):
        self._usedSV.append((sv, constraint))

    def addCT(self, ct):
        ct.setServiceCT()
        self._cts.append(ct)

    def get_scope(self):
        for ct in self._cts:
            if (ct.get_scope() == CgtConstants.SCOPE_COMPUTE_RESOURCE):
                return CgtConstants.SCOPE_COMPUTE_RESOURCE
        return CgtConstants.SCOPE_SERVICE

    def getCTs(self):
        return self._cts

    def addToProcedure(self, currentProcedure, currentCampaign, campaigns, nodes):
        if self.isInstalled(nodes):
            return

        if self._to_be_upgraded and currentProcedure.getType() == Procedure.PROCEDURE_TYPE_SINGLESTEP:
            return

        for (sv, constraint) in self._usedSV:
            if constraint != SV.CONSTRAINT_TYPE_NONE:
                if currentProcedure.isInstalled(sv.getName()):
                    return
            if constraint == SV.CONSTRAINT_TYPE_DIFFERENT_CAMPAIGN:
                for procedure in currentCampaign.getProcedures():
                    if procedure.isInstalled(sv.getName()):
                        return

        for node in self._nodes:
            for ct in self.getCTs():
                if not ct.isInstallable(node, currentProcedure, currentCampaign, campaigns):
                    return

        # for node in self._nodes:
        if self._nodes:
            currentProcedure.install(self, nodes)
        self.to_be_deployed(nodes)

    def isToBeMigrated(self):
        for ct in self.getCTs():
            if ct.isToBeMigrated():
                return True
        return False

    def entity_needs_upgrade(self, otherunit):

        csmunit = self.get_csm_unit()
        if csmunit and csmunit.is_upgrade():
            logging.debug("entity_needs_upgrade upgrade for SV %s (component %s, %s)", self.getName(), csmunit.getUid(), csmunit.getName())
            return True

        return False

    def is_present_in_config(self, reference_pool, target_config):
        target_pool = target_config.findPool(reference_pool.getName())
        if target_pool:
            for other_sv in target_pool.getSVs().values():
                if other_sv == self:
                    return True
        return False

class CT(_UNIT):
    def __init__(self,
                 name,
                 instance_name,
                 version,
                 nodes=set(),
                 sw_bundle_names=set(),
                 install_scope=CgtConstants.SCOPE_SERVICE,
                 upgrade_scope=CgtConstants.SCOPE_COMPUTE_RESOURCE,
                 upgrade_migration_scope=CgtConstants.SCOPE_SERVICE,
                 install_need_reboot=False,
                 upgrade_need_reboot=False):
        super(CT, self).__init__(name, version, nodes, install_scope, upgrade_scope)
        self._instance_name = instance_name
        self._usedCT = []
        self._sw_bundle_names = sw_bundle_names
        self._to_be_migrated = False
        self._sw_to_be_upgraded = False
        self._serviceCT = False
        self._upgrade_migration_scope = upgrade_migration_scope.lower()
        self._install_need_reboot = install_need_reboot
        self._upgrade_need_reboot = upgrade_need_reboot
        self._SV = None
        self._plugin = None
        self._existing_type = False
        self._sv_csm_unit = None
        assert (not self._install_need_reboot) or self._install_scope == CgtConstants.SCOPE_COMPUTE_RESOURCE, "Invalid scope for reboot, reboot always requires node level scope"

    def toString(self):
        return "CT " + \
               self._name + "(" + str(self._instance_name) + ") " +\
               " upgd: " + str(self._to_be_upgraded) +\
               " inst: " + str(self._isInstalled) +\
               " version: " + str(self._version) +\
               " nodes: " + str(self._nodes) +\
               " id: " + str(id(self))

    def __str__(self):
        return self.toString()

    def __repr__(self):
        return '\n\t' + str(self) + '\n'

    def satisfies_dependency(self, unit):
        if (type(unit) != CT):
            return False
        else:
            return self.getName() == unit.getName() and \
                   self.getNodes() == unit.getNodes()

    def __eq__(self, other):
        if other is None:
            return False
        if type(other) != CT:
            return False

        return self.getName() == other.getName() and \
               self.getInstanceName() == other.getInstanceName() and \
               self.getNodes() == other.getNodes() and \
               self.getSV() == other.getSV()


    def equal_except_nodes(self, other):
        '''Return True when two CT objects have
        same component UID and component instance name.
        '''
        return type(self) == type(other) and \
            self.getName() == other.getName() and \
            self.getInstanceName() == other.getInstanceName()

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        myKey = self.getName() + str(self.getInstanceName())
        for node in sorted(list(self.getNodes())):
            myKey = myKey + node
        myKey = myKey + str(hash(self._SV))
        return hash(myKey)

    def addSV(self, sv):
        if self._SV is not None:
            tcg_error("A component instance can only have one associated service")
        self._SV = sv

    def getSV(self):
        return self._SV

    def getPlugin(self):
        return self._plugin

    def setPlugin(self, plugin):
        self._plugin = plugin

    def set_existing_type(self, exist):
        """
        Used to indicate if the component type associated to this component
        instance already exists in the base system.
        Note that _to_be_upgraded or _isInstalled cannot be used because that
        condition refers to the particular component instance. For one ct type
        there could be instances being updated and created at the same time
        """
        self._existing_type = exist

    def is_existing_type(self):
        return self._existing_type

    def dependsOn(self, other):
        for (ct, constr) in self._usedCT:
            if other == ct:
                return constr
        return None

    def getAllDeps(self):
        if self.isToBeRemoved():
            return []
        else:
            dep = list(self._usedCT)
            if (self._SV is not None):
                dep.append((self._SV, self.CONSTRAINT_TYPE_NONE))
            return dep

    def setSwToBeUpgraded(self):
        self._sw_to_be_upgraded = True

    def setToBeMigrated(self):
        self._to_be_migrated = True

    def isToBeMigrated(self):
        return self._to_be_migrated

    def isSwToBeUpgraded(self):
        return self._sw_to_be_upgraded

    def getName(self):
        return self._name

    def getInstanceName(self):
        return self._instance_name

    def getSwBundleNames(self):
        return self._sw_bundle_names

    def usesCT(self, ct, constraint):
        self._usedCT.append((ct, constraint))

    def getUsedCT(self):
        return self._usedCT

    def setServiceCT(self):
        self._serviceCT = True

    def getServiceCT(self):
        return self._serviceCT

    def getUpgradeMigrationScope(self):
        return self._upgrade_migration_scope

    def setUpgradeMigrationScope(self, scope):
        self._upgrade_migration_scope = scope

    def isRebootNeeded(self):
        if self._existing_type or self.isToBeMigrated():
            return self._upgrade_need_reboot
        else:
            #TODO: support uninstallation constraint
            return self._install_need_reboot

    def get_scope(self):
        if self._existing_type:
                return self._upgrade_scope
        else:
            if self.isToBeMigrated():
                return self._upgrade_migration_scope
            else:
                return self._install_scope

    def set_sv_csm_unit(self, csm_unit):
        self._sv_csm_unit = csm_unit

    def get_sv_csm_unit(self):
        return self._sv_csm_unit


    def isInstallable(self, node, currentProcedure, currentCampaign, campaigns):
        for (usedCT, constraint) in self.getUsedCT():
            # print "CT %s uses %s with constraint type %s" % (self.getName(), usedCT.getName(), constraint)
            if constraint == CT.CONSTRAINT_TYPE_NONE and node not in usedCT.getNodes():
                tcg_error("CT %s is to be installed on %s, but its dependency %s is not." % (
                self.getName(), node, usedCT.getName()))
                return False
            if constraint != CT.CONSTRAINT_TYPE_NONE:
                if currentProcedure.isInstalled(usedCT.getName(), node):
                    tcg_error("CT %s depends on %s, but its constraints does not allow installing it" % (
                    self.getName(), usedCT.getName()))
                    return False
            if constraint == CT.CONSTRAINT_TYPE_DIFFERENT_CAMPAIGN:
                for procedure in currentCampaign.getProcedures():
                    if procedure.isInstalled(usedCT.getName(), node):
                        tcg_error("CT %s depends on %s, but its constraints does not allow installing it" % (
                        self.getName(), usedCT.getName()))
                        return False
        return True

    def addToProcedure(self, currentProcedure, currentCampaign, campaigns, nodes):
        if self._to_be_upgraded and currentProcedure.getType() == Procedure.PROCEDURE_TYPE_SINGLESTEP:
            return

        if self.isInstalled(nodes):
            return

        need_to_install = False
        for node in self._nodes:
            if not self.isInstallable(node, currentProcedure, currentCampaign, campaigns):
                return
            else:
                need_to_install = True

        if need_to_install:
            currentProcedure.install(self, nodes)

        self.to_be_deployed(nodes)


    def entity_needs_upgrade(self, otherct):
        """
        check the component instance to see if an updgrade is needed
        """

        # an upgrade in the component type automatically means upgrade in the component instance
        csmunit = self.get_csm_unit()
        if csmunit and csmunit.is_upgrade():
            logging.debug("entity_needs_upgrade upgrade for CT %s (component %s, %s)", self.getName(), csmunit.getUid(), csmunit.getName())
            return True

        # check also the compenent's service to has been an attribute upgrade which causes update in a component instance
        if self._SV:
            svcsmunit = self._SV.get_csm_unit()
            if svcsmunit and svcsmunit.comp_inst_is_upgraded(self._instance_name):
                logging.debug("entity_needs_upgrade upgrade found for component instance CT %s in SV %s)", self._instance_name, svcsmunit.getName())
                return True

        # legacy calc for CT upgrade needed until the Dependency Calculator interface is in place...to be taken away
        # to be removed
        if self.getVersion() != otherct.getVersion():
            logging.debug("entity_needs_upgrade upgrade version diff for CT: %s %s %s", self.getName(), self.getInstanceName(), self.getNodes())
            return True

        return False

    def is_present_in_config(self, reference_pool, target_config):
        target_pool = target_config.findPool(reference_pool.getName())
        if target_pool:
            for sv in target_pool.getSVs().values():
                if self.getSV() == sv:
                    for ct in sv.getCTs():
                        if ct == self:
                            return True
            for ct in target_pool.getCTs():
                if ct == self:
                    return True
        return False


class Pool(object):
    def __init__(self, name, nodes):
        self._name = name
        self._svs = {}
        self._cts = []
        self._nodes = nodes

    def getName(self):
        return self._name

    def addSV(self, sv):
        self._svs[sv.getName()] = sv

    def addCT(self, ct):
        if ct not in self._cts:
            self._cts.append(ct)

    def getSVs(self):
        return self._svs

    def getCTs(self):
        return self._cts

    def getNodes(self):
        return self._nodes


class Campaign(object):
    def __init__(self, index):
        self._procedures = []
        self._index = index

    def addProcedure(self, procedure):
        self._procedures.append(procedure)

    def isEmpty(self):
        return len(self._procedures) == 0

    def getProcedures(self):
        return self._procedures

    def getComponentTypes(self):
        """
        returns the set of the uids of the components types that have at least
        one instance in at least one procedure of this campaign.
        """
        ret = set()
        for proc in self._procedures:
            ret.update(proc.getComponentTypes())
        return ret

    def dump(self):
        print "Campaign " + str(self._index)
        for p in self._procedures:
            p.dump()

    def getIndex(self):
        return self._index


class Procedure(object):
    PROCEDURE_TYPE_SINGLESTEP = "SingleStep"
    PROCEDURE_TYPE_ROLLING = "Rolling"

    def __init__(self, index, type):
        self._result = {}
        self._empty = True
        self._index = index
        self._type = type
        self._changed = False
        self._negative = False

    def install(self, entity, nodes):
        self._empty = False
        if nodes == Procedure.PROCEDURE_TYPE_SINGLESTEP:
            for node in entity.getNodes():
                if node not in self._result:
                    self._result[node] = set()
                self._result[node].add(entity)
        else:
            for node in nodes:
                if node not in self._result:
                    self._result[node] = set()
                self._result[node].add(entity)
        self._changed = True

    def isInstalled(self, entity, node=None):
        if node == None:
            for entities in self._result.values():
                if entity in entities:
                    return True
            return False
        if node not in self._result:
            return False
        return entity in self._result[node]

    def isUpgrade(self):
        return self._type == Procedure.PROCEDURE_TYPE_ROLLING

    def isEmpty(self):
        return self._empty

    def changed(self):
        return self._changed

    def resetChanged(self):
        self._changed = False

    def getType(self):
        return self._type

    def getNodes(self):
        return sorted(self._result.keys())

    def dump(self):
        print "Procedure " + str(self._index) + " type: " + self._type
        for (node, entities) in self._result.items():
            print "Node: " + node + ", entities: " + str(entities)

    def getIndex(self):
        return self._index

    def getResult(self):
        return self._result

    def getComponentTypes(self):
        """
        returns the set of uids of the components types that have at least one
        instance in this procedure
        """
        ret = set()
        for entities in self._result.itervalues():
            for entity in entities:
                if type(entity) == CT:
                    ret.add(entity.getName())
        return ret

    def getCTs(self):
        ret = {}
        for entities in self._result.itervalues():
            for entity in entities:
                if type(entity) == CT:
                    ret[entity.getName()] = entity
        return ret


class Calculator(object):
    def __init__(self, isUpgrade, inverseCalc=False):
        self._pools = {}
        self._campaigns = []
        self._procIndex = 0
        self._currentCampaign = None
        self._isUpgrade = isUpgrade
        self._inverseCalc = inverseCalc

    def addPool(self, pool):
        self._pools[pool.getName()] = pool

    def validate_everything_processed(self):
        for pool in self._pools.values():
            for ct in pool.getCTs():
                if not ct.isInstalled() and not ct.is_to_be_deployed() and not (ct.isToBeUpgraded()):
                     tcg_error("CT %s is not installed nor deployed" % ct.getName())
            for sv in pool.getSVs().values():
                if not sv.isInstalled() and not sv.is_to_be_deployed() and not (sv.isToBeUpgraded()):
                    tcg_error("SV %s is not installed nor deployed" % sv.getName())

    def composeProcedure(self, units, procType, nodes):
        currentProcedure = Procedure(self._procIndex, procType)
        self._procIndex = self._procIndex + 1
        for unit in units:
            unit.addToProcedure(currentProcedure, self._currentCampaign, self._campaigns, nodes)
        self._currentCampaign.addProcedure(currentProcedure)

    def nextCampaign(self):
        if self._currentCampaign != None:
            self._campaigns.append(self._currentCampaign)
        self._currentCampaign = Campaign(len(self._campaigns))

    def processCT(self, targetct, targetsv, targetPool, sourceConfig, fullBaseCTMap, proc0):
        # print "processing CT " + targetct.getName() + " from pool " + targetPool.getName()
        for pool in sourceConfig.getPools():
            if pool.getName() != targetPool.getName():
                continue
            ctList = list(pool.getCTs())
            for sv in pool.getSVs().values():
                ctList.extend(sv.getCTs())
            for ct in ctList:
                if ct == targetct:
                    if (targetsv == None or targetsv == ct.getSV()):
                        # check if there is any new nodes in the current ct and leave only those
                        # the CT is already installed
                        if not targetct.entity_needs_upgrade(ct):
                            #print "CT " + targetct.getName() + " is already installed on nodes", pool.getNodes()
                            diff = ((list(set(targetct.getNodes()) - fullBaseCTMap[targetct])))
                            # print "diff is", diff
                            if not diff:
                                proc0.install(targetct, tuple(pool.getNodes()))
                                targetct.installed(pool.getNodes())
                            else:
                                tcg_error("Pool of CT " + targetct.getName() + " in SV " + (
                                'None' if targetsv is None else targetsv.getName()) + " changed")
                                # the CT will not be upgraded, add it to proc0 and mark it as installed
                        else:
                            # print "CT " + targetct.getName() + " will be upgraded from " + ct.getVersion() + " to " + targetct.getVersion()
                            # the CT will be upgraded, do not add it to proc0
                            targetct.setToBeUpgraded()
                            if ct.getSwBundleNames() ^ targetct.getSwBundleNames():
                                targetct.setSwToBeUpgraded()
                        if pool.getNodes() != targetPool.getNodes():
                            tcg_error("Pool of CT " + targetct.getName() + " in SV " + (
                            'None' if targetsv is None else targetsv.getName()) + " changed")
                        return
                    else:
                        diff = ((list(set(targetct.getNodes()) - fullBaseCTMap[targetct])))
                        if not diff:
                            proc0.install(targetct, tuple(pool.getNodes()))
                            targetct.installed(pool.getNodes())
                        else:
                            targetct.setNodes(diff)
            break
            # print "CT " + targetct.getName() + " is newly added"

    def processSV(self, targetsv, targetPool, sourceConfig, fullBaseCTMap, proc0):
        for pool in sourceConfig.getPools():
            if pool.getName() != targetPool.getName():
                continue


            svlist =  pool.getSVs().values()
            for sv in svlist:
                if sv == targetsv:
                    # check if there is any new nodes for the current sv
                    # the SV is already installed on this node set
                    if targetsv.entity_needs_upgrade(None):
                        targetsv.setToBeUpgraded()
                    else:
                        targetsv.installed(pool.getNodes())
                    return
            break

    def calculate_partition(self, sourceConfig, targetConfig):
        (partitioning, success, mergeResult) = self.partitionInstall(sourceConfig, targetConfig)
        if success:
            # print "success! We can install! The final partitioning:"
            # Compose procedures
            for campaign in partitioning:
                self.nextCampaign()
                # print "{campaign"
                for (nodes, (procedure, procType)) in campaign:
                    # print "nodes:", nodes
                    # print "\t["
                    # for unit in procedure:
                    # print unit.getName(),
                    # print "\n\t], "
                    self.composeProcedure(procedure, procType, nodes)
                    # print "\n}/campaign, "
            self.nextCampaign()
        else:
            # Something went wrong during partitioning
            print "There is a cycle containing a constrained dependency in the following units:"
            for units in partitioning.values():
                for u in units:
                    print u.getName(), [(d[0].getName(), d[1]) for d in u.getAllDeps()]
            tcg_error("Could not calculate install/upgrade order due to cyclic dependencies")
        self.validate_everything_processed()
        return mergeResult

    def install(self, sourceConfig, targetConfig, comp_types_to_be_migrated):
        campaign0 = Campaign(0)
        proc0 = Procedure(0, Procedure.PROCEDURE_TYPE_SINGLESTEP)
        campaign0.addProcedure(proc0)
        # full list of installed cts
        fullBaseCTMap = {}
        for pool in sourceConfig.getPools():
            for sv in pool.getSVs().values():
                for ct in sv.getCTs():
                    if ct not in fullBaseCTMap:
                        fullBaseCTMap[ct] = set(pool.getNodes())
                    else:
                        fullBaseCTMap[ct].update(set(pool.getNodes()))
            for ct in pool.getCTs():
                if ct not in fullBaseCTMap:
                    fullBaseCTMap[ct] = set(pool.getNodes())
                else:
                    fullBaseCTMap[ct].update(set(pool.getNodes()))
        self._campaigns.append(campaign0)
        # first process the CTs from the source config to mark the non upgraded and upgraded CTs
        for targetPool in targetConfig.getPools():
            for ct in targetPool.getCTs():
                self.processCT(ct, None, targetPool, sourceConfig, fullBaseCTMap, proc0)
                if (not ct.isToBeUpgraded() and not ct.is_existing_type() and ct.getName() in comp_types_to_be_migrated):
                    ct.setToBeMigrated()
            for sv in targetPool.getSVs().values():
                self.processSV(sv, targetPool, sourceConfig, fullBaseCTMap, proc0)
                for ct in sv.getCTs():
                    self.processCT(ct, sv, targetPool, sourceConfig, fullBaseCTMap, proc0)
                    if (not ct.isToBeUpgraded() and not ct.is_existing_type() and ct.getName() in comp_types_to_be_migrated):
                        ct.setToBeMigrated()
            self.addPool(targetPool)

        self._detect_svs_cts_to_remove(sourceConfig, targetConfig)
        # then do the same with the SVs (SV is upgraded if at least one CT it contains is upgraded)
        for targetPool in targetConfig.getPools():
            for targetsv in targetPool.getSVs().values():
                for pool in sourceConfig.getPools():

                    for sv in pool.getSVs().values():
                        if sv == targetsv:
                            for ct in targetsv.getCTs():
                                if ct.isToBeUpgraded():
                                    # TODO: recheck later if ct.isToBeRemoved() is needed
                                    # force the service to be marked as upgraded
                                    if not targetsv.isToBeUpgraded():
                                        #print "SV " + targetsv.getName() + " will be upgraded"
                                        targetsv.setToBeUpgraded()
                                        break
                            if not (targetsv.isToBeUpgraded() or targetsv.isToBeRemoved()):
                                # print "SV " + targetsv.getName() + " is already installed"
                                targetsv.installed(targetPool.getNodes())

    def _detect_svs_cts_to_remove(self, sourceConfig, targetConfig):
        """
        This method looks for CTs in the target configuration that are not
        present in the source configuration, i.e. CTs that were removed.
        When this method finds removed CTs, it marks them as "removed" and
        introduces them in the target configuration.
        """
        for src_pool in sourceConfig.getPools():
            svs_to_check = [sv for sv in src_pool.getSVs().values()]
            for sv in svs_to_check:
                if not sv.is_present_in_config(src_pool, targetConfig):
                    sv.setToBeRemoved()
                    self._add_removed_sv(sv, src_pool, targetConfig)
                else:
                    for ct in sv.getCTs():
                        if not ct.is_present_in_config(src_pool, targetConfig):
                            ct.setToBeRemoved()
                            self._add_removed_ct(ct, sv, src_pool, targetConfig)
            cts_to_check = [ct for ct in src_pool.getCTs()]
            for ct in cts_to_check:
                if not ct.is_present_in_config(src_pool, targetConfig):
                    ct.setToBeRemoved()
                    self._add_removed_ct(ct, None, src_pool, targetConfig)

    def _add_removed_sv(self, sv, reference_pool, config):
        """
        @param sv: service to be added to target configration
        @param reference_pool: referenced pool from the base to figure out the target pull in the target configuration
        @param config: target configuration
        @return: None

        This fucntion add the sv to the same pool on the target configuration
        """
        target_pool = config.findPool(reference_pool.getName())
        if not(target_pool):
            target_pool = Pool(reference_pool.getName(), reference_pool.getNodes())
            config.addPool(target_pool)
        target_pool.addSV(sv)
        for ct in sv.getCTs():
            ct.setToBeRemoved()

    def _add_removed_ct(self, ct, reference_sv, reference_pool, config):
        """
        @param ct: ct to be added to target configration
        @param reference_sv: referenced service
        @param reference_pool: referenced pool from the base to figure out the target pull in the target configuration
        @param config: target configuration
        @return: None

        This fucntion add the ct to the target service in to a pool in the target configuration with the same name with
        the referenced pool
        Not found pool is considered as error since we does not support Role removal
        """
        target_pool = config.findPool(reference_pool.getName())
        assert(target_pool)
        if reference_sv:
            for sv in target_pool.getSVs().values():
                if sv == reference_sv:
                    sv.addCT(ct)
                    break
            else:
                tcg_error("Could not find the reference_sv %s in target configuration" % (sv.getName()))
        else:
            target_pool.addCT(ct)


    def getCampaigns(self):
        return self._campaigns

    def partitionInstall(self, sourceConfig, targetConfig):
        success = True
        partitions = []
        prev = PrevStruct()

        # building the list of units already installed
        for pool in sourceConfig.getPools():
            nodez = tuple(pool.getNodes())
            prev.add(nodez,
                     pool.getCTs() + pool.getSVs().values() + [c for s in pool.getSVs().values() for c in s.getCTs()])

        # but remove the ones that are upgraded because other upgraded software may depend on the changes
        for pool in targetConfig.getPools():
            for ct in pool.getCTs():
                if ct.isToBeUpgraded() or ct.isToBeRemoved():
                    prev.remove(pool.getNodes(), ct)
            for sv in pool.getSVs().values():
                if sv.isToBeUpgraded() or sv.isToBeRemoved():
                    prev.remove(pool.getNodes(), sv)
                for ct in sv.getCTs():
                    if ct.isToBeUpgraded() or ct.isToBeRemoved():
                        prev.remove(pool.getNodes(), ct)

        # building the initial leftover map
        leftover = {Procedure.PROCEDURE_TYPE_SINGLESTEP: []}
        mergeResult = False
        for pool in targetConfig.getPools():
            # We now need to check if there are any toBeInstalled unit that scope on COMPUTE-RESOURCE level and
            # move them into the ROLLING_UPGRADE procedure to avoid service outage.
            # But for the migration case, those unit could not be moved to ROLLING_UPGRADE since migration need
            # to be tied to the SINGLE_STEP procedure.
            # We can basically check if the unit will be migrated first before moving it to the ROLLING_UPGRADE.
            # But there is also cases where the migrated unit depends on other units, which will be moved
            # to the ROLLING_UPGRADE then we will make the campaign failed.
            # The same things happen with the units which depend on the toBeMigrated one, those units also could not
            # be moved to ROLLING_UPGRADE as well (because if they're moved, since they depend on the migrated unit,
            # this unit will also need to be moved to protect the dependencies which will break the migration campaign)
            # So for a chain of dependency, if there is one element of the chain is marked as not_movable, it will make
            # the whole chain is not movable.
            # An item can only be marked as movable if the unit itself is not migrated and all of its dependencies
            # as well as all the units depend on it is also movable.
            # To avoid the case that we move a unit to ROLLING_UPGRADE but need to move it back (leading to moving all
            # of its dependencies/dependents as well) later, we need to go through the whole list and calculate the
            # moving strategy first.

            # At starting point, all units will be marked as movable
            unitslist = set(pool.getCTs() + pool.getSVs().values() + [c for s in pool.getSVs().values() for c in s.getCTs()])
            movable = unitslist.copy()
            stop = False
            while not stop:
                stop = True
                remlist = set()
                for unit in movable:
                    if unit.isToBeMigrated():
                        # If unit isToBeMigrated, mark it as not_movable
                        unit.setMovable(False)
                        remlist.add(unit)
                        for (depunit, _) in unit.getAllDeps():
                            # Mark all units that this one depended on as not_movable as well
                            depunit.setMovable(False)
                        stop = False
                    elif not unit.isMovable():
                        # Unit has just been set as non_movable by previous unit in the same
                        # run or by later unit in previous run
                        remlist.add(unit)
                        for (depunit, _) in unit.getAllDeps():
                            # Also mark its dependencies as non_movable
                            depunit.setMovable(False)
                        stop = False
                    else:
                        # Unit has not been touched before, but we also need to check for its
                        # dependencies since there is a chance that those dependencies have
                        # been marked as non_movable
                        for (depunit, _) in unit.getAllDeps():
                            if not depunit.isMovable():
                                unit.setMovable(False)
                                remlist.add(unit)
                                stop = False
                                break

                movable -= remlist

            for unit in unitslist:
                if unit.getNodes():
                    # if something is upgraded put it in rolling steps
                    if unit.isToBeUpgraded():
                        if tuple(unit.getNodes()) in leftover:
                            leftover[tuple(unit.getNodes())].append(unit)
                        else:
                            leftover[tuple(unit.getNodes())] = [unit]
                    # if something is being installed and we have a pure
                    # installation without upgrade we just put everything
                    # in singlestep
                    elif not unit.isInstalled() and not self._isUpgrade:
                        # print "EBALZFE", unit.getName(), unit._isInstalled
                        leftover[Procedure.PROCEDURE_TYPE_SINGLESTEP].append(unit)
                    # if we have upgrade and something is installed and it is
                    # scoped on node group level then put it in rolling steps
                    # to avoid complete service outage.
                    elif not unit.isInstalled() and unit.isMovable() and self._isUpgrade and unit.get_scope() == CgtConstants.SCOPE_COMPUTE_RESOURCE:
                        #logging.debug("partitionInstall SCOPE_COMPUTE_RESOURCE is working on: %s, %s ", unit.getName(), unit.getNodes())
                        if tuple(unit.getNodes()) in leftover:
                            leftover[tuple(unit.getNodes())].append(unit)
                        else:
                            leftover[tuple(unit.getNodes())] = [unit]
                    elif unit.isToBeRemoved() or not unit.isInstalled():
                        leftover[Procedure.PROCEDURE_TYPE_SINGLESTEP].append(unit)

        # check to see if units A are going to leftover[tuple(unit.getNodes())] (TYPE_ROLLING) while
        # other units B - that depend on the units A are going to leftover[Procedure.PROCEDURE_TYPE_SINGLESTEP]
        # this causes an error in the creation procedures down the road where the system installs SINGLE_STEP
        # before ROLLING causing in upgrade failure
        # This happens when unit B will be installed but scoped on COMPUTE-RESOURCE level, but unit A which depends on
        # B is only scoped on SERVICE-UNIT level. If this happen then also move A to ROLLING_UPGRADE procedure.
        # NOTE: this will not break the dependency because B is "movable", which means A is also "movable"
        check_single_step_dependencies(leftover, prev)

        # Another check to see if there are any unit C left in SINGLE_STEP which has its dependents is moved to ROLLING
        # This happens when unit A which is at ROLLING and depends on unit C - scoped on SERVICE-UNIT.
        # Again, moving C to ROLLING won't break the dependencies since both A and C are "movable".
        check_rolling_step_dependencies(leftover)

        # as an optimization, if the singlestep procedure would only contain cts that are not associated with svs, and we are upgrading, dont generate singlestep.
        ## This way the campaign might be site independent.
        # first check if the optimization step can be done:
        containsService = False
        svType = type(SV("", "", []))
        for tunit in leftover[Procedure.PROCEDURE_TYPE_SINGLESTEP]:
            if (type(tunit) == svType) or tunit.getServiceCT():
                containsService = True
                break

        # if it is possible to optimize, move units to to other nodesets:
        if not containsService and self._isUpgrade:
            for tunit in leftover[Procedure.PROCEDURE_TYPE_SINGLESTEP][:]:
                if tunit.isMovable():
                    if tuple(tunit.getNodes()) in leftover:
                        leftover[tuple(tunit.getNodes())].append(tunit)
                    else:
                        leftover[tuple(tunit.getNodes())] = [tunit]
                    leftover[Procedure.PROCEDURE_TYPE_SINGLESTEP].remove(tunit)

        # finally delete the singlestep part if it is no longer necessary:
        if (leftover[Procedure.PROCEDURE_TYPE_SINGLESTEP] == []):
            del leftover[Procedure.PROCEDURE_TYPE_SINGLESTEP]
            # and try to optimize further, by merging procedures if it is possible to achieve a single rolling over all the nodes.
            # print "EBALZFE, calling mergebizbasz leftover is", leftover
            (leftover, mergeResult) = mergeRollingNodeSets(leftover)
            # print "EBALZFE, after mergebizbasz leftover keys are", leftover.keys()

        # partitioning until we are stuck or finished.
        part = ["dummy"]
        # print "EBALZFE wut", leftover, part
        while leftover and part[0]:
            # print "calling calcPartitions with leftovers:"
            # for (key, value) in leftover.items():
            # print key, ":\n\t",
            # for unit in value:
            # print "\t", unit.getName(),
            # print
            (part, nodes, leftover) = calcPartition(leftover, prev, strategy=CgtConstants.GROUPED_CT_DEPENDENCIES)
            if not part[0]:
                (part, nodes, leftover) = calcPartition(leftover, prev, strategy=CgtConstants.INDIVIDUAL_CT_DEPENDENCIES)
                if not part[0]:
                    break
            partitions.append((nodes, list(part[0]), part[1]))
            # TODO: fix string later
            prev.add(nodes, [unit for unit in part[0] if not unit.isToBeRemoved()])

        if leftover:
            # means that 'part' was empty, but some units are still left over. Return the problematic units and let the caller deal with it.
            # print "\nleftover not empty", leftover
            partitions = leftover
            success = False
        else:
            # so far partitions is the list of procedures, now determine the procedure types.
            # finally, determine which of these procedures can be in the same campaign.
            partitions = groupCampaings(partitions)

        return (partitions, success, mergeResult)

def check_single_step_dependencies(unitlist, prev):
    '''
    It can happen that units are placed into 'unitlist[Procedure.PROCEDURE_TYPE_SINGLESTEP]'
    that have dependencies that are in a PROCEDURE_TYPE_ROLLING list - causing a failure in dependency
    This function will remove from  'unitlist[Procedure.PROCEDURE_TYPE_SINGLESTEP]'
    any unit with a dependent unit elsewhere, and all of its associated units to a PROCEDURE_TYPE_ROLLING list.
    '''
    unitlistunits = unitlist[Procedure.PROCEDURE_TYPE_SINGLESTEP]
    dependencies_set = set()

    for (unit) in unitlistunits:
        for (depunit, constr) in unit.getAllDeps():
            #logging.debug("\n>>> dependency found from to constr: %s, %s, %s, %s, %s", unit.getName(), unit.getNodes(), depunit.getName(),depunit.getNodes(), constr)
            # a dependency to another object exists, so check to make sure that this obect is
            # ALSO in unitlist[Procedure.PROCEDURE_TYPE_SINGLESTEP]
            if  depunit not in unitlistunits and not prev.satisfies_dependency(depunit):
                # the object to which the present unit depends on IS NOT in unitlist[Procedure.PROCEDURE_TYPE_SINGLESTEP]
                # so we transfer save the present unit and all of its dependencies of type CONSTRAINT_TYPE_NONE
                dependencies_set.add(unit)
                for (depunit1, constr) in unit.getAllDeps():
                    if (depunit1 in unitlistunits):
                        dependencies_set.add(depunit1)

    if not len(dependencies_set):
        return

    # the saved units from unitlist[Procedure.PROCEDURE_TYPE_SINGLESTEP]
    # to the correct list within 'unitlist' according to the unit's nodes
    for unit in dependencies_set:
        # logging.debug("\n>>> check_single_step_dependendies moving to rolling %s, %s ", unit.getName(), unit.getNodes())
        unitlist[Procedure.PROCEDURE_TYPE_SINGLESTEP].remove(unit)
        if tuple(unit.getNodes()) in unitlist:
            unitlist[tuple(unit.getNodes())].append(unit)
        else:
            unitlist[tuple(unit.getNodes())] = [unit]

    check_single_step_dependencies(unitlist, prev)


def check_rolling_step_dependencies(unitlist):
    '''
    It can happen that units are placed into rolling upgrade that have componets on which they depend in
    in single step ('unitlist[Procedure.PROCEDURE_TYPE_SINGLESTEP]') causing a failure in an upgrade.
    This function will remove from  'unitlist[Procedure.PROCEDURE_TYPE_SINGLESTEP]'
    any such unit on which another unit is dependent, and all of its associated units to a PROCEDURE_TYPE_ROLLING list.
    '''
    dependencies_set = set()
    for nodes, unitlistunits in unitlist.items():
        if (unitlistunits == unitlist[Procedure.PROCEDURE_TYPE_SINGLESTEP]):
            continue
        for (unit) in unitlistunits:
            # logging.debug("check_rolling_step_dependencies is working on: %s, %s ", unit.getName(), unit.getNodes())
            # First we findout if this unit is dependent on anything
            for (depunit, constr) in unit.getAllDeps():
                # logging.debug("\n>>> check_rolling_step_dependencies dependency found from to constr: %s, %s, %s, %s, %s", unit.getName(), unit.getNodes(), depunit.getName(),depunit.getNodes(), constr)
                # a dependency to another object exists, so check to make sure that this obect is
                # NOT in unitlist[Procedure.PROCEDURE_TYPE_SINGLESTEP]
                if depunit in unitlist[Procedure.PROCEDURE_TYPE_SINGLESTEP]:
                    # the object to which the present unit depends on IS in unitlist[Procedure.PROCEDURE_TYPE_SINGLESTEP]
                    # so we transfer it and all of its dependencies of type CONSTRAINT_TYPE_NONE
                    dependencies_set.add(depunit)
                    # logging.debug("\n>>> check_rolling_step_dependencies dependency found in PROCEDURE_TYPE_SINGLESTEP %s, %s, %s", unit.getName(), depunit.getName(), constr)
                    for (depunit1, constr) in depunit.getAllDeps():
                        if (constr == depunit.CONSTRAINT_TYPE_NONE and depunit1 in unitlist[
                            Procedure.PROCEDURE_TYPE_SINGLESTEP]):
                            dependencies_set.add(depunit1)
                            # logging.debug("\n>>> check_rolling_step_dependencies dependency of type _NONE_ found in PROCEDURE_TYPE_SINGLESTEP %s, %s, %s", depunit.getName(), depunit1.getName(), constr)

    # the saved units from unitlist[Procedure.PROCEDURE_TYPE_SINGLESTEP]
    # to the correct list within 'unitlist' according to the unit's nodes
    for unit in dependencies_set:
        # logging.debug("\n>>> check_rolling_step_dependencies moving to rolling %s, %s ", unit.getName(), unit.getNodes())
        unitlist[Procedure.PROCEDURE_TYPE_SINGLESTEP].remove(unit)
        if tuple(unit.getNodes()) in unitlist:
            unitlist[tuple(unit.getNodes())].append(unit)
        else:
            unitlist[tuple(unit.getNodes())] = [unit]


def satisfies_dependency_in_leftover(leftover, unit):
    '''Return True if unit(SV or CT) is not existed in leftover.
    This detect will ignore node allocation. It will return
    False when unit is existed in leftover even it is allocated
    on different nodes.
    '''
    for item in [i for l in leftover.values() for i in l]:
        if item.equal_except_nodes(unit):
            return False
    return True


def calcPartition(leftover, prev, strategy=CgtConstants.INDIVIDUAL_CT_DEPENDENCIES):
    part = []
    procType = None  # if it is not set later, that is a bug
    # print "adssssssssss", sorted(leftover.items(), key=compareByNodeNumber)
    for (nodes, units) in sorted(leftover.items(), key=compareByNodeNumber):
        # print "calcPartition is working on: ", nodes, units
        part = list(units)
        lftUnits = list(leftover.values()).remove(units)
        if lftUnits:
            rest = [u for ul in lftUnits for u in ul]
        else:
            rest = []
        changed = True
        while changed:
            changed = False
            for unit in list(part):
                calc_nodes_later = False
                for (depunit, constr) in unit.getAllDeps():
                    can_in_current_proc = False
                    if constr == unit.CONSTRAINT_TYPE_NONE:
                        '''NONE type dependency represent NOT BEFORE relationship,
                        if been depended unit is satisfied in previous or in same
                        procedure, then the unit can be in current procedure.
                        There are 3 known cases for NONE type dependency:
                         - SV - CT dependency (CT in SV)
                         - Component depends-on attribute in CSM model
                         - vDicos plugin create some SV to SV dependency in NONE type
                        '''
                        if (depunit in part) or prev.satisfies_dependency(depunit):
                            can_in_current_proc = True
                    else:
                        '''For CT to CT or SV to SV dependency, if been depended
                        unit is satisfied in leftover, then the unit can be current
                        procedure.
                        '''
                        if satisfies_dependency_in_leftover(leftover, depunit):
                            can_in_current_proc = True
                    if not can_in_current_proc:
                        if strategy == CgtConstants.INDIVIDUAL_CT_DEPENDENCIES or depunit in part or depunit in rest:
                            rest.append(unit)
                            part.remove(unit)
                            changed = True
                        elif strategy == CgtConstants.GROUPED_CT_DEPENDENCIES:
                            calc_nodes_later = True
                        break
                if calc_nodes_later is True:
                    part = []
                    break
        if part:
            leftover[nodes] = [u for u in leftover[nodes] if u not in part]
            if nodes == Procedure.PROCEDURE_TYPE_SINGLESTEP:
                procType = Procedure.PROCEDURE_TYPE_SINGLESTEP
            else:
                procType = Procedure.PROCEDURE_TYPE_ROLLING
            # print "\n>>>>>>>>>>>>>> leftover[nodes]", nodes, leftover[nodes]
            if not leftover[nodes]:
                del leftover[nodes]
                # print "\n}}}}}}}}}}}}}}}}}}}} leftover after del:", leftover
            break
    return ((part, procType), nodes, leftover)


def groupCampaings(partitions):
    campaigns = []
    currCampaign = []
    # print partitions
    for (nodes, part, procType) in partitions:
        if not isDependent(part, currCampaign):
            currCampaign.append((nodes, (list(part), procType)))
        else:
            campaigns.append(list(currCampaign))
            currCampaign = [(nodes, (part, procType))]
    if currCampaign:
        campaigns.append(currCampaign)
    return campaigns


def isDependent(part, currCampaign):
    for unit in part:
        for (nodes, (currPart, proctype)) in currCampaign:
            for toUnit in currPart:
                if unit.dependsOn(toUnit) == unit.CONSTRAINT_TYPE_DIFFERENT_CAMPAIGN:
                    return True
    return False


# for some optimization of number of rolls on a given node.
def mergeRollingNodeSets(leftover):
    # print "EBALZFE mergeRollingNodeSets called with leftover", leftover
    possibleNodeGroups = [tuple(sorted(key)) for key in leftover.keys()]
    # print "EBALZFE", possibleNodeGroups
    nodeToUnitsMap = {}
    unitListToNodeMap = {}
    for (nodes, unitList) in leftover.iteritems():
        for node in nodes:
            if node in nodeToUnitsMap:
                nodeToUnitsMap[node] += unitList
            else:
                nodeToUnitsMap[node] = list(unitList)

    # printNiceDict(nodeToUnitsMap)
    for (node, unitList) in nodeToUnitsMap.iteritems():
        for tunit in unitList:
            for (depunit, constr) in tunit.getAllDeps():
                if constr != tunit.CONSTRAINT_TYPE_NONE and depunit in unitList:
                    ''' If the units(most possibly components) on same node group
                    (which means the units will be merge to same rolling procedure)
                    have different-proc or different-campaign depenedncy, then TCG
                    should not merge rolling procedure and stop optimization.
                    '''
                    logging.debug("mergeRollingNodeSets failed. Unit %s has a dependency towards unit %s and they are allocated to the same node." % (tunit.getName(), depunit.getName()))
                    return (leftover, False)
        tunitList = tuple(set(unitList))
        if tunitList in unitListToNodeMap:
            unitListToNodeMap[tunitList].append(node)
        else:
            unitListToNodeMap[tunitList] = [node]

    newLeftover = {}
    for (unitList, nodeList) in unitListToNodeMap.iteritems():
        sortedNodeTuple = tuple(sorted(nodeList))
        if sortedNodeTuple in possibleNodeGroups:
            if sortedNodeTuple in newLeftover:
                logging.debug("How could this happen??")
                assert (False)
                # newLeftover[sortedNodeList] += unitList
            else:
                newLeftover[sortedNodeTuple] = unitList
        else:
            logging.debug("mergeRollingNodeSets failed. There were nodes left with no nodegroup to roll on: {0}".format(sortedNodeTuple))
            return (leftover, False)
    return (newLeftover, True)


# for some optimization on the number of rolling procedures.
def compareByNodeNumber(item):
    return (-1) * len(item[0])


class Config(object):
    def __init__(self):
        self._pools = []

    def addPool(self, pool):
        self._pools.append(pool)

    def getPools(self):
        return self._pools

    def findPool(self, name):
        for pool in self._pools:
            if (pool.getName() == name):
                return pool
        # Not found
        return None

    def displayConfig(self, heading="DependencyCalculator.Config():"):
        logging.debug(heading)
        for pool in self.getPools():
            logging.debug("    pool %s, nodes: %s" % (pool.getName(), pool.getNodes()))
            for svid, sv in pool.getSVs().items():
                logging.debug("        sv %s, version: %s, install: %s, upgrade: %s" % (
                svid, sv.getVersion(), sv.isInstalled(), sv.isToBeUpgraded()))
                for ct in sv.getCTs():
                    logging.debug("            ct %s, instance: %s, version: %s, install: %s, upgrade: %s" % (
                    ct.getName(), ct.getInstanceName(), ct.getVersion(), ct.isInstalled(), ct.isToBeUpgraded()))
                    logging.debug("                sw:")
                    for sw in ct.getSwBundleNames():
                        logging.debug("                    %s" % sw)
            for ct in pool.getCTs():
                logging.debug("        ct %s, instance: %s, version: %s, install: %s, upgrade: %s" % (
                ct.getName(), ct.getInstanceName(), ct.getVersion(), ct.isInstalled(), ct.isToBeUpgraded()))
                logging.debug("            sw:")
                for sw in ct.getSwBundleNames():
                    logging.debug("                %s" % sw)


class PrevStruct():
    def __init__(self):
        self._repr = {}

    def __str__(self):
        return str(self._repr)

    def add(self, nodes, units):
        if nodes == Procedure.PROCEDURE_TYPE_SINGLESTEP:
            if nodes not in self._repr:
                self._repr[nodes] = []
            self._repr[nodes] += units
        else:
            for node in nodes:
                if node not in self._repr:
                    self._repr[node] = []
                self._repr[node] += units

    def remove(self, nodes, unit):
        if nodes == Procedure.PROCEDURE_TYPE_SINGLESTEP:
            assert(nodes in self._repr)
            self._repr[nodes].remove(unit)
        else:
            for node in nodes:
                assert(node in self._repr)
                self._repr[node].remove(unit)

    def satisfies_dependency(self, unit):
        for prev_unit in [u for subl in self._repr.values() for u in subl]:
            if (prev_unit.satisfies_dependency(unit)):
                return True
        return False
