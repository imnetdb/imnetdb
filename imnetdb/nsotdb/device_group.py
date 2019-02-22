
from imnetdb.nsotdb import node_utils


class DeviceGroupNodes(node_utils.NameKeyCollection):

    COLLECTION_NAME = 'DeviceGroup'

    def add_device(self, group_node, device_node):
        """
        Add a Device to a DeviceGroup

        Parameters
        ----------
        group_node : dict
            The DeviceGroup node dict

        device_node : dict
            The Device node dict

        """
        self.client.ensure_edge((device_node, 'device_member', group_node))

    def del_device(self, group_node, device_node):
        """
        Remove a Device from a DeviceGroup

        Parameters
        ----------
        group_node : dict
            The DeviceGroup node dict

        device_node : dict
            The Device node dict
        """
        self.client.ensure_edge((device_node, 'device_member', group_node), present=False)
