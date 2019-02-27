from ipaddress import ip_network
from itertools import chain


def test_rpools_basic_loopback(rpoolsdb):

    pool = rpoolsdb.resource_pool('loopbacks')

    # add 30 hosts to the pool.

    pool.add(ip_network('9.9.1.0/27').hosts(), rt_name='global')

    got1 = pool.take_batch(10, role='spine')
    got2 = pool.take_batch(15, role='leaf')

    assert len(got1) == 10
    assert len(got2) == 15

    assert all(item['role'] == 'spine' for item in got1)
    assert all(item['role'] == 'leaf' for item in got2)

    # put back all of the nodes we too.  but do not clear the user defined fields

    pool.put_batch(chain.from_iterable([got1, got2]), clear_fields=False)
