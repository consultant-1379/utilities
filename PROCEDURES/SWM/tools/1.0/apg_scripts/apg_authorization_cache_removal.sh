#!/bin/bash
##
# ------------------------------------------------------------------------
#     Copyright (C) 2016 Ericsson AB. All rights reserved.
# ------------------------------------------------------------------------
##
# Name:
#       apg_authorization_cache_removal.sh
# Description:
#      A script to remove the authorization cache used for cached credentials
#      feature during the SLES11-SLES12 update.
#
# Note:
#      -
##
# Output:
#       None.
##
# Changelog:
#
# - Wed Aug 31 2016 - Alessio Cascone (ealocae)
#       First version.
##

# Load the apos common functions.
. /opt/ap/apos/conf/apos_common.sh

# Global variables
AWK_CMD=''
CAT_CMD=''
GREP_CMD=''
HEAD_CMD=''
RM_CMD=''
SSH_CMD=''
TR_CMD=''

# Function to execute some sanity checks before starting the execution
# Usage: sanity_check
function sanity_check() {
  AWK_CMD=$(which awk 2> /dev/null)
  [ -z "$AWK_CMD" ] && AWK_CMD='/usr/bin/awk'
  
  CAT_CMD=$(which cat 2> /dev/null)
  [ -z "$CAT_CMD" ] && CAT_CMD='/usr/bin/cat'

  GREP_CMD=$(which grep 2> /dev/null)
  [ -z "$GREP_CMD" ] && GREP_CMD='/usr/bin/grep'
  
  HEAD_CMD=$(which head 2> /dev/null)
  [ -z "$HEAD_CMD" ] && HEAD_CMD='/usr/bin/head'
  
  RM_CMD=$(which rm 2> /dev/null)
  [ -z "$RM_CMD" ] && RM_CMD='/usr/bin/rm'
  
  SSH_CMD=$(which ssh 2> /dev/null)
  [ -z "$SSH_CMD" ] && SSH_CMD='/usr/bin/ssh'
  
  TR_CMD=$(which tr 2> /dev/null)
  [ -z "$TR_CMD" ] && TR_CMD='/usr/bin/tr'
}

#                                              __    __   _______   _   __    _
#                                             |  \  /  | |  ___  | | | |  \  | |
#                                             |   \/   | | |___| | | | |   \ | |
#                                             | |\  /| | |  ___  | | | | |\ \| |
#                                             | | \/ | | | |   | | | | | | \   |
#                                             |_|    |_| |_|   |_| |_| |_|  \__|
#

apos_intro $0

# Sanity check before starting
sanity_check

# Retrieve the OS version for the local node
LOCAL_OS_VERSION=$(${CAT_CMD} /etc/*release| ${GREP_CMD} -P '^VERSION[[:space:]]*='| ${HEAD_CMD} -n 1| ${AWK_CMD} -F'=' '{print $2}'| ${TR_CMD} -d [[:space:]])
[ -z "$LOCAL_OS_VERSION" ] && apos_abort 'Failed to retrieve the OS version for the local node'

# Retrieve the OS version for the peer node
PEER_NODE=$($CAT_CMD /etc/cluster/nodes/peer/hostname)
PEER_OS_VERSION=$(${SSH_CMD} $PEER_NODE ${CAT_CMD} /etc/*release| ${GREP_CMD} -P '^VERSION[[:space:]]*='| ${HEAD_CMD} -n 1| ${AWK_CMD} -F'=' '{print $2}'| ${TR_CMD} -d [[:space:]])
[ -z "$PEER_OS_VERSION" ] && apos_abort 'Failed to retrieve the OS version for the peer node'

# If the OS versions of the two nodes differ, that mean that we are in a 
# SLES11 -> SLES12 upgrade and that the authorization cache must be deleted.
# That is mainly due to the fact that Boost library version was changed and
# that the files serialized with the old version of Boost are not readable 
# with the new one.
if [ "$LOCAL_OS_VERSION" != "$PEER_OS_VERSION" ]; then
  apos_log "Local node is SLES-$LOCAL_OS_VERSION and peer node is SLES-$PEER_OS_VERSION"
  AUTHORIZATION_CACHE_FILE=/cluster/storage/clear/acs-apgccbin/rolesMap
  if [ -r "$AUTHORIZATION_CACHE_FILE" ]; then
    apos_log "Removing the '$AUTHORIZATION_CACHE_FILE' cache file!"
    ${RM_CMD} -f $AUTHORIZATION_CACHE_FILE
  else
    apos_log "The file '$AUTHORIZATION_CACHE_FILE' is not present, nothing to do!"
  fi  
else
  apos_log "Both nodes are on SLES-$LOCAL_OS_VERSION, nothing to do!"
fi

apos_outro $0
exit $TRUE
