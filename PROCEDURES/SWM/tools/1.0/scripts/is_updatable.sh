#!/bin/bash
##
# ------------------------------------------------------------------------
#     Copyright (C) 2016 Ericsson AB. All rights reserved.
# ------------------------------------------------------------------------
##
# Name:
#      is_updatable.sh 
# Description:
# A script used in smart campaign to check installed version for a 
# application
##
# Changelog:
# - 2016 Aug 18 - Yeswanth Vankayala (xyesvan)
#       Support for BUP
# - 2016 Jul 5  - Yeswanth Vankayala (xyesvan)
#          Added function description
# - 2016 May 17 - Yeswanth Vankayala (xyesvan)
#
##

true=$(true; echo $?)
false=$(false; echo $?)

appname=$(basename $0)
current_dir="$(dirname "$(readlink -f $0)")"
install_list_file="$current_dir/apps_list.csv"
cache_file="$current_dir"/.${appname}.cache


# This function check for version dependent blocks to 
# upgrade or not. 
# Output:
# return true  
#  old version (CXC1372174_6-R1A01) is different from new version and 
#  if old version is not present
# return false
#  if old version is same as new version
function is_updatable(){
	bundlename=$1		# e.g. CPHW_MAUSLBIN
	newversion=$2	 	# e.g. CXC1372174_6-R1A01
	nodeid="SC-$(</etc/cluster/nodes/this/id)"

	if [[ ! -f ${cache_file} ]]; then
		immfind -c SaAmfNodeSwBundle > ${cache_file}
	fi

	oldversion=$(grep -P "ERIC-${bundlename}-[A-Z0-9_-]+,safAmfNode=${nodeid}," ${cache_file} | awk -F'=' '{print $3}' | awk -F',' '{print $1}' | awk -F "-" '{print $3"-"$4}')
	if [[ -n $oldversion  && "$oldversion" != $newversion ]]; then
		return $true
	fi

        return $false
}

# M A I N

block=$1
cxc_version=$2

if [ -f $install_list_file ];then
  # for RUP we will be having install_file present from framework and so parsing is done
  # for BUP we will not have install_file so this part is skipped 
  if grep -q "^${block}:" $install_list_file; then
    block=$(grep -P "^${block}:" $install_list_file | awk -F ';' '{print $1}' | awk -F ':' '{print $2}')
  fi
fi

is_updatable $block $cxc_version

exit $?


