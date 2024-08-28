#!/bin/bash
##
# ------------------------------------------------------------------------
#     Copyright (C) 2016 Ericsson AB. All rights reserved.
# ------------------------------------------------------------------------
##
# Name:
#       apg_unlock_sec_sg.sh
# Description:
#       A script to modify unlock the Sg of SEC (sec-Acs)
#
# Note:
#       None.
##
# Output:
#       None.
##
# Changelog:
#
##

# Load the apos common functions.
. /opt/ap/apos/conf/apos_common.sh

# The function will check for the script's prerequisites to be satisfied.
function sanity_check(){

    CMD_GREP=$( which grep 2>/dev/null )
        [ -z "$CMD_GREP" ] && CMD_GREP='/usr/bin/grep'


}

#                                              __    __   _______   _   __    _
#                                             |  \  /  | |  ___  | | | |  \  | |
#                                             |   \/   | | |___| | | | |   \ | |
#                                             | |\  /| | |  ___  | | | | |\ \| |
#                                             | | \/ | | | |   | | | | | | \   |
#                                             |_|    |_| |_|   |_| |_| |_|  \__|
#

apos_intro $0

sanity_check

#unlock-in sec acs
amf-adm unlock-in safSg=NoRed,safApp=ERIC-SecAcs
[ $? -ne 0 ] && apos_abort "ERROR: unlock-in of SG safSg=NoRed,safApp=ERIC-SecAcs is failed"
amf-adm unlock safSg=NoRed,safApp=ERIC-SecAcs
[ $? -ne 0 ] && apos_abort "ERROR: unlock of SG safSg=NoRed,safApp=ERIC-SecAcs is failed"




apos_outro $0
exit $TRUE

