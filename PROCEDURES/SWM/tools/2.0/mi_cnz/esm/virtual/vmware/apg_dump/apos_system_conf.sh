#!/bin/bash
##
# ------------------------------------------------------------------------
#     Copyright (C) 2016 Ericsson AB. All rights reserved.
# ------------------------------------------------------------------------
##
# Name:
#       apos_system_conf.sh
#
# Description:
#       A script to apply APG configuration during deploy time in cloud
#
##
# Usage:
#       ./apos_system_conf.sh [early|late]
##
# Changelog:
# - Wed Feb 05 2020 - Pratap Reddy (xpraupp)
#   IPv6 impacts for virtual
# - Fri May 05 2017 - Usha Manne (XUSHMAN)
#   Handling of additional custom networks during early stage of deploy phase.
# - Mon Dec 12 2016 - Francesco Rainone (EFRARAI)
#   Local MAC address handling for the non-static MAC case.
# - Mon Nov 14 2016 - Franco D'Ambrosio (EFRADAM)
#   Modified the methods to fetch deployment parameters
# - Fri Jan 22 2016 - Pratap Reddy (xpraupp)
#   First version.
##

# Load the apos common functions.
. /opt/ap/apos/conf/apos_common.sh

#-------------------------------------------------------------------------------
function create_structure(){
  # Here cluster config creates the folders with new
  # IP address that are added in /boot/.cluster.conf
  
  # Fetch the user data related information
  local network_ip_addresses=$($CMD_GETINFO properties | grep -E 'ip_address|ipv')

  # Read the parameters to configured
  for parm in $network_ip_addresses; do
    eval $parm 2>/dev/null
  done

  apos_log "INFO: apos_systemconf --> Begin --util repo"
  IP_LIST=$(ls -1 /etc/cluster/nodes/this/ip)
  if [ -n "$node1_public_network_ipv4_ip_address" ]; then
    THIS_IP="$node1_public_network_ipv4_ip_address"
    [ "$(get_node_id)" -eq 2 ] && THIS_IP="$node2_public_network_ipv4_ip_address"
  elif [ -n "$node1_public_network_ipv6_ip_address" ]; then
    THIS_IP="$node1_public_network_ipv6_ip_address"
    [ "$(get_node_id)" -eq 2 ] && THIS_IP="$node2_public_network_ipv6_ip_address"
  fi
  apos_log "INFO: apos_systemconf --> THIS_IP=$THIS_IP"
  if [ -n "$THIS_IP" ]; then
    if ! echo "$IP_LIST" | grep -q "$THIS_IP"; then
      if ! /usr/bin/cluster config --create; then
        apos_abort 1 "Failed to create configuration structure --util repo"
      fi
    fi
  fi
  apos_log "INFO: apos_systemconf --> End"
}

#-------------------------------------------------------------------------------
function configure_local_macs() {
  echo 'current nic/mac setup --util repo'
  show_current_nic_setup
  set_local_macs_in_cluster_conf local
  echo 'local macs correctly setup --util repo'
}

#-------------------------------------------------------------------------------
function configure_local_nics() {
  echo 'configure nics in cluster.conf --util repo'
  add_custom_interfaces_in_cluster_conf local
  echo 'local nics correctly setup --util repo'
}


#                                              __    __   _______   _   __    _
#                                             |  \  /  | |  ___  | | | |  \  | |
#                                             |   \/   | | |___| | | | |   \ | |
#                                             | |\  /| | |  ___  | | | | |\ \| |
#                                             | | \/ | | | |   | | | | | | \   |
#                                             |_|    |_| |_|   |_| |_| |_|  \__|
#

case $1 in
  early)
    if is_system_configuration_allowed; then
      if is_deploy_phase && ! is_SIMULATED; then
        configure_local_nics
        configure_local_macs
      fi
    fi
  ;;
  late)  
    if is_system_configuration_allowed; then
      if is_dnr_phase; then
        echo "DNR PHASE"
      elif is_snr_phase; then
        echo "SNR PHASE"
      elif is_deploy_phase; then
        #commenting this line as with ovf-env.xml this part will be handled by LDE
        #set_ips_in_cluster_conf local
        create_structure
      fi
    fi
  ;;
  *)
    echo "unsupported option specified: $1" >&2
    exit $FALSE
  ;;
esac
exit $TRUE
