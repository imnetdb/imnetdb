#  Copyright 2019 Jeremy Schulman, nwkautomaniac@gmail.com
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

from first import first


_query_device_extracto = """
LET $device = DOCUMENT("Device", @device_name)

LET $if_node_list = (
    FOR if_node IN OUTBOUND $device equip_interface 
        RETURN if_node
)

LET $if_node_id_list = $if_node_list[*]._id

LET $lag_node_list = (FOR if_node in $if_node_list 
    FOR lag_node in OUTBOUND if_node lag_member 
    RETURN DISTINCT lag_node
)

LET $lag_node_id_list = $lag_node_list[*]._id

LET $cabling_items = MERGE(
    FOR if_node IN $if_node_list 
    
        FOR cable IN OUTBOUND if_node cabled
            LET peer_if_node = FIRST(FOR peer_if_node IN INBOUND cable cabled
                FILTER peer_if_node != if_node
                LIMIT 1
                RETURN peer_if_node
            )
            
            RETURN {[if_node.name]: {
                    cable: KEEP(cable, ATTRIBUTES(cable, true)),
                    remote: { 
                        device: peer_if_node.device, 
                        interface: peer_if_node.name 
                    }
                }                    
            }
    )

LET $peer_name_list = (FOR item IN VALUES($cabling_items)
    COLLECT peer = item.remote.device
    RETURN DISTINCT peer
)
    
LET $device_peer_items = MERGE(FOR name IN $peer_name_list
    LET node = DOCUMENT("Device", name)
    RETURN {[node.name]: KEEP(node, MINUS(ATTRIBUTES(node, true), ["name"]))}
)

// Find VLANs that are bound to Interface | LAG nodes

LET $check_node_list = APPEND($if_node_list, $lag_node_list)


// Find IPInterface nodes that are bound to VLAN | LAG nodes

LET $ipifs_assigned_items = MERGE(
    FOR check_node in $check_node_list
        LET node_has_ips = (FOR ipif_node IN INBOUND check_node ip_assigned
            RETURN KEEP(ipif_node, ATTRIBUTES(ipif_node, true))
        )
        FILTER FIRST(node_has_ips) != null
        RETURN {[check_node._id]: node_has_ips}
)

LET $ipifs_assigned_id_list = ATTRIBUTES($ipifs_assigned_items)
LET $ipifs_addrs_list = VALUES($ipifs_assigned_items)

LET $if_used_items = MERGE(FOR pool_node in InterfaceRP
        FILTER pool_node.device == @device_name
        RETURN {[pool_node.name]: pool_node.used}
)

LET $vlans_assigned_items = MERGE(
    FOR check_node in $check_node_list
        LET node_has_vlans = FLATTEN(FOR vlan_thing IN INBOUND check_node vlan_assigned
            LET vlan_name_list = (IS_SAME_COLLECTION(vlan_thing, "VLAN") 
                    ? [vlan_thing.name]
                    : (FOR vlan IN INBOUND vlan_thing vlan_member RETURN vlan.name)
            )   
            RETURN vlan_name_list
        )
        FILTER FIRST(node_has_vlans) != null
        RETURN {[check_node._id]: node_has_vlans}
)

LET $vlans_assigned_id_list = ATTRIBUTES($vlans_assigned_items)

LET $vlan_name_list = UNIQUE(VALUES($vlans_assigned_items)[**])

LET $vlans = MERGE(FOR vlan_name in $vlan_name_list
    LET vlan_node = DOCUMENT("VLAN", vlan_name)
    
    // if IPs are assigned to the VLAN, then create an 'ipaddrs' key
    LET ipaddrs = FIRST(
        LET ip_nodes = (
            FOR ip_node IN INBOUND vlan_node ip_assigned 
            RETURN KEEP(ip_node, ATTRIBUTES(ip_node, true))
        )
        RETURN LENGTH(ip_nodes) ? {ipaddrs: ip_nodes} : {}
    )        

    RETURN {
        [vlan_name]: MERGE(
            KEEP(vlan_node, MINUS(ATTRIBUTES(vlan_node, true), ["name"])),
            ipaddrs)
    }
        
)

LET $interfaces = MERGE(FOR if_node in $if_node_list

    // if vlans are assigned to the IF, then create a 'vlans' key
    LET vlans = FIRST(RETURN if_node._id in $vlans_assigned_id_list 
        ? {vlans: $vlans_assigned_items[if_node._id]}
        : {}
    )
    
    // if ip_ifs are assigned to the IF, then create an 'ipaddrs' key
    LET ipaddrs = FIRST(RETURN if_node._id in $ipifs_assigned_id_list
        ? {ipaddrs: $ipifs_assigned_items[if_node._id]}
        : {}
    )        

    // check if this interface is used or not; if not, then set a key unused=True
    LET unused = FIRST(RETURN $if_used_items[if_node.name] ? {} : {unused: true})
        
    RETURN {[if_node.name]: MERGE(
        UNSET(if_node, ['_id', '_rev', '_key', 'name', 'device']), 
        unused,
        vlans, 
        ipaddrs)
    }
)

LET $lags = MERGE(FOR lag_node in $lag_node_list
    LET interfaces = {
        interfaces: (FOR if_node IN INBOUND lag_node lag_member RETURN if_node.name)
    }        
    
    // if vlans are assigned to the IF, then create a 'vlans' key
    LET vlans = FIRST(RETURN lag_node._id in $vlans_assigned_id_list 
        ? {vlans: $vlans_assigned_items[lag_node._id]}
        : {}
    )
    
    // if ip_ifs are assigned to the IF, then create an 'ipaddrs' key
    LET ipaddrs = FIRST(RETURN lag_node._id in $ipifs_assigned_id_list
        ? {ipaddrs: $ipifs_assigned_items[lag_node._id]}
        : {}
    )        

    RETURN {[lag_node.name]: MERGE(
        UNSET(lag_node, ['_id', '_rev', '_key', 'name', 'device']), 
        interfaces,
        vlans, 
        ipaddrs)
    }
)

RETURN {
    device: KEEP($device, ATTRIBUTES($device, true)),
    device_peers: $device_peer_items,
    cabling: $cabling_items,
    interfaces: $interfaces,
    lags: $lags,
    vlans: $vlans
}
"""

def extracto_device(db, device_name):
    """
    Device oriented data extractor.

    Parameters
    ----------
    db : IMNetDB
        The instance of the database

    device_name : str
        The device name

    Returns
    -------
    dict
        Complex dictionary of data.  Structure To Be Documented
    """

    res = first(db.query(_query_device_extracto, bind_vars={
        'device_name': device_name
    }))

    return res
