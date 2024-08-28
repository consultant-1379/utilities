#!/bin/bash
##
# ------------------------------------------------------------------------
#     Copyright (C) 2012 Ericsson AB. All rights reserved.
# ------------------------------------------------------------------------
##
# Name:
#       mac_addr_op.sh
# Description:
#       A common library providing MAC addresses handling for APOS routines.
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
# - Mon Feb 28 2022 - Amrutha Padi (ZPDXMRT)
#       Improved lock mechanism and increased sleep interval in MAC updation module.
# - Tue Dec 13 2016 - Francesco Rainone (efrarai)
#	Addition of set_local_macs_in_cluster_conf function and related routines.
# - Tue Dec 04 2012 - Francesco Rainone (efrarai)
#	First version.
##

# checks if the passed parameter is in the form FF:FF:FF:FF:FF:FF
function is_mac() {
  local mac="${1}"
  [[ "$mac" =~  ^(([a-fA-F0-9]{2}:){5}([a-fA-F0-9]{2}))$ ]] && return $TRUE
  return $FALSE
}

function mac_exists(){
  local mac=$1
  ! is_mac "$mac" && return $FALSE
  grep -iq ${mac} /sys/class/net/*/address || return $FALSE
  return $TRUE
}

# converts a MAC address (in the form FF:FF:FF:FF:FF:FF) to an hex string
function mac2hex(){
  if [ $# -gt 0 ]; then
    local MAC="${1}"
    echo "$MAC" | sed 's@[^0-9A-Fa-f]@@g'
    return $TRUE
  fi
  return $FALSE
}

# converts an hex string to a MAC address (in the form FF:FF:FF:FF:FF:FF)
function hex2mac(){
  if [ $# -gt 0 ]; then
    local HEX="000000000000${1}"
    HEX=${HEX: -12}
    printf "%02s:%02s:%02s:%02s:%02s:%02s" ${HEX:0:2} ${HEX:2:2} ${HEX:4:2} ${HEX:6:2} ${HEX:8:2} ${HEX:10:2}
    return $TRUE
  fi
  return $FALSE
}

# checks if the MAC address passed as argument has the LAA bit set.
function is_LAA_set() {
  if [ $# -gt 0 ]; then
    if is_mac "${1}"; then
      local LAA_MASK='020000000000'
      local MAC=$( mac2hex ${1} )
      local RESULT=$(printf "%012x" "$(( 16#${MAC} & 16#${LAA_MASK} ))")
      if [ "$RESULT" == "$LAA_MASK" ]; then
        return $TRUE
      fi
    fi
  fi
  return $FALSE
}

# Flags the LAA bit to the MAC addres passed as parameter.
function set_LAA() {
  if [ $# -gt 0 ]; then
    if is_mac "${1}"; then
      local LAA_MASK='020000000000'
      local MAC=$( mac2hex ${1} )
      hex2mac $(printf "%012x" "$(( 16#${MAC} | 16#${LAA_MASK} ))" | tr '[:lower:]' '[:upper:]')
      return $TRUE
    fi
  fi
  return $FALSE
}

# Provides a random MAC address re-using the MSB of the MAC passed as parameter.
function get_random_mac() {
  if [ $# -gt 0 ]; then
    if is_mac "${1}"; then
      MSB=${1:0:2}
      local RNDMAC=$( (date; cat /proc/interrupts) | md5sum | sed -r 's/^(.{10}).*$/\1/; s/([0-9a-f]{2})/\1:/g; s/:$//;' )
      echo "${MSB}:$RNDMAC" | tr '[:lower:]' '[:upper:]'
    fi
  fi
  return $FALSE
}

# Usage: set_local_macs_in_cluster_conf <local/cluster>
##
# The function fetches the local mac addresses from "getinfo netinfo" and
# replaces the cluster.conf "interface" entries with these values.
# A parameter (local/cluster) specifies which cluster.conf file shall be updated
# (either the local one - under /boot - or the cluster one - under /cluster).
function set_local_macs_in_cluster_conf(){

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
      echo "trap unlock EXIT --util repo"
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
    message="setting local macs in --util repo $cluster_file"
    echo "$message"
    apos_log "$message"
  fi
  
  while read net_entry; do
    echo "net entry: --util repo \"$net_entry\""
    nic=$(/usr/bin/echo $net_entry| /usr/bin/awk -F';' '{print $3}')
    mac=$(/usr/bin/echo $net_entry| /usr/bin/awk -F';' '{print $4}')
    if ! mac_exists "${mac}"; then
      message="non-valid mac identified: ${mac}"
      echo "ABORT: $message" >&2
      apos_abort "$message"
    fi
    node_id=$(get_node_id)
    echo "setting mac ${mac} to nic --util repo ${nic}..."
    if [ $mutex -eq $TRUE ]; then
      echo "executing lock if mutex true --util repo"
      lock
    fi
    echo "sed command execution--setting macs --util repo"
    usleep 10000
    echo "after sleep of 10ms"
    /usr/bin/sed -i -r "s@^([[:space:]]*interface[[:space:]]+${node_id}[[:space:]]+)(${nic})([[:space:]]+ethernet[[:space:]]+)(([a-fA-F0-9]{2}:){5}([a-fA-F0-9]{2}))[[:space:]]*\$@\1\2\3${mac}@g" $cluster_file 2>${tmp_error}
    return_code=$?
    
    if [ $return_code -ne $TRUE ]; then
      echo "Sed command failed once,so going for retry... --util repo"
      local n=0
      until [ "$n" -ge 9 ]
      do
        n=$((n+1)) 
        usleep 2000
        echo "In --util repo ..going for retry - $n"
        /usr/bin/sed -i -r "s@^([[:space:]]*interface[[:space:]]+${node_id}[[:space:]]+)(${nic})([[:space:]]+ethernet[[:space:]]+)(([a-fA-F0-9]{2}:){5}([a-fA-F0-9]{2}))[[:space:]]*\$@\1\2\3${mac}@g" $cluster_file 2>${tmp_error}
        return_code=$?
        if [ $return_code -eq $TRUE ]; then
           break
        fi
     done
    fi
    
    if [ $mutex -eq $TRUE ]; then
      echo "unlock if mutex = true --util repo"
      unlock
    fi

    if [ $return_code -ne $TRUE ]; then
      echo "Executing trap -EXIT if return code is not true --util repo"
      trap - EXIT
      message="failure while executing sed in-place on the file --util repo \"$cluster_file\" ($(<${tmp_error}))"
      echo "ABORT: $message" >&2
      apos_abort "$message"
    fi
    apos_log 'done'
  done  < <($CMD_GETINFO netinfo)
  if [ $mutex -eq $TRUE ]; then
    echo "mutex true outside loop --util repo"
    # restore the previous handler for the EXIT signal, or completely reset it.
    if [ -n "$old_trap" ]; then
      echo "eval old trap --util repo"
      eval $old_trap
    else
      echo "otherwise execute trap EXIT --util repo"
      trap - EXIT
    fi
  fi

  #Unset nested functions
  unset lock
  unset unlock
}

function show_current_nic_setup() {
  local mac=''
  local nic=''
  for nic in /sys/class/net/*; do
    mac=$(<${nic}/address)
    local message="nic=$(/usr/bin/basename ${nic}) mac=${mac}"
    echo "$message"
    apos_log "$message"
  done
}

function mac2nic() {
  if mac_exists "$1"; then
    local my_mac="$1"
    local nic_path=''
    local nic_mac=''
    local nic=''
    while read nic_path; do
      nic_mac=$(<${nic_path}/address)
      if [ "$nic_mac" == "$my_mac" ]; then
        nic="$(/usr/bin/basename ${nic_path})"
        echo "${nic}"
        return $TRUE
      fi
    done < <(find /sys/class/net/ -regex "/sys/class/net/eth[0-9]+")
  fi
  return $FALSE
}

function nic2mac() {
  local my_nic="$1"
	local mac=$(</sys/class/net/$my_nic/address)
  echo "${mac}"
}
