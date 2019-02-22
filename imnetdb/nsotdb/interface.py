from imnetdb.nsotdb.node_utils import DictKeyCollection


class InterfaceNodes(DictKeyCollection):

    COLLECTION_NAME = 'Interface'

    def ensure(self, key, **fields):
        """
        Ensure the interface exists.  The key is a dict that contains the device, name values.

        Parameters
        ----------
        key : dict
            device : str
                The name of the Device node
            device_node : dict (optional)
                The Device node dict
            name : str
                The interface name

        fields : dict
            user-defined collection of fields to assign to this interface

        Returns
        -------
        dict
            The interface node dict
        """
        dev_node = key.get('device_node') or self.client.devices[key['device']]
        if_node = super(InterfaceNodes, self).ensure(dict(device=dev_node['name'], name=key['name']), **fields)
        self.client.ensure_edge((dev_node, 'equip_interface', if_node))
        return if_node
