import PyYaml_3_11
import sys
import tcg.CgtConstants as CgtConstants
import logging
from logger_tcg import tcg_error


class YamlParser(PyYaml_3_11.YAMLObject):

    def __init__(self, nodeList = [], schemaPath = None):

        '''
        Things to be done:

        YAML schema version in the schema file ???
        '''
        self.nodes = nodeList
        self.schemaPath = schemaPath

    _instance = None

    @staticmethod
    def getInstance():
        '''
        Returns instance of Yaml_Parser
        '''
        if not YamlParser._instance :
            YamlParser._instance = YamlParser()

        return YamlParser._instance

    def getNodesByName(self, name = None, filters = {}, inputYaml = None,
                       applyFilterFor = None, recursionFlag = True):
        '''
        The functions searches the inputYaml for the  tagName  given in  name
        Returns the lists of tagNames and its values . filters are used to screens the search..

        ex: In yaml file assume there is tag type  under components then  the argument
               name = components.type
            if there are more than one  component  we can specify component name as
               filters = {name : comp1}
               then function return [type: 'somevalue'] of comp1 component

            if name = componets.sortware.type  we can specify for which we can applyFilter
               through applyFilterFor
               ex: applyFilter = software  , applies filter at software

            If recursionFlag = True the function recursively searches  name  in inner tags of
               inputYaml else checks at outer tags :
        '''
        try:
            yamlStream = PyYaml_3_11.load(open(inputYaml, 'r'))
        except PyYaml_3_11.YAMLError, message:
                tcg_error("In inputyaml :\n %s" % (message))
        if not yamlStream :
            logging.warning('%s is either empty or not a yaml file' % inputYaml)
            return []
        nameList = name.split('.')
        if filters != {} and filters is not None:
            if applyFilterFor not in nameList and applyFilterFor:
                logging.info('%s  is not in %s' % (applyFilterFor, name))
            if len(nameList) == 1 :
                applyFilterFor = name
            elif len(nameList) > 1 and not applyFilterFor:
                logging.warning("Please specify the entity name for which the \
                                filter should be applied to through 'applyFilterFlag'")

        originalFilters = filters
        filters = {}
        dictList = [yamlStream]
        for entry in nameList :
            if entry == applyFilterFor:
               filters = originalFilters
            elif not applyFilterFor:
                filters = {}
            dictList = self._getNodes_1(name = entry, filters = filters, dictList = dictList,
                                        recursionFlag = recursionFlag)
            filters = {}

        self._stringify_numbers(dictList)
        return dictList

    def getNodesByName2(self, name = None, filters = {}, inputDictList = None,
                        applyFilterFor = None, recursionFlag = True):
        '''
        The functions searches the inputDictList(list of dictionaries) for the  tagName  given in name
        Returns the lists of tagNames and its values . filters are used to screens the search.

        ex: In inputDictList assume there is tag type  under components then  the argument
               name = components.type
            if there are more than one  component  we can specify component name as
               filters = {name : comp1}
               then function return [type: 'somevalue'] of comp1 component

            if name = componets.sortware.type  we can specify for which we can applyFilter
               through applyFilterFor
               ex: applyFilter = software  , applies filter at software

            If recursionFlag = True the function recursively searches  name  in inner tags of
               inputDictList else checks at outer tags

        '''
        nameList = name.split('.')
        if filters != {} and filters is not None :
            if applyFilterFor not in nameList and applyFilterFor :
                logging.info('%s  is not in %s' % (applyFilterFor, name))
            if len(nameList) == 1 :
                applyFilterFor = name
            elif len(nameList) > 1 and not applyFilterFor:
                logging.warning("Please specify the entity name for which the \
                                filter should be applied to through 'applyFilterFlag'")

        originalFilters = filters
        filters = {}
        dictList = inputDictList
        for entry in nameList :
            if entry == applyFilterFor :
               filters = originalFilters
            elif not applyFilterFor :
                filters = {}
            dictList = self._getNodes_1(name = entry, filters = filters, dictList = dictList,
                                        recursionFlag = recursionFlag)
            filters = {}

        self._stringify_numbers(dictList)
        return dictList


    def getChildNodesInParentNodeFromYaml(self, inputYaml= None,
                                          parentNodeName= None, childNodeName = None, recursionFlag = False):
        '''
        The function takes a parentNodeName in  the inputYaml and returns the list of  childNodes with the name = childNodeName

        ex: suppose parentNodeName = component childNodeName = type
            the function returns all types under components as list  [ {type:'-'},{type:'-'} ]
        '''
        if not parentNodeName or parentNodeName == '' :
            tcg_error("%s cannot be None or empty" % parentNodeName)

        childNodeList = []
        ParentNodeResult = YamlParser.getInstance().getNodesByName(name = parentNodeName,
                                                inputYaml = inputYaml, recursionFlag = recursionFlag)
        # FIXME: manage this print out with log level, also printout some other info, otherwise this printout is just a ridiculous amount irrelevant textflood
        # Do we even need it???
        #if ParentNodeResult == []:
        #       print("No %s found "%(parentNodeName))
        #else:
        if ParentNodeResult:
            if type(ParentNodeResult[0][parentNodeName]) is not list:
                inputDictList = [ParentNodeResult[0][parentNodeName]]
            else :
                inputDictList = ParentNodeResult[0][parentNodeName]
            childNodeList = YamlParser.getInstance().getNodesByName2(name = childNodeName,
                                                                     inputDictList = inputDictList,
                                                                     recursionFlag = recursionFlag)
        return  childNodeList

    def getChildNodesInParentNodeFromDictionaries(self, inputDictList = [],
                                    parentNodeName = None, childNodeName = None, recursionFlag = False):
        '''
        The function takes a parentNodeName in  the inputYaml and returns the list of  childNodes with the name = childNodeName

        ex: suppose parentNodeName = component childNodeName = type
            the function returns all types under components as list  [ {type:'-'},{type:'-'} ]
        '''
        if not parentNodeName or parentNodeName == '' :
            tcg_error("%s cannot be None or empty" %parentNodeName)

        childNodeList = []
        ParentNodeResult = YamlParser.getInstance().getNodesByName2(name = parentNodeName,
                                                inputDictList = inputDictList, recursionFlag = recursionFlag)
        # FIXME: manage this print out with log level, also printout some other useful info, otherwise this printout is just a ridiculous amount of irrelevant textflood
        # Do we even need it???
        #if ParentNodeResult == []:
        #       print("No %s found "%(parentNodeName))
        #if ParentNodeResult == []:
        #       print("No %s found "%(parentNodeName))
        #else:
        if ParentNodeResult:
            if type(ParentNodeResult[0][parentNodeName]) is not list:
                inputDictList = [ParentNodeResult[0][parentNodeName]]
            else :
                inputDictList = ParentNodeResult[0][parentNodeName]
            childNodeList = YamlParser.getInstance().getNodesByName2(name = childNodeName,
                                                                     inputDictList = inputDictList,
                                                                     recursionFlag = recursionFlag)
        return  childNodeList
    def _getNodes(self, inputDict = {}, inputKey = None, recursionFlag = True):
        result = []
        for key, value in inputDict.iteritems():
            if inputKey == key :
                result.append({key:value})

            if recursionFlag :
                if type(value) is dict :
                    result.extend(self._getNodes(inputDict = value, inputKey = inputKey))

                elif type(value) is list :
                    for item in value :
                        if type(item) is dict :
                            result.extend(self._getNodes(inputDict = item, inputKey = inputKey))

        return result


    def _stringify_numbers(self, yaml_element):
        '''
        This function provides support for parsing numbers as string. Numbers starting with 0
        may be corrupted. Users should be alertet to avoid using numbers and instead pass them
        as strings between quotes.
        '''
        ret_val = None
        if not yaml_element:
            return ret_val
        elif isinstance(yaml_element, list):
            to_remove = []
            for sub_element in yaml_element:
                if isinstance(sub_element, int) or isinstance(sub_element, float):
                    logging.warning("Number %d used as list element in the model, converting it to string. " \
                                    "Non-decimal numbers may be corrupted. To avoid this, pass the " \
                                    "value as string by putting it between quotes" % sub_element)
                    yaml_element.append(str(sub_element))
                    to_remove.append(sub_element)
            for extra_element in to_remove:
                    yaml_element.remove(extra_element)
            for sub_element in yaml_element:
                if isinstance(sub_element, list) or isinstance(sub_element, dict):
                    self._stringify_numbers(sub_element)
        elif isinstance(yaml_element, dict):
            for (key, value) in yaml_element.items():
                #This should not be the case ever, since we write the csm speicification
                if isinstance(key, int) or isinstance(key, float):
                    logging.warning("Number %d used as key in the model, converting it to string. " \
                                    "Non-decimal numbers may be corrupted. To avoid this, pass the " \
                                    "value as string by putting it between quotes" % key)
                    yaml_element[str(key)] = value
            for key in yaml_element:
                if isinstance(key, int):
                    del yaml_element[key]
            for (key, value) in yaml_element.items():
                if not isinstance(value, bool):
                    if isinstance(value, int):
                        logging.debug("Number %d used as value for attribute %s in the model, " \
                                     "converting it to string. " %(value, key))
                        yaml_element[key] = str(value)
                    if isinstance(value, float):
                        logging.warning("Number %d used as value for attribute %s in the model, " \
                                     "converting it to string. " \
                                    "Non-decimal numbers may be corrupted. To avoid this, pass the " \
                                    "value as string by putting it between quotes" % (value, key))
                        yaml_element[key] = str(value)
                    elif isinstance(value, list) or isinstance(value, dict):
                        self._stringify_numbers(value)
        #If for some reason it is only called on a simple value
        #should not be the case if used correctly
        elif isinstance(yaml_element, int) or isinstance(yaml_element, float):
            ret_val = str(yaml_element)
        return ret_val

    def _filterNode(self, filters = {}, inputDict = {}):

        filterFlag = True
        for key, value in filters.iteritems() :
            if type(inputDict) is dict :
                if key in inputDict:
                    if inputDict[key] != value :
                        filterFlag = False
                else :
                    filterFlag = False
            else :
                filterFlag = False

        return filterFlag

    def _filterNodes(self, name = None, filters = {}, dictList = []):
        #for key, value in filters.iteritems() :
        for dictItem in list(dictList) :
            for key, value in dictItem.iteritems():
                if type(value) is dict :
                    if not self._filterNode(filters = filters, inputDict = value) :
                        dictList.remove(dictItem)

                elif type(value) is list :
                    value = [item for item in value if self._filterNode(filters = filters,
                                                                        inputDict = item)]
                    '''for item in value :
                        if type(item) is dict :
                            if not self._filterNode(filters = filters, inputDict = item) :
                                print value
                                del value[value.index(item)]
                                print value'''
                    dictItem[key] = value
                    if len(value) == 0 :
                        del dictList[dictList.index(dictItem)]
                elif type(value) is str and len(dictList)== 1 :
                          for fkey, fvalue in filters.iteritems():
                              if fkey == key and fvalue == value:
                                   return dictList
                              else:
                                   dictList.remove(dictItem)

        return dictList

    def _getNodes_1(self, name = None, filters = {}, dictList = [], recursionFlag = True):
        '''
        Recursively parses the inputYaml and returns a list of dictionaries
        each dictionary containing only one key,value pair with key name as 'name'
        and corresponding value
        '''
        dictList1 = []
        dictList2 = []
        '''if type(inputYaml) is dict :
            yamlStream = inputYaml
        else :
            yamlStream = PyYaml_3_11.load(open(inputYaml, 'r'))'''
        for dictItem in dictList :
            if not dictItem == None:
                dictList1 = self._getNodes(inputDict = dictItem, inputKey = name,
                                           recursionFlag = recursionFlag)
                dictList2.extend(self._filterNodes(name = name, filters = filters,
                                                   dictList = dictList1))

        return dictList2
    def _checkItemInList(self,item={},referenceList=[]):
        '''Check the  dictionary item  in  referenceList
           If the item is found in referenceList returns True  else returns False
           Note : it won't check the dictionary values of item in referenceList '''

        found = False
        for element in referenceList:
            if type(element) is dict:
               if len(set(item.keys()).intersection(element.keys())) == len(item.keys()):
                   found =  True
            elif type(element) is str:
                 if item.has_key(element):
                     found = True


        return found
    def _compareListOfDicts(self,inputList=[],referenceList= [],tagName = ''):
        ''' Compare the inputList with referenceList
            the items of inputList which are not in referenceList  will be returned as a list'''
        returnList= []
        for re_element in referenceList:
             if type(re_element) is dict:
                 if not self._checkItemInList(referenceList = inputList, item = re_element):
                     returnList.append(re_element)
             if type(re_element) is str:
                 if not self._checkItemInList(referenceList = inputList, item = re_element):
                     returnList.append(re_element)

        return returnList

    def mergeModule(self, module_a, module_b):
        """
        Merge the input modules and return the merged result.
        Input Parameters:
          module_a, module_b - dict for CSM module.
        """
        module = dict(module_a)
        for key in module_b:
            if key in module:
                # system and csm-version is special. All others should be list
                if key == CgtConstants.SYSTEM_TAG:
                    tcg_error("ERROR: There can only be one system defined")
                elif key == CgtConstants.CSM_VERSION_TAG:
                    if module[key] != module_b[key]:
                        tcg_error("ERROR: Different {0} in yaml documents.".format(CgtConstants.CSM_VERSION_TAG))
                    # Nothing need to do for duplicated csm-version.
                else:
                    module[key] = module[key] + module_b[key]
            else:
                module[key] = module_b[key]
        return module

    def loadModule(self, yamlFiles):
        """
        The generator to return module which is loaded from yaml file.
        Input Parameters:
          yamlFiles - Input yaml file list.
        """
        for yamlfile in yamlFiles:
            m = set([])
            try:
                with open(yamlfile) as f:
                    m = PyYaml_3_11.load(f)
                    f.close()
            except PyYaml_3_11.YAMLError, exc:
                if hasattr(exc, 'problem_mark'):
                    mark = exc.problem_mark
                    logging.error("Yaml file %s Error position: (%s:%s)" % (yamlfile, mark.line+1, mark.column+1))
            except IOError as e:
                logging.error('Can not open file {0} for read, error({1}): {2}'.format(yamlfile, e.errno, e.strerror))
            if m:
                yield m

    def dump_yaml_dict_to_file(self, yaml_dict, dumpfile):
        '''
        Dump yaml dictionary to file.
        Input parameters:
            yaml_dict - dictionary with parsed yaml file.
            dumpfile - file name including path of output file.
        '''
        try:
            mergedModule = {}
            with open(dumpfile, 'w') as f:
                mergedModule = self.mergeModule(
                    mergedModule,
                    yaml_dict)
                PyYaml_3_11.dump(
                        yaml_dict,
                        f,
                        default_flow_style=False)
                f.close()
        except IOError as e:
            tcg_error('Can not open file {0} for write, error({1}): {2}'.format(dumpfile, e.errno, e.strerror))
