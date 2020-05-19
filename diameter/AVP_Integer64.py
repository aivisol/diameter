from diameter.AVP import AVP
from diameter.Error import InvalidAVPLengthError
import struct

class AVP_Integer64(AVP):
    """64-bit signed integer AVP."""
    
    def __init__(self,code,value,vendor_id=0):
        AVP.__init__(self,code,struct.pack("!Q",value),vendor_id)
    
    def queryValue(self):
        """Returns the payload as a 64-bit signed value."""
        return struct.unpack("!Q",self.payload)[0]
    
    def setValue(self,value):
        """Sets the payload to the specified 64-bit signed value."""
        self.payload = struct.pack("!Q",value)
    
    def __str__(self):
        return str(self.code) + ":" + str(self.queryValue())

    def narrow(avp):
        """Convert generic AVP to AVP_Integer64
        Raises: InvalidAVPLengthError
        """
        if len(avp.payload)!=8:
            raise InvalidAVPLengthError(avp)
        value = struct.unpack("!Q",avp.payload)[0]
        a = AVP_Integer64(avp.code, value, avp.vendor_id)
        a.flags = avp.flags
        return a
    narrow = staticmethod(narrow)
