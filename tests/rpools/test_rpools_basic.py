from ipaddress import ip_network
# from itertools import chain


def test_rpools_add_batch_idempotent(rpoolsdb):

    pool = rpoolsdb.resource_pool('idaddbatch')
    pool.reset()

    pool.add_batch(ip_network('9.9.1.0/28').hosts(), rt_name='global')
    pool.add_batch(ip_network('9.9.1.0/28').hosts(), rt_name='private')

    total_count0 = pool.col.count()

    # add the same set of batches

    pool.add_batch(ip_network('9.9.1.0/28').hosts(), rt_name='global')
    pool.add_batch(ip_network('9.9.1.0/28').hosts(), rt_name='private')

    total_count1 = pool.col.count()

    assert total_count0 == total_count1


def test_rpools_idempodent_add_individual(rpoolsdb):
    pool = rpoolsdb.resource_pool('idadd')
    pool.col.truncate()

    pool.add('red', used=True, group='one')
    pool.add('red', group='two')
    pool.add('green')
    pool.add('blue')

    count0 = pool.col.count()

    # add them all again.

    pool.add('red', group='one')
    pool.add('red', group='two')
    pool.add('green')
    pool.add('blue')

    total_items = pool.col.count()
    assert total_items == 4

    # try to add a value that has duplicates

    pool.add('red', group='three')
    count1 = pool.col.count()

    assert count1 == count0 + 1


def test_rpools_basic_batch_usage(rpoolsdb):

    pool = rpoolsdb.resource_pool('loopbacks')

    # add 30 hosts to the pool.

    pool.add_batch(ip_network('9.9.1.0/28').hosts(), rt_name='global')
    pool.add_batch(ip_network('9.9.1.0/28').hosts(), rt_name='private')

    got1 = pool.take_batch(10, role='spine')
    got2 = pool.take_batch(15, role='leaf')

    assert len(got1) == 10
    assert len(got2) == 15

    assert all(item['role'] == 'spine' for item in got1)
    assert all(item['role'] == 'leaf' for item in got2)

    # put back all of the nodes we too.  but do not clear the user defined fields

    # pool.put_batch(chain.from_iterable([got1, got2]), clear_fields=False)

