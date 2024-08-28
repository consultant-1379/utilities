"""
Constants representing the action that a component has in the campaign
"""
CT_INSTALL = 1
CT_UPGRADE = 2
CT_REMOVE = 3
CT_NOOP = 4
CT_MIGRATE = 5

"""
Constants to be used when injecting dependencies
"""
NOT_BEFORE = 1
DIFFERENT_PROCEDURE = 2
DIFFERENT_CAMPAIGN = 3

CAMP_INIT_PHASE_ADD_TO_IMM = "addToImm"
CAMP_INIT_PHASE_CB_AT_INIT = "callbackAtInit"
CAMP_INIT_PHASE_CB_AT_BACKUP = "callbackAtBackup"
CAMP_INIT_PHASE_CB_AT_ROLLBACK = "callbackAtRollback"
CAMP_INIT_PHASE_CAMP_INIT_ACTION = "campInitAction"

CAMP_INIT_PHASES = set([CAMP_INIT_PHASE_ADD_TO_IMM,
                        CAMP_INIT_PHASE_CB_AT_INIT,
                        CAMP_INIT_PHASE_CB_AT_BACKUP,
                        CAMP_INIT_PHASE_CB_AT_ROLLBACK,
                        CAMP_INIT_PHASE_CAMP_INIT_ACTION])

CALLBACK_LABEL_CMD = "OsafSmfCbkUtil-Cmd"
CALLBACK_LABEL_UPGRADE_CMD = "OsafSmfCbkUtil-UpgradeCmd"
CALLBACK_LABEL_ROLLBACK_CMD = "OsafSmfCbkUtil-RollbackCmd"

CALLBACK_LABEL = set([CALLBACK_LABEL_CMD,
                      CALLBACK_LABEL_UPGRADE_CMD,
                      CALLBACK_LABEL_ROLLBACK_CMD])


CALLBACK_ON_STEP_EVERY_STEP = "onEveryStep"
CALLBACK_ON_STEP_FIRST_STEP = "onFirstStep"
CALLBACK_ON_STEP_LAST_STEP = "onLastStep"
CALLBACK_ON_STEP_HALF_WAY = "halfWay"

CALLBACK_ON_STEP = set([CALLBACK_ON_STEP_EVERY_STEP,
                        CALLBACK_ON_STEP_FIRST_STEP,
                        CALLBACK_ON_STEP_LAST_STEP,
                        CALLBACK_ON_STEP_HALF_WAY])


CALLBACK_AT_ACTION_BEFORE_LOCK = "beforeLock"
CALLBACK_AT_ACTION_BEFORE_TERMINATION = "beforeTermination"
CALLBACK_AT_ACTION_AFTER_IMM_MODIFICATION = "afterImmModification"
CALLBACK_AT_ACTION_AFTER_INSTANTIATION = "afterInstantiation"
CALLBACK_AT_ACTION_AFTER_UNLOCK = "afterUnlock"

CALLBACK_AT_ACTION = set([CALLBACK_AT_ACTION_BEFORE_LOCK,
                          CALLBACK_AT_ACTION_BEFORE_TERMINATION,
                          CALLBACK_AT_ACTION_AFTER_IMM_MODIFICATION,
                          CALLBACK_AT_ACTION_AFTER_INSTANTIATION,
                          CALLBACK_AT_ACTION_AFTER_UNLOCK])


BREAKPOINT_LABEL = "OsafSmfCbkUtil-UpgradeCmd"
BREAKPOINT_TIMEOUT = "60000000000"
BREAKPOINT_STRING_TO_PASS = "/opt/coremw/lib/ecim-swm-breakpoint"
