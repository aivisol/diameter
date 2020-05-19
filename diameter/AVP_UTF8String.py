from diameter.AVP import AVP
import codecs
from codecs import getencoder,getdecoder

utf8encoder=getencoder("utf_8")
utf8decoder=getdecoder("utf_8")

class AVP_UTF8String(AVP):
    """AVP with UTF-8 string payload."""
    
    def __init__(self,code,value="",vendor_id=0):
        AVP.__init__(self,code,utf8encoder(value)[0],vendor_id)
    
    def queryValue(self):
        """Returns the payload as a string (possibly a unicode string)"""
        return utf8decoder(self.payload)[0]
    
    def setValue(self,value):
        self.payload = utf8encoder(value)[0]
    
    def __str__(self):
        return AVP.str_prefix__(self) + " " + self.queryValue()
    
    def narrow(avp):
        """Convert generic AVP to AVP_UTF8String
        """
        a = AVP_UTF8String(avp.code, vendor_id=avp.vendor_id)
        a.flags = avp.flags
        a.payload = avp.payload
        return a
    narrow = staticmethod(narrow)
