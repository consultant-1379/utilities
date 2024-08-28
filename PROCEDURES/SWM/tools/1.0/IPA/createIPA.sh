#!/bin/bash
# ------------------------------------------------------------------------
#     Copyright (C) 2012 Ericsson AB. All rights reserved.
# ------------------------------------------------------------------------
######
# Name:
#       createIPA.sh
# Description:
#       <script_functionality_description>
# Note:
#       <script_notes>
#####
# Usage:
#       ./createIPA.sh 
#####
# Output:
#       <script_output_description>
#####
# Changelog
# 2014-11-27 XFABPAG - Fixed issue in parsing the cc4mi.txt file
# 2014-05-14 XFABPAG - Consistency check of block R-states skipped for NOAMF
# 2014-04-22 XFABPAG - Consistency check of block R-states in sources.list
# 2013-05-14 Dual AP adaptation 
# 2013-02-21 LDE naming convenction
# 2013-02-19 Automatic create of mini ipa resize
# 2013-02-18 Automatic remove of LOTC reboot
# 2012-04-19 first version eanbuon 
#
###########################################################################

CAMPAIGN_SCRIPT_NAME="createIPAcampaign.sh"
CAMPAIGN_SCRIPT_FOLDER="."
OUT_FOLDER="./out"
IPA_FOLDER="$OUT_FOLDER/ipa"
RESIZE_FOLDER="$OUT_FOLDER/resize"
SINGLE_STEP_FOLDER="$OUT_FOLDER/single_step"

IPA_CAMPAIGN_FOLDER="cgn"
IPA_CMW_FOLDER="cmw"
IPA_SDPS_FOLDER="bdl"
IPA_NAME="sw.tgz"

CONF_FOLDER="./conf"
SOURCE_LIST_FOLDER=$CONF_FOLDER
SOURCE_FILE_NAME="sources.list"
SOURCE_SDPS_FOLDER=$CONF_FOLDER
SOURCE_APG_SDP="source.csv"
CMW_ID_FILE="IDENTITY"
MINIIPA_FILE_NAME="MINI-IPA.conf"

# local folder for SDSs
LOCAL_SDPS_FOLDER="./local/sdps"
LOCAL_CMW_FOLDER="./local/cmw"
LOCAL_CBA_FOLDER="./local/cba"

# APOS variables
APOS_SDP_PATH="/vobs/cm4ap/apos/mi_cnz/targz/out" 

# CBA variables
CBA_VOBS_PATH="/vobs/cm4ap/apos/3pp_cnz"
CBA_LIST_FILE="cc4mi.txt"
CBA_CMW_FOLDER="coremw"

# mini ipa with resize impacts
MINI_IPA_APG_BLOCKs="LCT\|HAAGENT\|DEVMON"
# end
. $CONF_FOLDER/common_functions_IPA

parse_cmdline $@

#Generating Temp folder
TMP_DIR=`mktemp -td swupdate_APG_XXX`
chmod 777 $TMP_DIR
is_verbose && echo "INFO: tmp folder is $TMP_DIR"
#clean output folder
rm -rf $IPA_FOLDER/*
is_verbose && echo "INFO: Clean output folder"

### Consistency check of block R-states in sources.list - START #
is_verbose && echo "DEBUG: consistency check of block R-states in sources.list"
if [ "$OPT_MINIIPA" == "$TRUE" ]; then
	is_verbose && echo "DEBUG : MINIIPA option"
	MINI_IPA_BLOCKS_TO_CHECK="BRF\|BRFC\|COM\|COMSA\|CMW\|LDEBRF\|LDEWS\|SEC\|\CRYPTO\|SECAGENT\|APOS\|LCT"
	cat "$CONF_FOLDER/$SOURCE_FILE_NAME" | grep $MINI_IPA_BLOCKS_TO_CHECK > "$TMP_DIR/tmpfile4rstate_check"
	FILE4_RSTATE_CHECK="$TMP_DIR/tmpfile4rstate_check"
else
	FILE4_RSTATE_CHECK="$CONF_FOLDER/$SOURCE_FILE_NAME"
fi

RSTATES_MATCH=$TRUE
while read line
do
	if [[ ! "$line" =~ ^#.* ]]; then
		BLOCK_TYPE=$(echo $line | awk -F';' '{print $1}')
		BLOCK_NAME=$(echo $line | awk -F';' '{print $2}'| sed  "s/^ERIC-//g")
		
		if [[ "$BLOCK_NAME" =~ ^sec-.* ]] ; then
                   BLOCK_NAME_RSTATE=$(echo "$BLOCK_NAME" | sed "s/\.sle12//g")
                   BLOCK_NAME_RSTATE=$(echo "$BLOCK_NAME_RSTATE"  | awk -F'-' '{print $5,"-",$6}'| tr -d ' ')
                elif [[ "$BLOCK_NAME" =~ ^COM-.* ]] ; then

                   BLOCK_NAME_RSTATE=$(echo "$BLOCK_NAME" | awk -F'-' '{ print $3 }')
                   TMP2_DIR=`mktemp -td swupdate_APG_XXX`
                   chmod 777 $TMP2_DIR
                   cp $LOCAL_CBA_FOLDER/COM*.sdp $TMP2_DIR
                   if [ "$?" != "0" ]
                   then
                        echo "ERROR: Fail to copy COM SDPs"
                        exit 4
                   fi
		#EXTRACTING ETF.xml from COM SDP to check safVersion of com cmponents	
                   COM_LOCAL_ETF=ETF.xml
                   tar -zxf $TMP2_DIR/COM*.sdp -C $TMP2_DIR ./$COM_LOCAL_ETF &> /dev/null
                   if [ "$?" != "0" ]; then
                        tar -zxf $TMP2_DIR/COM*.sdp -C $TMP2_DIR $COM_LOCAL_ETF &> /dev/null
                        if [ "$?" != "0" ]; then
                                echo "ERROR: Fail to extract COM  ETF.xml"
                                exit 4
                        fi
                        COMSA_CMW=$(grep ERIC-ComSa-Cmw  $TMP2_DIR/$COM_LOCAL_ETF | grep componentType | cut -d"=" -f5 | cut -d'"' -f1)
                        COMSA_TLSD=$(grep ERIC-ComSa-tlsd  $TMP2_DIR/$COM_LOCAL_ETF | grep componentType | cut -d"=" -f5 | cut -d'"' -f1)
                        COMSA_SSHD=$(grep ERIC-ComSa-sshd  $TMP2_DIR/$COM_LOCAL_ETF | grep componentType | cut -d"=" -f5 | cut -d'"' -f1)
                        if ( [ ! -z $COMSA_CMW ] && [ ! -z $COMSA_TLSD ] && [ ! -z $COMSA_SSHD ] ); then
                                if ( [  $COMSA_CMW = $COMSA_TLSD ] && [ $COMSA_CMW = $COMSA_SSHD ] ); then
                                        BLOCK_NAME_RSTATE=$COMSA_CMW
				else 
					echo "ERROR: R-state not consistent for BLOCK $BLOCK_NAME"
	                                exit 4

                                fi
			else
				echo "ERROR: R-state is empty for BLOCK $BLOCK_NAME"
				exit 4
                        fi
                   fi
                rm -rf $TMP2_DIR
		else
                    BLOCK_NAME_RSTATE=$(echo "$BLOCK_NAME" | awk -F'-' '{ print $3 }')	
		fi
		
		RSTATE=$(echo $line | awk -F';' '{ print $7 }')
		if [ "$RSTATE" == "" ] ; then
			if [ "$BLOCK_TYPE" != "NOAMF" ] ; then
				is_verbose && echo "WARNING: R-state for BLOCK $BLOCK_NAME not set"
			fi
		elif [ "$BLOCK_NAME_RSTATE" != "$RSTATE" ] ; then
			echo "ERROR: R-state $RSTATE not consistent for BLOCK $BLOCK_NAME"
			RSTATES_MATCH='FALSE'
		fi
	fi

done < $FILE4_RSTATE_CHECK

[[ "$OPT_MINIIPA" == "$TRUE" ]] && rm -f "$TMP_DIR/tmpfile4rstate_check"

if [ "$RSTATES_MATCH" != "$TRUE" ] ; then
	echo "ERROR: consistency check of block R-states in sources.list FAILED"
	exit 30
fi
### Consistency check of block R-states in sources.list - END #

# Import CBAs List and remove comment, if local option is used sdps are fetched from sdps folder
	if [ "$OPT_LOCAL" != "" ]
	then
		is_verbose && echo "INFO: Local Version of CBAs used"
	elif [ -e $CBA_VOBS_PATH/$CBA_LIST_FILE ]
	then
		is_verbose && echo "INFO: Clearcase Version of CBAs used"
		cp $CBA_VOBS_PATH/$CBA_LIST_FILE $TMP_DIR/$CBA_LIST_FILE
		#sed -i 's@^.*[[:space:]+]@@g' $TMP_DIR/$CBA_LIST_FILE
		sed -i '/^$/d' $TMP_DIR/$CBA_LIST_FILE
		sed -i 's@[[:space:]+]@:@' $TMP_DIR/$CBA_LIST_FILE
		sed -i 's@[[:space:]+]@@g' $TMP_DIR/$CBA_LIST_FILE
		sed -i 's@:\./@:@g' $TMP_DIR/$CBA_LIST_FILE
	else
		echo "$CBA_LIST_FILE file not found!!!"
		exit 2
	fi
# Import APG SDP List and remove comment, if local option is used sdps are fetched from sdps folder.
	if [ "$OPT_LOCAL" != "" ]
	then
		is_verbose && echo "INFO: Local Version"
		# check if the folder is empty or the number of SDP not match with conf file for IPA
		# create a file with a list of spds
		touch $TMP_DIR/sdp.tmp.list
		ls -1 $LOCAL_SDPS_FOLDER > $TMP_DIR/sdp.tmp.list
		#check if sdps folder is empty
		CHECK_SDPS_IPA=$(cat $TMP_DIR/sdp.tmp.list | wc -l)	
		if [ "$CHECK_SDPS_IPA" = "0" ]
		then
			echo "ERROR: sdps folder is empty, it is no possible create an empty IPA"
			exit 2
		fi
	elif [ -e $SOURCE_SDPS_FOLDER/$SOURCE_APG_SDP ]
	then
		is_verbose && echo "INFO: Clearcase Version"
		is_verbose && echo "INFO: APG SDPs list detected"
		cp $SOURCE_SDPS_FOLDER/$SOURCE_APG_SDP $TMP_DIR/$SOURCE_APG_SDP
		sed -i "s/^#.*$//g" $TMP_DIR/$SOURCE_APG_SDP
		sed -i '/^$/d' $TMP_DIR/$SOURCE_APG_SDP
		SOURCE_FILE_CHECK=$(cat $TMP_DIR/$SOURCE_APG_SDP| wc -l)
		if [ "$SOURCE_FILE_CHECK" = "0" ]
		then
			echo "ERROR: $SOURCE_APG_SDP file is empty"
			exit 4
		fi
	else
		echo "$SOURCE_APG_SDP file is missing!!!"
		exit 2
	fi
#Create IPA Structure
# RESIZE campaign
mkdir -p $TMP_DIR/$IPA_CAMPAIGN_FOLDER
# CMW folder
mkdir -p $TMP_DIR/$IPA_CMW_FOLDER
# SDPs folder
mkdir -p $TMP_DIR/$IPA_SDPS_FOLDER
# Resize campaign creation
if [ -e $CAMPAIGN_SCRIPT_FOLDER/$CAMPAIGN_SCRIPT_NAME ]
then
	V=''
	if [ is_verbose ]; then
		V='v'
	fi
	if [ "$OPT_RESIZE" = "$TRUE" ];then
		#    RESIZE 0-1
		if [ "$OPT_MINIIPA" = "$TRUE" ]; then
			$CAMPAIGN_SCRIPT_FOLDER/$CAMPAIGN_SCRIPT_NAME -m"$V" -r 0-1
			echo "DEBUG: MINI IPA RESIZE"
		else
			echo "DEBUG: NOT MINI IPA"
			$CAMPAIGN_SCRIPT_FOLDER/$CAMPAIGN_SCRIPT_NAME -"$V" -r 0-1
		fi
		if [ "$?" != "0" ] 
		then
			echo "ERROR: Creation of Resize campaign 0-1 failed"
			exit 4
		else
			cp -f $RESIZE_FOLDER/*.sdp $TMP_DIR/$IPA_CAMPAIGN_FOLDER
			is_verbose && echo "INFO: RESIZE 0-1 CREATION DONE"
		fi
		#    RESIZE 1-2
		if [ "$OPT_MINIIPA" = "$TRUE" ]; then
			$CAMPAIGN_SCRIPT_FOLDER/$CAMPAIGN_SCRIPT_NAME -m"$V"r 1-2
		else
			$CAMPAIGN_SCRIPT_FOLDER/$CAMPAIGN_SCRIPT_NAME -"$V"r 1-2
		fi
		if [ "$?" != "0" ] 
		then
			echo "ERROR: Creation of Resize campaign 1-2 failed"
			exit 4
		else
			cp $RESIZE_FOLDER/*.sdp $TMP_DIR/$IPA_CAMPAIGN_FOLDER
			is_verbose && echo "INFO: RESIZE 1-2 CREATION DONE"			
		fi	
	else
        	if [ "$OPT_MINIIPA" = "$TRUE" ]; then
        	        $CAMPAIGN_SCRIPT_FOLDER/$CAMPAIGN_SCRIPT_NAME -m"$V"
        	        echo "DEBUG: MINI IPA SINGLE STEP"
        	else
        	        echo "DEBUG: NOT MINI IPA"
        	        $CAMPAIGN_SCRIPT_FOLDER/$CAMPAIGN_SCRIPT_NAME -"$V"
        	fi
        	if [ "$?" != "0" ]
        	then
        	        echo "ERROR: Creation of campaign failed"
        	        exit 4
        	else
        	        cp -f $SINGLE_STEP_FOLDER/*.sdp $TMP_DIR/$IPA_CAMPAIGN_FOLDER
        	        is_verbose && echo "INFO: CAMPAIGN SINGLE STEP CREATION DONE"
        	fi
	fi
else
	echo "ERROR: Script for Campaign creation missing!!!"
	exit 2
fi
# COREMW RUNTIME
if [ "$OPT_LOCAL" != "" ]
then
	is_verbose && echo "INFO: Local Version of CMW used"	
        pushd "$LOCAL_CMW_FOLDER" > /dev/null 2>&1
	#CMW_FILE_PATH=$( ls $LOCAL_CMW_FOLDER/*RUNTIME*.tar )
	#CMW_FILE_NAME=`basename $CMW_FILE_PATH`
        CMW_FILE_NAME=$(find . -name "COREMW_RUNTIME.tar")
        if [ -z $CMW_FILE_NAME ]; then
		CMW_FILE_NAME=$(find . -name "coremw_x86_64-*runtime*.tar")
	fi 
	if [ -e $CMW_FILE_NAME ] 
	then
		cp $CMW_FILE_NAME $TMP_DIR/$IPA_CMW_FOLDER/COREMW_RUNTIME.tar
		is_verbose && echo "INFO: COREMW FILES GETTED"
	else
		echo "ERROR: Local CMW RUNTIME FILE NOT EXISTS"
		exit 4
	fi
        popd > /dev/null 2>&1
      
elif [ -d $CBA_VOBS_PATH/$CBA_CMW_FOLDER ]
then
	CMW_FILE_PATH=$( ls $CBA_VOBS_PATH/$CBA_CMW_FOLDER/*RUNTIME*.tar )
        CMW_FILE_NAME=$(basename $CMW_FILE_PATH)
	if [ "$?" != "0" ]; then
		CMW_FILE_PATH=$( ls $CBA_VOBS_PATH/$CBA_CMW_FOLDER/coremw_x86_64-*runtime*.tar )
		CMW_FILE_NAME=$(basename $CMW_FILE_PATH)
	fi
	# check if more than one runetime exists
	if [ "$?" != "0" ] 
	then
		echo "ERROR: CMW RUNTIME FILE NOT EXISTS"
		exit 4
	else
                cp $CBA_VOBS_PATH/$CBA_CMW_FOLDER/$CMW_FILE_NAME $TMP_DIR/$IPA_CMW_FOLDER/COREMW_RUNTIME.tar
		is_verbose && echo "INFO: COREMW FILES COPIED"	
	fi
	# show VERSION of CMW
else
	echo "ERROR: 3PP - CMW folder not found, check config spec used !!!"
	exit 2
fi
# CBA : COM - COMSA - BRF - BRFC - BRF_LDE - LOTC_CBA  #
if [ "$OPT_LOCAL" != "" ]
then
	if [ "$(ls -A $LOCAL_CBA_FOLDER)" ]; then
		is_verbose && echo "INFO: Local Version of CBA used"
		cp $LOCAL_CBA_FOLDER/*.sdp $TMP_DIR/$IPA_SDPS_FOLDER/
		if [ "$?" != "0" ] 
		then
			echo "ERROR: Fail to copy CBA SDPs"
			exit 4
		fi
		# Adaptation to SEC rpm format
		cp $LOCAL_CBA_FOLDER/*.rpm $TMP_DIR/$IPA_SDPS_FOLDER/
		if [ "$?" != "0" ] 
		then
			echo "ERROR: Fail to copy CBA RPMs"
			exit 4
		fi
	# Remove in LOTC ETF.xml the reboot flag.
		#Create tmp folder for LOTC.
		LOTC_LOCAL_TMP="$TMP_DIR/$IPA_SDPS_FOLDER/LOTC_FIX"
		mkdir -p $LOTC_LOCAL_TMP
		#ERIC-LINUX_CONTROL-CXP9013151_3.sdp
		LOTC_LOCAL_SDP=$(ls -1 $TMP_DIR/$IPA_SDPS_FOLDER |grep ERIC-LINUX_CONTROL-*)
		if [ "$LOTC_LOCAL_SDP" = "" ];then
			echo "ERROR: LOTC SDP Not Found!"
			exit 14
		else
			LOTC_LOCAL_ETF=$LOTC_LOCAL_TMP/ETF.xml
			tar -zxf $TMP_DIR/$IPA_SDPS_FOLDER/$LOTC_LOCAL_SDP -C $LOTC_LOCAL_TMP ./ETF.xml &> /dev/null
			if [ "$?" != "0" ] 
			then
                             tar -zxf $TMP_DIR/$IPA_SDPS_FOLDER/$LOTC_LOCAL_SDP -C $LOTC_LOCAL_TMP ETF.xml &> /dev/null
			        if [ "$?" != "0" ]
                        	then
					echo "ERROR: Fail to extract LOTC ETF.xml"
					exit 4
				fi
			fi
			#Verify if reboot fix is needed
			LOTC_LOCAL_FIX_FLAG=$(cat $LOTC_LOCAL_ETF | grep "executionEnvironment"|wc -l)
			if [ "$LOTC_LOCAL_FIX_FLAG" = "0" ];then
				#Fix not needed
				is_verbose && echo "INFO: CBA ADAPTATION REBOOT ALREADY REMOVED"
				rm -rf $LOTC_LOCAL_TMP
			else
				#Fix Needed
				tar -zxf $TMP_DIR/$IPA_SDPS_FOLDER/$LOTC_LOCAL_SDP -C $LOTC_LOCAL_TMP/
				rm -f $TMP_DIR/$IPA_SDPS_FOLDER/$LOTC_LOCAL_SDP
				sed -i "s/executionEnvironment/serviceUnit/g" $LOTC_LOCAL_ETF
				pushd $LOTC_LOCAL_TMP >> /dev/null
				tar -czf $LOTC_LOCAL_SDP *
				popd >> /dev/null
				mv $LOTC_LOCAL_TMP/$LOTC_LOCAL_SDP $TMP_DIR/$IPA_SDPS_FOLDER/
				rm -rf $LOTC_LOCAL_TMP/
				is_verbose && echo "INFO: CBA ADAPTATION REBOOT REMOVED"
			fi
		fi
	else
		echo "ERROR: No SDPs found in CBA local folder"
		exit 5		
	fi
elif [ -e $TMP_DIR/$CBA_LIST_FILE ]
then
	if [ -s $TMP_DIR/$CBA_LIST_FILE ]; then
		mkdir -p $TMP_DIR/cba_tmp
		while read line    
		do    
			cba_name=`echo $line | awk -F':' '{print $1}'`
			cba_path=`echo $line | awk -F':' '{print $2}'`
			if [ "$cba_name" != "CMW" ] 
			then
				cba_file=$(basename $cba_path)		
				echo $cba_path
				echo $cba_name
				echo $cba_file
				echo "----------"
				mkdir -p $TMP_DIR/cba_tmp/$cba_name
				cp $CBA_VOBS_PATH/$cba_path $TMP_DIR/cba_tmp/$cba_name/
				pushd $TMP_DIR/cba_tmp/$cba_name/ >> /dev/null
					if [ "${cba_file##*.}" != "rpm" ];then
						tar -xf $cba_file
					else
						echo "rpm file found"
					fi
				popd >> /dev/null
				if [ "$cba_name" = "LOTC" ] || [ "$cba_name" = "LDEWS" ];
				then
					mv $TMP_DIR/cba_tmp/$cba_name/*CONTROL*.sdp $TMP_DIR/$IPA_SDPS_FOLDER/
					# Remove in LOTC ETF.xml the reboot flag.
					#Create tmp folder for LOTC.
					LOTC_LOCAL_TMP="$TMP_DIR/$IPA_SDPS_FOLDER/LOTC_FIX"
					mkdir -p $LOTC_LOCAL_TMP
					#ERIC-LINUX_CONTROL-CXP9013151_3.sdp
					LOTC_LOCAL_SDP=$(ls -1 $TMP_DIR/$IPA_SDPS_FOLDER |grep ERIC-LINUX_CONTROL-*)
					if [ "$LOTC_LOCAL_SDP" = "" ]; then
						echo "ERROR: LOTC SDP Not Found!"
						exit 14
					else
						LOTC_LOCAL_ETF=$LOTC_LOCAL_TMP/ETF.xml
						tar -zxf $TMP_DIR/$IPA_SDPS_FOLDER/$LOTC_LOCAL_SDP -C $LOTC_LOCAL_TMP ./ETF.xml &>/dev/null
						if [ "$?" != "0" ] 
						then
                                                        tar -zxf $TMP_DIR/$IPA_SDPS_FOLDER/$LOTC_LOCAL_SDP -C $LOTC_LOCAL_TMP ETF.xml &>/dev/null
	                                                if [ "$?" != "0" ]
        	                                        then
								echo "ERROR: Fail to extract LOTC ETF.xml"
								exit 4
							fi
						fi
						#Verify if reboot fix is needed
						LOTC_LOCAL_FIX_FLAG=$(cat $LOTC_LOCAL_ETF | grep "executionEnvironment"|wc -l)
						if [ "$LOTC_LOCAL_FIX_FLAG" = "0" ]; then
							#Fix not needed
							is_verbose && echo "INFO: CBA ADAPTATION REBOOT ALREADY REMOVED"
							rm -rf $LOTC_LOCAL_TMP
						else
							#Fix Needed
							tar -zxf $TMP_DIR/$IPA_SDPS_FOLDER/$LOTC_LOCAL_SDP -C $LOTC_LOCAL_TMP/
							rm -f $TMP_DIR/$IPA_SDPS_FOLDER/$LOTC_LOCAL_SDP
							sed -i "s/executionEnvironment/serviceUnit/g" $LOTC_LOCAL_ETF
							pushd $LOTC_LOCAL_TMP >> /dev/null
							tar -czf $LOTC_LOCAL_SDP *
							popd >> /dev/null
							mv $LOTC_LOCAL_TMP/$LOTC_LOCAL_SDP $TMP_DIR/$IPA_SDPS_FOLDER/
							rm -rf $LOTC_LOCAL_TMP/
							is_verbose && echo "INFO: CBA ADAPTATION REBOOT REMOVED"
						fi
					fi
				elif [ "${cba_file##*.}" = "rpm" ]
				then
					mv $TMP_DIR/cba_tmp/$cba_name/*.rpm $TMP_DIR/$IPA_SDPS_FOLDER/
				else
					mv $TMP_DIR/cba_tmp/$cba_name/*.sdp $TMP_DIR/$IPA_SDPS_FOLDER/
				fi
			fi
			rm -rf $TMP_DIR/cba_tmp/$cba_name/
		done < $TMP_DIR/$CBA_LIST_FILE
	else
		echo "ERROR: $CBA_LIST_FILE is empty"
		exit 5	
	fi	
else
	echo "ERROR: 3PP - $CBA_LIST_FILE not found under tmp dir !!!"
	exit 2	
fi
# APOS SDP
if [ "$OPT_LOCAL" != "" ]
then
	is_verbose && echo "INFO: Local Version of APOS used"
else
	is_verbose && echo "INFO: ClearCase Version of APOS used"
	#Retrive Files names
	APOS_BUNDLES_FILES=`ls $APOS_SDP_PATH | grep -E '^APOS.+BIN-CX[CP]'`
	if [ "$APOS_BUNDLES_FILES" = "" ]
	then
		echo "ERROR: NO SDPs found"
		exit 4
	fi
	for i in $APOS_BUNDLES_FILES
	do
		cp $APOS_SDP_PATH/$i $TMP_DIR/$IPA_SDPS_FOLDER/
		if [ "$?" != "0" ]
		then
			echo "ERROR: Fail to copy APOS SDP"
			exit 4
		else
			echo "INFO: APOS SDP COPIED"
		fi
	done
fi
# APG SDPs
if [ "$OPT_LOCAL" != "" ]
then
	is_verbose && echo "INFO: Local Version of APG SDPs used"	
	cp $LOCAL_SDPS_FOLDER/*.sdp $TMP_DIR/$IPA_SDPS_FOLDER/
	if [ "$?" != "0" ] 
	then
		echo "ERROR: Fail to copy APG SDP"
		exit 4
	else
		
		is_verbose && echo "INFO: APG SDPs COPIED"	
	
	fi	
else
	if [ "$OPT_MINIIPA" = "$TRUE" ]; then	
		echo "DEBUG : MINIIPA option "	
		is_verbose && echo "$SOURCE_APG_SDP file is changed for mini ipa"
		cat $TMP_DIR/$SOURCE_APG_SDP | grep $MINI_IPA_APG_BLOCKs > $TMP_DIR/tmpfile
		chmod 777 $TMP_DIR/$SOURCE_APG_SDP
		cat $TMP_DIR/tmpfile > $TMP_DIR/$SOURCE_APG_SDP
		rm $TMP_DIR/tmpfile
	fi
	while read line
	do    
		BLOCK_NAME=`echo $line | awk -F';' '{print $1}'`
		CXC_PATH=`echo $line | awk -F';' '{print $2}'`
		echo "DEBUG: check for CXC PATH $CXC_PATH "
		if [ -d $CXC_PATH/packages/sdp/ ]
		then
			# check if there is more than one SDP		
			SDP_CHECK=$(ls $CXC_PATH/packages/sdp/*.sdp | grep -Ev 'I1|U1|TEMPLATE|contrib' | wc -l)
			if [ "$SDP_CHECK" != "1" ]
			then
				echo "WARNING: There are more than one SDP for $BLOCK_NAME"
			fi
			SDP_NAME_PATH=`ls $CXC_PATH/packages/sdp/*.sdp | grep -Ev 'I1|U1|TEMPLATE|contrib'`
			for i in $SDP_NAME_PATH; do 
				SDP_NAME=$(basename $i)
				cp $CXC_PATH/packages/sdp/$SDP_NAME $TMP_DIR/$IPA_SDPS_FOLDER
			done
		else
			echo "ERROR: SDP folder not found for $BLOCK_NAME"
			exit 7
		fi	
	done < $TMP_DIR/$SOURCE_APG_SDP
fi
#check if sources.list bloks are the same as downloaded bundles

if [ "$OPT_MINIIPA" = "$TRUE" ]; then
	is_verbose && echo "DEBUG: skipping check for sources.list and  bundles match "
else 
	is_verbose && echo "DEBUG: check if sources list and downloaded bundle match"
	MATCH=$TRUE

	while read line
        do
	    if [[ ! "$line" =~ ^#.* ]]; then
		BLOCK_NAME=`echo $line | awk -F';' '{print $2}'| sed  "s/^ERIC-//g"`
		
		if [[ ! "$BLOCK_NAME" =~ ^COM.* ]] && [[ ! "$BLOCK_NAME" =~ ^ComSa.* ]]; then

                	echo "DEBUG: check for BLOCK $BLOCK_NAME "

                	if ls $TMP_DIR/$IPA_SDPS_FOLDER/$BLOCK_NAME* &> /dev/null; then
                        	is_verbose && echo "$BLOCK_NAME --------------- DO EXIST"
                	else
                           	is_verbose && echo "$BLOCK_NAME --------------- DO NOT EXIST"
			   	MATCH='FALSE'
                	fi
		fi
	    fi

        done < $CONF_FOLDER/$SOURCE_FILE_NAME
fi

if [ "$MATCH" != "$TRUE" ] && [ "$OPT_MINIIPA" != "$TRUE" ]; then
	echo "ERROR: campaign sdps list and downloaded bundle do not match" 
#	exit 7
fi
#if not a MINIIPA copy AP2.conf file in the root for sw.tgz
#this file will be used durign deploy
if [ "$OPT_MINIIPA" == "$TRUE" ]; then
  cp $CONF_FOLDER/$MINIIPA_FILE_NAME $TMP_DIR
fi

# CHECK IF CAMPAIGN FILE AND SDP FILE MATCH IN NUMBER	

# Create the package sw.tgz
pushd $TMP_DIR >> /dev/null
if [ "$OPT_MINIIPA" == "$TRUE" ]; then
  tar -czf $IPA_NAME $MINIIPA_FILE_NAME $IPA_CAMPAIGN_FOLDER/ $IPA_CMW_FOLDER/ $IPA_SDPS_FOLDER/
else
   tar -czf $IPA_NAME $IPA_CAMPAIGN_FOLDER/ $IPA_CMW_FOLDER/ $IPA_SDPS_FOLDER/
fi
popd >> /dev/null
cp $TMP_DIR/$IPA_NAME $IPA_FOLDER/$IPA_NAME
is_verbose && echo "INFO: $IPA_NAME successfully created!!!"
#Remove TMP folder
rm -rf $TMP_DIR
