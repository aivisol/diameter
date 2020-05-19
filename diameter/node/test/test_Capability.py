import unittest

from diameter import ProtocolConstants
from diameter.node import Capability

class CapabilityTestCase(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_Capability(self):
        #vendor id
        c = Capability()
        assert not c.isSupportedVendor(1)
        assert not c.isSupportedVendor(2)
        c.addSupportedVendor(1)
        assert     c.isSupportedVendor(1)
        assert not c.isSupportedVendor(2)
        
        #auth app
        c = Capability()
        assert not c.isAllowedAuthApp(17)
        assert not c.isAllowedAuthApp(42)
        c.addAuthApp(17)
        assert     c.isAllowedAuthApp(17)
        assert not c.isAllowedAuthApp(42)
        
        c = Capability()
        assert not c.isAllowedAuthApp(17)
        assert not c.isAllowedAuthApp(42)
        c.addAuthApp(ProtocolConstants.DIAMETER_APPLICATION_RELAY)
        assert     c.isAllowedAuthApp(17)
        assert     c.isAllowedAuthApp(42)
        
        #acct app
        c = Capability()
        assert not c.isAllowedAcctApp(17)
        assert not c.isAllowedAcctApp(42)
        c.addAcctApp(17)
        assert     c.isAllowedAcctApp(17)
        assert not c.isAllowedAcctApp(42)
        
        c = Capability()
        assert not c.isAllowedAcctApp(17)
        assert not c.isAllowedAcctApp(42)
        c.addAcctApp(ProtocolConstants.DIAMETER_APPLICATION_RELAY)
        assert     c.isAllowedAcctApp(17)
        assert     c.isAllowedAcctApp(42)
        
        #empty
        c = Capability()
        assert c.isEmpty()
        c.addSupportedVendor(1)
        assert c.isEmpty()
        c.addAuthApp(17)
        assert not c.isEmpty()
        
        #calculateIntersection
        c1 = Capability()
        c2 = Capability()
        c1.addAuthApp(17)
        c1.addAuthApp(18)
        c2.addAuthApp(18)
        c2.addAuthApp(19)
        c3 = Capability.calculateIntersection(c1,c2)
        assert not c3.isAllowedAuthApp(17)
        assert     c3.isAllowedAuthApp(18)
        assert not c3.isAllowedAuthApp(19)
    