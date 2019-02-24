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

import retrying
from arango import ArangoClient
from arango.exceptions import ServerConnectionError
from imnetdb.db import models

from imnetdb.db.device import DeviceNodes, DeviceGroupNodes
from imnetdb.db.interface import InterfaceNodes
from imnetdb.db.cabling import CableNodes
from imnetdb.db.lag import LAGNodes
from imnetdb.db.vlan import VlanNodes, VlanGroupNodes

__all__ = ['IMNetDB']


class IMNetDB(object):

    def __init__(self, password, user='root', db_name='imnetdb',
                 host='0.0.0.0', port=8529, timeout=10):

        self._arango = ArangoClient(host=host, port=port)
        self._sysdb = self._arango.db('_system', username=user, password=password)

        self.db = None
        self.db_name = db_name
        self.graph = None
        self.query = None

        self._user = user
        self._password = password

        @retrying.retry(retry_on_exception=lambda e:  isinstance(e, ServerConnectionError),
                        stop_max_delay=timeout * 1000)
        def _await_arange_server():
            self._sysdb.ping()

        _await_arange_server()
        self.ensure_database()

        self.device_groups = DeviceGroupNodes(client=self)
        self.devices = DeviceNodes(client=self)
        self.interfaces = InterfaceNodes(client=self)
        self.cabling = CableNodes(client=self)
        self.lags = LAGNodes(client=self)
        self.vlans = VlanNodes(client=self)
        self.vlan_groups = VlanGroupNodes(client=self)

    def reset_database(self):
        self.wipe_database()
        self.ensure_database()

    def wipe_database(self):
        self._sysdb.delete_database(self.db_name, ignore_missing=True)

    def ensure_database(self):
        if not self._sysdb.has_database(self.db_name):
            self._sysdb.create_database(self.db_name, users=[
                dict(username=self._user, password=self._password, active=True)])

        self.db = self._arango.db(self.db_name, username=self._user, password=self._password)
        self.query = self.db.aql.execute

        for node_type in models.nodes_types:
            if not self.db.has_collection(node_type):
                self.db.create_collection(node_type)

        for _from_node, edge_col, _to_node in models.edge_defs:
            if not self.db.has_collection(edge_col):
                self.db.create_collection(edge_col, edge=True)

        if not self.db.has_graph('master'):
            self.db.create_graph('master', edge_definitions=[
                dict(edge_collection=edge_col,
                     from_vertex_collections=[_from_node],
                     to_vertex_collections=[_to_node])
                for _from_node, edge_col, _to_node in models.edge_defs
            ])

        self.graph = self.db.graph('master')

    _query_ensure_edge = """
    UPSERT { _from: @rel._from, _to: @rel._to }
    INSERT @rel
    UPDATE @rel
    IN @@edge_name
    RETURN { doc: NEW, old: OLD }
    """

    def ensure_edge(self, edge, present=True):
        """
        Ensure that an edge relationship either exists (present=True) or does not
        (present=False).

        Parameters
        ----------
        edge : tuple
            (from_node_dict, edge_col_name, to_node_dict)

        present : bool
            If True ensure the edge exists.
            If False ensure the edge does not exist.
        """
        from_node, edge_col, to_node = edge

        if present is True:
            self.query(self._query_ensure_edge, bind_vars={
                'rel': dict(_from=from_node['_id'], _to=to_node['_id']),
                '@edge_name': edge_col
            })
        else:
            self.db.collection(edge_col).delete_match(filters={
                '_from': from_node['_id'],
                '_to': to_node['_id']
            })
