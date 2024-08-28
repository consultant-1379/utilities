#!/bin/bash -ux
##
# ------------------------------------------------------------------------
#     Copyright (C) 2012 Ericsson AB. All rights reserved.
# ------------------------------------------------------------------------
##
# Name:
#       apos_common.sh
# Description:
#       A script to define common functions for apos configuration scripts.
# Note:
#	None.
##
# Usage:
#	Insert the following line in your script in order to make the functions
#	contained in this file available within your script:
#	# Load the apos common functions.
#	. /opt/ap/apos/conf/apos_common.sh
##
# Output:
#       None.
##
# Changelog:
# - Mon Dec 30 2019 - Pratap Reddy (xpraupp)
#   IPv6 impacts for virtual 
# - Tue Sep 18 2018 - Suman Kumar Sahu (zsahsum)
#   Added a function to update PSO paramenters for Virtual configuration.
# - Thr Jul 06 2017 - Sowjanya Medak (xsowmed)
#   Added support for GEP7 hardware
# - Tue Jul 25 2017 - Yeswanth Vankayala (xyesvan)
#   Adapted changes for Ephermal storage 
#   New function is added get_axe_toggle_value 
# - Wed Apr 12 2017 - Yeswanth Vankayala (xyesvan)
#   Added a new function to fetch system_type attribute.
# - Fri Mar 17 2017 - Rajashekar Narla (xcsrajn)
#   Moved the functions that are not common back to netdef.
# - Tue Feb 28 2017 - Usha Manne (xushman)
#   Added common functions for netdef and netrm scripts.
# - Mon July 25 2016 - Raghavendra Rao K (xkodrag)
#   Added support for single node recovery using adhoc tempalte
# - Thu Apr 28 2016 - Francesco Rainone (EFRARAI)
#   Impact in apos_check_and_exlocall function for avoiding the creation of
#   lockfile in backed-up directory.
# - Wed Apr 06 2016 - Alessio Cascone (ealocae)
#   Added RESTORE_FLAG and isRestore function
# - Mon Feb 01 2016 - Pratap Reddy Uppada (xpraupp)
#   added functions to support system configuration in virtualization
# - Thu Jan 14 2016 - Sindhuja Palla (xsinpal)
#   Modified get_shelf_architecture_attr function for addition of SMX architecture
# - Thu Dec 10 2015 - Pratap Reddy Uppada (xpraupp)
#   updated with parmtool to fetch parameters
# - Mon 11 MAY 2015 - Sindhuja Palla (XSINPAL)
#	Added get_shelf_architecture function to get shelfarchitecture
# - Thu Nov 27 2014 - Madhu Muthyala (XMADMUT)
# 	Added get_shelf_architecture_attr function 
# - Tue Apr 29 2014 - Gianluigi Crispino(xgiacri)
# 	Added get_oam_access_attr function
# - Mon Apr 21 2014 - Pratap Reddy(xpraupp)
# 	Added get_oam_param function
# - Thu Mar 13 2014 - Antonio Buonocunto (eanbuon)
#	Added apos_get_ap2_oam function.
# - Tue Jul 23 2014 - Pratap Reddy (xpraupp)
#	Added get_storage_type for MD & DRBD support.
# - Wed Mar 20 2013 - Vincenzo Conforti (qvincon)
#	Added the apos_get_ap_type
# - Tue Dec 04 2012 - Francesco Rainone (efrarai)
#	Added pluggable structure to easily extend the library.
# - Fri Nov 23 2012 - Paolo Palmieri (epaopal)
#	Added the apos_check_and_exlocall function to manage exclusive lock when destination is a file under /cluster.
# - Tue Jun 28 2012 - Antonio Buonocunto (eanbuon)
#	Add function apos_create_brf_folder.
# - Tue Jan 31 2012 - Paolo Palmieri (epaopal)
#	Configuration scripts rework.
# - Tue Jan 10 2012 - Francesco Rainone (efrarai)
#	Added apos_log and rework of the other functions.
# - Mon Jan 31 2011 - Francesco Rainone (efrarai)
#	First version.
##

# Common variables
TRUE=$( true; echo $? )
FALSE=$( false; echo $? )
AP2="AP2"

APOS_APP_NAME=''
COMMON_RES_PATH="${AP_HOME:-/opt/ap}/apos/conf/apos_common_res"

# Global variables
STORAGE_PATHS="/usr/share/pso/storage-paths"
STORAGE_CONFIG_PATH="$STORAGE_PATHS/config"
AP_TYPE_FILE="apos/aptype.conf"
AP2_OAM="ap2_oam"
CACHED_CREDS_DURATION="cached_creds_duration"
CMD_PARMTOOL="/opt/ap/apos/bin/parmtool/parmtool"
STAGE_FILE='/boot/.config_stage'
config_dir='/mnt/config_drive'
RESTORE_FLAG="apos_restore_flag"
SNRINT_REBUILD_INPROGRESS='/boot/.snrinit.rebuildinprogress'
CMD_GETINFO='/opt/ap/apos/bin/gi/apos_getinfo'
exit_virtual_arch_string='Illegal command in this system configuration'
is_swm_2_0="/cluster/storage/system/config/apos/swm_version"
# command-list
CMD_CAT='/usr/bin/cat'


LOG_APP='/usr/bin/logger'
if [ ! -x $LOG_APP ]; then
	LOG_APP='echo -e'
fi


#-------------------------------------------------------------------------------
# usage: apos_log [<priority>] <message_to_log>
#        <priority> must be in the form <facility>.<level>
#        <facility> must be one of auth, authpriv, cron, daemon, kern, lpr,
#                                  mail, news, syslog, user, uucp, local[0-7].
#        <level> must be one of debug, info, notice, warning, err, crit, alert,
#                               emerg.
function apos_log() {
  TAG="-t ${APOS_APP_NAME:-apos}"
  PRIO=''
  MESSAGE=''
  if [ $# -gt 0 ]; then
    if [ $# -eq 1 ]; then
      MESSAGE=$1
    else
      PRIO="-p $1"
      MESSAGE=$2
    fi
  fi
  $LOG_APP $PRIO $TAG -- "$MESSAGE"
}

#-------------------------------------------------------------------------------
function update_pso_params() {
  # Read the parameters from the config drive
  # and update it in APOS PSO.
  local TMP_FILE='/tmp'
  local STORAGE_API='/usr/share/pso/storage-paths/config'
  [ -f $STORAGE_API ] && PSO_PATH=$(<$STORAGE_API)
  [ ! -d $PSO_PATH ] && apos_abort 1 "PSO path not Found"
  local APOS_PSO="$PSO_PATH/apos"
  local NBI_ADDRESS=$(cat /etc/cluster/nodes/this/mip/nbi/address)

  # Fetch the config stage file depends on the phase of the system.
  CONFIG_FILE=$($CMD_GETINFO properties)
  ALLOWED_CONFIG_FILES=$(find $APOS_PSO 2>/dev/null)
  NETWORK_IP_ADDRESS_LIST='node1_public_network_ipv4_ip_address
                           node2_public_network_ipv4_ip_address
                           cluster_public_network_ipv4_ip_address
                           default_network_ipv4_gateway_ip_address
                           public_network_ipv4_prefix
                           node1_public_network_ipv6_ip_address
                           node2_public_network_ipv6_ip_address
                           cluster_public_network_ipv6_ip_address
                           default_network_ipv6_gateway_ip_address
                           public_network_ipv6_prefix'

   for LINE in $CONFIG_FILE; do
    eval $LINE 2>/dev/null
    LVALUE=$(echo $LINE | awk -F "=" '{print $1}')
    if ! $( echo "$ALLOWED_CONFIG_FILES" | grep -wq "$LVALUE" 2>/dev/null); then
      continue
    fi
    if echo "$LVALUE" | grep -q 'public_network_ipv[46]_prefix' 2>/dev/null ; then
       RVALUE=$(echo $LINE | awk -F "=" '{print $2}' | awk -F "/" '{print $2}')
    else
       RVALUE=$(echo $LINE | awk -F "=" '{print $2}')
    fi
    echo $RVALUE > $APOS_PSO/$LVALUE
  done

  # Update nodeA_MEId parameter
  if ! cmp -s $APOS_PSO/me_name $APOS_PSO/nodeA_MEId; then
    cp $APOS_PSO/me_name $APOS_PSO/nodeA_MEId
  fi

  # Update nodeA_MEId parameter
  if ! cmp -s $APOS_PSO/me_name $APOS_PSO/nodeB_MEId; then
    cp $APOS_PSO/me_name $APOS_PSO/nodeB_MEId
  fi

  # Empty the network cpnfig parameters based on the deployment
  # For example, in case of IPv6, IPv6 network parameters are filled
  # with empty values
  for ip_name in $NETWORK_IP_ADDRESS_LIST; do
    if ! echo "$CONFIG_FILE" | grep -qw "$ip_name" 2>/dev/null; then
      echo > $APOS_PSO/$ip_name
    fi
  done

}

#-------------------------------------------------------------------------------
# usage: apos_abort [<return_value>] <message_to_stderr>
function apos_abort() {
  if [ $# -ge 1 ]; then
    if [ $# -eq 2 ]; then
      apos_log 'user.crit' "ABORT ($2)"
      #echo -e "APOS: Aborting ($2)" >&2
      if [[ $1 =~ [0-9]+ ]]; then
        exit $1
      else
        exit $FALSE
      fi
    else
      apos_log 'user.crit' "ABORT ($1)"
      #echo -e "APOS: Aborting ($1)" >&2
    fi
  fi
  exit $FALSE
}

#-------------------------------------------------------------------------------
# usage: apos_intro <script_name>
function apos_intro() {
  local TEXT=''
  if [ $# -ge 1 ]; then
    APOS_APP_NAME="$(basename $1)"
    TEXT="entering the script..."
  fi
  apos_log "$TEXT"
  #echo -e "$TEXT"
}

#-------------------------------------------------------------------------------
# usage: apos_outro [<script_name>]
function apos_outro() {
  if [ $# -gt 0 ]; then
    APOS_APP_NAME="$(basename $1)"
  fi
  local TEXT="script successfully completed."
  apos_log "$TEXT"
  #echo -e "$TEXT"
  APOS_APP_NAME=''
}

#-------------------------------------------------------------------------------
# usage: apos_check_and_call <abs_path> <script_name>
function apos_check_and_call() {
  if [ -x $1/$2 ]; then
    ./$2
    if [ ! $? = 0 ]; then
      apos_abort 1 "\"$2\" exited with non-zero return code"
    fi
  else
    apos_abort 1 "$1/$2 not found or not executable"
  fi
}

#-------------------------------------------------------------------------------
# usage: apos_check_and_exlocall <abs_path> <script_name>
# Note: the function aborts the script execution if it has not been able
#       acquiring the lock after sleeptime*retries seconds.
function apos_check_and_exlocall() {
  local fl_fold="$(apos_create_brf_folder clear)"
  local fl_file='.aposconf.exclusivelock'
  local sleeptime=2
  local retries=30

  # check for directory presence
  if [[ -z "${fl_fold}" || ! -d "${fl_fold}" ]]; then
    apos_abort "directory \"${fl_fold}\" not found"
  fi
  # tries to acquire lock
  lockfile -${sleeptime} -r ${retries} ${fl_fold}/${fl_file} &>/dev/null
  if [ $? -ne $TRUE ]; then
    apos_abort "unable to acquire the lock for ${fl_fold}/${fl_file} resource"
  fi
  # do stuff
  if [ ! -d "$1" ]; then
    apos_abort "path \"$1\" not found"
  fi
  pushd "$1" &>/dev/null || apos_abort "failure while entering the directory \"$1\""
  if [ -x $1/$2 ]; then
    ./$2
    if [ $? -ne $TRUE ]; then
      apos_abort 1 "\"$2\" exited with non-zero return code"
    fi
  else
    apos_abort 1 "$1/$2 not found or not executable"
  fi
  popd &>/dev/null
  # unlock
  rm -f ${fl_fold}/${fl_file} || apos_abort "failure while trying to delete \"${fl_fold}/${fl_file}\""
}

#-------------------------------------------------------------------------------
# usage: apos_check_and_cat <file_with_abs_path>
function apos_check_and_cat() {
  local file=$1
  local out=""
  if [ -f $file ]; then
    out=$(cat $file)
    if [ $out == "" ]; then
      apos_abort 1 "unable to read $file file content"
    fi
  else
    apos_abort 1 "$file file not found"
  fi
  echo "$out"
}

#-------------------------------------------------------------------------------
# usage: apos_create_brf_folder <type>
function apos_create_brf_folder() {
  local allowed_folder='clear config no-backup software user'
  local is_allowed=''
  for item in $allowed_folder; do
    if [ "$1" == "$item" ]; then
      is_allowed=$TRUE
    fi
  done
  if [  $is_allowed ]; then
    local brf_folder=$(apos_check_and_cat $STORAGE_PATHS/$1)
    local apos_folder=$brf_folder/apos
    if [ -d $apos_folder ]; then
      apos_log "Folder $apos_folder found"
    else
      mkdir -p $apos_folder
      if [ ! $? = 0 ]; then
        apos_abort 1 "mkdir -p $apos_folder exited with non-zero return code"
      fi
    fi
    echo $apos_folder
  fi
}

#-------------------------------------------------------------------------------
# usage: get_storage_type
function get_storage_type() {
   # datadisk_replication_type is optional parameter set in the factory
   # parameters file. If this parameter is not set, then the installation
   # checks for installation_hw type to decide the replication type.
   # Following are the valid combinations:
   # installation_hw=GEP1/GEP2    -- replication_type=MD/DRBD
   # installation_hw=GEP4/GEP5/VM/GEP7 -- replication_type=DRBD
   #
  local STORAGE_TYPE=''
  local CMD_HWTYPE='/opt/ap/apos/conf/apos_hwtype.sh'
  local HW_TYPE=$( $CMD_HWTYPE)
  [ ! -x $CMD_PARMTOOL ] && apos_abort 1 "$CMD_PARMTOOL not found or not executable"
  # in case of vAPG, fetch the storage type using parmtool
  STORAGE_TYPE=$( $CMD_PARMTOOL get --item-list datadisk_replication_type 2>/dev/null | \
    awk -F'=' '{print $2}')
  [ -z "$STORAGE_TYPE" ] && {
    MI_PATH='/cluster/mi/installation'
    STORAGE_TYPE='MD'
    if [ -f $MI_PATH/datadisk_replication_type ]; then
      STORAGE_TYPE=$( cat $MI_PATH/datadisk_replication_type)
      if [ -z "$STORAGE_TYPE" ]; then
        [[ "$HW_TYPE" =~ "GEP4" || "$HW_TYPE" =~ "GEP5" || "$HW_TYPE" =~ "GEP7" || "$HW_TYPE" == 'VM' ]] && \
          STORAGE_TYPE='DRBD'
      else
        [[ "$HW_TYPE" =~ "GEP4" || "$HW_TYPE" =~ "GEP5" || "$HW_TYPE" =~ "GEP7" ]] && [[ "$STORAGE_TYPE" != "DRBD" ]] && \
          apos_abort 1 "$STORAGE_TYPE not supported on $HW_TYPE"
      fi
    else
      [[ "$HW_TYPE" =~ "GEP4" || "$HW_TYPE" =~ "GEP5" || "$HW_TYPE" =~ "GEP7" || "$HW_TYPE" == 'VM' ]] && \
        STORAGE_TYPE='DRBD'
    fi
  }
  echo $STORAGE_TYPE
}

#-------------------------------------------------------------------------------
# usage: apos_get_ap_type 
function apos_get_ap_type() {

  local AP_TYPE=''
  # in case of vAPG, fetch the ap_type using parmtool
  # For vAPG, as of now only AP1 is supported(default configuration)
  [ ! -x $CMD_PARMTOOL ] && apos_abort 1 "$CMD_PARMTOOL not found or not executable"
  AP_TYPE=$( $CMD_PARMTOOL get --item-list ap_type 2>/dev/null | \
  awk -F'=' '{print $2}')
  if [ -z "$AP_TYPE" ]; then
    local BOOT_APTYPE="/boot/aptype.conf"
    if [ -f "$BOOT_APTYPE" ]; then
      AP_TYPE=$( $CMD_CAT $BOOT_APTYPE 2>/dev/null )
      if [ -z "$AP_TYPE" ]; then
        AP_TYPE="AP1"
        apos_log "ap_type found NULL in boot, setting default value"
      else
        apos_log "ap_type found with $AP_TYPE value in boot"
      fi
    else
      AP_TYPE="AP1"
      apos_log "ap_type found NULL in pso, setting default value"
    fi
  else
    apos_log "ap_type found with $AP_TYPE value in pso"
  fi
  echo "$AP_TYPE"
}


#-------------------------------------------------------------------------------
# usage: apos_get_ap2_oam . Return Value= YES|NO
function apos_get_ap2_oam() {
  local ap2_oam=""
  # get config storage path by pso api
  local APOS_PSO_FOLDER=$( apos_check_and_cat $STORAGE_CONFIG_PATH)
  local AP2_OAM_PATH="$APOS_PSO_FOLDER/apos/$AP2_OAM"
  if [ -f $AP2_OAM_PATH ]; then
    ap2_oam=$( cat $AP2_OAM_PATH)
    if [ -z $ap2_oam ]; then
      apos_log "$AP2_OAM_PATH file empty,setting default value"
    fi
  else
    apos_log "$AP2_OAM_PATH file not found"
  fi
  echo "$ap2_oam"
}

#-------------------------------------------------------------------------------
# To fetch the apg_oam_access parameter
# NOCABLE/FRONTCABLE vaules are supported
function get_oam_param() {

  local OAM_ACCESS=''
  # in case of vAPG, fetch the apg_oam_access using parmtool
  # for vAPG, it is always NOCABLE
  [ ! -x $CMD_PARMTOOL ] && apos_abort 1 "$CMD_PARMTOOL not found or not executable"
  OAM_ACCESS=$( $CMD_PARMTOOL get --item-list apg_oam_access 2>/dev/null | \
  awk -F'=' '{print $2}')
  if [ -z "$OAM_ACCESS" ]; then
    OAM_ACCESS='FRONTCABLE'
    apos_log "apg_oam_access parameter found NULL,setting default value"
  fi
  echo $OAM_ACCESS
}

#-------------------------------------------------------------------------------
function get_shelf_architecture() {
  local SHELF_ARCH=''
  [ ! -x $CMD_PARMTOOL ] && apos_abort 1 "$CMD_PARMTOOL not found or not executable"
  SHELF_ARCH=$( $CMD_PARMTOOL get --item-list shelf_architecture 2>/dev/null | \
  awk -F'=' '{print $2}')
  if [ -z "$SHELF_ARCH" ]; then
    SHELF_ARCH='SCB'
    apos_log "$SHELF_ARCH file empty,setting default value"
  fi
  echo $SHELF_ARCH
}

#-----------------------------------------------------------------------------
# This function retrives the system type. i.e., SCP or MCP
function get_system_type() {
  local SYSTEM_TYPE=''
  SYSTEM_TYPE=$( $CMD_PARMTOOL get --item-list system_type 2>/dev/null | \
  awk -F'=' '{print $2}')
  [ -z "$SYSTEM_TYPE" ] && apos_abort 1 "system_type parameter not found!"
  echo $SYSTEM_TYPE
}

#-------------------------------------------------------------------------------
# To fetch the apg_oam_access parameter from IMM
# FRONTCABLE=0 | NOCABLE=1 | NOTAPPLICABLE=2

function get_oam_access_attr(){

  # Default Cablelesss not defined
  local rCode=0
  local imm_class_name=$(immfind -c AxeFunctions)
  if [ ! -z $imm_class_name ] ; then
    local cable_status=$(immlist  -a apgOamAccess $imm_class_name| awk ' BEGIN { FS = "=" } ; { print $2 }')
    if [ ! -z $cable_status ] ; then
      rCode="$cable_status"  
    else
      apos_log "unable to read attribute apgOamAccess in $imm_class_name class"
    fi
  else
    apos_log "unable to find $imm_class_name class"
  fi

  echo $rCode
}

#-------------------------------------------------------------------------------
# usage: apos_get_cached_creds_duration
function apos_get_cached_creds_duration() {
  local cached_creds_duration=""
  local ap_type=$(apos_get_ap_type)	
  if [ "$ap_type" ==  "AP1" ]; then 
    # get apos_get_cached_creds_duration
    [ ! -x $CMD_PARMTOOL ] && apos_abort 1 "$CMD_PARMTOOL not found or not executable"
    cached_creds_duration=$( $CMD_PARMTOOL get --item-list cached_creds_duration 2>/dev/null | \
    awk -F'=' '{print $2}')
    if [ -z $cached_creds_duration ]; then
      apos_abort "cached_creds_duration file empty"
    fi
    [[ $cached_creds_duration =~ ^[0-9]+$ ]] || apos_abort "value $cached_creds_duration for cached credentials duration not valid"
  else
    cached_creds_duration="0"
  fi
  echo "$cached_creds_duration"
}

#-------------------------------------------------------------------------------
# To fetch the apgShelfArchitecture parameter from IMM
# SCB=0 | SCX=1 | BSP=2 | VIRTUALIZED=3 | SMX=4 
function get_shelf_architecture_attr(){
  #Default shelf architecture (SCB)
  local shelf_arch_str=""
  local shelf_arch_int=""

    shelf_arch_str=$(get_shelf_architecture)
    if [ -z "$shelf_arch_str" ]; then
      shelf_arch_int='0'
      apos_log "$STORAGE_PATH/$CFG_FILE file empty, default value"
    else
      case $shelf_arch_str in
        SCB)
          shelf_arch_int='0'
          ;;
        SCX)
          shelf_arch_int='1'
          ;;
        BSP|DMX)
          shelf_arch_int='2'
          ;;
        VIRTUALIZED)
          shelf_arch_int='3'
          ;;
        SMX)
          shelf_arch_int='4'
          ;;
        *)
          shelf_arch_int='0'
      esac
    fi

  echo $shelf_arch_int
}

#-------------------------------------------------------------------------------
# in case vAPG, DNR phase
function is_dnr_phase() {
  return $FALSE
}

#-------------------------------------------------------------------------------
# in case vAPG, SNR phase
function is_snr_phase() {
  local phase=$FALSE
  if is_system_configuration_allowed ; then
    if [ -f $SNRINT_REBUILD_INPROGRESS ]; then
      phase=$TRUE
    fi
  fi
 
  return $phase
}

#-------------------------------------------------------------------------------
function is_deploy_phase() {
  local phase=$FALSE
  local CMD_HWTYPE='/opt/ap/apos/conf/apos_hwtype.sh'  
  
  #check for single node recovery start
  if ! is_snr_phase ; then
    ENV=$( $CMD_HWTYPE --verbose | grep "system-manufacturer" | awk -F"=" '{print $2}' |\
        sed -e 's@^[[:space:]]*@@g' -e 's@^"@@g' -e 's@"$@@g' )
    if [ "$ENV" != 'eri-adk' ]; then
      phase=$TRUE
    fi
  fi
  
  return $phase
}

#-------------------------------------------------------------------------------
function is_adk_phase() {
  local phase=$FALSE
  local CMD_HWTYPE='/opt/ap/apos/conf/apos_hwtype.sh'
  ENV=$( $CMD_HWTYPE --verbose | grep "system-manufacturer" | awk -F"=" '{print $2}' |\
        sed -e 's@^[[:space:]]*@@g' -e 's@^"@@g' -e 's@"$@@g' )
  if [ "$ENV" == 'eri-adk' ]; then
    phase=$TRUE
  fi
  return $phase
}

#-------------------------------------------------------------------------------
function mount_config_drive() {
  local OPTS='--options ro'
  # Check if config-drive avaiable or not
  for label in $(find "/dev/disk/by-label" -maxdepth 1 -type l ); do
    if [ "$(/usr/bin/basename $label)" == 'config-2' ]; then
      if [ -L $label ]; then
        config_drive=$(/usr/bin/readlink -m $label)
      fi
    fi
  done

  [ -z "$config_drive" ] && apos_abort 1 "Config-drive Not Found"
  [ ! -d "$config_dir" ] && mkdir -p "$config_dir"

  # mount the config_drive with read only option
  if ! /bin/mount $OPTS "$config_drive" "$config_dir" 2>/dev/null; then
    apos_abort 1 "Failed to mount config drive"
  fi
}

#-------------------------------------------------------------------------------
function get_config_stage() {
  local CONFIG_STAGE=3
  if [ -e "$STAGE_FILE" ]; then
    CONFIG_STAGE=$(<$STAGE_FILE)
  fi
  echo "$CONFIG_STAGE"
}

#-------------------------------------------------------------------------------
function is_system_configuration_allowed() {
  local STATUS=$FALSE
  STAGE=$(get_config_stage)
  if [ -z "$STAGE" ]; then
    STATUS=$FALSE
  elif [ $STAGE -le 2 ]; then
    STATUS=$TRUE
  fi
  return $STATUS
}

#-------------------------------------------------------------------------------
# Delete all traling zeroes of IPv6
# 2001:0102:0000:0000:0000:0000:0000:325 -> 2001:102:0:0:0:0:0:325
#-------------------------------------------------------------------------------
function remove_trailing_zeroes_ipv6() {

  # Remove all trailing zeros
  local ipv6_addr=:$1:
  ipv6_addr=$(echo $ipv6_addr | sed 's/:00*/:/g')

  # Run the following command 2 times to make sure that it replaces all ::
  ipv6_addr=$(echo $ipv6_addr | sed 's/::/:0:/g')
  ipv6_addr=$(echo $ipv6_addr | sed 's/::/:0:/g')
  ipv6_addr=${ipv6_addr:1:$((${#ipv6_addr}-2))}

  echo "$ipv6_addr"
}

#-------------------------------------------------------------------------------
# Convert from non-abbreviated IPv6 to shorted abbreviated form
# 2001:0:0:8:0:0:0:417A -> 2001:0:0:8::417A
#-------------------------------------------------------------------------------
function convert_IPv6_to_abbreviated_form() {

  local ipv6_addr=:$1
  local ipv6_addr_length=$(expr length $ipv6_addr)

  local index=1
  local abbreviated_addr=$(echo $ipv6_addr | sed "s/:0:0\(:0\)*/:/$index")
  local abbreviated_addr_length=$(expr length $abbreviated_addr)

  local new_abbreviated_addr=$abbreviated_addr
  local new_abbreviated_addr_length=$abbreviated_addr_length
  local second_char=""
  local last_char=""

  # Find the shortest abbreviated form of ipv6
  while [ "$new_abbreviated_addr_length" -lt "$ipv6_addr_length" ]
  do
    ((index++))
    new_abbreviated_addr=$(echo $ipv6_addr | sed "s/:0:0\(:0\)*/:/$index")
    new_abbreviated_addr_length=$(expr length $new_abbreviated_addr)
    if [ "$new_abbreviated_addr_length" -lt "$abbreviated_addr_length" ]; then
      abbreviated_addr=$new_abbreviated_addr
      abbreviated_addr_length=$new_abbreviated_addr_length
    fi
  done

  second_char=$(expr substr $abbreviated_addr 2 1)
  if [ "$second_char" != ":" ]; then
    abbreviated_addr=${abbreviated_addr:1}
  fi

  last_char=$(expr substr $abbreviated_addr ${#abbreviated_addr} 1)
  if [ "$last_char" == ":" ]; then
    abbreviated_addr="$abbreviated_addr":
  fi
  echo $abbreviated_addr
}

#------------------------------------------------------------------------------
# Convert from abbreviated IPv6 to non-abbreviated form
# 2001::8:0:0:0:417A -> 2001:0:0:8:0:0:0:417A
#------------------------------------------------------------------------------
convert_IPv6_to_non_abbreviated_form() {
  local ipv6_addr=$1
  local zeros_string=:0:
  local zeros_num=""
  local first_char=""
  local last_char=""

  # Count number of ":"
  local delimiter_count="${ipv6_addr//[^:]}"
  delimiter_count="${#delimiter_count}"

  zeros_num=$(expr 8 - $delimiter_count)

  # Set string of zeros to replace ::
  case $zeros_num in
    "2")
         zeros_string=:0:0:
         ;;
    "3")
         zeros_string=:0:0:0:
         ;;
    "4")
         zeros_string=:0:0:0:0:
         ;;
    "5")
         zeros_string=:0:0:0:0:0:
         ;;
    "6")
         zeros_string=:0:0:0:0:0:0:
         ;;
    "7")
         zeros_string=:0:0:0:0:0:0:0:
         ;;
  esac

  ipv6_addr=$(echo $ipv6_addr | sed "s/::/$zeros_string/g")

  first_char=$(expr substr $ipv6_addr 1 1)
  if [ "$first_char" == ":" ]; then
    ipv6_addr=0$ipv6_addr
  fi

  last_char=$(expr substr $ipv6_addr ${#ipv6_addr} 1)
  if [ "$last_char" == ":" ]; then
    ipv6_addr="$ipv6_addr"0
  fi

  echo $ipv6_addr
}

#------------------------------------------------------------------------------
# Convert the configured IPv6 to shortest abbreviated IPv6
#------------------------------------------------------------------------------
function get_ipv6_shortest_form() {
  local addr=$1

  # Convert ipv6 to non-abbreviated form if it is in abbreviated format
  if [[ "$addr" =~ "::" ]]; then
    addr=$(convert_IPv6_to_non_abbreviated_form "$addr")
  fi

   # Delete trailing zeroes
   addr=$(remove_trailing_zeroes_ipv6 "$addr")

   addr=$(convert_IPv6_to_abbreviated_form "$addr")

   echo "$addr"
}

#------------------------------------------------------------------------------
# usage: expand_ipv6_address
#        This function is used to expand the IPv6 address in long format. 
#        It takes the input as IPv6 address in short form and returns the 
#        same address in long format.
#------------------------------------------------------------------------------
function expand_ipv6_address () {
  local ip_address=$1
  if [ "$ip_address" = "::" ]; then
    ip_address="0::0"
  fi
  local last=""
  local input="$(echo "$ip_address"|tr 'a-f' 'A-F')"

  # While there are fields left to fill with zeroes
  while [ "$last" != "$input" ]; do
    last="$input"

    # Zero fill fields with three octets
    input="$(echo "$input"|sed 's|:\([0-9A-F]\{3\}\):|:0\1:|g')"
    input="$(echo "$input"|sed 's|:\([0-9A-F]\{3\}\)$|:0\1|g')"
    input="$(echo "$input"|sed 's|^\([0-9A-F]\{3\}\):|0\1:|g')"

    # Zero fill fields with two octets
    input="$(echo "$input"| sed 's|:\([0-9A-F]\{2\}\):|:00\1:|g')"
    input="$(echo "$input"| sed 's|:\([0-9A-F]\{2\}\)$|:00\1|g')"
    input="$(echo "$input"| sed 's|^\([0-9A-F]\{2\}\):|00\1:|g')"

    # Zero fill fields with one octet
    input="$(echo "$input"| sed 's|:\([0-9A-F]\):|:000\1:|g')"
    input="$(echo "$input"| sed 's|:\([0-9A-F]\)$|:000\1|g')"
    input="$(echo "$input"| sed 's|^\([0-9A-F]\):|000\1:|g')"
  done

  # now expand the ::
  local zeroes=""
  local missing

  echo "$input" | grep -qs "::" 
  if [ $? -eq 0 ]; then 
    local groups="$(echo "$input"|sed  's|[0-9A-F]||g'| wc -m)"
    groups=$((groups-1)) # carriage return
    missing=$((8-groups))
    for i in $(seq 1 $missing); do
      zeroes="$zeroes:0000"
    done

    # Note: Be careful where to place the :
    input="$(echo "$input"| sed 's|\(.\)::\(.\)|\1'$zeroes':\2|g')"
    input="$(echo "$input"| sed 's|\(.\)::$|\1'$zeroes':0000|g')"
    input="$(echo "$input"| sed 's|^::\(.\)|'$zeroes':0000:\1|g;s|^:||g')"

  fi

  echo "$input"
}

#----------------------------------------------------------------------------------------
# usage: isValidIPv6
#        This function checks whether IPv6 address supplied is Valid IPv6 address or not
#        Returns TRUE    : In case of valid IPv6 address.
#        Returns FALSE   : In case of invalid IPv6 address.
#----------------------------------------------------------------------------------------
function isValidIPv6() {
  local input_addr=$(expand_ipv6_address "$1")
  local VALIDITY=$FALSE
  local Invalid_first_octet='FE80|FF00|FEC0|FE00|F800'

  # first check it is global unicast or not
  input_addr="$(echo "$input_addr" | tr 'a-z' 'A-Z')"
  first_octet=$(echo "$input_addr" | awk -F ':' '{print $1}')
  echo "$Invalid_first_octet" | grep -qE "$first_octet" 2>/dev/null
  if [ $? -ne $TRUE ]; then
    if [ $(echo "$input_addr" | wc -m) = 40 ]; then
      # check for regular expression
      [[ "$input_addr" =~ ^((([0-9A-F]{1,4}:){7}[0-9A-F]{1,4}))$ ]] && VALIDITY=$TRUE
    fi
  fi
  return $VALIDITY
}

#-------------------------------------------------------------------------------
function netbits_ipv6() {
  local prefix=$2
  local address=$1
  bytes=
  pos=0
  address=${address//:/}
  strlen=${#address}

  for i in $(seq 1 $strlen); do
    bits=
    val=0x${address:$pos:1}
    for i in 1 2 3 4
    do
      bits=$(( $val - ($val/2*2) ))${bits}
      val=$(($val/2))
     done
     bytes=${bytes}${bits}
     pos=$(($pos + 1))
  done
  echo ${bytes:0:$prefix}
}

#-------------------------------------------------------------------------------
# usage: partof_ipv6_subnet
#        This function checks whether the IPv6 address provided belongs to the
#        subnet provided.
#        returns TRUE : If the IPv6 addreess belongs to the provided subnet.
#        returns FALSE: If the IPv6 addreess does not belong to the provided subnet.
#-------------------------------------------------------------------------------
function partof_ipv6_subnet() {
  local expanded_address=$(expand_ipv6_address $1)
  local expanded_network_address=$(expand_ipv6_address $2)
  local network_prefix=$3

  netbits_of_address=$(netbits_ipv6 "$expanded_address" $3)
  netbits_of_network=$(netbits_ipv6 "$expanded_network_address" $3)
  if [ "$netbits_of_address" == "$netbits_of_network" ]; then
    return $TRUE;
  else
    return $FALSE;
  fi
}

#-------------------------------------------------------------------------------
# usage: populate_apg_protocol_version_type
#        This function identifies the deployment type and populates the result in 
#        the file apg_protocol_version_type in apos PSO path.
#        apg_protocol_version_type with  4   : In case of only IPv4 deployment
#        apg_protocol_version_type with  6   : In case of only Ipv6 deployment
#        apg_protocol_version_type with  4,6 : In case of dual stack deployment
#-------------------------------------------------------------------------------
function populate_apg_protocol_version_type() {

  local StackType=''
  local IPv4Stack=$FALSE
  local IPv6Stack=$FALSE
  local DualStack=$FALSE
  local PSO_PATH=$( apos_check_and_cat $STORAGE_CONFIG_PATH)
  local APOS_PSO="$PSO_PATH/apos"

  # Fetch the user data related information
  local network_ip_addresses=$($CMD_GETINFO properties | grep -E 'ip_address|ipv')
  [  -z "$network_ip_addresses" ] && apos_abort 1 "network_ip_addresses variable found NULL"

  # Read the parameters to configured
  for parm in $network_ip_addresses; do
    eval $parm 2>/dev/null
  done

  # check for IPv4 stack
  [[ -n "$node1_public_network_ipv4_ip_address"    && \
     -n "$node2_public_network_ipv4_ip_address"    && \
     -n "$cluster_public_network_ipv4_ip_address"  && \
     -n "$default_network_ipv4_gateway_ip_address" ]] && IPv4Stack=$TRUE

  # check for IPv6 stack
  [[ -n "$node1_public_network_ipv6_ip_address"    && \
     -n "$node2_public_network_ipv6_ip_address"    && \
     -n "$cluster_public_network_ipv6_ip_address"  && \
     -n "$default_network_ipv6_gateway_ip_address" ]] && IPv6Stack=$TRUE

  # check for Dual stack
  [[ $IPv4Stack -eq $TRUE && $IPv6Stack -eq $TRUE ]] && DualStack=$TRUE

  [ $IPv4Stack -eq $TRUE ] && StackType='4'
  [ $IPv6Stack -eq $TRUE ] && StackType='6'
  [ $DualStack -eq $TRUE ] && StackType='4,6'

  if [ -n "$StackType" ]; then 
    echo "$StackType" > $APOS_PSO/apg_protocol_version_type || \
     apos_abort 'Failure while populating stackType'
  fi 
}

#-------------------------------------------------------------------------------
# usage: get_apg_protocol_version_type 
#        This function returns the apg protocol version type
#        returns 4   : In case of only IPv4 deployment
#        returns 6   : In case of only Ipv6 deployment
#        returns 4,6 : In case of dual stack deployment
# Note: In case of Native, this function returns '4'
#-------------------------------------------------------------------------------
function get_apg_protocol_version_type() {

  local PROTO_VER_TYPE=''
  # get apg_protocol_version_type
  if [ ! -x $CMD_PARMTOOL ]; then 
    local PSO_FOLDER=$( apos_check_and_cat $STORAGE_CONFIG_PATH)
    local APOS_PSO_FOLDER="$PSO_FOLDER/apos"
    PROTO_VER_TYPE="$(<$APOS_PSO_FOLDER/apg_protocol_version_type 2>/dev/null)"
  else
    PROTO_VER_TYPE=$( $CMD_PARMTOOL get --item-list apg_protocol_version_type 2>/dev/null | \
      awk -F'=' '{print $2}')
  fi 

  [ -z "$PROTO_VER_TYPE" ] && PROTO_VER_TYPE='4'
  if ! echo "$PROTO_VER_TYPE" | grep -Eq '^4$|^6$|^4,6$' 2>/dev/null; then
    apos_log "INFO: Setting to default APG protocol version type: IPv4"
    PROTO_VER_TYPE='4'
  fi
  echo "$PROTO_VER_TYPE"
}

#-------------------------------------------------------------------------------
# usage: isIPv4Stack
#        This function checks whether deployed stack is of IPv4 or not.
#        Returns TRUE    : In case of only IPv4 deployment
#        Returns FALSE   : Otherwise
#-------------------------------------------------------------------------------
function isIPv4Stack(){
  
  local PROTO_VER_TYPE="$(get_apg_protocol_version_type)"

  if echo "$PROTO_VER_TYPE" | grep -q '^4$' 2>/dev/null; then
    apos_log "INFO: APG protocol version type: IPv4"
    return $TRUE
  fi

  return $FALSE
}

#-------------------------------------------------------------------------------
# usage: isIPv6Stack
#        This function checks whether deployed stack is of IPv6 or not.
#        Returns TRUE    : In case of only IPv6 deployment
#        Returns FALSE   : Otherwise
#-------------------------------------------------------------------------------
function isIPv6Stack(){
  
  local PROTO_VER_TYPE="$(get_apg_protocol_version_type)"

  if echo "$PROTO_VER_TYPE" | grep -q '^6$' 2>/dev/null; then
    apos_log "INFO: APG protocol version type: IPv6"
    return $TRUE
  fi

  return $FALSE
}

#-------------------------------------------------------------------------------
# usage: isDualStack
#        This function checks whether deployed stack supports both 
#        IPv4 and IPv6 or not.
#        Returns TRUE    : In case of only Dual Stack(IPv4+IPv6) deployment
#        Returns FALSE   : Otherwise
#-------------------------------------------------------------------------------
function isDualStack(){
  
  local PROTO_VER_TYPE="$(get_apg_protocol_version_type)"

  if echo "$PROTO_VER_TYPE" | grep -q '^4,6$' 2>/dev/null; then
    apos_log "INFO: APG protocol version type: Dual"
    return $TRUE
  fi

  return $FALSE
}

#-------------------------------------------------------------------------------
function isValidIPv4() {
  local rCode=$FALSE

  local ip_address="$1"
  local letters=$(echo $ip_address | tr -dc "([0-9]|\.)")
  local diff=$( echo $(( ${#ip_address} - ${#letters} )))

  if [ $diff -eq 0 ] ; then
    local ip_address_components=(${ip_address//./ })
    if [ ${#ip_address_components[@]} -eq 4 ] ; then
      local dots=$(echo $ip_address | tr -dc "(\.)")
      if [ ${#dots} -eq 3 ] ; then
        local status=$TRUE
        local ip_component
        for ip_component in "${ip_address_components[@]}" ; do
          if [ ${#ip_component} -le 0 ] || [ ${#ip_component} -gt 3 ] || \
             [ $ip_component -lt 0 ] || [ $ip_component -gt 255 ]; then
            status=$FALSE;
            break;
          fi
        done

        [[ $status -eq $TRUE ]] && rCode=$TRUE
      fi
    fi
  fi
  return $rCode
}

#-------------------------------------------------------------------------------
function verify_network_IPs_are_different() {
  local node1_ip_addr="$1"
  local node2_ip_addr="$2"
  local cluster_ip_addr="$3"
  local gateway_ip_addr="$4"

  [[ "$node1_ip_addr" == "$node2_ip_addr" ]] && \
  apos_abort 1 "Unreasonable value < $node1_ip_addr, $node2_ip_addr >"

  [[ "$node1_ip_addr" == "$cluster_ip_addr" ]] && \
  apos_abort 1 "Unreasonable value < $node1_ip_addr, $cluster_ip_addr >"

  [[ "$node2_ip_addr" == "$cluster_ip_addr" ]] && \
  apos_abort 1 "Unreasonable value < $node2_ip_addr, $cluster_ip_addr >"

  [[ "$node1_ip_addr" == "$gateway_ip_addr" ]] && \
  apos_abort 1 "Unreasonable value < $node1_ip_addr, $gateway_ip_addr >"

  [[ "$node2_ip_addr"    == "$gateway_ip_addr" ]] && \
  apos_abort 1 "Unreasonable value < $node2_ip_addr, $gateway_ip_addr >"

  [[ "$cluster_ip_addr" == "$gateway_ip_addr" ]] && \
  apos_abort 1 "Unreasonable value < $cluster_ip_addr, $gateway_ip_addr >"

}

#-------------------------------------------------------------------------------
function compute_subnet_address() {
  local ip_address="$1"
  local subnet_mask="$2"

  if [ "$subnet_mask" != "" ] ; then
    local ip_address_component=(${ip_address//./ })
    local subnet_mask_component=(${subnet_mask//./ })

    local subnet_id_A=$(echo $((${ip_address_component[0]} & ${subnet_mask_component[0]})))
    local subnet_id_B=$(echo $((${ip_address_component[1]} & ${subnet_mask_component[1]})))
    local subnet_id_C=$(echo $((${ip_address_component[2]} & ${subnet_mask_component[2]})))
    local subnet_id_D=$(echo $((${ip_address_component[3]} & ${subnet_mask_component[3]})))

    echo "$subnet_id_A.$subnet_id_B.$subnet_id_C.$subnet_id_D/$cidr_netmask"
  fi
}

#-------------------------------------------------------------------------------
function compute_broadcast_address() {
  local ip_address="$1"
  local subnet_mask="$2"

  if [ "$subnet_mask" != "" ] ; then
    local ip_address_component=(${ip_address//./ })
    local subnet_mask_component=(${subnet_mask//./ })

    (( a = ~${subnet_mask_component[0]} + 256 ))
    (( b = ~${subnet_mask_component[1]} + 256 ))
    (( c = ~${subnet_mask_component[2]} + 256 ))
    (( d = ~${subnet_mask_component[3]} + 256))

    local broadcast_ip_A=$(echo $((${ip_address_component[0]} | $a)))
    local broadcast_ip_B=$(echo $((${ip_address_component[1]} | $b)))
    local broadcast_ip_C=$(echo $((${ip_address_component[2]} | $c)))
    local broadcast_ip_D=$(echo $((${ip_address_component[3]} | $d)))

    echo "$broadcast_ip_A.$broadcast_ip_B.$broadcast_ip_C.$broadcast_ip_D"
  fi
}

#-------------------------------------------------------------------------------
function verify_network_IPs_subnet() {
  local node1_ip_addr="$1"
  local node2_ip_addr="$2"
  local cluster_ip_addr="$3"
  local cidr_netmask="$4"

  local nodeA_subnet_ip_binary=$(ip_to_bin "$node1_ip_addr")
  local nodeB_subnet_ip_binary=$(ip_to_bin "$node2_ip_addr")
  local cluster_subnet_ip_binary=$(ip_to_bin "$cluster_ip_addr")

  local subnetA_ip_firstBits=${nodeA_subnet_ip_binary:0:$cidr_netmask}
  local subnetB_ip_firstBits=${nodeB_subnet_ip_binary:0:$cidr_netmask}
  local subnetC_ip_firstBits=${cluster_subnet_ip_binary:0:$cidr_netmask}

  if [[ "$subnetA_ip_firstBits" == "$subnetB_ip_firstBits" && \
        "$subnetB_ip_firstBits" == "$subnetC_ip_firstBits" && \
        "$subnetA_ip_firstBits" == "$subnetC_ip_firstBits" ]]; then
    apos_log "NodeA, NodeB and Cluster IPs are in same subnet."
  else
    apos_abort 1 "NodeA, NodeB and Cluster IPs are not in same subnet."
  fi
}

#-------------------------------------------------------------------------------
function verify_gateway_compliance() {
  local cluster_ip_addr="$1"
  local gateway_ip_addr="$2"
  local netmask="$3"

  # Verify Gateway and Source Network (Cluster IP) are in same subnet
  local source_subnet="$(compute_subnet_address $cluster_ip_addr $netmask )"
  local gateway_subnet="$(compute_subnet_address $gateway_ip_addr $netmask )"
  if [ "$source_subnet" == "$gateway_subnet" ]; then
    apos_log "Gateway and Source Network are in same subnet"
  else
    apos_abort 1 "Gateway and Source Network are NOT in same subnet"
  fi

  # Verify Gateway adress is NOT equal to Source Subnet address and Source Broadcast address
  local source_broadcast_addr="$(compute_broadcast_address $cluster_ip_addr $netmask )"
  local source_ip_address="$(echo $source_subnet | awk -F/ '{print $1}')"
  if [[ "$gateway_ip_addr" != "$source_ip_address" && "$gateway_ip_addr" != "$source_broadcast_addr" ]]; then
    apos_log "Gateway adress is not equal to Source Subnet address and Source Broadcast address"
  else
    apos_abort 1 "Gateway adress is equal to Source Subnet address or Source Broadcast address"
  fi
}

#---------------------------------------------------------------------------------------------------
#This function is used to get property values from user_data section
function get_axe_toggle_value(){
  local property=$1
  local validation_regex=$2
  local default_value=$3

  apos_log "reading property \"${property}\""
  local property_value=$($CMD_GETINFO properties.${property})
  property_value="$(echo $property_value | awk -F'=' '{print $2}')"
  if [ -z "$property_value" ]; then
    if [ -z "$default_value" ]; then
      apos_abort "empty value detected and no default specified. Aborting."
    else
      apos_log "empty value detected, falling back to default (${default_value})"
      property_value="${default_value}"
    fi
  elif [[ ! "$property_value" =~ $validation_regex ]];then
    apos_abort "unsupported value: \"$property_value\""
  else
    apos_log "valid value \"$property_value\" identified"
  fi
  echo "${property_value}"
}

#---------------------------------------------------------------------------------------------------
function set_ips_in_cluster_conf() {
  local IPv4Stack=$FALSE
  local IPv6Stack=$FALSE
  local DualStack=$FALSE

  # nested lock function to ensure mutual exclusion in the case of editing
  # clustered resource (e.g. /cluster/etc/cluster.conf)
  function lock() {
    message="acquiring lock on $lockfile..."
    echo "$message"
    apos_log "$message"
    
    /usr/bin/lockfile -2 -l 16 -s 4 $lockfile
    
    local return_code=$?
    if [ $return_code -eq $TRUE ]; then
      message="lock successfully acquired"
      echo "$message"
      apos_log "$message"
    else
      message="unable to acquire lock"
      echo "ERROR: $message" >&2
      apos_log user.crit "$message"
    fi
    return $return_code
  }

  # nested unlock function to ensure mutual exclusion in the case of editing
  # clustered resource (e.g. /cluster/etc/cluster.conf)
  function unlock() {
    message="releasing lock on $lockfile"
    echo "$message"
    apos_log "$message"
    
    /usr/bin/rm -f $lockfile
    
    local return_code=$?
    if [ $return_code -eq $TRUE ]; then
      message="lock successfully released"
      echo "$message"
      apos_log "$message"
    else
      message="unable to release lock"
      echo "ERROR: $message" >&2
      apos_log user.crit "$message"
    fi
    return $return_code
  }
 
  function cleanup_clusterconf () {
    
    if [ $IPv4Stack -eq $TRUE ]; then
       # cleanup IPv6 cluster details.
       public='public_v6'; nbi='nbi_v6'; default='default_v6'; alias_id='2'
    fi

    if [ $IPv6Stack -eq $TRUE ]; then 
      # cleanup IPv4 cluster details
       public='public'; nbi='nbi'; default='default'; alias_id='1'
    fi

    # Remove Public network entry
    if grep -q "network $public" $cluster_file 2>/dev/null; then 
      sed -i -r "/^[[:space:]]*network[[:space:]]$public[[:space:]]+.*$"/d $cluster_file
      [ $? -ne $TRUE ] && apos_log "WARNING: Failure while cleaning-up network entry for $public"
    else
      apos_log "INFO: network entry for $public not found" 
    fi 
   
    # Remove Public Node 1 entry
    if grep -q "ip 1 eth1 $public" $cluster_file 2>/dev/null ; then
      sed -i -r "/^[[:space:]]*ip[[:space:]]1[[:space:]]eth1[[:space:]]$public[[:space:]]+.*$"/d $cluster_file
      [ $? -ne $TRUE ] && apos_log "WARNING: Failure while cleaning-up ip 1 entry for $public"
    else
      apos_log "INFO: ip entry of $public for node-A not found"
    fi 

    # Remove Public Node 2 entry
    if grep -q "ip 2 eth1 $public" $cluster_file 2>/dev/null; then
      sed -i -r "/^[[:space:]]*ip[[:space:]]2[[:space:]]eth1[[:space:]]$public[[:space:]]+.*$"/d $cluster_file
      [ $? -ne $TRUE ] && apos_log "WARNING: Failure while cleaning-up ip 2 entry for $public"
    else
      apos_log "INFO: ip entry of $public for node-B not found"
    fi 

    # Remove nbi/nbi6 entry
    if grep -q "mip control $nbi" $cluster_file 2>/dev/null; then
      sed -i -r "/^[[:space:]]*mip[[:space:]]control[[:space:]]$nbi[[:space:]]eth1:$alias_id[[:space:]]$public[[:space:]]+.*$"/d $cluster_file
      [ $? -ne $TRUE ] && apos_log "WARNING: Failure while cleaning-up nbi entry for $public"
    else
      apos_log "INFO: nbi entry for $public not found"
    fi

    # Remove default/default6 entry
    if grep -q "route control $default" $cluster_file 2>/dev/null; then
      sed -i -r "/^[[:space:]]*route[[:space:]]control[[:space:]]$default[[:space:]]gateway[[:space:]]+.*$"/d $cluster_file
      [ $? -ne $TRUE ] && apos_log "WARNING: Failure while cleaning-up default gateway entry for $public"
    else
      apos_log "INFO: default gateway entry for $public not found"
    fi

    # Remove gateway entry
    if grep -q "network $default" $cluster_file 2>/dev/null; then
      sed -i -r "/^[[:space:]]*network[[:space:]]$default[[:space:]]+.*$"/d $cluster_file    
    else
      apos_log "INFO: $default entry not found"
    fi

    # Remove alias entry
    if grep -q "interface control eth1:$alias_id alias" $cluster_file 2>/dev/null; then
      sed -i -r "/^[[:space:]]*interface[[:space:]]control[[:space:]]eth1:$alias_id[[:space:]]+.*$"/d $cluster_file
    else
      apos_log "INFO: ethernet alias for $public not found"
    fi
  }

  function update_ips_in_cluster_conf(){

    local node1_public_network_ip_address="$1"
    local node2_public_network_ip_address="$2"
    local cluster_public_network_ip_address="$3"
    local default_network_gateway_ip_address="$4"
    local public_network_prefix="$5"
    local stack=$6

    if [ $stack == 'ipv4' ]; then
       # updating IPv4 cluster details.
       public='public'; nbi='nbi'; default='default'; alias_id='1'
    fi

    if [ $stack == 'ipv6' ]; then
      # updatig IPv6 cluster details
      public='public_v6'; nbi='nbi_v6'; default='default_v6'; alias_id='2'
    fi

    if ! grep -qw "$node1_public_network_ip_address" $cluster_file; then
      hook="^[[:space:]]*ip[[:space:]]+1[[:space:]]+eth1[[:space:]]+$public[[:space:]]+.*"
      newrow="ip 1 eth1 $public $node1_public_network_ip_address"
      sed -i -r "s@$hook@$newrow@g" $cluster_file
      [ $? -ne 0 ] && apos_abort 1 "Failure while updating node-A address in cluster.conf"
    fi

    if ! grep -qw "$node2_public_network_ip_address" $cluster_file; then
      hook="^[[:space:]]*ip[[:space:]]+2[[:space:]]+eth1[[:space:]]+$public[[:space:]]+.*"
      newrow="ip 2 eth1 $public $node2_public_network_ip_address"
      sed -i -r "s@$hook@$newrow@g" $cluster_file
      [ $? -ne 0 ] && apos_abort 1 "Failure while updating node-B address in cluster.conf"
    fi

    if ! grep -qw "$cluster_public_network_ip_address" $cluster_file; then
      hook="^[[:space:]]*mip[[:space:]]+control[[:space:]]+$nbi[[:space:]]+eth1:.+[[:space:]]+$public[[:space:]]+.*"
      newrow="mip control $nbi eth1:$alias_id $public $cluster_public_network_ip_address"
      sed -i -r "s@$hook@$newrow@g" $cluster_file
      [ $? -ne 0 ] && apos_abort 1 "Failed to replace cluster IP address in cluster.conf"
    fi

    if ! grep -qw "$public_network_prefix" $cluster_file; then
      hook="^[[:space:]]*network[[:space:]]+$public[[:space:]]+.*"
      newrow="network $public $public_network_prefix"
      sed -i -r "s@$hook@$newrow@g" $cluster_file
      [ $? -ne 0 ] && apos_abort 1 "Failure while updating $public network prefix in cluster.conf"
    fi

    if ! grep -qw "$default_network_gateway_ip_address" $cluster_file; then
      hook="^[[:space:]]*route[[:space:]]+control[[:space:]]+$default[[:space:]]+gateway[[:space:]]+.*"
      newrow="route control $default gateway $default_network_gateway_ip_address"
      sed -i -r "s@$hook@$newrow@g" $cluster_file
      [ $? -ne 0 ] && apos_abort 1 "Failure while updating $default gateway address in cluster.conf"
    fi
  }

  local lockdir=$(apos_create_brf_folder clear)
  local lockfile=$lockdir/$FUNCNAME.lock
  local message=''
  local return_code=''
  local config_param_file='/opt/ap/apos/conf/config_params.conf'
  local mutex=$FALSE

  case $1 in
    local)
      cluster_file=/boot/.cluster.conf
    ;;
    cluster)
      cluster_file=/cluster/etc/cluster.conf
      mutex=$TRUE
      # store the current handler for the EXIT signal.
      old_trap=$(trap | grep -P '[[:space:]]EXIT$')
      # overwrite the handler for the EXIT signal.
      trap unlock EXIT
    ;;
    *)
      message="function $FUNCNAME: missing or invalid parameter ($1)"
      echo "ABORT: $message" >&2
      apos_abort "$message"
    ;;
  esac

  # Fetch the user data related information
  user_data_file=$($CMD_GETINFO properties)
  [  -z "$user_data_file" ] && apos_abort 1 "user data not found"

  # Read the parameters to configured
  for parm in $user_data_file; do
    l_val=$( echo "$parm" | awk -F"=" '{print $1}')
    if grep -wq "$l_val" $config_param_file 2>/dev/null; then
      eval $parm 2>/dev/null
    fi
  done

  # updating network parameters
  if [ -w "$cluster_file" ]; then
    if [ $mutex -eq $TRUE ]; then
      lock
    fi

    # check for IPv4 stack 
    [[ -n "$node1_public_network_ipv4_ip_address"    && \
       -n "$node2_public_network_ipv4_ip_address"    && \
       -n "$cluster_public_network_ipv4_ip_address"  && \
       -n "$default_network_ipv4_gateway_ip_address" ]] && IPv4Stack=$TRUE
    
    # check for IPv6 stack
    [[ -n "$node1_public_network_ipv6_ip_address"    && \
       -n "$node2_public_network_ipv6_ip_address"    && \
       -n "$cluster_public_network_ipv6_ip_address"  && \
       -n "$default_network_ipv6_gateway_ip_address" ]] && IPv6Stack=$TRUE

    # check for Dual stack 
    [[ $IPv4Stack -eq $TRUE && $IPv6Stack -eq $TRUE ]] && DualStack=$TRUE

    [ $DualStack -eq $FALSE ] && cleanup_clusterconf

    if [[ $IPv4Stack -eq $TRUE || $DualStack -eq $TRUE ]]; then 
      
      ### VALIDATION OF IPv4 IP addresses : BEGIN
      isValidIPv4 "$node1_public_network_ipv4_ip_address" 
      [ $? -ne 0 ]  && apos_abort 1 "Unreasonable value < $node1_public_network_ipv4_ip_address>"

      isValidIPv4 "$node2_public_network_ipv4_ip_address"
      [ $? -ne 0 ]  && apos_abort 1 "Unreasonable value < $node2_public_network_ipv4_ip_address>"

      isValidIPv4 "$cluster_public_network_ipv4_ip_address"
      [ $? -ne 0 ]  && apos_abort 1 "Unreasonable value < $cluster_public_network_ipv4_ip_address>"

      isValidIPv4 "$default_network_ipv4_gateway_ip_address"
      [ $? -ne 0 ]  && apos_abort 1 "Unreasonable value < $default_network_ipv4_gateway_ip_address>"

      verify_network_IPs_are_different "$node1_public_network_ipv4_ip_address" "$node2_public_network_ipv4_ip_address" \
      "$cluster_public_network_ipv4_ip_address" "$default_network_ipv4_gateway_ip_address"
      ### VALIDATION OF IPv4 IP addresses : BEGIN

      ### Update IPv4 IP's in cluster.conf: BEGIN
      update_ips_in_cluster_conf "$node1_public_network_ipv4_ip_address" "$node2_public_network_ipv4_ip_address" \
      "$cluster_public_network_ipv4_ip_address" "$default_network_ipv4_gateway_ip_address" "$public_network_ipv4_prefix" 'ipv4'
      ### Update IPv4 IP's in cluster.conf: END
    fi

    if [[ $IPv6Stack -eq $TRUE || $DualStack -eq $TRUE ]]; then 

      ### VALIDATION OF IPv6 IP addresses : BEGIN 
      isValidIPv6 "$node1_public_network_ipv6_ip_address" 
      [ $? -ne 0 ]  && apos_abort 1 "Unreasonable value < $node1_public_network_ipv6_ip_address>"

      isValidIPv6 "$node2_public_network_ipv6_ip_address"
      [ $? -ne 0 ]  && apos_abort 1 "Unreasonable value < $node2_public_network_ipv6_ip_address>"

      isValidIPv6 "$cluster_public_network_ipv6_ip_address"
      [ $? -ne 0 ]  && apos_abort 1 "Unreasonable value < $cluster_public_network_ipv6_ip_address>"

      isValidIPv6 "$default_network_ipv6_gateway_ip_address"
      [ $? -ne 0 ]  && apos_abort 1 "Unreasonable value < $default_network_ipv6_gateway_ip_address>"

      verify_network_IPs_are_different "$node1_public_network_ipv6_ip_address" "$node2_public_network_ipv6_ip_address" \
      "$cluster_public_network_ipv6_ip_address" "$default_network_ipv6_gateway_ip_address"

      local public_network=$(echo $public_network_ipv6_prefix | awk -F "/" '{print $1}')
      local prefix=$(echo $public_network_ipv6_prefix | awk -F "/" '{print $2}')

      if ! partof_ipv6_subnet $node1_public_network_ipv6_ip_address $public_network $prefix; then
        apos_abort 1 "Address $node1_public_network_ipv6_ip_address not in subnet $public_network"
      fi

      if ! partof_ipv6_subnet $node2_public_network_ipv6_ip_address $public_network $prefix; then
        apos_abort 1 "Address $node2_public_network_ipv6_ip_address not in subnet $public_network"
      fi

      if ! partof_ipv6_subnet $cluster_public_network_ipv6_ip_address $public_network $prefix; then
        apos_abort 1 "Address $cluster_public_network_ipv6_ip_address not in subnet $public_network"
      fi

      if ! partof_ipv6_subnet $default_network_ipv6_gateway_ip_address $public_network $prefix; then
        apos_abort 1 "Address $default_network_ipv6_gateway_ip_address not in subnet $public_network"
      fi
      ### VALIDATION OF IPv6 IP addresses: END
 
      ### Update IPv6 IP's in cluster.conf: BEGIN
      update_ips_in_cluster_conf "$node1_public_network_ipv6_ip_address" "$node2_public_network_ipv6_ip_address" \
      "$cluster_public_network_ipv6_ip_address" "$default_network_ipv6_gateway_ip_address" "$public_network_ipv6_prefix" 'ipv6'
      ### Update IPv6 IP's in cluster.conf: END
    fi
    
    if [ $mutex -eq $TRUE ]; then
      # restore the previous handler for the EXIT signal, or completely reset it.
      if [ -n "$old_trap" ]; then
        eval $old_trap
      else
        trap - EXIT
      fi
    fi
  else
    apos_abort "file $cluster_file not found or not writable"
  fi
  
  #Unset nested functions
  unset lock
  unset unlock
}

# The function retrieves node_id (as retrieved at rpm installation time) from
# either /cluster/etc/nodes/this/id or /boot/.node_id. This is to ease some
# virtualization use-cases like, for example, dynamic MAC address handling.
get_node_id(){
  local lde_id_file=/etc/cluster/nodes/this/id
  local apg_id_file=/boot/.node_id
  local id=$(<$lde_id_file)
  local return_code=$TRUE
  if [[ ! "$id" =~ ^[0-9]+$ ]]; then
    apos_log user.crit "non-valid node id ($id) retrieved from $lde_id_file. Falling back to $apg_id_file..."
    local id=$(<$apg_id_file)
    if [[ ! "$id" =~ ^[0-9]+$ ]]; then
      apos_log user.crit "non-valid node id ($id) retrieved from $apg_id_file. Falling back to ovf-env.xml file..."
      local id=$(${CMD_GETINFO} properties.node_id |awk -F'=' '{print $2}')
      if [[ ! "$id" =~ ^[0-9]+$ ]]; then
        apos_log user.crit "non-valid node id ($id) retrieved from $apg_id_file."
        return_code=$FALSE
      fi
    fi
  fi
  echo "${id}"
  return $return_code
}

#-------------------------------------------------------------------------------
#To fetch the node state
function get_node_state(){
  local node_state=''
  # check if we are running on 'active-node'
  node_id=$(get_node_id) 
  if [ -f $is_swm_2_0 ]; then  
	  COMMAND="immlist -a saAmfSISUHAState safSISU=safSu=SC-$node_id\,safSg=2N\,safApp=ERIC-apg.nbi.aggregation.service,safSi=apg.nbi.aggregation.service-2N-1,safApp=ERIC-apg.nbi.aggregation.service"
  else
	COMMAND="immlist -a saAmfSISUHAState safSISU=safSu=$node_id\,safSg=2N\,safApp=ERIC-APG,safSi=AGENT,safApp=ERIC-APG"
  fi
  NODE_STATE=$(kill_after_try 5 1 5 $COMMAND)
  local return_code=$?
  if [ $return_code -ne 0 ] ; then
        apos_log "The command $COMMAND failed with return code $return_code" 
    return $FALSE
  fi
  NODE_STATE=$(echo "$NODE_STATE" | cut -d = -f2)
  case $NODE_STATE in
    1)
      node_state='active'
    ;;
    2)
      node_state='passive'
    ;;
    *)
      node_state='undefined'
      return $FALSE
    ;;
  esac
  
  echo $node_state
  return $TRUE
}

#-------------------------------------------------------------------------------
#To fetch the node state
function get_peer_node_state(){
  local peer_node_state=''
  # check if we are running on 'active-node'
  peer_node_id=$(</etc/cluster/nodes/peer/id) 
  if [ -f $is_swm_2_0 ]; then  
	  COMMAND="immlist -a saAmfSISUHAState safSISU=safSu=SC-$peer_node_id\\,safSg=2N\\,safApp=ERIC-apg.nbi.aggregation.service,safSi=apg.nbi.aggregation.service-2N-1,safApp=ERIC-apg.nbi.aggregation.service"
  else
	COMMAND="immlist -a saAmfSISUHAState safSISU=safSu=$peer_node_id\,safSg=2N\,safApp=ERIC-APG,safSi=AGENT,safApp=ERIC-APG"
  fi
  NODE_STATE=$(kill_after_try 5 1 5 $COMMAND)
  local return_code=$?
  if [ $return_code -ne 0 ] ; then
        apos_log "The command $COMMAND failed with return code $return_code" 
    return $FALSE
  fi
  NODE_STATE=$(echo "$NODE_STATE" | cut -d = -f2)
  case $NODE_STATE in
    1)
      node_state='active'
    ;;
    2)
      node_state='passive'
    ;;
    *)
      node_state='undefined'
      return $FALSE
    ;;
  esac
  
  echo $node_state
  return $TRUE
}

#-------------------------------------------------------------------------------
function is_SIMULATED() {
  local PSO_FOLDER=$( apos_check_and_cat $STORAGE_CONFIG_PATH)
  local APOS_PSO_FOLDER="$PSO_FOLDER/apos"
  # Note: The same "/boot/.installation_platform" file name is also used in 
  # AIT plugin scripts(i.e non_exec-common_functions). So, If the file name is 
  # changed in this script(i.e apos-common.sh)then non_exec-common_functions 
  # script also needs to be updated with the new name.
  local INSTALLATION_PLATFORM_FILE='/boot/.installation_platform'
  if [ -d $APOS_PSO_FOLDER ]; then
    local count=$(find $APOS_PSO_FOLDER -mindepth 1 -maxdepth 1 -name 'simulated_*' | wc -l)
    [[ -n "$count" && $count -gt 0 ]] && return $TRUE
  elif grep -q 'simulated' $INSTALLATION_PLATFORM_FILE 2>/dev/null; then 
    return $TRUE
  fi
  return $FALSE
}

#-------------------------------------------------------------------------------
function is_vAPG() {
  local HW_TYPE=$(/opt/ap/apos/conf/apos_hwtype.sh)
  local SHELF_ARCH=$(get_shelf_architecture)
  if [[ "$HW_TYPE" == 'VM' && "$SHELF_ARCH" == "VIRTUALIZED" ]]; then 
    return $TRUE
  fi
  return $FALSE
}

#----------------------------------------------------------------------------------------
function isSMX(){
  local HW_TYPE=$(/opt/ap/apos/conf/apos_hwtype.sh)
  local SHELF_ARCH=$(get_shelf_architecture)
  [ "$SHELF_ARCH" == "SMX" ] && return $TRUE
  return $FALSE
}

#----------------------------------------------------------------------------------------
function isBSP(){
  local HW_TYPE=$(/opt/ap/apos/conf/apos_hwtype.sh)
  local SHELF_ARCH=$(get_shelf_architecture)
  [ "$SHELF_ARCH" == "DMX" ] && return $TRUE
  return $FALSE
}

#----------------------------------------------------------------------------------------
function is_dscp_supported() {
  isSMX && return $TRUE
  isBSP && return $TRUE
  is_vAPG && return $TRUE
  return $FALSE
}

#-------------------------------------------------------------------------------
# To understand if the current script has been invoked after a restore operation.
function is_restore() {
  # Check if the restore flag is present or not
  if [ -e $(apos_create_brf_folder clear)/$RESTORE_FLAG ]; then
    return $FALSE
  fi
  return $TRUE
}

#-------------------------------------------------------------------------------
#To get an AxeInfo parameter
function getAxeInfo(){
  local AxeInfoItem="$1"
  if [ -z "$AxeInfoItem" ];then
        return $FALSE
    fi
    local getAxeInfoCacheDir="/dev/shm"
  local getAxeInfoCachePrefix="cache_AxeInfo"
  if [ -r "$getAxeInfoCacheDir/$getAxeInfoCachePrefix-$AxeInfoItem" ];then
    cat "$getAxeInfoCacheDir/$getAxeInfoCachePrefix-$AxeInfoItem"
    if [ $? -eq 0 ] ; then
      return $TRUE
    else
        apos_log "Failure while reading cache file for $AxeInfoItemValue"
        #try to remove cache file
        rm -f "$getAxeInfoCacheDir/$getAxeInfoCachePrefix-$AxeInfoItem"		
    fi 
  fi
  COMMAND="immlist -a value axeInfoId=$AxeInfoItem"
  AxeInfoItemValue=$(kill_after_try 5 1 5 $COMMAND 2> /dev/null)
  local return_code=$?
  if [ $return_code -ne 0 ] ; then
      apos_log "The command $COMMAND failed with return code $return_code" 
    return $FALSE
  fi
  AxeInfoItemValue="$(echo $AxeInfoItemValue | awk -F'=' '{print $2}')"
  echo "$AxeInfoItemValue" > "$getAxeInfoCacheDir/$getAxeInfoCachePrefix-$AxeInfoItem"
  if [ $return_code -ne 0 ] ; then
        apos_log "Failure while creating cache file for $AxeInfoItemValue" 
  fi
  echo "$AxeInfoItemValue"
  return $TRUE
  }

#-------------------------------------------------------------------------------
#This is the function to stop and disable sshd daemon on sshd_config
function stop_disable_sshdconfig(){
  apos_servicemgmt disable 'lde-sshd@sshd_config.service' --stop &>/dev/null || apos_abort "failure while disabling and stopping \"lde-sshd@sshd_config\""
}

#-------------------------------------------------------------------------------
#------------------------------------------------------------------------------#
# Extending library by scanning the pluggable structure for script sourcing    #
#------------------------------------------------------------------------------#
for RESOURCE_FILE in $(find $COMMON_RES_PATH -maxdepth 1 -name '*.sh' -type f); do	
         . $RESOURCE_FILE || apos_log "failure while loading $RESOURCE_FILE"
done
