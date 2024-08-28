#!/bin/bash
##
# ------------------------------------------------------------------------
#     Copyright (C) 2017 Ericsson AB. All rights reserved.
# ------------------------------------------------------------------------
##
# Name:
#       cs_iptables.sh
# Description:
#       This script is to delete iptables rules on passive node during upgrade.
# Note:
#       None.
##
# Usage:
#       None.
##
# Output:
#       None.
##
# Changelog:
# - Wed Sep 13 2017 - Harika B (xharbav)
#       First Version
. /opt/ap/apos/conf/apos_common.sh

COMPUTERESOURCE_CLASS="AxeEquipmentComputeResource"
IMM_FIND="/usr/bin/immfind"
IMM_LIST="/usr/bin/immlist"
AWK="/usr/bin/awk"
GREP="/usr/bin/grep"
SYSTEMCTL="/usr/bin/systemctl"
IPADDRESSETHA="ipAddressEthA"
IPADDRESSETHB="ipAddressEthB"
AXE_FUNCTIONS="axeFunctionsId=1"
SHELF_ARCHITECTURE_ATTR="apgShelfArchitecture"
VIRTUALIZED=3
CLUSTER_CONFIG="cluster config "
DELETERULESCOUNT=0
SSH="/usr/bin/ssh"

LOG_TAG="cs_iptables"
LOGGER="/bin/logger"

# exit-code error flags
exit_sucs=0



#----------------------------------------------------------------------------------------
# log to system-log
function log(){
    $LOGGER -t "$LOG_TAG" "$*"
}

#----------------------------------------------------------------------------------------


function deleteRule() {
    local ipAddressToFetch=$1
    ipAddress=$($IMM_LIST -a $ipAddressToFetch $computeResourceDN | $AWK 'BEGIN { FS = "=" } ; {print $2}')
    ruleNumberPrefix=$(iptables -L --line-number | $GREP $ipAddress | $AWK '{print $1}')
    if [ "$ruleNumberPrefix" != "" ]; then
        iptables -D INPUT $ruleNumberPrefix
    fi
}
# _____________________ _____________________
#|    _ _   _  .  _    |    _ _   _  .  _    |
#|   | ) ) (_| | | )   |   | ) ) (_| | | )   |
#|_____________________|_____________________|
# Here begins the "main" function...

# Set the interpreter to exit if a non-initialized variable is used.
set -u

log "START: <$0>"

#Get Node 1 Status
NODE_1_STATE=$(amf-state siass ha safSISU=safSu=1\\,safSg=2N\\,safApp=ERIC-APG,safSi=AGENT,safApp=ERIC-APG | grep saAmfSISUHAState | $AWK -F'=' '{print $2}'| $AWK -F'(' '{print $1}')
#Get Node 2 Status
NODE_2_STATE=$(amf-state siass ha safSISU=safSu=2\\,safSg=2N\\,safApp=ERIC-APG,safSi=AGENT,safApp=ERIC-APG | grep saAmfSISUHAState | $AWK -F'=' '{print $2}'| $AWK -F'(' '{print $1}')

NODE=""

if [ "$NODE_1_STATE" = "ACTIVE" ];then
    ACTIVE_NODE="SC-2-1"
	log "START: SC-2-1"
elif [ "$NODE_1_STATE" = "STANDBY" ]; then
    ACTIVE_NODE="SC-2-2"
	log "START: SC-2-2"
else
	log "APG STATUS NOT VALID"
    apos_abort "APG STATUS NOT VALID"
fi

THIS_NODE=$(cat /etc/cluster/nodes/this/hostname)
PEER_NODE=$(cat /etc/cluster/nodes/peer/hostname)
if [ "$THIS_NODE" == "$ACTIVE_NODE" ]; then
#Removing iptable rule entries from clusterconf file if rules are present
	log "Removing iptable rule entries from clusterconf file if rules are present"
	shelf_architecture=$($IMM_LIST -a $SHELF_ARCHITECTURE_ATTR $AXE_FUNCTIONS | $AWK 'BEGIN { FS = "=" } ; {print $2}')
	 [ -z $shelf_architecture ] && apos_abort "Cannot read APG Shelf Architecture"

	if [ $shelf_architecture != $VIRTUALIZED ]; then
		#Fetching IP Addresses form hwcls
		log "Fetching IP Addresses form hwcls"
		while read -r line;
		do     id=$(echo $line | $AWK '{print $5}');
			if [ "$id" == "MAUB" ] || [ "$id" == "APUB" ] || [ "$id" == "CPUB" ]
			then
				ipa=$(echo $line | $AWK '{print $6}');
				log "Finding rules from iptables"
				findRule=$(/opt/ap/apos/bin/clusterconf/clusterconf iptables -D | grep $ipa | $AWK '{$1=""}1'  | $AWK '{$1=$1}1');
				if [ "$findRule" != "" ]; then
					log "Delete rules from /clusterconf"
					sed -i "\#\b$findRule\b#d" /cluster/etc/cluster.conf
					DELETERULESCOUNT=$DELETERULESCOUNT+1
				fi
			fi
		done < <(hwcls)
		if [ $DELETERULESCOUNT != 0 ]
		then
			echo "Reloading cluster conf"
			log "Reloading cluster conf"
			$CLUSTER_CONFIG -v
			$CLUSTER_CONFIG -r -a
			$SYSTEMCTL restart lde-iptables.service
			#$SYSTEMCTL -H $PEER_NODE restart lde-iptables.service
                        $SSH $PEER_NODE $SYSTEMCTL restart lde-iptables.service
		fi
	fi
else
#Removing iptables rules from paasive node after immediate upgrade	
	log "Removing iptables rules from paasive node after immediate upgrade"
    for computeResourceDN in $($IMM_FIND -c $COMPUTERESOURCE_CLASS );
    do        
		log "DeleteRules"
        deleteRule $IPADDRESSETHA
        deleteRule $IPADDRESSETHB
    done	
fi
log "END: <$0>"
exit $exit_sucs

