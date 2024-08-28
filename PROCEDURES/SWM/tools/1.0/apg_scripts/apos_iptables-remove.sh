#!/bin/bash -u
##
# ------------------------------------------------------------------------
#     Copyright (C) 2016 Ericsson AB. All rights reserved.
# ------------------------------------------------------------------------
##
# Name:
#       apos_iptables-remove.sh
# Description:
#       A script to remove the IP tables rules not used anymore.
# Note:
#	None.
##
# Changelog:
# - Fri Jul 11 2016 - Alessio Cascone (ealocae)
#	First version.
##

# Load the apos common functions.
. /opt/ap/apos/conf/apos_common.sh

# Common variables
CLUSTER_CONF_CMD='/opt/ap/apos/bin/clusterconf/clusterconf'
SSH_CMD='/usr/bin/ssh'
RULES_CPS=(
	"all -A INPUT -p tcp --dport 23 -m state --state NEW -m limit --limit 160/second --limit-burst 1 -j ACCEPT"
	"all -A INPUT -p tcp --dport 23 -m state --state NEW -j DROP"
	"all -A INPUT -p tcp --dport 4423 -m state --state NEW -m limit --limit 160/second --limit-burst 1 -j ACCEPT"
	"all -A INPUT -p tcp --dport 4423 -m state --state NEW -j DROP"
	"all -A INPUT -p tcp --dport 5000 -m state --state NEW -m limit --limit 160/second --limit-burst 1 -j ACCEPT"
	"all -A INPUT -p tcp --dport 5000 -m state --state NEW -j DROP"
	"all -A INPUT -p tcp --dport 5001 -m state --state NEW -m limit --limit 160/second --limit-burst 1 -j ACCEPT"
	"all -A INPUT -p tcp --dport 5001 -m state --state NEW -j DROP"
	"all -A INPUT -p tcp --dport 5002 -m state --state NEW -m limit --limit 160/second --limit-burst 1 -j ACCEPT"
	"all -A INPUT -p tcp --dport 5002 -m state --state NEW -j DROP"
	"all -A INPUT -p tcp --dport 5010 -m state --state NEW -m limit --limit 160/second --limit-burst 1 -j ACCEPT"
	"all -A INPUT -p tcp --dport 5010 -m state --state NEW -j DROP"
	"all -A INPUT -p tcp --dport 5011 -m state --state NEW -m limit --limit 160/second --limit-burst 1 -j ACCEPT"
	"all -A INPUT -p tcp --dport 5011 -m state --state NEW -j DROP"
	"all -A INPUT -p tcp --dport 5100 -m state --state NEW -m limit --limit 160/second --limit-burst 1 -j ACCEPT"
	"all -A INPUT -p tcp --dport 5100 -m state --state NEW -j DROP"
	"all -A INPUT -p tcp --dport 5101 -m state --state NEW -m limit --limit 160/second --limit-burst 1 -j ACCEPT"
	"all -A INPUT -p tcp --dport 5101 -m state --state NEW -j DROP"
	"all -A INPUT -p tcp --dport 5110 -m state --state NEW -m limit --limit 160/second --limit-burst 1 -j ACCEPT"
	"all -A INPUT -p tcp --dport 5110 -m state --state NEW -j DROP"
	"all -A INPUT -p tcp --dport 5111 -m state --state NEW -m limit --limit 160/second --limit-burst 1 -j ACCEPT"
	"all -A INPUT -p tcp --dport 5111 -m state --state NEW -j DROP"
	)


# Main
apos_intro $0

SOMETHING_CHANGED=$FALSE
for RULE in "${RULES_CPS[@]}"; do
  RULE_ID=$(${CLUSTER_CONF_CMD} iptables --display | grep "$RULE" | awk -F ' ' '{print $1}')
  if [ -n "$RULE_ID" ]; then
    ${CLUSTER_CONF_CMD} iptables --m_delete $RULE_ID
    if [ $? -ne 0 ]; then
      apos_log "WARNING: Failed to delete the following rule: \"$RULE\""
    else
      SOMETHING_CHANGED=$TRUE
    fi
  else
    apos_log "WARNING: Rule not found: \"$RULE\""
  fi
done
	
# Reload cluster configuration to apply removal
if [ $SOMETHING_CHANGED -eq $TRUE ]; then
  cluster config -r -a || apos_abort "Failed to reload cluster configuration."
  # iptables restart (on both nodes) to make the new rules effective
  ${SSH_CMD} SC-2-1 /opt/ap/apos/bin/servicemgmt/servicemgmt restart lde-iptables.service &>/dev/null || apos_abort "failure while reloading iptables rules on SC-2-1"
  ${SSH_CMD} SC-2-2 /opt/ap/apos/bin/servicemgmt/servicemgmt restart lde-iptables.service &>/dev/null || apos_abort "failure while reloading iptables rules on SC-2-2"
fi

apos_outro $0
exit $TRUE

# End of file
