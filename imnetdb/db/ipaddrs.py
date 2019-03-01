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
        rt_node, name = key_tuple
        ip_addr = self.IP_FUNC(name)
        ip_node = super().ensure(key_tuple, version=ip_addr.version, **fields)
        self.client.routing_tables.add_member(rt_node, ip_node)
        return ip_node


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
