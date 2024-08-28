#!/bin/bash
##
# ------------------------------------------------------------------------
#     Copyright (C) 2014 Ericsson AB. All rights reserved.
# ------------------------------------------------------------------------
##
# Name:
#       update_apg_nodegroup.sh
# Description:
#       The script will force campaign to upgarde STANDBY node first
# Note:
#       <script_notes>
##
# Usage:
#       ./update_apg_nodegroup.sh
##
# Output:
#       <script_output_description>
##
# Changelog:
#
#Wed 012 Mar 2015 Aarish Shahab(XAARSHA)
#       - First Release
##


OSU1="safSISU=safSu=1\\,safSg=2N\\,safApp=ERIC-APG,safSi=AGENT,safApp=ERIC-APG "
amfNode1="safAmfNode=SC-1,safAmfCluster=myAmfCluster"
amfNode2="safAmfNode=SC-2,safAmfCluster=myAmfCluster"

immcfg="retry_command immcfg "

retry_command()
{
    local result
    local retry
    local count=0
    while true
    do
        output=`"$@"`
        result=$?
        retry=`echo output | grep -cE '(saImmOmAdminOwnerSet|SA_AIS_ERR_TRY_AGAIN|SA_AIS_ERR_BUSY|SA_AIS_ERR_TIMEOUT|SA_AIS_ERR_NO_RESOURCES)'`
        if [ $retry == 0 ] || [ count > 300 ]; then
            break
        fi
    count=$(($count+1))
        sleep 1
    done
    if [ -n "$output" ]; then
        echo "${output%x}"
    fi
    return $result
}

create_apg_scs() {
	currActiveSI=`immlist $OSU1 | grep saAmfSISUHAState | awk {'print $3'}`
	if [[ $currActiveSI -eq 1 ]]; then
	   # Active Node is  SC-1, add amfNode2 first
	   $immcfg -c SaAmfNodeGroup -a saAmfNGNodeList=$amfNode2 safAmfNodeGroup=APG_SCs,safAmfCluster=myAmfCluster
	   $immcfg -a saAmfNGNodeList+=$amfNode1 safAmfNodeGroup=APG_SCs,safAmfCluster=myAmfCluster
	else
	   $immcfg -c SaAmfNodeGroup -a saAmfNGNodeList=$amfNode1 safAmfNodeGroup=APG_SCs,safAmfCluster=myAmfCluster
	   $immcfg -a saAmfNGNodeList+=$amfNode2 safAmfNodeGroup=APG_SCs,safAmfCluster=myAmfCluster
	fi
}

delete_apg_scs() {
	$immcfg -d safAmfNodeGroup=APG_SCs,safAmfCluster=myAmfCluster
}

case $1 in
"create")
        create_apg_scs
        ;;
"delete")
        delete_apg_scs
    ;;
esac
exit 0


