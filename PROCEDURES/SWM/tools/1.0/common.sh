#!/bin/bash
###########################################################################
# Copyright (C) 2018 Ericsson AB. All rights reserved.
# ------------------------------------------------------------------------
###########################################################################

export VOL_ROOT="$1"
export AM_WORKSPACE="$VOL_ROOT/am-ws"
export CSM_REGISTRY="$VOL_ROOT/DP-repo"

export SWM_1_HOME="$VOL_ROOT/../tools/1.0"
export BASELINE_DIR="$VOL_ROOT/baseline"
export PACKAGE_DIR="$VOL_ROOT/package"
export PACKAGE_SDPS_DIR="$VOL_ROOT/package/sdp"

echo ""
echo "########################################"
echo "##### SwM1.0 ENVIRONMENT VARIABLES #####"
echo "########################################"
echo "VOL_ROOT:      <${VOL_ROOT}>"
echo "AM_WORKSPACE:  <${AM_WORKSPACE}>"
echo "CSM_REGISTRY:  <${CSM_REGISTRY}>"
echo "PACKAGE_DIR:   <${PACKAGE_DIR}>"
echo ""

