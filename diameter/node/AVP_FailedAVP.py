from diameter.AVP_Grouped import AVP_Grouped
import diameter.ProtocolConstants

class AVP_FailedAVP(AVP_Grouped):
    def __init__(self,a,vendor_id=0):
        AVP_Grouped.__init__(self,[a],vendor_id)
