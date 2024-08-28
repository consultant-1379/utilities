#!/bin/bash 
##
# ------------------------------------------------------------------------
#     Copyright (C) 2015 Ericsson AB. All rights reserved.
# ------------------------------------------------------------------------
##
# Name:
#       apg_ldap_version.sh
# Description:
#       A script to update version attribute in LDAP MO to version 1 
# Note:
#       None.
##
# Changelog:
# - Wed Jul 27 2016 - Yeswanth Vankayala (xyesvan)
#       First Version
##
# Common variables
current_dir="$(dirname "$(readlink -f $0)")"
. $current_dir/apg_common.sh

apos_intro $0

kill_after_try 3 3 4 immcfg -a version=1 ericssonFilterId=1,ldapId=1,ldapAuthenticationMethodId=1
[ $? -ne 0 ] && abort "Ldap version change is failed"

apos_outro $0

# End of file
