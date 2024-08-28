#!/bin/bash -x
##
# ------------------------------------------------------------------------
#     Copyright (C) 2013 Ericsson AB. All rights reserved.
# ------------------------------------------------------------------------
##
# Name:
#      apg_symlink_update.sh  
# Description:
#       A script to change symlink of sw_package/APG 
# Note:
#       None.
##
# Output:
#       None.
##
# Changelog:
# - 2017 Dec 01 - Swetha R (xsweram)
#       First version.
##

# Load the apos common functions.

. /opt/ap/apos/conf/apos_common.sh

apos_intro $0

#commnd list to use
###############################
CMD_READLINK='/usr/bin/readlink'
CMD_LN='/bin/ln'
CMD_RM='/usr/bin/rm'

SoftwareManagementDir='/storage/no-backup/coremw/SoftwareManagement'
DataSwPackageDir='/data/opt/ap/internal_root/sw_package/APG'
ClusterSwPackageDir='/cluster/sw_package/APG'

function create_newlink(){  
  apos_log "(enter) create_newlink"
  local SwPackageDir=$( $CMD_READLINK -f $DataSwPackageDir 2>/dev/null)
	
	if [[ ! -z "$SwPackageDir" && "$SwPackageDir" != "$SoftwareManagementDir" ]]; then
	  # delete the old link
		$CMD_RM -f $DataSwPackageDir
		
		# create the new one
		apos_log "creating the softlink: $SoftwareManagementDir -> $DataSwPackageDir"
	  $CMD_LN -s $SoftwareManagementDir $DataSwPackageDir 2>/dev/null
  elif [[ -z "$SwPackageDir" ]]; then
	  # create the new one
		apos_log "creating the softlink: $SoftwareManagementDir -> $DataSwPackageDir"
	  $CMD_LN -s $SoftwareManagementDir $DataSwPackageDir 2>/dev/null
	fi 
	
	apos_log "(exit) create_newlink"
}
 
 
function restore_oldlink(){
  apos_log "(enter) restore_oldlink"
   
  local SwPackageDir=$( $CMD_READLINK -f $DataSwPackageDir 2>/dev/null)
	if [[ ! -z "$SwPackageDir" && "$SwPackageDir" == "$SoftwareManagementDir" ]]; then
	  # delete the old link
		$CMD_RM -f $DataSwPackageDir
		
		# create the new one
		apos_log "creating the softlink: $ClusterSwPackageDir -> $DataSwPackageDir"
	  $CMD_LN -s $ClusterSwPackageDir $DataSwPackageDir 2>/dev/null
  elif [[ -z "$SwPackageDir" ]]; then
	  # create the new one
		apos_log "creating the softlink: $SoftwareManagementDir -> $DataSwPackageDir"
	  $CMD_LN -s $ClusterSwPackageDir $DataSwPackageDir 2>/dev/null
	fi 
	
	apos_log "(exit) restore_oldlink"
}


#### M A I N #####
NODE_1_STATE=$(amf-state siass ha safSISU=safSu=1\\,safSg=2N\\,safApp=ERIC-APG,safSi=AGENT,safApp=ERIC-APG | grep saAmfSISUHAState | awk -F'=' '{print $2}'| awk -F'(' '{print $1}')
#Get Node 2 Status
NODE_2_STATE=$(amf-state siass ha safSISU=safSu=2\\,safSg=2N\\,safApp=ERIC-APG,safSi=AGENT,safApp=ERIC-APG | grep saAmfSISUHAState | awk -F'=' '{print $2}'| awk -F'(' '{print $1}')

NODE=""

if [ "$NODE_1_STATE" = "ACTIVE" ];then
  NODE="SC-2-1"
elif [ "$NODE_1_STATE" = "STANDBY" ]; then
  NODE="SC-2-2"
else
  abort "APG STATUS NOT VALID"
fi

THIS_NODE=$(cat /etc/cluster/nodes/this/hostname)
if [ "$THIS_NODE" = "$NODE" ]; then
  if [ "$1" == "do" ];then
    create_newlink
  elif [ "$1" == "undo" ];then
    restore_oldlink
  else
    apos_log "invalid argument"
  fi
else
  apos_log "Node is Passive skip!!!"
fi

apos_outro $0

exit $TRUE    
     

