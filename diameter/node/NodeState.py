import time
import _thread
import random

class NodeState:
    
    def __init__(self):
        now = int(time.time())
        self.state_id = now
        self.end_to_end_identifier = int((now<<20) | random.randint(0,0x000FFFFF))&0xFFFFFFFF
        self.session_id_high = now
        self.session_id_low = 0
        self.lock = _thread.allocate_lock()
    
    def nextEndToEndIdentifier(self):
        self.lock.acquire()
        v = self.end_to_end_identifier
        self.end_to_end_identifier += 1
        self.lock.release()
        return v
    
    def nextSessionId_second_part(self):
        self.lock.acquire()
        v = self.session_id_low
        self.session_id_low += 1
        if self.session_id_low == 0:
            self.session_id_high += 1
        self.lock.release()
        return str(self.session_id_high) + ";" + str(v)
        