#!/bin/bash -x
##
# ------------------------------------------------------------------------
#     Copyright (C) 2016 Ericsson AB. All rights reserved.
# ------------------------------------------------------------------------
##
# Name:
#       apg_update_cluster_conf_with_SLES12_option.sh
# Description:
#     A script to update the cluster.conf with new options available only 
#     in SLES12 baseline
#
# Note:
#      -
##
# Output:
#       None.
##
# Changelog:
#
# - Sat May 14 2016 - Fabio Ronca (efabron)
#       First version.
##

# Load the apos common functions.
. /opt/ap/apos/conf/apos_common.sh

RELOAD_CLUSTER='false'

# Check if the option nfs-manage-gids is already present
/usr/bin/grep -q 'nfs-manage-gids' /cluster/etc/cluster.conf
if [ $? -ne 0 ]; then
  sed -i '/ssh.rootlogin control off/a\\n# Enable GIDs lookup locally on the NFS server\nnfs-manage-gids on' /cluster/etc/cluster.conf
  RELOAD_CLUSTER='true'
  if [ $? -eq 0 ]; then
        #Validate cluster.conf
        apos_log "Validate cluster.conf"
        cluster config -v -V
        [ $? -ne 0 ] && apos_abort "ERROR: cluster.conf validation failed after update with option nfs-manage-gids"
        apos_log "nfs-manage-gids added to the cluster.conf!"
  else
    apos_abort "Failure while adding nfs-manage-gids option in cluster.conf"
  fi
else
  apos_log "Option nfs-manage-gids already present in cluster.conf"
fi


# Check if the option rpm-post-errors is already present
/usr/bin/grep -q 'rpm-post-errors' /cluster/etc/cluster.conf
if [ $? -ne 0 ]; then
  sed -i '/ssh.rootlogin control off/a\\n# Catch of RPM post installation failure enabled\nrpm-post-errors on' /cluster/etc/cluster.conf
  RELOAD_CLUSTER='true'
  if [ $? -eq 0 ]; then
        #Validate cluster.conf
        apos_log "Validate cluster.conf"
        cluster config -v -V
        [ $? -ne 0 ] && apos_abort "ERROR: cluster.conf validation failed after update with option rpm-post-errors"
        apos_log "rpm-post-errors added to the cluster.conf!"
  else
    apos_abort "Failure while adding rpm-post-errors option in cluster.conf"
  fi
else
  apos_log "Option rpm-post-errors already present in cluster.conf"
fi

#Reload cluster.conf
if [ $RELOAD_CLUSTER == "true" ]; then 
  cluster config -V -r --all
  apos_log "Cluster.conf successfully reloaded!!!"
  [ $? -ne 0 ] && apos_abort "ERROR: cluster.conf reload failed!!!"
else
  apos_log "Cluster.conf already updated, reload of cluster.conf not needed!!!"	
fi 



apos_outro $0
exit $TRUE