import unittest

from diameter import AVP_Unsigned64, AVP
from diameter.Error import InvalidAVPLengthError

class AVP_Unsigned64TestCase(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_unsigned64(self):
        a = AVP_Unsigned64(1,17)
        
        assert a.queryValue()==17
        
        a.setValue(42);
        assert a.queryValue()==42
        
        a = AVP_Unsigned64.narrow(AVP(1,b"        "))
        assert a.queryValue()==0x2020202020202020
        try:
            a = AVP_Unsigned64.narrow(AVP(1,b"     "))
            assert False
        except InvalidAVPLengthError as detail:
            pass
