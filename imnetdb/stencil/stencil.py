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
from collections import defaultdict


class Stencils(object):
    DEVICE_STRIP_FIELDS = {'interfaces', 'name'}

    def __init__(self):
        self.registry = dict()

    def _make_stencil(self, stencil_name, stencil_def):
        if stencil_name in self.registry:
            return

        stencil_dict = deepcopy(stencil_def)

        stencil_dict['name'] = stencil_name
        interfaces = stencil_dict.pop('interfaces', None)
        if not interfaces:
            raise ValueError(f"{stencil_name} missing required 'interfaces'")

        stencil_dict['interfaces'] = defaultdict(dict)

        # we are going to expand the list of interface and 'deepcopy' the if_data
        # dict so that we can then later (potentially) update the interface
        # data dictionary fields.  If we do not use deepcopy, then all interfaces
        # share the same if_data dict; and updating one, will in effect update
        # all interfaces.

        for if_names, if_data in interfaces.items():
            if_name_list = expand(if_names) if '[' in if_names else [if_names]
            for if_name in if_name_list:
                stencil_dict['interfaces'][if_name] = deepcopy(if_data)

        self.registry[stencil_name] = stencil_dict

    def _make_extended_stencil(self, all_stencil_defs, stencil_name, stencil_def):

        if stencil_name in self.registry:
            return self.registry[stencil_name]

        # if the 'base' stencil is not yet defined, then we are going to recursively invoke
        # the 'define_stencil' method.  The recursion technique allows the user to define
        # stencils that have multiple-linear base definitions.

        base_name = stencil_def['base']
        if base_name not in self.registry:
            base_def = all_stencil_defs[base_name]
            self.define_stencil(all_stencil_defs=all_stencil_defs,
                                stencil_name=base_name, stencil_def=base_def)

        # create a copy of the base stencil dictionary.  we'll use this to "merge in" the
        # new stencil definition.

        copyof_base_dict = deepcopy(self[base_name])
        stencil_def.pop('base')
        self._make_stencil(stencil_name, stencil_def)
        new_stencil_dict = self.registry.pop(stencil_name)

        # remove the interfaces information from the new stencil since (1) we
        # are going to merge the new stencil dict into our base copy and (2) we
        # are going to merge the specific interfaces information with the base
        # stencil interfaces.

        new_interfaces = new_stencil_dict.pop('interfaces')

        # merge in the new stencil definition, then merge each interface

        copyof_base_dict.update(new_stencil_dict)
        for if_name, if_data in new_interfaces.items():
            copyof_base_dict['interfaces'][if_name].update(if_data)

        self.registry[stencil_name] = copyof_base_dict

    def define_stencil(self, all_stencil_defs, stencil_name, stencil_def):
        if 'base' in stencil_def:
            self._make_extended_stencil(all_stencil_defs=all_stencil_defs,
                                        stencil_name=stencil_name,
                                        stencil_def=stencil_def)
            return

        self._make_stencil(stencil_name=stencil_name, stencil_def=stencil_def)

    def load(self, stencils_defs):
        for stencil_name, stencil_def in stencils_defs.items():
            self.define_stencil(all_stencil_defs=stencils_defs,
                                stencil_name=stencil_name,
                                stencil_def=stencil_def)

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
