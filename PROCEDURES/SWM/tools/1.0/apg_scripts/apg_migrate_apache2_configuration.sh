#!/bin/bash
##
# ------------------------------------------------------------------------
#     Copyright (C) 2016 Ericsson AB. All rights reserved.
# ------------------------------------------------------------------------
##
# Name:
#       apg_migrate_apache2_configuration.sh
# Description:
#      A script to migrate the GNSH configuration according SLES12 syntax 
#       
# Note:
#      -
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

SCRIPT_PATH=$(dirname $0)
HTTP_CONFIGURATION_FILE='http_config_file'
HTTP_CONFIGURATION_FILE_PATH=''
SCRIPT_TO_EXECUTE='httpmgr_patched.sh'
HOST_TO_CONNECT=''

# The function will check for the script's prerequisites to be satisfied.
function sanity_check(){
 	
	CMD_CAT=$( which cat 2>/dev/null )
	[ -z "$CMD_CAT" ] && CMD_CAT='/usr/bin/cat'
	
	CMD_SSH=$( which ssh 2>/dev/null )
	[ -z "$CMD_SSH" ] && CMD_CAT='/usr/bin/ssh'
	
	CMD_GREP=$( which grep 2>/dev/null )
	[ -z "$CMD_GREP" ] && CMD_GREP='/usr/bin/grep'
	
	CMD_HEAD=$( which head 2>/dev/null )
	[ -z "$CMD_HEAD" ] && CMD_HEAD='/usr/bin/head'
	
	CMD_AWK=$( which awk 2>/dev/null )
	[ -z "$CMD_AWK" ] && CMD_AWK='/usr/bin/awk'
	
	CMD_TR=$( which tr 2>/dev/null )
	[ -z "$CMD_TR" ] && CMD_TR='/usr/bin/tr'

}


function get_storage_config_paths() {
    local config_path=$(cat /usr/share/pso/storage-paths/config)
        
    [ -z "$config_path" ] && abort "unable to read pso storage path" 
    HTTP_CONFIGURATION_FILE_PATH="$config_path/apos"
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

get_storage_config_paths

if [ -f "${HTTP_CONFIGURATION_FILE_PATH}/${HTTP_CONFIGURATION_FILE}" ]; then
    apos_log "Migrate the apache configuration files to SLES12 format"

    os_version=$($CMD_CAT /etc/*release| $CMD_GREP -P '^VERSION[[:space:]]*='| $CMD_HEAD -n 1| $CMD_AWK -F'=' '{print $2}'| $CMD_TR -d [[:space:]])
    [ -z $os_version ] && apos_abort "ERROR: Unable to determinate the OS version installed."
    if [ "$os_version" == "11" ]; then
        HOST_TO_CONNECT=$($CMD_CAT /etc/cluster/nodes/peer/hostname)
    elif [ "$os_version" == "12" ]; then 
        HOST_TO_CONNECT=$($CMD_CAT /etc/cluster/nodes/this/hostname) 
    else
        apos_abort "ERROR: OS Version: $os_version NOT valid. " 
    fi

    [ -z $HOST_TO_CONNECT ] && apos_abort "ERROR: Unable to determinate the node where execute the script."
    apos_log "Execute the script ${SCRIPT_PATH}/${SCRIPT_TO_EXECUTE} on node $HOST_TO_CONNECT "
    $CMD_SSH $HOST_TO_CONNECT ${SCRIPT_PATH}/${SCRIPT_TO_EXECUTE} -c /cluster/storage/system/config/apos/http_config_file
    [ $? -ne 0 ] && apos_abort "ERROR: Unable to execute the patched HTTPMGR on node $HOST_TO_CONNECT"
	
else
  apos_log "Migrate of apache configuration files skipped!!!"
fi

apos_outro $0
exit $TRUE
