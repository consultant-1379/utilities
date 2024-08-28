##
## Copyright (c) Ericsson AB, 2016.
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

TAG="${0##*/}"
COM_USER_MGMT_GROUP="com-emergency"

logger  -p local0.info -t "${TAG}" "Start"

# Creating emergency groups for troubleshooting user and certificate management
if [ ! $(getent group $COM_USER_MGMT_GROUP 2> /dev/null) ];
then
    groupadd $COM_USER_MGMT_GROUP
    LDE_GROUP_ADD_CMD=$(which lde-global-user 2> /dev/null)
    if  [ -x ${LDE_GROUP_ADD_CMD} ]; then
         ${LDE_GROUP_ADD_CMD} -g ${COM_USER_MGMT_GROUP}
    fi
fi

logger  -p local0.info -t "${TAG}" "End"

exit 0
