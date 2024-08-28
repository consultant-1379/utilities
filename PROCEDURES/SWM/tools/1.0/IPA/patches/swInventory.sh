#!/bin/bash
##
# ------------------------------------------------------------------------
#     Copyright (C) 2011 Ericsson AB. All rights reserved.
# ------------------------------------------------------------------------
##
# Name:
#       swInventory.sh
# Description:
#       A script to configure sWinventory.
# Note:
#	None.
##
# Output:
#       None.
##
# Changelog:
# - Mon Sep 19  2017 - Praveen Rathod (xprarat - Removing SwInventory Description update in MO)
# - Thu Jul 6  2017 - Sindhuja Palla (xsinpal - SwInventory Description update in MO)
# - Tue Oct 1  2013 - Antonio Buonocunto (eanbuon)
# - Tue Nov 20 2012 - Antonio Buonocunto (eanbuon)
#	First version.
##

#CoreMW class definition
coremw_class_swm="CmwSwMSwM"
coremw_class_swinventory="CmwSwIMSwInventory"
coremw_class_swversionmain="CmwSwMSwVersionMain"
coremw_class_swversion="CmwSwIMSwVersion"
coremw_class_swmproductdata="CmwSwMProductData"
coremw_class_swinventoryproductdata="CmwSwIMProductData"
#CoreMW ID definition
coremw_id_sw=$(immfind -c $coremw_class_swm)
coremw_id_swinventory=$(immfind -c $coremw_class_swinventory)
# Ferth info from classes
inventory=$(immfind -c $coremw_class_swinventory)
swm=$(immfind -c $coremw_class_swm)

#Create new SwVersion
currentTime=$(date +"%Y-%m-%dT%T")


LOG=/bin/logger
readonly COREMW_PREFIX="ERIC-COREMW"

# verify if packageInfo.xml file is included in the campaign bundle
if [ -r $1 ]; then
	packageInfo=$1
else
	$LOG "packageInfo file NOT found!"
	exit 12
fi

#DESTROY COREMW INFORMATION
coremw_item_1=$(immfind -c $coremw_class_swversion | grep -i COREMW_RUNTIME)
coremw_item_2=$(immfind -c $coremw_class_swversionmain | grep -i COREMW_RUNTIME)
coremw_item_3=$(immfind -c $coremw_class_swmproductdata |grep -i 'COREMW_RUNTIME')
coremw_item_4=$(immfind -c $coremw_class_swinventoryproductdata | grep -i 'COREMW_RUNTIME')

immcfg -d $coremw_item_3 &> /dev/null
if [ $? -ne 0 ]; then
	$LOG "ERROR: Failed to remove CMW object $coremw_item_3"
	exit 20
fi

immcfg -d $coremw_item_4 &> /dev/null
if [ $? -ne 0 ]; then
	$LOG "ERROR: Failed to remove CMW object $coremw_item_4"
	exit 20
fi

immcfg -d $coremw_item_1 &> /dev/null
if [ $? -ne 0 ]; then
	$LOG "ERROR: Failed to remove CMW object $coremw_item_1"
	exit 20
fi

immcfg -d $coremw_item_2 &> /dev/null
if [ $? -ne 0 ]; then
	$LOG "ERROR: Failed to remove CMW object $coremw_item_2"
	exit 20
fi

#collect swdomain infos from packageInfo

domain=$(cat $packageInfo | grep "<DomainId")
if [ -z "$domain" ]; then
	$LOG "DomainId not found in packageInfo" 
	exit 14
fi

domain_product_name=$(echo $domain | awk {'print $2'} | awk -F'"' {'print $2'})
domain_product_number=$(echo $domain | awk {'print $3'} | awk -F'"' {'print $2'})
domain_product_revision=$(echo $domain | awk {'print $4'} | awk -F'"' {'print $2'})


if [ -z "$domain_product_name" ]; then
	$LOG "DomainId product Name not found in packageInfo" 
	exit 14
fi
if [ -z "$domain_product_number" ]; then
	$LOG "DomainId Product Number not found in packageInfo" 
	exit 14
fi
if [ -z "$domain_product_revision" ]; then
	$LOG "DomainId Product Revision not found in packageInfo" 
	exit 14
fi





#collect in switem_list all sdp included in packageInfo
switem_list=$(cat $packageInfo | grep "<SwBundle" | awk -F'"' {'print $2'})

for swItem in $switem_list; do
    swItemAdminDataDn="id=administrativeData,swItemId=$swItem,$coremw_id_swinventory"
	
	immlist $swItemAdminDataDn &> /dev/null
	if [ $? -ne 0 ]; then
		$LOG "ERROR: swItem $swItem included in packageInfo not found"
		exit 14
	fi
    
    # productionDate
    productionDate=$(immlist -a productionDate "$swItemAdminDataDn" | cut -d= -f2 | sed -e 's,<Empty>,,')
    if [ -z "$productionDate" ]; then
        immcfg -a productionDate="$currentTime" "$swItemAdminDataDn" 
    fi
    
    # type
    type=$(immlist -a type "$swItemAdminDataDn" | cut -d= -f2 | sed -e 's,<Empty>,,')
    if [ -z "$type" ]; then
        if [[ "$swItemAdminDataDn" == "id=administrativeData,swItemId=$COREMW_PREFIX"* ]]; then
            immcfg -a type=MW "$swItemAdminDataDn"
        else
            immcfg -a type=OTHER "$swItemAdminDataDn"
        fi
    fi
    
    # description
    description=$(immlist -a description "$swItemAdminDataDn"  | cut -d= -f2 | sed -e 's,<Empty>,,')
    if [ -z "$description" ]; then
        immcfg -a description="`immlist -a productName "$swItemAdminDataDn" | cut -d= -f2`" "$swItemAdminDataDn"
    fi
done

# SwVersion
swVersionDn="swVersionId=$domain_product_name-$domain_product_number-$domain_product_revision,$coremw_id_swinventory"
swVersionAdminDataDn="id=administrativeData,$swVersionDn"

# Create new SwVersion 
immcfg -c $coremw_class_swversion -a timeOfInstallation="$currentTime" -a timeOfActivation="$currentTime" -a administrativeData="$swVersionAdminDataDn" $swVersionDn 
if [ $? -ne 0 ]; then
	$LOG "ERROR: Failed to create SwVersion object [$swVersionDn]"
	exit 20
fi	
# Attach swItems under SwVersion created
for swItem in $switem_list; do
	itemDn="swItemId=$swItem,$coremw_id_swinventory"
    immcfg -a consistsOf+=$itemDn $swVersionDn
	if [ $? -ne 0 ]; then
		$LOG "ERROR: Failed to append consistsOf data for $swItem under SwVersion object [$swVersionDn]"
		exit 20
	fi	
done
# SwVersion administrativeData
query_admin_data="-a productName=$domain_product_name "
query_admin_data+="-a productNumber=$domain_product_number "
query_admin_data+="-a productRevision=$domain_product_revision " 
query_admin_data+="-a type=APG "
query_admin_data+="-a description=$domain_product_name "
query_admin_data+="-a productionDate=$currentTime "

immcfg -c $coremw_class_swinventoryproductdata $query_admin_data $swVersionAdminDataDn
if [ $? -ne 0 ]; then
	$LOG "ERROR:Failed to create Administrative Data object [$swVersionAdminDataDn]"
	exit 20
fi

# Set active SwVersion
immcfg -a active=$swVersionDn $coremw_id_swinventory
if [ $? -ne 0 ]; then
	$LOG "ERROR:Failed to append to active attribute to object [$coremw_id_swinventory]"
	exit 20
fi

# Create new SwVersionMain
swVersionMainDn="swVersionMainId=$domain_product_name-$domain_product_number-$domain_product_revision,$coremw_id_sw"
swVersionMainAdminDataDn="id=administrativeData,$swVersionMainDn"

immcfg -c $coremw_class_swversionmain -a administrativeData=$swVersionMainAdminDataDn -a swVersion=$swVersionDn $swVersionMainDn -a name="$domain_product_name-$domain_product_number"
if [ $? -ne 0 ]; then
	$LOG "ERROR:Failed to create SwVersionMain object [$swVersionMainDn]"
	exit 20
fi

# SwVersionMain administrativeData
query_admin_main="-a productName=$domain_product_name "
query_admin_main+="-a productNumber=$domain_product_number "
query_admin_main+="-a productRevision=$domain_product_revision "
query_admin_main+="-a type=APG "
query_admin_main+="-a description=$domain_product_name "
query_admin_main+="-a productionDate="$currentTime" "

immcfg -c $coremw_class_swmproductdata $query_admin_main $swVersionMainAdminDataDn
if [ $? -ne 0 ]; then
	$LOG "ERROR:Failed to create Administrative Data object [$swVersionMainAdminDataDn]"
	exit 20
fi	

# set SwVersionMain active
immcfg -a activeSwVersion=$swVersionMainDn $coremw_id_sw
if [ $? -ne 0 ]; then
	$LOG "ERROR:Failed to set active SwVersionMain to object [$coremw_id_sw]"
	exit 20
fi	

exit 0

