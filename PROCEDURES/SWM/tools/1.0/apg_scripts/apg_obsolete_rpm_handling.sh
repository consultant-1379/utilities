#!/bin/bash -u
##
# ------------------------------------------------------------------------
#     Copyright (C) 2016 Ericsson AB. All rights reserved.
# ------------------------------------------------------------------------
##
# Name:
#       apg_obsolete_rpm_handling.sh
# Description:
#       A script containing FIX for TR HU42259 to handle the obsolete RPM.
# Note:
#	None.
##
# Changelog:
# - Wed Apr 6 2016 - Fabio Ronca (efabron)
#	First version.
##

# Load the apos common functions.
. /opt/ap/apos/conf/apos_common.sh


apos_intro $0

#START PATCH: WAITING FOR FIX OF TR HU42259
FILE_TO_PATCH="/usr/lib/cmwea/rpm-config-add"
if [ -f $FILE_TO_PATCH ]; then
   	apos_log "Apply patch for TR HU42259"
   	sed -i -r 's@[[:space:]]+-o "\$OLD_NAME"[[:space:]]=[[:space:]]"\$INSTALLED_NAME"[[:space:]]+@ @g' $FILE_TO_PATCH
else
   	apos_abort "File $FILE_TO_PATCH not exist"
fi
#END PATCH

apos_outro $0
exit $TRUE
