# IMNetDB NSOT

This project contains the python library for the IMNetDB network source
of truth database.  This project is build using [ArangoDB](https://www.arangodb.com/).

The purpose of this library is to allow a network automation engineer to quickly craft 
a graph-database composed of the building blocks they need to represent their application specific
"source of truth".  While every application will ultimately be different,
there are a common set of building blocks to get started with.  These include
the following:

   * Device - represents a single managed device
   * DeviceGroup - represents a group of devices
   * Interface - represents a device interface
   * Cable - represents the connection between two device interfaces
   * VLAN - represents a VLAN
   * VLANGroup - represents a group of VLANs
   * IPAddress - represents an IPv4 or IPv6 address
   * IPNetwork - represents an IPv4 or IPv6 network address
   * IPInterface - represents an IPv4 or IPv6 interface address
   
Each of these nodes can contain a collect of user-defined fields.
That is to say, the ArangoDB system does not require a *schema*, and
therefore lends itself well to network applications that want to
define their own fields for their own purposes.

# Installation

This library is presently not installed in PyPi.  Therefore
you must clone and install into your environment for now.  

You should create a virtualenv and activate it before installing
this project.

````bash
$ python setup.py install
````

You will also need to have ArangoDB installed.  For convenience,
there is a [docker-compose](tests/docker-compose.yml) file located in the **tests** directory.
Presuming you have Docker installed on your system, and you have Internet access, you can
download the ArangoDB docker image and start the server using the following 
command:

```bash
$ make arangodb-start
```

At this point you should be able to open you webbrowser to the ArangoDB WebUI
page:

```bash
http://localhost:8529
```

# Usage

To get connected to the database:

````python
from imnetdb.nsotdb import IMNetDB

client = IMNetDB(password='admin123')
````

At this point you can then start using the client to manage the database.
For examples, you can review the files in the **tests** directory.

Here is a basic example to create a devices with interfaces:

````python
from bracket_expansion import bracket_expansion
from imnetdb.nsotdb import IMNetDB

client = IMNetDB(password='admin123')

leaf = client.devices.ensure('leaf1', role='leaf', description='this is my spine')

for if_name in bracket_expansion("Ethernet[1-48]"):
    client.interfaces.ensure(dict(device_node=leaf, name=if_name), speed=10)

for if_name in bracket_expansion("Ethernet[49-56]"):
    client.interfaces.ensure(dict(device_node=leaf, name=if_name), speed=100)
````

*NOTE: There is a companion project for device-templates that is used to fabricate devices and
interfaces that are specific to VENDOR and MODEL.  Refer to the [device-stencils](https://github.com/imnetdb/device-stencils)
project for more details*
# Interface Allocation

The `interfaces` attribute provides a method that allows you to allocate a number of unused
interfaces based on the criteria you provide.  By default all interfaces are added
to the NSOTDB with a field `used = False`.  For more information on this feature,
please refer to:

````python
help(client.interfaces.allocate)
````

# WORK IN PROGRESS

This is a work in progress ....