#!/bin/bash

# if brfp is not installed, it is normal that we can't register
# our participant: exit without causing problems (rc=0)

rc=0

if [ $# -ne 3 ]; then
	exit 1
fi

PSO_TYPE=$1
REBOOT_USER=$2
REBOOT_SYSTEM=$3

# Save the configuration for the rpm postinstall scriptlet
BRF_PSO_CONFIG_FILE=/cluster/etc/pso-config.conf
echo "$PSO_TYPE $REBOOT_USER $REBOOT_SYSTEM" > $BRF_PSO_CONFIG_FILE

PSO_PATH=/opt/ericsson/brf/libexec/pso
SYSTEM_CFG=${PSO_PATH}/LDE-BRF-SYSTEM/lde-brf-system.cfg
USER_CFG=${PSO_PATH}/LDE-BRF-USER/lde-brf-user.cfg

# NOTE: Because of a bug in brf-participant-register, now it
# works only with calling the register script with 1 parameter!

if [ "$PSO_TYPE" = "USER" -o "$PSO_TYPE" = "BOTH" ]; then
	sed -i "s/\$reboot/$REBOOT_USER/g" $USER_CFG
	if [ -f /opt/ericsson/brf/libexec/common/brf-participant-register ]; then
		/opt/ericsson/brf/libexec/common/brf-participant-register $USER_CFG
		rc=$?
		if [ $rc -eq 4 ]; then
			logger -t $(basename $0) "Recieved (and ignoring) a timeout from BRFp (rc=4)."
			rc=0
		fi
	fi
fi

if [ $rc -ne 0 ]; then
	exit $rc
fi

if [ "$PSO_TYPE" = "SYSTEM" -o "$PSO_TYPE" = "BOTH" ]; then
	sed -i "s/\$reboot/$REBOOT_SYSTEM/g" $SYSTEM_CFG
	if [ -f /opt/ericsson/brf/libexec/common/brf-participant-register ]; then
		/opt/ericsson/brf/libexec/common/brf-participant-register $SYSTEM_CFG
		rc=$?
		if [ $rc -eq 4 ]; then
			logger -t $(basename $0) "Recieved (and ignoring) a timeout from BRFp (rc=4)."
			rc=0
		fi
	fi
fi

exit $rc
