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


class InterfaceNodes(TupleKeyCollection):

    COLLECTION_NAME = 'Interface'

    def __init__(self, client):
        super(InterfaceNodes, self).__init__(client=client)
        self.pool = client.resource_pool('RPOOL_%s' % self.COLLECTION_NAME)

    def _key(self, key_tuple):
        return {
            'device': key_tuple[0]['name'],
            'name': key_tuple[1]
        }

    def ensure(self, key_tuple, used=False, **fields):
        """
        Ensure the interface exists.  The key is a dict that contains the device, name values.
        The key can identify the device either by name 'device' or by the 'device_node' specifically.

        Parameters
        ----------
        key_tuple: tuple
            [0] device_node : dict (optional)
                The Device node dict

            [1] name : str
                The interface name

        used : bool
            The initial state of interface used field.  Default is False.  Use
            the :meth:`allocate` to obtain unused interfaces.

        fields : dict
            user-defined collection of fields to assign to this interface

        Returns
        -------
        dict
            The interface node dict
        """
        device_node, if_name = key_tuple
        if_node = super(InterfaceNodes, self).ensure(key_tuple, **fields)
        self.client.ensure_edge((device_node, 'equip_interface', if_node))

        # add the if_node id as the value in the resource pool.  copy the user-defined
        # fields by default into the pool as well, so that they can be later used for matching purposes.

        # WARNING: you should consider these fields as "constants" in the pool node because if they are
        # changed in the Interface node dict, those changes WILL NOT be reflected into the pool node.  For example,
        # if you create an interface with "role=server" and then change the Interface node role value
        # to "role=spine", then the corresponding pool doc will not be updated.  In these cases, you will
        # need to remove the pool node and then add a new pool node with the new "constant field" values.

        self.pool.add(value=if_node['_id'],
                      device=device_node['name'], name=if_node['name'],
                      **fields)

        return if_node

    def take(self, device, name):
        """
        Take the interface node given the device name and interface name values.   This will mark the interface
        as "used" for allocation purposes.  If the given device/iface does not exist, then None is returned.

        Parameters
        ----------
        device : str
            The name of the device, for example "spine1"

        name : str
            The interface name, for example "Ethernet1"

        Returns
        -------
        dict
            The interface node dict

        None
            If the given device and interface name does not find a match in the pool.
        """
        taken = self.pool.take({'device': device, 'name': name})
        if not taken:
            return None

        if_node_id = taken['value']
        return self.col.get(if_node_id)

    def put(self, device, name):
        """
        Mark the interface node associated by the device and interface name as unused.

        Parameters
        ----------
        device : str
            The device name, for example "spine1"

        name : str
            The interface name, for example "Ethernet1"

        Raises
        ------
        ValueError
            When the device / interface name does not exist in the resource pool.
        """
        taken = self.pool.take({'device': device, 'name': name})
        if not taken:
            raise ValueError('{} {} does not exist in pool'.format(device, name))

        self.pool.put(taken, clear_fields=False)
