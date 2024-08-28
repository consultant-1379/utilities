#!/bin/bash
##
# ------------------------------------------------------------------------
#     Copyright (C) 2017 Ericsson AB. All rights reserved.
# ------------------------------------------------------------------------
##
# Name:
#   enable_auto_backup_restore.sh
#
# Description:
#   A script to add some IMM attributes setting during the campaign
#   generation phase, corresponding to the 'createUpgradePackageLocal' action
#   invokation.
#
# Return value:
#   0 -> true  -> Success: the part of campaign is included.
#   1 -> false -> Success: the part of campaign is excluded.
#   2 -> error -> Failure: error occurred and the campaign generation stops. 
#
# Changelog:
# - Mon Dic 4 2017 - Luisa Cioffi (teiclui)
#     First version.
##

# BEGIN: Variables section
APP_NAME=$(basename $0)
EXIT_SUCCESS_INCLUDE=$(true; echo $?)
EXIT_SUCCESS_EXCLUDE=$(false; echo $?)    # Not used, for now.
EXIT_FAILURE=2
# END: Variables section

# BEGIN: Functions section
function log() {
  /bin/logger -t $APP_NAME "$*"
}

function abort() {  /bin/logger -p err -t $APP_NAME "ABORTING: $*"
  exit $EXIT_FAILURE
}

function enable_auto_backup_restore() {
 log "Entering: $FUNCNAME"
 
 ## To set to 1 automaticBackup and automaticRestore attributes during 
 # createUpgradePackageLocal action in order to support the automatic fallback 
 # during a SW upgrade procedure
  /opt/coremw/bin/cmw-swm-config-set -b 1 &>/dev/null || abort 0 "failure while executing \"cmw-swm-config-set -b 1\"" 
  
  /opt/coremw/bin/cmw-swm-config-set -r 1 &>/dev/null || abort 0 "failure while executing \"cmw-swm-config-set -r 1\"" 

  
 log "Exiting: $FUNCNAME"
}


#                                              __    __   _______   _   __    _
#                                             |  \  /  | |  ___  | | | |  \  | |
#                                             |   \/   | | |___| | | | |   \ | |
#                                             | |\  /| | |  ___  | | | | |\ \| |
#                                             | | \/ | | | |   | | | | | | \   |
#                                             |_|    |_| |_|   |_| |_| |_|  \__|
#
log "Entering: $APP_NAME"

# Prints error in case of unset variables
set -u

# Change automaticBackup and automaticRestore attributes value (to 1) in order to support the automatic backup and restore during the upgrade
enable_auto_backup_restore

log "Exiting: $APP_NAME"
exit $EXIT_SUCCESS_INCLUDE

# End of file
