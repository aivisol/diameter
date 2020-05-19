import unittest

from diameter import AVP_Float32, AVP
from diameter.Error import InvalidAVPLengthError

class AVP_Float32TestCase(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_float32(self):
        a = AVP_Float32(1,17.5)
        
        assert a.queryValue()==17.5
        
        a.setValue(42.75);
        assert a.queryValue()==42.75
        
        a = AVP_Float32.narrow(AVP(1,b"\102\053\000\000"))
        assert a.queryValue()==42.75
        try:
            a = AVP_Float32.narrow(AVP(1,b"     "))
            assert False
        except InvalidAVPLengthError as detail:
            pass
