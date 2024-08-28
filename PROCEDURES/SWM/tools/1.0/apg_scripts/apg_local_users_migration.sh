#!/bin/bash
##
# ------------------------------------------------------------------------
#     Copyright (C) 2016 Ericsson AB. All rights reserved.
# ------------------------------------------------------------------------
##
# Name:
#       apg_local_users_migration.sh
# Description:
#       A script to migrate APG local users from the temporary solution 
#       (LA ph. 0) to the final solution implemented in APG43L 3.2
##
# Changelog:
# - Wed May 3 2017 - Avinash G
#     Adaptations for Sec 2.2.2
# - Wed Jul 20 2016 - Alessio Cascone (ealocae)
#       Added pre-checks on uppercase username values.
# - Mon May 23 2016 - Alessio Cascone (ealocae)
#       Improvements.
# - Mon May 13 2016 - Alessio Cascone (ealocae)
#       First version.
##

# Load the apos common functions.
. /opt/ap/apos/conf/apos_common.sh

##### START: Common variables section
# Script options
OPTION_PRECHECKS=$FALSE
OPTION_RUN_MIGRATION=$FALSE
OPTION_MIGRATE=$FALSE

# Commands used inside the script itself
AWK_CMD=''
CAT_CMD=''
CP_CMD=''
ECHO_CMD=''
GETOPT_CMD=''
GREP_CMD=''
HEAD_CMD=''
ID_CMD=''
IMMADM_CMD=''
IMMCFG_CMD=''
IMMLIST_CMD=''
MKTEMP_CMD=''
PASSWD_CMD=''
PKILL_CMD=''
PS_CMD=''
RM_CMD=''
SED_CMD=''
SSH_CMD=''
TR_CMD=''
USERDEL_CMD=''
WHO_CMD=''
SECLA_PASSWD='/opt/eric/sec-la-cxp9026994/bin/sec-la-passwd'
SCRIPT_NAME=$(readlink -f $0)
LOCAL_USER_MGMT_CMD="$(dirname $SCRIPT_NAME)/apg_local_user_management"

# UserID and groups related information
UNIX_USERS_MIN_UID=500
UNIX_USERS_MAX_UID=699
MAX_ALLOWED_UNIX_USERS=$(($UNIX_USERS_MAX_UID - $UNIX_USERS_MIN_UID + 1))
# It should start from 700, but a position is reserved for laadmin
LOCAL_USERS_MIN_UID=701
LOCAL_USERS_MAX_UID=999
MAX_ALLOWED_LOCAL_USERS=$(($LOCAL_USERS_MAX_UID - $LOCAL_USERS_MIN_UID + 1))
PASSWD_FILE_PATH='/cluster/etc/passwd'
PASSWD_WORKING_COPY="${PASSWD_FILE_PATH}_working"
SHADOW_FILE_PATH='/cluster/etc/shadow'
LOCAL_USERS_PH0_GROUP_NAME='apg-local'
LOCAL_USERS_PH0_GROUP_NAME_ESCAPED='apg\-local'
COM_LDAP_GROUP_NAME_ESCAPED='com\-ldap'

# Common variables for sharing DNs of objects common to each user
ACCOUNT_POLICY_DN=''
ACCOUNT_POLICY_INDEX_MAX_INDEX=100
PASSWORD_POLICY_INDEX_MAX_INDEX=$ACCOUNT_POLICY_INDEX_MAX_INDEX
PASSWORD_POLICY_INDEX=0
PASSWORD_POLICY_NEVER_EXPIRING_DN=''
PASSWORD_POLICY_EXPIRING_DN=''
ADMINISTRATIVE_STATE_UNLOCKED=1
DUMMY_PASSWORD='DummyPassword@12345'
##### END  : Common variables section

# Function to print the script usage
# Usage: usage
function usage() {
  echo "Incorrect usage:"
  echo "apg_local_users_migration.sh --migrate | -m"
  echo "apg_local_users_migration.sh --pre-checks | -p"
  echo "apg_local_users_migration.sh --run-migration | -r"
  echo 
}

# Function to execute all the needed cleanup operation at script termination.
# Usage: cleanup
function cleanup() {
  # Remove the working copy of passwd file (if created)
  if [ -r $PASSWD_WORKING_COPY ]; then
    ${RM_CMD} -f $PASSWD_WORKING_COPY
  fi
}

# Function to execute some sanity checks before starting the execution
# Usage: sanity_check
function sanity_check() {
  # Sanity check on passwd file existence  
  if [ ! -r $PASSWD_FILE_PATH ]; then
    apos_abort "The file '$PASSWD_FILE_PATH' was not found or not readable!"
  fi
  
  # Sanity check on shadow file existence
  if [ ! -r $SHADOW_FILE_PATH ]; then
    apos_abort "The file '$SHADOW_FILE_PATH' was not found or not readable!"
  fi 

  # Sanity check on commands paths. 
  # In case the command is not found by which, use default path
  AWK_CMD=$(which awk 2>/dev/null)
  [ -z "$AWK_CMD" ] && AWK_CMD='/usr/bin/awk'
  
  CAT_CMD=$(which cat 2>/dev/null)
  [ -z "$CAT_CMD" ] && CAT_CMD='/bin/cat'
  
  CP_CMD=$(which cp 2>/dev/null)
  [ -z "$CP_CMD" ] && CP_CMD='/bin/cp'
  
  ECHO_CMD=$(which echo 2>/dev/null)
  [ -z "$ECHO_CMD" ] && ECHO_CMD='/bin/echo'

  GETOPT_CMD=$(which getopt 2>/dev/null)
  [ -z "$GETOPT_CMD" ] && GETOPT_CMD='/usr/bin/getopt'

  GREP_CMD=$(which grep 2>/dev/null)
  [ -z "$GREP_CMD" ] && GREP_CMD='/usr/bin/grep'

  HEAD_CMD=$(which head 2>/dev/null)
  [ -z "$HEAD_CMD" ] && HEAD_CMD='/usr/bin/head'
  
  ID_CMD=$(which id 2>/dev/null)
  [ -z "$ID_CMD" ] && ID_CMD='/usr/bin/id'

  IMMADM_CMD=$(which immadm 2>/dev/null)
  [ -z "$IMMADM_CMD" ] && IMMADM_CMD='/usr/bin/immadm'

  IMMCFG_CMD=$(which immcfg 2>/dev/null)
  [ -z "$IMMCFG_CMD" ] && IMMCFG_CMD='/usr/bin/immcfg'

  IMMLIST_CMD=$(which immlist 2>/dev/null)
  [ -z "$IMMLIST_CMD" ] && IMMLIST_CMD='/usr/bin/immlist'

  MKTEMP_CMD=$(which mktemp 2>/dev/null)
  [ -z "$MKTEMP_CMD" ] && MKTEMP_CMD='/bin/mktemp'

  PASSWD_CMD=$(which passwd 2>/dev/null)
  [ -z "$PASSWD_CMD" ] && PASSWD_CMD='/usr/bin/passwd'
  
  PKILL_CMD=$(which pkill 2>/dev/null)
  [ -z "$PKILL_CMD" ] && PKILL_CMD='/usr/bin/pkill'

  PS_CMD=$(which ps 2>/dev/null)
  [ -z "$PS_CMD" ] && PS_CMD='/usr/bin/ps'
  
  RM_CMD=$(which rm 2>/dev/null)
  [ -z "$RM_CMD" ] && RM_CMD='/usr/bin/rm'
  
  SED_CMD=$(which sed 2>/dev/null)
  [ -z "$SED_CMD" ] && SED_CMD='/usr/bin/sed'

  SSH_CMD=$(which ssh 2>/dev/null)
  [ -z "$SSH_CMD" ] && SSH_CMD='/usr/bin/ssh'

  TR_CMD=$(which tr 2>/dev/null)
  [ -z "$TR_CMD" ] && TR_CMD='/usr/bin/tr'

  USERDEL_CMD=$(which userdel 2>/dev/null)
  [ -z "$USERDEL_CMD" ] && USERDEL_CMD='/usr/sbin/userdel'

  WHO_CMD=$(which who 2>/dev/null)
  [ -z "$WHO_CMD" ] && WHO_CMD='/usr/bin/who'
}

# Function to parse the provided command line.
# Usage: parse_cmdline $@
function parse_cmdline() {
  local SHORT_OPTIONS='m p r'
  local LONG_OPTIONS='migrate pre-checks run-migration'
  
  # Check that only a single option has been provided
  if [ $# -ne 1 ]; then 
    usage
    apos_abort "A single option must be provided on command line."
  fi

  ${GETOPT_CMD} --quiet --quiet-output --longoptions=$LONG_OPTIONS $SHORT_OPTIONS -- $@
  if [ $? -ne 0 ]; then
    usage
    apos_abort "Failed to parse the command line!"
  fi
  
  while [ $# -gt 0 ]; do
    case $1 in
	--migrate|-m)
	  OPTION_MIGRATE=$TRUE
	  break
	;;

	--pre-checks|-p)	
      OPTION_PRECHECKS=$TRUE
      break
	;;
	
	--run-migration|-r)
	  OPTION_RUN_MIGRATION=$TRUE
	  break
	;;
	
	*)
      usage
	  apos_abort "Undefined option found on command line ($1)"
	;;
	esac
	shift
  done
}

# Function to execute some preliminary checks before starting the update phase.
# The following items will be checked:
#   1) The number of local users must be less than MAX_ALLOWED_LOCAL_USERS.
#   2) The number of existing UNIX users (TS users, tsadmin, apgsys) whose UID 
#      is in the range [LOCAL_USERS_MIN_UID-1, LOCAL_USERS_MAX_UID] must be 
#      less than the number of configured local user plus 1 (administrator 
#      account).
#   3) Two or more users whose usernames differ only for uppercase/lowercase
#      characters must be not present.
#   4) No user whose username contains uppercase characters must exist.
# In case the conditions are not fullfilled, the upgrade must fail.
# Usage: execute_pre_checks
function execute_pre_checks() {
  local LOCAL_USERS_PH0_COUNT=0
  declare -a LOCAL_USERS_PH0
  local UNIX_USERS_COUNT=0
  declare -a UNIX_USERS
  local UNIX_USERS_OUT_OF_RANGE_COUNT=0
  declare -a UNIX_USERS_OUT_OF_RANGE

  # First, extract the users currently defined on the system (UNIX/local users)
  while read USER_LINE
  do
    local USER=$(${ECHO_CMD} $USER_LINE | ${AWK_CMD} -F':' '{print $1}')
    local USER_ID=$(${ECHO_CMD} $USER_LINE | ${AWK_CMD} -F':' '{print $3}')
	local USER_GROUPS=$(${ID_CMD} $USER)
	
	if [[ "$USER_GROUPS" =~ "$LOCAL_USERS_PH0_GROUP_NAME" ]]; then
	  LOCAL_USERS_PH0[$LOCAL_USERS_PH0_COUNT]=$USER
	  LOCAL_USERS_PH0_COUNT=$(($LOCAL_USERS_PH0_COUNT + 1))
	else
	  UNIX_USERS[$UNIX_USERS_COUNT]=$USER
	  UNIX_USERS_COUNT=$(($UNIX_USERS_COUNT + 1))
	  
	  # If the UNIX user is out of the allowed ranges (in SLES12), store it
	  # into a different vector to be used later for consistency checks.
	  if [ $USER_ID -gt $UNIX_USERS_MAX_UID ]; then
	    UNIX_USERS_OUT_OF_RANGE[$UNIX_USERS_OUT_OF_RANGE_COUNT]=$USER
	    UNIX_USERS_OUT_OF_RANGE_COUNT=$(($UNIX_USERS_OUT_OF_RANGE_COUNT + 1))
	  fi
    fi
  done < $PASSWD_FILE_PATH
  apos_log "There are $LOCAL_USERS_PH0_COUNT local users and $UNIX_USERS_COUNT UNIX users defined on the system."
  
  # Check the number of local users currently present on the system
  if [ $LOCAL_USERS_PH0_COUNT -gt $MAX_ALLOWED_LOCAL_USERS ]; then
    apos_log "Defined local users: '${LOCAL_USERS_PH0[*]}'"
    apos_abort "Maximum value of local user is '$MAX_ALLOWED_LOCAL_USERS', found value is '$LOCAL_USERS_PH0_COUNT'!"
  fi

  # Check the number of UNIX users currently present on the system
  if [ $UNIX_USERS_COUNT -gt $MAX_ALLOWED_UNIX_USERS ]; then
    apos_log "Defined UNIX users: '${UNIX_USERS[*]}'"
    apos_log "WARNING: Maximum value of UNIX users is '$MAX_ALLOWED_UNIX_USERS', found value is '$UNIX_USERS_COUNT'!"
  fi

  # Check that the number of UNIX users whose UID falls into local users' UID 
  # range is smaller than the total number of local users plus 1 (laadmin).
  if [ $(($MAX_ALLOWED_LOCAL_USERS - $UNIX_USERS_OUT_OF_RANGE_COUNT - $LOCAL_USERS_PH0_COUNT)) -lt 0 ]; then
    apos_log "The following users are out of range: '${UNIX_USERS_OUT_OF_RANGE[*]}'"
	apos_abort "There are too many UNIX users in [$(($LOCAL_USERS_MIN_UID - 1)), $LOCAL_USERS_MAX_UID] range ($UNIX_USERS_OUT_OF_RANGE_COUNT)"
  fi  
  
  # Check that no couple of users exists whose usernames differ only for a 
  # uppercase/lowercase character.
  local NUM_OF_USERS_CASE_INSENSITIVE=-1
  NUM_OF_USERS_CASE_INSENSITIVE=$(${ECHO_CMD} ${LOCAL_USERS_PH0[@]} | tr [:lower:] [:upper:] | tr ' ' '\n' | uniq | wc -l)
  if [ $NUM_OF_USERS_CASE_INSENSITIVE -ne $LOCAL_USERS_PH0_COUNT ]; then
    apos_log "Defined local users: '${LOCAL_USERS_PH0[*]}'"
	apos_abort "There is at least one user whose username differs from another one only for a uppercase/lowercase character."
  fi
}

# Function to execute the migration operation on the node actually already 
# updated to SLES12 software level.
# After understanding the OS revision, this function calls, via ssh command,
# the script itself with a different option.
function execute_migration_on_updated_node() {
  local OS_VERSION=$(${CAT_CMD} /etc/*release| ${GREP_CMD} -P '^VERSION[[:space:]]*='| ${HEAD_CMD} -n 1| ${AWK_CMD} -F'=' '{print $2}'| ${TR_CMD} -d [[:space:]])
  if [ -z "$OS_VERSION" ]; then
    apos_abort "Failed to retrieve the OS version."
  fi
  
  # Retrive the hostname according to the OS version previously retrieved
  local HOST_NAME=''
  if [ "$OS_VERSION" == "11" ]; then
    # The peer node is running with SLES12 software
	HOST_NAME=$(${CAT_CMD} /etc/cluster/nodes/peer/hostname)
  elif [ "$OS_VERSION" == "12" ]; then
    # The current node is running with SLES12 software
	HOST_NAME=$(${CAT_CMD} /etc/cluster/nodes/this/hostname)
  else
    apos_abort "Invalid OS version ($OS_VERSION) retrieved."
  fi

  # Sanity check on retrieved value
  if [ -z "$HOST_NAME" ]; then
    apos_abort "Empty value retrieved for hostname."
  fi
  
  # Execute the current script with the --run-migration option  
  ${SSH_CMD} $HOST_NAME $SCRIPT_NAME --run-migration
  if [ $? -ne 0 ]; then
    apos_abort "Failed to launch '$SCRIPT_NAME' (with --run-migration option) on $HOST_NAME."
  fi
}

# Function to create the (unique) instance of the AccountPolicy MO.
# The MO will be created using the default value for the dormantTimer attribute.
# After the MO has been created, the ACCOUNT_POLICY_DN variable will be filled
# with the DN of the created MO.
# Usage: create_account_policy
function create_account_policy() {
  local ACCOUNT_POLICY_CLASS_NAME='SecLAAccountPolicy'
  local ACCOUNT_POLICY_ID=1
  local ACCOUNT_POLICY_EXPECTED_DN=''
  
  # The instance of the AccountPolicy MO must be created only if not yet done
  if [ -z "$ACCOUNT_POLICY_DN" ]; then
    # Find the first free ID for AccountPolicy MO
	apos_log "The account policy was not yet created, looking for its DN..."
    while [ $ACCOUNT_POLICY_ID -le $ACCOUNT_POLICY_INDEX_MAX_INDEX ]
    do
	  # Check if a policy with that DN is already present or not
	  ACCOUNT_POLICY_EXPECTED_DN="accountPolicyId=$ACCOUNT_POLICY_ID,SecLAlocalAuthenticationMethodId=1"
	  ${IMMLIST_CMD} $ACCOUNT_POLICY_EXPECTED_DN &> /dev/null
	  if [ $? -ne 0 ]; then
	    apos_log "The account policy will be created with DN $ACCOUNT_POLICY_EXPECTED_DN"
	    break
	  fi

	  ACCOUNT_POLICY_ID=$(($ACCOUNT_POLICY_ID + 1))
	  ACCOUNT_POLICY_EXPECTED_DN=""
    done
  
    # Check if a valid DN value has been found or not
	if [ -z "$ACCOUNT_POLICY_EXPECTED_DN" ]; then
	  apos_abort "No value found for AccountPolicy DN."
	fi
  	
	# Create the AccountPolicy MO with the retrieved DN
    ${IMMCFG_CMD} -c $ACCOUNT_POLICY_CLASS_NAME $ACCOUNT_POLICY_EXPECTED_DN
	if [ $? -ne 0 ]; then
	  apos_abort "Failed to create an instance of $ACCOUNT_POLICY_CLASS_NAME class with DN $ACCOUNT_POLICY_EXPECTED_DN"
	fi
	ACCOUNT_POLICY_DN=$ACCOUNT_POLICY_EXPECTED_DN
  fi
}

# Function to create a generic instance of PasswordPolicy.
# It is an implementation function and should not be called directly.
# It must be used as follow:
#   create_password_policy_i $TRUE: to create a never expiring policy.
#   create_password_policy_i $FALSE: to create an expiring policy.
# Usage: create_password_policy_i <is_never_expiring_policy>
function create_password_policy_i() {
  # Check the number of input parameters
  if [ $# -ne 1 ]; then
    apos_abort "Bad usage: please provide exactly two arguments to this function!"
  fi
  
  # Extract all the needed info from the TS users policy fragment
  local TS_USERS_POLICY_DN='AxeLocalTsUsersPolicylocalTsUsersPolicyMId=1'
  local HISTORY_LENGTH=$(${IMMLIST_CMD} $TS_USERS_POLICY_DN | ${GREP_CMD} passwordHistorySize | ${AWK_CMD} '{print $3}') 
  local LOCKOUT_DURATION=$(${IMMLIST_CMD} $TS_USERS_POLICY_DN | ${GREP_CMD} lockoutDuration | ${AWK_CMD} '{print $3}') 
  local MIN_PASSWORD_LENGTH=$(${IMMLIST_CMD} $TS_USERS_POLICY_DN | ${GREP_CMD} minimumPasswordLength | ${AWK_CMD} '{print $3}') 
  if [ -z "$HISTORY_LENGTH" ] || [ -z "$LOCKOUT_DURATION" ] || [ -z "$MIN_PASSWORD_LENGTH" ]; then
    apos_abort "Invalid values read for attributes into '$TS_USERS_POLICY_DN' object."
  fi
  
  # Create the PasswordPolicy object with the retrieved information.
  # For this purpose, use a C program, since immcfg doesn't support the 
  # setting of multi-value attribues and since SEC-LA OI rejects the adding
  # of a new value for a multi-value attribute.
  # This execution will also set the cross-reference between PasswordPolicy MO
  # and the used PasswordQuality MO.
  PASSWORD_POLICY_INDEX=$(($PASSWORD_POLICY_INDEX + 1))
  local PASSWORD_POLICY_DN='' 
  
  # Find the first free ID for PasswordPolicy MO
  apos_log "The Looking for the right PasswordPolicy DN..."
  while [ $PASSWORD_POLICY_INDEX -le $PASSWORD_POLICY_INDEX_MAX_INDEX ]
  do
    # Check if a policy with that DN is already present or not
	PASSWORD_POLICY_DN="passwordPolicyId=$PASSWORD_POLICY_INDEX,SecLAlocalAuthenticationMethodId=1"
	${IMMLIST_CMD} $PASSWORD_POLICY_DN &> /dev/null
	if [ $? -ne 0 ]; then
	  apos_log "The password policy will be created with DN $PASSWORD_POLICY_DN"
	  break
	fi

	PASSWORD_POLICY_INDEX=$(($PASSWORD_POLICY_INDEX + 1))
	PASSWORD_POLICY_DN=""
  done
  
  # Check if a valid DN value has been found or not
  if [ -z "$PASSWORD_POLICY_DN" ]; then
    apos_abort "No value found for PasswordPolicy DN."
  fi
    
  local PASSWORD_QUALITY_DEFAULT_DN='passwordQualityId=1,SecLAlocalAuthenticationMethodId=1'
  ${LOCAL_USER_MGMT_CMD} --id=$PASSWORD_POLICY_INDEX --history-len=$HISTORY_LENGTH --min-len=$MIN_PASSWORD_LENGTH --lock-duration=$(($LOCKOUT_DURATION * 60)) --quality=$PASSWORD_QUALITY_DEFAULT_DN
  if [ $? -ne 0 ]; then
    apos_abort "Failed to create an instance of PasswordPolicy class with DN $PASSWORD_POLICY_DN."
  fi
	
  # Setup the attribues about the password age according to the input argument
  local IS_NEVER_EXPIRING_POLICY=$1  
  ATTRIBUTES=" -a minAge= "
  if [ $IS_NEVER_EXPIRING_POLICY -eq $TRUE ]; then
    ATTRIBUTES+=" -a maxAge= "
  fi

  # Modify the attribute values
  # This setting must be done after the object has been correctly created.
  ${IMMCFG_CMD} $ATTRIBUTES $PASSWORD_POLICY_DN
  if [ $? -ne 0 ]; then
    apos_abort "Failed to modify values for the MO with DN '$PASSWORD_POLICY_DN'"
  fi

  # Fill with DN the correct variable, according to the input argument
  if [ $IS_NEVER_EXPIRING_POLICY -eq $TRUE ]; then
    PASSWORD_POLICY_NEVER_EXPIRING_DN=$PASSWORD_POLICY_DN
  else
    PASSWORD_POLICY_EXPIRING_DN=$PASSWORD_POLICY_DN
  fi
}

# Function to create an instance of PasswordPolicy MO to be associated to the
# never expiring users.
# The object attributes will be set as follow:
#   historyLength   = passwordHistorySize (in TS users fragment)
#   lockoutDuration = lockoutDuration (in TS users fragment)
#   maxAge          = no value
#   minAge          = no value
#   minLength       = minimumPasswordLength (in TS users fragment)
# After the MO has been created, the PASSWORD_POLICY_NEVER_EXPIRING_DN variable 
# will be filled with the DN of the created MO.
# Usage: create_password_policy_never_expiring
function create_password_policy_never_expiring() {
  # The instance of the PasswordPolicy MO must be created only if not yet done
  if [ -z "$PASSWORD_POLICY_NEVER_EXPIRING_DN" ]; then
    apos_log "The never expiring password policy was not yet created, creating it..."
    create_password_policy_i $TRUE
	
	# Consistency check on the returned value
	if [ -z "$PASSWORD_POLICY_NEVER_EXPIRING_DN" ]; then
	  apos_abort "Empty value provided for the PasswordPolicy DN."
	fi
  fi
}

# Function to create an instance of PasswordPolicy MO to be associated to the
# local users whose password will expire after some time.
# The object attributes will be set as follow:
#   historyLength   = passwordHistorySize (in TS users fragment)
#   lockoutDuration = lockoutDuration (in TS users fragment)
#   maxAge          = default value (90)
#   minAge          = no value
#   minLength       = minimumPasswordLength (in TS users fragment)
# After the MO has been created, the PASSWORD_POLICY_EXPIRING_DN variable 
# will be filled with the DN of the created MO.
# Usage: create_password_policy_expiring
function create_password_policy_expiring() {
  # The instance of the PasswordPolicy MO must be created only if not yet done
  if [ -z "$PASSWORD_POLICY_EXPIRING_DN" ]; then
    apos_log "The expiring password policy was not yet created, creating it..."
	create_password_policy_i $FALSE

	# Consistency check on the returned value
	if [ -z "$PASSWORD_POLICY_EXPIRING_DN" ]; then
	  apos_abort "Empty value provided for the PasswordPolicy DN."
	fi
  fi
}

# Function to remove all the opened sessions for the given username.
# Usage: kill_opened_sessions <user> <kill_on_peer_node>
function kill_opened_sessions() {
  # Check the number of input parameters
  if [ $# -ne 2 ]; then
    apos_abort "Bad usage: please provide exactly two arguments to this function!"
  fi
  
  local USERNAME=$1
  local SSH_CMD_WITH_HOSTNAME=''
  
  # Check if the function must act on the peer node
  if [ $2 -eq $TRUE ]; then
    # Retrieve the remote node hostname
	local HOST_NAME=$(${CAT_CMD} /etc/cluster/nodes/peer/hostname)
    if [ -z "$HOST_NAME" ]; then
      apos_abort "Failed to retrieve the peer node hostname."
    fi
    
	# Build the command with ssh execution
	SSH_CMD_WITH_HOSTNAME="${SSH_CMD} $HOST_NAME"
  fi

  # Kill all the processes associated to the user
  apos_log "Removing the opened sessions for user $USERNAME"
  ${SSH_CMD_WITH_HOSTNAME} ${PKILL_CMD} -9 -u $USERNAME 2> /dev/null

  # Kill all the other processes opened by the user.
  # This will be achieved by simply retrieving the list of PTS associated
  # to the user and killing them.
  for PTS in $(${SSH_CMD_WITH_HOSTNAME} ${WHO_CMD} | ${GREP_CMD} $USERNAME | ${AWK_CMD} '{print $2}')
  do
    ${SSH_CMD_WITH_HOSTNAME} ${PKILL_CMD} -9 -t $PTS 2> /dev/null
  done
}

# Function to execute the whole local user migration from local authentication
# phase 0 solution to the new CBA-based solution.
# Usage: execute_migration
function execute_migration() {
  # Create the working copy of passwd file
  ${CP_CMD} $PASSWD_FILE_PATH $PASSWD_WORKING_COPY
  if [ $? -ne 0 ]; then
    apos_abort "Failed to create a backup copy of passwd file."
  fi
  
  while read USER_LINE
  do
  {
    # For each user present into passwd file, extract its name and groups,
	# in order to understand if it is a local user or not.
    local USER_NAME=$(${ECHO_CMD} $USER_LINE | ${AWK_CMD} -F':' '{print $1}')
	local USER_GROUPS=$(${ID_CMD} -nG $USER_NAME)
	if [[ "$USER_GROUPS" =~ "$LOCAL_USERS_PH0_GROUP_NAME" ]]; then
	  apos_log "The user $USER_NAME must be migrated!"
	
	  # The user is a local user, extract the ECIM roles from the user's groups.
	  # To make that, strip the not needed groups
	  local ECIM_USER_ROLES=$(${ECHO_CMD} $USER_GROUPS | ${SED_CMD} -r "s/(($LOCAL_USERS_PH0_GROUP_NAME_ESCAPED)|($COM_LDAP_GROUP_NAME_ESCAPED))//g")
	  # Build the user roles string as a comma-separated list of values
	  local USER_ROLES=$(${ECHO_CMD} ${ECIM_USER_ROLES[@]} | ${TR_CMD} ' ' ',')

	  # Extract the information about the user's password and its expiring date
	  local SHADOW_LINE=$(${GREP_CMD} $USER_NAME $SHADOW_FILE_PATH)
	  local USER_PASSWORD=$(${ECHO_CMD} $SHADOW_LINE | ${AWK_CMD} -F':' '{print $2}')
	  local USER_PASSWORD_EXPIRATION=$(${ECHO_CMD} $SHADOW_LINE | ${AWK_CMD} -F':' '{print $5}')

	  # In order to avoid connections with the user to 
	  # be migrated, invalidate its password.
	  apos_log "Invalidating the password for the user $USER_NAME."
	  ${PASSWD_CMD} -d $USER_NAME
	  if [ $? -ne 0 ]; then
	    apos_log "WARNING: Failed to invalidate the password for user $USER_NAME!!!"
	  fi

	  # Kill the user's active sessions on both local and peer node
	  apos_log "Checking if the user $USER_NAME has active sessions on local node."
	  kill_opened_sessions $USER_NAME $FALSE

	  apos_log "Checking if the user $USER_NAME has active sessions on remote node."
	  kill_opened_sessions $USER_NAME $TRUE
	  
	  # Create the account policy if not yet done
	  create_account_policy
	  local ACCOUNT_POLICY_ATTR_VALUE=$ACCOUNT_POLICY_DN
	  
	  # Create the password policy (if not yet done) according 
	  # to the user's password expiration
	  local PASSWORD_POLICY_ATTR_VALUE=''
	  if [ -z "$USER_PASSWORD_EXPIRATION" ]; then
	    create_password_policy_never_expiring
		PASSWORD_POLICY_ATTR_VALUE=$PASSWORD_POLICY_NEVER_EXPIRING_DN
	  else
	    create_password_policy_expiring
		PASSWORD_POLICY_ATTR_VALUE=$PASSWORD_POLICY_EXPIRING_DN
	  fi
	  
	  # Delete the local user to be migrated before defining it
	  apos_log "Deleting the user $USER_NAME."
	  ${USERDEL_CMD} $USER_NAME
	  if [ $? -ne 0 ]; then
	    apos_abort "Failed to delete the user '$USER_NAME'."
	  fi
	  
	  # Create the local user into SEC LA model
	  # For this purpose, use a C program, since immcfg doesn't support the 
	  # setting of multi-value attribues and since SEC-LA OI rejects the adding
	  # of a new value for a multi-value attribute.
	  # This execution will also set the cross-references between UserAccount MO
	  # and the used AccountPolicy and PasswordPolicy MOs.
	  apos_log "Creating the user $USER_NAME with roles $USER_ROLES"
	  ${LOCAL_USER_MGMT_CMD} --user $USER_NAME --pwd-policy $PASSWORD_POLICY_ATTR_VALUE --acc-policy $ACCOUNT_POLICY_ATTR_VALUE --state $ADMINISTRATIVE_STATE_UNLOCKED --roles=$USER_ROLES
	  if [ $? -ne 0 ]; then
	    apos_abort "Failed to create the user '$USER_NAME'."
	  fi
	  
	  # Execute the resetPassword administrative operation to unlock the user.
	  # Use the noChange option in order to avoid the password change request
	  # at user login. Use a dummy password, since the real user password will
	  # be migrated later.
	  apos_log "Resetting password for user $USER_NAME."
	  ${IMMADM_CMD} -o 0 -p password:SA_STRING_T:$DUMMY_PASSWORD -p noChange:SA_INT32_T:1 "userAccountId=$USER_NAME,userAccountMId=1,SecLAlocalAuthenticationMethodId=1"
	  if [ $? -ne 0 ]; then
	    apos_abort "Failed to execute the resetPassword action for '$USER_NAME'."
	  fi

	  # The last step needed for the user migration is the injection 
	  # of the password. This will be achieved using a dedicated SEC LA script
	  # providing it the password in hash format.
	  apos_log "Injecting password for user $USER_NAME."
	  ${SECLA_PASSWD} $USER_NAME -h $USER_PASSWORD &> /dev/null
	  if [ $? -ne 0 ]; then
	    apos_abort "Failed to set the hashed password for '$USER_NAME'."
	  fi
	fi
  } < /dev/null; 
  done < $PASSWD_WORKING_COPY
}

#                                              __    __   _______   _   __    _
#                                             |  \  /  | |  ___  | | | |  \  | |
#                                             |   \/   | | |___| | | | |   \ | |
#                                             | |\  /| | |  ___  | | | | |\ \| |
#                                             | | \/ | | | |   | | | | | | \   |
#                                             |_|    |_| |_|   |_| |_| |_|  \__|
#
apos_intro $0

# Prints error in case of unset variables
set -u

# Register a handler to execute any type of cleanup operations when the script exits
trap cleanup EXIT

# Sanity check before starting
sanity_check

# Parse the command line arguments to understand the operation to be executed
parse_cmdline $@

# If needed, execute the pre-checks phase
if [ $OPTION_PRECHECKS -eq $TRUE ]; then
  execute_pre_checks
fi

# If needed, execute the preliminary checks to understand 
# the node on which execute the migration.
if [ $OPTION_MIGRATE -eq $TRUE ]; then
  execute_migration_on_updated_node  
fi

# If needed, execute the local users migration from phase 0
if [ $OPTION_RUN_MIGRATION -eq $TRUE ]; then
  execute_migration
fi

apos_outro $0
exit $TRUE

# End of file
