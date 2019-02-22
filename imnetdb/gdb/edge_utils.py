query_ensure_edge = """
UPSERT { _from: @rel._from, _to: @rel._to }
INSERT @rel
UPDATE @rel
IN @@edge_name
RETURN { doc: NEW, old: OLD }
"""


def ensure_edge(db, edge, present=True):
    """
    Ensure that an edge relationship either exists (preset=True) or does not.

    Parameters
    ----------
    db : StandardDatabase
    edge
    present

    Returns
    -------

    """

    self.exec(rel_utils.query_ensure_member_in_group, bind_vars={
        'rel': dict(_from=device_node['_id'], _to=group_node['_id']),
        '@edge_name': 'device_member'
    })
    pass

