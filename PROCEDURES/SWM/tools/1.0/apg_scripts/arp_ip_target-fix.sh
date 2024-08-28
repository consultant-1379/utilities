#!/bin/bash
##
#-------------------------------------------------------------------------------
#             Copyright (C) 2015 Ericsson AB. All rights reserved.
#-------------------------------------------------------------------------------
##
# Name:
#       arp_ip_target-fix.sh
##
# Description:
#       A script implementing the modifications to arp_ip_target for BSP setup.
##
# Note:
#       This script is intended to be run as procInit action in update campaign.
##
# Changelog:
# - Wed Jun 22 2016 - Yeswanth Vankayala (XYESVAN)
#     updated changes for vAPG
# - Tue Oct 13 2015 - Francesco Rainone (EFRARAI)
#       First version.
##

function log(){
    /bin/logger -t $(basename $0) -- "$*"
}

function abort(){
    log "ABORT: $*"
    cleanup
    exit $FALSE
}

function cleanup(){
    rm $ORIG_CLUSTERCONF &>/dev/null
}

function roll_back_and_abort(){
    if [ -s $ORIG_CLUSTERCONF ]; then
        cp $ORIG_CLUSTERCONF $CLUSTERCONF &>/dev/null || log "failure while copying $ORIG_CLUSTERCONF to $CLUSTERCONF"
        cluster config --reload --all &>/dev/null || log "failure while reloading cluster configuration"
    else
        log "$ORIG_CLUSTERCONF not existing or empty"
    fi
    abort "$*"
}

function isCableless(){
    local OAM_ACCESS=$(< $(</usr/share/pso/storage-paths/config)/apos/apg_oam_access)
    if [ -z "$OAM_ACCESS" ]; then
        log "empty or non-existing apg_oam_access file" >&2
        exit $FALSE
    else
        log "found \"$OAM_ACCESS\" in apg_oam_access"
    fi
    
    if [ "$OAM_ACCESS" == 'NOCABLE' ]; then
        return $TRUE
    fi
    return $FALSE
}

function isvAPG(){
     local HW_TYPE=$(< $(</usr/share/pso/storage-paths/config)/apos/installation_hw)
    if [ "$HW_TYPE" == 'VM' ];then
       return $TRUE
    fi
    return $FALSE
}


function manipulate_cluster_conf(){
    local NODE_B_IP='169\.254\.213\.2'
    local NODE_A_IP='169\.254\.213\.1'
    local LEGACY_ROW_1="^[[:space:]]*bonding[[:space:]]+1[[:space:]]+bond1[[:space:]]+arp_ip_target[[:space:]]+([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)[[:space:]]+${NODE_B_IP}"
    local LEGACY_ROW_2="^[[:space:]]*bonding[[:space:]]+2[[:space:]]+bond1[[:space:]]+arp_ip_target[[:space:]]+([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)[[:space:]]+${NODE_A_IP}"
    local GATEWAY_IP=$(</etc/cluster/nodes/this/routes/0/gateway)
    [ -z "$GATEWAY_IP" ] && abort "no default gateway found"
    local NEW_ROW="bonding control bond1 arp_ip_target ${GATEWAY_IP}"
    for LEGACY_ROW in $LEGACY_ROW_1 $LEGACY_ROW_2; do
        if grep -Pq "$LEGACY_ROW" $CLUSTERCONF; then
            sed -r -i "/$LEGACY_ROW/ d" $CLUSTERCONF \
                || roll_back_and_abort "failure while deleting legacy arp_ip_target entry from cluster.conf"
        else
            roll_back_and_abort "Expected bonding row not found!"
        fi
    done
    sed -r -i "/^#[[:space:]]*arp target/ a ${NEW_ROW}" $CLUSTERCONF \
        || roll_back_and_abort "failure while inserting new arp_ip_target entry in cluster.conf"
}

function old_rows_are_present(){
    COUNT=$(grep -P '^[[:space:]]*bonding[[:space:]]+[12][[:space:]]+bond1[[:space:]]+arp_ip_target[[:space:]]+([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)[[:space:]]+([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)' $CLUSTERCONF | wc -l)
    if [ $COUNT -eq 2 ]; then
        return $TRUE
    fi
    return $FALSE
}

function new_row_is_present(){
    local GATEWAY_IP=$(</etc/cluster/nodes/this/routes/0/gateway)
    [ -z "$GATEWAY_IP" ] && abort "no default gateway found"
    local NEW_ROW="bonding control bond1 arp_ip_target ${GATEWAY_IP}"
    COUNT=$(grep -P "^[[:space:]]*${NEW_ROW}" $CLUSTERCONF | wc -l)
    if [ $COUNT -eq 1 ]; then
        return $TRUE
    fi
    return $FALSE
}

function verify_settings(){
    if ! old_rows_are_present && new_row_is_present; then
        log "new settings successfully verified"
    else
        roll_back_and_abort "failure while verifying settings"
    fi
}

function reload_cluster_conf(){
    cluster config --validate &>/dev/null || roll_back_and_abort "failure while validating new cluster.conf"
    cluster config --reload --all &>/dev/null || roll_back_and_abort "failure while reloading cluster.conf"
}

function apply_configuration(){
    local LOCAL_NODE_ADDRESS=$(</etc/cluster/nodes/this/ip/169.254.213.?/address)
    local PEER_NODE_ADDRESS=$(</etc/cluster/nodes/peer/ip/169.254.213.?/address)
    local PEER_NODE_HOSTNAME=$(</etc/cluster/nodes/peer/hostname)
    if grep -q "$PEER_NODE_ADDRESS" /sys/class/net/bond1/bonding/arp_ip_target; then
        echo -$PEER_NODE_ADDRESS > /sys/class/net/bond1/bonding/arp_ip_target
    else
        log "$PEER_NODE_ADDRESS not present in arp_ip_target. Skipping configuration"
    fi
    if grep -q "$LOCAL_NODE_ADDRESS" <(ssh $PEER_NODE_HOSTNAME cat /sys/class/net/bond1/bonding/arp_ip_target); then
        ssh $PEER_NODE_HOSTNAME "echo -$LOCAL_NODE_ADDRESS > /sys/class/net/bond1/bonding/arp_ip_target"
    else
        log "$LOCAL_NODE_ADDRESS not present in arp_ip_target. Skipping configuration"
    fi
}


#                                              __    __   _______   _   __    _
#                                             |  \  /  | |  ___  | | | |  \  | |
#                                             |   \/   | | |___| | | | |   \ | |
#                                             | |\  /| | |  ___  | | | | |\ \| |
#                                             | | \/ | | | |   | | | | | | \   |
#                                             |_|    |_| |_|   |_| |_| |_|  \__|
#
TRUE=$(true; echo $?)
FALSE=$(false; echo $?)
CLUSTERCONF='/cluster/etc/cluster.conf'
ORIG_CLUSTERCONF=$(mktemp --tmpdir cluster.conf.XXX)

trap "roll_back_and_abort 'signal received. Rolling-back and cleaning up...'" SIGINT SIGTERM SIGHUP

log "entering the script..."

if isCableless; then
    log "Cable-less (NOCABLE) configuration found. Applying arp_ip_target modifications..."
     if isvAPG; then
        log "VM configuration found. Skipping arp_ip_target modifications."
    else
     if old_rows_are_present; then
         cp $CLUSTERCONF $ORIG_CLUSTERCONF || abort "failure while backing-up original cluster.conf."
         manipulate_cluster_conf
         verify_settings
         reload_cluster_conf
         apply_configuration
         log "arp_ip_target modifications done"
         cleanup
     elif new_row_is_present; then
         log "Configuration already present in cluster.conf. Skipping configuration."
     else
         abort "Unexpected cluster.conf configuration found."
      fi
    fi
else
    log "FRONTCABLE configuration found. Skipping arp_ip_target modifications."
fi

log "script successfully completed."
exit $TRUE

