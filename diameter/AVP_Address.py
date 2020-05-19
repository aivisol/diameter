from diameter.AVP import AVP
from diameter.Error import InvalidAVPLengthError,InvalidAddressTypeError
import struct
import socket

def _pack_address(address):
    addrs=socket.getaddrinfo(address, 0)
    for a in addrs:
        if a[0]==socket.AF_INET:
            raw = socket.inet_pton(socket.AF_INET,a[4][0]);
            return struct.pack("!h4s",1,raw)
        if a[0]==socket.AF_INET6:
            raw = socket.inet_pton(socket.AF_INET6,a[4][0]);
            return struct.pack("!h16s",2,raw)
    raise InvalidAddressTypeError()

class AVP_Address(AVP):
    """An internet address AVP.
    This class reflects the Address type AVP described in RFC3588.
    It supports both IPv4 and IPv6.
    Note: Values not conforming to RFC3588 has been seen in the wild.
    """
    
    def __init__(self,code,address,vendor_id=0):
        """Constructs an AVP_Address. The address is expected to tuple (family,address)"""
        AVP.__init__(self,code,_pack_address(address),vendor_id)
    
    def queryAddress(self):
        """Returns the payload as a tuple (family,address)
        Raises: InvalidAddressTypeError
        """
        if len(self.payload)==2+4:            
            return (socket.AF_INET,socket.inet_ntop(socket.AF_INET,self.payload[2:]))
        elif len(self.payload)==2+16:
            return (socket.AF_INET6,socket.inet_ntop(socket.AF_INET6,self.payload[2:]))
        else:
            raise InvalidAddressTypeError(self)
        
    def setAddress(self,address):
        """Sets the payload. The address is expected to tuple (family,address)
        Raises: InvalidAddressTypeError
        """
        self.payload = _pack_address(address)
    
    def __str__(self):
        if len(self.payload)==2+4:
            return self.str_prefix__() + " " + socket.inet_ntop(socket.AF_INET,self.payload[2:])
        elif len(self.payload)==2+16:
            return self.str_prefix__() + " " + socket.inet_ntop(socket.AF_INET6,self.payload[2:])
        else:
            return AVP.__str__(self)
    
    def narrow(avp):
        """Convert a generic AVP to AVP_Address
        Attempts to interpret the payload as an address and returns
        an AVP_Address instance on success.
        Raises: InvalidAVPLengthError
        """
        if len(avp.payload)<2:
            raise InvalidAVPLengthError(avp)
        payload = bytes(avp.payload[0:2], 'utf-8')
        address_family = struct.unpack("!h",payload)[0]
        if address_family==1:
            if len(avp.payload) != 2+4:
                raise InvalidAVPLengthError(avp)
        elif address_family==2:
            if len(avp.payload) != 2+16:
                raise InvalidAVPLengthError(avp)
        else:
            raise InvalidAddressTypeError(avp)
        a = AVP_Address(avp.code, "0.0.0.0", avp.vendor_id)
        a.payload = bytes(avp.payload[:], 'utf-8')
        a.flags = avp.flags
        return a
    narrow = staticmethod(narrow)

