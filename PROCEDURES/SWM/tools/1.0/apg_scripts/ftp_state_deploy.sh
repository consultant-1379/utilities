#!/bin/bash

# ------------------------------------------------------------------------
#     Copyright (C) 2015 Ericsson AB. All rights reserved.
# ------------------------------------------------------------------------
##
# Name:
#       ftp_state_deploy.sh
# Description:
#       A script to deploy ftp status file in cluster location
# Note:
#       None.
##
# Usage:
#       None.
##
# Output:
#       None.
##
# Changelog:#
#     - Aug 14 2015 - Dharma Teja (XDHATEJ)
#       First version.
##


if [ -r /opt/ap/apos/conf/apos_common.sh ];then
  . /opt/ap/apos/conf/apos_common.sh
else
  /bin/logger "/opt/ap/apos/conf/apos_common.sh not found"
  exit 1
fi

pushd '/opt/ap/apos/conf/' >/dev/null
if [ -x /opt/ap/apos/conf/apos_deploy.sh ]; then
 DEST_DIR=$(apos_create_brf_folder config)
 [ ! -d $DEST_DIR ] && apos_abort 1 'unable to retrieve ftpstate configuration folder'
 ftpstate_file_temp='/opt/ap/apos/conf/apos_ftp_state.conf'
 
 if [ -e $DEST_DIR/ftp_state.conf ]; then
	/bin/logger "$DEST_DIR/ftp_state.conf already exists....exiting"
 else 
	if [ -f $ftpstate_file_temp ];then
		MESSAGE=$(./apos_deploy.sh --from /opt/ap/apos/conf/apos_ftp_state.conf --to $DEST_DIR/ftp_state.conf 2>&1)
		if [ $? -ne 0 ]; then
			apos_abort 1 "\"apos_deploy.sh\" exited with non-zero return code. Error: \"${MESSAGE}\""
		fi
		else
			apos_abort 1 'unable to retrieve ftpstate configuration file'
		fi
  fi
else
  apos_abort 1 '/opt/ap/apos/conf/apos_deploy.sh not found or not executable'
fi
popd &>/dev/null

