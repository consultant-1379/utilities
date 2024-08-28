#!/bin/bash
##
# ------------------------------------------------------------------------
#     Copyright (C) 2012 Ericsson AB. All rights reserved.
# ------------------------------------------------------------------------
##
# Name:
#       createIpaCampaign.sh
# Description:
#       <script_functionality_description>
# Note:
#       <script_notes>
##
# Usage:
#       ./createIpaCampaign.sh 
#		./createIpaCampaign.sh -r 0-1
#		./createIpaCampaign.sh -r 1-2
##
# Output:
#       <script_output_description>
##
# Changelog:
# 2016-04-13 xyesvan smart campaign changes 
# 2015-02-25 eanbuon adaptation to batch mode
# 2014-02-19 xphagat Brfc 1.2 SH5 Adaptation
# 2014-01-07 eanbuon SEC 1.2 Adaptation
# 2013-02-21 LDE naming convention
# 2013-02-19 automatic creation of mini ipa resize
# 2012-03-29 resize adaptation
# 2012-03-13 bugfix, added a dependency for comsa
# 2012-02-14 eanbuon First Release
##


CONF_FOLDER="./conf"
TEMPLATES_FOLDER="./templates"
PATCH_FOLDER="./patches"
PARMTOOL_DIR="$PATCH_FOLDER/parmtool"
EXCLUDE_BUNDLES="entry_matches.sh"
INSTALL_ENTRY_FILE="$CONF_FOLDER/apps_list.csv"
ACTIVATE_ENTRY_FILE="$CONF_FOLDER/apps_lock_list.csv"
INSTALL_TYPE="install"
ACTIVATE_TYPE="app-lock"
# mini ipa with resize impacts
MINI_IPA_APOS_LIST="Agent\|DEVMON\|APOSCONFBIN\|APOSCMDBIN\|APOSEXTBIN\|COMSA\|COM\|ERIC-Sec-Control"
# end

. $CONF_FOLDER/common_functions

parse_cmdline $@

if [ "$OPT_OUTPUT" == "$TRUE" ];then
  OUT_FOLDER="$OPT_OUTPUT_ARG"
  RESIZE_FOLDER="$OPT_OUTPUT_ARG"
  SING_STEP_FOLDER="$OPT_OUTPUT_ARG"
else
OUT_FOLDER="./out"
RESIZE_FOLDER="$OUT_FOLDER/resize"
SING_STEP_FOLDER="$OUT_FOLDER/single_step"
fi

if [ "$OPT_SOURCE" == "$TRUE" ];then
  SOURCE_LIST_FOLDER="$(dirname $OPT_SOURCE_ARG)"
  SOURCE_FILE_NAME="$(basename $OPT_SOURCE_ARG)"
else
SOURCE_LIST_FOLDER=$CONF_FOLDER
SOURCE_FILE_NAME="sources.list"
fi

if [ "$OPT_ENV" == "$TRUE" ];then
  ENV_FILE_NAME="$OPT_ENV_ARG"
else
  ENV_FILE_NAME="$CONF_FOLDER/env.conf"
fi

#Loading Environment variables"
if [ -e $CONF_FOLDER/env.conf ]; then
	. $CONF_FOLDER/env.conf
else
	echo "Configuration file is missing!!!"
	exit 2
fi

echo "$CAMPAIGN_FILE_NAME_S1"
echo "$CAMPAIGN_FILE_NAME_S2"

CAMPAIGN_FILE_NAME_S1=$AP_CAMPAIGN_FILE_NAME_S1
CAMPAIGN_FILE_NAME_S2=$AP_CAMPAIGN_FILE_NAME_S2	

#check if patch is needed

if [ "$(ls -A $PATCH_FOLDER)" ]; then
    is_verbose && echo "INFO: Patch is included into Campaign bundle"
else
    is_verbose && echo "INFO: No patch to include into Campaign bundle"
fi

#clean output folder

if [ "$OPT_RESIZE" = "" ] ; then

	rm -f $SING_STEP_FOLDER/*

else

	rm -f $RESIZE_FOLDER/*
		
fi
# mini ipa with resize impacts
if [ "$OPT_MINIRES" = "$TRUE" ] ; then
	is_verbose && echo "INFO: Mini IPA mode with resize"	
#end
elif [ "$OPT_MINI" = "$TRUE" ] ; then
	is_verbose && echo "INFO: Mini IPA mode single step"
	
fi

is_verbose && echo "INFO: Clean output folder"

#Generating Temp folder

TMP_DIR=`mktemp -td swupdate_APG_XXX`

chmod 777 $TMP_DIR

mkdir -p $TMP_DIR/campaign

is_verbose && echo "INFO: tmp folder is $TMP_DIR"

function isEntryExclude() {
        local return_code=$FALSE
        local entry="$1"
        local file="$2"
        local count=0

        count=$(grep -w "$entry" "$file" | wc -l )
        [ "$count" -gt 1 ] && abort " $comp_name has multiple entries"
        if grep -w "$entry" "$file" &> /dev/null; then
             return_code=$TRUE
        fi
        return $return_code
}

function isSuPresent(){
       local dn=$(echo safSu=$1,safSg=$2,safApp=ERIC-APG)
       local output=$(isEntryExclude $dn $ACTIVATE_ENTRY_FILE ; echo $?)
       return $output
} 

function shallExcludeApp(){
       local output=$(isEntryExclude $1 $INSTALL_ENTRY_FILE; echo $?)
       return $output
}


function check_parmtool_structure(){

	[ ! -f $PARMTOOL_DIR/files.list ] && abort "ERROR: [ $PARMTOOL_DIR/files.list ] not found"

	while read line
	do
		[[ $( echo $line | grep -E '^#.*|^$|^.*.man') ]] && continue
		PARMTOOL_STRUCTURE="$PARMTOOL_STRUCTURE $( echo $line | awk -F ':' '{print $2}')"
	done < $PARMTOOL_DIR/files.list

  for ITEM in ${PARMTOOL_STRUCTURE[@]}
	do 
  	local FOUND=$FALSE
	  for ENTRY in $(find $PARMTOOL_DIR)
  	do 
  	  REL_PATH=$( echo $ENTRY | sed 's|'$PARMTOOL_DIR'/||')
  	  [[ $REL_PATH =~ .*.man.* ]] && continue
    	if [[ "$REL_PATH" == "$ITEM" ]]; then
      	FOUND=$TRUE
      	break
    	fi
  	done

  	if [[ $FOUND -eq $FALSE ]];then
    	abort "ERROR: paramtool structure mismatch [$ITEM] not found"
  	fi
	done
}


if [ -e $SOURCE_LIST_FOLDER/$SOURCE_FILE_NAME ]
        then
                is_verbose && echo "INFO: $SOURCE_FILE_NAME detected"
				cp $SOURCE_LIST_FOLDER/$SOURCE_FILE_NAME $TMP_DIR/$SOURCE_FILE_NAME
				
				sed -i "s/^#.*$//g" $TMP_DIR/$SOURCE_FILE_NAME  #remove all lines beginning with #
				sed -i '/^$/d' $TMP_DIR/$SOURCE_FILE_NAME	     #remove all empty lines
				
				SOURCE_FILE_CHECK=`cat $TMP_DIR/$SOURCE_FILE_NAME| wc -l`
				
				if [ "$SOURCE_FILE_CHECK" = "0" ]
					then
						echo "ERROR: $SOURCE_FILE_NAME file is empty"
						exit 4
				fi
								
				# mini ipa with resize impacts
				if [ "$OPT_MINIRES" = "$TRUE" ]; then
					is_verbose && echo "$SOURCE_FILE_NAME file is changed for mini ipa resize"
					cat $TMP_DIR/$SOURCE_FILE_NAME | grep $MINI_IPA_APOS_LIST > $TMP_DIR/tmpfile
					chmod 777 $TMP_DIR/$SOURCE_FILE_NAME
					cat $TMP_DIR/tmpfile > $TMP_DIR/$SOURCE_FILE_NAME
					rm $TMP_DIR/tmpfile
				fi	
				# end				
				validate_sources $TMP_DIR/$SOURCE_FILE_NAME
        else
                echo "$SOURCE_FILE_NAME file is missing!!!"
				exit 2
fi

#create the final file

touch $TMP_DIR/final.xml
touch $TMP_DIR/apos_ipa_0_1.xml		
touch $TMP_DIR/apos_ipa_1_2.xml

if [ "$OPT_CC" = "" ]
then
	is_verbose && echo "INFO: local version without repository control"
	else
	is_verbose && echo "INFO: version with repository control"
fi

## Create PackageInfo for IPA
function createPackageInfo(){
	# create file under tmpdir
	touch $TMP_DIR/packageInfo.xml
	# Create init part
	cat $TEMPLATES_FOLDER/TEMPLATE_PACKAGE_INFO/template_info_init >> $TMP_DIR/packageInfo.xml
	# Create info file
	cp $TEMPLATES_FOLDER/TEMPLATE_PACKAGE_INFO/template_info_file $TMP_DIR/template_info_file
	sed -i "s/#PACKAGE_INFO_NAME#/$IPA_PACKAGE_INFO_NAME/g" $TMP_DIR/template_info_file
	cat $TMP_DIR/template_info_file >> $TMP_DIR/packageInfo.xml
	# Create up id
	cp $TEMPLATES_FOLDER/TEMPLATE_PACKAGE_INFO/template_info_upid $TMP_DIR/template_info_upid
	sed -i "s/#IPA_PRODUCT_NAME#/$IPA_PRODUCT_NAME/g" $TMP_DIR/template_info_upid
	sed -i "s/#IPA_PRODUCT_NUMBER#/$IPA_PRODUCT_NUMBER/g" $TMP_DIR/template_info_upid
	sed -i "s/#IPA_PRODUCT_REVISION#/$IPA_PRODUCT_REVISION/g" $TMP_DIR/template_info_upid
	sed -i "s/#IPA_PRODUCT_DATE#/$IPA_PRODUCT_DATE/g" $TMP_DIR/template_info_upid
	sed -i "s/#IPA_DESCRIPTION#/$IPA_DESCRIPTION/g" $TMP_DIR/template_info_upid
	sed -i "s/#IPA_TYPE#/$IPA_TYPE/g" $TMP_DIR/template_info_upid
	cat $TMP_DIR/template_info_upid >> $TMP_DIR/packageInfo.xml
	# Create ME SubType
	cp $TEMPLATES_FOLDER/TEMPLATE_PACKAGE_INFO/template_info_mesubtype $TMP_DIR/template_info_mesubtype
	sed -i "s/#IPA_SUBTYPE_NAME#/$IPA_SUBTYPE_NAME/g" $TMP_DIR/template_info_mesubtype
	sed -i "s/#IPA_ACTIVATION_TIMEOUT#/$IPA_ACTIVATION_TIMEOUT/g" $TMP_DIR/template_info_mesubtype
	if [ "$OPT_RESIZE" = "" ]; then	
		if [ "$OPT_MINI" = "$TRUE" ] ; then
			sed -i "s/#IPA_CAMPAIGN_FILE_NAME#/$CAMPAIGN_FILE_NAME_MINI/g" $TMP_DIR/template_info_mesubtype
		else
			sed -i "s/#IPA_CAMPAIGN_FILE_NAME#/$CAMPAIGN_FILE_NAME/g" $TMP_DIR/template_info_mesubtype
		fi
	elif [ "$OPT_RESIZE_ARG" = "1-2" ]; then
		sed -i "s/#IPA_CAMPAIGN_FILE_NAME#/$CAMPAIGN_FILE_NAME_S2/g" $TMP_DIR/template_info_mesubtype
	elif [ "$OPT_RESIZE_ARG" = "0-1" ]; then
		sed -i "s/#IPA_CAMPAIGN_FILE_NAME#/$CAMPAIGN_FILE_NAME_S1/g" $TMP_DIR/template_info_mesubtype
	fi
	cat $TMP_DIR/template_info_mesubtype >> $TMP_DIR/packageInfo.xml
	# Create Sw Domain
	echo "		<SwDomain>" >> $TMP_DIR/packageInfo.xml
	cp $TEMPLATES_FOLDER/TEMPLATE_PACKAGE_INFO/template_info_domainid $TMP_DIR/template_info_domainid
	sed -i "s/#IPA_DOMAINID_NAME#/$IPA_DOMAINID_NAME/g" $TMP_DIR/template_info_domainid
	sed -i "s/#IPA_DOMAINID_PRODUCT_NUMBER#/$IPA_DOMAINID_PRODUCT_NUMBER/g" $TMP_DIR/template_info_domainid
	sed -i "s/#IPA_DOMAINID_PRODUCT_REVISION#/$IPA_DOMAINID_PRODUCT_REVISION/g" $TMP_DIR/template_info_domainid
	sed -i "s/#IPA_DOMAINID_PRODUCT_DATE#/$IPA_DOMAINID_PRODUCT_DATE/g" $TMP_DIR/template_info_domainid
	sed -i "s/#IPA_DOMAINID_DESCRIPTION#/$IPA_DOMAINID_DESCRIPTION/g" $TMP_DIR/template_info_domainid
	sed -i "s/#IPA_DOMAINID_TYPE#/$IPA_DOMAINID_TYPE/g" $TMP_DIR/template_info_domainid
	cat $TMP_DIR/template_info_domainid >> $TMP_DIR/packageInfo.xml
	if [ "$OPT_MINI" = "$TRUE" ] ; then
		local MINI_IPA_APOS_BLOCK="Agent DEVMON LCT APOSCONFBIN APOSCMDBIN APOSEXTBIN COMSA COM ERIC-Sec-Control"
		while read line
			do
			BUNDLE_NAME=$(echo $line | awk -F';' '{print $2}')
			COMP_NAME=$(echo $line | awk -F';' '{print $3}')
                        # AFTER COMSA/COM MERGE only a one SWItem is required
                        if [ "$COMP_NAME" = "COMSA" ];then
                                  continue;
                        fi
			is_info_allowed=''
			for exc in $MINI_IPA_APOS_BLOCK; do 
				if [ "$COMP_NAME" == "$exc" ]; then
					is_info_allowed='true'
				fi
			done
			if [ "$is_info_allowed" = "true" ]; then
				cp $TEMPLATES_FOLDER/TEMPLATE_PACKAGE_INFO/template_info_swbundle $TMP_DIR/template_info_$BUNDLE_NAME
				TMP_BUNDLE_FILE_NAME=`echo $BUNDLE_NAME.x86_64.sdp| cut -c6-`
				sed -i "s/#BUNDLE_NAME#/$BUNDLE_NAME/g" $TMP_DIR/template_info_$BUNDLE_NAME
				sed -i "s/#BUNDLE_FILE_NAME#/$TMP_BUNDLE_FILE_NAME/g" $TMP_DIR/template_info_$BUNDLE_NAME
				cat $TMP_DIR/template_info_$BUNDLE_NAME >> $TMP_DIR/packageInfo.xml
				rm -f $TMP_DIR/template_info_$BUNDLE_NAME
			fi
		done < $TMP_DIR/$SOURCE_FILE_NAME
	else
		while read line
		do
			BUNDLE_NAME=$(echo $line | awk -F';' '{print $2}')
                        COMP_NAME=$(echo $line | awk -F';' '{print $3}')
                        # AFTER COMSA/COM MERGE only a one SWItem is required
                        if [ "$COMP_NAME" = "COMSA" ];then
                                continue;
                        fi
			cp $TEMPLATES_FOLDER/TEMPLATE_PACKAGE_INFO/template_info_swbundle $TMP_DIR/template_info_$BUNDLE_NAME
			TMP_BUNDLE_FILE_NAME=`echo $BUNDLE_NAME.x86_64.sdp| cut -c6-`
			sed -i "s/#BUNDLE_NAME#/$BUNDLE_NAME/g" $TMP_DIR/template_info_$BUNDLE_NAME
			sed -i "s/#BUNDLE_FILE_NAME#/$TMP_BUNDLE_FILE_NAME/g" $TMP_DIR/template_info_$BUNDLE_NAME
			cat $TMP_DIR/template_info_$BUNDLE_NAME >> $TMP_DIR/packageInfo.xml
			rm -f $TMP_DIR/template_info_$BUNDLE_NAME
		done < $TMP_DIR/$SOURCE_FILE_NAME
	fi
	# ADDING BUNDLE INFO FOR BRF - BRF_CMW - BRFP - BRFEIA - LOTC-CBA - COREMW
	cp $TEMPLATES_FOLDER/TEMPLATE_PACKAGE_INFO/template_info_swbundle_cba $TMP_DIR/template_info_BRF
	cp $TEMPLATES_FOLDER/TEMPLATE_PACKAGE_INFO/template_info_swbundle_cba $TMP_DIR/template_info_BRF_CMW
	cp $TEMPLATES_FOLDER/TEMPLATE_PACKAGE_INFO/template_info_swbundle_cba $TMP_DIR/template_info_BRFP
	cp $TEMPLATES_FOLDER/TEMPLATE_PACKAGE_INFO/template_info_swbundle_cba $TMP_DIR/template_info_BRFEIA
	cp $TEMPLATES_FOLDER/TEMPLATE_PACKAGE_INFO/template_info_swbundle_cba $TMP_DIR/template_info_BRF_LDE
	cp $TEMPLATES_FOLDER/TEMPLATE_PACKAGE_INFO/template_info_swbundle_cba $TMP_DIR/template_info_LDE_CBA
	cp $TEMPLATES_FOLDER/TEMPLATE_PACKAGE_INFO/template_info_swbundle_cba $TMP_DIR/template_info_coremw_opensaf
	cp $TEMPLATES_FOLDER/TEMPLATE_PACKAGE_INFO/template_info_swbundle_cba $TMP_DIR/template_info_coremw_sc
	cp $TEMPLATES_FOLDER/TEMPLATE_PACKAGE_INFO/template_info_swbundle_cba $TMP_DIR/template_info_coremw_common
        cp $TEMPLATES_FOLDER/TEMPLATE_PACKAGE_INFO/template_info_swbundle_cba $TMP_DIR/template_info_SEC_CRYPTO	
	cp $TEMPLATES_FOLDER/TEMPLATE_PACKAGE_INFO/template_info_swbundle_cba $TMP_DIR/template_info_SEC_AGENT
	cp $TEMPLATES_FOLDER/TEMPLATE_PACKAGE_INFO/template_info_swbundle_cba $TMP_DIR/template_info_SEC_ACS
        cp $TEMPLATES_FOLDER/TEMPLATE_PACKAGE_INFO/template_info_swbundle_cba $TMP_DIR/template_info_SEC_LA_LDAP
        cp $TEMPLATES_FOLDER/TEMPLATE_PACKAGE_INFO/template_info_swbundle_cba $TMP_DIR/template_info_SEC_LA_OI
        cp $TEMPLATES_FOLDER/TEMPLATE_PACKAGE_INFO/template_info_swbundle_cba $TMP_DIR/template_info_SEC_LA_SM
        cp $TEMPLATES_FOLDER/TEMPLATE_PACKAGE_INFO/template_info_swbundle_cba $TMP_DIR/template_info_SEC_LDAP_SM
        cp $TEMPLATES_FOLDER/TEMPLATE_PACKAGE_INFO/template_info_swbundle_cba $TMP_DIR/template_info_SEC_LDAP
        cp $TEMPLATES_FOLDER/TEMPLATE_PACKAGE_INFO/template_info_swbundle_cba $TMP_DIR/template_info_SEC_SECM
        cp $TEMPLATES_FOLDER/TEMPLATE_PACKAGE_INFO/template_info_swbundle_cba $TMP_DIR/template_info_SEC_SECM_LN

	sed -i "s/#BUNDLE_NAME#/$BRF_BUNDLE/g" $TMP_DIR/template_info_BRF
	sed -i "s/#BUNDLE_NAME#/$BRFCMW_BUNDLE/g" $TMP_DIR/template_info_BRF_CMW
	sed -i "s/#BUNDLE_NAME#/$BRFP_BUNDLE/g" $TMP_DIR/template_info_BRFP
	sed -i "s/#BUNDLE_NAME#/$BRFEIA_BUNDLE/g" $TMP_DIR/template_info_BRFEIA
	sed -i "s/#BUNDLE_NAME#/$BRFLDE_BUNDLE/g" $TMP_DIR/template_info_BRF_LDE
	sed -i "s/#BUNDLE_NAME#/$LDE_BUNDLE/g" $TMP_DIR/template_info_LDE_CBA
	sed -i "s/#BUNDLE_NAME#/$COREMW_OPENSAF_BUNDLE/g" $TMP_DIR/template_info_coremw_opensaf
	sed -i "s/#BUNDLE_NAME#/$COREMW_SC_BUNDLE/g" $TMP_DIR/template_info_coremw_sc
	sed -i "s/#BUNDLE_NAME#/$COREMW_COMMON_BUNDLE/g" $TMP_DIR/template_info_coremw_common
        sed -i "s/#BUNDLE_NAME#/$SEC_CRYPTO_BUNDLE/g" $TMP_DIR/template_info_SEC_CRYPTO
	sed -i "s/#BUNDLE_NAME#/$SEC_AGENT_BUNDLE/g" $TMP_DIR/template_info_SEC_AGENT
        sed -i "s/#BUNDLE_NAME#/$SEC_ACS_BUNDLE/g" $TMP_DIR/template_info_SEC_ACS
        sed -i "s/#BUNDLE_NAME#/$SEC_LA_LDAP_BUNDLE/g" $TMP_DIR/template_info_SEC_LA_LDAP
        sed -i "s/#BUNDLE_NAME#/$SEC_LA_OI_BUNDLE/g" $TMP_DIR/template_info_SEC_LA_OI
        sed -i "s/#BUNDLE_NAME#/$SEC_LA_SM_BUNDLE/g" $TMP_DIR/template_info_SEC_LA_SM
        sed -i "s/#BUNDLE_NAME#/$SEC_SECM_BUNDLE/g" $TMP_DIR/template_info_SEC_SECM
        sed -i "s/#BUNDLE_NAME#/$SEC_SECM_LN_BUNDLE/g" $TMP_DIR/template_info_SEC_SECM_LN
        sed -i "s/#BUNDLE_NAME#/$SEC_LDAP_SM_BUNDLE/g" $TMP_DIR/template_info_SEC_LDAP_SM
        sed -i "s/#BUNDLE_NAME#/$SEC_LDAP_BUNDLE/g" $TMP_DIR/template_info_SEC_LDAP

	cat $TMP_DIR/template_info_BRF >> $TMP_DIR/packageInfo.xml
	cat $TMP_DIR/template_info_BRF_CMW >> $TMP_DIR/packageInfo.xml
	cat $TMP_DIR/template_info_BRFP >> $TMP_DIR/packageInfo.xml
	cat $TMP_DIR/template_info_BRFEIA >> $TMP_DIR/packageInfo.xml
	cat $TMP_DIR/template_info_BRF_LDE >> $TMP_DIR/packageInfo.xml
	cat $TMP_DIR/template_info_LDE_CBA >> $TMP_DIR/packageInfo.xml
	cat $TMP_DIR/template_info_coremw_opensaf >> $TMP_DIR/packageInfo.xml
	cat $TMP_DIR/template_info_coremw_sc >> $TMP_DIR/packageInfo.xml
	cat $TMP_DIR/template_info_coremw_common >> $TMP_DIR/packageInfo.xml
        cat $TMP_DIR/template_info_SEC_CRYPTO >> $TMP_DIR/packageInfo.xml
	cat $TMP_DIR/template_info_SEC_AGENT >> $TMP_DIR/packageInfo.xml	
        cat $TMP_DIR/template_info_SEC_ACS >> $TMP_DIR/packageInfo.xml	
	cat $TMP_DIR/template_info_SEC_LA_LDAP >> $TMP_DIR/packageInfo.xml
        cat $TMP_DIR/template_info_SEC_LA_OI >> $TMP_DIR/packageInfo.xml
        cat $TMP_DIR/template_info_SEC_LA_SM >> $TMP_DIR/packageInfo.xml
	cat $TMP_DIR/template_info_SEC_LDAP_SM >> $TMP_DIR/packageInfo.xml
	cat $TMP_DIR/template_info_SEC_LDAP >> $TMP_DIR/packageInfo.xml
	cat $TMP_DIR/template_info_SEC_SECM >> $TMP_DIR/packageInfo.xml
        cat $TMP_DIR/template_info_SEC_SECM_LN >> $TMP_DIR/packageInfo.xml
	rm -f $TMP_DIR/template_info_BRF
        rm -f $TMP_DIR/template_info_SEC_CRYPTO
	rm -f $TMP_DIR/template_info_SEC_AGENT
        rm -f $TMP_DIR/template_info_SEC_ACS
        rm -f $TMP_DIR/template_info_SEC_LA_LDAP
        rm -f $TMP_DIR/template_info_SEC_LA_OI
        rm -f $TMP_DIR/template_info_SEC_LA_SM
	rm -f $TMP_DIR/template_info_BRF_CMW
	rm -f $TMP_DIR/template_info_BRF_LDE
	rm -f $TMP_DIR/template_info_BRFP
	rm -f $TMP_DIR/template_info_BRFEIA
	rm -f $TMP_DIR/template_info_LDE_CBA
	rm -f $TMP_DIR/template_info_coremw_sc
	rm -f $TMP_DIR/template_info_coremw_opensaf
	rm -f $TMP_DIR/template_info_coremw_common
	rm -f $TMP_DIR/template_info_SEC_LDAP_SM
	rm -f $TMP_DIR/template_info_SEC_LDAP_SM
	rm -f $TMP_DIR/template_info_SEC_SECM
	rm -f $TMP_DIR/template_info_SEC_SECM_LN
	echo "		</SwDomain>" >> $TMP_DIR/packageInfo.xml
	# Create end part
	cat $TEMPLATES_FOLDER/TEMPLATE_PACKAGE_INFO/template_info_end >> $TMP_DIR/packageInfo.xml
	cp $TMP_DIR/packageInfo.xml $TMP_DIR/campaign/packageInfo.xml
}

#START creating the intro part of the campaign ===================================================================================================================================================

	cp $TEMPLATES_FOLDER/TEMPLATE_INTRO_END/template_intro $TMP_DIR/
	if [ "$OPT_RESIZE" = "" ] ; then
		if [ "$OPT_MINI" = "$TRUE" ] ; then
			sed -i "s/#CAMPAIGN_NAME#/$CAMPAIGN_NAME_MINI/g" $TMP_DIR/template_intro
		else
			sed -i "s/#CAMPAIGN_NAME#/$CAMPAIGN_NAME/g" $TMP_DIR/template_intro
        fi
		cat $TMP_DIR/template_intro >> $TMP_DIR/final.xml
		echo "			<amfEntityTypes>" >> $TMP_DIR/final.xml
	fi
	if [ "$OPT_RESIZE_ARG" = "0-1" ] ; then
		sed -i "s/#CAMPAIGN_NAME#/$CAMPAIGN_NAME_S1/g" $TMP_DIR/template_intro
        cat $TMP_DIR/template_intro >> $TMP_DIR/final.xml			
		echo "			<amfEntityTypes>" >> $TMP_DIR/final.xml
	fi
	if [ "$OPT_RESIZE_ARG" = "1-2" ] ; then
		sed -i "s/#CAMPAIGN_NAME#/$CAMPAIGN_NAME_S2/g" $TMP_DIR/template_intro
		cat $TMP_DIR/template_intro >> $TMP_DIR/final.xml
	fi
	rm -f $TMP_DIR/template_intro
	is_verbose && echo "STEP: INTRO CREATION DONE"

#END creating the intro part of the campaign ===============================================================================================================================================


#START Creating component type name part for 2N and NoRed =====================================================================================================================================

if [ "$OPT_RESIZE" = "" ] || [ "$OPT_RESIZE_ARG" = "0-1" ] ; then
	while read line    
	do    
		type=`echo $line | awk -F';' '{print $1}'`
		if [ "$type" = "2N" ] || [ "$type" = "NORED" ]
		then
			BUNDLE_NAME=$(echo $line | awk -F';' '{print $2}')
			COMP_NAME=$(echo $line | awk -F';' '{print $3}')
			COMP_TYPE_NAME=$(echo $line | awk -F';' '{print $5}')
			CS_TYPE=$(echo $line | awk -F';' '{print $6}')
			COMP_VERSION=$(echo $line | awk -F';' '{print $7}')
			CLC_NAME=$(echo $line | awk -F';' '{print $8}')
			HelthCheck=$(echo $line | awk -F';' '{print $9}')
			if [ "$COMP_TYPE_NAME" = "ERIC-ComSa-Cmw" ]
			then
				cp $TEMPLATES_FOLDER/TEMPLATE_COMP_TYPE/template_comp_type_comsa $TMP_DIR/
				sed -i "s/#COMP_TYPE_NAME#/$COMP_TYPE_NAME/g" $TMP_DIR/template_comp_type_comsa
				sed -i "s/#COMP_VERSION#/$COMP_VERSION/g" $TMP_DIR/template_comp_type_comsa
				sed -i "s/#CS_TYPE#/$CS_TYPE/g" $TMP_DIR/template_comp_type_comsa
				sed -i "s@#CLC_NAME#@$CLC_NAME@g" $TMP_DIR/template_comp_type_comsa
				sed -i "s/#HCK_MAX_DURATION#/$HCK_MAX_DURATION/g" $TMP_DIR/template_comp_type_comsa
				sed -i "s/#HCK#/$HelthCheck/g" $TMP_DIR/template_comp_type_comsa
				sed -i "s/#HCK_PERIOD#/$HCK_PERIOD/g" $TMP_DIR/template_comp_type_comsa
				sed -i "s/#BUNDLE_NAME#/$BUNDLE_NAME/g" $TMP_DIR/template_comp_type_comsa
				sed -i "s/#QUIESCING_COMPLETE_TIMEOUT#/$QUIESCING_COMPLETE_TIMEOUT/g" $TMP_DIR/template_comp_type_comsa
 				sed -i "s/#CLC_CLI_TIMEOUT_COMSA#/$CLC_CLI_TIMEOUT_COMSA/g" $TMP_DIR/template_comp_type_comsa
				sed -i "s/#CALLBACK_TIMEOUT_COMSA#/$CALLBACK_TIMEOUT_COMSA/g" $TMP_DIR/template_comp_type_comsa
				cat $TMP_DIR/template_comp_type_comsa >> $TMP_DIR/final.xml
				rm -f $TMP_DIR/template_comp_type_comsa
        cp $TEMPLATES_FOLDER/TEMPLATE_COMP_TYPE/template_comp_type_comsa_sshd $TMP_DIR/
				sed -i "s/#QUIESCING_COMPLETE_TIMEOUT#/$QUIESCING_COMPLETE_TIMEOUT/g" $TMP_DIR/template_comp_type_comsa_sshd
        sed -i "s/#CLC_CLI_TIMEOUT_COMSA#/$CLC_CLI_TIMEOUT_COMSA/g" $TMP_DIR/template_comp_type_comsa_sshd
        sed -i "s/#CALLBACK_TIMEOUT_COMSA#/$CALLBACK_TIMEOUT_COMSA/g" $TMP_DIR/template_comp_type_comsa_sshd
			  sed -i "s/#HCK_MAX_DURATION#/$HCK_MAX_DURATION/g" $TMP_DIR/template_comp_type_comsa_sshd
 				sed -i "s/#HCK_PERIOD#/$HCK_PERIOD/g" $TMP_DIR/template_comp_type_comsa_sshd
				sed -i "s/#BUNDLE_NAME#/$BUNDLE_NAME/g" $TMP_DIR/template_comp_type_comsa_sshd	
				sed -i "s/#COMP_SSH_NAME#/$COMSA_COMP_SSHD/g" $TMP_DIR/template_comp_type_comsa_sshd
				sed -i "s/#COMP_SSH_VERSION#/$COMSA_SSHD_RSTATE/g" $TMP_DIR/template_comp_type_comsa_sshd
				sed -i "s/#CS_SSH_TYPE#/$COMSA_CS_SSHD/g" $TMP_DIR/template_comp_type_comsa_sshd
				cat $TMP_DIR/template_comp_type_comsa_sshd >> $TMP_DIR/final.xml
				rm -f $TMP_DIR/template_comp_type_comsa_sshd
				cp $TEMPLATES_FOLDER/TEMPLATE_COMP_TYPE/template_comp_type_comsa_tlsd $TMP_DIR/
				sed -i "s/#QUIESCING_COMPLETE_TIMEOUT#/$QUIESCING_COMPLETE_TIMEOUT/g" $TMP_DIR/template_comp_type_comsa_tlsd
				sed -i "s/#CLC_CLI_TIMEOUT_COMSA#/$CLC_CLI_TIMEOUT_COMSA/g" $TMP_DIR/template_comp_type_comsa_tlsd
				sed -i "s/#CALLBACK_TIMEOUT_COMSA#/$CALLBACK_TIMEOUT_COMSA/g" $TMP_DIR/template_comp_type_comsa_tlsd
				sed -i "s/#HCK_MAX_DURATION#/$HCK_MAX_DURATION/g" $TMP_DIR/template_comp_type_comsa_tlsd
        sed -i "s/#HCK_PERIOD#/$HCK_PERIOD/g" $TMP_DIR/template_comp_type_comsa_tlsd
        sed -i "s/#BUNDLE_NAME#/$BUNDLE_NAME/g" $TMP_DIR/template_comp_type_comsa_tlsd
        sed -i "s/#COMP_TLS_NAME#/$COMSA_COMP_TLSD/g" $TMP_DIR/template_comp_type_comsa_tlsd
        sed -i "s/#COMP_TLS_VERSION#/$COMSA_TLSD_RSTATE/g" $TMP_DIR/template_comp_type_comsa_tlsd
				sed -i "s/#CS_TLS_TYPE#/$COMSA_CS_TLSD/g" $TMP_DIR/template_comp_type_comsa_tlsd
				cat $TMP_DIR/template_comp_type_comsa_tlsd >> $TMP_DIR/final.xml
				rm -f $TMP_DIR/template_comp_type_comsa_tlsd
				cp $TEMPLATES_FOLDER/TEMPLATE_COMP_TYPE/template_comp_type_comsa_vsftpd $TMP_DIR/
				sed -i "s/#QUIESCING_COMPLETE_TIMEOUT#/$QUIESCING_COMPLETE_TIMEOUT/g" $TMP_DIR/template_comp_type_comsa_vsftpd
				sed -i "s/#CLC_CLI_TIMEOUT_COMSA#/$CLC_CLI_TIMEOUT_COMSA/g" $TMP_DIR/template_comp_type_comsa_vsftpd
				sed -i "s/#CALLBACK_TIMEOUT_COMSA#/$CALLBACK_TIMEOUT_COMSA/g" $TMP_DIR/template_comp_type_comsa_vsftpd
				sed -i "s/#HCK_MAX_DURATION#/$HCK_MAX_DURATION/g" $TMP_DIR/template_comp_type_comsa_vsftpd
        sed -i "s/#HCK_PERIOD#/$HCK_PERIOD/g" $TMP_DIR/template_comp_type_comsa_vsftpd
        sed -i "s/#BUNDLE_NAME#/$BUNDLE_NAME/g" $TMP_DIR/template_comp_type_comsa_vsftpd
        sed -i "s/#COMP_VSFTPD_NAME#/$COMSA_COMP_VSFTPD/g" $TMP_DIR/template_comp_type_comsa_vsftpd
        sed -i "s/#COMP_VSFTPD_VERSION#/$COMSA_VSFTPD_RSTATE/g" $TMP_DIR/template_comp_type_comsa_vsftpd
				sed -i "s/#CS_VSFTPD_TYPE#/$COMSA_CS_VSFTPD/g" $TMP_DIR/template_comp_type_comsa_vsftpd
				cat $TMP_DIR/template_comp_type_comsa_vsftpd >> $TMP_DIR/final.xml
				rm -f $TMP_DIR/template_comp_type_comsa_vsftpd


			elif [ "$COMP_TYPE_NAME" = "ERIC-Sec-Control" ]
			then
				cp $TEMPLATES_FOLDER/TEMPLATE_COMP_TYPE/template_comp_type_sec $TMP_DIR/template_comp_type_sec
				sed -i "s/#COMP_TYPE_NAME#/$COMP_TYPE_NAME/g" $TMP_DIR/template_comp_type_sec
				sed -i "s/#COMP_VERSION#/$COMP_VERSION/g" $TMP_DIR/template_comp_type_sec
				sed -i "s/#CS_TYPE#/$CS_TYPE/g" $TMP_DIR/template_comp_type_sec
				sed -i "s@#CLC_NAME#@$CLC_NAME@g" $TMP_DIR/template_comp_type_sec
				sed -i "s/#HCK#/$HelthCheck/g" $TMP_DIR/template_comp_type_sec
				sed -i "s/#HCK_PERIOD#/$HCK_PERIOD/g" $TMP_DIR/template_comp_type_sec
				sed -i "s/#HCK_MAX_DURATION_SEC#/$HCK_MAX_DURATION_SEC/g" $TMP_DIR/template_comp_type_sec
				sed -i "s/#BUNDLE_NAME#/$BUNDLE_NAME/g" $TMP_DIR/template_comp_type_sec
				sed -i "s/#RECOVERY_ON_ERROR#/$RECOVERY_ON_ERROR/g" $TMP_DIR/template_comp_type_sec
				sed -i "s/#QUIESCING_COMPLETE_TIMEOUT#/$QUIESCING_COMPLETE_TIMEOUT/g" $TMP_DIR/template_comp_type_sec
				sed -i "s/#CLC_CLI_TIMEOUT#/$CLC_CLI_TIMEOUT/g" $TMP_DIR/template_comp_type_sec
				sed -i "s/#CALLBACK_TIMEOUT#/$CALLBACK_TIMEOUT/g" $TMP_DIR/template_comp_type_sec
				cat $TMP_DIR/template_comp_type_sec >> $TMP_DIR/final.xml
				rm -f $TMP_DIR/template_comp_type_sec
			else
                                if shallExcludeApp $COMP_NAME; then
	                                 cp $TEMPLATES_FOLDER/TEMPLATE_BUNDLE/template_init_apg $TMP_DIR/
                                         sed -i "s/#PARAM#/$COMP_NAME/g" $TMP_DIR/template_init_apg
                                         sed -i "s/#SCRIPT#/$EXCLUDE_BUNDLES/g" $TMP_DIR/template_init_apg
                                         sed -i "s/#TYPE#/$INSTALL_TYPE/g" $TMP_DIR/template_init_apg
	                                 cat $TMP_DIR/template_init_apg >> $TMP_DIR/final.xml
				         rm -f $TMP_DIR/template_init_apg
                                fi
				cp $TEMPLATES_FOLDER/TEMPLATE_COMP_TYPE/template_comp_type $TMP_DIR/template_comp_type_$COMP_NAME
				sed -i "s/#COMP_TYPE_NAME#/$COMP_TYPE_NAME/g" $TMP_DIR/template_comp_type_$COMP_NAME
				
				if isOldNamingConvention "$BUNDLE_NAME" ; then
					# Old naming convention for APG block's component type
					# safVersion=<Rstate>,safCompType=<CompTypeName>
					# Example: safVersion=R1E,safCompType=ERIC-APG_ASEC
				sed -i "s/#COMP_VERSION#/$COMP_VERSION/g" $TMP_DIR/template_comp_type_$COMP_NAME
				else
					# New naming convention for APG block's component type
					# safVersion=<CXC>-<Rstate>,safCompType=<CompTypeName>
					# Example: safVersion=CXC1371474-R1E,safCompType=ERIC-APG_ASEC
					BUNDLE_CXC=$(echo "$BUNDLE_NAME" | sed 's/-[^-]*$//' | awk -F'-' '{ print $NF }')
					sed -i "s/#COMP_VERSION#/$BUNDLE_CXC-$COMP_VERSION/g" $TMP_DIR/template_comp_type_$COMP_NAME
				fi
				
					sed -i "s/#CS_TYPE#/$CS_TYPE/g" $TMP_DIR/template_comp_type_$COMP_NAME
					sed -i "s@#CLC_NAME#@$CLC_NAME@g" $TMP_DIR/template_comp_type_$COMP_NAME
					sed -i "s/#HCK#/$HelthCheck/g" $TMP_DIR/template_comp_type_$COMP_NAME
					sed -i "s/#QUIESCING_COMPLETE_TIMEOUT#/$QUIESCING_COMPLETE_TIMEOUT/g" $TMP_DIR/template_comp_type_$COMP_NAME
					sed -i "s/#BUNDLE_NAME#/$BUNDLE_NAME/g" $TMP_DIR/template_comp_type_$COMP_NAME
					if [ "$COMP_TYPE_NAME" = "ERIC-APG_Agent" ]
					then
						sed -i "s/#RECOVERY_ON_ERROR#/$RECOVERY_ON_ERROR_AGENT/g" $TMP_DIR/template_comp_type_$COMP_NAME
						sed -i "s/#CLC_CLI_TIMEOUT#/$CLC_CLI_TIMEOUT_AGENT/g" $TMP_DIR/template_comp_type_$COMP_NAME
						sed -i "s/#CALLBACK_TIMEOUT#/$CALLBACK_TIMEOUT_AGENT/g" $TMP_DIR/template_comp_type_$COMP_NAME
						sed -i "s/#HCK_PERIOD#/$HCK_PERIOD_AGENT/g" $TMP_DIR/template_comp_type_$COMP_NAME
						sed -i "s/#HCK_MAX_DURATION#/$HCK_MAX_DURATION_AGENT/g" $TMP_DIR/template_comp_type_$COMP_NAME
					else
						sed -i "s/#RECOVERY_ON_ERROR#/$RECOVERY_ON_ERROR/g" $TMP_DIR/template_comp_type_$COMP_NAME
						sed -i "s/#CLC_CLI_TIMEOUT#/$CLC_CLI_TIMEOUT/g" $TMP_DIR/template_comp_type_$COMP_NAME
						sed -i "s/#CALLBACK_TIMEOUT#/$CALLBACK_TIMEOUT/g" $TMP_DIR/template_comp_type_$COMP_NAME
						sed -i "s/#HCK_PERIOD#/$HCK_PERIOD/g" $TMP_DIR/template_comp_type_$COMP_NAME
						sed -i "s/#HCK_MAX_DURATION#/$HCK_MAX_DURATION/g" $TMP_DIR/template_comp_type_$COMP_NAME
					fi
					cat $TMP_DIR/template_comp_type_$COMP_NAME >> $TMP_DIR/final.xml
					rm -f $TMP_DIR/template_comp_type_$COMP_NAME
					if shallExcludeApp $COMP_NAME; then                                
					    cp $TEMPLATES_FOLDER/TEMPLATE_BUNDLE/template_end_apg $TMP_DIR/template_end_apg
					    cat $TMP_DIR/template_end_apg >> $TMP_DIR/final.xml
					    rm -f $TMP_DIR/template_end_apg
					fi
				fi
			fi
		done < $TMP_DIR/$SOURCE_FILE_NAME
	is_verbose && echo "STEP: COMP_TYPE CREATION DONE"
	fi	

#END Creating component type name part for 2N and NoRed ==============================================================================================================================================


#START Creating SU_BASE_TYPE FOR 2N ==================================================================================================================================================================

if [ "$OPT_RESIZE" = "" ] || [ "$OPT_RESIZE_ARG" = "0-1" ] ; then
	cp $TEMPLATES_FOLDER/TEMPLATE_SU_TYPE/template_su_type_2n_init $TMP_DIR/
	cp $TEMPLATES_FOLDER/TEMPLATE_SU_TYPE/template_su_type_end $TMP_DIR/
	sed -i "s/#SAF_VERSION#/$SAF_VERSION/g" $TMP_DIR/template_su_type_2n_init
	sed -i "s/#SU_2N_TYPE#/$SU_2N_TYPE/g" $TMP_DIR/template_su_type_2n_init
	cat $TMP_DIR/template_su_type_2n_init >> $TMP_DIR/final.xml
	rm -f $TMP_DIR/template_su_type_2n_init
	while read line    
	do    
		type=`echo $line | awk -F';' '{print $1}'`
		if [ "$type" = "2N" ] 
		then
			BUNDLE_NAME=$(echo $line | awk -F';' '{print $2}')
			COMP_NAME=$(echo $line | awk -F';' '{print $3}')
			COMP_TYPE_NAME=$(echo $line | awk -F';' '{print $5}')
			CS_TYPE=$(echo $line | awk -F';' '{print $6}')
			COMP_VERSION=$(echo $line | awk -F';' '{print $7}')
			CLC_NAME=$(echo $line | awk -F';' '{print $8}')
			HelthCheck=$(echo $line | awk -F';' '{print $9}')
                        if shallExcludeApp $COMP_NAME; then
                               cp $TEMPLATES_FOLDER/TEMPLATE_BUNDLE/template_init_apg $TMP_DIR/
                               sed -i "s/#PARAM#/$COMP_NAME/g" $TMP_DIR/template_init_apg
                               sed -i "s/#SCRIPT#/$EXCLUDE_BUNDLES/g" $TMP_DIR/template_init_apg
                               sed -i "s/#TYPE#/$INSTALL_TYPE/g" $TMP_DIR/template_init_apg
                               cat $TMP_DIR/template_init_apg >> $TMP_DIR/final.xml
                               rm -f $TMP_DIR/template_init_apg
                        fi
			cp $TEMPLATES_FOLDER/TEMPLATE_SU_TYPE/template_su_type_component $TMP_DIR/template_su_type_component_$COMP_NAME
			sed -i "s/#COMP_TYPE_NAME#/$COMP_TYPE_NAME/g" $TMP_DIR/template_su_type_component_$COMP_NAME
			
			if [ "$COMP_TYPE_NAME" != "ERIC-ComSa-Cmw" ] && [ "$COMP_TYPE_NAME" != "ERIC-Sec-Control" ] ; then
				if isOldNamingConvention "$BUNDLE_NAME" ; then
					# Old naming convention for APG block's component type
					# safVersion=<Rstate>,safCompType=<CompTypeName>
					# Example: safVersion=R1E,safCompType=ERIC-APG_ASEC
					sed -i "s/#COMP_VERSION#/$COMP_VERSION/g" $TMP_DIR/template_su_type_component_$COMP_NAME
				else
					# New naming convention for APG block's component type
					# safVersion=<CXC>-<Rstate>,safCompType=<CompTypeName>
					# Example: safVersion=CXC1371474-R1E,safCompType=ERIC-APG_ASEC
					BUNDLE_CXC=$(echo "$BUNDLE_NAME" | sed 's/-[^-]*$//' | awk -F'-' '{ print $NF }')
					sed -i "s/#COMP_VERSION#/$BUNDLE_CXC-$COMP_VERSION/g" $TMP_DIR/template_su_type_component_$COMP_NAME
				fi
			else
				# CMW & SEC
				if [ "$COMP_TYPE_NAME" == "ERIC-ComSa-Cmw" ];then
					sed -i "s/#COMP_VERSION#/$COMP_VERSION/g" $TMP_DIR/template_su_type_component_$COMP_NAME
					cp $TEMPLATES_FOLDER/TEMPLATE_SU_TYPE/template_su_type_component $TMP_DIR/template_su_type_component_sshd
					sed -i "s/#COMP_TYPE_NAME#/$COMSA_COMP_SSHD/g" $TMP_DIR/template_su_type_component_sshd
					sed -i "s/#COMP_VERSION#/$COMP_VERSION/g" $TMP_DIR/template_su_type_component_sshd
					cat $TMP_DIR/template_su_type_component_sshd >> $TMP_DIR/final.xml
					rm -f $TMP_DIR/template_su_type_component_sshd

	        cp $TEMPLATES_FOLDER/TEMPLATE_SU_TYPE/template_su_type_component $TMP_DIR/template_su_type_component_tlsd
          sed -i "s/#COMP_TYPE_NAME#/$COMSA_COMP_TLSD/g" $TMP_DIR/template_su_type_component_tlsd
          sed -i "s/#COMP_VERSION#/$COMP_VERSION/g" $TMP_DIR/template_su_type_component_tlsd
          cat $TMP_DIR/template_su_type_component_tlsd >> $TMP_DIR/final.xml
          rm -f $TMP_DIR/template_su_type_component_tlsd


	        cp $TEMPLATES_FOLDER/TEMPLATE_SU_TYPE/template_su_type_component $TMP_DIR/template_su_type_component_vsftpd
          sed -i "s/#COMP_TYPE_NAME#/$COMSA_COMP_VSFTPD/g" $TMP_DIR/template_su_type_component_vsftpd
          sed -i "s/#COMP_VERSION#/$COMP_VERSION/g" $TMP_DIR/template_su_type_component_vsftpd
          cat $TMP_DIR/template_su_type_component_vsftpd >> $TMP_DIR/final.xml
          rm -f $TMP_DIR/template_su_type_component_vsftpd

				else
					sed -i "s/#COMP_VERSION#/$COMP_VERSION/g" $TMP_DIR/template_su_type_component_$COMP_NAME
				fi	
				
			fi
			
			cat $TMP_DIR/template_su_type_component_$COMP_NAME >> $TMP_DIR/final.xml
			rm -f $TMP_DIR/template_su_type_component_$COMP_NAME
                        if shallExcludeApp $COMP_NAME; then
                               cp $TEMPLATES_FOLDER/TEMPLATE_BUNDLE/template_end_apg $TMP_DIR/template_end_apg
                               cat $TMP_DIR/template_end_apg >> $TMP_DIR/final.xml
		               rm -f $TMP_DIR/template_end_apg
                        fi
		fi
	done < $TMP_DIR/$SOURCE_FILE_NAME 
	while read line    
	do    
		type=$(echo $line | awk -F';' '{print $1}')
		if [ "$type" = "2N" ] 
		then
			SVC_TYPE=$(echo $line | awk -F';' '{print $10}')
			COMP_NAME=$(echo $line | awk -F';' '{print $3}')
                        if shallExcludeApp $COMP_NAME; then
                               cp $TEMPLATES_FOLDER/TEMPLATE_BUNDLE/template_init_apg $TMP_DIR/
                               sed -i "s/#PARAM#/$COMP_NAME/g" $TMP_DIR/template_init_apg
                               sed -i "s/#SCRIPT#/$EXCLUDE_BUNDLES/g" $TMP_DIR/template_init_apg
                               sed -i "s/#TYPE#/$INSTALL_TYPE/g" $TMP_DIR/template_init_apg
                               cat $TMP_DIR/template_init_apg >> $TMP_DIR/final.xml
                               rm -f $TMP_DIR/template_init_apg
                        fi
			cp $TEMPLATES_FOLDER/TEMPLATE_SU_TYPE/template_svc_type $TMP_DIR/template_svc_type_$COMP_NAME
			sed -i "s/#SAF_VERSION#/$SAF_VERSION/g" $TMP_DIR/template_svc_type_$COMP_NAME
			sed -i "s/#SAF_SVC_TYPE#/${SVC_TYPE}/g" $TMP_DIR/template_svc_type_$COMP_NAME
			cat $TMP_DIR/template_svc_type_$COMP_NAME >> $TMP_DIR/final.xml
			rm -f $TMP_DIR/template_svc_type_$COMP_NAME
                        if shallExcludeApp $COMP_NAME; then
                               cp $TEMPLATES_FOLDER/TEMPLATE_BUNDLE/template_end_apg $TMP_DIR/template_end_apg
                               cat $TMP_DIR/template_end_apg >> $TMP_DIR/final.xml
                               rm -f $TMP_DIR/template_end_apg
                        fi
		fi
	done < $TMP_DIR/$SOURCE_FILE_NAME
	cat $TMP_DIR/template_su_type_end >> $TMP_DIR/final.xml
	rm -f $TMP_DIR/template_su_type_end
	is_verbose && echo "STEP: SU_TYPE 2N CREATION DONE"
fi

#END Creating SU_BASE_TYPE FOR 2N ======================================================================================================================================================================


#START Creating SU_BASE_TYPE FOR NO_RED =============================================================================================================================================================================

if [ "$OPT_RESIZE" = "" ] || [ "$OPT_RESIZE_ARG" = "0-1" ] ; then
	while read line    
	do    
		type=$(echo $line | awk -F';' '{print $1}')
		if [ "$type" = "NORED" ] 
		then
			BUNDLE_NAME=$(echo $line | awk -F';' '{print $2}')
			COMP_NAME=$(echo $line | awk -F';' '{print $3}')
			COMP_TYPE_NAME=$(echo $line | awk -F';' '{print $5}')
			CS_TYPE=$(echo $line | awk -F';' '{print $6}')
			COMP_VERSION=$(echo $line | awk -F';' '{print $7}')
			CLC_NAME=$(echo $line | awk -F';' '{print $8}')
			HelthCheck=$(echo $line | awk -F';' '{print $9}')
			SVC_TYPE=$(echo $line | awk -F';' '{print $10}')
			CSI_NAME=$(echo $line | awk -F';' '{print $11}')
                        if shallExcludeApp $COMP_NAME; then
                               cp $TEMPLATES_FOLDER/TEMPLATE_BUNDLE/template_init_apg $TMP_DIR/
                               sed -i "s/#PARAM#/$COMP_NAME/g" $TMP_DIR/template_init_apg
                               sed -i "s/#SCRIPT#/$EXCLUDE_BUNDLES/g" $TMP_DIR/template_init_apg
                               sed -i "s/#TYPE#/$INSTALL_TYPE/g" $TMP_DIR/template_init_apg
                               cat $TMP_DIR/template_init_apg >> $TMP_DIR/final.xml
                               rm -f $TMP_DIR/template_init_apg
                        fi
			cp $TEMPLATES_FOLDER/TEMPLATE_SU_TYPE/template_su_type_nored_init $TMP_DIR/
			cp $TEMPLATES_FOLDER/TEMPLATE_SU_TYPE/template_su_type_end $TMP_DIR/
			sed -i "s/#SAF_VERSION#/$SAF_VERSION/g" $TMP_DIR/template_su_type_nored_init
			sed -i "s/#CSI_NAME#/${CSI_NAME}/g" $TMP_DIR/template_su_type_nored_init
			cat $TMP_DIR/template_su_type_nored_init >> $TMP_DIR/final.xml
			rm -f $TMP_DIR/template_su_type_nored_init
			cp $TEMPLATES_FOLDER/TEMPLATE_SU_TYPE/template_su_type_component $TMP_DIR/template_su_type_component_$COMP_NAME
			sed -i "s/#COMP_TYPE_NAME#/$COMP_TYPE_NAME/g" $TMP_DIR/template_su_type_component_$COMP_NAME
			
			if isOldNamingConvention "$BUNDLE_NAME" ; then
				# Old naming convention for APG block's component type
				# safVersion=<Rstate>,safCompType=<CompTypeName>
				# Example: safVersion=R1E,safCompType=ERIC-APG_ASEC
				sed -i "s/#COMP_VERSION#/$COMP_VERSION/g" $TMP_DIR/template_su_type_component_$COMP_NAME
			else
				# New naming convention for APG block's component type
				# safVersion=<CXC>-<Rstate>,safCompType=<CompTypeName>
				# Example: safVersion=CXC1371474-R1E,safCompType=ERIC-APG_ASEC
				BUNDLE_CXC=$(echo "$BUNDLE_NAME" | sed 's/-[^-]*$//' | awk -F'-' '{ print $NF }')
				sed -i "s/#COMP_VERSION#/$BUNDLE_CXC-$COMP_VERSION/g" $TMP_DIR/template_su_type_component_$COMP_NAME
			fi
			
			cat $TMP_DIR/template_su_type_component_$COMP_NAME >> $TMP_DIR/final.xml
			rm -f $TMP_DIR/template_su_type_component_$COMP_NAME
			cp $TEMPLATES_FOLDER/TEMPLATE_SU_TYPE/template_svc_type_nored $TMP_DIR/template_svc_type_nored_$COMP_NAME
			sed -i "s/#SAF_VERSION#/$SAF_VERSION/g" $TMP_DIR/template_svc_type_nored_$COMP_NAME
			sed -i "s/#SAF_SVC_TYPE#/${CSI_NAME}/g" $TMP_DIR/template_svc_type_nored_$COMP_NAME
			cat $TMP_DIR/template_svc_type_nored_$COMP_NAME >> $TMP_DIR/final.xml
			cat $TMP_DIR/template_su_type_end >> $TMP_DIR/final.xml
                        if shallExcludeApp $COMP_NAME; then
                               cp $TEMPLATES_FOLDER/TEMPLATE_BUNDLE/template_end_apg $TMP_DIR/
                               cat $TMP_DIR/template_end_apg >> $TMP_DIR/final.xml
                               rm -f $TMP_DIR/template_end_apg
                        fi
			rm -f $TMP_DIR/template_svc_type_nored_$COMP_NAME
			rm -f $TMP_DIR/template_su_type_end
		fi
	done < $TMP_DIR/$SOURCE_FILE_NAME 
	is_verbose && echo "STEP: SU_TYPE NO_RED CREATION DONE"
fi

#END Creating SU_BASE_TYPE FOR NO_RED ======================================================================================================================================================================


#START Creating SG_BASE_TYPE ============================================================================================================================================================================

if [ "$OPT_RESIZE" = "" ] || [ "$OPT_RESIZE_ARG" = "0-1" ] ; then
	cp $TEMPLATES_FOLDER/TEMPLATE_SG_TYPE/template_SG_TYPE_2N $TMP_DIR/
	sed -i "s/#SG_2N_TYPE#/$SG_2N_TYPE/g" $TMP_DIR/template_SG_TYPE_2N
	sed -i "s/#SU_2N_TYPE#/$SU_2N_TYPE/g" $TMP_DIR/template_SG_TYPE_2N
	sed -i "s/#SU_REST_PROB#/$SU_REST_PROB_2N/g" $TMP_DIR/template_SG_TYPE_2N
	sed -i "s/#COMP_RESTART_MAX#/$COMP_RESTART_MAX_2N/g" $TMP_DIR/template_SG_TYPE_2N
	sed -i "s/#COMP_RESTART_PROB#/$COMP_RESTART_PROB_2N/g" $TMP_DIR/template_SG_TYPE_2N
	sed -i "s/#SAF_VERSION#/$SAF_VERSION/g" $TMP_DIR/template_SG_TYPE_2N
	cat $TMP_DIR/template_SG_TYPE_2N >> $TMP_DIR/final.xml
	while read line    
	do    
		type=$(echo $line | awk -F';' '{print $1}')
		if [ "$type" = "NORED" ] 
		then	
			COMP_NAME=$(echo $line | awk -F';' '{print $3}')
			CSI_NAME=$(echo $line | awk -F';' '{print $11}')
                        if shallExcludeApp $COMP_NAME; then
                               cp $TEMPLATES_FOLDER/TEMPLATE_BUNDLE/template_init_apg $TMP_DIR/
                               sed -i "s/#PARAM#/$COMP_NAME/g" $TMP_DIR/template_init_apg
                               sed -i "s/#SCRIPT#/$EXCLUDE_BUNDLES/g" $TMP_DIR/template_init_apg
                               sed -i "s/#TYPE#/$INSTALL_TYPE/g" $TMP_DIR/template_init_apg
                               cat $TMP_DIR/template_init_apg >> $TMP_DIR/final.xml
                               rm -f $TMP_DIR/template_init_apg
                        fi
			cp $TEMPLATES_FOLDER/TEMPLATE_SG_TYPE/template_SG_TYPE_NORED $TMP_DIR/template_SG_TYPE_NORED_$COMP_NAME
			sed -i "s/#CSI_NAME#/$CSI_NAME/g" $TMP_DIR/template_SG_TYPE_NORED_$COMP_NAME
			sed -i "s/#SU_REST_PROB#/$SU_REST_PROB_NORED/g" $TMP_DIR/template_SG_TYPE_NORED_$COMP_NAME
			sed -i "s/#COMP_RESTART_MAX#/$COMP_RESTART_MAX_NORED/g" $TMP_DIR/template_SG_TYPE_NORED_$COMP_NAME
			sed -i "s/#COMP_RESTART_PROB#/$COMP_RESTART_PROB_NORED/g" $TMP_DIR/template_SG_TYPE_NORED_$COMP_NAME	
			sed -i "s/#SAF_VERSION#/$SAF_VERSION/g" $TMP_DIR/template_SG_TYPE_NORED_$COMP_NAME
			cat $TMP_DIR/template_SG_TYPE_NORED_$COMP_NAME >> $TMP_DIR/final.xml
                        if shallExcludeApp $COMP_NAME; then
                               cp $TEMPLATES_FOLDER/TEMPLATE_BUNDLE/template_end_apg $TMP_DIR/
                               cat $TMP_DIR/template_end_apg >> $TMP_DIR/final.xml
                               rm -f $TMP_DIR/template_end_apg
                        fi
		fi
	done < $TMP_DIR/$SOURCE_FILE_NAME 	
	is_verbose && echo "STEP: SG_TYPE CREATION DONE"
fi

#END Creating SG_BASE_TYPE ============================================================================================================================================================================


#Creating APP_BASE_TYPE============================================================================================================================================================================ò

if [ "$OPT_RESIZE" = "" ] || [ "$OPT_RESIZE_ARG" = "0-1" ] ; then
	cp $TEMPLATES_FOLDER/TEMPLATE_APP_TYPE/template_app_type_init $TMP_DIR/
	sed -i "s/#APP_TYPE#/$APP_TYPE/g" $TMP_DIR/template_app_type_init
	sed -i "s/#SAF_VERSION#/$SAF_VERSION/g" $TMP_DIR/template_app_type_init
	cat $TMP_DIR/template_app_type_init >> $TMP_DIR/final.xml
	cp $TEMPLATES_FOLDER/TEMPLATE_APP_TYPE/template_app_type_group_type_2n $TMP_DIR/
	sed -i "s/#SG_2N_TYPE#/$SG_2N_TYPE/g" $TMP_DIR/template_app_type_group_type_2n
	cat $TMP_DIR/template_app_type_group_type_2n >> $TMP_DIR/final.xml
	while read line    
	do    
		type=$(echo $line | awk -F';' '{print $1}')
		if [ "$type" = "NORED" ] 
		then
			COMP_NAME=$(echo $line | awk -F';' '{print $3}')
			CSI_NAME=$(echo $line | awk -F';' '{print $11}')
                        if shallExcludeApp $COMP_NAME; then
                               cp $TEMPLATES_FOLDER/TEMPLATE_BUNDLE/template_init_apg $TMP_DIR/
                               sed -i "s/#PARAM#/$COMP_NAME/g" $TMP_DIR/template_init_apg
                               sed -i "s/#SCRIPT#/$EXCLUDE_BUNDLES/g" $TMP_DIR/template_init_apg
                               sed -i "s/#TYPE#/$INSTALL_TYPE/g" $TMP_DIR/template_init_apg
                               cat $TMP_DIR/template_init_apg >> $TMP_DIR/final.xml
                               rm -f $TMP_DIR/template_init_apg
                        fi
			cp $TEMPLATES_FOLDER/TEMPLATE_APP_TYPE/template_app_type_group_type_nored $TMP_DIR/template_app_type_group_type_nored_$COMP_NAME	
			sed -i "s/#CSI_NAME#/$CSI_NAME/g" $TMP_DIR/template_app_type_group_type_nored_$COMP_NAME
			cat $TMP_DIR/template_app_type_group_type_nored_$COMP_NAME >> $TMP_DIR/final.xml
                        if shallExcludeApp $COMP_NAME; then
                               cp $TEMPLATES_FOLDER/TEMPLATE_BUNDLE/template_end_apg $TMP_DIR/
                               cat $TMP_DIR/template_end_apg >> $TMP_DIR/final.xml
                               rm -f $TMP_DIR/template_end_apg
                        fi
		fi
	done < $TMP_DIR/$SOURCE_FILE_NAME
	cp $TEMPLATES_FOLDER/TEMPLATE_APP_TYPE/template_app_type_end $TMP_DIR/
	cat $TMP_DIR/template_app_type_end >> $TMP_DIR/final.xml
	is_verbose && echo "STEP: APP_TYPE CREATION DONE"
fi

#END Creating APP_BASE_TYPE ============================================================================================================================================================================


#START Creating CS Type ============================================================================================================================================================================

if [ "$OPT_RESIZE" = "" ] || [ "$OPT_RESIZE_ARG" = "0-1" ] ; then
	while read line    
	do    
		type=$(echo $line | awk -F';' '{print $1}')
		if [ "$type" = "2N" ] || [ "$type" = "NORED" ]
		then
			COMP_NAME=$(echo $line | awk -F';' '{print $3}')
			CS_TYPE=$(echo $line | awk -F';' '{print $6}')
			if [ "$COMP_NAME" = "COMSA" ]; then
			cp $TEMPLATES_FOLDER/TEMPLATE_CS_TYPE/template_CS_type $TMP_DIR/template_CS_type_$COMP_NAME
			sed -i "s/#CS_TYPE#/$CS_TYPE/g" $TMP_DIR/template_CS_type_$COMP_NAME
			cat $TMP_DIR/template_CS_type_$COMP_NAME >> $TMP_DIR/final.xml
			rm -f $TMP_DIR/template_CS_type_$COMP_NAME
	    cp $TEMPLATES_FOLDER/TEMPLATE_CS_TYPE/template_CS_type $TMP_DIR/template_CS_type_sshd
			sed -i "s/#CS_TYPE#/$COMSA_CS_SSHD/g" $TMP_DIR/template_CS_type_sshd		
			cat $TMP_DIR/template_CS_type_sshd >> $TMP_DIR/final.xml
			rm -f $TMP_DIR/template_CS_type_sshd
      cp $TEMPLATES_FOLDER/TEMPLATE_CS_TYPE/template_CS_type $TMP_DIR/template_CS_type_tlsd
      sed -i "s/#CS_TYPE#/$COMSA_CS_TLSD/g" $TMP_DIR/template_CS_type_tlsd
      cat $TMP_DIR/template_CS_type_tlsd >> $TMP_DIR/final.xml
      rm -f $TMP_DIR/template_CS_type_tlsd
      cp $TEMPLATES_FOLDER/TEMPLATE_CS_TYPE/template_CS_type $TMP_DIR/template_CS_type_vsftpd
      sed -i "s/#CS_TYPE#/$COMSA_CS_VSFTPD/g" $TMP_DIR/template_CS_type_vsftpd
      cat $TMP_DIR/template_CS_type_vsftpd >> $TMP_DIR/final.xml
      rm -f $TMP_DIR/template_CS_type_vsftpd

	    		else
                        if shallExcludeApp $COMP_NAME; then
                               cp $TEMPLATES_FOLDER/TEMPLATE_BUNDLE/template_init_apg $TMP_DIR/
                               sed -i "s/#PARAM#/$COMP_NAME/g" $TMP_DIR/template_init_apg
                               sed -i "s/#SCRIPT#/$EXCLUDE_BUNDLES/g" $TMP_DIR/template_init_apg
                               sed -i "s/#TYPE#/$INSTALL_TYPE/g" $TMP_DIR/template_init_apg
                               cat $TMP_DIR/template_init_apg >> $TMP_DIR/final.xml
                               rm -f $TMP_DIR/template_init_apg
                        fi
			cp $TEMPLATES_FOLDER/TEMPLATE_CS_TYPE/template_CS_type $TMP_DIR/template_CS_type_$COMP_NAME
                        sed -i "s/#CS_TYPE#/$CS_TYPE/g" $TMP_DIR/template_CS_type_$COMP_NAME
                        cat $TMP_DIR/template_CS_type_$COMP_NAME >> $TMP_DIR/final.xml
                        rm -f $TMP_DIR/template_CS_type_$COMP_NAME
                        if shallExcludeApp $COMP_NAME; then
                               cp $TEMPLATES_FOLDER/TEMPLATE_BUNDLE/template_end_apg $TMP_DIR/
                               cat $TMP_DIR/template_end_apg >> $TMP_DIR/final.xml
                               rm -f $TMP_DIR/template_end_apg
                        fi
			fi
		fi
	done < $TMP_DIR/$SOURCE_FILE_NAME 
	is_verbose && echo "STEP: CS_TYPE CREATION DONE"
fi

#END Creating CS Type ============================================================================================================================================================================


#START Creating ServiceBaseType ============================================================================================================================================================================

if [ "$OPT_RESIZE" = "" ] || [ "$OPT_RESIZE_ARG" = "0-1" ] ; then
#####
#  SI for 2N
#####
	while read line    
		do    
		type=$(echo $line | awk -F';' '{print $1}')
		if [ "$type" = "2N" ]
			then
			CS_TYPE=$(echo $line | awk -F';' '{print $6}')
			SVC_TYPE=$(echo $line | awk -F';' '{print $10}')
			CSI_NAME=$(echo $line | awk -F';' '{print $11}')
			COMP_NAME=$(echo $line | awk -F';' '{print $3}')
			if [ "$SVC_TYPE" = "COMSA" ]; then
			cp $TEMPLATES_FOLDER/TEMPLATE_SERVICE_BASE_TYPE/template_service_base_type_init $TMP_DIR/template_service_base_type_init_$SVC_TYPE
			cp $TEMPLATES_FOLDER/TEMPLATE_SERVICE_BASE_TYPE/template_service_base_type_end $TMP_DIR/
			sed -i "s/#SAF_VERSION#/$SAF_VERSION/g" $TMP_DIR/template_service_base_type_init_$SVC_TYPE
			sed -i "s/#SAF_SVC_TYPE#/${SVC_TYPE}/g" $TMP_DIR/template_service_base_type_init_$SVC_TYPE
			cat $TMP_DIR/template_service_base_type_init_$SVC_TYPE >> $TMP_DIR/final.xml
			rm -f $TMP_DIR/template_service_base_type_init_$SVC_TYPE
			cp $TEMPLATES_FOLDER/TEMPLATE_SERVICE_BASE_TYPE/template_service_base_type_cs $TMP_DIR/template_service_base_type_cs_$SVC_TYPE			
			sed -i "s/#SAF_VERSION#/$SAF_VERSION/g" $TMP_DIR/template_service_base_type_cs_$SVC_TYPE
			sed -i "s/#CS_TYPE#/$CS_TYPE/g" $TMP_DIR/template_service_base_type_cs_$SVC_TYPE
			cat $TMP_DIR/template_service_base_type_cs_$SVC_TYPE >> $TMP_DIR/final.xml
			rm -f $TMP_DIR/template_service_base_type_cs_$SVC_TYPE
			cp $TEMPLATES_FOLDER/TEMPLATE_SERVICE_BASE_TYPE/template_service_base_type_cs_sshd $TMP_DIR/template_service_base_type_cs_sshd
			sed -i "s/#SAF_VERSION#/$SAF_VERSION/g" $TMP_DIR/template_service_base_type_cs_sshd
			sed -i "s/#CS_SSH_TYPE#/$COMSA_CS_SSHD/g" $TMP_DIR/template_service_base_type_cs_sshd
			cat $TMP_DIR/template_service_base_type_cs_sshd >> $TMP_DIR/final.xml
			rm -f $TMP_DIR/template_service_base_type_cs_sshd
      cp $TEMPLATES_FOLDER/TEMPLATE_SERVICE_BASE_TYPE/template_service_base_type_cs_tlsd $TMP_DIR/template_service_base_type_cs_tlsd
      sed -i "s/#SAF_VERSION#/$SAF_VERSION/g" $TMP_DIR/template_service_base_type_cs_tlsd
      sed -i "s/#CS_TLS_TYPE#/$COMSA_CS_TLSD/g" $TMP_DIR/template_service_base_type_cs_tlsd
      cat $TMP_DIR/template_service_base_type_cs_tlsd >> $TMP_DIR/final.xml
      rm -f $TMP_DIR/template_service_base_type_cs_tlsd
      cp $TEMPLATES_FOLDER/TEMPLATE_SERVICE_BASE_TYPE/template_service_base_type_cs_vsftpd $TMP_DIR/template_service_base_type_cs_vsftpd
      sed -i "s/#SAF_VERSION#/$SAF_VERSION/g" $TMP_DIR/template_service_base_type_cs_vsftpd
      sed -i "s/#CS_VSFTPD_TYPE#/$COMSA_CS_VSFTPD/g" $TMP_DIR/template_service_base_type_cs_vsftpd
      cat $TMP_DIR/template_service_base_type_cs_vsftpd >> $TMP_DIR/final.xml
      cat $TMP_DIR/template_service_base_type_end >> $TMP_DIR/final.xml
      rm -f $TMP_DIR/template_service_base_type_cs_vsftpd
      rm -f $TMP_DIR/template_service_base_type_end
		else
                        if shallExcludeApp $COMP_NAME; then
                               cp $TEMPLATES_FOLDER/TEMPLATE_BUNDLE/template_init_apg $TMP_DIR/
                               sed -i "s/#PARAM#/$COMP_NAME/g" $TMP_DIR/template_init_apg
                               sed -i "s/#SCRIPT#/$EXCLUDE_BUNDLES/g" $TMP_DIR/template_init_apg
                               sed -i "s/#TYPE#/$INSTALL_TYPE/g" $TMP_DIR/template_init_apg
                               cat $TMP_DIR/template_init_apg >> $TMP_DIR/final.xml
                               rm -f $TMP_DIR/template_init_apg
                        fi
			cp $TEMPLATES_FOLDER/TEMPLATE_SERVICE_BASE_TYPE/template_service_base_type_init $TMP_DIR/template_service_base_type_init_$SVC_TYPE
                        cp $TEMPLATES_FOLDER/TEMPLATE_SERVICE_BASE_TYPE/template_service_base_type_end $TMP_DIR/
                        sed -i "s/#SAF_VERSION#/$SAF_VERSION/g" $TMP_DIR/template_service_base_type_init_$SVC_TYPE
                        sed -i "s/#SAF_SVC_TYPE#/${SVC_TYPE}/g" $TMP_DIR/template_service_base_type_init_$SVC_TYPE
                        cat $TMP_DIR/template_service_base_type_init_$SVC_TYPE >> $TMP_DIR/final.xml
                        rm -f $TMP_DIR/template_service_base_type_init_$SVC_TYPE
                        cp $TEMPLATES_FOLDER/TEMPLATE_SERVICE_BASE_TYPE/template_service_base_type_cs $TMP_DIR/template_service_base_type_cs_$SVC_TYPE
                        sed -i "s/#SAF_VERSION#/$SAF_VERSION/g" $TMP_DIR/template_service_base_type_cs_$SVC_TYPE
                        sed -i "s/#CS_TYPE#/$CS_TYPE/g" $TMP_DIR/template_service_base_type_cs_$SVC_TYPE
                        cat $TMP_DIR/template_service_base_type_cs_$SVC_TYPE >> $TMP_DIR/final.xml
                        cat $TMP_DIR/template_service_base_type_end >> $TMP_DIR/final.xml
                        rm -f $TMP_DIR/template_service_base_type_cs_$SVC_TYPE
                        rm -f $TMP_DIR/template_service_base_type_end
                        if shallExcludeApp $COMP_NAME; then
                               cp $TEMPLATES_FOLDER/TEMPLATE_BUNDLE/template_end_apg $TMP_DIR/
                               cat $TMP_DIR/template_end_apg >> $TMP_DIR/final.xml
                               rm -f $TMP_DIR/template_end_apg
                        fi
			fi
		fi
	done < $TMP_DIR/$SOURCE_FILE_NAME 
			
#####
#  SI for NORED
#####
	while read line    
		do    
		type=$(echo $line | awk -F';' '{print $1}')
		if [ "$type" = "NORED" ]
			then
			CS_TYPE=$(echo $line | awk -F';' '{print $6}')
			SVC_TYPE=$(echo $line | awk -F';' '{print $10}')
			CSI_NAME=$(echo $line | awk -F';' '{print $11}')
			COMP_NAME=$(echo $line | awk -F';' '{print $3}')
                        if shallExcludeApp $COMP_NAME; then
                               cp $TEMPLATES_FOLDER/TEMPLATE_BUNDLE/template_init_apg $TMP_DIR/
                               sed -i "s/#PARAM#/$COMP_NAME/g" $TMP_DIR/template_init_apg
                               sed -i "s/#SCRIPT#/$EXCLUDE_BUNDLES/g" $TMP_DIR/template_init_apg
                               sed -i "s/#TYPE#/$INSTALL_TYPE/g" $TMP_DIR/template_init_apg
                               cat $TMP_DIR/template_init_apg >> $TMP_DIR/final.xml
                               rm -f $TMP_DIR/template_init_apg
                        fi
			cp $TEMPLATES_FOLDER/TEMPLATE_SERVICE_BASE_TYPE/template_service_base_type_init_nored $TMP_DIR/template_service_base_type_init_nored_$SVC_TYPE
			cp $TEMPLATES_FOLDER/TEMPLATE_SERVICE_BASE_TYPE/template_service_base_type_end $TMP_DIR/
			sed -i "s/#SAF_VERSION#/$SAF_VERSION/g" $TMP_DIR/template_service_base_type_init_nored_$SVC_TYPE
			sed -i "s/#CSI_NAME#/${CSI_NAME}/g" $TMP_DIR/template_service_base_type_init_nored_$SVC_TYPE
			cat $TMP_DIR/template_service_base_type_init_nored_$SVC_TYPE >> $TMP_DIR/final.xml
			cp $TEMPLATES_FOLDER/TEMPLATE_SERVICE_BASE_TYPE/template_service_base_type_cs $TMP_DIR/template_service_base_type_cs_$SVC_TYPE		
			sed -i "s/#SAF_VERSION#/$SAF_VERSION/g" $TMP_DIR/template_service_base_type_cs_$SVC_TYPE
			sed -i "s/#CS_TYPE#/$CS_TYPE/g" $TMP_DIR/template_service_base_type_cs_$SVC_TYPE
			cat $TMP_DIR/template_service_base_type_cs_$SVC_TYPE >> $TMP_DIR/final.xml
			cat $TMP_DIR/template_service_base_type_end >> $TMP_DIR/final.xml
			rm -f $TMP_DIR/template_service_base_type_cs_$SVC_TYPE
			rm -f $TMP_DIR/template_service_base_type_end
                        if shallExcludeApp $COMP_NAME; then
                               cp $TEMPLATES_FOLDER/TEMPLATE_BUNDLE/template_end_apg $TMP_DIR/
                               cat $TMP_DIR/template_end_apg >> $TMP_DIR/final.xml
                               rm -f $TMP_DIR/template_end_apg
                        fi
		fi
	done < $TMP_DIR/$SOURCE_FILE_NAME
	is_verbose && echo "STEP: Service_Base_TYPE CREATION DONE"
fi

#END Creating ServiceBaseType =============================================================================================================================================================================

#START Creating LDE Type part ========================================================================================================================================================================

if [ "$OPT_RESIZE" = "" ] || [ "$OPT_RESIZE_ARG" = "0-1" ] ; then
        cp $TEMPLATES_FOLDER/TEMPLATE_LDE/template_lde_type $TMP_DIR/
        sed -i "s/#LDE_BUNDLE#/$LDE_BUNDLE/g" $TMP_DIR/template_lde_type
        sed -i "s/#LDE_PMCOUNTER_RSTATE#/$LDE_PMCOUNTER_RSTATE/g" $TMP_DIR/template_lde_type
        sed -i "s/#LDE_CFSMONITOR_RSTATE#/$LDE_CFSMONITOR_RSTATE/g" $TMP_DIR/template_lde_type
        sed -i "s/#LDE_BONDMONITOR_RSTATE#/$LDE_BONDMONITOR_RSTATE/g" $TMP_DIR/template_lde_type
        sed -i "s/#LDE_CONFIG_RSTATE#/$LDE_CONFIG_RSTATE/g" $TMP_DIR/template_lde_type
        cat $TMP_DIR/template_lde_type >> $TMP_DIR/final.xml
        rm -f $TMP_DIR/template_lde_type
        is_verbose && echo "STEP: LDE_TYPE CREATION DONE"
fi

#END Creating ServiceBaseType =============================================================================================================================================================================

#START Creating BRF LDE Type part ====================================================================================================================================================================

if [ "$OPT_RESIZE" = "" ] || [ "$OPT_RESIZE_ARG" = "0-1" ] ; then
	cp $TEMPLATES_FOLDER/TEMPLATE_BRF/template_brf_lde_type $TMP_DIR/
	sed -i "s/#BRFLDE_BUNDLE#/$BRFLDE_BUNDLE/g" $TMP_DIR/template_brf_lde_type
	sed -i "s/#BRFLDE_RSTATE#/$BRFLDE_RSTATE/g" $TMP_DIR/template_brf_lde_type
	cat $TMP_DIR/template_brf_lde_type >> $TMP_DIR/final.xml
	rm -f $TMP_DIR/template_brf_lde_type
	is_verbose && echo "STEP: BRF_TYPE CREATION DONE"
fi

#END Creating BRF LDE Type part ====================================================================================================================================================================


#START Creating BRF Type part ====================================================================================================================================================================

if [ "$OPT_RESIZE" = "" ] || [ "$OPT_RESIZE_ARG" = "0-1" ] ; then
	cp $TEMPLATES_FOLDER/TEMPLATE_BRF/template_brf_type $TMP_DIR/
	sed -i "s/#BRF_BUNDLE#/$BRF_BUNDLE/g" $TMP_DIR/template_brf_type
	sed -i "s/#BRF_RSTATE#/$BRF_RSTATE/g" $TMP_DIR/template_brf_type
	sed -i "s/#BRFCMW_BUNDLE#/$BRFCMW_BUNDLE/g" $TMP_DIR/template_brf_type
	sed -i "s/#BRFCMW_RSTATE#/$BRFCMW_RSTATE/g" $TMP_DIR/template_brf_type
	sed -i "s/#BRFP_BUNDLE#/$BRFP_BUNDLE/g" $TMP_DIR/template_brf_type
	sed -i "s/#BRFP_RSTATE#/$BRFP_RSTATE/g" $TMP_DIR/template_brf_type
	cat $TMP_DIR/template_brf_type >> $TMP_DIR/final.xml
	rm -f $TMP_DIR/template_brf_type
	is_verbose && echo "STEP: BRF_TYPE CREATION DONE"
fi

#END Creating BRF Type part ====================================================================================================================================================================

#START Creating SEC ACS Type part ====================================================================================================================================================================

if [ "$OPT_RESIZE" = "" ] || [ "$OPT_RESIZE_ARG" = "0-1" ] ; then
        cp $TEMPLATES_FOLDER/TEMPLATE_SEC/template_sec_acs_type $TMP_DIR/
        sed -i "s/#SEC_ACS_BUNDLE#/$SEC_ACS_BUNDLE/g" $TMP_DIR/template_sec_acs_type
        sed -i "s/#SEC_ACS_RSTATE#/$SEC_ACS_RSTATE/g" $TMP_DIR/template_sec_acs_type
        cat $TMP_DIR/template_sec_acs_type >> $TMP_DIR/final.xml
        rm -f $TMP_DIR/template_sec_acs_type
        is_verbose && echo "STEP: SEC_ACS_TYPE CREATION DONE"
fi

#END Creating SEC ACS Type part ====================================================================================================================================================================

#START Creating SEC LA Type part ====================================================================================================================================================================

if [ "$OPT_RESIZE" = "" ] || [ "$OPT_RESIZE_ARG" = "0-1" ] ; then
        cp $TEMPLATES_FOLDER/TEMPLATE_SEC/template_sec_la_type $TMP_DIR/
        sed -i "s/#SEC_LA_OI_BUNDLE#/$SEC_LA_OI_BUNDLE/g" $TMP_DIR/template_sec_la_type
        sed -i "s/#SEC_LA_OI_RSTATE#/$SEC_LA_OI_RSTATE/g" $TMP_DIR/template_sec_la_type
        sed -i "s/#SEC_LA_LDAP_BUNDLE#/$SEC_LA_LDAP_BUNDLE/g" $TMP_DIR/template_sec_la_type
        sed -i "s/#SEC_LA_LDAP_RSTATE#/$SEC_LA_LDAP_RSTATE/g" $TMP_DIR/template_sec_la_type
	cat $TMP_DIR/template_sec_la_type >> $TMP_DIR/final.xml
        rm -f $TMP_DIR/template_sec_la_type
        is_verbose && echo "STEP: SEC_LA_TYPE CREATION DONE"
fi

#END Creating SEC LA Type part ====================================================================================================================================================================


#START Creating SEC SECM Type part ====================================================================================================================================================================

if [ "$OPT_RESIZE" = "" ] || [ "$OPT_RESIZE_ARG" = "0-1" ] ; then
        cp $TEMPLATES_FOLDER/TEMPLATE_SEC/template_sec_secm_type $TMP_DIR/
        sed -i "s/#SEC_SECM_BUNDLE#/$SEC_SECM_BUNDLE/g" $TMP_DIR/template_sec_secm_type
        sed -i "s/#SEC_SECM_RSTATE#/$SEC_SECM_RSTATE/g" $TMP_DIR/template_sec_secm_type
  cat $TMP_DIR/template_sec_secm_type >> $TMP_DIR/final.xml
        rm -f $TMP_DIR/template_sec_secm_type
        is_verbose && echo "STEP: SEC_SECM_TYPE CREATION DONE"
fi

#END Creating SEC SECM Type part ====================================================================================================================================================================


#START Creating SEC LDAP Type part ====================================================================================================================================================================

if [ "$OPT_RESIZE" = "" ] || [ "$OPT_RESIZE_ARG" = "0-1" ] ; then
        cp $TEMPLATES_FOLDER/TEMPLATE_SEC/template_sec_ldap_type $TMP_DIR/
        sed -i "s/#SEC_LDAP_SM_BUNDLE#/$SEC_LDAP_SM_BUNDLE/g" $TMP_DIR/template_sec_ldap_type
        sed -i "s/#SEC_LDAP_BUNDLE#/$SEC_LDAP_BUNDLE/g" $TMP_DIR/template_sec_ldap_type
        sed -i "s/#SEC_LDAP_RSTATE#/$SEC_LDAP_RSTATE/g" $TMP_DIR/template_sec_ldap_type
        cat $TMP_DIR/template_sec_ldap_type >> $TMP_DIR/final.xml
        rm -f $TMP_DIR/template_sec_ldap_type
        is_verbose && echo "STEP: SEC_LDAP_TYPE CREATION DONE"
fi

#END Creating SEC LDAP Type part ====================================================================================================================================================================

#START Creating SEC SECM part ====================================================================================================================================================================
if [ "$OPT_RESIZE" = "" ]; then
        echo "             </amfEntityTypes>" >> $TMP_DIR/final.xml
        cp $TEMPLATES_FOLDER/TEMPLATE_SEC/template_sec_secm $TMP_DIR/
        sed -i "s/#SEC_SECM_BUNDLE#/$SEC_SECM_BUNDLE/g" $TMP_DIR/template_sec_secm
        sed -i "s/#SEC_SECM_RSTATE#/$SEC_SECM_RSTATE/g" $TMP_DIR/template_sec_secm
        sed -i "s/#SEC_SECM_LN_BUNDLE#/$SEC_SECM_LN_BUNDLE/g" $TMP_DIR/template_sec_secm

        cat $TMP_DIR/template_sec_secm >> $TMP_DIR/final.xml
        rm -f $TMP_DIR/template_sec_secm
elif [ "$OPT_RESIZE_ARG" = "0-1" ] ; then
        echo "                  </amfEntityTypes>" >> $TMP_DIR/final.xml
        cp $TEMPLATES_FOLDER/TEMPLATE_SEC/template_sec_secm_0_1 $TMP_DIR/
        sed -i "s/#SEC_SECM_BUNDLE#/$SEC_SECM_BUNDLE/g" $TMP_DIR/template_sec_secm_0_1
        sed -i "s/#SEC_SECM_RSTATE#/$SEC_SECM_RSTATE/g" $TMP_DIR/template_sec_secm_0_1
        sed -i "s/#SEC_SECM_LN_BUNDLE#/$SEC_SECM_LN_BUNDLE/g" $TMP_DIR/template_sec_secm_0_1

        cat $TMP_DIR/template_sec_secm_0_1 >> $TMP_DIR/final.xml
        rm -f $TMP_DIR/template_sec_secm_0_1
elif [ "$OPT_RESIZE_ARG" = "1-2" ] ; then
        cp $TEMPLATES_FOLDER/TEMPLATE_SEC/template_sec_secm_1_2 $TMP_DIR/
        sed -i "s/#SEC_SECM_BUNDLE#/$SEC_SECM_BUNDLE/g" $TMP_DIR/template_sec_secm_1_2
        sed -i "s/#SEC_SECM_RSTATE#/$SEC_SECM_RSTATE/g" $TMP_DIR/template_sec_secm_1_2
        sed -i "s/#SEC_SECM_LN_BUNDLE#/$SEC_SECM_LN_BUNDLE/g" $TMP_DIR/template_sec_secm_1_2

        cat $TMP_DIR/template_sec_secm_1_2 >> $TMP_DIR/final.xml
        rm -f $TMP_DIR/template_sec_secm_1_2
fi
is_verbose && echo "STEP: SEC SECM CREATION DONE"

#END Creating SEC SECM part ======================================================================================================================================================================


#START Creating COM - COMSA part ====================================================================================================================================================================

if [ "$OPT_RESIZE" = "" ] || [ "$OPT_RESIZE_ARG" = "0-1" ]; then
	cp $TEMPLATES_FOLDER/TEMPLATE_COM_COMSA/template_com_comsa $TMP_DIR/
	sed -i "s/#COM_BUNDLE#/$COM_BUNDLE/g" $TMP_DIR/template_com_comsa
	sed -i "s/#COM_PATH#/$COM_PATH/g" $TMP_DIR/template_com_comsa
	if [ "$OPT_RESIZE_ARG" = "0-1" ] ; then
		sed -i "s/^.*SC-2.*$//g"  $TMP_DIR/template_com_comsa
		sed -i '/^$/d' $TMP_DIR/template_com_comsa
	fi
	cat $TMP_DIR/template_com_comsa >> $TMP_DIR/final.xml
	rm -f $TMP_DIR/template_com_comsa
elif [ "$OPT_RESIZE_ARG" = "1-2" ] ; then
	cp $TEMPLATES_FOLDER/TEMPLATE_COM_COMSA/template_com_comsa_resize $TMP_DIR/
	sed -i "s/#COM_BUNDLE#/$COM_BUNDLE/g" $TMP_DIR/template_com_comsa_resize
	sed -i "s/#COM_PATH#/$COM_PATH/g" $TMP_DIR/template_com_comsa_resize
	sed -i "s/^.*SC-1.*$//g"  $TMP_DIR/template_com_comsa_resize
	sed -i '/^$/d' $TMP_DIR/template_com_comsa_resize
	cat $TMP_DIR/template_com_comsa_resize >> $TMP_DIR/final.xml
	rm -f $TMP_DIR/template_com_comsa_resize
fi
is_verbose && echo "STEP: COM_COMSA CREATION DONE"

#END Creating COM - COMSA part ====================================================================================================================================================================


#START Creating LDE adaptation part ==================================================================================================================================================================

if [ "$OPT_RESIZE" = "" ]; then
	cp $TEMPLATES_FOLDER/TEMPLATE_LDE/template_lde $TMP_DIR/
	sed -i "s/#LDE_BUNDLE#/$LDE_BUNDLE/g" $TMP_DIR/template_lde
	sed -i "s/#LDE_PMCOUNTER_RSTATE#/$LDE_PMCOUNTER_RSTATE/g" $TMP_DIR/template_lde
	sed -i "s/#LDE_CFSMONITOR_RSTATE#/$LDE_CFSMONITOR_RSTATE/g" $TMP_DIR/template_lde
  sed -i "s/#LDE_CONFIG_RSTATE#/$LDE_CONFIG_RSTATE/g" $TMP_DIR/template_lde
	cat $TMP_DIR/template_lde >> $TMP_DIR/final.xml
	rm -f $TMP_DIR/template_lde
elif [ "$OPT_RESIZE_ARG" = "0-1" ] ; then
	cp $TEMPLATES_FOLDER/TEMPLATE_LDE/template_lde_0_1 $TMP_DIR/
	sed -i "s/#LDE_BUNDLE#/$LDE_BUNDLE/g" $TMP_DIR/template_lde_0_1
	sed -i "s/#LDE_PMCOUNTER_RSTATE#/$LDE_PMCOUNTER_RSTATE/g" $TMP_DIR/template_lde_0_1
	sed -i "s/#LDE_CFSMONITOR_RSTATE#/$LDE_CFSMONITOR_RSTATE/g" $TMP_DIR/template_lde_0_1
  sed -i "s/#LDE_CONFIG_RSTATE#/$LDE_CONFIG_RSTATE/g" $TMP_DIR/template_lde_0_1
	cat $TMP_DIR/template_lde_0_1 >> $TMP_DIR/final.xml
	rm -f $TMP_DIR/template_lde_0_1
elif [ "$OPT_RESIZE_ARG" = "1-2" ] ; then
	cp $TEMPLATES_FOLDER/TEMPLATE_LDE/template_lde_1_2 $TMP_DIR/
	sed -i "s/#LDE_BUNDLE#/$LDE_BUNDLE/g" $TMP_DIR/template_lde_1_2
	sed -i "s/#LDE_PMCOUNTER_RSTATE#/$LDE_PMCOUNTER_RSTATE/g" $TMP_DIR/template_lde_1_2
	sed -i "s/#LDE_CFSMONITOR_RSTATE#/$LDE_CFSMONITOR_RSTATE/g" $TMP_DIR/template_lde_1_2
  sed -i "s/#LDE_CONFIG_RSTATE#/$LDE_CONFIG_RSTATE/g" $TMP_DIR/template_lde_1_2
	cat $TMP_DIR/template_lde_1_2 >> $TMP_DIR/final.xml
	rm -f $TMP_DIR/template_lde_1_2
fi
is_verbose && echo "STEP: LDE ADAPTATION CREATION DONE"

#END Creating LDE adaptation part=====================================================================================================================================================================


#START Creating BRF LDE part ====================================================================================================================================================================

if [ "$OPT_RESIZE" = "" ]; then
	cp $TEMPLATES_FOLDER/TEMPLATE_BRF/template_brf_lde $TMP_DIR/
	sed -i "s/#BRFLDE_BUNDLE#/$BRFLDE_BUNDLE/g" $TMP_DIR/template_brf_lde
	sed -i "s/#BRFLDE_RSTATE#/$BRFLDE_RSTATE/g" $TMP_DIR/template_brf_lde
	cat $TMP_DIR/template_brf_lde >> $TMP_DIR/final.xml
	rm -f $TMP_DIR/template_brf_lde
elif [ "$OPT_RESIZE_ARG" = "0-1" ] ; then
	cp $TEMPLATES_FOLDER/TEMPLATE_BRF/template_brf_lde_0_1 $TMP_DIR/
	sed -i "s/#BRFLDE_BUNDLE#/$BRFLDE_BUNDLE/g" $TMP_DIR/template_brf_lde_0_1
	sed -i "s/#BRFLDE_RSTATE#/$BRFLDE_RSTATE/g" $TMP_DIR/template_brf_lde_0_1
	cat $TMP_DIR/template_brf_lde_0_1 >> $TMP_DIR/final.xml	
elif [ "$OPT_RESIZE_ARG" = "1-2" ] ; then
	cp $TEMPLATES_FOLDER/TEMPLATE_BRF/template_brf_lde_1_2 $TMP_DIR/
	sed -i "s/#BRFLDE_BUNDLE#/$BRFLDE_BUNDLE/g" $TMP_DIR/template_brf_lde_1_2
	sed -i "s/#BRFLDE_RSTATE#/$BRFLDE_RSTATE/g" $TMP_DIR/template_brf_lde_1_2
	cat $TMP_DIR/template_brf_lde_1_2 >> $TMP_DIR/final.xml
fi
is_verbose && echo "STEP: BRF LDE CREATION DONE"

#END Creating BRF LDE part ====================================================================================================================================================================


#START Creating BRF part ====================================================================================================================================================================

if [ "$OPT_RESIZE" = "" ]; then
	cp $TEMPLATES_FOLDER/TEMPLATE_BRF/template_brf $TMP_DIR/
	sed -i "s/#BRF_BUNDLE#/$BRF_BUNDLE/g" $TMP_DIR/template_brf
	sed -i "s/#BRF_RSTATE#/$BRF_RSTATE/g" $TMP_DIR/template_brf
	sed -i "s/#BRFCMW_BUNDLE#/$BRFCMW_BUNDLE/g" $TMP_DIR/template_brf
	sed -i "s/#BRFCMW_RSTATE#/$BRFCMW_RSTATE/g" $TMP_DIR/template_brf
	sed -i "s/#BRFP_BUNDLE#/$BRFP_BUNDLE/g" $TMP_DIR/template_brf
	sed -i "s/#BRFP_RSTATE#/$BRFP_RSTATE/g" $TMP_DIR/template_brf
	cat $TMP_DIR/template_brf >> $TMP_DIR/final.xml
elif [ "$OPT_RESIZE_ARG" = "0-1" ] ; then
	cp $TEMPLATES_FOLDER/TEMPLATE_BRF/template_brf_0_1 $TMP_DIR/
	sed -i "s/#BRF_BUNDLE#/$BRF_BUNDLE/g" $TMP_DIR/template_brf_0_1
	sed -i "s/#BRF_RSTATE#/$BRF_RSTATE/g" $TMP_DIR/template_brf_0_1
	sed -i "s/#BRFCMW_BUNDLE#/$BRFCMW_BUNDLE/g" $TMP_DIR/template_brf_0_1
	sed -i "s/#BRFCMW_RSTATE#/$BRFCMW_RSTATE/g" $TMP_DIR/template_brf_0_1
	sed -i "s/#BRFP_BUNDLE#/$BRFP_BUNDLE/g" $TMP_DIR/template_brf_0_1
    sed -i "s/#BRFP_RSTATE#/$BRFP_RSTATE/g" $TMP_DIR/template_brf_0_1
	cat $TMP_DIR/template_brf_0_1 >> $TMP_DIR/final.xml	
elif [ "$OPT_RESIZE_ARG" = "1-2" ] ; then
	cp $TEMPLATES_FOLDER/TEMPLATE_BRF/template_brf_1_2 $TMP_DIR/
	sed -i "s/#BRF_BUNDLE#/$BRF_BUNDLE/g" $TMP_DIR/template_brf_1_2
	sed -i "s/#BRF_RSTATE#/$BRF_RSTATE/g" $TMP_DIR/template_brf_1_2
	sed -i "s/#BRFCMW_BUNDLE#/$BRFCMW_BUNDLE/g" $TMP_DIR/template_brf_1_2
	sed -i "s/#BRFCMW_RSTATE#/$BRFCMW_RSTATE/g" $TMP_DIR/template_brf_1_2
	sed -i "s/#BRFP_BUNDLE#/$BRFP_BUNDLE/g" $TMP_DIR/template_brf_1_2
        sed -i "s/#BRFP_RSTATE#/$BRFP_RSTATE/g" $TMP_DIR/template_brf_1_2
	cat $TMP_DIR/template_brf_1_2 >> $TMP_DIR/final.xml
fi	
is_verbose && echo "STEP: BRF CREATION DONE"

#END Creating BRF part ====================================================================================================================================================================

#START Creating BRFEIA part ====================================================================================================================================================================
if [ "$OPT_RESIZE" = "" ]; then
	cp $TEMPLATES_FOLDER/TEMPLATE_BRF/template_brfe $TMP_DIR/
	sed -i "s/#BRFEIA_BUNDLE#/$BRFEIA_BUNDLE/g" $TMP_DIR/template_brfe
	cat $TMP_DIR/template_brfe >> $TMP_DIR/final.xml
	rm -f $TMP_DIR/template_brfe
elif [ "$OPT_RESIZE_ARG" = "0-1" ] ; then
	cp $TEMPLATES_FOLDER/TEMPLATE_BRF/template_brfe_0_1 $TMP_DIR/
	sed -i "s/#BRFEIA_BUNDLE#/$BRFEIA_BUNDLE/g" $TMP_DIR/template_brfe_0_1
	cat $TMP_DIR/template_brfe_0_1 >> $TMP_DIR/final.xml	
elif [ "$OPT_RESIZE_ARG" = "1-2" ] ; then
	cp $TEMPLATES_FOLDER/TEMPLATE_BRF/template_brfe_1_2 $TMP_DIR/
	sed -i "s/#BRFEIA_BUNDLE#/$BRFEIA_BUNDLE/g" $TMP_DIR/template_brfe_1_2
	cat $TMP_DIR/template_brfe_1_2 >> $TMP_DIR/final.xml
fi
is_verbose && echo "STEP: BRFEIA CREATION DONE"

#START Creating SEC part ====================================================================================================================================================================

if [ "$OPT_RESIZE" = "" ]; then
	cp $TEMPLATES_FOLDER/TEMPLATE_SEC/template_sec_upgrade_procedure $TMP_DIR/template_sec_upgrade_procedure
	sed -i "s/#SEC_CRYPTO_BUNDLE#/$SEC_CRYPTO_BUNDLE/g" $TMP_DIR/template_sec_upgrade_procedure
	sed -i "s/#SEC_BUNDLE#/$SEC_BUNDLE/g" $TMP_DIR/template_sec_upgrade_procedure
	sed -i "s/#SEC_AGENT_BUNDLE#/$SEC_AGENT_BUNDLE/g" $TMP_DIR/template_sec_upgrade_procedure
	cat $TMP_DIR/template_sec_upgrade_procedure >> $TMP_DIR/final.xml
	rm -f $TMP_DIR/template_sec_upgrade_procedure
elif [ "$OPT_RESIZE_ARG" = "0-1" ] ; then
	cp $TEMPLATES_FOLDER/TEMPLATE_SEC/template_sec_upgrade_procedure_resize_0_1 $TMP_DIR/template_sec_upgrade_procedure_resize_0_1
	sed -i "s/#SEC_CRYPTO_BUNDLE#/$SEC_CRYPTO_BUNDLE/g" $TMP_DIR/template_sec_upgrade_procedure_resize_0_1
	sed -i "s/#SEC_BUNDLE#/$SEC_BUNDLE/g" $TMP_DIR/template_sec_upgrade_procedure_resize_0_1
	sed -i "s/#SEC_AGENT_BUNDLE#/$SEC_AGENT_BUNDLE/g" $TMP_DIR/template_sec_upgrade_procedure_resize_0_1
	cat $TMP_DIR/template_sec_upgrade_procedure_resize_0_1 >> $TMP_DIR/final.xml
	rm -f $TMP_DIR/template_sec_upgrade_procedure_resize_0_1
elif [ "$OPT_RESIZE_ARG" = "1-2" ] ; then
	cp $TEMPLATES_FOLDER/TEMPLATE_SEC/template_sec_upgrade_procedure_resize_1_2 $TMP_DIR/template_sec_upgrade_procedure_resize_1_2
	sed -i "s/#SEC_CRYPTO_BUNDLE#/$SEC_CRYPTO_BUNDLE/g" $TMP_DIR/template_sec_upgrade_procedure_resize_1_2
	sed -i "s/#SEC_BUNDLE#/$SEC_BUNDLE/g" $TMP_DIR/template_sec_upgrade_procedure_resize_1_2
	sed -i "s/#SEC_AGENT_BUNDLE#/$SEC_AGENT_BUNDLE/g" $TMP_DIR/template_sec_upgrade_procedure_resize_1_2
	cat $TMP_DIR/template_sec_upgrade_procedure_resize_1_2 >> $TMP_DIR/final.xml
	rm -f $TMP_DIR/template_sec_upgrade_procedure_resize_1_2
fi
is_verbose && echo "STEP: SEC CREATION DONE"	
	
#END Creating SEC part ======================================================================================================================================================================

#START Creating SEC ACS part ====================================================================================================================================================================

if [ "$OPT_RESIZE" = "" ]; then
        cp $TEMPLATES_FOLDER/TEMPLATE_SEC/template_sec_acs $TMP_DIR/template_sec_acs
        sed -i "s/#SEC_ACS_BUNDLE#/$SEC_ACS_BUNDLE/g" $TMP_DIR/template_sec_acs
        sed -i "s/#SEC_ACS_RSTATE#/$SEC_ACS_RSTATE/g" $TMP_DIR/template_sec_acs
        cat $TMP_DIR/template_sec_acs >> $TMP_DIR/final.xml
        rm -f $TMP_DIR/template_sec_acs
elif [ "$OPT_RESIZE_ARG" = "0-1" ] ; then
        cp $TEMPLATES_FOLDER/TEMPLATE_SEC/template_sec_acs_0_1 $TMP_DIR/template_sec_acs_0_1
        sed -i "s/#SEC_ACS_BUNDLE#/$SEC_ACS_BUNDLE/g" $TMP_DIR/template_sec_acs_0_1
        sed -i "s/#SEC_ACS_RSTATE#/$SEC_ACS_RSTATE/g" $TMP_DIR/template_sec_acs_0_1
        cat $TMP_DIR/template_sec_acs_0_1 >> $TMP_DIR/final.xml
        rm -f $TMP_DIR/template_sec_acs_0_1
elif [ "$OPT_RESIZE_ARG" = "1-2" ] ; then
        cp $TEMPLATES_FOLDER/TEMPLATE_SEC/template_sec_acs_1_2 $TMP_DIR/template_sec_acs_1_2
        sed -i "s/#SEC_ACS_BUNDLE#/$SEC_ACS_BUNDLE/g" $TMP_DIR/template_sec_acs_1_2
        sed -i "s/#SEC_ACS_RSTATE#/$SEC_ACS_RSTATE/g" $TMP_DIR/template_sec_acs_1_2
        cat $TMP_DIR/template_sec_acs_1_2 >> $TMP_DIR/final.xml
        rm -f $TMP_DIR/template_sec_acs_1_2
fi
is_verbose && echo "STEP: SEC ACS CREATION DONE"

#END Creating SEC ACS part ======================================================================================================================================================================

#START Creating SEC LA part ====================================================================================================================================================================

if [ "$OPT_RESIZE" = "" ]; then
        cp $TEMPLATES_FOLDER/TEMPLATE_SEC/template_sec_la $TMP_DIR/template_sec_la
        sed -i "s/#SEC_LA_LDAP_BUNDLE#/$SEC_LA_LDAP_BUNDLE/g" $TMP_DIR/template_sec_la
        sed -i "s/#SEC_LA_LDAP_RSTATE#/$SEC_LA_LDAP_RSTATE/g" $TMP_DIR/template_sec_la
        sed -i "s/#SEC_LA_OI_BUNDLE#/$SEC_LA_OI_BUNDLE/g" $TMP_DIR/template_sec_la
        sed -i "s/#SEC_LA_OI_RSTATE#/$SEC_LA_OI_RSTATE/g" $TMP_DIR/template_sec_la
        sed -i "s/#SEC_LA_SM_BUNDLE#/$SEC_LA_SM_BUNDLE/g" $TMP_DIR/template_sec_la
        cat $TMP_DIR/template_sec_la >> $TMP_DIR/final.xml
        rm -f $TMP_DIR/template_sec_la
elif [ "$OPT_RESIZE_ARG" = "0-1" ] ; then
        cp $TEMPLATES_FOLDER/TEMPLATE_SEC/template_sec_la_0_1 $TMP_DIR/template_sec_la_0_1
        sed -i "s/#SEC_LA_LDAP_BUNDLE#/$SEC_LA_LDAP_BUNDLE/g" $TMP_DIR/template_sec_la_0_1
        sed -i "s/#SEC_LA_LDAP_RSTATE#/$SEC_LA_LDAP_RSTATE/g" $TMP_DIR/template_sec_la_0_1
        sed -i "s/#SEC_LA_OI_BUNDLE#/$SEC_LA_OI_BUNDLE/g" $TMP_DIR/template_sec_la_0_1
        sed -i "s/#SEC_LA_OI_RSTATE#/$SEC_LA_OI_RSTATE/g" $TMP_DIR/template_sec_la_0_1
        sed -i "s/#SEC_LA_SM_BUNDLE#/$SEC_LA_SM_BUNDLE/g" $TMP_DIR/template_sec_la_0_1
        cat $TMP_DIR/template_sec_la_0_1 >> $TMP_DIR/final.xml
        rm -f $TMP_DIR/template_sec_la_0_1
elif [ "$OPT_RESIZE_ARG" = "1-2" ] ; then
        cp $TEMPLATES_FOLDER/TEMPLATE_SEC/template_sec_la_1_2 $TMP_DIR/template_sec_la_1_2
        sed -i "s/#SEC_LA_LDAP_BUNDLE#/$SEC_LA_LDAP_BUNDLE/g" $TMP_DIR/template_sec_la_1_2
        sed -i "s/#SEC_LA_LDAP_RSTATE#/$SEC_LA_LDAP_RSTATE/g" $TMP_DIR/template_sec_la_1_2
        sed -i "s/#SEC_LA_OI_BUNDLE#/$SEC_LA_OI_BUNDLE/g" $TMP_DIR/template_sec_la_1_2
        sed -i "s/#SEC_LA_OI_RSTATE#/$SEC_LA_OI_RSTATE/g" $TMP_DIR/template_sec_la_1_2
        sed -i "s/#SEC_LA_SM_BUNDLE#/$SEC_LA_SM_BUNDLE/g" $TMP_DIR/template_sec_la_1_2
        cat $TMP_DIR/template_sec_la_1_2 >> $TMP_DIR/final.xml
        rm -f $TMP_DIR/template_sec_la_1_2
fi
is_verbose && echo "STEP: SEC LA CREATION DONE"

#END Creating SEC LA part ================================================================================


#START Creating SEC LDAP part ====================================================================================================================================================================

if [ "$OPT_RESIZE" = "" ]; then
        cp $TEMPLATES_FOLDER/TEMPLATE_SEC/template_sec_ldap $TMP_DIR/template_sec_ldap
        sed -i "s/#SEC_LDAP_SM_BUNDLE#/$SEC_LDAP_SM_BUNDLE/g" $TMP_DIR/template_sec_ldap
        sed -i "s/#SEC_LDAP_BUNDLE#/$SEC_LDAP_BUNDLE/g" $TMP_DIR/template_sec_ldap
        sed -i "s/#SEC_LDAP_RSTATE#/$SEC_LDAP_RSTATE/g" $TMP_DIR/template_sec_ldap
        cat $TMP_DIR/template_sec_ldap >> $TMP_DIR/final.xml
        rm -f $TMP_DIR/template_sec_ldap
elif [ "$OPT_RESIZE_ARG" = "0-1" ] ; then
        cp $TEMPLATES_FOLDER/TEMPLATE_SEC/template_sec_ldap_0_1 $TMP_DIR/template_sec_ldap_0_1
        sed -i "s/#SEC_LDAP_SM_BUNDLE#/$SEC_LDAP_SM_BUNDLE/g" $TMP_DIR/template_sec_ldap_0_1
        sed -i "s/#SEC_LDAP_BUNDLE#/$SEC_LDAP_BUNDLE/g" $TMP_DIR/template_sec_ldap_0_1
        sed -i "s/#SEC_LDAP_RSTATE#/$SEC_LDAP_RSTATE/g" $TMP_DIR/template_sec_ldap_0_1
        cat $TMP_DIR/template_sec_ldap_0_1 >> $TMP_DIR/final.xml
        rm -f $TMP_DIR/template_sec_ldap_0_1
elif [ "$OPT_RESIZE_ARG" = "1-2" ] ; then
        cp $TEMPLATES_FOLDER/TEMPLATE_SEC/template_sec_ldap_1_2 $TMP_DIR/template_sec_ldap_1_2
        sed -i "s/#SEC_LDAP_SM_BUNDLE#/$SEC_LDAP_SM_BUNDLE/g" $TMP_DIR/template_sec_ldap_1_2
        sed -i "s/#SEC_LDAP_BUNDLE#/$SEC_LDAP_BUNDLE/g" $TMP_DIR/template_sec_ldap_1_2
        sed -i "s/#SEC_LDAP_RSTATE#/$SEC_LDAP_RSTATE/g" $TMP_DIR/template_sec_ldap_1_2
        cat $TMP_DIR/template_sec_ldap_1_2 >> $TMP_DIR/final.xml
        rm -f $TMP_DIR/template_sec_ldap_1_2
fi
is_verbose && echo "STEP: SEC LDAP CREATION DONE"

#END Creating SEC LA part ================================================================================

#START Creating APOS part================================================================================================================================================================================
if [ "$OPT_RESIZE" = "" ]; then
	cp $TEMPLATES_FOLDER/TEMPLATE_APOS/template_apos $TMP_DIR/
	sed -i "s/#APOS_CNF_BUNDLE#/$APOS_CNF_BUNDLE/g" $TMP_DIR/template_apos
	sed -i "s/#APOS_CMD_BUNDLE#/$APOS_CMD_BUNDLE/g" $TMP_DIR/template_apos
	sed -i "s/#APOS_EXT_BUNDLE#/$APOS_EXT_BUNDLE/g" $TMP_DIR/template_apos
	sed -i "s/#APOS_CONF_PATH#/$APOS_CONF_PATH/g" $TMP_DIR/template_apos
	sed -i "s/#APOS_POST_INSTALL_SCRIPT#/$APOS_POST_INSTALL_SCRIPT/g" $TMP_DIR/template_apos
	while read line    
		do    
		type=$(echo $line | awk -F';' '{print $1}')
		if [ "$type" = "2N" ]
			then
			CSI_NAME=$(echo $line | awk -F';' '{print $11}')
			BUNDLE_NAME=$(echo $line | awk -F';' '{print $2}')
			if [ "$CSI_NAME" = "LCT" ]
			then
				sed -i "s/#LCT_BUNDLE#/$BUNDLE_NAME/g" $TMP_DIR/template_apos
			fi
		fi
	done < $TMP_DIR/$SOURCE_FILE_NAME
	cat $TMP_DIR/template_apos >> $TMP_DIR/final.xml
elif [ "$OPT_RESIZE_ARG" = "0-1" ] ; then
	cp $TEMPLATES_FOLDER/TEMPLATE_APOS/template_apos_0_1 $TMP_DIR/
	sed -i "s/#APOS_CNF_BUNDLE#/$APOS_CNF_BUNDLE/g" $TMP_DIR/template_apos_0_1
	sed -i "s/#APOS_CMD_BUNDLE#/$APOS_CMD_BUNDLE/g" $TMP_DIR/template_apos_0_1
	sed -i "s/#APOS_EXT_BUNDLE#/$APOS_EXT_BUNDLE/g" $TMP_DIR/template_apos_0_1
	sed -i "s/#APOS_CONF_PATH#/$APOS_CONF_PATH/g" $TMP_DIR/template_apos_0_1
	sed -i "s/#APOS_POST_INSTALL_SCRIPT#/$APOS_POST_INSTALL_SCRIPT/g" $TMP_DIR/template_apos_0_1
	while read line    
		do    
		type=$(echo $line | awk -F';' '{print $1}')
		if [ "$type" = "2N" ]
			then
			CSI_NAME=$(echo $line | awk -F';' '{print $11}')
			BUNDLE_NAME=$(echo $line | awk -F';' '{print $2}')
			if [ "$CSI_NAME" = "LCT" ]
			then
				sed -i "s/#LCT_BUNDLE#/$BUNDLE_NAME/g" $TMP_DIR/template_apos_0_1
			fi
		fi
	done < $TMP_DIR/$SOURCE_FILE_NAME
	# mini ipa resize impacts
	if [ "$OPT_MINIRES" = "$TRUE" ]; then
		LCT_LINE=$(cat $SOURCE_LIST_FOLDER/$SOURCE_FILE_NAME | grep 'LCT')
		BUNDLE_NAME=$(echo $LCT_LINE | awk -F';' '{print $2}')
		sed -i "s/#LCT_BUNDLE#/$BUNDLE_NAME/g" $TMP_DIR/template_apos_0_1
	fi
	# end
	# APOS MINI IPA 0-1
	cat $TMP_DIR/template_apos_0_1 >> $TMP_DIR/final.xml
	cp $TMP_DIR/final.xml $TMP_DIR/apos_ipa_0_1.xml
elif [ "$OPT_RESIZE_ARG" = "1-2" ] ; then
	cp $TEMPLATES_FOLDER/TEMPLATE_APOS/template_apos_1_2 $TMP_DIR/
	sed -i "s/#APOS_CNF_BUNDLE#/$APOS_CNF_BUNDLE/g" $TMP_DIR/template_apos_1_2
	sed -i "s/#APOS_CMD_BUNDLE#/$APOS_CMD_BUNDLE/g" $TMP_DIR/template_apos_1_2
	sed -i "s/#APOS_EXT_BUNDLE#/$APOS_EXT_BUNDLE/g" $TMP_DIR/template_apos_1_2
	sed -i "s/#APOS_CONF_PATH#/$APOS_CONF_PATH/g" $TMP_DIR/template_apos_1_2
	sed -i "s/#APOS_POST_INSTALL_SCRIPT#/$APOS_POST_INSTALL_SCRIPT/g" $TMP_DIR/template_apos_1_2
	while read line    
		do    
		type=$(echo $line | awk -F';' '{print $1}')
		if [ "$type" = "2N" ]
			then
			CSI_NAME=$(echo $line | awk -F';' '{print $11}')
			BUNDLE_NAME=$(echo $line | awk -F';' '{print $2}')
			if [ "$CSI_NAME" = "LCT" ]
			then
				sed -i "s/#LCT_BUNDLE#/$BUNDLE_NAME/g" $TMP_DIR/template_apos_1_2
			fi
		fi
	done < $TMP_DIR/$SOURCE_FILE_NAME
	# mini ipa resize impacts
	if [ "$OPT_MINIRES" = "$TRUE" ]; then
		LCT_LINE=$(cat $SOURCE_LIST_FOLDER/$SOURCE_FILE_NAME | grep 'LCT')
		BUNDLE_NAME=$(echo $LCT_LINE | awk -F';' '{print $2}')
		sed -i "s/#LCT_BUNDLE#/$BUNDLE_NAME/g" $TMP_DIR/template_apos_1_2
	fi
	# end
	# APOS MINI IPA 1-2
	cat $TMP_DIR/template_apos_1_2 >> $TMP_DIR/final.xml
	cp $TMP_DIR/final.xml $TMP_DIR/apos_ipa_1_2.xml
fi	
is_verbose && echo "STEP: APOS CREATION DONE"

#END Creating APOS part================================================================================================================================================================================


#START Creating AP part==============================================================================================================================================================================

#Creating Proc init action for IMM and COM models import for AP apps
cat $TEMPLATES_FOLDER/TEMPLATE_AP_APPS/template_apps_intro >> $TMP_DIR/final.xml
if [ "$OPT_RESIZE" = "" ] || [ "$OPT_RESIZE_ARG" = "0-1" ]; then
	if [ "$OPT_MINI" = "$TRUE" ] ; then
		while read line    
		do    
			COMP_NAME=$(echo $line | awk -F';' '{print $3}')
			BUNDLE_NAME=$(echo $line | awk -F';' '{print $2}')
			model_allowed='Agent DEVMON'
			is_model_allowed=''
			for exc in $model_allowed; do 
				if [ "$COMP_NAME" == "$exc" ]; then
					is_model_allowed='true'
				fi
			done
			if [ "$is_model_allowed" = "true" ]; then
				cp $TEMPLATES_FOLDER/TEMPLATE_AP_APPS/template_apps_procinit $TMP_DIR/template_apps_procinit_$COMP_TYPE_NAME
				sed -i "s/#BUNDLE_NAME#/$BUNDLE_NAME/g" $TMP_DIR/template_apps_procinit_$COMP_TYPE_NAME
				cat $TMP_DIR/template_apps_procinit_$COMP_TYPE_NAME >> $TMP_DIR/final.xml
				rm -f $TMP_DIR/template_apps_procinit_$COMP_TYPE_NAME
			fi
		done < $TMP_DIR/$SOURCE_FILE_NAME
		cat $TEMPLATES_FOLDER/TEMPLATE_AP_APPS/template_apps_end >> $TMP_DIR/final.xml
	else
		while read line    
		do    
			COMP_NAME=$(echo $line | awk -F';' '{print $3}')
			BUNDLE_NAME=$(echo $line | awk -F';' '{print $2}')
			exceptions='COMSA APOSCONFBIN APOSCMDBIN APOSEXTBIN COM LCT ERIC-Sec-Control'
			is_exception=''
			for exc in $exceptions; do 
				if [ "$COMP_NAME" == "$exc" ]; then
					is_exception='true'
				fi
			done
			if [ -z $is_exception ]; then
                                if shallExcludeApp $COMP_NAME; then
                                        cp $TEMPLATES_FOLDER/TEMPLATE_BUNDLE/template_init_apg $TMP_DIR/
                                        sed -i "s/#PARAM#/$COMP_NAME/g" $TMP_DIR/template_init_apg
                                        sed -i "s/#SCRIPT#/$EXCLUDE_BUNDLES/g" $TMP_DIR/template_init_apg
                                        sed -i "s/#TYPE#/$INSTALL_TYPE/g" $TMP_DIR/template_init_apg
                                        cat $TMP_DIR/template_init_apg >> $TMP_DIR/final.xml
                                        rm -f $TMP_DIR/template_init_apg
                                fi
				cp $TEMPLATES_FOLDER/TEMPLATE_AP_APPS/template_apps_procinit $TMP_DIR/template_apps_procinit_$COMP_TYPE_NAME
				sed -i "s/#BUNDLE_NAME#/$BUNDLE_NAME/g" $TMP_DIR/template_apps_procinit_$COMP_TYPE_NAME
				cat $TMP_DIR/template_apps_procinit_$COMP_TYPE_NAME >> $TMP_DIR/final.xml
				rm -f $TMP_DIR/template_apps_procinit_$COMP_TYPE_NAME
                               if shallExcludeApp $COMP_NAME; then
                                       cp $TEMPLATES_FOLDER/TEMPLATE_BUNDLE/template_end_apg $TMP_DIR/
                                       cat $TMP_DIR/template_end_apg >> $TMP_DIR/final.xml
                                       rm -f $TMP_DIR/template_end_apg
                               fi
			fi
		done < $TMP_DIR/$SOURCE_FILE_NAME
		cat $TEMPLATES_FOLDER/TEMPLATE_AP_APPS/template_apps_end >> $TMP_DIR/final.xml
		
	fi

fi
is_verbose && echo "STEP: PROCINIT ACTIONS FOR APG APPS DONE"

#END Creating AP part==================================================================================================================================================================================


#START Creating safApp ==========================================================================================================================================================================

if [ "$OPT_RESIZE" = "" ] || [ "$OPT_RESIZE_ARG" = "0-1" ]; then
	cp $TEMPLATES_FOLDER/TEMPLATE_AP_APPS/template_safApp $TMP_DIR/
	sed -i "s/#APP_TYPE#/$APP_TYPE/g" $TMP_DIR/template_safApp
	sed -i "s/#SAF_APP#/$SAF_APP/g" $TMP_DIR/template_safApp
	sed -i "s/#SAF_VERSION#/$SAF_VERSION/g" $TMP_DIR/template_safApp
	cat $TMP_DIR/template_safApp >> $TMP_DIR/final.xml
	is_verbose && echo "STEP: SAF_APP DONE"
fi

#END Creating safApp ==========================================================================================================================================================================


#START Creating SG 2N==========================================================================================================================================================================

if [ "$OPT_RESIZE" = "" ] || [ "$OPT_RESIZE_ARG" = "0-1" ]; then
	cp $TEMPLATES_FOLDER/TEMPLATE_AP_APPS/template_sg_2n $TMP_DIR/
	sed -i "s/#SAF_APP#/$SAF_APP/g" $TMP_DIR/template_sg_2n
	sed -i "s/#SG_2N#/$SG_2N/g" $TMP_DIR/template_sg_2n
	sed -i "s/#SG_2N_TYPE#/$SG_2N_TYPE/g" $TMP_DIR/template_sg_2n
	sed -i "s/#SAF_VERSION#/$SAF_VERSION/g" $TMP_DIR/template_sg_2n
	cat $TMP_DIR/template_sg_2n >> $TMP_DIR/final.xml
	is_verbose && echo "STEP: SG_2N DONE"
fi

#END Creating SG 2N==========================================================================================================================================================================


#START Creating SGs NO_RED==========================================================================================================================================================================

if [ "$OPT_RESIZE" = "" ] || [ "$OPT_RESIZE_ARG" = "0-1" ]; then
	if [ "$OPT_MINI" != "$TRUE" ] ; then
		while read line    
			do    
			type=$(echo $line | awk -F';' '{print $1}')
			if [ "$type" = "NORED" ]
				then
				CS_TYPE=$(echo $line | awk -F';' '{print $6}')
				SVC_TYPE=$(echo $line | awk -F';' '{print $10}')
				CSI_NAME=$(echo $line | awk -F';' '{print $11}')
			        COMP_NAME=$(echo $line | awk -F';' '{print $3}')
                                if shallExcludeApp $COMP_NAME; then
                                     cp $TEMPLATES_FOLDER/TEMPLATE_BUNDLE/template_init_apg $TMP_DIR/
                                     sed -i "s/#PARAM#/$COMP_NAME/g" $TMP_DIR/template_init_apg
                                     sed -i "s/#SCRIPT#/$EXCLUDE_BUNDLES/g" $TMP_DIR/template_init_apg
                                     sed -i "s/#TYPE#/$INSTALL_TYPE/g" $TMP_DIR/template_init_apg
                                     cat $TMP_DIR/template_init_apg >> $TMP_DIR/final.xml
                                     rm -f $TMP_DIR/template_init_apg
                                fi
				cp $TEMPLATES_FOLDER/TEMPLATE_AP_APPS/template_sg_nored $TMP_DIR/template_sg_nored_$CSI_NAME
				sed -i "s/#SAF_APP#/$SAF_APP/g" $TMP_DIR/template_sg_nored_$CSI_NAME
				sed -i "s/#CSI_NAME#/$CSI_NAME/g" $TMP_DIR/template_sg_nored_$CSI_NAME
				sed -i "s/#SAF_VERSION#/$SAF_VERSION/g" $TMP_DIR/template_sg_nored_$CSI_NAME
				cat $TMP_DIR/template_sg_nored_$CSI_NAME >> $TMP_DIR/final.xml
                                if shallExcludeApp $COMP_NAME; then
                                         cp $TEMPLATES_FOLDER/TEMPLATE_BUNDLE/template_end_apg $TMP_DIR/
                                         cat $TMP_DIR/template_end_apg >> $TMP_DIR/final.xml
                                         rm -f $TMP_DIR/template_end_apg
                                fi
			fi
		done < $TMP_DIR/$SOURCE_FILE_NAME
	fi
	is_verbose && echo "STEP: SGs_NO_RED DONE"
fi

#END Creating SG NO_RED==========================================================================================================================================================================


#START Creating SU 1 NO_RED==========================================================================================================================================================================

if [ "$OPT_RESIZE" = "" ] || [ "$OPT_RESIZE_ARG" = "0-1" ]; then
	if [ "$OPT_MINI" != "$TRUE" ] ; then
		while read line    
			do    
			type=$(echo $line | awk -F';' '{print $1}')
			if [ "$type" = "NORED" ]
				then
				CS_TYPE=$(echo $line | awk -F';' '{print $6}')
				SVC_TYPE=$(echo $line | awk -F';' '{print $10}')
				CSI_NAME=$(echo $line | awk -F';' '{print $11}')
                                COMP_NAME=$(echo $line | awk -F';' '{print $3}')
                                if shallExcludeApp $COMP_NAME; then
                                     cp $TEMPLATES_FOLDER/TEMPLATE_BUNDLE/template_init_apg $TMP_DIR/
                                     sed -i "s/#PARAM#/$COMP_NAME/g" $TMP_DIR/template_init_apg
                                     sed -i "s/#SCRIPT#/$EXCLUDE_BUNDLES/g" $TMP_DIR/template_init_apg
                                     sed -i "s/#TYPE#/$INSTALL_TYPE/g" $TMP_DIR/template_init_apg
                                     cat $TMP_DIR/template_init_apg >> $TMP_DIR/final.xml
                                     rm -f $TMP_DIR/template_init_apg
                                fi
				cp $TEMPLATES_FOLDER/TEMPLATE_AP_APPS/template_su_nored_1 $TMP_DIR/template_su_nored_1_$CSI_NAME	
				sed -i "s/#SAF_APP#/$SAF_APP/g" $TMP_DIR/template_su_nored_1_$CSI_NAME
				sed -i "s/#SAF_VERSION#/$SAF_VERSION/g" $TMP_DIR/template_su_nored_1_$CSI_NAME
				sed -i "s/#CSI_NAME#/$CSI_NAME/g" $TMP_DIR/template_su_nored_1_$CSI_NAME
				cat $TMP_DIR/template_su_nored_1_$CSI_NAME >> $TMP_DIR/final.xml
                                if shallExcludeApp $COMP_NAME; then
                                         cp $TEMPLATES_FOLDER/TEMPLATE_BUNDLE/template_end_apg $TMP_DIR/
                                         cat $TMP_DIR/template_end_apg >> $TMP_DIR/final.xml
                                         rm -f $TMP_DIR/template_end_apg
                                fi
			fi
		done < $TMP_DIR/$SOURCE_FILE_NAME
	fi
fi
is_verbose && echo "STEP: SUs_1_NO_RED DONE"

#END Creating SU 1 NO_RED==========================================================================================================================================================================


#START Creating COMP 1 NO_RED==========================================================================================================================================================================

if [ "$OPT_RESIZE" = "" ] || [ "$OPT_RESIZE_ARG" = "0-1" ]; then
	if [ "$OPT_MINI" != "$TRUE" ] ; then
		while read line    
			do    
			type=$(echo $line | awk -F';' '{print $1}')
			if [ "$type" = "NORED" ]
			then
				BUNDLE_NAME=$(echo $line | awk -F';' '{print $2}')
				COMP_NAME=$(echo $line | awk -F';' '{print $3}')
				COMP_TYPE_NAME=$(echo $line | awk -F';' '{print $5}')
				CS_TYPE=$(echo $line | awk -F';' '{print $6}')
				COMP_VERSION=$(echo $line | awk -F';' '{print $7}')
				CLC_NAME=$(echo $line | awk -F';' '{print $8}')
				HelthCheck=$(echo $line | awk -F';' '{print $9}')
				CSI_NAME=$(echo $line | awk -F';' '{print $11}')
                                if shallExcludeApp $COMP_NAME; then
                                           cp $TEMPLATES_FOLDER/TEMPLATE_BUNDLE/template_init_apg $TMP_DIR/
                                           sed -i "s/#PARAM#/$COMP_NAME/g" $TMP_DIR/template_init_apg
                                           sed -i "s/#SCRIPT#/$EXCLUDE_BUNDLES/g" $TMP_DIR/template_init_apg
                                           sed -i "s/#TYPE#/$INSTALL_TYPE/g" $TMP_DIR/template_init_apg
                                           cat $TMP_DIR/template_init_apg >> $TMP_DIR/final.xml
                                          rm -f $TMP_DIR/template_init_apg
                                fi
				cp $TEMPLATES_FOLDER/TEMPLATE_COMP_NO_RED/TEMPLATE_COMP_NO_RED1 $TMP_DIR/TEMPLATE_COMP_NO_RED1_$COMP_NAME
				sed -i "s/#SAF_APP#/$SAF_APP/g" $TMP_DIR/TEMPLATE_COMP_NO_RED1_$COMP_NAME
				sed -i "s/#COMP_NAME#/$COMP_NAME/g" $TMP_DIR/TEMPLATE_COMP_NO_RED1_$COMP_NAME
				
				if isOldNamingConvention "$BUNDLE_NAME" ; then
					# Old naming convention for APG block's component type
					# safVersion=<Rstate>,safCompType=<CompTypeName>
					# Example: safVersion=R1E,safCompType=ERIC-APG_ASEC
				sed -i "s/#COMP_VERSION#/$COMP_VERSION/g" $TMP_DIR/TEMPLATE_COMP_NO_RED1_$COMP_NAME
				else
					# New naming convention for APG block's component type
					# safVersion=<CXC>-<Rstate>,safCompType=<CompTypeName>
					# Example: safVersion=CXC1371474-R1E,safCompType=ERIC-APG_ASEC
					BUNDLE_CXC=$(echo "$BUNDLE_NAME" | sed 's/-[^-]*$//' | awk -F'-' '{ print $NF }')
					sed -i "s/#COMP_VERSION#/$BUNDLE_CXC-$COMP_VERSION/g" $TMP_DIR/TEMPLATE_COMP_NO_RED1_$COMP_NAME
				fi
				
				sed -i "s/#COMP_TYPE_NAME#/$COMP_TYPE_NAME/g" $TMP_DIR/TEMPLATE_COMP_NO_RED1_$COMP_NAME
				sed -i "s/#CS_TYPE#/$CS_TYPE/g" $TMP_DIR/TEMPLATE_COMP_NO_RED1_$COMP_NAME
				sed -i "s/#SAF_VERSION#/$SAF_VERSION/g" $TMP_DIR/TEMPLATE_COMP_NO_RED1_$COMP_NAME
				sed -i "s/#HCK#/$HelthCheck/g" $TMP_DIR/TEMPLATE_COMP_NO_RED1_$COMP_NAME
				sed -i "s/#HCK_MAX_DURATION#/$HCK_MAX_DURATION/g" $TMP_DIR/TEMPLATE_COMP_NO_RED1_$COMP_NAME
				sed -i "s/#HCK_PERIOD#/$HCK_PERIOD/g" $TMP_DIR/TEMPLATE_COMP_NO_RED1_$COMP_NAME
				sed -i "s/#CSI_NAME#/$CSI_NAME/g" $TMP_DIR/TEMPLATE_COMP_NO_RED1_$COMP_NAME
				cat $TMP_DIR/TEMPLATE_COMP_NO_RED1_$COMP_NAME >> $TMP_DIR/final.xml
                                if shallExcludeApp $COMP_NAME; then
                                         cp $TEMPLATES_FOLDER/TEMPLATE_BUNDLE/template_end_apg $TMP_DIR/
                                         cat $TMP_DIR/template_end_apg >> $TMP_DIR/final.xml
                                         rm -f $TMP_DIR/template_end_apg
                                fi
			fi
		done < $TMP_DIR/$SOURCE_FILE_NAME 
	fi
fi
is_verbose && echo "STEP: COMP 1 FOR NO_RED CREATION DONE"	

#END Creating COMP 1 NO_RED==========================================================================================================================================================================


#START Creating SU 1 2N==========================================================================================================================================================================

if [ "$OPT_RESIZE" = "" ] || [ "$OPT_RESIZE_ARG" = "0-1" ]; then
	cp $TEMPLATES_FOLDER/TEMPLATE_AP_APPS/template_su_2n_1 $TMP_DIR/
	sed -i "s/#SAF_APP#/$SAF_APP/g" $TMP_DIR/template_su_2n_1
	sed -i "s/#SG_2N#/$SG_2N/g" $TMP_DIR/template_su_2n_1
	sed -i "s/#SAF_VERSION#/$SAF_VERSION/g" $TMP_DIR/template_su_2n_1
	sed -i "s/#SU1_2N#/$SU1_2N/g" $TMP_DIR/template_su_2n_1
	sed -i "s/#SU_2N_TYPE#/$SU_2N_TYPE/g" $TMP_DIR/template_su_2n_1
	cat $TMP_DIR/template_su_2n_1 >> $TMP_DIR/final.xml
fi
is_verbose && echo "STEP: SU_1_2N DONE"

#END Creating SU 1 2N==========================================================================================================================================================================


#START Creating component for 2N SU 1 ===================================================================================================================================================

if [ "$OPT_RESIZE" = "" ] || [ "$OPT_RESIZE_ARG" = "0-1" ]; then
	if [ "$OPT_MINI" = "$TRUE" ] ; then
		while read line    
		do    
			type=$(echo $line | awk -F';' '{print $1}')
			COMP_NAME=$(echo $line | awk -F';' '{print $3}')
			allowed_comp_2N_su1='COMSA ERIC-Sec-Control Agent DEVMON'
			is_allowed_comp_2N_su1=''
			for exc in $allowed_comp_2N_su1; do 
				if [ "$COMP_NAME" == "$exc" ]; then
					is_allowed_comp_2N_su1='true'
				fi
			done
			if [ "$is_allowed_comp_2N_su1" = "true" ]; then
				if [ "$type" = "2N" ]
					then
					BUNDLE_NAME=$(echo $line | awk -F';' '{print $2}')
					COMP_TYPE_NAME=$(echo $line | awk -F';' '{print $5}')
					CS_TYPE=$(echo $line | awk -F';' '{print $6}')
					COMP_VERSION=$(echo $line | awk -F';' '{print $7}')
					CLC_NAME=$(echo $line | awk -F';' '{print $8}')
					HelthCheck=$(echo $line | awk -F';' '{print $9}')
					if [ "$COMP_TYPE_NAME" = "ERIC-ComSa-Cmw" ]
						then
						cp $TEMPLATES_FOLDER/TEMPLATE_COMP_2N/TEMPLATE_COMP_2N_COMSA_1 $TMP_DIR/
						sed -i "s/#SU1_2N#/$SU1_2N/g" $TMP_DIR/TEMPLATE_COMP_2N_COMSA_1
						sed -i "s/#SG_2N#/$SG_2N/g" $TMP_DIR/TEMPLATE_COMP_2N_COMSA_1
						sed -i "s/#SAF_APP#/$SAF_APP/g" $TMP_DIR/TEMPLATE_COMP_2N_COMSA_1
						sed -i "s/#COMP_NAME#/$COMP_NAME/g" $TMP_DIR/TEMPLATE_COMP_2N_COMSA_1
						sed -i "s/#COMP_VERSION#/$COMP_VERSION/g" $TMP_DIR/TEMPLATE_COMP_2N_COMSA_1
						sed -i "s/#COMP_TYPE_NAME#/$COMP_TYPE_NAME/g" $TMP_DIR/TEMPLATE_COMP_2N_COMSA_1
						sed -i "s/#SAF_VERSION#/$SAF_VERSION/g" $TMP_DIR/TEMPLATE_COMP_2N_COMSA_1
						sed -i "s/#CS_TYPE#/$CS_TYPE/g" $TMP_DIR/TEMPLATE_COMP_2N_COMSA_1
						sed -i "s/#COMP_SSH_NAME#/$COMSA_COMP_SSHD/g" $TMP_DIR/TEMPLATE_COMP_2N_COMSA_1
						sed -i "s/#COMP_SSH_VERSION#/$COMSA_SSHD_RSTATE/g" $TMP_DIR/TEMPLATE_COMP_2N_COMSA_1
						sed -i "s/#CS_SSH_TYPE#/$COMSA_CS_SSHD/g" $TMP_DIR/TEMPLATE_COMP_2N_COMSA_1
            sed -i "s/#COMP_TLS_NAME#/$COMSA_COMP_TLSD/g" $TMP_DIR/TEMPLATE_COMP_2N_COMSA_1
            sed -i "s/#COMP_TLS_VERSION#/$COMSA_TLSD_RSTATE/g" $TMP_DIR/TEMPLATE_COMP_2N_COMSA_1
            sed -i "s/#CS_TLS_TYPE#/$COMSA_CS_TLSD/g" $TMP_DIR/TEMPLATE_COMP_2N_COMSA_1
            sed -i "s/#COMP_VSFTPD_NAME#/$COMSA_COMP_VSFTPD/g" $TMP_DIR/TEMPLATE_COMP_2N_COMSA_1
            sed -i "s/#COMP_VSFTPD_VERSION#/$COMSA_VSFTPD_RSTATE/g" $TMP_DIR/TEMPLATE_COMP_2N_COMSA_1
            sed -i "s/#CS_VSFTPD_TYPE#/$COMSA_CS_VSFTPD/g" $TMP_DIR/TEMPLATE_COMP_2N_COMSA_1

						cat $TMP_DIR/TEMPLATE_COMP_2N_COMSA_1 >> $TMP_DIR/final.xml
					else
                                                if shallExcludeApp $COMP_NAME; then
                                                        cp $TEMPLATES_FOLDER/TEMPLATE_BUNDLE/template_init_apg $TMP_DIR/
                                                        sed -i "s/#PARAM#/$COMP_NAME/g" $TMP_DIR/template_init_apg
                                                        sed -i "s/#SCRIPT#/$EXCLUDE_BUNDLES/g" $TMP_DIR/template_init_apg
                                                        sed -i "s/#TYPE#/$INSTALL_TYPE/g" $TMP_DIR/template_init_apg
                                                        cat $TMP_DIR/template_init_apg >> $TMP_DIR/final.xml
                                                        rm -f $TMP_DIR/template_init_apg
                                                fi
						cp $TEMPLATES_FOLDER/TEMPLATE_COMP_2N/TEMPLATE_COMP_2N_1 $TMP_DIR/TEMPLATE_COMP_2N_1_$COMP_NAME
						sed -i "s/#SU1_2N#/$SU1_2N/g" $TMP_DIR/TEMPLATE_COMP_2N_1_$COMP_NAME
						sed -i "s/#SG_2N#/$SG_2N/g" $TMP_DIR/TEMPLATE_COMP_2N_1_$COMP_NAME
						sed -i "s/#SAF_APP#/$SAF_APP/g" $TMP_DIR/TEMPLATE_COMP_2N_1_$COMP_NAME
						sed -i "s/#COMP_NAME#/$COMP_NAME/g" $TMP_DIR/TEMPLATE_COMP_2N_1_$COMP_NAME
						
						if [ "$COMP_TYPE_NAME" != "ERIC-Sec-Control" ] ; then
							if isOldNamingConvention "$BUNDLE_NAME" ; then
								# Old naming convention for APG block's component type
								# safVersion=<Rstate>,safCompType=<CompTypeName>
								# Example: safVersion=R1E,safCompType=ERIC-APG_ASEC
								sed -i "s/#COMP_VERSION#/$COMP_VERSION/g" $TMP_DIR/TEMPLATE_COMP_2N_1_$COMP_NAME
							else
								# New naming convention for APG block's component type
								# safVersion=<CXC>-<Rstate>,safCompType=<CompTypeName>
								# Example: safVersion=CXC1371474-R1E,safCompType=ERIC-APG_ASEC
								BUNDLE_CXC=$(echo "$BUNDLE_NAME" | sed 's/-[^-]*$//' | awk -F'-' '{ print $NF }')
								sed -i "s/#COMP_VERSION#/$BUNDLE_CXC-$COMP_VERSION/g" $TMP_DIR/TEMPLATE_COMP_2N_1_$COMP_NAME
							fi
						else
							# SEC
							sed -i "s/#COMP_VERSION#/$COMP_VERSION/g" $TMP_DIR/TEMPLATE_COMP_2N_1_$COMP_NAME
						fi
						
						sed -i "s/#COMP_TYPE_NAME#/$COMP_TYPE_NAME/g" $TMP_DIR/TEMPLATE_COMP_2N_1_$COMP_NAME
						sed -i "s/#SAF_VERSION#/$SAF_VERSION/g" $TMP_DIR/TEMPLATE_COMP_2N_1_$COMP_NAME
						sed -i "s/#CS_TYPE#/$CS_TYPE/g" $TMP_DIR/TEMPLATE_COMP_2N_1_$COMP_NAME
						sed -i "s/#HCK#/$HelthCheck/g" $TMP_DIR/TEMPLATE_COMP_2N_1_$COMP_NAME
						if [ "$COMP_TYPE_NAME" = "ERIC-APG_Agent" ]
						then
							sed -i "s/#HCK_PERIOD_2N#/$HCK_PERIOD_AGENT/g" $TMP_DIR/TEMPLATE_COMP_2N_1_$COMP_NAME
							sed -i "s/#HCK_MAX_DURATION_2N#/$HCK_MAX_DURATION_AGENT/g" $TMP_DIR/TEMPLATE_COMP_2N_1_$COMP_NAME
						else
							sed -i "s/#HCK_PERIOD_2N#/$HCK_PERIOD/g" $TMP_DIR/TEMPLATE_COMP_2N_1_$COMP_NAME
							sed -i "s/#HCK_MAX_DURATION_2N#/$HCK_MAX_DURATION/g" $TMP_DIR/TEMPLATE_COMP_2N_1_$COMP_NAME				
						fi
						cat $TMP_DIR/TEMPLATE_COMP_2N_1_$COMP_NAME >> $TMP_DIR/final.xml
                                                if shallExcludeApp $COMP_NAME; then
                                                        cp $TEMPLATES_FOLDER/TEMPLATE_BUNDLE/template_end_apg $TMP_DIR/
                                                        cat $TMP_DIR/template_end_apg >> $TMP_DIR/final.xml
                                                        rm -f $TMP_DIR/template_end_apg
                                                fi
 
					fi
				fi
			fi
		done < $TMP_DIR/$SOURCE_FILE_NAME
	else
		while read line    
		do    
			type=$(echo $line | awk -F';' '{print $1}')
			if [ "$type" = "2N" ]
				then
				BUNDLE_NAME=$(echo $line | awk -F';' '{print $2}')
				COMP_NAME=$(echo $line | awk -F';' '{print $3}')
				COMP_TYPE_NAME=$(echo $line | awk -F';' '{print $5}')
				CS_TYPE=$(echo $line | awk -F';' '{print $6}')
				COMP_VERSION=$(echo $line | awk -F';' '{print $7}')
				CLC_NAME=$(echo $line | awk -F';' '{print $8}')
				HelthCheck=$(echo $line | awk -F';' '{print $9}')
                                if shallExcludeApp $COMP_NAME; then
                                        cp $TEMPLATES_FOLDER/TEMPLATE_BUNDLE/template_init_apg $TMP_DIR/
                                        sed -i "s/#PARAM#/$COMP_NAME/g" $TMP_DIR/template_init_apg
                                        sed -i "s/#SCRIPT#/$EXCLUDE_BUNDLES/g" $TMP_DIR/template_init_apg
                                        sed -i "s/#TYPE#/$INSTALL_TYPE/g" $TMP_DIR/template_init_apg
                                        cat $TMP_DIR/template_init_apg >> $TMP_DIR/final.xml
                                        rm -f $TMP_DIR/template_init_apg
                                fi
				if [ "$COMP_TYPE_NAME" = "ERIC-ComSa-Cmw" ]
					then
					cp $TEMPLATES_FOLDER/TEMPLATE_COMP_2N/TEMPLATE_COMP_2N_COMSA_1 $TMP_DIR/
					sed -i "s/#SU1_2N#/$SU1_2N/g" $TMP_DIR/TEMPLATE_COMP_2N_COMSA_1
					sed -i "s/#SG_2N#/$SG_2N/g" $TMP_DIR/TEMPLATE_COMP_2N_COMSA_1
					sed -i "s/#SAF_APP#/$SAF_APP/g" $TMP_DIR/TEMPLATE_COMP_2N_COMSA_1
					sed -i "s/#COMP_NAME#/$COMP_NAME/g" $TMP_DIR/TEMPLATE_COMP_2N_COMSA_1
					sed -i "s/#COMP_VERSION#/$COMP_VERSION/g" $TMP_DIR/TEMPLATE_COMP_2N_COMSA_1
					sed -i "s/#COMP_TYPE_NAME#/$COMP_TYPE_NAME/g" $TMP_DIR/TEMPLATE_COMP_2N_COMSA_1
					sed -i "s/#SAF_VERSION#/$SAF_VERSION/g" $TMP_DIR/TEMPLATE_COMP_2N_COMSA_1
					sed -i "s/#CS_TYPE#/$CS_TYPE/g" $TMP_DIR/TEMPLATE_COMP_2N_COMSA_1
					sed -i "s/#COMP_SSH_NAME#/$COMSA_COMP_SSHD/g" $TMP_DIR/TEMPLATE_COMP_2N_COMSA_1
					sed -i "s/#COMP_SSH_VERSION#/$COMSA_SSHD_RSTATE/g" $TMP_DIR/TEMPLATE_COMP_2N_COMSA_1
					sed -i "s/#CS_SSH_TYPE#/$COMSA_CS_SSHD/g" $TMP_DIR/TEMPLATE_COMP_2N_COMSA_1
	        sed -i "s/#COMP_TLS_NAME#/$COMSA_COMP_TLSD/g" $TMP_DIR/TEMPLATE_COMP_2N_COMSA_1
          sed -i "s/#COMP_TLS_VERSION#/$COMSA_TLSD_RSTATE/g" $TMP_DIR/TEMPLATE_COMP_2N_COMSA_1
          sed -i "s/#CS_TLS_TYPE#/$COMSA_CS_TLSD/g" $TMP_DIR/TEMPLATE_COMP_2N_COMSA_1
	        sed -i "s/#COMP_VSFTPD_NAME#/$COMSA_COMP_VSFTPD/g" $TMP_DIR/TEMPLATE_COMP_2N_COMSA_1
          sed -i "s/#COMP_VSFTPD_VERSION#/$COMSA_VSFTPD_RSTATE/g" $TMP_DIR/TEMPLATE_COMP_2N_COMSA_1
          sed -i "s/#CS_VSFTPD_TYPE#/$COMSA_CS_VSFTPD/g" $TMP_DIR/TEMPLATE_COMP_2N_COMSA_1

					cat $TMP_DIR/TEMPLATE_COMP_2N_COMSA_1 >> $TMP_DIR/final.xml
				else
					cp $TEMPLATES_FOLDER/TEMPLATE_COMP_2N/TEMPLATE_COMP_2N_1 $TMP_DIR/TEMPLATE_COMP_2N_1_$COMP_NAME
					sed -i "s/#SU1_2N#/$SU1_2N/g" $TMP_DIR/TEMPLATE_COMP_2N_1_$COMP_NAME
					sed -i "s/#SG_2N#/$SG_2N/g" $TMP_DIR/TEMPLATE_COMP_2N_1_$COMP_NAME
					sed -i "s/#SAF_APP#/$SAF_APP/g" $TMP_DIR/TEMPLATE_COMP_2N_1_$COMP_NAME
					sed -i "s/#COMP_NAME#/$COMP_NAME/g" $TMP_DIR/TEMPLATE_COMP_2N_1_$COMP_NAME
					
					if [ "$COMP_TYPE_NAME" != "ERIC-Sec-Control" ] ; then						
						if isOldNamingConvention "$BUNDLE_NAME" ; then
							# Old naming convention for APG block's component type
							# safVersion=<Rstate>,safCompType=<CompTypeName>
							# Example: safVersion=R1E,safCompType=ERIC-APG_ASEC
							sed -i "s/#COMP_VERSION#/$COMP_VERSION/g" $TMP_DIR/TEMPLATE_COMP_2N_1_$COMP_NAME
						else
							# New naming convention for APG block's component type
							# safVersion=<CXC>-<Rstate>,safCompType=<CompTypeName>
							# Example: safVersion=CXC1371474-R1E,safCompType=ERIC-APG_ASEC
							BUNDLE_CXC=$(echo "$BUNDLE_NAME" | sed 's/-[^-]*$//' | awk -F'-' '{ print $NF }')
							sed -i "s/#COMP_VERSION#/$BUNDLE_CXC-$COMP_VERSION/g" $TMP_DIR/TEMPLATE_COMP_2N_1_$COMP_NAME
						fi
					else
						# SEC
						sed -i "s/#COMP_VERSION#/$COMP_VERSION/g" $TMP_DIR/TEMPLATE_COMP_2N_1_$COMP_NAME
					fi
					
					sed -i "s/#COMP_TYPE_NAME#/$COMP_TYPE_NAME/g" $TMP_DIR/TEMPLATE_COMP_2N_1_$COMP_NAME
					sed -i "s/#SAF_VERSION#/$SAF_VERSION/g" $TMP_DIR/TEMPLATE_COMP_2N_1_$COMP_NAME
					sed -i "s/#CS_TYPE#/$CS_TYPE/g" $TMP_DIR/TEMPLATE_COMP_2N_1_$COMP_NAME
					sed -i "s/#HCK#/$HelthCheck/g" $TMP_DIR/TEMPLATE_COMP_2N_1_$COMP_NAME
					if [ "$COMP_TYPE_NAME" = "ERIC-APG_Agent" ]
					then
						sed -i "s/#HCK_PERIOD_2N#/$HCK_PERIOD_AGENT/g" $TMP_DIR/TEMPLATE_COMP_2N_1_$COMP_NAME
						sed -i "s/#HCK_MAX_DURATION_2N#/$HCK_MAX_DURATION_AGENT/g" $TMP_DIR/TEMPLATE_COMP_2N_1_$COMP_NAME
					else
						sed -i "s/#HCK_PERIOD_2N#/$HCK_PERIOD/g" $TMP_DIR/TEMPLATE_COMP_2N_1_$COMP_NAME
						sed -i "s/#HCK_MAX_DURATION_2N#/$HCK_MAX_DURATION/g" $TMP_DIR/TEMPLATE_COMP_2N_1_$COMP_NAME				
					fi
					cat $TMP_DIR/TEMPLATE_COMP_2N_1_$COMP_NAME >> $TMP_DIR/final.xml
				fi
                                if shallExcludeApp $COMP_NAME; then
                                          cp $TEMPLATES_FOLDER/TEMPLATE_BUNDLE/template_end_apg $TMP_DIR/
                                          cat $TMP_DIR/template_end_apg >> $TMP_DIR/final.xml
                                          rm -f $TMP_DIR/template_end_apg
                                fi
			fi
		done < $TMP_DIR/$SOURCE_FILE_NAME
	fi
fi
is_verbose && echo "STEP: COMP 1 FOR 2N CREATION DONE"	
	
#END Creating component for 2N SU 1 ===================================================================================================================================================


#START Creating SU 2 NO_RED==========================================================================================================================================================================

if [ "$OPT_RESIZE" = "" ] || [ "$OPT_RESIZE_ARG" = "1-2" ]; then
	if [ "$OPT_MINI" != "$TRUE" ] ; then
		if [ "$OPT_RESIZE_ARG" = "1-2" ]; then
			cat $TEMPLATES_FOLDER/TEMPLATE_AP_APPS/template_proc_init >> $TMP_DIR/final.xml
		fi
		while read line    
		do    
			type=$(echo $line | awk -F';' '{print $1}')
			if [ "$type" = "NORED" ]
				then
				CS_TYPE=$(echo $line | awk -F';' '{print $6}')
				SVC_TYPE=$(echo $line | awk -F';' '{print $10}')
				CSI_NAME=$(echo $line | awk -F';' '{print $11}')
                                COMP_NAME=$(echo $line | awk -F';' '{print $3}')
                                if shallExcludeApp $COMP_NAME; then
                                        cp $TEMPLATES_FOLDER/TEMPLATE_BUNDLE/template_init_apg $TMP_DIR/
                                        sed -i "s/#PARAM#/$COMP_NAME/g" $TMP_DIR/template_init_apg
                                        sed -i "s/#SCRIPT#/$EXCLUDE_BUNDLES/g" $TMP_DIR/template_init_apg
                                        sed -i "s/#TYPE#/$INSTALL_TYPE/g" $TMP_DIR/template_init_apg
                                        cat $TMP_DIR/template_init_apg >> $TMP_DIR/final.xml
                                        rm -f $TMP_DIR/template_init_apg
                                fi
				cp $TEMPLATES_FOLDER/TEMPLATE_AP_APPS/template_su_nored_2 $TMP_DIR/template_su_nored_2_$CSI_NAME
				sed -i "s/#SAF_APP#/$SAF_APP/g" $TMP_DIR/template_su_nored_2_$CSI_NAME
				sed -i "s/#SAF_VERSION#/$SAF_VERSION/g" $TMP_DIR/template_su_nored_2_$CSI_NAME
				sed -i "s/#CSI_NAME#/$CSI_NAME/g" $TMP_DIR/template_su_nored_2_$CSI_NAME
				cat $TMP_DIR/template_su_nored_2_$CSI_NAME >> $TMP_DIR/final.xml
                                if shallExcludeApp $COMP_NAME; then
                                          cp $TEMPLATES_FOLDER/TEMPLATE_BUNDLE/template_end_apg $TMP_DIR/
                                          cat $TMP_DIR/template_end_apg >> $TMP_DIR/final.xml
                                          rm -f $TMP_DIR/template_end_apg
                                fi
			fi
		done < $TMP_DIR/$SOURCE_FILE_NAME
	fi
fi
is_verbose && echo "STEP: SU_2_NO_RED DONE"

#END Creating SU 2 NO_RED==========================================================================================================================================================================


#START Creating COMP 2 NO_RED==========================================================================================================================================================================

if [ "$OPT_RESIZE" = "" ] || [ "$OPT_RESIZE_ARG" = "1-2" ]; then
	if [ "$OPT_MINI" != "$TRUE" ] ; then
		while read line    
		do    
			type=$(echo $line | awk -F';' '{print $1}')
			if [ "$type" = "NORED" ]
			then
				BUNDLE_NAME=$(echo $line | awk -F';' '{print $2}')
				COMP_NAME=$(echo $line | awk -F';' '{print $3}')
				COMP_TYPE_NAME=$(echo $line | awk -F';' '{print $5}')
				CS_TYPE=$(echo $line | awk -F';' '{print $6}')
				COMP_VERSION=$(echo $line | awk -F';' '{print $7}')
				CLC_NAME=$(echo $line | awk -F';' '{print $8}')
				HelthCheck=$(echo $line | awk -F';' '{print $9}')
				CSI_NAME=$(echo $line | awk -F';' '{print $11}')
                                if shallExcludeApp $COMP_NAME; then
                                       cp $TEMPLATES_FOLDER/TEMPLATE_BUNDLE/template_init_apg $TMP_DIR/
                                       sed -i "s/#PARAM#/$COMP_NAME/g" $TMP_DIR/template_init_apg
                                       sed -i "s/#SCRIPT#/$EXCLUDE_BUNDLES/g" $TMP_DIR/template_init_apg
                                       sed -i "s/#TYPE#/$INSTALL_TYPE/g" $TMP_DIR/template_init_apg
                                       cat $TMP_DIR/template_init_apg >> $TMP_DIR/final.xml
                                       rm -f $TMP_DIR/template_init_apg
                                fi
				cp $TEMPLATES_FOLDER/TEMPLATE_COMP_NO_RED/TEMPLATE_COMP_NO_RED2 $TMP_DIR/TEMPLATE_COMP_NO_RED2_$COMP_NAME
				sed -i "s/#SAF_APP#/$SAF_APP/g" $TMP_DIR/TEMPLATE_COMP_NO_RED2_$COMP_NAME
				sed -i "s/#COMP_NAME#/$COMP_NAME/g" $TMP_DIR/TEMPLATE_COMP_NO_RED2_$COMP_NAME
				
				if isOldNamingConvention "$BUNDLE_NAME" ; then
					# Old naming convention for APG block's component type
					# safVersion=<Rstate>,safCompType=<CompTypeName>
					# Example: safVersion=R1E,safCompType=ERIC-APG_ASEC
				sed -i "s/#COMP_VERSION#/$COMP_VERSION/g" $TMP_DIR/TEMPLATE_COMP_NO_RED2_$COMP_NAME
				else
					# New naming convention for APG block's component type
					# safVersion=<CXC>-<Rstate>,safCompType=<CompTypeName>
					# Example: safVersion=CXC1371474-R1E,safCompType=ERIC-APG_ASEC
					BUNDLE_CXC=$(echo "$BUNDLE_NAME" | sed 's/-[^-]*$//' | awk -F'-' '{ print $NF }')
					sed -i "s/#COMP_VERSION#/$BUNDLE_CXC-$COMP_VERSION/g" $TMP_DIR/TEMPLATE_COMP_NO_RED2_$COMP_NAME
				fi
				
				sed -i "s/#COMP_TYPE_NAME#/$COMP_TYPE_NAME/g" $TMP_DIR/TEMPLATE_COMP_NO_RED2_$COMP_NAME
				sed -i "s/#CS_TYPE#/$CS_TYPE/g" $TMP_DIR/TEMPLATE_COMP_NO_RED2_$COMP_NAME
				sed -i "s/#SAF_VERSION#/$SAF_VERSION/g" $TMP_DIR/TEMPLATE_COMP_NO_RED2_$COMP_NAME
				sed -i "s/#HCK#/$HelthCheck/g" $TMP_DIR/TEMPLATE_COMP_NO_RED2_$COMP_NAME
				sed -i "s/#CSI_NAME#/$CSI_NAME/g" $TMP_DIR/TEMPLATE_COMP_NO_RED2_$COMP_NAME
				sed -i "s/#HCK_MAX_DURATION#/$HCK_MAX_DURATION/g" $TMP_DIR/TEMPLATE_COMP_NO_RED2_$COMP_NAME
				sed -i "s/#HCK_PERIOD#/$HCK_PERIOD/g" $TMP_DIR/TEMPLATE_COMP_NO_RED2_$COMP_NAME
				cat $TMP_DIR/TEMPLATE_COMP_NO_RED2_$COMP_NAME >> $TMP_DIR/final.xml
                                if shallExcludeApp $COMP_NAME; then
                                          cp $TEMPLATES_FOLDER/TEMPLATE_BUNDLE/template_end_apg $TMP_DIR/
                                          cat $TMP_DIR/template_end_apg >> $TMP_DIR/final.xml
                                          rm -f $TMP_DIR/template_end_apg
                                fi
			fi
		done < $TMP_DIR/$SOURCE_FILE_NAME
	fi
fi
is_verbose && echo "STEP: COMP 2 FOR NO_RED CREATION DONE"	

#END Creating COMP 2 NO_RED==========================================================================================================================================================================


#START Creating SU 2 2N==========================================================================================================================================================================

if [ "$OPT_RESIZE" = "" ] || [ "$OPT_RESIZE_ARG" = "1-2" ]; then
		cp $TEMPLATES_FOLDER/TEMPLATE_AP_APPS/template_su_2n_2 $TMP_DIR/
		sed -i "s/#SAF_APP#/$SAF_APP/g" $TMP_DIR/template_su_2n_2
		sed -i "s/#SG_2N#/$SG_2N/g" $TMP_DIR/template_su_2n_2
		sed -i "s/#SAF_VERSION#/$SAF_VERSION/g" $TMP_DIR/template_su_2n_2
		sed -i "s/#SU2_2N#/$SU2_2N/g" $TMP_DIR/template_su_2n_2
		sed -i "s/#SU_2N_TYPE#/$SU_2N_TYPE/g" $TMP_DIR/template_su_2n_2
		cat $TMP_DIR/template_su_2n_2 >> $TMP_DIR/final.xml
		is_verbose && echo "STEP: SU_2_2N DONE"
fi

#END Creating SU 2 2N=============================================================================================================================================================================


#START Creating component for 2N SU 2 ===================================================================================================================================================

if [ "$OPT_RESIZE" = "" ] || [ "$OPT_RESIZE_ARG" = "1-2" ]; then
	if [ "$OPT_MINI" = "$TRUE" ] ; then
		while read line    
		do    
			type=$(echo $line | awk -F';' '{print $1}')
			COMP_NAME=$(echo $line | awk -F';' '{print $3}')
			allowed_comp_2N_su2='COMSA ERIC-Sec-Control Agent DEVMON'
			is_allowed_comp_2N_su2=''
			for exc in $allowed_comp_2N_su2; do 
				if [ "$COMP_NAME" == "$exc" ]; then
					is_allowed_comp_2N_su2='true'
				fi
			done
			if [ "$is_allowed_comp_2N_su2" = "true" ]; then
				if [ "$type" = "2N" ]
					then
					BUNDLE_NAME=$(echo $line | awk -F';' '{print $2}')
					COMP_NAME=$(echo $line | awk -F';' '{print $3}')
					COMP_TYPE_NAME=$(echo $line | awk -F';' '{print $5}')
					CS_TYPE=$(echo $line | awk -F';' '{print $6}')
					COMP_VERSION=$(echo $line | awk -F';' '{print $7}')
					CLC_NAME=$(echo $line | awk -F';' '{print $8}')
					HelthCheck=$(echo $line | awk -F';' '{print $9}')
					if [ "$COMP_TYPE_NAME" = "ERIC-ComSa-Cmw" ]
						then
						cp $TEMPLATES_FOLDER/TEMPLATE_COMP_2N/TEMPLATE_COMP_2N_COMSA_2 $TMP_DIR/
						sed -i "s/#SU2_2N#/$SU2_2N/g" $TMP_DIR/TEMPLATE_COMP_2N_COMSA_2
						sed -i "s/#SG_2N#/$SG_2N/g" $TMP_DIR/TEMPLATE_COMP_2N_COMSA_2
						sed -i "s/#SAF_APP#/$SAF_APP/g" $TMP_DIR/TEMPLATE_COMP_2N_COMSA_2
						sed -i "s/#COMP_NAME#/$COMP_NAME/g" $TMP_DIR/TEMPLATE_COMP_2N_COMSA_2
						sed -i "s/#COMP_VERSION#/$COMP_VERSION/g" $TMP_DIR/TEMPLATE_COMP_2N_COMSA_2
						sed -i "s/#COMP_TYPE_NAME#/$COMP_TYPE_NAME/g" $TMP_DIR/TEMPLATE_COMP_2N_COMSA_2
						sed -i "s/#SAF_VERSION#/$SAF_VERSION/g" $TMP_DIR/TEMPLATE_COMP_2N_COMSA_2
						sed -i "s/#CS_TYPE#/$CS_TYPE/g" $TMP_DIR/TEMPLATE_COMP_2N_COMSA_2
						sed -i "s/#COMP_SSH_NAME#/$COMSA_COMP_SSHD/g" $TMP_DIR/TEMPLATE_COMP_2N_COMSA_2
						sed -i "s/#COMP_SSH_VERSION#/$COMSA_SSHD_RSTATE/g" $TMP_DIR/TEMPLATE_COMP_2N_COMSA_2
						sed -i "s/#CS_SSH_TYPE#/$COMSA_CS_SSHD/g" $TMP_DIR/TEMPLATE_COMP_2N_COMSA_2
            sed -i "s/#COMP_TLS_NAME#/$COMSA_COMP_TLSD/g" $TMP_DIR/TEMPLATE_COMP_2N_COMSA_2
            sed -i "s/#COMP_TLS_VERSION#/$COMSA_TLSD_RSTATE/g" $TMP_DIR/TEMPLATE_COMP_2N_COMSA_2
            sed -i "s/#CS_TLS_TYPE#/$COMSA_CS_TLSD/g" $TMP_DIR/TEMPLATE_COMP_2N_COMSA_2
            sed -i "s/#COMP_VSFTPD_NAME#/$COMSA_COMP_VSFTPD/g" $TMP_DIR/TEMPLATE_COMP_2N_COMSA_2
            sed -i "s/#COMP_VSFTPD_VERSION#/$COMSA_VSFTPD_RSTATE/g" $TMP_DIR/TEMPLATE_COMP_2N_COMSA_2
            sed -i "s/#CS_VSFTPD_TYPE#/$COMSA_CS_VSFTPD/g" $TMP_DIR/TEMPLATE_COMP_2N_COMSA_2
						cat $TMP_DIR/TEMPLATE_COMP_2N_COMSA_2 >> $TMP_DIR/final.xml
					else
						cp $TEMPLATES_FOLDER/TEMPLATE_COMP_2N/TEMPLATE_COMP_2N_2 $TMP_DIR/TEMPLATE_COMP_2N_2_$COMP_NAME
						sed -i "s/#SU2_2N#/$SU2_2N/g" $TMP_DIR/TEMPLATE_COMP_2N_2_$COMP_NAME
						sed -i "s/#SG_2N#/$SG_2N/g" $TMP_DIR/TEMPLATE_COMP_2N_2_$COMP_NAME
						sed -i "s/#SAF_APP#/$SAF_APP/g" $TMP_DIR/TEMPLATE_COMP_2N_2_$COMP_NAME
						sed -i "s/#COMP_NAME#/$COMP_NAME/g" $TMP_DIR/TEMPLATE_COMP_2N_2_$COMP_NAME
						
						if [ "$COMP_TYPE_NAME" != "ERIC-Sec-Control" ] ; then
							if isOldNamingConvention "$BUNDLE_NAME" ; then
								# Old naming convention for APG block's component type
								# safVersion=<Rstate>,safCompType=<CompTypeName>
								# Example: safVersion=R1E,safCompType=ERIC-APG_ASEC
								sed -i "s/#COMP_VERSION#/$COMP_VERSION/g" $TMP_DIR/TEMPLATE_COMP_2N_2_$COMP_NAME
							else
								# New naming convention for APG block's component type
								# safVersion=<CXC>-<Rstate>,safCompType=<CompTypeName>
								# Example: safVersion=CXC1371474-R1E,safCompType=ERIC-APG_ASEC
								BUNDLE_CXC=$(echo "$BUNDLE_NAME" | sed 's/-[^-]*$//' | awk -F'-' '{ print $NF }')
								sed -i "s/#COMP_VERSION#/$BUNDLE_CXC-$COMP_VERSION/g" $TMP_DIR/TEMPLATE_COMP_2N_2_$COMP_NAME
							fi
						else
							# SEC
							sed -i "s/#COMP_VERSION#/$COMP_VERSION/g" $TMP_DIR/TEMPLATE_COMP_2N_2_$COMP_NAME
						fi
						
						sed -i "s/#COMP_TYPE_NAME#/$COMP_TYPE_NAME/g" $TMP_DIR/TEMPLATE_COMP_2N_2_$COMP_NAME
						sed -i "s/#SAF_VERSION#/$SAF_VERSION/g" $TMP_DIR/TEMPLATE_COMP_2N_2_$COMP_NAME
						sed -i "s/#CS_TYPE#/$CS_TYPE/g" $TMP_DIR/TEMPLATE_COMP_2N_2_$COMP_NAME
						sed -i "s/#HCK#/$HelthCheck/g" $TMP_DIR/TEMPLATE_COMP_2N_2_$COMP_NAME
						if [ "$COMP_TYPE_NAME" = "ERIC-APG_Agent" ]
							then
							sed -i "s/#HCK_PERIOD_2N#/$HCK_PERIOD_AGENT/g" $TMP_DIR/TEMPLATE_COMP_2N_2_$COMP_NAME
							sed -i "s/#HCK_MAX_DURATION_2N#/$HCK_MAX_DURATION_AGENT/g" $TMP_DIR/TEMPLATE_COMP_2N_2_$COMP_NAME
						else
							sed -i "s/#HCK_PERIOD_2N#/$HCK_PERIOD/g" $TMP_DIR/TEMPLATE_COMP_2N_2_$COMP_NAME
							sed -i "s/#HCK_MAX_DURATION_2N#/$HCK_MAX_DURATION/g" $TMP_DIR/TEMPLATE_COMP_2N_2_$COMP_NAME				
						fi
						cat $TMP_DIR/TEMPLATE_COMP_2N_2_$COMP_NAME >> $TMP_DIR/final.xml
					fi
				fi
			fi
		done < $TMP_DIR/$SOURCE_FILE_NAME
	else
		while read line    
		do    
			type=$(echo $line | awk -F';' '{print $1}')
			if [ "$type" = "2N" ]
				then
				BUNDLE_NAME=$(echo $line | awk -F';' '{print $2}')
				COMP_NAME=$(echo $line | awk -F';' '{print $3}')
				COMP_TYPE_NAME=$(echo $line | awk -F';' '{print $5}')
				CS_TYPE=$(echo $line | awk -F';' '{print $6}')
				COMP_VERSION=$(echo $line | awk -F';' '{print $7}')
				CLC_NAME=$(echo $line | awk -F';' '{print $8}')
				HelthCheck=$(echo $line | awk -F';' '{print $9}')
				if [ "$COMP_TYPE_NAME" = "ERIC-ComSa-Cmw" ]
					then
					cp $TEMPLATES_FOLDER/TEMPLATE_COMP_2N/TEMPLATE_COMP_2N_COMSA_2 $TMP_DIR/
					sed -i "s/#SU2_2N#/$SU2_2N/g" $TMP_DIR/TEMPLATE_COMP_2N_COMSA_2
					sed -i "s/#SG_2N#/$SG_2N/g" $TMP_DIR/TEMPLATE_COMP_2N_COMSA_2
					sed -i "s/#SAF_APP#/$SAF_APP/g" $TMP_DIR/TEMPLATE_COMP_2N_COMSA_2
					sed -i "s/#COMP_NAME#/$COMP_NAME/g" $TMP_DIR/TEMPLATE_COMP_2N_COMSA_2
					sed -i "s/#COMP_VERSION#/$COMP_VERSION/g" $TMP_DIR/TEMPLATE_COMP_2N_COMSA_2
					sed -i "s/#COMP_TYPE_NAME#/$COMP_TYPE_NAME/g" $TMP_DIR/TEMPLATE_COMP_2N_COMSA_2
					sed -i "s/#SAF_VERSION#/$SAF_VERSION/g" $TMP_DIR/TEMPLATE_COMP_2N_COMSA_2
					sed -i "s/#CS_TYPE#/$CS_TYPE/g" $TMP_DIR/TEMPLATE_COMP_2N_COMSA_2
					sed -i "s/#COMP_SSH_NAME#/$COMSA_COMP_SSHD/g" $TMP_DIR/TEMPLATE_COMP_2N_COMSA_2
					sed -i "s/#COMP_SSH_VERSION#/$COMSA_SSHD_RSTATE/g" $TMP_DIR/TEMPLATE_COMP_2N_COMSA_2
					sed -i "s/#CS_SSH_TYPE#/$COMSA_CS_SSHD/g" $TMP_DIR/TEMPLATE_COMP_2N_COMSA_2
          sed -i "s/#COMP_TLS_NAME#/$COMSA_COMP_TLSD/g" $TMP_DIR/TEMPLATE_COMP_2N_COMSA_2
          sed -i "s/#COMP_TLS_VERSION#/$COMSA_TLSD_RSTATE/g" $TMP_DIR/TEMPLATE_COMP_2N_COMSA_2
          sed -i "s/#CS_TLS_TYPE#/$COMSA_CS_TLSD/g" $TMP_DIR/TEMPLATE_COMP_2N_COMSA_2
          sed -i "s/#COMP_VSFTPD_NAME#/$COMSA_COMP_VSFTPD/g" $TMP_DIR/TEMPLATE_COMP_2N_COMSA_2
          sed -i "s/#COMP_VSFTPD_VERSION#/$COMSA_VSFTPD_RSTATE/g" $TMP_DIR/TEMPLATE_COMP_2N_COMSA_2
          sed -i "s/#CS_VSFTPD_TYPE#/$COMSA_CS_VSFTPD/g" $TMP_DIR/TEMPLATE_COMP_2N_COMSA_2
					cat $TMP_DIR/TEMPLATE_COMP_2N_COMSA_2 >> $TMP_DIR/final.xml
				else
                                        if shallExcludeApp $COMP_NAME; then
                                               cp $TEMPLATES_FOLDER/TEMPLATE_BUNDLE/template_init_apg $TMP_DIR/
                                               sed -i "s/#PARAM#/$COMP_NAME/g" $TMP_DIR/template_init_apg
                                               sed -i "s/#SCRIPT#/$EXCLUDE_BUNDLES/g" $TMP_DIR/template_init_apg
                                               sed -i "s/#TYPE#/$INSTALL_TYPE/g" $TMP_DIR/template_init_apg
                                               cat $TMP_DIR/template_init_apg >> $TMP_DIR/final.xml
                                               rm -f $TMP_DIR/template_init_apg
                                        fi
					cp $TEMPLATES_FOLDER/TEMPLATE_COMP_2N/TEMPLATE_COMP_2N_2 $TMP_DIR/TEMPLATE_COMP_2N_2_$COMP_NAME
					sed -i "s/#SU2_2N#/$SU2_2N/g" $TMP_DIR/TEMPLATE_COMP_2N_2_$COMP_NAME
					sed -i "s/#SG_2N#/$SG_2N/g" $TMP_DIR/TEMPLATE_COMP_2N_2_$COMP_NAME
					sed -i "s/#SAF_APP#/$SAF_APP/g" $TMP_DIR/TEMPLATE_COMP_2N_2_$COMP_NAME
					sed -i "s/#COMP_NAME#/$COMP_NAME/g" $TMP_DIR/TEMPLATE_COMP_2N_2_$COMP_NAME
					
					if [ "$COMP_TYPE_NAME" != "ERIC-Sec-Control" ] ; then
						if isOldNamingConvention "$BUNDLE_NAME" ; then
							# Old naming convention for APG block's component type
							# safVersion=<Rstate>,safCompType=<CompTypeName>
							# Example: safVersion=R1E,safCompType=ERIC-APG_ASEC
							sed -i "s/#COMP_VERSION#/$COMP_VERSION/g" $TMP_DIR/TEMPLATE_COMP_2N_2_$COMP_NAME
						else
							# New naming convention for APG block's component type
							# safVersion=<CXC>-<Rstate>,safCompType=<CompTypeName>
							# Example: safVersion=CXC1371474-R1E,safCompType=ERIC-APG_ASEC
							BUNDLE_CXC=$(echo "$BUNDLE_NAME" | sed 's/-[^-]*$//' | awk -F'-' '{ print $NF }')
							sed -i "s/#COMP_VERSION#/$BUNDLE_CXC-$COMP_VERSION/g" $TMP_DIR/TEMPLATE_COMP_2N_2_$COMP_NAME
						fi
					else
						# SEC
						sed -i "s/#COMP_VERSION#/$COMP_VERSION/g" $TMP_DIR/TEMPLATE_COMP_2N_2_$COMP_NAME
					fi
					
					sed -i "s/#COMP_TYPE_NAME#/$COMP_TYPE_NAME/g" $TMP_DIR/TEMPLATE_COMP_2N_2_$COMP_NAME
					sed -i "s/#SAF_VERSION#/$SAF_VERSION/g" $TMP_DIR/TEMPLATE_COMP_2N_2_$COMP_NAME
					sed -i "s/#CS_TYPE#/$CS_TYPE/g" $TMP_DIR/TEMPLATE_COMP_2N_2_$COMP_NAME
					sed -i "s/#HCK#/$HelthCheck/g" $TMP_DIR/TEMPLATE_COMP_2N_2_$COMP_NAME
					if [ "$COMP_TYPE_NAME" = "ERIC-APG_Agent" ]
						then
						sed -i "s/#HCK_PERIOD_2N#/$HCK_PERIOD_AGENT/g" $TMP_DIR/TEMPLATE_COMP_2N_2_$COMP_NAME
						sed -i "s/#HCK_MAX_DURATION_2N#/$HCK_MAX_DURATION_AGENT/g" $TMP_DIR/TEMPLATE_COMP_2N_2_$COMP_NAME
					else
						sed -i "s/#HCK_PERIOD_2N#/$HCK_PERIOD/g" $TMP_DIR/TEMPLATE_COMP_2N_2_$COMP_NAME
						sed -i "s/#HCK_MAX_DURATION_2N#/$HCK_MAX_DURATION/g" $TMP_DIR/TEMPLATE_COMP_2N_2_$COMP_NAME				
					fi
					cat $TMP_DIR/TEMPLATE_COMP_2N_2_$COMP_NAME >> $TMP_DIR/final.xml
                                        if shallExcludeApp $COMP_NAME; then
                                                cp $TEMPLATES_FOLDER/TEMPLATE_BUNDLE/template_end_apg $TMP_DIR/
                                                cat $TMP_DIR/template_end_apg >> $TMP_DIR/final.xml
                                                rm -f $TMP_DIR/template_end_apg
                                        fi
				fi
			fi
		done < $TMP_DIR/$SOURCE_FILE_NAME
	fi
fi
is_verbose && echo "STEP: COMP 2 FOR 2N CREATION DONE"	

#END Creating component for 2N SU 2 ===================================================================================================================================================


#START Creating SI for 2N ==============================================================================================================================================================

if [ "$OPT_RESIZE" = "" ] || [ "$OPT_RESIZE_ARG" = "0-1" ]; then
	if [ "$OPT_MINI" = "$TRUE" ] ; then
		allowed_SI_2N='COMSA ERIC-Sec-Control Agent DEVMON'
		while read line    
		do    
			type=$(echo $line | awk -F';' '{print $1}')
			COMP_NAME=$(echo $line | awk -F';' '{print $3}')
			SI_NAME=$(echo $line | awk -F';' '{print $10}')
			CSI_NAME=$(echo $line | awk -F';' '{print $11}')
			is_allowed_SI_2N=''
			for exc in $allowed_SI_2N; do 
				if [ "$COMP_NAME" == "$exc" ]; then
					is_allowed_SI_2N='true'
				fi
			done
			if [ "$is_allowed_SI_2N" = "true" ]; then
				if [ "$type" = "2N" ]
				then
					cp $TEMPLATES_FOLDER/TEMPLATE_SI/template_si_2n $TMP_DIR/template_si_2n_$COMP_NAME
					sed -i "s/#SAF_APP#/$SAF_APP/g" $TMP_DIR/template_si_2n_$COMP_NAME
					sed -i "s/#SAF_VERSION#/$SAF_VERSION/g" $TMP_DIR/template_si_2n_$COMP_NAME
					sed -i "s/#SG_2N#/$SG_2N/g" $TMP_DIR/template_si_2n_$COMP_NAME
					sed -i "s/#SAF_SI#/$CSI_NAME/g" $TMP_DIR/template_si_2n_$COMP_NAME
					sed -i "s/#SAF_SVC_TYPE#/$SI_NAME/g" $TMP_DIR/template_si_2n_$COMP_NAME
					if [ "$CSI_NAME" = "AGENT" ]
					then
						sed -i "s/#SI_RANK_2N#/$SI_RANK_AGENT/g" $TMP_DIR/template_si_2n_$COMP_NAME
						cat $TMP_DIR/template_si_2n_$COMP_NAME >> $TMP_DIR/final.xml
					elif [ "$CSI_NAME" = "COMSA" ]
					then
						sed -i "s/#SI_RANK_2N#/$SI_RANK_COMSA/g" $TMP_DIR/template_si_2n_$COMP_NAME
						cat $TMP_DIR/template_si_2n_$COMP_NAME >> $TMP_DIR/final.xml
						#DEPENDENCY FOR COMSA SI
						cp $TEMPLATES_FOLDER/TEMPLATE_SI/template_si_dependency $TMP_DIR/template_si_dependency_$COMP_NAME
						sed -i "s/#SAF_APP#/$SAF_APP/g" $TMP_DIR/template_si_dependency_$COMP_NAME
						sed -i "s/#SAF_SVC_TYPE#/$CSI_NAME/g" $TMP_DIR/template_si_dependency_$COMP_NAME
						sed -i "s/#SI_NAME_AGENT#/$SI_NAME_AGENT/g" $TMP_DIR/template_si_dependency_$COMP_NAME
						cat $TMP_DIR/template_si_dependency_$COMP_NAME >> $TMP_DIR/final.xml
					else
                                                if shallExcludeApp $COMP_NAME; then
                                                        cp $TEMPLATES_FOLDER/TEMPLATE_BUNDLE/template_init_apg $TMP_DIR/
                                                        sed -i "s/#PARAM#/$COMP_NAME/g" $TMP_DIR/template_init_apg
                                                        sed -i "s/#SCRIPT#/$EXCLUDE_BUNDLES/g" $TMP_DIR/template_init_apg
                                                        sed -i "s/#TYPE#/$INSTALL_TYPE/g" $TMP_DIR/template_init_apg
                                                        cat $TMP_DIR/template_init_apg >> $TMP_DIR/final.xml
                                                        rm -f $TMP_DIR/template_init_apg
                                                fi
						sed -i "s/#SI_RANK_2N#/$SI_RANK_2N/g" $TMP_DIR/template_si_2n_$COMP_NAME
						cp $TEMPLATES_FOLDER/TEMPLATE_SI/template_si_dependency $TMP_DIR/template_si_dependency_$COMP_NAME
						sed -i "s/#SAF_APP#/$SAF_APP/g" $TMP_DIR/template_si_dependency_$COMP_NAME
						sed -i "s/#SAF_SVC_TYPE#/$CSI_NAME/g" $TMP_DIR/template_si_dependency_$COMP_NAME
						sed -i "s/#SI_NAME_AGENT#/$SI_NAME_AGENT/g" $TMP_DIR/template_si_dependency_$COMP_NAME
						cat $TMP_DIR/template_si_2n_$COMP_NAME >> $TMP_DIR/final.xml
						cat $TMP_DIR/template_si_dependency_$COMP_NAME >> $TMP_DIR/final.xml
                                                if shallExcludeApp $COMP_NAME; then
                                                        cp $TEMPLATES_FOLDER/TEMPLATE_BUNDLE/template_end_apg $TMP_DIR/
                                                        cat $TMP_DIR/template_end_apg >> $TMP_DIR/final.xml
                                                        rm -f $TMP_DIR/template_end_apg
                                                fi
					fi
				fi
			fi
		done < $TMP_DIR/$SOURCE_FILE_NAME
	else
		while read line    
		do    
			type=$(echo $line | awk -F';' '{print $1}')
			COMP_NAME=$(echo $line | awk -F';' '{print $3}')
			SI_NAME=$(echo $line | awk -F';' '{print $10}')
			CSI_NAME=$(echo $line | awk -F';' '{print $11}')
			if [ "$type" = "2N" ]
			then
				cp $TEMPLATES_FOLDER/TEMPLATE_SI/template_si_2n $TMP_DIR/template_si_2n_$COMP_NAME
				sed -i "s/#SAF_APP#/$SAF_APP/g" $TMP_DIR/template_si_2n_$COMP_NAME
				sed -i "s/#SAF_VERSION#/$SAF_VERSION/g" $TMP_DIR/template_si_2n_$COMP_NAME
				sed -i "s/#SG_2N#/$SG_2N/g" $TMP_DIR/template_si_2n_$COMP_NAME
				sed -i "s/#SAF_SI#/$CSI_NAME/g" $TMP_DIR/template_si_2n_$COMP_NAME
				sed -i "s/#SAF_SVC_TYPE#/$SI_NAME/g" $TMP_DIR/template_si_2n_$COMP_NAME
				if [ "$CSI_NAME" = "AGENT" ]
				then
					sed -i "s/#SI_RANK_2N#/$SI_RANK_AGENT/g" $TMP_DIR/template_si_2n_$COMP_NAME
					cat $TMP_DIR/template_si_2n_$COMP_NAME >> $TMP_DIR/final.xml
				elif [ "$CSI_NAME" = "COMSA" ]
				then
					sed -i "s/#SI_RANK_2N#/$SI_RANK_COMSA/g" $TMP_DIR/template_si_2n_$COMP_NAME
					cat $TMP_DIR/template_si_2n_$COMP_NAME >> $TMP_DIR/final.xml
					#DEPENDENCY FOR COMSA SI
					cp $TEMPLATES_FOLDER/TEMPLATE_SI/template_si_dependency $TMP_DIR/template_si_dependency_$COMP_NAME
					sed -i "s/#SAF_APP#/$SAF_APP/g" $TMP_DIR/template_si_dependency_$COMP_NAME
					sed -i "s/#SAF_SVC_TYPE#/$CSI_NAME/g" $TMP_DIR/template_si_dependency_$COMP_NAME
					sed -i "s/#SI_NAME_AGENT#/$SI_NAME_AGENT/g" $TMP_DIR/template_si_dependency_$COMP_NAME
					cat $TMP_DIR/template_si_dependency_$COMP_NAME >> $TMP_DIR/final.xml
				else
                                        if shallExcludeApp $COMP_NAME; then
					       cp $TEMPLATES_FOLDER/TEMPLATE_BUNDLE/template_init_apg $TMP_DIR/
                                               sed -i "s/#PARAM#/$COMP_NAME/g" $TMP_DIR/template_init_apg
                                               sed -i "s/#SCRIPT#/$EXCLUDE_BUNDLES/g" $TMP_DIR/template_init_apg
                                               sed -i "s/#TYPE#/$INSTALL_TYPE/g" $TMP_DIR/template_init_apg
                                               cat $TMP_DIR/template_init_apg >> $TMP_DIR/final.xml
                                               rm -f $TMP_DIR/template_init_apg
                                        fi
					sed -i "s/#SI_RANK_2N#/$SI_RANK_2N/g" $TMP_DIR/template_si_2n_$COMP_NAME
					cp $TEMPLATES_FOLDER/TEMPLATE_SI/template_si_dependency $TMP_DIR/template_si_dependency_$COMP_NAME
					sed -i "s/#SAF_APP#/$SAF_APP/g" $TMP_DIR/template_si_dependency_$COMP_NAME
					sed -i "s/#SAF_SVC_TYPE#/$CSI_NAME/g" $TMP_DIR/template_si_dependency_$COMP_NAME
					sed -i "s/#SI_NAME_AGENT#/$SI_NAME_AGENT/g" $TMP_DIR/template_si_dependency_$COMP_NAME
					cat $TMP_DIR/template_si_2n_$COMP_NAME >> $TMP_DIR/final.xml
					cat $TMP_DIR/template_si_dependency_$COMP_NAME >> $TMP_DIR/final.xml
                                        if shallExcludeApp $COMP_NAME; then
                                                 cp $TEMPLATES_FOLDER/TEMPLATE_BUNDLE/template_end_apg $TMP_DIR/
                                                 cat $TMP_DIR/template_end_apg >> $TMP_DIR/final.xml
                                                 rm -f $TMP_DIR/template_end_apg
                                        fi
				fi
			fi
		done < $TMP_DIR/$SOURCE_FILE_NAME
	fi
fi
is_verbose && echo "STEP: SI FOR 2N CREATION DONE"

#END Creating SI for 2N =============================================================================================================================================================


#START Creating SI for NORED ==============================================================================================================================================================
#####
# Part for multiple SI for NORED
#####
if [ "$OPT_MINI" != "$TRUE" ] ; then
	while read line    
	do    
	type=$(echo $line | awk -F';' '{print $1}')
		if [ "$type" = "NORED" ]
		then
			COMP_NAME=$(echo $line | awk -F';' '{print $3}')
			SI_NAME=$(echo $line | awk -F';' '{print $10}')
			CSI_NAME=$(echo $line | awk -F';' '{print $11}')
                        if shallExcludeApp $COMP_NAME; then
			           cp $TEMPLATES_FOLDER/TEMPLATE_BUNDLE/template_init_apg $TMP_DIR/
			           sed -i "s/#PARAM#/$COMP_NAME/g" $TMP_DIR/template_init_apg
                                   sed -i "s/#SCRIPT#/$EXCLUDE_BUNDLES/g" $TMP_DIR/template_init_apg
                                   sed -i "s/#TYPE#/$INSTALL_TYPE/g" $TMP_DIR/template_init_apg
			           cat $TMP_DIR/template_init_apg >> $TMP_DIR/final.xml
                                   rm -f $TMP_DIR/template_init_apg
                        fi
			if [ "$OPT_RESIZE" = "" ]; then
				cp $TEMPLATES_FOLDER/TEMPLATE_SI/template_si_nored_1 $TMP_DIR/template_si_nored_1_$COMP_NAME
				cp $TEMPLATES_FOLDER/TEMPLATE_SI/template_si_nored_2 $TMP_DIR/template_si_nored_2_$COMP_NAME
				sed -i "s/#SAF_APP#/$SAF_APP/g" $TMP_DIR/template_si_nored_1_$COMP_NAME
				sed -i "s/#SAF_APP#/$SAF_APP/g" $TMP_DIR/template_si_nored_2_$COMP_NAME
				sed -i "s/#SAF_VERSION#/$SAF_VERSION/g" $TMP_DIR/template_si_nored_1_$COMP_NAME
				sed -i "s/#SAF_VERSION#/$SAF_VERSION/g" $TMP_DIR/template_si_nored_2_$COMP_NAME
				sed -i "s/#SI_RANK_NORED#/$SI_RANK_NORED/g" $TMP_DIR/template_si_nored_1_$COMP_NAME
				sed -i "s/#SI_RANK_NORED#/$SI_RANK_NORED/g" $TMP_DIR/template_si_nored_2_$COMP_NAME
				sed -i "s/#CSI_NAME#/$CSI_NAME/g" $TMP_DIR/template_si_nored_1_$COMP_NAME
				sed -i "s/#CSI_NAME#/$CSI_NAME/g" $TMP_DIR/template_si_nored_2_$COMP_NAME
				cat $TMP_DIR/template_si_nored_1_$COMP_NAME >> $TMP_DIR/final.xml
				cat $TMP_DIR/template_si_nored_2_$COMP_NAME >> $TMP_DIR/final.xml
			elif [ "$OPT_RESIZE_ARG" = "0-1" ]; then
				cp $TEMPLATES_FOLDER/TEMPLATE_SI/template_si_nored_1 $TMP_DIR/template_si_nored_1_$COMP_NAME
				sed -i "s/#SAF_APP#/$SAF_APP/g" $TMP_DIR/template_si_nored_1_$COMP_NAME
				sed -i "s/#SAF_VERSION#/$SAF_VERSION/g" $TMP_DIR/template_si_nored_1_$COMP_NAME
				sed -i "s/#SI_RANK_NORED#/$SI_RANK_NORED/g" $TMP_DIR/template_si_nored_1_$COMP_NAME
				sed -i "s/#CSI_NAME#/$CSI_NAME/g" $TMP_DIR/template_si_nored_1_$COMP_NAME
				cat $TMP_DIR/template_si_nored_1_$COMP_NAME >> $TMP_DIR/final.xml
			elif [ "$OPT_RESIZE_ARG" = "1-2" ]; then
				cp $TEMPLATES_FOLDER/TEMPLATE_SI/template_si_nored_2 $TMP_DIR/template_si_nored_2_$COMP_NAME
				sed -i "s/#SAF_APP#/$SAF_APP/g" $TMP_DIR/template_si_nored_2_$COMP_NAME
				sed -i "s/#SAF_VERSION#/$SAF_VERSION/g" $TMP_DIR/template_si_nored_2_$COMP_NAME
				sed -i "s/#SI_RANK_NORED#/$SI_RANK_NORED/g" $TMP_DIR/template_si_nored_2_$COMP_NAME
				sed -i "s/#CSI_NAME#/$CSI_NAME/g" $TMP_DIR/template_si_nored_2_$COMP_NAME
				cat $TMP_DIR/template_si_nored_2_$COMP_NAME >> $TMP_DIR/final.xml
			fi
                        if shallExcludeApp $COMP_NAME; then
                                 cp $TEMPLATES_FOLDER/TEMPLATE_BUNDLE/template_end_apg $TMP_DIR/
                                 cat $TMP_DIR/template_end_apg >> $TMP_DIR/final.xml
                                 rm -f $TMP_DIR/template_end_apg
                        fi
		fi
	done < $TMP_DIR/$SOURCE_FILE_NAME
	is_verbose && echo "STEP: SI FOR NORED CREATION DONE"	
fi

#END Creating SI for NORED =============================================================================================================================================================


#START Creating CSI for 2N ===================================================================================================================================================

if [ "$OPT_RESIZE" = "" ] || [ "$OPT_RESIZE_ARG" = "0-1" ]; then
	allowed_CSI_2N='COMSA ERIC-Sec-Control Agent DEVMON'
	if [ "$OPT_MINI" = "$TRUE" ] ; then
		while read line    
		do    
			type=$(echo $line | awk -F';' '{print $1}')
			COMP_NAME=$(echo $line | awk -F';' '{print $3}')
			is_allowed_CSI_2N=''
			for exc in $allowed_CSI_2N; do 
				if [ "$COMP_NAME" == "$exc" ]; then
					is_allowed_CSI_2N='true'
				fi
			done
			if [ "$is_allowed_CSI_2N" = "true" ]; then
				if [ "$type" = "2N" ]
				then
					CS_TYPE=$(echo $line | awk -F';' '{print $6}')
					SI_NAME=$(echo $line | awk -F';' '{print $10}')
					CSI_NAME=$(echo $line | awk -F';' '{print $11}')
					cp $TEMPLATES_FOLDER/TEMPLATE_CSI/template_csi_2n $TMP_DIR/template_csi_2n_$COMP_NAME
					sed -i "s/#SAF_APP#/$SAF_APP/g" $TMP_DIR/template_csi_2n_$COMP_NAME
					sed -i "s/#SI_NAME#/$CSI_NAME/g" $TMP_DIR/template_csi_2n_$COMP_NAME
					sed -i "s/#CSI_NAME#/$CSI_NAME/g" $TMP_DIR/template_csi_2n_$COMP_NAME		
					sed -i "s/#SAF_VERSION#/$SAF_VERSION/g" $TMP_DIR/template_csi_2n_$COMP_NAME
					sed -i "s/#CS_TYPE#/$CS_TYPE/g" $TMP_DIR/template_csi_2n_$COMP_NAME
					cat $TMP_DIR/template_csi_2n_$COMP_NAME >> $TMP_DIR/final.xml
				fi
			fi
		done < $TMP_DIR/$SOURCE_FILE_NAME
	else
		while read line    
		do    
			type=$(echo $line | awk -F';' '{print $1}')
			if [ "$type" = "2N" ]
			then
				COMP_NAME=$(echo $line | awk -F';' '{print $3}')
				CS_TYPE=$(echo $line | awk -F';' '{print $6}')
				SI_NAME=$(echo $line | awk -F';' '{print $10}')
				CSI_NAME=$(echo $line | awk -F';' '{print $11}')
				if [ "$CSI_NAME" = "COMSA" ];then
				cp $TEMPLATES_FOLDER/TEMPLATE_CSI/template_csi_2n $TMP_DIR/template_csi_2n_$COMP_NAME
				sed -i "s/#SAF_APP#/$SAF_APP/g" $TMP_DIR/template_csi_2n_$COMP_NAME
				sed -i "s/#SI_NAME#/$CSI_NAME/g" $TMP_DIR/template_csi_2n_$COMP_NAME
				sed -i "s/#CSI_NAME#/$CSI_NAME/g" $TMP_DIR/template_csi_2n_$COMP_NAME		
				sed -i "s/#SAF_VERSION#/$SAF_VERSION/g" $TMP_DIR/template_csi_2n_$COMP_NAME
				sed -i "s/#CS_TYPE#/$CS_TYPE/g" $TMP_DIR/template_csi_2n_$COMP_NAME
				cat $TMP_DIR/template_csi_2n_$COMP_NAME >> $TMP_DIR/final.xml
				cp $TEMPLATES_FOLDER/TEMPLATE_CSI/template_csi_2n_comsa_sshd $TMP_DIR/template_csi_2n_sshd
				sed -i "s/#SAF_APP#/$SAF_APP/g" $TMP_DIR/template_csi_2n_sshd
				sed -i "s/#SI_NAME#/$CSI_NAME/g" $TMP_DIR/template_csi_2n_sshd
				sed -i "s/#SAF_VERSION#/$SAF_VERSION/g" $TMP_DIR/template_csi_2n_sshd
				sed -i "s/#CSI_NAME#/$CSI_NAME/g" $TMP_DIR/template_csi_2n_sshd	
				sed -i "s/#CSI_SSH_NAME#/$COMSA_COMP_SSHD/g" $TMP_DIR/template_csi_2n_sshd
				sed -i "s/#CS_TYPE#/$COMSA_CS_SSHD/g" $TMP_DIR/template_csi_2n_sshd
				cat $TMP_DIR/template_csi_2n_sshd >> $TMP_DIR/final.xml
				rm -f $TMP_DIR/template_csi_2n_sshd
        cp $TEMPLATES_FOLDER/TEMPLATE_CSI/template_csi_2n_comsa_tlsd $TMP_DIR/template_csi_2n_tlsd
        sed -i "s/#SAF_APP#/$SAF_APP/g" $TMP_DIR/template_csi_2n_tlsd
        sed -i "s/#SI_NAME#/$CSI_NAME/g" $TMP_DIR/template_csi_2n_tlsd
        sed -i "s/#SAF_VERSION#/$SAF_VERSION/g" $TMP_DIR/template_csi_2n_tlsd
        sed -i "s/#CSI_NAME#/$CSI_NAME/g" $TMP_DIR/template_csi_2n_tlsd
        sed -i "s/#CSI_TLS_NAME#/$COMSA_COMP_TLSD/g" $TMP_DIR/template_csi_2n_tlsd
        sed -i "s/#CS_TYPE#/$COMSA_CS_TLSD/g" $TMP_DIR/template_csi_2n_tlsd
        cat $TMP_DIR/template_csi_2n_tlsd >> $TMP_DIR/final.xml
        rm -f $TMP_DIR/template_csi_2n_tlsd
        cp $TEMPLATES_FOLDER/TEMPLATE_CSI/template_csi_2n_comsa_vsftpd $TMP_DIR/template_csi_2n_vsftpd
        sed -i "s/#SAF_APP#/$SAF_APP/g" $TMP_DIR/template_csi_2n_vsftpd
        sed -i "s/#SI_NAME#/$CSI_NAME/g" $TMP_DIR/template_csi_2n_vsftpd
        sed -i "s/#SAF_VERSION#/$SAF_VERSION/g" $TMP_DIR/template_csi_2n_vsftpd
        sed -i "s/#CSI_NAME#/$CSI_NAME/g" $TMP_DIR/template_csi_2n_vsftpd
        sed -i "s/#CSI_VSFTPD_NAME#/$COMSA_COMP_VSFTPD/g" $TMP_DIR/template_csi_2n_vsftpd
        sed -i "s/#CS_TYPE#/$COMSA_CS_VSFTPD/g" $TMP_DIR/template_csi_2n_vsftpd
        cat $TMP_DIR/template_csi_2n_vsftpd >> $TMP_DIR/final.xml
        rm -f $TMP_DIR/template_csi_2n_vsftpd


				else
                                if shallExcludeApp $COMP_NAME; then
                                        cp $TEMPLATES_FOLDER/TEMPLATE_BUNDLE/template_init_apg $TMP_DIR/
                                        sed -i "s/#PARAM#/$COMP_NAME/g" $TMP_DIR/template_init_apg
                                        sed -i "s/#SCRIPT#/$EXCLUDE_BUNDLES/g" $TMP_DIR/template_init_apg
                                        sed -i "s/#TYPE#/$INSTALL_TYPE/g" $TMP_DIR/template_init_apg
                                        cat $TMP_DIR/template_init_apg >> $TMP_DIR/final.xml
                                        rm -f $TMP_DIR/template_init_apg
                                fi
				cp $TEMPLATES_FOLDER/TEMPLATE_CSI/template_csi_2n $TMP_DIR/template_csi_2n_$COMP_NAME
                                sed -i "s/#SAF_APP#/$SAF_APP/g" $TMP_DIR/template_csi_2n_$COMP_NAME
                                sed -i "s/#SI_NAME#/$CSI_NAME/g" $TMP_DIR/template_csi_2n_$COMP_NAME
                                sed -i "s/#CSI_NAME#/$CSI_NAME/g" $TMP_DIR/template_csi_2n_$COMP_NAME
                                sed -i "s/#SAF_VERSION#/$SAF_VERSION/g" $TMP_DIR/template_csi_2n_$COMP_NAME
                                sed -i "s/#CS_TYPE#/$CS_TYPE/g" $TMP_DIR/template_csi_2n_$COMP_NAME
                                cat $TMP_DIR/template_csi_2n_$COMP_NAME >> $TMP_DIR/final.xml
                                if shallExcludeApp $COMP_NAME; then 
                                          cp $TEMPLATES_FOLDER/TEMPLATE_BUNDLE/template_end_apg $TMP_DIR/
                                          cat $TMP_DIR/template_end_apg >> $TMP_DIR/final.xml
                                          rm -f $TMP_DIR/template_end_apg
                                fi
				fi
			fi
		done < $TMP_DIR/$SOURCE_FILE_NAME
	fi
fi
is_verbose && echo "STEP: CSI FOR 2N CREATION DONE"	
	
#END Creating CSI for 2N ===================================================================================================================================================


#START Creating CSI for NO_RED ===================================================================================================================================================

if [ "$OPT_MINI" != "$TRUE" ] ; then
	while read line    
	do    
		type=$(echo $line | awk -F';' '{print $1}')
		if [ "$type" = "NORED" ]
		then
			COMP_NAME=$(echo $line | awk -F';' '{print $3}')
			CS_TYPE=$(echo $line | awk -F';' '{print $6}')
			SI_NAME=$(echo $line | awk -F';' '{print $10}')
			CSI_NAME=$(echo $line | awk -F';' '{print $11}')
                       if shallExcludeApp $COMP_NAME; then
                               cp $TEMPLATES_FOLDER/TEMPLATE_BUNDLE/template_init_apg $TMP_DIR/
                               sed -i "s/#PARAM#/$COMP_NAME/g" $TMP_DIR/template_init_apg
                               sed -i "s/#SCRIPT#/$EXCLUDE_BUNDLES/g" $TMP_DIR/template_init_apg
                               sed -i "s/#TYPE#/$INSTALL_TYPE/g" $TMP_DIR/template_init_apg
                               cat $TMP_DIR/template_init_apg >> $TMP_DIR/final.xml
                               rm -f $TMP_DIR/template_init_apg
                       fi
			if [ "$OPT_RESIZE" = "" ]; then
				cp $TEMPLATES_FOLDER/TEMPLATE_CSI/template_csi_nored_1 $TMP_DIR/template_csi_nored_1_$COMP_NAME
				cp $TEMPLATES_FOLDER/TEMPLATE_CSI/template_csi_nored_2 $TMP_DIR/template_csi_nored_2_$COMP_NAME
				sed -i "s/#SAF_APP#/$SAF_APP/g" $TMP_DIR/template_csi_nored_1_$COMP_NAME
				sed -i "s/#SAF_APP#/$SAF_APP/g" $TMP_DIR/template_csi_nored_2_$COMP_NAME
				sed -i "s/#CSI_NAME#/$CSI_NAME/g" $TMP_DIR/template_csi_nored_1_$COMP_NAME
				sed -i "s/#CSI_NAME#/$CSI_NAME/g" $TMP_DIR/template_csi_nored_2_$COMP_NAME
				sed -i "s/#SAF_VERSION#/$SAF_VERSION/g" $TMP_DIR/template_csi_nored_1_$COMP_NAME
				sed -i "s/#SAF_VERSION#/$SAF_VERSION/g" $TMP_DIR/template_csi_nored_2_$COMP_NAME
				sed -i "s/#CS_TYPE#/$CS_TYPE/g" $TMP_DIR/template_csi_nored_1_$COMP_NAME
				sed -i "s/#CS_TYPE#/$CS_TYPE/g" $TMP_DIR/template_csi_nored_2_$COMP_NAME
				cat $TMP_DIR/template_csi_nored_1_$COMP_NAME >> $TMP_DIR/final.xml
				cat $TMP_DIR/template_csi_nored_2_$COMP_NAME >> $TMP_DIR/final.xml
			elif [ "$OPT_RESIZE_ARG" = "0-1" ]; then
				cp $TEMPLATES_FOLDER/TEMPLATE_CSI/template_csi_nored_1 $TMP_DIR/template_csi_nored_1_$COMP_NAME
				sed -i "s/#SAF_APP#/$SAF_APP/g" $TMP_DIR/template_csi_nored_1_$COMP_NAME
				sed -i "s/#CSI_NAME#/$CSI_NAME/g" $TMP_DIR/template_csi_nored_1_$COMP_NAME
				sed -i "s/#SAF_VERSION#/$SAF_VERSION/g" $TMP_DIR/template_csi_nored_1_$COMP_NAME
				sed -i "s/#CS_TYPE#/$CS_TYPE/g" $TMP_DIR/template_csi_nored_1_$COMP_NAME
				cat $TMP_DIR/template_csi_nored_1_$COMP_NAME >> $TMP_DIR/final.xml
			elif [ "$OPT_RESIZE_ARG" = "1-2" ]; then
				cp $TEMPLATES_FOLDER/TEMPLATE_CSI/template_csi_nored_2 $TMP_DIR/template_csi_nored_2_$COMP_NAME
				sed -i "s/#SAF_APP#/$SAF_APP/g" $TMP_DIR/template_csi_nored_2_$COMP_NAME
				sed -i "s/#CSI_NAME#/$CSI_NAME/g" $TMP_DIR/template_csi_nored_2_$COMP_NAME
				sed -i "s/#SAF_VERSION#/$SAF_VERSION/g" $TMP_DIR/template_csi_nored_2_$COMP_NAME
				sed -i "s/#CS_TYPE#/$CS_TYPE/g" $TMP_DIR/template_csi_nored_2_$COMP_NAME
				cat $TMP_DIR/template_csi_nored_2_$COMP_NAME >> $TMP_DIR/final.xml				
			fi
                        if shallExcludeApp $COMP_NAME; then
                                     cp $TEMPLATES_FOLDER/TEMPLATE_BUNDLE/template_end_apg $TMP_DIR/
                                     cat $TMP_DIR/template_end_apg >> $TMP_DIR/final.xml
                                     rm -f $TMP_DIR/template_end_apg
                        fi
		fi
	done < $TMP_DIR/$SOURCE_FILE_NAME
fi
cp $TEMPLATES_FOLDER/TEMPLATE_CSI/template_csi_end $TMP_DIR/template_csi_end
cat $TMP_DIR/template_csi_end >> $TMP_DIR/final.xml
is_verbose && echo "STEP: CSI FOR NO_RED CREATION DONE"	
	
#END Creating CSI for NO_RED ===================================================================================================================================================


#START ACTED ON part ===================================================================================================================================================

#INIT PART
cp $TEMPLATES_FOLDER/TEMPLATE_BUNDLE/template_bundle_acted_init $TMP_DIR/
sed -i "s/#SCRIPT#/$EXCLUDE_BUNDLES/" $TMP_DIR/template_bundle_acted_init
cat $TMP_DIR/template_bundle_acted_init >> $TMP_DIR/final.xml
if [ "$OPT_MINI" = "$TRUE" ] ; then
	#SU 1 2N
             if isSuPresent $SU1_2N $SG_2N ;then
                    cp $TEMPLATES_FOLDER/TEMPLATE_BUNDLE/template_su_init_apg $TMP_DIR/
                    sed -i "s/#SCRIPT#/$EXCLUDE_BUNDLES/" $TMP_DIR/template_su_init_apg
		    sed -i "s/#TYPE#/$ACTIVATE_TYPE/g" $TMP_DIR/template_su_init_apg
		    sed -i "s/#SU#/$SU1_2N/g" $TMP_DIR/template_su_init_apg
		    sed -i "s/#SAF_APP#/$SAF_APP/g" $TMP_DIR/template_su_init_apg
		    sed -i "s/#SG#/$SG_2N/g" $TMP_DIR/template_su_init_apg
                    cat $TMP_DIR/template_su_init_apg >> $TMP_DIR/final.xml
                    rm -f $TMP_DIR/template_su_init_apg
                 fi
        cp $TEMPLATES_FOLDER/TEMPLATE_BUNDLE/template_bundle_acted_su1_2n $TMP_DIR/
	sed -i "s/#SU1_2N#/$SU1_2N/g" $TMP_DIR/template_bundle_acted_su1_2n
	sed -i "s/#SAF_APP#/$SAF_APP/g" $TMP_DIR/template_bundle_acted_su1_2n
	sed -i "s/#SG_2N#/$SG_2N/g" $TMP_DIR/template_bundle_acted_su1_2n
	cat $TMP_DIR/template_bundle_acted_su1_2n >> $TMP_DIR/final.xml
                if isSuPresent $SU1_2N $SG_2N ;then
                    cp $TEMPLATES_FOLDER/TEMPLATE_BUNDLE/template_end_apg $TMP_DIR/
                    cat $TMP_DIR/template_end_apg >> $TMP_DIR/final.xml
                    rm -f $TMP_DIR/template_end_apg
                fi
	#SU 2 2N
             if isSuPresent $SU2_2N $SG_2N ;then
                    cp $TEMPLATES_FOLDER/TEMPLATE_BUNDLE/template_su_init_apg $TMP_DIR/
                    sed -i "s/#SCRIPT#/$EXCLUDE_BUNDLES/" $TMP_DIR/template_su_init_apg
		    sed -i "s/#TYPE#/$ACTIVATE_TYPE/g" $TMP_DIR/template_su_init_apg
		    sed -i "s/#SU#/$SU2_2N/g" $TMP_DIR/template_su_init_apg
		    sed -i "s/#SAF_APP#/$SAF_APP/g" $TMP_DIR/template_su_init_apg
		    sed -i "s/#SG#/$SG_2N/g" $TMP_DIR/template_su_init_apg
                    cat $TMP_DIR/template_su_init_apg >> $TMP_DIR/final.xml
                    rm -f $TMP_DIR/template_su_init_apg
                 fi
        cp $TEMPLATES_FOLDER/TEMPLATE_BUNDLE/template_bundle_acted_su2_2n $TMP_DIR/
	sed -i "s/#SU2_2N#/$SU2_2N/g" $TMP_DIR/template_bundle_acted_su2_2n
	sed -i "s/#SAF_APP#/$SAF_APP/g" $TMP_DIR/template_bundle_acted_su2_2n
	sed -i "s/#SG_2N#/$SG_2N/g" $TMP_DIR/template_bundle_acted_su2_2n
	cat $TMP_DIR/template_bundle_acted_su2_2n >> $TMP_DIR/final.xml
                if isSuPresent $SU2_2N $SG_2N ;then
                    cp $TEMPLATES_FOLDER/TEMPLATE_BUNDLE/template_end_apg $TMP_DIR/
                    cat $TMP_DIR/template_end_apg >> $TMP_DIR/final.xml
                    rm -f $TMP_DIR/template_end_apg
                fi
else
	       if [ "$OPT_RESIZE" = "" ] || [ "$OPT_RESIZE_ARG" = "0-1" ]; then
		#SU 1 2N
                 if isSuPresent $SU1_2N $SG_2N ;then
                    cp $TEMPLATES_FOLDER/TEMPLATE_BUNDLE/template_su_init_apg $TMP_DIR/
                    sed -i "s/#SCRIPT#/$EXCLUDE_BUNDLES/" $TMP_DIR/template_su_init_apg
		    sed -i "s/#TYPE#/$ACTIVATE_TYPE/g" $TMP_DIR/template_su_init_apg
		    sed -i "s/#SU#/$SU1_2N/g" $TMP_DIR/template_su_init_apg
		    sed -i "s/#SAF_APP#/$SAF_APP/g" $TMP_DIR/template_su_init_apg
		    sed -i "s/#SG#/$SG_2N/g" $TMP_DIR/template_su_init_apg
                    cat $TMP_DIR/template_su_init_apg >> $TMP_DIR/final.xml
                    rm -f $TMP_DIR/template_su_init_apg
                 fi
		cp $TEMPLATES_FOLDER/TEMPLATE_BUNDLE/template_bundle_acted_su1_2n $TMP_DIR/
		sed -i "s/#SU1_2N#/$SU1_2N/g" $TMP_DIR/template_bundle_acted_su1_2n
		sed -i "s/#SAF_APP#/$SAF_APP/g" $TMP_DIR/template_bundle_acted_su1_2n
		sed -i "s/#SG_2N#/$SG_2N/g" $TMP_DIR/template_bundle_acted_su1_2n
		cat $TMP_DIR/template_bundle_acted_su1_2n >> $TMP_DIR/final.xml
                if isSuPresent $SU1_2N $SG_2N ;then
                    cp $TEMPLATES_FOLDER/TEMPLATE_BUNDLE/template_end_apg $TMP_DIR/
                    cat $TMP_DIR/template_end_apg >> $TMP_DIR/final.xml
                    rm -f $TMP_DIR/template_end_apg
                fi
		#SU 1 NORED
		while read line    
			do    
			type=$(echo $line | awk -F';' '{print $1}')
			if [ "$type" = "NORED" ]
				then
					COMP_NAME=$(echo $line | awk -F';' '{print $3}')
					CS_TYPE=$(echo $line | awk -F';' '{print $6}')
					SI_NAME=$(echo $line | awk -F';' '{print $10}')
					CSI_NAME=$(echo $line | awk -F';' '{print $11}')
                                        NORED_SG="NoRed_$CSI_NAME"
                                        if isSuPresent $SU1_2N $NORED_SG ;then
                                                cp $TEMPLATES_FOLDER/TEMPLATE_BUNDLE/template_su_init_apg $TMP_DIR/
                                                sed -i "s/#SCRIPT#/$EXCLUDE_BUNDLES/" $TMP_DIR/template_su_init_apg
                                                sed -i "s/#SG#/$NORED_SG/" $TMP_DIR/template_su_init_apg
		                                sed -i "s/#SU#/$SU1_2N/g" $TMP_DIR/template_su_init_apg
		                                sed -i "s/#SAF_APP#/$SAF_APP/g" $TMP_DIR/template_su_init_apg
                                                sed -i "s/#TYPE#/$ACTIVATE_TYPE/g" $TMP_DIR/template_su_init_apg
                                                cat $TMP_DIR/template_su_init_apg >> $TMP_DIR/final.xml
                                                rm -f $TMP_DIR/template_su_init_apg
                                        fi
					cp $TEMPLATES_FOLDER/TEMPLATE_BUNDLE/template_bundle_acted_su1_nored $TMP_DIR/template_bundle_acted_su1_nored_$CSI_NAME
					sed -i "s/#SAF_APP#/$SAF_APP/g" $TMP_DIR/template_bundle_acted_su1_nored_$CSI_NAME
					sed -i "s/#CSI_NAME#/$CSI_NAME/g" $TMP_DIR/template_bundle_acted_su1_nored_$CSI_NAME
					cat $TMP_DIR/template_bundle_acted_su1_nored_$CSI_NAME >> $TMP_DIR/final.xml
                                        if isSuPresent $SU1_2N $NORED_SG;then
                                                 cp $TEMPLATES_FOLDER/TEMPLATE_BUNDLE/template_end_apg $TMP_DIR/
                                                 cat $TMP_DIR/template_end_apg >> $TMP_DIR/final.xml
                                                 rm -f $TMP_DIR/template_end_apg
                                        fi
			fi
		done < $TMP_DIR/$SOURCE_FILE_NAME
	fi
	if [ "$OPT_RESIZE" = "" ] || [ "$OPT_RESIZE_ARG" = "1-2" ]; then
		#SU 2 2N
                 if isSuPresent $SU2_2N $SG_2N ;then
                    cp $TEMPLATES_FOLDER/TEMPLATE_BUNDLE/template_su_init_apg $TMP_DIR/
                    sed -i "s/#SCRIPT#/$EXCLUDE_BUNDLES/" $TMP_DIR/template_su_init_apg
		    sed -i "s/#TYPE#/$ACTIVATE_TYPE/g" $TMP_DIR/template_su_init_apg
		    sed -i "s/#SU#/$SU2_2N/g" $TMP_DIR/template_su_init_apg
		    sed -i "s/#SAF_APP#/$SAF_APP/g" $TMP_DIR/template_su_init_apg
		    sed -i "s/#SG#/$SG_2N/g" $TMP_DIR/template_su_init_apg
                    cat $TMP_DIR/template_su_init_apg >> $TMP_DIR/final.xml
                    rm -f $TMP_DIR/template_su_init_apg
                 fi
		cp $TEMPLATES_FOLDER/TEMPLATE_BUNDLE/template_bundle_acted_su2_2n $TMP_DIR/
		sed -i "s/#SU2_2N#/$SU2_2N/g" $TMP_DIR/template_bundle_acted_su2_2n
		sed -i "s/#SAF_APP#/$SAF_APP/g" $TMP_DIR/template_bundle_acted_su2_2n
		sed -i "s/#SG_2N#/$SG_2N/g" $TMP_DIR/template_bundle_acted_su2_2n
		cat $TMP_DIR/template_bundle_acted_su2_2n >> $TMP_DIR/final.xml
                if isSuPresent $SU2_2N $SG_2N ; then
                    cp $TEMPLATES_FOLDER/TEMPLATE_BUNDLE/template_end_apg $TMP_DIR/
                    cat $TMP_DIR/template_end_apg >> $TMP_DIR/final.xml
                    rm -f $TMP_DIR/template_end_apg
                fi
		#SU 2 NORED
		while read line    
			do    
			type=$(echo $line | awk -F';' '{print $1}')
			if [ "$type" = "NORED" ]
			then
				COMP_NAME=$(echo $line | awk -F';' '{print $3}')
				CS_TYPE=$(echo $line | awk -F';' '{print $6}')
				SI_NAME=$(echo $line | awk -F';' '{print $10}')
				CSI_NAME=$(echo $line | awk -F';' '{print $11}')
                                NORED_SG="NoRed_$CSI_NAME"
                                        if isSuPresent $SU2_2N $NORED_SG ;then
                                                cp $TEMPLATES_FOLDER/TEMPLATE_BUNDLE/template_su_init_apg $TMP_DIR/
                                                sed -i "s/#SCRIPT#/$EXCLUDE_BUNDLES/" $TMP_DIR/template_su_init_apg
                                                sed -i "s/#SG#/$NORED_SG/" $TMP_DIR/template_su_init_apg
		                                sed -i "s/#SU#/$SU2_2N/g" $TMP_DIR/template_su_init_apg
		                                sed -i "s/#SAF_APP#/$SAF_APP/g" $TMP_DIR/template_su_init_apg
                                                sed -i "s/#TYPE#/$ACTIVATE_TYPE/g" $TMP_DIR/template_su_init_apg
                                                cat $TMP_DIR/template_su_init_apg >> $TMP_DIR/final.xml
                                                rm -f $TMP_DIR/template_su_init_apg
                                        fi
				cp $TEMPLATES_FOLDER/TEMPLATE_BUNDLE/template_bundle_acted_su2_nored $TMP_DIR/template_bundle_acted_su2_nored_$CSI_NAME
				sed -i "s/#SAF_APP#/$SAF_APP/g" $TMP_DIR/template_bundle_acted_su2_nored_$CSI_NAME
				sed -i "s/#CSI_NAME#/$CSI_NAME/g" $TMP_DIR/template_bundle_acted_su2_nored_$CSI_NAME
				cat $TMP_DIR/template_bundle_acted_su2_nored_$CSI_NAME >> $TMP_DIR/final.xml
                                if isSuPresent $SU2_2N $NORED_SG ;then
                                       cp $TEMPLATES_FOLDER/TEMPLATE_BUNDLE/template_end_apg $TMP_DIR/
                                       cat $TMP_DIR/template_end_apg >> $TMP_DIR/final.xml
                                       rm -f $TMP_DIR/template_end_apg
                                fi
			fi
		done < $TMP_DIR/$SOURCE_FILE_NAME
	fi
fi
cp $TEMPLATES_FOLDER/TEMPLATE_BUNDLE/template_bundle_acted_end $TMP_DIR/
sed -i "s/#SCRIPT#/$EXCLUDE_BUNDLES/" $TMP_DIR/template_bundle_acted_end
#END PART
cat $TMP_DIR/template_bundle_acted_end >> $TMP_DIR/final.xml
is_verbose && echo "STEP: ACTEDON CREATION DONE"	
	
#END ACTEDON part ===================================================================================================================================================


#START BUNDLE swadd ===================================================================================================================================================

if [ "$OPT_MINI" = "$TRUE" ] ; then
	while read line    
	do    
		COMP_NAME=$(echo $line | awk -F';' '{print $3}')
		BUNDLE_NAME=$(echo $line | awk -F';' '{print $2}')
		COMP_PATH=$(echo $line | awk -F';' '{print $4}')
		allowed_swadd='Agent DEVMON'
		is_allowed_swadd=''
		for exc in $allowed_swadd; do 
			if [ "$COMP_NAME" == "$exc" ]; then
				is_allowed_swadd='true'
			fi
		done
		if [ "$is_allowed_swadd" = "true" ]; then
			cp $TEMPLATES_FOLDER/TEMPLATE_BUNDLE/template_bundle_add $TMP_DIR/template_bundle_add_$COMP_NAME
			sed -i "s/#BUNDLE_NAME#/$BUNDLE_NAME/g" $TMP_DIR/template_bundle_add_$COMP_NAME
			sed -i "s@#COMP_PATH#@$COMP_PATH@g" $TMP_DIR/template_bundle_add_$COMP_NAME
			if [ "$OPT_RESIZE_ARG" = "1-2" ]; then
				sed -i "s/^.*SC-1.*$//g" $TMP_DIR/template_bundle_add_$COMP_NAME
				sed -i '/^$/d' $TMP_DIR/template_bundle_add_$COMP_NAME
			elif [ "$OPT_RESIZE_ARG" = "0-1" ]; then
				sed -i "s/^.*SC-2.*$//g" $TMP_DIR/template_bundle_add_$COMP_NAME
				sed -i '/^$/d' $TMP_DIR/template_bundle_add_$COMP_NAME
			fi
			cat $TMP_DIR/template_bundle_add_$COMP_NAME >> $TMP_DIR/final.xml
			rm -f $TMP_DIR/template_bundle_add_$COMP_NAME
		fi
	done < $TMP_DIR/$SOURCE_FILE_NAME
else
	while read line    
	do    
		COMP_NAME=$(echo $line | awk -F';' '{print $3}')
		BUNDLE_NAME=$(echo $line | awk -F';' '{print $2}')
		COMP_PATH=$(echo $line | awk -F';' '{print $4}')
		exceptions='COMSA APOSCONFBIN APOSCMDBIN APOSEXTBIN COM LCT ERIC-Sec-Control'
		is_exception=''
		for exc in $exceptions; do 
			if [ "$COMP_NAME" == "$exc" ]; then
				is_exception='true'
			fi
		done
		if [ -z $is_exception ]; then
                        if shallExcludeApp $COMP_NAME; then
                               cp $TEMPLATES_FOLDER/TEMPLATE_BUNDLE/template_init_apg $TMP_DIR/
                               sed -i "s/#PARAM#/$COMP_NAME/g" $TMP_DIR/template_init_apg
                               sed -i "s/#SCRIPT#/$EXCLUDE_BUNDLES/g" $TMP_DIR/template_init_apg
                               sed -i "s/#TYPE#/$INSTALL_TYPE/g" $TMP_DIR/template_init_apg
                               cat $TMP_DIR/template_init_apg >> $TMP_DIR/final.xml
                               rm -f $TMP_DIR/template_init_apg
                        fi
			cp $TEMPLATES_FOLDER/TEMPLATE_BUNDLE/template_bundle_add $TMP_DIR/template_bundle_add_$COMP_NAME
			sed -i "s/#BUNDLE_NAME#/$BUNDLE_NAME/g" $TMP_DIR/template_bundle_add_$COMP_NAME
			sed -i "s@#COMP_PATH#@$COMP_PATH@g" $TMP_DIR/template_bundle_add_$COMP_NAME
			if [ "$OPT_RESIZE_ARG" = "1-2" ]; then
				sed -i "s/^.*SC-1.*$//g" $TMP_DIR/template_bundle_add_$COMP_NAME
				sed -i '/^$/d' $TMP_DIR/template_bundle_add_$COMP_NAME
			elif [ "$OPT_RESIZE_ARG" = "0-1" ]; then
				sed -i "s/^.*SC-2.*$//g" $TMP_DIR/template_bundle_add_$COMP_NAME
				sed -i '/^$/d' $TMP_DIR/template_bundle_add_$COMP_NAME
			fi
			cat $TMP_DIR/template_bundle_add_$COMP_NAME >> $TMP_DIR/final.xml
			rm -f $TMP_DIR/template_bundle_add_$COMP_NAME
                        if shallExcludeApp $COMP_NAME; then
                               cp $TEMPLATES_FOLDER/TEMPLATE_BUNDLE/template_end_apg $TMP_DIR/
                               cat $TMP_DIR/template_end_apg >> $TMP_DIR/final.xml
                               rm -f $TMP_DIR/template_end_apg
                        fi
		fi
	done < $TMP_DIR/$SOURCE_FILE_NAME
fi
is_verbose && echo "STEP: BUNDLES CREATION DONE"	

#END BUNDLE swadd ===================================================================================================================================================


#START final part ===================================================================================================================================================
	
cp $TEMPLATES_FOLDER/TEMPLATE_INTRO_END/template_pre_end $TMP_DIR/
cp $TEMPLATES_FOLDER/TEMPLATE_INTRO_END/template_end $TMP_DIR/
if [ "$OPT_RESIZE" = "" ]; then
	cat $TMP_DIR/template_pre_end >> $TMP_DIR/final.xml	
	if [ "$OPT_MINI" = "$TRUE" ] ; then
		cp $TEMPLATES_FOLDER/TEMPLATE_INTRO_END/template_end_ipa_apos $TMP_DIR/
                sed -i "s/#SCRIPT#/$EXCLUDE_BUNDLES/" $TMP_DIR/template_end_ipa_apos
		cat $TMP_DIR/template_end_ipa_apos >> $TMP_DIR/final.xml
	else
                sed -i "s/#SCRIPT#/$EXCLUDE_BUNDLES/" $TMP_DIR/template_end
		cat $TMP_DIR/template_end >> $TMP_DIR/final.xml	
	fi	
elif [ "$OPT_RESIZE_ARG" = "1-2" ]; then
	cp $TEMPLATES_FOLDER/TEMPLATE_INTRO_END/template_end_resize_1_2 $TMP_DIR/	
	cat $TMP_DIR/template_pre_end >> $TMP_DIR/final.xml
        if [ "$OPT_MINIRES" = "$TRUE" ] ; then
                cp $TEMPLATES_FOLDER/TEMPLATE_INTRO_END/template_end_ipa_apos $TMP_DIR/
                sed -i "s/#SCRIPT#/$EXCLUDE_BUNDLES/" $TMP_DIR/template_end_ipa_apos
                cat $TMP_DIR/template_end_ipa_apos >> $TMP_DIR/final.xml
        else
                sed -i "s/#SCRIPT#/$EXCLUDE_BUNDLES/" $TMP_DIR/template_end_resize_1_2
                cat $TMP_DIR/template_end_resize_1_2 >> $TMP_DIR/final.xml
		cat $TMP_DIR/template_end >> $TMP_DIR/apos_ipa_1_2.xml	
	fi
elif [ "$OPT_RESIZE_ARG" = "0-1" ]; then
	cp $TEMPLATES_FOLDER/TEMPLATE_INTRO_END/template_end_resize_0_1 $TMP_DIR/	
        sed -i "s/#SCRIPT#/$EXCLUDE_BUNDLES/" $TMP_DIR/template_end_resize_0_1
	cat $TMP_DIR/template_pre_end >> $TMP_DIR/final.xml		
	cat $TMP_DIR/template_end_resize_0_1 >> $TMP_DIR/final.xml		
	cat $TMP_DIR/template_end >> $TMP_DIR/apos_ipa_0_1.xml	
fi
is_verbose && echo "STEP: END CREATION DONE"		

#END final part ===================================================================================================================================================


#START ETF part ===================================================================================================================================================
	
cp $TEMPLATES_FOLDER/TEMPLATE_BUNDLE/template_etf $TMP_DIR/template_etf
if [ "$OPT_RESIZE" = "" ]; then
	if [ "$OPT_MINI" = "$TRUE" ] ; then
		sed -i "s/#CAMPAIGN_NAME#/$CAMPAIGN_NAME_MINI/g" $TMP_DIR/template_etf		
	else
		sed -i "s/#CAMPAIGN_NAME#/$CAMPAIGN_NAME/g" $TMP_DIR/template_etf
	fi
elif [ "$OPT_RESIZE_ARG" = "1-2" ]; then
	sed -i "s/#CAMPAIGN_NAME#/$CAMPAIGN_NAME_S2/g" $TMP_DIR/template_etf
elif [ "$OPT_RESIZE_ARG" = "0-1" ]; then
	sed -i "s/#CAMPAIGN_NAME#/$CAMPAIGN_NAME_S1/g" $TMP_DIR/template_etf
fi
cp $TMP_DIR/template_etf $TMP_DIR/campaign/ETF.xml
is_verbose && echo "STEP: ETF DONE"	
	
#END ETF part ===================================================================================================================================================


#START packageInfo part ===================================================================================================================================================

createPackageInfo
if [  $? != 0 ]
then
	echo "Error occurs during PackageInfo creation"
	exit 2
fi
is_verbose && echo "STEP: PACKAGE INFO DONE"	

#END packageInfo part ===================================================================================================================================================


#START Packaging part ===================================================================================================================================================
	
if [ "$(ls -A $PATCH_FOLDER)" ]; then
         if [[ -L $PATCH_FOLDER/parmtool_cc && -d $PATCH_FOLDER/parmtool_cc ]];then
            PARMTOOL_DIR=$(readlink -f $PATCH_FOLDER/parmtool_cc)
            cp -r $PARMTOOL_DIR/  $TMP_DIR/campaign
	      else
           PARMTOOL=$( find $PATCH_FOLDER -maxdepth 1 -type d -name "parmtool")
	         if [ -z "$PARMTOOL" ]; then
            rm -rf $TMP_DIR
            abort "ERROR: parmtool is missing in patches folder "
           fi
           check_parmtool_structure
            # remove dangling symlink from campaign
            rm -f $TMP_DIR/campaign/parmtool_cc
	      fi
        PARMTOOL=$( find $TMP_DIR/campaign -maxdepth 1 -type d -name "parmtool")
	      if [ -z "$PARMTOOL" ]; then
          rm -rf $TMP_DIR
          abort "ERROR: parmtool is missing in package"
        fi
        if [[ -L $PATCH_FOLDER/entry_matches_cc ]];then
             ENTRY_MATCH=$(readlink -f $PATCH_FOLDER/entry_matches_cc)
             cp $ENTRY_MATCH $TMP_DIR/campaign
             cp $PATCH_FOLDER/* $TMP_DIR/campaign 2>/dev/null
        else
            cp -r $PATCH_FOLDER/* $TMP_DIR/campaign
        fi
        # remove dangling symlink from campaign
        rm -f $TMP_DIR/campaign/entry_matches_cc
        ENTRY_MATCH=$( find $TMP_DIR/campaign -maxdepth 1 -type f -name "entry_matches.sh")
        if [ -z "$ENTRY_MATCH" ];then
           rm -rf $TMP_DIR
           abort "ERROR: entry_matches.sh file is missing in package"
        fi
        cp $CONF_FOLDER/apps_lock_list.csv $TMP_DIR/campaign 
        cp $CONF_FOLDER/apps_list.csv $TMP_DIR/campaign 
        cp $CONF_FOLDER/node_lock_list.conf $TMP_DIR/campaign 
        chmod 755 $TMP_DIR/campaign/*
fi
cp $TMP_DIR/final.xml $TMP_DIR/campaign/campaign.template.xml
pushd $TMP_DIR/campaign/ >> /dev/null
if [ "$OPT_RESIZE" = "" ]; then	
	if [ "$OPT_MINI" = "$TRUE" ] ; then
		tar -czf $CAMPAIGN_FILE_NAME_MINI *		
	else
		tar -czf $CAMPAIGN_FILE_NAME *
	fi
elif [ "$OPT_RESIZE_ARG" = "1-2" ]; then
	tar -czf $CAMPAIGN_FILE_NAME_S2 *
elif [ "$OPT_RESIZE_ARG" = "0-1" ]; then
	tar -czf $CAMPAIGN_FILE_NAME_S1 *
fi
popd >> /dev/null
if [ "$OPT_RESIZE" = "" ]; then	
	if [ "$OPT_MINI" = "$TRUE" ] ; then
		cp $TMP_DIR/campaign/$CAMPAIGN_FILE_NAME_MINI $SING_STEP_FOLDER		
	else
		cp $TMP_DIR/campaign/$CAMPAIGN_FILE_NAME $SING_STEP_FOLDER
	fi
elif [ "$OPT_RESIZE_ARG" = "1-2" ]; then
	cp $TMP_DIR/campaign/$CAMPAIGN_FILE_NAME_S2 $RESIZE_FOLDER
elif [ "$OPT_RESIZE_ARG" = "0-1" ]; then
	cp $TMP_DIR/campaign/$CAMPAIGN_FILE_NAME_S1 $RESIZE_FOLDER
fi
is_verbose && echo "STEP: PACKAGING DONE"
rm -rf $TMP_DIR

#END Packaging part =====================================================================================================================================================
