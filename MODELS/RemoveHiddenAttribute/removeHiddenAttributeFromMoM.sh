#!/bin/bash
set -e
# Check for proper number of command line args.

EXPECTED_ARGS=1
E_BADARGS=65

if [ $# -ne $EXPECTED_ARGS ]
then
  echo "Usage: `basename $0` <absolute path mp>"
  exit $E_BADARGS
fi

if [ -e $1 ]; then
	echo "Removing Hidden attribute from mp file..."
	java -classpath . RemoveHiddenAttributesFromMoM $1 1>$1_tmp
	2>&1
	echo "Hidden attribute removed"
	echo "New intermediate file" $1_tmp
	echo "Removing original" $1
	rm $1
	2>&1
	echo "Renaming" $1_tmp "to" $1
	mv $1_tmp $1
	2>&1
else
	echo "File" $1 "does not exist!"
fi
