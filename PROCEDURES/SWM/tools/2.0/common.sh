#!/bin/bash
###########################################################################
# Copyright (C) 2018 Ericsson AB. All rights reserved.
# ------------------------------------------------------------------------
###########################################################################

export VOL_ROOT="$1"
export CSM_WORKSPACE="$VOL_ROOT/csm-ws"
export AM_WORKSPACE="$VOL_ROOT/am-ws"
export CSM_REGISTRY="$VOL_ROOT/DP-repo"
export CSP_DIR="$VOL_ROOT/package/csp"

echo ""
echo "########################################"
echo "##### SwM2.0 ENVIRONMENT VARIABLES #####"
echo "########################################"
echo "VOL_ROOT:      <${VOL_ROOT}>"
echo "CSM_WORKSPACE: <${CSM_WORKSPACE}>"
echo "AM_WORKSPACE:  <${AM_WORKSPACE}>"
echo "CSM_REGISTRY:  <${CSM_REGISTRY}>"
echo "CSP_DIR:       <${CSP_DIR}>"
echo ""

