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
# - Thur Dec  07 2017 - Raghavendra Koduri  (xkodrag)
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

is_syncOn() {
     cstate=$( $CMD_DRBDADM cstate $DRBD_RESOURCE 2>/dev/null)
     [[ "$cstate" == 'SyncSource'    || "$cstate" == 'SyncTarget'  ]] && return $TRUE
     [[ "$cstate" == 'StartingSyncS' || "$cstate" == 'PausedSyncS' ]] && return $TRUE
     [[ "$cstate" == 'StartingSyncT' || "$cstate" == 'PausedSyncT' ]] && return $TRUE
     return $FALSE
}

log "START:"
rCode=$TRUE

HW_TYPE=$( $CMD_HWTYPE)
[[ $HW_TYPE =~ "GEP5"  || $HW_TYPE =~ "GEP7" ]] && {
    is_syncOn && {
        log "APOS DRBD Synchronization is in progress,Software Upgrade is not allowed."
        rCode=$FALSE
    }
}

log "END:"
exit $rCode


