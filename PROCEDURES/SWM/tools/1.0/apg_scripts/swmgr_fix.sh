#!/bin/bash
##
# ------------------------------------------------------------------------
#     Copyright (C) 2013 Ericsson AB. All rights reserved.
# ------------------------------------------------------------------------
##
# Name:
#       swmgr_fix.sh
# Description:
#   A script to perform the sanity checks required for swmgr execution
#	  This script shall execute only on active node
##
# Usage:
##
# Changelog:
# - Wed 31 Jan 2017 - Mallikarjuna Rao (xmalrao)
#      First revision
##
#return codes
TRUE=$( true; echo $? )
FALSE=$( false; echo $? )

#other variables
user_file='/etc/passwd'
group_file='/etc/group'
USER='apgswmgr'
GROUP='apgsys'
swmgr_dir='/data/ext/swmgr'
permissions='765'
USER_MGMT_SCRIPT='/opt/ap/apos/bin/usermgmt/usermgmt'
USERADD="${USER_MGMT_SCRIPT} user add --global"
USERADDSLES11='/usr/sbin/useradd'
USERMODSLES11='/usr/sbin/usermod'
USERMOD="${USER_MGMT_SCRIPT} user modify"
shell_opt="--shell=/sbin/nologin"
usropt="-s /sbin/nologin "
src_g_name='SWPKGGRP'
src_sec_grp='system-nbi-data,apgsys,com-emergency,tsgroup'


function check_node_state(){
	local rCode

	#Get Node 1 Status
	NODE_1_STATE=$(amf-state siass ha safSISU=safSu=1\\,safSg=2N\\,safApp=ERIC-APG,safSi=AGENT,safApp=ERIC-APG | grep saAmfSISUHAState | awk -F'=' '{print $2}'| awk -F'(' '{print $1}')
	#Get Node 2 Status
	NODE_2_STATE=$(amf-state siass ha safSISU=safSu=2\\,safSg=2N\\,safApp=ERIC-APG,safSi=AGENT,safApp=ERIC-APG | grep saAmfSISUHAState | awk -F'=' '{print $2}'| awk -F'(' '{print $1}')

	CURRENT_NODE="$(cat /etc/cluster/nodes/this/name)"

	if ([[ "SC-2-1" = "$CURRENT_NODE" && "$NODE_1_STATE" = "ACTIVE" ]] || [[ "SC-2-2" = "$CURRENT_NODE" && "$NODE_2_STATE" = "ACTIVE" ]]);then
		rCode=1
	else
		rCode=0
	fi

	return $rCode
}

function create_user(){
	local suse_release=$(cat /etc/SuSE-release | grep VERSION  |awk '{print $3}')
	cat $user_file | grep $USER &>/dev/null
	if [ $? -ne 0 ]; then
		# 1. Add apgswmgr user
		if [ $suse_release == 11 ]; then
			echo "Yes SLES11"
			${USERADDSLES11} -P /cluster/etc $usropt -g $src_g_name -m $USER
		else
			${USERADD} $shell_opt --gname=$src_g_name --uname=$USER
		fi

		# If node is busy it might take time to reflect so sleep for 2 seconds
		sleep 2

		# 2. Now we are checking if this existing user is already a member of its corresponding group
		local config_user_gid=$(grep "^$USER:" /cluster/etc/passwd | awk -F: '{print $4}') #retrieving primary gid of this use
		local config_group_gid=$(grep "^$src_g_name:"  /cluster/etc/group | awk -F: '{print $3}') #retrieving gid of the group

		#checking if they donot match
		if [ "$config_user_gid" != "$config_group_gid" ]; then
			# The primary group for the current user does not match with the config file: modify it
			if [ $suse_release == 11 ]; then
				${USERMODSLES11} -P /cluster/etc $usropt -g $src_g_name $USER
    	else	
				${USERMOD} $shell_opt --gname=$src_g_name --uname=$USER
			fi
		fi

		# 3. Adding secondary groups to user
		if [ $suse_release == 11 ]; then
			${USERMODSLES11} -P /cluster/etc -G $src_sec_grp $USER
   	else 
			${USERMOD} --secgroups=$src_sec_grp --uname=$USER
		fi

	else
		id apgswmgr | grep com-emergency | grep tsgroup &>/dev/null
		if [ $? -ne 0 ]; then
			if [ $suse_release == 11 ]; then
      	${USERMODSLES11} -P /cluster/etc -G $src_sec_grp $USER
			else
				${USERMOD} --secgroups=$src_sec_grp --uname=$USER
			fi
		fi
	fi

	#unable to create the user. exit
	cat $user_file | grep $USER &>/dev/null
	if [ $? -ne 0 ]; then
		apos_abort "unable to create $USER"
	fi
}

function create_dir(){
	if [ ! -d $swmgr_dir ]; then
		mkdir $swmgr_dir
		chown $USER $swmgr_dir
		chgrp $GROUP $swmgr_dir
		chmod $permissions $swmgr_dir

	else
		ls -l $swmgr_dir | grep $USER
		[ $? -ne 0 ] && chown -R $USER $swmgr_dir
	fi

	#unable to create the directory. exit 
	if [ ! -d $swmgr_dir ]; then
		apos_abort "unable to create $swmgr_dir"
	fi
}

function invoke(){
	#1. Verify whether node is active or passive
	if check_node_state; then
		#Node is STANDBY, no need to execute script here
		exit $TRUE
	fi

	#2. Verify the existence of 'apgswmgr', if not create the user
	create_user

	#3. Verify the existence of '/data/ext/swmgr' directory, if not create the directory
	create_dir
}
# _____________________
#|    _ _   _  .  _    |
#|   | ) ) (_| | | )   |
#|_____________________|
# Here begins the "main" function...

#invoke the script 
invoke

# if we are here, command executed successfully.
exit $TRUE

