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

from imnetdb.db.collection import TupleKeyCollection

from first import first


class LAGNodes(TupleKeyCollection):

    COLLECTION_NAME = 'LAG'

    def _key(self, key_tuple):
        return dict(device=key_tuple[0]['name'], name=key_tuple[1])

    def add_interface(self, lag_node, interface_node):
        """
        Add an interface to a LAG

        Parameters
        ----------
        lag_node : dict
            The LAG node dict

        interface_node : dict
            The Interface node dict
        """
        self.client.ensure_edge((interface_node, 'lag_member', lag_node))

    def del_interface(self, lag_node, interface_node):
        """
        Remove an interface from a LAG

        Parameters
        ----------
        lag_node : dict
            The LAG node dict

        interface_node : dict
            The Interface node dict
        """
        self.client.ensure_edge((interface_node, 'lag_member', lag_node), present=False)

    _query_lag_members = """
    FOR lag in LAG
        FILTER lag.device == @device_name and lag.name == @lag_name
        for interface in inbound lag lag_member
            return interface    
    """

    def get_members(self, lag_node):
        """
        Return the list of Interface node dicts that are members of the given Lag node.

        Parameters
        ----------
        lag_node : dict
            The LAG node dict

        Returns
        -------
        list[dict]
            The list of Interface nodes.  If no nodes, then an empty list is returned.
        """
        return list(self.query(self._query_lag_members, bind_vars={
            'device_name': lag_node['device'],
            'lag_name': lag_node['name']
        }))

    _query_lags_in_device = """
    return MERGE(
        FOR lag in LAG
            FILTER lag.device == @device_name
            LET if_nodes = MERGE(
                for interface in inbound lag lag_member
                    return {[interface.name]: interface}
            )
            return {[lag.name]: {lag: lag, interfaces: if_nodes}}
    )              
    """

    def device_catalog(self, device_name):
        """
        Return a catalog of all LAGs and associated interfaces given the specific device name.

        Parameters
        ----------
        device_name : str
            The name of the device

        Returns
        -------
        dict
            The outer key is the LAG name, for example "ae0".  Each dictionary contains the following keys:
                'lag': LAG node dictionary
                'interfaces': dict
                    key = interface name, for example "Ethernet12"
                    value = interface node dict
        None
            If not LAG nodes found for the given device.
        """
        return first(self.query(self._query_lags_in_device, bind_vars={
            'device_name': device_name
        }))

    def find(self, interface_node):
        """
        Find the LAG node for which this interface is associated.

        Parameters
        ----------
        interface_node : dict
            The Interface node dict

        Returns
        -------
        dict
            The LAG node dict.
        None
            If no LAG is associated to this interface.
        """
        found = first(self.db.collection('lag_member').find(dict(_from=interface_node['_id'])))
        return self.col.get(found['_to']) if found else None

    _query_lag_catalog = """
    return MERGE(
        FOR lag in LAG
            LET if_nodes = MERGE(
                for interface in inbound lag lag_member
                    return {[interface.name]: interface}
            )
            COLLECT device_name = lag.device into device_info = {
                [lag.name]: {
                    lag: lag,
                    interfaces: if_nodes
                }
            }
            return {
                [device_name]: MERGE(device_info)
            }        
    )            
    """

    def catalog(self):
        """
        Return a catalog of all known LAGS, oriented by device, LAG name and collected interfaces.

        Returns
        -------
        dict:
            outer-key is the device name, e.g. "spine1".  Each value is a dict:
                key = LAG name, e.g. "ae0"
                value = dict:
                    lag: LAG node dict
                    interfaces: dict
                        key: interface name
                        value: Interface node dict
        """
        return first(self.query(self._query_lag_catalog))
