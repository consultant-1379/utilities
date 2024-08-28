#!/bin/bash -u
##

# Load the apos common functions.
. /opt/ap/apos/conf/apos_common.sh

GEP_PREFIX='GEP'
VM='VM'
VERBOSE=''

CACHE_DIR="/dev/shm/"
CACHE_FILE="${CACHE_DIR}/apos_hwtype.cache"
CACHE_FILE_VERBOSE="${CACHE_DIR}/apos_hwtype_verbose.cache"
CACHE_FILE_OWNER="root"
CACHE_FILE_GROUP="root"
CACHE_FILE_PERMISSIONS="644"

ROJ_DB_FILE="/opt/ap/apos/conf/hwtype.dat"

# Common functions
function usage() {
	echo 'apos_hwtype.sh'
	echo 'A script to detect the current hardware revision.'
	echo
	echo 'Usage:    apos_hwtype.sh [--verbose|-V]'	
	echo	
}

function verbose_gep_detect() {
	local ROJ=$( dmidecode -s baseboard-product-name | tr '[:upper:]' '[:lower:]'|sed -e "s/ //g" )
   	if [ -z "$ROJ" ]; then
   		ROJ=$( eri-ipmitool gp | grep ROJ | tr '[:upper:]' '[:lower:]' | awk '{print $3,$4,$5}' |sed -e "s/ //g" )
   	fi
   	if [ -z "$ROJ" ]; then
       	apos_abort $FALSE 'unable to retrieve the ROJ code'
   	else
      SPECIFIC_HW_TYPE=$(cat $ROJ_DB_FILE | grep -i $ROJ | sed 's@.*;@@g')
      if [ -z "$SPECIFIC_HW_TYPE" ]; then
        apos_abort $FALSE "Hardware $ROJ not supported"
      fi
      MANUFACTURER="system-manufacturer=$MANUFACTURER"
      ROJ="baseboard-product-name=$ROJ"
      SPECIFIC_HW_TYPE="hw-type=$SPECIFIC_HW_TYPE"
      echo "$MANUFACTURER" >${CACHE_FILE_VERBOSE}
      echo "$ROJ" >>${CACHE_FILE_VERBOSE}
      echo "$SPECIFIC_HW_TYPE" >>${CACHE_FILE_VERBOSE}
      echo "$MANUFACTURER" 
      echo "$ROJ" 
      echo "$SPECIFIC_HW_TYPE" 
   	fi
   	return 0
}

function gep_detect() {
	ROJ=$( dmidecode -s baseboard-product-name | tr '[:upper:]' '[:lower:]'|sed -e "s/ //g" )	
	if [ -z "$ROJ" ]; then
		ROJ=$( eri-ipmitool gp | grep ROJ | tr '[:upper:]' '[:lower:]' | awk '{print $3,$4,$5}' |sed -e "s/ //g" )
	fi
	if [ -z "$ROJ" ]; then
		apos_abort 'unable to retrieve the ROJ code'
	else
		GEP_TYPE=$(echo "$ROJ" | sed 's@.*/@@g')
		HW_TYPE="$GEP_PREFIX${GEP_TYPE:0:1}"
		echo "$HW_TYPE" >${CACHE_FILE}
		echo "$HW_TYPE"
	fi
 	return 0
}

function identify(){
    MANUFACTURER=$( dmidecode -s system-manufacturer | tr '[:upper:]' '[:lower:]' )
    if [ -z "$MANUFACTURER" ]; then
      apos_abort 'no board manufacturer information found'
    else
        case "$MANUFACTURER" in
            *vmware*|*openstack*|*innotek*|*eri-adk*)
                if [ "$VERBOSE" ]; then echo "system-manufacturer=$MANUFACTURER"; fi
                HW_TYPE="$VM"
                echo "$VM" >${CACHE_FILE}
                if [ "$VERBOSE" ]; then HW_TYPE="hw-type=$HW_TYPE"; fi
                echo "$HW_TYPE"
            ;;

            *bochs*)
                if [ "$VERBOSE" ]; then echo "system-manufacturer: \"$MANUFACTURER\""; fi
                HW_TYPE="$VM"
                echo "$VM" >${CACHE_FILE}
                if [ "$VERBOSE" ]; then HW_TYPE="hw-type: \"$HW_TYPE\""; fi
                echo "$HW_TYPE"
            ;;

            *ericsson*)
                if [ "$VERBOSE" ]; then
                  verbose_gep_detect
                else
                  gep_detect
                fi;
            ;;
            *)
                #checking for different variants of openstack, 
                #if systemd-detect-virt detects any valid   hypervisor
                #then hardware is considered as virtual on openstack platform
                local VIRT_ENV=''
                VIRT_ENV=$( systemd-detect-virt  )
                [[ -z "$VIRT_ENV" || "$VIRT_ENV" == "none" ]] &&  apos_abort "unsupported manufacturer found: \"$MANUFACTURER\" "

                if [[ "$VIRT_ENV" == "qemu" || "$VIRT_ENV" == "kvm" ]]; then
                  apos_log "openstack platform is detected on hypervisor $VIRT_ENV"
                else
                  apos_log "detected hypervisor $VIRT_ENV, proceeding by assuming the underlying platform as openstack"
                fi

                if [ "$VERBOSE" ]; then echo "system-manufacturer=openstack foundation"; fi
                HW_TYPE="$VM"
                echo "$VM" >${CACHE_FILE}
                if [ "$VERBOSE" ]; then HW_TYPE="hw-type=$HW_TYPE"; fi
                echo "$HW_TYPE"
            ;;
        esac
    fi


    if [ "$VERBOSE" ]; then
      if [ -w "${CACHE_FILE_VERBOSE}" ]; then
        /bin/chown ${CACHE_FILE_OWNER} ${CACHE_FILE_VERBOSE}
        /bin/chgrp ${CACHE_FILE_GROUP} ${CACHE_FILE_VERBOSE}
        /bin/chmod ${CACHE_FILE_PERMISSIONS} ${CACHE_FILE_VERBOSE}
      fi
    else
      if [ -w "${CACHE_FILE}" ]; then
        /bin/chown ${CACHE_FILE_OWNER} ${CACHE_FILE}
        /bin/chgrp ${CACHE_FILE_GROUP} ${CACHE_FILE}
        /bin/chmod ${CACHE_FILE_PERMISSIONS} ${CACHE_FILE}
      fi
    fi
}

# Main
if [ $# -gt 0 ]; then
	if [[ "$1" == "-V" || "$1" == "--verbose" ]]; then
		VERBOSE=$TRUE
	else
		usage
		exit $FALSE
	fi
fi

if [ "$VERBOSE" ]; then
	if [ -r "${CACHE_FILE_VERBOSE}" ]; then
   		OUT="$(cat $CACHE_FILE_VERBOSE)"
       	if [ -n "$OUT" ]; then
       		echo "$OUT"
          exit $TRUE
        fi
  fi
else
  if [ -r "${CACHE_FILE}" ]; then
    HW_TYPE="$(cat $CACHE_FILE)"
    if [ -n "${HW_TYPE}" ]; then
      echo "$HW_TYPE"
      exit $TRUE
		fi
	fi
fi

identify

exit $TRUE

# End of file
