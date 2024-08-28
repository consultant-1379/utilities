#!/bin/bash
##
# ------------------------------------------------------------------------
#     Copyright (C) 2016 Ericsson AB. All rights reserved.
# ------------------------------------------------------------------------
##
# Name:
#       apg_cacheduration_conf.sh
# Description:
#       A script to convert the cache duration value from seconds to days
##
# Changelog:
# - Mon May 09 2016 - Alessio Cascone (ealocae)
#       First version.
##

# Load the apos common functions.
current_dir="$(dirname "$(readlink -f $0)")"
. $current_dir/apg_common.sh


apos_intro $0

CACHE_DURATION_FILE="$(apos_create_brf_folder config)/cached_creds_duration"
CACHE_DURATION=$(apos_get_cached_creds_duration)
if [ -z $CACHE_DURATION ]; then
	apos_abort "Empty value found for cache duration"
fi

if [ $CACHE_DURATION -gt 0 ]; then
	NEW_CACHE_DURATION=$(($CACHE_DURATION / 86400))
	if [ -z $NEW_CACHE_DURATION ] || [ $NEW_CACHE_DURATION -le 0 ]; then
		NEW_CACHE_DURATION=1
	fi
	
	apos_log "Modifying cache duration value from '$CACHE_DURATION' to '$NEW_CACHE_DURATION'"
	echo $NEW_CACHE_DURATION > $CACHE_DURATION_FILE 
	if [ $? -ne 0 ];then
	  apos_abort "Failure while updating the '$CACHE_DURATION_FILE' file."
	fi
	
	kill_after_try 3 1 5 /usr/bin/immcfg  -a administrativeState=1 ldapAuthenticationMethodId=1 &> /dev/null
fi

apos_outro $0
exit $TRUE

# End of file
