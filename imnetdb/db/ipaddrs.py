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

from ipaddress import ip_address, ip_interface, ip_network
from first import first
from imnetdb.db.collection import NameKeyCollection, TupleKeyCollection, CommonNodeGroup


class RoutingTableNodes(NameKeyCollection, CommonNodeGroup):

    COLLECTION_NAME = 'RoutingTable'
    EDGE_NAME = 'ip_member'

    # TODO: not preently using the following AQL, but leaving here for now since there may
    # TODO: be a use-case for retrieving just the values without the assigned nodes.

    _query_members = """
    LET rt = DOCUMENT('RoutingTable', @rt_name)
    
    for entry in inbound rt ip_member
        FILTER IS_SAME_COLLECTION(@col_name, entry)
        return entry    
    """

    _query_members_assigned = """
    LET rt = DOCUMENT('RoutingTable', @rt_name)
    
    for ip in inbound rt ip_member
        FILTER IS_SAME_COLLECTION(@col_name, ip)
        LET assigned = FIRST(for $assigned in outbound ip ip_assigned return $assigned)
        return {
            ip: ip, 
            assigned: assigned,
            collection: PARSE_IDENTIFIER(assigned)['collection']
        }
    """

    def get_host_members(self, rt_node):
        return list(self.query(self._query_members_assigned, bind_vars={
            'rt_name': rt_node['name'],
            'col_name': 'IPAddress'
        }))

    def get_interface_members(self, rt_node):
        return list(self.query(self._query_members_assigned, bind_vars={
            'rt_name': rt_node['name'],
            'col_name': 'IPInterface'
        }))

    def get_network_members(self, rt_node):
        return list(self.query(self._query_members_assigned, bind_vars={
            'rt_name': rt_node['name'],
            'col_name': 'IPNetwork'
        }))


class CommonIPNode(TupleKeyCollection):
    IP_FUNC = None

    def _key(self, key_tuple):
        return dict(rt=key_tuple[0]['name'], name=key_tuple[1])

    def ensure(self, key_tuple, **fields):
        """
        Ensure the node exists in the database collection using the key_tuple
        value to determine a unique item.  The tuple can contain an optional
        third item (dict) for user-defined key-values beyond the required
        rt-node, ip-string.

        Parameters
        ----------
        key_tuple: tuple
            [0]: dict - routing-table node
            [1]: str - IP string value
            [2]: (optional) dict - any additional items user wants as part of key

        Other Parameters
        ----------------
        The `fields` are additional key-values that will be added to the node
        when it is created or updated (ensured).

        Examples
        --------
        Standard use-case where key_tuple is only the rt-node and the IP address:

            ret_node = mycol.ensure((rt_node, "10.1.1.0/30"))

        The second use-case is for creating "private" or "shared" items; for
        example when the same IP address is used by multiple devices. This
        use-case key_tuple has an additional field to ensure unqiueness beyond
        the (RT, IP) value.  In this example use/store a field called "group"
        as part of the unique key:

            ret_node = mycol.ensure((rt_node, "10.1.1.0/30", dict(group="foobaz"))

        The same call could be made with a different group, but using the same IP string
        value, for example:

            another_node = mycol.ensure((rt_node, "10.1.1.0/30", dict(group="gizmo"))

        The DB collection will now contain two nodes both with the same (RT, IP) value
        but with different group values.

        Returns
        -------
        dict
            The collection node that was created/updated.
        """
        rt_node, name, *other_key_fields = key_tuple
        other_key_fields = first(other_key_fields) or {}
        ip_addr = self.IP_FUNC(name)
        ip_node = super().ensure(key_tuple, version=ip_addr.version, **fields, **other_key_fields)
        self.client.routing_tables.add_member(rt_node, ip_node)
        return ip_node

    def assign(self, ip_node, other_node):
        self.client.ensure_edge((ip_node, 'ip_assigned', other_node))


class IPAddressNodes(CommonIPNode):
    """
    The tuple key is (rt_node, ip_address_value)
    """

    COLLECTION_NAME = 'IPAddress'
    IP_FUNC = staticmethod(ip_address)


class IPInterfaceNodes(CommonIPNode):
    """
    The tuple key is (rt_node, ip_ifaddr_value)
    """

    COLLECTION_NAME = 'IPInterface'
    IP_FUNC = staticmethod(ip_interface)


class IPNetworkNodes(CommonIPNode):
    """
    The tuple key is (rt_node, ip_netaddr_value)
    """

    COLLECTION_NAME = 'IPNetwork'
    IP_FUNC = staticmethod(ip_network)


_query_all_assignments = """
LET $ipif_assignments = (FOR ipif_node in IPInterface
    FOR asgn_node IN OUTBOUND ipif_node ip_assigned
        return {
            ip: ipif_node,
            assigned: asgn_node
        }
)

LET $ipaddr_assignments = (FOR ipif_node in IPAddress
    LET $assigned = FIRST(FOR asgn_node IN OUTBOUND ipif_node ip_assigned RETURN asgn_node)
    return {
        ip: ipif_node,
        assigned: $assigned
    }
)

LET $ipnet_assignments = (FOR ipif_node in IPNetwork
    LET $assigned = FIRST(FOR asgn_node IN OUTBOUND ipif_node ip_assigned RETURN asgn_node)
    return {
        ip: ipif_node,
        assigned: $assigned
    }
)

RETURN {
    'address': $ipaddr_assignments,
    'interface': $ipif_assignments,
    'network': $ipnet_assignments
}
"""


def query_all_assignments(db):
    return first(db.query(_query_all_assignments))
