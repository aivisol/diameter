class Error(Exception):
    """Common base class for Diameter errors"""
    def __init__(self,avp=None):
        Exception.__init__(self,avp)

class InvalidAddressTypeError(Error):
    """An Address AVP with invalid address type was encountered"""
    def __init__(self,avp=None):
        Error.__init__(self,avp)

class InvalidAVPLengthError(Error):
    """An AVP with invalid length (according to its expected type) was encountered"""
    def __init__(self,avp=None):
        Error.__init__(self,avp)

class InvalidAVPValueError(Error):
    """An AVP was well-formed but had invalid value in the context"""
    def __init__(self,avp):
        Error.__init__(self,avp)

def _unittest():
    pass
