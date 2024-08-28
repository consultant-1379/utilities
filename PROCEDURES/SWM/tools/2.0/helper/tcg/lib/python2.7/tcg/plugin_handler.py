import sys
import imp
import os
import logging
from utils.logger_tcg import tcg_error
from SystemModels import SystemModels


def loadPluginsUsingVDicosHardcodedDependency(the_filter):
    """
    This is the old way of loading plugins containing the hardcoded dependency
    for vDicos plugings.
    TODO: Remove this function when the old campaign generator plugin interface is fully
    removed from the system. Instead use the regular "loadPlugins" function that
    does not contain any hardcoded dependency
    """
    logging.debug("Loading plugins...")

    pluginModules = {}

    pluginModulePaths = {}

    containsAnyUnit = False

    for service in SystemModels.targetCSMModel.system.getServices():
        containsAnyUnit = True

        relativePluginPath = service.getPlugin()

        if relativePluginPath:
            pluginModulePaths[service.getUid()] = os.path.join(service.getPluginsBaseDir(), relativePluginPath)

    for component in SystemModels.targetCSMModel.system.getComponents():
        containsAnyUnit = True

        relativePluginPath = component.getPlugin()

        if relativePluginPath :
            pluginModulePaths[component.getUid()] = os.path.join(component.getPluginsBaseDir(), relativePluginPath)

    if not containsAnyUnit:
        logging.debug("The specified yaml model does not contain any components or services")
        return pluginModules

    # Workaround for plugin dependencies
    # need to remove it once plugin dependencies are supported

    unitId = "CXC1731651"

    if unitId in pluginModulePaths:
        unitPluginDir = pluginModulePaths[unitId]
        pythonDir = getPythonDir(unitPluginDir)

        if not pythonDir :
            tcg_error("Error: Plugin path %s referenced in %s not found" % (unitPluginDir, unitId))

        logging.debug("Looking for Python modules in %s (%s)" % (unitId, unitPluginDir))

        origPathLength = len(sys.path)
        sys.path.append(pythonDir)
        logging.debug("  Python path=" + ":".join(sys.path))

        for module in getPluginsInDirectory(pythonDir, the_filter):
            pluginModules[unitId] = module
            logging.debug("Plugin for %s is loaded" % unitId)

        sys.path = sys.path[:origPathLength]

    for unitId in pluginModulePaths:
        if unitId != "CXC1731651":
            unitPluginDir = pluginModulePaths[unitId]
            pythonDir = getPythonDir(unitPluginDir)

            if not pythonDir :
                tcg_error("Error: Plugin path %s referenced in %s not found" % (unitPluginDir, unitId))

            logging.debug("Looking for Python modules in %s (%s)" % (unitId, unitPluginDir))

            origPathLength = len(sys.path)
            sys.path.append(pythonDir)
            logging.debug("  Python path=" + ":".join(sys.path))

            for module in getPluginsInDirectory(pythonDir, the_filter):
                pluginModules[unitId] = module
                logging.debug("Plugin for %s is loaded" % unitId)

            sys.path = sys.path[:origPathLength]

    return pluginModules


def loadPlugins(the_filter):
    logging.debug("Loading plugins...")

    pluginModules = {}

    pluginModulePaths = {}

    containsAnyUnit = False

    # plugins at service level are deprecated
    for service in SystemModels.targetCSMModel.system.getServices():
        containsAnyUnit = True

        relativePluginPath = service.getPlugin()

        if relativePluginPath:
            pluginModulePaths[service.getUid()] = os.path.join(service.getPluginsBaseDir(), relativePluginPath)

    for component in SystemModels.targetCSMModel.system.getComponents():
        containsAnyUnit = True

        relativePluginPath = component.getPlugin()

        if relativePluginPath:
            pluginModulePaths[component.getUid()] = os.path.join(component.getPluginsBaseDir(), relativePluginPath)

    if not containsAnyUnit:
        logging.debug("The specified yaml model does not contain any components or services")
        return pluginModules

    for unitId in pluginModulePaths:
        unitPluginDir = pluginModulePaths[unitId]
        pythonDir = getPythonDir(unitPluginDir)

        if not pythonDir:
            tcg_error("Error: Plugin path %s referenced in %s not found" %
                      (unitPluginDir, unitId))

        logging.debug("Looking for Python modules in %s (%s)" %
                      (unitId, unitPluginDir))

        origPathLength = len(sys.path)
        sys.path.append(pythonDir)
        logging.debug("  Python path=" + ":".join(sys.path))

        for module in getPluginsInDirectory(pythonDir, the_filter):
            pluginModules[unitId] = module
            logging.debug("Plugin for %s is loaded" % unitId)

        sys.path = sys.path[:origPathLength]

    return pluginModules

# -------------------------------------------------------------------------------

pythonDirs = ["python%d.%d.%d" % (sys.version_info.major,
                                  sys.version_info.minor,
                                  sys.version_info.micro),
              "python%d.%d" % (sys.version_info.major,
                               sys.version_info.minor),
              "python%d" % (sys.version_info.major,),
              "python"]

# -------------------------------------------------------------------------------


def getPythonDir(unitDirectory):
    """Get the Python directory of the given unit.

    The Python directory considered is  the first one found from the following:
    - lib/pythonX.Y.Z, where X is the major, Y is the minor and Z is the micro
    version
    - lib/pythonX.Y
    - lib/pythonX
    - lib/python

    Returns the path of the directory found, or None if none was found."""
    for the_dir in pythonDirs:
        the_dir = os.path.join(unitDirectory, "lib", the_dir)
        if os.path.isdir(the_dir):
            return the_dir

    return None

# -----------------------------------------------------------------------------


def getPluginsInDirectory(directory, the_filter):
    """Get an iterator over the modules in a directory, that match certain
    criteria."""
    old_dont_write_bytecode = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    for fileName in os.listdir(directory):
        if fileName.endswith(".py"):
            the_file = os.path.join(directory, fileName)
            # For some reason postfixing the plugins with a counter does not work
            # and sometimes one of the plugins overwrite the other, so that has been removed.
            # Postfixing them with the full path of the file seems to work, for now...
            postfix = the_file.replace("/", "_").replace(".", "_")
            module = imp.load_source("plugin%s" % (postfix), the_file)
            if the_filter(module):
                logging.debug("  the_file " + the_file + " is a plugin")
                yield module
    sys.dont_write_bytecode = old_dont_write_bytecode
