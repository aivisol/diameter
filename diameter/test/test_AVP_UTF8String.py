import unittest
import socket

from diameter import AVP_UTF8String, AVP

class AVP_UTF8StringTestCase(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_UTF8String(self):
        
        a = AVP_UTF8String(1,"user");
        assert a.queryValue()=="user"
        
        a.setValue("user2")
        assert a.queryValue()=="user2"
        
        a = AVP_UTF8String(1,'\xe6\xf8\xe5')
        assert len(a.payload)>3
        assert len(a.queryValue())==3
        
        a.setValue('\xe6\xf8\xe5')
        assert len(a.payload)>3
        assert len(a.queryValue())==3
