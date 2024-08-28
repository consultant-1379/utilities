from utils.logger_tcg import tcg_error
import ImmHelper
import xml.dom.minidom

class ImmAttribute(object):
    def __init__(self):
        self._name = None
        self._type = None
        self._category = None
        self._flags = []
        self._defaultValue = None

    def addChild(self, name, value, parentNode, doc):
        if value == None:
            return
        child = doc.createElement(name)
        child.appendChild(doc.createTextNode(value))
        parentNode.appendChild(child)

    def writeXML(self, root, doc, parent):
        parentNode = doc.createElement(parent)
        self.addChild("name", self._name, parentNode, doc)
        self.addChild("type", self._type, parentNode, doc)
        self.addChild("category", self._category, parentNode, doc)
        for f in self._flags:
            self.addChild("flag", f, parentNode, doc)
        self.addChild("default-value", self._defaultValue, parentNode, doc)
        root.appendChild(parentNode)

class ImmClass(object):
    def __init__(self, name):
        self._name = name
        self._category = None
        self._rdn = None
        self._attributes = []

    def writeXML(self, root, doc):
        classNode = doc.createElement("class")
        classNode.setAttribute("name", self._name)
        root.appendChild(classNode)
        categoryNode = doc.createElement("category")
        categoryNode.appendChild(doc.createTextNode(self._category))
        classNode.appendChild(categoryNode)
        self._rdn.writeXML(classNode, doc, "rdn")
        for attr in self._attributes:
            attr.writeXML(classNode, doc, "attr")

class ImmClassMerger(object):
    def __init__(self):
        self._currentClass = None
        self._currentAttribute = None
        self._current = None # used for category parsing
        self._classes = {}

    def parseChildren(self, node):
        for child in node.childNodes:
            if child.nodeType == xml.dom.Node.ELEMENT_NODE:
                self.parseNode(child)

    def parseIMMcontents(self, node):
        self.parseChildren(node)

    def parseClass(self, node):
        className = node.getAttribute("name")
        self._currentClass = self._current = ImmClass(className)
        if className in self._classes.keys():
            tcg_error("Duplicated class (%s) found while merging IMM class definitions" % (className))
        self._classes[className] = self._currentClass
        self.parseChildren(node)

    def parseCategory(self, node):
        category = node.childNodes[0].data
        self._current._category = category

    def parseName(self, node):
        name = node.childNodes[0].data
        self._currentAttribute._name = name

    def parseType(self, node):
        _type = node.childNodes[0].data
        self._currentAttribute._type = _type

    def parseFlag(self, node):
        flag = node.childNodes[0].data
        self._currentAttribute._flags.append(flag)

    def parseRdn(self, node):
        self._currentClass._rdn = self._current = ImmAttribute()
        self._currentAttribute = self._currentClass._rdn
        self.parseChildren(node)

    def parseAttr(self, node):
        self._currentAttribute = self._current = ImmAttribute()
        self._currentClass._attributes.append(self._currentAttribute)
        self.parseChildren(node)

    def parseDefaultValue(self, node):
        defaultValue = node.childNodes[0].data
        self._currentAttribute._defaultValue = defaultValue

    def parseNode(self, node):
        name = node.nodeName
        if  name == "imm:IMM-contents":
            self.parseIMMcontents(node)
        elif  name == "class":
            self.parseClass(node)
        elif  name == "category":
            self.parseCategory(node)
        elif  name == "rdn":
            self.parseRdn(node)
        elif  name == "name":
            self.parseName(node)
        elif  name == "type":
            self.parseType(node)
        elif  name == "flag":
            self.parseFlag(node)
        elif  name == "attr":
            self.parseAttr(node)
        elif  name == "default-value":
            self.parseDefaultValue(node)
        else:
            tcg_error("Unsupported element: " + name)

    def mergeXML(self, fileName):
        doc = xml.dom.minidom.parse(fileName)
        root = doc.documentElement
        self.parseNode(root)

    def writeXML(self, fileName):
        doc = xml.dom.minidom.Document()
        root = doc.createElement("imm:IMM-contents")
        root.setAttribute("xmlns:imm", "http://www.saforum.org/IMMSchema")
        root.setAttribute("xmlns:xsi", "http://www.w3.org/2001/XMLSchema-instance")
        root.setAttribute("xsi:noNamespaceSchemaLocation", "SAI-AIS-IMM-XSD-A.01.01.xsd")
        doc.appendChild(root)
        for c in self._classes.values():
            c.writeXML(root, doc)
        output = open(fileName, "w")
        doc.writexml(output, addindent = "  ", newl = "\n")
        output.close()

    def isEmpty(self):
        return len(self._classes) == 0
