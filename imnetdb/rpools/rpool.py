from first import first


class ResourcePool(object):

    def __init__(self, client, collection_name, value_type=str):
        self.client = client
        self.db = client.db
        self.query = client.query
        self.col = client.ensure_collection(collection_name)
        self.value_type = value_type

    def __iter__(self):
        return self.col.all()

    _query_add_new_items = """
    FOR item IN @items
        INSERT 
            MERGE({value: item}, @user_defined_fields)
        INTO @@col_name
    """

    def add(self, items, used=False, **fields):
        """
        Add new items into the pool so that they can be later taken.

        Parameters
        ----------
        items : Iterable

        used : bool (optional)
            The initial used state

        Other Parameters
        ----------------
        fields are a comment set of values that will be stored into all items.
        """

        actual_items = [self.value_type(item) for item in items]
        user_defined_fields = dict(fields, used=used)

        self.query(self._query_add_new_items, bind_vars={
            '@col_name': self.col.name,
            'items': actual_items,
            'user_defined_fields': user_defined_fields
        })

    _query_take_key = """
    LET find_key = MERGE(@user_key, {used: true})
    
    LET found = FIRST(
        FOR pool_item IN @@col_name
            FILTER MATCHES(pool_item, find_key)
            LIMIT 1
            RETURN pool_item
    )
    
    LET runQuery = found != null ? [] : [1]
    
    LET alternative = FIRST(FOR dummy IN runQuery 
        FOR pool_item IN @@col_name
            FILTER pool_item.used == false
            LIMIT 1
            UPDATE pool_item WITH MERGE(
                {used: true},
                @user_key,
                @user_defined_fields)
            INTO @@col_name
            RETURN NEW
    )
    
    RETURN found ? {doc: found, exists: true} : {doc: alternative, new: true}
    """

    def take(self, key, **fields):
        """
        Take an item from the pool that has a specific key value; if such a key does not exist, then
        take an unused item and assign the key.  Include/update the item with any additional field kwargs

        Parameters
        ----------
        key : dict
            The fields that make a unique identity within the pool.

        Other Parameters
        ----------------
        fields, if provided, will be updated into the item.

        Returns
        -------
        dict
            The item node dict
        """

        # TODO: may need to add control for allowing the call to determine the used state, rather
        # TODO: than hardcoding the query to check for true in the find_key.

        bind_vars = {
            '@col_name': self.col.name,
            'user_key': key,
            'user_defined_fields': fields
        }

        found = first(self.query(self._query_take_key, bind_vars=bind_vars))
        doc = found['doc']

        # if there are no more items in the pool, then return None now.

        if not doc:
            return None

        # if the item is new, then it contains all of the fields provided.  if it is an existing
        # item, and no new fields provided by caller, then we can return the doc now.

        if ('new' in found) or (not fields):
            return doc

        # if here, then caller has provided fields, and the existing doc may need to be
        # updated.  if all of the fields exist as they are, then no update, otherwise do an update

        fields_exist = all(f in doc and doc[f] == v for f, v in fields.items())
        return doc if fields_exist else self.col.update(dict(doc, **fields), return_new=True)['new']

    _query_take_batch = """
    FOR pool_item in @@col_name
        FILTER pool_item.used == false
        LIMIT @count
        UPDATE pool_item 
            WITH MERGE({used: true}, @user_defined_fields)
        INTO @@col_name
        RETURN NEW
    """

    def take_batch(self, count=1, **fields):
        """
        Take a batch of count items from the pool.  Any additional fields will be stored within all
        items as they are taken.  If you want to "key" each item, you will need to make a subsequent call
        to add keys to each item.  Suggest using :meth:`self.col.update_many` for this purpose.

        The total number of returned items may **not** be the requested `count` value.  The caller is required
        to check the length of the returned.

        Parameters
        ----------
        count : int (optional)
            The number of items to take from the pool.

        Other Parameters
        ----------------
        fields are user-defined kwargs to store into all of the items.

        Returns
        -------
        list[dict]
            List of allocated nodes
        """

        return list(self.query(self._query_take_batch, bind_vars={
            '@col_name': self.col.name,
            'count': count,
            'user_defined_fields': fields
        }))

    _query_reset_clear_fields = """
    FOR pool_item in @@col_name
        REPLACE pool_item 
            WITH { used: false, value: pool_item.value } 
        INTO @@col_name    
    """

    _query_reset_noclear_fields = """    
    FOR pool_item in @@col_name
        UPDATE pool_item 
            WITH { used: false } 
        INTO @@col_name    
    """

    def reset(self, clear_fields=True):
        """
        This call will reset all pool items to unused.  If `clear_fields` is True then any user defined
        fields will be removed from all of the items.  If `clear_fields` is False, then the fields that exist
        in each item will remain.

        Parameters
        ----------
        clear_fields : bool
            See description
        """
        self.query(self._query_reset_clear_fields if clear_fields else self._query_reset_noclear_fields,
                   bind_vars={'@col_name': self.col.name})

    _query_put_clear_fields = """
    LET doc = DOCUMENT(@doc_id)
    REPLACE doc WITH {used: false, value: doc.value} INTO @@col_name
    RETURN NEW
    """

    def put(self, item_node, clear_fields=True):
        """
        Put (return) a node back into the pool.

        Parameters
        ----------
        item_node : dict
            The pool item node dict

        clear_fields : bool (optional)
            When True, the all user defined fields are removed
            When False, only the used field is set to False, user defined fields not removed

        Returns
        -------
        dict
            The updated (used=False) pool item node dict
        """
        if clear_fields is True:
            return first(self.query(self._query_put_clear_fields, bind_vars={
                '@col_name': self.col.name,
                'doc_id': item_node['_id']
            }))

        item_node['used'] = False
        return self.col.update(item_node, return_new=True)['new']

    _query_put_batch_clear_fields = """
    FOR pool_id in @pool_id_list
        LET pool_item = DOCUMENT(pool_id)
        REPLACE pool_item 
            WITH { used: false, value: pool_item.value } 
        INTO @@col_name    
    """

    _query_put_batch_noclear_fields = """    
    FOR pool_id in @pool_id_list
        LET pool_item = DOCUMENT(pool_id)
        UPDATE pool_item 
            WITH { used: false } 
        INTO @@col_name    
    """

    def put_batch(self, items, clear_fields=True):
        pool_id_list = [p['_id'] for p in items]

        query = self._query_put_batch_clear_fields if clear_fields else self._query_put_batch_noclear_fields

        self.query(query, bind_vars={
            'pool_id_list': pool_id_list,
            '@col_name': self.col.name
        })
