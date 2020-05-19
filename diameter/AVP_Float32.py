from diameter.AVP import AVP
from diameter.Error import InvalidAVPLengthError,InvalidAVPValueError
import struct

class AVP_Float32(AVP):
    """32-bit floating point AVP"""
    
    def __init__(self,code,value,vendor_id=0):
        AVP.__init__(self,code,struct.pack("!f",value),vendor_id)
    
    def queryValue(self):
        """Returns the payload interpreted as a 32-bit floating point value"""
        return struct.unpack("!f",self.payload)[0]
    
    def setValue(self,value):
        """Sets the payload to the spcified 32-bit floating point value"""
        self.payload = struct.pack("!f",value)
    
    def __str__(self):
        return str(self.code) + ":" + str(self.queryValue())
    
    def narrow(avp):
        """Convert generic AVP to AVP_Float32
        Raises: InvalidAVPLengthError, InvalidAVPValueError
        """
        if len(avp.payload)!=4:
            raise InvalidAVPLengthError(avp)
        try:
            value = struct.unpack("!f",avp.payload)[0]
        except struct.error:
            raise InvalidAVPValueError(avp)
        a = AVP_Float32(avp.code, value, avp.vendor_id)
        a.flags = avp.flags
        return a
    narrow = staticmethod(narrow)
