#!/bin/bash
##
# ------------------------------------------------------------------------
#     Copyright (C) 2013 Ericsson AB. All rights reserved.
# ------------------------------------------------------------------------
##
# Name:
#      check_imm_dn.sh  
# Description:
#       A script to check DN's are present or not.
# Note:
#       None.
##
# Output:
#       None.
##
# Changelog:
# - 2016 Jun 30 - Yeswanth Vankayala (xyesvan)
#      immfind cache file is used to decrease parsing time during upgrade and function description
# - 2016 Feb 26 - Yeswanth Vankayala (xyesvan)
#       First version.
##

# Load the apos common functions.
current_dir="$(dirname "$(readlink -f $0)")"
. $current_dir/apg_common.sh
cache_file="$current_dir"/immfind_cache

# This function returns:
#  TRUE, if the DN does not exist in IMM
#  FALSE, if the DN exist in IMM
# Note:
#  If this function returns 'TRUE', if will include 
#  the "INCLDUE_IF_CMD" TAGS in campaign.
function if_dn_exist_exclude_app(){
  local dn="$@"
  local CMD="/usr/bin/immfind"
  if [ ! -e $cache_file ]; then
     kill_after_try 3 3 4 $CMD > $cache_file
  fi
  if grep -qE $dn $cache_file &>/dev/null ;then
    return $FALSE
  fi
  return $TRUE
}

#### M A I N #####
if_dn_exist_exclude_app "$@"
