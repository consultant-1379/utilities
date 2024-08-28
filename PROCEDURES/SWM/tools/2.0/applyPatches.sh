#!/bin/bash
# ------------------------------------------------------------------------
#     Copyright (C) 2018 Ericsson AB. All rights reserved.
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

DIRNAME="$view/$SWM_HOME/workspace"
PACK_NAME="sw"
LDE_STREAMING_DIR="$DIRNAME/csm-ws/config/initial/ldews.streamingservice"
TEMP_DIR="$view/$SWM_HOME/tools/2.0/workspace"
CAMDIR="$DIRNAME/CSM2AM_FOLD"
RT_REPO="$DIRNAME/RT-repo"
AM_CACHE="$view/$DIRNAME/am-cache/"
AF="artifact_manager"
CMD_GETOPT="/usr/bin/getopt"
CSCONFG="csmconfig"
C2AM="csm2am"
RM="/usr/bin/rm"
SED="/usr/bin/sed"

function usage {
cat <<- EOF

Usage: $0 OPTION

Apply a patch in LDE runtime package to remove completely ECIM Equipment.
Invoke this script before the CSP creation, just after makeAPGcsm

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

function create_csmdir {
    #Creation of csm-dir and with ovf-env.xml files
    if [ ! -f  "$CSM_WORKSPACE/ovf-env.xml" ] ; then
        echo ""
        echo "[INFO] Executing csmconfig to create csmdir layout:"
        echo "[COMMAND] $CSCONFG init -d $CSM_REGISTRY -c $CSM_WORKSPACE"
        $CSCONFG init -d $CSM_REGISTRY -c $CSM_WORKSPACE 
    fi

    res=$?
    if [ $res != 0 ] ; then
        echo "[ERROR] $CSCONFIG could not create the configuration: check the error messages" 
        exit 1
    fi
}

function download_runtimes {
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
    echo "[COMMAND] $AF --get-packages --input $CAMDIR/version.xml --outputDir $RT_REPO --flat"
    $AF --get-packages --input $CAMDIR/version.xml --outputDir $RT_REPO --flat

    #Check result
    res=$?
    if [ $res != 0 ] ; then 
        echo "[ERROR] $AF could not download runtime packages: check error messages."
        echo "Try again." 
        exit 1
    fi
}

function rsyslog_disk_size_change {

echo ""
echo "[INFO]Changing the rsyslog_action_diskspace size"
if [ -f  "$LDE_STREAMING_DIR/rsyslog-queue.conf" ] ; then
        echo ""
        echo "[INFO] Executing sed command to change the rsyslog_action_diskspace size:"
        echo "[COMMAND] sed -i 's/rsyslog_action_diskspace,1/rsyslog_action_diskspace,10/g' $LDE_STREAMING_DIR/rsyslog-queue.conf"
        $SED -i 's/rsyslog_action_diskspace,1/rsyslog_action_diskspace,10/g' $LDE_STREAMING_DIR/rsyslog-queue.conf
    	#Check result
    	res=$?
    	if [ $res != 0 ] ; then
        	echo "[ERROR] $LDE_STREAMING_DIR/rsyslog-queue.conf was not changed: check the error messages"
        	exit 1
    	fi
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


#               |\/|  /\  | |\ |                #
#               |  | /--\ | | \|                #
#################################################
parse_cmdline $@
source ./common.sh $DIRNAME
verify_mandatory_folders $CAMDIR
cleaning_content $CAMDIR $RT_REPO
create_csmdir
download_runtimes
rsyslog_disk_size_change
exit 0
