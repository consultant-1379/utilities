#!/bin/bash
##
# ------------------------------------------------------------------------
#     Copyright (C) 2018 Ericsson AB. All rights reserved.
# ------------------------------------------------------------------------
##
# Name:
#      configap.sh
# Description:
#       A script to create/restore the folder structure and the permissions.
# Note:
# None.
##
# Changelog:
# - Tue Feb 13 2018 - 
# First version.

LOG_TAG='campaign.configap.sh'
function log(){
   /bin/logger -t  "$LOG_TAG" "$*"
}

function set_permissions(){
  local FOLDER="$1"
  local PERMISSIONS="$2"
  local MESSAGE=''
  if [ ! -d "$FOLDER" ]; then
    log "creating folder: [$FOLDER]" 
    mkdir -p "$FOLDER" &>/dev/null
  fi

  MESSAGE="applying [$PERMISSIONS] to [$FOLDER]"
  log "$MESSAGE"
  chmod $PERMISSIONS $FOLDER &>/dev/null
  if [ $? -ne 0 ]; then
    log "$MESSAGE ...failed, proceeding anyway..."
  else
    log "$MESSAGE ...done"
  fi
}

function invoke(){
  local MESSAGE='invoking configap -d:'
  log "$MESSAGE"
  /opt/ap/acs/bin/acs_lct_configap.sh -d &>/dev/null
  if [ $? -ne 0 ]; then 
    log "$MESSAGE ...ended with errors, proceeding anyway..."
  else
    log "$MESSAGE ...done"
  fi

  # configap -d removes the full permission applied to nbi_root, so apply again here.
  local FOLDER='/data/opt/ap/internal_root'
  set_permissions $FOLDER 777

  FOLDER='/cluster/sw_package/APG'
  set_permissions $FOLDER 2775

  FOLDER='/storage/no-backup/coremw/SoftwareManagement'
  set_permissions $FOLDER 2775
}

# M A I N
log "START: <$0>"

invoke

log "END: <$0>"

exit 0

