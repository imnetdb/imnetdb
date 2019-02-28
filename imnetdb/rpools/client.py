# Copyright 2019 Jeremy Schulman, nwkautomaniac@gmail.com
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


from imnetdb.db.common_client import CommonDBClient
from imnetdb.rpools.rpool import ResourcePool


__all__ = ['RPoolsDB']


class RPoolsDB(CommonDBClient):
    """
    About Using a Resource Database
    -------------------------------
    # TODO: need to write this up.
    """

    def __init__(self, password, user='root', db_name='rpools',
                 host='0.0.0.0', port=8529, connect_timeout=10):
        """
        Create a client instance to the RPoolsDB stored within the ArangoDB server.  If the database
        does not exist, then it will be created.  Once available, the caller can then define new
        collections in the database using  :meth:`resource_pool`.

        Parameters
        ----------
        password : str
            The login password value

        user : str (optional)
            The login user-name, defaults to 'root'

        db_name : str (optional)
            The name of the database

        host : str (optional)
            The ArangoDB server host-name or ip-addr

        port : int (optional)
            The ArangoDB server port value

        connect_timeout : int (optional)
            When connecting to the ArangoDB server, this value defines the timeout in seconds
            before aborting.
        """
        super(RPoolsDB, self).__init__(password=password, user=user, db_name=db_name,
                                       host=host, port=port, connect_timeout=connect_timeout)

    def resource_pool(self, pool_name, value_type=str):
        """
        Ensure that a resource pool (database collection) exists by the given `pool_name`.  If it does not
        exist, then it will be created.

        Parameters
        ----------
        pool_name : str
            The pool name.

        value_type : type (optional)
            The item value type, by default is a string.  This property is used when adding
            new items to the pool.  The value_type will be called against each item to ensure
            that it stored as the type desired.  Therefore, the caller could provide any
            callable, providing it returns a value that can be stored within the ArangoDB document.

        Returns
        -------
        ResourcePool
            An instance of the resource pool.
        """
        return ResourcePool(client=self, collection_name=pool_name, value_type=value_type)
