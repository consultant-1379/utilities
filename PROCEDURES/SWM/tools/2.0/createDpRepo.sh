#!/bin/bash

###########################################################################
# ------------------------------------------------------------------------
#     Copyright (C) 2018 Ericsson AB. All rights reserved.
# ------------------------------------------------------------------------
###########################################################################

view=$1
get_arg="$(echo $view | cut -f2 -d '/')"
echo $get_arg
if [[ $get_arg == view ]]; then
echo "*********"
shift 1
fi

SWM_HOME=$( pwd)
SWM_HOME=$( SWM_HOME=${SWM_HOME:1}; echo $SWM_HOME | sed 's@/SWM.*@/SWM@g')

DIRNAME="$view/$SWM_HOME/workspace"
APG_VERSIONS_AP='apg43l_versions_ap.xml'
APG_VERSIONS_ALL='apg43l_versions_all.xml'
AF_CONFIG='ArtifactManager.cfg'
AF_CONFIG_AP='ArtifactManager_ap.cfg'
AF_CONFIG_ALL='ArtifactManager_all.cfg'
CMD_GETOPT='/usr/bin/getopt'
CP='/usr/bin/cp'
CD='/usr/bin/cd'
RM='/usr/bin/rm'
AF='artifact_manager'

function declaring_variables {
#if [ $USER == teiaxeio ]; then
#	 LOCALSW="/home/teiaxeio/esm_workspace/local-sw"
#else
LOCALSW="$DIRNAME/local-sw"
#fi
BASE="$DIRNAME/baseline"
}

function usage {
cat <<- EOF

Usage: $0 OPTION

First copy APG deployment and runtime packages to local-sw repo, then download CBA and APG deployment packages using artifact manager to populate the DP-repo

    [-w, --workspace=PATH]           Full path of CSM workspace. Default value is $DIRNAME
    [-h, --help]                     Display this help and exit

Example:
    $0
    $0 -w $view/$SWM_HOME/workspace 

Exit status:
   0    Success
   1    Error
   2	Wrong usage

EOF
}

function parse_cmdline {
	local PARAM=$@
	$CMD_GETOPT --quiet --quiet-output --longoptions="workspace:" --options="w:" -- "$@"
	local ARGS="$@"
	eval set -- "$ARGS"
	
	if [ $# -eq 0 ];then
		echo "[INFO] using default workspace: <$DIRNAME>"
		return
	fi
	
	# Make sure to handle the cases for all the options listed in OPTIONS
	#  and LONG_OPTIONS and to fill up the right script-wide variables.
	while [ $# -gt 0 ]; do
		case "$1" in
		--workspace|-w)
			DIRNAME=$2
			if [[ "$2" =~ [a-zA-z0-9]+$ ]] ; then
				echo "INFO" "The csm workspace path is $2"
				shift
			else
				usage
				exit 2
			fi
		;;
		--help|-h)
			usage
			exit 0
		;;
		*)
			usage
			exit 1
		;;
		esac
		shift
	done
}

################################################
### COPY COMPONENTS FROM ARM to local-sw repo ###
################################################

function get_apg_packages {
  # remove existing/old ArtifactManager.cfg
  $RM -f $AM_WORKSPACE/$AF_CONFIG &>/dev/null

  # update ArtifactManager configuration 
  $CP $AM_WORKSPACE/$AF_CONFIG_AP  $AM_WORKSPACE/$AF_CONFIG -f &>/dev/null
  if [ $? != 0 ]; then 
    echo ""
    echo "[ERROR] $AM_WORKSPACE/$AF_CONFIG_AP Copy failed"
    echo ""
    exit 1
  fi

  echo ""
  echo "#########################################################################"
  echo "###### DOWNLOADING APG DEPLOYMENT AND RUNTIME PACKAGES FROM ARM ######"
  echo "artifact_manager --get-packages --input $BASE/$APG_VERSIONS_AP --outputDir $LOCALSW --flat"
  $AF --get-packages --input $BASE/$APG_VERSIONS_AP --outputDir $LOCALSW --flat
  if [ $? == 0 ]; then
    echo ""
    echo "[INFO] artifact_manager command executed successfully"
    echo "[INFO] local-sw populated with all needed packages"
    echo ""
  else
    echo ""
    echo "[ERROR] artifact_manager could not download packages: check the error messages"
    echo ""
    exit 1
  fi
}

function get_all_packages {
  # remove existing/old ArtifactManager.cfg
  $RM -f $AM_WORKSPACE/$AF_CONFIG

  # update ArtifactManager configuration 
  $CP $AM_WORKSPACE/$AF_CONFIG_ALL  $AM_WORKSPACE/$AF_CONFIG -f
  if [ $? != 0 ]; then 
    echo ""
    echo "[ERROR] $AM_WORKSPACE/$AF_CONFIG_ALL Copy failed"
    echo ""
    exit 1
  fi

  echo ""
  echo "#########################################################"
  echo "####### DOWNLOADING APG & CBA DEPLOYMENT PACKAGES #######"
  echo "artifact_manager --get-packages --input $BASE/$APG_VERSIONS_ALL --flat --outputDir $CSM_REGISTRY --extract"
  $AF --get-packages --input $BASE/$APG_VERSIONS_ALL --flat --outputDir $CSM_REGISTRY --extract
  if [ $? == 0 ];then
    echo ""
    echo "[INFO] artifact_manager command executed successfully"
    echo "[INFO] DP-repo populated with all needed deployment packages"
    echo ""
  else
    echo ""
    echo "[ERROR] artifact_manager could not download deployment packages: check the error messages"
    echo ""
    exit 1
 fi
} 

function verify_mandatory_folders {
  local FOLDERS_LIST="$@"
  for i in $FOLDERS_LIST; do
    if [ ! -d $i ];then
      mkdir -p $i
      echo "#Folder $i is created"
    fi
  done
}

function verify_mandatory_files {
  local FILE_LIST="$BASE/$APG_VERSIONS_AP $BASE/$APG_VERSIONS_ALL $AM_WORKSPACE/$AF_CONFIG_AP $AM_WORKSPACE/$AF_CONFIG_ALL"
  for FILE in $FILE_LIST; do
    if [ ! -f $FILE ]; then 
      echo "[ERROR] $FILE not exist.. exiting"
      echo ""
      exit 1
    fi
  done
}

#################################################
#Setting of PSO TYPE in LDE BRF
function set_pso_type(){
  echo "BEGIN: Applying fix for PSO Type ... "
  local LDE_BRF=$(find $CSM_REGISTRY -name "ldews-brf*")
  local PREINSTALL_CONF=$(find $LDE_BRF -name "preinstall.conf")
  if [[ -n "$PREINSTALL_CONF" && -f $PREINSTALL_CONF ]];then
    echo "File $PREINSTALL_CONF exist applying the patch ..."
    if grep -qw 'PSO_TYPE=BOTH' $PREINSTALL_CONF 2>/dev/null; then
      sed -i 's/PSO_TYPE=BOTH/PSO_TYPE=SYSTEM/' $PREINSTALL_CONF
      if [ $? -ne 0 ]; then
        echo "Failure in setting PSO_TYPE from BOTH to SYSTEM... "
      else
        echo "Setting of PSO_TYPE from BOTH to SYSTEM done.."
      fi
    else
      echo 'Already PSO_TYPE is set to SYSTEM, Skipping changes...'
    fi
  else
    echo "File $PREINSTALL_CONF does not exist..."
  fi
  echo "END: Applying fix for PSO_TYPE... "
}

# campaignInstantiationTimeout --> 1800s(default) --> 7200s(New val for virtual)
# Update the timeout for activating campaign during instantiation. 
# In virtual scenario, installation taking morethan 30 mins and this
# needs to be updated to 60 mins to allow deployment to success
function update_campaign_timeout() {
  echo "BEGIN: Updating campaignInstantiationTimeout for virtual... "
  local CMW_SLE_DEPLOY=$(find $CSM_REGISTRY -name "coremw_x86_64-[0-9]*-deployment-sle*")
  local PREINSTALL_CONF=$(find $CMW_SLE_DEPLOY/sle12/csm -name "preinstall.conf")
  if [[ -n "$PREINSTALL_CONF" && -f $PREINSTALL_CONF ]];then
    echo "File preinstall.conf[$PREINSTALL_CONF]exist.."
    echo "updating campaignInstantiationTimeout ..."
    if grep -qw 'campaignInstantiationTimeout' $PREINSTALL_CONF 2>/dev/null; then    
      sed -i 's/campaignInstantiationTimeout=.*/campaignInstantiationTimeout=7200/' $PREINSTALL_CONF 2>/dev/null
      if [ $? -ne 0 ]; then
        echo "Failure in setting campaignInstantiationTimeout to 120min... "
        exit 1
      else
        echo "Setting of campaignInstantiationTimeout to 120 min done... "
      fi
    else
      echo 'campaignInstantiationTimeout parameter not found, Skipping changes...'
    fi 
  else
    echo "File $PREINSTALL_CONF does not exist..."
  fi
  echo "END: Updating campaignInstantiationTimeout for virtual... " 

}

#Setting customize_log_hostname_with_meid to TRUE in lde-log-controller.conf  file of LDEwS
#This logic is required to have the Managed element ID tagged to streamed log events
function customize_log_hostname(){
  echo "BEGIN: Setting customize_log_hostname_with_NME attribute to TRUE ... "
  local LDEwS_SLE_DEPLOY=$(find $CSM_REGISTRY -name "ldews-[0-9]*-deployment-sle-cxp9020284")
  local LOG_CONTROLLER_CONF=$(find $LDEwS_SLE_DEPLOY/csm/config/initial/ldews.logcontroller -name "lde-log-controller.conf")
  if [[ -n "$LDEwS_SLE_DEPLOY" && -f $LOG_CONTROLLER_CONF ]];then
    echo "File $LOG_CONTROLLER_CONF exist applying the patch ..."
    if grep -qw 'customize_log_hostname' $LOG_CONTROLLER_CONF 2>/dev/null; then
      sed -i 's/{customize_log_hostname,false}/{customize_log_hostname,true}/' $LOG_CONTROLLER_CONF
      if [ $? -ne 0 ]; then
        echo "Failure in setting customize_log_hostname_with_NME to TRUE... "
      else
        echo "Setting of customize_log_hostname_with_NME to TRUE done.."
      fi
    else
      echo "customize_log_hostname_with_NME attribute does not exists, Skipping changes..."
    fi
  else
    echo "File $LOG_CONTROLLER_CONF does not exist..."
  fi
  echo "END: Setting customize_log_hostname_with_NME attribute to TRUE ... "
}

function enable_reject_password_with_username(){
  echo "BEGIN: Setting SEC_ACS_PAM_REJECT_PASSWORD_WITH_PART_USERNAME attribute to enable ... "
  local SEC_SLE_DEPLOY=$(find $CSM_REGISTRY -name "sec-acs-[0-9]*-deployment-sle-cxp9026451")
  local SEC_CSM_YML=$(find $SEC_SLE_DEPLOY/csm -name "cba-sec-acs-csm.yml")
  if [[ -n "$SEC_SLE_DEPLOY" && -f $SEC_CSM_YML ]];then
    echo "File $SEC_CSM_YML exist applying the patch ..."
    if grep -qw 'SEC_ACS_PAM_REJECT_PASSWORD_WITH_PART_USERNAME' $SEC_CSM_YML 2>/dev/null; then
echo "......inside if ....."
      sed -i 's/SEC_ACS_PAM_REJECT_PASSWORD_WITH_PART_USERNAME: "disable"/SEC_ACS_PAM_REJECT_PASSWORD_WITH_PART_USERNAME: "enable"/' $SEC_CSM_YML
      if [ $? -ne 0 ]; then
        echo "Failure in setting SEC_ACS_PAM_REJECT_PASSWORD_WITH_PART_USERNAME to enable... "
      else
        echo "Setting of SEC_ACS_PAM_REJECT_PASSWORD_WITH_PART_USERNAME to enable done.."
      fi
    else
      echo "SEC_ACS_PAM_REJECT_PASSWORD_WITH_PART_USERNAME attribute does not exists, Skipping changes..."
    fi
  else
    echo "File $SEC_CSM_YML does not exist..."
  fi
  echo "END: Setting SEC_ACS_PAM_REJECT_PASSWORD_WITH_PART_USERNAME attribute to enable ... "
}


#Setting lde_runas_nonroot attribute to DISABLE in lde-nonroot.conf file of LDEwS
#This logic needs to be removed incase SUGaR feature 
#needs to be used in APG
function disable_sugar_feature(){
  echo "BEGIN: Setting lde_runas_nonroot attribute to DISABLED ... "
  local LDEwS_SLE_DEPLOY=$(find $CSM_REGISTRY -name "ldews-[0-9]*-deployment-sle-cxp9020284")
  local LDE_SUGAR_CONF=$(find $LDEwS_SLE_DEPLOY/csm/config/initial/ldews.os -name "lde-nonroot.conf")
  if [[ -n "$LDEwS_SLE_DEPLOY" && -f $LDE_SUGAR_CONF ]];then
    echo "File $LDE_SUGAR_CONF exist applying the patch ..."
    if grep -qw 'lde_runas_nonroot' $LDE_SUGAR_CONF 2>/dev/null; then
      sed -i 's/{lde_runas_nonroot,enabled}/{lde_runas_nonroot,disabled}/' $LDE_SUGAR_CONF
      if [ $? -ne 0 ]; then
        echo "Failure in setting lde_runas_nonroot to DISABLED... "
      else
        echo "Setting of lde_runas_nonroot to DISABLED done.."
      fi
    else
      echo "lde_runas_nonroot attribute does not exists, Skipping changes..."
    fi
  else
    echo "File $LDE_SUGAR_CONF does not exist..."
  fi
  echo "END: Setting lde_runas_nonroot attribute to DISABLED ... "
}

#Setting SEC_ACS_PAM_USER_GROUP_HARDENING attribute to DISABLE in cba-sec-acs-csm.yml file
#This logic needs to be removed incase SEC provided PAM hardening needs to be used in APG
function disable_pam_user_group_hardening(){
  echo "BEGIN: Setting SEC_ACS_PAM_USER_GROUP_HARDENING attribute to disable ... "
  local SEC_SLE_DEPLOY=$(find $CSM_REGISTRY -name "sec-acs-[0-9]*-deployment-sle-cxp9026451")
  local SEC_CSM_YML=$(find $SEC_SLE_DEPLOY/csm -name "cba-sec-acs-csm.yml")
  if [[ -n "$SEC_SLE_DEPLOY" && -f $SEC_CSM_YML ]];then
    echo "File $SEC_CSM_YML exist applying the patch ..."
    if grep -qw 'SEC_ACS_PAM_USER_GROUP_HARDENING' $SEC_CSM_YML 2>/dev/null; then
      sed -i 's/SEC_ACS_PAM_USER_GROUP_HARDENING: "enable"/SEC_ACS_PAM_USER_GROUP_HARDENING: "disable"/' $SEC_CSM_YML
      if [ $? -ne 0 ]; then
        echo "Failure in setting SEC_ACS_PAM_USER_GROUP_HARDENING to disable... "
      else
        echo "Setting of SEC_ACS_PAM_USER_GROUP_HARDENING to disable done.."
      fi
    else
      echo "SEC_ACS_PAM_USER_GROUP_HARDENING attribute does not exists, Skipping changes..."
    fi
  else
    echo "File $SEC_CSM_YML does not exist..."
  fi
  echo "END: Setting SEC_ACS_PAM_USER_GROUP_HARDENING attribute to disable ..."
}

#Enabling enhanced audit rules(8 rules) as part of CISCAT Improvements feature
function enable_enhanced_auditrules() {
  echo "BEGIN: Enabling the audit rules for the CISCAT Improvements..."
  local LDEwS_SLE_DEPLOY=$(find $CSM_REGISTRY -name "ldews-[0-9]*-deployment-sle-cxp9020284")
  local LDE_AUDIT_CONF=$(find $LDEwS_SLE_DEPLOY/csm/config/initial/ldews.os -name "audit-log.conf")
  if [[ -n "$LDEwS_SLE_DEPLOY" && -f $LDE_AUDIT_CONF ]];then
      echo "File $LDE_AUDIT_CONF exist applying the patch ..."

      #1###START: Enabling time and date audit rule####
      if grep -qw 'enable_auditd_time_change_logging' $LDE_AUDIT_CONF 2>/dev/null; then
        sed -i 's/{enable_auditd_time_change_logging,false}/{enable_auditd_time_change_logging,true}/' $LDE_AUDIT_CONF
        if [ $? -ne 0 ]; then
          echo "Failure in setting enable_auditd_time_change_logging... "
        else
          echo "Setting of enable_auditd_time_change_logging done.."
        fi
      else
      echo "enable_auditd_time_change_logging  attribute does not exists, Skipping changes..."
      fi
      ####END: Enabling time and date audit rule####

      #2###START: Enabling system locale audit rule####
      if grep -qw 'enable_auditd_system_locale_logging' $LDE_AUDIT_CONF 2>/dev/null; then
        sed -i 's/{enable_auditd_system_locale_logging,false}/{enable_auditd_system_locale_logging,true}/' $LDE_AUDIT_CONF
        if [ $? -ne 0 ]; then
          echo "Failure in setting enable_auditd_system_locale_logging... "
        else
          echo "Setting of enable_auditd_system_locale_logging done.."
        fi
      else
        echo "enable_auditd_system_locale_logging attribute does not exists, Skipping changes..."
      fi
      ####END: Enabling system locale audit rule####

      #3###START: Enabling identity audit rule####
      if grep -qw 'enable_auditd_identity_logging' $LDE_AUDIT_CONF 2>/dev/null; then
        sed -i 's/{enable_auditd_identity_logging,false}/{enable_auditd_identity_logging,true}/' $LDE_AUDIT_CONF
        if [ $? -ne 0 ]; then
          echo "Failure in setting enable_auditd_identity_logging... "
        else
          echo "Setting of enable_auditd_identity_logging done.."
        fi
      else
        echo "enable_auditd_identity_logging attribute does not exists, Skipping changes..."
      fi
      ####END: Enabling identity audit rule####

      #4###START: Enabling MAC policy audit rule####
      if grep -qw 'enable_auditd_mac_policy_logging' $LDE_AUDIT_CONF 2>/dev/null; then
        sed -i 's/{enable_auditd_mac_policy_logging,false}/{enable_auditd_mac_policy_logging,true}/' $LDE_AUDIT_CONF
        if [ $? -ne 0 ]; then
          echo "Failure in setting enable_auditd_mac_policy_logging... "
        else
          echo "Setting of enable_auditd_mac_policy_logging done.."
        fi
      else
        echo "enable_auditd_mac_policy_logging attribute does not exists, Skipping changes..."
      fi
      ####END: Enabling MAC policy audit rule####

      #5###START: Enabling login & logout audit rule####
      if grep -qw 'enable_auditd_logins_logging' $LDE_AUDIT_CONF 2>/dev/null; then
        sed -i 's/{enable_auditd_logins_logging,false}/{enable_auditd_logins_logging,true}/' $LDE_AUDIT_CONF
        if [ $? -ne 0 ]; then
          echo "Failure in setting enable_auditd_logins_logging... "
        else
          echo "Setting of enable_auditd_logins_logging done.."
        fi
      else
        echo "enable_auditd_logins_logging attribute does not exists, Skipping changes..."
      fi
      ####END: Enabling login & logout audit rule####

     #6###START: Enabling sessions  audit rule####
     if grep -qw 'enable_auditd_session_logging' $LDE_AUDIT_CONF 2>/dev/null; then
       sed -i 's/{enable_auditd_session_logging,false}/{enable_auditd_session_logging,true}/' $LDE_AUDIT_CONF
       if [ $? -ne 0 ]; then
         echo "Failure in setting enable_auditd_session_logging... "
       else
          echo "Setting of enable_auditd_session_logging done.."
       fi
     else
       echo "enable_auditd_session_logging attribute does not exists, Skipping changes..."
     fi
     ####END: Enabling sessions  audit rule####

     #7###START: Enabling kernel module  audit rule####
     if grep -qw 'enable_auditd_modules_logging' $LDE_AUDIT_CONF 2>/dev/null; then
       sed -i 's/{enable_auditd_modules_logging,false}/{enable_auditd_modules_logging,true}/' $LDE_AUDIT_CONF
       if [ $? -ne 0 ]; then
         echo "Failure in setting enable_auditd_modules_logging... "
       else
         echo "Setting of enable_auditd_modules_logging done.."
       fi
     else
       echo "enable_auditd_modules_logging attribute does not exists, Skipping changes..."
     fi
     ####END: Enabling kernel module audit rule####

     #8###START: Enabling sudoers audit rule#### 
     if grep -qw 'enable_auditd_scope_logging' $LDE_AUDIT_CONF 2>/dev/null; then
       sed -i 's/{enable_auditd_scope_logging,false}/{enable_auditd_scope_logging,true}/' $LDE_AUDIT_CONF
       if [ $? -ne 0 ]; then
         echo "Failure in setting enable_auditd_scope_logging... "
       else
         echo "Setting of enable_auditd_scope_logging done.."
       fi
     else
       echo "enable_auditd_scope_logging attribute does not exists, Skipping changes..."
     fi
     ####END: Enabling sudoers audit rule####

     #9###START: Enabling shell cmd and bash built-in cmd logging#### 
     if grep -qw 'enable_auditd_cmd_logging' $LDE_AUDIT_CONF 2>/dev/null; then
       sed -i 's/{enable_auditd_cmd_logging,false}/{enable_auditd_cmd_logging,true}/' $LDE_AUDIT_CONF
       if [ $? -ne 0 ]; then
         echo "Failure in setting enable_auditd_cmd_logging... "
       else
         echo "Setting of enable_auditd_cmd_logging done.."
       fi
     else
       echo "enable_auditd_cmd_logging attribute does not exists, Skipping changes..."
     fi
     ####END: Enabling shell cmd and bash built-in cmd logging####

  else

    echo "Failed to enable audit rules, the audit-log.conf file or the LDE base pkg does not exist..."

  fi

  echo "END: Enabling the audit rules for the CISCAT Improvements... "

}

#################################################

#################################################
#               |\/|  /\  | |\ |                #
#               |  | /--\ | | \|                #
#################################################

parse_cmdline $@
source ./common.sh $DIRNAME
declaring_variables
verify_mandatory_folders $LOCALSW
get_apg_packages
get_all_packages
set_pso_type
update_campaign_timeout
customize_log_hostname
enable_reject_password_with_username
disable_sugar_feature
disable_pam_user_group_hardening
enable_enhanced_auditrules
exit 0
