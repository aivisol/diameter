import unittest
from xdrlib import Packer,Unpacker

from diameter import AVP_Unsigned32, AVP
from diameter.Error import InvalidAVPLengthError

class AVP_TestCase(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_AVP(self):
        
        a1 = AVP(1,b"user")
        
        a1.setMandatory(True);
        assert a1.isMandatory()
        a1.setMandatory(False);
        assert not a1.isMandatory()
        
        a1.setPrivate(True);
        assert a1.isPrivate()
        a1.setPrivate(False);
        assert not a1.isPrivate()
        
        a1 = AVP(1,b"user")
        e_sz1 = a1.encodeSize()
        p = Packer()
        e_sz2 = a1.encode(p)
        assert e_sz1 == 12
        assert e_sz2 == 12
        assert e_sz1==e_sz2
        
        u = Unpacker(p.get_buffer())
        
        d_sz1 = AVP.decodeSize(u,e_sz2)
        assert d_sz1 == e_sz2
        
        a2 = AVP()
        assert a2.decode(u,d_sz1)
        
        assert a1.code == a2.code
        assert a1.vendor_id == a2.vendor_id
        
        #same as above, but requires padding
        a1 = AVP(1,b"user")
        e_sz1 = a1.encodeSize()
        p = Packer()
        e_sz2 = a1.encode(p)
        assert e_sz1==e_sz2
        
        u = Unpacker(p.get_buffer())
        
        d_sz1 = AVP.decodeSize(u,e_sz2)
        assert d_sz1 == e_sz2
        
        a2 = AVP()
        assert a2.decode(u,d_sz1)
        
        assert a1.code == a2.code
        assert a1.vendor_id == a2.vendor_id
