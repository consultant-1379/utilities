#!/bin/bash

# This is a dirty, but unavoidable fix, which
# removes the 2 PSO objects, which were created,
# but never removed by the lde-brf-cmw binary.
#
# These calls also remove the child runtime objects,
# which were possibly created, when the user created
# backups on the system (it would be possible to
# remove these objects in the <removeFromImm> section
# in the campaign, but when child objects are present,
# the removal fails).
#
# Also, always return success:
# - when the objects are present, they are surely deleted
#   because of the '--unsafe' flag
# - when the objects are not present, no change happens to
#   the imm database

PSO_SYSTEM=brfPersistentStorageOwnerId=LDE_BRF_SYSTEM,brfParticipantContainerId=1
PSO_USER=brfPersistentStorageOwnerId=LDE_BRF_USER,brfParticipantContainerId=1

if ret=$(immfind $PSO_SYSTEM 2>/dev/null); then
	immcfg -d $PSO_SYSTEM --unsafe 2>/dev/null
	logger "INFO: Remove_old_pso (System): $?"
fi

if ret=$(immfind $PSO_USER 2>/dev/null); then
	immcfg -d $PSO_USER --unsafe 2>/dev/null
	logger "INFO: Remove_old_pso (User): $?"
fi

exit 0
