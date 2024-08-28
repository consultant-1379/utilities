#! /bin/sh
##
## Copyright (c) Ericsson LMF, 2014-2016
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

# This script is executed during the upgrade campaign to update class and instance models
# upgrade from sdp name is passed as the first argument
# upgrade to sdp name is passed as the second argument

from_SDP_NAME=$(echo "$2" | sed 's/safSmfBundle=//')
to_SDP_NAME=$3
cmw_REPO_PATH="$(cat /usr/share/pso/storage-paths/software)/coremw/repository"

#-----------------------------------------------------------------
# Information print
#-----------------------------------------------------------------

info() {
        logger -s -t Sec_Cert -p user.err "INFORMATION: $@"
}

#-----------------------------------------------------------------
# Function to execute any passed command
#-----------------------------------------------------------------

execute_cmd () {

    tmp="$($*)"

    if [ $? -ne 0 ]
    then
        info "${to_SDP_NAME} upgrade failed: $*" 	
        exit 1
    fi
}

#-----------------------------------------------------------------
# If comsa-mim-tool has been previously used to deliver COM
# model, model type configuration file for MDF is created
# and old COM model is deleted. SEC Cert R1A and R1B
#-----------------------------------------------------------------

cert_model_upgrade() {

        info "COM and IMM model files are updated." 

	if [ -e "${cmw_REPO_PATH}/${from_SDP_NAME}/com-model.config" ]
	then
	    mv "${cmw_REPO_PATH}/${from_SDP_NAME}/com-model.config" "${cmw_REPO_PATH}/${from_SDP_NAME}/COM_R1-model.config"
	fi

	#-----------------------------------------------------------------
	# MDF installed COM model is unconditionally deleted before
	# general modify, due to CertM model name change in SEC Cert R1C
	# which situation the MDF modify command can not handel.
	#-----------------------------------------------------------------

	execute_cmd cmw-model-delete "${from_SDP_NAME}" --mt COM_R1
	execute_cmd cmw-model-done

	#-----------------------------------------------------------------
	# New models modified/added by using MDF
	#-----------------------------------------------------------------

	execute_cmd cmw-model-modify "${to_SDP_NAME}"
	execute_cmd cmw-model-done
}

case "$1" in 
"cert_upgrade")
        cert_model_upgrade
        ;;
esac

exit 0
#
