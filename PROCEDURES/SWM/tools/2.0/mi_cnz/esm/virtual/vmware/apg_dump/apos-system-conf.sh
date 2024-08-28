#!/bin/bash
##
# Usage:
#       apos-system-conf.sh [early|late]
##

# Load the apos common functions.
. /opt/ap/apos/conf/apos_common.sh

is_boot_mounted() {
  /usr/bin/mountpoint --quiet /boot/
  local return_code=$?
  if [ $return_code -ne $TRUE ]; then
    echo "/boot not mounted --util repo"
  fi
  return $return_code
}

function mount_boot() {
  if /usr/bin/mount --label 'lde-boot' /boot; then
    echo "/boot correctly mounted --util repo"
  else
    echo "ABORT: failure while mounting /boot --util repo" >&2
    exit $FALSE
  fi
}

function umount_boot() {
  if /usr/bin/umount /boot; then
    echo "/boot correctly unmounted --util repo"
  else
    echo "ABORT: failure while unmounting /boot --util repo" >&2
  fi
}

echo "In apos-system-conf.sh --util repo"

# if /boot is not mounted, let's mount it (later we will unmount it).
# This is for the "early" case, that usually gets executed when /boot is not
# mounted.
was_boot_mounted=$TRUE
if ! is_boot_mounted; then
  was_boot_mounted=$FALSE
  mount_boot
fi

HW_TYPE=$(/opt/ap/apos/conf/apos_hwtype.sh)

stage=$1
if [[ ! "$stage" =~ ^(early)|(late)$ ]]; then
  echo "ABORT: unsupported value: $stage" >&2
  exit $FALSE
fi
if [[ "$HW_TYPE" == 'VM' ]]; then
  echo "hw_type is VM --util repo"
  if is_system_configuration_allowed; then
    echo "applying APG initial configuration --util repo"
    if [ ! -x /opt/ap/apos/conf/apos_system_conf.sh ]; then
      echo "ABORT: apos_system_conf.sh not found or not executable --util repo" >&2
      exit $FALSE
    fi
    /opt/ap/apos/conf/apos_system_conf.sh $stage
    return_code=$?
    if [ $return_code -ne $TRUE ] ; then
      echo "ABORT: failure while applying APG initial configuration --util repo (return code: $return_code)" >&2
      exit $return_code
    fi
  fi
	# WORK AROUND to handle Dynamic MAC in SWM 2.0
	if [ -f /boot/initrd.old ]; then 
		mv /boot/initrd.old /boot/initrd >&2 
	fi 
fi


# if /boot was not mounted when the present script started, let's unmount it.
if [ $was_boot_mounted -eq $FALSE ]; then
  echo "umount boot --util repo"
  umount_boot
fi

echo "APG initial configuration successfully completed --util repo"
exit $TRUE
