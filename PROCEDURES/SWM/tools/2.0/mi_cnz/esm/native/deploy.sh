#!/bin/bash
##
# ------------------------------------------------------------------------
#     Copyright (C) 2012 Ericsson AB. All rights reserved.
# ------------------------------------------------------------------------
##
# Name:
#       deploy.sh
# Description:
#       A script to deploy the APG43L software on the tftp server.
# Note:
#       See the maiden installation document for more information.
##
# Usage:
#       Used during APG43L maiden installation.
##
# Output:
#       None.
##
# Changelog:
# - Thu Nov 05 2020 - Pratap Reddy Uppada (xpraupp)
#    Included a check for mau_type and apg_aom_access 
#    parameters to support EvoC8200
# - Thu Oct 29 2020 - Neelam Kumar (xneelku)
#    Support for SCX with cabless OAM aceess.
# - Mon Sep 8 2018 - Gnaneswara Seshu (zbhegna)
#    Fix for removal of LDE Payload Rpm
# - Thu Sep 20 2018 - Yeswanth Vankayala (xyesvan)
#     Fix for TR HX21044
# - Tue Jun 19 2018 - Yeswanth Vankayala (xyesvan)
#      Adapotation for SwM 2.0
# - Mon May 21 2018 - Yeswanth Vankayala (xyesvan)
#   WA for GSNH issue
# - Mon Feb 12 2018 - Sowjanya Medak (XSOWMED)
# Renamed gep7Lasgep5-64 parameter to turbo_boost_cp in factoryparams.conf
# - Mon Jan 22 2018 - Raghavendra Koduri (XKODRAG)
# Support for additional parameter ge7lasge5-64 in factoryparams.conf
#   Support for GEP7_128_1600 hardware
# - Wed Jul 06 2017 - Sowjanya Medak (XSOWMED)
# Impacts to support GEP7 hardware
# - Mon Jul 25 2016 - Mallikarjuna Rao (xmalrao)
#				Added new apt-type IPSTP
# - Tue May 10 2016 - Yeswanth Vankayala (xyesvan)
#        Impacts due to smart campaign
# - Tue Feb 09 2016 - Anna Maria Santonicola (teisaam)
#   	Fix for wrong removal of AP2.conf bundles in MINI-IPA case.
# - Thu Jan 14 2016 Sindhuja Palla (XSINPAL)
#	    Impacts to support SMX architecture
# - Thu Nov 19 2015 - Roni Newatia (XRONNEW)
#   	Modified to support GEP5-64-1200
# - Wed Nov 18 2015 - Sindhuja Palla (XSINPAL)
#   	Updated Sanity checks for mau_type in factoryparam.conf
# - Mon Mar 09 2015 - Giuseppe Pontillo (QGIUPON)
#  	 Adaptation for APG-VM
# - Mon Apr 7 2014 - Pratap Reddy (XPRAUPP)
# 	cableless changes
# - Tue Mar 11 2014 Antonio Buonocunto (EANBUON)
#	Impacts to support ap2_oam 
# - Sat Fri 1 2014 Stefano Volpe (ESTEVOL)
#	Impacts to support configurable TIPC vlan and BGCI networks
# - Wed Nov 13 2013 Fabio Imperato (EFABIMP)
#	Impacts to support GEP5 for Dual AP configuration
# - Thu Oct 31 2013 Fabio Ronca (EFABRON)
#	FIX on Sanity checks for datadisk_replication_type for GEP1
# - Tue Sep 03 2013 Pratap Reddy (XPRAUPP)
#	Updated Sanity checks for datadisk_replication_type in
#	factoryparam.conf
# - Wed Jun 26 2013
#	Default partitions size updated
# - Tue Jun 18 2013 - Fabio Ronca (efabron)
#	Introuction of base mac address 
# - Mon Jun 03 2013 - Partitions size control
# - Tue May 14 2013 - Partition tool impacts
# - Tue Apr 30 2013 - installation_hw handling for GEP4
# - Fri Feb 22 2013 - LDE naming convention adaptation
# - Fri May 31 2013 - Stefano Volpe (estevol)
#	Added function fetch_shelf_architecture()
#	Added cluster conf selection for DMX environment
# - Fri Apr 12 2013 - Francesco Rainone (efrarai)
#	Fixes and workarounds.
# - Fri Apr 12 2013 - Claudia Atteo (eattcla)
#	Added operations to manage sw.tgz for Dual AP
# - Tue Mar 21 2013 - Salvatore Delle Donne (teisdel)
#       Updated Sanity checks for ap_type in factoryparam.conf
#	Added function fetch_ap_type()
#	Added cluster conf selection based on agp_type.
# - Fri Oct 26 2012 - Paolo Palmieri (epaopal)
#       Sanity checks.
# - Tue Mar 13 2012 - Paolo Palmieri (epaopal)
#       First version.
##

# --- Common variables
TRUE=$( true; echo $? )
FALSE=$( false; echo $? )
EXIT_SUCCESS=$TRUE
EXIT_FAILURE=$FALSE

isVirtual_env_profile=$TRUE
isDeployment_environment=$TRUE
isDatadisk_replication_type=$TRUE

virtual_env_profile=""
deployment_environment=""
datadisk_replication_type=""
turbo_boost_cp=""

function trim() {
  echo $1;
}

function abort() {
  echo "ABORTING: $@"
  exit $EXIT_FAILURE
}

function delete_dir() {
	if [ -d $@ ]; then
		rm -rf $@;
	else
		echo " No temporary folder to be deleted "
	fi
}



function str_replace() {
  # Local variables
  local FILE=$1
  local STATEMENT=$2
  local REPLACEMENT=$3

  # Statement replace
  if [ -f "$FILE" ]; then
    cat $FILE | grep $STATEMENT &>/dev/null
    local RET_CODE=$?
    if [ $RET_CODE -eq 0 ]; then
      sed -i "s@$STATEMENT@$REPLACEMENT@g" $FILE ||  abort "Failure while editing $FILE to change the \"$STATEMENT\" statement"
    else
      echo "WARNING: Statement \"$STATEMENT\" not found in \"$FILE\"!"
    fi
  else
    abort "\"$FILE\" not found"
  fi
}

function scabort() {
  echo "-   FAILED CHECK: $@ !"
  exit $EXIT_FAILURE
}

function scinfo() {
  echo "-   Info: $@"
}


function scisdefined() {
  local filename="$1"
  local matchstr="$2"
  local retvalue=""
  local linenr=0
  local match=""

  [ ! -f $filename ] && abort "$filename not found"
  match=$( cat $filename | grep $matchstr )
  if [ -z $match ]; then
    retvalue=${FALSE}
  else
    retvalue=${TRUE}
  fi
  echo $retvalue
}

function scparse() {
  local filename="$1"
  local matchstr="$2"
  local retvalue=""
  local linenr=0

  [ ! -f $filename ] && abort "$filename not found"
  while read cline
  do
    linenr=$(expr $linenr + 1);
    line=$(echo ${cline%%;*})
    if [ ! -z "$line" ]; then
      myname=$(trim ${line%%=*})
      myvalue=$(echo ${line#*=} | tr -d '\n')
      if [ ! -z $myname ]; then
        if [ "$myname" == "$matchstr" ]; then
	  retvalue="${myvalue}"
        fi
      fi
    fi
  done < "$filename"
  echo "${retvalue}"
}

function scregex() {
  local regex=$1
  local string=$2

  if [[ $string =~ $regex ]]; then
    echo $TRUE
  else
    echo $FALSE
  fi
}


#--------------------------------------------------------------------
function isSIMULATED() {
	
	local rCode=$FALSE
	local FOLDER_ETC="etc"
	local FILE_FP="factoryparam.conf"
  local DEPLOYMENT_ENVIRONMENT="deployment_environment"
	
	[ "$deployment_environment" == "SIMULATED" ] && rCode=$TRUE

	return $rCode
}

#--------------------------------------------------------------------
function isGEP5_VM() {
	
	local rCode=$FALSE
	local FOLDER_ETC="etc"
	local FILE_FP="factoryparam.conf"
	local INSTALLATION_HW="installation_hw"
	
	hw_type=$( scparse $FOLDER_ETC/$FILE_FP $INSTALLATION_HW )
	
	isSIMULATED && [ "$hw_type" == "GEP5" ] && rCode=$TRUE
	
	return $rCode
}

# -------------------------------------------------------------
function check_vlan() {
  local PARAM=$1
  local VLAN_ID=$2
  $( echo $VLAN_ID | grep -Eq "^[0-9]+$")
  [ $? -ne 0 ] && scabort "$PARAM must be a valid integer: $VLAN_ID"

}

# -------------------------------------------------------------
function validate_vlan(){
  local PARAM=$1
  local VLAN_ID=$2
  local SHELF_ARCHITECTURE=$(fetch_shelf_architecture)
  local SHELF_SWITCH=$( fetch_shelf_switch)
  local APG_OAM_ACCESS=$( fetch_apg_oam_access)

  if [[ "$SHELF_ARCHITECTURE" == "DMX" ||  "$SHELF_ARCHITECTURE" == "SMX" ]]; then
    if [ "$APG_OAM_ACCESS" == "NOCABLE" ]; then
    [[ "$PARAM" == 'network_10g_vlantag' || "$PARAM" == 'oam_vlanid' ]] && {
      [  "$VLAN_ID" == 'NULL' ] && scabort "$PARAM must not be empty: $VLAN_ID"
        check_vlan $PARAM $VLAN_ID
     }
    fi

    if [[ "$SHELF_ARCHITECTURE" == "DMX" && "$APG_OAM_ACCESS" == "FRONTCABLE" ]]; then
     [ "$PARAM" == 'network_10g_vlantag' ] && {
       [ "$VLAN_ID" == 'NULL' ] && scabort "$PARAM must not be empty: $VLAN_ID"
         check_vlan $PARAM $VLAN_ID
     }
   fi
   elif [[ "$SHELF_ARCHITECTURE" == "SCX" && "$APG_OAM_ACCESS" == "NOCABLE" ]]; then
    [[ "$PARAM" == 'network_10g_vlantag' || "$PARAM" == 'oam_vlanid' ]] && {
      [ "$VLAN_ID" == 'NULL' ] && scabort "$PARAM must not be empty: $VLAN_ID"
      check_vlan $PARAM $VLAN_ID
   }
  elif [[ "$SHELF_ARCHITECTURE" == "SCX" && "$SHELF_SWITCH" == "CMXB3" ]]; then
    [[ "$VLAN_ID" == 'NULL' ]] && scabort "$PARAM must not be empty: $VLAN_ID"
      check_vlan $PARAM $VLAN_ID
  fi

}

# -------------------------------------------------------------
function valid_bgci() {
	local param=$1
	local network=$2
	
	local SHELF_ARCHITECTURE=$(fetch_shelf_architecture)
	
	if [ "$SHELF_ARCHITECTURE" == "DMX" ]; then
		[ $network == 'NULL' ] && scabort "$param must not be empty: $network"
		#Only netmask lenght accepted is 24
		echo $network | grep -Eq "^((25[0-5]|2[0-4][0-9]|[0-1]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[0-1]?[0-9][0-9]?)\/24$"
		[ $? -ne 0 ] && scabort "$param must be a valid network with netmask length of 24: $network"
	fi
}

# Test an IPv4 address for validity
function valid_ip() {
  local parameter=$1
  local quad=$2
  local oldIFS=${IFS}

  IFS='.'
  set -- $quad
  if [ "$#" -ne "4" ]; then
    IFS=${oldIFS}; scabort "$parameter must have 4 parts: $quad"
  fi
  if [ "$1" -eq "0" ]; then
    IFS=${oldIFS}; scabort "First octet of $parameter must not be '0': $quad"
  fi
  if [ "$1" -eq "127" ]; then
    IFS=${oldIFS}; scabort "First octet of $parameter must not be '127': $quad"
  fi
  if [ "$1" -eq "255" ]; then
    IFS=${oldIFS}; scabort "First octet of $parameter must not be '255': $quad"
  fi
  if [ "$4" -eq "255" ]; then
    IFS=${oldIFS}; scabort "Last octet of $parameter must not be '255': $quad"
  fi
  for oct in $1 $2 $3 $4; do
    echo $oct | egrep "^[0-9]+$" >/dev/null 2>&1
    if [ "$?" -ne "0" ]; then
      IFS=${oldIFS}; scabort "The $oct octet of $parameter must be numeric: $quad"
    else
      if [ "$oct" -lt "0" -o "$oct" -gt "255" ]; then
        IFS=${oldIFS}; scabort "The $oct octet of $parameter is out of range: $quad"
      fi
    fi
  done
  echo "$quad" | grep "\.$" >/dev/null 2>&1
  if [ "$?" -eq "0" ]; then
    IFS=${oldIFS}; scabort "The trailing period of $parameter is invalid: $quad"
  fi
  IFS=${oldIFS}
}

# Test a MAC address for validity
function valid_mac() {
  local parameter=$1
  local sistine=$2
  local oldIFS=${IFS}

  IFS=':'
  set -- $sistine
  if [ "$#" -ne "6" ]; then
    IFS=${oldIFS}; scabort "$parameter must have 6 parts: $sistine"
  fi
  echo $1 | egrep "^[a-f0-9][c048]$" >/dev/null 2>&1
  if [ "$?" -ne "0" ]; then
    IFS=${oldIFS}; scinfo "The first octet of $parameter should end with '0' or '4' or '8' or 'c': $sistine !!!"
  fi
  for oct in $1 $2 $3 $4 $5 $6; do
    echo $oct | egrep "^[a-f0-9][a-f0-9]$" >/dev/null 2>&1
    if [ "$?" -ne "0" ]; then
      IFS=${oldIFS}; scabort "The $oct octet of $parameter must be a lowercase hex value: $sistine"
    fi
  done
  echo "$sistine" | grep ":$" >/dev/null 2>&1
  if [ "$?" -eq "0" ]; then
    IFS=${oldIFS}; scabort "The trailing period of $parameter is invalid: $sistine"
  fi
  IFS=${oldIFS}
}

#
# Configuration file: factoryparam.conf
#
# Parameters:
# - me_name=1
# - shelf_id=1.2.0.4
# - shelf_architecture=SCB
# - system_type=SCP
# - system_version=APG43L CD3
# - system_package=CXC1371469
# - apt_type=BSC
# - ap_type=AP1
# - ap2_oam=YES
# - apg_oam_access=FRONTCABLE/NOCABLE
# - apz_protocol_type=APZ21255_OR_LATER_TCPIP
# - installation_type=MI
# - installation_hw= GEP5 
# - virtual_env_profile=
# - deployment_environment=NOT_SIMULATED
# - installation_root=/tftpboot
# - datadisk_replication_type=MD/DRBD
# - mau_type=MAUB
# - turbo_boost_cp=TRUE/FALSE
function sanity_checks_factory_params() {
  local FOLDER_ETC="etc"
  local FILE_FP="factoryparam.conf"

  local ME_NAME="me_name"
  local SHELF_ID="shelf_id"
  local SHELF_ARCHITECTURE="shelf_architecture"
  local SHELF_SWITCH="shelf_switch"
  local SYSTEM_TYPE="system_type"
  local MAU_TYPE="mau_type"
  local SYSTEM_VERSION="system_version"
  local SYSTEM_PACKAGE="system_package"
  local APT_TYPE="apt_type"
  local APZ_PROTOCOL_TYPE="apz_protocol_type"
  local INSTALLATION_TYPE="installation_type"
  local INSTALLATION_HW="installation_hw"
  local VIRTUAL_ENV_PROFILE="virtual_env_profile"
  local DEPLOYMENT_ENVIRONMENT="deployment_environment"
  local INSTALLATION_ROOT="installation_root"
  local AP_TYPE="ap_type"
  local AP2_OAM="ap2_oam"
  local APG_OAM_ACCESS="apg_oam_access"
  local DATADISK_REPLICATION_TYPE="datadisk_replication_type"
	local TURBO_BOOST_CP="turbo_boost_cp"

  local DEF_ME_NAME="1"
  local DEF_SHELF_ID="1.2.0.4"
  local DEF_MAU_TYPE="MAUB"
  local DEF_SHELF_ARCHITECTURE="SCB"
  local DEF_SHELF_SWITCH="CMXB3"
  local DEF_SYSTEM_TYPE="SCP"
  local DEF_SYSTEM_VERSION="APG43L CD3"
  local DEF_SYSTEM_PACKAGE="CXC1371469"
  local DEF_APT_TYPE="BSC"
  local DEF_APZ_PROTOCOL_TYPE="APZ21255_OR_LATER_TCPIP"
  local DEF_INSTALLATION_TYPE="MI"
  local DEF_INSTALLATION_HW="GEP2"
  local DEF_VIRTUAL_ENV_PROFILE="VE0"
  local DEF_DEPLOYMENT_ENVIRONMENT="NOT_SIMULATED"
  local DEF_INSTALLATION_ROOT="/tftpboot"
  local DEF_AP_TYPE="AP1"
  local DEF_AP2_OAM="YES"
  local DEF_APG_OAM_ACCESS="FRONTCABLE"
  local DEF_DDISK_REPLICATION_TYPE="MD"

  value=$( scparse $FOLDER_ETC/$FILE_FP $ME_NAME )
  if [ -z "${value}" ]; then
    scabort "$ME_NAME value must be no empty"
  fi
  if [ "$value" != "$DEF_ME_NAME" ]; then
    scinfo "$ME_NAME value changed to: $value"
  fi

  value=$( scparse $FOLDER_ETC/$FILE_FP $SHELF_ID )
  if [ -z "${value}" ]; then
    scabort "$SHELF_ID value must be no empty"
  fi
  if [ $( scregex '[0-99]\.[0-99]\.[0-99]\.[0-99]' $value ) -ne $TRUE ]; then
    scabort "$SHELF_ID value not valid: $value"
  fi
  if [ "$value" != "$DEF_SHELF_ID" ]; then
    scinfo "$SHELF_ID value changed to: $value"
  fi
  
  value=$( scparse $FOLDER_ETC/$FILE_FP $MAU_TYPE )
  if [ -z "${value}" ]; then
	value="MAUB"
  fi
  if [ $( scregex '^MAUB$|^MAUS$' $value ) -ne $TRUE ]; then
    scabort "$MAU_TYPE value not valid: $value"
  fi
  if [ "$value" != "$DEF_MAU_TYPE" ]; then
    scinfo "$MAU_TYPE value changed to: $value"
  fi

  value=$( scparse $FOLDER_ETC/$FILE_FP $SHELF_ARCHITECTURE )
  shelf_arch="${value}"
  if [ -z "${value}" ]; then
    scabort "$SHELF_ARCHITECTURE value must be no empty"
  fi
  if [ $( scregex '^SCB$|^SCX$|^SMX$|^DMX$' $value ) -ne $TRUE ]; then
    scabort "$SHELF_ARCHITECTURE value not valid: $value"
  fi
  if [ "$value" != "$DEF_SHELF_ARCHITECTURE" ]; then
    scinfo "$SHELF_ARCHITECTURE value changed to: $value"
  fi

  value=$( scparse $FOLDER_ETC/$FILE_FP $SYSTEM_TYPE )
  if [ -z "${value}" ]; then
    scabort "$SYSTEM_TYPE value must be no empty"
  fi
  if [ $( scregex '^SCP$|^MCP$' $value ) -ne $TRUE ]; then
    scabort "$SYSTEM_TYPE value not valid: $value"
  fi
  if [ "$value" != "$DEF_SYSTEM_TYPE" ]; then
    scinfo "$SYSTEM_TYPE value changed to: $value"
  fi

  value=$( scparse $FOLDER_ETC/$FILE_FP $SYSTEM_VERSION )
  if [ -z "${value}" ]; then
    scabort "$SYSTEM_VERSION value must be no empty"
  fi
  if [ $( scregex '^APG43L' "${value}" ) -ne $TRUE ]; then
    scabort "$SYSTEM_VERSION value not valid: ${value}"
  fi

  value=$( scparse $FOLDER_ETC/$FILE_FP $SYSTEM_PACKAGE )
  if [ -z "${value}" ]; then
    scabort "$SYSTEM_PACKAGE value must be no empty"
  fi
  if [ "$value" != "$DEF_SYSTEM_PACKAGE" ]; then
    scabort "$SYSTEM_PACKAGE value not valid: $value"
  fi

  value=$( scparse $FOLDER_ETC/$FILE_FP $APT_TYPE )
  if [ -z "${value}" ]; then
    scabort "$APT_TYPE value must be no empty"
  fi
  if [ $( scregex '^MSC$|^HLR$|^BSC$|^WIRELINE$|^TSC$|^IPSTP$' $value ) -ne $TRUE ]; then
    scabort "$APT_TYPE value not valid: $value"
  fi
  if [ "$value" != "$DEF_APT_TYPE" ]; then
    scinfo "$APT_TYPE value changed to: $value"
  fi

  value=$( scparse $FOLDER_ETC/$FILE_FP $APZ_PROTOCOL_TYPE )
  if [ -z "${value}" ]; then
    scabort "$APZ_PROTOCOL_TYPE value must be no empty"
  fi
  if [ $( scregex '^APZ2123X_SDLC$|^APZ2123X_TCPIP$|^APZ21240_TCPIP$|^APZ21250_TCPIP$|^APZ21255_OR_LATER_TCPIP$' $value ) -ne $TRUE ]; then
    scabort "$APZ_PROTOCOL_TYPE value not valid: $value"
  fi
  if [ "$value" != "$DEF_APZ_PROTOCOL_TYPE" ]; then
    scinfo "$APZ_PROTOCOL_TYPE value changed to: $value"
  fi

  value=$( scparse $FOLDER_ETC/$FILE_FP $INSTALLATION_TYPE )
  if [ -z "${value}" ]; then
    scabort "$INSTALLATION_TYPE value must be no empty"
  fi
  if [ $( scregex '^DR$|^MI$|^OSU$' $value ) -ne $TRUE ]; then
    scabort "$INSTALLATION_TYPE value not valid: $value"
  fi
  if [ "$value" != "$DEF_INSTALLATION_TYPE" ]; then
    scinfo "$INSTALLATION_TYPE value changed to: $value"
  fi

  value=$( scparse $FOLDER_ETC/$FILE_FP $INSTALLATION_HW )
  hw_type="${value}" 

  value=$( scparse $FOLDER_ETC/$FILE_FP $TURBO_BOOST_CP )
  if [ -z $value ]; then
    turbo_boost_cp="FALSE"
  else
    turbo_boost_cp="${value}"
    scinfo "$TURBO_BOOST_CP value changed to: $value"
  fi
  [ $( scregex '^TRUE$|^FALSE$' $turbo_boost_cp ) -ne $TRUE ] &&
  scabort "$TURBO_BOOST_CP value not valid: $turbo_boost_cp"

  [[ ! "$hw_type" =~ "GEP7"  && $turbo_boost_cp == "TRUE" ]] && scabort "TURBO_BOOST_CP ($turbo_boost_cp) not supported on $hw_type"
  
  value=$( scparse $FOLDER_ETC/$FILE_FP $VIRTUAL_ENV_PROFILE )
  virtual_env_profile="${value}"
  if [ -z "${virtual_env_profile}" ]; then
    isVirtual_env_profile=$FALSE
  fi
  if [ -n "${hw_type}" ] ; then
	  if [ -n "${virtual_env_profile}" ]; then
			scabort "$INSTALLATION_HW and $VIRTUAL_ENV_PROFILE can not both be filled. These are mutually exclusive."
	  fi
	  virtual_env_profile="VE0"
    if [ $( scregex '^GEP1$|^GEP2$|^GEP4_400$|^GEP4_1600$|^GEP5_400$|^GEP5_1200$|^GEP5_1600$|^GEP5$|^GEP5_64_1200$|^GEP7$|^GEP7L_400$|^GEP7L_1600$|^GEP7_128_1600$' $hw_type ) -ne $TRUE ]; then
		scabort "$INSTALLATION_HW value not valid: $hw_type"
	  fi
	  if [[ "$hw_type" == 'GEP5_64_1200' && "${shelf_arch}" != 'DMX' ]];then
		scabort "$SHELF_ARCHITECTURE:$shelf_arch not supported on $hw_type"		
	  fi
	  if [ "$hw_type" != "$DEF_INSTALLATION_HW" ]; then
		scinfo "$INSTALLATION_HW value changed to: $hw_type"
	  fi
  else 
		if [ -z "${virtual_env_profile}" ]; then
			scabort "$INSTALLATION_HW and $VIRTUAL_ENV_PROFILE can not both be empty"
		fi
		if [ $( scregex '^VE1$' $virtual_env_profile ) -ne $TRUE ]; then
			scabort "$VIRTUAL_ENV_PROFILE value not valid: $virtual_env_profile"
		fi
		if [ "$virtual_env_profile" != "$DEF_VIRTUAL_ENV_PROFILE" ]; then
			scinfo "$VIRTUAL_ENV_PROFILE value changed to: $virtual_env_profile"
		fi 
  fi
  
  value=$( scparse $FOLDER_ETC/$FILE_FP $DEPLOYMENT_ENVIRONMENT )
  
  if [ -z $value ]; then
    deployment_environment="NOT_SIMULATED"
	isDeployment_environment=$FALSE
  else
	deployment_environment="${value}" 
  fi

  if [ $( scregex '^SIMULATED$|^NOT_SIMULATED$' $deployment_environment ) -ne $TRUE ]; then
    scabort "$DEPLOYMENT_ENVIRONMENT value not valid: $deployment_environment"
  fi
  if [ "$deployment_environment" != "$DEF_DEPLOYMENT_ENVIRONMENT" ]; then
    scinfo "$DEPLOYMENT_ENVIRONMENT value changed to: $deployment_environment"
  fi
  
  value=$( scparse $FOLDER_ETC/$FILE_FP $DATADISK_REPLICATION_TYPE )

  if [ -z $value ]; then
    datadisk_replication_type="MD"
	isDatadisk_replication_type=$FALSE
  else
	datadisk_replication_type="${value}" 
  fi
  
  [ $( scregex '^MD$|^DRBD$' $datadisk_replication_type ) -ne $TRUE ] &&
  scabort "$DATADISK_REPLICATION_TYPE value not valid: $datadisk_replication_type"
  #[ "$datadisk_replication_type" != "$DEF_DDISK_REPLICATION_TYPE" ] && 
  #scinfo "$DATADISK_REPLICATION_TYPE value changed to: $datadisk_replication_type"
  [[ "$hw_type" =~ "GEP4" || "$hw_type" =~ "GEP5" || "$hw_type" =~ "GEP7" ]] && [[ "$datadisk_replication_type" != "DRBD" ]] &&
  scabort "data disk replication type ($datadisk_replication_type) not supported on $hw_type"
  if [ "$deployment_environment" == "SIMULATED" ]; then
		[ "$datadisk_replication_type" != "DRBD" ] &&
		scabort "data disk replication type ($datadisk_replication_type) not supported on $deployment_environment"
  elif [[ "$hw_type" == "GEP1" || "$hw_type" == "GEP2" ]]; then
		if [ "$datadisk_replication_type" != "MD" ]; then
			scabort "data disk replication type ($datadisk_replication_type) not supported on $hw_type"
		fi;
  fi;

  value=$( scparse $FOLDER_ETC/$FILE_FP $SHELF_SWITCH )
   if [[ "$hw_type" =~ "GEP4" || "$hw_type" =~ "GEP5" || "$hw_type" =~ "GEP7" ]]; then
   [[ "${shelf_arch}" == 'DMX' || "${shelf_arch}" == 'SCX' || "${shelf_arch}" == 'SMX' ]] && {
     if [ -z "${value}" ]; then
      	scabort "$SHELF_SWITCH value must not be empty"
     fi
     if [ $( scregex '^SCB-RP$|^SCXB3$|^CMXB3$|^SMXB$' $value ) -ne $TRUE ]; then
      	scabort "$SHELF_SWITCH value not valid: $value"
     fi
	if [[ "$hw_type" == 'GEP5_64_1200' && "${value}" != 'CMXB3' ]];then
		scabort "$SHELF_SWITCH:$value not supported on $hw_type"
	fi
	 if [ "$value" != "$DEF_SHELF_SWITCH" ]; then
	 	scinfo "$SHELF_SWITCH value changed to: $value"
	 fi	
   }
  fi
	
  value=$( scparse $FOLDER_ETC/$FILE_FP $APG_OAM_ACCESS)
  APG_OAM_CHECK=$( scisdefined $FOLDER_ETC/$FILE_FP $APG_OAM_ACCESS)
  if [ "$APG_OAM_CHECK" -eq "$TRUE" ]; then
    [ -z "${value}" ] && scabort "$APG_OAM_ACCESS value must not be empty"
  fi

  if [ "${shelf_arch}" == 'SCX' ]; then 
    if [ $( scregex '^GEP7L_.*$' $hw_type ) -eq $TRUE ]; then
      [ "${value}" != 'NOCABLE' ] && scabort "$APG_OAM_ACCESS with $value not supported for GEP7L with $shelf_arch"
    fi 
  elif [[ "${shelf_arch}" != 'DMX' && "${shelf_arch}" != 'SMX' ]]; then
    [ "${value}" != 'FRONTCABLE' ] && scabort "$APG_OAM_ACCESS with $value not supported for $shelf_arch"
  else
    if [ $( scregex '^GEP1$|^GEP2$' $hw_type ) -eq $TRUE ]; then
      [ "${value}" != "FRONTCABLE" ] && scabort "$APG_OAM_ACCESS with $value not supported for $shelf_arch"
    else
      [ "${value}" != "NOCABLE" ] && scabort "$APG_OAM_ACCESS value not valid: $value"
    fi
  fi

 # mau_type verification for EvoC8200
  value=$( scparse $FOLDER_ETC/$FILE_FP $MAU_TYPE)
  if [ "${shelf_arch}" == 'SCX' ]; then
    if [ $( scregex '^GEP7L_.*$' $hw_type ) -eq $TRUE ]; then
      [ "${value}" != 'MAUS' ] && scabort "$MAU_TYPE with $value not supported for GEP7L with $shelf_arch"
    fi
  fi
  
  value=$( scparse $FOLDER_ETC/$FILE_FP $INSTALLATION_ROOT )
  if [ -z "${value}" ]; then
    scabort "$INSTALLATION_ROOT value must be no empty"
  fi
  value_wo_space=$( echo "${value}" | sed 's/ //g')
  if [ "${value}" != "${value_wo_space}" ]; then
    scabort "$INSTALLATION_ROOT value contains a whitespace: $value"
  fi
  if [ $( scregex '^\/.*(\/.*)*' $value ) -ne $TRUE ]; then
    scabort "$INSTALLATION_ROOT value not valid: $value"
  fi
  if [ $( scregex '.*\/$' $value ) -eq $TRUE ]; then
    scabort "$INSTALLATION_ROOT value not valid: $value"
  fi
  if [ -d "${value}" ]; then
    shopt -q nullglob || local resetnullglob=1
    shopt -s nullglob
    shopt -q dotglob || local resetdotglob=1
    shopt -s dotglob
    local files=(/some/dir/*)
    if [ "$files" ]; then
      pushd "${value}" > /dev/null 2>&1
      if [ ! -f "initrd" ] && [ ! -f "vmlinuz" ]; then
        scabort "$INSTALLATION_ROOT value points to an unusual folder: $value"
      fi
    fi
    popd > /dev/null 2>&1
    [ "$resetdotglob" ] && shopt -u dotglob
    [ "$resetnullglob" ] && shopt -u nullglob;
  fi
  if [ "$value" != "$DEF_INSTALLATION_ROOT" ]; then
    scinfo "$INSTALLATION_ROOT value changed to: $value"
  fi
  
  #CHECK THAT THE AP TYPE IS EITHER AP1 OR AP2
  #EMPTY VALUE OR VALUE EITHER THEN  AP1 OR AP2
  #IS A NOT VALID VALUE
  value=$( scparse $FOLDER_ETC/$FILE_FP $AP_TYPE )
  if [ -z "${value}" ]; then
    scabort "$AP_TYPE value must be no empty"
  fi
  if [ $( scregex '^AP1$|^AP2$' $value ) -ne $TRUE ]; then
    scabort "$AP_TYPE value not valid: $value"
  fi
  if [ "$value" != "$DEF_AP_TYPE" ]; then
    scinfo "$AP_TYPE value changed to: $value"
  fi

  #Perform the validation of ap2_oam
  value=$( scparse $FOLDER_ETC/$FILE_FP $AP2_OAM )
  AP_TYPE_CHECK=$( scparse $FOLDER_ETC/$FILE_FP $AP_TYPE )
  if [ "$AP_TYPE_CHECK" = "AP1" ];then
    AP2_OAM_CHECK=$( scisdefined $FOLDER_ETC/$FILE_FP $AP2_OAM )
    if [ "$AP2_OAM_CHECK" = "$TRUE" ]; then
      scabort "$AP2_OAM value must be used only in AP2"
    fi
  else
    if [ -z "${value}" ]; then
      scabort "$AP2_OAM value must be no empty"
    fi
    if [ $( scregex '^YES$|^NO$' $value ) -ne $TRUE ]; then
      scabort "$AP2_OAM value not valid: $value"
    fi
    if [ "$value" != "$DEF_AP2_OAM" ]; then
      scinfo "$AP2_OAM value changed to: $value"
    fi
  fi
}

#
# Configuration file: installation.conf
#
# Parameters:
# - root_password_hash=$2y$10$Z95LNixlC9JulkDpSc9M/up8ccIjlvWXmgd9ydTGOn5vqTHw7fHcK
# - standalone_install=n
# - disk_device_path=<system_disk_device>
# - partition_boot_size=4G
# - partition_log_size=20G
# - partition_root_size=8G
# - partition_swap_size=6G
# - shared_filesystem_size=15G
# - cluster_install_reboot=y
# - disk_cache=y
# - control_rpm_name=<linux_control_x86_64_rpm>
#
function sanity_checks_install_params() {
  local FOLDER_ETC="etc"
  local FILE_FP="installation.conf"

  local ROOT_PASSWORD_HASH="root_password_hash"
  local STANDALONE_INSTALL="standalone_install"
  local DISK_DEVICE_PATH="disk_device_path"
  local PARTITION_BOOT_SIZE="partition_boot_size"
  local PARTITION_LOG_SIZE="partition_log_size"
  local PARTITION_ROOT_SIZE="partition_root_size"
  local PARTITION_SWAP_SIZE="partition_swap_size"
  local SHARED_FILESYSTEM_SIZE="shared_filesystem_size"
  local CLUSTER_INSTALL_REBOOT="cluster_install_reboot"
  local DISK_CACHE="disk_cache"
  local CONTROL_RPM_NAME="control_rpm_name"

  local DEF_ROOT_PASSWORD_HASH="\$2y\$10\$Z95LNixlC9JulkDpSc9M/up8ccIjlvWXmgd9ydTGOn5vqTHw7fHcK"
  local DEF_STANDALONE_INSTALL="n"
  local DEF_DISK_DEVICE_PATH="<system_disk_device>"
  local DEF_PARTITION_BOOT_SIZE_GEP1_2="4Gb"
  local DEF_PARTITION_BOOT_SIZE_GEP5_7="4Gb"
  local DEF_PARTITION_BOOT_SIZE_GEP5_VM="4Gb"
  local DEF_PARTITION_LOG_SIZE_GEP1_2="20Gb"
  local DEF_PARTITION_LOG_SIZE_GEP5_7="25Gb"
  local DEF_PARTITION_LOG_SIZE_GEP5_VM="8Gb"
  local DEF_PARTITION_ROOT_SIZE_GEP1_2="8Gb"
  local DEF_PARTITION_ROOT_SIZE_GEP5_7="12Gb"
  local DEF_PARTITION_ROOT_SIZE_GEP5_VM="8Gb"
  local DEF_PARTITION_SWAP_SIZE_GEP1_2="6Gb"
  local DEF_SHARED_FILESYSTEM_SIZE_GEP1_2="15Gb"
  local DEF_SHARED_FILESYSTEM_SIZE_GEP5_7="50Gb"
  local DEF_SHARED_FILESYSTEM_SIZE_GEP5_VM="16Gb"
  local DEF_CLUSTER_INSTALL_REBOOT="y"
  local DEF_DISK_CACHE="y"
  local DEF_CONTROL_RPM_NAME="<linux_control_x86_64_rpm>"

  if [ -n "$VIRTUAL_ENV_PROFILE" ]; then
     scabort "virtual_env_profile value not yet supported: $VIRTUAL_ENV_PROFILE"
  fi
  
  value=$( scparse $FOLDER_ETC/$FILE_FP $ROOT_PASSWORD_HASH )
  if [ -z "${value}" ]; then
    scabort "$ROOT_PASSWORD_HASH value must be no empty"
  fi
  if [ $( scregex '^\$2y\$10\$' "${value}" ) -ne $TRUE ]; then
    scabort "$ROOT_PASSWORD_HASH value not valid: ${value}"
  fi
  if [ "${value}" != "${DEF_ROOT_PASSWORD_HASH}" ]; then
    scinfo "$ROOT_PASSWORD_HASH value changed to: $value"
  fi

  value=$( scparse $FOLDER_ETC/$FILE_FP $STANDALONE_INSTALL )
  if [ -z "${value}" ]; then
    scabort "$STANDALONE_INSTALL value must be no empty"
  fi
  if [ "$value" != "$DEF_STANDALONE_INSTALL" ]; then
    scabort "$STANDALONE_INSTALL value not valid: $value"
  fi

  value=$( scparse $FOLDER_ETC/$FILE_FP $DISK_DEVICE_PATH )
  if [ -z "${value}" ]; then
    scabort "$DISK_DEVICE_PATH value must be no empty"
  fi
  if [ "$value" != "$DEF_DISK_DEVICE_PATH" ]; then
    scabort "$DISK_DEVICE_PATH value not valid: $value"
  fi

  value=$( scparse $FOLDER_ETC/$FILE_FP $PARTITION_BOOT_SIZE )
  if [ -z "${value}" ]; then
    scabort "$PARTITION_BOOT_SIZE value must be no empty"
  else
    if [[ "$INST_HW" == "GEP1" || "$INST_HW" == "GEP2" ]]; then
      if [ "$value" != "$DEF_PARTITION_BOOT_SIZE_GEP1_2" ]; then
        scabort "$PARTITION_BOOT_SIZE value not valid: $value"
      fi
    elif isGEP5_VM  ; then
	    if [ "$value" != "$DEF_PARTITION_BOOT_SIZE_GEP5_VM" ]; then
        scabort "$PARTITION_BOOT_SIZE value not valid: $value"
	    fi
	  else
      if [ "$value" != "$DEF_PARTITION_BOOT_SIZE_GEP5_7" ]; then
        scabort "$PARTITION_BOOT_SIZE value not valid: $value"
      fi
    fi
  fi
  
  value=$( scparse $FOLDER_ETC/$FILE_FP $PARTITION_LOG_SIZE )
  if [ -z "${value}" ]; then
    scabort "$PARTITION_LOG_SIZE value must be no empty"
  else
    if [[ "$INST_HW" == "GEP1" || "$INST_HW" == "GEP2" ]]; then
      if [ "$value" != "$DEF_PARTITION_LOG_SIZE_GEP1_2" ]; then
        scabort "$PARTITION_LOG_SIZE value not valid: $value"
      fi
    elif  isGEP5_VM ; then
	    if [ "$value" != "$DEF_PARTITION_LOG_SIZE_GEP5_VM" ]; then
        scabort "$PARTITION_LOG_SIZE value not valid: $value"
	    fi
    else
      if [ "$value" != "$DEF_PARTITION_LOG_SIZE_GEP5_7" ]; then
        scabort "$PARTITION_LOG_SIZE value not valid: $value"
      fi
    fi
  fi
  value=$( scparse $FOLDER_ETC/$FILE_FP $PARTITION_ROOT_SIZE )
  if [ -z "${value}" ]; then
    scabort "$PARTITION_ROOT_SIZE value must be no empty"
  else
    if [[ "$INST_HW" == "GEP1" || "$INST_HW" == "GEP2" ]]; then
      if [ "$value" != "$DEF_PARTITION_ROOT_SIZE_GEP1_2" ]; then
        scabort "$PARTITION_ROOT_SIZE value not valid: $value"
      fi
    elif  isGEP5_VM ; then
	    if [ "$value" != "$DEF_PARTITION_ROOT_SIZE_GEP5_VM" ]; then
        scabort "$PARTITION_ROOT_SIZE value not valid: $value"
	    fi
    else
      if [ "$value" != "$DEF_PARTITION_ROOT_SIZE_GEP5_7" ]; then
        scabort "$PARTITION_ROOT_SIZE value not valid: $value"
      fi
    fi
  fi
  if [[ "$INST_HW" == "GEP1" || "$INST_HW" == "GEP2" ]]; then
    value=$( scparse $FOLDER_ETC/$FILE_FP $PARTITION_SWAP_SIZE )
    if [ -z "${value}" ]; then
      scabort "$PARTITION_SWAP_SIZE value must be no empty"
    fi
    if [ "$value" != "$DEF_PARTITION_SWAP_SIZE_GEP1_2" ]; then
      scabort "$PARTITION_SWAP_SIZE value not valid: $value"
    fi
  elif [[ "$INST_HW" == GEP4* || "$INST_HW" == GEP5* || "$INST_HW" == GEP7* ]]; then
    value=$( scparse $FOLDER_ETC/$FILE_FP $PARTITION_SWAP_SIZE )
    if [ -n "${value}" ]; then
      scabort "$PARTITION_SWAP_SIZE value must be empty"
    fi
  fi
  value=$( scparse $FOLDER_ETC/$FILE_FP $SHARED_FILESYSTEM_SIZE )
  if [ -z "${value}" ]; then
    scabort "$SHARED_FILESYSTEM_SIZE value must be no empty"
  else
    if [[ "$INST_HW" == "GEP1" || "$INST_HW" == "GEP2" ]]; then
      if [ "$value" != "$DEF_SHARED_FILESYSTEM_SIZE_GEP1_2" ]; then
        scabort "$SHARED_FILESYSTEM_SIZE value not valid: $value"
      fi
    elif  isGEP5_VM ; then
	    if [ "$value" != "$DEF_SHARED_FILESYSTEM_SIZE_GEP5_VM" ]; then
        scabort "$SHARED_FILESYSTEM_SIZE value not valid: $value"
	    fi
    else
      if [ "$value" != "$DEF_SHARED_FILESYSTEM_SIZE_GEP5_7" ]; then
        scabort "$SHARED_FILESYSTEM_SIZE value not valid: $value"
      fi
    fi
  fi

  value=$( scparse $FOLDER_ETC/$FILE_FP $CLUSTER_INSTALL_REBOOT )
  if [ -z "${value}" ]; then
    scabort "$CLUSTER_INSTALL_REBOOT value must be no empty"
  fi
  if [ "$value" != "$DEF_CLUSTER_INSTALL_REBOOT" ]; then
    scabort "$CLUSTER_INSTALL_REBOOT value not valid: $value"
  fi

  value=$( scparse $FOLDER_ETC/$FILE_FP $DISK_CACHE )
  if [ -z "${value}" ]; then
    scabort "$DISK_CACHE value must be no empty"
  fi
  if [ "$value" != "$DEF_DISK_CACHE" ]; then
    scabort "$DISK_CACHE value not valid: $value"
  fi

  value=$( scparse $FOLDER_ETC/$FILE_FP $CONTROL_RPM_NAME )
  if [ -z "${value}" ]; then
    scabort "$CONTROL_RPM_NAME value must be no empty"
  fi
  if [ "$value" != "$DEF_CONTROL_RPM_NAME" ]; then
    scabort "$CONTROL_RPM_NAME value not valid: $value"
  fi
}

#
# Configuration file: installation.conf
#
# Parameters:
# - root_password_hash=$2y$10$Z95LNixlC9JulkDpSc9M/up8ccIjlvWXmgd9ydTGOn5vqTHw7fHcK
# - standalone_install=y
# - standalone_volatile_logs=y
# - disk_device_path=/dev/sda
# - control_rpm_name=<linux_control_x86_64_rpm>
#
function sanity_checks_install_flash_params() {
  local FOLDER_ETC="flash/etc"
  local FILE_FP="installation.conf"

  local ROOT_PASSWORD_HASH="root_password_hash"
  local STANDALONE_INSTALL="standalone_install"
  local STANDALONE_VOLATILE_LOGS="standalone_volatile_logs"
  local DISK_DEVICE_PATH="disk_device_path"
  local CONTROL_RPM_NAME="control_rpm_name"

  local DEF_STANDALONE_INSTALL="y"
  local DEF_STANDALONE_VOLATILE_LOGS="y"
  local DEF_DISK_DEVICE_PATH="/dev/sda"
  local DEF_CONTROL_RPM_NAME="<linux_control_x86_64_rpm>"

  value=$( scparse $FOLDER_ETC/$FILE_FP $ROOT_PASSWORD_HASH )
  if [ -z "${value}" ]; then
    scabort "$ROOT_PASSWORD_HASH value must be no empty"
  fi
  if [ $( scregex '^\$2y\$10\$' "${value}" ) -ne $TRUE ]; then
    scabort "$ROOT_PASSWORD_HASH value not valid: ${value}"
  fi
  if [ "${value}" != "${DEF_ROOT_PASSWORD_HASH}" ]; then
    scinfo "$ROOT_PASSWORD_HASH value changed to: $value"
  fi

  value=$( scparse $FOLDER_ETC/$FILE_FP $STANDALONE_INSTALL )
  if [ -z "${value}" ]; then
    scabort "$STANDALONE_INSTALL value must be no empty"
  fi
  if [ "$value" != "$DEF_STANDALONE_INSTALL" ]; then
    scabort "$STANDALONE_INSTALL value not valid: $value"
  fi

  value=$( scparse $FOLDER_ETC/$FILE_FP $STANDALONE_VOLATILE_LOGS )
  if [ -z "${value}" ]; then
    scabort "$STANDALONE_VOLATILE_LOGS value must be no empty"
  fi
  if [ "$value" != "$DEF_STANDALONE_VOLATILE_LOGS" ]; then
    scabort "$STANDALONE_VOLATILE_LOGS value not valid: $value"
  fi

  # Need to be updated
  #value=$( scparse $FOLDER_ETC/$FILE_FP $DISK_DEVICE_PATH )
  #if [ -z "${value}" ]; then
  #  scabort "$DISK_DEVICE_PATH value must be no empty"
  #fi
  #if [ "$value" != "$DEF_DISK_DEVICE_PATH" ]; then
  #  scabort "$DISK_DEVICE_PATH value not valid: $value"
  #fi

  value=$( scparse $FOLDER_ETC/$FILE_FP $CONTROL_RPM_NAME )
  if [ -z "${value}" ]; then
    scabort "$CONTROL_RPM_NAME value must be no empty"
  fi
  if [ "$value" != "$DEF_CONTROL_RPM_NAME" ]; then
    scabort "$CONTROL_RPM_NAME value not valid: $value"
  fi
}

#
# Configuration file: siteparam.conf
#
# Parameters:
# - cluster_timezone=UTC
# - public_network_ipv4_address=10.246.15.0
# - public_network_ipv4_prefix=24
# - public2_network_ipv4_address=
# - public2_network_ipv4_prefix=
# - physep_network_ipv4_address=
# - physep_network_ipv4_prefix=
# - node1_base_mac_address=00:11:22:33:44:54
# - node2_base_mac_address=00:21:22:33:44:54
# - node1_mac_address_eth0=00:11:22:33:44:51
# - node1_mac_address_eth1=00:11:22:33:44:52
# - node1_mac_address_eth2=00:11:22:33:44:53
# - node1_mac_address_eth3=00:11:22:33:44:54
# - node1_mac_address_eth4=00:11:22:33:44:55
# - node1_mac_address_eth5=00:11:22:33:44:56
# - node1_mac_address_eth6=00:11:22:33:44:57
# - node2_mac_address_eth0=00:21:22:33:44:51
# - node2_mac_address_eth1=00:21:22:33:44:52
# - node2_mac_address_eth2=00:21:22:33:44:53
# - node2_mac_address_eth3=00:21:22:33:44:54
# - node2_mac_address_eth4=00:21:22:33:44:55
# - node2_mac_address_eth5=00:21:22:33:44:56
# - node2_mac_address_eth6=00:21:22:33:44:57
# - node1_mac_address_mvl0=
# - node1_mac_address_mvl1=
# - node2_mac_address_mvl0=
# - node2_mac_address_mvl1=
# - node1_public_network_ipv4_ip_address=10.246.15.30
# - node2_public_network_ipv4_ip_address=10.246.15.31
# - cluster_public_network_ipv4_ip_address=10.246.15.32
# - node1_public2_network_ipv4_ip_address=
# - node2_public2_network_ipv4_ip_address=
# - cluster_public2_network_ipv4_ip_address=
# - physep_network_ipv4_gateway_ip_address=
# - default_network_ipv4_gateway_ip_address=10.246.15.1
# - cluster_keymap=us
#
function sanity_checks_site_params() {
  local FOLDER_ETC="etc"
  local FILE_FP="siteparam.conf"
  local CLUSTER_TIMEZONE="cluster_timezone"
  local PUBLIC_NETWORK_IPV4_ADDRESS="public_network_ipv4_address"
  local PUBLIC_NETWORK_IPV4_PREFIX="public_network_ipv4_prefix"
  local PUBLIC2_NETWORK_IPV4_ADDRESS="public2_network_ipv4_address"
  local PUBLIC2_NETWORK_IPV4_PREFIX="public2_network_ipv4_prefix"
  local PHYSEP_NETWORK_IPV4_ADDRESS="physep_network_ipv4_address"
  local PHYSEP_NETWORK_IPV4_PREFIX="physep_network_ipv4_prefix"
  local NODE1_BASE_MAC_ADDRESS="node1_base_mac_address"
  local NODE2_BASE_MAC_ADDRESS="node2_base_mac_address"
  if [[ "$hw_type" =~ "GEP1" || "$hw_type" =~ "GEP2" ||"$hw_type" =~ "GEP4" ||"$hw_type" =~ "GEP5" ]]; then
    local NODE1_MAC_ADDRESS_ETH0="node1_mac_address_eth0"
    local NODE1_MAC_ADDRESS_ETH1="node1_mac_address_eth1"
    local NODE2_MAC_ADDRESS_ETH0="node2_mac_address_eth0"
    local NODE2_MAC_ADDRESS_ETH1="node2_mac_address_eth1"
  fi
  local NODE1_MAC_ADDRESS_ETH2="node1_mac_address_eth2"
  local NODE1_MAC_ADDRESS_ETH3="node1_mac_address_eth3"
  local NODE1_MAC_ADDRESS_ETH4="node1_mac_address_eth4"
  local NODE1_MAC_ADDRESS_ETH5="node1_mac_address_eth5"
  local NODE1_MAC_ADDRESS_ETH6="node1_mac_address_eth6"
  local NODE1_MAC_ADDRESS_ETH7="node1_mac_address_eth7"
  local NODE1_MAC_ADDRESS_ETH8="node1_mac_address_eth8"
  local NODE2_MAC_ADDRESS_ETH2="node2_mac_address_eth2"
  local NODE2_MAC_ADDRESS_ETH3="node2_mac_address_eth3"
  local NODE2_MAC_ADDRESS_ETH4="node2_mac_address_eth4"
  local NODE2_MAC_ADDRESS_ETH5="node2_mac_address_eth5"
  local NODE2_MAC_ADDRESS_ETH6="node2_mac_address_eth6"
  local NODE2_MAC_ADDRESS_ETH7="node2_mac_address_eth7"
  local NODE2_MAC_ADDRESS_ETH8="node2_mac_address_eth8"
  local NODE1_MAC_ADDRESS_MVL0="node1_mac_address_mvl0"
  local NODE1_MAC_ADDRESS_MVL1="node1_mac_address_mvl1"
  local NODE1_MAC_ADDRESS_MVL2="node1_mac_address_mvl2"
  local NODE2_MAC_ADDRESS_MVL0="node2_mac_address_mvl0"
  local NODE2_MAC_ADDRESS_MVL1="node2_mac_address_mvl1"
  local NODE2_MAC_ADDRESS_MVL2="node2_mac_address_mvl2"
  local NODE1_PUBLIC_NETWORK_IPV4_IP_ADDRESS="node1_public_network_ipv4_ip_address"
  local NODE2_PUBLIC_NETWORK_IPV4_IP_ADDRESS="node2_public_network_ipv4_ip_address"
  local CLUSTER_PUBLIC_NETWORK_IPV4_IP_ADDRESS="cluster_public_network_ipv4_ip_address"
  local NODE1_PUBLIC2_NETWORK_IPV4_IP_ADDRESS="node1_public2_network_ipv4_ip_address"
  local NODE2_PUBLIC2_NETWORK_IPV4_IP_ADDRESS="node2_public2_network_ipv4_ip_address"
  local CLUSTER_PUBLIC2_NETWORK_IPV4_IP_ADDRESS="cluster_public2_network_ipv4_ip_address"
  local PHYSEP_NETWORK_IPV4_GATEWAY_IP_ADDRESS="physep_network_ipv4_gateway_ip_address"
  local DEFAULT_NETWORK_IPV4_GATEWAY_IP_ADDRESS="default_network_ipv4_gateway_ip_address"
  local NETWORK_10G_VLANTAG="network_10g_vlantag"
  local TIPC_VLANTAG="tipc_vlantag"
  local BGCI_A_NETWORK="bgci_a_network"
  local BGCI_B_NETWORK="bgci_b_network"
  local OAM_VLANID="oam_vlanid"
  local CLUSTER_KEYMAP="cluster_keymap"

  local DEF_CLUSTER_TIMEZONE="UTC"
  local DEF_PUBLIC_NETWORK_IPV4_ADDRESS="10.246.15.0"
  local DEF_PUBLIC_NETWORK_IPV4_PREFIX="24"
  local DEF_PUBLIC2_NETWORK_IPV4_ADDRESS=""
  local DEF_PUBLIC2_NETWORK_IPV4_PREFIX=""
  local DEF_PHYSEP_NETWORK_IPV4_ADDRESS=""
  local DEF_PHYSEP_NETWORK_IPV4_PREFIX=""
  local DEF_NODE1_BASE_MAC_ADDRESS="00:11:22:33:44:54"
  local DEF_NODE2_BASE_MAC_ADDRESS="00:21:22:33:44:54"
  if [[ "$hw_type" =~ "GEP1" || "$hw_type" =~ "GEP2" ||"$hw_type" =~ "GEP4" ||"$hw_type" =~ "GEP5" ]]; then
    local DEF_NODE1_MAC_ADDRESS_ETH0="00:11:22:33:44:51"
    local DEF_NODE1_MAC_ADDRESS_ETH1="00:11:22:33:44:52"
    local DEF_NODE2_MAC_ADDRESS_ETH0="00:21:22:33:44:51"
    local DEF_NODE2_MAC_ADDRESS_ETH1="00:21:22:33:44:52"
  fi
  local DEF_NODE1_MAC_ADDRESS_ETH2="00:11:22:33:44:53"
  local DEF_NODE1_MAC_ADDRESS_ETH3="00:11:22:33:44:54"
  local DEF_NODE1_MAC_ADDRESS_ETH4="00:11:22:33:44:55"
  local DEF_NODE1_MAC_ADDRESS_ETH5="00:11:22:33:44:56"
  local DEF_NODE1_MAC_ADDRESS_ETH6="00:11:22:33:44:57"
  local DEF_NODE1_MAC_ADDRESS_ETH7="00:11:22:33:44:58"
  local DEF_NODE1_MAC_ADDRESS_ETH8="00:11:22:33:44:59"
  local DEF_NODE2_MAC_ADDRESS_ETH2="00:21:22:33:44:53"
  local DEF_NODE2_MAC_ADDRESS_ETH3="00:21:22:33:44:54"
  local DEF_NODE2_MAC_ADDRESS_ETH4="00:21:22:33:44:55"
  local DEF_NODE2_MAC_ADDRESS_ETH5="00:21:22:33:44:56"
  local DEF_NODE2_MAC_ADDRESS_ETH6="00:21:22:33:44:57"
  local DEF_NODE2_MAC_ADDRESS_ETH7="00:21:22:33:44:58"
  local DEF_NODE2_MAC_ADDRESS_ETH8="00:21:22:33:44:59"
  local DEF_NODE1_MAC_ADDRESS_MVL0=""
  local DEF_NODE1_MAC_ADDRESS_MVL1=""
  local DEF_NODE1_MAC_ADDRESS_MVL2=""
  local DEF_NODE2_MAC_ADDRESS_MVL0=""
  local DEF_NODE2_MAC_ADDRESS_MVL1=""
  local DEF_NODE2_MAC_ADDRESS_MVL2=""
  local DEF_NODE1_PUBLIC_NETWORK_IPV4_IP_ADDRESS="10.246.15.30"
  local DEF_NODE2_PUBLIC_NETWORK_IPV4_IP_ADDRESS="10.246.15.31"
  local DEF_CLUSTER_PUBLIC_NETWORK_IPV4_IP_ADDRESS="10.246.15.32"
  local DEF_NODE1_PUBLIC2_NETWORK_IPV4_IP_ADDRESS=""
  local DEF_NODE2_PUBLIC2_NETWORK_IPV4_IP_ADDRESS=""
  local DEF_CLUSTER_PUBLIC2_NETWORK_IPV4_IP_ADDRESS=""
  local DEF_PHYSEP_NETWORK_IPV4_GATEWAY_IP_ADDRESS=""
  local DEF_DEFAULT_NETWORK_IPV4_GATEWAY_IP_ADDRESS="10.246.15.1"
  local DEF_NETWORK_10G_VLANTAG=""
  local DEF_TIPC_VLANTAG=""
  local DEF_OAM_VLANID=""
  local DEF_BGCI_A_NETWORK="192.254.15.0/24"
  local DEF_BGCI_A_NETWORK="192.254.16.0/24"
  local DEF_CLUSTER_KEYMAP="us"

  value=$( scparse $FOLDER_ETC/$FILE_FP $CLUSTER_TIMEZONE )
  if [ -z "${value}" ]; then
    scabort "$CLUSTER_TIMEZONE value must be no empty"
  fi
  if [ "$value" != "$DEF_CLUSTER_TIMEZONE" ]; then
    scinfo "$CLUSTER_TIMEZONE value changed to: $value"
  fi

  value=$( scparse $FOLDER_ETC/$FILE_FP $PUBLIC_NETWORK_IPV4_ADDRESS )
  if [ -z "${value}" ]; then
    scabort "$PUBLIC_NETWORK_IPV4_ADDRESS value must be no empty"
  fi
  valid_ip $PUBLIC_NETWORK_IPV4_ADDRESS $value
  if [ "$value" != "$DEF_PUBLIC_NETWORK_IPV4_ADDRESS" ]; then
    scinfo "$PUBLIC_NETWORK_IPV4_ADDRESS value changed to: $value"
  fi

  value=$( scparse $FOLDER_ETC/$FILE_FP $PUBLIC_NETWORK_IPV4_PREFIX )
  if [ -z "${value}" ]; then
    scabort "$PUBLIC_NETWORK_IPV4_PREFIX value must be no empty"
  fi
  echo $value | egrep "^[0-9]+$" >/dev/null 2>&1
  if [ "$?" -ne "0" ]; then
    scabort "$PUBLIC_NETWORK_IPV4_PREFIX value must be numeric: $value"
  fi
  if [[ $value -lt 0 || $value -gt 32 ]]; then
    scabort "$PUBLIC_NETWORK_IPV4_PREFIX value is not valid: $value"
  fi
  if [ "$value" != "$DEF_PUBLIC_NETWORK_IPV4_PREFIX" ]; then
    scinfo "$PUBLIC_NETWORK_IPV4_PREFIX value changed to: $value"
  fi

  value=$( scparse $FOLDER_ETC/$FILE_FP $PUBLIC2_NETWORK_IPV4_ADDRESS )
  if [ -n "${value}" ]; then
    scabort "$PUBLIC2_NETWORK_IPV4_ADDRESS value must be empty"
  fi

  value=$( scparse $FOLDER_ETC/$FILE_FP $PUBLIC2_NETWORK_IPV4_PREFIX )
  if [ -n "${value}" ]; then
    scabort "$PUBLIC2_NETWORK_IPV4_PREFIX value must be empty"
  fi

  value=$( scparse $FOLDER_ETC/$FILE_FP $PHYSEP_NETWORK_IPV4_ADDRESS )
  if [ -n "${value}" ]; then
    scabort "$PHYSEP_NETWORK_IPV4_ADDRESS value must be empty"
  fi

  value=$( scparse $FOLDER_ETC/$FILE_FP $PHYSEP_NETWORK_IPV4_PREFIX )
  if [ -n "${value}" ]; then
    scabort "$PHYSEP_NETWORK_IPV4_PREFIX value must be empty"
  fi

  value=$( scparse $FOLDER_ETC/$FILE_FP $NODE1_BASE_MAC_ADDRESS )
  if [ -z "${value}" ]; then

    # if the mac base address for the Node 2 is specified also the mac base address for the Node1 must be specified
    value=$( scparse $FOLDER_ETC/$FILE_FP $NODE2_BASE_MAC_ADDRESS )
    if [ -n "${value}" ]; then
      scabort "$NODE1_BASE_MAC_ADDRESS value must be no empty"
    fi    
    if [[ $INST_HW != GEP7* ]]; then
      value=$( scparse $FOLDER_ETC/$FILE_FP $NODE1_MAC_ADDRESS_ETH0 )
      if [ -z "${value}" ]; then
        scabort "$NODE1_MAC_ADDRESS_ETH0 value must be no empty"
      fi
      valid_mac $NODE1_MAC_ADDRESS_ETH0 $value
      if [ "$value" != "$DEF_NODE1_MAC_ADDRESS_ETH0" ]; then
        scinfo "$NODE1_MAC_ADDRESS_ETH0 value changed to: $value"
      fi

      value=$( scparse $FOLDER_ETC/$FILE_FP $NODE1_MAC_ADDRESS_ETH1 )
      if [ -z "${value}" ]; then
        scabort "$NODE1_MAC_ADDRESS_ETH1 value must be no empty"
      fi
      valid_mac $NODE1_MAC_ADDRESS_ETH1 $value
      if [ "$value" != "$DEF_NODE1_MAC_ADDRESS_ETH1" ]; then
        scinfo "$NODE1_MAC_ADDRESS_ETH1 value changed to: $value"
      fi
   fi

    value=$( scparse $FOLDER_ETC/$FILE_FP $NODE1_MAC_ADDRESS_ETH2 )
    if [ -z "${value}" ]; then
      scabort "$NODE1_MAC_ADDRESS_ETH2 value must be no empty"
    fi
    valid_mac $NODE1_MAC_ADDRESS_ETH2 $value
    if [ "$value" != "$DEF_NODE1_MAC_ADDRESS_ETH2" ]; then
      scinfo "$NODE1_MAC_ADDRESS_ETH2 value changed to: $value"
    fi

    value=$( scparse $FOLDER_ETC/$FILE_FP $NODE1_MAC_ADDRESS_ETH3 )
    if [ -z "${value}" ]; then
      scabort "$NODE1_MAC_ADDRESS_ETH3 value must be no empty"
    fi
    valid_mac $NODE1_MAC_ADDRESS_ETH3 $value
    if [ "$value" != "$DEF_NODE1_MAC_ADDRESS_ETH3" ]; then
      scinfo "$NODE1_MAC_ADDRESS_ETH3 value changed to: $value"
    fi

    value=$( scparse $FOLDER_ETC/$FILE_FP $NODE1_MAC_ADDRESS_ETH4 )
    if [ -z "${value}" ]; then
      scabort "$NODE1_MAC_ADDRESS_ETH4 value must be no empty"
    fi
    valid_mac $NODE1_MAC_ADDRESS_ETH4 $value
    if [ "$value" != "$DEF_NODE1_MAC_ADDRESS_ETH4" ]; then
      scinfo "$NODE1_MAC_ADDRESS_ETH4 value changed to: $value"
    fi

    if [[ $INST_HW == GEP4* || $INST_HW == GEP5* || $INST_HW == GEP7* ]]; then
      value=$( scparse $FOLDER_ETC/$FILE_FP $NODE1_MAC_ADDRESS_ETH5 )
      if [ -z "${value}" ]; then
        scabort "$NODE1_MAC_ADDRESS_ETH5 value must be no empty"
      fi
      valid_mac $NODE1_MAC_ADDRESS_ETH5 $value
      if [ "$value" != "$DEF_NODE1_MAC_ADDRESS_ETH5" ]; then
        scinfo "$NODE1_MAC_ADDRESS_ETH5 value changed to: $value"
      fi

      value=$( scparse $FOLDER_ETC/$FILE_FP $NODE1_MAC_ADDRESS_ETH6 )
      if [ -z "${value}" ]; then
        scabort "$NODE1_MAC_ADDRESS_ETH6 value must be no empty"
      fi
      valid_mac $NODE1_MAC_ADDRESS_ETH6 $value
      if [ "$value" != "$DEF_NODE1_MAC_ADDRESS_ETH6" ]; then
        scinfo "$NODE1_MAC_ADDRESS_ETH6 value changed to: $value"
      fi
      if [[ "$INST_HW" == 'GEP5_64_1200' || $INST_HW == GEP7* ]]; then
      	value=$( scparse $FOLDER_ETC/$FILE_FP $NODE1_MAC_ADDRESS_ETH7 )
      	if [ -z "${value}" ]; then
        	scabort "$NODE1_MAC_ADDRESS_ETH7 value must be no empty"
      	fi
      	valid_mac $NODE1_MAC_ADDRESS_ETH7 $value
      	if [ "$value" != "$DEF_NODE1_MAC_ADDRESS_ETH7" ]; then
        	scinfo "$NODE1_MAC_ADDRESS_ETH7 value changed to: $value"
      	fi

      	value=$( scparse $FOLDER_ETC/$FILE_FP $NODE1_MAC_ADDRESS_ETH8 )
      	if [ -z "${value}" ]; then
        	scabort "$NODE1_MAC_ADDRESS_ETH8 value must be no empty"
      	fi
      	valid_mac $NODE1_MAC_ADDRESS_ETH8 $value
      	if [ "$value" != "$DEF_NODE1_MAC_ADDRESS_ETH8" ]; then
        	scinfo "$NODE1_MAC_ADDRESS_ETH8 value changed to: $value"
      	fi
    	else
	 			value=$( scparse $FOLDER_ETC/$FILE_FP $NODE1_MAC_ADDRESS_ETH7 )
      	if [ -n "${value}" ]; then
       		scabort "$NODE1_MAC_ADDRESS_ETH7 value must be empty for $INST_HW "
      	fi

      	value=$( scparse $FOLDER_ETC/$FILE_FP $NODE1_MAC_ADDRESS_ETH8 )
      	if [ -n "${value}" ]; then
        	scabort "$NODE1_MAC_ADDRESS_ETH8 value must be empty for $INST_HW "
      	fi	
    	fi
    else
      # if the hardware_wc value is GEP1 or GEP2 and deployment_environment is NOT_SIMULATED node1_mac_address_eth5 and node1_mac_address_eth6 must be empty 	
      value=$( scparse $FOLDER_ETC/$FILE_FP $NODE1_MAC_ADDRESS_ETH5 )
      if [ -n "${value}" ]; then
        scabort "$NODE1_MAC_ADDRESS_ETH5 value must be empty for $INST_HW "
      fi

      value=$( scparse $FOLDER_ETC/$FILE_FP $NODE1_MAC_ADDRESS_ETH6 )
      if [ -n "${value}" ]; then
        scabort "$NODE1_MAC_ADDRESS_ETH6 value must be empty for $INST_HW "
      fi

      value=$( scparse $FOLDER_ETC/$FILE_FP $NODE1_MAC_ADDRESS_ETH7 )
      if [ -n "${value}" ]; then
        scabort "$NODE1_MAC_ADDRESS_ETH7 value must be empty for $INST_HW "
      fi

      value=$( scparse $FOLDER_ETC/$FILE_FP $NODE1_MAC_ADDRESS_ETH8 )
      if [ -n "${value}" ]; then
        scabort "$NODE1_MAC_ADDRESS_ETH8 value must be empty for $INST_HW "
      fi
    fi
  else
    valid_mac $NODE1_BASE_MAC_ADDRESS $value
    if [ "$value" != "$DEF_$NODE1_BASE_MAC_ADDRESS" ]; then
      scinfo "$NODE1_BASE_MAC_ADDRESS value changed to: $value"
    fi
    # if the base mac address is specified the other mac addresses must be empty!!!	
    value=$( scparse $FOLDER_ETC/$FILE_FP $NODE1_MAC_ADDRESS_ETH0 )
    if [ -n "${value}" ]; then
      scabort "$NODE1_MAC_ADDRESS_ETH0 value must be empty because the base mac address is specified"
    fi
    if [ "$INST_HW" != GEP7* ]; then
      value=$( scparse $FOLDER_ETC/$FILE_FP $NODE1_MAC_ADDRESS_ETH1 )
      if [ -n "${value}" ]; then
        scabort "$NODE1_MAC_ADDRESS_ETH1 value must be empty because the base mac address is specified"
      fi
    
      value=$( scparse $FOLDER_ETC/$FILE_FP $NODE1_MAC_ADDRESS_ETH2 )
      if [ -n "${value}" ]; then
        scabort "$NODE1_MAC_ADDRESS_ETH2 value must be empty because the base mac address is specified"
      fi
   fi
    
    value=$( scparse $FOLDER_ETC/$FILE_FP $NODE1_MAC_ADDRESS_ETH3 )
    if [ -n "${value}" ]; then
      scabort "$NODE1_MAC_ADDRESS_ETH3 value must be empty because the base mac address is specified"
    fi
    
    value=$( scparse $FOLDER_ETC/$FILE_FP $NODE1_MAC_ADDRESS_ETH4 )
    if [ -n "${value}" ]; then
      scabort "$NODE1_MAC_ADDRESS_ETH4 value must be empty because the base mac address is specified"
    fi
    
    value=$( scparse $FOLDER_ETC/$FILE_FP $NODE1_MAC_ADDRESS_ETH5 )
    if [ -n "${value}" ]; then
      scabort "$NODE1_MAC_ADDRESS_ETH5 value must be empty because the base mac address is specified"
    fi

    value=$( scparse $FOLDER_ETC/$FILE_FP $NODE1_MAC_ADDRESS_ETH6 )
    if [ -n "${value}" ]; then
      scabort "$NODE1_MAC_ADDRESS_ETH6 value must be empty because the base mac address is specified"
    fi    

    value=$( scparse $FOLDER_ETC/$FILE_FP $NODE1_MAC_ADDRESS_ETH7 )
    if [ -n "${value}" ]; then
      scabort "$NODE1_MAC_ADDRESS_ETH7 value must be empty because the base mac address is specified"
    fi
     
    value=$( scparse $FOLDER_ETC/$FILE_FP $NODE1_MAC_ADDRESS_ETH8 )
    if [ -n "${value}" ]; then
      scabort "$NODE1_MAC_ADDRESS_ETH8 value must be empty because the base mac address is specified"
    fi
  fi	

  value=$( scparse $FOLDER_ETC/$FILE_FP $NODE2_BASE_MAC_ADDRESS )
  if [ -z "${value}" ]; then
    
    # if the mac base address for the Node 1 is specified also the mac base address for the Node2 must be specified
    value=$( scparse $FOLDER_ETC/$FILE_FP $NODE1_BASE_MAC_ADDRESS )
    if [ -n "${value}" ]; then
      scabort "$NODE2_BASE_MAC_ADDRESS value must be no empty"
    fi
    if [ "$INST_HW" != GEP7* ]; then
      value=$( scparse $FOLDER_ETC/$FILE_FP $NODE2_MAC_ADDRESS_ETH0 )
      if [ -z "${value}" ]; then
        scabort "$NODE2_MAC_ADDRESS_ETH0 value must be no empty"
      fi
      valid_mac $NODE2_MAC_ADDRESS_ETH0 $value
      if [ "$value" != "$DEF_NODE2_MAC_ADDRESS_ETH0" ]; then
        scinfo "$NODE2_MAC_ADDRESS_ETH0 value changed to: $value"
      fi

      value=$( scparse $FOLDER_ETC/$FILE_FP $NODE2_MAC_ADDRESS_ETH1 )
      if [ -z "${value}" ]; then
        scabort "$NODE2_MAC_ADDRESS_ETH1 value must be no empty"
      fi
      valid_mac $NODE2_MAC_ADDRESS_ETH1 $value
      if [ "$value" != "$DEF_NODE2_MAC_ADDRESS_ETH1" ]; then
        scinfo "$NODE2_MAC_ADDRESS_ETH1 value changed to: $value"
      fi
   fi
    value=$( scparse $FOLDER_ETC/$FILE_FP $NODE2_MAC_ADDRESS_ETH2 )
    if [ -z "${value}" ]; then
      scabort "$NODE2_MAC_ADDRESS_ETH2 value must be no empty"
    fi
    valid_mac $NODE2_MAC_ADDRESS_ETH2 $value
    if [ "$value" != "$DEF_NODE2_MAC_ADDRESS_ETH2" ]; then
      scinfo "$NODE2_MAC_ADDRESS_ETH2 value changed to: $value"
    fi

    value=$( scparse $FOLDER_ETC/$FILE_FP $NODE2_MAC_ADDRESS_ETH3 )
    if [ -z "${value}" ]; then
      scabort "$NODE2_MAC_ADDRESS_ETH3 value must be no empty"
    fi
    valid_mac $NODE2_MAC_ADDRESS_ETH3 $value
    if [ "$value" != "$DEF_NODE2_MAC_ADDRESS_ETH3" ]; then
      scinfo "$NODE2_MAC_ADDRESS_ETH3 value changed to: $value"
    fi

    value=$( scparse $FOLDER_ETC/$FILE_FP $NODE2_MAC_ADDRESS_ETH4 )
    if [ -z "${value}" ]; then
      scabort "$NODE2_MAC_ADDRESS_ETH4 value must be no empty"
    fi
    valid_mac $NODE2_MAC_ADDRESS_ETH4 $value
    if [ "$value" != "$DEF_NODE2_MAC_ADDRESS_ETH4" ]; then
      scinfo "$NODE2_MAC_ADDRESS_ETH4 value changed to: $value"
    fi

    if [[ $INST_HW == GEP4* || $INST_HW == GEP5* || $INST_HW == GEP7* ]]; then
      value=$( scparse $FOLDER_ETC/$FILE_FP $NODE2_MAC_ADDRESS_ETH5 )
      if [ -z "${value}" ]; then
        scabort "$NODE2_MAC_ADDRESS_ETH5 value must be no empty"
      fi
      valid_mac $NODE2_MAC_ADDRESS_ETH5 $value
      if [ "$value" != "$DEF_NODE2_MAC_ADDRESS_ETH5" ]; then
        scinfo "$NODE2_MAC_ADDRESS_ETH5 value changed to: $value"
      fi

      value=$( scparse $FOLDER_ETC/$FILE_FP $NODE2_MAC_ADDRESS_ETH6 )
      if [ -z "${value}" ]; then
        scabort "$NODE2_MAC_ADDRESS_ETH6 value must be no empty"
      fi
      valid_mac $NODE2_MAC_ADDRESS_ETH6 $value
      if [ "$value" != "$DEF_NODE2_MAC_ADDRESS_ETH6" ]; then
        scinfo "$NODE2_MAC_ADDRESS_ETH6 value changed to: $value"
      fi

      if [[ "$INST_HW" == 'GEP5_64_1200' || $INST_HW == GEP7* ]]; then
      	value=$( scparse $FOLDER_ETC/$FILE_FP $NODE2_MAC_ADDRESS_ETH7 )
       	if [ -z "${value}" ]; then
        	scabort "$NODE2_MAC_ADDRESS_ETH7 value must be no empty"
       	fi
       	valid_mac $NODE2_MAC_ADDRESS_ETH7 $value
       	if [ "$value" != "$DEF_NODE2_MAC_ADDRESS_ETH7" ]; then
        	scinfo "$NODE2_MAC_ADDRESS_ETH7 value changed to: $value"
       	fi

       	value=$( scparse $FOLDER_ETC/$FILE_FP $NODE2_MAC_ADDRESS_ETH8 )
       	if [ -z "${value}" ]; then
        	scabort "$NODE2_MAC_ADDRESS_ETH8 value must be no empty"
       	fi
       	valid_mac $NODE2_MAC_ADDRESS_ETH8 $value
       	if [ "$value" != "$DEF_NODE2_MAC_ADDRESS_ETH8" ]; then
        	scinfo "$NODE2_MAC_ADDRESS_ETH8 value changed to: $value"
       	fi
			else
				value=$( scparse $FOLDER_ETC/$FILE_FP $NODE2_MAC_ADDRESS_ETH7 )
      	if [ -n "${value}" ]; then
        	scabort "$NODE2_MAC_ADDRESS_ETH7 value must be empty for $INST_HW "
      	fi

      	value=$( scparse $FOLDER_ETC/$FILE_FP $NODE2_MAC_ADDRESS_ETH8 )
      	if [ -n "${value}" ]; then
        	scabort "$NODE2_MAC_ADDRESS_ETH8 value must be empty for $INST_HW "
      	fi
     	fi
    else
      # if the hardware_wc value is GEP1 or GEP2 and deployment_environment is NOT_SIMULATED node2_mac_address_eth5 and node2_mac_address_eth6 must be empty 	
      value=$( scparse $FOLDER_ETC/$FILE_FP $NODE2_MAC_ADDRESS_ETH5 )
      if [ -n "${value}" ]; then
        scabort "$NODE2_MAC_ADDRESS_ETH5 value must be empty for $INST_HW "
      fi

      value=$( scparse $FOLDER_ETC/$FILE_FP $NODE2_MAC_ADDRESS_ETH6 )
      if [ -n "${value}" ]; then
        scabort "$NODE2_MAC_ADDRESS_ETH6 value must be empty for $INST_HW "
      fi
     
      value=$( scparse $FOLDER_ETC/$FILE_FP $NODE2_MAC_ADDRESS_ETH7 )
      if [ -n "${value}" ]; then
        scabort "$NODE2_MAC_ADDRESS_ETH7 value must be empty for $INST_HW "
      fi

      value=$( scparse $FOLDER_ETC/$FILE_FP $NODE2_MAC_ADDRESS_ETH8 )
      if [ -n "${value}" ]; then
        scabort "$NODE2_MAC_ADDRESS_ETH8 value must be empty for $INST_HW "
      fi
    fi
  else
    valid_mac $NODE2_BASE_MAC_ADDRESS $value
    if [ "$value" != "$DEF_$NODE2_BASE_MAC_ADDRESS" ]; then
      scinfo "$NODE2_BASE_MAC_ADDRESS value changed to: $value"
    fi
    # check if the mac base address for the Node 1 is specified also the mac base address for the Node2 must be specified
    value=$( scparse $FOLDER_ETC/$FILE_FP $NODE1_BASE_MAC_ADDRESS )
    if [ -z "${value}" ]; then
      scabort "$NODE1_BASE_MAC_ADDRESS value must be no empty"
    fi
    # if the base mac address is specified the other mac addresses must be empty!!!
    if [[ $INST_HW != GEP7* ]]; then
      value=$( scparse $FOLDER_ETC/$FILE_FP $NODE2_MAC_ADDRESS_ETH0 )
      if [ -n "${value}" ]; then
        scabort "$NODE2_MAC_ADDRESS_ETH0 vvalue must be empty because the base mac address is specified"
      fi
   
      value=$( scparse $FOLDER_ETC/$FILE_FP $NODE2_MAC_ADDRESS_ETH1 )
      if [ -n "${value}" ]; then
        scabort "$NODE2_MAC_ADDRESS_ETH1 value must be empty because the base mac address is specified"
      fi
   fi

    value=$( scparse $FOLDER_ETC/$FILE_FP $NODE2_MAC_ADDRESS_ETH2 )
    if [ -n "${value}" ]; then
      scabort "$NODE2_MAC_ADDRESS_ETH2 value must be empty because the base mac address is specifiedy"
    fi
    
    value=$( scparse $FOLDER_ETC/$FILE_FP $NODE2_MAC_ADDRESS_ETH3 )
    if [ -n "${value}" ]; then
      scabort "$NODE2_MAC_ADDRESS_ETH3 value must be empty because the base mac address is specified"
    fi

    value=$( scparse $FOLDER_ETC/$FILE_FP $NODE2_MAC_ADDRESS_ETH4 )
    if [ -n "${value}" ]; then
      scabort "$NODE2_MAC_ADDRESS_ETH4 value must be empty because the base mac address is specified"
    fi
    
    value=$( scparse $FOLDER_ETC/$FILE_FP $NODE2_MAC_ADDRESS_ETH5 )
    if [ -n "${value}" ]; then
      scabort "$NODE2_MAC_ADDRESS_ETH5 value must be empty because the base mac address is specified"
    fi
      
    value=$( scparse $FOLDER_ETC/$FILE_FP $NODE2_MAC_ADDRESS_ETH6 )
    if [ -n "${value}" ]; then
      scabort "$NODE2_MAC_ADDRESS_ETH6 value must be empty because the base mac address is specified"
    fi

    value=$( scparse $FOLDER_ETC/$FILE_FP $NODE2_MAC_ADDRESS_ETH7 )
    if [ -n "${value}" ]; then
      scabort "$NODE2_MAC_ADDRESS_ETH7 value must be empty because the base mac address is specified"
    fi

    value=$( scparse $FOLDER_ETC/$FILE_FP $NODE2_MAC_ADDRESS_ETH8 )
    if [ -n "${value}" ]; then
      scabort "$NODE2_MAC_ADDRESS_ETH8 value must be empty because the base mac address is specified"
    fi
  fi

  value=$( scparse $FOLDER_ETC/$FILE_FP $NODE1_MAC_ADDRESS_MVL0 )
  if [ -n "${value}" ]; then
    scabort "$NODE1_MAC_ADDRESS_MVL0 value must be empty"
  fi

  value=$( scparse $FOLDER_ETC/$FILE_FP $NODE1_MAC_ADDRESS_MVL1 )
  if [ -n "${value}" ]; then
    scabort "$NODE1_MAC_ADDRESS_MVL1 value must be empty"
  fi

  value=$( scparse $FOLDER_ETC/$FILE_FP $NODE1_MAC_ADDRESS_MVL2 )
  if [ -n "${value}" ]; then
    scabort "$NODE1_MAC_ADDRESS_MVL2 value must be empty"
  fi

  value=$( scparse $FOLDER_ETC/$FILE_FP $NODE2_MAC_ADDRESS_MVL0 )
  if [ -n "${value}" ]; then
    scabort "$NODE2_MAC_ADDRESS_MVL0 value must be empty"
  fi

  value=$( scparse $FOLDER_ETC/$FILE_FP $NODE2_MAC_ADDRESS_MVL1 )
  if [ -n "${value}" ]; then
    scabort "$NODE2_MAC_ADDRESS_MVL1 value must be empty"
  fi

  value=$( scparse $FOLDER_ETC/$FILE_FP $NODE2_MAC_ADDRESS_MVL2 )
  if [ -n "${value}" ]; then
    scabort "$NODE2_MAC_ADDRESS_MVL2 value must be empty"
  fi

  value=$( scparse $FOLDER_ETC/$FILE_FP $NODE1_PUBLIC_NETWORK_IPV4_IP_ADDRESS )
  if [ -z "${value}" ]; then
    scabort "$NODE1_PUBLIC_NETWORK_IPV4_IP_ADDRESS value must be no empty"
  fi
  valid_ip $NODE1_PUBLIC_NETWORK_IPV4_IP_ADDRESS $value
  if [ "$value" != "$DEF_NODE1_PUBLIC_NETWORK_IPV4_IP_ADDRESS" ]; then
    scinfo "$NODE1_PUBLIC_NETWORK_IPV4_IP_ADDRESS value changed to: $value"
  fi

  value=$( scparse $FOLDER_ETC/$FILE_FP $NODE2_PUBLIC_NETWORK_IPV4_IP_ADDRESS )
  if [ -z "${value}" ]; then
    scabort "$NODE2_PUBLIC_NETWORK_IPV4_IP_ADDRESS value must be no empty"
  fi
  valid_ip $NODE2_PUBLIC_NETWORK_IPV4_IP_ADDRESS $value
  if [ "$value" != "$DEF_NODE2_PUBLIC_NETWORK_IPV4_IP_ADDRESS" ]; then
    scinfo "$NODE2_PUBLIC_NETWORK_IPV4_IP_ADDRESS value changed to: $value"
  fi

  value=$( scparse $FOLDER_ETC/$FILE_FP $CLUSTER_PUBLIC_NETWORK_IPV4_IP_ADDRESS )
  if [ -z "${value}" ]; then
    scabort "$CLUSTER_PUBLIC_NETWORK_IPV4_IP_ADDRESS value must be no empty"
  fi
  valid_ip $CLUSTER_PUBLIC_NETWORK_IPV4_IP_ADDRESS $value
  if [ "$value" != "$DEF_CLUSTER_PUBLIC_NETWORK_IPV4_IP_ADDRESS" ]; then
    scinfo "$CLUSTER_PUBLIC_NETWORK_IPV4_IP_ADDRESS value changed to: $value"
  fi

  value=$( scparse $FOLDER_ETC/$FILE_FP $NODE1_PUBLIC2_NETWORK_IPV4_IP_ADDRESS )
  if [ -n "${value}" ]; then
    scabort "$NODE1_PUBLIC2_NETWORK_IPV4_IP_ADDRESS value must be empty"
  fi

  value=$( scparse $FOLDER_ETC/$FILE_FP $NODE2_PUBLIC2_NETWORK_IPV4_IP_ADDRESS )
  if [ -n "${value}" ]; then
    scabort "$NODE2_PUBLIC2_NETWORK_IPV4_IP_ADDRESS value must be empty"
  fi

  value=$( scparse $FOLDER_ETC/$FILE_FP $CLUSTER_PUBLIC2_NETWORK_IPV4_IP_ADDRESS )
  if [ -n "${value}" ]; then
    scabort "$CLUSTER_PUBLIC2_NETWORK_IPV4_IP_ADDRESS value must be empty"
  fi

  value=$( scparse $FOLDER_ETC/$FILE_FP $PHYSEP_NETWORK_IPV4_GATEWAY_IP_ADDRESS )
  if [ -n "${value}" ]; then
    scabort "$PHYSEP_NETWORK_IPV4_GATEWAY_IP_ADDRESS value must be empty"
  fi

  value=$( scparse $FOLDER_ETC/$FILE_FP $DEFAULT_NETWORK_IPV4_GATEWAY_IP_ADDRESS )
  if [ -z "${value}" ]; then
    scabort "$DEFAULT_NETWORK_IPV4_GATEWAY_IP_ADDRESS value must be no empty"
  fi
  valid_ip $DEFAULT_NETWORK_IPV4_GATEWAY_IP_ADDRESS $value
  if [ "$value" != "$DEF_DEFAULT_NETWORK_IPV4_GATEWAY_IP_ADDRESS" ]; then
    scinfo "$DEFAULT_NETWORK_IPV4_GATEWAY_IP_ADDRESS value changed to: $value"
  fi

  if [[ "$INST_HW" == GEP4* || "$INST_HW" == GEP5* || "$INST_HW" == GEP7* ]]; then
		value=$( scparse $FOLDER_ETC/$FILE_FP $NETWORK_10G_VLANTAG )
		[ -z "$value" ] && value='NULL'
		validate_vlan $NETWORK_10G_VLANTAG $value

		# capture the value for oam_vlanid
    value=$( scparse $FOLDER_ETC/$FILE_FP $OAM_VLANID )
    [ -z "$value" ] && value='NULL'
    validate_vlan $OAM_VLANID $value
  fi

  value=$( scparse $FOLDER_ETC/$FILE_FP $TIPC_VLANTAG )
  if [ -z "${value}" ]; then
    scabort "$TIPC_VLANTAG value must be no empty"
  fi
  $( echo $value | grep -Eq "^[0-9]+$")
	[ $? -ne 0 ] && scabort "$TIPC_VLANTAG must be a valid integer: $value"
	
 value=$( scparse $FOLDER_ETC/$FILE_FP $BGCI_A_NETWORK )
 [ -z "$value" ] && value='NULL'
 valid_bgci $BGCI_A_NETWORK $value
 if [ "$value" != "$DEF_BGCI_A_NETWORK" ] && [ $value != 'NULL' ]; then
    scinfo "$BGCI_A_NETWORK value changed to: $value"
 fi
 
  
  value=$( scparse $FOLDER_ETC/$FILE_FP $BGCI_B_NETWORK )
  [ -z "$value" ] && value='NULL'
  valid_bgci $BGCI_B_NETWORK $value
  if [ "$value" != "$DEF_BGCI_B_NETWORK" ] && [ $value != 'NULL' ]; then
    scinfo "$BGCI_B_NETWORK value changed to: $value"
  fi

  
  value=$( scparse $FOLDER_ETC/$FILE_FP $CLUSTER_KEYMAP )
  if [ -z "${value}" ]; then
    scabort "$CLUSTER_KEYMAP value must be no empty"
  fi
  keymaps='
          azerty
          be-latin1
          fr-latin1
          fr-latin9
          fr-pc
          fr
          wangbe
          wangbe2
          ANSI-dvorak
          dvorak-l
          dvorak-r
          dvorak
          no
          tr_f-latin5
          trf
          applkey
          backspace
          ctrl
          euro
          euro1
          euro2
          keypad
          unicode
          windowkeys
          es-olpc
          pt
          Pl02
          arabic
          bashkir
          bg-cp1251
          bg-cp855
          bg_bds-cp1251
          bg_bds-utf8
          bg_pho-cp1251
          bg_pho-utf8
          br-abnt-alt
          br-abnt
          br-abnt2-old
          br-abnt2
          br-latin1-abnt2
          br-latin1-us
          by-cp1251
          by
          bywin-cp1251
          cf
          chinese
          cn-latin1
          cz-cp1250
          cz-lat2-prog
          cz-lat2-us
          cz-lat2
          cz
          defkeymap
          defkeymap_V1.0
          dk-latin1
          dk
          emacs
          emacs2
          es-cp850
          es
          et-nodeadkeys
          et
          fi-latin1
          fi-latin9
          fi
          gr-pc
          gr
          hu101
          il-heb
          il-phonetic
          il
          is-latin1-us
          is-latin1
          it-ibm
          it
          it2
          jp106
          kazakh
          khmer
          korean
          kyrgyz
          la-latin1
          lt.baltic
          lt.l4
          lt
          mk-cp1251
          mk-utf
          mk
          mk0
          nl
          nl2
          no-latin1
          no
          pc110
          pl
          pl1
          pl2
          pl3
          pl4
          pt-latin1
          pt-latin9
          ro
          ro_std
          ro_win
          ru-cp1251
          ru-ms
          ru-yawerty
          ru
          ru1
          ru1_win-utf
          ru2
          ru3
          ru4
          ru_win
          ruwin_alt-CP1251
          ruwin_alt-KOI8-R
          ruwin_alt-UTF-8
          ruwin_cplk-CP1251
          ruwin_cplk-KOI8-R
          ruwin_cplk-UTF-8
          ruwin_ct_sh-CP1251
          ruwin_ct_sh-KOI8-R
          ruwin_ct_sh-UTF-8
          ruwin_ctrl-CP1251
          ruwin_ctrl-KOI8-R
          ruwin_ctrl-UTF-8
          se-fi-ir209
          se-fi-lat6
          se-ir209
          se-lat6
          se-latin1
          sk-prog-qwerty
          sk-qwerty
          sr-cy
          sv-latin1
          taiwanese
          tj_alt-UTF8
          tr_q-latin5
          tralt
          trf
          trq
          ttwin_alt-UTF-8
          ttwin_cplk-UTF-8
          ttwin_ct_sh-UTF-8
          ttwin_ctrl-UTF-8
          ua-cp1251
          ua-utf-ws
          ua-utf
          ua-ws
          ua
          uk
          us-acentos-old
          us-acentos
          us
          croat
          cz-us-qwertz
          cz
          de-latin1-nodeadkeys
          de-latin1
          de
          de_CH-latin1
          fr_CH-latin1
          fr_CH
          hu
          ro-latin2
          sg-latin1-lk450
          sg-latin1
          sg
          sk-prog-qwertz
          sk-qwertz
          slovene
          '
  local result=$FALSE
  for keymap in $keymaps; do
    if [ $keymap == $value ]; then result=$TRUE; break; fi
  done
  if [ $result -ne $TRUE ]; then scabort "$CLUSTER_KEYMAP value not valid: $value"; fi
  if [ "$value" != "$DEF_CLUSTER_KEYMAP" ]; then
    scinfo "$CLUSTER_KEYMAP value changed to: $value"
  fi
  
  value_base_1=$( scparse $FOLDER_ETC/$FILE_FP $NODE1_BASE_MAC_ADDRESS )
  value_base_2=$( scparse $FOLDER_ETC/$FILE_FP $NODE2_BASE_MAC_ADDRESS )
  if [[ -n "${value_base_1}" || -n "${value_base_2}" ]]; then
    echo "-   NOTE: "
    if [ -n "${value_base_1}" ]; then 
      echo "-   MAC addresses of Node1 will be defined starting from the following base MAC address: $value_base_1"
    fi
    if [ -n "${value_base_2}" ]; then 
      echo "-   MAC addresses of Node2 will be defined starting from the following base MAC address: $value_base_2"
    fi  
  fi
}

function sanity_checks() {
  local FOLDER_ETC="etc"
  local FILE_FP="factoryparam.conf"
  local FILE_IP="installation.conf"
  local FILE_SP="siteparam.conf"

  # Check directory structure
  if [ ! -d ${FOLDER_ETC} ]; then
    scabort "Unable to find the \"${FOLDER_ETC}\" folder"
  fi
  # Check files presence
  if [ ! -f ${FOLDER_ETC}/${FILE_FP} ]; then
    scabort "Unable to find the \"${FOLDER_ETC}/\${FILE_FP}\" file"
  fi
  if [ ! -f ${FOLDER_ETC}/${FILE_IP} ]; then
    scabort "Unable to find the \"${FOLDER_ETC}/\${FILE_IP}\" file"
  fi
  if [ ! -f ${FOLDER_ETC}/${FILE_SP} ]; then
    scabort "Unable to find the \"${FOLDER_ETC}/\${FILE_SP}\" file"
  fi
  # Check the read permissions
  if [ ! -r ${FOLDER_ETC}/${FILE_FP} ]; then
    scabort "Unable to find the \"${FOLDER_ETC}/\${FILE_FP}\" file"
  fi
  if [ ! -r ${FOLDER_ETC}/${FILE_IP} ]; then
    scabort "Unable to find the \"${FOLDER_ETC}/\${FILE_IP}\" file"
  fi
  if [ ! -r ${FOLDER_ETC}/${FILE_SP} ]; then
    scabort "Unable to find the \"${FOLDER_ETC}/\${FILE_SP}\" file"
  fi
  # Check the factory parameters
  sanity_checks_factory_params
  # Check the installation parameters
  if [ $OPT_SYSTEM -eq $TRUE ]; then
    sanity_checks_install_params
  else
    sanity_checks_install_flash_params
  fi
  # Check the site parameters
  sanity_checks_site_params
}

function usage() {
  echo 'USAGE:'
  echo '  deploy.sh [--system|-s] [--nosanitychecks|-n]'
  echo '  deploy.sh --flash|-f [--nosanitychecks|-n]'
  echo '  deploy.sh --help|-h'
}

# The function reads the command line argument list and parses it flagging the
#  right variables in a case/esac switch.
#  Input: the function must be invoked with the $@ parameter:
#   parse_cmdline $*
#  Required: please make attention to handle the cases in the right way.
#
function parse_cmdline() {
  # OPTIONS is a list of single-character options.
  #  The string must be in the form:
  #   Example: 'ovl' (for -o -v -l options).
  #  Options that takes an argument must be followed by a colon:
  #   Example: 'ovl:' (-v takes a mandatory argument).
  #  Options with an optional argument must be followed by a double colon:
  #   Example: 'ovl::' (-l takes an optional argument).
  local OPTIONS='s f n h'

  # LONG_OPTIONS is a list of space-separated multi-character options.
  #  The string must be in the form:
  #   Example: 'option1 option2 ... optionN'.
  #  Options that takes an argument must be followed by a colon:
  #   Example: 'option1: option2 ... optionN:'
  #  Options with an optional argument must be followed by a double colon:
  #   Example: 'option1:: option2:: ... optionN'
  local LONG_OPTIONS='system flash nosanitychecks help'

  ARGS=$(getopt --longoptions "$LONG_OPTIONS" --options "$OPTIONS" -- "$@")
  RETURN_CODE=$?	
  if [ $RETURN_CODE -ne 0 ]; then
    usage
    abort "Wrong parameters"
  fi

  eval set -- "$ARGS"

  # Make sure to handle the cases for all the options listed in OPTIONS
  #  and LONG_OPTIONS and to fill up the right script-wide variables.
  while [ $# -gt 0 ]; do		
    case "$1" in
      -s|--system)
        # Nothing to do!
      ;;
      -f|--flash)
        OPT_SYSTEM=$FALSE
        OPT_FLASH=$TRUE
      ;;
      -n|--nosanitychecks)
        OPT_NOSANITYCHECKS=$FALSE
      ;;
      -h|--help)
        OPT_HELP=$TRUE
      ;;
      --)
        shift
        break
      ;;
      *)
        # Nothing to do!
      ;;
    esac
    shift
  done
}

function options_check() {
  if [ $OPT_HELP -eq $TRUE ]; then
    usage
    exit $EXIT_SUCCESS
  else
    if [[ $OPT_SYSTEM -eq $TRUE && $OPT_FLASH -eq $TRUE ]]; then
      abort "Script error!"
    fi
  fi
}

function fetch_ap_type() {

	local AP_TYPE=""
	local file="$(pwd)/etc/factoryparam.conf"
	AP_TYPE=$(grep '^ap_type=' $file | awk -F'=' '{print $2}')
	echo "$AP_TYPE"
}

function fetch_shelf_architecture() {
	local SHELF_ARCH=""
	local file="$(pwd)/etc/factoryparam.conf"
	SHELF_ARCH=$(grep '^shelf_architecture=' $file | awk -F'=' '{print $2}')
	echo "$SHELF_ARCH"
}

#------------------------------------------------------------
function fetch_shelf_switch() {
	local SHELF_SWITCH=""
	local file="$(pwd)/etc/factoryparam.conf"
	SHELF_SWITCH=$(grep '^shelf_switch=' $file | awk -F'=' '{print $2}')
	echo "$SHELF_SWITCH"
}

#-------------------------------------------------------------
function fetch_apg_oam_access() {
  local OAM_ACESS=""
  local file="$(pwd)/etc/factoryparam.conf"
  OAM_ACESS=$(grep '^apg_oam_access=' $file | awk -F'=' '{print $2}')
  echo "$OAM_ACESS"
}


function copy_ph_template() {

  local template='non_exec-clusterconf_template_'
  local input="$1"
  local TEMPLATE_FILE=''

  HOOKS_TEMPLATE_DIR="$HOOKS_DIR/templates"
  HOOKS_PH_TEMPLATE="$HOOKS_DIR/ph/non_exec-clusterconf_template"  
  
  # formulate the template file name
  if [ -z "$input" ]; then
    TEMPLATE_FILE='non_exec-clusterconf_template'
  else
    TEMPLATE_FILE="$template$input" 
  fi 
  
  cp $HOOKS_TEMPLATE_DIR/$TEMPLATE_FILE $HOOKS_PH_TEMPLATE || \
   abort "Failure while copying template[$template]"
}

#                                              __    __   _______   _   __    _
#                                              __    __   _______   _   __    _
#                                             |  \  /  | |  ___  | | | |  \  | |
#                                             |   \/   | | |___| | | | |   \ | |
#                                             | |\  /| | |  ___  | | | | |\ \| |
#                                             | | \/ | | | |   | | | | | | \   |
#                                             |_|    |_| |_|   |_| |_| |_|  \__|

# --- Command line variables
OPT_SYSTEM=$TRUE
OPT_FLASH=$FALSE
OPT_HELP=$FALSE
OPT_NOSANITYCHECKS=$TRUE

# --- Command line parser
parse_cmdline $*
options_check

# --- Folders
# --  MI package folders
ETC_DIR="etc"
HOOKS_DIR="hooks"
LOTC_DIR="lotc"
SW_DIR="sw"
PLUGIN_DIR="plugins"
# --  Installation hardware type
INST_HW=""
file="$(pwd)/etc/factoryparam.conf"
linenr=0
[ ! -f $file ] && abort "$file not found"
while read cline
do
  linenr=$(expr $linenr + 1);
  line=$(echo ${cline%%;*})
  if [ ! -z "$line" ]; then
    myname=$(trim ${line%%=*})
    myvalue=$(echo ${line#*=} | tr -d '\n')
    if [ ! -z $myname ]; then
      case $myname in
      installation_hw)
        INST_HW=$myvalue
        ;;
      esac
    fi
  fi
done < "$file"
file=""; linenr=""; line=""; myname=""; myvalue=""
# --  TFTP server folders
# -   Base folder
TFTP_BASE_DIR=""
file="$(pwd)/etc/factoryparam.conf"
linenr=0
[ ! -f $file ] && abort "$file not found"
while read cline
do
  linenr=$(expr $linenr + 1);
  line=$(echo ${cline%%;*})
  if [ ! -z "$line" ]; then
    myname=$(trim ${line%%=*})
    myvalue=$(echo ${line#*=} | tr -d '\n')
    if [ ! -z $myname ]; then
      case $myname in
      installation_root)
        TFTP_BASE_DIR=$myvalue
        ;;
      esac
    fi
  fi
done < "$file"
file=""; linenr=""; line=""; myname=""; myvalue=""
# --  Take the sizes from installation.conf
BOOT_SIZE=""
LOG_SIZE=""
ROOT_SIZE=""
SWAP_SIZE=""
FILESYSTEM_SIZE=""
ROOT_HASH=""
DEF_ROOT_PASSWORD_HASH="\$2y\$10\$Z95LNixlC9JulkDpSc9M/up8ccIjlvWXmgd9ydTGOn5vqTHw7fHcK"
# -   
file="$(pwd)/etc/installation.conf"
linenr=0
[ ! -f $file ] && abort "$file not found"
while read cline
do
  linenr=$(expr $linenr + 1);
  line=$(echo ${cline%%;*})
  if [ ! -z "$line" ]; then
    myname=$(trim ${line%%=*})
    myvalue=$(echo ${line#*=} | tr -d '\n')
    if [ ! -z $myname ]; then
      case $myname in
      partition_boot_size)
        BOOT_SIZE=$myvalue
        ;;
      partition_log_size)
        LOG_SIZE=$myvalue
        ;;
      partition_root_size)
        ROOT_SIZE=$myvalue
        ;;
      partition_swap_size)
        SWAP_SIZE=$myvalue
        ;;
      shared_filesystem_size)
        FILESYSTEM_SIZE=$myvalue
        ;;
      root_password_hash)
        ROOT_HASH=$myvalue
        ;;
      esac
    fi
  fi
done < "$file"
file=""; linenr=""; line=""; myname=""; myvalue=""
# -   Temporary folder for development purposes
# -   Note: Set to empty by default
TFTP_DEV_TMPDIR=""
# --  Other folders
LOTC_RUNTIME_DIR=$SW_DIR/$LOTC_DIR
AIT_DIR=$SW_DIR/$LOTC_DIR/"ait"
CURRENT_DIR=$(pwd)

# Applications
DEPLOY_TOOL=$AIT_DIR/"lde-installation-env-setup"

# Deployment tool attributes
#DEPLOY_SYSTEM=$(cat $ETC_DIR/apg_system)
DEPLOY_SYSTEM=""
file="$(pwd)/etc/factoryparam.conf"
linenr=0
[ ! -f $file ] && abort "$file not found"
while read cline
do
  linenr=$(expr $linenr + 1);
  line=$(echo ${cline%%;*})
  if [ ! -z "$line" ]; then
    myname=$(trim ${line%%=*})
    myvalue=$(echo ${line#*=} | tr -d '\n')
    if [ ! -z $myname ]; then
      case $myname in
      system_version)
        DEPLOY_SYSTEM=$myvalue
        ;;
      esac
    fi
  fi
done < "$file"
file=""; linenr=""; line=""; myname=""; myvalue=""
DEPLOY_EDITION="lfr"     # LDE on RHEL
DEPLOY_EDITION="lws"     # LDE on SLES
DEPLOY_TYPE="usb"        # Installation media
DEPLOY_TYPE="net"        # Installation server
DEPLOY_DEBUG="--debug 1" # Enable debug mode
DEPLOY_DEBUG=""          # Disable debug mode

# Welcome message mgmt
WELCOME_MSG="--- Maiden Installation for $DEPLOY_SYSTEM ---"
WELCOME_MSG_LEN=$(echo "${#WELCOME_MSG}")
WELCOME_SEP=""
for i in $(seq 1 $WELCOME_MSG_LEN); do WELCOME_SEP=${WELCOME_SEP}-; done

echo $WELCOME_SEP
echo $WELCOME_MSG
echo $WELCOME_SEP
echo ""
echo -n "--- MI Preparation for the "
if [ $OPT_SYSTEM -eq $TRUE ]; then
  echo "System disk"
else
  echo "Flash disk"
fi

# Sanity checks mgmt
if [ $OPT_NOSANITYCHECKS -eq $TRUE ]; then
  echo "--  Sanity checks ongoing... "
  sanity_checks
  echo "-   done"
else
  echo "--  Sanity checks skipped!!!"
fi

# Check if lotc is available
[ ! -d "$CURRENT_DIR/$SW_DIR" ] && abort "Folder $CURRENT_DIR/$SW_DIR not found"
pushd "$CURRENT_DIR/$SW_DIR" > /dev/null 2>&1
# LDE naming convention adaptation
# LOTC_RUNTIME_PKG=$(find . -name "LOTC_RUNTIME-*.tar.gz")
gz="z"
LOTC_RUNTIME_PKG=$(find ./os -name "*.tar.gz" -or -name "*.tgz")
if [ -z $LOTC_RUNTIME_PKG ]; then
	LOTC_RUNTIME_PKG=$(find ./os -name "*.tar")
	gz=""
fi
[ -z $LOTC_RUNTIME_PKG ] && abort "No LDE with SLES RUNTIME package found"

PKG_NAME=$(basename $LOTC_RUNTIME_PKG)
echo "--  Unpacking the $PKG_NAME package"

[ -z $LOTC_DIR ] && abort "Variable LOTC_DIR not populated"

if [ ! -d $LOTC_DIR ]; then
  echo -n "-   Creating the $LOTC_DIR folder... "
  mkdir -p $LOTC_DIR || abort "Failure in creating $LOTC_DIR"
  echo "done"
else
  echo -n "-   Deleting the $LOTC_DIR folder content... "
  if find $LOTC_DIR/* -depth -delete &>/dev/null; then
    echo "done"
  else
    echo "done (no files to be deleted)"
  fi
fi
tar -x"$gz"f $LOTC_RUNTIME_PKG -C $LOTC_DIR || abort "Failure while unpacking $LOTC_RUNTIME_PKG"
[ ! -d "$LOTC_DIR" ] && abort "Folder $LOTC_DIR not found"
pushd "$LOTC_DIR" > /dev/null 2>&1
[ ! -f control ] && abort "File control not found"
LOTC_CTRL_PKG_PREFIX=$(cat control)
[ -z $LOTC_CTRL_PKG_PREFIX ] && abort "Variable LOTC_CTRL_PKG_PREFIX not populated"
LOTC_CTRL_PKG=$(find . -name "$LOTC_CTRL_PKG_PREFIX-*.sdp" -type l)
if [ -z $LOTC_CTRL_PKG ]; then
  LOTC_CTRL_PKG=$(find . -name "$LOTC_CTRL_PKG_PREFIX-*.sdp")
fi
[ -z $LOTC_CTRL_PKG ] && abort "Variable LOTC_CTRL_PKG not populated"
LOTC_CTRL_PKG_DIR=$LOTC_CTRL_PKG_PREFIX
if [ ! -d $LOTC_CTRL_PKG_DIR ]; then
  echo -n "-   Creating the $LOTC_CTRL_PKG_DIR folder... "
  mkdir -p $LOTC_CTRL_PKG_DIR || abort "Failure in creating $LOTC_CTRL_PKG_DIR"
  echo "done"
else
  echo -n "$LOTC_CTRL_PKG_DIR found. Deleting its content... "
  if find $LOTC_CTRL_PKG_DIR/* -depth -delete &>/dev/null; then
    echo "done"
  else
    echo "done (no files to be deleted)"
  fi
fi
tar -xf $LOTC_CTRL_PKG -C $LOTC_CTRL_PKG_DIR || abort "Failure while unpacking $LOTC_CTRL_PKG"

[ ! -d $LOTC_CTRL_PKG_DIR ] && abort "Folder $LOTC_CTRL_PKG_DIR not found"
pushd "$LOTC_CTRL_PKG_DIR/" > /dev/null 2>&1
LOTC_CTRL_RPM_DIR="RPM"
if [ ! -d $LOTC_CTRL_RPM_DIR ]; then
  echo -n "-   Creating the $LOTC_CTRL_RPM_DIR folder... "
  mkdir -p $LOTC_CTRL_RPM_DIR || abort "Failure in creating $LOTC_CTRL_RPM_DIR"
  echo "done"
else
  echo -n "-   The $LOTC_CTRL_RPM_DIR folder is already present, deleting its content... "
  if find $LOTC_CTRL_RPM_DIR/* -depth -delete &>/dev/null; then
    echo "done"
  else
    echo "done (no files to be deleted)"
  fi
fi
LOTC_CTRL_RPM=$(find . -name "linux-control-*.x86_64.rpm" | sed "s@.*/@@g")
if [ -z $LOTC_CTRL_RPM ]; then
  LOTC_CTRL_RPM=$(find . -name "ldews-control-*.x86_64.rpm" | sed "s@.*/@@g")
fi
[ -z $LOTC_CTRL_RPM ] && abort "Variable LOTC_CTRL_RPM not populated"
[ ! -d $LOTC_CTRL_RPM_DIR ] && abort "Folder $LOTC_CTRL_RPM_DIR not found"
pushd "$LOTC_CTRL_RPM_DIR/" > /dev/null 2>&1
rpm2cpio ../$LOTC_CTRL_RPM | cpio -idm 2>/dev/null || abort "Failure while extracting $LOTC_CTRL_RPM"
popd > /dev/null 2>&1; popd > /dev/null 2>&1; popd > /dev/null 2>&1; popd > /dev/null 2>&1
# Check if tftpboot folder structure is available
TFTP_DIR=""
if [ -n "$TFTP_DEV_TMPDIR" ]; then
  echo "--  Using the TFTP server development $TFTP_DEV_TMPDIR folder!"
  TFTP_DIR=$TFTP_DEV_TMPDIR
else
  echo "--  Using the TFTP server base (delivery) $TFTP_BASE_DIR folder!"
  TFTP_DIR=$TFTP_BASE_DIR
fi
if [ -d $TFTP_DIR ]; then
  echo -n "-   The $TFTP_DIR folder is already present, deleting its content... "
  if find $TFTP_DIR/* -depth -delete &>/dev/null; then
    echo "done"
  else
    echo "done (no files to be deleted)"
  fi
else
  echo -n "-   Creating the $LOTC_CTRL_RPM_DIR folder... "
  mkdir -p $TFTP_DIR || abort "Failure in creating $TFTP_DIR"
  echo "done"
fi
# Create ./lotc folder and content
echo "--  Preparing the LOTC software"
if [ ! -d $LOTC_DIR ]; then
  echo -n "-   Creating the $LOTC_DIR folder... "
  mkdir $LOTC_DIR || abort "Failure in creating $LOTC_DIR"
  echo "done"
else
  echo -n "-   The $LOTC_DIR folder is already present, deleting its content... "
  if find $LOTC_DIR/* -depth -delete &>/dev/null; then
    echo "done"
  else
    echo "done (no files to be deleted)"
  fi
fi
cp $AIT_DIR/boot.msg $LOTC_DIR/. || abort "Failure while copying boot.msg"
cp $LOTC_RUNTIME_DIR/$LOTC_CTRL_PKG_DIR/$LOTC_CTRL_RPM_DIR/initrd $LOTC_DIR/. || abort "Failure while copying initrd"
cp $LOTC_RUNTIME_DIR/$LOTC_CTRL_PKG_DIR/$LOTC_CTRL_RPM $LOTC_DIR/. || abort "Failure while copying $LOTC_CTRL_RPM"
cp $AIT_DIR/pxelinux.0 $LOTC_DIR/. || abort "Failure while copying pxelinux.0"
cp -R $AIT_DIR/pxelinux.cfg/ $LOTC_DIR/. || abort "Failure while copying the folder pxelinux.cfg"
cp $LOTC_RUNTIME_DIR/$LOTC_CTRL_PKG_DIR/$LOTC_CTRL_RPM_DIR/vmlinuz $LOTC_DIR/. || abort "Failure while copying the folder vmlinuz"

# Check if software is available

echo ""
echo "--- MI Deployment"
#setting executing permission to hooks
find $HOOKS_DIR -not -regex '.*non_exec.*' -type f -exec chmod +x {} \;

# Select the correct cluster.conf template depending on deployment environment
# based on AP_TYPE and SHELF_ARCHITECTURE copy the correct cluster conf from /templates/ folder to ah and ph hooks
# the cluster template file name in ah and ph folders will be respectively: 
# non_exec-clusterconf_01_template
# non_exec-clusterconf_12_template

AP_TYPE=$(fetch_ap_type)
SHELF_ARCHITECTURE=$(fetch_shelf_architecture)
SHELF_SWITCH=$( fetch_shelf_switch)
APG_OAM_ACCESS=$( fetch_apg_oam_access)

HOOKS_TEMPLATE_DIR="$HOOKS_DIR/templates"
HOOKS_PH_TEMPLATE="$HOOKS_DIR/ph/non_exec-clusterconf_template"
 
if  isGEP5_VM ; then
   copy_ph_template 'simulated'
else
   # based on AP_TYPE and SHELF_ARCHITECTURE copy the correct cluster conf from /templates/ folder to ah and ph hooks
   # the cluster template file name in ah and ph folders will be respectively: 
   # non_exec-clusterconf_01_template
   # non_exec-clusterconf_12_template
   if [ "$SHELF_ARCHITECTURE" == "" ]; then
      abort "Failure while filling SHELF_ARCHITECTURE"
   fi
	
   if [ -n "$AP_TYPE" ]; then
      case "$AP_TYPE" in
         AP1)
            if [ "$SHELF_ARCHITECTURE" == "DMX" ]; then
               if [[ "$INST_HW" == "GEP1" || "$INST_HW" == "GEP2" ]]; then
                  copy_ph_template 'dmx'
               elif [[ ! -z "$SHELF_SWITCH" && "$SHELF_SWITCH" =~ "CMX" && "$APG_OAM_ACCESS" == "FRONTCABLE" ]]; then
                 copy_ph_template 'gep5_dmx_10g_bonding'
               elif [[ ! -z "$SHELF_SWITCH" && "$SHELF_SWITCH" =~ "CMX" && "$APG_OAM_ACCESS" == "NOCABLE" ]]; then
                  if [[ "$INST_HW" =~ "GEP7" ]];then
                    copy_ph_template 'gep7L_dmx_cableless'
                  elif [ "$INST_HW" == 'GEP5_64_1200' ];then
                    copy_ph_template 'gep5_64_1200_dmx_cableless'
                  else
                    copy_ph_template 'gep5_dmx_cableless'
                  fi
               else	
	         copy_ph_template 'gep5_dmx'
               fi
            elif [[ "$SHELF_ARCHITECTURE" == "SCX" ]] && [[ "$SHELF_SWITCH" =~ "CMX" && "$INST_HW" =~ GEP5.* ]]; then
		copy_ph_template 'gep5_10g_haiad'
            elif [[ "$SHELF_ARCHITECTURE" == "SMX" ]] || [[ "$SHELF_ARCHITECTURE" == "SCX" && "$APG_OAM_ACCESS" == "NOCABLE" ]]; then
               if [[ "$INST_HW" =~ GEP5.* ]]; then
                 copy_ph_template 'gep5_smx_cableless'
               else
	         copy_ph_template 'gep7L_cableless'
               fi
            else
               if [[ "$INST_HW" == "GEP1" || "$INST_HW" == "GEP2" ]]; then
                  copy_ph_template
               else
		  copy_ph_template 'gep5'
               fi
            fi
            ;;

         AP2)
            if [[ "$SHELF_ARCHITECTURE" == "DMX" ]]  && [[ "$INST_HW" =~ GEP5.* || "$INST_HW" =~ "GEP7" ]]; then
              if [[ ! -z "$SHELF_SWITCH" && "$SHELF_SWITCH" =~ "CMX" && "$APG_OAM_ACCESS" == "FRONTCCABLE" ]]; then
                copy_ph_template 'gep5_ap2_dmx_10g_bonding'
              elif [[ ! -z "$SHELF_SWITCH" && "$SHELF_SWITCH" =~ "CMX" && "$APG_OAM_ACCESS" == "NOCABLE" ]]; then
                if [[ "$INST_HW" =~ "GEP7" ]];then
                  copy_ph_template 'gep7L_ap2_dmx_cableless' 
                elif [ "$INST_HW" == 'GEP5_64_1200' ];then
                  copy_ph_template 'gep5_64_1200_ap2_dmx_cableless' 
                else
	          copy_ph_template 'gep5_ap2_dmx_cableless' 
                fi
               else
                 copy_ph_template 'gep5_ap2_dmx' 
               fi
             elif [[ "$INST_HW" =~ GEP5.* ]]; then
               if [[ "$SHELF_ARCHITECTURE" == "SCX" && "$SHELF_SWITCH" =~ "CMX" ]]; then
                 copy_ph_template 'gep5_ap2_10g_haiad'
               else
                 copy_ph_template 'gep5_ap2'
               fi
             elif [[ "$SHELF_ARCHITECTURE" == "SMX" ]]; then
               if [[ "$INST_HW" =~ "GEP7" ]];then
                 copy_ph_template 'gep7L_ap2_smx_cableless'
               fi
             else			
	       copy_ph_template 'ap2'
             fi	
             ;;            
          esac
       else
          abort "Failure while filling AP_TYPE"
       fi
   fi
# Check available AIT plugins
AIT_DEPLOY="deploy_ait_ta.sh"
AIT_REPO="non_exec-ait-repo.conf"
AIT_OPT="non_exec-NOBCK"
AIT_PKG=""
[ ! -f $SW_DIR/$PLUGIN_DIR/$AIT_DEPLOY ] && abort "$SW_DIR/$PLUGIN_DIR/$AIT_DEPLOY not found"
[ ! -f $SW_DIR/$PLUGIN_DIR/$AIT_REPO ] && abort "$SW_DIR/$PLUGIN_DIR/$AIT_REPO not found"
[ ! -f $SW_DIR/$PLUGIN_DIR/$AIT_OPT ] && abort "$SW_DIR/$PLUGIN_DIR/$AIT_OPT not found"
AIT_PKG=$(find ./$SW_DIR/$PLUGIN_DIR/ -name "dxtoolbox-ait_*runtime*cxp9020536.tar.gz" | sed "s@.*/@@g")
[ -z $AIT_PKG ] && abort "$SW_DIR/$PLUGIN_DIR/$AIT_PKG not found"
echo $AIT_PKG
# Prepare AIT plugins
AIT_TA_RPM=""
AIT_TMP_DIR="TMP"
mkdir -p $SW_DIR/$PLUGIN_DIR/$AIT_TMP_DIR || abort "Failure in creating $SW_DIR/$PLUGIN_DIR/$AIT_TMP_DIR"
tar xf $SW_DIR/$PLUGIN_DIR/$AIT_PKG -C $SW_DIR/$PLUGIN_DIR/$AIT_TMP_DIR || abort "Failure in extracting $AIT_PKG"
# Find AIT-TA rp
AIT_TA_PKG=$(find ./$SW_DIR/$PLUGIN_DIR/$AIT_TMP_DIR/ -name "dxtoolbox-ait_ta-*runtime*cxp9019385.tar.gz" | sed "s@.*/@@g")
echo $AIT_TA_PKG
[ -z $AIT_TA_PKG ] && abort "$AIT_TA_PKG not found"
tar xf $SW_DIR/$PLUGIN_DIR/$AIT_TMP_DIR/$AIT_TA_PKG -C $SW_DIR/$PLUGIN_DIR/$AIT_TMP_DIR/ || abort "Failure in extracting $AIT_TA_PKG"
AIT_TA_RPM=$(find ./$SW_DIR/$PLUGIN_DIR/$AIT_TMP_DIR/ -name "*ait-ta-cxp9019385*.noarch.rpm" | sed "s@.*/@@g")
[ -z $AIT_TA_RPM ] && abort "$AIT_TA_RPM not found"

# Copy AIT plugins to ah hooks
cp $SW_DIR/$PLUGIN_DIR/$AIT_TMP_DIR/$AIT_TA_RPM $HOOKS_DIR/ah/$AIT_TA_RPM || abort "Failure while copying $SW_DIR/$PLUGIN_DIR/$AIT_TMP_DIR/$AIT_TA_RPM"
cp $SW_DIR/$PLUGIN_DIR/$AIT_DEPLOY $HOOKS_DIR/ah/$AIT_DEPLOY || abort "Failure while copying $SW_DIR/$PLUGIN_DIR/$AIT_DEPLOY"
cp $SW_DIR/$PLUGIN_DIR/$AIT_REPO $HOOKS_DIR/ah/$AIT_REPO || abort "Failure while copying $SW_DIR/$PLUGIN_DIR/$AIT_REPO"
cp $SW_DIR/$PLUGIN_DIR/$AIT_OPT $HOOKS_DIR/ah/$AIT_OPT || abort "Failure while copying $SW_DIR/$PLUGIN_DIR/$AIT_OPT"

# Clean AIT tmp plugins
rm -rf $SW_DIR/$PLUGIN_DIR/$AIT_TMP_DIR

TEMPLATES_DIR="templates"
TEMPLATE_1="DiskPartGEP1-2.conf"
TEMPLATE_2="DiskPartGEP400.conf"
TEMPLATE_3="DiskPartGEP1200.conf"
TEMPLATE_4="DiskPartGEP1600.conf"
TEMPLATE_5="DiskPartGEP5VM.conf"
TEMPLATE_6="DiskPartGEP5_64_1200.conf"
TEMPLATE_7="DiskPartGEP7L_400.conf"
TEMPLATE_8="DiskPartGEP7L_1600.conf"
TEMPLATE_9="DiskPartGEP7L_1200.conf"

TMP_ETC_DIR="etc_tmp"
INST_CONF="installation.conf"

if [ -d $TEMPLATES_DIR ]; then
  
  # make a temporary directory
  mkdir -p $TMP_ETC_DIR || abort "Failure in creating $TMP_ETC_DIR"
  
  case "$INST_HW" in
    GEP1|GEP2)
      [ ! -f $TEMPLATES_DIR/$TEMPLATE_1 ] && abort "Template $TEMPLATES_DIR/$TEMPLATE_1 not found"
      cp $TEMPLATES_DIR/$TEMPLATE_1 $TMP_ETC_DIR/$INST_CONF
    ;;
    GEP4_400|GEP5_400)
      [ ! -f $TEMPLATES_DIR/$TEMPLATE_2 ] && abort "Template $TEMPLATES_DIR/$TEMPLATE_2 not found"
      cp $TEMPLATES_DIR/$TEMPLATE_2 $TMP_ETC_DIR/$INST_CONF
    ;;
    GEP5_1200)
      [ ! -f $TEMPLATES_DIR/$TEMPLATE_3 ] && abort "Template $TEMPLATES_DIR/$TEMPLATE_3 not found"
      cp $TEMPLATES_DIR/$TEMPLATE_3 $TMP_ETC_DIR/$INST_CONF
    ;;
    GEP4_1600|GEP5_1600)
      [ ! -f $TEMPLATES_DIR/$TEMPLATE_4 ] && abort "Template $TEMPLATES_DIR/$TEMPLATE_4 not found"
      cp $TEMPLATES_DIR/$TEMPLATE_4 $TMP_ETC_DIR/$INST_CONF
    ;;
	  GEP5)
      [ ! -f $TEMPLATES_DIR/$TEMPLATE_5 ] && abort "Template $TEMPLATES_DIR/$TEMPLATE_5 not found"
      cp $TEMPLATES_DIR/$TEMPLATE_5 $TMP_ETC_DIR/$INST_CONF
    ;;
    GEP5_64_1200)
      [ ! -f $TEMPLATES_DIR/$TEMPLATE_6 ] && abort "Template $TEMPLATES_DIR/$TEMPLATE_6 not found"
      cp $TEMPLATES_DIR/$TEMPLATE_6 $TMP_ETC_DIR/$INST_CONF
    ;;
    GEP7L_400)
      [ ! -f $TEMPLATES_DIR/$TEMPLATE_7 ] && abort "Template $TEMPLATES_DIR/$TEMPLATE_7 not found"
      cp $TEMPLATES_DIR/$TEMPLATE_7 $TMP_ETC_DIR/$INST_CONF
    ;;
    GEP7L_1600)
        [ ! -f $TEMPLATES_DIR/$TEMPLATE_8 ] && abort "Template $TEMPLATES_DIR/$TEMPLATE_8 not found"
        cp $TEMPLATES_DIR/$TEMPLATE_8 $TMP_ETC_DIR/$INST_CONF
    ;;
    GEP7_128_1600)
      [ ! -f $TEMPLATES_DIR/$TEMPLATE_8 ] && abort "Template $TEMPLATES_DIR/$TEMPLATE_8 not found"
      cp $TEMPLATES_DIR/$TEMPLATE_8 $TMP_ETC_DIR/$INST_CONF
    ;;

    *)
      abort "Failure while taking the template file. Invalid hardware : ${INST_CONF}"
    ;;
  esac

  [ ! -f $TMP_ETC_DIR/$INST_CONF ] && abort "File $TMP_ETC_DIR/$INST_CONF not found. Problem during template copy"

  str_replace "$TMP_ETC_DIR/$INST_CONF" "${DEF_ROOT_PASSWORD_HASH}" "${ROOT_HASH}"
  
  # Filling the installation.conf file
  if [ $OPT_SYSTEM -eq $TRUE ]; then
    case "$INST_HW" in
      GEP1)
        str_replace "$TMP_ETC_DIR/$INST_CONF" "<system_disk_device>" "\/dev\/sdd"
      ;;
      GEP2)
        str_replace "$TMP_ETC_DIR/$INST_CONF" "<system_disk_device>" "\/dev\/sdb"
      ;;
      GEP4_400|GEP5_400|GEP5_1200|GEP5_64_1200|GEP4_1600|GEP5_1600|GEP5|GEP7|GEP7L_400|GEP7L_1600|GEP7_128_1600)
        # do nothing because the system disk is fixed in the templates
      ;;
      *)
        abort "Failure while filling the ${INST_CONF} file. Invalid hardware"
      ;;
    esac
  fi


  str_replace "$TMP_ETC_DIR/$INST_CONF" "<partition_boot_size>" $BOOT_SIZE
  str_replace "$TMP_ETC_DIR/$INST_CONF" "<partition_log_size>" $LOG_SIZE
  str_replace "$TMP_ETC_DIR/$INST_CONF" "<partition_root_size>" $ROOT_SIZE  
  if [[ "$INST_HW" == "GEP1" || "$INST_HW" == "GEP2" ]]; then
    str_replace "$TMP_ETC_DIR/$INST_CONF" "<partition_swap_size>" $SWAP_SIZE
  fi

  str_replace "$TMP_ETC_DIR/$INST_CONF" "<shared_filesystem_size>" $FILESYSTEM_SIZE
  str_replace "$TMP_ETC_DIR/$INST_CONF" "<linux_control_x86_64_rpm>" "$LOTC_CTRL_RPM"

else
  abort "Folder $TEMPLATES_DIR not found"
fi

touch $TMP_ETC_DIR/cluster.conf

# Deployment tool invocation
[ ! -x "$DEPLOY_TOOL" ] && abort "$DEPLOY_TOOL not found or not executable"
if [ $OPT_SYSTEM -eq $TRUE ]; then
  $DEPLOY_TOOL -l $DEPLOY_EDITION -s $LOTC_DIR -c $TMP_ETC_DIR -t $DEPLOY_TYPE -b $TFTP_DIR -P $HOOKS_DIR/ph -O $HOOKS_DIR/oh -A $HOOKS_DIR/ah $DEPLOY_DEBUG
else
  $DEPLOY_TOOL -l $DEPLOY_EDITION -s $LOTC_DIR -c flash/etc -t $DEPLOY_TYPE -b $TFTP_DIR $DEPLOY_DEBUG
fi

# Notes:
# 1. The /tftpboot/mi/del/base folder contains the software (vmlinuz, pxelinux.0, initrd, boot.msg, <LOTC control RPM>, pxelinux.cfg/*) from the RUNTIME package as it is.
# 2. The /tftpboot/mi/template/base folder contains the cluster.conf and the installation.conf files from the RUNTIME package as it is.
# 3. The /tftpboot/mi/template/current folder contains the cluster.conf and the installation.conf files adapted according to the lsv delivery of APOS.

# Clean temporary directory
if [ -d $TMP_ETC_DIR ]; then
  rm -rf $TMP_ETC_DIR
fi

# Deploying the siteparam.conf and factoryparam.conf files
if [ $OPT_SYSTEM -eq $TRUE ]; then
  [ ! -d $ETC_DIR ] && abort "Folder $ETC_DIR not found"
  pushd "$ETC_DIR" > /dev/null 2>&1
  SITE_CONF="siteparam.conf"
  FACT_CONF="factoryparam.conf"

  if [ -f $SITE_CONF ]; then
    cp $SITE_CONF $TFTP_DIR/$ETC_DIR || abort "Failure while copying $SITE_CONF"
  else
    abort "$SITE_CONF not found!"
  fi
  if [ -f $FACT_CONF ]; then
    cp $FACT_CONF $TFTP_DIR/$ETC_DIR || abort "Failure while copying $FACT_CONF"
	
	if [ $isVirtual_env_profile -eq $FALSE ]; then
		if grep "virtual_env_profile" $TFTP_DIR/$ETC_DIR/$FACT_CONF > /dev/null
		then
			str_replace "$TFTP_DIR/$ETC_DIR/$FACT_CONF" "virtual_env_profile=" "virtual_env_profile=$virtual_env_profile" 
		else
			echo "virtual_env_profile=$virtual_env_profile"  >> $TFTP_DIR/$ETC_DIR/$FACT_CONF
		fi
	fi

	if [ $isDeployment_environment -eq $FALSE ]; then
		if grep "deployment_environment" $TFTP_DIR/$ETC_DIR/$FACT_CONF > /dev/null
		then
			str_replace "$TFTP_DIR/$ETC_DIR/$FACT_CONF" "deployment_environment=" "deployment_environment=$deployment_environment" 
		else
			echo "deployment_environment=$deployment_environment" >> $TFTP_DIR/$ETC_DIR/$FACT_CONF
		fi
	fi

	if [ $isDatadisk_replication_type -eq $FALSE ]; then
		if grep "datadisk_replication_type" $TFTP_DIR/$ETC_DIR/$FACT_CONF > /dev/null
		then
			str_replace "$TFTP_DIR/$ETC_DIR/$FACT_CONF" "datadisk_replication_type=" "datadisk_replication_type=$datadisk_replication_type" 
		else
			echo "datadisk_replication_type=$datadisk_replication_type" >> $TFTP_DIR/$ETC_DIR/$FACT_CONF
		fi
	fi
  else
    echo "WARNING: The $FACT_CONF configuration file is not present!"
  fi
  popd > /dev/null 2>&1
fi

# Deploying the sw.tar.gz file
if [ $OPT_SYSTEM -eq $TRUE ]; then
  [ ! -d $SW_DIR ] && abort "Folder $SW_DIR not found"
  pushd "$SW_DIR" > /dev/null 2>&1
  SW_TGZ="sw.tar.gz"
  if [ -f $SW_TGZ ]; then
     echo "--  Deploying the $SW_TGZ file"
  else
     abort " Failure. $SW_TGZ not found. "
  fi
fi

# AP2 impacts - create a temporary folder
#TEMP_DIR="temp"
#if [ ! -d $TEMP_DIR ]; then
#  echo -n "-   Creating the $TEMP_DIR folder... "
#  mkdir $TEMP_DIR || abort "Failure in creating $TEMP_DIR"
#  echo "--  done"
#else
#  echo -n "-   The $TEMP_DIR folder is already present, deleting its content... "
#  if find $TEMP_DIR/* -depth -delete &>/dev/null; then
#    echo "--  done"
#  else
#    echo "--  done (no files to be deleted)"
#  fi
#fi	
#if [ -d $TEMP_DIR ]; then
#  tar -xzf $SW_TGZ -C $TEMP_DIR 2>/dev/null || abort " Failure. Unable to untar the sw.tar.gz file. "
#  pushd "$TEMP_DIR" > /dev/null 2>&1
#  MINI_IPA="MINI-IPA.conf"
#  BDL_DIR="bdl"
#  CMW_DIR="cmw"
#  CGN_DIR="cgn"

  echo "--  Checking sw.tar.gz content..."
  CSMFILE=$(tar tf sw.tar.gz|grep -x csm.metadata)
  if [ $CSMFILE == "csm.metadata" ]; then
     echo "-- Done"
  else
     abort " Failure. Missing content of sw.tar.gz  "
  fi
  #Recreate sw.tgz
  #tar czf sw.tgz * || abort " Fatal error during tar operation of sw.tgz "
  #if [ -f $SW_TGZ ]; then
   mkdir -p $TFTP_DIR/$SW_DIR || abort "Failure while creating $TFTP_DIR/$SW_DIR"
   cp $SW_TGZ $TFTP_DIR/$SW_DIR || abort "Failure while copying $SW_TGZ"
   echo "- Operations on sw.tgz executed SUCCESSFULLY!"
#  else
#    abort "WARNING: The $SW_TGZ file is not present!"
#  fi
#  delete_dir "../$TEMP_DIR"
#  popd > /dev/null 2>&1
#else
#  abort " Failure. Unable to untar the sw.tgz file in the temporary folder. "
#fi
	
# Applying patches
PATCHES_DIR="patches"
PXE_CFG_DIR="pxelinux.cfg"
if [ -d $PATCHES_DIR ]; then
  echo ""; echo "WARNING: Applying patches!"
  pushd "$PATCHES_DIR" > /dev/null 2>&1
  # To change the boot.msg and/or the initrd and/or the linux control rpm and/or
  # the pxelinux.0 and/or the vmlinuz file(s) with patched versions.
  if [ -d $LOTC_DIR ]; then
    # Look for not empty directory
    if [ "$(ls -A $LOTC_DIR)" ]; then
      pushd "$LOTC_DIR" > /dev/null 2>&1
      for FILE in ./*; do
        echo "Overwriting LOTC $FILE file in the $TFTP_DIR folder."
        cp -f $FILE $TFTP_DIR || abort "Failure while copying $FILE"
      done
      popd > /dev/null 2>&1
    fi
  fi
  # To configure the PXE server with more than one STP.
  if [ -d $PXE_CFG_DIR ]; then
    # Look for not empty directory
    if [ "$(ls -A $PXE_CFG_DIR)" ]; then
      pushd "$PXE_CFG_DIR" > /dev/null 2>&1
      for FILE in ./*; do
        echo "Writing PXE $FILE configuration file in the $TFTP_DIR/$PXE_CFG_DIR folder."
        cp $FILE $TFTP_DIR/$PXE_CFG_DIR || abort "Failure while copying $FILE"
      done
      popd > /dev/null 2>&1
    fi
  fi
  popd > /dev/null 2>&1
fi


## BEGIN
# Checks and workaround to handle download_path entries in pxelinux.cfg/default
##
function is_dp_set() {
  for ITEM in $(cat $TFTP_DIR/$PXE_CFG_DIR/default | grep download_path); do
    if [[ "$ITEM" =~ ^cluster= ]]; then
      DP=$(echo "$ITEM" | awk -F"download_path=" '{print $2}' | tr -d ')')
      if [ -z "$DP" ]; then
        return $FALSE
      fi
   fi
  done
  return $TRUE
}

chmod +x $TFTP_DIR/$PXE_CFG_DIR
echo "-   added executing permissions to $TFTP_DIR/$PXE_CFG_DIR"

echo "-   populating download_path"
TFTPROOT=''

if [ -f /etc/sysconfig/atftpd ]; then
	echo "-   atftpd daemon identified"
	TFTPROOT=$(grep 'ATFTPD_DIRECTORY=' /etc/sysconfig/atftpd | awk -F= '{print $2}' | tr -d '"')
elif [ -f /etc/xinetd.d/tftp ]; then
	echo "-   tftpd daemon identified"
	TFTPROOT=$(grep 'server_args' /etc/xinetd.d/tftp | awk -F'-s' '{print $2}' | awk '{print $1}' | tr -d [:space:])
else
	abort "no supported tftp daemon has been found"
fi

[ -z "$TFTPROOT" ] && abort "unable to fetch tftp root directory"
	
if [ "$TFTP_DIR" == "$TFTPROOT" ]; then
	DOWNLOAD_PATH=/
else
	DOWNLOAD_PATH=$(echo $TFTP_DIR | sed "s@${TFTPROOT}@@g")
fi

sed -i -r "s@cluster=\(type=install(\)|,download_path=\))@cluster=\(type=install,download_path=${DOWNLOAD_PATH}\)@g" $TFTP_DIR/$PXE_CFG_DIR/default
sed -i -e "s@TIMEOUT.*@TIMEOUT 50@g" $TFTP_DIR/$PXE_CFG_DIR/default

if is_dp_set; then
	echo "-   download_path populated with \"${DOWNLOAD_PATH}\""
else
	abort 'failure while populating download_path'
fi

##
# Checks and workaround to handle download_path entries in pxelinux.cfg/default
## END

#delete_dir "$LOTC_DIR"
delete_dir "../$LOTC_DIR"
delete_dir "../$SW_DIR/$LOTC_DIR"

echo " * DEPLOYMENT COMPLETED * "
echo $WELCOME_SEP

exit $EXIT_SUCCESS

# EOF
