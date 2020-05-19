from diameter.node.ConnectionTimers import ConnectionTimers
from diameter.node.ConnectionBuffers import NormalConnectionBuffers
import random

class ConnectionKey:
    pass

class Connection:
    #public Peer peer;  //initially null
    #public String host_id; //always set, updated from CEA/CER
    #public ConnectionTimers timers;
    #public ConnectionKey key;
    #private int hop_by_hop_identifier_seq;
    #SocketChannel channel;
    #ConnectionBuffers connection_buffers;
    
    state_connecting=0
    state_connected_in=1  #connected, waiting for cer
    state_connected_out=2 #connected, waiting for cea
    state_tls=3           #CE completed, negotiating TLS
    state_ready=4         #ready
    state_closing=5       #DPR sent, waiting for DPA
    state_closed=6
    
    def __init__(self):
        self.peer = None
        self.host_id = None
        self.timers = ConnectionTimers(30,3600) #todo
        self.key = ConnectionKey()
        self.hop_by_hop_identifier_seq = random.randint(0,0xFFFFFFFF)
        self.fd = None
        self.state = Connection.state_connected_in
        self.connection_buffers = NormalConnectionBuffers()
    
    def nextHopByHopIdentifier(self):
        v = self.hop_by_hop_identifier_seq
        self.hop_by_hop_identifier_seq += 1
        return v
    
    def appendNetInBuffer(self,stuff):
        self.connection_buffers.appendNetInBuffer(stuff)
    def appendAppOutputBuffer(self,stuff):
        self.connection_buffers.appendAppOutputBuffer(stuff)
	
    def processNetInBuffer(self):
        self.connection_buffers.processNetInBuffer()
    def processAppOutBuffer(self):
        self.connection_buffers.processAppOutBuffer()
    
    def hasAppInput(self):
        return self.connection_buffers.hasAppInput()
    def hasNetOutput(self):
        return self.connection_buffers.hasNetOutput()
    
    def getAppInBuffer(self):
        return self.connection_buffers.getAppInBuffer()
    def getNetOutBuffer(self):
        return self.connection_buffers.getNetOutBuffer()
    
    def consumeAppInBuffer(self,bytes):
        self.connection_buffers.consumeAppInBuffer(bytes)
    def consumeNetOutBuffer(self,bytes):
        self.connection_buffers.consumeNetOutBuffer(bytes)
    