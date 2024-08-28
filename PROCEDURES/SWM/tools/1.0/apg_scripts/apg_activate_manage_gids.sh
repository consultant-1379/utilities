#!/bin/bash -x
##
# ------------------------------------------------------------------------
#     Copyright (C) 2016 Ericsson AB. All rights reserved.
# ------------------------------------------------------------------------
##
# Name:
#       apg_activate_manage_gids.sh
# Description:
#      A script to activate the option manage-gids
#
# Note:
#      -
##
# Output:
#       None.
##
# Changelog:
# - Tue Jan 9 2018 - Avinash Gundlapally (xavigun)
#       adopted the script for SLES 12 SP2 changes.
#
# - Sat May 14 2016 - Fabio Ronca (efabron)
#       First version.
##

# Load the apos common functions.
. /opt/ap/apos/conf/apos_common.sh

SCRIPT_PATH=$(dirname $0)
SCRIPT_TO_EXECUTE=$(basename $0)
HOST_TO_CONNECT=''
CLUSTER_FILE='/cluster/etc/cluster.conf'
CMD_HWTYPE='/opt/ap/apos/conf/apos_hwtype.sh'
DRBDADM="/sbin/drbdadm"

# The function will check for the script's prerequisites to be satisfied.
function sanity_check(){

        CMD_CAT=$( which cat 2>/dev/null )
        [ -z "$CMD_CAT" ] && CMD_CAT='/usr/bin/cat'

        CMD_SSH=$( which ssh 2>/dev/null )
        [ -z "$CMD_SSH" ] && CMD_CAT='/usr/bin/ssh'

        CMD_GREP=$( which grep 2>/dev/null )
        [ -z "$CMD_GREP" ] && CMD_GREP='/usr/bin/grep'

        CMD_HEAD=$( which head 2>/dev/null )
        [ -z "$CMD_HEAD" ] && CMD_HEAD='/usr/bin/head'

        CMD_AWK=$( which awk 2>/dev/null )
        [ -z "$CMD_AWK" ] && CMD_AWK='/usr/bin/awk'

        CMD_TR=$( which tr 2>/dev/null )
        [ -z "$CMD_TR" ] && CMD_TR='/usr/bin/tr'


}

# The fucntion is to fetch roles of drbd resource on local and peer node.
function show_role(){
  OWN_HOSTNAME=$(</etc/cluster/nodes/this/hostname)
  PEER_HOSTNAME=$(</etc/cluster/nodes/peer/hostname)
  local own_role=""
  local peer_role=""
  local exit_fail=1 
  if [ $3 == "local" ]; then
    own_role=$($DRBDADM status $2 | $CMD_GREP -w "$2 $1" | $CMD_AWK -F : '{print $2}' | $CMD_AWK '{print $1}')
    if [ "$own_role" == "" ]; then
      apos_abort "Failed to fetch role of local node for $2"
    fi
    echo $own_role
  elif [ $3 == "peer" ]; then
    peer_role=$($DRBDADM status $2 | $CMD_GREP -w "$PEER_HOSTNAME $1" | $CMD_AWK -F : '{print $2}' | $CMD_AWK '{print $1}')
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
LDE_INFO="lde-info"
os_version=$($CMD_CAT /etc/*release| $CMD_GREP -P '^VERSION[[:space:]]*='| $CMD_HEAD -n 1| $CMD_AWK -F'=' '{print $2}'| $CMD_TR -d [[:space:]])

lde_version=$($LDE_INFO | $CMD_GREP -E '^Version' | $CMD_AWK -F ' ' '{print $2}')
[ -z $os_version ] && apos_abort "ERROR: Unable to determinate the OS version installed."
if [ "$os_version" == "11" ]; then
  HOST_TO_CONNECT=$($CMD_CAT /etc/cluster/nodes/peer/hostname)
  HOST_TO_CONNECT_PEER=$($CMD_CAT /etc/cluster/nodes/this/hostname)
elif [ "$os_version" == "12" ]; then
    peer_os_version=$(ssh $($CMD_CAT /etc/cluster/nodes/peer/hostname) "cat /etc/*release| grep -P '^VERSION[[:space:]]*='| head -n 1| awk -F'=' '{print \$2}'| tr -d [[:space:]]")
    if [ "$peer_os_version" == "12" ];then
      if [ "$lde_version" = "R2A08" ];then
        HOST_TO_CONNECT=$($CMD_CAT /etc/cluster/nodes/peer/hostname)
        HOST_TO_CONNECT_PEER=$($CMD_CAT /etc/cluster/nodes/this/hostname)
      else
        HOST_TO_CONNECT=$($CMD_CAT /etc/cluster/nodes/this/hostname)
        HOST_TO_CONNECT_PEER=$($CMD_CAT /etc/cluster/nodes/peer/hostname)
      fi
    else
      HOST_TO_CONNECT=$($CMD_CAT /etc/cluster/nodes/this/hostname)
      HOST_TO_CONNECT_PEER=$($CMD_CAT /etc/cluster/nodes/peer/hostname)
    fi
else
  apos_abort "ERROR: OS Version: $os_version NOT valid. "
fi

[ -z $HOST_TO_CONNECT ] && apos_abort "ERROR: Unable to determinate the node where execute the script."
apos_log "Applying patch on node $HOST_TO_CONNECT"


# Check if the option is already present
/usr/bin/ssh $HOST_TO_CONNECT /usr/bin/grep -q 'nfs-manage-gids' /cluster/etc/cluster.conf
if [ $? -ne 0 ]; then
  /usr/bin/ssh $HOST_TO_CONNECT_PEER sed -i \'\/ssh.rootlogin control off\/a\\\\n# Enable GIDs lookup locally on the NFS server\\nnfs-manage-gids on\' /cluster/etc/cluster.conf
  if [ $? -eq 0 ]; then
        #Validate cluster.conf
        apos_log "Validate cluster.conf"
        $CMD_SSH $HOST_TO_CONNECT cluster config -v -V
        [ $? -ne 0 ] && apos_abort "ERROR: cluster.conf validation failed after updation on node $HOST_TO_CONNECT"
        apos_log "Cluster conf validation successful!"
  else
    apos_abort "Failure while adding nfs-manage-gids option in cluster.conf on node $HOST_TO_CONNECT"
  fi
  
  #Reload cluster.conf
  $CMD_SSH $HOST_TO_CONNECT cluster config -r -V
  [ $? -ne 0 ] && apos_abort "ERROR: cluster.conf reload failed on node HOST_TO_CONNECT"
  
  #restart of failoverd
  #drbd_role=$(drbd-overview | grep drbd0 | awk -F' ' '{print $3}')
  #[ -z $drbd_role ] && apos_abort "ERROR: Unable to determinate the DRDB role."
  own_role=$(show_role role drbd0 local)
  if [ $? -ne 0 ]; then
    apos_abort "ERROR: failed to fetch drbd0 role"
  fi
  peer_role=$(show_role role drbd0 peer)
  if [ $? -ne 0 ]; then
    apos_abort "ERROR: failed to fetch drbd0 role"
  fi

  drbd_role="$own_role/$peer_role"
  
   if [[ $drbd_role == "Secondary/Primary" ]]; then
     HOST_TO_CONNECT=$($CMD_CAT /etc/cluster/nodes/peer/hostname)
     $CMD_SSH $HOST_TO_CONNECT "service lde-failoverd stop"
     sleep 1
     $CMD_SSH $HOST_TO_CONNECT "$DRBDADM up drbd0"
     sleep 1
     $CMD_SSH $HOST_TO_CONNECT "$DRBDADM secondary drbd0"
     sleep 1
     $CMD_SSH $HOST_TO_CONNECT "service lde-failoverd start"
   elif [[ $drbd_role == "Primary/Secondary" ]]; then
     service lde-failoverd stop
     sleep 1
     $DRBDADM up drbd0
     sleep 1
     $DRBDADM secondary drbd0
     sleep 1
     service lde-failoverd start
   else
     apos_abort "ERROR: Unable to take a decision: OS Version: $os_version DRBD ROLE: $drbd_role "
   fi  
else
  apos_log "Option nfs-manage-gids already present on node $HOST_TO_CONNECT: Nothing to do"
fi
	
apos_outro $0
exit $TRUE

