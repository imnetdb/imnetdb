# Copyright 2019 Jeremy Schulman, nwkautomaniac@gmail.com
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from string import Template
from first import first
from imnetdb.db.collection import CommonCollection


class LACPNodes(CommonCollection):

    COLLECTION_NAME = 'LACP'
    MEMBER_COLLECTION_NAME = 'LAG'
    EDGE_NAME = 'lacp_member'

    def ensure(self, peer_nodes, **fields):
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
        if len(peer_nodes) != 2:
            raise ValueError('interface_nodes requires two interface nodes')

        found = self.find(peer_nodes)
        if found:
            return found['peering_node']

        peering_node = self.col.insert(fields or {}, return_new=True)['new']

        edge_col = self.db.collection(self.EDGE_NAME)
        edge_col.insert(dict(_from=peer_nodes[0]['_id'], _to=peering_node['_id']))
        edge_col.insert(dict(_from=peer_nodes[1]['_id'], _to=peering_node['_id']))

        return peering_node

    def find(self, peer_nodes):
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
        if len(peer_nodes) > 2:
            raise ValueError("interface_nodes must be list length <= 2")

        edge_col = self.db.collection(self.EDGE_NAME)

        found_peering_nodes = [first(edge_col.find(dict(_from=peer_node['_id'])))
                               for peer_node in peer_nodes]

        if not all(found_peering_nodes):
            return None

        peering_node = self.db.collection(self.COLLECTION_NAME).get(found_peering_nodes[0]['_to'])

        if len(found_peering_nodes) == 2:

            if found_peering_nodes[0]['_to'] == found_peering_nodes[1]['_to']:
                return dict(peering_node=peering_node, peer_nodes=peer_nodes)

            raise RuntimeError('peers not connected to same peering node',
                               dict(peer_nodes=peer_nodes,
                                    peering_nodes=found_peering_nodes))

        # if we were give two interfaces, but only found one, then we might have
        # an issue here

        if len(peer_nodes) == 2:
            raise RuntimeError("two peers given, but only one connected",
                               dict(peer_nodes=peer_nodes,
                                    found_peering_nodes=found_peering_nodes))

        # if we are here, then we were given only one interface node, and we have found
        # one peering node.  We need to find the "other side" of the edge.from

        found_edges = list(edge_col.find(dict(_to=peering_node['_id'])))

        if len(found_edges) != 2:
            raise RuntimeError("one peer give, but did not find both ends",
                               dict(peer_nodes=peer_nodes,
                                    found_peering_node=peering_node,
                                    found_edges=found_edges))

        # if we are here, then we've found everything AOK, and need to return
        # the dictionary of information

        member_col = self.db.collection(self.MEMBER_COLLECTION_NAME)

        return dict(peering_node=peering_node,
                    interface_nodes=[member_col.get(edge['_from'])
                                     for edge in found_edges])

    _query_get_peering = Template("""
    FOR peering_node in @@col_name
        ${user_defined_filter}
        RETURN {
            peering_node: peering_node,
            peer_nodes: (FOR peer_node IN INBOUND peering_node @@edge_name RETURN peer_node)
        }
    """)

    def get_peering(self, match=None, filterexpr=None):
        """
        Return a list of peering information, where each list item is a dictionary with keys:
            - peering_node: the node dict that connects the peer nodes
            - peer_nodes: a list of peer node dics

        Parameters
        ----------
        match : dict (optional)
            If provided, this dictionary is used to match fields on peering node dict items.  For example,
            if you have added a field called "role" to the peering node, you can use match={'role': <value>}
            to only return peering items that have a role matching <value>.

        filterexpr : str (optional)
            This is an AQL FILTER expression, excluding the FILTER statement.  For example, if
            the peering node has a field called 'role' and you want to get cabling for either role is leaf-spine
            or role is leaf-server, then the filterexpr parameter would be:

                filterexpr='peering_node.role == "leaf-spine" or peering_node.role == "leaf-server"'

        Notes
        -----
        You cannot mix the use of `match` and `filterexpr`.  You can use one or the other.

        Returns
        -------
        list[dict]
            see above.
        """

        bind_vars = {
            '@col_name': self.COLLECTION_NAME,
            '@edge_name': self.EDGE_NAME
        }

        udf = ''

        if match:
            udf = 'FILTER MATCHES(peer_node, @user_match)'
            bind_vars['user_match'] = match

        elif filterexpr:
            udf = f'FILTER {filterexpr}'

        query = self._query_get_peering.substitute(user_defined_filter=udf)
        return list(self.query(query, bind_vars=bind_vars))
