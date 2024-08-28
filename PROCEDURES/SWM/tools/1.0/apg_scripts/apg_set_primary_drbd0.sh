#!/bin/bash
##
# ------------------------------------------------------------------------
#     Copyright (C) 2016 Ericsson AB. All rights reserved.
# ------------------------------------------------------------------------
##
# Name:
#       apg_set_primary_drbd0.sh
# Description:
#       A script to set the primary role of DRBD0 on active node
#
# Note:
#       PA3
##
# Output:
#       None.
##
# Changelog:
# - Tue Jan 9 2018 - Avinash Gundlapally (xavigun)
#	adopted the script for SLES 12 SP2 changes.
#
# - Wed June 28 2017 - Fabio Ronca 
#      Added log and sleep for avaDown issue
#
# - Fri June 23 2017 - Praveen Kumar (XKUPRAV)
#       Added commands to su change.
#
# - Tue Mar 7 2017 - Yeswanth Vankayala (xyesvan)
#       First version
##

# Load the apos common functions.
. /opt/ap/apos/conf/apos_common.sh
DRBDADM="/sbin/drbdadm"

# The function will check for the script's prerequisites to be satisfied.
function sanity_check(){

    CMD_GREP=$( which grep 2>/dev/null )
    [ -z "$CMD_GREP" ] && CMD_GREP='/usr/bin/grep'

    CMD_AWK=$( which awk 2>/dev/null )
    [ -z "$CMD_AWK" ] && CMD_AWK='/usr/bin/awk'

    CMD_SSH=$( which ssh 2>/dev/null )
    [ -z "$CMD_SSH" ] && CMD_SSH='/usr/bin/ssh'

    CMD_SYM=$( which systemctl 2>/dev/null )
    [ -z "$CMD_SYM" ] && CMD_SYM='/usr/bin/systemctl'
    
    CMD_REPO_LIST=$( which cmw-repository-list 2>/dev/null )
    [ -z "$CMD_REPO_LIST" ] && CMD_REPO_LIST='/opt/coremw/bin/cmw-repository-list'

}

# The fucntion is to fetch roles of drbd resource on local and peer node.
function show_role(){
  OWN_HOSTNAME=$(</etc/cluster/nodes/this/hostname)
  PEER_HOSTNAME=$(</etc/cluster/nodes/peer/hostname)
  local own_role=""
  local peer_role=""
  local exit_fail=1
  
  if [ $3 == "local" ]; then
    own_role=$($CMD_SSH $UPGRADED_NODE $DRBDADM status $2 | $CMD_GREP -w "$2 $1" | $CMD_AWK -F : '{print $2}' | $CMD_AWK '{print $1}')
    if [ "$own_role" == "" ]; then
      apos_abort "Failed to fetch role of local node for $2"
    fi
    echo $own_role
  elif [ $3 == "peer" ]; then
    peer_role=$($CMD_SSH $UPGRADED_NODE $DRBDADM status $2 | $CMD_GREP -w "$OWN_HOSTNAME $1" | $CMD_AWK -F : '{print $2}' | $CMD_AWK '{print $1}')
    if [ "$peer_role" == "" ]; then
      apos_abort "Failed to fetch role of peer node for $2"
    fi
    echo $peer_role
  else
    apos_abort "Invalid argument $3"
  fi
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
drbd_role=''
HOST_TO_CONNECT=''
status=''

UPGRADED_NODE=$($CMD_REPO_LIST --node | $CMD_GREP -i sec-ldap-sm | $CMD_AWK '{print $1}')
[ -z "$UPGRADED_NODE" ] && apos_abort "ERROR: SEC bundle not imported in the system"
apos_log "upgraded node which sec ldap is updated $UPGRADED_NODE"


NUMBER_OF_NODES=$(echo $UPGRADED_NODE | wc -w)
if [ $NUMBER_OF_NODES -eq 1 ]; then
  apos_log "Number of node where sec-ldap-sm bundle is imported is $NUMBER_OF_NODES. I suppose that is the first node to upgrade"
  own_role=$(show_role role drbd0 local $UPGRADED_NODE)
  if [ $? -ne 0 ]; then
    apos_abort "ERROR: failed to fetch drbd0 role"
  fi
  peer_role=$(show_role role drbd0 peer $UPGRADED_NODE)
  if [ $? -ne 0 ]; then
    apos_abort "ERROR: failed to fetch drbd0 role"
  fi
  drbd_role="$own_role/$peer_role"

  #drbd_role=$($CMD_SSH $UPGRADED_NODE $DRBD_CMD)
  apos_log "Role of DRBD0 is $drbd_role"
  [ -z "$drbd_role" ] && apos_abort "ERROR: Impossible fetch the drbd0 status on $UPGRADED_NODE node"
  if [ $drbd_role == "Secondary/Primary" ]; then
    apos_log "Change drbd0 role on node $UPGRADED_NODE"
    if [ "$UPGRADED_NODE" == "SC-2-2" ]; then
      HOST_TO_CONNECT="SC-2-1"
      apos_log "Stop lde-failoved on node $HOST_TO_CONNNECT"
      $CMD_SSH $HOST_TO_CONNECT $CMD_SYM "stop lde-failoverd"
      [ $? -ne 0 ] && apos_abort "ERROR: systemctl stop command failed"
      sleep 5
      apos_log "Start lde-failoved on node $HOST_TO_CONNNECT" 
      $CMD_SSH $HOST_TO_CONNECT $CMD_SYM "start lde-failoverd"	
      [ $? -ne 0 ] && apos_abort "ERROR: systemctl start command failed"
    else
      HOST_TO_CONNECT="SC-2-2"
      apos_log "Stop lde-failoved on node $HOST_TO_CONNNECT"
      $CMD_SSH $HOST_TO_CONNECT $CMD_SYM "stop lde-failoverd"
      [ $? -ne 0 ] && apos_abort "ERROR: systemctl stop command failed"
      sleep 5
      apos_log "Start lde-failoved on node $HOST_TO_CONNNECT"
      $CMD_SSH $HOST_TO_CONNECT $CMD_SYM "start lde-failoverd"
      [ $? -ne 0 ] && apos_abort "ERROR: systemctl  start command failed"
    fi
	sleep 2
  else
    sleep 2
    apos_log "The $UPGRADED_NODE node has the role primary for drbd0"
  fi
else
  apos_log "This is the second activation. Nothing to do!!"
fi

apos_outro $0
exit $TRUE


