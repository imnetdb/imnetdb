from ipaddress import ip_network
from itertools import chain


def test_rpools_batch_match(rpoolsdb):

    pool = rpoolsdb.resource_pool('loopbacks')

    # add 30 hosts to the pool.

    pool.add_batch(ip_network('9.9.1.0/27').hosts(), rt_name='global')
    pool.add_batch(ip_network('9.9.1.0/27').hosts(), rt_name='private')

    got_spine = pool.take_batch(10, match={'rt_name': 'private'}, role='spine')
    got_leaf = pool.take_batch(15, match={'rt_name': 'global'}, role='leaf')

    assert len(got_spine) == 10
    assert len(got_leaf) == 15

    assert all(item['role'] == 'spine' for item in got_spine)
    assert all(item['rt_name'] == 'private' for item in got_spine)

    assert all(item['role'] == 'leaf' for item in got_leaf)
    assert all(item['rt_name'] == 'global' for item in got_leaf)

    # put back all of the nodes we too.  but do not clear the user defined fields
    pool.put_batch(chain.from_iterable([got_spine, got_leaf]), clear_fields=False)


def test_rpools_take_match(rpoolsdb):
    rpoolsdb.reset_database()
    pool = rpoolsdb.resource_pool('loopbacks')

    pool.add_batch(ip_network('9.9.1.0/27').hosts(), rt_name='global')
    pool.add_batch(ip_network('9.9.1.0/27').hosts(), rt_name='private')

    # "take-1" ... we are going to take by a given name, matching criteria on
    # the routing table name, and then set the role into the taken pool item.

    # save these for comparison for taking again

    t1_s_e0 = pool.take({'s:if_name': 'eth0'}, match={'rt_name': 'global'}, role='spine')
    t1_s_e1 = pool.take({'s:if_name': 'eth1'}, match={'rt_name': 'global'}, role='spine')
    spine_if_list = (t1_s_e0, t1_s_e1)

    t1_l_e0 = pool.take({'l:if_name': 'eth0'}, match={'rt_name': 'private'}, role='leaf')
    t1_l_e1 = pool.take({'l:if_name': 'eth1'}, match={'rt_name': 'private'}, role='leaf')
    leaf_if_list = (t1_l_e0, t1_l_e1)

    # ensure we got what we expect

    assert all(item['role'] == 'spine' and item['rt_name'] == 'global' for item in spine_if_list)
    assert all(item['role'] == 'leaf' and item['rt_name'] == 'private' for item in leaf_if_list)

    # "take-2" ... for idempotent check

    # spine interfaces

    t2_s_e0 = pool.take({'s:if_name': 'eth0'})
    t2_s_e1 = pool.take({'s:if_name': 'eth1'})

    assert t1_s_e0 == t2_s_e0
    assert t1_s_e1 == t2_s_e1

    # leaf interfaces

    t2_l_e0 = pool.take({'l:if_name': 'eth0'})
    t2_l_e1 = pool.take({'l:if_name': 'eth1'})

    assert t1_l_e0 == t2_l_e0
    assert t1_l_e1 == t2_l_e1

