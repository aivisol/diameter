import unittest
import socket

from diameter import AVP_Address, AVP
from diameter.Error import InvalidAVPLengthError, InvalidAddressTypeError

class AVP_AddressTestCase(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_ip4(self):
        ip4="127.0.0.1"
        a = AVP_Address(1,ip4)
        assert a.queryAddress()[0]==socket.AF_INET
        assert a.queryAddress()[1]==ip4

    def test_ip6(self):    
        ip6="2001:db8::1"
        a = AVP_Address(1,ip6)
        assert a.queryAddress()[0]==socket.AF_INET6
        assert a.queryAddress()[1]==ip6

    def test_narrow(self):    
        a = AVP_Address.narrow(AVP(1,"\000\001\177\000\000\001"))
        assert a.queryAddress()[0]==socket.AF_INET
        assert a.queryAddress()[1]=="127.0.0.1"
        
    def test_narrow1(self):
        try:
            a = AVP_Address.narrow(AVP(1,"\000\001\177\000\000"))
        except InvalidAVPLengthError as details:
            pass
    
    def test_narrow2(self):    
        try:
            a = AVP_Address.narrow(AVP(1,"\000\003\177\000\000\001"))
        except InvalidAddressTypeError as details:
            pass