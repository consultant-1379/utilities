#!/bin/sh

# This script is executed to check, whether any old
# (USER or SYSTEM) pso is present on the system, or not.

PSO_USER=brfPersistentStorageOwnerId=LDE_BRF_USER,brfParticipantContainerId=1
PSO_SYSTEM=brfPersistentStorageOwnerId=LDE_BRF_SYSTEM,brfParticipantContainerId=1

if ret=$(immfind $PSO_USER 2>/dev/null); then
	exit 0
else
	if ret=$(immfind $PSO_SYSTEM 2>/dev/null); then
		exit 0
	fi
fi

exit 1
