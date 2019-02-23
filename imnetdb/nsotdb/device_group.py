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

from imnetdb.nsotdb import node_utils


class DeviceGroupNodes(node_utils.NameKeyCollection):

    COLLECTION_NAME = 'DeviceGroup'

    def add_device(self, group_node, device_node):
        """
        Add a Device to a DeviceGroup

        Parameters
        ----------
        group_node : dict
            The DeviceGroup node dict

        device_node : dict
            The Device node dict

        """
        self.client.ensure_edge((device_node, 'device_member', group_node))

    def del_device(self, group_node, device_node):
        """
        Remove a Device from a DeviceGroup

        Parameters
        ----------
        group_node : dict
            The DeviceGroup node dict

        device_node : dict
            The Device node dict
        """
        self.client.ensure_edge((device_node, 'device_member', group_node), present=False)
