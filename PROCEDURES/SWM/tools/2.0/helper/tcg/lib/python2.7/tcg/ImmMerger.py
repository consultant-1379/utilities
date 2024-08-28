from utils.logger_tcg import tcg_error
import ImmHelper
import xml.dom.minidom

class ImmAttribute(object):
    def __init__(self, name):
        self._name = name
        self._values = []

    def addValue(self, value):
        self._values.append(value)

class ImmObject(object):
    def __init__(self, _class):
        self._class = _class
        self._dn = None
        self._attributes = []

    def getDn(self):
        return self._dn

    def getParentDn(self):
        return ImmHelper.getParentDn(self._dn)

    def setDn(self, dn):
        self._dn = dn

    def addAttribute(self, attr):
        self._attributes.append(attr)

    def parseXML(self, node):
        dns = node.getElementsByTagName("dn")
        if len(dns) != 1:
            tcg_error("object has " + str(len(dns)) + " dn(s) but it should have one")
        self.setDn(dns[0].childNodes[0].nodeValue)
        for attribute in node.getElementsByTagName("attr"):
            names = attribute.getElementsByTagName("name")
            if len(names) != 1:
                tcg_error("object attribute has " + str(len(names)) + " name(s) but it should have one")
            name = names[0].childNodes[0].nodeValue
            attr = ImmAttribute(name)
            self.addAttribute(attr)
            for value in attribute.getElementsByTagName("value"):
                if len(value.childNodes) > 0:
                    attr.addValue(value.childNodes[0].nodeValue)

    def writeXML(self, parent, doc):
        obj = doc.createElement("object")
        parent.appendChild(obj)
        obj.setAttribute("class", self._class)
        dn = doc.createElement("dn")
        obj.appendChild(dn)
        dn.appendChild(doc.createTextNode(self._dn))
        for attribute in self._attributes:
            attr = doc.createElement("attr")
            obj.appendChild(attr)
            name = doc.createElement("name")
            attr.appendChild(name)
            name.appendChild(doc.createTextNode(attribute._name))
            if len(attribute._values) == 0:
                value = doc.createElement("value")
                attr.appendChild(value)
            else:
                for v in attribute._values:
                    value = doc.createElement("value")
                    attr.appendChild(value)
                    value.appendChild(doc.createTextNode(v))

class ImmMerger(object):
    def __init__(self):
        self._objects = {}
        self._objectList = []

    def isEmpty(self):
        return len(self._objects.keys()) == 0

    def mergeXML(self, fileName):
        doc = xml.dom.minidom.parse(fileName)
        root = doc.documentElement
        for _obj in root.getElementsByTagName("object"):
            _class = _obj.getAttribute("class")
            obj = ImmObject(_class)
            obj.parseXML(_obj)
            self.addObject(obj)

    def merge(self, other):
        for (dn, obj) in other._objects.items():
            self.addObject(obj)

    def addObject(self, obj):
        if obj.getDn() in self._objects.keys():
            tcg_error("Multiple instance of object %s exists" % (obj.getDn()))
        self._objects[obj.getDn()] = obj
        self._objectList.append(obj)

    def writeXML(self, fileName, partial = False):
        doc = xml.dom.minidom.Document()
        root = doc.createElement("imm:IMM-contents")
        root.setAttribute("xmlns:imm", "http://www.saforum.org/IMMSchema")
        root.setAttribute("xmlns:xsi", "http://www.w3.org/2001/XMLSchema-instance")
        root.setAttribute("xsi:noNamespaceSchemaLocation", "SAI-AIS-IMM-XSD-A.01.01.xsd")
        doc.appendChild(root)
        writtenObjects = []
        while True:
            written = False
            for obj in self._objectList:
                if obj.getDn() in writtenObjects:
                    continue
                parent = obj.getParentDn()
                # write the object if
                # - the object has no parent
                # - the parent is already written
                # - this is a partial config and we do not care about the order at all
                # - the parent object is NOT in the original object set (this last condition is a HACK and should be removed
                # when the IMM object handling is properly designed...)
                if parent == "" or parent in writtenObjects or partial or (parent not in self._objects.keys()):
                    written = True
                    writtenObjects.append(obj.getDn())
                    obj.writeXML(root, doc)
            if not written:
                if len(writtenObjects) != len(self._objects.keys()):
                    tcg_error("Failed to write merged xml (%s) due to missing parent object(s)" % (fileName))
                else:
                    break;
        output = open(fileName, "w")
        doc.writexml(output, addindent = "  ", newl = "\n")
        output.close()
