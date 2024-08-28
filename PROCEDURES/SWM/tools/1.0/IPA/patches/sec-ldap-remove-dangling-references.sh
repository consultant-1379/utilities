#!/bin/bash
##
## remove-dangling-references <class> <attribute>
##   Check if there are any dangling references, print them and set the
##   reference to NULL.
##
##   Exit codes:
##   0 - OK - References successfully removed
##   1 - Error - An error occurred while setting the references to NULL
##
##   Version 1.0
##

# Copyright (C) 2014 by Ericsson AB
# S - 125 26  STOCKHOLM
# SWEDEN, tel int + 46 10 719 0000
#
# The copyright to the computer program herein is the property of
# Ericsson AB. The program may be used and/or copied only with the
# written permission from Ericsson AB, or in accordance with the terms
# and conditions stipulated in the agreement/contract under which the
# program has been supplied.
#
# All rights reserved.

. /opt/coremw/lib/common

class=$1
attr=$2
prg=$(basename "$0")
err_code=0
if [ "$#" -ne 2 ];then
    die "Invalid number of parameters. Try --help to get more info"
fi

# Check if old COM instance of Ldap class exist
$immfind | grep ^ldapId=1,ldapAuthenticationMethodId=1
if [ $? -ne 0 ];then
    log -s "$prg Instance of $class class does not exist"
    # It is OK if the class instance does not exist. Then there is no need to check for dangling references.
    exit 0
fi


# the class-name should exist
$immlist -c "$class" &> /dev/null
if [ $? -ne 0 ];then
    log -s "$prg class $class does not exist"
    exit 1
fi
# the attribute name should exist for this class
line=$($immlist -c "$class" | grep "^$attr :")
if [ -z "$line" ];then
    log -s "$prg attribute $attr does not exist in class $class"
    exit 1
fi
# even if the user pass in an attribute name that is not of type SA_NAME_T or
# which is RDN, we still check the reference (or whatever) it points to
for n in $($immfind -c "$class"); do
    #find the line with given attribute
    line=$($immlist -a "$attr" "$n")
    if [ -n "$line" ];then
        value=${line#*=} #chop off the attribute name
        #decode the value, <Empty> or null is allowed
        if [ -n "$value" ] && [ "$value" != "<Empty>" ];then
            # decode $value, there might be multiple references in $value seperated by ':'
            count=1
            obj=''
            # exit the loop when there's just one reference or all references are checked
            until [ "$obj" = "$value" ]; do
                obj=$(echo "$value" | cut -f$count -d':')
                let count+=1
                if [ -n "$obj" ];then
                    $immfind "$obj" | grep "^$obj\$" &> /dev/null
                    if [ $? -ne 0 ];then
                        # print the error message to both stderr and syslog
                        log -s "$prg DN=$n class $class attribute $attr reference [$obj] does not exist"
                        # remove this attribute value
                        $immcfg -a "$attr"-="$obj" "$n" &> /dev/null
                        if [ $? -ne 0 ];then
                            # print the error message to both stderr and syslog
                            log -s "$prg failed to remove reference [$obj] for DN=$n class $class attribute $attr"
                            err_code=1
                        fi
                    fi
                else
                    break
                fi
            done
        fi
    fi
done
exit $err_code
