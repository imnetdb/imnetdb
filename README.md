# Why IMNetDB?

As a network automation engineer you may want to create applications that have a database backend that stores
the "source of truth" or "intent" of your network and services.  This repo contains a Python library that
uses the [ArangoDB](https://www.arangodb.com/) database software to create such application-specific backed
databases.  While every application will ultimately be different, this project provdes a common set of networking 
constructs to get started with.  

This library is meant to be a "low level" programming interface, but provide specific capabilities that are 
commonly needed for network management oriented applications.  For example, this library supports the ability
to "allocate unused interfaces" and manage "cable relationships between devices".  This library also contains 
constructs so that you, as a python developer, can create your own new database nodes and edges and extend the use 
of this repo in a way that is specific to your application.

# Why ArangoDB?

I chose AranagoDB after looking at a few other database systems.  There are many to choose from, and they each
have their own sets of pros & cons.  I selected ArangoDB for the following reasons:

  * Single database system that provide a Graph and NoSQL capabilities
  * Does not require pre-defining schemas, which lends itself well for organic changes
  * Community and Enterprise editions available
  * Docker image freely available
  * WebUI for human interaction and dev-testing 
  * Came highly recommended from a trusted colleague and network automation expert
  
For more from ArangoDB themselves, see: [Why AranagoDB](https://www.arangodb.com/why-arangodb/).  

# What Comes with IMNetDB?

## Basic Networking Building Blocks

The following constructs are provided as part of the "basic" data model.  These constructs act more as
scaffolding since there are no pre-defined schema/field definitions.  As a developer, you can choose what
fields to place in each of these node types.  In addition to these node types, the basic data model 
defines a set of relationship types.  For details refer to the file [basic_db_model.py](imnetdb/db/basic_db_model.py).
 
*Basic Device*

   * **Device** - represents a single managed device
   * **DeviceGroup** - represents a group of devices
   * **Interface** - represents a device interface
   * **Cable** - represents the connection between two device interfaces
   * **LAG** - represents Link Aggregation Groups
   * **LACP** - represents the LACP connection between LAGs

*Virtual Networking*
   
   * **VLAN** - represents a VLAN
   * **VLANGroup** - represents a group of VLANs
   
*IP management*

   * **RoutingTable** - represents a routing-table
   * **IPAddress** - represents an IPv4 or IPv6 address
   * **IPNetwork** - represents an IPv4 or IPv6 network address
   * **IPInterface** - represents an IPv4 or IPv6 interface address

## Resource Pools

Another common aspect of building a NSOT application is managing "resources" such as IP addresses, ASN values,
VLAN numbers, or any *pool* of data.  The IMNetDB library defines a Resource Pool construct that allows you to 
put/take items from your defined pools.  You can manage your Resource Pool database separately from your
application NSOT database for sharing across multiple tools you need to create.
For more details, refer to [rpools](imnetdb/rpools).

# Get Started!
   
## Before You Begin

Before using this repo you need to have the following installed on your system:

  * Python3.6
  * Docker
  
You must also have access to the Internet so that you can download the ArangoDB docker image.  
  
## Installation

This library is presently not installed in PyPi.  Therefore
you must clone and install into your environment for now.  

You should create a virtualenv and activate it before installing
this project.

````bash
$ python setup.py install
````

You will also need to have ArangoDB installed.  For convenience,
there is a [docker-compose](tests/docker-compose.yml) file located in the **tests** directory.  This
file contains the default login user password.  You can change the value in the docker-compose.yml file,
or use other ArangoDB methods to handle login user-passwords.

Presuming you have Docker installed on your system, and you have Internet access, you can
download the ArangoDB docker image and start the server using the following 
command:

```bash
$ cd tests
$ docker-compose up -d
```

At this point you should be able to open you webbrowser to the ArangoDB WebUI
page:

```bash
http://localhost:8529
```

## First Usage

The first step is to connect to the database.  If the database does not exist, it will automatically be
created based on the defined nodes and edges defined in the [models.py](imnetdb/db/basic_db_model.py) file.  You
can create different databases, each representing your specific network application.  If you do not provide
the `db_name` parameters, the default value is "imnetdb".

````python
from imnetdb import IMNetDB

client = IMNetDB(password='admin123', db_name='myappdb')
````

At this point you can then start using the client to manage the database.
For examples, you can review the files in the **tests** directory.

You can also open the WebUI to see what is created from this initial step.

Now lets create a device with some interfaces ...

````python
from imnetdb import IMNetDB

client = IMNetDB(password='admin123')

leaf = client.devices.ensure('leaf1', role='leaf', description='this is my spine')

# create 48x10g ports

for if_name in ("Ethernet{}".format(num) for num in range(1, 49)):   # range does not include stop value, so +1
    client.interfaces.ensure((leaf, if_name), speed=10)

# create 8x100g ports

for if_name in ("Ethernet{}".format(num) for num in range(1, 9):
    client.interfaces.ensure((leaf, if_name), speed=100)
````

*NOTE: There is a companion repo that is used to fabricate devices and interfaces that are specific to 
VENDOR and MODEL.  Refer to the [device-stencils](https://github.com/imnetdb/device-stencils)
project for more details*


# WORK IN PROGRESS

This is a work in progress ....
