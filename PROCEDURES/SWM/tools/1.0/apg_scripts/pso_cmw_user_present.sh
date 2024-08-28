#!/bin/sh

# This script is executed to check, whether the old
# LDE_BRF_USER pso is present on the system, or not.

PSO_USER=brfPersistentStorageOwnerId=LDE_BRF_USER,brfParticipantContainerId=1

if ret=$(immfind $PSO_USER 2>/dev/null); then
	exit 0
else
	exit 1
fi
