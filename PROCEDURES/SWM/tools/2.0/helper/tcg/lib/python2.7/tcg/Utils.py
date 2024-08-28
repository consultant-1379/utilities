import os
import errno
from utils.logger_tcg import tcg_error

NON_MANAGED_CT_IDENTIFIER = "cdf-non-managed-ct-identifier"


def mkdir_safe(path):
    try:
        os.makedirs(path)
    except OSError as e:
        if e.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            tcg_error("Failed to create directory %s: %s" % (path, str(e)))

def isNonManagedCT(ct):
    envs = ct.getsaAmfCtDefCmdEnv()
    return len(envs) > 0 and envs[0] == NON_MANAGED_CT_IDENTIFIER

def getExactMatchPattern(dn):
    return ("^" + dn + "$").replace("\,", "\\\\,")
