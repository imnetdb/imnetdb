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

    def __init__(self, password, user='root', db_name='rpools',
                 host='0.0.0.0', port=8529, connect_timeout=10):
        """
        Create a client instance to the IMNetDB stored within the ArangoDB server.  If the database
        does not exist, then it will be created, using the registered the database model (nodes/edges) name.
        For reference, the basic database model is located in the basic_db_model.py file.

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
        return ResourcePool(client=self, collection_name=pool_name, value_type=value_type)
