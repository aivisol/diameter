import unittest

from diameter.AVP_Integer32 import AVP_Integer32, AVP
from diameter.Error import InvalidAVPLengthError

class AVP_Integer32TestCase(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_integer32(self):
        a = AVP_Integer32(1,17)
        
        assert a.queryValue()==17
        
        a.setValue(42);
        assert a.queryValue()==42
        
        a = AVP_Integer32.narrow(AVP(1,b"    "))
        assert a.queryValue()==0x20202020
        try:
            a = AVP_Integer32.narrow(AVP(1,b"12345"))
            assert False
        except InvalidAVPLengthError as ex:
            pass
