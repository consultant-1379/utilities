#!/bin/bash

<< 'About'
	This script filters out excess files generated that are not considered as part of baseline.
	Filtering is done with reference to "acs_lct_integrityAP_base.conf" file.
About

INTEGRITYAPBASE="acs_lct_integrityAP_base.conf"
INCLUSION=()
EXCLUSION=()
INCLUSION_FILES=()
EXCLUSION_FILES=()
prefix_list=()
IFS=' '
COMMENT="#"
pwd
#Parsing "acs_lct_integrityAP_base.conf" file to create above mentioned Arrays
while read -r line
do
	#echo $line
	IFS=' '
	CURARR=($line)
	#echo ${CURARR[1]}
	if [[ "$line" =~ ^$COMMENT ]];then
                continue;
        fi
	if [ "${CURARR[1]}" = "false" ];then
		EXCLUSION+=(${CURARR[0]:1:-1})
		prefix=${CURARR[0]:1:-1}
		prefix_list+=($prefix)
		for i in ${CURARR[@]:3}
		do
			IS_REGEX=0
			if [[ "$i" =~ "["|"{"|"}"|"$"|"]" ]];then
				IS_REGEX=1
				#echo $i, "This is a regular expression"
				INCLUSION+=($prefix/$i)
			fi
			if [ "$IS_REGEX" -eq "0" ]; then
		                #echo "This is not regex"
				INCLUSION_FILES+=($prefix/$i)
				EXTENSION=$(echo $i | awk -F '/' '{print $NF}' | awk -F '.' '{print $NF}')
				FILE_NAME=$(echo $i | awk -F '/' '{print $NF}')
				#echo $i $EXTENSION $FILE_NAME
				if [ $EXTENSION = $FILE_NAME ]; then
					INCLUSION+=($prefix/$i/)
				fi
        		fi

			#echo $prefix/$i
		done
	else
		INCLUSION+=(${CURARR[0]:1:-1})
                prefix=${CURARR[0]:1:-1}
		prefix_list+=($prefix)
                for i in ${CURARR[@]:3}
                do
			IS_REGEX=0
                        if [[ "$i" =~ "["|"{"|"}"|"$"|"]" ]];then
                                IS_REGEX=1
                                #echo $i, "This is a regular expression"
				EXCLUSION+=($prefix/$i)
                        fi
                        if [ "$IS_REGEX" -eq "0" ]; then
                                #echo "This is not regex"
				EXCLUSION_FILES+=($prefix/$i)
                                EXTENSION=$(echo $i | awk -F '/' '{print $NF}' | awk -F '.' '{print $NF}')
				FILE_NAME=$(echo $i | awk -F '/' '{print $NF}')
				#echo $i $EXTENSION $FILE_NAME
                                if [ $EXTENSION = $FILE_NAME ]; then
                                        EXCLUSION+=($prefix/$i/)
                                fi
                        fi
                        
			#echo $prefix/$i
                done
	fi

done < "$INTEGRITYAPBASE"
IFS='
'
#Filtering out each entry in baseline file 
for i in $(cat res/formatted_intermediate_baseline); do
	binary_name=$(echo $i | awk -F '"' '{print $2}')
	canInclude=0
	mustExclude=0
	for item in "${EXCLUSION[@]}"; do
        	if [[ "$binary_name" =~ ^$item ]]; then
			if [ "$(echo ${prefix_list[@]} | grep $item | wc -l)" -eq "0" ];then
				mustExclude=1
			fi
	        	canInclude=0
        	fi
	done
	
	for item in "${INCLUSION[@]}"; do
                if [[ "$binary_name" =~ ^$item ]]; then
			if [ "$mustExclude" -eq "0" ];then
                        	canInclude=1
			fi
                fi
        done

	for item in "${INCLUSION_FILES[@]}"; do
                if [ "$binary_name" = $item ]; then
                        canInclude=1
                fi
        done

	for item in "${EXCLUSION_FILES[@]}"; do
                if [ "$binary_name" = $item ]; then
                        canInclude=0
                fi
        done

	if [ "$canInclude" -eq "1" ]; then
        	echo "$i" >> res/filtered_intermediate_baseline 
	#else
        	#echo "$i not included"
    	fi

done
