from itertools import islice
from ipaddress import ip_network


def test_basci_routing_table(imnetdb):
    db_rt = imnetdb.routing_tables
    db_ip_net = imnetdb.ip_net_addrs
    db_ip_host = imnetdb.ip_host_addrs

    # create a routing table called "global"

    rt_global = db_rt.ensure('global')

    # create a network address "192.168.10.0/24" into the global routing table

    this_net = ip_network('192.168.10.0/24')
    db_ip_net.ensure((rt_global, str(this_net)))

    # now add the first 10 host address

    host_ip_nodes = [
        db_ip_host.ensure((rt_global, str(ip_host)))
        for ip_host in islice(this_net.hosts(), 0, 10)
    ]

    # now get the IPAddress members in the global rt and ensure a match with
    # what we added.

    members = db_rt.get_host_members(rt_global)
    assert [h['name'] for h in members] == [h['name'] for h in host_ip_nodes]

    # now get the IPNetwork members in the global rt and ensure a match with
    # what we added.

    members = db_rt.get_network_members(rt_global)
    assert [n['name'] for n in members] == [str(this_net)]
