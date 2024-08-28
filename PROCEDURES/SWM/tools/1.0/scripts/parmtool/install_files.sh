#!/bin/bash -ux

function abort(){
	echo -e "$*"
	exit 1
}

function get_lines(){
	cat $(dirname $0)/files.list | grep -Ev "^[[:space:]]*#|^[[:space:]]*$"	
}

function check_missing(){
	[ $# -ne 1 ] && abort "usage: $FUNCNAME <SOURCE_DIRECTORY>"
	pushd $1 &>/dev/null
	diff <(get_lines | awk -F: '{print $2}'|sort) <(find * | sort) || abort "misconfiguration in files.list"
	popd &>/dev/null
}

function install_files(){
	[ $# -ne 2 ] && abort "usage: $FUNCNAME <SOURCE_DIRECTORY> <DESTINATION_DIRECTORY>"
	local SRC_DIR=$1
	local DEST_DIR=$2
	chmod -R 777 $DEST_DIR
	rm -rf $DEST_DIR/*
	local LINES=$(get_lines)
	for L in $LINES; do
		local PERM=$(echo $L|awk -F':' '{print $1}')
		local FILE=$(echo $L|awk -F':' '{print $2}')
		if [ -d $SRC_DIR/$FILE ]; then
			#echo "mkdir -p -m $PERM $DEST_DIR/$FILE"
			mkdir -p -m 777 $DEST_DIR/$FILE || abort "failure while creating the $DEST_DIR/$FILE directory"		
		elif [ -f $SRC_DIR/$FILE ]; then
			#echo "install -m $PERM $SRC_DIR/$FILE $DEST_DIR/$FILE"
			install -m $PERM $SRC_DIR/$FILE $DEST_DIR/$FILE || abort "failure during the copy of the $FILE file"
		else
			abort "$SRC_DIR/$FILE is not a file nor a directory"
		fi
	done
	for L in $LINES; do
		local PERM=$(echo $L|awk -F':' '{print $1}')
		local FILE=$(echo $L|awk -F':' '{print $2}')
		if [ -d $SRC_DIR/$FILE ]; then
			#echo "mkdir -p -m $PERM $DEST_DIR/$FILE"
			chmod $PERM $DEST_DIR/$FILE || abort "failure while changing the permissions of the $DEST_DIR/$FILE directory"
		fi
	done
}

function list_files(){
	[ $# -ne 2 ] && abort "usage: $FUNCNAME <SOURCE_DIRECTORY> <DESTINATION_DIRECTORY>"
	local SRC_DIR=$1
	local DEST_DIR=$2
	for F in $(get_lines | awk -F':' '{print $2}'); do
		[ ! -d $SRC_DIR/$F ] && echo $DEST_DIR/$F
	done
}

[ $# -ne 2 ] && abort "usage: $0 <SOURCE_DIRECTORY> <DESTINATION_DIRECTORY>"
[ ! -d $1 ] && abort "$1 is not a directory"
[ ! -d $2 ] && abort "$2 is not a directory"
check_missing $1
install_files $1 $2

