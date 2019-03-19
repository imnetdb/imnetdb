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
        'LAG', 'LACP',
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
        ('LAG',             "lacp_member",          "LACP"),

        # IP address node types, must be bound to a routing table for address management

        ('IPAddress',       'ip_member',            'RoutingTable'),
        ('IPInterface',     'ip_member',            'RoutingTable'),
        ('IPNetwork',       'ip_member',            'RoutingTable'),

        # IP interface can be assigned to any of the following nodes:

        ('IPInterface',     'ip_assigned',          'Interface'),
        ('IPInterface',     'ip_assigned',          'LAG'),
        ('IPInterface',     'ip_assigned',          'VLAN'),

        # IP memberships within types

        ('IPAddress',       'ip_member',            'IPInterface'),
        ('IPAddress',       'ip_member',            'IPNetwork'),
        ('IPInterface',     'ip_member',            'IPNetwork'),

        # VLAN, VLANGroup can be assigned to any of the following nodes:

        ('VLAN',            'vlan_assigned',        'Interface'),
        ('VLANGroup',       'vlan_assigned',        'Interface'),
        ('VLAN',            'vlan_assigned',        'LAG'),
        ('VLANGroup',       'vlan_assigned',        'LAG'),
    ]
)
