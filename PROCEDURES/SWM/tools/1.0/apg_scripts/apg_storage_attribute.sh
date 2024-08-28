#!/bin/bash
##
# ------------------------------------------------------------------------
#     Copyright (C) 2016 Ericsson AB. All rights reserved.
# ------------------------------------------------------------------------
##
# Name:
#       apg_storage_attribute.sh
# Description:
#      This script will creates compute resource objects, if objects are
#      not created
# Note:
#
# Output:
#     None.
##
# Changelog:
# Thr Feb 22 2018 - Sowjanya Medak (xsowmed)
#	turbo_boost_cp parameter addition to storage
# Thu Jun 09 2016 - Yeswanth Vankayala (xyesvan)
#       First Version
##

# Load the apos common functions.

if [ ! -r /opt/ap/apos/conf/apos_common.sh ];then
	/bin/logger "/opt/ap/apos/conf/apos_common.sh not found"
  apos_abort "apos_common.sh file not found"
fi

. /opt/ap/apos/conf/apos_common.sh 
STORAGE_PATH=$(apos_create_brf_folder config)
SHELF_ARCH="$STORAGE_PATH/shelf_architecture"
TURBO_BOOST_CP="$STORAGE_PATH/turbo_boost_cp"

apos_intro $0

imm_value=$(immlist axeFunctionsId=1 | grep apgShelfArchitecture | awk -F ' ' '{print $3}')
[ $imm_value -eq '0' ] && shelf=SCB
[ $imm_value -eq '1' ] && shelf=SCX
[ $imm_value -eq '2' ] && shelf=DMX
[ $imm_value -eq '3' ] && shelf=VIRTUALIZED
[ $imm_value -eq '4' ] && shelf=SMX

echo $shelf > $SHELF_ARCH

if [ ! -f "$TURBO_BOOST_CP" ]; then
   echo "FALSE" > $TURBO_BOOST_CP
fi

apos_outro $0

exit 0
