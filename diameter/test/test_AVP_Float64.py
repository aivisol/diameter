import unittest

from diameter import AVP_Float64, AVP
from diameter.Error import InvalidAVPLengthError

class AVP_Float64TestCase(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_float64(self):
        
        a = AVP_Float64(1,17.5)
        
        assert a.queryValue()==17.5
        
        a.setValue(42.75);
        assert a.queryValue()==42.75
        
        a = AVP_Float64.narrow(AVP(1,b"\100\105\140\000\000\000\000\000"))
        assert a.queryValue()==42.75
        try:
            a = AVP_Float64.narrow(AVP(1,b"     "))
            assert False
        except InvalidAVPLengthError as detail:
            pass
