#!/bin/bash
##
# ------------------------------------------------------------------------
#     Copyright (C) 2017 Ericsson AB. All rights reserved.
# ------------------------------------------------------------------------
##
# Name:
#   apg_deploy_clu_parse_patched.sh 
# Description:
#   A script to deploy the new version of clu_parse script to 
#   folder /opt/ap/apos/bin/clusterconf
#       .
# Note:
#   This script is invoked only in below upgrade paths:
#   3.2.3, 3.2.4, 3.2.5 and 3.2.6 
##
# Changelog:
# - Thu Oct 26 2017 - Pratap Reddy Uppada (xpraupp)
#   First version.
##

# Load the apos common functions.
. /opt/ap/apos/conf/apos_common.sh

apos_intro $0

# variables
CFG_PATH="opt/ap/apos/conf/"
SOURCE_PATH="$(dirname "$(readlink -f $0)")"
DESTINATION_PATH="/opt/ap/apos/bin/clusterconf"
SCRIPT_TO_DEPLOY="clu_parse.patched"

if [ -x /opt/ap/apos/conf/apos_deploy.sh ]; then
  if [ -f "${SOURCE_PATH}/${SCRIPT_TO_DEPLOY}" ]; then
    /opt/ap/apos/conf/apos_deploy.sh --from "${SOURCE_PATH}/${SCRIPT_TO_DEPLOY}" --to "${DESTINATION_PATH}/clu_parse"
    if [ $? -ne $TRUE ]; then
      apos_log "Failed to deploy clu_parse script to ${DESTINATION_PATH}"
      apos_abort 1 "\"apos_deploy.sh\" exited with non-zero return code"
    fi
    apos_log "PATCH for TR HW37688 applied with success."
  else
    apos_abort 1 "patched version of clu_parse script not found in campaign folder"
  fi
else
  apos_abort 1 "apos_deploy.sh script found not executable"
fi

apos_outro $0
exit $TRUE

# End of file