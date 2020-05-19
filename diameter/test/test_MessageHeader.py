import unittest
from xdrlib import Packer,Unpacker

from diameter import MessageHeader


class MessageHeaderTestCase(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_MessageHeader(self):
        mh = MessageHeader()
        
        assert mh.version == 1
        
        mh.setRequest(True)
        assert mh.isRequest()
        mh.setRequest(False)
        assert not mh.isRequest()
        
        mh.setProxiable(True)
        assert mh.isProxiable()
        mh.setProxiable(False)
        assert not mh.isProxiable()
        
        mh.setError(True)
        assert mh.isError()
        mh.setError(False)
        assert not mh.isError()
        
        mh.setRetransmit(True)
        assert mh.isRetransmit()
        mh.setRetransmit(False)
        assert not mh.isRetransmit()
        
        mh.setRequest(True)
        mh.setProxiable(True)
        mh.setRetransmit(True)
        mh.command_code = 42
        mh.hop_by_hop_identifier = 17
        mh.end_to_end_identifier = 117
        
        mh2 = MessageHeader();
        
        mh2.prepareResponse(mh)
        assert not mh2.isRequest()
        assert mh2.isProxiable()
        assert not mh2.isRetransmit()
        assert mh2.command_code == mh.command_code
        assert mh2.hop_by_hop_identifier == mh.hop_by_hop_identifier
        assert mh2.end_to_end_identifier == mh.end_to_end_identifier
        
        p = Packer()
        ml = mh.encodeSize()
        mh.encode(p,ml)
        mh3 = MessageHeader()
        u = Unpacker(p.get_buffer())
        #u.reset(p.get_buffer())
        mh3.decode(u);
        assert mh3.version == 1
        assert mh3.version == mh.version
        assert mh3.command_flags == mh.command_flags
        assert mh3.command_code == mh.command_code
        assert mh3.hop_by_hop_identifier == mh.hop_by_hop_identifier
        assert mh3.end_to_end_identifier == mh.end_to_end_identifier
