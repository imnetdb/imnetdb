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


from collections import defaultdict
from bracket_expansion import bracket_expansion


def make_device(imnetdb, device_name):
    dataset = defaultdict(dict)

    device_node = imnetdb.devices.ensure(device_name)
    dataset['device'][device_name] = device_node

    for if_name in bracket_expansion("Ethernet[1-48]"):
        if_node = imnetdb.interfaces.ensure((device_node, if_name), speed=10, role='server')
        dataset['interface'][if_name] = if_node

    for if_name in bracket_expansion("Ethernet[49-56]"):
        if_node = imnetdb.interfaces.ensure((device_node, if_name), speed=100, role='fabric')
        dataset['interface'][if_name] = if_node

    return dataset


def test_basic_pass(imnetdb):
    dataset = make_device(imnetdb, 'spine1')

