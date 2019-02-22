from first import first
from copy import deepcopy


class NamedCollection(object):

    COLLECTION_NAME = None

    def __init__(self, client):
        self.gdb = client
        self.col = client.db.collection(self.COLLECTION_NAME)
        self.exec = client.db.aql.execute

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
        result = first(self.exec(self.__aql_ensure_node, bind_vars={
            'fields': _fields,
            '@col_name': self.COLLECTION_NAME
        }))

        return result['doc']

    def __iter__(self):
        return self.col.all()

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
