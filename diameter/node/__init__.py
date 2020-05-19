# -*- coding: iso-8859-1 -*-
"""Diameter node classes.
This package contains classes for dealing with and implementing Diameter nodes.

How to create a node:.
  1: The first step in creating a Diameter Node is creating a set of
     capabilities. This is later on used for negotiating with peers.
     The capability set includes supported applications and vendor-IDs.
  2: The next step is creating a NodeSettings instance. A NodeSettings
     instance specifies the settings for your node including the
     capabilities, host-ID, etc.
  3: Then you are ready to create a Node, and NodeManager or SimpleSyncClient.
"""

from diameter.node.Capability import Capability
from diameter.node.Peer import Peer
from diameter.node.NodeSettings import NodeSettings
from diameter.node.Node import Node
from diameter.node.NodeManager import NodeManager
from diameter.node.SimpleSyncClient import SimpleSyncClient
from diameter.node.Error import error, InvalidSettingError, StartError,InvalidAVPValueError,StaleConnectionError,NotARequestError,NotRoutableError,NotProxiableError
#from Error import *

__author__="Ivan Skytte J�rgensen"

def _unittest():
    pass
