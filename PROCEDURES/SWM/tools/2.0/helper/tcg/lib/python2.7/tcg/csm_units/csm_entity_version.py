from tcg.utils.logger_tcg import tcg_error
import logging
import re

VERSION_TYPE_DOTTED = "dotted-version"
VERSION_TYPE_HASH = "hash-version"
VERSION_TYPE_AUTO = "auto-version"

class CSMEntityVersion():
    """
    A general class representing the version of CSM entities
    """
    def __init__(self, version_string=None, owner_uid=None, version_type=VERSION_TYPE_AUTO):
        if version_string == None or owner_uid == None:
            self.valid = False
            self.version_string = "uninitialized"
            self.owner_uid = "uninitialized"
            self.major = None
            self.minor = None
            self.patch = None
            self.verif_level = None
            self.extensions = None
            self.version_type = None
        else:
            self.setVersion(version_string, owner_uid, version_type=version_type)

    def setVersion(self, version_string, owner_uid, version_type=VERSION_TYPE_AUTO):
        """
        This function is generating version object parsed from
        a string. Invalid version formats are captured.
        """
        self.valid = False
        self.version_type = version_type
        self.version_string = version_string

        # All warnings in the following conditionals are workarounds while components adjust their
        # model to the requirements. Upon removal the invocation should be fixed so that every csm
        # entity type calls setVersion with the appropriate version type. For now comp and sys are
        # dotted version which gets them validated, but func/serv/role is auto, so they get only a
        # if the version is invalid. Which means it is also possible to have hashed func version and
        # dotted serv/role version.
        if version_string == None or owner_uid == None:
            logging.debug("Cannot create version object with missing version information for uid %s. Ignoring." %owner_uid)
            return

        if self.version_type == VERSION_TYPE_AUTO:
            if re.search("^[0123456789abcdef]+$", self.version_string):
                self.version_type = VERSION_TYPE_HASH
            elif re.search("\d+\.\d+\.\d+(-\d+(\..*)?)?", self.version_string):
                self.version_type = VERSION_TYPE_DOTTED
            else:
                logging.warning("Attempt to create version object with unrecognized version format: %s" % self.version_string)
                return

        if self.version_type == VERSION_TYPE_HASH:
            if not re.search("^[0123456789abcdef]+$", self.version_string):
                #tcg_error("Attempt to create hash version with invalid hash string: %s" % self.version_string)
                logging.warning("Attempt to create hash version with invalid hash string: %s" % self.version_string)
                return
            else:
                self.valid = True
                return

        if self.version_type == VERSION_TYPE_DOTTED:
            if not owner_uid:
                tcg_error("Attempt to create version object whithout owner csm entity")
            self.owner_uid = owner_uid
            if not version_string:
                tcg_error("Attempt to create version object without version string for csm entity %s" % self.owner_uid)

            dash_tokens = version_string.split("-", 1)
            if len(dash_tokens) < 1:
                tcg_error("Invalid version format for entity %s: %s" % (owner_uid, version_string))
            first_tokens = dash_tokens[0].split(".")
            if len(first_tokens) != 3:
                tcg_error("Invalid version format for entity %s: %s" % (owner_uid, version_string))
            try:
                self.major = int(first_tokens[0])
                self.minor = int(first_tokens[1])
                self.patch = int(first_tokens[2])
            except ValueError:
                tcg_error("Invalid version format for entity %s: %s" % (owner_uid, version_string))
            if len(dash_tokens) > 1:
                second_tokens = dash_tokens[1].split(".", 1)
                if len(second_tokens) < 1:
                    tcg_error("Invalid version format for entity %s: %s" % (owner_uid, version_string))
                try:
                    self.verif_level = int(second_tokens[0])
                except ValueError:
                    tcg_error("Invalid version format for entity %s: %s" % (owner_uid, version_string))
                if len(second_tokens) > 1:
                    self.extensions = second_tokens[1]
                else:
                    self.extensions = None
            else:
                self.verif_level = None
                self.extensions = None

            self.valid = True

    def isValid(self):
        return self.valid

    def __str__(self):
        if self.valid:
            return self.version_string
        else:
            return "INVALID_VERSION"

    def getVersionString(self):
        return self.version_string

    def getVersionType(self):
        return self.version_type

    def dump(self):
        """
        Dump the contents of this version object
        """
        if self.valid:
            if self.version_type == VERSION_TYPE_DOTTED:
                logging.debug("Version type: dotted    %s.%s.%s verfication level: %s extensions: %s" % (self.major, self.minor, self.patch, self.verif_level, self.extensions))
            else:
                logging.debug("Version type: hashed    %s", self.version_string)
        else:
            logging.debug("This csm entity version is invalid: %s" % self.version_string)

    def compare(self, other):
        """
        Compare this version object with another. If this is the older one
        the return value is -1. If this is younger the return value is 1.
        Otherwise it is 0.
        """
        if self.version_type == VERSION_TYPE_DOTTED and other.version_type == VERSION_TYPE_DOTTED:
            if not self.valid:
                tcg_error("Trying to compare invalid version object %s for entity %s" % (self.version_string, self.owner_uid))
            if not other.valid:
                tcg_error("Trying to compare against invalid version object %s for entity %s" % (other.version_string, other.owner_uid))
            """
            Major/minor/patch parts are mandatory. Simple integer comparison
            ex:    1.1.1 < 2.1.1,    1.1.3 > 1.1.1,    1.2.1 > 1.1.45
            """
            if self.major < other.major:
                return -1
            if self.major > other.major:
                return 1
            if self.minor < other.minor:
                return -1
            if self.minor > other.minor:
                return 1
            if self.patch < other.patch:
                return -1
            if self.patch > other.patch:
                return 1
            """
            Verification level and extensions are optional. We should do an integer
            comparison and a string comparison if they are present. If they are not
            present the shorter version will be the older.
            ex:    1.1.1-1.1 < 1.1.1-1.2,    1.1.1-1.1 < 1.1.1-1.11,    1.1.1-1.a < 1.1.1-1.a1
                   1.1.1 < 1.1.1-1.2,        1.1.1-4 < 1.1.1-1.f        1.1.1-1.ab > 1.1.1-1.b
            """
            """
            According to artf771781 TCG should ignore the optional part VerifLevel and Extension
            The code is not removed for the case that this part should be considered again.
            if self.verif_level:
                if not other.verif_level:
                    return 1
                if self.verif_level < other.verif_level:
                    return -1
                if self.verif_level > other.verif_level:
                    return 1
                if self.extensions:
                    if not other.extensions:
                        return 1
                    if self.extensions < other.extensions:
                        return -1
                    if self.extensions > other.extensions:
                        return 1
                elif other.extensions:
                    return -1
            elif other.verif_level:
                return -1
            """
            return 0

        else:
            tcg_error("Comparison only supported between dotted versions.")
