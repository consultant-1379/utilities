#!/bin/bash
##
# ------------------------------------------------------------------------
#     Copyright (C) 2011 Ericsson AB. All rights reserved.
# ------------------------------------------------------------------------
##
# Name:
#       remove_unused_apps.sh 
# Description:
#       A script to remove imm entries of not used blocks.
# Note:
#       None.
##
# Output:
#       None.
##
# Changelog:
# - Mon Mar 14 2016 - Yeswanth Vankayala (xyesvan)
#       First version.
##

CMW_REPO="cmw-repository-list"
CMD_GREP="/usr/bin/grep"
CMD_AWK="/usr/bin/awk"
CMD_SDP_REMOVE="cmw-sdp-remove"

function abort(){
        echo -e ${@:-"An error occurred. Exiting!"}
        exit 1
}

for entry in $($CMW_REPO | $CMD_GREP -i NOTUSED | $CMD_AWK -F ' ' '{print $1}');
do
          $CMD_SDP_REMOVE $entry
          [ $? -ne 0 ] && abort "failed to remove entry : $entry"
done

exit 0

