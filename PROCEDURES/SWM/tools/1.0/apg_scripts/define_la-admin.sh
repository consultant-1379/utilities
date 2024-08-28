#!/bin/bash
##
# ------------------------------------------------------------------------
#     Copyright (C) 2016 Ericsson AB. All rights reserved.
# ------------------------------------------------------------------------
##
# Name:
#       define_la-admin.sh
# Description:
#       A script to configure username and password of LA administrator SEC LA installation. 
#
# Note:
#       None.
##
# Output:
#       None.
##
# Changelog:
# 
# - Tue Mar 29 2016 - Franco D'Ambrosio (efradam)
#       First version.
##

# Load apos common functions
#. /opt/ap/apos/conf/apos_commos.sh


# Common commands
SED=`which sed`
GREP=`which grep`
CAT=`which cat`

function abort() {
  local ERROR_STRING=""

  if [ "$1" ]; then
    ERROR_STRING="ERROR: $1"
    echo "$ERROR_STRING"
  fi
  echo "Aborting"
  echo ""
  exit 1
}


function define_la_account() {
  # This function is used to define username and password of SEC LA administrator
  echo "Defining LA administrator account configuration file ..."
        
  local SEC_LA_CONFIG_PATH='/storage/system/config/sec-apr9010539/la/etc'
  local SEC_LA_CONFIG_FILE='la-admin.conf'
 
  if [ ! -d $SEC_LA_CONFIG_PATH ]; then
    mkdir -p $SEC_LA_CONFIG_PATH
    if [ $? -ne 0 ]; then
      abort "Failure while creating sec_la configuration folder $SEC_LA_CONFIG_PATH" 
    fi
  fi
  $CAT > $SEC_LA_CONFIG_PATH/$SEC_LA_CONFIG_FILE << EOF
ADMIN_USERID=laadmin
ADMIN_PASSWD=!\$6\$rZPQ75jIt6PoP\$/wPqicx1kQpfYvxGCXJCZEL//OpW7WhqaVy03ope5FNW6Yf9sSkUgYWgT87NXuK3zSFvH18N/lkVzpotNVb8p/
EOF
  if [ $? -ne 0 ];then
    abort "Failure while creating sec_la configuration file $SEC_LA_CONFIG_FILE"
  fi
  echo "LA administrator account configuration file defined!"
}

#                                              __    __   _______   _   __    _
#                                             |  \  /  | |  ___  | | | |  \  | |
#                                             |   \/   | | |___| | | | |   \ | |
#                                             | |\  /| | |  ___  | | | | |\ \| |
#                                             | | \/ | | | |   | | | | | | \   |
#                                             |_|    |_| |_|   |_| |_| |_|  \__|
#

#set -x

define_la_account
