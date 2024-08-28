#!/bin/bash

###########################################################################
# ------------------------------------------------------------------------
#     Copyright (C) 2018 Ericsson AB. All rights reserved.
# ------------------------------------------------------------------------
###########################################################################

SWM_HOME=$( pwd)
SWM_HOME=$( echo $SWM_HOME | sed 's@/SWM.*@/SWM@g')

DIRNAME="$SWM_HOME/workspace"
APG_VERSIONS_AP='apg43l_versions_ap.xml'
AF_CONFIG='ArtifactManager.cfg'
AF_CONFIG_AP='ArtifactManager_ap.cfg'
CP='/usr/bin/cp'
AF='artifact_manager'

function abort() {
  echo -e ${@:-"An error occurred. Exiting!"}
  exit 1
}

trap abort INT 
trap abort ERR

#-------------------------------------------------------------------------
function declaring_variables {
#  if [ $USER == teiaxeio ]; then
#    LOCALSW="/home/teiaxeio/esm_workspace/local-sw"
#  else
LOCALSW="$DIRNAME/local-sw"
#  fi
BASE="$DIRNAME/baseline"
}

#-------------------------------------------------------------------------
function verify_mandatory_folders {
  local FOLDERS_LIST="$@"
  for i in $FOLDERS_LIST; do
    if [ ! -d $i ];then
      mkdir -p $i
      echo "#Folder $i is created"
    fi
  done
}

#-------------------------------------------------------------------------
function get_packages {
  echo "[INFO] Downloading packages:"  
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

  echo "[INFO} Downloading packages ...done"  
}

#-------------------------------------------------------------------------
function extract_packages(){
  echo ""
  echo "[INFO] Extracting SDPs"
  # extract apg paclages
  local SDPDIR="$PACKAGE_DIR/sdp"
  local TMP_DIR="$PACKAGE_DIR/sdp/tmp"
  verify_mandatory_folders $SDPDIR

  if [ ! -d $TMP_DIR ];then
    mkdir -p $TMP_DIR
  fi

  pushd $LOCALSW &>/dev/null
    for PKG in $( find . -iname "*-runtime-*.tar.gz"); do
      tar -xvzf $PKG -C $TMP_DIR &>/dev/null || abort	"Extraction failed!!"
    done
  popd &>/dev/null

  # add cba when needed
  echo "[INFO] Extracting SDPs ...done"
  echo ""
}

#-------------------------------------------------------------------------
function copy_sdps() {
  echo "[INFO] Copying SDPs"
  local SDPDIR="$PACKAGE_DIR/sdp"
  local TMP_SDPREPO="$PACKAGE_DIR/sdp/tmp"
  
  if [ ! -d $TMP_SDPREPO ]; then
    abort "[ERROR] $TMP_SDPREPO not found... exiting"
  fi

  pushd $TMP_SDPREPO &>/dev/null 
    for PKG in $( find . -type f \( -name \*.sdp -or -name \*.rpm \)); do
      $CP $PKG $SDPDIR/ -f
      if [ $? != 0 ]; then
        echo ""
        abort "[ERROR] $PKG Copy failed"
        echo ""
      fi
    done
  popd &>/dev/null
  echo "[INFO] Copying SDPs ...done"
  echo ""

  # clean up $TMP_SDPREPO
  rm -rf $TMP_SDPREPO
}

#################################################
#               |\/|  /\  | |\ |                #
#               |  | /--\ | | \|                #
#################################################
source ./common.sh $DIRNAME
declaring_variables
get_packages
extract_packages
copy_sdps
exit 0

