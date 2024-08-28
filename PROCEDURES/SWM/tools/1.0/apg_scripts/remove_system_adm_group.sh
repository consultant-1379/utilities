#!/bin/bash

#Description: Remove system-adm group from tsuser

#setting  global variables
##############################
TS_GROUP="tsgroup"
CLU_PASSWD_FILE="/cluster/etc/passwd"
SYSTEM_ADM_GROUP="system-adm"
CLU_GROUP_FILE="/cluster/etc/group"
LOCAL_GROUP_FILE="/etc/group"
CAMP_PATH="$(dirname "$(readlink -f $0)")"
TMP_FILE="$CAMP_PATH/temp"


# The function will log and print an error message and will terminate the script
#  with a $FALSE return code.
function abort(){
        local MESSAGE=$1
        log_msg "ERROR: $MESSAGE"
        exit $FALSE
}

# The function will log an  message in the system log.
function log_msg(){

        local PRIO='-p user.notice'
        local MESSAGE="${*:-notice}"

        $CMD_LOGGER $PRIO $LOG_TAG $MESSAGE &>/dev/null
}


# The function will check for the script's prerequisites to be satisfied.
function sanity_check(){

        CMD_LOGGER=$( which logger 2>/dev/null )
        [ -z "$CMD_LOGGER" ] && CMD_LOGGER='/bin/logger'

        USERMOD=$( which usermod 2>/dev/null )
        [  -z "$USERMOD" ] && USERMOD='/usr/sbin/usermod'

        AWK=$( which awk 2>/dev/null )
        [  -z "$AWK" ] && AWK='/usr/bin/awk'

        CMD_RM=$( which rm 2>/dev/null )
        [  -z "$CMD_RM" ] && CMD_RM='/bin/rm'

        CMD_GROUPS=$( which groups 2>/dev/null )
        [  -z "$CMD_GROUPS" ] && CMD_GROUPS='/usr/bin/groups'

        CMD_GETENT=$( which getent 2>/dev/null )
        [  -z "$CMD_GETENT" ] && CMD_GETENT='/usr/bin/getent'

        CMD_SED=$( which sed 2>/dev/null )
        [  -z "$CMD_SED" ] && CMD_SED='/usr/bin/sed'

        GREP=$( which grep 2>/dev/null )
        [  -z "$GREP" ] && GREP='/usr/bin/grep'

        CMD_NSCD=$( which nscd 2>/dev/null )
        [  -z "$CMD_NSCD" ] && CMD_NSCD='/usr/sbin/nscd'

}

# The function will get the defined ts users on the node.
function  get_tsusers() {
        tsgroup_id=`${GREP} "^$TS_GROUP:" $CLU_GROUP_FILE | ${AWK} -F: '{print $3}'`

        for tsuser in `${AWK} -F: '{if($4 == '$tsgroup_id') print $1}' $CLU_PASSWD_FILE`
        do
                echo -e "$tsuser"
        done
}

function remove_sysadm_group(){
        log_msg "function remove_sysadm_group start..."

        local tsuser_list=($(get_tsusers))
        for tsuser in "${tsuser_list[@]}" ;do
                ${CMD_GROUPS} $tsuser|${GREP} $SYSTEM_ADM_GROUP 1>/dev/null
                        if [ $? -eq 0 ]; then
                                #Remove the system-adm group to user
                                ${USERMOD} -P /cluster/etc -R $SYSTEM_ADM_GROUP $tsuser 1>/dev/null
                                if [ $? != 0 ]; then
                                        abort "Error removing the user $tsuser from the group $SYSTEM_ADM_GROUP"
                                else
                                        log_msg "User $tsuser removed from the group $SYSTEM_ADM_GROUP"
                                fi
                        else
                                log_msg "User $tsuser not belongs to group $SYSTEM_ADM_GROUP"
                        fi
        done

        log_msg "function remove_sysadm_group end!!!"
}

# Remove the system-adm entry from the /cluster/etc/group file
function localize_group(){
        log_msg "function localize_group start..."

        local GROUP=""
        # The fetch group from databases supported by the Name Service Switch
        GROUP="$($CMD_GETENT group $SYSTEM_ADM_GROUP | ${AWK} -F: '{print $1":"$2":"$3":"}')"
        if [ -z "$GROUP" ]; then
                abort "Group $SYSTEM_ADM_GROUP does not exist"
        fi

        # Remove group from /cluster/etc/group
        $CMD_SED -i -e "/^$GROUP/ d" $CLU_GROUP_FILE
        if [ $? != 0 ]; then
                abort "Cannot delete $SYSTEM_ADM_GROUP group $CLU_GROUP_FILE"
        fi

        # Save the entry in a temp file (it will be used to perform the upgrade also on the peer node)
        echo $GROUP > $TMP_FILE

        log_msg "function localize_group end!!!"
}

# Add the system-adm entry to /etc/group file
function recreate_local_group(){

        log_msg "function recreate_local_group start..."
        local GROUP=""

        if [ -f $TMP_FILE ]; then
                GROUP=$(cat $TMP_FILE)
                if [ -z "$GROUP" ]; then
                        abort "Error fetching the entry to insert in $LOCAL_GROUP_FILE"
                fi
                echo "$GROUP" >> $LOCAL_GROUP_FILE
        else
                abort "file $TMP_FILE file missing!!!"
        fi

        log_msg "function recreate_local_group end!!!"
}

# MAIN ------------------------------------------------------------------- BEGIN

sanity_check
log_msg "remove_system_adm_group.sh start..."

if [ -f $TMP_FILE ]; then
        log_msg "Add the $SYSTEM_ADM_GROUP to $LOCAL_GROUP_FILE"
        recreate_local_group

        log_msg "Update cache"
        $CMD_NSCD -i group

        log_msg "Remove the $TMP_FILE file"
        $CMD_RM $TMP_FILE

else
        log_msg "Removing the $SYSTEM_ADM_GROUP group to tsusers"
        remove_sysadm_group

        log_msg "Remove the $SYSTEM_ADM_GROUP from $CLU_GROUP_FILE"
        localize_group

        log_msg "Add the $SYSTEM_ADM_GROUP to $LOCAL_GROUP_FILE"
        recreate_local_group

        log_msg "Update cache"
        $CMD_NSCD -i group
fi

log_msg "remove_system_adm_group.sh end!!!"

# MAIN --------------------------------------------------------------------- END
exit $TRUE
