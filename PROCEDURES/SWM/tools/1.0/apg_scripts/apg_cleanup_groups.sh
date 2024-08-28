#!/bin/bash
##
# ------------------------------------------------------------------------
#     Copyright (C) 2012 Ericsson AB. All rights reserved.
# ------------------------------------------------------------------------
##
# Name:
#       cleanup_groups
# Description:
#       A script to set the cleanup old groups in the cluster.
# Note:
#	None.
##
# Usage:
#	None.
##
# Output:
#       None.
##
# Changelog:
# - Thu May 19 2011 - Antonio Buonocunto (eanbuon)
#       First version.
##

# Load the apos common functions.
. /opt/ap/apos/conf/apos_common.sh

apos_intro $0

# Variables
FILE="/etc/group"
GROUPS_LIST="apg-local SystemAdministrator SystemSecurityAdministrator SystemReadOnly EricssonSupport CpRole0 CpRole1 CpRole2 CpRole3 CpRole4 CpRole5 CpRole6 CpRole7 CpRole8 CpRole9 CpRole10 CpRole11 CpRole12 CpRole13 CpRole14 CpRole15"

USERMGMT='/opt/ap/apos/bin/usermgmt/usermgmt'

for GROUP in $GROUPS_LIST;do
 /usr/bin/getent group $GROUP &> /dev/null
 if [ $? -eq 0 ];then
   apos_log "Deleting group $GROUP"
   $USERMGMT "group delete --gname=$GROUP"
   if [ $? -ne 0 ];then
     apos_log "Failure while deleting group $GROUP"
   else
     apos_log "Group $GROUP successfully deleted."
   fi
 else
   apos_log "Group $GROUP already deleted."
 fi 
done

apos_outro $0
exit $TRUE

# End of file
