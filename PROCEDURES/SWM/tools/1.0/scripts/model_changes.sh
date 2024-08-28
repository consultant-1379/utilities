#!/bin/bash
##
# ------------------------------------------------------------------------
#     Copyright (C) 2013 Ericsson AB. All rights reserved.
# ------------------------------------------------------------------------
##
# Description:
#       Script used to perform IMM model changes during software upgrade.
##
##
# Changelog:
# 2018-09-18 - XSRVAN  - Added changes for adopting to  APOS-COM_R1 model file
# - jan 26 2016 - Alessio Cascone (EALOCAE)
#       Removed comsa-mim-tool com_switchover command execution in procInitAction
# - jan 25 2016 - Alessio Cascone (EALOCAE)
#       Adapted to MDF models migration
# - jul 3 2014 - Fabrizio Paglia (XFABPAG)
#       Fixed to avoid problem with special chars (\) in immcfg regexs
# - jan 15 2013 - Fabrizio Paglia (XFABPAG)
#       Automatic log of instructions in models.info
# - jan 13/15 2013 - Fabrizio Paglia (XFABPAG)
#       Changed regular expressions to avoid problems with Windows new line
#       and CXCs in the format CXC1234567/8
# - dec 12 2013 - Fabrizio Paglia (XFABPAG)
#       Bug fixed in MP files comparison
# - nov 28 2013 - Fabrizio Paglia (XFABPAG)
#       Changed path to check for previous MP files
# - nov 27 2013 - Fabrizio Paglia (XFABPAG)
#       Inverted execution order of customized model change script
# - nov 26 2013 - Fabrizio Paglia (XFABPAG)
#       Bugs fixed in the support for customized model change script
#       Added check to skip any action if current version is the same you're upgrading to
# - nov 25 2013 - Fabrizio Paglia (XFABPAG)
#       Changes in the support for customized model change script
# - nov 21 2013 - Fabrizio Paglia (XFABPAG)
#       Changes in the support for customized model change script
# - nov 20 2013 - Fabrizio Paglia (XFABPAG)
#       Removed IMM class changes support
#       Added support for customized model change script
# - nov 15 2013 - Claudia Atteo (XCLAATT)
#       Added support for:
#       - MP change
# - nov 14 2013 - Fabrizio Paglia (XFABPAG)
#       First version
#       Supported model changes:
#       - IMM class add
#       - IMM class modify
##

#Exit codes
EXIT_SUCCESS=0
EXIT_FAILURE=1

#Input parameters
if [ $# -ne 2 ] ; then
	exit $EXIT_SUCCESS
fi

BUNDLE_NAME="$1"
PREVIOUS_NAME="$(echo "$2" | sed 's/safSmfBundle=//')"

if [ "$BUNDLE_NAME" == "$PREVIOUS_NAME" ] ; then
	exit $EXIT_SUCCESS
fi

#Constants
TRUE=$(true;echo $?)
FALSE=$(false;echo $?)
LOG_TAG="swu_model_changes"

BUNDLE_REPOSITORY="/cluster/storage/system/software/coremw/repository/"
PSO_CONFIG_DIR=$(cat /usr/share/pso/storage-paths/config)
HOME_COM_MODEL_DIR="${PSO_CONFIG_DIR}/com-apr9010443/etc/model"
HOME_COM_MODEL_FILE="${HOME_COM_MODEL_DIR}/model_file_list.cfg"
MP_FILES="/models/*_mp.xml"
PREVIOUS_MP_FILES="/*_mp.xml"
CUSTOM_SCRIPT="/models.info"
MODEL_FILE="APOS-COM_R1"
#Commands
CMD_LOGGER="/bin/logger"

#######################################################################
#                             Functions                               #
#######################################################################

#######################################################################
# function log($message);                                             #
#                                                                     #
# Arguments:                                                          #
# $message message to append to the system log                        #
#######################################################################
function log() {
        local message="${*:-notice}"
        local prio='-p user.notice'
        
        ${CMD_LOGGER} $prio $LOG_TAG "$message"
}

#######################################################################
# function log_error($message);                                       #
#                                                                     #
# Arguments:                                                          #
# $message error message to append to the system log                  #
#######################################################################
function log_error(){
        local message="${*:-error}"
        local prio='-p user.err'
        
        ${CMD_LOGGER} $prio $LOG_TAG "$message"
}

#######################################################################
#                               MAIN                                  #
#######################################################################
custom_script="$BUNDLE_REPOSITORY$BUNDLE_NAME$CUSTOM_SCRIPT"

mp_current_files="$BUNDLE_REPOSITORY$BUNDLE_NAME$MP_FILES"
mp_previous_files="$BUNDLE_REPOSITORY$PREVIOUS_NAME$MP_FILES"
base_sdp_name=$(echo $BUNDLE_NAME|awk -F"-CXC" '{print $1}')
mp_previous_list=/tmp/mp_previous.list
mp_current_list=/tmp/mp_current.list
exec_mp_update=$FALSE

touch $mp_previous_list 
touch $mp_current_list

ls $mp_previous_files > $mp_previous_list
ls $mp_current_files > $mp_current_list
if [ -s $mp_current_list ] ; then
	if [ -s $mp_previous_list ] ; then
		#diff $mp_current_list $mp_previous_list &> /dev/null
		current_list_lines=$(cat $mp_current_list | wc -l)
		previous_list_lines=$(cat $mp_previous_list | wc -l)
		if [ $current_list_lines -ne $previous_list_lines ]; then
			exec_mp_update=$TRUE
		else
			current_list=($(cat $mp_current_list | tr "\n" " "))
			count=0
			break_sig=$FALSE
			while [ $break_sig -ne $TRUE ]
				do
					while read line
					do
					diff $line ${current_list[$count]}  &> /dev/null
					res_diff=$?
					((count=$count +1))
					if [ $res_diff -ne 0 ] ; then
						exec_mp_update=$TRUE
						break_sig=$TRUE
					fi
					done < $mp_previous_list
				break_sig=$TRUE
			done
		fi
	else
		exec_mp_update=$TRUE
	fi
fi

if [ $exec_mp_update -eq $TRUE ] ; then 
	log "Updating MP files from ${PREVIOUS_NAME} to ${BUNDLE_NAME}"
	if [[ "${BUNDLE_NAME}" =~ "ERIC-APOS_OSCONFBIN" ]]; then
	cmw-model-modify ${BUNDLE_NAME} --mt COM_R1
	else
	cmw-model-modify ${BUNDLE_NAME} --mt $MODEL_FILE
	fi
	if [ $? -ne 0 ]; then
		log_error "Error modifying MP from ${PREVIOUS_NAME} to ${BUNDLE_NAME}"
		exit $EXIT_FAILURE
	fi
	if [[ "${BUNDLE_NAME}" =~ "ERIC-APOS_OSCONFBIN" ]]; then
	cmw-model-done --mt COM_R1
	else
	cmw-model-done --mt $MODEL_FILE
	fi
	if [ $? -ne 0 ]; then
		log_error "Error during cmw-model-done command execution"
		exit $EXIT_FAILURE
	fi
	
	log "Updated mp files from $PREVIOUS_NAME to $BUNDLE_NAME"
fi

rm $mp_previous_list &> /dev/null
rm $mp_current_list &> /dev/null

if [ -s "$custom_script" ] ; then
	previous_bundle_version=$(echo "$PREVIOUS_NAME" | awk -F'-' '{print $3"-"$4}')
	versions="$(cat -n $custom_script | grep -E '^(\s)*[0-9]*(\s)*VERSION(\s)*' | sort -r -n | tr -d '\r' | tr '\n' '*' | tr -d '\t ')"
	versions_array=(${versions//"*"/ })
	found_current_version=$FALSE
	i=0
	while [ $i -lt ${#versions_array[@]} ] && [ $found_current_version -eq $FALSE ] ; do
		version=$(echo "${versions_array[$i]}" | awk -F'VERSION:' '{print $2}' | tr '/' '_')
		if [ "$version" == "$previous_bundle_version" ] ; then
			found_current_version=$TRUE
			(( start_from_index = i + 1 ))
		fi
		(( i = i + 1 ))
	done
	if [ $found_current_version -eq $FALSE ] ; then
		log_error "Currently installed version $PREVIOUS_NAME not found in models.info"
		exit $EXIT_FAILURE
	fi
	i=$start_from_index
	while [ $i -lt ${#versions_array[@]} ] ; do
		row_number=$(echo "${versions_array[$i]}" | awk -F'VERSION:' '{print $1}')
		version_number=$(echo "${versions_array[$i]}" | awk -F'VERSION:' '{print $2}')
		version_has_instructions=$FALSE
		row_count=1
		while read line || [ -n "$line" ] ; do
			if [ $row_count -gt $row_number ] ; then
				if [ "$line" != "" ] ; then
					if [[ "$line" =~ ^(\s)*VERSION: ]] ; then
						break;
					elif [[ ! "$line" =~ ^# ]] ; then
						version_has_instructions=$TRUE
					fi
				fi
			fi
			(( row_count = $row_count + 1 ))
		done < $custom_script
		if [ $version_has_instructions -eq $TRUE ] ; then
			log "Executing model changes introduced in $base_sdp_name-$version_number"
			row_count=1
			while read -r line || [ -n "$line" ] ; do
				if [ $row_count -gt $row_number ] ; then
					if [ "$line" != "" ] ; then
						if [[ "$line" =~ ^(\s)*VERSION: ]] ; then
							break;
						elif [[ ! "$line" =~ ^# ]] ; then
							line=$(echo "$line" | tr -d '\r')
							log "Executing: $line"
							eval $line
							if [ $? -ne 0 ] ; then
								exit $EXIT_FAILURE							
							fi
						fi
					fi
				fi
				(( row_count = $row_count + 1 ))
			done < $custom_script
		fi
		(( i = i + 1 ))
	done
fi

exit $EXIT_SUCCESS

