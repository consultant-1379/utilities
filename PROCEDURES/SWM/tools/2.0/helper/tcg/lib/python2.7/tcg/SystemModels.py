import logging
from CSMModel import CSMModel
import CgtConstants
import CSMConstants
from utils.logger_tcg import tcg_error
from csm_units import component
from csm_units import service
from csm_units import function
from csm_units import role
from csm_units import system
from model_context import ModelContextData
from tcg.utils.exceptions import TcgException


class SystemModels():
    baseCSMModel    = None
    targetCSMModel  = None

    def __init__(self):

        ''' Constructor '''

    @staticmethod
    def setBaseCSMModel(baseModelFiles, modelContextData, online_adapter = None) :
        SystemModels.baseCSMModel = CSMModel(modelContextData)
        SystemModels.baseCSMModel.generateCSMUnitInstances(baseModelFiles, online_adapter=online_adapter)

    @staticmethod
    def setTargetCSMModel(targetModelFiles, modelContextData, online_adapter = None) :
        SystemModels.targetCSMModel = CSMModel(modelContextData)
        SystemModels.targetCSMModel.generateCSMUnitInstances(targetModelFiles, config_base=SystemModels.baseCSMModel, online_adapter=online_adapter)

    @staticmethod
    def finalizeBaseCSMModel(online_adapter=None):
        SystemModels.baseCSMModel.finalize_model(True, online_adapter)
        # SystemModels.__try_to_use_site_dependent_information()
        # SystemModels.__compare_base_target_system()

    @staticmethod
    def finalizeTargetCSMModel(online_adapter=None):
        SystemModels.targetCSMModel.finalize_model(False, online_adapter)
        SystemModels.__try_to_use_site_dependent_information()
        SystemModels.__compare_base_target_system()
        logging.debug("Target CSM model status when set target csm model")
        logging_target_model_change_status()

    @staticmethod
    def __try_to_use_site_dependent_information():
        if SystemModels.targetCSMModel:
            SystemModels.targetCSMModel.copy_site_dependent_information(SystemModels.baseCSMModel)

    @staticmethod
    def __compare_base_target_system():
        """
        Compare CSM unit between base and target model, and set status flag on
        target CSM model units.
        """
        if not SystemModels.baseCSMModel or not SystemModels.targetCSMModel:
            # No base CSM model is an installation.
            # All CSM units is set to install by default, no extra set needed.
            # No target CSM model means it haven't been parsed.
            return
        SystemModels.__compare_system()
        SystemModels.__compare_roles()
        SystemModels.__compare_functions()
        SystemModels.__compare_services()
        SystemModels.__compare_components()
        SystemModels.__upgrade_availability_check()

    @staticmethod
    def __compare_system():
        base = SystemModels.baseCSMModel.getSystem()
        target = SystemModels.targetCSMModel.getSystem()
        if base and target:
            if target != base:
                target.set_upgrade()
            else:
                target.set_unchange()
        elif base and not target:
            # Remove system? undefined behavior.
            tcg_error("Remove system {uid} is not supported by TCG.".format(uid=base.getUid()))
            return
        elif not base and target:
            target.set_install()
        else:
            tcg_error("Neither base nor target system is detected by TCG.")
            return

    @staticmethod
    def __common_compare_function(traversal, get_method):
        for unit in traversal(SystemModels.targetCSMModel):
            if unit in SystemModels.baseCSMModel:
                base_unit = get_method(SystemModels.baseCSMModel, unit.getUid())
                if unit.check_for_upgrade(base_unit):
                     unit.set_upgrade()
                else:
                    unit.set_unchange()
            else:
                unit.set_install()
        for unit in traversal(SystemModels.baseCSMModel):
            if unit not in SystemModels.targetCSMModel:
                unit.set_removed()

    @staticmethod
    def __compare_roles():
        SystemModels.__common_compare_function(
            lambda m: m.roles_in_system(),
            lambda m, uid: m.get_role_in_system(uid))

    @staticmethod
    def __compare_functions():
        SystemModels.__common_compare_function(
            lambda m: m.functions_in_system(),
            lambda m, uid: m.get_function_in_system(uid))

    @staticmethod
    def __compare_services():
        SystemModels.__common_compare_function(
            lambda m: m.services_in_system(),
            lambda m, uid: m.get_service_in_system(uid))

    @staticmethod
    def __compare_components():
        SystemModels.__common_compare_function(
            lambda m: m.components_in_system(),
            lambda m, uid: m.get_component_in_system(uid))

    @staticmethod
    def __common_csm_unit_status_check_method(obj, obj_type, traversal, which_check):
        """
        Return CSM Unit object obj's which_check method return on target CSM model.
        Argument obj can be UID string or obj_type object.
        """
        if type(obj) is not str and type(obj) is not obj_type:
            tcg_error("Invalid csm unit status check argument. Input argument should be string or CSM Unit object.")
            return False
        uid = obj
        if type(obj) is obj_type:
            uid = obj.getUid()
        for o in traversal(SystemModels.targetCSMModel):
            if o.getUid() == uid:
                return which_check(o)
        return False

    @staticmethod
    def __common_csm_unit_delete_detect(obj, obj_type, traversal):
        """
        Return True if the object is deleted on target CSM model.
        """
        if not SystemModels.baseCSMModel:
            # Cant perform delete in installation campaign
            return False
        uid = obj
        if type(obj) is obj_type:
            uid = obj.getUid()
        for o in traversal(SystemModels.baseCSMModel):
            if o.getUid() == uid and o not in SystemModels.targetCSMModel:
                return True
        return False

    @staticmethod
    def service_to_be_installed(sv):
        """
        Return True if sv should be consider as install in target CSM model
        Argument sv can be service UID string or Service object.
        """
        return SystemModels.__common_csm_unit_status_check_method(
            sv,
            service.Service,
            lambda m: m.services_in_system(),
            lambda o: o.is_install())

    @staticmethod
    def if_service_is_upgrade(sv):
        """
        Return True if sv should be consider as upgrade in target CSM model
        Argument sv can be service UID string or Service object.
        """
        return SystemModels.__common_csm_unit_status_check_method(
            sv,
            service.Service,
            lambda m: m.services_in_system(),
            lambda o: o.is_upgrade())

    @staticmethod
    def if_service_is_unchange(sv):
        """
        Return True if sv should be consider as unchange in target CSM model
        Argument sv can be service UID string or Service object.
        """
        return SystemModels.__common_csm_unit_status_check_method(
            sv,
            service.Service,
            lambda m: m.services_in_system(),
            lambda o: o.is_unchange())

    @staticmethod
    def if_service_is_delete(sv):
        """
        Return True if sv should be consider as delete in target CSM model
        Argument sv can be service UID string or Service object.
        """
        return SystemModels.__common_csm_unit_delete_detect(
            sv,
            service.Service,
            lambda m: m.services_in_system())

    @staticmethod
    def component_to_be_installed(ct):
        """
        Return True if ct should be consider as install in target CSM model
        Argument ct can be component UID string or Component object.
        """
        return SystemModels.__common_csm_unit_status_check_method(
            ct,
            component.Component,
            lambda m: m.components_in_system(),
            lambda o: o.is_install())

    @staticmethod
    def if_component_is_upgrade(ct):
        """
        Return True if ct should be consider as upgrade in target CSM model
        Argument ct can be component UID string or Component object.
        """
        return SystemModels.__common_csm_unit_status_check_method(
            ct,
            component.Component,
            lambda m: m.components_in_system(),
            lambda o: o.is_upgrade())

    @staticmethod
    def if_component_is_unchange(ct):
        """
        Return True if ct should be consider as unchange in target CSM model
        Argument ct can be component UID string or Component object.
        """
        return SystemModels.__common_csm_unit_status_check_method(
            ct,
            component.Component,
            lambda m: m.components_in_system(),
            lambda o: o.is_unchange())

    @staticmethod
    def if_component_is_delete(ct):
        """
        Return True if ct should be consider as delete in target CSM model
        Argument ct can be component UID string or Component object.
        """
        return SystemModels.__common_csm_unit_delete_detect(
            ct,
            component.Component,
            lambda m: m.components_in_system())

    @staticmethod
    def role_to_be_installed(ro):
        """
        Return True if role ro should be consider as install in target CSM model
        Argument ro can be role UID string or Role object.
        """
        return SystemModels.__common_csm_unit_status_check_method(
            ro,
            role.Role,
            lambda m: m.roles_in_system(),
            lambda o: o.is_install())

    @staticmethod
    def if_role_is_upgrade(ro):
        """
        Return True if role should be consider as upgrade in target CSM model
        Argument ro can be role UID string or Role object.
        """
        return SystemModels.__common_csm_unit_status_check_method(
            ro,
            role.Role,
            lambda m: m.roles_in_system(),
            lambda o: o.is_upgrade())

    @staticmethod
    def if_role_is_unchange(ro):
        """
        Return True if role should be consider as unchange in target CSM model
        Argument ro can be role UID string or Role object.
        """
        return SystemModels.__common_csm_unit_status_check_method(
            ro,
            role.Role,
            lambda m: m.roles_in_system(),
            lambda o: o.is_unchange())

    @staticmethod
    def if_role_is_delete(ro):
        """
        Return True if role should be consider as delete in target CSM model
        Argument ro can be role UID string or Role object.
        """
        return SystemModels.__common_csm_unit_delete_detect(
            ro,
            role.Role,
            lambda m: m.roles_in_system())

    @staticmethod
    def __component_upgrade_availability_check():
        for comp in SystemModels.baseCSMModel.components_in_system():
            if SystemModels.if_component_is_upgrade(comp):
                target_comp = SystemModels.targetCSMModel.get_component_in_system(comp.getUid())
                if not target_comp.upgrade_availability_check(comp):
                    logging.error("Component {uid} have illegal change in upgrade.".format(uid=comp.getUid()))
                    return False
        return True

    @staticmethod
    def __service_upgrade_availability_check():
        for serv in SystemModels.baseCSMModel.services_in_system():
            if SystemModels.if_service_is_upgrade(serv):
                target_serv = SystemModels.targetCSMModel.get_service_in_system(serv.getUid())
                if not target_serv.upgrade_availability_check(serv):
                    logging.error("Service {uid} have illegal change in upgrade.".format(uid=serv.getUid()))
                    return False
        return True

    @staticmethod
    def __function_upgrade_availability_check():
        # No need to check function change.
        return True

    @staticmethod
    def __role_upgrade_availability_check():
        for ro in SystemModels.baseCSMModel.roles_in_system():
            if SystemModels.if_role_is_delete(ro):
                logging.error("Not allowed to delete role {uid}".format(uid=ro.getUid()))
                return False
            elif SystemModels.if_role_is_upgrade(ro):
                target_role = SystemModels.targetCSMModel.get_role_in_system(ro.getUid())
                if not target_role.upgrade_availability_check(ro):
                    logging.error("Role {uid} have illegal change in upgrade.".format(uid=ro.getUid()))
                    return False
        return True

    @staticmethod
    def __system_upgrade_availability_check():
        # No need to check system change.
        return True

    @staticmethod
    def __special_upgrade_availability_check():
        # TODO: What is special cases? Something like environment attributes
        return True

    @staticmethod
    def __upgrade_availability_check():
        """
        Check every CSM parameter change in upgrade to make sure it is
        allowed according to CSM upgrade specification.
        Throw TcgException for not allowed upgrade change.
        """
        if not SystemModels.baseCSMModel or not SystemModels.targetCSMModel:
            # Not upgrade
            return
        if not (SystemModels.__component_upgrade_availability_check() and
                SystemModels.__service_upgrade_availability_check() and
                SystemModels.__function_upgrade_availability_check() and
                SystemModels.__role_upgrade_availability_check() and
                SystemModels.__system_upgrade_availability_check() and
                SystemModels.__special_upgrade_availability_check()
                ):
            raise TcgException("Upgrade availability check fail.")

    @staticmethod
    def generate_target_component_allocations():
        if not SystemModels.targetCSMModel:
            return {}
        return SystemModels.targetCSMModel.generate_component_allocations()

    @staticmethod
    def generate_base_component_allocations(baseAmfModel):
        if not SystemModels.baseCSMModel:
            return {}
        return SystemModels.baseCSMModel.generate_component_allocations(baseAmfModel)

    @staticmethod
    def get_component_allcated_services_on_target(comp):
        if not SystemModels.targetCSMModel:
            return []
        return SystemModels.targetCSMModel.get_component_allcated_services(comp)


def __unit_status(unit):
    if unit.is_install():
        return "INSTALL"
    elif unit.is_upgrade():
        return "UPGRADE"
    elif unit.is_unchange():
        return "unchange"
    else:
        return "-UNKNOWN-"


def logging_target_model_change_status():
    logging.debug("System UID {uid} status {sta}".format(uid=SystemModels.targetCSMModel.getSystem().getUid(), sta=__unit_status(SystemModels.targetCSMModel.getSystem())))
    for r in SystemModels.targetCSMModel.roles_in_system():
        logging.debug("Role UID {uid} status {sta}".format(uid=r.getUid(), sta=__unit_status(r)))
    for f in SystemModels.targetCSMModel.functions_in_system():
        logging.debug("Function UID {uid} status {sta}".format(uid=f.getUid(), sta=__unit_status(f)))
    for s in SystemModels.targetCSMModel.services_in_system():
        logging.debug("Service UID {uid} status {sta}".format(uid=s.getUid(), sta=__unit_status(s)))
    for c in SystemModels.targetCSMModel.components_in_system():
        logging.debug("Component UID {uid} status {sta}".format(uid=c.getUid(), sta=__unit_status(c)))

