#!/bin/bash
##
# -----------------------------------------------------------------------------
#             Copyright (C) 2015 Ericsson AB. All rights reserved.
# -----------------------------------------------------------------------------
##
# Name:
#   apg_common.sh
# Description:
#   A common file to use kill_after_try functionality
# Usage:
#   None.
##
# Output:
#   None.
##
# Changelog:
# - Thr Jun 16 2016 - Yeswanth Vankayala (xyesvan)
#          first release
##
. /opt/ap/apos/conf/apos_common.sh

# global variables
EXHAUSTED=255

# usage:
#   try <attempts> <interval> <command> [<argument1> ... <argumentN>]
#
# The function executes <command> for a maximum of <attempts> times and waits
# <interval> seconds between each attempt. It returns <command>'s return code
# upon completion, $EXHAUSTED in the case the command has failed for all
# available attempts, $FALSE in the case of wrong usage.
function try(){
  if [ $# -lt 3 ]; then
    echo "wrong number of parameters ($#)" >&2
    return $FALSE
  elif [[ ! $1 =~ ^[0-9]+$ ]]; then
    echo "positive integer expected (found \"$1\")" >&2
    return $FALSE
  elif [[ ! $2 =~ ^[0-9]+(\.[0-9]+)*$ ]]; then
    echo "positive decimal expected (found \"$2\")" >&2
    return $FALSE
  else
    local MAX_ATTEMPTS=$1
    local SLEEP_TIME=$2
    shift; shift
    local COMMANDLINE=$@
    
    for ((i=0; i<${MAX_ATTEMPTS}; i++)); do
      ${COMMANDLINE}
      local RETCODE=$?
      if [ $RETCODE -eq 0 ]; then
        return $RETCODE
      fi
      sleep ${SLEEP_TIME}
    done
    return $EXHAUSTED
  fi
}

# usage:
#   kill_after <timeout> <command> [<argument1> ... <argumentN>]
#
# The function executes <command> and awaits for its completion for a maximum of
# <timeout> seconds before interrupting (SIGINT) the process.
# If after <timeout>+2 seconds the process is still executing (SIGINT has not 
# successfully interrupted it), SIGKILL gets sent.
# The function returns 124 if timeout has expired before command completion,
# $FALSE in the case of wrong usage or the return code of $COMMAND otherwise.
function kill_after(){
  if [ $# -lt 2 ]; then
    echo "wrong number of parameters ($#)" >&2
    return $FALSE
  elif [[ ! $1 =~ ^[0-9]+$ ]]; then
    echo "positive integer expected (found \"$1\")" >&2    
    return $FALSE
  else
    local SIGINT_TMOUT=$1
    shift
    local SIGKILL_TMOUT=$((${SIGINT_TMOUT}+2))
    local COMMANDLINE=$@
    
    /usr/bin/timeout --signal=INT --kill-after=${SIGKILL_TMOUT} ${SIGINT_TMOUT} ${COMMANDLINE}
    return $?
  fi
}

# usage:
#   kill_after_try <attempts> <interval> <timeout> <command> [<argument1> ... <argumentN>]
#
# The function executes <command> for a maximum of <attempts> times and waits
# <interval> seconds between each attempt. If each command invocation does not
# terminate after <timeout> seconds, it gets interrupted (SIGINT).
# If after <timeout>+2 seconds the process is still executing (SIGINT has not 
# successfully interrupted it), SIGKILL gets sent.
# The function returns 124 if timeout has expired before command completion,
# $FALSE in the case of wrong usage or the return code of $COMMAND otherwise.
function kill_after_try(){
  if [ $# -lt 4 ]; then
    echo "wrong number of parameters ($#)" >&2
    return $FALSE
  else
    local MAX_ATTEMPTS=$1
    local SLEEP_TIME=$2
    local SIGINT_TMOUT=$3
    shift; shift; shift
    local COMMANDLINE=$@

    try $MAX_ATTEMPTS $SLEEP_TIME kill_after $SIGINT_TMOUT $COMMANDLINE
    return $?
  fi
}
