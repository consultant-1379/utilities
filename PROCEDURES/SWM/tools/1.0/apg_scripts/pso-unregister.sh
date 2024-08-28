#!/bin/bash

# if brfp is not installed, it is normal that we can't unregister
# our participant: exit without causing problems (rc=0)

rc=0

# Delete the configuration of the lde pso-s
BRF_PSO_CONFIG_FILE=/cluster/etc/pso-config.conf
rm -f $BRF_PSO_CONFIG_FILE

PSO_PATH=/opt/ericsson/brf/libexec/pso
SYSTEM_CFG=${PSO_PATH}/LDE-BRF-SYSTEM/lde-brf-system.cfg
USER_CFG=${PSO_PATH}/LDE-BRF-USER/lde-brf-user.cfg

if [ ! -f /opt/ericsson/brf/libexec/common/brf-participant-unregister ]; then
	exit 0
fi

if immfind | grep -i persistent | grep LDE_BRF_USER >/dev/null; then
	/opt/ericsson/brf/libexec/common/brf-participant-unregister $USER_CFG
	rc=$?
fi

if [ $rc -ne 0 ]; then
	exit $rc
fi

if immfind | grep -i persistent | grep LDE_BRF_SYSTEM >/dev/null; then
	/opt/ericsson/brf/libexec/common/brf-participant-unregister $SYSTEM_CFG
	rc=$?
fi

exit $rc
