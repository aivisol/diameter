import unittest

from diameter.node import Peer

class NodeTestCase(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_Peer(self):        
        assert Peer("127.0.0.1")==Peer("127.0.0.1",3868)
        assert Peer("127.0.0.1")!=Peer("127.0.0.1",7)
        assert Peer("host.example.net")!=Peer("127.0.0.1",3868)