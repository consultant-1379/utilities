###########################################################################
# ------------------------------------------------------------------------
#     Copyright (C) 2018 Ericsson AB. All rights reserved.
# ------------------------------------------------------------------------
#
# Description:
#	source esm.modules
#   Load needed modules in both bash and tcsh shell.
#
###########################################################################

echo ""
echo "#############################"
echo "##### LOAD SWM2.0 TOOLS #####"
echo "#############################"
module use /app/dxtoolbox/modules/
echo "module use /app/dxtoolbox/modules/       # RC:<$?>"
module add dxtoolbox/1.29
echo "module add dxtoolbox/1.29/                # RC:<$?>"

##########################################################
## Using qemu and libvirt installed on edeaclx0730
#module add qemu/2.8.0
#echo "module add qemu/2.8.0                    # RC:<$?>"
#module add libvirt/3.0.0
#echo "module add libvirt/3.0.0                 # RC:<$?>"
#module load libvirt/3.0.0
#echo "module add libvirt/3.0.0                 # RC:<$?>"
##########################################################

module add python/2.7.9
echo "module add python/2.7.9                  # RC:<$?>"
module add python/2.7-addons-pyyaml-3.12
echo "module add python/2.7-addons-pyyaml-3.12 # RC:<$?>"
echo ""
