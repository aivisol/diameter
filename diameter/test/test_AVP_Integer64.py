import unittest

from diameter.AVP_Integer64 import AVP_Integer64, AVP
from diameter.Error import InvalidAVPLengthError

class AVP_Integer64TestCase(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_integer64(self):
        a = AVP_Integer64(1,17)
        
        assert a.queryValue()==17
        
        a.setValue(42);
        assert a.queryValue()==42
        
        a = AVP_Integer64.narrow(AVP(1,b"        "))
        assert a.queryValue()==0x2020202020202020
        try:
            a = AVP_Integer64.narrow(AVP(1,b"     "))
            assert False
        except InvalidAVPLengthError as detail:
            pass
