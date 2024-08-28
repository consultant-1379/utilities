#!/bin/bash
# ------------------------------------------------------------------------
#     Copyright (C) 2018 Ericsson AB. All rights reserved.
# ------------------------------------------------------------------------

view=$1
if [ ! -z "$1" ]; then
   if [ $1 == "GEP2" ];then
      view=$2
   else 
      view=$1
   fi
fi
get_arg="$(echo $view | cut -f2 -d '/')"
echo $get_arg
if [[ $get_arg == view ]]; then
echo "*********"
shift 1
fi

SWM_HOME=$( pwd)
SWM_HOME=$( SWM_HOME=${SWM_HOME:1}; echo $SWM_HOME | sed 's@/SWM.*@/SWM@g')
GEP2=false

DIRNAME="$view/$SWM_HOME/workspace"
PACK_NAME="sw"
TEMP_DIR="$view/$SWM_HOME/tools/2.0/workspace"
AIT_PLUGIN_DIR="$view/$SWM_HOME/workspace/ait-plugin"
BASELINE_FILES_DIR="$view/$SWM_HOME/workspace/integrity-files"
LCT_PLUGIN="$view/$SWM_HOME/workspace/baseline/apg_sw_control_gep2.sh"

function declaring_variables {
	CAMDIR="$DIRNAME/CSM2AM_FOLD"
	SPDIR="$DIRNAME/CSM2CSP_FOLD"
	RT="$DIRNAME/RT-repo"
	OUT_FOLD="$DIRNAME/package/csp"
	AF="artifact_manager"
	CMD_GETOPT="/usr/bin/getopt"
	CSCONFG="csmconfig"
	C2AM="csm2am"
	C2CSP="csm2csp"
	CUP="csp-upgrade-package-create"
	RM="/usr/bin/rm"
}


function usage {
cat <<- EOF

Usage: $0 OPTION

Create CSP2.0 Package

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
	$CMD_GETOPT --quiet --quiet-output --longoptions="workspace:" --options="w:" -- "$@" 2>/dev/null
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
		GEP2)
			GEP2=true
		;;
		*)
			usage
			exit 1
		;;
		esac
		shift
	done
}


function create_csmdir {
	#Creation of csm-dir and with ovf-env.xml files
	if [ ! -f  "$CSM_WORKSPACE/ovf-env.xml" ] ; then
		echo ""
   		echo "[INFO] Executing csmconfig to create csmdir layout:"
   		echo "[COMMAND] $CSCONFG init -d $CSM_REGISTRY -c $CSM_WORKSPACE"
   		$CSCONFG init -d $CSM_REGISTRY -c $CSM_WORKSPACE
	else
		echo ""
  		echo "[INFO] Executing csm configuration udpate" 
   		echo "[COMMAND] $CSCONFG update -d $CSM_REGISTRY"
   		$CSCONFG update -d $CSM_REGISTRY 
	fi
	
	res=$?
	if [ $res != 0 ] ; then
 		echo "[ERROR] $CSCONFIG could not create the configuration: check the error messages" 
		exit 1
	fi
}


function create_apgswpack {
	echo ""
	echo "[INFO] Prepare RT Repository for downloading runtime packages"
	echo "[COMMAND] $C2AM init $CAMDIR $CSM_WORKSPACE"
	$C2AM init $CAMDIR $CSM_WORKSPACE

	#check result
	res=$?
	if [ $res != 0 ] ; then
		echo "[ERROR] $C2AM failed: check the error messages"
		exit 1
	fi

	#Downloading the packages from the artifact with version.xml generated and storing in the repo folder
	echo ""
	echo "[INFO] Download runtime packages and populate RT-repo"
	echo "[COMMAND] $AF --get-packages --input $CAMDIR/version.xml --outputDir $RT --flat"
	$AF --get-packages --input $CAMDIR/version.xml --outputDir $RT --flat

	#Check result
	res=$?
	if [ $res != 0 ] ; then 
		echo "[ERROR] $AF could not download runtime packages: check error messages" 
		exit 1
	fi


	#Execting the command to create swdp and store in the repo path 
	echo ""
	echo "[INFO] Create swdp"
	echo "[COMMAND] $C2CSP create-swdp $SPDIR --repo-path $RT --dep-repo-path $CSM_REGISTRY --csm-dir $CSM_WORKSPACE"
	$C2CSP create-swdp $SPDIR --repo-path $RT --dep-repo-path $CSM_REGISTRY --csm-dir $CSM_WORKSPACE

	res=$?
	if [ $res != 0 ]; then
		echo "[ERROR] $C2CSP cannot create swdp: check logs in tools folder" 
		exit 1
	fi
  
  #Patch to copy postinstall.sh script
  echo "Patch baseline"
  pushd $SPDIR 
  mkdir temp
  tar -xvzf CSM_PLUGIN.tar.gz -C temp/
  #copying baseine files
  echo ""
  echo "[INFO] Copying Baseline files" 
  echo "[COMMAND] cp -r $BASELINE_FILES_DIR/AP* temp/csm/plugin/acs.lct/scripts/"
  cp -r  $BASELINE_FILES_DIR/AP* temp/csm/plugin/acs.lct/scripts/
  res=$?
  if [ $res != 0 ];then
	echo "[ERROR] copying baseline files failed"
        exit 1
  fi
  if $GEP2 ;then
        cp $LCT_PLUGIN temp/csm/plugin/acs.lct/scripts/apg_sw_control.sh
  fi
  cp $AIT_PLUGIN_DIR/postinstall.sh temp/ 
  pushd temp/
  tar -cvzf CSM_PLUGIN.tar.gz *
  mv CSM_PLUGIN.tar.gz ../
  popd
  rm -rf temp/
  popd

	echo ""
	echo "[INFO] Create CSP2.0 package"
	echo "[COMMAND] $CUP --swdp $SPDIR/swdp --package-name $PACK_NAME --package-format CSP2.0 $OUT_FOLD"
	$CUP --swdp $SPDIR/swdp --package-name $PACK_NAME --package-format CSP2.0 $OUT_FOLD

	res=$?
	if [ $res != 0 ] ; then
		echo "[ERROR] $CUP cannot create ${PACK_NAME}: check logs in tools folder"
		exit 1
	else
		echo ""
		echo "############################################"
		echo "[INFO] CSP2.0 ${PACK_NAME}.tar.gz is created"
		echo "############################################"
		echo ""
		cleaning_folders $TEMP_DIR  
	fi
}


function verify_mandatory_folders {
	local FOLDERS_LIST="$@"
	for i in $FOLDERS_LIST;do
		if [ ! -d $i ];then
			mkdir -p $i
			if [ $? -ne 0 ];then
        			echo "[ERROR] Cannot create <$i>. RC: <$?>"
                		exit 1
			fi
			echo "[INFO] Created $i"
		fi
	done
}

function cleaning_folders {
	local FOLDERS_LIST="$@"
	for i in $FOLDERS_LIST;do
		if [ -d $i ];then
			$RM -rf $i
			if [ $? -ne 0 ];then
				echo "[ERROR] Cannot remove <$i>. RC: <$?>"
				exit 1
			fi
			echo "[INFO] Deleted $i"
		fi
	done
}

function cleaning_content {
	local FOLDERS_LIST="$@"
	for i in $FOLDERS_LIST;do
		if [ -d $i ];then
			$RM -rf $i/*
			if [ $? -ne 0 ];then
				echo "[ERROR] Cannot clean <$i>. RC: <$?>"
				exit 1
			fi
			echo "[INFO] Delete content of $i" 
		fi
	done
}


function remove_logs {
        local CSPLOGS="$DIRNAME/../tools/2.0/csp.log*"
	echo "[COMMAND] $RM -rf $CSPLOGS"
        $RM -rf $CSPLOGS
	if [ $? -ne 0 ];then
		echo "[ERROR] Cannot remove <$CSPLOGS>. RC: <$?>"
	fi
}


#################################################
#               |\/|  /\  | |\ |                #
#               |  | /--\ | | \|                #
#################################################
parse_cmdline $@
source ./common.sh $DIRNAME
declaring_variables
verify_mandatory_folders $OUT_FOLD $SPDIR $CAMDIR
cleaning_content $SPDIR $CAMDIR $OUT_FOLD $RT
create_csmdir
create_apgswpack
echo "[INFO] Clean temporary data"
cleaning_folders $SPDIR $CAMDIR 
remove_logs
exit 0
