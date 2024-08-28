#!/bin/bash
##
# ------------------------------------------------------------------------
#     Copyright (C) 2014 Ericsson AB. All rights reserved.
# ------------------------------------------------------------------------
##
# Description:
#       Script used to change the APG43L software version.
#	Script works only if there is only one APG43L software version.
#	In case of more than two APG43L software versions the script shows an error.
##
##
# Changelog:
# - Dec 1 2014 - Fabrizio Paglia (XFABPAG)
#       First version.
##

#Exit codes
EXIT_SUCCESS=0
EXIT_FAILURE=1

#Constants
TRUE=$(true;echo $?)
FALSE=$(false;echo $?)
LOG_TAG="swu_fix_sw_version"

#Commands
CMD_LOGGER="/bin/logger"
CMD_IMMFIND="/usr/bin/immfind"
CMD_IMMLIST="/usr/bin/immlist"
CMD_IMMCFG="/usr/bin/immcfg"

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
        
        ${CMD_LOGGER} $prio -t $LOG_TAG "$message"
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
        
        ${CMD_LOGGER} $prio -t $LOG_TAG "$message"
}

#Input parameters
[[ $# -ne 2 ]] && {
	log_error "Wrong parameters number!"
	exit $EXIT_FAILURE
}
WANTED_PRODUCT_NUMBER="$1"
WANTED_PRODUCT_REVISION="$2"

#######################################################################
#                               MAIN                                  #
#######################################################################

# Get the current time
currentTime=$(date +"%Y-%m-%dT%T")

# Get the SwInventory
inventory=$($CMD_IMMFIND -c SwInventory)
[[ "$inventory" == "" ]] && inventory=$($CMD_IMMFIND -c CmwSwIMSwInventory)
# Get the SwM
swm=$($CMD_IMMFIND -c SwM)
[[ "$swm" == "" ]] && swm=$($CMD_IMMFIND -c CmwSwMSwM)

# Count APG43L software versions
numAPGSwVersions=$($CMD_IMMFIND | grep ^swVersionId=APG43L- | wc -l)

if [ $numAPGSwVersions -gt 2 ] ; then
	log_error "Unexpected software versions count!"
	exit $EXIT_FAILURE
fi

if [ $numAPGSwVersions -eq 1 ] ; then # Abormal upgrade scenario (change the sw version manually)
	if $CMD_IMMLIST -c SwVersion &> /dev/null ; then
		swVersionClass="SwVersion"
		productDataClass="ProductData"
		swVersionMainClass="SwVersionMain"
	else
		swVersionClass="CmwSwIMSwVersion"
		productDataClass="CmwSwIMProductData"
		swVersionMainClass="CmwSwMSwVersionMain"
	fi

	# Get the current swVersionDn
	currentSwVersionDn=$($CMD_IMMFIND | grep ^swVersionId=APG43L-)
	# Get the current product productNumber
	currentProductNumber=$(echo "$currentSwVersionDn" | awk -F'-' '{ print $2 }')
	# Get the current product productRevision
	currentProductRevision=$(echo "$currentSwVersionDn" | awk -F'-' '{ print $3 }' | awk -F',' '{ print $1 }')
	
	if [ "$currentProductNumber" == "$WANTED_PRODUCT_NUMBER" ] && [ "$currentProductRevision" == "$WANTED_PRODUCT_REVISION" ] ; then
		log "Software version already updated. Nothing to do!"
		exit $EXIT_SUCCESS
	fi
	
	# Get the swItem array
	swItemsArray=($($CMD_IMMLIST -a consistsOf "$currentSwVersionDn" | sed -r 's/^.{11}//' | awk -F ":" '{ for (i = 1;i <= NF;i++) { print $i } }' | tr '\n' ' '))
	
	# Create the new SwVersion
	newSwVersionDn="swVersionId=APG43L-$WANTED_PRODUCT_NUMBER-$WANTED_PRODUCT_REVISION,$inventory"
	newSwVersionAdminDataDn="id=administrativeData,$newSwVersionDn"
	log "Running $CMD_IMMCFG -c $swVersionClass -a timeOfInstallation="$currentTime" -a timeOfActivation="$currentTime" -a administrativeData=$newSwVersionAdminDataDn $newSwVersionDn"
	eval $CMD_IMMCFG -c $swVersionClass -a timeOfInstallation="$currentTime" -a timeOfActivation="$currentTime" -a administrativeData=$newSwVersionAdminDataDn $newSwVersionDn || {
		log_error "Failed to create SwVersion object [$newSwVersionDn]"
		exit $EXIT_FAILURE
	}
	
	for swItem in "${swItemsArray[@]}"; do
		log "Running $CMD_IMMCFG -a consistsOf+="$swItem" $newSwVersionDn"
	        eval $CMD_IMMCFG -a consistsOf+="$swItem" $newSwVersionDn || {
			log_error "Failed to append consistsOf data to SwVersion object [$newSwVersionDn]"
			exit $EXIT_FAILURE
		}
	done
	
	# Create the new SwVersion administrativeData
	attr="-a productName='APG43L' "
	attr+="-a productNumber='$WANTED_PRODUCT_NUMBER' "
	attr+="-a productRevision='$WANTED_PRODUCT_REVISION' "
	attr+="-a description='APG43L SW Version' "
	attr+="-a productionDate='$currentTime' "
	log "Running $CMD_IMMCFG -c $productDataClass "$attr" $newSwVersionAdminDataDn"
	eval $CMD_IMMCFG -c $productDataClass "$attr" $newSwVersionAdminDataDn || {
		log_error "Failed to create Administrative Data object [$newSwVersionAdminDataDn]"
		exit $EXIT_FAILURE
	}
	
	# Set active SwVersion
	log "Running $CMD_IMMCFG -a active+=$newSwVersionDn $inventory"
	eval $CMD_IMMCFG -a active+=$newSwVersionDn $inventory || {
		log_error "Failed to append to active attribute to object [$inventory]"
		exit $EXIT_FAILURE
	}
	
	# Create the new SwVersionMain
	newSwVersionMainDn="swVersionMainId=APG43L-$WANTED_PRODUCT_NUMBER-$WANTED_PRODUCT_REVISION,$swm"
	newSwVersionMainAdminDataDn="id=administrativeData,$newSwVersionMainDn"

	log "Running $CMD_IMMCFG -c $swVersionMainClass -a administrativeData=$newSwVersionMainAdminDataDn -a swVersion=$newSwVersionDn $newSwVersionMainDn"
	eval $CMD_IMMCFG -c $swVersionMainClass -a administrativeData=$newSwVersionMainAdminDataDn -a swVersion=$newSwVersionDn $newSwVersionMainDn || {
		log_error "Failed to create SwVersionMain object [$newSwVersionMainDn]"
		exit $EXIT_FAILURE
	}

	# Create the new SwVersionMain administrativeData
        attr="-a productName=APG43L "
	attr+="-a productNumber='$WANTED_PRODUCT_NUMBER' "
	attr+="-a productRevision='$WANTED_PRODUCT_REVISION' "
        attr+="-a description='APG43L SW Version' "
	attr+="-a productionDate='$currentTime' "
	log "Running $CMD_IMMCFG -c $productDataClass "$attr" $newSwVersionMainAdminDataDn"
	eval $CMD_IMMCFG -c $productDataClass "$attr" $newSwVersionMainAdminDataDn || {
		log_error "Failed to create Administrative Data object [$newSwVersionMainAdminDataDn]"
		exit $EXIT_FAILURE
	}

	# set SwVersionMain active
	log "Running $CMD_IMMCFG -a activeSwVersion+=$newSwVersionMainDn $swm"
	eval $CMD_IMMCFG -a activeSwVersion+=$newSwVersionMainDn $swm || {
		log_error "Failed to set active SwVersionMain to object [$swm]"
		exit $EXIT_FAILURE
	}
	
	# Delete old SwVersionMain
	swVersionMainDn="swVersionMainId=APG43L-$currentProductNumber-$currentProductRevision,$swm"
	log "Running $CMD_IMMCFG -d $swVersionMainDn"
	eval $CMD_IMMCFG -d $swVersionMainDn || {
		log_error "Failed to delete SwVersionMain object [$swVersionMainDn]"
		exit $EXIT_FAILURE
	}

	# delete SwVersion
	swVersionDn="swVersionId=APG43L-$currentProductNumber-$currentProductRevision,$inventory"
	log "Running $CMD_IMMCFG -d $swVersionDn"
	eval $CMD_IMMCFG -d $swVersionDn || {
		log_error "Failed to delete SwVersion object [$swVersionDn]"
		exit $EXIT_FAILURE
	}

	# unset active attrib in SwVersion
	log "Running $CMD_IMMCFG -a active-=$currentSwVersionDn $inventory"
	eval $CMD_IMMCFG -a active-=$currentSwVersionDn $inventory || {
		log_error "Failed to remove active attribute to object [$inventory]"
		exit $EXIT_FAILURE
	}
	
	# unset activeSwVersion in SwVersionMain
	log "Running $CMD_IMMCFG -a activeSwVersion-=$swVersionMainDn $swm"
	eval $CMD_IMMCFG -a activeSwVersion-=$swVersionMainDn $swm || {
		log_error "Failed to remove active SwVersionMain to object [$swm]"
		exit $EXIT_FAILURE
	}
fi
