#!/bin/bash
##
# ------------------------------------------------------------------------
#     Copyright (C) 2017 Ericsson AB. All rights reserved.
# ------------------------------------------------------------------------
##
# Name:
#       apg_lm_data_transfer.sh
# Description:
#       taking backup of lmdata file during start of the upgrade.
# Note:
#       <script_notes>
##
# Usage:
#       ./apg_lm_data_transfer.sh
##
# Output:
#       <script_output_description>
##
# Changelog:
#
# 2017-10-10 XGOUMON First Release
##

# Load the apos common functions.
if [ -r /opt/ap/apos/conf/apos_common.sh ];then
  . /opt/ap/apos/conf/apos_common.sh
else
  /bin/logger "/opt/ap/apos/conf/apos_common.sh not found"
  exit 1
fi

# Variables
LM_DATA_MAIN_FILE="/data/acs/data/ACS-LM/lmdata"
LM_DATA_BACKUP_LOCATION="/cluster/"
LM_DATA_CLUSTER="/cluster/lmdata"
NODE_ID=$(cat /etc/nodeid)
NODE_STATE=$(amf-state siass ha safSISU=safSu=$NODE_ID\\,safSg=2N\\,safApp=ERIC-APG,safSi=AGENT,safApp=ERIC-APG | grep saAmfSISUHAState | awk -F'=' '{print $2}'| awk -F'(' '{print $1}')

#function to copy the file
copy_lm_into_cluster() {
   if [ "$NODE_STATE" = "ACTIVE" ];then
   	if [ -e $LM_DATA_MAIN_FILE ]; then

        	cp $LM_DATA_MAIN_FILE $LM_DATA_BACKUP_LOCATION
          	if [ $? -eq 0 ]; then
             	apos_log "file copied to the cluster location>>>>"

          	else
             	apos_log "failed to copy lmdata file into cluster location >>>>"
          	fi
   	else
         apos_log "file not present on the target folder>>>>"
   	fi
   else
	apos_log "Current Node is PASSIVE>>>>"
   fi
}

#function to delete from cluster
delete_lm_from_cluster() {

        if [ -e $LM_DATA_CLUSTER ]; then

           rm $LM_DATA_CLUSTER

            if [ $? -eq 0 ]; then
                 apos_log "file deleted from the cluster location>>>>"

            else
                  apos_log "failed to delete lmdata file from cluster location >>>>"
            fi

        else
        apos_log "lmdata file not present in the cluster location >>>>>"
        fi
}


case $1 in
"copy")
        copy_lm_into_cluster
        ;;
"delete")
        delete_lm_from_cluster
    ;;
esac

apos_outro $0
exit $TRUE


