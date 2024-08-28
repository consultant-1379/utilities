#!/bin/bash
##
# ------------------------------------------------------------------------
#     Copyright (C) 2015 Ericsson AB. All rights reserved.
# ------------------------------------------------------------------------
##
# Name:
#       update_iptables.sh
# Description:
#       A script to remove iptable rules on 830 port
# Note:
# None.
##
# Changelog:
# - Thu Sep 03 2015 - Pratap Reddy Uppada(XPRAUPP)
# First version.
##

# Load the apos common functions.
. /opt/ap/apos/conf/apos_common.sh

CFG_PATH="/opt/ap/apos/conf"
CLU_PATH="/opt/ap/apos/bin/clusterconf"
CLU_CMD="clusterconf"

# To reload cluster.conf after changes applied
cluster_conf_reload() {
  local lcc_name="/usr/bin/cluster"
  $lcc_name config -v &>/dev/null
  local status=$?

  if [ $status -ne $TRUE ]; then
    echo -e "\nSyntax error in the new iptables configuration"
  else
    $lcc_name config -r 
  fi

  return $status
}

# To check reliable ethernet feature is enabled on node
# return TRUE, if it is enabled
function is_rif_defined(){
  local stateToReturn=$FALSE
  local APOS_RE_CONF="/cluster/storage/system/config/apos/apos_rif.conf"

  if [ -e $APOS_RE_CONF ]; then
    rifStateA=$(cat $APOS_RE_CONF | grep RIFSTATE1 | awk ' BEGIN { FS = "=" } ; { print $2}'| awk ' BEGIN { FS = ";" } ; { print $1}')
    rifStateB=$(sed -n "$2p" $APOS_RE_CONF | grep RIFSTATE2 | awk ' BEGIN { FS = "=" } ; { print $2}'| awk ' BEGIN { FS = ";" } ; { print $1}')
    if [ $rifStateA -eq 1 ] && [ $rifStateB -eq 1 ] ; then
      stateToReturn=$TRUE
    fi
  else
    apos_log "reliable network interface not defined"
    stateToReturn=$FALSE
  fi
  return $stateToReturn
}

function fetch_rules() {
  # For NOCABLE, interface is bond1.<oam_vlanid>
  # For FRONTCABLE, interface is eth1
  # interface eth2 is common for all configurations
  rules=''
  local INTERFACE1=''
  local INTERFACE2='eth2'
  local OAM_ACCESS="$(get_oam_param)"
  if [ $OAM_ACCESS == "NOCABLE" ]; then
    INTERFACE1="bond1+"
  elif [ $OAM_ACCESS == "FRONTCABLE" ]; then
    INTERFACE1="eth1"
  else
     is_rif_defined && INTERFACE1="bond1"
  fi

  # update rules with interfaces
  # rule syntax like below:
  # iptables all -A INPUT -p tcp --dport 830 -i <interface> -j DROP>
  rules=(
"iptables all -A INPUT -p tcp --dport 830 -i $INTERFACE1 -j DROP"
"iptables all -A INPUT -p udp --dport 830 -i $INTERFACE1 -j DROP"
"iptables all -A INPUT -p tcp --dport 830 -i $INTERFACE2 -j DROP"
"iptables all -A INPUT -p udp --dport 830 -i $INTERFACE2 -j DROP"
)

}

function delete_rule() {
  # fetch the list of rules to remove
  fetch_rules

  # Here removal of rules will start.
  pushd ${CLU_PATH} > /dev/null 2>&1
  for rule in "${rules[@]}"; do
    rule_id=$(./${CLU_CMD} iptables --display | grep "${rule}" |awk -F" " '{print $1}')
    [ -z $rule_id ] && break
    ./${CLU_CMD} iptables --m_delete $rule_id
    [ $? -ne $TRUE ] && apos_abort "Deletion of iptable rule is failed"
  done
  popd > /dev/null 2>&1
  cluster_conf_reload
  [ $? -ne $TRUE ] && apos_abort "the iptables configuration went wrong!"
}

## M A I N

# Removing iptable rules on 830 port, in order to
# allow netconf session
if $CLU_PATH/$CLU_CMD iptables --display | grep -qw "830" ; then
  # Delete the rules from cluster.conf
  delete_rule

# iptables restart to make the new rules effective
sleep 7
systemctl restart lde-iptables.service || apos_abort "failure while reloading iptables rules"
sleep 3

fi
# E N D
