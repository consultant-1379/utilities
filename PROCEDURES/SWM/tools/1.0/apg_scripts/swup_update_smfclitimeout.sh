#!/bin/bash
##
# ------------------------------------------------------------------------
#     Copyright (C) 2013 Ericsson AB. All rights reserved.
# ------------------------------------------------------------------------
##
# Name:
#      swup_update_smfclitimeout.sh  
# Description:
#       A script to change timeout of smfclitimeout  
# Note:
#       None.
##
# Output:
#       None.
##
# Changelog:
# - 2016 Jun 25 - Yeswanth Vankayala (xyesvan)
#       First version.
##

# Load the apos common functions.
current_dir="$(dirname "$(readlink -f $0)")"
. $current_dir/apg_common.sh

apos_intro $0

CMD_HWTYPE='/opt/ap/apos/conf/apos_hwtype.sh'
HW_TYPE=$( $CMD_HWTYPE)

function set_timeout(){
 default_timeout=$(immlist smfConfig=1,safApp=safSmfService | grep smfCliTimeout | awk -F ' ' '{print $3}')
 echo "$default_timeout" > $current_dir/default_smfclitimeout.txt
 if [[ "$HW_TYPE" == "GEP1" || "$HW_TYPE" == "GEP2" ]];then
   # its been observed that on GEP1 based nodes, OSEXTBIN software 
   # installation is failling with the reason of installation timeout
   # has expired. The default installation timeout from SMF is 10m.
   # OSEXBIN is responsible for installaing apg required os rpms on the node.
   # Hence, the timeout is increased to 20m in this case. 20m=2000000000000 nanoseconds
   kill_after_try 3 1 5 /usr/bin/immcfg  -a smfCliTimeout=2000000000000 smfConfig=1,safApp=safSmfService &> /dev/null 
   apos_log "$HW_TYPE: smfCliTimeout = 2000000000000"
 else
    apos_log "$HW_TYPE: default smfCliTimeout considered "
 fi
   
}

function default_timeout(){
 if [[ "$HW_TYPE" == "GEP1" || "$HW_TYPE" == "GEP2" ]];then
    kill_after_try 3 1 5 /usr/bin/immcfg  -a smfCliTimeout=$(<$current_dir/default_smfclitimeout.txt) smfConfig=1,safApp=safSmfService &> /dev/null
    apos_log "$HW_TYPE: smfCliTimeout value set to default"      
 else
     apos_log "$HW_TYPE: default smfCliTimeout considered "
 fi
}


#### M A I N #####

if [ "$1" == "set" ];then
     set_timeout
elif [ "$1" == "default" ];then
   default_timeout
else
  apos_log "invalid argument"
fi

exit $TRUE    
     
