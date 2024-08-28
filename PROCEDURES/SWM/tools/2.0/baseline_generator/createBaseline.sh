#!/bin/bash

RPM="rpm"
SDP="sdp"
RUNTIME_PACKAGES="runtime"
WORKING_DIR="baseline_generator"
WORKSPACE="../../workspace"

#Creating/Formatting RPM Folder 
if [ ! -d $WORKING_DIR/$RPM ];then
	mkdir $WORKING_DIR/$RPM
else
	rm -rf $WORKING_DIR/$RPM/*
fi

#Creating/Formatting SDP Folder
if [ ! -d $WORKING_DIR/$SDP ];then
	mkdir $WORKING_DIR/$SDP
else
	rm -rf $WORKING_DIR/$SDP/*
fi

#Removing checksum file if it is present
if [ -f $WORKING_DIR/intermediate_baseline ];then
	rm -rf $WORKING_DIR/intermediate_baseline
fi

#Collecting all runtime packages into temp folder
if [ ! -d $WORKING_DIR/$RUNTIME_PACKAGES ];then
	mkdir $WORKING_DIR/$RUNTIME_PACKAGES 
	for i in $(find $WORKSPACE -iname *.tar.gz | grep runtime) 
	do 
		cp -u $i $WORKING_DIR/$RUNTIME_PACKAGES 
	done
else
	for i in $(find $WORKSPACE -iname *.tar.gz | grep runtime)
        do
                cp -u $i $WORKING_DIR/$RUNTIME_PACKAGES
        done
fi

#Removing LDE runtime package since LDE is not included for baseline creation
rm -rf $(ls $WORKING_DIR/$RUNTIME_PACKAGES | grep ldews-[0-9.-]*-runtime-sle-cxp[0-9]*.tar.gz)

#extracting rpms and sdps from packages 
for item in $(find $WORKING_DIR/$RUNTIME_PACKAGES -iname *.tar.gz)
do
	#extracting only .rpm extension files into RPM folder
	if [ $(tar -tzf $item | grep '.rpm$' | wc -l) -ge 1 ];then
		tar -xvf $item -C $WORKING_DIR/$RPM/ --wildcards --no-anchored '*.rpm'
	fi
	#extracting only .sdp extension files into SDP folder
	if [ $(tar -tzf $item | grep '.sdp$' | wc -l) -ge 1 ];then
		tar -xvf $item -C $WORKING_DIR/$SDP/ --wildcards --no-anchored '*.sdp'
	fi
done

#Extracting only .rpm extension files from SDPs
for sdp in $(find $WORKING_DIR/$SDP/ -iname *.sdp)
do
	if [ $(tar -tzf $sdp | grep '.rpm$' | wc -l) -ge 1 ];then
		tar -xvf $sdp -C $WORKING_DIR/$RPM/ --wildcards --no-anchored '*.rpm'
	fi
done

#Generating checksum of rpm files
for rpm_name in $(find $WORKING_DIR/$RPM/ -iname *.rpm)
do
        rpm -qlp --dump $rpm_name | awk -F ' ' '{print $1,$4}' >> $WORKING_DIR/intermediate_baseline
done

echo "Re-Formatting checksum file"
#Creating/Formatting res Folder
if [ ! -d $WORKING_DIR/res ]; then
	mkdir $WORKING_DIR/res
else
	rm -rf $WORKING_DIR/res/*
fi

#Updating checksum of directories from '00000000000000000000000000000000' -> ''
awk -v q='"' '{print q$1q$2}' $WORKING_DIR/intermediate_baseline | sed 's/00000000000000000000000000000000//g' > $WORKING_DIR/res/formatted_intermediate_baseline

echo "Filtering intermediate baseline file based on configuration file acs_lct_integrityAP_base.conf"
pushd $WORKING_DIR/
./baseline_filter.sh

echo "renaming checksum file"
sort res/filtered_intermediate_baseline | uniq > res/acs_lct_sha1verify.conf

#Creating baseline files for vm and gep
./baseline_infraspecific.sh gep vm

echo "Executing legacy baseline Generator"
#Generating Other infra baselines using baseline_generator.sh script
./baseline_generator.sh output_baseline/AP1_GEP5_acs_lct_sha1verify.conf AP1_GEP7
./baseline_generator.sh output_baseline/AP1_GEP5_acs_lct_sha1verify.conf AP1_GEP5_SMX
./baseline_generator.sh output_baseline/AP1_GEP5_acs_lct_sha1verify.conf AP1_GEP7_SMX
./baseline_generator.sh output_baseline/AP2_GEP5_acs_lct_sha1verify.conf AP2_GEP7

#Copying Baselines Generated in output_baseline by script to workspace/integrity-files/ for packaging
cp output_baseline/AP1_VM_acs_lct_sha1verify.conf ../../../workspace/integrity-files/
cp output_baseline/AP1_GEP5_acs_lct_sha1verify.conf ../../../workspace/integrity-files/
cp output_baseline/AP2_GEP5_acs_lct_sha1verify.conf ../../../workspace/integrity-files/
cp output_baseline/AP1_GEP2_acs_lct_sha1verify.conf ../../../workspace/integrity-files/
cp output_baseline/AP2_GEP2_acs_lct_sha1verify.conf ../../../workspace/integrity-files/

echo "Cleaning Up directories"
if [ -d $RPM ];then
	rm -rf $RPM
fi

if [ -d $SDP ];then
	rm -rf $SDP
fi

if [ -d $RUNTIME_PACKAGES ];then
	rm -rf $RUNTIME_PACKAGES
fi

if [ -d res ];then
	rm -rf res
fi

if [ -f intermediate_baseline ];then
	rm -rf intermediate_baseline
fi

popd
