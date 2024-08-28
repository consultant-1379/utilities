import ImmHelper
import AMFModel
import AMFConstants
import re
from utils.logger_tcg import tcg_error

def validateAndSetOptionalArg(func, value, validate=None, errmsg=None, convert=None):
    if value == None or value == "" :
        return
    else:
        validateAndSetMandatoryArg(func, value, validate, errmsg, convert)

def validateAndSetMandatoryArg(func, value, validate=None, errmsg=None, convert=None):
    if value == None or value == "" or value == []:
        tcg_error("Error: %s" % errmsg)

    if isinstance(value, list):
        value = " ".join(value)

    if not validate == None:
        if not validate(value):
            tcg_error("Error: %s" % errmsg)

    if not convert == None:
        func(convert(value))
    else:
        func(value)

def getProvider():
    return "ERIC"

def chopProvider(nameOrDn):
    return ImmHelper.getName(nameOrDn)[len(getProvider()) + 1:]

def splitName(nameOrDn):
    return ImmHelper.getName(nameOrDn).split("-")


def getModelVersion(version):
    # Example: R1A/2 -> R1A_2
    version = version.replace("/", "_")
    return version.replace("-", "_")

def getUnitIdFromModelName(name):
    # Example: ERIC-foo-CT_Agent -> CT/Agent
    # Could also have been CT-Agent before, we don't knoe, we don't care, should be removed later
    return splitName(name)[-1]

def getUnitNameFromModelName(name):
    # Example: ERIC-foo-CT_Agent -> foo
    return splitName(name)[-2]

def getNodeNameFromNodeDn(nodeDn):
    # Example: safAmfNode=<name>,safAmfCluster=myAmfCluster -> name
    return ImmHelper.getName(ImmHelper.splitDn(nodeDn)[0])

def getFullModelNameFromUnit(identity):
    # Example: <provider>-<identity>
    return getProvider() + "-" + identity

def getUnitIdFromDn(dn):
    # Example: safVersion=4.0.0,safCompType=ERIC-foo-CT_Agent -> CT/Agent
    return getUnitIdFromModelName(ImmHelper.getName(ImmHelper.splitDn(dn)[-1]))

def getCompTypeDnFromUnit(identity, version):
    # Example: safVersion=<version>,safCompType=ERIC-<id>
    return AMFModel.SaAmfCompType.createDn(getModelVersion(version),
                                           getCompBaseTypeDnFromUnit(identity))

def getCompBaseTypeDnFromUnit(identity):
    # Example: safCompType=ERIC-<uid>
    return AMFModel.SaAmfCompBaseType.createDn(getFullModelNameFromUnit(identity))

def getHealthcheckTypeDnFromUnit(key, identity, version):
    # Example: safHealthcheckKey=<key>,safVersion=<version>,safCompType=ERIC-<id>
    return AMFModel.SaAmfHealthcheckType.createDn(key, getCompTypeDnFromUnit(identity, version))

def getCSBaseTypeDnFromUnit(identity):
    # Example: safCSType=ERIC-<id>
    return AMFModel.SaAmfCSBaseType.createDn(getFullModelNameFromUnit(identity))

def getCSTypeDnFromUnit(identity, version):
    # Example: safVersion=<version>,safCSType=ERIC-<id>
    return AMFModel.SaAmfCSType.createDn(getModelVersion(version),
                                         getCSBaseTypeDnFromUnit(identity))

def getCtCsTypeDnFromUnit(ct_unit_id, ct_version, cst_version):
    # Example: safSupportedCsType=safVersion=<cst_version>\,safCSType=ERIC-<id>,
    #	                          safVersion=<ct_version>,safCompType=ERIC-<id>
    return AMFModel.SaAmfCtCsType.createDn(getCSTypeDnFromUnit(ct_unit_id, cst_version), getCompTypeDnFromUnit(ct_unit_id, ct_version))

def getSaSmfSwBundleDnFromUnit(sdpName):
    # Example: safSmfBundle=<sdp_name>
    return AMFModel.SaSmfSwBundle.createDn(sdpName)

def getNodeSwBundleDnFromUnit(sdpName, node=None):
    # Example: safInstalledSwBundle=safSmfBundle=<sdp_name>
    return AMFModel.SaAmfNodeSwBundle.createDn(AMFModel.SaSmfSwBundle.createDn(sdpName), node)

def getNodeSwBundleTemplateDnFromSDP(sdp):
    # Example: safInstalledSwBundle=safSmfBundle=<sdp_name>
    return AMFModel.SaAmfNodeSwBundle.createDn(AMFModel.SaSmfSwBundle.createDn(sdp), None) + ".*"

def getSvcBaseTypeDnFromUnit(identity):
    # Example: safSvcType=ERIC-<id>
    return AMFModel.SaAmfSvcBaseType.createDn(getFullModelNameFromUnit(identity))

def getSvcTypeDnFromUnit(identity, version):
    # Example: safVersion=<version>,safSvcType=ERIC-<id>
    return AMFModel.SaAmfSvcType.createDn(getModelVersion(version),
                                          getSvcBaseTypeDnFromUnit(identity))

def getSvcTypeCSTypesDnFromUnit(unit_svt_id, unit_svt_version,
                                unit_cst_id, version):
    # Example: safMemberCSType=safVersion=<cst_version>\,safCSType=ERIC-<cst_id>,
    #                          safVersion=<svt_version>,safSvcType=ERIC-<svt_id>
    return AMFModel.SaAmfSvcTypeCSTypes.createDn(getCSTypeDnFromUnit(unit_cst_id, version),
                                                 getSvcTypeDnFromUnit(unit_svt_id, version))

def getSUBaseTypeDnFromUnit(identity):
    # Example: safSuType=ERIC-<id>
    return AMFModel.SaAmfSUBaseType.createDn(getFullModelNameFromUnit(identity))

def getSUTypeDnFromUnit(identity, version):
    # Example: safVersion=<version>,safSuType=ERIC- <id>
    return AMFModel.SaAmfSUType.createDn(getModelVersion(version),
                                         getSUBaseTypeDnFromUnit(identity))

def getSutCompTypeDnFromUnit(unit_sut_id, sutVersion, unit_ct_id, ctVersion):
    # Example: safMemberCompType=safVersion=<ct_version>\,safCompType=ERIC-<ct_id>,
    #                            safVersion=<sut_version>,safSuType=ERIC-<sut_id>
    return AMFModel.SaAmfSutCompType.createDn(getCompTypeDnFromUnit(unit_ct_id, ctVersion),
                                              getSUTypeDnFromUnit(unit_sut_id, sutVersion))

def getSGBaseTypeDnFromUnit(identity):
    # Example: safSgType=ERIC-<id>
    return AMFModel.SaAmfSGBaseType.createDn(getFullModelNameFromUnit(identity))

def getSGTypeDnFromUnit(identity, version):
    # Example: safVersion=<version>,safSgType=ERIC-<id>
    return AMFModel.SaAmfSGType.createDn(getModelVersion(version),
                                         getSGBaseTypeDnFromUnit(identity))

def generateAppBaseTypeDn(identity):
    # Example: safAppType=ERIC-<id>
    return AMFModel.SaAmfAppBaseType.createDn( getFullModelNameFromUnit(identity) )

def generateAppTypeDn(identity, version):
    # Example: safVersion=<version>,safAppType=ERIC-<id>
    return AMFModel.SaAmfAppType.createDn(version, generateAppBaseTypeDn(identity))

def getAmfCluster():
    return AMFModel.SaAmfCluster.createDn("myAmfCluster")

def getNodeDnFromName(name):
    # Example: safAmfNode=<name>,safAmfCluster=myAmfCluster
    return AMFModel.SaAmfNode.createDn(name, getAmfCluster())

def getNodeGroupDnFromPGName(name):
    # Example: safAmfNodeGroup=<name>,safAmfCluster=myAmfCluster
    return AMFModel.SaAmfNodeGroup.createDn(name, getAmfCluster())

def generateSUDn(node, sgDn):
    # Example: safSu=<node>,safSg=<sv_name>-<sv_id>,safApp=ERIC-<pa_id>
    return AMFModel.SaAmfSU.createDn(node, sgDn)

def generateCompDn(ct_name, suDn):
    # Example: safComp=<ct_name>,safSu=<node>,safSg=<sv_name>-<sv_id>,safApp=ERIC-<pa_id>
    return AMFModel.SaAmfComp.createDn(ct_name, suDn)

def generateCompCsTypeDn(csType, compDn):
    # Example: safSupportedCsType=<csType>,safComp=<ct_name>,safSu=<node>,safSg=<sv_name>-<sv_id>,safApp=ERIC-<pa_id>
    return AMFModel.SaAmfCompCsType.createDn(csType, compDn)

def generateSIDn(sv_name, sgRedMode, id, appDn, nodeId=None):
    # Example: safSi=<sv_name>-<SgRedMod>-<unique_id>,safApp=ERIC-<pa_id>
    # NORED:   safSi=<sv_name>-<SgRedMod>-<unique_id>-<node_id>,safApp=ERIC-<pa_id>
    if nodeId:
        return AMFModel.SaAmfSI.createDn(sv_name + "-" + sgRedMode + "-" + (id) + "-" + nodeId, appDn)
    else:
        return AMFModel.SaAmfSI.createDn(sv_name + "-" + sgRedMode + "-" + (id), appDn)

def generateCSIDn(cst_name, siDn, nodeId=None):
    # Example: safCsi=<cst_name>,safSi=<sv_name>-<SgRedMod>-<unique_id>,safApp=ERIC-<pa_id>
    # NORED:   safCsi=<cst_name>-<node_id>,safSi=<sv_name>-<SgRedMod>-<unique_id>-<node_id>,safApp=ERIC-<pa_id>
    if nodeId:
        return AMFModel.SaAmfCSI.createDn(cst_name + "-" + nodeId, siDn)
    else:
        return AMFModel.SaAmfCSI.createDn(cst_name, siDn)

def generateCSIAttributeDn(attrName, csiDn):
    # Example: safCsiAttr=attrName,safCsi=<cst_name>,safSi=<sv_name>-<SgRedMod>-<unique_id>,safApp=ERIC-<pa_id>
    return AMFModel.SaAmfCSIAttribute.createDn(attrName, csiDn)


def compCategoryInRange(category, categoryMasks):
    """
    Return True if category is in range categoryMasks.

    category: component category value, it can be an integer value,
    or a str which will be convert to integer.
    categoryMasks: a list of expected component category.

    Examples:
      if:
      category = SA_AMF_COMP_LOCAL | SA_AMF_COMP_PROXIED_NPI
      categoryMasks = [SA_AMF_COMP_PROXIED, SA_AMF_COMP_PROXIED_NPI]
      compCategoryInRange(category, categoryMasks) will return True
      if:
      category = SA_AMF_COMP_PROXY
      categoryMasks = [SA_AMF_COMP_PROXIED, SA_AMF_COMP_PROXIED_NPI]
      compCategoryInRange(category, categoryMasks) will return False
    """
    cat = category
    if type(category) is str:
        cat = int(category)
    if cat == 0:  # 0, no bit is setted, not in any range
        return False
    r = 0
    for c in categoryMasks:
        r = r | c
    return (cat & r) > 0


def compCategoryOnlyInRange(category, categoryMasks):
    """
    Return True if category is in range categoryMasks and only in
    range categoryMasks.

    category: component category value, it can be an integer value,
    or a str which will be convert to integer.
    categoryMasks: a list of expected component category.

    Examples:
      if:
      category = SA_AMF_COMP_PROXIED_NPI
      categoryMasks = [SA_AMF_COMP_PROXIED, SA_AMF_COMP_PROXIED_NPI]
      compCategoryOnlyInRange(category, categoryMasks) will return True
      if:
      category = SA_AMF_COMP_LOCAL | SA_AMF_COMP_PROXIED_NPI
      categoryMasks = [SA_AMF_COMP_PROXIED, SA_AMF_COMP_PROXIED_NPI]
      compCategoryOnlyInRange(category, categoryMasks) will return False
    """
    cat = category
    if type(category) is str:
        cat = int(category)
    if cat == 0:  # 0, no bit is setted, not in any range
        return False
    r = 0
    for c in categoryMasks:
        r = r | c
    return (cat == (cat & r))


def compCategoryNotInRange(category, categoryMasks):
    """
    Return True if category is not in range categoryMasks.

    category is a component category value, it can be an integer value,
    or a str which will be convert to integer.
    categoryMasks is a list of expected component category.

    Examples:
      if:
      category = SA_AMF_COMP_LOCAL
      categoryMasks = [SA_AMF_COMP_PROXIED, SA_AMF_COMP_PROXIED_NPI]
      compCategoryNotInRange(category, categoryMasks) will return True
      if:
      category = SA_AMF_COMP_LOCAL | SA_AMF_COMP_PROXIED_NPI
      categoryMasks = [SA_AMF_COMP_PROXIED, SA_AMF_COMP_PROXIED_NPI]
      compCategoryNotInRange(category, categoryMasks) will return False
    """
    cat = category
    if type(category) is str:
        cat = int(category)
    r = 0
    for c in categoryMasks:
        r = r | c
    return (cat ^ r) == (cat | r)


def checkCategory(category, categoryType):
    cat = category
    if type(category) is str:
        cat = int(category)
    return (cat & categoryType) != 0


def isSaAwareComponent(category):
    return checkCategory(category, AMFConstants.SA_AMF_COMP_SA_AWARE)


def isProxyComponent(category):
    return checkCategory(category, AMFConstants.SA_AMF_COMP_PROXY)


def isProxiedComponent(category):
    return checkCategory(category, AMFConstants.SA_AMF_COMP_PROXIED)


def isLocalComponent(category):
    return checkCategory(category, AMFConstants.SA_AMF_COMP_LOCAL)


def isProxiedNpiComponent(category):
    return checkCategory(category, AMFConstants.SA_AMF_COMP_PROXIED_NPI)


def isCategoryAMFRelated(category):
    return category is not None and (
        isSaAwareComponent(category) or
        isProxyComponent(category) or
        isProxiedComponent(category) or
        isLocalComponent(category) or
        isProxiedNpiComponent(category))
