NODE_TYPE_CONTROLLER = "controller"
NODE_TYPE_PAYLOAD = "payload"


NODEPROFILE_TYPE_AUTOSCALE = "autoscale"

CDSVCALLBACKTIMEOUT = "3600000000000"

COM_CONSUMER_NAME = "COM_R1"
IMM_R1_CONSUMER_NAME = "IMM_R1"
IMM_I_Local_Authorization_R1_CONSUMER_NAME = "IMM-I-Local_Authorization_R1"
IMM_I_FM_R1_CONSUMER_NAME = "IMM-I-FM_R1"

CDFCGT_CONFIG_BASE_CSM_PART = "CSM"
CDFCGT_CONFIG_BASE_CSM_MODEL_FILENAME = "model.yml"

#=========================== YAML TAGS ========================================

CSM_VERSION_TAG                             = "csm-version"

COMPONENTS_TAG                              = "components"
SERVICES_TAG                                = "services"
FUNCTIONS_TAG                               = "functions"

#-----------------------------------------------------------------------------

ROLES_TAG                                   = "roles"
SYSTEM_TAG                                  = "systems"
DEPLOYMENT_PROFILE_TAG                      = "deployment-profile"



# SYSTEM_COMPUTE_RESOURCES_TAG is not a real CSM tag
SYSTEM_COMPUTE_RESOURCES_TAG                = "SYSTEM_COMPUTE_RESOURCES_TAG"

#------------------------------------------------------------------------------

ALLOCATION_NAME_TAG                         = "name"
ALLOCATION_ROLE_TAG                         = "role"

SYSTEM_UID_TAG                              = "uid"
SYSTEM_NAME_TAG                             = "name"
SYSTEM_VERSION_TAG                          = "version"
SYSTEM_PRODUCT_NUMBER_TAG                   = "product-number"
SYSTEM_DESCRIPTION_TAG                      = "description"
SYSTEM_FUNCTIONS_TAG                        = "functions"
SYSTEM_ROLES_TAG                            = "roles"
SYSTEM_ROLE_TAG                             = "role"
SYSTEM_ROLE_ASSIGN_TO_TAG                   = "assigned-to"
SYSTEM_MAX_CLUSTER_SIZE_TAG                 = "max-cluster-size"
SYSTEM_CONSTRAINTS_TAG                      = "constraints"
SYSTEM_CONSTRAINTS_OLDEST_VERSION_TAG       = "upgrade-oldest-version"
SYSTEM_CONSTRAINTS_EXTEND_TAG               = "extends"


ROLE_UID_TAG                                = "uid"
ROLE_NAME_TAG                               = "name"
ROLE_SERVICES_TAG                           = "services"
ROLE_DESCRIPTION_TAG                        = "description"
ROLE_SCALING_TAG                            = "scaling"
ROLE_MINNODES_TAG                           = "min-nodes"
ROLE_WEIGHT_TAG                             = "weight"
ROLE_RANK_TAG                               = "rank"
ROLE_EXTERNAL_TAG                           = "external"
ROLE_CONSTRAINTS_TAG                        = "constraints"
ROLE_CONSTRAINTS_EXTEND_TAG                 = "extends"

#------------------------------------------------------------------------------

COMPONENT_COMMANDS_TAG                      = "commands"
COMPONENT_EXTENDED_CONFIG_TAG               = "extended-configuration"
COMPONENT_UID_TAG                           = "uid"
COMPONENT_DESCRIPTION_TAG                   = "description"
COMPONENT_INSTALL_PREFIX_TAG                = "prefix"
COMPONENT_NAME_TAG                          = "name"
COMPONENT_SOFTWARE_TAG                      = "software"
COMPONENT_SOFTWARE_SDP_TAG                  = "sdp"
COMPONENT_SOFTWARE_RPM_TAG                  = "rpms"

COMPONENT_CONFIGURATIONFILE_TAG             = "configuration-files"
COMPONENT_CONFIGURATIONFILE_NAME_TAG        = "name"
COMPONENT_CONFIGURATIONFILE_TYPE_TAG        = "data-type"
COMPONENT_CONFIGURATIONFILE_CATEGORY_TAG    = "data-category"
COMPONENT_PROMOTION_ATTRIBUTES_TAG          = "promotion-attributes"
COMPONENT_ENVIRONMENT_ATTRIBUTES_TAG        = "environment-attributes"
COMPONENT_ATTRIBUTE_NAME_TAG                = "name"
COMPONENT_ATTRIBUTE_FORMAT_TAG              = "format-rule"
COMPONENT_ATTRIBUTE_DESCRIPTION_TAG         = "description"
COMPONENT_ATTRIBUTE_DEFAULTVALUE_TAG        = "default-value"

COMPONENT_HEALTHCHECK_DATA_TAG              = "healthcheck-data"
COMPONENT_DEPENDS_ON_TAG                    = "depends-on"
COMPONENT_CONSTRAINTS                       = "constraints"
COMPONENT_INSTALLATION_CONSTRAINTS          = "installation"
COMPONENT_UPGRADE_CONTRAINTS                = "upgrade"
COMPONENT_CONSTRAINTS_SCOPE                 = "scope"
COMPONENT_CONSTRAINTS_REBOOT                = "reboot"
COMPONENT_CONSTRAINTS_AFTER                 = "after"
COMPONENT_CONSTRAINTS_COMPONENT             = "component"
COMPONENT_CONSTRAINTS_METHOD                = "method"
COMPONENT_CONSTRAINTS_MIGRATION_SCOPE       = "migration-scope"
COMPONENT_CONSTRAINTS_BOOTSTRAP             = "bootstrap"
COMPONENT_CONSTRAINTS_OLDEST_VERSION_TAG    = "oldest-version"

SCOPE_SERVICE                               = "service"
SCOPE_COMPUTE_RESOURCE                      = "compute-resource"

COMPONENT_SCALING_TAG                       = "scaling"
COMPONENT_SCALING_MIN_NODES_TAG             = "min-nodes"
COMPONENT_SCALING_MAX_NODES_TAG             = "max-nodes"

COMPONENT_CONTROL_POLICY_TAG                = "control-policy"
COMPONENT_CONTROL_POLICY_TYPE_TAG           = "type"
COMPONENT_CONTROL_POLICY_PARENT_TAG         = "parent"
COMPONENT_NODE_ACTIVE_TAG                   = "node-active"
COMPONENT_NODE_STANDBY_TAG                  = "node-standby"
COMPONENT_NODE_ACTIVE_STANDBY_TAG           = "node-active-standby"
COMPONENT_CLUSTER_ACTIVE_TAG                = "cluster-active"
COMPONENT_CLUSTER_STANDBY_TAG               = "cluster-standby"
COMPONENT_START_STOP_TIMEOUT_TAG            = "start-stop-timeout"
COMPONENT_PROMOTE_DEMOTE_TIMEOUT_TAG        = "promote-demote-timeout"
COMPONENT_MIGRATE_TIMEOUT_TAG               = "migrate-timeout"
COMPONENT_RECOVERY_POLICY_TAG               = "recovery-policy"
COMPONENT_EXTERNAL_TAG                      = "external"
COMPONENT_PLUGIN_TAG                        = "plugin"
COMPONENT_AVAILABILITY_MANAGER_TAG          = "availability-manager"

COMPONENT_SUPERSEDES_TAG                    = "supersedes"
COMPONENT_SUPERSEDES_BASE_COMPONENT_TAG     = "base-component"
COMPONENT_SUPERSEDES_SOFTWARE_TAG           = "software"

# meta-data related tags
META_METADATA_TAG                           = "meta-data"
# component meta-data
META_COMPONENT_VERSION_TAG                  = "component-version"
META_DELIVERABLE_TAG                        = "deliverable"
META_DEPLOYMENT_PACKAGE_TAG                 = "deployment-package"
META_RUNTIME_PACKAGE_TAG                    = "runtime-package"
META_SOFTWARE_TAG                           = "software"
META_FILE_NAME_TAG                          = "file-name"
META_BUNDLE_NAME_TAG                        = "bundle-name"
# service meta-data
META_SERVICE_VERSION_TAG                    = "service-version"
META_COMPONENTS_TAG                         = "components"
META_COMPONENT_TAG                          = "component"
META_VERSION_TAG                            = "version"
META_SERVICES_TAG                           = "services"
META_SERVICE_TAG                            = "service"
# function meta-data
META_FUNCTIONS_TAG                          = "functions"
META_FUNCTION_TAG                           = "function"
# role meta-data
META_ROLE_VERSION_TAG                       = "role-version"
# system meta-data
META_ROLES_TAG                              = "roles"
META_ROLE_TAG                               = "role"
# meta-data related tags - end

COMMANDS_START_TAG                          = "start"
COMMANDS_STOP_TAG                           = "stop"
COMMANDS_CONCLUDE_TAG                       = "conclude"
COMMANDS_MONITOR_TAG                        = "monitor"
COMMANDS_ARGUMENTS_TAG                      = "arguments"

HEALTHCHECK_KEYS_TAG                        = "monitor-keys"
HEALTHCHECK_KEY_TAG                         = "key"
HEALTHCHECK_PERIOD_TAG                      = "period"
HEALTHCHECK_TIMEOUT_TAG                     = "timeout"

#------------------------------------------------------------------------------

SERVICE_UID_TAG                             = "uid"

SERVICE_EXTENDED_CONFIG_TAG                 = "extended-configuration"
SERVICE_NAME_TAG                            = "name"
SERVICE_VERSION_TAG                         = "service-version"
SERVICE_REDUNDANCY_TAG                      = "redundancy-model"
SERVICE_MAX_PROMOTIONS_TAG                  = "max-promotions"
SERVICE_DESCRIPTION_TAG                     = "description"
SERVICE_COMPONENTS_TAG                      = "components"
SERVICE_SERVICES_TAG                        = "services"
SERVICE_DEPENDS_ON_TAG                      = "depends-on"
SERVICE_DEPLOYMENT_TAG                      = "deployment"
SERVICE_MONITOR_PERIOD_TAG                  = "monitor-period"
SERVICE_MAX_FAILURE_NR_TAG                  = "max-failure-nr"
SERVICE_MODEL_COMPILER_TAG                  = "model-compiler"
SERVICE_PLUGIN_TAG                          = "plugin"
SERVICE_METADATA_TAG                        = "meta-data"
SERVICE_PROMOTION_DEPENDENCY_TAG            = "service-promotion-dependency"
SERVICE_TOLERANCE_TIMEOUT_TAG               = "tolerance-timeout"
SERVICE_COMPONENT_NAME_TAG                  = "name"
SERVICE_COMPONENT_INSTANCES_OF_TAG          = "instance-of"
SERVICE_COMPONENT_INSTANCE_ATTRIBUTE        = "attributes"
SERVICE_COMPONENT_PROMOTION_ORDER_TAG       = "promotion-order"
SERVICE_COMPONENT_PROMOTION_AFTER_TAG       = "after"
SERVICE_COMPONENT_PROMOTION_BEFORE_TAG      = "before"

EXTCONF_SERVICE_GROUP_TYPE_DATA_TAG         = "service-group-type-data"
EXTCONF_SERVICE_UNIT_TYPE_DATA              = "service-unit-type-data"
EXTCONF_SERVICE_TYPE_DATA                   = "service-type-data"
EXTCONF_CAMPAIGN_DATA_TAG                   = "campaign-data"

CAMPAIGN_DATA_PLUGIN_TAG                    = "plugin"

#------------------------------------------------------------------------------

CONSTRAINTS_COMPONENT_TAG                   = "component"
CONSTRAINTS_SERVICE_TAG                     = "service"
DEPENDS_ON_FUNCTIONS_TAG                    = "function"
VERSION_TAG                                 = "version"
SERVICE_VERSION_TAG                         = "service-version"

CONSTRAINTS_INSTALL_CONSTRAINT_TAG          = "install-constraint"
CONSTRAINTS_UPGRADE_CONSTRAINT_TAG          = "upgrade-constraint"
INSTALL_REBOOT_FLAG                         = "install-reboot"
UPGRDADE_REBOOT_FLAG                        = "upgrade-reboot"
COMPONENTS_REBOOT_LIST                      = "components"
COMPONENTS_BUNDLE_FILE_NAME                 = "bundle-file-name"

#------------------------------------------------------------------------------

FUNCTION_UID_TAG                            = "uid"
FUNCTION_SERVICES_TAG                       = "services"
FUNCTION_FUNCTIONS_TAG                      = "functions"
FUNCTION_DESCRIPTION_TAG                    = "description"
FUNCTION_NAME_TAG                           = "name"
FUNCTION_VERSION_TAG                        = "version"

#------------------------------------------------------------------------------

DEPLOYMENT_PROFILE_INSTANCE_OF_TAG          = "instance-of"

#------------------------------------------------------------------------------
# With this strategy the dependencies for all the components in the list have to be satisfied in order to install the group
# (if only one component does not have satisfied dependencies, the entire group is not include in the partition)
GROUPED_CT_DEPENDENCIES                     = 1
# With this strategy a CT is included in the partition when its dependencies are satisfied,
# independent from the dependencies of the other components in the group
INDIVIDUAL_CT_DEPENDENCIES                  = 2

#==============================================================================
