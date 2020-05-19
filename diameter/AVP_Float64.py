from diameter.AVP import AVP
from diameter.Error import InvalidAVPLengthError
from diameter.Error import InvalidAVPValueError
import struct

class AVP_Float64(AVP):
    """64-bit floating point AVP"""
    
    def __init__(self,code,value,vendor_id=0):
        AVP.__init__(self,code,struct.pack("!d",value),vendor_id)
    
    def queryValue(self):
        """Returns the payload interpreted as a 64-bit floating point value"""
        return struct.unpack("!d",self.payload)[0]
    
    def setValue(self,value):
        """Sets the payload to the spcified 64-bit floating point value"""
        self.payload = struct.pack("!d",value)
    
    def __str__(self):
        return str(self.code) + ":" + str(self.queryValue())
    
    def narrow(avp):
        """Convert generic AVP to AVP_Float64
        Raises: InvalidAVPLengthError, InvalidAVPValueError
        """
        if len(avp.payload)!=8:
            raise InvalidAVPLengthError(avp)
        try:
            value = struct.unpack("!d",avp.payload)[0]
        except struct.error:
            raise InvalidAVPValueError(avp)
        a = AVP_Float64(avp.code, value, avp.vendor_id)
        a.flags = avp.flags
        return a
    narrow = staticmethod(narrow)
