from diameter.AVP import AVP

class AVP_OctetString(AVP):
    """AVP containing arbitrary data of variable length."""
    
    def __init__(self,code=0,payload="",vendor_id=0):
        AVP.__init__(self,code,payload,vendor_id)
