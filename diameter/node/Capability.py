from diameter import *

class VendorApplication:
    def __init__(self,vendor_id,application_id):
        self.vendor_id = vendor_id
        self.application_id = application_id
    
    def __eq__(self,other):
        return self.vendor_id==other.vendor_id and self.application_id==other.application_id
    def __hash__(self):
        return hash(self.vendor_id+self.application_id)
    
class Capability:
    def __init__(self):
        self.supported_vendor = set()
        self.auth_app = set()
        self.acct_app = set()
        self.auth_vendor = set()
        self.acct_vendor = set()
    
    def isSupportedVendor(self,vendor_id):
        return vendor_id in self.supported_vendor
    
    def isAllowedAuthApp(self,app):
        return (app in self.auth_app) or \
               (ProtocolConstants.DIAMETER_APPLICATION_RELAY in self.auth_app)
    def isAllowedAcctApp(self,app):
        return (app in self.acct_app) or \
               (ProtocolConstants.DIAMETER_APPLICATION_RELAY in self.acct_app)
    
    def isAllowedVendorAuthApp(self,vendor_id,app):
        return VendorApplication(vendor_id,app) in self.auth_vendor
    def isAllowedVendorAcctApp(self,vendor_id,app):
        return VendorApplication(vendor_id,app) in self.acct_vendor
    
    def addSupportedVendor(self,vendor_id):
        self.supported_vendor.add(vendor_id)
    def addAuthApp(self,application_id):
        self.auth_app.add(application_id)
    def addAcctApp(self,application_id):
        self.acct_app.add(application_id)
    def addVendorAuthApp(self,vendor_id,app):
        self.auth_vendor.add(VendorApplication(vendor_id,app))
    def addVendorAcctApp(self,vendor_id,app):
        self.acct_vendor.add(VendorApplication(vendor_id,app))
    
    def isEmpty(self):
        return len(self.auth_app)==0 and \
               len(self.acct_app)==0 and \
               len(self.auth_vendor)==0 and \
               len(self.acct_vendor)==0

    def calculateIntersection(us, peer):
	    #assumption: we are not a relay
	    c = Capability()
	    for vendor_id in peer.supported_vendor:
		    if vendor_id in us.supported_vendor:
			    c.addSupportedVendor(vendor_id)
	    for app in peer.auth_app:
		    if app==ProtocolConstants.DIAMETER_APPLICATION_RELAY or \
		       (app in us.auth_app):
			    c.addAuthApp(app)
	    for app in peer.acct_app:
		    if app==ProtocolConstants.DIAMETER_APPLICATION_RELAY or \
		       (app in us.acct_app):
			    c.addAcctApp(app)
	    for va in peer.auth_vendor:
		    #relay app is not well-defined for vendor-app
		    if us.isAllowedVendorAuthApp(va.vendor_id,va.application_id):
			    c.addVendorAuthApp(va.vendor_id,va.application_id)
	    for va in peer.acct_vendor:
		    #relay app is not well-defined for vendor-app
		    if us.isAllowedVendorAcctApp(va.vendor_id,va.application_id):
			    c.addVendorAcctApp(va.vendor_id,va.application_id)
	    return c;
    calculateIntersection = staticmethod(calculateIntersection)
 