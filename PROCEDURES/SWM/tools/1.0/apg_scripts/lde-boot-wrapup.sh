#!/bin/bash
##
# ------------------------------------------------------------------------
#     Copyright (C) 2017 Ericsson AB. All rights reserved.
# ------------------------------------------------------------------------
##
# Name:
#       lde-boot-wrapup
# Description:
#       A script to change the boot label to "lde-boot" in boot file system and installation.conf files.
# Note:
#       None.
##
# Usage:
#       None.
##
# Output:
#       None.
##
# Changelog:
# - Thu Mar 15 2017  - Dharma Gondu (xdhatej)
#       First version.
##

# command-list
cmd_hwtype='/opt/ap/apos/conf/apos_hwtype.sh'

# script-wide variables
HW_TYPE=''
blkid_VAR=''
exit_fail=1

sed='/usr/bin/sed'
grep='/usr/bin/grep'
cat='/bin/cat'

function abort() {
    /bin/logger "ABORTING(lde-boot-wrapup): <"$1">"
    exit $exit_fail
}


# fetch hardware type
        [[ -x $cmd_hwtype ]] && HW_TYPE=$($cmd_hwtype)
        [ $? != 0 ] && abort "Error:Unable to retreive GEP version"
	if [[ "$HW_TYPE" == "GEP2"  || "$HW_TYPE" == "GEP1" ]]; then
        	blkid -L lde_boot &>/dev/null
		blkid_VAR=$?
                	if [ $blkid_VAR -eq 0 ];then
                        	e2label $(blkid -L lde_boot) lde-boot &>/dev/null
			elif [ $blkid_VAR -ne 2 ];then
				abort "Error: blkid command execution failed"
			fi
                

               	[ -r /cluster/etc/installation.conf ] && $grep lde_boot /cluster/etc/installation.conf &>/dev/null
                      	if [ $? == 0 ];then
                      		$sed -i 's/lde_boot/lde-boot/g' /cluster/etc/installation.conf &>/dev/null
                      	fi
		[ -r /boot/.installation.conf ] && $grep lde_boot /boot/.installation.conf &>/dev/null
			if [ $? == 0 ];then
                        	$sed -i 's/lde_boot/lde-boot/g' /boot/.installation.conf &>/dev/null
                      	fi
fi

