#  Copyright 2019 Jeremy Schulman, nwkautomaniac@gmail.com
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

from copy import deepcopy
from bracket_expansion import expand


class Stencils(object):
    DEVICE_STRIP_FIELDS = {'interfaces', 'name'}

    def __init__(self):
        self.registry = dict()

    def _make_stencil_dict(self, stencil_name, stencil_data):
        stencil_dict = deepcopy(stencil_data)

        stencil_dict['name'] = stencil_name
        interfaces = stencil_dict.pop('interfaces', None)
        if not interfaces:
            raise ValueError(f"{stencil_name} missing required 'interfaces'")

        stencil_dict['interfaces'] = dict()

        # we are going to expand the list of interface and 'deepcopy' the if_data
        # dict so that we can then later (potentially) update the interface
        # data dictionary fields.  If we do not use deepcopy, then all interfaces
        # share the same if_data dict; and updating one, will in effect update
        # all interfaces.

        for if_names, if_data in interfaces.items():
            if_name_list = expand(if_names) if '[' in if_names else [if_names]
            for if_name in if_name_list:
                stencil_dict['interfaces'][if_name] = deepcopy(if_data)

        return stencil_dict

    def _make_extended_stencil_dict(self, stencil_name, stencil_data):
        # if here, then using a previously defined stencil as a base
        # stencil and then "extending" it to this new one.

        base_name = stencil_data.pop('base')
        stencil_dict = deepcopy(self[base_name])
        ext_dict = self._make_stencil_dict(stencil_name, stencil_data)
        ext_interfaces = ext_dict.pop('interfaces')
        stencil_dict.update(ext_dict)

        for if_name, if_data in ext_interfaces.items():
            stencil_dict['interfaces'][if_name].update(if_data)

        return stencil_dict

    def define_stencil(self, stencil_name, stencil_data):
        _maker = self._make_stencil_dict if 'base' not in stencil_data else self._make_extended_stencil_dict
        stencil_dict = _maker(stencil_name, stencil_data)
        self.registry[stencil_name] = stencil_dict
        return stencil_dict

    def load(self, stencils):
        for stencil_name, stencil_data in stencils.items():
            self.define_stencil(stencil_name, stencil_data)

    def ensure_device(self, db, stencil_def, device_name, **device_fields):
        nodes = dict(interfaces=dict())

        # remove the stencil "meta" information so it is not stored into the
        # device DB node

        udf_items = stencil_def.keys() - self.DEVICE_STRIP_FIELDS

        udf_data = dict(list(filter(lambda i: i[0] in udf_items, stencil_def.items())),
                        **device_fields)

        # but do include the stencil name as "stencil" into the node

        udf_data['stencil'] = stencil_def['name']

        # --------------------------------------------------------
        # now ensure the Device node and the associated interfaces
        # --------------------------------------------------------

        device_node = db.devices.ensure(device_name, **udf_data)
        nodes['device'] = device_node

        for if_name, if_fields in stencil_def['interfaces'].items():
            if_node = db.interfaces.ensure((device_node, if_name), **if_fields)
            nodes['interfaces'][if_name] = if_node

        return nodes

    def __iter__(self):
        return iter(self.registry)

    def __contains__(self, item):
        return item in self.registry

    def __getitem__(self, item):
        if item not in self.registry:
            raise ValueError(f"stencil pack does not include {item}")

        return self.registry[item]
