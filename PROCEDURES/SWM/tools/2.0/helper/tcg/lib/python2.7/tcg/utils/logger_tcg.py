'''
Created on 28 Feb 2015

@author: ekirven

Logging related functionalities, like default and extended logging are present
in this module
'''

import logging.handlers
import sys
import os
import traceback
from inspect import getframeinfo, stack
from tcg.utils.exceptions import TcgException
from datetime import datetime


class NoErrorFilter(logging.Filter):
    # A special filter is needed for not send error log to stdout
    def filter(self, record):
        return record.levelno < logging.ERROR

class HijackedFormatter(logging.Formatter):
    """
    The extra argument (the dictionary which is used to populate the __dict__
    of the LogRecord) is not allow to clash with the keys used by the logging
    system. Which means you can not overwrite the those keys in logging module.

    HijackedFormatter is use for overwrite the keys which is used by the logging
    system.

    Use HijackedFormatter instead of logging.Formatter for your Logger Handler
    instance, and pass the keys which you want to overwrite in beginning with
    hijack keyword HijackedFormatter.HIJACK_KEYWORD

    For example, if you want to overwrite the filename and lineno, you can pass
    a dictionary like following:
    extra_keys = {
        HijackedFormatter.HIJACK_KEYWORD+'filename' : 'some_filename.py',
        HijackedFormatter.HIJACK_KEYWORD+'lineno' : 12345
    }
    logging.debug('log message', extra = extra_key)
    """
    HIJACK_KEYWORD = 'hijack_'

    def format(self, record):
        hijacked_len = len(self.HIJACK_KEYWORD)
        newdict = {}
        for key in record.__dict__:
            if key.startswith(self.HIJACK_KEYWORD):
                hijacked_key = key[hijacked_len:]
                if len(hijacked_key) <= 0:
                    continue
                newdict[hijacked_key] = record.__dict__[key]
        record.__dict__.update(newdict)
        return logging.Formatter.format(self, record)

    def formatTime(self, record, datefmt=None):
        if datefmt:
            ct = self.converter(record.created)
            s = datefmt.strftime(ct)
        else:
            s = datetime.fromtimestamp(record.created).strftime("%b %d %H:%M:%S.%f")
        return s

def loggingInit(loglevel, dedicated_log_file=None):
    logger = logging.getLogger()
    level = logging.NOTSET
    if loglevel == 'DEBUG':
        level = logging.DEBUG
    elif loglevel == 'INFO':
        level = logging.INFO
    elif loglevel == 'WARNING':
        level = logging.WARNING
    elif loglevel == 'ERROR':
        level = logging.ERROR
    elif loglevel == 'CRITICAL':
        level = logging.CRITICAL

    fmt = 'tcg[%(process)s]: %(levelname)s %(message)s'
    formatter = logging.Formatter(fmt)

    # sysh sends log to a Unix syslog daemon, default level WARNING
    sysh = logging.handlers.SysLogHandler(address='/dev/log')
    sysh.setFormatter(formatter)
    sysh.setLevel(logging.WARNING)

    fmt = '%(asctime)s tcg[%(process)s][%(filename)s:%(lineno)d] %(levelname)s %(message)s'
    formatter = HijackedFormatter(fmt)

    if loglevel != 'NOLOG':
        # stdout sends log to stdout stream, level DEBUG
        stdout = logging.StreamHandler(sys.stdout)
        stdout.setFormatter(formatter)
        if level == logging.NOTSET:
            stdout.setLevel(logging.WARNING)
        else:
            stdout.setLevel(logging.DEBUG)

        noerr = NoErrorFilter()
        stdout.addFilter(noerr)
        # stderr sends log to stderr stream, level ERROR
        stderr = logging.StreamHandler(sys.stderr)
        stderr.setFormatter(formatter)
        stderr.setLevel(logging.ERROR)
        logger.addHandler(stdout)
        logger.addHandler(stderr)

    logger.addHandler(sysh)
    logger.setLevel(level)

    if dedicated_log_file is not None:
        try:
            new_log = logging.handlers.RotatingFileHandler(dedicated_log_file, maxBytes=10*1024*1024, backupCount=5)
        except Exception as e:
            tcg_error("error while creating file log stream: " + str(e))
        else:
            new_log.setFormatter(formatter)
            new_log.setLevel(logging.DEBUG)

        logger.addHandler(new_log)

def tcg_critical(msg):
    """
    Write an error message to stderr and logging it to the log file as an
    "Critical" error, also log the stack to the log file for "debug"

    @param msg: The error message
    """
    caller = getframeinfo(stack()[1][0])
    filename = os.path.basename(caller.filename)
    extra_keys = {
        HijackedFormatter.HIJACK_KEYWORD+'filename' : filename,
        HijackedFormatter.HIJACK_KEYWORD+'lineno' : caller.lineno
    }

    logging.critical(msg, extra = extra_keys)
    logging.debug(traceback.format_stack(), extra = extra_keys)

    raise TcgException(2)

def tcg_error(msg):
    """
    Write an error message to stderr and logging it to the log file as an "error",
    also log the stack to the log file for "debug"

    @param msg: The error message
    """
    caller = getframeinfo(stack()[1][0])
    filename = os.path.basename(caller.filename)
    extra_keys = {
        HijackedFormatter.HIJACK_KEYWORD+'filename' : filename,
        HijackedFormatter.HIJACK_KEYWORD+'lineno' : caller.lineno
    }

    logging.error(msg, extra = extra_keys)
    all_line = traceback.format_stack()
    for line in all_line:
        logging.debug(line.rstrip('\n'), extra = extra_keys)

    raise TcgException(msg)

def trace_enter():
    caller = getframeinfo(stack()[1][0])
    filename = os.path.basename(caller.filename)
    extra_keys = {
        HijackedFormatter.HIJACK_KEYWORD+'filename' : filename,
        HijackedFormatter.HIJACK_KEYWORD+'lineno' : caller.lineno
    }
    logging.debug(">>" + caller.function, extra = extra_keys)

def trace_leave():
    caller = getframeinfo(stack()[1][0])
    filename = os.path.basename(caller.filename)
    extra_keys = {
        HijackedFormatter.HIJACK_KEYWORD+'filename' : filename,
        HijackedFormatter.HIJACK_KEYWORD+'lineno' : caller.lineno
    }
    logging.debug("<<" + caller.function, extra = extra_keys)
