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
CURRENT_DIR="$(dirname "$(readlink -f $0)")"

if [ -r /opt/ap/apos/conf/apos_common.sh ]; then
 . /opt/ap/apos/conf/apos_common.sh
else
  echo '/opt/ap/apos/conf/apos_common.sh not found or not readable!' >&2
  exit 1
fi

apos_intro $0
os_version="$(cat /etc/*release| grep -P '^VERSION[[:space:]]*='| head -n 1| awk -F'=' '{print $2}'| tr -d [[:space:]])"
if [ "$os_version" == "11" ]; then
  $CURRENT_DIR/usaFm_upgrade.sh &
  if [ $? -eq 0 ];then
    apos_log "Launch of xml update script success"
  else
    apos_log "Launch of xml update script failed"
  fi
else
  apos_log "UsaFM patch not required on SLES12"
fi
apos_outro $0
exit $TRUE
