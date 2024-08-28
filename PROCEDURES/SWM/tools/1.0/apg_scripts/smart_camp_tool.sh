#!/bin/bash
##
# ------------------------------------------------------------------------
#     Copyright (C) 2016 Ericsson AB. All rights reserved.
# ------------------------------------------------------------------------
##
# Name:
#   smart_camp_tool.sh
##
# Description:
#   A tool used in smart campaign to include/exclude a block/application
##
# Usage:
#   smart_camp_tool.sh install block dn
#   smart_camp_tool.sh install block update-to=<CXC_VERSION>
#   smart_camp_tool.sh node-lock install block dn
#   smart_camp_tool.sh node-lock dn
##
# Changelog:
# - 2017 Apr 18 - Francesco Rainone (EFRARAI) and Fabio Ronca (EFABRON)
#   Implemented aging cache mechanism to fix TR HV68851.
# - 2016 Aug 05 - Francesco Rainone (EFRARAI)
#   Implemented caching mechanism for improving speed of execution.
# - 2016 Jun 15 - Yeswanth Vankayala (xyesvan)
#   called is_updatable script to handle APG SW Version 
# - 2016 May 17 - Yeswanth Vankayala (xyesvan)
##

true=$(true; echo $?)
false=$(false; echo $?)

tag='smart_camp_tool.sh'
current_dir="$(dirname "$(readlink -f $0)")"
check_immdn="$current_dir/check_imm_dn.sh"
is_updatable="$current_dir/is_updatable.sh"
launch_script=''
exitstatus=$false
cmd_path="/opt/ap/apos/bin/em/"

if [ -x $cmd_path/entry_matches.sh ];then
   entry_match="$cmd_path/entry_matches.sh"
else
   entry_match="$current_dir/entry_matches.sh"
fi

function log(){
  /bin/logger -t $tag "$*"
}

abort(){
  log "ABORTING: <ERROR: $*>"
  exit 1
}

function usage(){
cat << EOF
Usage:

smart_camp_tool.sh install block dn
smart_camp_tool.sh install block update-to=<CXC_VERSION>
smart_camp_tool.sh node-lock install block dn
smart_camp_tool.sh node-lock dn

EOF
}

function main() {
  # M A I N

  if [ $# -le 0 ]; then
    usage
    abort "Usage error"
  fi

  last_arg="${!#}"
  length=$(($#-1))
  args=${@:1:$length}

  [[ ! -x $check_immdn || ! -x $entry_match || ! -x $is_updatable ]] && 
  abort "Execute permissions not found for [$check_immdn] [$entry_match] [$is_updatable]"

  launch_script=$check_immdn
  if [[ "$last_arg" =~ ^update-to.* ]]; then
    block=${@:2:1}
    last_arg=$( echo $last_arg | awk -F = '{print $2}')	
    launch_script=$is_updatable
  fi

  if (( ! $( $entry_match $args &>/dev/null; echo $?) & ! $( $launch_script $block $last_arg &>/dev/null; echo $?) )); then
    exitstatus=$true
  fi

  return $exitstatus
}
  
function is_cached() {
  function encode() {
   if [ $# -gt 0 ]; then 
      echo "$*" | base64 -i -w 0 | tr '/' '-'
    else
      cat | base64 -i -w 0 | tr '/' '-'
    fi
  }
  
  is_cache_expired() {
    local cache_file=$1
    local max_age_in_secs=900
    local cache_age=$(/usr/bin/stat --format=%Y ${cache_file})
    local now=$(date +%s)
    local age=$(($now - $cache_age))
    if [[ "$age" -lt 0 || "$age" -gt "$max_age_in_secs" ]]; then
      return $true
    fi
    return $false
  }
  
  purge_old_cache() {
    local cache_file=$1
    if [ -f ${cache_file} ] && is_cache_expired ${cache_file}; then
      # delete che cache file in the case it exists, but it's too old.
      rm -f ${cache_file}
    fi
  }


  function cache_stdout() {
    local retcode=$true
    local filename=${base_filename}_out
    local map_file=${dirname}/${filename}
    purge_old_cache ${map_file}
    if [ ! -f ${map_file} ]; then
      # cache doesn't exist and must be created
      touch ${map_file}   # if file does not exist, redirect fails
      exec 6>&1           # save stout in fd 6 (as output)
      exec >${map_file}   # redirect stdout to ${map_file} (as output)
      retcode=$false
    fi
    exec 7<${map_file}    # assign fd 7 to ${map_file} (as input)
    return $retcode
  }

  function cache_return() {
    local retcode=$true
    local filename=${base_filename}_ret
    local map_file=${dirname}/${filename}
    purge_old_cache ${map_file}
    if [ ! -f ${map_file} ]; then
      # cache doesn't exist and must be created
      touch ${map_file}   # if file does not exist, redirect fails
      exec 8>${map_file}  # assign fd 8 to ${map_file} (as output)
      retcode=$false
    fi
    exec 9<${map_file}    # assign fd 9 to ${map_file} (as input)
    return $retcode
  }


  local progname=$(basename $0)
  local dirname=/dev/shm/${progname}
  [ ! -d ${dirname} ] && mkdir -p ${dirname}
  local base_filename=$(encode "${@}")
  
  local return_code=$true
  
  cache_stdout || return_code=$false
  cache_return || return_code=$false
  
  return $return_code
}


if ! is_cached "$@"; then
  main "$@"
  echo $? >&8   # save return value in fd 8
  exec >&6      # restore stdout (as output)
fi

cat <&7         # print the content of fd 7 on stdout
exit $(cat <&9) # use content of fd 9 as exit code

