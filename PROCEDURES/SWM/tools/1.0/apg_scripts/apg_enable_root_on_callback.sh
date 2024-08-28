#!/bin/bash
##
# ------------------------------------------------------------------------
#     Copyright (C) 2016 Ericsson AB. All rights reserved.
# ------------------------------------------------------------------------
##
# Name:
#       apg_enable_root_on_callback.sh
# Description:
#       A script to enebale root privileges for execution 
#       of callback scripts
# Note:
#       To remove when TR HU84292 will be fixed!!!
##
# Output:
#       None.
##
# Changelog:
# 
# - Sat May 14 2016 - Fabio Ronca (efabron)
#       First version.
##

# Load the apos common functions.
. /opt/ap/apos/conf/apos_common.sh

FILE_TO_PATCH='/etc/sudoers.d/cmw-required-cmds'
SCRIPT_TO_EXECUTE='apg_migrate_apache2_configuration.sh'
SCRIPT_TO_EXECUTE_2='apg_activate_manage_gids.sh'
SCRIPT_TO_EXECUTE_3='apg_local_users_migration.sh'
SCRIPT_TO_EXECUTE_4='apg_authorization_cache_removal.sh'
SCRIPT_TO_EXECUTE_5='usaFm_launch.sh'
SCRIPT_TO_EXECUTE_6='apg_set_primary_drbd0.sh'

# The function will check for the script's prerequisites to be satisfied.
function sanity_check(){
 
    CMD_SED=$( which sed 2>/dev/null )
	[ -z "$CMD_SED" ] && CMD_SED='/usr/bin/sed'
	
	CMD_GREP=$( which grep 2>/dev/null )
	[ -z "$CMD_GREP" ] && CMD_GREP='/usr/bin/grep'
	
	CMD_CAT=$( which cat 2>/dev/null )
	[ -z "$CMD_CAT" ] && CMD_CAT='/usr/bin/cat'

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
SCRIPT_PATH=$(dirname $0)

apos_log "Patch the $FILE_TO_PATCH file to execute the script ${SCRIPT_TO_EXECUTE} as root in callback"
$CMD_SED -i -r "/\/usr\/bin\/pkill,.*/ a\\\t\t\t\t\t${SCRIPT_PATH}/${SCRIPT_TO_EXECUTE}, \\\\" $FILE_TO_PATCH
[ $? -ne 0 ] && apos_abort "ERROR: Unable to patch file $FILE_TO_PATCH"

apos_log "Patch the $FILE_TO_PATCH file to execute the script ${SCRIPT_TO_EXECUTE_2} as root in callback"
$CMD_SED -i -r "/\/usr\/bin\/pkill,.*/ a\\\t\t\t\t\t${SCRIPT_PATH}/${SCRIPT_TO_EXECUTE_2}, \\\\" $FILE_TO_PATCH
[ $? -ne 0 ] && apos_abort "ERROR: Unable to patch file $FILE_TO_PATCH"

apos_log "Patch the $FILE_TO_PATCH file to execute the script ${SCRIPT_TO_EXECUTE_3} as root in callback"
$CMD_SED -i -r "/\/usr\/bin\/pkill,.*/ a\\\t\t\t\t\t${SCRIPT_PATH}/${SCRIPT_TO_EXECUTE_3}, \\\\" $FILE_TO_PATCH
[ $? -ne 0 ] && apos_abort "ERROR: Unable to patch file $FILE_TO_PATCH"

apos_log "Patch the $FILE_TO_PATCH file to execute the script ${SCRIPT_TO_EXECUTE_4} as root in callback"
$CMD_SED -i -r "/\/usr\/bin\/pkill,.*/ a\\\t\t\t\t\t${SCRIPT_PATH}/${SCRIPT_TO_EXECUTE_4}, \\\\" $FILE_TO_PATCH
[ $? -ne 0 ] && apos_abort "ERROR: Unable to patch file $FILE_TO_PATCH"

apos_log "Patch the $FILE_TO_PATCH file to execute the script ${SCRIPT_TO_EXECUTE_5} as root in callback"
$CMD_SED -i -r "/\/usr\/bin\/pkill,.*/ a\\\t\t\t\t\t${SCRIPT_PATH}/${SCRIPT_TO_EXECUTE_5}, \\\\" $FILE_TO_PATCH
[ $? -ne 0 ] && apos_abort "ERROR: Unable to patch file $FILE_TO_PATCH"

apos_log "Patch the $FILE_TO_PATCH file to execute the script ${SCRIPT_TO_EXECUTE_6} as root in callback"
$CMD_SED -i -r "/\/usr\/bin\/pkill,.*/ a\\\t\t\t\t\t${SCRIPT_PATH}/${SCRIPT_TO_EXECUTE_6}, \\\\" $FILE_TO_PATCH
[ $? -ne 0 ] && apos_abort "ERROR: Unable to patch file $FILE_TO_PATCH"




apos_outro $0
exit $TRUE
