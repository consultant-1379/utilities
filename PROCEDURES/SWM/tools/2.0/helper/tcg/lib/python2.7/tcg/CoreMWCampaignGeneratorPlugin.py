import Utils
import DependencyCalculator
import CgtConstants
import ConfigMerger

from utils.logger_tcg import tcg_error
import AMFModel
import AMFConstants
import CSMConstants
import tcg.plugin_api.SMFConstants as SMFConstants
import AMFTools
import SDPTools
import ImmHelper

import os
import re
import logging
from SystemModels import SystemModels
from DependencyCalculator import Procedure
import copy
from csm_units import component

DUMMY_MIGRATED_COMPONENT_UID = "dummy_migrated_component"

# -----------------------------------------------------------------------------


class CoreMWCampaignGeneratorPlugin():

    EntityRemoveOrder = [
        AMFModel.SaAmfSIRankedSU,
        AMFModel.SaAmfSIDependency,
        AMFModel.SaAmfCompCsType,
        AMFModel.SaAmfCSIAttribute,
        AMFModel.SaAmfHealthcheck,
        AMFModel.SaAmfComp,
        AMFModel.SaAmfSU,
        AMFModel.SaAmfCSI,
        AMFModel.SaAmfSI,
        AMFModel.SaAmfSG,
        AMFModel.SaAmfApplication
    ]

    def __init__(self, gen_instantiation_campaign=False, online_adapter=None):
        self.generate_instantiation_campaign = gen_instantiation_campaign

        self._SVIndependentObjectsAdded = False
        self._campaignName = None
        self._typesWritten = False
        self._smfCampaign = None
        self._allSmfCampaigns = []
        self._app_base_type_dns = set()
        self._svTargetModels = None
        self._targetAmfModel = None
        self._baseAmfModel = None
        self._campaignCTs = {}
        self._campaignSVs = {}
        self._procedureType = None
        self._procedureCTs = {}
        self._procedureCTInsts = {}
        self._procedureSVs = {}
        self._ctsTobeInstalled = []
        self._predefCoremwPGs = None
        self._nonAMFCTChanges = None
        self._campaignCount = 0
        self._mergedRolling = False
        self._isFirstProc = False
        self._campaignDirectory = None
        self._migration_info = {}
        self._migration_base = None
        self._suDict = {}
        self._sgDict = {}
        self._appDict = {}
        self._lockedNodes = []
        self._online_adapter = online_adapter
        self._created_objs = set()
        self._deleted_objs = set()
        self._cached_related_objects = {}
        self._migrated_app_types = set()
        self._migrated_comp_base_types = set()
        self._cached_in_used_comptype = None
        self._adding_bundles_in_campaign = {}
        self._amf_diff_calc_result = None

    def initialize(self, installPrefixes):
        return

    def setMigrationInfo(self, migrationInfo):
        self._migration_info = migrationInfo

    def fillConfig(self, dep_calc_config, ctAllocations, isBaseConfig):
        calc_pools = {}
        pool_svs = {}
        default_provider = AMFTools.getProvider()

        for (ct, ctAllocList) in ctAllocations.items():
            # we do not include CDS because these are specifically used by vDicos, and
            # these objects will be handled in 'CSM model extension' plug-in
            if ct.getAvailabilityManager().upper() == "CDS":
                continue

            for (_, sv, role_name, nodeSet) in ctAllocList:
                if not nodeSet:
                    continue

                # check to see if a new pool should be taken up and added
                if role_name not in calc_pools.keys():
                    calc_pools[role_name] = DependencyCalculator.Pool(role_name, nodeSet)
                    pool_svs[role_name] = {}
                    dep_calc_config.addPool(calc_pools[role_name])
                curr_calc_pool = calc_pools[role_name]

                sw_bundle_names = set()

                for filename, bundle in ct.getMetaData().softwares():
                    if not (bundle.startswith(default_provider + "-") or bundle.startswith("3PP-")):
                        bundle = self._online_adapter.get_rpm_name(bundle, filename)
                        logging.debug('Online adapter returned %s for %s' % (bundle, filename))
                    sw_bundle_names.add(bundle)

                install_scope = ct.getInstallationConstraints().getScope()
                upgrade_scope = ct.getUpgradeConstraints().getScope()
                install_need_reboot = ct.getInstallationConstraints().getReboot()
                upgrade_need_reboot = ct.getUpgradeConstraints().getReboot()
                upgrade_migration_scope = ct.getUpgradeConstraints().getMigrationScope()
                if install_scope is None:
                    install_scope = CgtConstants.SCOPE_SERVICE
                if upgrade_scope is None:
                    upgrade_scope = CgtConstants.SCOPE_COMPUTE_RESOURCE
                if upgrade_migration_scope is None:
                    upgrade_migration_scope = CgtConstants.SCOPE_SERVICE
                if install_need_reboot is None:
                    install_need_reboot = False
                if upgrade_need_reboot is None:
                    upgrade_need_reboot = False

                instance_names = []
                if sv:
                    for (inst_name, comp_type) in sv.getComponentInstances().items():
                        if comp_type.getUid() == ct.getUid():
                            instance_names.append(inst_name)
                else:
                    instance_names.append(None)

                for inst_name in instance_names:
                    calcCt = DependencyCalculator.CT(ct.getUid(), inst_name, ct.getVersion(), nodeSet, sw_bundle_names, install_scope,
                                                 upgrade_scope, upgrade_migration_scope, install_need_reboot,
                                                 upgrade_need_reboot)
                    calcCt.setPlugin(self)
                    if not isBaseConfig:
                        calcCt.set_existing_type(ct.getUid() not in self._ctsTobeInstalled)
                    calcCt.set_csm_unit(ct)
                    calcCt.set_sv_csm_unit(sv)
                    if sv is None or (ct.getAvailabilityManager().upper() == CSMConstants.AVAILABILTY_MANAGER_NONE):
                        curr_calc_pool.addCT(calcCt)
                    else:
                        sv_uid = sv.getUid()
                        if sv_uid not in pool_svs[role_name].keys():
                            calcSv = DependencyCalculator.SV(sv_uid, ct.getVersion(), nodeSet)
                            calcSv.setPlugin(self)
                            pool_svs[role_name][sv_uid] = calcSv
                            curr_calc_pool.addSV(calcSv)

                        calcSv = pool_svs[role_name][sv_uid]
                        calcCt.addSV(calcSv)
                        calcSv.addCT(calcCt)
                        calcSv.set_csm_unit(sv)

    @staticmethod
    def convertConstraint(constraint_method, uid):
        strc = str(constraint_method)
        if strc == component.GenericConstraints.METHOD_DIFFERENT_PROCEDURE:
            return DependencyCalculator.CT.CONSTRAINT_TYPE_DIFFERENT_PROCEDURE
        elif strc == component.GenericConstraints.METHOD_DIFFERENT_CAMPAIGN:
            return DependencyCalculator.CT.CONSTRAINT_TYPE_DIFFERENT_CAMPAIGN
        else:
            tcg_error("Unsupported constraint method %s in unit %s" % (strc, uid))

    def getSVDependencies(self, role, svId, isToBeRemoved=False):
        if isToBeRemoved:
            #TODO: support uninstallation dependencies
            return []
        model = SystemModels.targetCSMModel
        role = model.getRole(role)
        uses = []

        if svId not in map(lambda x: x.getUid(), role.getServices()):
            tcg_error("Error while fetching SV dependencies. Incosistency in model: Dependent service %s is not in role %s" % (svId, role.getUid()))

        service = model.getService(svId)

        # check as well the promotional dependendencies
        for dependObject in service.getDependsOnServices() :
            if not dependObject.getDependsOnService():
                tcg_error("ERROR: depends-on in %s defined without giving any service" % svId)
            uses.append((dependObject.getDependsOnService(), DependencyCalculator.SV.CONSTRAINT_TYPE_DIFFERENT_PROCEDURE))
        return uses

    def getCTDependencies(self, roleId, ctId, isToBeMigrated=False, isToBeRemoved=False):
        if isToBeRemoved:
            # TODO: Uninstallation dependencies
            return []
        model = SystemModels.targetCSMModel
        role = model.getRole(roleId)
        component = None
        #Workaround-ish solution. This way it is not ensured that the actual
        #correct component instance is fetched. For now this is okay because
        #all we need is the node allocation to match. But for a proper
        #solution we need to redesign the dependency calculator, to work on a
        #per node basis rather than a per role basis.
        for ct in role.getComponents():
            if ctId == ct.getUid():
                component = ct
                break
        if not component:
            return []
        uses = []

        if ctId in self._ctsTobeInstalled and not isToBeMigrated:
            for (ct_uid, isolation_method) in component.getInstallationConstraints().getAfterComponents():
                constraint = self.convertConstraint(isolation_method, ctId)
                uses.append((ct_uid, constraint))
        else:
            for (ct_uid, isolation_method) in component.getUpgradeConstraints().getAfterComponents():
                constraint = self.convertConstraint(isolation_method, ctId)
                if constraint == DependencyCalculator.CT.CONSTRAINT_TYPE_DIFFERENT_CAMPAIGN:
                    tcg_error('ERROR: in component %s DIFFERENT-FLOW is not supported for upgrade constraint'
                              % ct_uid)
                uses.append((ct_uid, constraint))

        for dependencyId in component.getDependsOnComponents():
            if dependencyId not in map(lambda x: x.getUid(), role.getFullComponents()):
                tcg_error("Error while fetching CT dependencies. Dependency component %s is not in role %s" % (dependencyId, role.getUid()))
            if not model.getComponent(dependencyId).getExternal():
                # dependency calculation only considers non-external components
                # external components are not part of dependency calculation
                uses.append((dependencyId, DependencyCalculator.CT.CONSTRAINT_TYPE_NONE))

        return uses

    def _imm_objs_in_proc_init_action(self):
        """
        Return a set/dict containing the objectis that need be add/updated/removed during the procedure init step
        """
        rmv_objs = set()
        upd_objs = {}
        add_objs = set()

        for ct_instance in self._procedureCTInsts.keys():
            if ct_instance.isToBeUpgraded() and ct_instance.getSV() is not None:
                svid = ct_instance.getSV().getName()

                ct_update_tup = self._amf_diff_calc_result.get_amf_diff_calc_result_dict_by_types(svid, ct_instance.getName(), self._amf_diff_calc_result.UPDATEABLE_COMPONENT_ATTRIBUTE_LIST)
                if ct_update_tup is None:
                    continue

                (added, updated, removed) = ct_update_tup
                add_objs.update(added)
                rmv_objs.update(removed)
                upd_objs.update(updated)

        for (sv, info) in self._procedureSVs.items():
            sv_update_tup = self._amf_diff_calc_result.get_amf_diff_calc_result_dict_by_types(sv, None, self._amf_diff_calc_result.UPDATEABLE_SERVICE_ATTRIBUTE_LIST)
            if info[0].isToBeUpgraded() and sv_update_tup is not None:
                (added, updated, removed) = sv_update_tup
                rmv_objs.update(removed)
                upd_objs.update(updated)
                add_objs.update(added)

        return (add_objs, rmv_objs, upd_objs)

    def generateProcInit(self, updated_cts_per_svs):
        """
        Generate actions in campaign at procedure init step.
        """
        (add_objects, rmv_objs, update_objs) = self._imm_objs_in_proc_init_action()
        self._lock_unlock_sis_for_service_upgrade(True)

        if add_objects or update_objs or rmv_objs:
            self._smfCampaign.beginProcInitAction()
            self._smfCampaign.beginImmCCB()
        for obj in add_objects:
            self._create_object_in_campaign(obj)
        for dn in update_objs:
            self._smfCampaign.generateModifyObject(dn, update_objs[dn], True)
        for obj in rmv_objs:
            if obj.getDn() not in self._deleted_objs:
                self._deleted_objs.add(obj.getDn())
                self._smfCampaign.generateDeleteObject(obj.getDn())
        if add_objects or update_objs or rmv_objs:
            self._smfCampaign.endImmCCB()
            self._smfCampaign.endProcInitAction()


    def _lock_unlock_sis_for_service_upgrade(self, do_lock_si = True):

        """
        Manually lock/unlock the SIs during upgrade of existing service
        """
        for (sv, info) in self._procedureSVs.items():
            sv_update_tup = self._amf_diff_calc_result.get_amf_diff_calc_result_dict_by_types(sv, None, self._amf_diff_calc_result.UPDATEABLE_SERVICE_ATTRIBUTE_LIST)
            if (not sv_update_tup) or (info[0].isToBeUpgraded() == False):
                continue
            silist = []
            # only necessary to lock SI if an attributes is being added/deleted
            (added, _, removed) = sv_update_tup
            silist.extend(added)
            silist.extend(removed)
            for amfobj in silist:
                pdn = amfobj.getParentDn()
                pobj = self._targetAmfModel.getObject(pdn)
                if type(pobj) != AMFModel.SaAmfSI:
                    continue
                si = pobj.getDn()
                if do_lock_si:
                    self._smfCampaign.beginProcInitAction()
                    self._smfCampaign.generateDoAdminOperation(si, AMFConstants.ADMIN_LOCK)
                    self._smfCampaign.generateUndoAdminOperation(si, AMFConstants.ADMIN_UNLOCK)
                    self._smfCampaign.endProcInitAction()
                else:
                    self._smfCampaign.beginProcWrapupAction()
                    self._smfCampaign.generateDoAdminOperation(si, AMFConstants.ADMIN_UNLOCK)
                    self._smfCampaign.generateUndoAdminOperation(si, AMFConstants.ADMIN_LOCK)
                    self._smfCampaign.endProcWrapupAction()

    def _createObjectInstancesInProcedureInit(self):
        if not self._SVIndependentObjectsAdded:
            self._SVIndependentObjectsAdded = True
            self._add_saAmfApplication_objects_to_smfCampaign()
            self._add_saAmfNodeGroup_objects_to_smfCampaign()

        self._add_saAmfService_objects_to_smfCampaign()
        # Add components of existing services
        self._add_SaAmf_component_objects_to_smfCampaign()

    def _add_saAmfApplication_objects_to_smfCampaign(self):
        apps = []


        for appBaseTypeDn in self._app_base_type_dns:
            (added, _, _) = self._amf_diff_calc_result.get_amf_diff_calc_result_dict_by_types(appBaseTypeDn, None, [AMFModel.SaAmfApplication])
            for amfobj in added:
                apps.append(amfobj)
        self._add_immccb_to_smfCampaign_from_amf_objects(apps)

    def _add_saAmfNodeGroup_objects_to_smfCampaign(self):
        # add missing SaAmfNodeGroup groups
        # currently node group changes or removes are not supported
        ngBaseModel = self._get_amfModel_with_saAmfNodeGroup_groups_from(self._baseAmfModel)
        ngTargetModel = self._get_amfModel_with_saAmfNodeGroup_groups_from(self._targetAmfModel)

        added, updated, _, _ = ngTargetModel.diff(ngBaseModel)
        if len(updated) > 0:
            tcg_error("Unsupported nodegroup change")

        ngs = []
        for (ngDn, ng) in ngTargetModel.getObjects().items():
            if ngDn in added and ImmHelper.getName(ngDn) not in self._predefCoremwPGs:
                ngs.append(ng)
        self._add_immccb_to_smfCampaign_from_amf_objects(ngs)

    def _add_saAmfService_objects_to_smfCampaign(self):
        objectTypesInOrder = [ AMFModel.SaAmfSG, AMFModel.SaAmfSI,
                               AMFModel.SaAmfSIDependency, AMFModel.SaAmfSU,
                               AMFModel.SaAmfCSI, AMFModel.SaAmfCSIAttribute,
                               AMFModel.SaAmfComp, AMFModel.SaAmfCompCsType ]
        for (sv, svInfo) in self._procedureSVs.items():
            if not svInfo[0].isToBeUpgraded():
                if not SystemModels.service_to_be_installed(sv):
                    # a service already installed in the system is being added to a new role
                    # this function is only for adding completely new services
                    continue
                (targetModel, _, sgDn, _, _, _, _) = self._svTargetModels[sv]
                if not targetModel.isObjectCreatedInCampaign():
                    if ((self._procNeedsReboot() or self._proc_at_compute_resource_scope()) and
                                sgDn not in self._baseAmfModel.getObjects() and
                                svInfo[0].isToBeMigrated()):
                        self._optimize_activation(self,targetModel)
                    self._add_immccb_to_smfCampaign(sgDn, [targetModel], objectTypesInOrder)

    def _add_SaAmf_component_objects_to_smfCampaign(self):

        all_obj = self._get_component_instance_objects_in_existing_services()
        if all_obj:
            self._add_immccb_to_smfCampaign_without_guards(all_obj)
            for obj in all_obj:
                self._created_objs.add(obj.getDn())

    def __su_for_existing_services_which_have_new_or_removed_comp_ins(self, include_existing_services_installed_on_new_nodes = False):
        sus = set()
        for (ct_inst, nodes) in [(c, n) for (c, n) in self._procedureCTInsts.items()
                                     if (not c.isToBeUpgraded() and not c.isInstalled()) or c.isToBeRemoved()]:
            theSV = ct_inst.getSV()
            if theSV is None:
                continue
            # sus that exist on this node
            include_su = (ct_inst.isToBeRemoved() or theSV.isToBeUpgraded() or theSV.isInstalled())
            if not include_su and include_existing_services_installed_on_new_nodes:
                # is the service installed in the system...but being installed on new nodes?
                include_su = not SystemModels.service_to_be_installed(theSV.getName()) and not theSV.isToBeUpgraded() and not theSV.isInstalled()

            if include_su:
                (targetModel, _, _, _, _, _, _) = self._svTargetModels[theSV.getName()]
                for (su, obj) in targetModel.getObjects(AMFModel.SaAmfSU).items():
                    node = obj.getsaAmfSUHostNodeOrNodeGroup()
                    ct_on_nodes = nodes
                    if ImmHelper.getName(node) in ct_on_nodes:
                        sus.add(su)
        return sus

    def _get_component_instance_objects_in_existing_services(self):

        amf_objects = []
        sus = self.__su_for_existing_services_which_have_new_or_removed_comp_ins(True)
        sgs = set([self._targetAmfModel.getObject(su).getParentDn() for su in sus])

        for sg in sgs:
            # if an SU is being added to a new role, we will see it here
            su_added = self._amf_diff_calc_result.get_amf_diff_calc_result_dict_by_types(sg, None, [AMFModel.SaAmfSU])
            if su_added:
                (added, _, _) = su_added
                for amf_obj in added:
                    if((amf_obj.getDn() not in self._created_objs)):
                        amf_objects.append(amf_obj)

            for ct_inst in self._procedureCTInsts.keys():
                if (ct_inst.isToBeUpgraded() or len(ct_inst.isInstalled())):
                    continue

                # All component specific instance entities
                objectTypeOrder = [AMFModel.SaAmfCSI, AMFModel.SaAmfCSIAttribute, AMFModel.SaAmfComp,
                               AMFModel.SaAmfCompCsType]

                amf_diff_dict = self._amf_diff_calc_result.get_amf_diff_calc_result_dict_by_types(sg, ct_inst.getName(), objectTypeOrder)

                if not amf_diff_dict:
                    continue

                (binding_obj, _, _) = amf_diff_dict

                for amf_obj in binding_obj:
                    if((amf_obj.getDn() not in self._created_objs)):
                        amf_objects.append(amf_obj)
                        # amf_objects is calculated based on the sg and the ct type.
                        # If a component type has multiple instances in the same sg
                        # all the instances are in the amf_objects.
                        # To avoid creating instances multiple times we set them as created
                        self._created_objs.add(amf_obj.getDn())
        return amf_objects

    def _get_amfModel_with_saAmfNodeGroup_groups_from(self, amf_model):
        target_model = AMFModel.AMFModel()
        for ng in amf_model.getObjects(AMFModel.SaAmfNodeGroup).values():
            target_model.addObject(ng)
        return target_model

    def _add_immccb_to_smfCampaign_from_amf_objects(self, amf_obj_list):
        for obj in amf_obj_list:
            self._add_immccb_to_smfCampaign(obj.getDn(), [obj])

    def _add_immccb_to_smfCampaign(self, dn, objects, object_types=[]):
        if not self.generate_instantiation_campaign:
            if not self._smfCampaign.skip_generate_markup_tag(Utils.getExactMatchPattern(dn)):
                self._add_immccb_to_smfCampaign_without_guards(objects, object_types)

    def _add_immccb_to_smfCampaign_without_guards(self, objects, object_types=[]):
        if not self.generate_instantiation_campaign:
            self._smfCampaign.beginProcInitAction()
            self._smfCampaign.beginImmCCB()
            for obj in objects:
                self._create_object_in_campaign(obj, object_types)
            self._smfCampaign.endImmCCB()
            self._smfCampaign.endProcInitAction()

    def _create_object_in_campaign(self, obj, object_types=[]):
        if object_types:
            for _type in object_types:
                obj.createObjectInCampaign(self._smfCampaign, _type)
                for objDn in obj.getObjects(_type).keys():
                    self._created_objs.add(objDn)
        else:
            obj.createObjectInCampaign(self._smfCampaign)

    def generateSingleStepProcedureInit(self):
        self.__lock_sus_for_existing_services_which_have_new_comp_ins()
        self._createObjectInstancesInProcedureInit()

    def __lock_sus_for_existing_services_which_have_new_comp_ins(self):
        for su in self.__su_for_existing_services_which_have_new_or_removed_comp_ins():
            """
            If we are adding new components to existing services
            we need to manually lock/unlock the SUs.
            """
            self._smfCampaign.beginProcInitAction()
            self._smfCampaign.generateDoAdminOperation(su, AMFConstants.ADMIN_LOCK)
            self._smfCampaign.generateUndoAdminOperation(su, AMFConstants.ADMIN_UNLOCK)
            self._smfCampaign.endProcInitAction()
            self._smfCampaign.beginProcInitAction()
            self._smfCampaign.generateDoAdminOperation(su,
                                                       AMFConstants.ADMIN_LOCK_INSTANTIATION)
            self._smfCampaign.generateUndoAdminOperation(su,
                                                         AMFConstants.ADMIN_UNLOCK_INSTANTIATION)
            self._smfCampaign.endProcInitAction()

    def __lock_unlock_sgs_for_removal_in_rolling_upgrade_proc(self, lock=True):
        for (sv, info) in self._procedureSVs.items():
            model = self._amf_diff_calc_result.get_instances_removed_from_base(sv)
            for sg in model.getObjects(AMFModel.SaAmfSG):
                # sg was locked in one of the previous procedures and was deleted too
                if sg in self._deleted_objs:
                    continue
                self._smfCampaign.beginProcInitAction()
                if lock:
                    self._smfCampaign.generateDoAdminOperation(sg, AMFConstants.ADMIN_LOCK)
                    self._smfCampaign.generateUndoAdminOperation(sg, AMFConstants.ADMIN_UNLOCK)
                    self._smfCampaign.endProcInitAction()
                    self._smfCampaign.beginProcInitAction()
                    self._smfCampaign.generateDoAdminOperation(sg, AMFConstants.ADMIN_LOCK_INSTANTIATION)
                    self._smfCampaign.generateUndoAdminOperation(sg, AMFConstants.ADMIN_UNLOCK_INSTANTIATION)
                else:
                    self._smfCampaign.generateDoAdminOperation(sg, AMFConstants.ADMIN_UNLOCK_INSTANTIATION)
                    self._smfCampaign.generateUndoAdminOperation(sg, AMFConstants.ADMIN_LOCK_INSTANTIATION)
                    self._smfCampaign.endProcInitAction()
                    self._smfCampaign.beginProcInitAction()
                    self._smfCampaign.generateDoAdminOperation(sg, AMFConstants.ADMIN_UNLOCK)
                    self._smfCampaign.generateUndoAdminOperation(sg, AMFConstants.ADMIN_LOCK)
                self._smfCampaign.endProcInitAction()

    def __collect_instances_to_be_deleted_in_upgrade_proc(self):
        deleting_obj_dns = {}
        for ct_instance in self._procedureCTInsts.keys():
            if ct_instance.getSV() is not None:
                svid = ct_instance.getSV().getName()
                model = self._amf_diff_calc_result.get_instances_removed_from_base(svid)
                for class_ in CoreMWCampaignGeneratorPlugin.EntityRemoveOrder:
                    for dn in model.getObjects(class_).keys():
                        if dn not in self._deleted_objs:
                            if class_ not in deleting_obj_dns:
                                deleting_obj_dns[class_] = []
                            deleting_obj_dns[class_].append(dn)
                            self._deleted_objs.add(dn)
        for (sv, _) in self._procedureSVs.items():
            model = self._amf_diff_calc_result.get_instances_removed_from_base(sv)
            for class_ in CoreMWCampaignGeneratorPlugin.EntityRemoveOrder:
                for dn in model.getObjects(class_).keys():
                    if dn not in self._deleted_objs:
                        if class_ not in deleting_obj_dns:
                            deleting_obj_dns[class_] = []
                        deleting_obj_dns[class_].append(dn)
                        self._deleted_objs.add(dn)
        return deleting_obj_dns

    def __delete_instances_in_upgrade_proc(self):
        deleting_obj_dns_dict = self.__collect_instances_to_be_deleted_in_upgrade_proc()
        deleting_obj_dns = []
        for class_ in CoreMWCampaignGeneratorPlugin.EntityRemoveOrder:
            if class_ in deleting_obj_dns_dict:
                for dn in deleting_obj_dns_dict[class_]:
                    deleting_obj_dns.append(dn)
        if len(deleting_obj_dns) == 0:
            return
        self._smfCampaign.beginProcWrapupAction()
        self._smfCampaign.beginImmCCB()
        for obj_dn in deleting_obj_dns:
            self._smfCampaign.beginDelete(obj_dn)
            self._smfCampaign.endDelete()
        self._smfCampaign.endImmCCB()
        self._smfCampaign.endProcWrapupAction()

    def _procNeedsReboot(self):
        for ct in self._procedureCTs.values():
            if ct[1].isRebootNeeded():
                return True
        return False

    def _proc_at_compute_resource_scope(self):
        if (self._procedureType == Procedure.PROCEDURE_TYPE_ROLLING):
            """
            In the current implementation the rolling procedures are always at
            compute resource level. This may change in the future to allow
            rolling procedures that iterate over SGs. When we have rolling
            procedures at SG level, we will need to revisit this method
            """
            return True
        for (ctId, (_, ct, _)) in self._procedureCTs.items():
            if ct.get_scope() == CgtConstants.SCOPE_COMPUTE_RESOURCE:
                return True
        return False

    def generateDeactivationUnit(self):
        acted_on_list = set()
        if len(self._procedureSVs) > 0:
            reboot_needed = self._procNeedsReboot()
            if not reboot_needed:
                nodes_acted_on = set()
                if self._proc_at_compute_resource_scope():
                    for sv in self._procedureSVs.keys():
                        (_, baseModel, _, _, _, _, _) = self._svTargetModels[sv]
                        for (dn, su) in baseModel.getObjects(AMFModel.SaAmfSU).items():
                            node = su.getsaAmfSUHostNodeOrNodeGroup()
                            nodes_acted_on.add(node)
                    for node in nodes_acted_on:
                        acted_on_list.add(node)
                else:
                    # The scope of the procedure is SERVICE
                    for (sv, svInfo) in self._procedureSVs.items():
                        (_, baseModel, _, _, _, _, _) = self._svTargetModels[sv]
                        for su in baseModel.getObjects(AMFModel.SaAmfSU).keys():
                            acted_on_list.add(su)
                for node in self._lockedNodes:
                    if (node not in nodes_acted_on):
                        acted_on_list.add(node)

                self._lockedNodes = []
        if self._lockedNodes:
            for node in self._lockedNodes:
                acted_on_list.add(node)
            self._lockedNodes = []

        amf_objs_to_remove = {}
        sdp_list = []

        installed_bundles = map(ImmHelper.getName, self._migration_base.getObjects(AMFModel.SaAmfNodeSwBundle))

        for ctId in self._procedureCTs:
            if ctId not in self._migration_info or self._procedureCTs[ctId][1].isToBeRemoved():
                continue
            supersedes = self._migration_info[ctId]
            '''
            Below code will loop through supersede entity, then get deprecated objects/bundle to remove.
            <base-component> has higher priority than <software> in generating deprecated items.
            '''
            for supersede in supersedes:
                if CgtConstants.COMPONENT_SUPERSEDES_BASE_COMPONENT_TAG in supersede:
                    if CgtConstants.COMPONENT_SUPERSEDES_SOFTWARE_TAG in supersede:
                        logging.info('%s" both <base-component> and <software> are specified for the same'
                                        'deprecated entity, ignore the software specification' % ctId)
                    base_comp_type_name = supersede[CgtConstants.COMPONENT_SUPERSEDES_BASE_COMPONENT_TAG]
                    objs = self.get_amf_related_objects(base_comp_type_name)
                    add_dict_list(amf_objs_to_remove, objs)

                elif CgtConstants.COMPONENT_SUPERSEDES_SOFTWARE_TAG in supersede:
                    deprecated_sdp = SDPTools.get_bundle_name_with_provider_missing(installed_bundles,
                                          supersede[CgtConstants.COMPONENT_SUPERSEDES_SOFTWARE_TAG])
                    if deprecated_sdp is not None:
                        sdp_list.append(deprecated_sdp)
                else:
                    logging.debug('<base-component> or <software> tag is not available under <supersedes> tag, '
                                  'ignore migrate %s' % ctId)

        unique_dict_list(amf_objs_to_remove)

        if amf_objs_to_remove:
            sus = get_list_by_key(amf_objs_to_remove, AMFModel.SaAmfSU)
            for su in sus:
                if su not in self._suDict:
                    self._suDict[su] = self._migration_base.getObjects(AMFModel.SaAmfComp, su).keys()

            sgs = get_list_by_key(amf_objs_to_remove, AMFModel.SaAmfSG)
            for sg in sgs:
                if sg not in self._sgDict:
                    self._sgDict[sg] = self._migration_base.getObjects(AMFModel.SaAmfSU, sg).keys()

            apps = get_list_by_key(amf_objs_to_remove, AMFModel.SaAmfApplication)
            for app in apps:
                if app not in self._appDict:
                    self._appDict[app] = self._migration_base.getObjects(AMFModel.SaAmfSG, app).keys()

            remaining_sus = calc_remove_children(get_list_by_key(amf_objs_to_remove, AMFModel.SaAmfComp),
                                                 get_list_by_key(amf_objs_to_remove, AMFModel.SaAmfSU), self._suDict)

            self.calc_su_related(amf_objs_to_remove, remaining_sus)

            calc_remove_children(get_list_by_key(amf_objs_to_remove, AMFModel.SaAmfSU),
                                 get_list_by_key(amf_objs_to_remove, AMFModel.SaAmfSG), self._sgDict)
            calc_remove_children(get_list_by_key(amf_objs_to_remove, AMFModel.SaAmfSG),
                                 get_list_by_key(amf_objs_to_remove, AMFModel.SaAmfApplication), self._appDict)

        add_dict_list(amf_objs_to_remove, self.__collect_instances_to_be_deleted_in_upgrade_proc())

        # in case of no component base specified
        # deactivation unit don't need to remove object, so we don't need to lock and lock-in su
        if amf_objs_to_remove:

            if not self._proc_at_compute_resource_scope():
                acted_on_list.update(get_list_by_key(amf_objs_to_remove, AMFModel.SaAmfSU))
            else:
                for removedDn in get_list_by_key(amf_objs_to_remove, AMFModel.SaAmfSU):
                    removedObject = self._migration_base.getObject(removedDn)
                    hostedOn = removedObject.getsaAmfSUHostNodeOrNodeGroup()
                    if hostedOn:
                        hostOnObject = self._migration_base.getObject(hostedOn)
                        if type(hostOnObject) == AMFModel.SaAmfNode:
                            acted_on_list.add(hostedOn)
                        elif type(hostOnObject) == AMFModel.SaAmfNodeGroup:
                            nodeDns = hostOnObject.getsaAmfNGNodeList()
                            acted_on_list.update(nodeDns)
                    else:
                        sgDn = ImmHelper.getParentDn(removedDn)
                        sgObject = self._migration_base.getObject(sgDn)
                        nodeGroupDn = sgObject.getsaAmfSGSuHostNodeGroup()
                        nodeGroupObject = self._migration_base.getObject(nodeGroupDn)
                        nodeDns = nodeGroupObject.getsaAmfNGNodeList()
                        acted_on_list.update(nodeDns)
                self._lockedNodes = list(acted_on_list)
                # Mark ONE-STEP Upgrade is needed for this campaign when we have one of its procedure is the migration
                # one which acts on Compute Resource level.
                self._smfCampaign.setOneStepUpgrade(True)

        if acted_on_list:
            self._smfCampaign.beginActedOn()
            for byName in acted_on_list:
                self._smfCampaign.generateByName(byName)
            self._smfCampaign.endActedOn()

        sdp_list = list(set(sdp_list))
        sdpNameList = sdp_list

        if amf_objs_to_remove:
            removing_entities = [removedDn for removeType in CoreMWCampaignGeneratorPlugin.EntityRemoveOrder
                                 for removedDn in get_list_by_key(amf_objs_to_remove, removeType)]

            # For this migration uses <removed> tag, but for uninstallation we are deleting in procwrapup to be
            # consistent between single step and rolling upgrade procedures
            if len(removing_entities):
                self._smfCampaign.beginRemoved()
                for entity in removing_entities:
                    self._smfCampaign.generateByName(entity)
                self._smfCampaign.endRemoved()

            for sdpName in get_list_by_key(amf_objs_to_remove, AMFModel.SaSmfSwBundle):
                found = False
                for sdp in sdp_list:
                    if sdpName.startswith("safSmfBundle=" + sdp):
                        found = True
                        break
                if not found:
                    parts = sdpName[len("safSmfBundle="):].rsplit("-", 2)
                    name = parts[0] + "-" + _stripProductNumberRevision(parts[1])
                    sdpNameList.append(name)

        for sdpName in sdpNameList:
            swInstalledObjects = self.get_amf_objects_with_name_pattern(AMFModel.SaAmfNodeSwBundle,
                                                                        "safSmfBundle=" + sdpName + ".*")

            if len(swInstalledObjects) == 0:
                # If superseded software is not installed
                continue

            # In case of migration, if version of target app is the same as base one then skip remove it
            targetSwInstallObjects = self.get_amf_objects_with_name_pattern(AMFModel.SaAmfNodeSwBundle,
                                                                        "safSmfBundle=" + sdpName + ".*",
                                                                        self._targetAmfModel)

            sw_installed_object_set = set(swInstalledObjects)
            sw_installing_object_set = set(targetSwInstallObjects)
            removing_bundles = sw_installed_object_set - sw_installing_object_set

            if removing_bundles:
                usedBundleDn = getCmwGetUsedBundleDnMacro(self._migration_base, sdpName)
                if usedBundleDn:
                    nodeList = set(map(ImmHelper.getParentDn, removing_bundles))
                    prefix = self._migration_base.getObject(swInstalledObjects[0]).getsaAmfNodeSwBundlePathPrefix()
                    self._smfCampaign.beginSwRemove(usedBundleDn, prefix)
                    for node in nodeList:
                        self._smfCampaign.generatePlmExecEnv(node)
                    self._smfCampaign.endSwRemove()

        self._add_swRemove(True)

    def generateSingleStepProcedureBody(self):
        if len(self._procedureSVs) > 0:
            reboot_needed = self._procNeedsReboot()
            if not reboot_needed:
                nodes_acted_on = set()
                au = set()
                if self._proc_at_compute_resource_scope():
                    for sv in self._procedureSVs.keys():
                        (targetModel, _, _, _, _, _, _) = self._svTargetModels[sv]
                        for (dn, su) in targetModel.getObjects(AMFModel.SaAmfSU).items():
                            node = su.getsaAmfSUHostNodeOrNodeGroup()
                            nodes_acted_on.add(node)
                    for node in nodes_acted_on:
                        au.add(node)
                else:
                    # The scope of the procedure is SERVICE
                    for (sv, svInfo) in self._procedureSVs.items():
                        (targetModel, _, _, _, _, _, _) = self._svTargetModels[sv]
                        for su in targetModel.getObjects(AMFModel.SaAmfSU).keys():
                            su_obj = targetModel.getObject(su)
                            old_state = self._get_old_SuAdminState(self,su_obj,targetModel)
                            #Don't activate SU in case of migration at SU level and old SU admin state LOCKED_IN
                            if old_state is None or old_state != AMFConstants.SA_AMF_ADMIN_LOCKED_INSTANTIATION:
                                au.add(su)
                for node in self._lockedNodes:
                    if (node not in nodes_acted_on):
                        au.add(node)
                if au:
                    self._smfCampaign.beginActedOn()
                    for unit in au:
                        self._smfCampaign.generateByName(unit)
                    self._smfCampaign.endActedOn()
                self._lockedNodes = []
        if self._lockedNodes:
            self._smfCampaign.beginActedOn()
            for node in self._lockedNodes:
                self._smfCampaign.generateByName(node)
            self._smfCampaign.endActedOn()
            self._lockedNodes = []

        if not self.generate_instantiation_campaign:
            self._add_swAdd(single_step=True)

    def generateRollingProcedureInit(self):
        self.__lock_sus_for_existing_services_which_have_new_comp_ins()
        self.__lock_unlock_sgs_for_removal_in_rolling_upgrade_proc()
        self._createObjectInstancesInProcedureInit()

    def generateRollingProcedureBody(self):
        pass

    def generateRollingProcedureAddSwRemove(self):
        if not self.generate_instantiation_campaign:
            self._add_swRemove()

    def generateRollingProcedureAddSwAdd(self):
        if not self.generate_instantiation_campaign:
            self._add_swAdd()

    def _add_swRemove(self, forSingleStep=False):
        rem_dict = {}
        self._add_swRemove_for_AMF_Components(rem_dict)
        self._add_swRemove_for_Non_AMF_Components(rem_dict)
        for bundle, nodes in rem_dict.items():
            if bundle not in self._amf_diff_calc_result.get_bundles_removed_from_base():
                continue
            if forSingleStep:
                affected_nodes = nodes & self._amf_diff_calc_result.get_bundles_removed_from_base()[bundle]
                if len(affected_nodes) == 0:
                    continue
                self._smfCampaign.beginSwRemove(bundle, AMFConstants.AMFCOMPONENTTYPE_DEFAULT_PREFIX)
                for node in affected_nodes:
                    self._smfCampaign.generatePlmExecEnv(AMFTools.getNodeDnFromName(node))
                self._smfCampaign.endSwRemove()
            else:
                self._smfCampaign.beginSwRemove(bundle, AMFConstants.AMFCOMPONENTTYPE_DEFAULT_PREFIX)
                self._smfCampaign.endSwRemove()


    def _add_swRemove_for_AMF_Components(self, rem_dict):
        for ct in self._procedureCTInsts:
            if ct.isSwToBeUpgraded() or ct.isToBeRemoved():  # FIXME: define and use isSwToBeRemoved()
                self.addSwRemove(rem_dict, ct.getName(), ct.getNodes())

    def _add_swRemove_for_Non_AMF_Components(self, rem_dict):
        for removedDn in self._nonAMFCTChanges[2]:
            ctId = AMFTools.getUnitIdFromModelName(ImmHelper.getName(ImmHelper.getParentDn(removedDn)))
            if ctId in self._procedureCTs.keys():
                self.addSwRemove(rem_dict, ctId, self._procedureCTs[ctId][2])
                continue

            # check to see if there has been an upgrade of the components uid
            for ctInfo in self._procedureCTs.values():
                ct = ctInfo[1]
                if not ct.get_sv_csm_unit():
                    continue
                if ct.get_sv_csm_unit().comp_inst_is_upgraded(ct.getInstanceName(),ct.getName(),ctId):
                    self.addSwRemove(rem_dict, ctId, ctInfo[2], True)

    def _add_swAdd(self, single_step=False):
        for ctId, ctInfo in self._procedureCTs.items():
            sdpNames = self._getSDPNameFromUnit(ctId)
            prefix = AMFConstants.AMFCOMPONENTTYPE_DEFAULT_PREFIX
            self._add_swAdd_elements_to_smfCampaign(sdpNames, prefix, ctInfo[2], single_step)

    def _add_swAdd_elements_to_smfCampaign(self, sdpNames, prefix, nodes, single_step):
        '''
        There would be a case if multiple components point to same software bundle, in that case
        there should not be multiple software add sections for the same software
        That is handled through addedBundles
        '''
        for sdpName in sdpNames:
            if self._is_sdp_assigned_to_any_of(sdpName, nodes):
                swInstalledObjects = self.get_amf_objects_with_name_pattern(AMFModel.SaAmfNodeSwBundle,
                                                                            "safSmfBundle=" + sdpName + ".*")
                if len(swInstalledObjects) > 0:
                    targetSwInstallingObjects = self.get_amf_objects_with_name_pattern(AMFModel.SaAmfNodeSwBundle,
                                                                                    "safSmfBundle=" + sdpName + ".*",
                                                                                    self._targetAmfModel)
                    if len(targetSwInstallingObjects) > 0:
                        sw_installed_object_set = set(swInstalledObjects)
                        sw_installing_object_set = set(targetSwInstallingObjects)
                        sdp_name_with_version = ImmHelper.getName(targetSwInstallingObjects[0])[len('safSmfBundle='):]
                        installed_bundles = map(lambda n: ImmHelper.getName(n)[len('safSmfBundle='):],
                                                sw_installed_object_set)
                        if sdp_name_with_version in installed_bundles:
                            prefix = self._migration_base.getObject(
                                swInstalledObjects[0]).getsaAmfNodeSwBundlePathPrefix()
                            nodes = set(map(ImmHelper.getName, map(ImmHelper.getParentDn,
                                                                   sw_installing_object_set - sw_installed_object_set)))
                if len(nodes) > 0:
                    if single_step:
                        self._add_swAdd_element_to_smfCampaign_for_single_step_upgr(sdpName, prefix, nodes)
                    else:
                        self._add_swAdd_tag_elmt_for_rolling_procedure(sdpName, prefix, nodes)

    def _is_sdp_assigned_to_any_of(self, sdpName, nodes):
        nodes_with_sdp = self._get_nodes_with_sdp(sdpName)
        il = nodes - nodes_with_sdp
        return len(il) > 0

    def _add_swAdd_tag_elmt_for_rolling_procedure(self, sdpName, prefix, nodes):
        if not nodes <= self._smfCampaign.get_installed_nodes_for_bundle_name(sdpName):
            self._smfCampaign.beginSwAdd(AMFTools.getSaSmfSwBundleDnFromUnit(sdpName), prefix)
            self._smfCampaign.endSwAdd()
            self._smfCampaign.addSoftwareBundleToNodes(sdpName = sdpName, nodes = nodes)

    def _add_swAdd_element_to_smfCampaign_for_single_step_upgr(self, sdpName, prefix, nodes):
        installed_nodes = self._smfCampaign.get_installed_nodes_for_bundle_name(sdpName)
        installed_nodes_in_campaign = self._smfCampaign.getAddedSoftwareBundlesToNodes()[sdpName]
        to_be_installed_nodes = (nodes - installed_nodes - installed_nodes_in_campaign)
        if to_be_installed_nodes:
            self._smfCampaign.beginSwAdd(AMFTools.getSaSmfSwBundleDnFromUnit(sdpName), prefix)
            self._add_plm_exec_env_to_smfCampaign(to_be_installed_nodes, sdpName)
            self._smfCampaign.endSwAdd()
            self._smfCampaign.addSoftwareBundleToNodes(sdpName=sdpName, nodes=to_be_installed_nodes)

    def _add_plm_exec_env_to_smfCampaign(self, nodes, sdpName):
        nodes_with_sdp = self._get_nodes_with_sdp(sdpName)
        nodes_to_generate = nodes - nodes_with_sdp
        for node in nodes_to_generate:
            node_dn = AMFTools.getNodeDnFromName(node)
            self._smfCampaign.generatePlmExecEnv(node_dn)

    def _get_nodes_with_sdp(self, sdpName):
        nodes = set()
        for camp in self._allSmfCampaigns:
            if sdpName in camp.getAddedSoftwareBundlesToNodes().keys():
                nodes.update(camp.getAddedSoftwareBundlesToNodes()[sdpName])
        return nodes

    def _is_comptype_in_used(self, comp_type_dn):
        if self._cached_in_used_comptype is None:
            self._cached_in_used_comptype = set([comp.getsaAmfCompType_unsafe()
                                                 for comp in self._migration_base.getObjects(AMFModel.SaAmfComp).values()])
        return comp_type_dn in self._cached_in_used_comptype

    def _add_dummy_migrated_component(self):
        for app_type_dn in self._migrated_app_types:
            dummy_ct_list = []
            for sg_type_dn in self._migration_base.getObject(app_type_dn).getsaAmfApptSGTypes():
                for su_type_dn in self._migration_base.getObject(sg_type_dn).getsaAmfSgtValidSuTypes():
                    for sut_comp_type_dn in self._migration_base.getObjects(AMFModel.SaAmfSutCompType, su_type_dn).keys():
                        comp_type_dn = ImmHelper.getName(sut_comp_type_dn)
                        if not self._is_comptype_in_used(comp_type_dn):
                            logging.warning('The unused comptype %s belongs to an going to be migrated application %s. '
                                            'Add it to dummy migrated list' % (comp_type_dn, app_type_dn))
                            dummy_ct_list.append(ImmHelper.getName(ImmHelper.getParentDn(comp_type_dn)))
            if dummy_ct_list:
                dummy_supersedes_info = [{CgtConstants.COMPONENT_SUPERSEDES_BASE_COMPONENT_TAG: ct}
                                         for ct in dummy_ct_list]
                if DUMMY_MIGRATED_COMPONENT_UID in self._migration_info:
                    self._migration_info[DUMMY_MIGRATED_COMPONENT_UID].extend(dummy_supersedes_info)
                else:
                    self._migration_info[DUMMY_MIGRATED_COMPONENT_UID] = dummy_supersedes_info

    def generateRollingProcedureTargetEntityTemplate(self):
        for ct in self._procedureCTInsts:
            if (ct.isToBeUpgraded() and ct.getSV() is not None):
                sv_uid = ct.getSV().getName()
                (_, _, sgDn, _, _, _, _) = self._svTargetModels[sv_uid]
                ctId = ct.getName()
                sws = self._getSDPNameFromUnit(ctId)
                for sw in sws:
                    bundleDn = AMFTools.getNodeSwBundleTemplateDnFromSDP(sw)
                    if not self._smfCampaign.skip_generate_markup_tag(bundleDn):
                        self._smfCampaign.beginTargetEntityTemplate(sgDn)
                        compRdn = ImmHelper.getRdn(AMFTools.generateCompDn(ct.getInstanceName(), "dummySu"))
                        compTypeDn = AMFTools.getCompTypeDnFromUnit(ctId, ct.getVersion())
                        self._smfCampaign.generateCompTypeUpgrade(compRdn, compTypeDn)
                        self._smfCampaign.endTargetEntityTemplate()

    def generateProcWrapup(self):
        sus = self.__su_for_existing_services_which_have_new_or_removed_comp_ins(True)
        # SGs to activate. These can be from optimizations for OICVI campaign or for node level procedures.
        sgs = set()
        """
        If we are adding new components to existing services
        we need to manually lock/unlock the SUs.
        """
        if self._procNeedsReboot() or self._proc_at_compute_resource_scope():
            """
            When the campaign requires reboot or the scope of the procedure
            is compute resource, we need to explicitly unlock the SUs that
            are created (SUs are automatically unlocked when the campaign
            acts at SU level
            """
            for sv, svInfo in self._procedureSVs.items():
                if SystemModels.service_to_be_installed(sv):
                    targetModel = self._svTargetModels[sv][0]
                    sgDn = self._svTargetModels[sv][2]
                    sg_obj = targetModel.getObject(sgDn)
                    if sg_obj.getsaAmfSGAdminState_unsafe() == AMFConstants.SA_AMF_ADMIN_LOCKED_INSTANTIATION:
                        sgs.add(sgDn)
                    else:
                        nodes = svInfo[1]
                        suDns = map(lambda node: AMFTools.generateSUDn(ImmHelper.getName(node), sgDn), nodes)
                        sus.update(suDns)

        self._lock_unlock_sis_for_service_upgrade(False)

        self.__delete_instances_in_upgrade_proc()
        for ent in list(sus) + list(sgs):
            self._smfCampaign.beginProcWrapupAction()
            self._smfCampaign.generateDoAdminOperation(ent, AMFConstants.ADMIN_UNLOCK_INSTANTIATION)
            self._smfCampaign.generateUndoAdminOperation(ent, AMFConstants.ADMIN_LOCK_INSTANTIATION)
            self._smfCampaign.endProcWrapupAction()
            self._smfCampaign.beginProcWrapupAction()
            self._smfCampaign.generateDoAdminOperation(ent, AMFConstants.ADMIN_UNLOCK)
            self._smfCampaign.generateUndoAdminOperation(ent, AMFConstants.ADMIN_LOCK)
            self._smfCampaign.endProcWrapupAction()


    def generateCommit(self):
        pass

    def generateRemoveFromImm(self):

        for appBaseTypeDn in self._app_base_type_dns:
            (_, _, removed) = self._amf_diff_calc_result.get_amf_diff_calc_result_dict_by_types(appBaseTypeDn, None, [AMFModel.SaAmfAppType])
            for amfobj in removed:
                if amfobj.getDn() not in self._deleted_objs:
                    self._deleted_objs.add(amfobj.getDn())
                    self._smfCampaign.generateAmfEntityTypeDN(amfobj.getDn())

        self._add_dummy_migrated_component()
        imm_remove_list = {}
        migrated_comp_base_types = set(self._migrated_comp_base_types)
        template_sv_compcstypes = []
        for uid, supersedes in self._migration_info.items():
            if uid == DUMMY_MIGRATED_COMPONENT_UID or uid in self._campaignCTs:
                for supersede in supersedes:
                    if CgtConstants.COMPONENT_SUPERSEDES_BASE_COMPONENT_TAG in supersede:
                        supersede_item = supersede[CgtConstants.COMPONENT_SUPERSEDES_BASE_COMPONENT_TAG]
                        if (uid != DUMMY_MIGRATED_COMPONENT_UID or
                                        u'safCompType=' + supersede_item not in migrated_comp_base_types):
                            objs = self.get_amf_related_objects(supersede_item)
                            if uid == DUMMY_MIGRATED_COMPONENT_UID:
                                template_sv_compcstypes.extend(objs.get(AMFModel.SaAmfCompCsType, []))
                            add_dict_list(imm_remove_list, objs)

        # removing template services SaCompCsType objects
        for removedDn in set(template_sv_compcstypes):
            self._smfCampaign.generateAmfEntityTypeDN(removedDn)

        # Removed components
        for dn, obj in self._amf_diff_calc_result.get_instances_removed_from_base().getObjects().items():
            dict_list_append(imm_remove_list, obj.__class__, dn)

        if imm_remove_list:
            unique_dict_list(imm_remove_list)
            self.validate_duplicated_base_type(imm_remove_list)

            for su_dn, comp_dns  in self._suDict.items():
                if comp_dns:
                    tcg_error('all components of su<%s> should be removed' %su_dn)

            remaining_dns = {}
            for sg_dn, su_dns  in self._sgDict.items():
                if su_dns:
                    sg_type_dn = self._migration_base.getObject(sg_dn).getsaAmfSGType()
                    dict_list_append(remaining_dns, AMFModel.SaAmfSGType, sg_type_dn)
                    dict_list_append(remaining_dns, AMFModel.SaAmfSGBaseType, ImmHelper.getParentDn(sg_type_dn))

            for app_dn, sg_dns  in self._appDict.items():
                if sg_dns:
                    app_type_dn = self._migration_base.getObject(app_dn).getsaAmfAppType()
                    dict_list_append(remaining_dns, AMFModel.SaAmfAppType, app_type_dn)
                    dict_list_append(remaining_dns, AMFModel.SaAmfAppBaseType, ImmHelper.getParentDn(app_type_dn))

            unique_dict_list(remaining_dns)
            remove_dict_list(imm_remove_list, remaining_dns)

            removeTypeOrder = [
                AMFModel.SaAmfHealthcheckType,
                AMFModel.SaAmfCtCsType,
                AMFModel.SaAmfSutCompType,
                AMFModel.SaAmfSvcTypeCSTypes,
                AMFModel.SaAmfCompType,
                AMFModel.SaAmfCompBaseType,
                AMFModel.SaAmfCSType,
                AMFModel.SaAmfCSBaseType,
                AMFModel.SaAmfSvcType,
                AMFModel.SaAmfSvcBaseType,
                AMFModel.SaAmfSUType,
                AMFModel.SaAmfSUBaseType,
                AMFModel.SaAmfSGType,
                AMFModel.SaAmfSGBaseType,
                AMFModel.SaAmfAppType,
                AMFModel.SaAmfAppBaseType
            ]
            for removeType in removeTypeOrder:
                for removedDn in get_list_by_key(imm_remove_list, removeType):
                    if removedDn not in self._deleted_objs:
                        self._deleted_objs.add(removedDn)
                        self._smfCampaign.generateAmfEntityTypeDN(removedDn)

    def generatePostCampaign(self):
        pass

    def endCampaign(self):
        self._smfCampaign = None
        self._campaignCTs = None
        self._siteSpecificAMFModelChanges = False
        self._mergedRolling = False
        self._isFirstProc = False


    def startCampaign(self, procedures, campaignName, smfCampaign, campaignDirectory):
        self._campaignCount += 1
        self._campaignName = campaignName
        self._smfCampaign = smfCampaign

        # Keeps track off all the campaigns generated. One CSM model can lead to
        # several smf campaigns
        self._allSmfCampaigns.append(smfCampaign)

        self._campaignCTs = {}
        self._campaignSVs = {}
        self._procedureCTs = {}
        self._procedureCTInsts = {}
        self._procedureSVs = {}
        self._campaignDirectory = campaignDirectory

        for proc in procedures:
            self.collectCTsAndSVsFromProcedure(proc, self._campaignSVs, self._campaignCTs)

    def startProcedure(self, procedure):
        self._procedureType = procedure.getType()
        self._procedureCTs = {}
        self._procedureCTInsts = {}
        self._procedureSVs = {}
        self.collectDCCTsAndSVsFromProcedure(procedure)

    def getCampaignSVs(self):
        return self._campaignSVs

    def getCampaignCTs(self):
        return self._campaignCTs

    def getSDPsInCampaign(self):
        #Original code:
        """
        SDPNames = []
        for key, CT in self._campaignCTs.items():
            for sw, bundle in self._softwares_in_component(CT.getUid()):
                SDPNames.append((sw, bundle))
        return SDPNames
        """
        #Workaround for unnecessary cmw-model-modify, need to be removed, after component adaptations
        SDPNames = []
        for key, CT in self._campaignCTs.items():
            if CT is None:
                continue
            for sw, bundle in self._softwares_in_component(CT.getUid()):
                SDPNames.append((CT.getUid(), sw, bundle))
        return SDPNames

    def getProcedureSVs(self):
        return self._procedureSVs

    def getProcedureCTs(self):
        return self._procedureCTs

    def _softwares_in_component(self, unitId, isTarget=True):
        csmModel = SystemModels.targetCSMModel if isTarget else SystemModels.baseCSMModel
        for comp in csmModel.system.getComponents():
            if comp.getUid() == unitId:
                for filename, sw_bundle in comp.software_bundle_names(self._online_adapter):
                    yield filename, sw_bundle

    def _getSDPNameFromUnit(self, unitId, isTarget=True):
        sws = []
        for filename, bundle in self._softwares_in_component(unitId, isTarget):
            sws.append(bundle)
        return sws

    def collectCTsAndSVsFromProcedure(self, proc, svs, cts):
        for (node, entities) in proc.getResult().items():
            for entity in entities:
                if entity.getPlugin() != self:
                    continue
                entityName = entity.getName()
                if type(entity) == type(DependencyCalculator.CT("", "", set(),[])):
                    if entityName not in cts.keys():
                        cts[entityName] = SystemModels.targetCSMModel.getComponent(entityName)
                # Need to check if service can be changed this way as well
                elif type(entity) == type(DependencyCalculator.SV("", "", [])):
                    if entityName not in svs.keys():
                        svs[entityName] = SystemModels.targetCSMModel.getService(entityName)
                else:
                    assert(0)

    #the same function were called for both proc CTs and camp CTs but
    #proc CTs actually using dep calc attributes, like nodes
    def collectDCCTsAndSVsFromProcedure(self, proc):
        for (node, entities) in proc.getResult().items():
            for entity in entities:
                if entity.getPlugin() != self:
                    continue
                entityName = entity.getName()
                if type(entity) == DependencyCalculator.CT:
                    if entity not in self._procedureCTInsts.keys():
                        self._procedureCTInsts[entity] = set()
                    self._procedureCTInsts[entity].add(node)
                    if entityName not in self._procedureCTs.keys():
                        if entity.isToBeRemoved():
                            comp = SystemModels.baseCSMModel.getComponent(entityName)
                        else:
                            comp = SystemModels.targetCSMModel.getComponent(entityName)
                        assert(comp)
                        self._procedureCTs[entityName] = (comp.getName(), entity, set())
                    self._procedureCTs[entityName][2].add(node)
                elif type(entity) == DependencyCalculator.SV:
                    #Actually it seems that we only need the id here,
                    #and not the nodes
                    if entityName not in self._procedureSVs.keys():
                        self._procedureSVs[entityName] = (entity, set())
                    self._procedureSVs[entityName][1].add(node)
                else:
                    assert(0)

    def addTypes(self):
        if not self._typesWritten:
            self._typesWritten = True

            entitychanges = []
            for appBaseTypeDn in self._app_base_type_dns:
                (added, _, _) = self._amf_diff_calc_result.get_amf_diff_calc_result_dict_by_types(appBaseTypeDn, None, [AMFModel.SaAmfAppType])
                entitychanges.extend(added)

            genenerateAmfEntityTypeSection(self, self._smfCampaign, entitychanges, self._svTargetModels)

    def generateCampInitActions(self, phase, campaignDirectory = None, mergeableCampaignName = None):

        if phase == SMFConstants.CAMP_INIT_PHASE_CAMP_INIT_ACTION:
            # The following objects are bindings between components and services.
            # They have to be introduced separately if a new component is added
            # to an existing service.
            self._add_saAmf_comp_services_bindings_to_smfCampaign()

            if self._campaignCount == 2:
                # update apps
                self._update_immccb_apps_in_smfCampaign()

    def _add_saAmf_comp_services_bindings_to_smfCampaign(self):
       solo_svc_type_cs_types_list = self._get_svc_type_cs_types_list()
       solo_sut_comp_type_list = self._get_sut_comp_type_list()

       entities = (solo_sut_comp_type_list + solo_svc_type_cs_types_list)
       if entities:
           self._add_camp_init_immccb_to_smfCampaign(entities,
                                                     self._create_object_in_campaign)

    def _update_immccb_apps_in_smfCampaign(self):
        for appBaseTypeDn in self._app_base_type_dns:
            (_, updated, _) = self._amf_diff_calc_result.get_amf_diff_calc_result_dict_by_types(appBaseTypeDn, None, [AMFModel.SaAmfAppType])
            for dn, update_tuple in updated.items():
                app = self._targetAmfModel.getObject(dn)
                self._update_immccb_app_attr_in_smfCampaign(app, update_tuple)

    def _update_immccb_app_attr_in_smfCampaign(self, objects, update_tuple):
        def update_obj_attributes(obj):
            self._smfCampaign.generateModifyObject(obj.getDn(), [update_tuple])

        if not self.generate_instantiation_campaign:
            self._add_camp_init_immccb_to_smfCampaign(objects, update_obj_attributes)

    def _add_camp_init_immccb_to_smfCampaign(self, objects, func_to_add_object):
        if not self.generate_instantiation_campaign:
            self._smfCampaign.beginCampInitAction()
            self._smfCampaign.beginImmCCB()
            for obj in objects:
                func_to_add_object(obj)
            self._smfCampaign.endImmCCB()
            self._smfCampaign.endCampInitAction()

    def _get_svc_type_cs_types_list(self):
        svc_type_cs_types_list = []
        for (svId, (targetModel, _, _, added, _, _, unchanged)) in self._svTargetModels.items():
            for (svcTypeDn, svcType) in targetModel.getObjects(AMFModel.SaAmfSvcType).items():
                if svcTypeDn in unchanged:
                    for (svcTypeCSTypesDn, svcTypeCSTypes) in targetModel.getObjects(AMFModel.SaAmfSvcTypeCSTypes, svcTypeDn).items():
                        if svcTypeCSTypesDn in added:
                            svc_type_cs_types_list.append(svcTypeCSTypes)
        return svc_type_cs_types_list

    def _get_sut_comp_type_list(self):
        sut_comp_type_list = []
        for (svId, (targetModel, _, _, added, _, _, unchanged)) in self._svTargetModels.items():
            for (suTypeDn, suType) in targetModel.getObjects(AMFModel.SaAmfSUType).items():
                if suTypeDn in unchanged:
                    for (sutCompTypeDn, sutCompType) in targetModel.getObjects(AMFModel.SaAmfSutCompType, suTypeDn).items():
                        if sutCompTypeDn in added:
                            sut_comp_type_list.append(sutCompType)
        return sut_comp_type_list

    def init(self, targetAmfModel, baseAmfModel,
             ctsTobeInstalled, predefCoremwPGs, nonAMFCTChanges, migration_base, amf_diff_calc_result):

        self._targetAmfModel = targetAmfModel
        self._baseAmfModel = baseAmfModel
        self._ctsTobeInstalled = ctsTobeInstalled
        self._predefCoremwPGs = predefCoremwPGs
        self._nonAMFCTChanges = nonAMFCTChanges
        self._migration_base = migration_base
        self._amf_diff_calc_result = amf_diff_calc_result

        if (amf_diff_calc_result): #this 'if' is only here for unit test purposes where value is 'None'
            self._svTargetModels = self._amf_diff_calc_result.get_sv_target_models()
            self._app_base_type_dns = self._amf_diff_calc_result.get_app_base_type_dns()

        if self._migration_info:
            self.validate_migration()

    def validate_duplicated_base_type(self, imm_remove_list):
        imm_remove_set = set()
        map(imm_remove_set.update, imm_remove_list.values())
        for _, _, _, added, _, _, _ in self._svTargetModels.values():
            inter = imm_remove_set.intersection(set(added))
            if len(inter):
                tcg_error('%s are in superseded type entities' % ', '.join(inter))

    def setMergedAndFirst(self):
        self._mergedRolling = True
        self._isFirstProc = True

    def addSwRemove(self, rem_dict, ctId, nodes, force_remove=False):
        def generateSwRemove(sw, nodes, macroBundle, ctId):
            bundleDnMacro = getCmwGetUsedBundleDnMacro(self._baseAmfModel, macroBundle)
            if bundleDnMacro:
                rem_dict[bundleDnMacro] = rem_dict.get(bundleDnMacro, set()) | nodes
            self._smfCampaign.addRemovedBundle(sw, nodes)

        def isSwToBeUpgradedOrRemoved(ctId):
            for ct in self._procedureCTInsts:
                if ct.getName() == ctId and (ct.isSwToBeUpgraded() or ct.isToBeRemoved()):  # FIXME: define and use isSwToBeRemoved()
                    return True
            return False
        isUpgradedOrRemoved = isSwToBeUpgradedOrRemoved(ctId)
        if isUpgradedOrRemoved or force_remove:
            sws = self._getSDPNameFromUnit(ctId, False)
        else:
            sw_type = SystemModels.targetCSMModel.getComponent(ctId).get_software_type()
            cut_off_parts = 2
            if sw_type == "rpms":
                cut_off_parts = 3
            sws = self._getSDPNameFromUnit(ctId)

        for sw in sws:
            if (sw not in self._smfCampaign.getRemovedBundles().keys()) or \
                    (not (self._smfCampaign.getRemovedBundles()[sw] & nodes)):
                if isUpgradedOrRemoved or force_remove:
                    generateSwRemove(sw, nodes, sw, ctId)
                else:
                    bundleDn = AMFTools.getNodeSwBundleTemplateDnFromSDP(sw)
                    if not self._smfCampaign.skip_generate_markup_tag(bundleDn):
                        splitBundle = sw.rsplit("-", cut_off_parts)
                        macroBundle = splitBundle[0] + "-" + _stripProductNumberRevision(splitBundle[1])
                        generateSwRemove(sw, nodes, macroBundle, ctId)

    def get_amf_objects_with_name(self, _class, name):
        res = []
        for dn in self._migration_base.getObjects(_class):
            if ImmHelper.getName(dn) == name:
                res.append(dn)
        return res

    def get_amf_objects_with_name_pattern(self, _class, pattern, model = None):
        if model == None:
            model = self._migration_base
        res = []
        pat = re.compile(pattern)
        for dn in model.getObjects(_class):
            if pat.match(ImmHelper.getName(dn)):
                res.append(dn)
        return res

    def get_amf_objects_with_attribute(self, _class, attr_name, attr_value):
        res = []
        for dn in self._migration_base.getObjects(_class):
            obj = self._migration_base.getObject(dn)
            attr_getter = getattr(obj, 'get' + attr_name)
            if attr_getter() == attr_value:
                res.append(dn)
        return res

    def get_amf_related_objects(self, comp_base_type_name):
        if comp_base_type_name in self._cached_related_objects:
            return copy.deepcopy(self._cached_related_objects[comp_base_type_name])

        objs = {}

        # SaAmfCompBaseType
        # check if comp base type exists
        comp_base_type = u"safCompType=" + comp_base_type_name
        if comp_base_type not in self._migration_base.getObjects():
            return {}

        dict_list_append(objs, AMFModel.SaAmfCompBaseType, comp_base_type)
        self._migrated_comp_base_types.add(comp_base_type)
        # SaAmfCompType
        comp_type_dns = self._migration_base.getObjects(AMFModel.SaAmfCompType, comp_base_type).keys()
        dict_list_extend(objs, AMFModel.SaAmfCompType, comp_type_dns)
        for comp_type_dn in comp_type_dns:
            comp_type_obj = self._migration_base.getObject(comp_type_dn)
            # SaSmfSwBundle
            swBundle = comp_type_obj.getsaAmfCtSwBundle_unsafe()
            if swBundle:
                dict_list_append(objs, AMFModel.SaSmfSwBundle, swBundle)

            # SaAmfHealthcheckType
            health_check_type_dns = self._migration_base.getObjects(AMFModel.SaAmfHealthcheckType, comp_type_dn).keys()
            dict_list_extend(objs, AMFModel.SaAmfHealthcheckType, health_check_type_dns)

            # SaAmfCtCsType
            ct_cs_type_dns = self._migration_base.getObjects(AMFModel.SaAmfCtCsType, comp_type_dn).keys()
            dict_list_extend(objs, AMFModel.SaAmfCtCsType, ct_cs_type_dns)
            for ct_cs_type_dn in ct_cs_type_dns:
                # SaAmfCSType, SaAmfCSBaseType
                cs_type_dn = ImmHelper.getName(ct_cs_type_dn)
                self.dict_list_append_type_basetype(objs, AMFModel.SaAmfCSType, AMFModel.SaAmfCSBaseType, cs_type_dn)
                # SaAmfSvcTypeCSTypes
                svc_type_cs_type_dns = self.get_amf_objects_with_name(AMFModel.SaAmfSvcTypeCSTypes, cs_type_dn)
                dict_list_extend(objs, AMFModel.SaAmfSvcTypeCSTypes, svc_type_cs_type_dns)
                for svc_type_cs_type_dn in svc_type_cs_type_dns:
                    # SaAmfSvcType, SaAmfSvcBaseType
                    svc_type_dn = ImmHelper.getParentDn(svc_type_cs_type_dn)
                    self.dict_list_append_type_basetype(objs, AMFModel.SaAmfSvcType, AMFModel.SaAmfSvcBaseType, svc_type_dn)

                # SaAmfCompCsType
                comp_cs_type_dns = self.get_amf_objects_with_name(AMFModel.SaAmfCompCsType, cs_type_dn)
                dict_list_extend(objs, AMFModel.SaAmfCompCsType, comp_cs_type_dns)
                su_dns = []
                for comp_cs_type_dn in comp_cs_type_dns:
                    # SaAmfComp
                    comp_dn = ImmHelper.getParentDn(comp_cs_type_dn)
                    dict_list_append(objs, AMFModel.SaAmfComp, comp_dn)

                    # SaAmfHealthcheck
                    health_check_dns = self._migration_base.getObjects(AMFModel.SaAmfHealthcheck, comp_dn).keys()
                    dict_list_extend(objs, AMFModel.SaAmfHealthcheck, health_check_dns)

                    # SaAmfSU
                    su_dns.append(ImmHelper.getParentDn(comp_dn))
                su_dns = list(set(su_dns))
                dict_list_extend(objs, AMFModel.SaAmfSU, su_dns)

                # SaAmfSG
                sg_dns = []
                for su_dn in su_dns:
                    sg_dns.append(ImmHelper.getParentDn(su_dn))
                sg_dns = list(set(sg_dns))
                dict_list_extend(objs, AMFModel.SaAmfSG, sg_dns)

                application_dns = []
                for sg_dn in sg_dns:
                    # SaAmfSGType, SaAmfSGBaseType
                    sg_obj = self._migration_base.getObject(sg_dn)
                    sg_type_dn = sg_obj.getsaAmfSGType()
                    self.dict_list_append_type_basetype(objs, AMFModel.SaAmfSGType, AMFModel.SaAmfSGBaseType, sg_type_dn)
                    # SaAmfApplication
                    application_dns.append(ImmHelper.getParentDn(sg_dn))
                application_dns = list(set(application_dns))
                dict_list_extend(objs, AMFModel.SaAmfApplication, application_dns)

                for application_dn in application_dns:
                    # SaAmfAppType, SaAmfAppBaseType
                    application_obj = self._migration_base.getObject(application_dn)
                    app_type_dn = application_obj.getsaAmfAppType()
                    self._migrated_app_types.add(app_type_dn)
                    self.dict_list_append_type_basetype(objs, AMFModel.SaAmfAppType, AMFModel.SaAmfAppBaseType, app_type_dn)

                # SaAmfCSI
                csi_dns = self.get_amf_objects_with_attribute(AMFModel.SaAmfCSI, 'saAmfCSType', cs_type_dn)
                dict_list_extend(objs, AMFModel.SaAmfCSI, csi_dns)
                for csi_dn in csi_dns:
                    # SaAmfCSIAttribute
                    csi_attribute_dns = self._migration_base.getObjects(AMFModel.SaAmfCSIAttribute, csi_dn).keys()
                    dict_list_extend(objs, AMFModel.SaAmfCSIAttribute, csi_attribute_dns)
                    # SaAmfSI
                    si_dn = ImmHelper.getParentDn(csi_dn)
                    dict_list_append(objs, AMFModel.SaAmfSI, si_dn)
                    # SaAmfSIDependency
                    si_dependency_dns = self.get_amf_objects_with_name(AMFModel.SaAmfSIDependency, si_dn)
                    dict_list_extend(objs, AMFModel.SaAmfSIDependency, si_dependency_dns)
                    # SaAmfSIRankedSU
                    si_ranked_su_dns = self._migration_base.getObjects(AMFModel.SaAmfSIRankedSU, si_dn).keys()
                    dict_list_extend(objs, AMFModel.SaAmfSIRankedSU, si_ranked_su_dns)

            # SaAmfSutCompType
            sut_comp_type_dns = self.get_amf_objects_with_name(AMFModel.SaAmfSutCompType, comp_type_dn)
            dict_list_extend(objs, AMFModel.SaAmfSutCompType, sut_comp_type_dns)
            for sut_comp_type_dn in sut_comp_type_dns:
                # SaAmfSUType, SaAmfSUBaseType
                sut_type_dn = ImmHelper.getParentDn(sut_comp_type_dn)
                self.dict_list_append_type_basetype(objs, AMFModel.SaAmfSUType, AMFModel.SaAmfSUBaseType, sut_type_dn)
        self._cached_related_objects[comp_base_type_name] = objs
        return copy.deepcopy(objs)

    @staticmethod
    def dict_list_append_type_basetype(dict_list, type_, basetype, dn):
        dict_list_append(dict_list, type_, dn)
        dict_list_append(dict_list, basetype, ImmHelper.getParentDn(dn))

    def validate_migration(self):

        amf_remove_objects = {}
        for supersedes in self._migration_info.values():
            for supersede in supersedes:
                if CgtConstants.COMPONENT_SUPERSEDES_BASE_COMPONENT_TAG in supersede:
                    base_comp_type_name = supersede[CgtConstants.COMPONENT_SUPERSEDES_BASE_COMPONENT_TAG]
                    objs = self.get_amf_related_objects(base_comp_type_name)
                    add_dict_list(amf_remove_objects, objs)

        # Validate all comps of su should be included in removing list
        sus = get_list_by_key(amf_remove_objects, AMFModel.SaAmfSU)
        comps_to_remove = set(get_list_by_key(amf_remove_objects, AMFModel.SaAmfComp))
        for su in sus:
            comps = set(self._migration_base.getObjects(AMFModel.SaAmfComp, su))
            if not comps_to_remove.issuperset(comps):
                tcg_error('all comps of su<%s> should be included in removing list' % su)

        # Validate partially migration
        bundles_to_be_removed = set(get_list_by_key(amf_remove_objects, AMFModel.SaSmfSwBundle))
        compTypes_to_be_removed = set(get_list_by_key(amf_remove_objects, AMFModel.SaAmfCompType))
        for compTypeDn, compTypeObj in self._migration_base.getObjects(AMFModel.SaAmfCompType).iteritems():
            swBundle = compTypeObj.getsaAmfCtSwBundle_unsafe()
            if not swBundle:
                logging.debug('compType<%s> does not refer to any bundle' % compTypeDn)
                continue
            if (swBundle in bundles_to_be_removed and self._is_comptype_in_used(compTypeDn)
                    and compTypeDn not in compTypes_to_be_removed):
                tcg_error('compType<%s> (reference to safSmfBundle<%s>) is not marked to be migrated' % (compTypeDn, swBundle))

    def calc_su_related(self, object_dict, su_dns):
        for su_dn in su_dns:
            si_dns = self.get_amf_objects_with_name(AMFModel.SaAmfSIAssignment, su_dn)
            for si_dn in si_dns:
                # SaAmfSIDependency
                si_dependency_dns = self.get_amf_objects_with_name(AMFModel.SaAmfSIDependency, si_dn)
                remove_dict_list(object_dict, {AMFModel.SaAmfSIDependency: si_dependency_dns})
                # SaAmfSIRankedSU
                si_ranked_su_dns = self._migration_base.getObjects(AMFModel.SaAmfSIRankedSU, si_dn).keys()
                remove_dict_list(object_dict, {AMFModel.SaAmfSIRankedSU: si_ranked_su_dns})
            # SaAmfSI
            remove_dict_list(object_dict, {AMFModel.SaAmfSI: si_dns})

    @staticmethod
    def _get_old_SuAdminState(self, su_obj, targetModel):
        # Migration should keep SU admin state
        # Idea: SU (get hosted node) -> comp -> old comp -> old SU (get admin state if same hosted node)
        hosted_node = su_obj.getsaAmfSUHostNodeOrNodeGroup()
        for sutCompType in targetModel.getObjects(AMFModel.SaAmfSutCompType,su_obj.getsaAmfSUType()).values():
            comp = AMFTools.getUnitIdFromModelName(ImmHelper.getParentDn(sutCompType.getCompType()))
            if not self._migration_info.has_key(comp) or len(self._migration_info[comp]) > 1:
                #Return None
                ##in case of comp is not for migration
                ##in case of migration: many old SUs -> 1 csm SU: still set UNLOCKED
                return None
            supersede = self._migration_info[comp][0]
            if CgtConstants.COMPONENT_SUPERSEDES_BASE_COMPONENT_TAG in supersede:
                old_comp_type = supersede[CgtConstants.COMPONENT_SUPERSEDES_BASE_COMPONENT_TAG]
                objs = self.get_amf_related_objects(old_comp_type)
                for old_su_dn in objs.get(AMFModel.SaAmfSU, []):
                    old_su_obj = self._migration_base.getObject(old_su_dn)
                    old_hosted_node = old_su_obj.getsaAmfSUHostNodeOrNodeGroup()
                    if old_hosted_node == hosted_node:
                        old_state = old_su_obj.getsaAmfSUAdminState()
                        logging.warn("Old SU:%s state:%s"%(old_su_dn,old_state))
                        return old_state
        return None

    @staticmethod
    def _optimize_activation(self, targetModel):
        for dn, obj in targetModel.getObjects().iteritems():
            if isinstance(obj, AMFModel.SaAmfSU):
                old_state = self._get_old_SuAdminState(self,obj,targetModel)
                if old_state is not None:
                    logging.warn("Set old state:%s for new SU:%s"%(old_state,obj.getDn()))
                    targetModel.getObject(obj.getDn()).setsaAmfSUAdminState(old_state)
                    continue
                targetModel.getObject(dn).setsaAmfSUAdminState(AMFConstants.SA_AMF_ADMIN_UNLOCKED)
            elif isinstance(obj, AMFModel.SaAmfSG):
                targetModel.getObject(dn).setsaAmfSGAdminState(AMFConstants.SA_AMF_ADMIN_LOCKED_INSTANTIATION)


def _stripProductNumberRevision(inputStr):
    """
    We strip the revision part of a product number.
    Example: CXC1736038_9 -> CXC1736038
    Example: CXC1736038 -> CXC1736038
    """
    splitInput = inputStr.rsplit("_", 2)  # separator="_", maxSplit=2
    return splitInput[0]

def genenerateAmfEntityTypeSection(plugin, smfCampaign, appTypeList, svTargetModels):
    sgTypeList = []
    suTypeList = []
    compTypeList = []
    csTypeList = []
    svcTypeList = []


    # add SGBaseType
    for (svId, (targetModel, _, _, added, _, _, _)) in svTargetModels.items():
        for (sgTypeDn, sgType) in targetModel.getObjects(AMFModel.SaAmfSGType).items():
            if sgTypeDn in added:
                sgTypeList.append(sgType)

    # add SUBaseType
    for (svId, (targetModel, _, _, added, _, _, _)) in svTargetModels.items():
        for (suTypeDn, suType) in targetModel.getObjects(AMFModel.SaAmfSUType).items():
            if suTypeDn in added:
                suTypeList.append((suType, targetModel.getObjects(AMFModel.SaAmfSutCompType, suTypeDn).values()))

    # add CompBaseType
    required_comp_types = {}
    already_installed_comp_types = set()
    for (svId, (targetModel, _, _, added, _, _, unchanged)) in svTargetModels.items():
        for (compTypeDn, compType) in targetModel.getObjects(AMFModel.SaAmfCompType).items():
            if compTypeDn in unchanged:
                already_installed_comp_types.add(compTypeDn)
                if compTypeDn in required_comp_types:
                    del required_comp_types[compTypeDn]
                continue
            if compTypeDn in added and compTypeDn not in already_installed_comp_types:
                required_comp_types[compTypeDn] = (compType, targetModel.getObjects(AMFModel.SaAmfCtCsType, compTypeDn).values(),
                                                   targetModel.getObjects(AMFModel.SaAmfHealthcheckType, compTypeDn).values())

    for (compTypeDn, compTypeData) in required_comp_types.items():
        if compTypeData not in compTypeList :
            compTypeList.append(compTypeData)

    # add CSBaseType
    required_cs_types = {}
    already_installed_cs_types = set()
    for (svId, (targetModel, _, _, added, updated, _, unchanged)) in svTargetModels.items():
        for (csTypeDn, csType) in targetModel.getObjects(AMFModel.SaAmfCSType).items():
            if csTypeDn in unchanged or csTypeDn in updated:
                already_installed_cs_types.add(csTypeDn)
                if csTypeDn in required_cs_types:
                    del required_cs_types[csTypeDn]
                continue
            if (csTypeDn in added) and (csTypeDn not in already_installed_cs_types):
                required_cs_types[csTypeDn] = csType
    for (csTypeDn, csType) in required_cs_types.items():
            csTypeList.append(csType)

    # add ServiceBaseType
    for (svId, (targetModel, _, _, added, _, _, _)) in svTargetModels.items():
        for (svcTypeDn, svcType) in targetModel.getObjects(AMFModel.SaAmfSvcType).items():
            if svcTypeDn in added:
                svcTypeList.append((svcType, targetModel.getObjects(AMFModel.SaAmfSvcTypeCSTypes, svcTypeDn).values()))


    if len(appTypeList) == 0 and len(sgTypeList) == 0 and len(suTypeList) == 0 and len(compTypeList) == 0 and len(csTypeList) == 0 and \
       len(svcTypeList) == 0:
        return

    smfCampaign.beginAmfEntityTypes()

    for app in appTypeList:
        smfCampaign.generateAppBaseType(app)
    for sg in sgTypeList:
        smfCampaign.generateSGBaseType(sg)
    for (su, sutcomp) in suTypeList:
        smfCampaign.generateSUBaseType(su, sutcomp)
    for (ct, ctcs, hct) in compTypeList:
        smfCampaign.generateCompBaseType(ct, ctcs, hct)
    for cst in csTypeList:
        smfCampaign.generateCSBaseType(cst)
    for (svct, svccst) in svcTypeList:
        smfCampaign.generateServiceBaseType(svct, svccst)
    smfCampaign.endAmfEntityTypes()


def getCmwGetUsedBundleDnMacro(baseAmfModel, s):
    bundleTemplateDn = AMFTools.getNodeSwBundleTemplateDnFromSDP(s)
    prog = re.compile(bundleTemplateDn)
    for bundle in baseAmfModel.getObjects(AMFModel.SaAmfNodeSwBundle).keys():
        if prog.match(bundle):
            return ImmHelper.getName(bundle)
    logging.info("Could not find installed bundle for %s" % s)
    return None

def dict_list_append(d, key, value):
    if key in d:
        d[key].append(value)
    else:
        d[key] = [value]

def dict_list_extend(d, key, sub_list):
    if key in d:
        d[key].extend(sub_list)
    else:
        d[key] = sub_list


def add_dict_list(dict_dest, dict_to_add):
    for key in dict_to_add:
        if key in dict_dest:
            dict_dest[key].extend(dict_to_add[key])
        else:
            dict_dest[key] = dict_to_add[key]

def remove_dict_list(dict_dest, dict_to_remove):
    for key in dict_to_remove:
        if key in dict_dest:
            dict_dest[key] = list(set(dict_dest[key]) - set(dict_to_remove[key]))

def unique_dict_list(the_dict):
    for key in the_dict:
        the_dict[key] = list(set(the_dict[key]))


def calc_remove_children(children, parents, parents_dict):
    """
    parent object will not be removed if all children are removed
    @param children:
    @param parents:
    @param parents_dict:
    @return:
    """
    remaining_objects = []
    for parent in parents_dict:
        for child in children:
            if child in parents_dict[parent]:
                parents_dict[parent].remove(child)
        if parents_dict[parent] and parent in parents:
            parents.remove(parent)
            remaining_objects.append(parent)
    return remaining_objects


def get_list_by_key(d, key):
    if not key in d:
        return []
    return d[key]


