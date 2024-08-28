#!/bin/sh
# Copyright (C) 2014 by Ericsson AB
# S - 125 26  STOCKHOLM
# SWEDEN, tel int + 46 10 719 0000
#
# The copyright to the computer program herein is the property of
# Ericsson AB. The program may be used and/or copied only with the
# written permission from Ericsson AB, or in accordance with the terms
# and conditions stipulated in the agreement/contract under which the
# program has been supplied.
#
# All rights reserved.
#
# **********************************
#
# One time upgrade change. Script sets all configuration attributes of type
# saAmfSGAutoRepair and saAmfSgtDefAutoRepair for SaAmfSG and SaAmfSGType
# classes to True. Previously the False option was ignored.
#

ZEROARG=1

. /opt/coremw/lib/common

log "Running $basename $0"

sgs=`$immfind -c SaAmfSG`
test $? = 0 || die "Unable to find SGs"

sgts=`$immfind -c SaAmfSGType`
test $? = 0 || die "Unable to find SGTypes"

for sgt in $sgts; do
    log "Setting saAmfSgtDefAutoRepair for $sgt to true"
    $immcfg -a saAmfSgtDefAutoRepair=1 $sgt
    test $? = 0 || die "immcfg returned non zero"
done

for sg in $sgs; do
    log "Setting saAmfSGAutoRepair for $sg to true"
    $immcfg -a saAmfSGAutoRepair=1 $sg
    test $? = 0 || die "immcfg returned non zero"
done
