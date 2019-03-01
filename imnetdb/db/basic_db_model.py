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

database_model = dict(


    nodes=[
        # ordered here alphabetically for humans
        'Cable',
        'Device', 'DeviceGroup',
        'Interface',
        'IPAddress', 'IPNetwork', 'IPInterface',
        'LAG',
        'RoutingTable',
        'VLAN', 'VLANGroup'
    ],

    edges=[

        # Basic network construct relationships

        ('Device',          'device_member',        'DeviceGroup'),
        ('Device',          'equip_interface',      'Interface'),
        ('Interface',       'lag_member',           'LAG'),
        ('Interface',       'cabled',               'Cable'),
        ('VLAN',            "vlan_member",          'VLANGroup'),

        # IP address node types, must be bound to a routing table for address management

        ('IPAddress',       'ip_member',            'RoutingTable'),
        ('IPInterface',     'ip_member',            'RoutingTable'),
        ('IPNetwork',       'ip_member',            'RoutingTable'),

        # an IP interface can be assigned to any of the following node:

        ('IPInterface',     'ip_assigned',          'Interface'),
        ('IPInterface',     'ip_assigned',          'LAG'),
        ('IPInterface',     'ip_assigned',          'VLAN'),

    ]
)
