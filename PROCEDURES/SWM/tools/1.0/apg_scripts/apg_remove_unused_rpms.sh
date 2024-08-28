#!/bin/bash
##
# ------------------------------------------------------------------------
#     Copyright (C) 2016 Ericsson AB. All rights reserved.
# ------------------------------------------------------------------------
##
# Name:
#       apg_remove_unused_rpms.h
# Description:
#       This script removes the unused RPMs that for an LDE issue are not
#       properly removed from the system. 
##
# Changelog:
# - Tue Aug 02 2016 - Alessio Cascone (ealocae)
#       First version.
##

# Load the apos common functions.
. /opt/ap/apos/conf/apos_common.sh

##### BEGIN: Common variables section
INSTALLED_RPMS_LIST=''
AVAILABLE_RPMS_LIST=''
##### END  : Common variables section

# Function to execute all the needed cleanup operation at script termination.
# Usage: cleanup
function cleanup() {
  if [ -r "$INSTALLED_RPMS_LIST" ]; then
    rm -f $INSTALLED_RPMS_LIST
  fi
  
  if [ -r "$AVAILABLE_RPMS_LIST" ]; then
    rm -f $AVAILABLE_RPMS_LIST
  fi
}

#                                              __    __   _______   _   __    _
#                                             |  \  /  | |  ___  | | | |  \  | |
#                                             |   \/   | | |___| | | | |   \ | |
#                                             | |\  /| | |  ___  | | | | |\ \| |
#                                             | | \/ | | | |   | | | | | | \   |
#                                             |_|    |_| |_|   |_| |_| |_|  \__|
#
apos_intro $0

# Prints error in case of unset variables
set -u

# Register a handler to execute any type of cleanup operations when the script exits
trap cleanup EXIT

# Create two temporary files, the first to store the list of the installed RPMs
# and the second to store the list of RPMs currently present on the system
INSTALLED_RPMS_LIST=$(mktemp -t $(basename $0)_XXXX)
AVAILABLE_RPMS_LIST=$(mktemp -t $(basename $0)_XXXX)

# Retrieve the list of the installed RPMs
cluster rpm --list --all | awk '{print $4}' | sort -u > $INSTALLED_RPMS_LIST
if [ $? -ne 0 ]; then
  apos_abort "Failed to retrieve the list of the installed RPMs."
fi

# Retrieve the list of the available RPMs (also including the unused ones)
find /cluster/rpms/ -mindepth 1 -maxdepth 1 -type f -exec basename {} \; > $AVAILABLE_RPMS_LIST
if [ $? -ne 0 ]; then
  apos_abort "Failed to retrieve the list of the available RPMs."
fi

# For each unused RPM, remove it from the /cluster/rpms folder
while read RPM
do
  RPM_FULL_PATH=/cluster/rpms/$RPM
  apos_log "Removing the unused RPM: $RPM_FULL_PATH"
  
  # Remove the unused RPM from the /cluster folder
  echo "rm -f $RPM_FULL_PATH"
  if [ $? -ne 0 ]; then
    apos_abort "Failed to remove the RPM '$RPM_FULL_PATH'."
  fi
done < <(comm -1 -3 $INSTALLED_RPMS_LIST $AVAILABLE_RPMS_LIST)

apos_outro $0
exit $TRUE

# End of file
