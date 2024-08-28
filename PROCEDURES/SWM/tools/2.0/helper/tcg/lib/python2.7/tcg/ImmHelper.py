from utils.logger_tcg import tcg_error

def unescapeName(name):
    return name.replace("\,",",")

def addQuoteMarker(dn):
    marker = "$$QUOTE_MARKER$$"
    return dn.replace("\,", marker)

def removeQuoteMarker(dn):
    marker = "$$QUOTE_MARKER$$"
    return dn.replace(marker, "\,")

def escapeName(name):
    return removeQuoteMarker(addQuoteMarker(name).replace(",", "\,"))

def getRdn(dn):
    return removeQuoteMarker(addQuoteMarker(dn).split(",", 1)[0])

def getName(dn):
    rdn = getRdn(dn)
    subs = rdn.split("=", 1)
    if (len(subs) == 1):
        return unescapeName(subs[0])
    return unescapeName(subs[1])

def getParentDn(dn, level = 1):
    parents = addQuoteMarker(dn).split(",", level)
    if (len(parents) < level+1):
        return ""
    return removeQuoteMarker(parents[level])

def isParentDn(dn, parent):
    realParent = getParentDn(dn, 1)
    return realParent == parent

def isInSubtree(dn, root):
    while len(dn) != 0:
        if dn == root:
            return True
        dn = getParentDn(dn)
    return False

def splitDn(dn, unescape=True):
    dn = addQuoteMarker(dn)
    parts = dn.split(",")
    parts = map(removeQuoteMarker, parts)
    if unescape:
        parts = map(unescapeName, parts)
    return parts

def validateSingle(value, dn, attrName):
    if value == None or value == "":
        import traceback
        traceback.print_stack()
        tcg_error("attribute " + attrName + " in object " + dn + " has no valid value")

def validateSingleInList(list, dn, attrName):
    if len(list) != 1:
        tcg_error("attribute " + attrName + " in object " + dn + " has " + str(len(list)) + " value(s) when it should have only one")

def validateName(value, dn, attrName):
    pass # cannot validate names in a meaningful way

def validateUint32(value, dn, attrName):
    if value is None or not str(value).isdigit():
        tcg_error("attribute " + attrName + " in object " + dn + " has value " + str(value) + " which is not a valid value for SA_UINT32_T")

def validateTime(value, dn, attrName):
    if value is None or not str(value).isdigit():
        tcg_error("attribute " + attrName + " in object " + dn + " has value " + str(value) + " which is not a valid value for SA_TIME_T")

def validateString(value, dn, attrName):
    pass # cannot validate strings in a meaningful way

def writeSingleAttribute(attrName, attrValue, doc, obj):
    if attrValue == None:
        return
    attr = doc.createElement("attr")
    obj.appendChild(attr)
    name = doc.createElement("name")
    attr.appendChild(name)
    name.appendChild(doc.createTextNode(attrName))
    value = doc.createElement("value")
    attr.appendChild(value)
    value.appendChild(doc.createTextNode(attrValue))

def writeMultiAttributes(attrName, attrValues, doc, obj):
    if len(attrValues) == 0:
        return

    attr = doc.createElement("attr")
    obj.appendChild(attr)
    name = doc.createElement("name")
    attr.appendChild(name)
    name.appendChild(doc.createTextNode(attrName))
    for v in attrValues:
        value = doc.createElement("value")
        attr.appendChild(value)
        value.appendChild(doc.createTextNode(v))
