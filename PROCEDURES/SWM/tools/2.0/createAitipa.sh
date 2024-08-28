#!/bin/bash
# ------------------------------------------------------------------------
#     Copyright (C) 2018 Ericsson AB. All rights reserved.
# ------------------------------------------------------------------------

SWM_HOME=$( pwd)
SWM_HOME=$( echo $SWM_HOME | sed 's@/SWM.*@/SWM@g')

MI_CNZ_NATIVE_PATH="$SWM_HOME/tools/2.0/mi_cnz/esm/native"
CMD_GETOPT='/usr/bin/getopt'
DIRNAME="$SWM_HOME/workspace"
CP="/usr/bin/cp"
MKDIR="/usr/bin/mkdir"
TAR="/bin/tar"
LS="/bin/ls"
WC="/usr/bin/wc"
RM="/usr/bin/rm"
RSYNC="/usr/bin/rsync"
GREP="/usr/bin/grep"

function abort {
  echo "$*"
  exit 1
}

function declaring_variables {
	PACK_PATH="$DIRNAME/package/csp"
	IPA_PATH="$DIRNAME/package/ipa"
	CC_DEPLOY="$MI_CNZ_NATIVE_PATH/deploy.sh"
	CC_ETC="$MI_CNZ_NATIVE_PATH/etc"
	CC_HOOKS="$MI_CNZ_NATIVE_PATH/hooks"
	CC_HOOKS_AH="$CC_HOOKS/ah"
	CC_HOOKS_PH="$CC_HOOKS/ph"
	CC_HOOKS_OH="$CC_HOOKS/oh"
	CC_HOOKS_TEMP="$CC_HOOKS/templates"
	CC_PATCHES="$MI_CNZ_NATIVE_PATH/patches"
	CC_SW="$MI_CNZ_NATIVE_PATH/sw"
	CC_SW_OS="$CC_SW/os"
	CC_SW_PLUG="$CC_SW/plugins"
	CC_TEMPLATES="$MI_CNZ_NATIVE_PATH/templates"
	SW_PKG="$IPA_PATH/sw"
	DEPLOY_PATH="$IPA_PATH/deploy.sh"
	ETC_PATH="$IPA_PATH/etc"
	HOOKS_PATH="$IPA_PATH/hooks"
	TEMP_PATH="$IPA_PATH/templates"
	PATCHES_PATH="$IPA_PATH/patches"
	HOOKS_AH_PATH="$HOOKS_PATH/ah"
	HOOKS_PH_PATH="$HOOKS_PATH/ph"
	HOOKS_OH_PATH="$HOOKS_PATH/oh"
	HOOKS_TEMP_PATH="$HOOKS_PATH/templates"
	SW_PATH="$IPA_PATH/sw"
	SW_PATH_OS="$SW_PATH/os"
	SW_PATH_PLUG="$SW_PATH/plugins"
	TEMP_SW_PATH_PLUG="$SW_PATH/plugins/temp"
  AFS_LDE_HOME="/app/APG43L/SDK/LDE"
  AFS_DX_HOME="/app/APG43L/SDK/dx_btd"
  COMP_VERSION=''
  COMP_AFS_VERSION=''
}


function usage {
cat <<- EOF
Usage: $0 OPTION

Create the IPA package to be deployed on the installation server.

    [-w, --workspace=PATH]           Full path of CSM workspace. Default value is $DIRNAME
    [-h, --help]                     Display this help and exit

Example:
    $0
    $0 -w $SWM_HOME/workspace 

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

function setversions {
  local COMPONENT="$1"
  local CBA_VERSIONS_FILE="$DIRNAME/baseline/apg43l_versions_all.xml"
  local COMPONENT_VERSION=$( $GREP "<name>${COMPONENT}.*</name>" $CBA_VERSIONS_FILE -A 3 2>/dev/null| grep -P "<version>.*</version>")
  COMP_VERSION=''
  COMP_AFS_VERSION=''

  COMP_VERSION=$( echo $COMPONENT_VERSION | awk -F '<' '{print $2}' | awk -F '>' '{print $2}')
  OLDIFS=$IFS
  IFS=.
  set -- $COMP_VERSION
  if [ $# -eq 2 ]; then 
    COMP_AFS_VERSION="$1_$2"
  elif [ $# -eq 3 ]; then
    COMP_AFS_VERSION="$1_$2_$3"
  else
  IFS=$OLDIFS
    COMP_AFS_VERSION=''
  fi
  IFS=$OLDIFS
  COMP_AFS_VERSION=$( echo $COMP_AFS_VERSION | sed 's@-.*@@g')
}

function prechecks {
  setversions ldews
  if [[ -z "${COMP_VERSION}" || -z "$COMP_AFS_VERSION" ]]; then 
    abort "[ERROR] LDEWS Version not found"
  fi

  local LDEWS_LOCAL="$CC_SW_OS/ldews-${COMP_VERSION}-runtime-sle-*.tar.gz"
  local LDEWS_RT_REPO="$DIRNAME/RT-repo/ldews-${COMP_VERSION}-runtime-sle-*.tar.gz"
  if !  ls -1 $LDEWS_LOCAL &>/dev/null; then
    if ! ls -1 $LDEWS_RT_REPO &>/dev/null; then
      local LDEWS_AFS="$AFS_LDE_HOME/$COMP_AFS_VERSION/ldews-${COMP_VERSION}-runtime-sle-*.tar.gz"
      if ! ls -1 $LDEWS_AFS &>/dev/null; then
        abort "[ERROR] File <$LDEWS_LOCAL> not found."
      else
        echo "[COMMAND] $CP -f $LDEWS_AFS $CC_SW_OS"
        $CP -f $LDEWS_AFS $CC_SW_OS || 
        abort "[ERROR] Copy <$LDEWS_AFS> Failed"
      fi
    else
       echo "[COMMAND] $CP -f $LDEWS_RT_REPO $CC_SW_OS"
       $CP -f $LDEWS_RT_REPO $CC_SW_OS ||
       abort "[ERROR] Copy <$LDEWS_RT_REPO> Failed"
    fi
  fi
  # set required permission
  chmod 555 $CC_SW_OS/*

  setversions dxtoolbox
  if [[ -z "${COMP_VERSION}" || -z "$COMP_AFS_VERSION" ]]; then 
    abort "[ERROR] LDEWS Version not found"
  fi

  local DX_PLUGIN_LOCAL="$CC_SW_PLUG/dxtoolbox-ait_agents-${COMP_VERSION}-runtime-linux-*.tar.gz"
  if ! ls -1 $DX_PLUGIN_LOCAL &>/dev/null; then
    local DX_DP_REPO="$DIRNAME/DP-repo/dxtoolbox-ait_agents-${COMP_VERSION}-runtime-linux-*"
    if ! ls -1 $DX_DP_REPO &>/dev/null; then
      local DX_PLUGIN_AFS="$AFS_DX_HOME/$COMP_AFS_VERSION/dxtoolbox-ait_agents-${COMP_VERSION}-runtime-linux-*.tar.gz"
      if ! ls -1 $DX_PLUGIN_AFS &>/dev/null; then
        abort "[ERROR] File <$DX_PLUGIN_LOCAL> not found."
      else
        echo "[COMMAND] $CP -f $DX_PLUGIN_AFS $CC_SW_PLUG"
        $CP -f $DX_PLUGIN_AFS $CC_SW_PLUG ||
        abort "[ERROR] Copy <$DX_PLUGIN_AFS> Failed"
      fi
     else 
       DX_DP_REPO=$( ls -d $DX_DP_REPO)
       if [ -d ${DX_DP_REPO} ]; then 
         local DXTOOLBOX_SW=$( basename $DX_DP_REPO)
         creation_of_temporary_files $TEMP_SW_PATH_PLUG
         copy_folder_content_if_destination_empty $DX_DP_REPO $TEMP_SW_PATH_PLUG

         DXTOOLBOX_SW="${DXTOOLBOX_SW}.tar.gz"
         pushd $TEMP_SW_PATH_PLUG &>/dev/null
           $TAR -czvf ${DXTOOLBOX_SW} -P *
           if [ $? != 0 ] ; then
             destroy_folder_content_cleanup $TEMP_SW_PATH_PLUG
             abort "[ERROR] Command failed. RC: <$?>"
           fi
           echo "[COMMAND] $CP -f $DXTOOLBOX_SW $CC_SW_PLUG"
           $CP ${DXTOOLBOX_SW} $CC_SW_PLUG &>/dev/null
           if [ $? != 0 ]; then 
             destroy_folder_content_cleanup $TEMP_SW_PATH_PLUG
             abort "[ERROR] Copy <${DXTOOLBOX_SW}> failed"
           fi  
         popd &>/dev/null
         destroy_folder_content_cleanup $TEMP_SW_PATH_PLUG
       fi
     fi
  fi

  # set required permission
  chmod 555 $CC_SW_PLUG/*
}


function verify_mandatory_files {
	local FILES_LIST="$@"
	for i in $FILES_LIST; do
		if [ ! -e $i ];then
			abort "[ERROR] File <$i> not found."
		fi
	done
}

function verify_mandatory_folders {
	local FOLDERS_LIST="$@"
	for i in $FOLDERS_LIST; do
		if [ ! -d $i ];then
			abort "[ERROR] Folder <$i> not found."
		fi
	done
}


function creation_of_temporary_files {
	local FOLDERS_LIST="$@"
	for i in $FOLDERS_LIST; do
		if [ ! -d $i ];then
			echo "[COMMAND] $MKDIR -p $i"
			$MKDIR -p $i
			if [ $? -ne 0 ]; then
         abort "[ERROR] Cannot create <$i>. RC: <$?>"
			fi
			echo "INFO" "Folder $i created"
		fi
	done
}

function copying_csp_package {
	PACK_NAME="$IPA_PATH/sw.tar.gz"
	if [ -e $PACK_NAME ] ; then
		echo "[COMMAND] $RM -rf $PACK_NAME"
		$RM -rf $PACK_NAME
		if [ $? -ne 0 ];then
			abort "[ERROR] Cannot remove file: <$PACK_NAME>. RC: <$?>"
		fi
	fi
	
	echo "[COMMAND] $CP $PACK_PATH/sw.tar.gz $SW_PKG"
	$CP $PACK_PATH/sw.tar.gz $SW_PKG
	res=$?
	if [ $res != 0 ] ; then
		abort "[ERROR] Command failed. RC: <$?>"
	fi
}

function create_ipa_package {
	echo "[COMMAND] pushd $IPA_PATH"
	pushd $IPA_PATH
	echo "[COMMAND] $TAR -czvf apg43l.tar.gz -P  etc patches templates sw deploy.sh hooks"
	$TAR -czvf apg43l.tar.gz -P  etc patches templates sw deploy.sh hooks
	if [ $? != 0 ] ; then
		abort "[ERROR] Command failed. RC: <$?>"
	else
		echo ""
		echo "[INFO] IPA package created and stored here: $IPA_PATH"
		echo ""
	fi
	popd
}


function destroy_folder_content_cleanup {
	local FOLDERS_LIST="$@"
	for i in $FOLDERS_LIST; do
		if [ ! -d $i ];then
			if [ $i == "deploy.sh" ];then
				echo "[COMMAND] $RM -rf $i"
				$RM -rf $i
				if [ $? -ne 0 ];then
					abort "[ERROR] Command failed. Cannot remove <$i>. RC: <$?>"
				fi
			fi
		fi
		
		echo "[COMMAND] $RM -rf $i"
		$RM -rf $i
		if [ $? -ne 0 ];then
			echo "[ERROR] Command failed. Cannot remove <$i>. RC: <$?>"
		fi
	done
}


function copy_folder_content_if_destination_empty {
	local SOURCE_FOLDER="$1"
	local DESTINATION_FOLDER="$2"
	if [ $($LS -A $SOURCE_FOLDER | $WC -l) -eq 0 ] ; then
		echo "[INFO] $SOURCE_FOLDER is empty: no content to copy"
	elif [ $($LS -A $DESTINATION_FOLDER | $WC -l) -eq 0 ]; then
		echo "[COMMAND] $RSYNC $SOURCE_FOLDER/* --exclude='*.keep' --exclude='*.contrib' $DESTINATION_FOLDER/"
		$RSYNC $SOURCE_FOLDER/* --exclude='*.keep' --exclude='*.contrib' $DESTINATION_FOLDER/
		if [ $? -ne 0 ];then
			echo "[ERROR] Cannot copy folder. RC: <$?>"
		fi
	fi
}


function copy_file_content_if_destination_empty {
	local SOURCE_FILE="$1"
	local DESTINATION_FOLDER="$2"
	if [ -e $2 ]; then
		echo "[COMMAND] $CP -f $SOURCE_FILE $DESTINATION_FOLDER/"
		$CP -f $SOURCE_FILE $DESTINATION_FOLDER/
		if [ $? -ne 0 ];then
			echo "[ERROR] Cannot copy folder. RC: <$?>"
		fi
	fi
}

#################################################
#               |\/|  /\  | |\ |                #
#               |  | /--\ | | \|                #
#################################################

parse_cmdline $@

source ./common.sh $DIRNAME

declaring_variables

prechecks

verify_mandatory_files $CC_DEPLOY_PATH

verify_mandatory_folders $CC_ETC $CC_HOOKS $CC_HOOKS_PH $CC_HOOKS_OH $CC_HOOKS_AH $CC_HOOKS_TEMP  $CC_PATCHES  $CC_SW $CC_SW_OS $CC_SW_PLUG $CC_TEMPLATES

creation_of_temporary_files $ETC_PATH $HOOKS_PATH $HOOKS_PH_PATH $HOOKS_OH_PATH $HOOKS_AH_PATH $HOOKS_TEMP_PATH $PATCHES_PATH $SW_PATH $SW_PATH_OS $SW_PATH_PLUG $TEMP_PATH 

copy_folder_content_if_destination_empty $CC_ETC $ETC_PATH

copy_folder_content_if_destination_empty $CC_HOOKS_OH $HOOKS_OH_PATH

copy_folder_content_if_destination_empty $CC_HOOKS_AH $HOOKS_AH_PATH 

copy_folder_content_if_destination_empty $CC_HOOKS_PH $HOOKS_PH_PATH

copy_folder_content_if_destination_empty $CC_HOOKS_TEMP $HOOKS_TEMP_PATH

copy_folder_content_if_destination_empty $CC_SW_OS $SW_PATH_OS

copy_folder_content_if_destination_empty  $CC_SW_PLUG $SW_PATH_PLUG

copy_folder_content_if_destination_empty $CC_PATCHES $PATCHES_PATH

copy_folder_content_if_destination_empty $CC_TEMPLATES $TEMP_PATH

copy_file_content_if_destination_empty $CC_DEPLOY $IPA_PATH

copying_csp_package 

create_ipa_package

destroy_folder_content_cleanup $DEPLOY_PATH $ETC_PATH $HOOKS_PATH $PATCHES_PATH $SW_PATH $TEMP_PATH

exit 0
