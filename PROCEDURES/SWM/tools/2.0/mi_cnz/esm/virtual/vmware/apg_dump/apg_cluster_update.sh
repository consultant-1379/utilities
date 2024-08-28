#!/bin/bash
##

# Load the apos common functions.
. /opt/ap/apos/conf/apos_common.sh

HW_TYPE=$(/opt/ap/apos/conf/apos_hwtype.sh)

function abort() {
  local rCode=$1
  local MESSAGE="$2"
  echo -e "Aborting ($rCode): $MESSAGE" >&2
  apos_abort $rCode "$MESSAGE"
}

function update_cluster_config() {
  # Set local mac addresses in /cluster/etc/cluster.conf
  add_custom_interfaces_in_cluster_conf cluster || abort 1 "failure while adding addtional custom interfaces in cluster.conf --util repo"
  sleep 3
  echo "after sleep of 3 second --util repo"
  set_local_macs_in_cluster_conf cluster || abort 1 "failure while setting local mac addresses in cluster.conf --util repo"

  # Set ip addresses in /cluster/etc/cluster.conf
  set_ips_in_cluster_conf cluster || abort 1 "failure while setting ip addresses in cluster.conf --util repo"

  # reload of cluster.conf (for mac address handling)
  /usr/bin/cluster config --reload || abort 1 "failure while reloading cluster configuration --util repo"

  return $TRUE
}

echo "in apg_cluster_update.sh --util repo"
case $1 in
  start)
    if [[ "$HW_TYPE" == 'VM' ]]; then
      if is_system_configuration_allowed; then
				if is_deploy_phase; then 
          update_cluster_config
          return_code=$?
          if [ $return_code -ne $TRUE ] ; then
            apos_abort "failure while syncing both nodes MAC addresses --util repo (return code: $return_code)" >&2
          fi
				fi
      fi
    fi
    ;;
  stop|restart|status)
    # At present it does nothing
    apos_log "nothing to do"
  ;;
  *)
    apos_abort "unsupported command $1"
  ;;
esac

apos_log "APG MAC addresses sync completed successfully --util repo"
exit $TRUE
