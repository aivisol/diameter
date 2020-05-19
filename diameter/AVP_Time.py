from diameter.AVP import AVP
from diameter.AVP_Unsigned32 import AVP_Unsigned32
from diameter.Error import InvalidAVPLengthError
from struct import *
from datetime import datetime

class AVP_Time(AVP_Unsigned32):
    """A timestamp AVP.
    AVP_Time contains a second count since 1900. You can get the raw second
    count using AVP_Unsigned32.queryValue but this class' method
    querySecondsSince1970() is probably more useful in your program.
    
    Diameter does not have any base AVPs (RFC3588) with finer granularity
    than seconds.
    """
    
    seconds_between_1900_and_1970 = ((70*365)+17)*86400
    
    def __init__(self,code,seconds_since_1970,vendor_id=0):
        AVP_Unsigned32.__init__(self,code,seconds_since_1970+AVP_Time.seconds_between_1900_and_1970,vendor_id)
    
    def querySecondsSince1970(self):
        return AVP_Unsigned32.queryValue(self)-AVP_Time.seconds_between_1900_and_1970
    
    def setSecondsSince1970(self,seconds_since_1970):
        AVP_Unsigned32.setValue(self,seconds_since_1970+AVP_Time.seconds_between_1900_and_1970)

    def narrow(avp):
        """Convert generic AVP to AVP_Float64
        Raises: InvalidAVPLengthError
        """
        if len(avp.payload)!=4:
            raise InvalidAVPLengthError(avp)
        value = unpack("!I",avp.payload)[0] - AVP_Time.seconds_between_1900_and_1970
        a = AVP_Time(avp.code, value, avp.vendor_id)
        a.flags = avp.flags
        return a
    narrow = staticmethod(narrow)
    
    def __str__(self):
        return AVP.str_prefix__(self) + " " + str(datetime.fromtimestamp(self.querySecondsSince1970()))
