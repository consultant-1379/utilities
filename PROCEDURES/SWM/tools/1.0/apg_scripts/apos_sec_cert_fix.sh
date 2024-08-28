#!/bin/bash
##
# ------------------------------------------------------------------------
#     Copyright (C) 2018 Ericsson AB. All rights reserved.
# ------------------------------------------------------------------------
##
# Name:
#      apos_sec_cert_fix.sh
# Description:
#       A script to create symbolic links during the upgrade.
# Note:
# None.
##
# Changelog:
# First version.

STORAGE_CONFIG_PATH="/usr/share/pso/storage-paths/config"
CONFIG_PATH=$(< "$STORAGE_CONFIG_PATH")
CERTM_PRIVATE_PATH="$CONFIG_PATH/apos/sec/var/db/"
SEC_CERTM_PRIVATE_PATH="$CONFIG_PATH/sec-apr9010539/var/db/"
APACHE_SSL_CONF_FILE='/etc/apache2/conf.d/ssl.conf'

function log(){
  /bin/logger -t apos_sec_cert_fix "$@"  
}

function abort(){
  log "$@"
  exit 1
}

function update(){
  # 1. create the local folder if not exist
  if [ ! -d "$CERTM_PRIVATE_PATH" ]; then
    local MESSAGE="creating folder: [$CERTM_PRIVATE_PATH]... "
    log "$MESSAGE"
    mkdir -p $CERTM_PRIVATE_PATH &>/dev/null 
    if [ $? -ne 0 ]; then
      abort "$MESSAGE failed"
    else
      log "$MESSAGE success"
    fi
  fi

  # 2. check if the apache server is configured and copy the key to the internal location
  if [ -s "${APACHE_SSL_CONF_FILE}" ]; then 
    if grep -q 'SSLCertificateKeyFile .*' ${APACHE_SSL_CONF_FILE}; then
      key_absolute_path=$( httpmgr -q all | grep -i 'Private key' | awk -F ':' '{print $2}')
      if [ -n "$key_absolute_path" ]; then 
        key=$( basename $key_absolute_path)
        # copy the key to the new location
        cp -f $key_absolute_path $CERTM_PRIVATE_PATH/$key
        if [ $? -ne 0 ]; then
         if [ -f "$SEC_CERTM_PRIVATE_PATH/$key" ]; then 
           cp -f $SEC_CERTM_PRIVATE_PATH/$key $CERTM_PRIVATE_PATH/$key 
           [ $? -ne 0 ] && log "copy [$SEC_CERTM_PRIVATE_PATH/$key -> $CERTM_PRIVATE_PATH/$key] failed"
         else
           abort "copy [$key_absolute_path -> $CERTM_PRIVATE_PATH/$key] failed"
         fi
	fi 

        id=$( echo $key | tr -cd '[[:digit:]]')
        # 3. update '/etc/apache2/conf.d/ssl.conf' with SSLCertificateFile information
        cert_key=node_cert_id_"$id".pem
        sed -i 's#SSLCertificateFile.*#SSLCertificateFile \"'$SEC_CERTM_PRIVATE_PATH$cert_key'\"#g' ${APACHE_SSL_CONF_FILE}
        # 4. update '/etc/apache2/conf.d/ssl.conf' with SSLCertificateKeyFile information
        sed -i 's#SSLCertificateKeyFile.*#SSLCertificateKeyFile \"'$CERTM_PRIVATE_PATH$key'\"#g' ${APACHE_SSL_CONF_FILE} || \
          abort "updation to ${APACHE_SSL_CONF_FILE} failed"

        # 5. update '/etc/apache2/conf.d/ssl.conf' with SSLCACertificateFile information
        trust_key="trusted_cert_id_"$id".pem"
        sed -i 's#SSLCACertificatePath.*#SSLCACertificateFile \"'$SEC_CERTM_PRIVATE_PATH$trust_key'\"#g' ${APACHE_SSL_CONF_FILE} || \
          abort "updation [SSLCACertificateFile $CERTM_PRIVATE_PATH/$key]to ${APACHE_SSL_CONF_FILE} failed"
         
        if ! grep -q 'SSLVerifyClient .*' ${APACHE_SSL_CONF_FILE}; then
          local new_row='SSLVerifyClient require'
          sed -i "/SSLCACertificateFile .*/a \t\t${new_row}" ${APACHE_SSL_CONF_FILE} || abort "adding SSLVerifyClient to ${APACHE_SSL_CONF_FILE} failed"
        fi 
      else
        log "httpmgr: Private Key empty!!"
      fi
    fi
  fi
}

function rollback(){
  # 1. rollback the folder informatioin
  if [ -d "$CERTM_PRIVATE_PATH" ]; then
    local MESSAGE="removing folder: [$CERTM_PRIVATE_PATH]... "
    log "$MESSAGE"
    rm -rf "$CERTM_PRIVATE_PATH" &>/dev/null
    if [ $? -ne 0 ]; then
      log "$MESSAGE failed"
    else
      log "$MESSAGE success"
    fi
  fi

  if [ -s "${APACHE_SSL_CONF_FILE}" ]; then
    if grep -q 'SSLCertificateKeyFile .*' ${APACHE_SSL_CONF_FILE}; then
      # 2. update '/etc/apache2/conf.d/ssl.conf' with the old information 
      key_absolute_path=$( grep SSLCertificateFile.* ${APACHE_SSL_CONF_FILE} | awk -F \" '{print $2}')
      key=$( basename $key_absolute_path)

      sed -i 's#SSLCertificateKeyFile.*#SSLCertificateKeyFile \"'$SEC_CERTM_PRIVATE_PATH/$key'\"#g' ${APACHE_SSL_CONF_FILE} || \
        log "updation [SSLCertificateKeyFile $SEC_CERTM_PRIVATE_PATH/$key] to ${APACHE_SSL_CONF_FILE} failed"

      local old_ca_certifcate_path="/storage/system/config/asec/https_certs/"
      sed -i 's#SSLCACertificateFile.*#SSLCACertificatePath \"'$old_ca_certifcate_path'\"#g' ${APACHE_SSL_CONF_FILE} || \
        log "updation [SSLCACertificatePath "$old_ca_certifcate_path"] to ${APACHE_SSL_CONF_FILE}"

      if grep -q 'SSLVerifyClient .*' ${APACHE_SSL_CONF_FILE}; then
        sed -i "/^[[:space:]]*SSLVerifyClient require/d" ${APACHE_SSL_CONF_FILE} || log "Deletion of [SSLVerifyClient require] from ${APACHE_SSL_CONF_FILE} is failed"
      fi 
    fi
  fi
}

# _____________________ _____________________
#|    _ _   _  .  _    |    _ _   _  .  _    |
#|   | ) ) (_| | | )   |   | ) ) (_| | | )   |
#|_____________________|_____________________|
# Here begins the "main" function...

log "START: <$0 $*>"

OPTION="$1"

if [ "$OPTION" == '--update' ]; then 
  update
elif [ "$OPTION" == '--rollback' ]; then
  rollback
else
  log 'invalid option'
fi

log "END: <$0 $*>"

exit 0

