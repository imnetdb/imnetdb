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

from setuptools import setup, find_packages

package_version = '0.0.2'
package_name = 'imnetdb-db'
packages = find_packages()
package_dir = packages[-1]

imnetdb_collection_entry_points = [
    ('cabling',         'cabling',      'CableNodes'),
    ('devices',         'device',       'DeviceNodes'),
    ('device_groups',   'device',       'DeviceGroupNodes'),
    ('interfaces',      'interface',    'InterfaceNodes'),
    ('ip_host_addrs',   'ipaddrs',      'IPAddressNodes'),
    ('ip_net_addrs',    'ipaddrs',      'IPNetworkNodes'),
    ('ip_if_addrs',     'ipaddrs',      'IPInterfaceNodes'),
    ('lags',            'lag',          'LAGNodes'),
    ('routing_tables',  'ipaddrs',      'RoutingTableNodes'),
    ('vlans',           'vlan',         'VlanNodes'),
    ('vlan_groups',     'vlan',         'VlanGroupNodes'),
]


def requirements(filename='requirements.txt'):
    return open(filename.strip()).readlines()


with open("README.md", "r") as fh:
    long_description = fh.read()


def create_entry_points():
    return ["{handler} = {pkgdir}.{module}:{class_name}".format(handler=handler, pkgdir=package_dir,
                                                                module=module, class_name=class_name)
            for handler, module, class_name in imnetdb_collection_entry_points]


setup(
    name=package_name,
    version=package_version,
    description='IMNetDB network source of truth graph database library',
    long_description=long_description,
    long_description_content_type="text/markdown",
    author='Jeremy Schulman',
    packages=packages,
    install_requires=requirements(),
    entry_points={
        'imnetdb_collections': create_entry_points(),
        'imnetdb_database_models': [
            'basic = {}.basic_db_model:database_model'.format(package_dir)
        ]
    }
)
