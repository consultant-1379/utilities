#!/bin/bash 
##
# ------------------------------------------------------------------------
#     Copyright (C) 2013 Ericsson AB. All rights reserved.
# ------------------------------------------------------------------------
##
# Name:
#      entry_matches.sh
# Description:
#       A script to check a include/exclude block/SU's.
# Note:
#       None.
##
# Output:
#       None.
##
# Changelog:
# - 2016 Jul 06 - Avinash Gundlapally (xavigun)
#      Added functionality for cmd inhibit feature, file in unix format
# - 2016 Jul 05 - Yeswanth Vankayala (xyesvan)
#      Description added to functions 
# - 2016 Jun 16 - Yeswanth Vankayala (xyesvan)
#       Update file to support BUP 2.2.0
# - 2016 May 17 - Yeswanth Vankayala (xyesvan)
#       Added some Enhancements
# - 2016 Feb 26 - Yeswanth Vankayala (xyesvan)
#       First version.
##

true=$(true; echo $?)
false=$(false; echo $?)

tag="entry_matches.sh"
current_dir="$(dirname "$(readlink -f $0)")"
storage_api='/usr/share/pso/storage-paths/config'
storage_path=$(cat $storage_api)
storage_apos="$storage_path/apos"
install_list_file="$current_dir/apps_list.csv"
activate_list_file="$current_dir/apps_lock_list.csv"
node_lock_list_file="$current_dir/node_lock_list.conf"
cmd_parmtool="$current_dir/parmtool/parmtool"
cmd_logger=''
ecode=$false
opt_node_lock=$false
opt_install=$false
opt_app_lock=$false
install_args=''
app_lock_args=''
shelf_arch=''
opt_evaluate_parms=$false
evaluate_parameters=''
libcli_extension_file="/opt/ap/apos/conf/libcli_extension_subshell.conf"

function abort(){
	log "An error occurred. Exiting!"
  exit 1
}

function log(){
	local message="$@"
	$cmd_logger -t $tag "$message" &>/dev/null
}

function usage_error(){
cat <<EOF
 Usage:
  
 entry_matches.sh install block
 entry_matches.sh app-lock dn
 entry_matches.sh node-lock
 entry_matches.sh node-lock install block

EOF
exit 1
}

function sanity_check(){
  cmd_logger=$( which logger 2>/dev/null )
  [ -z "$cmd_logger" ] && cmd_logger='/bin/logger'
}

# This function will fetch configuration parameters from the node and returns the 
# configuration parameter value.
function fetch_value(){
	local lvalue=$1
	local rvalue=$( $cmd_parmtool get --simulated --item-list $lvalue 2>/dev/null | awk -F'=' '{print $2}')
  if [ -z "$rvalue" ];then
    [ $lvalue == 'ap_type' ] && lvalue='aptype.conf'
    rvalue=$(cat "$storage_apos/$lvalue" 2>/dev/null)
    if [[ "$lvalue" == 'shelf_architecture' && -z "$rvalue" ]];then
      if [ -z "$shelf_arch" ];then
        shelf_arch=$(immlist axeFunctionsId=1 | grep -w apgShelfArchitecture | awk -F' ' '{print $3}')
      fi
      [ $shelf_arch -eq '0' ] && rvalue='SCB'
      [ $shelf_arch -eq '1' ] && rvalue='SCX'
      [ $shelf_arch -eq '2' ] && rvalue='DMX'
      [ $shelf_arch -eq '3' ] && rvalue='VIRTUALIZED'
      [ $shelf_arch -eq '4' ] && rvalue='SMX'
    fi
    [ -z "$rvalue" ] && abort "Parameter [$lvalue] value found NULL!"
  fi
  echo "$rvalue"
}

# This function will check the entry in the .csv provided and 
# returns true or false based on the conditions provided in .csv 
# file.                                                          
function entry_in_file_matches(){
  local entry=$1
  local entry_list_file=$2
  local file=$(mktemp --tmpdir $(basename $entry_list_file)_XXX)

  tail -n +2 $entry_list_file >$file
  local list=$(grep -wP "^${entry}" $file)
  [ -z "$list" ] && return $true  # in case the block not found in the $file

  local tag=$(echo $list | awk -F ";" '{print $2}')
  list=$(echo $list | sed -r 's/^\w+,\w+(,|$)//g' | tr -d '\r' | cut -d';' -f3-)
  old_IFS=$IFS;IFS=$'\n'
  local include_result="$false"
  local exclude_result="$true"
  for item in $(echo $list | tr ';' $'\n'); do
    if echo $item | grep -Eq '^.*.&&.*.$'; then
      IFS=$old_IFS
      validate_multiple_conditions "$item"
      result=$(echo $?)
      if [[ "$tag" == "EXCLUDE" && $result -eq $true  ]];then
         exclude_result="$false"
      elif [[ "$tag" == "INCLUDE" && $result -eq $true  ]];then
         include_result="$true"
      fi 
    else
      lvalue=$(echo $item | awk -F'=' '{print $1}'| tr -d '[[:space:]]')
      rvalue1=$(echo $item | awk -F'=' '{print $2}'| tr -d '[[:space:]]')
      rvalue2=$(fetch_value $lvalue)
      
      # if reqex in rvalue1
      if [[ ${rvalue1:0:1} == '~' ]]; then
        length=${#rvalue1}
        if [[ $rvalue2 =~ ${rvalue1:1:$length} ]]; then
          rm -f $file
          log " in match regex"
          log "$entry  matched .. checking condition"
          [ "$tag" == "EXCLUDE" ] && exclude_result="$false"
          [ "$tag" == "INCLUDE" ] && include_result="$true"
        fi
      else
         if [[ "$rvalue2" == "$rvalue1" ]]; then      #rvalue1 without regex
           rm -f $file
           log " in match "
           log "$entry  matched .. checking condition"
           [ "$tag" == "EXCLUDE" ] && exclude_result="$false"
           [ "$tag" == "INCLUDE" ] && include_result="$true"
         fi
      fi
     fi
  done
  rm -f $file

  [ "$tag" == "EXCLUDE" ] && return $exclude_result
  [ "$tag" == "INCLUDE" ] && return $include_result
  log "$entry not matched .. "
  [ "$tag" == 'EXCLUDE' ] && return $true
  return $false
}

# This functions will handles regex expressions and also multiple 
# AND conditions of an entry in .csv file                                                         
function validate_multiple_conditions(){
  local entry="$@"
	local rcode=$true

  for item in $(echo $entry | tr '&&' '\n'); do
    lvalue=$(echo $item | awk -F'=' '{print $1}' | tr -d '[[:space:]]')
    rvalue1=$(echo $item | awk -F'=' '{print $2}'| tr -d '[[:space:]]')
    rvalue2=$(fetch_value $lvalue)

		# if reqex in rvalue1
		if [[ ${rvalue1:0:1} == '~' ]]; then
			length=${#rvalue1}
			[[ $rvalue2 =~ ${rvalue1:1:$length} ]] && continue
			rcode=$false; break
		else # without regex
      [[ "$rvalue2" == "$rvalue1" ]] && continue
      rcode=$false; break
    fi
  done

  return $rcode
}

# This function returns true or false to lock nodes based on 
# hardware platform entry present in node_lock_list.conf            
function lock_nodes(){
	local rcode=$true
  while read line
  do
   if echo $line | grep -Eq '^.*.&&.*.$'; then
	    validate_multiple_conditions "$line"
      result=$(echo $?)
  	  
	    # flip the result
      [ $result -eq $true ] && return $false
      return $true
    else
      lvalue=$(echo $line | awk -F'=' '{print $1}' | tr -d '[[:space:]]')
      rvalue1=$(echo $line | awk -F'=' '{print $2}'| tr -d '[[:space:]]')
      rvalue2=$(fetch_value $lvalue)
			
			# if reqex in rvalue1
			if [[ ${rvalue1:0:1} == '~' ]]; then
				length=${#rvalue1}
				if [[ $rvalue2 =~ ${rvalue1:1:$length} ]];then
					rcode=$false
					break
        fi
			else
        [[ $rvalue2 == $rvalue1 ]] && rcode=$false # without regex
				break
      fi
    fi
  done < $node_lock_list_file
  return $rcode
}

# This functions will returns true/false to lock apps present in
# apps_lock_list.csv file based on the conditions             
function lock_apps(){
    local entry=$1
    local sg=$(echo $entry | awk -F ',' '{print $2}' | awk -F '=' '{print $2}')
    if [ "$sg" != '2N' ];then
      block=$(echo $sg | awk -F '_' '{print $2}' | awk -F ',' '{print $1}')
      [ -z "$block" ] && return $true
      entry_in_file_matches $block $install_list_file
      [ $? -eq $false ] && return $false
    fi
    rcode=$(entry_in_file_matches $entry $activate_list_file; echo $?)  
    
    return $rcode
}

# This function parses command line arguments.
function parse_args(){
  local OPTIONS='node-lock install: app-lock: evaluate:'

  /usr/bin/getopt --quiet --quiet-output --longoptions="$OPTIONS" "$@"

  ARGS="$@"
  eval set -- "$ARGS"
  ARGC=$#
  while [ $# -gt 0 ]
  do
    case $1 in
       node-lock)
            opt_node_lock=$true
            shift 1
       ;;
       install)
						opt_install=$true
						install_args=$2
						[ -z "$install_args" ] && usage_error
            shift 2
       ;;
       app-lock)
						opt_app_lock=$true
						app_lock_args=$2
						[ -z "$app_lock_args" ] && usage_error
            shift 2
       ;;
	evaluate)
                                                opt_evaluate_parms=$true
          shift 1
                                                evaluate_parameters="$@"
                                                [ -z "$evaluate_parameters" ] && usage_error
           shift `expr $ARGC - 1`
       ;;
			*)
				usage_error
			 ;;
    esac
 done
}
#This function is to validate command applicability in a specfic configuration based in the paramaters passed.
function validate_conditions(){
cmd_name=$1
libcli_ext_file=$2
local list=$(cat $libcli_ext_file | grep -wP "^$cmd_name")
[ -z "$list" ] && return $true  # in case the block not found in the $file
list=$(echo $list | cut -d ";" -f 5-)

local tag=$(echo $list | awk -F ";" '{print $1}')
local argcount=$(echo $list | tr ';' $'\n'|wc -l)
if [ $argcount -gt 1 ]; then
  list=$(echo $list | cut -d ";" -f 2- )
  old_IFS=$IFS;IFS=$'\n'
  local include_result="$false"
  local exclude_result="$true"
  for item in $(echo $list | tr ';' $'\n'); do
    if echo $item | grep -Eq '^.*.&&.*.$'; then
      IFS=$old_IFS
      validate_multiple_conditions "$item"
      result=$(echo $?)
      if [[ "$tag" == "EXCLUDE" && $result -eq $true  ]];then
         exclude_result="$false"
      elif [[ "$tag" == "INCLUDE" && $result -eq $true  ]];then
         include_result="$true"
      fi
    else
      lvalue=$(echo $item | awk -F'=' '{print $1}'| tr -d '[[:space:]]')
      rvalue1=$(echo $item | awk -F'=' '{print $2}'| tr -d '[[:space:]]')
      rvalue2=$(fetch_value $lvalue)

      # if reqex in rvalue1
      if [[ ${rvalue1:0:1} == '~' ]]; then
        length=${#rvalue1}
        if [[ $rvalue2 =~ ${rvalue1:1:$length} ]]; then
          rm -f $file
          log " in match regex"
          log "$cmd_name command conditions for node matched .. checking to include/exclude the command..."
          [ "$tag" == "EXCLUDE" ] && exclude_result="$false"
          [ "$tag" == "INCLUDE" ] && include_result="$true"
        fi
      else
         if [[ "$rvalue2" == "$rvalue1" ]]; then      #rvalue1 without regex
           rm -f $file
           log " in match "
           log "$cmd_name command conditions for node matched .. checking to include/exclude the command..."
           [ "$tag" == "EXCLUDE" ] && exclude_result="$false"
           [ "$tag" == "INCLUDE" ] && include_result="$true"
         fi
      fi
     fi
  done
  [ "$tag" == "EXCLUDE" ] && return $exclude_result
  [ "$tag" == "INCLUDE" ] && return $include_result
else
  [ "$tag" == "EXCLUDE" ] && return $false
  [ "$tag" == "INCLUDE" ] && return $true
fi
}

# This function will invokes relavant functions based on the conditions.
function invoke(){
	ecode=$false

  if [[ $opt_node_lock -eq $true && $opt_install -eq $true ]]; then
		if (( ! $( lock_nodes; echo $?) & ! $( entry_in_file_matches $install_args $install_list_file; echo $?))); then
			ecode=$true
		fi		
  elif [[ $opt_node_lock -eq $true && $opt_install -eq $false ]]; then
  	ecode=$( lock_nodes; echo $?)
	elif [[ $opt_install -eq $true && $opt_node_lock -eq $false ]]; then
		ecode=$( entry_in_file_matches $install_args $install_list_file; echo $?)
  elif [[ $opt_app_lock -eq $true ]]; then
    ecode=$( lock_apps $app_lock_args; echo $?)
  elif [[ $opt_evaluate_parms -eq $true ]]; then
    ecode=$(validate_conditions $evaluate_parameters $libcli_extension_file)	
	fi
 
  return $ecode
}

#### M A I N #####

sanity_check

parse_args "$@"

invoke

exit $ecode
