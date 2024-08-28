#!/bin/sh

# This script is executed to check, whether any new
# LDE_BRF_SCIPT PSO is present on the system, or not.

# The PSO objects in IMM are created and named by BRF-P, so
# checking their names might not be the best thing to do
# here on the long run. So instead, let's check if the
# lde-brf-script package is installed, or not.
# The pso-unregister.sh script will take care of the rest
# of the pso-presence checking.

if rpm -qi lde-brf-script > /dev/null || rpm -qi lde-brf-script-cxp9021148 > /dev/null; then
	exit 0
else
	exit 1
fi
