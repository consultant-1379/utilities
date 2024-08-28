import AMFModel
from tcg import ImmHelper

from tcg.utils.logger_tcg import tcg_error


class AMFModelPostScaleTransformation(object):

    """
    When a cluster is scaled out, CMW creates new Service Units (SUs), Service
    Instances (SIs) and children objects (safComp, safSupportedCsType, safCsi,
    etc.) for the new nodes. The name of the new SUs and SIs is calculated using
    a hash (example: safSu=72db9a6ce2,safSg=NR,safApp=ERIC-brfc.brfp). This is
    different from the TCG naming convention for SUs and SIs (example:
    safSu=PL-4,safSg=NR,safApp=ERIC-brfc.brfp.)

    When TCG generates an upgrade campaign in a system that has been scaled
    out, it creates the expected SUs and SIs for the target system which are
    different from the SUs and SIs in the base systems. When TCG compares the
    base and target models, TCG believes that some SUs/SIs have been removed
    (the ones corresponding to the new nodes in the base system that contain
    the hashing) and that some SUs/SIs have been added (the ones created using
    the TCG naming convention for the new nodes). Adding and removing SUs or
    SIs during and upgrade is not a valid operation and TCG aborted the
    campaign generation.

    This class is used to solve the described problem. The strategy followed is
    to replace the TCG created objects in the target model by the existing
    objects in the base model. To achieve this, each SU and SI from the target
    model that is not in the base model is matched and replaced by the
    corresponding instance from the base
    """

    def __init__(self, base_amf_model, target_amf_model):
        self._base_amf_model = base_amf_model
        self._target_amf_model = target_amf_model

    def post_scale_transform(self):
        # Sg related transformations
        # The transform should be invoked before check
        # mismatched_SUs for handle both scale-out and
        # scale-in case.
        self._transform_SG()

        mismatched_SUs = self._get_SG_with_mismatch_in_SU()

        # When all the SG match (no mismatch) we assume that that there is
        # nothing to transform (the base has not been scaled out)
        if (len(mismatched_SUs) == 0):
            return

        # Su related transformations
        su_mapping = self._transform_DNs(mismatched_SUs)
        comp_mapping = self._transform_comps(su_mapping)
        self._transform_compType_env_attr(comp_mapping)
        self._transform_SupportedCsType(su_mapping)

        # Si related transformations
        mismatched_SIs = self._get_app_with_mismatch_in_SI()
        si_mapping = self._transform_DNs(mismatched_SIs)
        self._transform_CSIs(si_mapping)

    def _get_SG_with_mismatch_in_SU(self):
        return self._get_DNs_with_mismatch(AMFModel.SaAmfSU, SUMismatch)

    def _get_app_with_mismatch_in_SI(self):
        return self._get_DNs_with_mismatch(AMFModel.SaAmfSI, SIMismatch)

    def _get_DNs_with_mismatch(self, amf_class_type, mismatch_class_type):
        ret_value = []

        base_DNs_dict = self._base_amf_model.getObjects(amf_class_type)
        target_DNs_dict = self._target_amf_model.getObjects(amf_class_type)

        base_parent_to_child_dict = self._map_parent_to_children_DNs(base_DNs_dict.iterkeys())
        target_parent_to_child_dict = self._map_parent_to_children_DNs(target_DNs_dict.iterkeys())

        # if the parent exists in the base and target system, it should have
        # the same set of children, otherwise it is mismatch
        for parent_dn in base_parent_to_child_dict.iterkeys():
            if parent_dn in target_parent_to_child_dict:
                if (base_parent_to_child_dict[parent_dn] != target_parent_to_child_dict[parent_dn]):
                    mismatched_dn = mismatch_class_type(base_parent_to_child_dict[parent_dn],
                                                     target_parent_to_child_dict[parent_dn],
                                                     self._base_amf_model,
                                                     self._target_amf_model)
                    ret_value.append(mismatched_dn)

        return ret_value

    def _map_parent_to_children_DNs(self, dn_iterator):
        """
        This function returns a dictionary where the keys are the parent DNs of
        the DNs from the received list, and the values are sets containing all the
        children DNs for that parent. Example:
        input: [ "y=1,x=1", "y=2,x=1", "y=1,x=2" ]
        output: { "x=1": ["y=1,x=1", "y=2,x=1"],
                  "x=2": [ "y=1,x=2" ] }
        """
        ret_parent_to_child_dict = dict()

        for dn in dn_iterator:
            parent_dn = ImmHelper.getParentDn(dn)
            if parent_dn not in ret_parent_to_child_dict:
                ret_parent_to_child_dict[parent_dn] = set()
            ret_parent_to_child_dict[parent_dn].add(dn)

        return ret_parent_to_child_dict

    def _transform_DNs(self, mismatched_DNs):
        ret_base_target_dn_mapping = dict()

        for mismatch in mismatched_DNs:
            map_DNs = mismatch.transform_dn_mismatch()
            ret_base_target_dn_mapping.update(map_DNs)

        return ret_base_target_dn_mapping

    def _transform_comps(self, su_mapping):
        ret_base_target_comp_mapping = dict()
        comps_in_target_model = self._target_amf_model.getObjects(AMFModel.SaAmfComp)
        for dn, comp in comps_in_target_model.iteritems():
            parent_su = ImmHelper.getParentDn(dn)
            if parent_su in su_mapping:
                # the SU for this component has been transformed. we need to
                # transform the component
                self._target_amf_model.removeObject(dn)
                comp._dn = comp.getRdn() + "," + su_mapping[parent_su]  # intentionally violating encapsulation, sorry :-)
                self._target_amf_model.addObject(comp)
                ret_base_target_comp_mapping[dn] = comp.getDn()
        return ret_base_target_comp_mapping

    def _transform_compType_env_attr(self, comp_mapping):
        compType_in_target_model = self._target_amf_model.getObjects(AMFModel.SaAmfCompType)
        for dn, compType in compType_in_target_model.iteritems():
            for env in compType.getsaAmfCtDefCmdEnv():
                comp = env.split('=', 1)[1] if 'PROXIED_COMP_DN' in env else env
                if comp in comp_mapping:
                    compType._saAmfCtDefCmdEnv.remove(env)
                    compType.addTosaAmfCtDefCmdEnv(env.replace(comp, comp_mapping[comp]))

    def _transform_SupportedCsType(self, su_mapping):
        suppCsType_in_target_model = self._target_amf_model.getObjects(AMFModel.SaAmfCompCsType)
        for dn, comp_cs_type in suppCsType_in_target_model.iteritems():
            # DN for SaAmfCompCsType is safSupportedCsType,safComp,safSu.
            # We need the parent at level 2 to get the Su
            parent_su = ImmHelper.getParentDn(dn, level=2)
            if parent_su in su_mapping:
                # the SU for this component has been transformed. we need to
                # transform the supportedCsType
                self._target_amf_model.removeObject(dn)
                parts = ImmHelper.splitDn(dn, unescape=False)
                new_dn = parts[0] + "," + parts[1] + "," + su_mapping[parent_su]
                comp_cs_type._dn = new_dn  # intentionally violating encapsulation, sorry :-)
                self._target_amf_model.addObject(comp_cs_type)

    def _transform_CSIs(self, si_mapping):
        CSIs_in_target_model = self._target_amf_model.getObjects(AMFModel.SaAmfCSI)
        for dn, csi in CSIs_in_target_model.iteritems():
            parent_SI_dn = ImmHelper.getParentDn(dn)
            if parent_SI_dn in si_mapping:
                # the SI for this CSI has been transformed. we need to
                # transform the CSI
                self._target_amf_model.removeObject(dn)
                base_CSI = self._get_base_CSI(si_mapping[parent_SI_dn], dn)
                csi._dn = base_CSI.getDn()  # intentionally violating encapsulation, sorry :-)
                # We also need to update all the reference to this CSI
                for old_csi in CSIs_in_target_model.itervalues():
                    if dn in old_csi.getsaAmfCSIDependencies():
                        new_dependencies = [item for item in old_csi.getsaAmfCSIDependencies()
                                            if item != dn]
                        new_dependencies.append(base_CSI.getDn())
                        old_csi.updateParams({'saAmfCSIDependencies': new_dependencies}, [])
                self._target_amf_model.addObject(csi)

    def _get_base_CSI(self, parent_si_dn, csi_dn=None):
        CSIs_found = []
        CSIs_in_base_model = self._base_amf_model.getObjects(AMFModel.SaAmfCSI)
        for dn, csi in CSIs_in_base_model.iteritems():
            if ImmHelper.getParentDn(dn) == parent_si_dn:
                CSIs_found.append(csi)

        if csi_dn is None:
            if len(CSIs_found) == 1:
                return CSIs_found[0]
            else:
                tcg_error("Found {found} CSIs for SI: {siDn} but no CSI information to filter"
                    .format(found=len(CSIs_found), siDn=parent_si_dn))
        else:
            csi_pattern = ImmHelper.getRdn(csi_dn)
            amf_nodes_list = self._base_amf_model.getObjects(AMFModel.SaAmfNode)
            for node_dn in amf_nodes_list.keys():
                node = ImmHelper.getName(node_dn)
                if '-'+node == csi_pattern[-(len(node)+1):]:
                    csi_pattern = csi_pattern[:-(len(node)+1)]
                    break

            filtered_csi = [csi for csi in CSIs_found if csi_pattern in csi._dn]
            if len(filtered_csi) == 1:
                return filtered_csi[0]
            else:
                tcg_error("Expected ONE but there are {found} CSIs matched the filter"
                    .format(found=len(filtered_csi)))

    def _transform_SG(self):
        """
        CMW cleans the value of the attribute 'saAmfSGNumPrefInserviceSUs'
        from the SGs when scaling. On the other hand, TCG always sets the
        value to the amount of nodes where the SG is configured. For this
        reason, after scaling the base SG will have an empty
        'saAmfSGNumPrefInserviceSUs' while the target SG will have the
        aforementioned amount of nodes. This difference is interpreted by TCG
        as a change in the SG which is not allowed. The solution is to
        transform the target SGs to match the base SGs (cleaning the
        attribute). It should be invoked for both post-scale-out and
        post-scle-in case.
        """
        target_SGs = self._target_amf_model.getObjects(AMFModel.SaAmfSG)
        base_SGs = self._base_amf_model.getObjects(AMFModel.SaAmfSG)
        for sgDn, targetSg in target_SGs.iteritems():
            if sgDn in base_SGs:
                base_SG = base_SGs[sgDn]
                prefInServSU = base_SG.getsaAmfSGNumPrefInserviceSUs_unsafe()
                if prefInServSU is None:
                    targetSg._saAmfSGNumPrefInserviceSUs = None  # intentionally violating encapsulation, sorry :-)


class DnMismatch(object):
    def __init__(self,
                 base_DNs,
                 target_DNs,
                 base_amf_model,
                 target_amf_model):
        self._baseDNs = base_DNs
        self._targetDNs = target_DNs
        self._base_amf_model = base_amf_model
        self._target_amf_model = target_amf_model

    def transform_dn_mismatch(self):
        ret_base_target_dn_mapping = dict()

        for base_dn in self._baseDNs:
            # we only need to transform when the base DN is not in the target.
            # Otherwise, there is nothing to transform
            if (base_dn not in self._targetDNs):
                candidate_target = self._find_candidate(base_dn)
                if candidate_target is None:
                    continue
                candidate_target_dn = candidate_target.getDn()

                ret_base_target_dn_mapping[candidate_target_dn] = base_dn

                # remove the candidate with old dn and replace with the new
                # the base dn
                self._target_amf_model.removeObject(candidate_target_dn)
                candidate_target._dn = base_dn  # intentionally violating encapsulation, sorry :-)
                self._target_amf_model.addObject(candidate_target)

        return ret_base_target_dn_mapping

    def _find_candidate(self, base_dn):
        base_obj = self._base_amf_model.getObject(base_dn)

        candidate = self._find_candidate_in_target(base_obj)

        if candidate is not None:
            # we found the candidate.
            # Remove it from the list of targets to avoid two base DNs map
            # to the same single DN in target
            self._targetDNs.remove(candidate.getDn())
        return candidate

    def _find_candidate_in_target(self, base_dn):
        # this is an "abstract" method. It has to be implemented by the
        # subclasses who know how to find candidates for the particular
        # class
        assert False


class SUMismatch(DnMismatch):

    def __init__(self,
                 base_su_DNs,
                 target_su_DNs,
                 base_amf_model,
                 target_amf_model):
        DnMismatch.__init__(self,
                            base_su_DNs,
                            target_su_DNs,
                            base_amf_model,
                            target_amf_model)

    def _find_candidate_in_target(self, base_su):
        node_name_in_base_su = base_su.getsaAmfSUHostNodeOrNodeGroup()

        for target_su_dn in self._targetDNs:
            target_su = self._target_amf_model.getObject(target_su_dn)
            node_name_in_target_su = target_su.getsaAmfSUHostNodeOrNodeGroup()
            if (node_name_in_base_su == node_name_in_target_su):
                # we found the candidate.
                return target_su

        # candidate not found
        return None


class SIMismatch(DnMismatch):

    def __init__(self,
                 base_si_DNs,
                 target_si_DNs,
                 base_amf_model,
                 target_amf_model):
        DnMismatch.__init__(self,
                            base_si_DNs,
                            target_si_DNs,
                            base_amf_model,
                            target_amf_model)
        self._validate_target_SIs()

    def _validate_target_SIs(self):
        # For any App in an AMF model, it is not possible, for any one
        # individual base SI, to find an equivalent SI in the target AMF model.
        # But within any individual App, all the SIs from the target are equal,
        # so any random mapping between base and target works OK.
        # This method guarantees that the SIs in the target are equal. If for
        # some reason in the future the SIs are not equal anymore, we will need
        # a new way of mapping base SIs to target SIs (this has to be analyzed
        # when such differences exist)
        target_DNs_list = list(self._targetDNs)  # convert set to list to be able to index it
        for index in range(0, len(target_DNs_list) - 1):
            one_si = self._target_amf_model.getObject(target_DNs_list[index])
            the_next_si = self._target_amf_model.getObject(target_DNs_list[index+1])
            changes = one_si.diff(the_next_si, fullCheck=True)
            if (len(changes) > 0):
                tcg_error("The SIs in the target model are different: "
                          "{one_si}, {otherSi}".format(one_si=one_si.getDn(),
                                                      otherSi=the_next_si.getDn()))
        # if the loops ends, the validation was successful

    def _find_candidate_in_target(self, baseSi):
        # since we guarantee that the content (attributes) of all SIs are the
        # same (regardless of DN), we just return the first one that is not
        # already in the base
        for target_si_dn in self._targetDNs:
            if (target_si_dn not in self._baseDNs):
                # candidate found
                return self._target_amf_model.getObject(target_si_dn)

        # candidate not found
        return None
