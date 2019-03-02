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

from first import first
from imnetdb.db.collection import NameKeyCollection, CommonNodeGroup


class VlanNodes(NameKeyCollection):
    COLLECTION_NAME = 'VLAN'

    _query_attached_vlans = """
    RETURN FLATTEN(
        FOR vlan_item IN INBOUND @node vlan_assigned
            RETURN IS_SAME_COLLECTION(vlan_item, "VLAN") 
                ? vlan_item
                : (
                    FOR vlan IN INBOUND vlan_item vlan_member 
                        RETURN vlan
                )
    )         
    """

    def get_attached_vlans(self, on_node):
        """
        Return a flat list of all VLAN nodes that are assigned to `on_node`.  This call is different
        from the vlan-groups get_members in that the query will "flatten" the list of vlans and vlans in groups
        into a single list.

        Parameters
        ----------
        on_node : dict
            The node dict for which to start on the query.  Since VLANs can be attached to many different
            types of nodes, for example [VLAN, LAG], the caller is required to provide this starting node.

        Returns
        -------
        list[dict]
            The list of VLAN node items.
        """
        return first(self.query(self._query_attached_vlans, bind_vars={
            'node': on_node
        }))


class VlanGroupNodes(NameKeyCollection, CommonNodeGroup):
    COLLECTION_NAME = 'VLANGroup'
    EDGE_NAME = 'vlan_member'
