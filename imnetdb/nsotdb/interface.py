from arango.exceptions import AQLQueryExecuteError
from imnetdb.nsotdb.node_utils import DictKeyCollection
from first import first
from string import Template

class InterfaceNodes(DictKeyCollection):

    COLLECTION_NAME = 'Interface'

    def ensure(self, key, used=False, **fields):
        """
        Ensure the interface exists.  The key is a dict that contains the device, name values.
        The key can identify the device either by name 'device' or by the 'device_node' specifically.

        Parameters
        ----------
        key : dict
            device : str (optional)
                The name of the Device node

            device_node : dict (optional)
                The Device node dict
            name : str
                The interface name

        used : bool
            The initial state of interface used field.  Default is False.  Use
            the :meth:`allocate` to obtain unused interfaces.

        fields : dict
            user-defined collection of fields to assign to this interface

        Returns
        -------
        dict
            The interface node dict
        """
        dev_node = key.get('device_node') or self.client.devices[key['device']]
        if_node = super(InterfaceNodes, self).ensure(
            dict(device=dev_node['name'], name=key['name']),
            used=used, **fields)
        self.client.ensure_edge((dev_node, 'equip_interface', if_node))
        return if_node

    # _query_allocate_interface = """
    # LET update_fields = MERGE(
    #     {used: true},
    #     @update_fields
    # )
    #
    # LET if_node_list = (
    #     FOR interface in Interface
    #         FILTER interface.device == @device_name and interface.used == false
    #         LIMIT @count
    #         UPDATE interface WITH update_fields IN Interface
    #         OPTIONS { keepNull: false }
    #         return NEW
    # )
    #
    # RETURN LENGTH(if_node_list) == @count ? if_node_list : FAIL("Count not allocated")
    # """

    _query_allocate_interface_fields = """
    LET update_fields = MERGE(
        {used: true},
        @update_fields
    )

    """

    _query_allocate_interface_filter_any = """
    LET if_node_list = (
        FOR interface in Interface
            FILTER interface.device == @device_name and interface.used == false
            LIMIT @count
            UPDATE interface WITH update_fields IN Interface
            OPTIONS { keepNull: false }
            return NEW
    )
    """

    _query_allocate_interface_filter_speed = """
    LET if_node_list = (
        FOR interface in Interface
            FILTER interface.device == @device_name and 
                   interface.used == false and 
                   interface.speed == @speed
            LIMIT @count
            UPDATE interface WITH update_fields IN Interface
            OPTIONS { keepNull: false }
            return NEW
    )
    """

    _query_allocate_interface_filter_user_defined = Template("""
    LET if_node_list = (
        FOR interface in Interface
            FILTER interface.device == @device_name
            FILTER ${user_defined_filter} 
            LIMIT @count
            UPDATE interface WITH update_fields IN Interface
            OPTIONS { keepNull: false }
            return NEW
    )
    """)

    _query_allocate_interface_return = """

    RETURN LENGTH(if_node_list) == @count ? if_node_list : FAIL("Count not allocated")    
    """

    def allocate(self, device_name, count, speed=None, filters=None, **fields):
        """
        Allocate the `count` number of unused interfaces; i.e. find those that are 'used == False'
        and also matching other filters criteria.  If the number of interfaces cannot be allocated
        then this method will return None.  If the interfaces are allocated, then the 'used' field
        will be set to True, any specific `fields` provided will be assigned, and the list of
        Interface node dicts will be returned.

        Parameters
        ----------
        device_name : str
            The name of the device

        count : int
            The number of interfaces to reserve

        speed : int (optional)
            The interface speed to match on

        filters : str (optional)
            The AQL FILTERS expression used to match.  The FILTER variable
            name to reference is "interface".  For example, if you have an
            Interface node with a field called "role", then you could
            create a filters expression 'interface.role == "server"'

        Other Parameters
        ----------------
        The `fields` kwargs allows you to define new fields to set into the interface
        nodes as they are being allocated.  If you set a key value to None, then
        it will remove the field if it exists.

        Returns
        -------
        None
            If the number of interfaces matching the criteria cannot be allocated.

        list[dict]
            The list of Interface node dict of those matched & updated.
        """

        bind_vars = {
            'device_name': device_name,
            'count': count,
            'update_fields': fields or {}
        }

        def _use_any():
            return self._query_allocate_interface_filter_any

        def _use_speed():
            bind_vars['speed'] = speed
            return self._query_allocate_interface_filter_speed

        def _use_filters():
            return self._query_allocate_interface_filter_user_defined.substitute(
                user_defined_filter=filters)

        def _use_filters_and_speed():
            return self._query_allocate_interface_filter_user_defined.substitute(
                user_defined_filter=filters + " and interface.speed == {}".format(speed))

        filter_jump_table = {
            (False, False): _use_any,
            (True, False): _use_speed,
            (False, True): _use_filters,
            (True, True): _use_filters_and_speed
        }

        query_filter = filter_jump_table[(speed is not None, filters is not None)]()

        query_expr = (self._query_allocate_interface_fields +
                      query_filter +
                      self._query_allocate_interface_return)

        try:
            return first(self.query(query_expr, bind_vars=bind_vars))
        except AQLQueryExecuteError:
            return None

    _query_mark_unused_all = """
    FOR interface in Interface
        FILTER interface.device == @device_name and interface.used == true
        UPDATE interface WITH {
            used: false
        } IN Interface
        return NEW    
    """

    def mark_unused_all(self, device_name):
        """
        Find all interfaces that have used == True and set them to used == False.

        Parameters
        ----------
        device_name : str
            The Device name

        Returns
        -------
        list[dict]
            The list of Interface node dict that were marked unused.
        """

        return list(self.query(self._query_mark_unused_all, bind_vars={
            'device_name': device_name
        }))
