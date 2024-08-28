#!/bin/bash
##
# ------------------------------------------------------------------------
#     Copyright (C) 2016 Ericsson AB. All rights reserved.
# ------------------------------------------------------------------------
##
# Name:
#       usaFM-config
# Description:
#       A script to continuously update USAFM xml file with originalTimeevent tag.
#
##
# Changelog:
# - Thu  Nov 2 2016 - sowjanya medak (xsowmed)
#       First version.
##
# libraries -------------------------------------------------------------- BEGIN
if [ -r /opt/ap/apos/conf/apos_common.sh ]; then
 . /opt/ap/apos/conf/apos_common.sh
else
  echo '/opt/ap/apos/conf/apos_common.sh not found or not readable!' >&2
  exit 1
fi

apos_intro $0

STORAGE_CLEAR=/usr/share/pso/storage-paths/clear
USAFM_XML_FILE="$(cat $STORAGE_CLEAR)/acs_usafm/active_fm_alarm_list.xml"
CMD_SED='/usr/bin/sed'
GROUP_TEST="com-core"
USER_TEST="com-core"

while :
do
  if [ -f "$USAFM_XML_FILE" ];then
    getent passwd $USER_TEST &> /dev/null
    USER_RC="$?"
    getent group $GROUP_TEST &> /dev/null
    GROUP_RC="$?"
    if [ $USER_RC -eq 0 ] && [ $GROUP_RC -eq 0 ];then
      if [ "$(stat -c %U $USAFM_XML_FILE)" != "com-core" ];then
        chown com-core $USAFM_XML_FILE
        if [ $? -eq 0 ];then
          apos_log "Owner update on USAFM XML success"
        else
          apos_log "Owner update on USAFM XML Failed"
        fi
      fi
      if [ "$(stat -c %G $USAFM_XML_FILE)" != "com-core" ];then
        chgrp com-core $USAFM_XML_FILE
        if [ $? -eq 0 ];then
          apos_log "Group update on USAFM XML success"
        else
          apos_log "Group update on USAFM XML Failed"
        fi
      fi
      if [ "$(stat -c %a $USAFM_XML_FILE)" != "660" ];then
        chmod 660 $USAFM_XML_FILE
        if [ $? -eq 0 ];then
          apos_log "Permission update on USAFM XML success"
        else
          apos_log "Permission update on USAFM XML Failed"
        fi
      fi
    else
      if [ "$(stat -c %a $USAFM_XML_FILE)" != "777" ];then
        chmod 777 $USAFM_XML_FILE
        if [ $? -eq 0 ];then
          apos_log "Permission 777 update on USAFM XML success"
        else
          apos_log "Permission 777 update on USAFM XML Failed"
        fi
      fi 
    fi
    grep -q 'originalEventTime' "$USAFM_XML_FILE" &> /dev/null
    if [ $? -ne 0 ];then
      $CMD_SED -i '/<node>/i\ \t \t<originalEventTime>0</originalEventTime>' $USAFM_XML_FILE
      rCode=$?
      [ $rCode -eq 0 ] && apos_log "Upgrade of USAFM XML success"
    else
      apos_log "originalEventTime available in XML"
    fi
  else
    apos_log "usaFM file not found"
  fi
  sleep 1
done

apos_outro $0
exit $TRUE
