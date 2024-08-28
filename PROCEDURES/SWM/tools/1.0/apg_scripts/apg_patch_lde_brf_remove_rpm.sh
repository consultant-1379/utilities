#!/bin/bash -u
##
# ------------------------------------------------------------------------
#     Copyright (C) 2016 Ericsson AB. All rights reserved.
# ------------------------------------------------------------------------
##
# Name:
#       apg_patch_lde_brf_remove_rpm.sh
# Description:
#       A script containing FIX for the removal of old LDE-BRF rpm.
# Note:
#	None.
##
# Changelog:
# - Wed Apr 7 2016 - Fabio Ronca (efabron)
#	First version.
##

# Load the apos common functions.
. /opt/ap/apos/conf/apos_common.sh


apos_intro $0

#START PATCH: WAITING FOR FIX OF TR HU42259
LDE_BRF_SDP=$(find /cluster/storage/system/software/coremw/repository/ -name ERIC-LDE_BRF-CXP9021148_1-R1*)
[ -z $LDE_BRF_SDP ] && apos_log "LDE BRF sdp to patch not found"
FILE_TO_PATCH="$LDE_BRF_SDP/installer.sh"
if [ -f $FILE_TO_PATCH ]; then
   apos_log "Apply FIX for LDE_BRF-CXP9021148_1-R1K01"
   sed -i -r 's@.x86_64.rpm@ @g' $FILE_TO_PATCH
else
   	apos_log "File $FILE_TO_PATCH not exist. Skip the FIX for LDE_BRF-CXP9021148_1-R1K01"
fi
#END PATCH

apos_outro $0
exit $TRUE
