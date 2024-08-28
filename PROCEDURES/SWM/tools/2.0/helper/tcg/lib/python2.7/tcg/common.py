import sys
import re
import os
import logging
from inspect import getframeinfo, stack
from utils.logger_tcg import tcg_error


def printNiceDict(dictionary):
    for (key, value) in dictionary.iteritems():
        print key, ":", len(value), [v.getName() for v in value]
        print

# ----------------------------------------------------------------------------------------------------------------------

def printNice(o, indent = 1, logging_type=logging.debug):
    i = "    "
    if isinstance(o, list):
        for v in o:
            printNice(v, indent, logging_type)
    elif isinstance(o, dict):
        for k,v in o.items():
            logging_type(i * indent + k + ":")
            printNice(v, indent + 1, logging_type)
    elif isinstance(o, tuple):
        logging_type(i * indent)
        for v in o:
             logging_type("%-20s" % v)
        logging_type("\n")
    else:
        logging_type(i * indent + str(o))

# -----------------------------------------------------------------------------------------------------------------

def error(msg):
    """error() is deprecated in favor of tcg_error()."""
    caller = getframeinfo(stack()[1][0])
    filename = os.path.basename(caller.filename)
    extrainfo = 'Original error from %s: %d - ' % (filename, caller.lineno)
    tcg_error(extrainfo+msg)

# -------------------------------------------------------------------------------

def assertNone(value, errmsg):
    if value is None:
        tcg_error(errmsg)

# -------------------------------------------------------------------------------


def assertIsKey(value, dictionary, errmsg):
    if value in dictionary.keys():
        tcg_error(errmsg)

# ------------------------------------------------------------------------------


def updateDictionary(inputDict = None, referenceDict = None):
    '''
    Updates the inputDict  with the referenceDict only if the key exists in both the dictionaries
    '''
    for key, value in referenceDict.iteritems() :
        if key in inputDict.keys() :
            inputDict[key] = value


def convert_s_and_ms_to_number(input_time):
    '''
    If the received input_time is a number followed by the time unit "s" (for
    seconds) or "ms" (for milliseconds), this function returns a number
    expressing the input_time in nanoseconds

    convert_s_and_ms_to_number("30 s")     = 30.000.000.000 # nanoseconds
    convert_s_and_ms_to_number("30000 ms") = 30.000.000.000 # nanoseconds

    If the received input_time is not a number followed by "s" or "ms" the
    function raises an exception
    '''

    convertedValue = None

    matcher = re.match("(\d+)\s*(s|ms)\s*", input_time, re.IGNORECASE)
    if matcher:
        value = matcher.group(1)
        unit = matcher.group(2)
        if unit == 's':
            convertedValue = int(value) * pow(10, 9) # 1 second = 1.000.000.000 nanoseconds
        elif unit == 'ms':
            convertedValue = int(value) * pow(10, 6) # 1 ms = 1.000.000 nanoseconds
    else:
        tcg_error("%s - wrong input. Only numbers in s or ms can be changed" % input_time)

    return convertedValue


def validate_is_number(input_number):
    input_number = str(input_number)
    if re.match("\d+$", input_number, re.IGNORECASE):
        return input_number
    else:
        tcg_error("wrong input. Expected number, received: %s" % input_number)


class Prioritize(object):
    '''
    Class which convert dependency relationship to priority level
    '''
    def __init__(self):
        self._priorityLevel = {}

    def getPrioritizeLevel(self, item):
        if item in self._priorityLevel:
            return self._priorityLevel[item]
        return -1

    def reset(self):
        self._priorityLevel.clear()

    @staticmethod
    def _rmItemRelationship(relationship, item):
        rmRelation = set([])
        for (f, t) in relationship:
            if t == item or f == item:
                rmRelation.add((f, t))
        relationship -= rmRelation

    def convertFrom(self, dependRelations):
        """
        Return true when convert is succeed.
        The priority level is stored in _priorityLevel.
        Input args:
        dependRelations - Set of dependency relationship.
            example: set([(A, B), (A, C)]) means A depends on B and C.
        """
        self.reset()
        curLev = 0
        depent = dependRelations.copy()
        todo = set([])
        for (f, t) in depent:
            todo.add(f)
            todo.add(t)
        while todo:
            exclude = set([])
            for (f, t) in depent:
                exclude.add(f)
            curLevItem = todo - exclude
            if not curLevItem:
                logging.error("dependency relationship error. Circular dependency exist.")
                return False
            for item in curLevItem:
                Prioritize._rmItemRelationship(depent, item)
                self._priorityLevel[item] = curLev
            todo -= curLevItem
            curLev = curLev + 1
        return True
