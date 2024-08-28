#!/bin/sh
##
## Copyright (c) Ericsson AB, 2013.
## 
## All Rights Reserved. Reproduction in whole or in part is prohibited
## without the written consent of the copyright owner.
## 
## ERICSSON MAKES NO REPRESENTATIONS OR WARRANTIES ABOUT THE
## SUITABILITY OF THE SOFTWARE, EITHER EXPRESS OR IMPLIED, INCLUDING
## BUT NOT LIMITED TO THE IMPLIED WARRANTIES OF MERCHANTABILITY,
## FITNESS FOR A PARTICULAR PURPOSE, OR NON-INFRINGEMENT. ERICSSON
## SHALL NOT BE LIABLE FOR ANY DAMAGES SUFFERED BY LICENSEE AS A
## RESULT OF USING, MODIFYING OR DISTRIBUTING THIS SOFTWARE OR ITS
## DERIVATIVES.
##
##

## This script is intended to be sourced by a com upgrade script. For example
## com_upgrade_do_wrapup.sh). The Access Management specific upgrade actions 
## is then possible to execute by calling appropiate function in this script.
## Variables and functions in this script are prefixed with AMC or amc 
## (Access Management Component) in order to avoid clashes with variable and 
## function names in the com upgrade scripts.
AMC_BACKUP_DIR="/tmp"

AMC_SYNCD_CONF="/etc/syncd.conf"
AMC_SYNCD_CONF_BACKUP="${AMC_BACKUP_DIR}/syncd.conf"

AMC_LDAP_CONF="/etc/openldap/ldap.conf"
AMC_CLUSTER_LDAP_CONF="/cluster/etc/openldap/ldap.conf"
AMC_LDAP_CONF_BACKUP="${AMC_BACKUP_DIR}/ldap.conf"
AMC_CLUSTER_LDAP_CONF_BACKUP="${AMC_BACKUP_DIR}/cluster/ldap.conf"
AMC_LDAP_CONF_UPGRADE_REMOVED="${AMC_LDAP_CONF}.upgradeRemoved"

AMC_LDAP_RC="/root/.ldaprc"
AMC_CLUSTER_LDAP_RC="/cluster/etc/openldap/.ldaprc"
AMC_LDAP_RC_BACKUP="${AMC_BACKUP_DIR}/.ldaprc"
AMC_CLUSTER_LDAP_RC_BACKUP="${AMC_BACKUP_DIR}/cluster/.ldaprc"
AMC_LDAP_RC_UPGRADE_REMOVED="${AMC_LDAP_RC}.upgradeRemoved"

## The introduction of an COM internal LDAP server makes the files 
## /etc/openldap/ldap.conf and /root/.ldaprc obsolete.
## For the upgrade to an COM internal LDAP client the following actions are 
## performed in this function:
## - Make a temporary backup of /etc/syncd.conf to be used in case of a 
##   upgrade roll back.
##
## - Remove sync specifications concerning the files /etc/openldap/ldap.conf
##   and /root/.ldaprc from /etc/syncd.conf.
##
## - Make a temporary backup of /cluster/etc/openldap/ldap.conf and 
##   /cluster/etc/openldap/.ldaprc to be used in case of a upgrade roll back.
##
## - Remove /cluster/etc/openldap/ldap.conf and /cluster/etc/openldap/.ldaprc
##
## - Make a temporary backup of /etc/openldap/ldap.conf and /root/.ldaprc to 
##   be used in case of a upgrade roll back.
##
## - Make a permanent backup of /etc/openldap/ldap.conf and /root/.ldaprc by 
##   creating a copy with the suffix '.upgradeRemoved' and then remove the original file
amc_upgrade_do_wrapup() {

    logger "AMC upgrade: start upgrade"

    mkdir -p ${AMC_BACKUP_DIR}/cluster
    check_exit_value "ERROR: Could not create backup directory ${AMC_BACKUP_DIR}/cluster"

    if [ -f $AMC_SYNCD_CONF ]; then
	cp -f $AMC_SYNCD_CONF $AMC_SYNCD_CONF_BACKUP
	check_exit_value "ERROR: Could not copy $AMC_SYNCD_CONF to $AMC_SYNCD_CONF_BACKUP"
 
	AMC_SED_FILTER_EXPR="sed -e 's/\//\\\ \//g' | sed -e 's/ //g' | sed -e 's/\./\\\./g'"

        # Add escape character before '/' and '.' to make the path fit into the sed expression.
	AMC_SED_LOCAL_LDAP_CONF=`echo $AMC_LDAP_CONF | eval $AMC_SED_FILTER_EXPR`
	AMC_SED_REMOTE_CLUSTER_LDAP_CONF=`echo $AMC_CLUSTER_LDAP_CONF | eval $AMC_SED_FILTER_EXPR`
	AMC_SED_LOCAL_LDAP_RC=`echo $AMC_LDAP_RC | eval $AMC_SED_FILTER_EXPR`
	AMC_SED_REMOTE_CLUSTER_LDAP_RC=`echo $AMC_CLUSTER_LDAP_RC | eval $AMC_SED_FILTER_EXPR`

        # Read 7 lines after the 'file' keyword and remove the file-clause based on
        # contents of local and remote file name. 
        # Remove identical consecutive newlines in file.
        # Remove trailing newline in file.
	cat $AMC_SYNCD_CONF_BACKUP | \
	    eval "sed -e '{/^file/ {N;N;N;N;N;N;N; /file[ \t\n]*{.*local[ \t]*=[ \t]*\"$AMC_SED_LOCAL_LDAP_CONF.*remote[ \t]*=[ \t]*\"$AMC_SED_REMOTE_CLUSTER_LDAP_CONF.*}/d}}'" | \
	    eval "sed -e '{/^file/ {N;N;N;N;N;N;N; /file[ \t\n]*{.*local[ \t]*=[ \t]*\"$AMC_SED_LOCAL_LDAP_RC.*remote[ \t]*=[ \t]*\"$AMC_SED_REMOTE_CLUSTER_LDAP_RC.*}/d}}'" | \
	    sed -e '$!N; /^\(.*\)\n\1$/!P; D' | \
	    sed -e '${/^$/d}' > $AMC_SYNCD_CONF
    fi

    if [ -f $AMC_CLUSTER_LDAP_RC ]; then
	cp -f $AMC_CLUSTER_LDAP_RC $AMC_CLUSTER_LDAP_RC_BACKUP
	check_exit_value "ERROR: Could not copy $AMC_CLUSTER_LDAP_RC to $AMC_CLUSTER_LDAP_RC_BACKUP"
	rm $AMC_CLUSTER_LDAP_RC
	check_exit_value "ERROR: Could not remove $AMC_CLUSTER_LDAP_RC"
    fi

    if [ -f $AMC_CLUSTER_LDAP_CONF ]; then
	cp -f $AMC_CLUSTER_LDAP_CONF $AMC_CLUSTER_LDAP_CONF_BACKUP
	check_exit_value "ERROR: Could not copy $AMC_CLUSTER_LDAP_CONF to $AMC_CLUSTER_LDAP_CONF_BACKUP"
	rm $AMC_CLUSTER_LDAP_CONF
	check_exit_value "ERROR: Could not remove $AMC_CLUSTER_LDAP_CONF"
    fi

    if [ -f $AMC_LDAP_RC ]; then
	cp -f $AMC_LDAP_RC $AMC_LDAP_RC_BACKUP
	check_exit_value "ERROR: Could not copy $AMC_LDAP_RC to $AMC_LDAP_RC_BACKUP"
	mv -f $AMC_LDAP_RC $AMC_LDAP_RC_UPGRADE_REMOVED
	check_exit_value "ERROR: Could not backup $AMC_LDAP_RC to $AMC_LDAP_RC_UPGRADE_REMOVED"
	
    fi

    if [ -f $AMC_LDAP_CONF ]; then
	cp -f $AMC_LDAP_CONF $AMC_LDAP_CONF_BACKUP
	check_exit_value "ERROR: Could not copy $AMC_LDAP_CONF to $AMC_LDAP_CONF_BACKUP"
	mv -f $AMC_LDAP_CONF "$AMC_LDAP_CONF_UPGRADE_REMOVED"
	check_exit_value "ERROR: Could not backup $AMC_LDAP_CONF to $AMC_LDAP_CONF_UPGRADE_REMOVED"
    fi

    logger "AMC upgrade: upgrade complete"
}

## For a roll back of the upgrade to an COM internal LDAP client the following
## actions are performed in this function:
## - Restore /etc/syncd.conf, /etc/openldap/ldap.conf, /root/.ldaprc, 
##   /cluster/etc/openldap/ldap.conf and /cluster/etc/openldap/.ldaprc from the 
##   backup directory if available.
## - Remove any permanent backup of etc/openldap/ldap.conf or /root/.ldaprc
amc_upgrade_undo_wrapup() {

    logger "AMC upgrade: start undo upgrade"

    if [ -f $AMC_SYNCD_CONF_BACKUP ]; then
	cp -f $AMC_SYNCD_CONF_BACKUP $AMC_SYNCD_CONF
	check_exit_value "ERROR: Could not copy $AMC_SYNCD_CONF_BACKUP to $AMC_SYNCD_CONF"
	rm -f $AMC_SYNCD_CONF_BACKUP
    fi

    if [ -f $AMC_CLUSTER_LDAP_RC_BACKUP ]; then
	cp -f $AMC_CLUSTER_LDAP_RC_BACKUP $AMC_CLUSTER_LDAP_RC
	check_exit_value "ERROR: Could not copy $AMC_CLUSTER_LDAP_RC_BACKUP to $AMC_CLUSTER_LDAP_RC"
	rm -f $AMC_CLUSTER_LDAP_RC_BACKUP
    fi

    if [ -f $AMC_CLUSTER_LDAP_CONF_BACKUP ]; then
	cp -f $AMC_CLUSTER_LDAP_CONF_BACKUP $AMC_CLUSTER_LDAP_CONF
	check_exit_value "ERROR: Could not copy $AMC_CLUSTER_LDAP_CONF_BACKUP to $AMC_CLUSTER_LDAP_CONF"
	rm -f $AMC_CLUSTER_LDAP_CONF_BACKUP
    fi

    if [ -f $AMC_LDAP_RC_BACKUP ]; then
	cp -f $AMC_LDAP_RC_BACKUP $AMC_LDAP_RC
	check_exit_value "ERROR: Could not copy $AMC_LDAP_RC_BACKUP to $AMC_LDAP_RC"
	rm -f $AMC_LDAP_RC_BACKUP
	rm -f $AMC_LDAP_RC_UPGRADE_REMOVED
    fi

    if [ -f $AMC_LDAP_CONF_BACKUP ]; then
	cp -f $AMC_LDAP_CONF_BACKUP $AMC_LDAP_CONF
	check_exit_value "ERROR: Could not copy $AMC_LDAP_CONF to $AMC_LDAP_CONF_BACKUP"
	rm -f $AMC_LDAP_CONF_BACKUP
	rm -f $AMC_LDAP_CONF_UPGRADE_REMOVED
    fi

    logger "AMC upgrade: Undo upgrade complete"
}
