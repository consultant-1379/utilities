#!/bin/bash 
##
# ------------------------------------------------------------------------
#     Copyright (C) 2015 Ericsson AB. All rights reserved.
# ------------------------------------------------------------------------
##
# Name:
#       parmtool_common.sh
# Description:
#       A collection of common functions for the parmtool script.
##
# Usage:
# source <parmtool_root>/lib/common/parmtool_common.sh
#
##
# Changelog:
# - Wed Nov 18 2015 - Pratap Reddy (xpraupp)
#   First Version
##

# exports
export TRUE=$( true; echo $? )
export FALSE=$( false; echo $? )
export LOG_TAG='parmtool'
export CMD_DIR="${PARMTOOL_ROOT}/cmd"
export LIB_DIR="${PARMTOOL_ROOT}/lib"
export MAN_DIR="${LIB_DIR}/man"
export CMD_VALIDATE_DIR="$CMD_DIR/validate"
export LIB_COMMON_DIR="$LIB_DIR/common"
export CMD_T2XCONVERTER="$CMD_VALIDATE_DIR/T2XConverter"
export CMD_SCRIPT_BASED_VALIDATION="$CMD_VALIDATE_DIR/script_based_validation"
export APG_SCHEMA="$CMD_VALIDATE_DIR/APGParms.xsd"
export PSO_DB="$LIB_COMMON_DIR/PSO.db"
export PSO_PATH=''

# commands set
CMD_CAT='/bin/cat'
CMD_GETOPT='/usr/bin/getopt'
CMD_XMLLINT='/usr/bin/xmllint'
CMD_RM='/bin/rm'
CMD_ECHO='/bin/echo'
CMD_CUT='/usr/bin/cut'
CMD_GREP='/usr/bin/grep'
CMD_AWK='/usr/bin/awk'
CMD_TR='/usr/bin/tr'
CMD_BASENAME='/usr/bin/basename'
CMD_LOGGER='/bin/logger'
CMD_FILE='/usr/bin/file'
CMD_INSTALL='/usr/bin/install'


# common checks
[ -f /usr/share/pso/storage-paths/config ] && PSO_PATH=$(</usr/share/pso/storage-paths/config)
[ ! -d /tmp/apos ] && mkdir -p /tmp/apos

# -----------------------------------------------------------------------------
function log(){
    local PRIO='-p user.notice'
    local MESSAGE="${*:-notice}"
    $CMD_LOGGER $PRIO $LOG_TAG "$MESSAGE" &>/dev/null
}

# -----------------------------------------------------------------------------
# The function will log an error message in the system log. If the --verbose
# option has been specified, it will print the same message on stderr too.
function log_error(){
    local PRIO='-p user.err'
    local MESSAGE="${*:-error}"
    $CMD_LOGGER $PRIO $LOG_TAG "$MESSAGE" &>/dev/null
}

# -----------------------------------------------------------------------------
function usage_error(){
  usage
  abort "$1"
}

# -----------------------------------------------------------------------------
function abort(){
  echo "ABORTING: <"$1">"
  exit $FALSE
}

# -----------------------------------------------------------------------------
function console_print(){
	echo -e "$@"
}

# -----------------------------------------------------------------------------
function get_commands(){
  local COMMANDS=''
  for DIR in $(find $CMD_DIR -type d 2>/dev/null); do
    DIR=$(basename $DIR)
    [[ ! $DIR =~ ^${CMD_DIR}$ ]] && COMMANDS="${COMMANDS}${DIR} "
  done
  echo $COMMANDS
}

# -----------------------------------------------------------------------------
function trim(){
  local LIST="$*"
  # remove leading whitespace characters
  LIST="${LIST#"${LIST%%[![:space:]]*}"}"
  # remove trailing whitespace characters
  LIST="${LIST%"${LIST##*[![:space:]]}"}"
  $CMD_ECHO -n "$LIST"
}

# -----------------------------------------------------------------------------
function is_cmd_valid(){
  local COMMAND=''
  if [ $# -gt 0 ]; then
    COMMAND=$1
  else
    abort 'missing parameter'
  fi
  local VALID_COMMANDS=$(get_commands)
  for C in $VALID_COMMANDS; do
    [ "$COMMAND" == "$C" ] && return $TRUE
  done
  return $FALSE
}

# -----------------------------------------------------------------------------
function isXML(){
  local FILE="$1"
  local FILE_FORMAT=$( $CMD_FILE $FILE | $CMD_AWK -F: '{print $2}' |\
  $CMD_TR -d "^[[:space:]]" &>/dev/null)
  if [ "$FILE_FORMAT" == 'XML' ]; then
    return $TRUE;
  fi

  return $FALSE
}

# -----------------------------------------------------------------------------
function check_file_format(){
	local FILE="$1"
	local PATTERN='[!@#$%^&*()-+/:;<>{}]'
	while read LINE; do
 		if $CMD_ECHO "$LINE" | $CMD_GREP -qP $PATTERN; then
   		return $FALSE
		fi
	done <$FILE

 	return $TRUE
}

# -----------------------------------------------------------------------------
function check_itemlist_format(){

  local ITEM_LIST=$1
  local COUNT=1
  local PATTERN1='^[^[:space:]=]+=[^[:space:]=,:#@!^]+$'
  local PATTERN2='^[^[:space:],]+,*[^[:space:],=:#@!^]+$'
  local PATTERN3='[!@#$%^&*()-+./:;<>{}]'
  local ITEM_COUNT=$($CMD_ECHO "$ITEM_LIST" | $CMD_AWK -F, '{print NF}')
  while [ $COUNT -le $ITEM_COUNT ]; do
    ITEM=$($CMD_ECHO "$ITEM_LIST" | $CMD_AWK -F',' "{print $"$COUNT"}")
    [[ -z "$ITEM" ]] && return $FALSE
    #$($CMD_ECHO "$ITEM" | $CMD_GREP -qP "$PATTERN1")
    #[[ $? -eq $FALSE ]] && return $FALSE

    $CMD_ECHO "$ITEM" | $CMD_GREP -qP "$PATTERN2"
    [ $? -eq $FALSE ] && return $FALSE

    $CMD_ECHO "$ITEM" | $CMD_GREP -qP "$PATTERN3"
    [ $? -eq $TRUE ] && return $FALSE

    ((COUNT++))
  done

  return $TRUE
}

# -----------------------------------------------------------------------------
function isNULL() {

  local RETVALUE=$FALSE
  [ $# -eq 0 ] && RETVALUE=$TRUE

  return $RETVALUE
}

# -----------------------------------------------------------------------------
function parmtool_get_all() {

  while read LINE ; do
    if ! $CMD_ECHO "$LINE" | $CMD_GREP -q "^#"; then
      PARAM_PATH=$( $CMD_ECHO $LINE | $CMD_AWK -F';' '{print $2}')
      PARAM=$( $CMD_ECHO $LINE | $CMD_AWK -F';' '{print $1}')
      RESULT="$RESULT $PARAM=$($CMD_CAT $PSO_PATH/$PARAM_PATH 2>/dev/null)"
    fi
  done < $PSO_DB
  $CMD_ECHO $RESULT
}

