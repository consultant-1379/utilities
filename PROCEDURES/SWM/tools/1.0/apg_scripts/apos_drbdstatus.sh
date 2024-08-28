#!/bin/bash
##
# ------------------------------------------------------------------------
#     Copyright (C) 2012 Ericsson AB. All rights reserved.
# ------------------------------------------------------------------------
##
# Name:
#       apos_drbdstatus.sh
# Description:
#       A script to check if DRBD1 synchronization is in progress during 
#       Software Upgrade.
# Note:
#       None.
##
# Usage:
#       apos_drbdstatus.sh
##
# Output:
#       None.
##
# Changelog:
# - Tue Jan 30 2018 - Avinash Gundlapally (xavigun)
#       Adopted the script to SLES12 SP2 changes
#
# - Thu Dec  07 2017 - Raghavendra Koduri  (xkodrag)
#
# - Tue sep 03 2013 - Pratap Reddy  (xpraupp)
#       First version.
##

DRBD_RESOURCE='drbd1'
CMD_DRBDADM='/sbin/drbdadm'
CMD_HWTYPE='/opt/ap/apos/conf/apos_hwtype.sh'
TAG='-t apos_drbdstatus.sh'
TRUE=$( true;echo $? )
FALSE=$( false;echo $? )

function log() {
    /bin/logger $TAG "$1"
}
function show_repstate(){
  local rep_state=''
  local is_replicating=''
  is_replicating=$($CMD_DRBDADM status $DRBD_RESOURCE | grep -w " replication")
  if [ "$is_replicating" == "" ];then
    rep_state=$($CMD_DRBDADM cstate $DRBD_RESOURCE)
  else
    rep_state=$($CMD_DRBDADM status $DRBD_RESOURCE | grep -w " replication"|awk -F : '{print $2}' | awk '{print $1}')
  fi
  echo $rep_state
}
is_syncOn() {
     cstate=$(show_repstate)
     [[ "$cstate" == 'SyncSource'    || "$cstate" == 'SyncTarget'  ]] && return $TRUE
     [[ "$cstate" == 'StartingSyncS' || "$cstate" == 'PausedSyncS' ]] && return $TRUE
     [[ "$cstate" == 'StartingSyncT' || "$cstate" == 'PausedSyncT' ]] && return $TRUE
     return $FALSE
}

log "START:"
rCode=$TRUE

HW_TYPE=$( $CMD_HWTYPE)
[[ $HW_TYPE =~ "GEP5"  || $HW_TYPE =~ "GEP7" || $HW_TYPE =~ "VM" ]] && {
    is_syncOn && {
        log "APOS DRBD Synchronization is in progress,Software Upgrade is not allowed."
        rCode=$FALSE
    }
}

log "END:"
exit $rCode


