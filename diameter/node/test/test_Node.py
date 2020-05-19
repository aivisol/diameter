import unittest
import _thread
import logging
import time

from diameter.node import Node
from diameter.node.Capability import Capability
from diameter import ProtocolConstants
from diameter.node.NodeSettings import NodeSettings

class NodeTestCase(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_Node(self):
        class CL:
            def handle(self,connkey,peer,updown):
                pass
        class MD:
            def handle(self,msg,connkey,peer):
                return False
        logging.basicConfig(level=logging.DEBUG,format='%(asctime)s %(name)s %(levelname)s %(message)s')
        
        cap = Capability();
        cap.addAuthApp(ProtocolConstants.DIAMETER_APPLICATION_NASREQ)
        settings = NodeSettings("isjsys.int.i1.dk","i1.dk",1,cap,3869,"pythondiameter",1)
        n = Node(MD(),CL(),settings)
        
        n.start()
        time.sleep(1)
        n.stop()
