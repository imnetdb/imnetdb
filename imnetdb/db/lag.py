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

from collections import defaultdict
from first import first

from imnetdb.db.collection import TupleKeyCollection, CommonNodeGroup


class LAGNodes(TupleKeyCollection, CommonNodeGroup):

    COLLECTION_NAME = 'LAG'
    EDGE_NAME = 'lag_member'

    def _key(self, key_tuple):
        return dict(device=key_tuple[0]['name'], name=key_tuple[1])

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

    def catalog_device(self, device_name):
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

    _query_cabled_lags = """
    FOR lag_node IN LAG
        FOR if_node IN INBOUND lag_node lag_member
            FOR cable_node IN OUTBOUND if_node cabled
                RETURN {
                    cable_id: cable_node._id,
                    lag_id: lag_node._id,
                    device: if_node.device,
                    if_name: if_node.name
                }    
    """

    def get_cabling(self, return_list=False):
        """
        This function queries the database for all LAGs that have a cabled peering relationship.  That is
        to say - find all the cabled interfaces, and find the LAGs that share cables.  Return a
        dictionary with:
            key = tuple of the LAG peers ((dev1, lag1), (dev2, lag2))
            value = list of cable-IDs

        If the caller would prefer to have the raw list of data so that they can orient the information
        in a different way, then set `return_list` to True

        Returns
        -------
        dict[tuple] - when return_list is False (default)
            As described

        list[dict] - when return_list is True
            Each dict entry will have the following:
                cable_id = Cable ID
                lag_id = LAG ID
                device = device name
                if_name = interface name on device
        """

        # if the caller simply wants the raw list of data, return that now

        cabled_lags = list(self.query(self._query_cabled_lags))
        if return_list is True:
            return cabled_lags

        # otherwise, organize the data as a dictionary with keys = LAG peers (tuple) and the
        # values are the list of cables between the LAG peers.

        by_cable_id = defaultdict(set)
        for item in cabled_lags:
            by_cable_id[item['cable_id']].add((item['device'], item['lag_id']))

        by_lag_peers = defaultdict(list)
        for cable_id, lag_peers in by_cable_id.items():
            by_lag_peers[tuple(lag_peers)].append(cable_id)

        return dict(by_lag_peers)
