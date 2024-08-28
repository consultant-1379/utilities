#! /bin/bash 

APOS_CONF_FOLDER='/boot/tmp/opt/ap/apos/conf/'
APOS_BIN_FOLDER='/boot/tmp/opt/ap/apos/bin/gi'

# Mount boot partition 
echo -n "Mounting /boot folder..."
mount -L lde-boot /boot
echo " Done"

# Unpack the initrd and inject the APG impacts to handle the
# 1. Create the temporary directory
[ ! -d /boot/tmp ] && mkdir -p /boot/tmp 

# 2. Extract the initrd content to temporary folder 
pushd /boot/tmp  >/dev/null 2>&1
echo -n "Unpacking initrd file to temporary folder..."
xz -dc < /boot/initrd | cpio --quiet -i --make-directories &>/dev/null
if [ $? -ne 0 ]; then
	echo " Failed"
	exit 1
fi 
echo "Done"
popd >/dev/null 2>&1

# Create the APG realted folder into the initrd
echo -n "Creating conf and bin directories into initrd..." 
mkdir -p ${APOS_CONF_FOLDER}
mkdir -p ${APOS_BIN_FOLDER}
echo  " Done"

mkdir /test
cp /mnt/APG_DUMP.tgz /test/

# Now inject APG scripts into the initrd
pushd /test >/dev/null 2>&1
echo -n "Unpacking APG dump into temporary folder..."
if [ -f ./APG_DUMP.tgz ]; then 
  tar -xzf ./APG_DUMP.tgz  &>/dev/null || exit 1
else
  echo " Failed"
  exit 1
fi
echo " Done"

echo -n "Copying the APG scripts into respective folders of initrd..."
# Now copy respective files to respective folders 
if [ -f ./apos-early-system-config.service ]; then 
  cp ./apos-early-system-config.service /usr/lib/systemd/system/
  cp /usr/lib/systemd/system/apos-early-system-config.service /boot/tmp/usr/lib/systemd/system/
  chmod 644 /boot/tmp/usr/lib/systemd/system/apos-early-system-config.service
  # create a symbolic link to /etc configuration folder
  ln -s /usr/lib/systemd/system/apos-early-system-config.service /boot/tmp/etc/systemd/system/lde-nodetype@control.target.wants/apos-early-system-config.service
  chmod 644 /boot/tmp/etc/systemd/system/lde-nodetype@control.target.wants/apos-early-system-config.service
fi 

if [ -f ./apos-system-config.service ]; then 
  cp ./apos-system-config.service /usr/lib/systemd/system/
  cp /usr/lib/systemd/system/apos-system-config.service /boot/tmp/usr/lib/systemd/system/ 
  chmod 644 /boot/tmp/usr/lib/systemd/system/apos-system-config.service
  # create a symbolic link to /etc configuration folder
  ln -s /usr/lib/systemd/system/apos-system-config.service /boot/tmp/etc/systemd/system/lde-nodetype@control.target.wants/apos-system-config.service
  chmod 644 /boot/tmp/etc/systemd/system/lde-nodetype@control.target.wants/apos-system-config.service
fi 

if [ -f ./apg-cluster-update.service ]; then 
  cp ./apg-cluster-update.service /usr/lib/systemd/system/
  cp /usr/lib/systemd/system/apg-cluster-update.service /boot/tmp/usr/lib/systemd/system/
  chmod 644 /boot/tmp/usr/lib/systemd/system/apg-cluster-update.service
  # create a symbolic link to /etc configuration folder
  ln -s /usr/lib/systemd/system/apg-cluster-update.service /boot/tmp/etc/systemd/system/lde-nodetype@control.target.wants/apg-cluster-update.service
  chmod 644 /boot/tmp/etc/systemd/system/lde-nodetype@control.target.wants/apg-cluster-update.service
fi 

cp -f ./apos-system-conf.sh /boot/tmp/usr/lib/systemd/scripts/ &>/dev/null
cp -f ./apg_cluster_update.sh /boot/tmp/usr/lib/systemd/scripts/ &>/dev/null
tar -xzf ./apos_getinfo.tgz -C ${APOS_BIN_FOLDER}/ &>/dev/null
chmod -R 755 ${APOS_BIN_FOLDER}/*
cp -f ./apos_system_conf.sh ${APOS_CONF_FOLDER} &>/dev/null
cp -f ./config_params.conf ${APOS_CONF_FOLDER} &>/dev/null
cp -f ./apos_hwtype.sh ${APOS_CONF_FOLDER} &>/dev/null
cp -f ./apos_common.sh ${APOS_CONF_FOLDER} &>/dev/null
cp -rf ./apos_common_res/ ${APOS_CONF_FOLDER} &>/dev/null
cp -f ./cluster.conf /boot/.cluster.conf &>/dev/null
popd >/dev/null 2>&1

echo " Done"

pushd /boot/tmp >/dev/null 2>&1
echo -n "Packing initrd with APG contents..."
find . 2>/dev/null | cpio --quiet -c -o | xz -9 --format=lzma > /boot/tmp/initrd
if [ $? -ne 0 ]; then
	echo " Failed"
	exit 1
fi 
popd >/dev/null 2>&1
echo " Done"

# Last but not lease actions
mv /boot/initrd /boot/initrd.old
sleep 2
mv /boot/tmp/initrd /boot/

# Create configuration stage file 
echo 2 > /boot/.config_stage

rm -rf /boot/tmp 2>/dev/null
rm -rf /test
umount /boot

echo "#################################################"
echo "    APG SCRIPTS INJECTED SUCCESSFULLY            "
echo "#################################################"