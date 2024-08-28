#!/bin/bash
##
# ------------------------------------------------------------------------
#     Copyright (C) 2016 Ericsson AB. All rights reserved.
# ------------------------------------------------------------------------
##
# Name:
#       apg_swpkg_folder_change.sh
# Description:
#      A script to change the permission, group and owner of existing file and folder
#	   under the path /data/opt/ap/internal_root/sw_package/APG/ in order to align it
#      with the SUGAR implementation
#
# Note:
#      -
##
# Output:
#       None.
##
# Changelog:
#
# - Sat Jun 14 2016 - Fabio Ronca (efabron)
#       First version.
##

# Load the apos common functions.
. /opt/ap/apos/conf/apos_common.sh


# The function will check for the script's prerequisites to be satisfied.
function sanity_check(){

        CMD_CHMOD=$( which chmod 2>/dev/null )
        [ -z "$CMD_CHMOD" ] && CMD_CHMOD='/usr/bin/chmod'

        CMD_CHGRP=$( which chgrp 2>/dev/null )
        [ -z "$CMD_CHGRP" ] && CMD_CHGRP='/usr/bin/chgrp'

        CMD_CHOWN=$( which chown 2>/dev/null )
        [ -z "$CMD_CHOWN" ] && CMD_CHOWN='/usr/bin/chown'
		
		CMD_MOUNTPOINT=$( which mountpoint 2>/dev/null )
        [ -z "$CMD_MOUNTPOINT" ] && CMD_MOUNTPOINT='/usr/bin/mountpoint'
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
path='/data/opt/ap/internal_root/sw_package/APG/'

$CMD_MOUNTPOINT /data/
if [ $? -eq 0 ]; then
  apos_log "Change permission of folders under $path"
  while read dir; do
    apos_log "Change permission of folder $dir"
    $CMD_CHMOD 2770 "$dir"
    [ $? -ne 0 ] && apos_log "ERROR: failed to change permission of folder $dir to 2777 "
    chgrp system-nbi-data "$dir"
    [ $? -ne 0 ] && apos_log "ERROR: failed to change group of folder $dir to system-nbi-data "
    chown com-core "$dir"
    [ $? -ne 0 ] && apos_log "ERROR: failed to change owner of folder $dir to com-core "
  done < <(find $path -type d)

  apos_log "Change permission of file under $path"
  while read file; do
    apos_log "Change permission of file $file"
    $CMD_CHMOD 660 "$file"
    [ $? -ne 0 ] && apos_log "ERROR: failed to change permission of file $file to 660 "
    chgrp system-nbi-data "$file"
    [ $? -ne 0 ] && apos_log "ERROR: failed to change group of file $file to system-nbi-data "
    chown com-core "$file"
    [ $? -ne 0 ] && apos_log "ERROR: failed to change owner of file $file to com-core "
  done < <(find $path -type f)  
else
  apos_log "Passive node, skip execution of script!!!"
fi
		
apos_outro $0
exit $TRUE

