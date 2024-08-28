#!/bin/bash

###########################################################################
# ------------------------------------------------------------------------
#     Copyright (C) 2018 Ericsson AB. All rights reserved.
#
# ------------------------------------------------------------------------
#
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
CMD_GETOPT='/usr/bin/getopt'
RM='/usr/bin/rm'

function declaring_variables {
	CLI="csmcli"
	CLNT="csmlint"
}

function usage {
cat <<- EOF

Usage: $0 OPTION

Create the APG CBA System Model using deployment packages available in DP-repo.

    [-w, --workspace=PATH]           Full path of CSM workspace. Default value is $DIRNAME
    [-h, --help]                     Display this help and exit

Example:
    $0
    $0 -w $view/$SWM_HOME/workspace 

Exit status:
   0    Success
   1    Error
   2    Wrong usage

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


function create_apgcsm {

###################
##### CBA #########
###################

echo "CLEAN workspace" ###
$CLI clean -c 
pushd $CSM_WORKSPACE
$RM -rf config ovf-env.xml plugin  # NOTE THAT config ovf-env.xml plugin are created by csmconfig init
popd

########################################
##        IMPORT THE CBA STACK        ##
########################################
## IMPORT FUNCTIONS AND REMOVE
## NOT NEEDED SEREVICES AND COMPONENTS

echo " "
echo "IMPORT functions coremw.base, coremw.brf, coremw.brfeia, coremw.logm.framework"
$CLI import --functions coremw.base
$CLI import --functions coremw.brf
$CLI import --functions coremw.brfeia
$CLI import --functions coremw.logm.framework


echo " "
echo "IMPORT functions ldews.ecim.equipment, ldews.base, ldews.logcontroller, ldews.streamingservice"
$CLI import --functions ldews.base
$CLI import --functions ldews.logcontroller
$CLI import --functions ldews.streamingservice


echo " "
echo "REMOVE ldews.os.payload service from the specified ldews.base function"
echo "REMOVE ldews.logcontroller.payload service from specified ldews.logcontroller function"
$CLI function-remove-services ldews.base ldews.os.payload
$CLI function-remove-services ldews.logcontroller ldews.logcontroller.payload


echo " "
echo "DELETE ldews.os.payload, ldews.os.pl, ldews.config.pl, ldews.pmcounters.pl, ldews.logcontroller.payload, ldews.logcontroller.pl"
$CLI service-delete ldews.os.payload
$CLI service-delete ldews.os.pl
$CLI service-delete ldews.config.pl
$CLI service-delete ldews.pmcounters.pl
$CLI service-delete ldews.logcontroller.payload
$CLI service-delete ldews.logcontroller.pl


echo " "
echo "DELETE component ldews.config.pl, ldews.pmcounters.pl, ldews.os.pl, ldews.logcontroller.pl"
$CLI component-delete ldews.config.pl
$CLI component-delete ldews.pmcounters.pl
$CLI component-delete ldews.os.pl
$CLI component-delete ldews.logcontroller.pl

echo " "
echo "IMPORT function ldews.brf.participant"
$CLI import --functions ldews.brf.participant

echo " "
echo "IMPORT function com.oam.base"
$CLI import --functions com.oam.base

echo " "
echo "IMPORT function sec.certm"
$CLI import --functions sec.certm

echo " "
echo "IMPORT service sec.crypto"
$CLI import --services sec.crypto
### SEC CRYPTO SERVICE (Doesn't have function)
### This is automatically imported by function sec.base

echo " "
echo "IMPORT function sec.base"
$CLI import --functions sec.base

echo " "
echo "IMPORT function sec.la"
$CLI import --functions sec.la

echo " "
echo "IMPORT function sec.ldap"
$CLI import --functions sec.ldap

$CLI service-remove-promotion-dependency sec.ldap sec.certm.aggregation
$CLI service-add-promotion-dependency sec.ldap --depends-on apg.nbi.aggregation.service

#Creating dependency between lde streaming service & sec.certm.oi 
#In order to fetch the Tls certs for streaming after node reboot & restore
$CLI service-remove-promotion-dependency ldews.streamingservice.aggregation sec.certm.aggregation
$CLI service-add-promotion-dependency ldews.streamingservice.aggregation --depends-on apg.nbi.aggregation.service --tolerance-timeout 20s 

#echo " "
#echo "DELETE service sec.ldap.agent"
#$CLI service-delete sec.ldap.agent

#echo " "
#echo "REMOVE sec.ldap.agent service from sec.ldap.all service"
#$CLI service-remove-services sec.ldap.all sec.ldap.agent

#echo " "
#echo "DELETE component sec.ldap.agent"
#$CLI component-delete sec.ldap.agent

#### REMOVE FUNCTIONS THAT MUST BE REDEFINED IN APG
#### Note that sec.certm and com.oam.base are redefined as part of the APG's NBI service
echo " "
echo "REMOVE com.oam.base function"
$CLI function-delete com.oam.base

echo " "
echo "REMOVE sec.certm function"
$CLI function-delete sec.certm

echo " "
echo "DELETE com.oam.access.aggregation service"
$CLI service-delete com.oam.access.aggregation

echo " "
echo "DELETE sec.certm.aggregation service"
$CLI service-delete sec.certm.aggregation

echo " "
echo "DELETE sec.certm.agent.all service"
$CLI service-delete sec.certm.agent.all

echo "DELETE sec.certm.brfp component"
$CLI component-delete sec.certm.brfp

#######################################################################
#######################################################################
#######################################################################

#############################################
##        IMPORT THE APG COMPONENTS        ##
#############################################

echo " "
echo "IMPORT APG components"

$CLI import --components apos.*
$CLI import --components acs.*
$CLI import --components aes.*
$CLI import --components mcs.*
$CLI import --components mas.*
$CLI import --components fixs.*
$CLI import --components cps.*
$CLI import --components pes.*
$CLI import --components cphw.*
$CLI import --components ocs.*
$CLI import --components fms.*
$CLI import --components cqs.*
$CLI import --components sts.*
$CLI import --components ext.*
$CLI import --components bsc.*
#######################################################################
#######################################################################
#######################################################################

#################################################
##        CREATE CBA WRAPPED COMPONENTS        ##
#################################################
### The following NO AMF components are wrappers 
###   of the original CBA components already imported above.
###   This operation is needed to deal with dependencies between
###   APG's components, ie apos conf, and CBA components.

### COM WRAPPER ###
echo " "
echo "CREATE component apg.com.oam.lib"
$CLI component-create apg.com.oam.lib
$CLI component-update apg.com.oam.lib --description "Install only COM libs"
$CLI component-update apg.com.oam.lib --availability-manager NONE
$CLI component-update apg.com.oam.lib --software-sdp ERIC-COM-CXP9028493


COM_OAM=com.oam.tlsdmgr
COM_OAM_LIB=apg.com.oam.lib
COM_OAM_VER=`csmcli component-info $COM_OAM | grep "component-version:" |awk '{print $2}'`
COM_OAM_DP=`csmcli component-info $COM_OAM | grep "deployment-package:" |awk '{print $2}'`
COM_OAM_RP=`csmcli component-info $COM_OAM | grep "runtime-package:" |awk '{print $2}'`
COM_OAM_FN=`csmcli component-info $COM_OAM | grep "file-name:" |awk '{print $3}'`
COM_OAM_BN=`csmcli component-info $COM_OAM | grep "bundle-name:" |awk '{print $2}'`		

$CLI set-attribute components[uid:$COM_OAM_LIB]:meta-data:component-version $COM_OAM_VER
$CLI set-attribute components[uid:$COM_OAM_LIB]:meta-data:deliverable:deployment-package $COM_OAM_DP
$CLI set-attribute components[uid:$COM_OAM_LIB]:meta-data:deliverable:runtime-package $COM_OAM_RP
$CLI set-attribute components[uid:$COM_OAM_LIB]:meta-data:software:file-name $COM_OAM_FN
$CLI set-attribute components[uid:$COM_OAM_LIB]:meta-data:software:bundle-name $COM_OAM_BN

### SEC CERTM WRAPPER ###
echo " "	
echo "CREATE component apg.sec.certm.oi.lib"
$CLI component-create apg.sec.certm.oi.lib
$CLI component-update apg.sec.certm.oi.lib --description "SEC CERTM library component"
$CLI component-update apg.sec.certm.oi.lib --availability-manager NONE

SEC_CERTM_OI=sec.certm.oi
SEC_CERTM_OI_LIB=apg.sec.certm.oi.lib
SEC_CERTM_OI_VER=`csmcli component-info $SEC_CERTM_OI | grep "component-version:" |awk '{print $2}'`
SEC_CERTM_OI_DP=`csmcli component-info $SEC_CERTM_OI | grep "deployment-package:" |awk '{print $2}'`
SEC_CERTM_OI_RP=`csmcli component-info $SEC_CERTM_OI | grep "runtime-package:" |awk '{print $2}'`
SEC_CERTM_OI_FN=`csmcli component-info $SEC_CERTM_OI | grep "file-name:" |awk '{print $3}'`
SEC_CERTM_OI_BN=`csmcli component-info $SEC_CERTM_OI | grep "bundle-name:" |awk '{print $2}'`		

$CLI set-attribute components[uid:apg.sec.certm.oi.lib]:software:rpms sec-cert-manager-cxp9027891
$CLI set-attribute components[uid:$SEC_CERTM_OI_LIB]:meta-data:component-version $SEC_CERTM_OI_VER
$CLI set-attribute components[uid:$SEC_CERTM_OI_LIB]:meta-data:deliverable:deployment-package $SEC_CERTM_OI_DP
$CLI set-attribute components[uid:$SEC_CERTM_OI_LIB]:meta-data:deliverable:runtime-package $SEC_CERTM_OI_RP
$CLI set-attribute components[uid:$SEC_CERTM_OI_LIB]:meta-data:software:file-name $SEC_CERTM_OI_FN
$CLI set-attribute components[uid:$SEC_CERTM_OI_LIB]:meta-data:software:bundle-name $SEC_CERTM_OI_BN

### SEC LDAP OBJECT IMPLEMENTER WRAPPER ###
echo " "
echo "CREATE component apg.sec.ldap.oi.lib"
$CLI component-create apg.sec.ldap.oi.lib
$CLI component-update apg.sec.ldap.oi.lib --description "CBA SEC LDAP library component"
$CLI component-update apg.sec.ldap.oi.lib --availability-manager NONE

SEC_LDAP_OI=sec.ldap.oi
SEC_LDAP_OI_LIB=apg.sec.ldap.oi.lib
SEC_LDAP_OI_VER=`csmcli component-info $SEC_LDAP_OI | grep "component-version:" |awk '{print $2}'`
SEC_LDAP_OI_DP=`csmcli component-info $SEC_LDAP_OI | grep "deployment-package:" |awk '{print $2}'`
SEC_LDAP_OI_RP=`csmcli component-info $SEC_LDAP_OI | grep "runtime-package:" |awk '{print $2}'`
SEC_LDAP_OI_FN=`csmcli component-info $SEC_LDAP_OI | grep "file-name:" |awk '{print $3}'`
SEC_LDAP_OI_BN=`csmcli component-info $SEC_LDAP_OI | grep "bundle-name:" |awk '{print $2}'`		

$CLI set-attribute components[uid:apg.sec.ldap.oi.lib]:software:rpms sec-ldap-cxp9028981
$CLI set-attribute components[uid:$SEC_LDAP_OI_LIB]:meta-data:component-version $SEC_LDAP_OI_VER
$CLI set-attribute components[uid:$SEC_LDAP_OI_LIB]:meta-data:deliverable:deployment-package $SEC_LDAP_OI_DP
$CLI set-attribute components[uid:$SEC_LDAP_OI_LIB]:meta-data:deliverable:runtime-package $SEC_LDAP_OI_RP
$CLI set-attribute components[uid:$SEC_LDAP_OI_LIB]:meta-data:software:file-name $SEC_LDAP_OI_FN
$CLI set-attribute components[uid:$SEC_LDAP_OI_LIB]:meta-data:software:bundle-name $SEC_LDAP_OI_BN

### SEC LIBRARY WRAPPER ###
echo " "
echo "CREATE component apg.sec.certm.agent.lib"
$CLI component-create apg.sec.certm.agent.lib
$CLI component-update apg.sec.certm.agent.lib --description "CBA SEC Certificate Manager Agent library providing the Credu API for APG"
$CLI component-update apg.sec.certm.agent.lib --availability-manager NONE


SEC_CERTM_AGENT=sec.certm.agent
SEC_CERTM_AGENT_LIB=apg.sec.certm.agent.lib
SEC_CERTM_AGENT_VER=`csmcli component-info $SEC_CERTM_AGENT | grep "component-version:" |awk '{print $2}'`
SEC_CERTM_AGENT_DP=`csmcli component-info $SEC_CERTM_AGENT | grep "deployment-package:" |awk '{print $2}'`
SEC_CERTM_AGENT_RP=`csmcli component-info $SEC_CERTM_AGENT | grep "runtime-package:" |awk '{print $2}'`
SEC_CERTM_AGENT_FN=`csmcli component-info $SEC_CERTM_AGENT | grep "file-name:" |awk '{print $3}'`
SEC_CERTM_AGENT_BN=`csmcli component-info $SEC_CERTM_AGENT | grep "bundle-name:" |awk '{print $2}'`		

$CLI set-attribute components[uid:apg.sec.certm.agent.lib]:software:rpms sec-cert-agent-cxp9027891
$CLI set-attribute components[uid:$SEC_CERTM_AGENT_LIB]:meta-data:component-version $SEC_CERTM_AGENT_VER
$CLI set-attribute components[uid:$SEC_CERTM_AGENT_LIB]:meta-data:deliverable:deployment-package $SEC_CERTM_AGENT_DP
$CLI set-attribute components[uid:$SEC_CERTM_AGENT_LIB]:meta-data:deliverable:runtime-package $SEC_CERTM_AGENT_RP
$CLI set-attribute components[uid:$SEC_CERTM_AGENT_LIB]:meta-data:software:file-name $SEC_CERTM_AGENT_FN
$CLI set-attribute components[uid:$SEC_CERTM_AGENT_LIB]:meta-data:software:bundle-name $SEC_CERTM_AGENT_BN

#################################################
##        CREATE APG WRAPPED COMPONENTS        ##
#################################################
###   The following NO AMF components are wrappers 
###   of the original APG components already imported above.
###   This operation is needed to deal with dependencies between
###   APG's components.


### LCT WRAPPER ###
LCT=acs.lct
LCT_LIB=acs.lct.lib
LCT_SDP=`csmcli component-info $LCT | grep "sdp:" |awk '{print $2}'`
LCT_SUPERSEDES=`csmcli component-info $LCT | grep "base-component:" |awk '{print $3}'`
LCT_PREFIX=`csmcli component-info $LCT | grep "prefix:" |awk '{print $2}'`
LCT_START=`csmcli component-info $LCT | grep "start:" |awk '{print $2 " " $3}'`
LCT_STOP=`csmcli component-info $LCT | grep "stop:" |awk '{print $2 " " $3}'`
LCT_KEY=`csmcli component-info $LCT | grep "key:" |awk '{print $3}'`
LCT_PERIOD=`csmcli component-info $LCT | grep "period:" |awk '{print $2}'`
LCT_TIMEOUT=`csmcli component-info $LCT | grep " timeout:" |awk '{print $2}'`
LCT_PDT=`csmcli component-info $LCT | grep "promote-demote-timeout:" |awk '{print $2}'`
LCT_MT=`csmcli component-info $LCT | grep "migrate-timeout:" |awk '{print $2}'`
LCT_RECPOL=`csmcli component-info $LCT | grep "recovery-policy:" |awk '{print $2}'`
LCT_SST=`csmcli component-info $LCT | grep "start-stop-timeout:" |awk '{print $2}'`
LCT_PLUGIN=`csmcli component-info $LCT | grep "plugin" |awk '{print $2}'`
LCT_AFTER=`csmcli component-info $LCT | grep " - component:" |awk '{print $3}'|head -n1`
LCT_VER=`csmcli component-info $LCT | grep "component-version:" |awk '{print $2}'`
LCT_DP=`csmcli component-info $LCT | grep "deployment-package:" |awk '{print $2}'`
LCT_RP=`csmcli component-info $LCT | grep "runtime-package:" |awk '{print $2}'`
LCT_FN=`csmcli component-info $LCT | grep "file-name:" |awk '{print $3}'`
LCT_BN=`csmcli component-info $LCT | grep "bundle-name:" |awk '{print $2}'`

echo " "
echo "DELETE component $LCT" 
$CLI component-delete $LCT

echo " "
echo "CREATE component $LCT_LIB"
$CLI component-create $LCT_LIB
if [ $? -ne 0 ]; then
  echo "Component $LCT_LIB already exist. Creation skipped "
else
  $CLI component-update $LCT_LIB --description "Install only LCT libs"
  $CLI component-update $LCT_LIB --availability-manager NONE
  $CLI component-update $LCT_LIB --software-sdp $LCT_SDP
  $CLI set-attribute components[uid:$LCT_LIB]:supersedes[0]:software $LCT_SDP
  $CLI component-update $LCT_LIB --plugin $LCT_PLUGIN
  $CLI component-add-constraints-installation-after $LCT_LIB --component $LCT_AFTER --method DIFFERENT-STEP
  $CLI set-attribute components[uid:$LCT_LIB]:meta-data:component-version $LCT_VER
  $CLI set-attribute components[uid:$LCT_LIB]:meta-data:deliverable:deployment-package $LCT_DP
  $CLI set-attribute components[uid:$LCT_LIB]:meta-data:deliverable:runtime-package $LCT_RP
  $CLI set-attribute components[uid:$LCT_LIB]:meta-data:software:file-name $LCT_FN
  $CLI set-attribute components[uid:$LCT_LIB]:meta-data:software:bundle-name $LCT_BN
fi


echo " "
echo "CREATE component $LCT"
$CLI component-create $LCT
$CLI component-update $LCT --description "Install only LCT server"
$CLI component-update $LCT --availability-manager AMF
$CLI component-update $LCT --software-sdp $LCT_SDP
$CLI set-attribute components[uid:$LCT]:supersedes[0]:base-component $LCT_SUPERSEDES
$CLI component-update $LCT --control-policy-type ADVANCED
$CLI component-update $LCT --node-active ONE
$CLI component-update $LCT --node-standby ONE
$CLI component-update $LCT --node-active-standby NO
$CLI component-update $LCT --cluster-active ONE
$CLI component-update $LCT --cluster-standby ONE
$CLI component-update $LCT --prefix $LCT_PREFIX
$CLI component-update $LCT --start "$LCT_START"
$CLI component-update $LCT --stop "$LCT_STOP"
$CLI component-update $LCT --start-stop-timeout $LCT_SST
$CLI component-update $LCT --promote-demote-timeout $LCT_PDT
$CLI component-update $LCT --migrate-timeout $LCT_MT
$CLI component-update $LCT --recovery-policy $LCT_RECPOL
$CLI set-attribute components[uid:$LCT]:availability-properties:lifecycle-control:monitor-keys:key $LCT_KEY
$CLI set-attribute components[uid:$LCT]:availability-properties:lifecycle-control:monitor-keys:period $LCT_PERIOD
$CLI set-attribute components[uid:$LCT]:availability-properties:lifecycle-control:monitor-keys:timeout $LCT_TIMEOUT
$CLI component-add-constraints-installation-after $LCT --component $LCT_LIB --method DIFFERENT-STEP
$CLI set-attribute components[uid:$LCT]:meta-data:component-version $LCT_VER
$CLI set-attribute components[uid:$LCT]:meta-data:deliverable:deployment-package $LCT_DP
$CLI set-attribute components[uid:$LCT]:meta-data:deliverable:runtime-package $LCT_RP
$CLI set-attribute components[uid:$LCT]:meta-data:software:file-name $LCT_FN
$CLI set-attribute components[uid:$LCT]:meta-data:software:bundle-name $LCT_BN


#######################################################################
#######################################################################
#######################################################################

#######################################
##        CREATE APG SERVICES        ##
#######################################

### This creates 4 levels of aggregation for the above APG's components:
###  1) apg.cba.lib.aggregation.service aggregates CBA wrappers
###  2) apg.base.lib.aggregation.service aggregates APG's NOAMF components
###  3) apg.nbi.aggregation.service aggregates APG's 2N components
###  4) All NO-RED components have their own service

# import services
$CLI import $DIRNAME/../tools/2.0/model/apg-services.yml  --services
#######################################################################
#######################################################################
#######################################################################

########################################
##        CREATE APG FUNCTIONS        ##
########################################

### This associate a function per service

echo " "
echo "CREATE APG functions"

$CLI function-create apg.cba.lib.aggregation.function --name apg.cba.lib.aggregation.function --description "Provide basic CBA libraries for APG Applications" --version 1.0.0
$CLI function-add-services apg.cba.lib.aggregation.function apg.cba.lib.aggregation.service

$CLI function-create apg.base.lib.aggregation.function --name apg.base.lib.aggregation.function --description "Provide APOS basic modules" --version 1.0.0
$CLI function-add-services apg.base.lib.aggregation.function apg.base.lib.aggregation.service

$CLI function-create apg.nbi.function --name apg.nbi.function --description "NBI function for APG" --version 1.0.0
$CLI function-add-services apg.nbi.function apg.nbi.aggregation.service

$CLI function-create apg.dsd.function --name apg.dsd.function --description "DSD function for APG" --version 1.0.0
$CLI function-add-services apg.dsd.function apg.dsd.service

$CLI function-create apg.alh.function --name apg.alh.function --description "ALH function for APG" --version 1.0.0
$CLI function-add-services apg.alh.function apg.alh.service

$CLI function-create apg.logm.function --name apg.logm.function --description "LOGM function for APG" --version 1.0.0
$CLI function-add-services apg.logm.function apg.logm.service

$CLI function-create apg.apbm.function --name apg.apbm.function --description "APBM function for APG" --version 1.0.0
$CLI function-add-services apg.apbm.function apg.apbm.service

$CLI function-create apg.csync.function --name apg.csync.function --description "CSYNC function for APG" --version 1.0.0
$CLI function-add-services apg.csync.function apg.csync.service

$CLI function-create apg.hbeat.function --name apg.hbeat.function --description "HBEAT function for APG" --version 1.0.0
$CLI function-add-services apg.hbeat.function apg.hbeat.service

$CLI function-create apg.usa.function --name apg.usa.function --description "USA function for APG" --version 1.0.0
$CLI function-add-services apg.usa.function apg.usa.service

$CLI function-create apg.maus1.function --name apg.maus1.function --description "MAUS1 function for APG" --version 1.0.0
$CLI function-add-services apg.maus1.function apg.maus1.service

$CLI function-create apg.maus2.function --name apg.maus2.function --description "MAUS2 function for APG" --version 1.0.0
$CLI function-add-services apg.maus2.function apg.maus2.service

$CLI function-create apg.tocap.function --name apg.tocap.function --description "TOCAP function for APG" --version 1.0.0
$CLI function-add-services apg.tocap.function apg.tocap.service


#######################################################################
#######################################################################
#######################################################################

###################################
##        DEFINE THE ROLE        ##
###################################

$CLI role-create Controller --name AP --description "AP" --scalable NO

$CLI role-add-services Controller coremw.aggregation coremw.all coremw.brf.all coremw.brf.aggregation coremw.brf.participantproxy coremw.brf.coordinator coremw.brf.cmwa.participant coremw.brfeia.aggregation coremw.logm.aggregation
$CLI role-add-services Controller ldews.os.aggregation ldews.os.sc ldews.pmcounters.sc ldews.cfsmonitor ldews.config.sc ldews.brf.participant.aggregation ldews.streamingservice.aggregation ldews.logcontroller.aggregation
$CLI role-add-services Controller sec.crypto sec.base.all sec.acs sec.secm sec.secm.ln sec.la.aggregation sec.la.sm.all sec.ldap.all sec.ldap sec.ldap.sm
$CLI role-add-services Controller apg.cba.lib.aggregation.service apg.base.lib.aggregation.service apg.nbi.aggregation.service apg.dsd.service apg.alh.service apg.logm.service apg.apbm.service apg.csync.service  apg.hbeat.service apg.usa.service apg.maus1.service apg.maus2.service apg.tocap.service

# import system
echo " "
echo "CREATE APG43L system"
#$CLI system-create APG43L --version 3.6.0 --description "APG43L" --name APG43L --product-number CXP9040501R7A
$CLI import $DIRNAME/../tools/2.0/model/apg-version.yml  --system

echo " "
echo "ADD role Controller to the system"
$CLI system-add-role APG43L --role Controller --assigned-to SC-2-1,SC-2-2

$CLI system-add-functions APG43L coremw.base coremw.brf coremw.brfeia coremw.logm.framework ldews.base ldews.brf.participant ldews.logcontroller ldews.streamingservice sec.base sec.la sec.ldap
$CLI system-add-functions APG43L apg.cba.lib.aggregation.function apg.base.lib.aggregation.function apg.nbi.function apg.dsd.function apg.alh.function apg.logm.function apg.apbm.function apg.csync.function apg.hbeat.function apg.usa.function apg.maus1.function apg.maus2.function apg.tocap.function

### SETTING CSM VERSION to 1.3 ###
$CLI set-csm-version 1.3

#######################################################################
#######################################################################
#######################################################################


#######################
### CHECK THE MODEL ###
#######################

echo " "
echo "START csm model verification"

$CLNT
$CLNT --check-dangling


}


################################
### VERIFY MANDATORY FOLDERS ###
################################

function verify_mandatory_folders(){
  local FOLDERS_LIST="$@"
  for i in $FOLDERS_LIST;do
    if [ ! -d $i ];then
      mkdir -p $i
      echo "#Folder $i is created " 
    fi
  done
}

#################################################
#               |\/|  /\  | |\ |                #
#               |  | /--\ | | \|                #
#################################################

parse_cmdline $@
source ./common.sh $DIRNAME
declaring_variables
verify_mandatory_folders $CSM_WORKSPACE
create_apgcsm

exit 0
