from imnetdb.gdb import node_utils


class CableNodes(node_utils.CommonCollection):
    COLLECTION_NAME = 'Cable'

    def ensure(self, interface_nodes, **fields):
        """
        Ensure that a Cable exists between two Interface nodes.

        Parameters
        ----------
        interface_nodes : tuple[dict]
            A tuple (or list) of two Interface document dict

        fields : kwargs
            Extra fields to be stored within the Cable node.
            
        Returns
        -------
        dict
            The new Cable document dict
        """
        if len(interface_nodes) != 2:
            raise ValueError('interface_nodes requires two interface nodes')

    def find(self, interface_nodes):
        """
        Find the Cable node that exists between the Interface nodes.

        Parameters
        ----------
        interface_nodes : tuple[dict]
            A tuple (or list) of either 1 or 2 Interface document dict.
            If two nodes, then find the exact match Cable node between the
            two.  If one node, then find the Cable node associated, and
            also return the "other side" Interface node.

        Returns
        -------
        TBD
        """
        pass