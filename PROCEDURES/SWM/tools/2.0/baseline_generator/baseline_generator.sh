#!/bin/bash
##
# ------------------------------------------------------------------------
#     Copyright (C) 2020 Ericsson AB. All rights reserved.
# ------------------------------------------------------------------------
##
# Name:
#       baseline_generator.sh 
# Description:
#       A script to generate baselines  
# Usage:
##   ./baseline_generator <input_baseline_file> <config>
##
# Changelog:
# - Thu Nov 26 2020 - Yeswanth Vankayala (XYESVAN)
#    Implemented changes for Phase 1
# - Wed Oct 7 2020 - Yeswanth Vankayala (XYESVAN)
#   First version.

#Common Variables
CURDIR=$(dirname $0)
OUTPUT_DIR="../../../workspace/integrity-files"
BASELINE_FILE="acs_lct_sha1verify.conf"
CONFIGURATION=$CURDIR/etc/files_list.cfg
AP_TYPE=$(echo $OUTPUT_CONFIG | awk -F '_' '{print $1}')
HW_TYPE=$(echo $OUTPUT_CONFIG | awk -F '_' '{print $2}')


#Logging Function
function logger {
   echo "$1"
}

#Usage Function
function usage() (
cat <<- EOF

Usage:
  ./baseline_generator <input_baseline_file> <config>

  input_baseline_file: This is the input baseline file required to generate
                       output baselines. 
                       Ex: AP1_GEP5_acs_lct_sha1verify.conf
  config: Configuration for which baselines to be generated 
          Ex: GEP5_AP1, GEP5_AP1_SMX etc

  Example:
     ./baseline_generator AP1_GEP5_acs_lct_sha1verify.conf AP1_GEP7


  [Supported Config]:
  
   Input     |        Output
  ----------------------------------------------------------------------
  AP1_GEP7    | AP1_GEP5, AP1_GEP5_SMX, AP1_GEP7_SMX, AP2_GEP7, AP2_GEP5
  ----------------------------------------------------------------------
  AP1_GEP5    | AP1_GEP7, AP1_GEP5_SMX, AP1_GEP7_SMX, AP2_GEP5, AP2_GEP7
  ----------------------------------------------------------------------
  AP1_GEP7_SMX| AP1_GEP5, AP1_GEP5_SMX, AP1_GEP7, AP2_GEP7, AP2_GEP5
  ----------------------------------------------------------------------
  AP1_GEP5_SMX| AP1_GEP7, AP1_GEP5, AP1_GEP7_SMX, AP2_GEP7, AP2_GEP5
  ----------------------------------------------------------------------
  AP2_GEP5    | AP2_GEP7
  ----------------------------------------------------------------------
  AP2_GEP7    | AP2_GEP5
  ----------------------------------------------------------------------
  AP1_GEP2    | AP2_GEP2
  ----------------------------------------------------------------------

EOF

)

#Generation of baseline files for Phase 0
function generate_baseline {
  GEN_CONFIG=$1
  INPUT_CONFIG=$2
  logger "Creation of baseline for $GEN_CONFIG started..."
  cp "$INPUT_CONFIG"  "$OUTPUT_DIR/${GEN_CONFIG}_$BASELINE_FILE"
  if [ $? -eq 0 ]; then
   logger "Creation of baseline for $GEN_CONFIG successfull..." 
   logger "Output is present in $OUTPUT_DIR"
  else
   logger "Creation of baseline for $GEN_CONFIG failed..." 
  fi
}


#Generation of baseline files for Phase 1
function generate_baseline_ap2 {
   GEN_CONFIG=$1
   INPUT_CONFIG=$2
   BASELINE="/tmp/${INPUT_CONFIG}"
   AP_TYPE=$(echo $GEN_CONFIG | awk -F '_' '{print $1}')
   if [ "$AP_TYPE" == "AP1" ]; then
     logger  "Invalid entry in AP2 Baseline Generation"
     usage
     exit 1
   fi
   cp $INPUT_CONFIG $BASELINE
  logger "Creation of baseline for $GEN_CONFIG started..."
   while read line
   do
     echo $line | grep $AP_TYPE &>/dev/null
     [ $? -ne 0 ] && continue
     baseline_entry=$(echo $line | awk -F ';' '{print $3}' )
     condition=$(echo $line | awk -F ';' '{print $2}')
     checksum=$(echo $line | awk -F ';' '{print $4}')
     if [ $condition == "EXCLUDE" ]; then
       sed -i "\|\"${baseline_entry}\"|d" $BASELINE
     else
       sed -i "\#$baseline_entry#c\"$baseline_entry\"$checksum" $BASELINE
     fi
  done <$CONFIGURATION
  mv "$BASELINE" "$OUTPUT_DIR/${GEN_CONFIG}_$BASELINE_FILE"
  logger "Creation of baseline for $GEN_CONFIG successfull..."

}


function sanity_check {
    INPUT_BASELINE=$1
    OUTPUT_CONFIG=$2
    INPUT_FILE=$CURDIR/$INPUT_BASELINE
    if [[ ! -f "$INPUT_FILE" || -z "$OUTPUT_CONFIG" ]]; then
      logger "File $INPUT_BASELINE does not exist or Invalid arguments"
      usage
      exit 1
    fi
}


# _____________________
#|    _ _   _  .  _    |
#|   | ) ) (_| | | )   |
#|_____________________|
# Here begins the "main" function...

if [ $# -le 1 ];then
  logger "Wrong number of arguments passed"
  usage
  exit 1
fi

sanity_check $@ 

INPUT_CONFIG=$(echo "$INPUT_BASELINE" | awk -F "/" '{print $NF}' | awk -F "_${BASELINE_FILE}" '{print $1}')

case "$INPUT_CONFIG" in
      AP1_GEP[5,7]|AP1_GEP[5,7]_SMX)
        #Baseline creator for GEP5 and GEP7 Config 
        if [[ "$OUTPUT_CONFIG" =~ AP1_GEP[5,7]$ || "$OUTPUT_CONFIG" =~ AP1_GEP[5,7]_SMX$ ]]; then
          generate_baseline "$OUTPUT_CONFIG" "$INPUT_BASELINE" 
        elif [[ "$OUTPUT_CONFIG" =~ AP2_GEP[5,7]$ ]]; then
          generate_baseline_ap2 "$OUTPUT_CONFIG" "$INPUT_BASELINE"
        else 
           logger "Invalid Configuration"
           usage
           exit 1
        fi
        ;;
      AP2_GEP[5,7])
        #Baseline creator for GEP5 and GEP7 Config AP2
        if [[ "$OUTPUT_CONFIG" =~ AP2_GEP[5,7]$ ]]; then
          generate_baseline "$OUTPUT_CONFIG" "$INPUT_BASELINE"
        else 
           logger "Invalid Configuration"
           usage
           exit 1
        fi
        ;;
        AP1_GEP2)
        #Baseline creator for GEP2 AP2 Config
        if [ "$OUTPUT_CONFIG" == "AP2_GEP2" ]; then
           generate_baseline_ap2 "$OUTPUT_CONFIG" "$INPUT_BASELINE"
        else
           logger "Invalid Configuration"
           usage
           exit 1
        fi
        ;;
      help|*)
        usage
        exit 1
        ;;
esac
