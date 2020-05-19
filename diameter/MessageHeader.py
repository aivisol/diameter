from xdrlib import Packer,Unpacker

class MessageHeader:
    """The header component of a message.
    See RFC3588 section 3. After you have read that understanding the
    class is trivial. The only fields and methods you will normally use
    are:
      command_code
      application_id (maybe)
      setProxiable
      setRequest
    Note: The default command flags does not include the proxiable bit, meaning
    that request messages by default cannot be proxied by diameter proxies and
    other gateways. It is still not determined if this is a reasonable default.
    You should always call setProxiable() explicitly so it has the value you
    expect it to be.
    """
    
    command_flag_request_bit    = 0x80
    command_flag_proxiable_bit  = 0x40
    command_flag_error_bit      = 0x20
    command_flag_retransmit_bit = 0x10
    
    def __init__(self,that=None):
        """Constructor for MessageHeader.
        If 'that' is None then the command flags are initialized to
        answer+not-proxiable+not-error+not-retransmit, also known as 0,
        and the command_code, application_id, hop_by_hop_identifier and
        end_to_end_identifier are initialized to 0.
        """
        if not that:
            self.version = 1
            self.command_flags = 0
            self.command_code = 0
            self.application_id = 0
            self.hop_by_hop_identifier = 0
            self.end_to_end_identifier = 0
        else:
            self.version = that.version
            self.command_flags = that.command_flags
            self.command_code = that.command_code
            self.application_id = that.application_id
            self.hop_by_hop_identifier = that.hop_by_hop_identifier
            self.end_to_end_identifier = that.end_to_end_identifier
    
    def isRequest(self):
        return (self.command_flags&MessageHeader.command_flag_request_bit)!=0
    def isProxiable(self):
        return (self.command_flags&MessageHeader.command_flag_proxiable_bit)!=0
    def isError(self):
        return (self.command_flags&MessageHeader.command_flag_error_bit)!=0
    def isRetransmit(self):
        return (self.command_flags&MessageHeader.command_flag_retransmit_bit)!=0
    
    def setRequest(self,f):
        if f:
            self.command_flags = (self.command_flags | MessageHeader.command_flag_request_bit)
        else:
            self.command_flags = (self.command_flags & ~MessageHeader.command_flag_request_bit)
    
    def setProxiable(self,f):
        if f:
            self.command_flags = (self.command_flags | MessageHeader.command_flag_proxiable_bit)
        else:
            self.command_flags = (self.command_flags & ~MessageHeader.command_flag_proxiable_bit)
    
    def setError(self,f):
        """Set error bit. See RFC3588 section 3 page 32 before you set this."""
        if f:
            self.command_flags = (self.command_flags | MessageHeader.command_flag_error_bit)
        else:
            self.command_flags = (self.command_flags & ~MessageHeader.command_flag_error_bit)
    
    def setRetransmit(self,f):
        """Set retransmit bit"""
        if f:
            self.command_flags = (self.command_flags | MessageHeader.command_flag_retransmit_bit)
        else:
            self.command_flags = (self.command_flags & ~MessageHeader.command_flag_retransmit_bit)
    
    def encodeSize(self):
        return 5*4
    
    def encode(self,packer,message_length):
        packer.pack_uint((self.version<<24)|message_length);
        packer.pack_uint((self.command_flags<<24)|self.command_code);
        packer.pack_uint(self.application_id);
        packer.pack_uint(self.hop_by_hop_identifier);
        packer.pack_uint(self.end_to_end_identifier);
    
    def decode(self,unpacker):
        v_ml = unpacker.unpack_uint();
        self.version = v_ml>>24;
        f_code = unpacker.unpack_uint();
        self.command_flags = f_code>>24;
        self.command_code = f_code&0x00FFFFFF;
        self.application_id = unpacker.unpack_uint()
        self.hop_by_hop_identifier = unpacker.unpack_uint()
        self.end_to_end_identifier = unpacker.unpack_uint()
    
    def prepareResponse(self,request):
        """Prepare a response from the specified request header.
        The proxiable flag is copied - the other flags are cleared.
        The command_code, application_id, hop_by_hop_identifier,
        end_to_end_identifier and 'proxyable' command flag
        are copied. The 'request', 'error' and 'retransmit' bits are cleared.
        """
        self.version = request.version
        self.command_flags = request.command_flags&MessageHeader.command_flag_proxiable_bit;
        self.command_code = request.command_code;
        self.application_id = request.application_id
        self.hop_by_hop_identifier = request.hop_by_hop_identifier
        self.end_to_end_identifier = request.end_to_end_identifier
