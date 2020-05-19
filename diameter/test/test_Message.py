import unittest
import xdrlib
import binascii
from diameter import Message, AVP

class Message_TestCase(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_Message(self):
        m1 = Message()
        assert len(m1)==0
        
        p = xdrlib.Packer()
        m1.encode(p)
        e_sz = len(p.get_buffer())
        assert len(p.get_buffer())==20
        u = xdrlib.Unpacker(p.get_buffer())
        m2 = Message()
        assert m2.decode(u,e_sz)==Message.decode_status_decoded
        
        a = AVP(1,b"hello")
        m1.append(a)
        assert len(m1)==1
        
        p = xdrlib.Packer()
        m1.encode(p)
        e_sz = len(p.get_buffer())
        assert len(p.get_buffer())==36
        
        u = xdrlib.Unpacker(p.get_buffer())
        m2 = Message()
        assert m2.decode(u,e_sz)==Message.decode_status_decoded
        
        #test container+iteration
        m3 = Message()
        m3.append(AVP(1,"user1"))
        m3.append(AVP(1,"user2"))
        assert len(m3)==2
        count=0
        for a in m3:
            count += 1
        assert count==2
        
        #test subset
        m4 = Message()
        m4.append(AVP(1,"user1"))
        m4.append(AVP(1,"user2"))
        m4.append(AVP(2,"foo1"))
        m4.append(AVP(1,"user3"))
        m4.append(AVP(2,"foo1"))
        assert len(m4)==5
        count=0
        for a in m4.subset(1):
            count += 1
        assert count==3
        count=0
        for a in m4.subset(2):
            count += 1
        assert count==2
        count=0
        for a in m4.subset(117):
            count += 1
        assert count==0
        
        #find
        m5 = Message()
        m5.append(AVP(1,"user1"))
        m5.append(AVP(2,"foo1"))
        assert m5.find(1)
        assert m5.find(2)
        assert not m5.find(117)
        
        #decode raw (good)
        raw = binascii.a2b_hex("0100003000000000000000000000000000000000000000010000000d7573657231000000000000020000000c666f6f31")
        u = xdrlib.Unpacker(raw)
        m6 = Message()
        assert m6.decode(u,len(raw))==Message.decode_status_decoded
        
        #decode raw (short)
        raw = binascii.a2b_hex("0100003000000000000000000000000000000000000000010000000d7573657231000000000000020000000c666f6f")
        u = xdrlib.Unpacker(raw)
        m7 = Message()
        assert m7.decode(u,len(raw))==Message.decode_status_not_enough
        
        #decode raw (garbage)
        raw = binascii.a2b_hex("0100002900000000000000000000000000000000000000010000000d7573657231000000000000020000000c666f6f")
        u = xdrlib.Unpacker(raw)
        m7 = Message()
        assert m7.decode(u,len(raw))==Message.decode_status_garbage
        
        #decode raw (garbage) (NUL bytes)
        raw = binascii.a2b_hex("0100000000000000000000000000000000000000000000010000000d7573657231000000000000020000000c666f6f")
        u = xdrlib.Unpacker(raw)
        m7 = Message()
        assert m7.decode(u,len(raw))==Message.decode_status_garbage
        
