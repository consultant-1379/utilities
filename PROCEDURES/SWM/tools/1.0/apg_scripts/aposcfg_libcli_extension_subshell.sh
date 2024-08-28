#!/bin/bash
##
# ------------------------------------------------------------------------
#     Copyright (C) 2016 Ericsson AB. All rights reserved.
# ------------------------------------------------------------------------
##
# Name:
#       apos_lib_subshell_config.sh
# Description:
#       A script to generate libcli_extension_subshell.cfg according to node configuration.
# Note:
#       To be executed only on one node.
##
# Usage:
#       None.
##
# Output:
#       None.
##
# Changelog:
# - Mon Jun 08 2016 - Avinash Gundlapally (xavigun)
#         First version.
##

# Load the apos common functions.
. /opt/ap/apos/conf/apos_common.sh

apos_intro $0
# Global variables
INCLUDE="INCLUDE"
EXCLUDE="EXCLUDE"
SOURCE_DIR="$(dirname "$(readlink -f $0)")"
HEADER_FILE="libcli_extension_subshell_header.conf"
TAIL_FILE="libcli_extension_subshell_tail.conf"
SOURCE_FILE_NAME="libcli_extension_subshell.conf"
DEST_FILE_NAME="libcli_extension_subshell.cfg"
CMD_PARMTOOL="$SOURCE_DIR/parmtool/parmtool"
IS_HIDDEN_TRUE="true"
COM="com"
TRUE=$( true; echo $? )
FALSE=$( false; echo $? )
CMD_ENTRY_MATCH="$SOURCE_DIR/entry_matches.sh"
TMP_DIR=''
EVALUATE="evaluate"
#-------------------------------------------------------------------------------------
# usage: function to update header part of libcli_extension_subshell.cfg
function update_lib_subshell_header() {
        cat  $SOURCE_DIR/$HEADER_FILE >> $TMP_DIR
        if [ $? -ne 0 ]; then
                return $FALSE
        else
                return $TRUE
        fi
}
#--------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------
#usage: function to update tail part of libcli_extension_subshell.cfg
function update_lib_subshell_tail() {
        cat  $SOURCE_DIR/$TAIL_FILE >> $TMP_DIR
        if [ $? -ne 0 ]; then
                return $FALSE
        else
                return $TRUE
        fi
}
#----------------------------------------------------------------------------------------
function update_lib_subshell(){
        #getting cmd name
        local CMD_NAME=$1
        #getting cmd description
        local CMD_DESC=$2
        #getting cmd executable path
        local CMD_EXECUTABLE_PATH=$3
        #getting ishidden value
        local CMD_IS_HIDDEN=$4
        echo -e "      <subshell>\n        <command>$CMD_NAME</command>\n        <description>$CMD_DESC</description>\n        <executable>$CMD_EXECUTABLE_PATH</executable>" >> $TMP_DIR
                                 if [ "$CMD_IS_HIDDEN" == "$IS_HIDDEN_TRUE" ]; then
                                        echo -e "        <hidden/>" >> $TMP_DIR
                                 fi
                                 echo -e "      </subshell>" >> $TMP_DIR
}

#---------------------------------------------------------------------------------------
#usage: function to update body part of libcli_extension_subshell.cfg
function update_lib_subshell_body_condtions() {
local errcode=$TRUE
local is_cmd_included=$FALSE
local ENTRY_MATCH_CONDITION=''
while read line
do
        #getting cmd name
        local CMD_NAME=$(echo $line | awk -F';' '{print $1}')
        #getting cmd description
        local CMD_DESC=$(echo $line | awk -F';' '{print $2}')
        #getting cmd executable path
        local CMD_EXECUTABLE_PATH=$(echo $line | awk -F';' '{print $3}')
	#getting ishidden value
        local CMD_IS_HIDDEN=$(echo $line | awk -F';' '{print $4}')
#       local CMD_CONDITIONS=$(echo $line | cut -d ";" -f 5-)
#               CMD_CONDITIONS=$(echo $CMD_CONDITIONS | sed 's/&/\\&/g')
                $CMD_ENTRY_MATCH $EVALUATE $CMD_NAME
        if [ $? -eq 0 ]; then
                update_lib_subshell "$CMD_NAME" "$CMD_DESC" "$CMD_EXECUTABLE_PATH" "$CMD_IS_HIDDEN"
        fi
done < $SOURCE_DIR/$SOURCE_FILE_NAME

}

#-------------------------------------------------------------------------------
#                                              __    __   _______   _   __    _
#                                             |  \  /  | |  ___  | | | |  \  | |
#                                             |   \/   | | |___| | | | |   \ | |
#                                             | |\  /| | |  ___  | | | | |\ \| |
#                                             | | \/ | | | |   | | | | | | \   |
#                                             |_|    |_| |_|   |_| |_| |_|  \__|
#
err_code=$TRUE
TMP_DIR=$(mktemp)
DEST_DIR='/opt/com'

[ ! -x $CMD_ENTRY_MATCH ] && apos_abort 1 "$CMD_ENTRY_MATCH not found or not executable"

#Updating lib_subshell header
        update_lib_subshell_header
        if [ $? -ne 0 ]; then
                err_code=$FALSE
        fi

#Updating lib_subshell body
        update_lib_subshell_body_condtions

#Updating lib_subshell_tail
        update_lib_subshell_tail
        if [ $? -ne 0 ]; then
                err_code=$FALSE
        fi
 #deploy libcli_extension_subshell.cfg
        /opt/ap/apos/conf/apos_deploy.sh --from $TMP_DIR --to $DEST_DIR/lib/comp/libcli_extension_subshell.cfg
        if [ $? -ne 0 ]; then
                apos_abort 1 "\"apos_deploy.sh\" exited with non-zero return code"
        fi

exit $err_code
#end of file
