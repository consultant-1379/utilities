#!/bin/bash
##
# ------------------------------------------------------------------------
#     Copyright (C) 2018 Ericsson AB. All rights reserved.
# ------------------------------------------------------------------------
##
# Name:
#      acs_lct_swmfix.sh
# Description:
#       A script to create symbolic links during the upgrade.
# Note:
# None.
##
# Changelog:
# - Sat Apr 28 2018 - Swetha Rambathini (XSWERAM)
#   added upgrade support
# - Tue Feb 13 2018 - Yeswanth Vankayala (XYESVAN)
# First version.

CHOWN="/usr/bin/chown"
CMD_LN="/usr/bin/ln"
CHMOD="/usr/bin/chmod"

log(){
  /bin/logger -t acs_lct_swmfix "$@"  
}

#-----------------------------------------------------------------
function create_swm_softlink(){
  local NAME="$1"
  local NBI_ROOT='/data/opt/ap/internal_root'
  local STORAGE_SOFTWARE_MGMT='/storage/no-backup/coremw/SoftwareManagement'
  local CLUSTER_SWPKG_APG='/cluster/sw_package/APG'
  local CLUSTER_SWPKG_APG_UPGRADE="$NBI_ROOT/sw_package/APG/UPGRADE"
  local NBI_SOFTWARE_MGMT="$NBI_ROOT/$NAME"
  local USER_GROUP=$( echo $NBI_SOFTWARE_MGMT | awk -F ';' '{print $2}')
  local NBI_SOFTWARE_MGMT_FOLDER

  if [ -z "$USER_GROUP" ]; then
    NBI_SOFTWARE_MGMT_FOLDER=${NBI_SOFTWARE_MGMT%/*}
  else
    NBI_SOFTWARE_MGMT=$( echo $NBI_SOFTWARE_MGMT | awk -F ';' '{print $1}')
    NBI_SOFTWARE_MGMT_FOLDER=${NBI_SOFTWARE_MGMT%/*}
  fi
  
  if [[ "$NBI_SOFTWARE_MGMT_FOLDER" == "$NBI_ROOT" ]]; then
    if [ ! -d $NBI_SOFTWARE_MGMT_FOLDER ]; then
      log "creating folder: [$NBI_SOFTWARE_MGMT_FOLDER]"
      mkdir -p $NBI_SOFTWARE_MGMT_FOLDER
      ${CHMOD} 777 $NBI_SOFTWARE_MGMT_FOLDER
    fi
    if [ ! -L $NBI_SOFTWARE_MGMT ];then
      if [ -d $NBI_SOFTWARE_MGMT ]; then
        log "$NBI_SOFTWARE_MGMT folder found.. removing it."
        rm -rf $NBI_SOFTWARE_MGMT
      fi
    fi
  elif [[ "$NBI_SOFTWARE_MGMT_FOLDER" == "$NBI_ROOT/sw_package" ]]; then
    if [ ! -d $NBI_SOFTWARE_MGMT_FOLDER ]; then
      log "creating folder: [$NBI_SOFTWARE_MGMT_FOLDER]"
      mkdir -p $NBI_SOFTWARE_MGMT_FOLDER
      ${CHMOD} 2775 $NBI_SOFTWARE_MGMT_FOLDER
      [ ! -z "$USER_GROUP" ] && ${CHOWN} -h "$USER_GROUP" $NBI_SOFTWARE_MGMT_FOLDER
    fi
    STORAGE_SOFTWARE_MGMT="$CLUSTER_SWPKG_APG"
  fi

  if [ -L $NBI_SOFTWARE_MGMT ]; then
    local LINK_NAME=$( readlink "$NBI_SOFTWARE_MGMT")
    if [[ "$LINK_NAME" != "$STORAGE_SOFTWARE_MGMT" ]]; then
      local PRINTOUT="deleting symbolic link: [$NBI_SOFTWARE_MGMT -> $LINK_NAME]..."
      log "$PRINTOUT"
      rm -f $NBI_SOFTWARE_MGMT &>/dev/null
      if [ $? -ne 0 ]; then
        log "$PRINTOUT failed"
      else
        log "$PRINTOUT success"
      fi
    fi
  fi

  if [ ! -L $NBI_SOFTWARE_MGMT ];then
    if [ -d $NBI_SOFTWARE_MGMT ]; then
      log "$NBI_SOFTWARE_MGMT folder found.. skipping symbolic creation"
    else
      local PRINTOUT="creating symbolic link: $NBI_SOFTWARE_MGMT -> $STORAGE_SOFTWARE_MGMT..."
      log "$PRINTOUT"
      $CMD_LN -s $STORAGE_SOFTWARE_MGMT $NBI_SOFTWARE_MGMT &>/dev/null
      if [ $? -ne 0 ]; then
        log "$PRINTOUT failed"
      else
        log "$PRINTOUT success"
        if [ ! -z "$USER_GROUP" ]; then
          ${CHOWN} -h  "$USER_GROUP" $NBI_SOFTWARE_MGMT
          [ $? -ne 0 ] && log "INFO: Failed to change the group owner and owner for files under [$NBI_SOFTWARE_MGMT] "
        fi
      fi
    fi
  else
    # remove recursive links found if any.
    pushd $NBI_SOFTWARE_MGMT &>/dev/null
    local LINK_NAME=${NBI_SOFTWARE_MGMT##*/}
    if [ -L $LINK_NAME ]; then        
      local PRINTOUT="recursive link found in [$NBI_SOFTWARE_MGMT], removing..."
      log "$PRINTOUT"
      rm -r $LINK_NAME &>/dev/null
      if [ $? -ne 0 ]; then  
        log "$PRINTOUT failed"
      else
        log "$PRINTOUT success"
      fi
    fi
  fi

  # this case is to retain the permissions of /cluster/sw_package/APG and nbi_root/SoftwareManagement
  # after the upgrade, while applying the permissions to only /cluster/sw_package/APG/UPGRADE
  if [[ ! -z "$USER_GROUP" && "$NBI_SOFTWARE_MGMT" == "$CLUSTER_SWPKG_APG_UPGRADE" ]]; then
    local E_USER_GROUP=$( stat -c '%U:%G' $NBI_SOFTWARE_MGMT)
    if [[ ! -z "$E_USER_GROUP" && "$E_USER_GROUP" != "$USER_GROUP" ]]; then
      log "user group [$NBI_SOFTWARE_MGMT], found:[$E_USER_GROUP], expecting:[$USER_GROUP], applying"
      ${CHOWN} -h  "$USER_GROUP" $NBI_SOFTWARE_MGMT
      [ $? -ne 0 ] && log "INFO: failed to apply [$USER_GROUP] to [$NBI_SOFTWARE_MGMT]"
    fi
  fi
}

#-----------------------------------------------------------------
function init(){
  local CONFIGAP_A='/tmp/configap_a'
  [ -f $CONFIGAP_A ] && rm -f $CONFIGAP_A
	
  # create nbi_root/softwaremanagement softlink if not exist
    create_swm_softlink 'SoftwareManagement;cmw-swm:cmw-swm'
}

#-----------------------------------------------------------------
function remove_upgrade_package(){
  local STORAGE_SOFTWARE_MGMT='/storage/no-backup/coremw/SoftwareManagement'
  local CLUSTER_SWPKG_APG='/cluster/sw_package/APG'
  local CAMPAIGN_SDP=$( find $STORAGE_SOFTWARE_MGMT -type f -name ERIC-APG*\.sdp 2>/dev/null)
  local DN=$( immfind | grep -P ^upgradePackageId=APG43L-.*,CmwSwMswMId=1 2>/dev/null)
  local URI=$( immlist -a uri $DN 2>/dev/null)
  local PATTERN='uri=file:///sw_package/APG/'
  local UPDIR=${URI##*$PATTERN}
  local PATTERN="$PATTERN$UPDIR" 

  if [ -z "$CAMPAIGN_SDP" ]; then 
    # this should cover upgrade paths 3.x -> 3.5
    log 'info: no campaign sdp found'
    return
  fi

  if [ "$URI" ==  "$PATTERN" ]; then
    local UPDIR=${UPDIR%%/*}
    if [ -d "$STORAGE_SOFTWARE_MGMT/$UPDIR" ]; then
      local PRINTOUT=''
      if [ -d $CLUSTER_SWPKG_APG/$UPDIR ]; then 
        # rename the exising folder with .upgrade
        PRINTOUT="moving the folder:[$CLUSTER_SWPKG_APG/$UPDIR -> $CLUSTER_SWPKG_APG/$UPDIR.upgrade]..."
        log "$PRINTOUT"
        mv -f $CLUSTER_SWPKG_APG/$UPDIR $CLUSTER_SWPKG_APG/$UPDIR.upgrade 2>/dev/null
        if [ $? -ne 0 ]; then
          log "$PRINTOUT failed"
        else
          log "$PRINTOUT success"
        fi 
      fi

      local PRINTOUT="moving the folder:[$STORAGE_SOFTWARE_MGMT/$UPDIR -> $CLUSTER_SWPKG_APG]..."
      log "$PRINTOUT"
      mv -f $STORAGE_SOFTWARE_MGMT/$UPDIR $CLUSTER_SWPKG_APG 2>/dev/null
      if [ $? -ne 0 ]; then
        log "$PRINTOUT failed"
      else
        log "$PRINTOUT success"
      fi
    else
      log "info: folder [$STORAGE_SOFTWARE_MGMT/$UPDIR] not found"
    fi
  else
    log "info: uri [$URI] not found"
  fi 
}

#-----------------------------------------------------------------
function commit(){
  local CONFIGAP_A='/tmp/configap_a'
  [ -f $CONFIGAP_A ] && rm -f $CONFIGAP_A
	
  # create nbi_root/softwaremanagement softlink if not exist
  create_swm_softlink 'SoftwareManagement;cmw-swm:cmw-swm'
 
  # create nbi_root/sw_package/APG softlink if not exist
  create_swm_softlink 'sw_package/APG;root:SWPKGGRP'

  # create nbi_root/sw_package/APG softlink if not exist
  create_swm_softlink 'sw_package/APG/UPGRADE;root:system-nbi-data'

  # move sw_package/APG/UPGRADE/UP --> sw_package/APG/UP if found
  remove_upgrade_package
}

# _____________________ _____________________
#|    _ _   _  .  _    |    _ _   _  .  _    |
#|   | ) ) (_| | | )   |   | ) ) (_| | | )   |
#|_____________________|_____________________|
# Here begins the "main" function...

log "START: <$0 $*>"

OPTION="$1"

if [ "$OPTION" == '--init' ]; then 
  init
elif [ "$OPTION" == '--commit' ]; then
  commit
else
  log 'invalid option'
fi

log "END: <$0 $*>"

exit 0

