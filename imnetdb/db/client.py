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
from pkg_resources import iter_entry_points

from first import first

from imnetdb.rpools import RPoolsDB

__all__ = ['IMNetDB']


class IMNetDB(RPoolsDB):
    """
    About IMNetDB
    -------------
    # TODO: write this up.
    """

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

        self.db_model_name = db_model_name
        self.db_model = None
        self.graph = None

        super(IMNetDB, self).__init__(password=password, user=user, db_name=db_name,
                                      host=host, port=port, connect_timeout=connect_timeout)

    def _init_collection_handlers(self):
        for ep in iter_entry_points('imnetdb_collections'):
            cls = ep.load()
            setattr(self, ep.name, cls(client=self))

    def ensure_database(self):
        """
        Ensure that the database exists, ensuring each collection exists as referenced by
        the database mode, as well as a master graph instance.

        Notes
        -----
        Overrides base class, called from :meth:`__init__`.
        """

        super(IMNetDB, self).ensure_database()

        # using the db_mode_name, lookup the registered database model, and then ensure
        # the database collections defined by that model exist in the database.

        db_ep = first(iter_entry_points('imnetdb_database_models', self.db_model_name))
        if not db_ep:
            raise RuntimeError("Unable to load database model {}".format(self.db_model_name))

        self.db_model = db_ep.load()

        for node_type in self.db_model['nodes']:
            if not self.db.has_collection(node_type):
                self.db.create_collection(node_type)

        for _from_node, edge_col, _to_node in self.db_model['edges']:
            if not self.db.has_collection(edge_col):
                self.db.create_collection(edge_col, edge=True)

        # finally, ensure that a master graph exists that includes all of the nodes/edge defined
        # in the model.

        self.ensure_master_graph()
        self._init_collection_handlers()

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
