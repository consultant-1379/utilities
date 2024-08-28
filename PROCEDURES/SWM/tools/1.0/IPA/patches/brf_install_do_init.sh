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


# This script is executed as an installation campaign init action.
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

# Initialize
BRFC_DIRECTORY="brfc-apr9010485"
PSO_API_DEFAULT_PATH="/usr/share/pso/storage-paths"

# Install IMM Model/Objects
execute_cmd cmw-model-add ${SDP_NAME} --mt IMM_R2 IMM_R1 IMM-I-Local_Authorization_R1

# Link BRFP model type to IMM_R1 to be used as MDF Interface
execute_cmd cmw-modeltype-link BRFP_R1 IMM_R1

# Check and install COM Model
execute_cmd cmw-model-add ${SDP_NAME} --mt COM_R1 IMM-I-FM_R1

# Finalize model install
execute_cmd cmw-model-done

comsa-mim-tool com_switchover

# Create BRFC directories under PSO
PSO_CLEAR_DIR=`cat ${PSO_API_DEFAULT_PATH}/clear`
mkdir -p ${PSO_CLEAR_DIR}/${BRFC_DIRECTORY}

exit 0
