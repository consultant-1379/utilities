#!/bin/bash
##
# ------------------------------------------------------------------------
#     Copyright (C) 2016 Ericsson AB. All rights reserved.
# ------------------------------------------------------------------------
##
# Name:
#        apg_inservice.sh
# Description:
#      A script to remove extra folder in internal_root path 
#
# Note:
#      -
##
# Output:
#       None.
##
# Changelog:
#
# - Wed Aug 10 2016 - Yeswanth Vankayala (xyesvan)
#       First version.
##

DATA_STORAGE="/data/opt/ap/internal_root/"


function log(){
  /bin/logger -t "$LOG_TAG" "$*"
}

function abort(){
        log "ABORTING: <"ERROR: $1">"
        exit $FALSE
}

#Get Node 1 Status
NODE_1_STATE=$(amf-state siass ha safSISU=safSu=1\\,safSg=2N\\,safApp=ERIC-APG,safSi=AGENT,safApp=ERIC-APG | grep saAmfSISUHAState | awk -F'=' '{print $2}'| awk -F'(' '{print $1}')
#Get Node 2 Status
NODE_2_STATE=$(amf-state siass ha safSISU=safSu=2\\,safSg=2N\\,safApp=ERIC-APG,safSi=AGENT,safApp=ERIC-APG | grep saAmfSISUHAState | awk -F'=' '{print $2}'| awk -F'(' '{print $1}')

NODE=""

if [ "$NODE_1_STATE" = "ACTIVE" ];then
        NODE="SC-2-1"
elif [ "$NODE_1_STATE" = "STANDBY" ]; then
        NODE="SC-2-2"
else
        abort "APG STATUS NOT VALID"
fi

THIS_NODE=$(cat /etc/cluster/nodes/this/hostname)
if [ "$THIS_NODE" = "$NODE" ]; then
       INSERVICE=$(find $DATA_STORAGE -name InServicePerformance)
       if [ -z $INSERVICE ]; then
          log "InServicePerformance folder is not present nothing to do"
       else
           rm -rf $INSERVICE
           log "InServicePerformance folder is removed"
       fi
else
       log "Node is Passive skip!!!"
fi     


