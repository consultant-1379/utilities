#! /bin/sh
##
## Copyright (c) Ericsson LMC, 2010.
##
## All Rights Reserved. Reproduction in whole or in part is prohibited
## without the written consent of the copyright owner.
##
## ERICSSON MAKES NO REPRESENTATIONS OR WARRANTIES ABOUT THE
## SUITABILITY OF THE SOFTWARE, EITHER EXPRESS OR IMPLIED, INCLUDING
## BUT NOT LIMITED TO THE IMPLIED WARRANTIES OF MERCHANTABILITY,
## FITNESS FOR A PARTICULAR PURPOSE, OR NON-INFRINGEMENT. ERICSSON
## SHALL NOT BE LIABLE FOR ANY DAMAGES SUFFERED BY LICENSEE AS A
## RESULT OF USING, MODIFYING OR DISTRIBUTING THIS SOFTWARE OR ITS
## DERIVATIVES.
##
##

# This script is executed as a rollback to the install campaign
# sdp name is passed as first argument
SDP_NAME=$1

#-----------------------------------------------------------------
# Function to execute any passed command
#-----------------------------------------------------------------
execute_cmd () {
    if [ $# -eq 0 ]
    then
        echo "Usage: $0 cmd [parameters list] "
        exit 1
    fi

    tmp=`$*`

    if [ $? -ne 0 ]
    then
        echo "Failed to execute: $*"
        exit 1
    fi
}

execute_cmd cmw-model-delete ${SDP_NAME} --mt IMM_R2 IMM_R1 IMM-I-FM_R1 IMM-I-Local_Authorization_R1

execute_cmd cmw-model-delete ${SDP_NAME} --mt COM_R1

execute_cmd cmw-model-done

comsa-mim-tool com_switchover

BRFC_DIRECTORY="brfc-apr9010485"
PSO_API_DEFAULT_PATH="/usr/share/pso/storage-paths"

# remove BRFC directories under PSO
PSO_CLEAR_DIR=`cat ${PSO_API_DEFAULT_PATH}/clear`

# remove BRFC directories under PSO
rm -rf ${PSO_CLEAR_DIR}/${BRFC_DIRECTORY}

exit 0
