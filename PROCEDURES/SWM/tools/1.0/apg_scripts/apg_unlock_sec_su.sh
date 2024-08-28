#!/bin/bash
##
# ------------------------------------------------------------------------
#     Copyright (C) 2016 Ericsson AB. All rights reserved.
# ------------------------------------------------------------------------
##
# Name:
#       apg_unlock_sec_su.sh
# Description:
#       A script to modify unlock the SU of SEC (sec-LA and sec-Acs)
#
# Note:
#       None.
##
# Output:
#       None.
##
# Changelog:
#
# - Tue Mar 29 2016 - Franco D'Ambrosio (efradam)
#       First version.
##

# Load the apos common functions.
. /opt/ap/apos/conf/apos_common.sh

# The function will check for the script's prerequisites to be satisfied.
function sanity_check(){

    CMD_GREP=$( which grep 2>/dev/null )
        [ -z "$CMD_GREP" ] && CMD_GREP='/usr/bin/grep'

        CMD_AWK=$( which awk 2>/dev/null )
        [ -z "$CMD_AWK" ] && CMD_AWK='/usr/bin/awk'

}


#                                              __    __   _______   _   __    _
#                                             |  \  /  | |  ___  | | | |  \  | |
#                                             |   \/   | | |___| | | | |   \ | |
#                                             | |\  /| | |  ___  | | | | |\ \| |
#                                             | | \/ | | | |   | | | | | | \   |
#                                             |_|    |_| |_|   |_| |_| |_|  \__|
#

apos_intro $0

sanity_check
NODE_ID=''
FILE='nodeID'
FOLDER='/cluster/storage/clear/apos'

UPGRADED_NODE=$(cmw-repository-list --node | $CMD_GREP -i sec-la-ldap | $CMD_AWK '{print $1}')
[ -z "$UPGRADED_NODE" ] && apos_abort "ERROR: SEC bundle not imported in the system"
NUMBER_OF_NODES=$(echo $UPGRADED_NODE | wc -w)
if [ $NUMBER_OF_NODES -eq 1 ]; then
  apos_log "Number of node where SecLa bundle is imported is $NUMBER_OF_NODES. I suppose that is the first node to upgrade"
  NODE_ID=$(echo $UPGRADED_NODE | $CMD_AWK -F '-' '{print $3}')
  [ -z "$NODE_ID" ] && apos_abort "ERROR: Impossible fetch the NODE_ID"
  apos_log "Node where perform the unlock has NODE_ID $NODE_ID"
else
  apos_log "Number of node where SecLa bundle is imported is $NUMBER_OF_NODES. This is the second node to upgrade."
  SU_STATE=$(immlist -a saAmfSUAdminState safSu=SC-1,safSg=2N,safApp=ERIC-SecLa | awk -F '=' '{print$2}')
  [ -z "$SU_STATE" ] && apos_abort "ERROR: Impossible fetch the Administrative state of SU of SecLA"
  if [ $SU_STATE -eq 1 ]; then
    NODE_ID="2"
  else
    NODE_ID="1"
  fi
fi

#unlock-in SecAcs and SecLa SU on node
amf-adm unlock-in safSu=SC-$NODE_ID,safSg=NoRed,safApp=ERIC-SecAcs
[ $? -ne 0 ] && apos_abort "ERROR: unlock-in of SU safSu=SC-$NODE_ID,safSg=NoRed,safApp=ERIC-SecAcs failed"
amf-adm unlock-in safSu=SC-$NODE_ID,safSg=2N,safApp=ERIC-SecLa
[ $? -ne 0 ] && apos_abort "ERROR: unlock-in of SU safSu=SC-$NODE_ID,safSg=2N,safApp=ERIC-SecLa failed"
#unlock SecAcs and SecLa SU on the first node
amf-adm unlock safSu=SC-$NODE_ID,safSg=NoRed,safApp=ERIC-SecAcs
[ $? -ne 0 ] && apos_abort "ERROR: unlock of SU safSu=SC-$NODE_ID,safSg=NoRed,safApp=ERIC-SecAcs failed"
amf-adm unlock safSu=SC-$NODE_ID,safSg=2N,safApp=ERIC-SecLa
[ $? -ne 0 ] && apos_abort "ERROR: unlock of SU safSu=SC-$NODE_ID,safSg=2N,safApp=ERIC-SecLa failed"


apos_outro $0
exit $TRUE
