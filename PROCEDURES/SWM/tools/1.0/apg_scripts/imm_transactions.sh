#!/bin/bash
##
# ------------------------------------------------------------------------
#     Copyright (C) 2015 Ericsson AB. All rights reserved.
# ------------------------------------------------------------------------
##
# Name:
#       imm_transactions.sh
# Description:
#       A script to delete rules from IMM.
# Note:
#       None.
##
# Changelog:
# - Mon Sep 14 2015 - Pratap Reddy Uppada(XPRAUPP)
# First version.

# script-wide variables
TRUE=$( true; echo $? )
FALSE=$( false; echo $? )
MAX_RETRY_NUMBER=3

LOG_TAG="imm_transactions"

function log(){
  /bin/logger -t $LOG_TAG "$*"
}

RULES_LIST='ruleId=AxeApCmd_61,roleId=SystemSecurityAdministrator,localAuthorizationMethodId=1
            ruleId=AxeApCmd_62,roleId=SystemReadOnly,localAuthorizationMethodId=1
            ruleId=AxeApCmd_63,roleId=EricssonSupport,localAuthorizationMethodId=1
            ruleId=AxeApCmd_64,roleId=CpRole0,localAuthorizationMethodId=1
            ruleId=AxeApCmd_65,roleId=CpRole1,localAuthorizationMethodId=1
            ruleId=AxeApCmd_66,roleId=CpRole2,localAuthorizationMethodId=1
            ruleId=AxeApCmd_67,roleId=CpRole3,localAuthorizationMethodId=1
            ruleId=AxeApCmd_68,roleId=CpRole4,localAuthorizationMethodId=1
            ruleId=AxeApCmd_69,roleId=CpRole5,localAuthorizationMethodId=1
            ruleId=AxeApCmd_70,roleId=CpRole6,localAuthorizationMethodId=1
            ruleId=AxeApCmd_71,roleId=CpRole7,localAuthorizationMethodId=1
            ruleId=AxeApCmd_72,roleId=CpRole8,localAuthorizationMethodId=1
            ruleId=AxeApCmd_73,roleId=CpRole9,localAuthorizationMethodId=1
            ruleId=AxeApCmd_74,roleId=CpRole10,localAuthorizationMethodId=1'

function abort() {
  log "ABORTING: $1"
  exit $FALSE
}

for ruleId in $RULES_LIST; do
  if /usr/bin/immlist $ruleId &>/dev/null ; then
    index=0
    while [ $index -le $MAX_RETRY_NUMBER ]; do
      f_flag=1;
      RULE_TOBE_DELETED=$(/usr/bin/timeout --signal=INT --kill-after=11 10 /usr/bin/immcfg -d $ruleId 2>/dev/null)
      if [ $? -eq 0 ]; then
        f_flag=0;
        break
      fi
      index=$(( $index + 1 ))
      sleep 2
   done
   if [ $f_flag -eq 1 ]; then
    abort "failure while try to delete ruleId from IMM"
   fi
  else
    log "$ruleId does not exist, no action required"
 fi
done
# End of the script

