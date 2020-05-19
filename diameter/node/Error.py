class error(Exception):
    def __init__(self,*args):
        Exception.__init__(self,*args)

class InvalidSettingError(error):
    def __init__(self,why):
        error.__init__(self,why)

class StartError(error):
    def __init__(self,why):
        error.__init__(self,why)

class InvalidAVPValueError(error):
    def __init__(self,avp):
        error.__init__(self,"An AVP was well-formed but had invalid value in the context",avp)

class StaleConnectionError(error):
    def __init__(self):
        error.__init__(self,"The connection no longer exist")

class NotARequestError(error):
    def __init__(self):
        error.__init__(self,"")

class NotRoutableError(error):
    def __init__(self, msg=None):
        if msg:
            error.__init__(self, msg)
        else:
            error.__init__(self, "The message could not be routed to any peers")
           
class NotProxiableError(error):
    def __init__(self):
        error.__init__(self,"")

