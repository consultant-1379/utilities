#!/bin/bash
######
# ------------------------------------------------------------------------
#     Copyright (C) 2016 Ericsson AB. All rights reserved.
# ------------------------------------------------------------------------
######
# Name:
#       migrate_models.sh
# Description:
#       This script executes all the needed operations to migrate models
#       from the old COMSA-based approach to the new MDF approach (if needed).
# Note:
#       -
#####
# Usage:
#       ./migrate_models.sh
#####
# Output:
#       <script_output_description>
#####
# Changelog
# 2018-09-18 - XSRVAN  - Added changes for adopting to  APOS-COM_R1 model file 
# 2016-09-05 - EALOCAE - Fix for HV21657
# 2016-05-25 - XYESVAN - Smart Campaign Impacts
# 2016-05-26 - EALOCAE - Improvements to handle also multiple updates.
# 2016-01-26 - EALOCAE - Adapted for Block-level UP
# 2016-01-21 - EALOCAE - First version
#
###########################################################################

################################################
# Common variables
################################################
EXIT_SUCCESS=0
EXIT_FAILURE=1
TRUE=1
FALSE=0
LOG_TAG='-t migrate_models.sh'
TMP_FILENAME=$(mktemp -t swupdate_APG_XXX)
APG_SUBSYSTEMS_NAMES_LIST="ACS|AES|APOS|BSC|CPHW|CPS|CQS|FIXS|FMS|MAS|MCS|OCS|PES|STS"
PSO_SOFTWARE_PATH_CONF_FILENAME=/usr/share/pso/storage-paths/software
PSO_CONFIG_PATH_CONF_FILENAME=/usr/share/pso/storage-paths/config
CMW_SDP_REPOSITORY=$(cat $PSO_SOFTWARE_PATH_CONF_FILENAME)/coremw/repository
CMD_ENTRY_MATCH="$(dirname $0)/entry_matches.sh"
COM_MODELS_CONFIG_FILE=$(cat $PSO_CONFIG_PATH_CONF_FILENAME)/com-apr9010443/etc/model/model_file_list.cfg
OLD_COM_MODEL_CONF_FILENAME="com-model.config"
NEW_APG_BUNDLES_LIST_FILENAME="bundles_list.conf"
MODEL_FILE="APOS-COM_R1"
################################################

################################################
# Common functions
################################################
function log() {
    /bin/logger $LOG_TAG "$1"
}

function cleanup() {
        rm -f $TMP_FILENAME
}

function check_if_models_migration_is_needed() {
        # Check if the models migration is needed or not.
        # This can be achieved by checking the content of installed APG
        # software bundles. In case at least one COM configuration file
        # having the old syntax is found, this means that we are coming
        # from an APG version where the old mechanism is used, that
        # needs the migration operation.
        local INSTALLED_APG_BUNDLES_LIST=$@

        for SDP in $INSTALLED_APG_BUNDLES_LIST; do
                if [ -e $CMW_SDP_REPOSITORY/$SDP/$OLD_COM_MODEL_CONF_FILENAME ]; then
                        log "The bundle '$SDP' has the old COM configuration file: migration to be executed!"
                        return $TRUE
                fi
        done

        return $FALSE
}

function execute_comsa_models_cleanup() {
  # In order to avoid a useless com_switchover operation,
  # execute the same cleanup operations executed in
  # comsa-mim-tool script.
  local COMSA_REPOSITORY="$(cat $PSO_CONFIG_PATH_CONF_FILENAME)/comsa_for_coremw-apr9010555/repository"
  local CLEANUP_FLAG_FILE="$COMSA_REPOSITORY/cleanFlagFolder"
  local REMOVE_SDP_LIST_FILE="$COMSA_REPOSITORY/remove_sdp_list"
  local ADD_SDP_LIST_FILE="$COMSA_REPOSITORY/add_sdp_list"

  rm -f $CLEANUP_FLAG_FILE
  rm -f $ADD_SDP_LIST_FILE

  if [ -f $REMOVE_SDP_LIST_FILE ]; then
    for ITEM in $(cat $REMOVE_SDP_LIST_FILE); do
      rm -rf $COMSA_REPOSITORY/$ITEM
    done
  fi

  rm -f $REMOVE_SDP_LIST_FILE

  for ITEM in $(ls $COMSA_REPOSITORY); do
    local ITEM_CONTENT=$(ls $COMSA_REPOSITORY/$ITEM)
    if [[ -z "$ITEM_CONTENT" ]] || [[ "$ITEM_CONTENT" == "com-model.config" ]]; then
      rm -rf $COMSA_REPOSITORY/$ITEM
    fi
  done
}
################################################

################################################
#                     MAIN                     #
################################################
# Register a handler to execute any type of cleanup operations when the script exits
trap cleanup EXIT

# Check that no input parameter has been provided
if [ $# -ne 0 ]; then
        log "Arguments found on command line: no arguments are allowed!"
        exit $EXIT_SUCCESS
fi

# Check that the file listing the new software bundles is available into the campaign
if [ ! -e $(dirname $0)/$NEW_APG_BUNDLES_LIST_FILENAME ]; then
        log "ERROR: No '$NEW_APG_BUNDLES_LIST_FILENAME' file has been found!"
        exit $EXIT_FAILURE
fi

# Check if the current upgrade is a RUP (Release UP) or a BUP (Block UP).
# In the first case, where there is more than a single bundle to be updated,
# the migration operation is needed.
# In the second one, instead, no migration will be performed.
if [ $(cat $(dirname $0)/$NEW_APG_BUNDLES_LIST_FILENAME | wc -l) -le 1 ]; then
        log "No migration operation is needed for Block-level UP!"
        exit $EXIT_SUCCESS
fi

# Retrieve the list of the installed APG bundles (applying filtering based on subsystems names)
cmw-repository-list | grep -E "$APG_SUBSYSTEMS_NAMES_LIST" | grep "Used" | awk '{print $1}' > $TMP_FILENAME
if [ $? -ne 0 ]; then
        log "ERROR: Failed to retrieve the list of installed bundles!"
        exit $EXIT_FAILURE
fi

# Check if the migration is needed or not. In case it is not needed, exit with success.
INSTALLED_APG_BUNDLES_LIST=$(cat $TMP_FILENAME)
check_if_models_migration_is_needed $INSTALLED_APG_BUNDLES_LIST
if [ $? -eq $FALSE ]; then
        log "No migration operation is needed for APG models!"
        exit $EXIT_SUCCESS
fi

# The migration operation is needed. The first step is to remove
# all the installed models using the comsa-mim-tool command.
for SDP in $INSTALLED_APG_BUNDLES_LIST; do
        # Remove the model for the current SDP bundle
        comsa-mim-tool remove $SDP
        if [ $? -ne 0 ]; then
                log "ERROR: Failed to remove model for bundle '$SDP'!"
                exit $EXIT_FAILURE
        fi
done

# Since APG bundles update doesn't mean that also models have been updated,
# the previously executed removal couldn't be enough.
# Execute another removal by taking info from COM configuration file.
for SDP in $(cat $COM_MODELS_CONFIG_FILE | grep -E "$APG_SUBSYSTEMS_NAMES_LIST" | awk -F '/' '{ print $7 }' | uniq)
do
    # Remove the model for the current SDP bundle
    comsa-mim-tool remove $SDP
    if [ $? -ne 0 ]; then
        log "ERROR: Failed to remove model for bundle '$SDP'!"
        exit $EXIT_FAILURE
    fi
done

# After removing all the models with comsa-mim-tool command, commit the changes
comsa-mim-tool commit
if [ $? -ne 0 ]; then
        log "ERROR: Failed to commit the models removal operation!"
        exit $EXIT_FAILURE
fi

# The last operation needed is the installation with MDF of all
# the models provided by the new APG software bundles with MDF
NEW_APG_BUNDLES_LIST=$(cat $(dirname $0)/$NEW_APG_BUNDLES_LIST_FILENAME)
for BUNDLE in $NEW_APG_BUNDLES_LIST; do
        # Check block to be installed or not
        COMP=$(echo $BUNDLE | awk -F ';' '{print $1}')
        SDP=$(echo $BUNDLE | awk -F ';' '{print $2}')
        $CMD_ENTRY_MATCH install $COMP
        if [ $? -eq 0 ];then
          # Install the model for the current SDP bundle
          if [[ "$BUNDLE" =~ "ERIC-APOS_OSCONFBIN" ]]; then
	    cmw-model-add $SDP --mt COM_R1
          else
	   cmw-model-add $SDP --mt $MODEL_FILE
          fi	
          if [ $? -ne 0 ]; then
                log "ERROR: Failed to install model with MDF for bundle '$SDP'!"
                exit $EXIT_FAILURE
          fi
       fi
       if [[ "$BUNDLE" =~ "ERIC-APOS_OSCONFBIN" ]]; then
	cmw-model-done --mt COM_R1
       else
	cmw-model-done --mt $MODEL_FILE
       fi
       if [ $? -ne 0 ]; then
        log "ERROR: Failed to commit models with MDF!"
        exit $EXIT_FAILURE
       fi

done

# After installing all the models provided by the new APG bundles, commit the changes
#cmw-model-done --mt $MODEL_FILE
#cmw-model-done --mt COM_R1
#if [ $? -ne 0 ]; then
 #       log "ERROR: Failed to commit models with MDF!"
  #      exit $EXIT_FAILURE
#fi

# Execute comsa cleanup operations in order to avoid a com_switchover operation
execute_comsa_models_cleanup

exit $EXIT_SUCCESS
