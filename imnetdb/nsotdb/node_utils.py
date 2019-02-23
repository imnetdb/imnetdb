"""
Copyright 2019 Jeremy Schulman, nwkautomaniac@gmail.com

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

   http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

from first import first
from copy import deepcopy


class CommonCollection(object):
    COLLECTION_NAME = None

    def __init__(self, client):
        self.client = client
        self.db = client.db
        self.col = client.db.collection(self.COLLECTION_NAME)
        self.query = client.db.aql.execute

    def __iter__(self):
        return self.col.all()

    def remove(self, node):
        vert_col = self.client.graph.vertex_collection(self.COLLECTION_NAME)
        vert_col.delete(node)


class DictKeyCollection(CommonCollection):

    __aql_ensure_node = """
    UPSERT @key
    INSERT @fields
    UPDATE @fields
    IN @@col_name OPTIONS {keepNull: False}
    RETURN {doc: NEW, old: OLD}
    """

    def ensure(self, key, **fields):
        _fields = deepcopy(fields)
        _fields.update(key)

        result = first(self.query(self.__aql_ensure_node, bind_vars={
            'key': key,
            'fields': _fields,
            '@col_name': self.COLLECTION_NAME
        }))

        return result['doc']

    def __getitem__(self, key_dict):
        """
        Return a document node dict that has a key value of `name`.

        Parameters
        ----------
        key_dict : dict
            Dictionary containing the fields to match on.

        Returns
        -------
        dict
            The document node dict

        None
            If there is not document matching key_dict fields.
        """
        return first(self.col.find(key_dict, limit=1))


class NameKeyCollection(CommonCollection):

    __aql_ensure_node = """
    UPSERT {_key: @fields.name}
    INSERT @fields
    UPDATE @fields
    IN @@col_name OPTIONS {keepNull: False}
    RETURN {doc: NEW, old: OLD}
    """

    def ensure(self, name, **fields):
        _fields = deepcopy(fields)
        _fields['_key'] = name
        _fields['name'] = name
        result = first(self.query(self.__aql_ensure_node, bind_vars={
            'fields': _fields,
            '@col_name': self.COLLECTION_NAME
        }))

        return result['doc']

    def __getitem__(self, name):
        """
        Return a document node dict that has a key value of `name`.

        Parameters
        ----------
        name : str,int
            The unique key value for the node

        Returns
        -------
        dict
            The document node dict

        None
            If there is not document by the given key `name`.
        """
        return self.col.get(name)
