#!/bin/bash
##
# ------------------------------------------------------------------------
#     Copyright (C) 2012 Ericsson AB. All rights reserved.
# ------------------------------------------------------------------------
##
# Name:
#       supervision.sh
# Description:
#       <script_functionality_description>
# Note:
#       <script_notes>
##
# Usage:
#       ./supervision.sh 
##
# Output:
#       <script_output_description>
##
# Changelog:
#
# 2012-07-12 efabron First Release
##

#Loading Environment variables"

# Global Variables ------------------------------------------------------- BEGIN
TRUE=$( true; echo $? )
FALSE=$( false; echo $? )

CMD_LOGGER=''
CMD_AMFADM=''
SWAP_TMOUT="201"
SI_AGENT="safSi=AGENT,safApp=ERIC-APG"

LOG_TAG='-t ecimswm'

# Global Variables --------------------------------------------------------- END

# The function will log and print an error message and will terminate the script
#  with a $FALSE return code.
function abort(){
    local MESSAGE=$1
    local ERROR_CODE=$2
    log_error "$MESSAGE - error code: $ERROR_CODE"		
    exit $FALSE
}

# The function will log an error message in the system log. 
function log_error(){
  
    local PRIO='-p user.notice'
	local MESSAGE="${*:-notice}"	
    
    $CMD_LOGGER $PRIO $LOG_TAG $MESSAGE &>/dev/null
    
}

# The function will check for the script's prerequisites to be satisfied.
function sanity_check(){

	CMD_AMFADM=$( which amf-adm 2>/dev/null )
	if [ $? -ne 0 ]
    then
        abort "Command amf-adm missing." "The command amf-adm required to provide the swap of SI AGENT not found" 2
    fi
    
    CMD_LOGGER=$( which logger 2>/dev/null )
	[ -z "$CMD_LOGGER" ] && CMD_LOGGER='/bin/logger'	
    
}


# MAIN ------------------------------------------------------------------- BEGIN

sanity_check

#Perform si-swap of safSi=AGENT
ERROR_MSG=$($CMD_AMFADM -t $SWAP_TMOUT si-swap $SI_AGENT 2>&1)
RETURN_CODE=$?
if [ $RETURN_CODE -ne 0 ]
then
    abort "Supervision script failed. si-swap of  $SI_AGENT failed. $ERROR_MSG" $RETURN_CODE
fi

# MAIN --------------------------------------------------------------------- END
exit $TRUE
