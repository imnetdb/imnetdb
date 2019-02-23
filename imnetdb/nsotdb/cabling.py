"""
Copyright 2019 Jeremy Schulman, nwkautomaniac@gmail.com

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

   http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

from first import first
from imnetdb.nsotdb import node_utils


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

        found = self.find(interface_nodes)
        if found:
            return found['cable_node']

        cable_node = self.col.insert(fields or {}, return_new=True)['new']

        cabled = self.db.collection('cabled')
        cabled.insert(dict(_from=interface_nodes[0]['_id'], _to=cable_node['_id']))
        cabled.insert(dict(_from=interface_nodes[1]['_id'], _to=cable_node['_id']))

        return cable_node

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
        dict
            Dictionary of information, structured:
                'cable_node': Cable node dict
                'interface_nodes: Interface node dicts

        Raises
        ------
        ValueError
            When caller provides more than two Interface nodes

        RuntimeError
            When Interface nodes provided do not connect to the same Cable node

        """
        if len(interface_nodes) > 2:
            raise ValueError("interface_nodes must be list length <= 2")

        cabled = self.db.collection('cabled')

        found = [first(cabled.find(dict(_from=if_node['_id'])))
                 for if_node in interface_nodes]

        if not all(found):
            return None

        found_cable = self.db.collection('Cable').get(found[0]['_to'])

        if len(found) == 2:

            if found[0]['_to'] == found[1]['_to']:
                return dict(cable_node=found_cable,
                            interface_nodes=interface_nodes)

            raise RuntimeError('interfaces not connected to same cable',
                               dict(interface_nodes=interface_nodes,
                                    found_cables=found))

        # if we were give two interfaces, but only found one, then we might have
        # an issue here

        if len(interface_nodes) == 2:
            raise RuntimeError("two interfaces given, but only one connected",
                               dict(interface_nodes=interface_nodes,
                                    found_cables=found))

        # if we are here, then we were given only one interface node, and we have found
        # one cable node.  We need to find the "other side" of the cable.from

        found_edges = list(cabled.find(dict(_to=found_cable['_id'])))

        if len(found_edges) != 2:
            raise RuntimeError("one interface give, but did not find both ends",
                               dict(interface_nodes=interface_nodes, found_cable=found_cable,
                                    found_edges=found_edges))

        # if we are here, then we've found everything AOK, and need to return
        # the dictionary of information

        if_col = self.db.collection('Interface')

        return dict(cable_node=found_cable,
                    interface_nodes=[if_col.get(edge['_from'])
                                     for edge in found_edges])
