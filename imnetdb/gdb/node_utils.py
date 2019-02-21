from first import first
from copy import deepcopy


class NamedCollection(object):

    COLLECTION_NAME = None

    def __init__(self, gdb):
        self.gdb = gdb
        self.col = gdb.db.collection(self.COLLECTION_NAME)
        self.exec = gdb.db.aql.execute

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
        return self.col.get(name)
