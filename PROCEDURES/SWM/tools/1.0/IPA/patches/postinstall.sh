#!/bin/bash
#
# Copyright (C) 2014 by Ericsson AB
#
# The copyright to the computer program herein is the property of
# Ericsson AB. The program may be used and/or copied only with the
# written permission from Ericsson AB, or in accordance with the terms
# and conditions stipulated in the agreement/contract under which the
# program has been supplied.
#
# All rights reserved.

. /opt/coremw/lib/common

## check exit status for critical commands
verifyExitStatus()
{
    # $1 exitstatus
    # $2 output of command
    # $3 description of command
    if [ $1 -ne 0 ] ; then
        echo "  CRITICAL: $3 returned non-zero ($1) - $2"
        echo "Aborting script! exitCode: $1"
        exit $1
    fi
}

die() {
    # $1 description of error
    echo "Error: $1"
    exit 1
}

getConfigFile()
{
    for i in $@ ; do
        numfile=`echo $i | grep $config_file | wc -l`
        if [ $numfile -eq 1 ]; then
            echo $i
            break
        fi
    done
}

USAGE="Usage: $0\n\
\t  --start\n\
\t  --configpath CONFIGPATH\n\
\t  --configfiles CONFIGFILES\n\
\n\
"

TEMP=`getopt -o h --long start,configpath:,configfiles: -- "$@"`
verifyExitStatus $? $TEMP "Failed to process command options"

eval set -- "$TEMP"

config_file="brfc.conf"

while true ; do
    case "$1" in
        --start)
            shift
            ;;
        --configpath)
            shift 2
            ;;
        --configfiles)
            shift
            CONFIG_FILE=`getConfigFile $@`
            shift
            ;;
        -h)
            echo -e $USAGE
            shift
            ;;
        --)
            shift
            break
            ;;
        *)
            echo "Internal error!"
            exit 1
            ;;
    esac
done

# We expect the brfc.conf file in configfiles and it contains the full path
test -z $CONFIG_FILE && die "config file not specified"

test -r $CONFIG_FILE || die "$CONFIG_FILE is not readable"

BRFC_CONFIG_OBJECT_DNAME="brfcConfigId=1"

DELETE_PRIMARY_RESTORE_CANDIDATE=$(grep deletePrimaryRestoreCandidate $CONFIG_FILE | cut -d '=' -f2 | tr -d '"')

if [ $DELETE_PRIMARY_RESTORE_CANDIDATE -lt 1 -o $DELETE_PRIMARY_RESTORE_CANDIDATE -gt 2 ]
then
    DELETE_PRIMARY_RESTORE_CANDIDATE=1
fi

# wait for config object to be created (if doesn't exist)
until immlist $BRFC_CONFIG_OBJECT_DNAME
do
    sleep 2
done

CMD="immcfg -u -a deletePrimaryRestoreCandidate=$DELETE_PRIMARY_RESTORE_CANDIDATE $BRFC_CONFIG_OBJECT_DNAME"
echo "Executing command: $CMD"
eval $CMD

verifyExitStatus $? "" "'$CMD'"
