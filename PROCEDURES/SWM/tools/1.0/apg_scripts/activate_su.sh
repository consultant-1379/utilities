#!/bin/bash
##
# ------------------------------------------------------------------------
#     Copyright (C) 2014 Ericsson AB. All rights reserved.
# ------------------------------------------------------------------------
##
# Description:
#       Script used to activate SUs during software upgrade/installation.
##
##
# Changelog:
# - Apr 29 2014 - Fabrizio Paglia (XFABPAG)
#       First version
##

#Exit codes
EXIT_SUCCESS=0
EXIT_FAILURE=1

#Input parameters
if [ $# -ne 1 ] ; then
	exit $EXIT_FAILURE
fi

SU="$1"

#Constants
TRUE=$(true;echo $?)
FALSE=$(false;echo $?)
LOG_TAG="swu_activate_su"

#Commands
CMD_LOGGER=$( which logger 2>/dev/null )
AMFADM_CMD=$( which amf-adm 2>/dev/null )
if [ $? -ne 0 ]; then
	die "Command amf-adm command which is required to activate the SUs is not found."
fi

#######################################################################
#                             Functions                               #
#######################################################################

#######################################################################
# function log($message);                                             #
#                                                                     #
# Arguments:                                                          #
# $message message to append to the system log                        #
#######################################################################
function log() {
        local message="${*:-notice}"
        local prio='-p user.notice'
        
        ${CMD_LOGGER} $prio $LOG_TAG "$message"
}

#######################################################################
# function log_error($message);                                       #
#                                                                     #
# Arguments:                                                          #
# $message error message to append to the system log                  #
#######################################################################
function log_error() {
        local message="${*:-error}"
        local prio='-p user.err'
        
        ${CMD_LOGGER} $prio $LOG_TAG "$message"
}

#######################################################################
# function die($message);                                             #
#                                                                     #
# Arguments:                                                          #
# $message error message to append to the system log                  #
#######################################################################
function die() {
        log_error $*
        exit $EXIT_FAILURE
}

#######################################################################
#                               MAIN                                  #
#######################################################################

log "Unlocking instantiation of $SU"
error_msg=$($AMFADM_CMD unlock-in $SU 2>&1)
if [ $? -ne 0 ]; then
    die "Failed to unlock instantiation $SU. $error_msg" 
fi
log "Unlocking $SU"
error_msg=$($AMFADM_CMD unlock $SU 2>&1)
if [ $? -ne 0 ]; then
    die "Failed to unlock $SU. $error_msg" 
fi

exit $EXIT_SUCCESS

