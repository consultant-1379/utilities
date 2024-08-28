#!/bin/bash
##
# ------------------------------------------------------------------------
#     Copyright (C) 2016 Ericsson AB. All rights reserved.
# ------------------------------------------------------------------------
##
# Name:
#       lde_unused_rpms.sh 
# Description:
#      A script to remove unused rpms. 
#
# Note:
#      -
##
# Output:
#       None.
##
# Changelog:
#
# - Fri Aug 26 2016 - Yeswanth Vankayala (xyesvan)
#       First version.
##
. /opt/ap/apos/conf/apos_common.sh

RPMS_DIR=/cluster/rpms
NODES=$(ls -1 /etc/cluster/nodes/all)

if [ ! -d $RPMS_DIR ]; then
    apos_log "ERROR: $RPMS_DIR not found"
    exit 1
fi

for RPM in $RPMS_DIR/*; do
    if [[ "$RPM" == *.rpm ]] || [[ "$RPM" == *.RPM ]]; then
        IS_INSTALLED=0
        RPM_NAME=$(basename $RPM)
        # Check if already installed
        for NODE in $NODES; do
            CONFIG_FILE=/cluster/nodes/$NODE/etc/rpm.conf
            grep -q "^$RPM_NAME$" $CONFIG_FILE
            if [ $? -eq 0 ]; then
                IS_INSTALLED=1
                break
            fi
        done

        if [ $IS_INSTALLED -eq 0 ]; then
            rm -f $RPM
            apos_log "Removed $RPM_NAME"
        fi
    fi
done

apos_log "Finished cleaning up unused rpms"
