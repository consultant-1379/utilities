#!/bin/bash
##
# ------------------------------------------------------------------------
#     Copyright (C) 2016 Ericsson AB. All rights reserved.
# ------------------------------------------------------------------------
##
# Name:
#       apg_change_permission.sh
# Description:
#       A script to change permissions to some folders
#
# Note:
#       None.
##
# Output:
#       None.
##
# Changelog:
#
# - Thu Oct 26 2017 - Asif Darvajkar (xasidar)
#	Fix TR HW13995 
# - Wed Nov 30 2016 - Fabio Ronca (efabron)
#       Fix TR HV44046
#
# - Fri Apr 22 2016 - Franco D'Ambrosio (efradam)
#       Added the directories in /data/opt/ap/internal_root/sw_package
#       to FOLDER_LIST.
#
# - Tue Mar 29 2016 - Franco D'Ambrosio (efradam)
#       First version.
##

# Load the apos common functions.
. /opt/ap/apos/conf/apos_common.sh

# Variables
FOLDER_LIST="/data/cps:777
/data/apz/logs:775
/data/opt/ap/internal_root:777
/data/opt/ap/internal_root/certificates:775
/data/opt/ap/internal_root/data_transfer/data_mirrored:775
/data/opt/ap/internal_root/data_transfer/destinations:775
/data/opt/ap/internal_root/health_check/reports:775
/data/opt/ap/internal_root/health_check/rules:775
/data/opt/ap/internal_root/media:775
/data/opt/ap/internal_root/sw_package/APG:777
/data/opt/ap/internal_root/sw_package/CMXB:775
/data/opt/ap/internal_root/sw_package/CP:775
/data/opt/ap/internal_root/sw_package/CP/CCF:775
/data/opt/ap/internal_root/sw_package/EPB1:775
/data/opt/ap/internal_root/sw_package/EvoET:775
/data/opt/ap/internal_root/sw_package/FW:775
/data/opt/ap/internal_root/sw_package/IPLB:775
/data/opt/ap/internal_root/sw_package/IPTB:775
/data/opt/ap/internal_root/sw_package/SCXB:775
/data/opt/ap/internal_root/sw_package/SMXB:775
/data/opt/ap/internal_root/sw_package/zip:775"


FOLDER_PARENT_LIST="/data/opt/ap/internal_root/data_transfer/source/cp_file:776
/data/opt/ap/internal_root/data_transfer/source:775
/data/opt/ap/internal_root/cp/mml:770"


# The function will check for the script's prerequisites to be satisfied.
function sanity_check(){
 
    CMD_CHMOD=$( which chmod 2>/dev/null )
	[ -z "$CMD_CHMOD" ] && CMD_CHMOD='/usr/bin/chmod'
	
	CMD_STAT=$( which stat 2>/dev/null )
	[ -z "$CMD_STAT" ] && CMD_STAT='/usr/bin/stat'

}

function apply_permission() {
  local OLD_PERMS=''
  local NEW_PERMS=''
  local permit=$1
  local folder=$2

  if [[ ! -z $permit && ! -z $folder ]]; then
    if [ -d $folder ]; then
      apos_log "Applying permissions $permit on folder \"$folder\"... "
      OLD_PERMS=$($CMD_STAT -c "%a" "$2") 
      apos_log "Current permissions: $OLD_PERMS"
      $CMD_CHMOD $permit $folder 2>/dev/null
      if [ $? -eq 0 ]; then
        NEW_PERMS=$($CMD_STAT -c "%a" "$2") 
        apos_log "Permissions changed from $OLD_PERMS to $NEW_PERMS"
      else
        apos_log "WARNING: failure while setting permissions $permit on folder: \"$folder\" with permission $OLD_PERMS"
      fi
    else
      apos_log "WARNING: folder $folder does not exist. Skip it!!!"
    fi
  fi
}


function fix_permission() {
  
  local OLD_PERMS=''
  local NEW_PERMS=''
  local CHILD_FOLDER=''
  local permit=$1
  local parent_folder=$2
  
  apos_log "Check parent folder \"$parent_folder\"...  "
  if [ -d "$parent_folder" ]; then
    while read F; do
      OLD_PERMS=$($CMD_STAT -c "%a" "$F")
      apos_log "Check children folder \"$F\" having permission: $OLD_PERMS... "
      $CMD_CHMOD $permit $F 2>/dev/null
      if [ $? -eq 0 ]; then
        NEW_PERMS=$($CMD_STAT -c "%a" "$F") 
        apos_log "Permissions changed from $OLD_PERMS to $NEW_PERMS"
      else
        apos_log "WARNING: failure while setting permissions $permit on folder: \"$F\" with permission $OLD_PERMS"
      fi	
    done < <(find $parent_folder -mindepth 1 -maxdepth 1 -type d)   
  else
    apos_log "WARNING: Parent folder \"$parent_folder\" not exist."
  fi
}



#                                              __    __   _______   _   __    _
#                                             |  \  /  | |  ___  | | | |  \  | |
#                                             |   \/   | | |___| | | | |   \ | |
#                                             | |\  /| | |  ___  | | | | |\ \| |
#                                             | | \/ | | | |   | | | | | | \   |
#                                             |_|    |_| |_|   |_| |_| |_|  \__|
#

#set -x

apos_intro $0

sanity_check

FOLDER=''
PERMIT=''

NODE_ID=$(cat /etc/nodeid)
#Get Node Status
NODE_STATE=$(amf-state siass ha safSISU=safSu=$NODE_ID\\,safSg=2N\\,safApp=ERIC-APG,safSi=AGENT,safApp=ERIC-APG | grep saAmfSISUHAState | awk -F'=' '{print $2}'| awk -F'(' '{print $1}')

if [ "$NODE_STATE" = "ACTIVE" ];then
  apos_log "Execute the script"
  for F in $FOLDER_LIST; do
    FOLDER=$(echo $F | awk -F':' '{print $1}')
    PERMIT=$(echo $F | awk -F':' '{print $2}')
    apply_permission $PERMIT $FOLDER
  done
  
  PERMIT=''
  FOLDER=''
  
  for F in $FOLDER_PARENT_LIST; do
    FOLDER=$(echo $F | awk -F':' '{print $1}')
    PERMIT=$(echo $F | awk -F':' '{print $2}')
    fix_permission $PERMIT $FOLDER
  done
	
elif [ "$NODE_STATE" = "STANDBY" ]; then
	apos_log "Node is passive, skip the script"
else
	apos_abort "ERROR: APG status not valid"
fi

apos_outro $0
exit $TRUE

