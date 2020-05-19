import unittest

from diameter import AVP_Grouped, AVP
from diameter.Error import InvalidAVPLengthError

class AVP_GroupedTestCase(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_grouped(self):
        a = AVP_Grouped(1)
        assert a.code==1
        assert len(a.getAVPs())==0
        
        a1 = AVP_Grouped(1,[AVP(2,b"u1"),AVP(2,b"u2")])
        assert len(a1.getAVPs())==2
        
        a = AVP(1,b"\000\000\000\002\000\000\000\012\165\061\000\000\000\000\000\002\000\000\000\012\165\062\000\000")
        a1 = AVP_Grouped.narrow(a)
        assert len(a1.getAVPs())==2
        
        a = AVP(1,b"\000\000\000\002\000\000\000\012\165\061\000\000\000")
        try:
            a1 = AVP_Grouped.narrow(a)
            assert False
        except InvalidAVPLengthError as details:
            pass
    