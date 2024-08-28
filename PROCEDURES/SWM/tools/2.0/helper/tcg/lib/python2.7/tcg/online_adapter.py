import tempfile
import subprocess
import os
import re
import time
import errno
import copy

from utils.logger_tcg import tcg_error
import logging
import AMFTools
import AMFModel
import CgtConstants

class OnlineAdapter(object):
    def __init__(self,
                 immdump_filename,
                 hostname_amfnode_filename,
                 offline_instantiation,
                 rpm_mappinng_filename,
                 rpm_repository_path):
        self._immdump_file_created = False
        self._rpm_mappinng_filename = rpm_mappinng_filename
        self._offline_instantiation = offline_instantiation
        self._rpm_bundle_mapping = {}
        self._sw_bundle_mapping = {}
        self._reboot_update_for_sw_bundle_mapping = {}
        self._reboot_info_mapping = {}
        self._used_bundle_names = set()
        self._rpm_repository_path = rpm_repository_path
        self._immdump_base = AMFModel.AMFModel()

        self._immdump_filename = immdump_filename
        if not self._immdump_filename and self.is_running_online():
            self._immdump_filename = self._create_immdump_file_online()
        if self._immdump_filename:
            logging.debug("Parsing imm dump file: %s", self._immdump_filename)
            try:
                self._immdump_base.parseXML(self._immdump_filename)
            except Exception as e:
                tcg_error("error while parsing base imm dump: " + str(e))


        self._hostname_amfnode_map = self._retrieve_hostname_amfnode_map(hostname_amfnode_filename)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if (self._immdump_file_created):
            os.remove(self._immdump_filename)

    def get_immdump_filename(self):
        return self._immdump_filename

    def get_reboot_update_for_sw_bundle_mapping(self):
        return self._reboot_update_for_sw_bundle_mapping

    def get_hostname_to_amfnode(self):
        return self._hostname_amfnode_map

    def is_running_online(self):
        return self._is_tcg_running_on_a_target_system() and not self.is_offline_instantiation()

    def is_offline_instantiation(self):
        return self._offline_instantiation

    def _is_tcg_running_on_a_target_system(self):
        return os.system("which immdump") == 0

    def _create_immdump_file_online(self):
        filename = tempfile.mkstemp()[1]
        self._immdump_file_created = True
        f = open(filename)
        try:
            subprocess.call(" -c ".join(["immdump"] + AMFModel.AMFModel.getInterestedAmfClasses()), stdout=f, shell=True)
        except OSError as e:
            if (e.errno == errno.ENOENT):
                tcg_error("Command immdump can not be executed. Possible root "
                          "cause is that TCG is being executed offline. The offline "
                          "option has to be used or the immdump has to be provided.")
            else:
                raise
        return filename

    def _retrieve_hostname_amfnode_map(self, h2a_filename):
        if h2a_filename:
            return self._retrieve_hostname_amfnode_map_from_file(h2a_filename)
        else:
            return self._retrieve_hostname_amfnode_map_from_imm()

    def _retrieve_hostname_amfnode_map_from_file(self, h2a_filename):
        logging.debug("Hostname to AmfNode mapping file: {0}".format(h2a_filename))
        return self._parse_host_node_map_file(h2a_filename)

    def _retrieve_hostname_amfnode_map_from_imm(self):
        hostname_amfnode_map = dict()
        if self.is_running_online():
            hostname_amfnode_map = self.__create_hostname_amfnodemap_online()
        else:
            logging.warning("No hostname to AmfNode mapping provided."
                            "It is assumed that the CSM model is using AmfNode names")
        return hostname_amfnode_map

    def _parse_host_node_map_file(self, filename):
        return_dict = dict()

        f = open(filename, 'r')
        line_num = 1
        for line in f:
            tokens = line.split()
            if not tokens:
                continue
            if len(tokens) != 2:
                tcg_error("Error in node name mapping file. Invalid number of entries in line %d: %s" % (line_num, line))
            if tokens[0] in return_dict:
                tcg_error("Error in node name mapping file. Second occurrence of host name %s in line %d: %s" % (tokens[0], line_num, line))
            return_dict[tokens[0]] = tokens[1]
            line_num = line_num + 1

        return return_dict

    def __create_hostname_amfnodemap_online(self):
        ''' Translate the hostname to amf-node name '''
        returnDict = dict()
        lines = self.__pcall('immfind -c SaAmfNode')
        for node in lines:
            nodeName = re.sub('safAmfNode=(.*),.*', r'\1', node)
            cmd = 'immlist -a saAmfNodeClmNode {0}'.format(node)
            host = re.sub('.*safNode=(.*),.*', r'\1', self.__pcall(cmd)[0])
            logging.debug("Hostname - AmfNode mapping - {0}:{1}".format(host, nodeName))
            returnDict[host] = nodeName
        return returnDict

    def get_rpm_name(self, bundle, filename):
        sw_bundle = None
        if filename in self._rpm_bundle_mapping:
            return self._rpm_bundle_mapping[filename]
        if bundle in self._sw_bundle_mapping:
            return self._sw_bundle_mapping[bundle]

        if self.is_running_online():
            if not self._sw_bundle_mapping:
                self._build_up_bundle_mapping_from_repository()
                if bundle in self._sw_bundle_mapping:
                  return self._sw_bundle_mapping[bundle]
            sw_bundle = self._get_software_name_with_ecim_file_util(filename)
        elif self._rpm_mappinng_filename:
            sw_bundle = self._get_software_name_from_mapping_file(filename)
        elif self._rpm_repository_path:
            sw_bundle = self._get_software_name_from_rpm_file(bundle, filename)
        else:
            return AMFTools.getProvider() + "-" + bundle

        self._rpm_bundle_mapping[filename] = sw_bundle
        self._sw_bundle_mapping[bundle] = sw_bundle
        return sw_bundle

    def get_reboot_info(self, bundle, filename):
        reboot_info = None
        if not self._reboot_info_mapping:
            self._reboot_info_mapping = self._build_up_reboot_info_mapping()
        candidates = ([bundle] if bundle.startswith('ERIC-') or bundle.startswith('3PP-') else
              ['ERIC-'+bundle, '3PP-'+bundle])
        for bundle_name in candidates:
            if bundle_name in self._reboot_info_mapping:
                reboot_info = copy.deepcopy(self._reboot_info_mapping[bundle_name])
                return reboot_info

        if self.is_running_online():
            reboot_info_tuple = self._get_reboot_info_with_ecim_file_util(filename)
            if reboot_info_tuple is not None:
                realBundleName = reboot_info_tuple[0]
                reboot_info = {CgtConstants.META_BUNDLE_NAME_TAG:realBundleName, CgtConstants.INSTALL_REBOOT_FLAG:reboot_info_tuple[1],CgtConstants.UPGRDADE_REBOOT_FLAG:reboot_info_tuple[2]}
                self._reboot_info_mapping[realBundleName] = copy.deepcopy(reboot_info)
        return reboot_info

    def get_reboot_info_of_used_bundle_with_prefix(self, bundleNamePrefix):
        reboot_info = None
        if not self._used_bundle_names:
            self._used_bundle_names = self._get_used_bundle_names()
        for bundleName in self._used_bundle_names:
            if bundleNamePrefix in bundleName:
                reboot_info = copy.deepcopy(self._reboot_info_mapping[bundleName])
                break
        return reboot_info

    def set_reboot_info(self, bundleName, reboot_info):
        rebootSwBundle = {}
        if reboot_info[CgtConstants.INSTALL_REBOOT_FLAG] and self._reboot_info_mapping[bundleName][CgtConstants.INSTALL_REBOOT_FLAG] is False:
            self._reboot_info_mapping[bundleName][CgtConstants.INSTALL_REBOOT_FLAG] = True
            rebootSwBundle[CgtConstants.INSTALL_REBOOT_FLAG] = True
            logging.info("Will update reboot info back to IMM of bundle %s with install reboot: %s" %(bundleName, rebootSwBundle[CgtConstants.INSTALL_REBOOT_FLAG]))
        if reboot_info[CgtConstants.UPGRDADE_REBOOT_FLAG] and self._reboot_info_mapping[bundleName][CgtConstants.UPGRDADE_REBOOT_FLAG] is False:
            self._reboot_info_mapping[bundleName][CgtConstants.UPGRDADE_REBOOT_FLAG] = True
            rebootSwBundle[CgtConstants.UPGRDADE_REBOOT_FLAG] = True
            logging.info("Will update reboot info back to IMM of bundle %s with upgrade reboot: %s" %(bundleName, rebootSwBundle[CgtConstants.UPGRDADE_REBOOT_FLAG]))
        if rebootSwBundle is not None:
            self._reboot_update_for_sw_bundle_mapping[bundleName] =  rebootSwBundle

    def _get_reboot_info_with_ecim_file_util(self, filename):
        reboot_info = None
        try:
            cmd = "/opt/coremw/lib/ecim-file-util --findBundleName %s" % filename
            realBundleName = self.__pcall(cmd)[0]
            if realBundleName is not None:
                cmd = 'cmw-utility immlist -a saSmfBundleInstallOfflineScope safSmfBundle=%s' % realBundleName
                result = self.__pcall(cmd)[0]
                installReboot = True if result == "saSmfBundleInstallOfflineScope=4" else False

                cmd = 'cmw-utility immlist -a saSmfBundleRemoveOfflineScope safSmfBundle=%s' % realBundleName
                result = self.__pcall(cmd)[0]
                upgradeReboot = True if result == "saSmfBundleRemoveOfflineScope=4" else False

                reboot_info = (realBundleName, installReboot, upgradeReboot)
                logging.debug("Got reboot info - {0} -install {1} -upgrade {2}".format(filename, installReboot, upgradeReboot))
            else:
                logging.warning("Failed to get reboot from the CSP package for file %s. Because of couldn't file bundle name" % filename)
        except Exception as e:
            logging.warning("Failed to get reboot from the CSP package for file " + filename + ". " + str(e) +
                      ". Check the syslog for more infomation")
        return reboot_info

    def _get_used_bundle_names(self):
        listUsedBundles = set()
        for nodeSwBundleObj in self._immdump_base.getObjects(AMFModel.SaAmfNodeSwBundle).values():
            bundleName = nodeSwBundleObj.getName().replace("safSmfBundle=","")
            if bundleName not in listUsedBundles:
                listUsedBundles.add(bundleName)
        return listUsedBundles

    def _get_software_name_with_ecim_file_util(self, filename):
        sw_bundle = None
        cmd = "/opt/coremw/lib/ecim-file-util --findBundleName %s" % filename
        try:
            sw_bundle = self.__pcall(cmd)[0]
        except Exception as e:
            tcg_error("Failed to get bundle name from the CSP package for file " + filename + ". " + str(e) +
                      ". Check the syslog for more infomation")
        if len(sw_bundle.split()) > 1:
            tcg_error("Found SW bundle for file {0} has unexpected format: {1}".format(filename, sw_bundle))
        logging.debug("Got rpm bundle name - {0}:{1}".format(sw_bundle, filename))
        return sw_bundle

    def _build_up_reboot_info_mapping(self):
        ''' build reboot info mapping file from imm '''
        rebootInfoDict = dict()
        for swBundleObj in self._immdump_base.getObjects(AMFModel.SaSmfSwBundle).values():
            bundleName = swBundleObj.getName()
            installScope = swBundleObj.getsaSmfBundleInstallOfflineScope()
            removeScope = swBundleObj.getsaSmfBundleRemoveOfflineScope()

            installReboot = True if installScope == "4" else False
            upgradeReboot = True if removeScope == "4" else False
            rebootInfoDict[bundleName] = {CgtConstants.META_BUNDLE_NAME_TAG:bundleName, CgtConstants.INSTALL_REBOOT_FLAG:installReboot,CgtConstants.UPGRDADE_REBOOT_FLAG:upgradeReboot}
            logging.debug("Reboot Info mapping - {0}: installReboot {1} removeReboot {2}".format( \
                          bundleName, installReboot, upgradeReboot))
        return rebootInfoDict

    def _build_up_bundle_mapping_from_repository(self):
        sw_bundles = None
        cmd = "/opt/coremw/bin/cmw-repository-list"
        try:
            sw_bundles = self.__pcall(cmd)
        except Exception as e:
            tcg_error("Failed to get list bundle names from system. " + str(e) +
                      ". Check the syslog for more infomation")

        for sw_bundle in sw_bundles:
            sw_bundle_name = sw_bundle.split(' ')[0]
            sw_bundle_name_without_prefix = re.sub('^(ERIC|3PP)-', '', sw_bundle_name)
            self._sw_bundle_mapping[sw_bundle_name_without_prefix] = sw_bundle_name


    def _get_software_name_from_mapping_file(self, filename):
        sw_bundle = None
        logging.debug("Try to get rpm bundle name from mapping file %s" % self._rpm_mappinng_filename)
        try:
            with open(self._rpm_mappinng_filename) as f: 
                for line in f.readlines():
                    if filename in line:
                        sw_bundle = line.split(" ")[1].replace("\n", "")
                        break
        except OSError as err:
            tcg_error("Failed to open rpm mapping file %s" % self._rpm_mappinng_filename)

        if sw_bundle is None:
            tcg_error("Couldn't map given rpm file %s in mapping file %s" % (filename, self._rpm_mappinng_filename))
        return sw_bundle

    def _get_software_name_from_rpm_file(self, bundle, filename):
        vendor = self._extract_vendor_from_rpm_file(filename)

        prefix = "3PP"
        if re.search("Ericsson AB", vendor):
            prefix = AMFTools.getProvider()

        sw_bundle = prefix + "-" + bundle
        logging.debug("Got rpm bundle name - {0}:{1}".format(sw_bundle, filename))
        return sw_bundle

    def _extract_vendor_from_rpm_file(self, filename):
        rpmfile = self._find_absolute_path_to_rpm(filename)

        vendor = None
        if rpmfile:
            vendor = self._query_vendor_with_rpm_command(rpmfile)

        if not vendor:
            vendor = "Ericsson AB"
            logging.debug(("Could not find rpm in the sytem, "
                           "returning the default vendor ({vendor}) for "
                           "rpm {rpm_file}").format(vendor=vendor,
                                                    rpm_file=filename))

        return vendor

    def _query_vendor_with_rpm_command(self, rpmfile):
        return subprocess.check_output("rpm -qp --qf '%%{VENDOR}' %s" % rpmfile,
                                       shell=True)

    def _find_absolute_path_to_rpm(self, filename):
        rpmfile = os.path.join(self._rpm_repository_path, filename)
        if not os.path.exists(rpmfile):
            logging.warning("Could not find '{fn}' in '{path}'".format(fn=filename,
                            path=self._rpm_repository_path))
            rpmfile = None
        return rpmfile

    # Constant defining the time in second the script wait between every retry
    # if an IMM operation fails.
    # This to avoid failing if the IMM synchronize and can not accept changes.
    # Note that this list is read by the code from the end to the beginning
    __CMW_TRYAGAIN_WAITTIME = (60, 30, 20, 5, 1)

    def __pcall(self, cmd):
        """ Start a command and get the output as a list of strings
            Tries again number of times according to parameter : TRYAGAIN_PATTERN
            Then raise Exception
        """
        retcode = 1
        try_again = len(self.__CMW_TRYAGAIN_WAITTIME)

        TRYAGAIN_PATTERN = "saImmOmAdminOwnerSet|SA_AIS_ERR_TRY_AGAIN|" +\
        "SA_AIS_ERR_BUSY|SA_AIS_ERR_TIMEOUT|SA_AIS_ERR_NO_RESOURCES|SA_AIS_ERR_FAILED_OPERATION"

        OFFLINE_PATTERN = "immfind: not found"
        run_command = True
        while run_command:
            pro = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
            output = pro.communicate()
            retcode = pro.poll()
            if retcode != 0 and re.search(OFFLINE_PATTERN, output[0]):
                tcg_error("Command '{0}' can not be executed. Possible root "
                          "cause is that TCG is being executed offline. The offline "
                          "option has to be used or required information has to be provided as arguments.".format(cmd))
            run_command = False
            try_again = try_again - 1
            if retcode != 0 and re.search(TRYAGAIN_PATTERN, output[0]) and try_again >= 0:
                time.sleep(self.__CMW_TRYAGAIN_WAITTIME[try_again])
                run_command = True
        if retcode != 0:
            raise Exception('poll() returned non zero exit code {0}'.format(retcode))
        return output[0].splitlines()
