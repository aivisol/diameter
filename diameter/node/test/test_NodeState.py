import unittest

from diameter.node.NodeState import NodeState


class NodeStateTestCase(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_NodeState(self):
        ns = NodeState()
        i1 = ns.nextEndToEndIdentifier()
        i2 = ns.nextEndToEndIdentifier()
        assert i1!=i2
        
        sp1 = ns.nextSessionId_second_part()
        sp2 = ns.nextSessionId_second_part()
        assert sp1 != sp2
    
