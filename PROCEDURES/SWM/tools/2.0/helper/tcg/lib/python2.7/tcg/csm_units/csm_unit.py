import os
import sys
import logging

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class CSMUnit(object):

    '''
    Base class for all CSM units
    '''
    def __init__(self):
        '''
        Constructor for CSMUnit
        This class contains functions that generates CDF Units from CSM Units
        '''
        # install_flag will be use in target CSM model, to indicate if it is a
        # newly added CSM unit
        self._install_flag = True
        # upgrade_flag will be use in target CSM model, to indicate if it is
        # a upgrade CSM unit
        self._upgrade_flag = False
        # removed_flag will be use in target CSM model, to indicate if it is
        # a removed CSM unit
        self._removed_flag = False
        # unchange_flag will be use in target CSM model, to indicate if it
        # is a unchanged CSM unit
        self._unchange_flag = False

    def set_install(self):
        self._install_flag = True
        self._upgrade_flag = False
        self._removed_flag = False
        self._unchange_flag = False

    def is_install(self):
        return self._install_flag

    def set_upgrade(self):
        self._install_flag = False
        self._upgrade_flag = True
        self._removed_flag = False
        self._unchange_flag = False

    def is_upgrade(self):
        return self._upgrade_flag

    def set_unchange(self):
        self._install_flag = False
        self._upgrade_flag = False
        self._removed_flag = False
        self._unchange_flag = True

    def is_unchange(self):
        return self._unchange_flag

    def set_removed(self):
        self._removed_flag = True
        self._install_flag = False
        self._upgrade_flag = False
        self._unchange_flag = False

    def is_removed(self):
        return self._removed_flag

    def check_for_upgrade(self, base_unit):
        # fallback behavior, use the __eq__ function defined in each unit
        return self != base_unit

    @staticmethod
    def getInstance():
        '''
        Returns instance of CSMUnit
        '''
        if not CSMUnit._instance :
            CSMUnit._instance = CSMUnit()

        return CSMUnit._instance

    '''
    Commented as this is creating some problems, just kept reference
    def __str__(self):
        return str(self.__dict__)
    '''

    def compare(self, other, excludeAttributes = []):
        differences = {}

        for attributeName, attributeValue in self.__dict__.iteritems() :
            if attributeName not in excludeAttributes :
                if attributeName not in other.__dict__.keys() :
                    differences[attributeName] = attributeValue
                    continue
                if isinstance(attributeValue, CSMUnit) :
                    diff = attributeValue.compare(other.__dict__[attributeName],
                                                  excludeAttributes = excludeAttributes
                                                  )
                    if diff != {} :
                        differences[attributeName] = diff

                else :
                    if type(attributeValue) is list and type(other.__dict__[attributeName]) is list :
                        diff = []
                        differenceFlag = True
                        for targetElement in attributeValue :
                            if isinstance(targetElement, CSMUnit) :
                                for baseElement in other.__dict__[attributeName] :
                                    temp = targetElement.compare(baseElement,
                                                                 excludeAttributes = excludeAttributes
                                                                )
                                    if temp == {} :
                                        differenceFlag = False
                                        break
                                if differenceFlag :
                                    diff.append(targetElement)

                            elif type(targetElement) in [ str, dict, None ] :
                                if targetElement not in other.__dict__[attributeName] :
                                    diff.append(targetElement)
                        if len(diff) != 0 :
                            differences[attributeName] = diff

                    elif type(attributeValue) in [ str, dict, None ] :
                        if attributeValue != other.__dict__[attributeName] :
                            differences[attributeName] = attributeValue
                            #differences[attributeName] = other.__dict__[attributeName]

        return differences

    @staticmethod
    def sort_yaml_dict(yaml_dict):
        if type(yaml_dict) is list:
            yaml_dict.sort()
        if hasattr(yaml_dict, '__iter__'):
            for item in yaml_dict:
                CSMUnit.sort_yaml_dict(item)

    @staticmethod
    def yaml_upgrade_availability_check(id, base, target, cau):
        """
        Return True when pass the upgrade availability check.
        id     - the tag for the whole yaml dict
        base   - the base yaml dict
        target - the target yaml dict
        cau    - must be None or a tuple which hold two values:
            cau[0] - boolean, indicate it is a cau flag
            cau[1] - default value for this attribute(if absent), None for no default value
            cau[2] - dict, leaf tags cau
        It not must to list an attribute in cau if it is CAU and all
        it's leafs are CAU.
        The parent node marked as None-CAU is logically equal to
        all it's leafs are None-CAU, but if any of it's leaf node
        has default value, you should mark the parent node as CAU,
        then mark all it's leafs as None-CAU, and set default value
        for it's leaf node.
        """
        rt = True
        if cau is None:
            return
        if not cau[0] and cau[1] is None and base != target:
            logging.error("Change attribute {uid} in CSM model is not allowed.".format(uid=id))
            rt = False
        if not cau[0] and cau[1] is not None:
            c_base = base if base else cau[1]
            c_target = target if target else cau[1]
            if c_base != c_target:
                logging.error("Change attribute {uid} in CSM model is not allowed.".format(uid=id))
                rt = False
        if cau[0] and cau[2] is not None:
            for k in cau[2]:
                child_base = None
                try:
                    child_base = base[k]
                except:
                    pass
                child_target = None
                try:
                    child_target = target[k]
                except:
                    pass
                child_id = '{p}.{c}'.format(p=id, c=k)
                child_rt = CSMUnit.yaml_upgrade_availability_check(
                    child_id, child_base, child_target, cau[2][k]
                )
                rt = False if not child_rt else rt
        return rt

    """@staticmethod
    def getRStateFromVersion(version):
        versionNumbers = version.split(".")
        rState = versionNumbers[0] + "-R" + str(int(versionNumbers[1]) + 1) + chr(int(versionNumbers[2]) + ord('A')) + versionNumbers[3]
        return rState"""
