#!/bin/bash
##
# ------------------------------------------------------------------------
#     Copyright (C) 2012 Ericsson AB. All rights reserved.
# ------------------------------------------------------------------------
##
# Name:
#       createQcow.sh
# Description:
#       A script  is used to create a Qcow2 image.
# Note:
#       None.
##
# Usage: run the createQcow.sh
#
# Output:
#       None.
##
# Changelog:
# - Fri Dec 16 2022 - Sainadth Pagadala (zpagsai)
#       Included Basleine copies for VM
# - Tue Dec 11 2018 - Anjireddy Daka(xdakanj)
#       First version.
##

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

#set -x
DIRNAME="$view/$SWM_HOME/workspace"
CP=/usr/bin/cp
SED=/usr/bin/sed
DATE=/usr/bin/date
MKDIR=/usr/bin/mkdir
TRUE=$( true; echo $? )
FALSE=$( false; echo $? )
exit_sucs=0
exit_fail=1
LOG_DIR="$view/$SWM_HOME/tools/2.0/log"
LOG_FILE='createQcow.log'
LCT_PATH="csm/plugin/acs.lct/scripts/"



function log_directory_creation(){
  $MKDIR -p "$view/$SWM_HOME/tools/2.0/log"
}

function abort(){
  echo "$1"
  exit $2
}


#########################################################################
### Declaring variables in function declaring_variables  ###
##########################################################################

function declaring_variables {
  
  CSMCLI="csmcli"
  CSM2ICT="csm2ict"
  CSMCONFIG="csmconfig"
  ICT="ict"
  OUT_FOLD="$DIRNAME/csm-ws/config/initial/ldews.os"
  IN_FOLD="$view/$SWM_HOME/tools/2.0/etc"
}

function flog(){
  echo "[$($DATE --utc +'%Y-%m-%d %H:%M:%S')] $@" >>$LOG_DIR/$LOG_FILE
}


######################################################################################################
### The function copy_external_templates has the goal to overwrite configuration files 
### present under the path $SWM_HOME/workspace/csm-ws/config/initial/ldews.os/ 
######################################################################################################

function copy_external_templates {
 
  flog "COPYING EXTERNAL_TEMPLATES FROM $IN_FOLD to $OUT_FOLD..."  
  echo "[COMMAND] $CP -f $IN_FOLD/*.conf $OUT_FOLD"
  $CP -f $IN_FOLD/*.conf $OUT_FOLD
  if [ $? -ne $TRUE ]; then
    flog "[COMMAND] $CP was failed"
    return $exit_fail
  else
    echo "[INFO] [COMMAND] $CP was successful"
    flog "[COMMAND] $CP was successful"
  fi
  return $exit_sucs
}

########################################################################################################
### The function create_iso_image has the goal to create an  config/initial/ldews.os/factoryparam.conf 
### entry in csm.yml file and  creates an ICT_config_template.yml and install.iso files
### $SWM_HOME/workspace/csm2ict_out/ folder  
########################################################################################################

function create_iso_image {
  
  flog "creaion of iso image file..."  
  grep "factoryparam.conf" $DIRNAME/csm-ws/csm.yml
  if [ $? -ne $TRUE ]; then
    flog "adding an config/initial/ldews.os/factoryparam.conf enrty in yml.conf file"
    echo "[INFO] adding an config/initial/ldews.os/factoryparam.conf enrty in yml.conf file"
    $CSMCLI component-add-config-file ldews.os.sc --config-file-name config/initial/ldews.os/factoryparam.conf
    #check result
    if [ $? -ne $TRUE ]; then
      flog "$CSMCLI component-add-config-file command failed"
      return $exit_fail
    fi
  else
  echo "[INFO] config/initial/ldews.os/factoryparam.conf enrty already added in yml.conf file"
  flog "config/initial/ldews.os/factoryparam.conf enrty already added in yml.conf file"
  fi

  #Updating CSM directory layout by using the csmconfig update
  echo "[INFO] Updating CSM directory layout"
  echo "[COMMAND] $CSMCONFIG update"
  flog "[COMMAND] $CSMCONFIG update..."
  $CSMCONFIG update
  if [ $? -ne $TRUE ]; then
    flog "CSMCONFIG failed to update the CSM directory layout"
    return $exit_fail
  fi
  #Copying Baseline files
  pushd $DIRNAME/DP-repo
  LCT_DIR=$(find . -name "acs_lct*" | awk -F "/" '{print $2}')
  flog "COPYING BASELINE FILES FROM $DIRNAME/integrity-files TO $LCT_DIR/$LCT_PATH" 
  echo "[COMMAND] $CP $DIRNAME/integrity-files/AP* $LCT_DIR/$LCT_PATH"
  $CP $DIRNAME/integrity-files/AP* $LCT_DIR/$LCT_PATH
  if [ $? -ne $TRUE ];then
    flog "Copying Baseline files failed"
    return $exit_fail
  else
    echo "[INFO] [COMMAND] $CP was successful"
    flog "[COMMAND] $CP was successful"
  fi 
  popd
  #Create the ISO image
  echo "[INFO] Create ISO image"
  echo "[COMMAND] $CSM2ICT create -c $DIRNAME/csm-ws -r $DIRNAME/RT-repo  $DIRNAME/DP-repo -o $DIRNAME/csm2ict_out"
  flog "[COMMAND] $CSM2ICT create -c $DIRNAME/csm-ws -r $DIRNAME/RT-repo  $DIRNAME/DP-repo -o $DIRNAME/csm2ict_out..."
  $CSM2ICT create -c $DIRNAME/csm-ws -r $DIRNAME/RT-repo  $DIRNAME/DP-repo -o $DIRNAME/csm2ict_out
  if [ $? -ne $TRUE ]; then
    flog "$CSM2ICT create command failed:"
    return $exit_fail
    else
      echo "[INFO] execution of $CSM2ICT create command successfully"
      flog "execution of $CSM2ICT create command successfully:"
  fi
  return $exit_sucs 
}

##########################################################################
### The function update_ict_config_template_yml has the goal to update 
### size parameter as 86G instead of 100G in ICT_config_template.yml file. 
##########################################################################

function update_ict_config_template_yml {
 
  flog "updation of ict_config_template_yml..."
  echo "[INFO] Updating the ICT_config_template.yml"
  echo "[COMMAND] $SED"
  $SED -i s/100G/86G/ $DIRNAME/csm2ict_out/ICT_config_template.yml
  if [ $? -ne $TRUE ]; then
    flog "[COMMAND] $SED was failed"
    return $exit_fail
    else
      flog " Execution of [COMMAND] $SED was successful"
      echo "Execution of [COMMAND] $SED was successful"
  fi
  return $exit_sucs
}

########################################################################
### The function create_qcow_image has the goal to create an qcow2 image 
### in $SWM_HOME/workspace/ict_out/ folder 
########################################################################

function create_qcow_image {

  flog "creation of Qcow2 image..."
  echo "###### Creating create_qcow_image file ######"
  $ICT create -o $DIRNAME/ict_out -i $DIRNAME/csm2ict_out/install.iso -c $DIRNAME/csm2ict_out/ICT_config_template.yml --clean --verbose -T 60
  if [ $? -ne $TRUE ]; then
    flog "ICT create command failed"  
    return $exit_fail 
    else
      flog "ICT create command execution was successfully"
      echo "[INFO]ICT create command execution was successfully"
  fi
  return $exit_sucs
}

#################################################
#               |\/|  /\  | |\ |                #
#               |  | /--\ | | \|                #
#################################################

source ./common.sh $DIRNAME
log_directory_creation
declaring_variables
copy_external_templates
if [ $? -ne $TRUE ]; then
flog "copying of conf files from $IN_FOLD to $OUT_FOLD was failed"
abort "copying of conf files from $IN_FOLD to $OUT_FOLD was failed" $exit_fail
else
flog "copying of conf files from $IN_FOLD to $OUT_FOLD was successful"
echo "copying of conf files from $IN_FOLD to $OUT_FOLD was successful"
fi
create_iso_image
if [ $? -ne $TRUE ]; then
flog "creaion of iso image file was failed"
abort "creaion of iso image file was failed" $exit_fail
else
flog "creaion of iso image file was successful"
echo "creaion of iso image file was successful"
fi
update_ict_config_template_yml
if [ $? -ne $TRUE ]; then
flog "Updation of ICT_config_template.yml file was failed"
abort "Updation of ICT_config_template.yml file was failed" $exit_fail
else
flog "Updation of ICT_config_template.yml file was successful"
echo "Updation of ICT_config_template.yml file was successful"
fi
create_qcow_image
if [ $? -ne $TRUE ]; then
flog "Qcow2 image creation failed" 
abort "Qcow2 image creation failed" $exit_fail
else
flog "Qcow2 image created successfully"
echo "[INFO]Qcow2 image created successfully"
fi
exit $exit_sucs
