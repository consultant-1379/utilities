<< 'About'
	pass command line arguments to generate respective infra specific checksumfiles
	Command Line Args 	INFRA
	GEP			GEP
	VM			VM
About

#Collecting uniq command line arguments and converting to lower case
CMDLINE_ARGUMENTS=($(for i in $*; do echo $i | tr '[:upper:]' '[:lower:]'; done | sort | uniq))

#Items to be excluded on Native node
#If new files are to be excluded introduce in the array

NATIVE_EXCLUSION=("/opt/ap/apos/bin/apos_ha_devmond_md" "/opt/ap/apos/bin/apos_ha_operations_md" "/opt/ap/apos/bin/apos_ha_rdeagentd_md" "/opt/ap/apos/bin/apos_ha_scsi_operations" "/opt/ap/apos/bin/apos_ha_srvcntl" "/opt/ap/apos/bin/cliss/raidmgr_md.sh" "/opt/ap/apos/bin/nodeState" "/opt/ap/apos/bin/raidmgmt" "/opt/ap/apos/bin/raidmgr_md" "/opt/ap/apos/conf/apos_ha_rdeagent.conf" "/opt/ap/apos/etc/deploy/etc/services_md" "/opt/ap/apos/etc/deploy/etc/sudoers.d/APG-comgroup_md" "/opt/ap/apos/etc/deploy/etc/sudoers.d/APG-tsgroup_md" "/opt/ap/apos/etc/deploy/etc/sysconfig/atftpd_AP2" "/opt/ap/apos/etc/enm_models/HLR_ENM_Roles_Rules.xml" "/opt/ap/apos/etc/enm_models/IPSTP_ENM_Roles_Rules.xml" "/opt/ap/cps/conf/busrv/busrv.dat" "/opt/brf/lib/libbrfc_trace.so" "/opt/brf/lib/libbrfcmwa_trace.so" "/opt/brf/lib/libbrfp_trace.so" "/opt/eric/sec-cert-cxp9027891/bin/sec-cert-pdo.sh" "/opt/eric/sec-cert-cxp9027891/bin/sec-cert-pre-pso.sh" "/opt/eric/sec-la-cxp9026994/bin/log-authentication-failure.sh" "/opt/eric/sec-la-cxp9026994/bin/sec-la-agent-status.sh" "/opt/eric/sec-la-cxp9026994/bin/sec-la-agent.sh" "/opt/eric/sec-la-cxp9026994/bin/sec-ldap-cert-slave.sh" "/opt/eric/sec-la-cxp9026994/bin/sec-ldap-server-slave.sh" "/opt/eric/sec-la-cxp9026994/bin/sec-ldap-status-slave.sh" "/opt/eric/sec-la-cxp9026994/bin/sec-ldap-trigger-account-sync.sh" "/opt/eric/sec-la-cxp9026994/bin/sec_la_agent.py" "/opt/eric/sec-la-cxp9026994/bin/sec_la_daemon.py" "/opt/ap/apos/conf/apos_finalize_system_conf.sh" "/opt/ap/apos/conf/apos_guest.sh" "/opt/ap/apos/conf/apos_snrinit_rebuild.sh" "/opt/ap/apos/conf/apos_system_conf.sh" "/opt/ap/apos/conf/enlarged_ddisk_impacts.sh" "/opt/ap/apos/etc/deploy/etc/dhcpd.conf.local_vm" "/opt/ap/apos/etc/deploy/usr/lib/systemd/scripts/apos-finalize-system-conf.sh" "/opt/ap/apos/etc/deploy/usr/lib/systemd/scripts/apos-recovery-conf.sh" "/opt/ap/apos/etc/deploy/usr/lib/systemd/scripts/apos-system-conf.sh" "/opt/ap/apos/etc/deploy/usr/lib/systemd/system/apos-finalize-system-config.service" "/opt/ap/apos/etc/deploy/usr/lib/systemd/system/apos-recovery-conf.service" "/opt/ap/apos/etc/deploy/usr/lib/systemd/system/apos-system-config.service")

#Items to be excluded in AP2
#If new files are to be excluded introduce in the array
AP2_EXCLUSION=("/opt/ap/cphw/doc" "/opt/ap/cphw/lib" "/opt/ap/cps/doc" "/opt/ap/cps/lib" "/opt/ap/fms/doc" "/opt/ap/fms/lib" "/opt/ap/mcs/lib" "/opt/ap/sts/doc" "/opt/ap/sts/lib" "/opt/ap/sts/lib64")

#Items to be included in GEP2
#If new files are to be included introduce in the array
GEP2_INCLUSION=("/opt/ap/apos/conf/apos_ha_rdeagent.conf" "/opt/ap/apos/bin/apos_ha_srvcntl" "/opt/ap/apos/bin/raidmgmt" "/opt/ap/apos/bin/nodeState" "/opt/ap/apos/bin/apos_ha_scsi_operations")

#Items to be excluded in GEP2
#If new files are to be excluded introduce in the array
GEP2_EXCLUSION=("/opt/ap/apos/conf/apos_ha_agentd.conf" "/opt/ap/apos/conf/apos_ha_devmond.conf" "/opt/ap/apos/etc/deploy/usr/lib/systemd/scripts/apos-drbd.sh" "/opt/ap/apos/etc/deploy/usr/lib/systemd/system/apos-drbd.service")

#Items to be excluded on VM node
#If new files are to be excluded introduce in the array
VM_EXCLUSION=("/opt/ap/apos/bin/apos_ha_devmond_md" "/opt/ap/apos/bin/apos_ha_operations_md" "/opt/ap/apos/bin/apos_ha_rdeagentd_md" "/opt/ap/apos/bin/apos_ha_scsi_operations" "/opt/ap/apos/bin/apos_ha_srvcntl" "/opt/ap/apos/bin/cliss/raidmgr_md.sh" "/opt/ap/apos/bin/nodeState" "/opt/ap/apos/bin/raidmgmt" "/opt/ap/apos/bin/raidmgr_md" "/opt/ap/apos/conf/apos_ha_rdeagent.conf" "/opt/ap/apos/etc/deploy/etc/services_md" "/opt/ap/apos/etc/deploy/etc/sudoers.d/APG-comgroup_md" "/opt/ap/apos/etc/deploy/etc/sudoers.d/APG-tsgroup_md" "/opt/ap/apos/etc/deploy/etc/sysconfig/atftpd_AP2" "/opt/ap/apos/etc/enm_models/HLR_ENM_Roles_Rules.xml" "/opt/ap/apos/etc/enm_models/IPSTP_ENM_Roles_Rules.xml" "/opt/ap/cps/conf/busrv/busrv.dat" "/opt/brf/lib/libbrfc_trace.so" "/opt/brf/lib/libbrfcmwa_trace.so" "/opt/brf/lib/libbrfp_trace.so" "/opt/eric/sec-cert-cxp9027891/bin/sec-cert-pdo.sh" "/opt/eric/sec-cert-cxp9027891/bin/sec-cert-pre-pso.sh" "/opt/eric/sec-la-cxp9026994/bin/log-authentication-failure.sh" "/opt/eric/sec-la-cxp9026994/bin/sec-la-agent-status.sh" "/opt/eric/sec-la-cxp9026994/bin/sec-la-agent.sh" "/opt/eric/sec-la-cxp9026994/bin/sec-ldap-cert-slave.sh" "/opt/eric/sec-la-cxp9026994/bin/sec-ldap-server-slave.sh" "/opt/eric/sec-la-cxp9026994/bin/sec-ldap-status-slave.sh" "/opt/eric/sec-la-cxp9026994/bin/sec-ldap-trigger-account-sync.sh" "/opt/eric/sec-la-cxp9026994/bin/sec_la_agent.py" "/opt/eric/sec-la-cxp9026994/bin/sec_la_daemon.py" "/opt/ap/acs/etc/nsf" "/opt/ap/apos/etc/deploy/etc/dhcpd.conf.local")

#Files that have to be renamed 
#E.g. abc_drbd file when installed on node will be renamed to abc
FILES_TO_RENAME=("/opt/ap/apos/bin/apos_ha_devmond_drbd" "/opt/ap/apos/bin/apos_ha_operations_drbd" "/opt/ap/apos/bin/apos_ha_rdeagentd_drbd" "/opt/ap/apos/bin/cliss/raidmgr_drbd.sh" "/opt/ap/apos/bin/raidmgr_drbd" "/opt/ap/apos/etc/deploy/etc/services_drbd" "/opt/ap/apos/etc/deploy/etc/sudoers.d/APG-comgroup_drbd" "/opt/ap/apos/etc/deploy/etc/sudoers.d/APG-tsgroup_drbd")

CHECKSUM_FILE_NAME="acs_lct_sha1verify.conf"
GEP="gep"
VM="vm"

#Standard Directory Structure on Native and VM
DIRECTORY_STRUCTURE_FILE="directoryStructure"

#Handling Overwritten files 
#E.g. Some files have been overwritten then their md5sum should have to be updated with the copied file's md5sum
declare -A OVERWRITTEN_FILES

OVERWRITTEN_FILES=(
	["/opt/com/lib/comp/libcom_authorization_agent.cfg"]="/opt/ap/apos/conf/libcom_authorization_agent.cfg"
)

#md5sum of key is replaced by md5sum of value value 
for key in ${!OVERWRITTEN_FILES[@]}
do
	value=$(echo ${OVERWRITTEN_FILES[$key]} | sed 's/\//\\\//g')
	replacement=$(cat res/$CHECKSUM_FILE_NAME | grep $value\" | awk -F '"' '{print $3}')
	to_be_replaced=$(cat res/$CHECKSUM_FILE_NAME | grep $(echo $key | sed 's/\//\\\//g')\" | awk -F '"' '{print $3}')
	sed -i "s/$to_be_replaced/$replacement/g" res/$CHECKSUM_FILE_NAME
done

function generate_ap2(){
	INPUT_FILE=$1
	INPUT_CONFIG=$2
	cp $INPUT_FILE AP2_$INPUT_CONFIG\_$CHECKSUM_FILE_NAME
        for i in ${AP2_EXCLUSION[@]}
        do
           DELETION_ITEM=$(echo $i | sed 's/\//\\\//g')
           sed -i "/$DELETION_ITEM\"/d" AP2_$INPUT_CONFIG\_$CHECKSUM_FILE_NAME
        done
        #AP2 update checksum of file /opt/ap/apos/etc/deploy/etc/sysconfig/atftpd to checksum of /opt/ap/apos/etc/deploy/etc/sysconfig/atftpd_AP2
        SEARCH_ITEM=$(echo "/opt/ap/apos/etc/deploy/etc/sysconfig/atftpd" | sed 's/\//\\\//g')
        SEARCH_ITEM_CHECKSUM=$(cat AP2_$INPUT_CONFIG\_$CHECKSUM_FILE_NAME | grep $SEARCH_ITEM | awk -F '"' '{print $3}')
        RELACE_ITEM_CHECKSUM=$(cat ../res/$CHECKSUM_FILE_NAME | grep $SEARCH_ITEM\_AP2 | awk -F '"' '{print $3}')
        sed -i "s/$SEARCH_ITEM_CHECKSUM/$REPLACE_ITEM_CHECKSUM/g" AP2_$INPUT_CONFIG\_$CHECKSUM_FILE_NAME	
}

#Generating infra specific baseline files
for i in ${CMDLINE_ARGUMENTS[@]}
do
	if [ $i = 'gep' ];then
		echo "Gep Infra Selected"

		pushd output_baseline/
		cp ../res/$CHECKSUM_FILE_NAME AP1_GEP5_$CHECKSUM_FILE_NAME
		
		#Renaming Files
		for i in ${FILES_TO_RENAME[@]}
		do
			SEARCH_ITEM=$(echo $i | sed 's/\//\\\//g')
			REPLACE_ITEM=$(echo $SEARCH_ITEM | sed 's/_drbd//')
			sed -i "s/$SEARCH_ITEM/$REPLACE_ITEM/g" AP1_GEP5_$CHECKSUM_FILE_NAME
		done
		
		#Removing Exclusion items from baseline file 
		for i in ${NATIVE_EXCLUSION[@]}
		do
			DELETION_ITEM=$(echo $i | sed 's/\//\\\//g')
			sed -i "/$DELETION_ITEM\"/d" AP1_GEP5_$CHECKSUM_FILE_NAME
		done
		
		echo "Copying directories to checksum file"
		cat ../$DIRECTORY_STRUCTURE_FILE >> AP1_GEP5_$CHECKSUM_FILE_NAME
		
		#Generating Baseline for AP2_GEP5
		generate_ap2 AP1_GEP5_$CHECKSUM_FILE_NAME GEP5

		#Generating Base for GEP2
		cp AP1_GEP5_$CHECKSUM_FILE_NAME AP1_GEP2_$CHECKSUM_FILE_NAME
	 	for i in ${GEP2_EXCLUSION[@]}
		do
			DELETION_ITEM=$(echo $i | sed 's/\//\\\//g')
			sed -i "/$DELETION_ITEM\"/d" AP1_GEP2_$CHECKSUM_FILE_NAME
		done	
		for i in ${GEP2_INCLUSION[@]}
		do
			echo $(cat ../res/$CHECKSUM_FILE_NAME | grep $i\") >> AP1_GEP2_$CHECKSUM_FILE_NAME
		done
		for i in ${FILES_TO_RENAME[@]}
		do
			SEARCH_ITEM=$(echo $i | sed 's/\//\\\//g' | sed 's/_drbd//')
			SEARCH_ITEM_CHECKSUM=$(cat AP1_GEP2_$CHECKSUM_FILE_NAME | grep $SEARCH_ITEM | awk -F '"' '{print $3}')
			RELACE_ITEM_CHECKSUM=$(cat ../res/$CHECKSUM_FILE_NAME | grep $SEARCH_ITEM\_md | awk -F '"' '{print $3}')
			sed -i "s/$SEARCH_ITEM_CHECKSUM/$REPLACE_ITEM_CHECKSUM/g" AP1_GEP2_$CHECKSUM_FILE_NAME
			
		done	

		#Generating Baseline for AP2_GEP2
		generate_ap2 AP1_GEP2_$CHECKSUM_FILE_NAME GEP2

		popd

	elif [ $i = 'vm' ];then
		echo "VM Infra Selected"

		pushd output_baseline/
                cp ../res/$CHECKSUM_FILE_NAME AP1_VM_$CHECKSUM_FILE_NAME
		
		#Renaming Files
                for i in ${FILES_TO_RENAME[@]}
                do
                        SEARCH_ITEM=$(echo $i | sed 's/\//\\\//g')
                        REPLACE_ITEM=$(echo $SEARCH_ITEM | sed 's/_drbd//')
                        sed -i "s/$SEARCH_ITEM/$REPLACE_ITEM/g" AP1_VM_$CHECKSUM_FILE_NAME
                done

		#Removing Exclusion items from baseline file
                for i in ${VM_EXCLUSION[@]}
                do
                        DELETION_ITEM=$(echo $i | sed 's/\//\\\//g')
                        sed -i "/$DELETION_ITEM\"/d" AP1_VM_$CHECKSUM_FILE_NAME
                done
	
		echo "Copying directories to checksum file"
                cat ../$DIRECTORY_STRUCTURE_FILE >> AP1_VM_$CHECKSUM_FILE_NAME
		#Excluding /opt/ap/acs/etc/nsf folder which is not present on VM 
		sed -i "/\/opt\/ap\/acs\/etc\/nsf\"/d" AP1_VM_$CHECKSUM_FILE_NAME
                popd

	else
		echo "Invalid Argument $i"
	fi
	
done

