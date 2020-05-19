import time

class ConnectionTimers:
    #last_activity;
    #last_real_activity;
    #last_in_dw;
    #dw_outstanding;
    #cfg_watchdog_timer;
    #cfg_idle_close_timeout;
    
    def __init__(self,watchdog_timer, idle_close_timeout):
        self.last_activity = time.time();
        self.last_real_activity = time.time()
        self.last_in_dw = time.time()
        self.dw_outstanding = False
        self.cfg_watchdog_timer = watchdog_timer
        self.cfg_idle_close_timeout = idle_close_timeout
    
    def markDWR(self): #got a DWR
        self.last_in_dw = time.time()
    
    def markDWA(self): #got a DWA    
        self.last_in_dw = time.time()
        self.dw_outstanding = False
    
    def markActivity(self): #got something
        self.last_activity = time.time()
    
    def markCER(self): #got a CER
        self.last_activity = time.time()
    
    def markRealActivity(self): #got something non-CER, non-DW
        self.last_real_activity = self.last_activity;
    
    def markDWR_out(self): #sent a DWR
        self.dw_outstanding = True
        self.last_activity = time.time()
    
    timer_action_none = 0
    timer_action_disconnect_no_cer = 1
    timer_action_disconnect_idle = 2
    timer_action_disconnect_no_dw = 3
    timer_action_dwr = 4

    def calcNextTimeout(self,ready):
        if not ready:
            #when we haven't received a CER or negotiated TLS it will time out
            return self.last_activity + self.cfg_watchdog_timer
        
        if not self.dw_outstanding:
            next_watchdog_timeout = self.last_activity + self.cfg_watchdog_timer; #when to send a DWR
        else:
            next_watchdog_timeout = self.last_activity + self.cfg_watchdog_timer + self.cfg_watchdog_timer; #when to kill the connection due to no response

        if self.cfg_idle_close_timeout!=0:
            idle_timeout = self.last_real_activity + self.cfg_idle_close_timeout;
            if idle_timeout<next_watchdog_timeout:
                return idle_timeout;
        return next_watchdog_timeout;
    
    def calcAction(self,ready):
        now = time.time()

        if not ready and now >= self.last_activity + self.cfg_watchdog_timer:
            return ConnectionTimers.timer_action_disconnect_no_cer
        
        if self.cfg_idle_close_timeout!=0:
            if now >= self.last_real_activity + self.cfg_idle_close_timeout:
                return ConnectionTimers.timer_action_disconnect_idle
        
        #section 3.4.1 item 1
        if now >= self.last_activity + self.cfg_watchdog_timer:
            if not self.dw_outstanding:
                return ConnectionTimers.timer_action_dwr;
            else:
                if now >= self.last_activity + self.cfg_watchdog_timer + self.cfg_watchdog_timer:
                    #section 3.4.1 item 3+4
                    return ConnectionTimers.timer_action_disconnect_no_dw;
        
        return ConnectionTimers.timer_action_none

