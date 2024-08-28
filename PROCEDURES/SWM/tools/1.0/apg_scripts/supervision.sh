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
# 2014-07-11 xmadmut updated to fetch cmw status
# 2014-10-27 xaarsha update to increase the count for maximum retry to fetch the cmw status 
# 2014-11-06 xaarsha updated to increase the timeout for SI swap
##

#Loading Environment variables"

# Global Variables ------------------------------------------------------- BEGIN
TRUE=$( true; echo $? )
FALSE=$( false; echo $? )

CMD_LOGGER=''
CMD_AMFADM=''
CMD_CMWSTATUS=''
CLASS_NAME="comp su si csiass siass sg app node"

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

# The function will log an error message in the system log.
function log_info(){
    local MESSAGE=$1
    local RET_CODE=$2
    log_error "INFO: $MESSAGE - return code: $RET_CODE"
}

# The function will check for the script's prerequisites to be satisfied.
function sanity_check(){

	CMD_AMFADM=$( which amf-adm 2>/dev/null )
	if [ $? -ne 0 ]
    then
        abort "Command amf-adm missing." "The command amf-adm required to provide the swap of SI AGENT not found" 2
    fi
    
	CMD_CMWSTATUS=$( which cmw-status 2>/dev/null )
    if [ $? -ne 0 ]
    then
        abort "Command cmw-status missing." "The command cmw-status required to check the system status to swap SI AGENT" 2
    fi

    CMD_LOGGER=$( which logger 2>/dev/null )
	[ -z "$CMD_LOGGER" ] && CMD_LOGGER='/bin/logger'	
    
}

# The function will check the system status. cmw-status of all the classes.
function check_cmw_status(){

    local TIMEOUT=25
    local COUNT=0
    local ERROR_MSG=''
    local RETURN_CODE=''
	local IS_TIMEOUT=0

    ERROR_MSG=$($CMD_CMWSTATUS $CLASS_NAME 2>&1)
    RETURN_CODE=$?
    if [ $RETURN_CODE -ne 0 ]; then
		log_info "CMW status NOT OK retrying the cmw-status. Cause:$ERROR_MSG" $RETURN_CODE
            while ((COUNT < TIMEOUT))
            do
				sleep 4
				ERROR_MSG=$($CMD_CMWSTATUS $CLASS_NAME 2>&1)
				RETURN_CODE=$?
				if [ $RETURN_CODE -eq 0 ]; then
					break;
				else
					((COUNT ++))
				fi
			done

			if test $COUNT -ge $TIMEOUT; then
				IS_TIMEOUT=1
				log_info "TIME-OUT: CMW status NOT OK. Cause:$ERROR_MSG" $RETURN_CODE
			fi
		fi
		
	if [ $IS_TIMEOUT -eq 0 ]; then
        log_info "CMW status SUCCESS. $ERROR_MSG" $RETURN_CODE
	fi
}


# MAIN ------------------------------------------------------------------- BEGIN

sanity_check

check_cmw_status

#Perform si-swap of safSi=AGENT
ERROR_MSG=$($CMD_AMFADM -t 301 si-swap $SI_AGENT 2>&1)
RETURN_CODE=$?
if [ $RETURN_CODE -ne 0 ]
then
    abort "Supervision script failed. si-swap of  $SI_AGENT failed. $ERROR_MSG" $RETURN_CODE
fi

# MAIN --------------------------------------------------------------------- END
exit $TRUE




