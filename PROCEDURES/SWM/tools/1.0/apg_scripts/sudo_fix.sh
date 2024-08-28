#!/bin/bash
##
# ------------------------------------------------------------------------
#     Copyright (C) 2016 Ericsson AB. All rights reserved.
# ------------------------------------------------------------------------
##
# Name:
#       sudo_fix.sh
# Description:
#       A script for the sudoers fix 
##
##
# Changelog:
# - Tue Aug 30 2016 - Yeshwanth Vankayala (xyesvan)
#   First version.
##

if [ ! -r /opt/ap/apos/conf/apos_common.sh ];then
  /bin/logger "/opt/ap/apos/conf/apos_common.sh not found"
  apos_abort "apos_common.sh file not found"
fi

. /opt/ap/apos/conf/apos_common.sh

#Script exepect to receive in input the path where to copy 
SOURCE_FOLDER="$(dirname "$(readlink -f $0)")"
STORAGE_TYPE=$(get_storage_type)

#Check Source folder
if [ ! -d "$SOURCE_FOLDER" ];then
  apos_abort "$SOURCE_FOLDER folder does not exist"
fi

#Fetch  sudoers destination folder
DD_REPLICATION_TYPE=$(get_storage_type)
DESTNATION_FOLDER="/etc/sudoers.d"
if [ ! -d $DESTNATION_FOLDER ]; then
	mkdir -p $DESTNATION_FOLDER
else
	apos_log "sudoers.d folder already exist"
fi

# Deployment of sudoers file
pushd '/opt/ap/apos/conf/' >/dev/null
[ ! -x /opt/ap/apos/conf/apos_deploy.sh ] && apos_abort 1 '/opt/ap/apos/conf/apos_deploy.sh not found or not executable'

	./apos_deploy.sh --from "$SOURCE_FOLDER/sudoers" --to "/cluster/etc/sudoers" --exlo || apos_abort "\"apos_deploy.sh\" exited with non-zero return code"
	./apos_deploy.sh --from "$SOURCE_FOLDER/sudoers" --to "/etc/sudoers" || apos_abort "\"apos_deploy.sh\" exited with non-zero return code"

if /bin/ls /etc/sudoers.d/APG* &>/dev/null; then
	pushd '/opt/ap/apos/conf/' >/dev/null
	if [ "$STORAGE_TYPE" == "MD" ] ; then
		./apos_deploy.sh --from "$SOURCE_FOLDER/APG-tsgroup_md" --to "/etc/sudoers.d/APG-tsgroup"
		./apos_deploy.sh --from "$SOURCE_FOLDER/APG-comgroup_md" --to "/etc/sudoers.d/APG-comgroup"
	else
		./apos_deploy.sh --from "$SOURCE_FOLDER/APG-tsgroup_drbd" --to "/etc/sudoers.d/APG-tsgroup"
		./apos_deploy.sh --from "$SOURCE_FOLDER/APG-comgroup_drbd" --to "/etc/sudoers.d/APG-comgroup"
	fi
chmod 0440 /cluster/etc/sudoers /etc/sudoers $DESTNATION_FOLDER/APG-comgroup $DESTNATION_FOLDER/APG-tsgroup $DESTNATION_FOLDER/APG-tsadmin
	popd &>/dev/null
  exit 0
fi	
chmod 0440 /cluster/etc/sudoers /etc/sudoers $DESTNATION_FOLDER/APG-comgroup $DESTNATION_FOLDER/APG-tsgroup $DESTNATION_FOLDER/APG-tsadmin

NODE_ID=$(cat /etc/nodeid)
#Get Node Status
NODE_STATE=$(amf-state siass ha safSISU=safSu=$NODE_ID\\,safSg=2N\\,safApp=ERIC-APG,safSi=AGENT,safApp=ERIC-APG | grep saAmfSISUHAState | awk -F'=' '{print $2}'| awk -F'(' '{print $1}')

if [ "$NODE_STATE" == 'ACTIVE' ];then
  apos_log "[$NODE_STATE]: Stopping lde-synd service"
  service lde-syncd stop
  if [ $? -ne 0 ]; then
    apos_abort "Failed to stop lde-syncd servie on active side"
  fi
  apos_log "Stopped lde-syncd service successfully" 
  [ ! -x /opt/ap/apos/conf/apos_deploy.sh ] && apos_abort 1 '/opt/ap/apos/conf/apos_deploy.sh not found or not executable'
  
  pushd '/opt/ap/apos/conf/' >/dev/null
  ./apos_deploy.sh --from "$SOURCE_FOLDER/sudoers" --to "/cluster/etc/sudoers" --exlo || apos_abort "\"apos_deploy.sh\" exited with non-zero return code"
  popd &>/dev/null
  
  apos_log "Deployed default lde sudoers file"
 
elif [ "$NODE_STATE" == 'STANDBY' ];then
  apos_log "sudo_fix script is skipping as node is passive"
else
  apos_abort "ERROR: APG status not valid"
fi
chmod 0440 /cluster/etc/sudoers /etc/sudoers $DESTNATION_FOLDER/APG-comgroup $DESTNATION_FOLDER/APG-tsgroup $DESTNATION_FOLDER/APG-tsadmin
exit 0
