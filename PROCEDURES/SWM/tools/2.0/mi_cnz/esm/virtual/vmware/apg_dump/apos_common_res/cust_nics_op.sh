#!/bin/bash
##
# ------------------------------------------------------------------------
#     Copyright (C) 2012 Ericsson AB. All rights reserved.
# ------------------------------------------------------------------------
##
# Name:
#       cust_nics_op.sh
# Description:
#       A common library providing addtional custom nic handling for APOS routines.
# Note:
#	This file is intended to be sourced by the apos_common.sh routines so it
#	MUST be compliant with the bash syntax and his name must end with ".sh"
##
# Usage:
#	None.
##
# Output:
#       None.
##
# Changelog:
# - Fri May 05 2017 - Malangsha Shaik (xmalsha)
# First version.
##

# checks if the passed parameter is in the form eth[0-9][0-9]
function is_nic() {
  local nic="${1}"
  [[ "$nic" =~  ^eth[0-9]{1,2}$ ]] && return $TRUE
  return $FALSE
}

function is_nic_present(){
  local nic=$1
  local cluster_file=$2
  local node_id=$3

  ! is_nic "$nic" && return $FALSE
  if ! grep -Eq "^[[:space:]]*interface[[:space:]]+${node_id}[[:space:]]+${nic}[[:space:]]+" $cluster_file 2>/dev/null; then
    return $FALSE
  fi

  return $TRUE
}

# Usage: add_custom_interfaces_in_cluster_conf <local/cluster>
##
# The function fetches the local nic information from "getinfo netinfo" and
# add the cluster.conf "interface" entries with the new nic information found.
# A parameter (local/cluster) specifies which cluster.conf file shall be updated
# (either the local one - under /boot - or the cluster one - under /cluster).
function add_custom_interfaces_in_cluster_conf(){

  # nested lock function to ensure mutual exclusion in the case of editing
  # clustered resource (e.g. /cluster/etc/cluster.conf)
  function lock() {
    message="acquiring lock on $lockfile..."
    echo "$message"
    apos_log "$message"
    
    /usr/bin/lockfile -2 -l 16 -s 4 $lockfile
    
    local return_code=$?
    if [ $return_code -eq $TRUE ]; then
      message="lock successfully acquired"
      echo "$message"
      apos_log "$message"
    else
      message="unable to acquire lock"
      echo "ERROR: $message" >&2
      apos_log user.crit "$message"
    fi
    return $return_code
  }

  # nested unlock function to ensure mutual exclusion in the case of editing
  # clustered resource (e.g. /cluster/etc/cluster.conf)
  function unlock() {
    message="releasing lock on $lockfile"
    echo "$message"
    apos_log "$message"
    
    /usr/bin/rm -f $lockfile
    
    local return_code=$?
    if [ $return_code -eq $TRUE ]; then
      message="lock successfully released"
      echo "$message"
      apos_log "$message"
    else
      message="unable to release lock"
      echo "ERROR: $message" >&2
      apos_log user.crit "$message"
    fi
    return $return_code
  }

  local CMD_GETINFO='/opt/ap/apos/bin/gi/apos_getinfo'
  local lockdir=$(apos_create_brf_folder clear)
  local lockfile=$lockdir/$FUNCNAME.lock
  local cluster_file=''
  local nic=''
  local mac=''
  local node_id=''
  local net_entry=''
  local message=''
  local return_code=''
  local tmp_error=$(/usr/bin/mktemp -t $(/usr/bin/basename $0).XXX)
  local mutex=$FALSE
  local old_trap=''

  case $1 in
    local)
      cluster_file=/boot/.cluster.conf
    ;;
    cluster)
      cluster_file=/cluster/etc/cluster.conf
      mutex=$TRUE
      # store the current handler for the EXIT signal.
      old_trap=$(trap | grep -P '[[:space:]]EXIT$')
      # overwrite the handler for the EXIT signal.
      trap unlock EXIT
    ;;
    *)
      message="function $FUNCNAME: missing or invalid parameter ($1)"
      echo "ABORT: $message" >&2
      apos_abort "$message"
    ;;
  esac
  
  if [ ! -w "$cluster_file" ]; then
    message="ABORT: file $cluster_file not found or not writable"
    echo "ABORT: $message" >&2
    apos_abort "$message"
  else
    message="setting additional (custom) nics in $cluster_file"
    echo "$message"
    apos_log "$message"
  fi
  
  while read net_entry; do
    echo "net entry: \"$net_entry\""
    nic=$(/usr/bin/echo $net_entry| /usr/bin/awk -F';' '{print $3}')
    mac=$(/usr/bin/echo $net_entry| /usr/bin/awk -F';' '{print $4}')

    node_id=$(get_node_id)
    if is_nic_present ${nic} $cluster_file $node_id; then
      message="existing nic: ${nic}"
      echo "$message"
      apos_log "$message"
      continue
    fi
  
    if [ $mutex -eq $TRUE ]; then
      lock
    fi

    custom_interface="interface ${node_id} ${nic} ethernet ${mac}"
    echo "adding \"${custom_interface}\" to $cluster_file"
    
    # adding custom interface to $cluster_file
    last_interface=$( grep -E "^[[:space:]]*interface[[:space:]]+${node_id}[[:space:]]+eth[0-9]{1,2}[[:space:]]+ethernet[[:space:]]" $cluster_file | tail -n -1)
    
    # append interface line to cluster_file
    /usr/bin/sed -i "/${last_interface}/a ${custom_interface}" $cluster_file 2>${tmp_error}
    return_code=$?
 
    if [ $return_code -eq $TRUE ]; then
      # append blank line above and below the interface line
      /usr/bin/sed -i "/${custom_interface}/{x;p;x;G;}" $cluster_file 2>${tmp_error}
      return_code=$?
    fi  

    if [ $mutex -eq $TRUE ]; then
      unlock
    fi

    if [ $return_code -ne $TRUE ]; then
      message="failure while executing sed in-place on the file \"$cluster_file\" ($(<${tmp_error}))"
      echo "ABORT: $message" >&2
      apos_abort "$message"
    fi

    apos_log 'done'
  done  < <($CMD_GETINFO netinfo)
  if [ $mutex -eq $TRUE ]; then
    # restore the previous handler for the EXIT signal, or completely reset it.
    if [ -n "$old_trap" ]; then
      eval $old_trap
    else
      trap - EXIT
    fi
  fi

  #Unset nested functions
  unset lock
  unset unlock
}

