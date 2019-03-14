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
from copy import deepcopy


class CommonCollection(object):

    COLLECTION_NAME = None

    def __init__(self, client):
        self.client = client
        self.db = client.db
        self.col = client.db.collection(self.COLLECTION_NAME)
        self.query = client.db.aql.execute

    def __iter__(self):
        return self.col.all()

    def __contains__(self, item):
        return self.col.has({'_key': item})

    def remove(self, node):
        vert_col = self.client.graph.vertex_collection(self.COLLECTION_NAME)
        vert_col.delete(node)


class NameKeyCollection(CommonCollection):
    """
    The document collection _key is the field.name value.  This value must be globally unique within
    the collection.
    """
    __aql_ensure_node = """
    UPSERT {_key: @fields.name}
    INSERT @fields
    UPDATE @fields
    IN @@col_name OPTIONS {keepNull: False}
    RETURN {doc: NEW, old: OLD}
    """

    def ensure(self, name, **fields):
        _fields = deepcopy(fields)
        _fields['_key'] = name
        _fields['name'] = name
        result = first(self.query(self.__aql_ensure_node, bind_vars={
            'fields': _fields,
            '@col_name': self.COLLECTION_NAME
        }))

        return result['doc']

    def __getitem__(self, name):
        """
        Return a document node dict that has a key value of `name`.

        Parameters
        ----------
        name : str,int
            The unique key value for the node

        Returns
        -------
        dict
            The document node dict

        None
            If there is not document by the given key `name`.
        """
        return self.col.get(name)


# class NamedKeyNodeGroup(NameKeyCollection):

class CommonNodeGroup(CommonCollection):
    EDGE_NAME = None

    def add_member(self, group_node, member_node):
        """
        Ensure the edge relationship from member_node to group_node exists.

        Parameters
        ----------
        group_node : dict
            The group node dict

        member_node : dict
            The member node dict
        """
        self.client.ensure_edge((member_node, self.EDGE_NAME, group_node))

    def del_member(self, group_node, member_node):
        """
        Ensure the edge relationship from member_node to group_node does not exists.

        Parameters
        ----------
        group_node : dict
            The group node dict

        member_node : dict
            The member node dict
        """
        self.client.ensure_edge((member_node, self.EDGE_NAME, group_node), present=False)

    _query_all_members = """
    RETURN MERGE(
        FOR member IN INBOUND DOCUMENT(@group_col, @group_name) @@edge_name
            RETURN {[member.name]: member}
    )        
    """

    def get_members(self, group_node):
        """
        Return a dictionary of the existing members that belong to the group.

        Parameters
        ----------
        group_node : dict
            The group node dict.  This must contain a 'name' field.

        Returns
        -------
        dict
            key: name of member
            value: member node dict
        """
        return first(self.query(self._query_all_members, bind_vars={
            'group_col': self.COLLECTION_NAME,
            'group_name': group_node['name'],
            '@edge_name': self.EDGE_NAME
        }))


class DictKeyCollection(CommonCollection):

    __aql_ensure_node = """
    UPSERT @key
    INSERT @fields
    UPDATE @fields
    IN @@col_name OPTIONS {keepNull: False}
    RETURN {doc: NEW, old: OLD}
    """

    def ensure(self, key, **fields):
        _fields = deepcopy(fields)
        _fields.update(key)

        result = first(self.query(self.__aql_ensure_node, bind_vars={
            'key': key,
            'fields': _fields,
            '@col_name': self.COLLECTION_NAME
        }))

        return result['doc']

    def __getitem__(self, key_dict):
        """
        Return a document node dict that has a key value of `name`.

        Parameters
        ----------
        key_dict : dict
            Dictionary containing the fields to match on.

        Returns
        -------
        dict
            The document node dict

        None
            If there is not document matching key_dict fields.
        """
        return first(self.col.find(key_dict, limit=1))


class TupleKeyCollection(CommonCollection):

    __aql_ensure_node = """
    UPSERT @key
    INSERT @fields
    UPDATE @fields
    IN @@col_name OPTIONS {keepNull: False}
    RETURN {doc: NEW, old: OLD}
    """

    def _key(self, key_tuple):
        raise NotImplementedError()

    def ensure(self, key_tuple, **fields):
        key = self._key(key_tuple)
        _fields = deepcopy(fields)
        _fields.update(key)

        result = first(self.query(self.__aql_ensure_node, bind_vars={
            'key': key,
            'fields': _fields,
            '@col_name': self.COLLECTION_NAME
        }))

        return result['doc']

    def __getitem__(self, key_tuple):
        """
        Return a document node dict that has a key value of `name`.

        Parameters
        ----------
        key_tuple : tuple
            [0]: primary node dict
            [1]: name

        Returns
        -------
        dict
            The document node dict

        None
            If there is not document matching key_dict fields.
        """
        return first(self.col.find(self._key(key_tuple), limit=1))


class PeeringCollection(CommonCollection):

    COLLECTION_NAME = None              # name of peering node collection, e.g. LACP
    MEMBER_COLLECTION_NAME = None       # name of peer node collection, e.g. LACP
    EDGE_NAME = None                    # name of edge collection between the two, e.g. lacp_member

    def ensure(self, peer_nodes, **fields):
        """
        Ensure that a peering node exists between two peer nodes.

        Parameters
        ----------
        peer_nodes : tuple[dict]
            A tuple (or list) of two peer node dict

        fields : kwargs
            Extra fields to be stored within the peering node.

        Returns
        -------
        dict
            The new peering node dict
        """
        if len(peer_nodes) != 2:
            raise ValueError('peer_nodes requires two nodes')

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
        Find the peering node that exists between the peer nodes.

        Parameters
        ----------
        peer_nodes : tuple[dict]
            A tuple (or list) of either 1 or 2 peer node document dict.
            If two nodes, then find the exact match peering node between the
            two.  If one node, then find the peering node associated, and
            also return the "other side" peer node.

        Returns
        -------
        dict
            Dictionary of information, structured:
                'peering_node': the peering node node dict
                'peer_nodes: The peer node dicts that 'connect' to the peering node

        Raises
        ------
        ValueError
            When caller provides more than two peer nodes

        RuntimeError
            When peer nodes provided do not connect to the same peering node

        """
        if len(peer_nodes) > 2:
            raise ValueError("peer_nodes must be list length <= 2")

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

        # if we were give two peers, but only found one, then we might have
        # an issue here

        if len(peer_nodes) == 2:
            raise RuntimeError("two peers given, but only one connected",
                               dict(peer_nodes=peer_nodes,
                                    found_peering_nodes=found_peering_nodes))

        # if we are here, then we were given only one peer node, and we have found
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
                    peer_nodes=[member_col.get(edge['_from'])
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
