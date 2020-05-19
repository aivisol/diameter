from xdrlib import Packer,Unpacker
import binascii


class AVP:
    """A Diameter AVP
    See RFC3588 section 4 for details.
    An AVP consists of a code, some flags, an optional vendor ID, and a payload.
    
    The payload is not checked for correct size and content until you try to
    construct one of its subclasses from it. Eg
    
    avp = ...
    try:
        application_id = AVP_Unsigned32.narrow(avp).queryValue()
        ...
    except InvalidAVPLengthError as ex:
        ..
    
    Members:
        code (int)          The AVP code
        vendor_id (int)     The vendor ID. Assigning directly to this has the delayed effect of of setting/unsetting the vendor flag bit
        payload
    
    See also: ProtocolConstants
    """
    
    avp_flag_vendor        = 0x80
    avp_flag_mandatory     = 0x40
    avp_flag_private       = 0x20
    
    def __init__(self,code=0,payload="",vendor_id=0):
        self.payload = payload
        self.code = code
        self.flags = 0
        self.vendor_id = vendor_id
    
    def decodeSize(unpacker,bytes):
        start = unpacker.get_position()
        if bytes<8:
            return 0
        unpacker.set_position(start+4)
        flags_and_length = unpacker.unpack_uint()
        unpacker.set_position(start)
        flags_ = (flags_and_length>>24)
        length = (flags_and_length&0x00FFFFFF)
        padded_length = ((length+3)&~3)
        if (flags_&AVP.avp_flag_vendor)!=0:
            if length<12:
                return 0  #garbage
        else:
            if length<8:
                return 0  #garbage
        return padded_length;
    decodeSize = staticmethod(decodeSize)
    
    def decode(self,unpacker,bytes):
        if bytes<8:
            return False
        i = 0
        self.code = unpacker.unpack_uint()
        i += 4
        flags_and_length = unpacker.unpack_uint()
        i += 4
        self.flags = (flags_and_length>>24)
        length = flags_and_length&0x00FFFFFF
        padded_length = ((length+3)&~3)
        if bytes!=padded_length:
            return False
        length -= 8
        if (self.flags&AVP.avp_flag_vendor)!=0:
            if length<4:
                return False
            self.vendor_id = unpacker.unpack_uint()
            i += 4
            length -= 4
        else:
            self.vendor_id = 0
        self.payload = unpacker.unpack_fopaque(length)
        
        return True
    
    def encodeSize(self):
        sz = 4 + 4
        if self.vendor_id!=0:
            sz += 4
        sz += (len(self.payload)+3)&~3
        return sz;
    
    def encode(self,packer):
        sz = 4 + 4
        if self.vendor_id!=0:
            sz += 4
        sz += len(self.payload)
        
        f = self.flags
        if self.vendor_id!=0:
            f |= AVP.avp_flag_vendor
        else:
            f &= ~AVP.avp_flag_vendor
        
        i=0
        packer.pack_uint(self.code)
        i += 4
        packer.pack_uint(sz | (f<<24))
        i += 4
        if self.vendor_id!=0:
            packer.pack_uint(self.vendor_id)
            i += 4
        padded_len = (len(self.payload)+3)&~3
        packer.pack_fopaque(padded_len,self.payload)
        i += padded_len
        
        return i
    
    def isVendorSpecific(self):
        """Returns if the AVP is vendor-specific (has non-zero vendor_id)"""
        return (self.vendor_id!=0)
    
    def isMandatory(self):
        """Returns if the mandatory (M) flag is set"""
        return (self.flags&AVP.avp_flag_mandatory)!=0
    
    def isPrivate(self):
        """Returns if the private (P) flag is set"""
        return (self.flags&AVP.avp_flag_private)!=0
    
    def setMandatory(self,f):
        """Sets/unsets the mandatory (M) flag"""
        if f:
            self.flags |= AVP.avp_flag_mandatory
        else:
            self.flags &= ~AVP.avp_flag_mandatory
    
    def setPrivate(self,f):
        """Sets/unsets the private (P) flag"""
        if f:
            self.flags |= AVP.avp_flag_private
        else:
            self.flags &= ~AVP.avp_flag_private
    
    def setM(self):
        """Sets the M-bit and returns the instance"""
        self.flags |= AVP.avp_flag_mandatory
        return self
    
    def str_prefix__(self):
        """Return a string prefix suitable for building a __str__ result"""
        s = str(self.code)
        if self.isVendorSpecific():
            s+= ".v"
        if self.isMandatory():
            s+= ".m"
        if self.isPrivate():
            s+= ".p"
        if self.vendor_id!=0:
            s+= ":"+str(self.vendor_id)
        return s
    
    def __str__(self):
        return self.str_prefix__() + " 0x" + binascii.b2a_hex(self.payload).decode('utf-8')

