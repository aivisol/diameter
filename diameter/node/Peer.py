from diameter.node.Capability import Capability

class Peer:
    def __init__(self,host=None,port=None,socket_address=None,use_ericsson_host_ip_address_format=False):
        self.host = None
        self.port = 3868
        self.secure = False
        self.capabilities = Capability()
        
        if host:
            self.host = host
        if port:
            self.port = port
        if socket_address:
            self.host = socket_address[0]
            self.port = socket_address[1]
        
        self.use_ericsson_host_ip_address_format = use_ericsson_host_ip_address_format
    
    def __str__(self):
        if self.secure: 
            proto="aaas"
        else: 
            proto="aaa"
        return proto+"://"+self.host+":"+str(self.port)
        
    def __eq__(self,other):
        return self.host==other.host and self.port==other.port
    def __ne__(self,other):
        return self.host!=other.host or self.port!=other.port
    def __hash__(self):
        return hash(self.host)+hash(self.port)
