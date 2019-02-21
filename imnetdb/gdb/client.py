import retrying
from arango import ArangoClient
from arango.exceptions import ServerConnectionError
from imnetdb.gdb import models

from imnetdb.gdb.device_group import DeviceGroupNodes
from imnetdb.gdb.device import DeviceNodes

__all__ = ['GDBClient']


class GDBClient(object):

    def __init__(self, password, user='root', db_name='imnetdb', host='0.0.0.0', port=8529, timeout=10):

        self._arango = ArangoClient(host=host, port=port)
        self._sysdb = self._arango.db('_system', username=user, password=password)

        self.db = None
        self.db_name = db_name
        self.graph = None
        self._user = user
        self._password = password

        @retrying.retry(retry_on_exception=lambda e:  isinstance(e, ServerConnectionError),
                        stop_max_delay=timeout * 1000)
        def _await_arange_server():
            self._sysdb.ping()

        _await_arange_server()
        self.ensure_database()

        self.devices = DeviceNodes(gdb=self)
        self.device_groups = DeviceGroupNodes(gdb=self)

    def wipe_database(self):
        self._sysdb.delete_database(self.db_name, ignore_missing=True)

    def ensure_database(self):
        if not self._sysdb.has_database(self.db_name):
            self._sysdb.create_database(self.db_name, users=[
                dict(username=self._user, password=self._password, active=True)])

        self.db = self._arango.db(self.db_name, username=self._user, password=self._password)

        for node_type in models.nodes_types:
            if not self.db.has_collection(node_type):
                self.db.create_collection(node_type)

        for _from_node, edge_col, _to_node in models.rel_types:
            if not self.db.has_collection(edge_col):
                self.db.create_collection(edge_col, edge=True)

        if not self.db.has_graph('master'):
            self.db.create_graph('master', edge_definitions=[
                dict(edge_collection=edge_col,
                     from_vertex_collections=[_from_node],
                     to_vertex_collections=[_to_node])
                for _from_node, edge_col, _to_node in models.rel_types
            ])

        self.graph = self.db.graph('master')