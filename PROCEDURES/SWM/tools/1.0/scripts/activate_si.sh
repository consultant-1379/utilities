#!/bin/bash
##
# ------------------------------------------------------------------------
#     Copyright (C) 2013 Ericsson AB. All rights reserved.
# ------------------------------------------------------------------------
##
# Description:
#       Script used to activate SIs during software upgrade/installation.
##
##
# Changelog:
# - Apr 20 2014 - Fabrizio Paglia (XFABPAG)
#       Fixed variable initialization
# - jan 27 2014 - Fabrizio Paglia (XFABPAG)
#       Re-arranged and generalized
# - ? - Antonio Buonocunto (EANBUON)
#       First draft for APSESH block
##

#Exit codes
EXIT_SUCCESS=0
EXIT_FAILURE=1

#Input parameters
if [ $# -ne 1 ] ; then
	exit $EXIT_FAILURE
fi

SI="$1"

#Constants
TRUE=$(true;echo $?)
FALSE=$(false;echo $?)
LOG_TAG="swu_activate_si"

#Commands
CMD_LOGGER=$( which logger 2>/dev/null )
AMFADM_CMD=$( which amf-adm 2>/dev/null )
if [ $? -ne 0 ]; then
	die "Command amf-adm command which is required to activate the SIs is not found."
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

log "Unlocking $SI"
error_msg=$($AMFADM_CMD unlock $SI 2>&1)
if [ $? -ne 0 ]; then
    die "Failed to unlock $SI. $error_msg" 
fi

exit $EXIT_SUCCESS

