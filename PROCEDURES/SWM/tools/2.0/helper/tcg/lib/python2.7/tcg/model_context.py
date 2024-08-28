class ModelContextData(object):
    """
    This class represents contextual data that is required to generate the
    campaigns but it is not present in the CSM model. An example of contextual
    model data could be information that is specific to the cluster, like the
    hostnames corresponding to the cluster nodes
    """
    def __init__(self, hostname_amfnode_map,
                       plugins_base_dir=None):
        self._hostname_amfnode_map = hostname_amfnode_map
        self._plugins_base_dir = plugins_base_dir

    def get_hostname_amfnode_map(self):
        return self._hostname_amfnode_map

    def get_plugins_base_dir(self):
        return self._plugins_base_dir
