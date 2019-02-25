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

from collections import defaultdict
import retrying
from first import first

from arango import ArangoClient
from arango.exceptions import ServerConnectionError
from pkg_resources import iter_entry_points


__all__ = ['IMNetDB']


class IMNetDB(object):

    def __init__(self, password, user='root',
                 db_name='imnetdb', db_model_name='basic',
                 host='0.0.0.0', port=8529, connect_timeout=10):
        """
        Create a client instance to the IMNetDB stored within the ArangoDB server.  If the database
        does not exist, then it will be created, using the registered the database model (nodes/edges) name.
        For reference, the basic database model is located in the basic_db_model.py file.

        Parameters
        ----------
        password : str
            The login password value

        user : str (optional)
            The login user-name, defaults to 'root'

        db_name : str (optional)
            The name of the database

        db_model_name : str (optional)
            The name of the database model.  This corresponds to a registered name
            that defines the database nodes and edges

        host : str (optional)
            The ArangoDB server host-name or ip-addr

        port : int (optional)
            The ArangoDB server port value

        connect_timeout : int (optional)
            When connecting to the ArangoDB server, this value defines the timeout in seconds
            before aborting.
        """

        self._user = user
        self._password = password

        self._arango = ArangoClient(host=host, port=port)
        self._sysdb = self._arango.db('_system', username=self._user, password=self._password)

        self.db_name = db_name
        self.db_model_name = db_model_name
        self.db_model = None

        self.db = None
        self.graph = None
        self.query = None

        @retrying.retry(retry_on_exception=lambda e:  isinstance(e, ServerConnectionError),
                        stop_max_delay=connect_timeout * 1000)
        def _await_arangodb_server():
            self._sysdb.ping()

        _await_arangodb_server()
        self.ensure_database()
        self._bind_entry_points()

    def _bind_entry_points(self):
        for ep in iter_entry_points('imnetdb_collections'):
            cls = ep.load()
            setattr(self, ep.name, cls(client=self))

    def reset_database(self):
        self.wipe_database()
        self.ensure_database()

    def wipe_database(self):
        self._sysdb.delete_database(self.db_name, ignore_missing=True)

    def ensure_master_graph(self, graph_name='master'):

        if not self.db.has_graph(graph_name):
            build = defaultdict(lambda: dict(from_vertex_collections=set(), to_vertex_collections=set()))

            for from_vc, edge_name, to_vc in self.db_model['edges']:
                build[edge_name]['from_vertex_collections'].add(from_vc)
                build[edge_name]['to_vertex_collections'].add(to_vc)

            edge_definitions = [dict(edge_collection=edge_name,
                                     from_vertex_collections=list(vc['from_vertex_collections']),
                                     to_vertex_collections=list(vc['to_vertex_collections']))
                                for edge_name, vc in build.items()]

            self.db.create_graph(graph_name, edge_definitions=edge_definitions)

        self.graph = self.db.graph(graph_name)

    def ensure_database(self):
        db_ep = first(iter_entry_points('imnetdb_database_models', self.db_model_name))
        if not db_ep:
            raise RuntimeError("Unable to load database model {}".format(self.db_model_name))

        self.db_model = db_ep.load()
        if not self._sysdb.has_database(self.db_name):
            self._sysdb.create_database(self.db_name, users=[
                dict(username=self._user, password=self._password, active=True)])

        self.db = self._arango.db(self.db_name, username=self._user, password=self._password)
        self.query = self.db.aql.execute

        for node_type in self.db_model['nodes']:
            if not self.db.has_collection(node_type):
                self.db.create_collection(node_type)

        for _from_node, edge_col, _to_node in self.db_model['edges']:
            if not self.db.has_collection(edge_col):
                self.db.create_collection(edge_col, edge=True)

        self.ensure_master_graph()

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
