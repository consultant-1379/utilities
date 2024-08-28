#! /bin/sh
##
## Copyright (c) Ericsson LMF, 2015
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
        logger -s -t Sec_La -p user.err "INFORMATION: $@"
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


la_model_upgrade() {

	#-----------------------------------------------------------------
	# New models modified/added by using MDF
	#-----------------------------------------------------------------

	execute_cmd cmw-model-modify "${to_SDP_NAME}"
	execute_cmd cmw-model-done
}

#-----------------------------------------------------------------
# Old sdp package is removed as CoreMW Programmers Guide
# chapter 5.2.2 instructs.
#-----------------------------------------------------------------

remove() {
        info "$from_SDP_NAME sdp package is removed" 
        execute_cmd cmw-sdp-remove "${from_SDP_NAME}"
}

case "$1" in 
"la_upgrade")
        la_model_upgrade
        ;;
"remove")
        remove
        ;;
esac

exit 0
#
