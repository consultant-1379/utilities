from csm_unit import CSMUnit

class DeploymentProfile(CSMUnit):
    '''
    CSM Deployment Profile class
    '''

    def __init__(self) :
        self.instance_of = None
        self._input_yaml_dict = None

    def setValues(
            self,
            instance_of=None,
            input_yaml_dict = None):
        ''' Constructor of System '''

        self.setInstanceOf(instance_of)
        self.set_input_yaml(input_yaml_dict)

    def getInstanceOf(self):
        return self.instance_of


    def get_input_yaml_dict(self):
        return self._input_yaml_dict

    def setInstanceOf(self, instance_of=None):
        self.instance_of = instance_of

    def set_input_yaml(self, input_yaml_dict):
        self._input_yaml_dict = input_yaml_dict
