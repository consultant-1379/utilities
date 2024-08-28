#!/bin/bash
##
# ------------------------------------------------------------------------
#     Copyright (C) 2016 Ericsson AB. All rights reserved.
# ------------------------------------------------------------------------
##
# Name:
#       com_timeout_fix.sh
# Description:
#       A script to change SYNC timeout for COM. 
#
# Note:
#      JIRA CASE:CC-18230
##
# Output:
#       None.
##
# Changelog:
#
#
# Apr 03 2017 - Suraj Kumar (xkursuj)
#               First version

# Global variables
COMSA_DEST_DIR="/storage/system/config/comsa_for_coremw-apr9010555/etc" 
COMSA_IMMA_SYNCR_TIMEOUT="360000" 
COMSA_IMMA_OI_TIMEOUT="24"
BUNDLE_REPOSITORY_AP1="/cluster/storage/system/software/coremw/repository/ERIC-APG_UP"
IMM_MODEL_CONSUMER_FILE='/opt/coremw/lib/imm-model-consumer'

# Load the apos common functions.
if [ -r /opt/ap/apos/conf/apos_common.sh ];then
  . /opt/ap/apos/conf/apos_common.sh
else
  /bin/logger "/opt/ap/apos/conf/apos_common.sh not found"
  exit 1
fi

# Increase SYNC timeout of IMM consumer to 30 seconds 
if [ -e "$IMM_MODEL_CONSUMER_FILE" ]; then 
  apos_log "Setting IMMA_SYNCR_TIMEOUT to 30 seconds"
  sed -i '/All rights reserved/a export IMMA_SYNCR_TIMEOUT=3000' /opt/coremw/lib/imm-model-consumer
else
  apos_log "imm-model-consumer file does exit"
fi  

#Check Destination folder
if [ ! -d "$COMSA_DEST_DIR" ];then
  apos_abort "Folder $COMSA_DEST_DIR does not exist"
else 
  # Configure imma syncr timeout for comsa.cfg 
  # The unit of time is 10 milliseconds. The minimum allowed value is 10 (0.1 seconds).         
  sed -i "s@[[:space:]]*imma_syncr_timeout=.*@imma_syncr_timeout=$COMSA_IMMA_SYNCR_TIMEOUT@g" $COMSA_DEST_DIR/comsa.cfg
  sed -i "s@[[:space:]]*imma_oi_callback_timeout=.*@imma_oi_callback_timeout=$COMSA_IMMA_OI_TIMEOUT@g" $COMSA_DEST_DIR/comsa.cfg
  sed -i "/codes/ a export IMMA_SYNCR_TIMEOUT=$COMSA_IMMA_SYNCR_TIMEOUT" $BUNDLE_REPOSITORY_AP1/model_changes.sh 
  if [ $? -ne 0 ]; then 
    apos_abort 1 "Configuration of imma_syncr_timeout failed." 
  else 
    apos_log "imma_syncr_timeout configured to $COMSA_IMMA_SYNCR_TIMEOUT."         
  fi
fi

hostname=$(</etc/cluster/nodes/this/hostname)
[ -z "$hostname" ] && apos_abort "hostname found NULL"
CMD_RCODE=$?
if [[ "$CMD_RCODE" -ne 0 ]]; then
  if [ "$hostname" == "SC-2-1" ];then
    apos_log "Restarting COM SC-1 to reflect the new changes:"
    amf-adm restart safComp=COMSA,safSu=1,safSg=2N,safApp=ERIC-APG
  else
    apos_log "Restarting COM SC-2 to reflect the new changes:"
    amf-adm restart safComp=COMSA,safSu=2,safSg=2N,safApp=ERIC-APG
  fi
fi 

exit 0 
