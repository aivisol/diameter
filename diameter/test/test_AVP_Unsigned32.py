import unittest

from diameter import AVP_Unsigned32, AVP
from diameter.Error import InvalidAVPLengthError

class AVP_Unsigned32TestCase(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_unsigned32(self):
        a = AVP_Unsigned32(1,17)
        
        assert a.queryValue()==17
        
        a.setValue(42);
        assert a.queryValue()==42
        
        a = AVP_Unsigned32.narrow(AVP(1,b"    "))
        assert a.queryValue()==0x20202020
        try:
            a = AVP_Unsigned32.narrow(AVP(1,b"12345"))
            assert False
        except InvalidAVPLengthError as ex:
            pass
