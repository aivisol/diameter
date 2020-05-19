from diameter.AVP import AVP
from diameter.Error import InvalidAVPLengthError
import struct

class AVP_Unsigned32(AVP):
    """32-bit unsigned integer AVP.
    RFC3855 describes the Unsigned32 AVP type. Python does not have an
    appropriate unsigned data type, so this class is functionally
    equivalent to AVP_Integer32
    """
    
    def __init__(self,code,value,vendor_id=0):
        AVP.__init__(self,code,struct.pack("!I",value),vendor_id)
    
    def queryValue(self):
        """Returns the payload as a 32-bit unsigned value."""
        return struct.unpack("!I",self.payload)[0]
    
    def setValue(self,value):
        """Sets the payload to the specified 32-bit unsigned value."""
        self.payload = struct.pack("!I",value)
    
    def __str__(self):
        return str(self.code) + ":" + str(self.queryValue())

    def narrow(avp):
        """Convert generic AVP to AVP_Unsigned32
        Raises: InvalidAVPLengthError
        """
        if len(avp.payload)!=4:
            raise InvalidAVPLengthError(avp)
        value = struct.unpack("!I",avp.payload)[0]
        a = AVP_Unsigned32(avp.code, value, avp.vendor_id)
        a.flags = avp.flags
        return a
    narrow = staticmethod(narrow)

