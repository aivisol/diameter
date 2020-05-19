from diameter.MessageHeader import MessageHeader
from diameter.AVP import AVP
import binascii
import xdrlib

class Message:
    """A Diameter message (header and AVPs)
    The Message is a container for the MessageHeader and the AVP s.
    It supports converting to/from the on-the-wire format, and
    manipulating the AVPs. The class is lean and mean, and does as little
    checking as possible.
    
    Example of building a Message:
        msg = Message()
        msg.hdr.application_id = ProtocolConstants.DIAMETER_APPLICATION_ACCOUNTING
        msg.hdr.command_code = ProtocolConstants.DIAMETER_COMMAND_ACCOUNTING
        msg.hdr.setRequest(True)
        msg.hdr.setProxiable(True)
        #Add AVPs
        ...
        msg.add(AVP_UTF8String(ProtocolConstants.DI_USER_NAME,"user@example.net"))
        msg.add(AVP_Unsigned64(ProtocolConstants.DI_ACCOUNTING_INPUT_OCTETS,36758373691049))
        ...
    
    Example of processing a message:
        msg ...
        for avp in msg.subset(ProtocolConstants.DI_FRAMED_IP_ADDRESS):
            try:
                address = AVP_Address.narrow(avp).queryAddress()
                #..do something useful with the address...
            except InvalidAVPLengthError, ex:
                #.. handle when peer sends garbage
            except InvalidAddressTypeError, ex:
                #.. handle when peer sends garbage
        avp_reply_message = msg.find(ProtocolConstants.DI_REPLY_MESSAGE)
        if avp:
            #..do something sensible with reply-message
    """
    
    def __init__(self,that=None):
        if not that:
            self.hdr = MessageHeader()
            self.avp = []
        else:
            self.hdr = MessageHeader(that.hdr)
            self.avp = that.avp[:]
    
    def encodeSize(self):
        """Calculate the size of the message in on-the-wire format.
        Returns the number of bytes the message will use on-the-wire.
        """
        sz = self.hdr.encodeSize()
        for a in self.avp:
            sz += a.encodeSize()
        return sz
    
    def encode(self,packer):
        """Encode the message in on-the-wire format to the specified byte array.
        packer: xdrlib.Packer
        """
        sz = self.encodeSize()
        self.hdr.encode(packer,sz)
        for a in self.avp:
            a.encode(packer)
    
    def decodeSize(unpacker):
        """Determine the complete size of the message from a on-the-wire
        byte array.
        There must be at least 4 bytes available in the array.
          unpacker: a xdrlib.Unpacker
        Returns the size (in bytes) of the message
        """
        start = unpacker.get_position()
        v_ml = unpacker.unpack_uint()
        unpacker.set_position(start)
        sz = v_ml&0x00FFFFFF
        if sz<20: sz=4 #interesting hack to detect NUL bytes
        if (sz % 4)!=0: sz=20 #interesting hack to detect NUL bytes
        return sz
    decodeSize = staticmethod(decodeSize)
    
    decode_status_decoded = 1
    decode_status_not_enough = 2
    decode_status_garbage = 3
    
    def decode(self,unpacker,bytes):
        """Decode a message from on-the-wire format.
        The message is checked to be in valid format and the VPs to be of
        the correct length etc. Invalid/reserved bits are not checked.
          unpacker  a xdrlib.Unpacker possibly containing a Diameter message
          bytes  the bytes to try to decode
        Return the result for the decode operation.
        """
        start = unpacker.get_position()
        if bytes < 4:
            return Message.decode_status_not_enough
        v_ml = unpacker.unpack_uint()
        version = v_ml>>24
        sz = v_ml&0x00FFFFFF
        if version!=1:
            return Message.decode_status_garbage
        if sz<20:
            return Message.decode_status_garbage
        if (sz%4)!=0:
            return Message.decode_status_garbage
        
        unpacker.set_position(start)
        
        # header looks ok
        if bytes<sz:
            return Message.decode_status_not_enough
        
        self.hdr.decode(unpacker)
        self.avp = []
        bytes_left = bytes - 20
        while bytes_left>0:
            if bytes_left<8:
                return Message.decode_status_garbage
            avp_sz = AVP.decodeSize(unpacker,bytes_left)
            if avp_sz==0:
                return Message.decode_status_garbage
            if avp_sz > bytes_left:
                return Message.decode_status_garbage
            a = AVP(0,[])
            a.decode(unpacker,avp_sz)
            self.avp.append(a)
            bytes_left -= avp_sz
            
        return Message.decode_status_decoded
    
    def prepareResponse(self, request):
        """Prepare a response the the supplied request.
        Implemented as hdr.prepareResponse(request.hdr)
        See: MessageHeader.prepareResponse
        """
        self.hdr.prepareResponse(request.hdr)
    
    #clone?
    
    def __len__(self):
        return len(self.avp)
    
    def __getitem__(self,key):
        return self.avp[key]
    
    def __setitem__(self,key,value):
        self.avp[key] = value
    
    def __delitem__(self,key):
        del self.avp[key]
    
    def __iter__(self):
        return self.avp.__iter__()
    
    def append(self,a):
        """Appends an AVP to the message"""
        self.avp.append(a)
    
    def subset(self,code,vendor_id=0):
        """Returns an iteratable subset of the AVPs where the code and vendor_id match"""
        class avp_subset:
            "A subset of the AVPs in a message"
            
            def __init__(self, message, code, vendor_id):
                self.message = message
                self.code = code
                self.vendor_id = vendor_id
                self.iter = message.__iter__()
            
            def __iter__(self):
                return self
            def __next__(self):
                while True:
                    a = next(self.iter)
                    if a.code==self.code and a.vendor_id==self.vendor_id:
                        return a
        return avp_subset(self,code,vendor_id)
    
    def find(self,code,vendor_id=0):
        """Returns the first AVP with a matching code (and vendor_id if nonzero)."""
        for a in self.avp:
            if a.code==code and a.vendor_id==vendor_id:
                return a
    
    def count(self,code,vendor_id=0):
        """Return the number of AVPs that matches the specified code (and vendor_id if nonzero)"""
        c=0
        for a in self.avp:
            if a.code==code and a.vendor_id==vendor_id:
                c += 1
        return c

