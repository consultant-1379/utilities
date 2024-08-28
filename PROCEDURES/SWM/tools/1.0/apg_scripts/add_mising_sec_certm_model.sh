#!/bin/bash
# ------------------------------------------------------------------------
#     Copyright (C) 2018 Ericsson AB. All rights reserved.
# ------------------------------------------------------------------------
######
# Name:
#       add_mising_sec_certm_model.sh
# Description:
#       This script executes all the needed operations to add missing models
#       from the previous upgrades.
#####
# Usage:
#       ./add_mising_sec_certm_model.sh
#####
# Output:
#       Success: Returns '0'
#       Failure: Returns '1'
#####
# Changelog
# 2016-01-21 - XPRAUPP - First version

# Common variables
EXIT_SUCCESS=0
EXIT_FAILURE=1
LOG_TAG='-t add_mising_sec_certm_model.sh'

# Common functions
function log() {
    /bin/logger $LOG_TAG "$1"
}

# check if model file present or not 
function is_model_file_exist() {
  local FILE_EXIST=0
  local PSO_CONFIG_PATH_CONF_FILENAME='/usr/share/pso/storage-paths/config'
  local COMSA_REPOSITORY="$(cat $PSO_CONFIG_PATH_CONF_FILENAME)/comsa_for_coremw-apr9010555/repository"
  if ! test -f "$COMSA_REPOSITORY/SEC_CertM_mp.xml"; then
    log "INFO: Model file for sec-cert-manager is not present. Creation of model file required!!"  
    FILE_EXIST=1
  fi
  return $FILE_EXIST
}

if ! is_model_file_exist; then 
  # Retrieve the current installed bundle in the system
  bundle_name=$(/opt/coremw/bin/cmw-repository-list | grep -i 'sec-cert-manager' | grep "Used" | awk '{print $1}' 2>/dev/null)
  if [ -z "$bundle_name" ]; then
    log "ERROR: Failed to retrieve the sec-cert-manager bundle!"
    exit $EXIT_FAILURE
  fi

  # Install the missing model for SEC-CERT-MANAGER
  /opt/coremw/bin/cmw-model-add "$bundle_name" --mt COM_R1
  if [ $? -ne 0 ]; then
    log "ERROR: Failed to install model with MDF for bundle '$bundle_name'!"
    exit $EXIT_FAILURE
  fi

  # After installing all the models, commit the changes
  /opt/coremw/bin/cmw-model-done --mt COM_R1
  if [ $? -ne 0 ]; then
    log "ERROR: Failed to commit models with MDF!"
    exit $EXIT_FAILURE
  fi
else
  log "INFO: Model file for sec-cert-manager already present, Skipping the model file creation"
fi 

exit $EXIT_SUCCESS

# END OF FILE
