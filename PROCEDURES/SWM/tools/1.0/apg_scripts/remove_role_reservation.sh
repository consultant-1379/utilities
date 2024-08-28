#!/bin/bash
##
# ------------------------------------------------------------------------
#     Copyright (C) 2013 Ericsson AB. All rights reserved.
# ------------------------------------------------------------------------
##
# Name:
#       remove_role_reservation.sh
# Description:
#		Remove CpRole reservation from Node_Role_Export file
# Note:
#	None.
##
# Output:
#       None.
##
# Changelog:
# - 2015 10 05 - eanform
#	First version.
##

#setting  global variables
##############################
ROLE_EXPORT_PATH="/data/opt/ap/internal_root/support_data/"
AXEROLES="Node_Role_Export.txt"
TRUE=$( true; echo $? )
FALSE=$( false; echo $? )
NODE_1="SC-2-1"
NODE_2="SC-2-2"
CMD_LOGGER=''

# The function will log and print an error message and will terminate the script
#  with a $FALSE return code.
function abort(){
    local MESSAGE=$1
    log_msg "ERROR: $MESSAGE"		
    exit $FALSE
}

# The function will log an  message in the system log. 
function log_msg(){
  
    local PRIO='-p user.notice'
	local MESSAGE="${*:-notice}"	
    
    $CMD_LOGGER $PRIO $MESSAGE &>/dev/null 
}

# The function will check for the script's prerequisites to be satisfied.
function sanity_check(){
 
    CMD_LOGGER=$( which logger 2>/dev/null )
	[ -z "$CMD_LOGGER" ] && CMD_LOGGER='/bin/logger'

}

function change_axe_roles() {
	
	log_msg "Updating $SUPPRT_DATA/$AXEROLES:"
	echo 'ROLE SystemAdministrator,SystemSecurityAdministrator,SystemReadOnly,EricssonSupport,CpRole0,CpRole1,CpRole2,CpRole3,CpRole4,CpRole5,CpRole6,CpRole7,CpRole8,CpRole9,CpRole10,CpRole11,CpRole12,CpRole13,CpRole14,CpRole15' > $ROLE_EXPORT_PATH/$AXEROLES

	chmod 444 $ROLE_EXPORT_PATH/$AXEROLES
}


# MAIN ------------------------------------------------------------------- BEGIN

log_msg "remove_role_reservation.sh start..."

sanity_check

#Get Node 1 Status
NODE_1_STATE=$(amf-state siass ha safSISU=safSu=1\\,safSg=2N\\,safApp=ERIC-APG,safSi=AGENT,safApp=ERIC-APG | grep saAmfSISUHAState | awk -F'=' '{print $2}'| awk -F'(' '{print $1}')
#Get Node 2 Status
NODE_2_STATE=$(amf-state siass ha safSISU=safSu=2\\,safSg=2N\\,safApp=ERIC-APG,safSi=AGENT,safApp=ERIC-APG | grep saAmfSISUHAState | awk -F'=' '{print $2}'| awk -F'(' '{print $1}')

#Get curent node name
CURRENT_NODE="$(cat /etc/cluster/nodes/this/name)"

if ([[ "$NODE_1" = "$CURRENT_NODE" && "$NODE_1_STATE" = "ACTIVE" ]] ||
	[[ "$NODE_2" = "$CURRENT_NODE" && "$NODE_2_STATE" = "ACTIVE" ]]);then
	log_msg "Add CpRole11..15 to the AXE Roles file"
	change_axe_roles
else 
	log_msg "Skip execution on STANDBY node !!!"
fi

log_msg "remove_role_reservation.sh end!!!"

# MAIN --------------------------------------------------------------------- END
exit $TRUE
