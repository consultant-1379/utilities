#!/usr/bin/python
#
# (C) Copyright 2018 Ericsson AB
import os
import sys
import getopt

class ExitStatus:
    """Collect all program's exit status codes"""
    #Exit codes
    OK = 0
    INPUT_ERROR = 1
    #Template to provide more details to the user on wrong usage
    INPUT_WARNING_TEMPLATE = """\nMissing option or  operand for option '{0}'.\nTry --help for more information."""

    INPUT_WRONG_OPERAND = """\nMode can only take the value install | upgrade | migrate '{0}'.\nTry --help for more information."""

    #Exit code descriptions
    OK_DESCRIPTION = 'if Succes'
    INPUT_ERROR_DESCRIPTION = 'if some of the command arguments is not valid'

class UserInput:
    """Store data provided by the user"""

    command_args    = None
    mode  = None
    imm_file = None
    verbose_mode    = False

    def __init__(self, arguments):
        """Initialize parameters with the command argument list"""
        self.command_args = arguments
    
    def __del__(self):
        self.command_args = []

    class Options:
        """Collects all command options"""
        MAX_COMMAND_ARGUMENTS = 17

        MODE = 'm'
        MODE_LONG = 'mode'
        MODE_HELP = 'install|upgrade|migrate'
        MODE_HELP_DESCRIPTION = 'Exact mode name: install|Upgrade|migrate'

        IMM_FILE = 'i'
        IMM_FILE_LONG = 'IMM DUMP FILE PATH'
        IMM_FILE_HELP = 'immdump.xml'
        IMM_FILE_HELP_DESCRIPTION = 'IMM DUMP FILE PATH E.g: immdump.xml'

        HELP = 'h'
        HELP_LONG = 'help'
        HELP_DESCRIPTION = 'display this help and exit'
        
        VERBOSE = 'v'
        VERBOSE_LONG = 'verbose'
        VERBOSE_DESCRIPTION = 'enable verbose mode'

        SHORT_OPTION_ARGUMENT_REQUIRED = ':'
        LONG_OPTION_ARGUMENT_REQUIRED = '='

        SHORT_OPTION_LIST = MODE + SHORT_OPTION_ARGUMENT_REQUIRED + \
                            IMM_FILE + SHORT_OPTION_ARGUMENT_REQUIRED + \
                            HELP + VERBOSE

        LONG_OPTION_LIST = [MODE_LONG+LONG_OPTION_ARGUMENT_REQUIRED, \
                            IMM_FILE_LONG+LONG_OPTION_ARGUMENT_REQUIRED, \
                            HELP_LONG+LONG_OPTION_ARGUMENT_REQUIRED, \
                            HELP_LONG, VERBOSE_LONG]

    def parse(self):
        """Parse command line arguments and set connection data"""
        try:
            opts, args = getopt.getopt(self.command_args, UserInput.Options.SHORT_OPTION_LIST, UserInput.Options.LONG_OPTION_LIST)
        except getopt.GetoptError as err:
            raise RuntimeError(err)
        if len(opts) ==  0 :
            print "\nInvalid options specified\n\nTry --help for more options"
            sys.exit(ExitStatus.INPUT_ERROR)
        for option, value in opts:
            if option in ('-' + UserInput.Options.HELP, '--' + UserInput.Options.HELP_LONG):
                self.usage()
                sys.exit(ExitStatus.OK)
            if option in ('-' + UserInput.Options.VERBOSE, '--' + UserInput.Options.VERBOSE_LONG):
                self.verbose_mode = True

            elif option in ('-' + UserInput.Options.MODE, '--' + UserInput.Options.MODE_LONG):
                if len(value) == 0:
                    raise Warning(ExitStatus.INPUT_WARNING_TEMPLATE.format('-%s|--%s' % (UserInput.Options.MODE, UserInput.Options.MODE_LONG)))
                self.mode = value
                if self.mode.lower() != "install"  and self.mode.lower() != "upgrade" and self.mode.lower() != "migrate" :
                    raise Warning(ExitStatus.INPUT_WRONG_OPERAND.format('-%s|--%s' % (UserInput.Options.MODE, UserInput.Options.MODE_LONG)))
                if self.mode.lower() == 'upgrade'or self.mode.lower() == 'migrate':
                    if len(opts) == 1:
                        raise Warning(ExitStatus.INPUT_WARNING_TEMPLATE.format('-%s|--%s' % (UserInput.Options.IMM_FILE, UserInput.Options.IMM_FILE_LONG)))
                        sys.exit(ExitStatus.INPUT_ERROR)
            elif option in ('-' + UserInput.Options.IMM_FILE, '--' + UserInput.Options.IMM_FILE_LONG):
                if len(value) == 0:
                    raise Warning(ExitStatus.INPUT_WARNING_TEMPLATE.format('-%s|--%s' % (UserInput.Options.IMM_FILE, UserInput.Options.IMM_FILE_LONG)))
                self.imm_file = value
            else:
                # NOTE: if an option does not exist getopt fails and raises RuntimeError exception
                #       This branch is for options present in the lists UserInput.Options.SHORT_OPTION_LIST and LONG_OPTION_LIST
                error_description = "Option \"%s\" not implemented yet." % (option)
                raise NotImplementedError(error_description)

   

    def usage(self):
        usage_output = 'Usage: {0} OPTION...\n{1}\n\n{2:40}{3}\n{4:40}{5}\n{6:40}{7}\n{8:40}{9}'.format(sys.argv[0],
            ('Generates the campaign for all the modes'),
            (('  -%s, --%s=%s') % (UserInput.Options.MODE, UserInput.Options.MODE_LONG, UserInput.Options.MODE_HELP)),
            UserInput.Options.MODE_HELP_DESCRIPTION,
            (('  -%s, --%s=%s') % (UserInput.Options.IMM_FILE, UserInput.Options.IMM_FILE_LONG, UserInput.Options.IMM_FILE_HELP)),
            UserInput.Options.IMM_FILE_HELP_DESCRIPTION,
            (('  -%s, --%s') % (UserInput.Options.HELP, UserInput.Options.HELP_LONG)),
            UserInput.Options.HELP_DESCRIPTION,
            (('  -%s, --%s') % (UserInput.Options.VERBOSE, UserInput.Options.VERBOSE_LONG)),
            UserInput.Options.VERBOSE_DESCRIPTION)

        exit_status_description = 'Exit status:\n   {0:5}{1},\n   {2:5}{3}'.format(('%i' % ExitStatus.OK), ('%s' % ExitStatus.OK_DESCRIPTION),
           ('%i' % ExitStatus.INPUT_ERROR), ('%s' % ExitStatus.INPUT_ERROR_DESCRIPTION))

        example_usage = """Example:\n  {0} -m install|upgrade|migrate -i immdump.xml \n""".format(sys.argv[0])

        print('\n' + usage_output + '\n' + example_usage + '\n' + exit_status_description)



############################################################################################################
def fetchPlugins():
        """Parse command line arguments and set connection data"""
        dp_repo='../../workspace/DP-repo/'
        dst='./'
        result = 0

        names = os.listdir(dp_repo)
        for name in names:
                src = os.path.join(dp_repo, name)
                if os.path.isdir(src):
                        plugin_folder = os.path.join(src, 'csm/plugin')
                        if os.path.isdir(plugin_folder):
                                cmd = 'cp -rf ' + plugin_folder + ' ' + dst
                                #returns the encoded process exit value
                                cmdResult = os.system(cmd)                        
                                if cmdResult != 0:
                                        print "[ERROR] Command failed [RC: <" + str(cmdResult) + ">]: " + cmd
                                        result = cmdResult
                else:
                        print "[INFO] ignore: " + dp_repo + name

        return result


############################################################################################################
def generateTargetConfiguration(mode,imm_dump):
        tcg = './tcg/bin/tcg'
        cms_ws = '../../workspace/csm-ws/'
        config_base = 'node_config/config_base'
        node_mapping = 'node_config/node-mapping.txt'

        pluginFolder = os.path.abspath(".")
        cmdResult = 1
        if mode.lower() == "install":
            tcgCommand = tcg + ' -o -dp ' + cms_ws + ' -d output -p ' + pluginFolder
        if mode.lower() == "upgrade":
            result = os.path.exists(imm_dump)
            if result == False :
                print "[ERROR] Please copy the IMM DUMP file from node to node_config folder"
                return cmdResult
            result = os.path.exists(config_base)
            if result == False:
                print "[ERROR] Please copy the config_base file from node to node_config folder"
                return cmdResult        
            tcgCommand = tcg + ' -o -dp ' + cms_ws + ' -d output -p ' + pluginFolder + ' -i '+imm_dump+' -cb ' + config_base +' -n '+node_mapping
        if mode.lower() == "migrate":
            result = os.path.exists(imm_dump)
            if result == False :
                print "[ERROR] Please copy the IMM DUMP file from node to node_config folder"
                return cmdResult
            tcgCommand = tcg + ' -o -dp ' + cms_ws + ' -d output -p ' + pluginFolder + ' -i '+imm_dump+' -n '+node_mapping


        if os.path.isdir(cms_ws):
                print "[INFO] " + tcgCommand
                cmdResult = os.system(tcgCommand)
                if cmdResult != 0:
                        print "[ERROR] TCG command failed [RC: <" + str(cmdResult) + ">]"
        else:
                print "[ERROR] Cannot find CSM WORKSPACE: " + os.path.abspath(cms_ws)
        return cmdResult

############################################################################################################
def fetchCampaign(mode):
        sdpFolder = "./output/target-config/campaign-bundles"
        files = os.listdir(sdpFolder)
        tmp = os.path.abspath('./tmp/')
        os.system('mkdir ' + tmp)
        cmdResult = 1
        for sdp in files:
                sdpFile = os.path.abspath(sdpFolder + '/' + sdp)
                print "found " + sdpFile
                untarCmd = 'tar -xvzf ' + sdpFile + ' -C ' + tmp
                print "Executing " + untarCmd
                cmdResult = os.system(untarCmd)
                if cmdResult == 0:
                        cmdResult = os.system('mv -f ./tmp/campaign.template.xml'+' ./'+mode.lower()+'.campaign.template.xml')
                        if cmdResult == 0:
                                print "[INFO] Campaign generated: "+mode.lower()+".campaign.template.xml"
                        else:
                                print "[ERROR] Move Command failed [RC: <" + str(cmdResult) + ">]"
        return cmdResult

############################################################################################################
def clean():
        tmp = os.path.abspath('./tmp')
        out = os.path.abspath('./output')
        plugins = os.path.abspath('./plugin')

        os.system(' rm -rf ' + tmp)
        os.system(' rm -rf ' + out)
        os.system(' rm -rf ' + plugins)
        

############################################################################################################
def main():
    """Command logic.
    """
   
    cmd_input = UserInput(sys.argv[1:])
    try:
        cmd_input.parse()
    except (Warning, NotImplementedError) as warn:
        print("%s: %s" % (warn.__class__.__name__, warn))
        sys.exit(ExitStatus.INPUT_ERROR)
    except (RuntimeError, ValueError) as err:
        cmd_input.usage()
        sys.exit(ExitStatus.INPUT_ERROR)
 
    #
    # Command Logic
    #
    if fetchPlugins() == 0:
        print "[INFO] CoreMW plugins fetched"
        if generateTargetConfiguration(cmd_input.mode,cmd_input.imm_file) == 0:
                print "[INFO] campaign generated"
                if fetchCampaign(cmd_input.mode) == 0:
                        clean()

    sys.exit(0)

############################################################################################################
main()  


