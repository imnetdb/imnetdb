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

from imnetdb.db.collection import PeeringCollection


class LACPNodes(PeeringCollection):
    """
    LACP nodes form a peering relationship between LAG nodes using edge "lacp_member"
    """
    COLLECTION_NAME = 'LACP'
    MEMBER_COLLECTION_NAME = 'LAG'
    EDGE_NAME = 'lacp_member'
