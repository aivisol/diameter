import unittest
import logging

from diameter.node import SimpleSyncClient

class SimpleSyncClientTestCase(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_SimpleSyncClient(self): 
        logging.basicConfig(level=logging.DEBUG,format='%(asctime)s %(name)s %(levelname)s %(message)s')
        
        from diameter.node import Capability,NodeSettings
        from diameter import ProtocolConstants,Message
        cap = Capability();
        cap.addAuthApp(ProtocolConstants.DIAMETER_APPLICATION_NASREQ)
        settings = NodeSettings("isjsys.int.i1.dk","i1.dk",1,cap,3868,"pythondiameter",1)
        
        ssc = SimpleSyncClient(settings,[])
        ssc.start()
        
        msg = Message()
        msg.hdr.application_id = ProtocolConstants.DIAMETER_APPLICATION_ACCOUNTING
        msg.hdr.command_code = ProtocolConstants.DIAMETER_COMMAND_ACCOUNTING
        msg.hdr.setRequest(True)
        msg.hdr.setProxiable(True)
        
        answer = ssc.sendRequest(msg)
        assert not answer
        
        ssc.stop()
        del ssc
 