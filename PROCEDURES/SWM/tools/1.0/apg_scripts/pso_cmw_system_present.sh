#!/bin/sh

# This script is executed to check, whether the old
# LDE_BRF_SYSTEM pso is present on the system, or not.

PSO_SYSTEM=brfPersistentStorageOwnerId=LDE_BRF_SYSTEM,brfParticipantContainerId=1

if ret=$(immfind $PSO_SYSTEM 2>/dev/null); then
	exit 0
else
	exit 1
fi
