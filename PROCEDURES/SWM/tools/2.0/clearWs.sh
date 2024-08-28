#!/bin/bash

view=$1

SWM_HOME=$( pwd)
SWM_HOME=$( SWM_HOME=${SWM_HOME:1}; echo $SWM_HOME | sed 's@/SWM.*@/SWM@g')

function abort() {
	echo "[ERROR] Unhandled error... exiting"
	echo ""
	exit 1
}	

trap abort ERR  # to capture pushd/popd failures

echo""
#if [ $USER == teiaxeio ]; then
#	echo "clean /home/teiaxeio/esm_workspace/local-sw directory"
#	echo "pushd /home/teiaxeio/esm_workspace/local-sw directory"
#	pushd /home/teiaxeio/esm_workspace/local-sw
#else
	echo "clean $view/$SWM_HOME/workspace/local-sw directory"
	echo "pushd $view/$SWM_HOME/workspace/local-sw"
	pushd $view/$SWM_HOME/workspace/local-sw
#fi

echo "rm -rf *"
rm -rf *   
popd
echo "***************************************************************************"
echo "[INFO] folder $view/$SWM_HOME/workspace/local-sw cleaned"
echo "***************************************************************************"

echo ""
echo "delete APG components from $view/$SWM_HOME/workspace/am-cache directory"
echo "pushd $view/$SWM_HOME/workspace/am-cache"
pushd $view/$SWM_HOME/workspace/am-cache
echo "rm -rf acs* apos* aes* mcs* mas* pes* fixs* cph* cps* sts* sec* coremw* cqs* fms* ldew* com* ocs* ext*"
rm -rf acs* apos* aes* mcs* mas* pes* fixs* cph* cps* sts* sec* coremw* cqs* fms* ldew* com* ocs* ext* bsc* dxtoolbox*
popd
echo "**************************************************************************************"
echo "[INFO] APG components deleted from $view/$SWM_HOME/workspace/am-cache"
echo "**************************************************************************************"

echo ""
echo "clean $view/$SWM_HOME/workspace/DP-repo directory"
echo "pushd $view/$SWM_HOME/workspace/DP-repo"
pushd $view/$SWM_HOME/workspace/DP-repo
echo "rm -rf *"
rm -rf *
popd
echo "**************************************************************************"
echo "[INFO] folder $view/$SWM_HOME/workspace/DP-repo cleaned"
echo "**************************************************************************"
echo ""

echo "clean $view/$SWM_HOME/workspace/RT-repo directory"
echo "pushd $view/$SWM_HOME/workspace/RT-repo"
pushd $view/$SWM_HOME/workspace/RT-repo
echo "rm -rf *"
rm -rf *
popd
echo "***************************************************************************"
echo "[INFO] folder $view/$SWM_HOME/workspace/RT-repo cleaned"
echo "***************************************************************************"
echo ""

echo "clean $view/$SWM_HOME/workspace/csm-ws directory"
echo "pushd $view/$SWM_HOME/workspace/csm-ws"
pushd $view/$SWM_HOME/workspace/csm-ws
echo "rm -rf *"
rm -rf *
popd
echo "*************************************************************************"
echo "[INFO] folder $view/$SWM_HOME/workspace/csm-ws cleaned"
echo "*************************************************************************"
echo ""

echo "clean $view/$SWM_HOME/workspace/package/csp directory"
echo "pushd $view/$SWM_HOME/workspace/package/csp"
pushd $view/$SWM_HOME/workspace/package/csp
echo "rm -rf *"
rm -rf *
popd
echo "******************************************************************************"
echo "[INFO] folder $view/$SWM_HOME/workspace/package/csp cleaned"
echo "******************************************************************************"
echo ""


echo""
echo "clean $view/$SWM_HOME/workspace/package/ipa directory"
echo "pushd $view/$SWM_HOME/workspace/package/ipa"
pushd $view/$SWM_HOME/workspace/package/ipa
echo "rm -rf *"
rm -rf *
popd
echo "******************************************************************************"
echo "[INFO] folder $view/$SWM_HOME/workspace/package/ipa cleaned"
echo "******************************************************************************"
echo ""

if [ -d $view/$SWM_HOME/workspace/package/up ]; then
echo""
echo "clean $view/$SWM_HOME/workspace/package/up directory"
echo "pushd $view/$SWM_HOME/workspace/package/up"
pushd $view/$SWM_HOME/workspace/package/up
echo "rm -rf *"
rm -rf *
popd
echo "******************************************************************************"
echo "[INFO] folder $view/$SWM_HOME/workspace/package/up cleaned"
echo "******************************************************************************"
echo ""
fi

if [ -d $view/$SWM_HOME/workspace/package/sdp ]; then
echo""
echo "clean $view/$SWM_HOME/workspace/package/sdp directory"
echo "pushd $view/$SWM_HOME/workspace/package/sdp"
pushd $view/$SWM_HOME/workspace/package/sdp
echo "rm -rf *"
rm -rf *
popd
echo "******************************************************************************"
echo "[INFO] folder $view/$SWM_HOME/workspace/package/sdp cleaned"
echo "******************************************************************************"
echo ""
fi

if [ -d $view/$SWM_HOME/workspace/am-ws/logs ];then
echo "clean $view/$SWM_HOME/workspace/am-ws/logs"
echo "pushd $view/$SWM_HOME/workspace/am-ws/"
pushd $view/$SWM_HOME/workspace/am-ws/
rm -rf logs 
popd
fi
echo "*****************************************************************************"
echo "[INFO] folder $view/$SWM_HOME/workspace/am-ws/logs cleaned"
echo "*****************************************************************************"

echo "cleam $view/$SWM_HOME/workspace/integrity-files/"
echo "pushd $view/$SWM_HOME/workspace/integrity-files/"
pushd $view/$SWM_HOME/workspace/integrity-files/
rm -rf *
popd
echo "*****************************************************************************"
echo "[INFO] folder $view/$SWM_HOME/workspace/integrity-files/ cleaned"
echo "*****************************************************************************"

if [ -d $view/$SWM_HOME/tools/2.0/log ];then
echo "clean $view/$SWM_HOME/tools/2.0/log"
echo "pushd $view/$SWM_HOME/tools/2.0/log"
pushd $view/$SWM_HOME/tools/2.0/
rm -rf log 
popd
fi

if [ -d $view/$SWM_HOME/workspace/csm2ict_out ];then
echo "clean $view/$SWM_HOME/workspace/csm2ict_out"
echo "pushd $view/$SWM_HOME/workspace/csm2ict_out"
pushd $view/$SWM_HOME/workspace/
rm -rf csm2ict_out 
popd
fi

if [ -d $view/$SWM_HOME/workspace/ict_out ];then
echo "clean $view/$SWM_HOME/workspace/ict_out"
echo "pushd $view/$SWM_HOME/workspace/ict_out"
pushd $view/$SWM_HOME/workspace/
rm -rf ict_out
popd
fi

echo ""
echo "pushd $view/$SWM_HOME/workspace"
pushd $view/$SWM_HOME/workspace
echo "tree -L 2"
tree -L 2
popd

echo ""
echo "Clearing the workspace for baseline files"
pushd "$view/$SWM_HOME/tools/2.0/baseline_generator/output_baseline/"
rm -rf *
popd
