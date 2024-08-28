#!/bin/bash
#ght (C) 2017 Ericsson AB. All rights reserved.
# ------------------------------------------------------------------------
##
# Name:
#      apos_update_clusterconf.sh
# Description:
#       A script to update cluster conf file to fix TR HW57634
# Note:
#       None.
##
# Changelog:
# - Tue 04 Apr 2018 - Sindhura Chintakindi (zchisin)
#     First version.
##

. /opt/ap/apos/conf/apos_common.sh

cluster_file='/cluster/etc/cluster.conf'


function add_clusterconf() {
if is_vAPG ; then
  if grep -q "quick-reboot all off" "$cluster_file"; then
    apos_log 'Already quick-reboot all off is present in /cluster.conf file'
  else
    sed -i '/node 2 control SC-2-2/a\quick-reboot all off\' $cluster_file
    cluster config -v &>/dev/null || apos_abort "cluster.conf validation has failed!"
    kill_after_try 3 30 30 "cluster config --reload &>/dev/null" 2>/dev/null || apos_abort 1 'ERROR: Failed to reload cluster configuration'
  fi
fi
}


##main##

add_clusterconf

