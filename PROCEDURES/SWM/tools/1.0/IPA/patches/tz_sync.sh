#!/bin/bash
##
# ------------------------------------------------------------------------
#     Copyright (C) 2013 Ericsson AB. All rights reserved.
# ------------------------------------------------------------------------
##
# Name:
#       MI_timezone.sh
# Description:
#       Create a Timezone link between AP and CP.
# Note:
#	None.
##
# Output:
#       None.
##
# Changelog:
# 
# - Tue Feb 04 2013 - Antonio Buonocunto (eanbuon)
#	First version.
##
 
# Load the apos common functions.
. /opt/ap/apos/conf/apos_common.sh
# Common variables
TRUE=$( true; echo $? )
FALSE=$( false; echo $? )
APOS_CONF_PATH="/opt/ap/apos/bin"
TMZ_VALUE=0

# Common commands
SED=`which sed`
GREP=`which grep`
TZLS=`which tzls`
MTZLN=`which mtzln`
CLUSTERTOOL="clusterconf"

# Main

#Exit if  OSU is ongoing
service osuengine status &> /dev/null
OSU_CHECK=$(echo $?)
if [ "$OSU_CHECK" = "0" ];then
        exit 0
fi
if [ ! -x $APOS_CONF_PATH/$CLUSTERTOOL ];then
	apos_abort 1 "file \"$APOS_CONF_PATH/$CLUSTERTOOL\" not found or not executable"
fi
# tzls | grep $(./clusterconf timezone -D | tail -1 | awk '{print $3}')
# Using cluster tool retrive current timezone
pushd $APOS_CONF_PATH/$CLUSTERTOOL >> /dev/null
TZ=$(./clusterconf timezone -D | tail -1 | awk '{print $3}')
popd >> /dev/null
#Verify TZ value
if [ -z $TZ ];then
	apos_abort 1 "timezone setting in cluster conf is empty"
fi
#Verify TZLS command
if [ ! -x $TZLS ];then
	apos_abort 1 "file \"$TZLS\" not found or not executable"
fi
#Get TZ_NAME from tzls command
TZ_NAME=$($TZLS | $GREP $TZ)
#Verify TZ_NAME value
if [ -z "$TZ_NAME" ];then
	apos_abort 1 "timezone not found using $TZLS command"
fi
#Prepare TZ_NAME for mtzln command
TZ_NAME=${$TZ_NAME:1}
#Execute MTZLN command
$MTZLN "$TZ_NAME" $TMZ_VALUE
if [ $? != 0 ];then
	apos_abort 1 "command $MTZLN \"$TZ_NAME\" $TMZ_VALUE failed"	
fi
apos_outro $0
exit $TRUE

# End of file

