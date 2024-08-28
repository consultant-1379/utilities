#!/bin/bash
##
# ------------------------------------------------------------------------
#     Copyright (C) 2012 Ericsson AB. All rights reserved.
# ------------------------------------------------------------------------
##
# Name:
#      apg_libcli_extension.sh 
# Description:
#       A script to deploy libcli_subshell 
##
##
# Changelog:
# - Wed Jul 13 2016 - Yeshwanth Vankayala (xyesvan)
#   Updated script with dynamic generation of lib_cli_subshell
# - Mon Jun 20 2016 - Yeshwanth Vankayala (xyesvan)
#   First version.
##

if [ ! -r /opt/ap/apos/conf/apos_common.sh ];then
  /bin/logger "/opt/ap/apos/conf/apos_common.sh not found"
  apos_abort "apos_common.sh file not found"
fi

. /opt/ap/apos/conf/apos_common.sh

SOURCE_FOLDER="$(dirname "$(readlink -f $0)")"

#Check Source folder
if [ ! -d "$SOURCE_FOLDER" ];then
  apos_abort "$SOURCE_FOLDER folder does not exist"
fi

apos_intro $0


pushd '/opt/ap/apos/conf/' >/dev/null

if [ -x /opt/ap/apos/conf/apos_deploy.sh ]; then
  if [ -x /opt/com/util/com_config_tool ]; then
       DEST_DIR=$(/opt/com/util/com_config_tool location)
  else
       DEST_DIR='/storage/system/config/com-apr9010443'
  fi
  [ ! -d $DEST_DIR ] && apos_abort 1 'unable to retrieve COM configuration folder'
   
  # libcli_extension_subshell.cfg
  #generate libcli_extension_subshell.cfg
  $SOURCE_FOLDER/aposcfg_libcli_extension_subshell.sh

  if [ $? -ne 0 ]; then
    apos_abort 1 "\"apos_deploy.sh\" exited with non-zero return code"
  fi
  
  ./apos_deploy.sh --from $SOURCE_FOLDER/libcom_cli_agent.cfg --to $DEST_DIR/lib/comp/libcom_cli_agent.cfg
  if [ $? -ne 0 ]; then
    apos_abort 1 "\"apos_deploy.sh\" exited with non-zero return code"
  fi
   
  ./apos_deploy.sh --from $SOURCE_FOLDER/libcom_authorization_agent.cfg --to $DEST_DIR/lib/comp/libcom_authorization_agent.cfg
  if [ $? -ne 0 ]; then
    apos_abort 1 "\"apos_deploy.sh\" exited with non-zero return code"
  fi 

fi

popd &>/dev/null

apos_outro $0
exit 0
