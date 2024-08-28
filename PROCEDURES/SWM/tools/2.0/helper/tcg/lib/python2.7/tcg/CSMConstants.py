import AMFConstants
import sys
import logging

from utils.logger_tcg import tcg_error

#CSM

CONFIG_ATTRIBUTE_MANAGER_AM_MODEL        = "AM_MODEL"
CONFIG_ATTRIBUTE_MANAGER_LINUX_ENV       = "LINUX_ENV"

AVAILABILTY_MANAGER_AMF                  = "AMF"
AVAILABILTY_MANAGER_CDS                  = "CDS"
AVAILABILTY_MANAGER_NONE                 = "NONE"
AVAILABILTY_VALID_OPTONS = [AVAILABILTY_MANAGER_AMF, AVAILABILTY_MANAGER_CDS, AVAILABILTY_MANAGER_NONE]

COMPONENT_CONTROL_POLICY_SIMPLE          = "SIMPLE"
COMPONENT_CONTROL_POLICY_ADVANCED        = "ADVANCED"
COMPONENT_CONTROL_POLICY_VALID_OPTIONS   = [COMPONENT_CONTROL_POLICY_SIMPLE, COMPONENT_CONTROL_POLICY_ADVANCED]

NODE_ACTIVE_ONE                         = "ONE"
NODE_ACTIVE_MANY                        = "MANY"
NODE_STANDBY_ONE                        = "ONE"
NODE_STANDBY_MANY                       = "MANY"
NODE_STANDBY_NONE                       = "NONE"
NODE_ACTIVE_STANDBY_YES                 = "YES"
NODE_ACTIVE_STANDBY_NO                  = "NO"
NODE_ACTIVE_VALID_OPTIONS = [NODE_ACTIVE_ONE, NODE_ACTIVE_MANY]
NODE_STANDBY_VALID_OPTIONS = [NODE_STANDBY_ONE, NODE_STANDBY_MANY, NODE_STANDBY_NONE]
NODE_ACTIVE_STANDBY_VALID_OPTIONS = [NODE_ACTIVE_STANDBY_YES, NODE_ACTIVE_STANDBY_NO]

CLUSTER_ACTIVE_ONE                      = "ONE"
CLUSTER_ACTIVE_MANY                     = "MANY"
CLUSTER_STANDBY_ONE                     = "ONE"
CLUSTER_STANDBY_MANY                    = "MANY"
CLUSTER_STANDBY_NONE                    = "NONE"
CLUSTER_ACTIVE_VALID_OPTIONS = [CLUSTER_ACTIVE_ONE, CLUSTER_ACTIVE_MANY]
CLUSTER_STANDBY_VALID_OPTIONS = [CLUSTER_STANDBY_ONE, CLUSTER_STANDBY_MANY, CLUSTER_STANDBY_NONE]

RECOVERY_POLICY_COMPONENT_RESTART       = 'COMPONENT_RESTART'
RECOVERY_POLICY_COMPONENT_FAILOVER      = 'COMPONENT_FAILOVER'
RECOVERY_POLICY_NODE_SWITCHOVER         = 'NODE_SWITCHOVER'
RECOVERY_POLICY_NODE_FAILOVER           = 'NODE_FAILOVER'
RECOVERY_POLICY_NODE_FAILFAST           = 'NODE_FAILFAST'
RECOVERY_POLICY_VALID_OPTIONS = [RECOVERY_POLICY_COMPONENT_RESTART, RECOVERY_POLICY_COMPONENT_FAILOVER, RECOVERY_POLICY_NODE_SWITCHOVER, RECOVERY_POLICY_NODE_FAILOVER, RECOVERY_POLICY_NODE_FAILFAST]

EXTERNAL_DEFAULT                        = "NO"

FORMAT_RULE_IPV4 = 'ipv4'
FORMAT_RULE_IPV6 = 'ipv6'
FORMAT_RULE_REGEXP = 'regexp'
FORMAT_RULE_PATH = 'path'
FORMAT_RULE_STRING = 'string'
FORMAT_RULE_DIGITS = 'digits'
FORMAT_RULE_URL = 'url'
FORMAT_RULE_VALID_OPTIONS = [ FORMAT_RULE_IPV4, FORMAT_RULE_IPV6, FORMAT_RULE_REGEXP, FORMAT_RULE_PATH, FORMAT_RULE_STRING, FORMAT_RULE_DIGITS, FORMAT_RULE_URL ]

STRING_YES = 'YES'
STRING_NO = 'NO'

STRING_BOOL_OPTIONS = [STRING_YES, STRING_NO]

CSM_VER_MINUMUM_MAJOR = 1
CSM_VER_MAXIMUM_MAJOR = 1
CSM_VER_MINUMUM_MINOR = 0
CSM_VER_MAXIMUM_MINOR = 1


def validateAndGetBool(inputBool, tagName):
    """
    This function is needed to provide extra flexibility in the parsing of tags
    that admit binary values. TCG will accept yes, no, YES, NO and any combination
    of upper and lower case for the strings 'YES' and 'NO'
    None is not accepted. We assume that if the tag is defined, a valid value must
    be provided. If the tag is optional and has a default value, it should not
    be defined at all to use the default value.
    """
    if (inputBool is None):
        tcg_error('Empty value for tag {tag}. Use a value from the following list: {valid}'
                  .format(tag=tagName, valid=STRING_BOOL_OPTIONS))

    if isinstance(inputBool, bool):
        return inputBool

    if isinstance(inputBool, basestring) and inputBool.upper() in STRING_BOOL_OPTIONS:
        return inputBool.upper() == STRING_YES

    tcg_error('{val} is not a valid option for {tag}. Use a value from the following list: {valid}'
                  .format(val=inputBool, tag=tagName, valid=STRING_BOOL_OPTIONS))

# ----------------------------------------------------------------------------

VALID_MULTIPLICITY_COMBINATION_1 = {'nodeActive' : NODE_ACTIVE_ONE, 'nodeStandby' : NODE_STANDBY_NONE, 'nodeActiveStandby' : NODE_ACTIVE_STANDBY_NO,
     'clusterActive' : CLUSTER_ACTIVE_ONE, 'clusterStandby' : CLUSTER_STANDBY_NONE}

VALID_MULTIPLICITY_COMBINATION_2 = {'nodeActive' : NODE_ACTIVE_ONE, 'nodeStandby' : NODE_STANDBY_NONE, 'nodeActiveStandby' : NODE_ACTIVE_STANDBY_NO,
 'clusterActive' : CLUSTER_ACTIVE_MANY, 'clusterStandby' : CLUSTER_STANDBY_NONE}

VALID_MULTIPLICITY_COMBINATION_3 = {'nodeActive' : NODE_ACTIVE_MANY, 'nodeStandby' : NODE_STANDBY_NONE, 'nodeActiveStandby' : NODE_ACTIVE_STANDBY_NO,
 'clusterActive' : CLUSTER_ACTIVE_MANY, 'clusterStandby' : CLUSTER_STANDBY_NONE}

VALID_MULTIPLICITY_COMBINATION_4 = {'nodeActive' : NODE_ACTIVE_ONE, 'nodeStandby' : NODE_STANDBY_ONE, 'nodeActiveStandby' : NODE_ACTIVE_STANDBY_NO,
 'clusterActive' : CLUSTER_ACTIVE_ONE, 'clusterStandby' : CLUSTER_STANDBY_ONE}

VALID_MULTIPLICITY_COMBINATION_5 = {'nodeActive' : NODE_ACTIVE_ONE, 'nodeStandby' : NODE_STANDBY_ONE, 'nodeActiveStandby' : NODE_ACTIVE_STANDBY_NO,
 'clusterActive' : CLUSTER_ACTIVE_MANY, 'clusterStandby' : CLUSTER_STANDBY_MANY}

VALID_MULTIPLICITY_COMBINATION_6 = {'nodeActive' : NODE_ACTIVE_MANY, 'nodeStandby' : NODE_STANDBY_MANY, 'nodeActiveStandby' : NODE_ACTIVE_STANDBY_YES,
 'clusterActive' : CLUSTER_ACTIVE_MANY, 'clusterStandby' : CLUSTER_STANDBY_MANY}

VALID_MULTIPLICITY_COMBINATIONS = [
                                   VALID_MULTIPLICITY_COMBINATION_1,
                                   VALID_MULTIPLICITY_COMBINATION_2,
                                   VALID_MULTIPLICITY_COMBINATION_3,
                                   VALID_MULTIPLICITY_COMBINATION_4,
                                   VALID_MULTIPLICITY_COMBINATION_5,
                                   VALID_MULTIPLICITY_COMBINATION_6
                                  ]

def getMultiplicityCombinationNumber(combination) :
    if combination == VALID_MULTIPLICITY_COMBINATION_1 :
        return '1'
    if combination == VALID_MULTIPLICITY_COMBINATION_2 :
        return '2'
    if combination == VALID_MULTIPLICITY_COMBINATION_3 :
        return '3'
    if combination == VALID_MULTIPLICITY_COMBINATION_4 :
        return '4'
    if combination == VALID_MULTIPLICITY_COMBINATION_5 :
        return '5'
    if combination == VALID_MULTIPLICITY_COMBINATION_6 :
        return '6'

    return None

#MULTIPLICITY_POLICY TO REDUNDANCY_MODEL MAPPING

MULTIPLICITY_TO_REDUNDANCY_MODELS = {
                       '1' : AMFConstants.REDUNDANCY_MODEL_NAME_NR,
                       '2' : AMFConstants.REDUNDANCY_MODEL_NAME_NWA,#'NR, NWA',
                       '3' : AMFConstants.REDUNDANCY_MODEL_NAME_NWA,#'NR, NWA',
                       '4' : AMFConstants.REDUNDANCY_MODEL_NAME_2N,
                       '5' : AMFConstants.REDUNDANCY_MODEL_NAME_2N,
                       '6' : AMFConstants.REDUNDANCY_MODEL_NAME_2N
                    }

#-------------------------------------------------------------------------------------------------


SUPPORTED_CAPABILITY_COMBINATION_1 = {'nodeActive' : NODE_ACTIVE_MANY, 'nodeStandby' : NODE_STANDBY_MANY,
                                       'nodeActiveStandby' : NODE_ACTIVE_STANDBY_YES,
                                       'controlPolicyType' : COMPONENT_CONTROL_POLICY_ADVANCED}
SUPPORTED_CAPABILITY_COMBINATION_2 = {'nodeActive' : NODE_ACTIVE_ONE, 'nodeStandby' : NODE_STANDBY_ONE,
                                       'nodeActiveStandby' : NODE_ACTIVE_STANDBY_NO,
                                       'controlPolicyType' : COMPONENT_CONTROL_POLICY_ADVANCED}
SUPPORTED_CAPABILITY_COMBINATION_3 = {'nodeActive' : NODE_ACTIVE_MANY, 'nodeStandby' : NODE_STANDBY_NONE,
                                       'nodeActiveStandby' : NODE_ACTIVE_STANDBY_NO,
                                       'controlPolicyType' : COMPONENT_CONTROL_POLICY_ADVANCED}
SUPPORTED_CAPABILITY_COMBINATION_4 = {'nodeActive' : NODE_ACTIVE_ONE, 'nodeStandby' : NODE_STANDBY_NONE,
                                       'nodeActiveStandby' : NODE_ACTIVE_STANDBY_NO,
                                       'controlPolicyType' : COMPONENT_CONTROL_POLICY_ADVANCED}
SUPPORTED_CAPABILITY_COMBINATION_5 = {'nodeActive' : '*', 'nodeStandby' : '*',
                                       'nodeActiveStandby' : '*',
                                       'controlPolicyType' : COMPONENT_CONTROL_POLICY_SIMPLE}

SUPPORTED_CAPABILITY_COMBINATIONS = [
                                   SUPPORTED_CAPABILITY_COMBINATION_1,
                                   SUPPORTED_CAPABILITY_COMBINATION_2,
                                   SUPPORTED_CAPABILITY_COMBINATION_3,
                                   SUPPORTED_CAPABILITY_COMBINATION_4,
                                   SUPPORTED_CAPABILITY_COMBINATION_5,
                                  ]

def getCapabilityCombinationNumber(combination) :
    if combination == SUPPORTED_CAPABILITY_COMBINATION_1 :
        return '1'
    if combination == SUPPORTED_CAPABILITY_COMBINATION_2 :
        return '2'
    if combination == SUPPORTED_CAPABILITY_COMBINATION_3 :
        return '3'
    if combination == SUPPORTED_CAPABILITY_COMBINATION_4 :
        return '4'
    if combination == SUPPORTED_CAPABILITY_COMBINATION_5 :
        return '5'

    return None

COMBINATION_TO_CAPABILITY_MODELS = {
                       '1' : AMFConstants.CAPABILITY_NAME_X_ACTIVE_AND_Y_STANDBY,
                       '2' : AMFConstants.CAPABILITY_NAME_ONE_ACTIVE_OR_ONE_STANDBY,
                       '3' : AMFConstants.CAPABILITY_NAME_X_ACTIVE,
                       '4' : AMFConstants.CAPABILITY_NAME_1_ACTIVE,
                       '5' : AMFConstants.CAPABILITY_NAME_NON_PRE_INSTANTIABLE,
                    }

CONFIGURATION_DATA_TYPE_INITIAL = 'INITIAL'
CONFIGURATION_DATA_TYPE_RESOURCE = 'RESOURCE'
CONFIGURATION_DATA_TYPE_OTHER = 'OTHER'

#-------------------------------------------------------------------------------------------------------------------------------------------

def isValidMultiplicityPolicy(nodeActive = None, nodeStandby = None, nodeActiveStandby = None,
                              clusterActive = None, clusterStandby = None):
    '''
    Checks if the passed values form a valid multiplicity combination
    '''
    currentMultiplicity = {'nodeActive' : nodeActive.upper(), 'nodeStandby' : nodeStandby.upper(),
                           'nodeActiveStandby' : nodeActiveStandby.upper(),
                           'clusterActive' : clusterActive.upper(), 'clusterStandby' : clusterStandby.upper()
                          }

    if currentMultiplicity in VALID_MULTIPLICITY_COMBINATIONS :
        return True
    else :
        return False

'''
def isValidMultiplicityPolicy2(nodeActive = None, nodeStandby = None, nodeActiveStandby = None,
                              clusterActive = None, clusterStandby = None):

    #Checks if the passed values form a valid multiplicity combination

    ONE  = 1
    NONE = 0
    MANY = 2

    #check for active policy
    if eval(nodeActive) > eval(clusterActive) :
        return False

    #check for standby policy
    if eval(nodeStandby) > eval(clusterStandby) :
        return False

    currentMultiplicity = {'nodeActive' : nodeActive, 'nodeStandby' : nodeStandby,
                           'nodeActiveStandby' : nodeActiveStandby,
                           'clusterActive' : clusterActive, 'clusterStandby' : clusterStandby
                          }

    if currentMultiplicity in VALID_MULTIPLICITY_COMBINATIONS :
        return True
    else :
        return False
'''

def getComponentRedundancyModel(nodeActive = None, nodeStandby = None, nodeActiveStandby = None,
                              clusterActive = None, clusterStandby = None):
    '''
    Get Component Redundancy Model from the component multiplicity policies
    '''
    currentMultiplicity = {'nodeActive' : nodeActive.upper(), 'nodeStandby' : nodeStandby.upper(),
                           'nodeActiveStandby' : nodeActiveStandby.upper(),
                           'clusterActive' : clusterActive.upper(), 'clusterStandby' : clusterStandby.upper()
                          }

    multiplicityNumber = getMultiplicityCombinationNumber(currentMultiplicity)

    return MULTIPLICITY_TO_REDUNDANCY_MODELS[multiplicityNumber] \
            if MULTIPLICITY_TO_REDUNDANCY_MODELS.has_key(multiplicityNumber) else None


def getServiceRedundancyModel(componentRedundancyModels = [], serviceuid = ""):
    '''
    Get Service Redundancy Model from the component redundancy models
    '''

    redundancy_group_2N         = []
    redundancy_group_NR_NWA     = []
    unknwon_redundancy_group    = []

    for redundancyModel in componentRedundancyModels :
        if redundancyModel == AMFConstants.REDUNDANCY_MODEL_NAME_2N:
            redundancy_group_2N.append(redundancyModel)
        elif redundancyModel == AMFConstants.REDUNDANCY_MODEL_NAME_NR or redundancyModel == AMFConstants.REDUNDANCY_MODEL_NAME_NWA :
            redundancy_group_NR_NWA.append(redundancyModel)
        else:
            unknwon_redundancy_group.append(redundancyModel)

    if unknwon_redundancy_group:
        tcg_error("Service %s contains components with unsupported redundancy models: %s " % (serviceuid, unknwon_redundancy_group))
    if redundancy_group_2N and redundancy_group_NR_NWA :
        tcg_error("Service %s contains components with conflicting redundancy models: %s " % (serviceuid, componentRedundancyModels))

    if redundancy_group_2N :
        return AMFConstants.REDUNDANCY_MODEL_NAME_2N
    elif redundancy_group_NR_NWA :
        '''According to CSM to AMF mapping spec, TCG always try to replace
        NR with NWA redundancy model.
        '''
        return AMFConstants.REDUNDANCY_MODEL_NAME_NWA
    return None


def getComponentDisableRestart(serviceRedundancyModel = None):
    '''
    Get the component disable restart if the
    component restart should be disabled as part of recovery
    '''
    componentDisableRestart = 'SA_FALSE'

    #change the value based on the redundancy model

    return componentDisableRestart

def getComponentCapabilityModel(nodeActive = None, nodeStandby = None, nodeActiveStandby = None,
                              controlPolicyType = COMPONENT_CONTROL_POLICY_SIMPLE) :
                              #clusterActive = None, clusterStandby = None):
    '''
    Get Component Redundancy Model from the component multiplicity policies
    '''
    if controlPolicyType.upper() == COMPONENT_CONTROL_POLICY_SIMPLE :
        nodeActive = '*'
        nodeStandby = '*'
        nodeActiveStandby = '*'

    combination = {'nodeActive' : nodeActive.upper(), 'nodeStandby' : nodeStandby.upper(),
                           'nodeActiveStandby' : nodeActiveStandby.upper(),
                           'controlPolicyType' : controlPolicyType.upper()
                          }

    combinationNumber = getCapabilityCombinationNumber(combination)

    return COMBINATION_TO_CAPABILITY_MODELS[combinationNumber] \
            if COMBINATION_TO_CAPABILITY_MODELS.has_key(combinationNumber) else None
