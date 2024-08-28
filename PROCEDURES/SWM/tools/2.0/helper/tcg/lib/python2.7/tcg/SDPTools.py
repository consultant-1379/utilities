import tarfile
import os
import stat
import shutil
import CgtConstants
from xml.dom.minidom import Document
from utils.logger_tcg import tcg_error
import logging
import AMFTools

SDP_SCRIPT_NAME = "cdf-sdp-handler.sh"

PROVIDER_ERIC = "ERIC-"
PROVIDER_3PP = "3PP-"


def generateSDPWrapperScript(fileName):
    f = open(fileName, "w")
    f.write("#!/bin/sh -f\n\n")
    f.write("SDP_ROOT=`dirname $0`\n\n")
    f.write("exec $SDP_ROOT/" + SDP_SCRIPT_NAME + " $@\n")
    f.close();
    st = os.stat(fileName)
    os.chmod(fileName, st.st_mode | stat.S_IEXEC)


def generateSDPScript(fileName):
    f = open(fileName, "w")
    f.write("#!/bin/bash\n\n")
    f.write("HOST=`hostname`\n")
    f.write("BUNDLENAME=$1\n")
    f.write("MODE=$2\n")
    f.write("ACTION=$3\n")
    f.write("SDP_ROOT=`dirname $0`\n")
    f.write("logger \"sdp_script: called on host $HOST with args: $@\"\n")
    f.write("RPM_LIST=`ls $SDP_ROOT/rpms/*`\n")
    f.write("if [ \"$ACTION\" == \"install\" -a \"$MODE\" == \"offline\" ]; then\n")
    f.write("    logger \"sdp_script: installation ordered\"\n")
    f.write("    for i in $RPM_LIST; do\n")
    f.write("        cmw-rpm-config-add $i\n")
    f.write("        logger \"sdp_script: installed rpm $i\"\n")
    f.write("    done\n")
    f.write("    logger \"sdp_script: installation finished\"\n")
    f.write("fi\n")
    f.write("if [ \"$ACTION\" == \"removal\" -a \"$MODE\" == \"offline\" ]; then\n")
    f.write("    logger \"sdp_script: removal ordered\"\n")
    f.write("    for i in $RPM_LIST; do\n")
    f.write("        RPM_NAME=`rpm -qp $i`\n")
    f.write("        cmw-rpm-config-delete $RPM_NAME $HOST\n")
    f.write("        logger \"sdp_script: removed rpm $i\"\n")
    f.write("    done\n")
    f.write("    logger \"sdp_script: removal finished\"\n")
    f.write("fi\n")
    f.close()
    st = os.stat(fileName)
    os.chmod(fileName, st.st_mode | stat.S_IEXEC)


def generateSDPFromDirectory(sourceDirectory, targetDirectory, sdpName, campaignSDP = False, ctUnit = None):
    sdpFileName = os.path.join(targetDirectory, sdpName + ".sdp")

    # check that the generated SDP rdn is not longer than 64 characters, this is a limitation for SA_STRING_T rdns in IMM
    rdn = "safSmfBundle=" + sdpName
    if len(rdn) > 64:
        tcg_error("Name of SDP %s is longer than 64 characters" % sdpName)

    # generate ETF.xml
    ETFFileName = os.path.join(sourceDirectory, "ETF.xml")
    doc = Document()
    rootElement = doc.createElement("entityTypesFile")
    rootElement.setAttribute("xmlns:xsi", "http://www.w3.org/2001/XMLSchema-instance")
    rootElement.setAttribute("name", sdpName)
    rootElement.setAttribute("provider", sdpName.split("-")[0])
    rootElement.setAttribute("xsi:noNamespaceSchemaLocation", "SAI-AIS-SMF-ETF-A.01.02_OpenSAF.xsd")
    doc.appendChild(rootElement)
    if not campaignSDP:
        swBundle = doc.createElement("swBundle")
        swBundle.setAttribute("name", rdn)
        rootElement.appendChild(swBundle)

        removal = doc.createElement("removal")
        swBundle.appendChild(removal)

        installation = doc.createElement("installation")
        swBundle.appendChild(installation)

        removal_offline =  doc.createElement("offline")
        removal.appendChild(removal_offline)

        removal_offline_command = doc.createElement("command")
        removal_offline_command.appendChild(doc.createTextNode("offline-remove"))
        removal_offline.appendChild(removal_offline_command)

        removal_offline_arg = doc.createElement("args")
        removal_offline_arg.appendChild(doc.createTextNode(sdpName + " offline removal"))
        removal_offline.appendChild(removal_offline_arg)

        removal_offline_serviceUnit = doc.createElement("serviceUnit")
        removal_offline.appendChild(removal_offline_serviceUnit)

        removal_online =  doc.createElement("online")
        removal.appendChild(removal_online)

        removal_online_command = doc.createElement("command")
        removal_online_command.appendChild(doc.createTextNode("online-remove"))
        removal_online.appendChild(removal_online_command)

        removal_online_arg = doc.createElement("args")
        removal_online_arg.appendChild(doc.createTextNode(sdpName + " online removal"))
        removal_online.appendChild(removal_online_arg)

        installation_offline =  doc.createElement("offline")
        installation.appendChild(installation_offline)

        installation_offline_command = doc.createElement("command")
        installation_offline_command.appendChild(doc.createTextNode("offline-install"))
        installation_offline.appendChild(installation_offline_command)

        installation_offline_arg = doc.createElement("args")
        installation_offline_arg.appendChild(doc.createTextNode(sdpName + " offline install"))
        installation_offline.appendChild(installation_offline_arg)

        installation_offline_serviceUnit = doc.createElement("serviceUnit")
        installation_offline.appendChild(installation_offline_serviceUnit)

        installation_online =  doc.createElement("online")
        installation.appendChild(installation_online)

        installation_online_command = doc.createElement("command")
        installation_online_command.appendChild(doc.createTextNode("online-install"))
        installation_online.appendChild(installation_online_command)

        installation_online_arg = doc.createElement("args")
        installation_online_arg.appendChild(doc.createTextNode(sdpName + " online install"))
        installation_online.appendChild(installation_online_arg)

        sdpDeployDir = os.path.join(ctUnit.directory, "scripts", "SDP-deploy")

        def genScript(scriptName, sourceDirectory, sdpDeployDir):
            deployScript = os.path.join(sdpDeployDir, scriptName)
            if os.path.exists(deployScript):
                shutil.copy2(deployScript, os.path.join(sourceDirectory, scriptName))
            else:
                generateSDPWrapperScript(os.path.join(sourceDirectory, scriptName))

        sdprootInCTDir = os.path.join(ctUnit.directory, "sdproot")
        if os.path.exists(sdprootInCTDir):
            for d in os.listdir(sdprootInCTDir):
                if os.path.isdir(os.path.join(sdprootInCTDir, d)):
                    shutil.copytree(os.path.join(sdprootInCTDir, d), os.path.join(sourceDirectory, d))
                else:
                    shutil.copy2(os.path.join(sdprootInCTDir, d), os.path.join(sourceDirectory, d))

        genScript("online-install", sourceDirectory, sdpDeployDir)
        genScript("offline-install", sourceDirectory, sdpDeployDir)
        genScript("online-remove", sourceDirectory, sdpDeployDir)
        genScript("offline-remove", sourceDirectory, sdpDeployDir)

        generateSDPScript(os.path.join(sourceDirectory, SDP_SCRIPT_NAME))

    xml = open(ETFFileName, "w")
    xml.write(doc.toprettyxml(indent="  "))
    xml.close()
    tar = tarfile.open(sdpFileName, "w:gz")
    for d in os.listdir(sourceDirectory):
        tar.add(os.path.join(sourceDirectory, d), arcname = d)
    tar.close()


def get_bundle_name_with_provider_missing(installed_bundles, bundle):
    if bundle.startswith(PROVIDER_ERIC) or bundle.startswith(PROVIDER_3PP):
        return bundle

    smf_bundle = "safSmfBundle="
    for installed_bundle in installed_bundles:
        if installed_bundle.startswith(smf_bundle + PROVIDER_ERIC + bundle):
            return PROVIDER_ERIC + bundle
        elif installed_bundle.startswith(smf_bundle + PROVIDER_3PP + bundle):
            return PROVIDER_3PP + bundle
    return None
