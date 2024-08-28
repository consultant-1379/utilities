#!/bin/bash
##
# ------------------------------------------------------------------------
#     Copyright (C) 2016 Ericsson AB. All rights reserved.
# ------------------------------------------------------------------------
##
# Name:
#       apg_compute_objects_create.sh
# Description:
#      This script will creates compute resource objects, if objects are 
#      not created
# Note:
#      Remove this script from UP campaign invocation,when TR:HU79123 is fixed
#
# Output: 
#     None.
##
# Changelog:
#    
# Tue May 24 2016 - Yeswanth Vankayala (xyesvan)
#       First Version
##

# Load the apos common functions.
current_dir="$(dirname "$(readlink -f $0)")"
. $current_dir/apg_common.sh

apos_intro $0

hostname=$(</etc/cluster/nodes/this/hostname)
[ -z "$hostname" ] && apos_abort "hostname found NULL"

CMD_RESULT=$( kill_after_try 3 3 4 /usr/bin/immfind ECIM_ComputeResourcecomputeResourceId="$hostname" 2>/dev/null)
CMD_RCODE=$?
if [[ -z "$CMD_RESULT" && "$CMD_RCODE" -ne 0 ]]; then
  kill_after_try 5 5 6 /usr/bin/immcfg -c ECIM_ComputeResourceComputeResource \
   ECIM_ComputeResourcecomputeResourceId="$hostname" || \
   apos_abort "Failure while creating CR object for $hostname"
fi

apos_outro $0
exit $TRUE
