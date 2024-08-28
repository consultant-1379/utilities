#!/bin/bash
##
# ------------------------------------------------------------------------
#     Copyright (C) 2017 Ericsson AB. All rights reserved.
# ------------------------------------------------------------------------
##
# Name:
#       migrate_home_dir.sh
# Description:
#       A script to migrate home directory of ts_users and tsadmin from
#       /home to /var/home/
##
# Changelog:
# - Thu Feb 09 2017 - Yeswanth Vankayala (xyesvan)
#       First version.
##

# Load the apos common functions.
. /opt/ap/apos/conf/apos_common.sh

PARENT_HOME_DIR="/var/home"
TSUSER_HOME_DIR="$PARENT_HOME_DIR/ts_users"
TSADMIN_HOME_DIR="$PARENT_HOME_DIR/tsadmin"
COMMON_HOME_TSUSERS='/home/ts_users'
PASSWD_FILE='/etc/passwd'

# create_folder <folder> <permissions>
function create_folder() {
  local folder_to_create=$1
  local folder_permissions=$2

  if [ ! -d $folder_to_create ]; then
    mkdir -p $folder_to_create || \
    apos_abort "ERROR: Failed to create folder '$folder_to_create'!"
  fi
  
  chmod $folder_permissions $folder_to_create 
  if [ $? -ne $TRUE ]; then
    apos_abort "ERROR: Failed to set the permissions '$folder_permissions' on folder '$folder_to_create'"
    return $FALSE
  fi
  
  return $TRUE
}

function create_home_dir() {
  local home_dir=$1
  local group_name=$2
  local PERMISSIONS_TO_APPLY=755

  # Creation of /var/home directory
  if [ ! -d $PARENT_HOME_DIR ]; then
    create_folder $PARENT_HOME_DIR $PERMISSIONS_TO_APPLY || \
     apos_abort "ERROR: Failed to create $PARENT_HOME_DIR directory"
  fi
  
  [ $group_name == tsgroup ] && PERMISSIONS_TO_APPLY=770
  
  # Create local home directory for all ts users and tsadmin user
  create_folder $home_dir $PERMISSIONS_TO_APPLY
  if [ $? -eq $TRUE ];then
    apos_log "INFO: Created common home directory [$home_dir] for tsusres"
    # change the group owner to tsgroup
    chgrp $group_name $home_dir
    if [ $? -ne $TRUE ];then
      apos_abort "ERROR: Failed to change group ownership [$group_name] of [$home_dir]"
    else
      apos_log "INFO: Successfully changed group ownership [$group_name] of [$home_dir]"
    fi
    configure_home_dir $home_dir $group_name
  fi

  return $TRUE
}

# To configure the common home directory for ts_users
function configure_home_dir() {
  local home_dir=$1
  local group_name=$2
  # copy the file & folders from /etc/skel/ to [$common_local_dir]
  cp -Ruf /etc/skel/. $home_dir
  if [ $? -ne $TRUE ];then
    apos_log "INFO: Failed to copy contents from /etc/skel to [$home_dir]"
  else
     # permit execute-access to common-home
    if [ $group_name == tsgroup ]; then
      chmod -R 770 $home_dir/
      if [ $? -ne 0 ];then
        apos_log "INFO: Failed to permit 770 access to files under the [$home_dir]"
      fi
    fi
    # change the group owner to tsgroup and owner as tsadmin
    chown -R tsadmin:$group_name $home_dir/
    if [ $? -ne $TRUE ];then
      apos_log "INFO: Failed to change the group owner and owner for files under [$home_dir] "
    fi

    # change the group owner to tsgroup and owner as root for /ts_user folder
    if [ $group_name == tsgroup ]; then
      chown root:$group_name $home_dir
    fi
  fi

  if [ $group_name == tsgroup ]; then
    if [ ! -d $home_dir/.ssh ];then
      create_folder $home_dir/.ssh 770
      if [ $? -ne $TRUE ];then
        apos_abort "ERROR: Failed to create directory .ssh under the [$home_dir]"
      else
        assign_acls $home_dir/.ssh "tsadmin" "$group_name"
        [ $? -ne $TRUE ] && apos_abort "ERROR: Failed to assign ACL's to ssh folder"
        [ ! -f $home_dir/.ssh/known_hosts ] && touch $home_dir/.ssh/known_hosts
        assign_acls $home_dir/.ssh/known_hosts "tsadmin" "$group_name" "660"
        [ $? -ne $TRUE ] && apos_abort "ERROR: Failed to assign ACL's to known_hosts file"
      fi
    else
      [ ! -f $home_dir/.ssh/known_hosts ] && touch $home_dir/.ssh/known_hosts
      assign_acls $home_dir/.ssh/known_hosts "tsadmin" "$group_name" "660"
      [ $? -ne $TRUE ] && apos_abort "ERROR: Failed to assign ACL's to known_hosts file"
    fi
  fi
  return $TRUE
}

function assign_acls(){
  src_file_name=$1
  src_owner=$2
  src_group=$3
  src_base_perm=$4

  #checking if the owner exists
  if [ ! -z $src_owner ];then
    chown $src_owner $src_file_name
    if [ $? -eq $TRUE ];then
      apos_log "INFO: [$src_file_name]: Set owner to [$src_owner]"
    else
      apos_log "ERROR: Failed to set owner for file:[$src_file_name]"
      return $FALSE
    fi

  fi

  #checking if the group exists
  if [ ! -z $src_group ];then
    chgrp $src_group $src_file_name
    if [ $? -eq $TRUE ];then
      apos_log "INFO: [$src_file_name]: Set group owner to [$src_group]"
    else
      apos_log "ERROR: Failed to set group owner for file [$src_file_name]"
      return $FALSE
    fi
  fi

  #setting the owner and group of the file as per the input file data
  #setting basic permissions of the file
  #${SETFACL} -n -m u::"$src_owner_perm",g::"$src_group_perm",o::"$src_other_perm",m::rwx $src_file_name
  if [ ! -z $src_base_perm ];then
    chmod $src_base_perm $src_file_name
    if [ $? -eq $TRUE ];then
      apos_log "INFO: [$src_file_name]: Basic permission set to [$src_base_perm]"
    else
      apos_log "ERROR: Failed to set basic linux permissions for file [$src_file_name]"
      return $FALSE
    fi
  fi

  #setting stickybit, suid and sgid permissions if any
  chmod -t,u-s,g-s $src_file_name #clearing previous special permission if any
  if [ $? -ne $TRUE ]; then
    apos_log "ERROR: Failed in processing of sticky bit,suid and sgid permissions for $print_str [$src_file_name]"
    return $FALSE
  fi
  return $TRUE
}	

function update_passwd_files() {
 if grep -wq "$COMMON_HOME_TSUSERS" $PASSWD_FILE; then
    sed -i -r 's@:\/home\/ts_users@:/var/home/ts_users@g' $PASSWD_FILE
    [ $? -ne $TRUE ] && apos_abort "Failed to update home directory path for ts users"
 fi

 if grep -wq "/cluster/home/ts_users" $PASSWD_FILE; then
    sed -i -r 's@:\/cluster\/home\/ts_users@:/var/home/ts_users@g' $PASSWD_FILE
    [ $? -ne $TRUE ] && apos_abort "Failed to update home directory path for ts users"
 fi

 if grep -wq "/home/tsadmin" $PASSWD_FILE; then
    sed -i -e 's@:\/home\/tsadmin@:/var/home/tsadmin@g' $PASSWD_FILE
    [ $? -ne $TRUE ] && apos_abort "Failed to update home directory path for tsadmin"
 fi
}


#### M A I N ####

if [ ! -d $TSADMIN_HOME_DIR ]; then 
  create_home_dir $TSADMIN_HOME_DIR tsadmin
  [ $? -ne $TRUE ] && apos_abort "ERROR: Failed to create $TSADMIN_HOME_DIR"
fi

if [ ! -d $TSUSER_HOME_DIR ]; then 
  create_home_dir $TSUSER_HOME_DIR tsgroup
  [ $? -ne $TRUE ] && apos_abort "ERROR: Failed to create $TSUSER_HOME_DIR"
fi

# replace /home path with /var/home
update_passwd_files

exit $TRUE
# END

