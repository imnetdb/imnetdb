
from imnetdb.gdb.node_utils import NamedCollection


class DeviceGroupNodes(NamedCollection):
    COLLECTION_NAME = 'DeviceGroup'

    _query_ensure_device_in_group = """
    UPSERT { _from: @rel._from, _to: @rel._to }
    INSERT @rel
    UPDATE @rel
    IN @@edge_name
    RETURN { doc: NEW, old: OLD }
    """

    def add_device(self, group_node, device_node):
        self.exec(self._query_ensure_device_in_group, bind_vars={
            'rel': dict(_from=device_node['_id'], _to=group_node['_id']),
            '@edge_name': 'device_member'
        })

    def del_device(self, group_node, device_node):
        self.gdb.db.collection('device_member').delete_match(filters={
            '_from': device_node['_id'],
            '_to': group_node['_id']
        })
