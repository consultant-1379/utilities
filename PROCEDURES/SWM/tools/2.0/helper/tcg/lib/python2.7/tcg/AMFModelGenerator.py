import sys

import ImmHelper
import AMFConstants
import AMFModel
import AMFTools
import SDPTools
from utils.logger_tcg import tcg_error, trace_enter, trace_leave
import logging
import csm_units

#------------------------------------------------------------------------------

class AMFModelGenerator():

    def __init__(self):
        self.amfModel = AMFModel.AMFModel()

    def componentGenerator(self, component, online_adapter):
        trace_enter()
        if AMFTools.isCategoryAMFRelated(component.getType()):
            self._generateModelForComponent(component, online_adapter)
        trace_leave()

    def serviceGenerator(self, service):
        trace_enter()
        if service.getAmfManagedComponents():
            self._generateModelForService(service)
        trace_leave()

    def _generateModelForComponent(self, component, online_adapter):
        if component.getAvailabilityManager().upper() == 'AMF' :
            self._parseComponentYaml(component, online_adapter)
            self._parseHealthcheckYaml(component)
            self._parseComponentServiceTypeYaml(component)

    def _generateModelForService(self, service):
        if service.getAmfManagedComponents() :
            self._parseAppTypeYaml(service)
            self._parseServiceTypeYaml(service)
            self._parseServiceUnitTypeYaml(service)
            self._parseServiceGroupTypeYaml(service)

    def _parseAppTypeYaml(self, service):
        serviceIdentity = service.getUid()
        redundancyModel = service.getRedundancyModel()  #redundancy_model_name
        redundancyModelNumber = AMFConstants.getRedundancyModelNumber(service.getRedundancyModel())

        appBaseType = AMFModel.SaAmfAppBaseType()
        appBaseType._dn = AMFTools.generateAppBaseTypeDn(serviceIdentity)
        self.amfModel.addObject(appBaseType)

        appType = AMFModel.SaAmfAppType()
        appType._dn = AMFTools.generateAppTypeDn(serviceIdentity, "1")
                            #specified in csm 0.9b wiki to hard-code the version to "1"
        self.amfModel.addObject(appType)

        #partially supported but mandatory
        appType.addTosaAmfApptSGTypes(AMFTools.getSGTypeDnFromUnit(serviceIdentity,
                                                                   redundancyModelNumber
                                                                   )
                                      )

        app = AMFModel.SaAmfApplication()
        app._dn = AMFModel.SaAmfApplication.createDn(ImmHelper.getName(appType.getParentDn()))
        app.setsaAmfAppType(appType.getDn())
        self.amfModel.addObject(app)

        sg = AMFModel.SaAmfSG()
        sg._dn = AMFModel.SaAmfSG.createDn(redundancyModel, app.getDn())
        sg.setsaAmfSGType(AMFTools.getSGTypeDnFromUnit(serviceIdentity,
                                                       redundancyModelNumber
                                                       )
                          )
        self.amfModel.addObject(sg)

    def _parseComponentYaml(self, component, online_adapter):
        # parse the yaml object received
        componentIdentity = component.getUid()
        componentVersion = component.getVersion()
        # create CompBaseType
        compBaseType = AMFModel.SaAmfCompBaseType()
        compBaseType._dn = AMFTools.getCompBaseTypeDnFromUnit(componentIdentity)
        self.amfModel.addObject(compBaseType)

        # create CompType
        compType = AMFModel.SaAmfCompType()
        compType._dn = AMFTools.getCompTypeDnFromUnit(componentIdentity, componentVersion)
        self.amfModel.addObject(compType)

        #create common attributes
        compType.setsaAmfCtCompCategory(component.getType())
        sw = component.get_single_sdp_name(online_adapter)
        if sw:
            swBundle = AMFTools.getSaSmfSwBundleDnFromUnit(sw)
            compType.setsaAmfCtSwBundle(swBundle)

        #Setting Linux Environment Variables set at CSM Component level

        # If you see this comment, please remove it
        #envs = {}
        for env_attr in component.get_environment_attributes():
            if env_attr.get_default_value():
                AMFTools.validateAndSetOptionalArg(
                                                   compType.addTosaAmfCtDefCmdEnv,
                                                   env_attr.get_name() + "=" + env_attr.get_default_value()
                                                   )

        compType.setsaAmfCtDefClcCliTimeout(component.getStartStopTimeout())
        compType.setsaAmfCtDefCallbackTimeout(component.getPromoteDemoteTimeout())

        compType.setsaAmfCtRelPathCleanupCmd(component.getCleanupCommand())
        AMFTools.validateAndSetOptionalArg(compType.addTosaAmfCtDefCleanupCmdArgv,
                                           component.getCleanupCommandArgs())

        if component.getMonitorCommand():
            compType.setosafAmfCtRelPathHcCmd(component.getMonitorCommand())
            AMFTools.validateAndSetOptionalArg(compType.addToosafAmfCtDefHcCmdArgv,
                                               component.getMonitorCommandArgs())

        AMFTools.validateAndSetOptionalArg(compType.setsaAmfCtDefRecoveryOnError,
                                           component.getRecoveryPolicy(),
                                           AMFConstants.isValidRecoveryOnErrorName,
                                           "invalid RecoveryOnError value in unit %s" % (componentIdentity),
                                           AMFConstants.getRecoveryOnErrorNumber)

        if component.getDisableRestart():
            AMFTools.validateAndSetOptionalArg(compType.setsaAmfCtDefDisableRestart,
                                               component.getDisableRestart(),
                                               AMFConstants.isValidBooleanName,
                                               "invalid DisableRestart value in unit %s" % (componentIdentity),
                                               AMFConstants.getBooleanNumber)

        # create component category specific attributes
        if AMFTools.isSaAwareComponent(component.getType()) or \
           AMFTools.isLocalComponent(component.getType()) or \
           AMFTools.isProxyComponent(component.getType()):

            compType.setsaAmfCtRelPathInstantiateCmd(component.getInstantiateCommand())
            AMFTools.validateAndSetOptionalArg(compType.addTosaAmfCtDefInstantiateCmdArgv,
                                               component.getInstantiateCommandArgs())

        if AMFTools.isLocalComponent(component.getType()):

            compType.setsaAmfCtRelPathTerminateCmd(component.getTerminateCommand())
            AMFTools.validateAndSetOptionalArg(compType.addTosaAmfCtDefTerminateCmdArgv,
                                               component.getTerminateCommandArgs(), None, "Terminate command missing for Local Component %s" % component.getUid())

        if AMFTools.isSaAwareComponent(component.getType()) or \
           AMFTools.isProxyComponent(component.getType()) or \
           AMFTools.isProxiedComponent(component.getType()):

            compType.setsaAmfCtDefQuiescingCompleteTimeout(component.getMigrateTimeout())
            compType.setsaAmfCtDefInstantiationLevel (0)


            '''
            if component.getHealthCheckData().getHealthCheckMonitor() == "OSAF-EXTERNAL" or \
               component.getHealthCheckData().getHealthCheckMonitor() == None:
            '''

            '''
            if not component.getMonitorCommand():
                tcg_error("LOCAL Component %s has missing status command which is mandatory \
                                            for OSAF-EXTERNAL monitor type" % component.getUid())
            '''

            # check not supported values for this category
            '''
            assertIsKey("saAmfCtRelPathAmStartCmd", component_type_data,
                       "saAmfCtRelPathAmStartCmd is not supported for SA-AWARE category in unit %s" % (componentIdentity))
            assertIsKey("saAmfCtDefAmStartCmdArgv", component_type_data,
                       "saAmfCtDefAmStartCmdArgv is not supported for SA-AWARE category in unit %s" % (componentIdentity))
            assertIsKey("saAmfCtRelPathAmStopCmd", component_type_data,
                       "saAmfCtRelPathAmStopCmd is not supported for SA-AWARE category in unit %s" % (componentIdentity))
            assertIsKey("saAmfCtDefAmStopCmdArgv", component_type_data,
                       "saAmfCtDefAmStopCmdArgv is not supported for SA-AWARE category in unit %s" % (componentIdentity))
            '''

    def _parseHealthcheckYaml(self, component):
        # create healthchecktype objects
        componentIdentity = component.getUid()
        componentVersion = component.getVersion()

        #if not monitor :
        keys = component.getHealthCheckKeys()
        '''
        if len(keys) == 0:
            tcg_error("INTERNAL monitoring, but no key given.")
        '''

        if not keys:
            '''default behavior when monitor-keys is missed'''
            if not component.getMonitorCommand():
                logging.error("monitor and monitor-keys are both omited in lifecycle-control for component {0}.".format(component.getName()))
                sys.exit(1)
            keys.append(csm_units.component.HealthCheckKey())

        for key in keys:
            healthCheckType = AMFModel.SaAmfHealthcheckType()
            healthCheckType._dn = AMFTools.getHealthcheckTypeDnFromUnit(key.getSafHealthcheckKey(),
                                                                        componentIdentity, componentVersion)
            healthCheckType.setsaAmfHctDefPeriod(key.getSaAmfHctDefPeriod())
            AMFTools.validateAndSetOptionalArg(healthCheckType.setsaAmfHctDefMaxDuration,
                                                   key.getSaAmfHctDefMaxDuration())
            self.amfModel.addObject(healthCheckType)

    def _parseComponentServiceTypeYaml(self, component):
        componentIdentity = component.getUid()
        componentVersion = component.getVersion()

        # create CSBaseType
        csBaseType = AMFModel.SaAmfCSBaseType()
        csBaseType._dn = AMFTools.getCSBaseTypeDnFromUnit(componentIdentity)
        self.amfModel.addObject(csBaseType)
        # create CSType
        csType = AMFModel.SaAmfCSType()
        csType._dn = AMFTools.getCSTypeDnFromUnit(componentIdentity, "1")
        self.amfModel.addObject(csType)
        # create CtCsType
        ctcsType = AMFModel.SaAmfCtCsType()
        ctcsType._dn = AMFTools.getCtCsTypeDnFromUnit(componentIdentity, componentVersion, "1")
        self.amfModel.addObject(ctcsType)

        AMFTools.validateAndSetMandatoryArg(ctcsType.setsaAmfCtCompCapability,
                                            component.getComponentCapabilityModel(),
                                            AMFConstants.isValidCapabilityName,
                                            "invalid Capability attribute in UnitAttributes of %s" % (componentIdentity),
                                            AMFConstants.getCapabilityNumber)

        #Partially supported omitted for now

        '''if "saAmfCtDefNumMaxActiveCSIs" in comp_service_type_data:
            AMFTools.validateAndSetOptionalArg(ctcsType.setsaAmfCtDefNumMaxActiveCSIs,
                                               comp_service_type_data["saAmfCtDefNumMaxActiveCSIs"])
        if "saAmfCtDefNumMaxStandbyCSIs" in comp_service_type_data:
            AMFTools.validateAndSetOptionalArg(ctcsType.setsaAmfCtDefNumMaxStandbyCSIs,
                                               comp_service_type_data["saAmfCtDefNumMaxStandbyCSIs"])'''

        """
        According to CSM spec, saAmfCSAttrName is partly supported by OpenSAF
        (only on model level). Therefore, the CSM model compiler should not
        generate any value for it on type level (SaAmfCSType MOC) but only on
        instance level (SaAmfCSIAttribute MOC).
        Leave comments here for possible improvement in the future.

        # for prom_attr in component.get_promotion_attributes():
        #     csType.addTosaAmfCSAttrName(prom_attr.get_name())
        """

    def _parseServiceTypeYaml(self, service):
        serviceIdentity = service.getUid()

        svcBaseType = AMFModel.SaAmfSvcBaseType()
        svcBaseType._dn = AMFTools.getSvcBaseTypeDnFromUnit(serviceIdentity)
        self.amfModel.addObject(svcBaseType)

        svcType = AMFModel.SaAmfSvcType()
        svcType._dn = AMFTools.getSvcTypeDnFromUnit(serviceIdentity, "1")
        self.amfModel.addObject(svcType)

        '''
        NOT SUPPORTED BY AMF
        if "saAmfSvcDefStandbyWeight" in service_type_data:
            AMFTools.validateAndSetOptionalArg(svcType.addTosaAmfSvcDefStandbyWeight,
                                               service_type_data["saAmfSvcDefStandbyWeight"])
        if "saAmfSvcDefActiveWeight" in service_type_data:
            AMFTools.validateAndSetOptionalArg(svcType.addTosaAmfSvcDefActiveWeight,
                                               service_type_data["saAmfSvcDefActiveWeight"])
        '''

        for component in service.getAmfManagedComponents():
            svcTypeCSType = AMFModel.SaAmfSvcTypeCSTypes()
            svcTypeCSType._dn = AMFTools.getSvcTypeCSTypesDnFromUnit(serviceIdentity,
                                                                     "1",
                                                                     component.getUid(),
                                                                     "1")
            self.amfModel.addObject(svcTypeCSType)


#        csTypeList = service_type_data[""]
#
#        usedCSTNum = 0
#
#        for ref in unit.findAllReferences("ConsistsOf", [self._environment]):
#            for unitRef in ref.unitReferences:
#                unit_cst = unitRef.unit
#                svcTypeCSType = AMFModel.SaAmfSvcTypeCSTypes()
#                svcTypeCSType._dn = AMFTools.getSvcTypeCSTypesDnFromUnit(unit, unit_cst)
#                for csType in csTypeList:
#                    if unit_cst.identity == csType.getid():
#                        AMFTools.validateAndSetOptionalArg(svcTypeCSType.setsaAmfSvctMaxNumCSIs,
#                                                        csType.getSvctMaxNumCSIs())
#                        usedCSTNum = usedCSTNum + 1
#                self.amfModel.addObject(svcTypeCSType)

#        if not usedCSTNum == len(csTypeList):
#            tcg_error("Some CST in AMF-ServiceType.xml was not found in unit relations of unit %s" % (unit.identity))

    def _parseServiceUnitTypeYaml(self, service):
        serviceIdentity = service.getUid()

        suBaseType = AMFModel.SaAmfSUBaseType()
        suBaseType._dn = AMFTools.getSUBaseTypeDnFromUnit(serviceIdentity)
        self.amfModel.addObject(suBaseType)

        suType = AMFModel.SaAmfSUType()
        suType._dn = AMFTools.getSUTypeDnFromUnit(serviceIdentity, "1")

        #Partially supported but mandatory
        suType.addTosaAmfSutProvidesSvcTypes(AMFTools.getSvcTypeDnFromUnit(serviceIdentity, "1"))
        suType.setsaAmfSutIsExternal("0")

        #Default should be used
        AMFTools.validateAndSetOptionalArg(suType.setsaAmfSutDefSUFailover,
                                           service.getSaAmfSutDefSUFailover(),
                                           AMFConstants.isValidBooleanName,
                                           "Invalid value for SutDefSUFailover in unit %s" % (serviceIdentity),
                                           AMFConstants.getBooleanNumber)

        self.amfModel.addObject(suType)

        for svComponent in service.getAmfManagedComponents():
            sutCompType = AMFModel.SaAmfSutCompType()
            sutCompType._dn = AMFTools.getSutCompTypeDnFromUnit(serviceIdentity,
                                                                "1",
                                                                svComponent.getUid(),
                                                                svComponent.getVersion())
            self.amfModel.addObject(sutCompType)

    def _parseServiceGroupTypeYaml(self, service):
        serviceIdentity = service.getUid()
        redundancyModelNumber = AMFConstants.getRedundancyModelNumber(service.getRedundancyModel())

        sgBaseType = AMFModel.SaAmfSGBaseType()
        sgBaseType._dn = AMFTools.getSGBaseTypeDnFromUnit(serviceIdentity)
        self.amfModel.addObject(sgBaseType)

        sgType = AMFModel.SaAmfSGType()
        sgType._dn = AMFTools.getSGTypeDnFromUnit(serviceIdentity, redundancyModelNumber)
        self.amfModel.addObject(sgType)


        AMFTools.validateAndSetMandatoryArg(sgType.setsaAmfSgtRedundancyModel,
                                            service.getRedundancyModel(),
                                            AMFConstants.isValidRedundancyModelName,
                                            "Invalid redundancy model in unit %s" % (serviceIdentity),
                                            AMFConstants.getRedundancyModelNumber)


        #Specified in CSM 0.9b specification to take redundancy model as RDN of sgtype
        #Partially supported but mandatory
        sgType.addTosaAmfSgtValidSuTypes(AMFTools.getSUTypeDnFromUnit(serviceIdentity,
                                                                      "1"))

        #not to be set, default value should be used.
        '''AMFTools.validateAndSetOptionalArg(sgType.setsaAmfSgtDefAutoRepair,
                                           service.getSaAmfSgtDefAutoRepair(),
                                           AMFConstants.isValidBooleanName,
                                           "Invalid value for SgtDefAutoRepair in unit %s" % (serviceIdentity),
                                           AMFConstants.getBooleanNumber)

        AMFTools.validateAndSetOptionalArg(sgType.setsaAmfSgtDefAutoAdjust,
                                           service.getSaAmfSgtDefAutoAdjust(),
                                           AMFConstants.isValidBooleanName,
                                           "Invalid value for SgtDefAutoAdjust in unit %s" % (serviceIdentity),
                                           AMFConstants.getBooleanNumber)'''

        ###FIXME
        # the saAmfSgtDefAutoAdjustProb is optional if the defautoadjust is not set or false however
        # the SMF campaign xsd is currently bugged and expects that this attribute is set no matter what
        # so right now this attribute is mandatory here as well
        #if serviceGroupTypeXML.getSgtDefAutoAdjust() == AMFConstants.BOOLEAN_NAME_TRUE:
        #    AMFTools.validateAndSetMandatoryArg(sgType.setsaAmfSgtDefAutoAdjustProb,
        #                                    serviceGroupTypeXML.getSgtDefAutoAdjustProb(),
        #                                    None,
        #                                    "Invalid value for SgtDefAutoAdjustProb in unit %s" % (unit.identity),
        #                                    None)
        #else:
        #    AMFTools.validateAndSetOptionalArg(sgType.setsaAmfSgtDefAutoAdjustProb,
        #                                    serviceGroupTypeXML.getSgtDefAutoAdjustProb())

        #Partially supported
        AMFTools.validateAndSetMandatoryArg(sgType.setsaAmfSgtDefAutoAdjustProb,
                                            service.getSaAmfSgtDefAutoAdjustProb(),
                                            None,
                                            "Invalid value for SgtDefAutoAdjustProb in unit %s" % (serviceIdentity),
                                            None)

        AMFTools.validateAndSetMandatoryArg(sgType.setsaAmfSgtDefCompRestartProb,
                                            service.getMonitorPeriod(),
                                            None,
                                            "Invalid value for SgtDefCompRestartProb in unit %s" % (serviceIdentity),
                                            None)

        AMFTools.validateAndSetMandatoryArg(sgType.setsaAmfSgtDefCompRestartMax,
                                            service.getMaxFailureNr(),
                                            None,
                                            "Invalid value for SgtDefCompRestartMax in unit %s" % (serviceIdentity),
                                            None)

        AMFTools.validateAndSetMandatoryArg(sgType.setsaAmfSgtDefSuRestartProb,
                                            service.getMonitorPeriod(),
                                            None,
                                            "Invalid value for SgtDefSuRestartProb in unit %s" % (serviceIdentity),
                                            None)

        AMFTools.validateAndSetMandatoryArg(sgType.setsaAmfSgtDefSuRestartMax,
                                            service.getMaxFailureNr(),
                                            None,
                                            "Invalid value for SgtDefSuRestartMax in unit %s" % (serviceIdentity),
                                            None)

    def generateFromCSM(self, csmModel, online_adapter):
        '''
        Generate related AMF Model entities from the component CSM Units
        '''
        for component in csmModel.system.getComponents():
            self.componentGenerator(component, online_adapter)

        '''
        Generate related AMF Model entities from the service CSM Units
        '''
        for service in csmModel.system.getServices():
            self.serviceGenerator(service)
