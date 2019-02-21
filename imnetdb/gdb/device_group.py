from first import first
from copy import deepcopy


class DeviceGroup(object):

    COLLECTION_NAME = 'DeviceGroup'

    def __init__(self, gdb):
        self.gdb = gdb
        self.col = gdb.db.collection(self.COLLECTION_NAME)
        self.exec = gdb.db.aql.execute

    _aql_ensure_device_group = """
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
        result = first(self.exec(self._aql_ensure_device_group, bind_vars={
            'fields': _fields,
            '@col_name': self.COLLECTION_NAME
        }))

        return result['doc']

    def __iter__(self):
        return self.col.all()

    def __getitem__(self, name):
        return self.col.get(name)
