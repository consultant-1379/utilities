#!/bin/bash

# ------------------------------------------------------------------------
#     Copyright (C) 2021 Ericsson AB. All rights reserved.
# ------------------------------------------------------------------------


view=$1
get_arg="$(echo $view | cut -f2 -d '/')"
echo $get_arg
if [[ $get_arg == view ]]; then
echo "*********"
shift 1
fi

SWM_HOME=$( pwd)
SWM_HOME=$( SWM_HOME=${SWM_HOME:1}; echo $SWM_HOME | sed 's@/SWM.*@/SWM@g')

## BEGIN: directory PATH variables 
DIRNAME="$view/$SWM_HOME/workspace"
LOCALSW="$DIRNAME/local-sw"
BASE="$DIRNAME/baseline"
CAMDIR="$DIRNAME/CSM2AM_FOLD"
SPDIR="$DIRNAME/CSM2CSP_FOLD"
RT="$DIRNAME/RT-repo"
OUT_FOLD="$DIRNAME/package/csp"
TEMP_DIR="$view/$SWM_HOME/tools/2.0/workspace"

## BEGIN: file name variables 
VRP_VERSIONS_ALL='vrp_baseos_version.xml'
AF_CONFIG='ArtifactManager.cfg'
AF_CONFIG_ALL='ArtifactManager_all.cfg'

## BEGIN: command variables 
CMD_GETOPT='/usr/bin/getopt'
CP='/usr/bin/cp'
CD='/usr/bin/cd'
RM='/usr/bin/rm'
AF='artifact_manager'
CLI='csmcli'
CLNT='csmlint'
CSCONFG="csmconfig"
C2AM="csm2am"
C2CSP="csm2csp"
CUP="csp-upgrade-package-create"
CSMCLI="csmcli"
CSM2ICT="csm2ict"
CSMCONFIG="csmconfig"

function console_print() {
  echo ""
  echo "$@"
}

function console_abort() {
  echo ""
  echo "[ERROR] $@"
  echo ""
  exit 1
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
  local FILE_LIST="$BASE/$VRP_VERSIONS_ALL
                   $AM_WORKSPACE/$AF_CONFIG_ALL"
  for FILE in $FILE_LIST; do
    if [ ! -f $FILE ]; then 
      echo "[ERROR] $FILE not exist.. exiting"
      echo ""
      exit 1
    fi
  done
}

function cleaning_folders {
  local FOLDERS_LIST="$@"
  for i in $FOLDERS_LIST;do
    if [ -d $i ];then
      $RM -rf $i || console_abort "[ERROR] Cannot remove <$i>. RC: <$?>"
      console_print "[INFO] Deleted $i"
    fi 
  done
}
   
function cleaning_content {
  local FOLDERS_LIST="$@"
  for i in $FOLDERS_LIST;do
    if [ -d $i ];then
      $RM -rf $i/* || console_abort "[ERROR] Cannot clean <$i>. RC: <$?>"
      console_print "[INFO] Delete content of $i"
    fi
  done
}

function remove_logs {
  local CSPLOGS="$DIRNAME/../tools/2.0/csp.log*"
  echo "[COMMAND] $RM -rf $CSPLOGS"
  $RM -rf $CSPLOGS || console_abort "[ERROR] Cannot remove <$CSPLOGS>. RC: <$?>"
}

function createDpRepo() {

  verify_mandatory_folders $LOCALSW

  # remove existing/old ArtifactManager.cfg
  $RM -f $AM_WORKSPACE/$AF_CONFIG

  # update ArtifactManager configuration
  $CP $AM_WORKSPACE/$AF_CONFIG_ALL  $AM_WORKSPACE/$AF_CONFIG -f
  [ $? != 0 ] && console_abort "$AM_WORKSPACE/$AF_CONFIG_ALL Copy failed"

  console_print "####### DOWNLOADING LDE DEPLOYMENT PACKAGE #######"
  #echo "artifact_manager --get-packages --input $BASE/$APG_VERSIONS_ALL --flat --outputDir $CSM_REGISTRY --extract"
  $AF --get-packages --input $BASE/$VRP_VERSIONS_ALL --flat --outputDir $CSM_REGISTRY --extract
  if [ $? == 0 ];then
    console_print "[INFO] DP-repo populated with all needed deployment packages"
  else
    console_abort "artifact_manager could not download deployment package: check the error messages"
 fi

}

function createCsm() {

  verify_mandatory_folders $CSM_WORKSPACE

  #create_ldecsm
  echo "CLEAN workspace" ###
  $CLI clean -c
  pushd $CSM_WORKSPACE
  $RM -rf config ovf-env.xml plugin  # NOTE THAT config ovf-env.xml plugin are created by csmconfig init
  popd

  console_print "IMPORT functions ldews.ecim.equipment, ldews.base"
  $CLI import --functions ldews.base

  console_print "REMOVE ldews.os.payload service from the specified ldews.base function"
  $CLI function-remove-services ldews.base ldews.os.payload

  console_print "DELETE ldews.os.payload, ldews.os.pl, ldews.config.pl, ldews.pmcounters.pl"

  $CLI service-delete ldews.os.payload
  $CLI service-delete ldews.os.pl
  $CLI service-delete ldews.config.pl
  $CLI service-delete ldews.pmcounters.pl

  console_print "DELETE component ldews.config.pl, ldews.pmcounters.pl, ldews.os.pl"
  $CLI component-delete ldews.config.pl
  $CLI component-delete ldews.pmcounters.pl
  $CLI component-delete ldews.os.pl

  $CLI system-create RP --version 1.0.0 --description "RP BASE OS" --name RP --product-number CXP9040501R7A
  $CLI role-create Controller --name RP --description "RP BASE OS" --scalable NO
  $CLI role-add-services Controller ldews.os.aggregation ldews.os.sc #ldews.config.sc
  $CLI system-add-functions RP ldews.base
  $CLI system-add-role RP --role Controller --assigned-to SC-1

  ### SETTING CSM VERSION to 1.3 ###
  $CLI set-csm-version 1.3

  console_print "START csm model verification"
  $CLNT
  $CLNT --check-dangling
}

function createCsp() {

  OUT_FOLD="$DIRNAME/package/csp"
  
  # Verify the mandatory folders required for CSP 
  verify_mandatory_folders $OUT_FOLD $SPDIR $CAMDIR

  # Clean the previous existing folders if any 
  cleaning_content $SPDIR $CAMDIR $OUT_FOLD $RT

  #Creation of csm-dir and with ovf-env.xml files
  if [ ! -f  "$CSM_WORKSPACE/ovf-env.xml" ] ; then
    console_print "[INFO] Executing csmconfig to create csmdir layout:"
    console_print "[COMMAND] $CSCONFG init -d $CSM_REGISTRY -c $CSM_WORKSPACE"
    $CSCONFG init -d $CSM_REGISTRY -c $CSM_WORKSPACE || \
      console_abort "[ERROR] $CSCONFIG could not create the configuration: check the error messages"
  else
    console_print "[INFO] Executing csm configuration udpate"
    $CSCONFG update -d $CSM_REGISTRY ||\
      console_abort "[ERROR] $CSCONFIG could not create the configuration: check the error messages"
  fi

  # create_swpack
  console_print "[INFO] Prepare RT Repository for downloading runtime packages"
  console_print "[COMMAND] $C2AM init $CAMDIR $CSM_WORKSPACE"
  $C2AM init $CAMDIR $CSM_WORKSPACE || console_abort "[ERROR] $C2AM failed: check the error messages"

  #Downloading the packages from the artifact with version.xml generated and storing in the repo folder
  console_print "[INFO] Download runtime packages and populate RT-repo"
  console_print "[COMMAND] $AF --get-packages --input $CAMDIR/version.xml --outputDir $RT --flat"
  $AF --get-packages --input $CAMDIR/version.xml --outputDir $RT --flat || \
    console_abort "[ERROR] $AF could not download runtime packages: check error messages"

  #Execting the command to create swdp and store in the repo path
  console_print "[INFO] Create swdp"
  console_print "[COMMAND] $C2CSP create-swdp $SPDIR --repo-path $RT --dep-repo-path $CSM_REGISTRY --csm-dir $CSM_WORKSPACE"
  $C2CSP create-swdp $SPDIR --repo-path $RT --dep-repo-path $CSM_REGISTRY --csm-dir $CSM_WORKSPACE ||\
    console_abort "[ERROR] $C2CSP cannot create swdp: check logs in tools folder"

  console_print "[INFO] Create CSP2.0 package"
  console_print "[COMMAND] $CUP --swdp $SPDIR/swdp --package-name sw --package-format CSP2.0 $OUT_FOLD"
  $CUP --swdp $SPDIR/swdp --package-name sw --package-format CSP2.0 $OUT_FOLD || \
    console_abort "[ERROR] $CUP cannot create sw: check logs in tools folder"

  console_print "[INFO] CSP2.0 sw.tar.gz is created"

  echo "[INFO] Clean temporary data"
  cleaning_folders $SPDIR $CAMDIR

  # cleanup the logs
  remove_logs
}

function createQcow2() {

  OUT_FOLD="$DIRNAME/csm-ws/config/initial/ldews.os"
  IN_FOLD="$view/$SWM_HOME/tools/2.0/etc/vRP/"
  local ISO_FILE="$DIRNAME/csm2ict_out/install.iso"
  local HOOKS_FOLDER="$view/$SWM_HOME/tools/2.0/mi_cnz/esm/virtual/vRP/post-installation"
  local ICT_CONFIG_TEMPLATE="$DIRNAME/csm2ict_out/ICT_config_template.yml"

  #### injecting hooks to handle docker and other 
  DP_REPO_PATH="$DIRNAME/DP-repo"
  LDE_WS=$(find $DP_REPO_PATH/ -name ldews-* -type d 2>/dev/null)
  if [ -n "$LDE_WS" ]; then 
    POST_INSTALLATION_HOOK_DIR="$LDE_WS/ict/post-installation/"
  fi

  console_print "#####################################################"
  console_print "Injecting post installation hook scripts into ict plugin"
  $CP -f $HOOKS_FOLDER/* $POST_INSTALLATION_HOOK_DIR || console_abort "Failed to inject post installation hook scripts"
  console_print " post installation hook scripts injected successfully "  
  console_print "#####################################################" 
 
  console_print "COPYING EXTERNAL_TEMPLATES FROM $IN_FOLD to $OUT_FOLD..."
  $CP -f $IN_FOLD/*.conf $OUT_FOLD || console_abort "Failed to copy external templates" 
  console_print "external templates copied successfully"

  #Updating CSM directory layout by using the csmconfig update
  console_print "[INFO] Updating CSM directory layout"
  $CSMCONFIG update || console_abort "CSMCONFIG failed to update the CSM directory layout"

  #Create the ISO image
  console_print "[INFO] Create ISO image"
  console_print "[COMMAND] $CSM2ICT create -c $DIRNAME/csm-ws -r $DIRNAME/RT-repo  $DIRNAME/DP-repo -o $DIRNAME/csm2ict_out"
  $CSM2ICT create -c $DIRNAME/csm-ws -r $DIRNAME/RT-repo  $DIRNAME/DP-repo -o $DIRNAME/csm2ict_out || console_abort "$CSM2ICT create command failed"
  console_print "execution of $CSM2ICT create command successfully:"

  # update of ict_config_template_yml
  console_print "[INFO] Updating the ICT_config_template.yml"
  /usr/bin/sed -i s/100G/10G/ $ICT_CONFIG_TEMPLATE
  [ $? -ne 0 ] && console_abort "Updation of ICT_config_template.yml file was failed"
  console_print "Updation of ICT_config_template.yml file was successful"

  ## create qcow image using ict command 
  console_print "###### Creating create_qcow_image file ######"
  ict create -o $DIRNAME/ict_out -i $ISO_FILE -c $ICT_CONFIG_TEMPLATE --clean --verbose -T 60 || console_abort "Qcow2 image creation failed"

  console_print  "[INFO]Qcow2 image created successfully"
}

#################################################
#               |\/|  /\  | |\ |                #
#               |  | /--\ | | \|                #
#################################################

source ./common.sh $DIRNAME

### Create DP repo 
createDpRepo

### create csm model 
createCsm

### create csp package with LDE 
createCsp

### create QCOW2 image 
createQcow2

exit 0

## END 
