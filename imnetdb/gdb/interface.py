from imnetdb.gdb.node_utils import DictKeyCollection


class InterfaceNodes(DictKeyCollection):

    COLLECTION_NAME = 'Interface'

    def ensure(self, key, **fields):
        if_node = super(InterfaceNodes, self).ensure(key, **fields)

        dev_node = self.client.devices[key['device']]
        self.client.ensure_edge((dev_node, 'equip_interface', if_node))
