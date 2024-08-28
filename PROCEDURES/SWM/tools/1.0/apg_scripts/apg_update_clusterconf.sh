#!/bin/bash
##
# ------------------------------------------------------------------------
#     Copyright (C) 2016 Ericsson AB. All rights reserved.
# ------------------------------------------------------------------------
##
# Name:
#       apg_update_clusterconf.sh
# Description:
#       A script to modify /cluster/etc/cluster.conf file.
#       Changes:
#         - add and configure bond0:4 interface
#         - enable default-output on serial
# Note:
#       None.
##
# Output:
#       None.
##
# Changelog:
# 
# - Tue Mar 29 2016 - Franco D'Ambrosio (efradam)
#       First version.
##

# Load the apos common functions.
. /opt/ap/apos/conf/apos_common.sh

# Variables
CLUSTER_FILE='/cluster/etc/cluster.conf'


# The function will check for the script's prerequisites to be satisfied.
function sanity_check(){
 
    CMD_SED=$( which sed 2>/dev/null )
	[ -z "$CMD_SED" ] && CMD_SED='/usr/bin/sed'
	
	CMD_GREP=$( which grep 2>/dev/null )
	[ -z "$CMD_GREP" ] && CMD_GREP='/usr/bin/grep'
	
	CMD_CAT=$( which cat 2>/dev/null )
	[ -z "$CMD_CAT" ] && CMD_CAT='/usr/bin/cat'

}

function isAP2(){
  local AP_TYPE=$(apos_get_ap_type)
  [ "$AP_TYPE" == "AP2" ] && return $TRUE
  return $FALSE
}


function configure_bond() {
  # This function is used to configure bond0:4 interface
  apos_log "Configuring bond0:4 interface ..."

  # Check if bond0:4 has already been configured
  $CMD_GREP -q bond0:4 $CLUSTER_FILE
  if [ $? -ne 0 ]; then
    $CMD_SED -i '/interface control bond0:3 alias/a\interface control bond0:4 alias' $CLUSTER_FILE
    [ $? -ne 0 ] && apos_abort "ERROR: Failure while defining interface bond0:4"
    
	if isAP2; then
	  apos_log "AP2 configuration: add mip control la-ldap bond0:4 internal 169.254.208.122"
	  $CMD_SED -i '/mip control boot_b bond0:3 internal 169.254.208.104/a\mip control la-ldap bond0:4 internal 169.254.208.122' $CLUSTER_FILE
	else
	  apos_log "AP1 configuration: add mip control la-ldap bond0:4 internal 169.254.208.121"
	  $CMD_SED -i '/mip control boot_b bond0:3 internal 169.254.208.102/a\mip control la-ldap bond0:4 internal 169.254.208.121' $CLUSTER_FILE
	fi
    
    if [ $? -eq 0 ]; then
      #Validate cluster.conf
	  apos_log "Validate cluster.conf"
	  cluster config -v -V
	  [ $? -ne 0 ] && apos_abort "ERROR: cluster.conf validation failed"
    else
      apos_abort "Failure while configuring bond0:4 interface" 
    fi
    apos_log "Interface bond0:4 configured!"	
  else
    apos_log "Interface bond0:4 already defined"
  fi
}

function modify_default-output() {
  # This function is used to modify default output

  apos_log "Modifying default output console ..."
  
  # Check if default output has already been modified
  $CMD_GREP -q \#default-output $CLUSTER_FILE
  if [ $? -eq 0 ]; then
    $CMD_SED -i 's/#default-output/default-output/g' $CLUSTER_FILE
    if [ $? -eq 0 ]; then
	  #Validate cluster.conf
	  apos_log "Validate cluster.conf"
	  cluster config -v -V
	  [ $? -ne 0 ] && apos_abort "ERROR: cluster.conf validation failed"
	  apos_log "Default output modified!"	
    else
      apos_abort "Failure while modifying default-output option" 
    fi   
  else
    apos_log "Default output already modified"
  fi
}


function modify_watchdog_timeout() {
  # This function is used to modify the watchdog time-out

  apos_log "Modifying watchdog time-out in cluster.conf ..."
  
  # Check if default output has already been modified
  $CMD_GREP -q "shutdown-timeout all 120" $CLUSTER_FILE
  if [ $? -eq 0 ]; then
    $CMD_SED -i 's/shutdown-timeout all 120/shutdown-timeout all 180/g' $CLUSTER_FILE
    if [ $? -eq 0 ]; then
	  #Validate cluster.conf
	  apos_log "Validate cluster.conf"
	  cluster config -v -V
	  [ $? -ne 0 ] && apos_abort "ERROR: cluster.conf validation failed"
	  apos_log "Watchdog time-out modified!"	
    else
      apos_abort "Failure while modifying default-output option" 
    fi   
  else
    apos_log "Watchdog time-out already set to 180 sec."
  fi
}


#                                              __    __   _______   _   __    _
#                                             |  \  /  | |  ___  | | | |  \  | |
#                                             |   \/   | | |___| | | | |   \ | |
#                                             | |\  /| | |  ___  | | | | |\ \| |
#                                             | | \/ | | | |   | | | | | | \   |
#                                             |_|    |_| |_|   |_| |_| |_|  \__|
#

apos_intro $0

sanity_check
configure_bond
modify_default-output
modify_watchdog_timeout
#Reload cluster.conf
cluster config -r -V --all
[ $? -ne 0 ] && apos_abort "ERROR: cluster.conf reload failed"

apos_outro $0
exit $TRUE
