#!/bin/bash
##
# ------------------------------------------------------------------------
#     Copyright (C) 2015 Ericsson AB. All rights reserved.
# ------------------------------------------------------------------------
##
# Name:
#      apg_cs_fix.sh 
# Description:
#       A script to remove multiple cs dns 
# Note:
# None.
##
# Changelog:
# - Tue Nov 22 2016 - Yeswanth Vankayala (XYESVAN)
# First version.

IMMFIND_CMD="/usr/bin/immfind"
CMD_GREP="/usr/bin/grep"

. /opt/ap/apos/conf/apos_common.sh

apos_intro $0

SAF_VERSION=$(immfind | grep -i ^safMemberCompType=safVersion=.*,safCompType=ERIC-APG_CS,safVersion=1.0.0,safSuType=ERIC-APG_SU_2N | cut -d = -f 3 | awk -F '\' '{print $1}')
     for i in $SAF_VERSION;
     do
          if [ $i != "CXC1371495_8-R1A04" ];then
              immcfg -d safMemberCompType=safVersion=$i\\,safCompType=ERIC-APG_CS,safVersion=1.0.0,safSuType=ERIC-APG_SU_2N
          fi
    done
    apos_log " Script successfully executed"

apos_outro $0
     
