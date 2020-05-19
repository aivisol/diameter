class ConnectionBuffers:
    #abstract ByteBuffer netOutBuffer();
    #abstract ByteBuffer netInBuffer();
    #abstract ByteBuffer appInBuffer();
    #abstract ByteBuffer appOutBuffer();
    #abstract void processNetInBuffer();
    #abstract void processAppOutBuffer();
    
    def __init__(self):
        pass
    
    def consumeNetOutBuffer(self,bytes):
        pass #todo
    
    def consumeAppInBuffer(self,bytes):
        pass #todo
    
    
#    static private void consume(ByteBuffer bb, int bytes) {
#        bb.limit(bb.position());
#        bb.position(bytes);
#        bb.compact();

class NormalConnectionBuffers(ConnectionBuffers):
    def __init__(self):
        ConnectionBuffers.__init__(self)
        self.in_buffer = b""
        self.out_buffer = b""
    
    def appendNetInBuffer(self,stuff):
        self.in_buffer += stuff
    def appendAppOutputBuffer(self,stuff):
        self.out_buffer += stuff
    
    def processNetInBuffer(self):
        pass
    def processAppOutBuffer(self):
        pass
    
    def hasAppInput(self):
        return len(self.in_buffer)!=0
    def hasNetOutput(self):
        return len(self.out_buffer)!=0
    
    def getAppInBuffer(self):
        return self.in_buffer
    def getNetOutBuffer(self):
        return self.out_buffer
    
    def consumeAppInBuffer(self,bytes):
        self.in_buffer = self.in_buffer[bytes:]
    def consumeNetOutBuffer(self,bytes):
        self.out_buffer = self.out_buffer[bytes:]

