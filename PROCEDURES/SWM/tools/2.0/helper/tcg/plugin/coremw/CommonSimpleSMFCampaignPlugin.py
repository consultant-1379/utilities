import os
from tcg import SMFCampaignPlugin

class CommonSimpleSMFCampaignPlugin(SMFCampaignPlugin):
    def __init__(self, commands, upgradeCommands = None):
        self.commands = commands
        self.upgradeCommands = upgradeCommands
        super(CommonSimpleSMFCampaignPlugin, self).__init__()

    def getCliActionAtCampInit(self):
        result = []
        if self.getCTAction() == SMFCampaignPlugin.CT_ACTION_INSTALL:
            ctRoot = self.getCTRootDirectory()
            for cmd in self.commands:
                doCliCommand = os.path.join("$OSAFCAMPAIGNROOT", ctRoot, "scripts", cmd)
                t = ((doCliCommand, None), ("/bin/true", None), None)
                result.append(t)
        if self.getCTAction() == SMFCampaignPlugin.CT_ACTION_UPGRADE:
            if self.upgradeCommands:
                ctRoot = self.getCTRootDirectory()
                for cmd in self.upgradeCommands:
                    doCliCommand = os.path.join("$OSAFCAMPAIGNROOT", ctRoot, "scripts", cmd)
                    t = ((doCliCommand, None), ("/bin/true", None), None)
                    result.append(t)
        return result
