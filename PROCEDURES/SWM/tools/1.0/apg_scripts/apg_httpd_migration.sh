#!/bin/bash -u
##
# ------------------------------------------------------------------------
#     Copyright (C) 2016 Ericsson AB. All rights reserved.
# ------------------------------------------------------------------------
##
# Name:
#       apg_httpd_migration.sh
# Description:
#       A script to migrate the httpd.conf file to new format according 
#       SLES12 needs.
# Note:
#       -
#
##
# Changelog:
# - Thue May 12 2016 - Fabio Ronca (efabron)
#       First version.
##
#
##


# Load the apos common functions.
. /opt/ap/apos/conf/apos_common.sh

apos_intro $0



HTTPD_CONF_FILE_PATH='/cluster/storage/system/config/apos/http_files/httpd.conf'
HTTP_CONFIGURATION_FILE_PATH=''
HTTP_CONFIGURATION_FILE='http_config_file'


function get_storage_config_paths() {
    local config_path=$(cat /usr/share/pso/storage-paths/config)
        
    [ -z "$config_path" ] && abort "unable to read pso storage path" 
    HTTP_CONFIGURATION_FILE_PATH="$config_path/apos"
}

#MAIN

get_storage_config_paths

if [ -f "$HTTP_CONFIGURATION_FILE_PATH/$HTTP_CONFIGURATION_FILE" ]; then
    apos_log "Migrate the $HTTPD_CONF_FILE_PATH to SLES12 format"

    if [ -e $HTTPD_CONF_FILE_PATH ]; then 
	    sed -i '/DefaultType text\/plain/d' $HTTPD_CONF_FILE_PATH 
		[ $? -ne 0 ] && apos_abort "ERROR: sed n. 1 failed!!!"
        sed -i '/AllowOverride None/a\    # See \/usr\/share\/doc\/packages\/apache2\/README-access_compat.txt\n    <IfModule mod_access_compat.c>' $HTTPD_CONF_FILE_PATH
		[ $? -ne 0 ] && apos_abort "ERROR: sed n. 2 failed!!!"
        sed -i 's/<\/Directory>/    <\/IfModule>\n    <IfModule !mod_access_compat.c>\n        Require all denied\n    <\/IfModule>\n&/' $HTTPD_CONF_FILE_PATH
        [ $? -ne 0 ] && apos_abort "ERROR: sed n. 3 failed!!!"
		sed -i '/<Files \~ "\^\\.ht">/a\    # See \/usr\/share\/doc\/packages\/apache2\/README-access_compat.txt\n    <IfModule mod_access_compat.c>' $HTTPD_CONF_FILE_PATH
        [ $? -ne 0 ] && apos_abort "ERROR: sed n. 4 failed!!!"
		sed -i 's/<\/Files>/    <\/IfModule>\n    <IfModule !mod_access_compat.c>\n        Require all denied\n    <\/IfModule>\n&/' $HTTPD_CONF_FILE_PATH
	    [ $? -ne 0 ] && apos_abort "ERROR: sed n. 5 failed!!!"
		sed -i 's/Include \/etc\/apache2\/vhosts.d\/\*.conf/IncludeOptional \/etc\/apache2\/vhosts.d\/\*.conf/g' $HTTPD_CONF_FILE_PATH	
        [ $? -ne 0 ] && apos_abort "ERROR: sed n. 6 failed!!!"
		sed -i 's/    Order allow,deny/        Order allow,deny/g' $HTTPD_CONF_FILE_PATH
	    [ $? -ne 0 ] && apos_abort "ERROR: sed n. 7 failed!!!"
		sed -i 's/    Order deny,allow/        Order deny,allow/g' $HTTPD_CONF_FILE_PATH
        [ $? -ne 0 ] && apos_abort "ERROR: sed n. 8 failed!!!"
		sed -i 's/    Deny from all/        Deny from all/g' $HTTPD_CONF_FILE_PATH
		[ $? -ne 0 ] && apos_abort "ERROR: sed n. 9 failed!!!"
    else
        apos_abort "ERROR: $HTTPD_CONF_FILE_PATH doesn't exist!!!"
    fi 
else
  apos_log "Migrate of $HTTPD_CONF_FILE_PATH skipped!!!"
fi



apos_outro $0
exit $TRUE

# End of file
