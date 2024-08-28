import logging
from utils.logger_tcg import tcg_error
from common import printNice
import AMFModel
import AMFTools
import ImmHelper
import itertools
import AMFConstants
from SystemModels import SystemModels

class AMFModelDiffCalcResult(object):
    '''
    This class contains the results of the diff calculation from AMFModelDiffCalculator
    '''
    def __init__(self, base_amf_model, target_amf_model, merged_app_base_type_dns):
        self._amf_diff_calc_result_dict = {}
        self._sv_target_models = {}
        self._app_base_type_dns = set()
        self._svid_to_sgdn = {}
        self._target_amf_model = target_amf_model
        self._base_amf_model = base_amf_model
        self._instances_removed_from_base = {}
        self._bundles_removed_from_base = set()
        AMFModelDiffCalculator(base_amf_model, target_amf_model, merged_app_base_type_dns, self)

    def add_svid_sgdn_dict(self, svid, sgdn):
        '''
        in different places services are referred to by their id's as found in the yml files (Dependency Calculator)
        and in other places by their SG domain names.
        The service is always added by use of the SG domain name, but this dict allows the dict to be accessed by svid as well
        '''
        if svid is None:
            svid = sgdn
        if svid not in self._svid_to_sgdn.keys():
            self._svid_to_sgdn[svid] = sgdn

    def get_amf_diff_calc_result_dict(self, svid, compid = None):

        if not svid in self._svid_to_sgdn.keys():
            return None

        sgdn = self._svid_to_sgdn[svid]
        tuple_key = (sgdn,compid)
        if tuple_key not in self._amf_diff_calc_result_dict.keys():
            return None
        return self._amf_diff_calc_result_dict[tuple_key]

    def get_amf_diff_calc_result_dict_by_types(self, svid, compid = None, obj_types_order = []):

        amf_diff_dict = self.get_amf_diff_calc_result_dict(svid, compid)
        if not amf_diff_dict:
            return None

        if obj_types_order == []:
            return amf_diff_dict

        def filter_list_by_type(listtofilter):
            amf_objects = []
            for t in obj_types_order:
                for amf_obj in listtofilter:
                    if(type(amf_obj) == t):
                        amf_objects.append(amf_obj)
            return amf_objects

        (added, updated, removed) = amf_diff_dict

        objupd = {}
        objadd = filter_list_by_type(added)
        objrmv = filter_list_by_type(removed)
        tmpupd = []
        tmpupd.extend([self._target_amf_model.getObject(dn) for dn in updated.keys()])
        filtered_tmpupd = filter_list_by_type(tmpupd)

        for obj in filtered_tmpupd:
           objupd[obj.getDn()] = updated[obj.getDn()]

        return (objadd, objupd, objrmv)

    def get_sgdn_by_svid(self, svid):
        if svid in self._svid_to_sgdn.keys():
            return self._svid_to_sgdn[svid]


    def add_to_amf_diff_calc_result_dict(self, sgdn, svid = None, compid = None, added = [], updated = {}, removed = []):

        resultdict = self.transform_update_dict_to_include_update_tuple_values(sgdn, updated)

        self.add_svid_sgdn_dict(svid, sgdn)
        tuple_key = (sgdn,compid)
        if tuple_key not in self._amf_diff_calc_result_dict.keys():
            self._amf_diff_calc_result_dict[tuple_key] = ([], {}, [])

        (tmpadd, tmpupd, tmprmv) = self._amf_diff_calc_result_dict[tuple_key]

        tmpadd.extend([self._target_amf_model.getObject(dn) for dn in added])
        tmprmv.extend([self._base_amf_model.getObject(dn) for dn in removed])

        tmpupd.update(resultdict)
        logging.debug("AMFModelDiffResult:add_to_amf_diff_calc_result_dict - info stored for sv %s, ct %s." % (svid, compid))

        if sgdn in self._target_amf_model.getObjects():
            obj = self._target_amf_model.getObject(sgdn)
            if type(obj) == AMFModel.SaAmfAppBaseType:
                self._app_base_type_dns.add(sgdn)

    def get_sv_target_models(self):
        return self._sv_target_models

    def get_app_base_type_dns(self):
        return self._app_base_type_dns

    def add_to_sv_target_models(self, svid, merged_target_sg_model, merged_base_sg_model, sg_dn, added, updated, removed, unchanged):
        self._sv_target_models[svid] = (merged_target_sg_model, merged_base_sg_model, sg_dn, added, updated, removed, unchanged)
        logging.debug("AMFModelDiffResult:add_to_sv_target_models - service target models stored for service %s." % (svid))

    def transform_update_dict_to_include_update_tuple_values(self, sgdn, updatedict):
        '''
        the updatedict is the result of the 'AMFModel.diff', it consists of the
        a domain name of the object as the key, and a list of the attributes that
        have been changed.
        This function constructs changes the list attributes to a list of tuples that
        will be used later in the generation of the SMFCampaign .
        '''
        tupledict = {}
        for i, att_list in updatedict.items():
            obj = self._target_amf_model.getObject(i)
            tuple_list = self._create_value_update_tuple_list(obj, att_list)
            if type(obj) == AMFModel.SaAmfSGType:
                # if the SaAmfSGType is being updated, then  modify the SaAmfSG instead
                tupledict[sgdn] = tuple_list
            else:
                tupledict[i] = tuple_list
        return tupledict

    # IF YOU UPDATE ONE OF THESE LISTS, BE SURE TO UPDATE FUNCTION _create_value_update_tuple_list
    UPDATEABLE_SERVICE_ATTRIBUTE_LIST   = [AMFModel.SaAmfSIDependency, AMFModel.SaAmfSI, AMFModel.SaAmfSG,AMFModel.SaAmfSGType]
    UPDATEABLE_COMPONENT_ATTRIBUTE_LIST = [AMFModel.SaAmfCSIAttribute]
    UPDATEABLE_COMPONENT_TYPE_ATTRIBUTE_LIST_HV88205 = [AMFModel.SaAmfCompType]

    def _create_value_update_tuple_list(self, updated_amf_obj, attribute_list):
        '''
        SmfCampaign.generateModifyObject expects a tuple for any value update.
        Package that tuple here.  Update this function as new attributes are
        introduced as updateable
        '''
        tuple_list = []
        tuple_entry = ()
        for attr in attribute_list:
            if type(updated_amf_obj) == AMFModel.SaAmfSIDependency:
                if attr == 'saAmfToleranceTime':
                    tuple_entry = (attr,"SA_IMM_ATTR_SATIMET", updated_amf_obj.getsaAmfToleranceTime_unsafe())

            elif type(updated_amf_obj) == AMFModel.SaAmfCSIAttribute:
                if attr == 'saAmfCSIAttriValue':
                    tuple_entry = (attr,"SA_IMM_ATTR_SASTRINGT", updated_amf_obj.getsaAmfCSIAttriValue_single())
            elif type(updated_amf_obj) == AMFModel.SaAmfApplication:
                if attr == 'saAmfAppType':
                    tuple_entry = (attr,"SA_IMM_ATTR_SANAMET", updated_amf_obj.getsaAmfAppType())
            elif type(updated_amf_obj) == AMFModel.SaAmfComp:
                if attr == 'saAmfCompType':
                    tuple_entry = (attr,"SA_IMM_ATTR_SANAMET", updated_amf_obj.getsaAmfCompType())
            elif type(updated_amf_obj) == AMFModel.SaAmfSI:
                if attr == 'saAmfSIPrefActiveAssignments':
                    tuple_entry = (attr,"SA_IMM_ATTR_SAUINT32T", updated_amf_obj.getsaAmfSIPrefActiveAssignments())
            elif type(updated_amf_obj) == AMFModel.SaAmfSG:
                if attr == 'saAmfSGNumPrefInserviceSUs':
                    tuple_entry = (attr,"SA_IMM_ATTR_SAUINT32T", updated_amf_obj.getsaAmfSGNumPrefInserviceSUs())
                elif attr == 'saAmfSGSuRestartProb':
                    tuple_entry = (attr,"SA_IMM_ATTR_SATIMET", updated_amf_obj.getsaAmfSGSuRestartProb())
                elif attr == 'saAmfSGSuRestartMax':
                    tuple_entry = (attr,"SA_IMM_ATTR_SAUINT32T", updated_amf_obj.getsaAmfSGSuRestartMax())
                elif attr == 'saAmfSGCompRestartProb':
                    tuple_entry = (attr,"SA_IMM_ATTR_SATIMET", updated_amf_obj.getsaAmfSGCompRestartProb())
                elif attr == 'saAmfSGCompRestartMax':
                    tuple_entry = (attr,"SA_IMM_ATTR_SAUINT32T", updated_amf_obj.getsaAmfSGCompRestartMax())
            elif type(updated_amf_obj) == AMFModel.SaAmfSGType:
                # if the SaAmfSGType is being updated, then  modify the SaAmfSG instead
                if attr == 'saAmfSgtDefSuRestartProb':
                    tuple_entry = ('saAmfSGSuRestartProb',"SA_IMM_ATTR_SATIMET", updated_amf_obj.getsaAmfSgtDefSuRestartProb())
                elif attr == 'saAmfSgtDefSuRestartMax':
                    tuple_entry = ('saAmfSGSuRestartMax',"SA_IMM_ATTR_SAUINT32T", updated_amf_obj.getsaAmfSgtDefSuRestartMax())
                elif attr == 'saAmfSgtDefCompRestartProb':
                    tuple_entry = ('saAmfSGCompRestartProb',"SA_IMM_ATTR_SATIMET", updated_amf_obj.getsaAmfSgtDefCompRestartProb())
                elif attr == 'saAmfSgtDefCompRestartMax':
                    tuple_entry = ('saAmfSGCompRestartMax',"SA_IMM_ATTR_SAUINT32T", updated_amf_obj.getsaAmfSgtDefCompRestartMax())
            elif type(updated_amf_obj) == AMFModel.SaAmfCompType:
                if attr == 'saAmfCtDefCmdEnv':
                    # Work-around for HV88205, to be fixed properly after agreement with OpenSAF
                    tuple_entry = (attr, "SA_IMM_ATTR_SASTRINGT", updated_amf_obj.getsaAmfCtDefCmdEnv())

            if tuple_entry:
                tuple_list.append(tuple_entry)
            else:
                 tcg_error("Unsupported Upgrade Use Case: unhandled attribute change of AMF obj %s of type %s, attribute %s."\
                     % (updated_amf_obj.getDn(), type(updated_amf_obj), attribute_list))

        return tuple_list

    def get_instances_removed_from_base(self, sv=None):
        if sv is None:
            ret = AMFModel.AMFModel()
            for model in self._instances_removed_from_base.values():
                ret._objects.update(model._objects)
            return ret
        app_base_type_dn = AMFTools.generateAppBaseTypeDn(sv)
        if app_base_type_dn not in self._instances_removed_from_base:
            return AMFModel.AMFModel()
        return self._instances_removed_from_base[app_base_type_dn]

    def get_bundles_removed_from_base(self):
        return self._bundles_removed_from_base


class AMFModelSVAndCTDiffCalculator(object):

    def __init__(self,  amf_diff_calc_result):

        self._amf_diff_calc_result = amf_diff_calc_result

        self._base_amf_model = None
        self._base_sg_models = {}
        self._base_sg_comp_models = {}
        self._base_sg_comp_bindings = {}
        self._base_sg_model = None
        self._base_sg_comp_bindings = {}
        self._base_sg_comp_binding = {}
        self._base_sg_comp_model = {}
        self._merged_base_comp_model = None

        self._target_amf_model = None
        self._target_sg_models = {}
        self._target_sg_comp_models = {}
        self._target_sg_comp_bindings = {}
        self._target_sg_model = None
        self._target_sg_comp_bindings = {}
        self._target_sg_comp_binding = None
        self._target_sg_comp_model = None
        self._merged_target_comp_model = None

        self._sg_dn = None
        self._sv_id = None
        self._comp_id = None
        self._binding_add_list = []

    @staticmethod
    def dumpChange(sgDn, added, updated, removed, unchanged):
        logging.error("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
        logging.error("Sg: " + sgDn)
        logging.error("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++\n")

        logging.error("=========================================================================\n")
        logging.error("ADDED:\n")
        printNice(added, logging_type=logging.error)
        logging.error("=========================================================================\n")
        logging.error("UPDATED:\n")
        printNice(updated, logging_type=logging.error)
        logging.error("=========================================================================\n")
        logging.error("REMOVED:\n")
        printNice(removed, logging_type=logging.error)
        logging.error("=========================================================================\n")
        logging.error("UNCHANGED:\n")
        printNice(unchanged, logging_type=logging.error)

    @staticmethod
    def filterObjectTypes(objectTypes, dnList, model, objects={}, strictMode=True):
        for type_ in objectTypes:
            objects[type_] = []

        for dn in dnList:
            object = model.getObject(dn)
            if type(object) not in objectTypes :
                if strictMode:
                    return False
            else:
                objects[type(object)].append(object)
        return True

    @staticmethod
    def mergeSgModels(sg_model, comp_models, bindings):
        merged_model = AMFModel.AMFModel()
        for obj_dn in sg_model.getObjects():
            merged_model.addObject(sg_model.getObject(obj_dn))
        for (_, comp_model) in comp_models.items():
            for obj_dn in comp_model.getObjects():
                merged_model.addObject(comp_model.getObject(obj_dn))
        for (_, comp_bindings) in bindings.items():
            for obj_dn in comp_bindings.getObjects():
                merged_model.addObject(comp_bindings.getObject(obj_dn))
        return merged_model

    @staticmethod
    def print_diff_result(msg ,added, updated, removed, unchanged):
        return
        logging.debug(" %s" % msg)
        logging.debug("  added:")
        for added_e in added:
            logging.debug("    %s" % added_e)
        logging.debug("  updated:")
        for updated_e in updated:
            logging.debug("    %s" % updated_e)
        logging.debug("  removed:")
        for removed_e in removed:
            logging.debug("    %s" % removed_e)
        logging.debug("  unchanged:")
        for unchanged_e in unchanged:
            logging.debug("      %s" % unchanged_e)

    def set_base(self, base_sg_models, base_sg_comp_models, base_sg_comp_bindings, base_amf_model):
        self._base_sg_models = base_sg_models
        self._base_sg_comp_models = base_sg_comp_models
        self._base_sg_comp_bindings = base_sg_comp_bindings
        self._base_amf_model = base_amf_model

    def set_target(self, target_sg_models, target_sg_comp_models, target_sg_comp_bindings, target_amf_model):
        self._target_sg_models = target_sg_models
        self._target_sg_comp_models = target_sg_comp_models
        self._target_sg_comp_bindings = target_sg_comp_bindings
        self._target_amf_model = target_amf_model

    def set_sv_info(self, sg_dn, sv_id):
        self._sg_dn = sg_dn
        self._sv_id = sv_id
        self._comp_id = None

    """
    AMF model diff and analysis to detect CSM Service change.
    """

    SV_NO_UPGRADE_FOUND = 0
    SV_VALID_UPGRADE_FOUND = 1
    SV_INVALID_UPGRADE_FOUND = 2

    def set_base_sv(self, base_sg_model, base_sg_comp_bindings):
        self._base_sg_model = base_sg_model
        self._base_sg_comp_bindings = base_sg_comp_bindings

    def set_target_sv(self, target_sg_model, base_sg_comp_bindings):
        self._target_sg_model = target_sg_model
        self._target_sg_comp_bindings = base_sg_comp_bindings

    def detect_sv_add(self):
        (added, updated, removed, unchanged) = self._target_sg_model.diff(self._base_sg_model)
        if not (len(added) > 0 and len(updated) == 0 and len(removed) == 0 and len(unchanged) == 0):
            return False
        for (comp_id, target_comp_binding) in self._target_sg_comp_bindings.items():
            (added, updated, removed, unchanged) = target_comp_binding.diff(self._base_sg_comp_bindings[comp_id])
            if (not len(added) > 0 and len(updated) == 0 and len(updated) == 0 and len(unchanged) == 0):
                return False
        return True

    def detect_sv_remove(self):
        (added, updated, removed, unchanged) = self._target_sg_model.diff(self._base_sg_model)
        if not (len(added) == 0 and len(updated) == 0 and len(removed) > 0 and len(unchanged) == 0):
            return False
        for (comp_id, target_comp_binding) in self._target_sg_comp_bindings.items():
            (added, updated, removed, unchanged) = target_comp_binding.diff(self._base_sg_comp_bindings[comp_id])
            if not (len(added) == 0 and len(updated) == 0 and len(removed) > 0 and len(unchanged) == 0):
                return False
        return True

    def detect_sv_reallocate(self):
        (added, updated, removed, unchanged) = self._target_sg_model.diff(self._base_sg_model)
        if len(removed) > 0 and len(unchanged) > 0:
            for dn in removed:
                # other objects rather than the one created by service-promotion-dependncy is removed
                if not isinstance(self._base_sg_model.getObject(dn), AMFModel.SaAmfSIDependency):
                    return True
        return False

    def detect_updated_attribute(self, added, updated, removed, object_types, target_model, base_model):
        '''
        look within current service/component to see if there is a change in an allowed attribute
        Remove found changes from the list/dictionary parameters accordingly
        '''
        retvalue = False


        addedlist = []
        removedlist = []
        updateddict = {}

        for objtype in object_types:
            filteredobjs = {}
            self.filterObjectTypes([objtype], added, target_model, filteredobjs, False)
            for v in filteredobjs[objtype]:
                logging.debug("detect_updated_attribute - sv %s, ct %s has ADDED: %s, type %s."\
                    % (self._sv_id, self._comp_id, v.getDn(), type(v)))
                retvalue = True
                addedlist.append(v.getDn())
                added.remove(v.getDn())

            filteredobjs = {}
            self.filterObjectTypes([objtype], removed, base_model, filteredobjs, False)
            for v in filteredobjs[objtype]:
                logging.debug("detect_updated_attribute - service %s, ct %s has REMOVED: %s, type %s."\
                    % (self._sv_id, self._comp_id, v.getDn(), type(v)))
                retvalue = True
                removedlist.append(v.getDn())
                removed.remove(v.getDn())

            filteredobjs = {}
            self.filterObjectTypes([objtype], updated.keys(), target_model, filteredobjs, False)
            for v in filteredobjs[objtype]:
                logging.debug("detect_updated_attribute - service %s, ct %s has UPDATED: %s, type %s."\
                    % (self._sv_id, self._comp_id, v.getDn(), type(v)))
                retvalue = True
                updateddict[v.getDn()] = updated[v.getDn()]
                del updated[v.getDn()]

        if (retvalue == True):
            self._amf_diff_calc_result.add_to_amf_diff_calc_result_dict(self._sg_dn, self._sv_id,self._comp_id, addedlist, updateddict, removedlist)
        return retvalue

    def detect_sv_upgrade(self):
        (added, updated, removed, unchanged) = self._target_sg_model.diff(self._base_sg_model)

        # check for changes in the service promotion dependencies and update the diff lists accordingly
        valid_update_found = False
        if self.detect_updated_attribute(added, updated, removed, self._amf_diff_calc_result.UPDATEABLE_SERVICE_ATTRIBUTE_LIST, self._target_sg_model, self._base_sg_model):
            logging.debug("detect_sv_upgrade - service promotion dependencies found to be changed in this upgrade")
            # along with any updated attributes there may be others added (example updated SaAmfSG may carry added SaAmfSUs)
            self._amf_diff_calc_result.add_to_amf_diff_calc_result_dict(self._sg_dn, self._sv_id,self._comp_id, added, {}, [])
            added = []
            valid_update_found = True

        if (len(added) == 0 and len(updated) == 0 and len(removed) == 0):
            if valid_update_found:
                return self.SV_VALID_UPGRADE_FOUND
            return self.SV_NO_UPGRADE_FOUND

        return self.SV_INVALID_UPGRADE_FOUND

    def detect_unchanged_sv(self):
        (added, updated, removed, unchanged) = self._target_sg_model.diff(self._base_sg_model)
        if not (len(added) == 0 and len(updated) == 0 and len(removed) == 0 and len(unchanged) > 0):
            return False
        # If there is a change in the bindings and it was not add or remove than
        # it will be handled in cts checks.
        return True

    def detect_and_validate_sv(self):
        '''
        check for changes and report if the service has been unchanged
        '''
        if self.detect_sv_add():
            return False

        if self.detect_sv_remove():
            logging.debug("Detected service removal in service {sv}".format(sv=self._sv_id))
            return False

        if self.detect_sv_reallocate():
            tcg_error("Not supported service reallocation in AMF models for sg: " + self._sg_dn)

        sv_upgrade_result = self.detect_sv_upgrade()
        if sv_upgrade_result == self.SV_INVALID_UPGRADE_FOUND:
            tcg_error('Detected service upgrade in service {sv}, which is not supported by TCG. '.format(sv=self._sv_id) +
                      'Check attributes and components included in service to find root cause')
        if sv_upgrade_result == self.SV_VALID_UPGRADE_FOUND:
            logging.debug("detect_and_validate_sv - valid service upgrade found for service {sv}.".format(sv=self._sv_id))
            return False

        if self.detect_unchanged_sv():
            return True

        (added, updated, removed, unchanged) = self._target_sg_model.diff(self._base_sg_model)
        self.dumpChange(self._sg_dn, added, updated, removed, unchanged)
        tcg_error("Not supported and unrecognized change in AMF models for sg: " + self._sg_dn)


    """
    AMF model diff and analysis to detect CSM Component change.
    """
    CT_NO_UPGRADE_FOUND = 0
    CT_VALID_UPGRADE_FOUND = 1
    CT_INVALID_UPGRADE_FOUND = 2

    def set_comp_info(self, comp_id):
        self._comp_id = comp_id
        self._binding_add_list = []
        self._target_sg_comp_binding = self._target_sg_comp_bindings[comp_id]
        self._base_sg_comp_binding = self._base_sg_comp_bindings[comp_id]

    def set_base_ct(self, base_sg_comp_model, merged_base_comp_model):
        self._base_sg_comp_model = base_sg_comp_model
        self._merged_base_comp_model = merged_base_comp_model

    def set_target_ct(self, target_sg_comp_model, merged_target_comp_model):
        self._target_sg_comp_model = target_sg_comp_model
        self._merged_target_comp_model = merged_target_comp_model

    def detect_ct_add(self):
        # Doing diff over component only objects
        (added, updated, removed, unchanged) = self._target_sg_comp_model.diff(self._base_sg_comp_model)
        if not (len(added) > 0 and len(updated) == 0 and len(removed) == 0 and len(unchanged) == 0):
            return False

        (added, updated, removed, unchanged) = self._target_sg_comp_binding.diff(self._base_sg_comp_binding)
        if not (len(added) > 0 and len(updated) == 0 and len(removed) == 0 and len(unchanged) == 0):
            return False

        self._binding_add_list.extend(added)

        return True

    def detect_ct_remove(self):
        (added, updated, removed, unchanged) = self._target_sg_comp_model.diff(self._base_sg_comp_model)
        (binding_added, binding_updated, binding_removed, binding_unchanged) = self._target_sg_comp_binding.diff(self._base_sg_comp_binding)

        # remove some instances of a component
        if (len(added) == 0 and len(updated) == 0 and len(removed) == 0 and len(unchanged) > 0 and
                len(binding_added) == 0 and len(binding_updated) == 0 and len(binding_removed) > 0 and len(binding_unchanged) > 0):
            return True

        if not (len(added) == 0 and len(updated) == 0 and len(removed) > 0 and len(unchanged) == 0):
            return False

        if not (len(binding_added) == 0 and len(binding_updated) == 0 and len(binding_removed) > 0 and len(binding_unchanged) == 0):
            return False
        return True

    def detect_unchanged_ct(self):
        (added, updated, removed, unchanged) = self._target_sg_comp_model.diff(self._base_sg_comp_model)

        if not (len(added) == 0 and len(updated) == 0 and len(removed) == 0 and len(unchanged) > 0):
            return False

        (added, updated, removed, unchanged) = self._target_sg_comp_binding.diff(self._base_sg_comp_binding)
        if not (len(added) == 0 and len(updated) == 0 and len(removed) == 0 and len(unchanged) > 0):
            return False
        return True

    def detect_added_duplicate_comps(self, addlist):
        '''
        detect in the model diffs if a duplicate component is being added to the servie
        (another instance of an existing component type) and then remove found AMF objects
        from the addlist accordingly
        '''
        if not len(addlist):
            return False

        target_comp_model = self._merged_target_comp_model
        base_comp_model = self._merged_base_comp_model
        target_model = self._target_amf_model
        base_model = self._base_amf_model

        # a function to see if there are any added component instances added to the service which are identical
        # other(s) that already exist in the service
        retvalue = False

        (added, updated, removed, unchanged) = target_comp_model.diff(base_comp_model)

        objectTypes = [AMFModel.SaAmfComp,
                       AMFModel.SaAmfCompCsType,
                       AMFModel.SaAmfCSI]


        baseFilteredObjects = {}
        targetFilteredObjects = {}

        # extract the SaAmfComps from the added and removed lists
        self.filterObjectTypes(objectTypes, added, target_comp_model, targetFilteredObjects, False)
        self.filterObjectTypes(objectTypes, removed, base_comp_model, baseFilteredObjects, False)
        # this prelim checks to see if there are possible added comps

        if not (len(targetFilteredObjects[AMFModel.SaAmfComp]) > len(baseFilteredObjects[AMFModel.SaAmfComp])):
            return False

        # make sure there is at least one SaAmfComp that already exists in the present SafSU that has identical SaAmfCompBaseType
        # as all of added SaAmfComps
        comptypesadded = {}
        for obj in targetFilteredObjects[AMFModel.SaAmfComp]:
            # retrieve SaAmfCompBaseType
            sa_amf_comp_base_type = target_comp_model.getObject(obj.getsaAmfCompType()).getParentDn()
            if sa_amf_comp_base_type not in comptypesadded.keys():
                comptypesadded[sa_amf_comp_base_type] = 0
            comptypesadded[sa_amf_comp_base_type] += 1

        # collect the SaAmfComps from the 'unchanged' or 'updated' list - there should be at least one SaAmfComp
        # of the same SaAmfCompBaseType as all of those in 'comptypesadded'
        unchanged.extend(updated.keys())
        self.filterObjectTypes(objectTypes, unchanged, base_comp_model, baseFilteredObjects, False)
        comptypesrest = {}

        for obj in baseFilteredObjects[AMFModel.SaAmfComp]:
            # retrieve SaAmfCompBaseType
            sa_amf_comp_base_type = base_comp_model.getObject(obj.getsaAmfCompType()).getParentDn()
            if sa_amf_comp_base_type not in comptypesrest.keys():
                comptypesrest[sa_amf_comp_base_type] = 0
            comptypesrest[sa_amf_comp_base_type] += 1

        # if the SaAmfComps being added are duplicates of already existing comps, the two dicts MUST be the same
        if comptypesrest == comptypesadded:
            logging.debug("detect_added_duplicate_comps - duplicate found in upgrade campaign")
        else:
            return False

        # remove from 'addlist' all of the found AMF Model objects that are related to these added SaAmfComps

        # first rmv all the SaAmfComps
        for obj in targetFilteredObjects[AMFModel.SaAmfComp]:
            addlist.remove(obj.getDn())
            self._binding_add_list.append(obj.getDn())

        # now rmv all SaAmfCompCSTypes associated with added SaAmfComps
        for obj in targetFilteredObjects[AMFModel.SaAmfCompCsType]:
            if obj.getDn() in addlist:
                addlist.remove(obj.getDn())
                self._binding_add_list.append(obj.getDn())

        # rmv the SaAmfCSI associated with added SaAmfComps
        for obj in targetFilteredObjects[AMFModel.SaAmfCSI]:
            if obj.getDn() in addlist:
                addlist.remove(obj.getDn())
                self._binding_add_list.append(obj.getDn())

        return True

    def detect_ct_type_upgrade(self, added, updated, removed):
        '''
        check that the added and removed contains the following 4 object types:
          SaAmfHealthcheckType
          SaAmfCompType
          SaAmfCtCsType
          SaAmfSutCompType
        and updated set only contains SaAmfComp objects and only their
        saAmfCompType, and possibly saAmfCSAttrName, attributes changed
        and neither set is empty
        and all the old saAmfCompTypes in updated SaAmfComps are in the removed set
        and all the new saAmfCompTypes in updated SaAmfComps are in the added set
        and that all SaAmfHealthcheckType object is child of one of the SaAmfCompType objects
        and that all SaAmfCtCsType object is child of one of the SaAmfCompType objects
        and that all SaAmfSutCompType object is child of one of the SaAmfCompType objects

        aftera all checks, remove found components from the 'added', 'updated' and 'removed' lists/dictionaries
        '''
        base_model = self._base_amf_model
        target_model = self._target_amf_model

        objectTypes = [AMFModel.SaAmfHealthcheckType,
                       AMFModel.SaAmfCompType,
                       AMFModel.SaAmfCtCsType,
                       AMFModel.SaAmfSutCompType]

        baseFilteredObjects = {}
        targetFilteredObjects = {}

        self.filterObjectTypes(objectTypes, added, target_model, targetFilteredObjects, False)
        self.filterObjectTypes(objectTypes, removed, base_model, baseFilteredObjects, False)

        updated_comp_type_ct = 0
        updated_value_set = set(list(itertools.chain.from_iterable(updated.values())))

        for updated_value in updated_value_set:
            if updated_value == 'saAmfCompType':
                updated_comp_type_ct += 1
            elif updated_value not in {
                'saAmfCSAttrName',
                'saAmfSIPrefActiveAssignments',
                'saAmfCompCmdEnv',
            }:
                return False  # any other type present is not allowed

        # if there is a saAmfCSAttrName present, there MUST also exist a saAmfCompType
        # this next check ensures that the updated_value_set is populated AND
        # that there does not exist a saAmfCSAttrName without a saAmfCompType
        if (updated_comp_type_ct == 0):
            return False

        if (len(added) == 0 or len(removed) == 0):
            # there is no compnenet update
            return False

        # the rest of the function is a check that the removed dns are exactly the same as the added
        addedCompTypeDnRefs = set()
        removedCompTypeDnRefs = set()

        # check the domains of the saAmfCompTypes that have come with the 'updated' dictionary
        for dn in updated.keys():
            values = updated[dn]
            if 'saAmfCompType' in values:
                removedCompTypeDnRefs.add(base_model.getObject(dn).getsaAmfCompType())
                addedCompTypeDnRefs.add(target_model.getObject(dn).getsaAmfCompType())

        addedCompTypeDns = set()
        removedCompTypeDns = set()

        for compType in baseFilteredObjects[AMFModel.SaAmfCompType]:
            removedCompTypeDns.add(compType.getDn())

        for compType in targetFilteredObjects[AMFModel.SaAmfCompType]:
            addedCompTypeDns.add(compType.getDn())

        addedHctParentDns = set()
        removedHctParentDns = set()

        for hct in baseFilteredObjects[AMFModel.SaAmfHealthcheckType]:
            removedHctParentDns.add(hct.getParentDn())

        for hct in targetFilteredObjects[AMFModel.SaAmfHealthcheckType]:
            addedHctParentDns.add(hct.getParentDn())

        addedCtCstParentDns = set()
        removedCtCstParentDns = set()

        for ctcst in baseFilteredObjects[AMFModel.SaAmfCtCsType]:
            removedCtCstParentDns.add(ctcst.getParentDn())

        for ctcst in targetFilteredObjects[AMFModel.SaAmfCtCsType]:
            addedCtCstParentDns.add(ctcst.getParentDn())

        addedSutCompTypeNames = set()
        removedSutCompTypeNames = set()

        for sutcomp in baseFilteredObjects[AMFModel.SaAmfSutCompType]:
            removedSutCompTypeNames.add(sutcomp.getName())

        for sutcomp in targetFilteredObjects[AMFModel.SaAmfSutCompType]:
            addedSutCompTypeNames.add(sutcomp.getName())

        if (addedCompTypeDnRefs == addedCompTypeDns and \
               addedCompTypeDnRefs == addedHctParentDns and \
               addedCompTypeDnRefs == addedCtCstParentDns and \
               addedCompTypeDnRefs == addedSutCompTypeNames and \
               removedCompTypeDnRefs == removedCompTypeDns and \
               removedCompTypeDnRefs == removedHctParentDns and \
               removedCompTypeDnRefs == removedCtCstParentDns and \
               removedCompTypeDnRefs == removedSutCompTypeNames) == False:
            return False

        # we have determined that the contents of the add, remove, update list/dictionaries
        # contained objects that had to do with the update of a comp type...now remove the
        # components from the list/dictionaries that contained them

        rmvlist = []
        addlist = []
        rmvlist.extend(baseFilteredObjects[AMFModel.SaAmfCompType])
        rmvlist.extend(baseFilteredObjects[AMFModel.SaAmfHealthcheckType])
        rmvlist.extend(baseFilteredObjects[AMFModel.SaAmfCtCsType])
        rmvlist.extend(baseFilteredObjects[AMFModel.SaAmfSutCompType])

        addlist.extend(targetFilteredObjects[AMFModel.SaAmfCompType])
        addlist.extend(targetFilteredObjects[AMFModel.SaAmfHealthcheckType])
        addlist.extend(targetFilteredObjects[AMFModel.SaAmfCtCsType])
        addlist.extend(targetFilteredObjects[AMFModel.SaAmfSutCompType])

        self._amf_diff_calc_result.add_to_amf_diff_calc_result_dict(self._sg_dn, self._sv_id,self._comp_id, [], updated, [])

        for amfobj in rmvlist:
            if amfobj.getDn() in removed:
                removed.remove(amfobj.getDn())

        for amfobj in addlist:
            if amfobj.getDn() in added:
                added.remove(amfobj.getDn())

        # we know from above that the updated dict contained only objects
        # having to do with the update of a component type -  so we clear it
        updated.clear()
        return True

    def remove_updated_service_attribute(self, added, updated, removed):
        rmlist = []
        hv88205_change = False
        for dn in added:
            obj = self._target_amf_model.getObject(dn)
            if type(obj) in self._amf_diff_calc_result.UPDATEABLE_SERVICE_ATTRIBUTE_LIST or type(obj) == AMFModel.SaAmfSU:
                rmlist.append(dn)
        [added.remove(dn) for dn in rmlist]
        for dn in updated.keys():
            obj = self._target_amf_model.getObject(dn)
            if (type(obj) in self._amf_diff_calc_result.UPDATEABLE_SERVICE_ATTRIBUTE_LIST):
                del updated[dn]
            elif type(obj) in self._amf_diff_calc_result.UPDATEABLE_COMPONENT_TYPE_ATTRIBUTE_LIST_HV88205:
                if type(obj) == AMFModel.SaAmfCompType and updated[dn] == ['saAmfCtDefCmdEnv']:
                    hv88205_change = True
                    del updated[dn]

        for dn in removed:
            obj = self._base_amf_model.getObject(dn)
            if type(obj) in self._amf_diff_calc_result.UPDATEABLE_SERVICE_ATTRIBUTE_LIST:
                removed.remove(dn)
        return hv88205_change

    def detect_ct_upgrade(self):
        base_sg_model = self._merged_base_comp_model
        target_sg_model = self._merged_target_comp_model

        (added, updated, removed, unchanged) = target_sg_model.diff(base_sg_model)

        valid_update_csi_change = False
        valid_added_duplicate_comps = False
        valid_update_comp_type = False
        valid_update_comp_type_change_hv88205 = False

        # there may be some attributes left that have been handled at the service level, remove them
        if self.remove_updated_service_attribute(added, updated, removed):
            logging.debug("detect_ct_upgrade - comptype attributes found to be changed in this upgrade")
            valid_update_comp_type_change_hv88205 = True

        # check for changes in the csi attribute and update the diff lists accordingly
        # before moving forward with other checks
        if self.detect_updated_attribute(added, updated, removed, self._amf_diff_calc_result.UPDATEABLE_COMPONENT_ATTRIBUTE_LIST, target_sg_model, base_sg_model):
            logging.debug("detect_ct_upgrade - CSI attributes found to be changed in this upgrade")
            valid_update_csi_change = True

        # check for added other instances of an existing component type within this service and
        # remove found AMF objects
        if self.detect_added_duplicate_comps(added):
            valid_added_duplicate_comps = True
            logging.debug("detect_ct_upgrade - duplicate components being added to this service in this upgrade")

        # check for an update in the component type and update the diff lists accordingly
        if self.detect_ct_type_upgrade(added, updated, removed):
            logging.debug("detect_ct_upgrade - upgrade of a component type found")
            valid_update_comp_type = True

        # at this point, the added, removed and updated lists should be empty if a valid
        # upgrade has been found
        if (len(added) > 0 or len(updated) > 0):
            logging.debug("an INVALID upgrade has been detected")
            self.dumpChange(self._sg_dn, added, updated, removed, unchanged)
            return self.CT_INVALID_UPGRADE_FOUND

        if (valid_update_csi_change or valid_added_duplicate_comps or valid_update_comp_type
                or valid_update_comp_type_change_hv88205):
            logging.debug("a valid upgrade has been detected")
            return self.CT_VALID_UPGRADE_FOUND
        else:
            logging.debug("NO upgrade has been detected")
            return self.CT_NO_UPGRADE_FOUND


    def detect_and_validate_ct(self):
        target_sg_comp_model = self._target_sg_comp_model
        comp_id = self._comp_id

        if self.detect_ct_add():
            logging.debug("ComponentAMFModelSVAndCTDiffCalculator  detect_and_validate_ct - a component instance %s added to service %s." % (comp_id,self._sv_id))
            return

        if self.detect_ct_remove():
            logging.debug("Detected component removal.")
            return

        ct_upg_result = self.detect_ct_upgrade()

        if ct_upg_result ==  self.CT_VALID_UPGRADE_FOUND:
            return


        if self.detect_unchanged_ct():
            return


        (added, updated, removed, unchanged) = self._target_sg_comp_model.diff(self._base_sg_comp_model)
        self.dumpChange(self._sg_dn, added, updated, removed, unchanged)
        tcg_error("Not supported and unrecognized change in AMF models for sg: " + self._sg_dn + ", comp: " + comp_id)

    def calculate_diff(self):

        for (sg_dn, target_sg_model) in self._target_sg_models.items():
            target_sg_comp_models = self._target_sg_comp_models[sg_dn]
            target_sg_comp_bindings = self._target_sg_comp_bindings[sg_dn]
            base_sg_model = self._base_sg_models[sg_dn]
            base_sg_comp_models = self._base_sg_comp_models[sg_dn]
            base_sg_comp_bindings = self._base_sg_comp_bindings[sg_dn]

            merged_base_sg_model = self.mergeSgModels(base_sg_model, base_sg_comp_models, base_sg_comp_bindings)
            merged_target_sg_model = self.mergeSgModels(target_sg_model, target_sg_comp_models, target_sg_comp_bindings)

            (added, updated, removed, unchanged) = merged_target_sg_model.diff(merged_base_sg_model)
            svid = AMFTools.getUnitIdFromModelName(ImmHelper.getParentDn(sg_dn))
            self.print_diff_result(("Diff for sg submodel " + sg_dn + ", svid " + svid),added, updated, removed, unchanged)
            self._amf_diff_calc_result.add_to_sv_target_models(svid, merged_target_sg_model, merged_base_sg_model, sg_dn, added, updated, removed, unchanged)

            self.set_sv_info(sg_dn, svid)
            self.set_base_sv(base_sg_model, base_sg_comp_bindings)
            self.set_target_sv(target_sg_model, target_sg_comp_bindings)
            self.detect_and_validate_sv()

            for (comp_id, target_sg_comp_model) in target_sg_comp_models.items():
                base_sg_comp_model = base_sg_comp_models[comp_id]
                target_sg_comp_binding = target_sg_comp_bindings[comp_id]
                base_sg_comp_binding = base_sg_comp_bindings[comp_id]
                merged_target_comp_model = self.mergeSgModels(target_sg_model, {comp_id:target_sg_comp_model}, {comp_id:target_sg_comp_binding})
                merged_base_comp_model = self.mergeSgModels(base_sg_model, {comp_id:base_sg_comp_model}, {comp_id:base_sg_comp_binding})

                self.set_comp_info(comp_id)
                self.set_base_ct(base_sg_comp_model, merged_base_comp_model)
                self.set_target_ct(target_sg_comp_model, merged_target_comp_model)
                self.detect_and_validate_ct()

                self._amf_diff_calc_result.add_to_amf_diff_calc_result_dict(sg_dn, None, comp_id,added = self._binding_add_list)

def filterObjectTypes(objectTypes, dnList, model, objects={}, strictMode=True):
    for type_ in objectTypes:
        objects[type_] = []

    for dn in dnList:
        object = model.getObject(dn)
        if type(object) not in objectTypes :
            if strictMode:
                return False
        else:
            objects[type(object)].append(object)
    return True

class AMFModelDiffCalculator(object):

    '''
    To be decided:  Right now there are 2 classes performing the diff calc:
        AMFModelSVAndCTDiffCalculator
        AMFModelDiffCalculator
    We can think about this, and what the names should be.
    '''

    """
    This calss performs the AMF model diff calculation. Properly detecting CT adds/removes
    or SV changes from AMF models are not that simple tasks. We have to filter the
    base model since it may contain irrelevant entities. After that we have basically
    two possible approach.

    The first one is that we create a diff from the whole models, and then check every
    AMF entity one by one to see if it is added/removed/updated/unchanged. And after
    this we would check the combiniations of these entities to decide whether or not
    it is a supported change. This would require a lot of coding and a lot of ifs.

    What we did instead is to split the model into submodels by services and
    components. In these submodels the AMF entities are grouped together in a way
    that if one them changes, all of them has to be changed. This way the change
    detection for a single CT or SV could be done with a simple diff over the model.
    Almost. The CT upgrade is not that simple (there are some new, some removed and
    some updated entities), but it is still simpler this way than  checking AMF entities
    one by one.
    Also another positive thing is that the splitting and the filtering can be combined.
    """

    def __init__(self, base_amf_model, target_amf_model, mergedAppBaseTypeDns, amf_diff_calc_result):
        self._base_amf_model = base_amf_model
        self._target_amf_model = target_amf_model
        self._merged_app_base_type_dns = mergedAppBaseTypeDns
        self._amf_diff_calc_result = amf_diff_calc_result
        self._amf_diff_sv_ct_calc = AMFModelSVAndCTDiffCalculator(self._amf_diff_calc_result)
        self.split_models_and_calculate_diffs()
        self._amf_diff_calc_result._instances_removed_from_base = self.calc_instances_removed_from_base()
        self._amf_diff_calc_result._bundles_removed_from_base = self.calc_bundles_removed_from_base()

    def split_models_and_calculate_diffs(self):
        (baseModels, targetModels) = self.get_split_mods()
        for app_base_type_dn in self._merged_app_base_type_dns:
            (baseAppModel, baseSgModels, baseCompModels, base_bindings) = baseModels[app_base_type_dn]
            (targetAppModel, targetSgModels, targetCompModels, target_bindings) = targetModels[app_base_type_dn]

            self.create_symmetric_models(baseSgModels, baseCompModels, base_bindings, targetSgModels, targetCompModels, target_bindings)



            (added, updated, removed, unchanged) = targetAppModel.diff(baseAppModel)
            self._amf_diff_calc_result.add_to_amf_diff_calc_result_dict(app_base_type_dn, None, None, added, updated, removed)

            if not self.detectValidAppTypeChange(app_base_type_dn, added, updated, removed, unchanged, baseAppModel, targetAppModel):
                self._amf_diff_sv_ct_calc.dumpChange(app_base_type_dn, added, updated, removed, unchanged)
                tcg_error("Not supported change in app type %s" % app_base_type_dn)

            self.log_models(baseAppModel, baseSgModels, baseCompModels, base_bindings, "Base model after filtering and splitting for app_type_dn:  " + app_base_type_dn)
            self.log_models(targetAppModel, targetSgModels, targetCompModels, target_bindings, "Target model after filtering and splitting for app_type_dn :" + app_base_type_dn)

            self._amf_diff_sv_ct_calc.set_base(baseSgModels, baseCompModels, base_bindings, self._base_amf_model)
            self._amf_diff_sv_ct_calc.set_target(targetSgModels, targetCompModels, target_bindings, self._target_amf_model)
            self._amf_diff_sv_ct_calc.calculate_diff()

    def get_split_mods(self):
        base_models = {}
        self.splitModel(self._base_amf_model, base_models, self._merged_app_base_type_dns)

        target_models = {}
        self.splitModel(self._target_amf_model, target_models, self._merged_app_base_type_dns)

        return (base_models, target_models)

    def detectSGChanges(self, app_base_type_dn, added, updated, removed, unchanged, baseAppModel, targetAppModel):
        objectTypes = [ AMFModel.SaAmfAppType ]

        if not filterObjectTypes(objectTypes, added, targetAppModel, {}):
            return False

        if not filterObjectTypes(objectTypes, removed, baseAppModel, {}):
            return False

        if not filterObjectTypes([AMFModel.SaAmfApplication], updated.keys(), targetAppModel) or \
           set(list(itertools.chain.from_iterable(updated.values()))) != set(["saAmfAppType"]):
            return False

        return True

    def detectValidAppTypeChange(self, app_base_type_dn, added, updated, removed, unchanged, baseAppModel, targetAppModel):
        return (len(added) > 0 and len(updated) == 0 and len(removed) == 0 and len(unchanged) == 0) or \
           (len(added) == 0 and len(updated) == 0 and len(removed) == 0 and len(unchanged) > 0) or \
           (len(added) == 0 and len(updated) == 0 and len(removed) > 0 and len(unchanged) == 0) or \
           (len(added) == 0 and len(updated) == 0 and len(removed) == 0 and len(unchanged) == 0) or \
           self.detectSGChanges(app_base_type_dn, added, updated, removed, unchanged, baseAppModel, targetAppModel)


    def create_symmetric_models(self, baseSgModels, baseCompModels, base_bindings, targetSgModels, targetCompModels, target_bindings):
        """
        create symmetrical structure in base and target models
        so we can easyly diff them.
        """
        for (sg_dn, sgModel) in targetSgModels.items():
            if sg_dn not in baseSgModels.keys():
                baseSgModels[sg_dn] = AMFModel.AMFModel()

        for (sg_dn, sgModel) in baseSgModels.items():
            if sg_dn not in targetSgModels.keys():
                targetSgModels[sg_dn] = AMFModel.AMFModel()

        for (sg_dn, sg_comp_models) in targetCompModels.items():
            if sg_dn not in baseCompModels.keys():
                baseCompModels[sg_dn] = {}
            for (comp_id, comp_model) in sg_comp_models.items():
                if comp_id not in baseCompModels[sg_dn]:
                    baseCompModels[sg_dn][comp_id] = AMFModel.AMFModel()

        for (sg_dn, sg_comp_models) in baseCompModels.items():
            if sg_dn not in targetCompModels.keys():
                targetCompModels[sg_dn] = {}
            for (comp_id, comp_model) in sg_comp_models.items():
                if comp_id not in targetCompModels[sg_dn]:
                    targetCompModels[sg_dn][comp_id] = AMFModel.AMFModel()

        for (sg_dn, sg_comp_bindings) in target_bindings.items():
            if sg_dn not in base_bindings.keys():
                base_bindings[sg_dn] = {}
            for (comp_id, comp_binding) in sg_comp_bindings.items():
                if comp_id not in base_bindings[sg_dn]:
                    base_bindings[sg_dn][comp_id] = AMFModel.AMFModel()

        for (sg_dn, sg_comp_bindings) in base_bindings.items():
            if sg_dn not in target_bindings.keys():
                target_bindings[sg_dn] = {}
            for (comp_id, comp_binding) in sg_comp_bindings.items():
                if comp_id not in target_bindings[sg_dn]:
                    target_bindings[sg_dn][comp_id] = AMFModel.AMFModel()


    def log_models(self, app_model, sg_models, comp_models, comp_bindings, extrainfo):

        logging.debug("\n")
        logging.debug(" %s" % extrainfo)

        logging.debug("  Component models by SG and CT dns:")
        for (sg_dn, comp_models) in comp_models.items():
            logging.debug("    SG: %s" % sg_dn)
            for (comp_dn, comp_model) in comp_models.items():
                logging.debug("      CT: %s" % comp_dn)
                for o in comp_model.getObjects():
                    logging.debug("        %s" % o)

        logging.debug("  Service models by SG dns:")
        for (sg_dn, sg_model) in sg_models.items():
            logging.debug("    SG: %s" % sg_dn)
            for o in sg_model.getObjects():
                logging.debug("      %s" % o)

        logging.debug("  CT-SV binding models by SG and CT dns:")
        for (sg_dn, bindings) in comp_bindings.items():
            logging.debug("    SG: %s" % sg_dn)
            for (comp_dn, sg_comp_binding) in bindings.items():
                logging.debug("      CT: %s" % comp_dn)
                for o in sg_comp_binding.getObjects():
                     logging.debug("        %s" % o)

    def splitModel(self, base_amf_model, base_models, app_base_type_dns):
        """
        Split the model into 3 parts, and also filter it while
        doing so. The 3 parts are seperated by service and
        component ids. The first part is containing service only
        entities. The second part is containing component only
        services by SV and CT id. The third part is containing
        SV-CT bindings.
        Also creating submodels contianing application data.

        Some binding objects are contained in the subtree of an
        SG model object. If we add the whole subtree to the SG model
        then we have to manually remove these "sub-binding-objects"
        and add them one by one to the BINDINGS model.
        """
        for app_base_type_dn in app_base_type_dns:
            app_base_model = AMFModel.AMFModel()
            sg_models = {}
            comp_models = {}
            bindings = {}
            base_models[app_base_type_dn] = (app_base_model, sg_models, comp_models, bindings)

            app_dn = AMFModel.SaAmfApplication.createDn(ImmHelper.getName(app_base_type_dn))
            app = base_amf_model.getObjectUnsafe(app_dn)

            if app is not None:
                # Adding to APP model SaAmfApplications,    dn: safApp=ERIC-<service_unique_id>
                app_base_model.addObject(app)

            # Adding to APP model the subTree of SaAmfAppBaseType,    dns ending with: safAppType=ERIC-<service_unique_id>
            app_base_model._objects.update(base_amf_model.getSubtree(app_base_type_dn))

            app_types = base_amf_model.getObjects(AMFModel.SaAmfAppType, app_base_type_dn)
            for (app_type_dn, app_type) in app_types.items():
                sg_type_dns = app_type.getsaAmfApptSGTypes()
                for sg_type_dn in sg_type_dns:
                    sg_type = base_amf_model.getObjectUnsafe(sg_type_dn)
                    if sg_type is None:
                        continue

                    sg_base_model = AMFModel.AMFModel()
                    found = False
                    sg_dn = None
                    for (_sg_dn, sg) in base_amf_model.getObjects(AMFModel.SaAmfSG, app_dn).items():
                        if sg.getsaAmfSGType() == sg_type_dn:
                            if found:
                                tcg_error("Multiple SG refers to the same sgType %s" % (sg_type_dn))
                            sg_dn = _sg_dn
                            comp_models[sg_dn] = {}
                            bindings[sg_dn] = {}
                            sg_models[sg_dn] = sg_base_model
                            found = True
                            # Adding to SG model the subTree of SaAmfSG,     dns ending with: safSg=<redundancy_model_name>, safApp=ERIC-<service_unique_id>
                            sg_base_model._objects.update(base_amf_model.getSubtree(sg_dn))

                    if not found:
                        tcg_error("No SG found for sgType %s" % (sg_type_dn))

                    sg_base_type_dn = sg_type.getParentDn()
                    # Adding to SG model the subtree of SaAmfSGBaseType,    dns ending with: safSgType=ERIC-<service_unique_id>
                    sg_base_model._objects.update(base_amf_model.getSubtree(sg_base_type_dn))

                    su_type_dns = sg_type.getsaAmfSgtValidSuTypes()
                    for su_type_dn in su_type_dns:
                        su_type = base_amf_model.getObjectUnsafe(su_type_dn)
                        if su_type is None:
                            continue

                        su_base_type_dn = su_type.getParentDn()
                        # Adding to SG model the subtree of SaAmfSUBaseType,    dns ending with: safSUType=ERIC-<service_unique_id>
                        sg_base_model._objects.update(base_amf_model.getSubtree(su_base_type_dn))

                        svc_type_dns = su_type.getsaAmfSutProvidesSvcTypes()

                        sut_comp_types = base_amf_model.getObjects(AMFModel.SaAmfSutCompType, su_type_dn)
                        for sut_comp_type in sut_comp_types.keys():
                            # Removing from SG model binding object SaAmfSutCompType,    dn: safMemberCompType=safVersion=<component_version>\,
                            #                                                                safCompType=ERIC-<component_unique_id>, safVersion=1,
                            #                                                                safSUType=ERIC-<service_unique_id>
                            sg_base_model.removeObject(sut_comp_type)
                        comp_type_dns = map(ImmHelper.getName, sut_comp_types.keys())
                        for comp_type_dn in comp_type_dns:
                            comp_type_id = AMFTools.getUnitIdFromDn(comp_type_dn)
                            comp_models[sg_dn][comp_type_id] = AMFModel.AMFModel()
                            # Addding to COMP model the subtree of SaAmfCompBaseType,    dns ending with: safCompType=ERIC-<component_unique_id>
                            comp_models[sg_dn][comp_type_id]._objects.update(base_amf_model.getSubtree(ImmHelper.getParentDn(comp_type_dn)))
                            for (sut_comp_type_dn, sut_comp_type) in sut_comp_types.items():
                                if comp_type_dn == ImmHelper.getName(sut_comp_type_dn):
                                    if sg_dn not in bindings.keys():
                                        bindings[sg_dn] = {}
                                    if comp_type_id not in bindings[sg_dn].keys():
                                        bindings[sg_dn][comp_type_id] = AMFModel.AMFModel()
                                    # Adding to BINDINGS model binding object SaAmfSutCompType,    dn: safMemberCompType=safVersion=<component_version>\,
                                    #                                                                  safCompType=ERIC-<component_unique_id>, safVersion=1,
                                    #                                                                  safSUType=ERIC-<service_unique_id>
                                    bindings[sg_dn][comp_type_id].addObject(base_amf_model.getObject(sut_comp_type_dn))
                            for (comp_cs_type_dn, comp_cs_type) in sg_base_model.getObjects(_class=AMFModel.SaAmfCompCsType).items():
                                csTypeDn = ImmHelper.getName(comp_cs_type_dn)
                                if AMFTools.getUnitIdFromDn(csTypeDn) == comp_type_id:
                                    assert bindings[sg_dn][comp_type_id], "Error in model, SaAmfSutCompType was not fetched before SaAmfCompCsType"
                                    # Adding to BINDINGS model binding object SaAmfCompCsType,    dn: safSupportedCsType=safVersion=1\,
                                    #                                                                 safCSType=ERIC-<component_unique_id>,
                                    #                                                                 safComp=<component_instance_name>, safSu=<node_name>,
                                    #                                                                 safSg=<redundancy_model_name>, safApp=ERIC-<service_unique_id>
                                    bindings[sg_dn][comp_type_id].addObject(comp_cs_type)
                                    # Removing from SG model binding object SaAmfCompCsType,    dn: safSupportedCsType=safVersion=1\,
                                    #                                                               safCSType=ERIC-<component_unique_id>,
                                    #                                                               safComp=<component_instance_name>, safSu=<node_name>,
                                    #                                                               safSg=<redundancy_model_name>, safApp=ERIC-<service_unique_id>
                                    sg_base_model.removeObject(comp_cs_type_dn)
                                    comp_uid = AMFTools.getUnitIdFromDn(ImmHelper.getParentDn(comp_type_dn))
                                    sg_serv_id = AMFTools.getUnitIdFromDn(ImmHelper.getName(ImmHelper.getParentDn(sg_dn)))
                                    for (comp_dn, comp) in sg_base_model.getObjects(_class=AMFModel.SaAmfComp).items():
                                        comp_serv_id = AMFTools.getUnitIdFromDn(ImmHelper.getParentDn(ImmHelper.getParentDn(ImmHelper.getParentDn(comp_dn))))
                                        if sg_serv_id == comp_serv_id and \
                                            AMFTools.getUnitIdFromDn(ImmHelper.getName(comp_cs_type_dn)) == comp_uid and \
                                            ImmHelper.getName(comp_dn) == ImmHelper.getName(ImmHelper.getParentDn(comp_cs_type_dn)):
                                                # Adding to BINDINGS model binding object SaAmfComp,    dn: safComp=<component_instance_name>, safSu=<node_name>,
                                                #                                                           safSg=<redundancy_model_name>,
                                                #                                                           safApp=ERIC-<service_unique_id>
                                                bindings[sg_dn][comp_type_id].addObject(comp)
                                                # Removing from SG model binding object SaAmfComp,    dn: safComp=<component_instance_name>, safSu=<node_name>,
                                                #                                                           safSg=<redundancy_model_name>,
                                                #                                                           safApp=ERIC-<service_unique_id>
                                                sg_base_model.removeObject(comp_dn)
                                        #FIXME: remove su_id, change the generation of csi id, remove the node_id from there
                                        #       this would effect multiple test cases, should be done in separate commit
                                        su_id = ImmHelper.getName(ImmHelper.getParentDn(comp_dn))
                                        for (csi_dn, csi) in base_amf_model.getObjects(_class=AMFModel.SaAmfCSI).items():
                                            csi_serv_id = AMFTools.getUnitIdFromDn(ImmHelper.getParentDn(ImmHelper.getParentDn(csi_dn)))
                                            if csi_serv_id == sg_serv_id and \
                                                AMFTools.getUnitIdFromDn(ImmHelper.getName(comp_cs_type_dn)) == comp_uid and \
                                                    (ImmHelper.getName(csi_dn) == ImmHelper.getName(ImmHelper.getParentDn(comp_cs_type_dn)) + "-" + su_id or ImmHelper.getName(
                                                        csi_dn) == ImmHelper.getName(ImmHelper.getParentDn(comp_cs_type_dn))):
                                                    # Adding to BINDINGS model binding object SaAmfCSI,    dn: safCsi=<component_instance_name>,
                                                    #                                                          safSi=<redundancy_model_name>-<service_instance_id>,
                                                    #                                                          safApp=ERIC-<service_unique_id>
                                                    bindings[sg_dn][comp_type_id]._objects.update(base_amf_model.getSubtree(csi_dn))

                        for svc_type_dn in svc_type_dns:
                            svc_type = base_amf_model.getObjectUnsafe(svc_type_dn)
                            if svc_type is None:
                                continue

                            for (si_dn, si) in base_amf_model.getObjects(AMFModel.SaAmfSI, app_dn).items():
                                if si.getsaAmfSvcType() == svc_type_dn:
                                    # Adding to SG model the subtree of SaAmfSI,    dns ending with: safSi=<redundancy_model_name>-<service_instance_id>,
                                    #                                                                safApp=ERIC-<service_unique_id>
                                    sg_base_model._objects.update(base_amf_model.getSubtree(si_dn))

                            svc_base_type_dn = svc_type.getParentDn()
                            # Adding to SG model the subtree of SaAmfSvcBaseType,    dns ending with: safSvcType=ERIC-<service_unique_id>
                            sg_base_model._objects.update(base_amf_model.getSubtree(svc_base_type_dn))

                            svc_type_cs_typeses = base_amf_model.getObjects(AMFModel.SaAmfSvcTypeCSTypes, svc_type_dn)
                            cs_type_dns = map(ImmHelper.getName, svc_type_cs_typeses.keys())
                            for cs_type_dn in cs_type_dns:
                                for comp_type_id in comp_models[sg_dn].keys():
                                    if comp_type_id == AMFTools.getUnitIdFromDn(cs_type_dn):
                                        # Addindg to COMP model the subtree of SaAmfCSBaseType,    dns ending with: safCSType=ERIC-<component_unique_id>
                                        comp_models[sg_dn][comp_type_id]._objects.update(base_amf_model.getSubtree(ImmHelper.getParentDn(cs_type_dn)))
                                        for (svc_type_cs_types_dn, svc_type_cs_types) in svc_type_cs_typeses.items():
                                            if cs_type_dn == ImmHelper.getName(svc_type_cs_types_dn):
                                                assert bindings[sg_dn][comp_type_id], "Error in model, SaAmfSutCompType was not fetched before SaAmfSvcTypeCSType"
                                                # Adding to BINDINGS model binding object SaAmfSvcTypeCSTypes,    dn: safMemberCSType=safVersion=1\,
                                                #                                                                     safCSType=ERIC-<component_unique_id>,
                                                #                                                                     safVersion=1, safSvcType=ERIC-<service_unique_id>
                                                bindings[sg_dn][comp_type_id].addObject(svc_type_cs_types)

                        for svc_type_cs_types_dn in sg_base_model.getObjects(_class=AMFModel.SaAmfSvcTypeCSTypes):
                            # Removing from SG model binding object SaAmfSvcTypeCSTypes,    dn: safMemberCSType=safVersion=1\,
                            #                                                                   safCSType=ERIC-<component_unique_id>,
                            #                                                                   safVersion=1, safSvcType=ERIC-<service_unique_id>
                            sg_base_model.removeObject(svc_type_cs_types_dn)

                        for csi_dn in sg_base_model.getObjects(_class=AMFModel.SaAmfCSI):
                            # Removing from SG model binding object SaAmfCSI,    dn: safCsi=<component_instance_name>,
                            #                                                        safSi=<redundancy_model_name>-<service_instance_id>,
                            #                                                        safApp=ERIC-<service_unique_id>
                            sg_base_model.removeObject(csi_dn)

                        for csi_dn in sg_base_model.getObjects(_class=AMFModel.SaAmfCSIAttribute):
                            # Removing from SG model binding object SaAmfCSIAttribute,    dn: safCsiAttr=<attribute_name>
                            #                                                                 safCsi=<component_instance_name>,
                            #                                                                 safSi=<redundancy_model_name>-<service_instance_id>,
                            #                                                                 safApp=ERIC-<service_unique_id>
                            sg_base_model.removeObject(csi_dn)

    def calc_instances_removed_from_base(self):
        rem_from_base = {}
        fun_sv_related = [
            AMFTools.generateAppBaseTypeDn,
            AMFTools.getSGBaseTypeDnFromUnit,
            AMFTools.getSUBaseTypeDnFromUnit,
            AMFTools.getSvcBaseTypeDnFromUnit,
        ]
        fun_comp_related = [
            AMFTools.getCompBaseTypeDnFromUnit,
            AMFTools.getCSBaseTypeDnFromUnit,
        ]
        for app_base_type_dn in self._merged_app_base_type_dns:
            model = AMFModel.AMFModel()
            app_dn = AMFModel.SaAmfApplication.createDn(ImmHelper.getName(app_base_type_dn))
            # instances
            for ent in self._base_amf_model.getSubtree(app_dn):
                if ent not in self._target_amf_model.getSubtree(app_dn):
                    model._objects[ent] = self._base_amf_model.getObject(ent)
            unit_name = AMFTools.getUnitIdFromDn(app_base_type_dn)
            if app_dn in self._base_amf_model.getObjects() and app_dn not in self._target_amf_model.getObjects():
                model._objects[app_dn] = self._base_amf_model.getObject(app_dn)
            # types
            for f in fun_sv_related:
                dn = f(unit_name)
                for ent in self._base_amf_model.getSubtree(dn):
                    if ent not in self._target_amf_model.getSubtree(dn):
                        model._objects[ent] = self._base_amf_model.getObject(ent)
                if dn in self._base_amf_model.getObjects() and dn not in self._target_amf_model.getObjects():
                    model._objects[dn] = self._base_amf_model.getObject(dn)
            model.getObjects(AMFModel.SaAmfSutCompType)
            for sutCompType in model.getObjects(AMFModel.SaAmfSutCompType).values():
                compTypeDn = sutCompType.getName()
                comp_uid = AMFTools.getUnitIdFromDn(compTypeDn)
                for f in fun_comp_related:
                    dn = f(comp_uid)
                    for ent in self._base_amf_model.getSubtree(dn):
                        if ent not in self._target_amf_model.getSubtree(dn):
                            model._objects[ent] = self._base_amf_model.getObject(ent)
                    if dn in self._base_amf_model.getObjects() and dn not in self._target_amf_model.getObjects():
                        model._objects[dn] = self._base_amf_model.getObject(dn)

            rem_from_base[app_base_type_dn] = model
        return rem_from_base

    def calc_bundles_removed_from_base(self):
        ret = {}
        removed_bundles = set(self._base_amf_model.getObjects(AMFModel.SaAmfNodeSwBundle)) - \
            set(self._target_amf_model.getObjects(AMFModel.SaAmfNodeSwBundle))
        for bundle_dn in removed_bundles:
            bundle = ImmHelper.getName(bundle_dn)
            node = ImmHelper.getName(ImmHelper.getParentDn(bundle_dn))
            if bundle not in ret:
                ret[bundle] = set()
            ret[bundle].add(node)
        return ret
