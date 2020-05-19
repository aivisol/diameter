import socket
import _thread
import threading
import time
import diameter.ProtocolConstants
from diameter.node.NodeSettings import NodeSettings
from diameter.node.NodeState import NodeState
from diameter.node.Peer import Peer
from diameter.node.Connection import Connection
from diameter.node.ConnectionTimers import ConnectionTimers
from diameter.node.Capability import Capability
from diameter import *
from diameter.node.Error import *
import struct
import xdrlib
import struct
import select
import errno
import logging

class SelectThread(threading.Thread):
    def __init__(self,node):
        threading.Thread.__init__(self,name="Diameter node thread");
        self.node=node
    def run(self):
        self.node.run_select()

class ReconnectThread(threading.Thread):
    def __init__(self,node):
        threading.Thread.__init__(self,name="Diameter node reconnect thread");
        self.node=node
    def run(self):
        self.node.run_reconnect()

class Node:
    """A Diameter node
    The Node class manages diameter transport connections and peers. It handles
    the low-level messages itself (CER/CEA/DPR/DPA/DWR/DWA). The rest is sent to
    the a message dispatcher. When connections are established or closed the
    connection listener is notified. Message can be sent and received through
    the node but no state is maintained per message.
    Node is quite low-level. You probably want to use NodeManager instead.
    """
    
    def __init__(self,message_dispatcher,connection_listener,settings):
        """
        Constructor for Node.
        Constructs a Node instance with the specified parameters.
        The node is not automatically started.
          message_dispatcher   A message dispatcher. Must have a member
                               handle_message(msg,connkey,peer)
          connection_listener  A connection observer. Can be null. Must have a
                               member handle_connection(connkey,peer,up_down)
          settings             The node settings.
        """
        self.message_dispatcher = message_dispatcher
        self.connection_listener = connection_listener
        self.settings = settings
        self.node_state = NodeState()
        self.map_key_conn_lock = threading.Lock()
        self.map_key_conn_cv = threading.Condition(self.map_key_conn_lock)
        self.obj_conn_wait = threading.Condition()
        self.fd_pipe = socket.socketpair()
        self.persistent_peers = set([])
        self.persistent_peers_lock = threading.Lock()
        self.node_thread = None
        self.reconnect_thread = None
        self.map_key_conn = {}
        self.map_fd_conn = {}
        self.logger = logging.getLogger("dk.i1.diameter.node")
    
    def start(self):
        """
        Start the node.
        The node is started. If the port to listen on is already used by
        another application or some other initial network error occurs a
        StartError is raised.
        """
        self.logger.log(logging.INFO,"Starting Diameter node")
        self.please_stop = False
        self.shutdown_deadline = None
        self.__prepare()
        
        self.node_thread = SelectThread(self)
        self.node_thread.setDaemon(True)
        self.node_thread.start()
        
        self.reconnect_thread = ReconnectThread(self)
        self.reconnect_thread.setDaemon(True)
        self.reconnect_thread.start()
        
        self.logger.log(logging.INFO,"Diameter node started")
    
    def stop(self,grace_time=0):
        """
        Stop the node.
        All connections are closed. A DPR is sent to the each connected
        peer unless the transport connection's buffers are full.
        Threads waiting in Node.waitForConnection() are woken.
        Graceful connection close is not guaranteed in all cases.
          grace_time  Maximum time to wait for connections to close gracefully.
        """
        self.logger.log(logging.INFO,"Stopping Diameter node")
        self.map_key_conn_cv.acquire()
        self.shutdown_deadline = time.time() + grace_time
        self.please_stop = True
        for connkey in list(self.map_key_conn.keys()):
            conn = self.map_key_conn[connkey]
            if conn.state==Connection.state_connecting or \
               conn.state==Connection.state_connected_in or \
               conn.state==Connection.state_connected_out:
                self.logger.log(logging.INFO,"Closing connection to %s because were are shutting down"%conn.host_id)
                del self.map_fd_conn[conn.fd.fileno()]
                del self.map_key_conn[connkey]
                conn.fd.close()
            elif conn.state==Connection.state_tls:
                pass #todo
            elif conn.state==Connection.state_ready:
                #self.__sendDPR(conn,ProtocolConstants.DI_DISCONNECT_CAUSE_REBOOTING)
                #self.__closeConnection_unlocked(conn,True)
                self.__initiateConnectionClose(conn,ProtocolConstants.DI_DISCONNECT_CAUSE_REBOOTING)
            elif conn.state==Connection.state_closing:
                pass #nothing to do
            elif conn.state==Connection.state_closed:
                pass #nothing to do
        self.map_key_conn_cv.release()
        self.__wakeSelectThread()
        self.map_key_conn_cv.acquire()
        self.map_key_conn_cv.notify()
        self.map_key_conn_cv.release()
        self.node_thread.join()
        self.node_thread = None
        self.reconnect_thread.join()
        self.reconnect_thread = None
        if self.sock_listen:
            self.sock_listen.close()
        self.sock_listen = None
        self.map_key_conn = {}
        self.map_fd_conn = {}
        self.logger.log(logging.INFO,"Diameter node stopped")
    
    def __prepare(self):
        if self.settings.port!=0:
            sock_listen = None
            for addr in socket.getaddrinfo(None, self.settings.port, 0, socket.SOCK_STREAM,socket.IPPROTO_TCP, socket.AI_PASSIVE):
                try:
                    sock_listen = socket.socket(addr[0], addr[1], addr[2])
                except socket.error:
                    #most likely error: server has IPv6 capability, but IPv6 not enabled locally
                    sock_listen = None
                    continue
                
                try:
                    sock_listen.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR,struct.pack("i",1));
                    sock_listen.bind(addr[4])
                    sock_listen.listen(10)
                except socket.error:
                    #most likely error: IPv6 enabled, but no interfaces has IPv6 address(es)
                    sock_listen.close()
                    sock_listen = None
                    continue
                
                #It worked...
                break
            
            if not sock_listen:
                raise StartError("Could not create listen-socket")
            self.sock_listen = sock_listen
        else:
            self.sock_listen = None
        self.map_key_conn = {}
    
    def __anyReadyConnection(self):
        rc=False
        self.map_key_conn_lock.acquire()
        for conn in list(self.map_key_conn.values()):
            if conn.state==Connection.state_ready:
                rc=True
                break
        self.map_key_conn_lock.release()
        return rc
    
    def waitForConnection(self,timeout=None):
        """Wait until at least one connection has been established or until the timeout expires.
        Waits until at least one connection to a peer has been established
        and capability-exchange has finished, or the specified timeout has expired.
          timeout  The maximum time to wait in seconds.
        """
        self.obj_conn_wait.acquire()
        if timeout==None:
            while not self.__anyReadyConnection():
                self.obj_conn_wait.wait()
        else:
            now = time.time()
            end = now+timeout
            while not self.__anyReadyConnection():
                now = time.time()
                w = end - now
                if w<0.0: break
                self.obj_conn_wait.wait(w)
        self.obj_conn_wait.release()

    def findConnection(self,peer):
        """Returns the connection key for a peer.
        Returns: The connection key. None if there is no connection to the peer.
        """
        self.logger.log(logging.DEBUG,"Finding '" + peer.host +"'")
        connkey=None
        self.map_key_conn_lock.acquire()
        for connkey2,conn in list(self.map_key_conn.items()):
            if conn.peer and conn.peer==peer:
                connkey=connkey2
                break
        self.map_key_conn_lock.release()
        if not connkey:
            self.logger.log(logging.DEBUG,peer.host+" NOT found")
        return connkey
    
    def isConnectionKeyValid(self,connkey):
        """Returns if the connection is still valid.
        This method is usually only of interest to programs that do lengthy
        processing of requests and are located in a poor network. It is
        usually much easier to just call sendMessage() and catch the
        exception if the connection has gone stale.
        """
        self.map_key_conn_lock.acquire()
        rc=connkey in self.map_key_conn
        self.map_key_conn_lock.release()
        return rc
    
    def connectionKey2Peer(self,connkey):
        self.map_key_conn_lock.acquire()
        try:
            peer = self.map_key_conn[connkey].peer
        except KeyError:
            peer = None
        self.map_key_conn_lock.release()
        return peer
    
    def connectionKey2InetAddress(self,connkey):
        self.map_key_conn_lock.acquire()
        try:
            conn = self.map_key_conn[connkey]
        except KeyError:
            self.map_key_conn_lock.release()
            return None
        a = conn.fd.getpeername()
        self.map_key_conn_lock.release()
        return a
    
    def nextHopByHopIdentifier(self,connkey):
        "Returns the next hop-by-hop identifier for a connection"
        self.map_key_conn_lock.acquire()
        try:
            conn = self.map_key_conn[connkey]
        except KeyError:
            self.map_key_conn_lock.release()
            raise StaleConnectionError()
        rc = conn.nextHopByHopIdentifier()
        self.map_key_conn_lock.release()
        return rc
    
    def sendMessage(self,msg,connkey):
        """Send a message.
        Send the specified message on the specified connection.
          msg      The message to be sent
          connkey  The connection to use. If the connection has been closed in
                   the meantime StaleConnectionError is thrown.
        """
        self.map_key_conn_lock.acquire()
        try:
            conn = self.map_key_conn[connkey]
        except KeyError:
            self.map_key_conn_lock.release()
            raise StaleConnectionError()
        if conn.state!=Connection.state_ready:
            self.map_key_conn_lock.release()
            raise StaleConnectionError()
        self.__sendMessage_unlocked(msg,conn)
        self.map_key_conn_lock.release()
    
    def __sendMessage_unlocked(self,msg,conn):
        self.logger.log(logging.DEBUG,"command=%d, to=%s"%(msg.hdr.command_code,conn.peer.host))
        p = xdrlib.Packer()
        msg.encode(p)
        raw = p.get_buffer()
        self.__hexDump(logging.DEBUG,"Sending to "+conn.host_id,raw);
        was_empty = not conn.hasNetOutput()
        conn.appendAppOutputBuffer(raw)
        conn.processAppOutBuffer()
        if was_empty:
            self.__handleWritable(conn)
            if conn.hasNetOutput():
                # still some output. Wake select thread so it re-evaluates fdsets
                self.__wakeSelectThread()
    
    def initiateConnection(self,peer,persistent=False):
        """Initiate a connection to a peer.
        A connection (if not already present) will be initiated to the peer.
        On return, the connection is probably not established and it may
        take a few seconds before it is. It is safe to call multiple times.
        If <code>persistent</code> true then the peer is added to a list of
        persistent peers and if the connection is lost it will automatically
        be re-established. There is no way to change a peer from persistent
        to non-persistent.
        
        If/when the connection has been established and capability-exchange
        has finished threads waiting in {@link #waitForConnection} are woken.
          peer        The peer that the node should try to establish a connection to.
          persistent  If true the Node wil try to keep a connection open to the peer.
        """
        if persistent:
            self.persistent_peers_lock.acquire()
            self.persistent_peers.add(peer)
            self.persistent_peers_lock.release()
        
        self.map_key_conn_lock.acquire()
        for conn in list(self.map_key_conn.values()):
            if conn.peer and \
               conn.peer == peer:
                #already has a connection to that peer
                self.map_key_conn_lock.release()
                return
            #what if we are connecting and the host_id matches?
        self.map_key_conn_lock.release()
        
        #look up the ip-address first without the large mutex held
        #We should really try all the possible addresses...
        try:
            ai = socket.getaddrinfo(peer.host,peer.port,0,socket.SOCK_STREAM,socket.IPPROTO_TCP)
        except socket.gaierror as ex:
            self.logger.log(logging.INFO,"getaddrinfo(%s/%d) failed"%(peer.host,peer.port),exc_info=ex)
            return
        
        self.logger.log(logging.INFO,"Initiating connection to '" + peer.host +"'");
        
        conn = Connection()
        conn.host_id = peer.host
        conn.peer = peer
        
        try:
            fd = socket.socket(ai[0][0], ai[0][1], ai[0][2]);
            fd.setblocking(False)
            fd.connect(ai[0][4])
        except socket.error as xxx_todo_changeme:
            (err,errstr) = xxx_todo_changeme.args
            import errno
            if err!=errno.EINPROGRESS:
                #real error
                self.logger.log(logging.ERROR,"socket() or connect() failed: %s"%errstr,exc_info=err)
                return
            conn.state = Connection.state_connecting
        else:
            self.logger.log(logging.DEBUG,"Connection to %s succeeded immediately"%peer.host)
            conn.state = Connection.state_connected_out
        conn.fd = fd
        
        self.map_key_conn_lock.acquire()
        self.map_key_conn[conn.key] = conn
        self.map_fd_conn[conn.fd.fileno()] = conn
        self.map_key_conn_lock.release()
        self.logger.log(logging.DEBUG,"connection state %s" % conn.state)
        if conn.state == Connection.state_connected_out:
            self.__sendCER(conn)
        else:
            self.__wakeSelectThread()

    def run_select(self):
        if self.sock_listen:
            self.sock_listen.setblocking(False)
        
        while True:
            if self.please_stop:
                if time.time()>=self.shutdown_deadline:
                    break
                self.map_key_conn_lock.acquire()
                isempty = len(self.map_key_conn)==0
                self.map_key_conn_lock.release()
                if isempty:
                    break
            
            #build FD sets
            self.map_key_conn_lock.acquire()
            iwtd=[]
            owtd=[]
            for conn in list(self.map_key_conn.values()):
                if conn.state!=Connection.state_closed:
                    iwtd.append(conn.fd)
                if conn.hasNetOutput() or conn.state == Connection.state_connecting:
                    owtd.append(conn.fd)
            self.map_key_conn_lock.release()
            if self.sock_listen:
                iwtd.append(self.sock_listen)
            iwtd.append(self.fd_pipe[0])
            #calc timeout
            timeout = self.__calcNextTimeout()
            #do select
            if timeout:
                now=time.time()
                if timeout>now:
                    ready_fds = select.select(iwtd,owtd,[],timeout - now)
                else:
                    ready_fds = select.select(iwtd,owtd,[])
            else:
                ready_fds = select.select(iwtd,owtd,[])
            for fd in ready_fds[0]:
                if fd==self.sock_listen:
                    #accept
                    self.logger.log(logging.DEBUG,"Got an inbound connection (key is acceptable)")
                    client = self.sock_listen.accept()
                    if client:
                        self.logger.log(logging.INFO,"Got an inbound connection from %s on %d"%(str(client[1]),client[0].fileno()))
                        if not self.please_stop:
                            conn = Connection()
                            conn.fd = client[0]
                            conn.fd.setblocking(False)
                            conn.host_id = client[1][0]
                            conn.state = Connection.state_connected_in
                            self.map_key_conn_lock.acquire()
                            self.map_key_conn[conn.key] = conn
                            self.map_fd_conn[conn.fd.fileno()] = conn
                            self.map_key_conn_lock.release()
                        else:
                            #We don't want to add the connection if were are shutting down.
                            client[0].close()
                    else:
                        self.logger.log(logging.DEBUG,"Spurious wakeup on listen socket")
                elif fd==self.fd_pipe[0]:
                    self.logger.log(logging.DEBUG,"wake-up pipe ready")
                    self.fd_pipe[0].recv(16)
                else:
                    #readable
                    self.logger.log(logging.DEBUG,"fd is readable")
                    self.map_key_conn_lock.acquire()
                    conn = self.map_fd_conn[fd.fileno()]
                    self.map_key_conn_lock.release()
                    self.__handleReadable(conn)
                    if conn.state==Connection.state_closed:
                        #remove from ready_fds[1] to avoid silly exception in fileno() call
                        for i in range(0,len(ready_fds[1])):
                            if ready_fds[1][i]==conn.fd:
                                del ready_fds[1][i]
                                break;
            for fd in ready_fds[1]:
                self.map_key_conn_lock.acquire()
                conn = self.map_fd_conn[fd.fileno()]
                if conn.state==Connection.state_connecting:
                    #connection status ready
                    self.logger.log(logging.DEBUG,"An outbound connection is ready (key is connectable)")
                    err = fd.getsockopt(socket.SOL_SOCKET,socket.SO_ERROR)
                    if err==0:
                        self.logger.log(logging.DEBUG,"Connected!")
                        conn.state = Connection.state_connected_out
                        self.__sendCER(conn)
                    else:
                        self.logger.log(logging.WARNING,"Connection to '"+conn.host_id+"' failed", ex)
                        fd.close()
                        del self.map_key_conn[conn.key]
                        del self.map_fd_conn[fd.fileno()]
                else:
                    #plain writable
                    self.logger.log(logging.DEBUG,"fd is writable")
                    self.__handleWritable(conn)
                self.map_key_conn_lock.release()
            
            self.__runTimers()
        
        #close all connections
        self.logger.log(logging.DEBUG,"Closing all transport connections")
        self.map_key_conn_lock.acquire()
        for connkey in list(self.map_key_conn.keys()):
            conn = self.map_key_conn[connkey]
            self.__closeConnection_unlocked(conn,True)
        self.map_key_conn_lock.release()
    
    def __wakeSelectThread(self):
        self.fd_pipe[1].send(b"d")
    
    def __calcNextTimeout(self):
        timeout = None
        self.map_key_conn_lock.acquire()
        for conn in list(self.map_key_conn.values()):
            ready = (conn.state==Connection.state_ready)
            conn_timeout = conn.timers.calcNextTimeout(ready)
            if conn_timeout and ((not timeout) or conn_timeout<timeout):
                timeout = conn_timeout
        self.map_key_conn_lock.release()
        if self.please_stop:
            if (not timeout) or self.shutdown_deadline<timeout:
                timeout = self.shutdown_deadline
        return timeout
    
    def __runTimers(self):
        self.map_key_conn_lock.acquire()
        for connkey in list(self.map_key_conn.keys()):
            conn = self.map_key_conn[connkey]
            ready = (conn.state==Connection.state_ready)
            action=conn.timers.calcAction(ready)
            if action==ConnectionTimers.timer_action_none:
                pass
            elif action==ConnectionTimers.timer_action_disconnect_no_cer:
                self.logger.log(logging.WARNING,"Disconnecting due to no CER/CEA")
                self.__closeConnection_unlocked(conn)
            elif action==ConnectionTimers.timer_action_disconnect_idle:
                self.logger.log(logging.WARNING,"Disconnecting due to idle")
                #busy is the closest thing to "no traffic for a long time. No point in keeping the connection"
                self.__sendDPR(conn,ProtocolConstants.DI_DISCONNECT_CAUSE_BUSY);
                self.__closeConnection_unlocked(conn)
            elif action==ConnectionTimers.timer_action_disconnect_no_dw:
                self.logger.log(logging.WARNING,"Disconnecting due to no DWA")
                self.__closeConnection_unlocked(conn)
            elif action==ConnectionTimers.timer_action_dwr:
                self.__sendDWR(conn)
        self.map_key_conn_lock.release()
    
    def run_reconnect(self):
        while True:
            self.map_key_conn_cv.acquire()
            if self.please_stop:
                self.map_key_conn_cv.release()
                break
            self.map_key_conn_cv.wait(30.0)
            self.map_key_conn_cv.release()
            
            self.persistent_peers_lock.acquire()
            for pp in self.persistent_peers:
                self.initiateConnection(pp,False);
            self.persistent_peers_lock.release()
    
    def __handleReadable(self,conn):
        self.logger.log(logging.DEBUG,"handlereadable()...")
        try:
            stuff = conn.fd.recv(32768)
        except socket.error as xxx_todo_changeme1:
            (err,errstr) = xxx_todo_changeme1.args
            if isTransientError(err):
                #Not a real error
                self.logger.log(logging.DEBUG,"recv() failed, err=%d, errstr=%s"%(err,errstr))
                return
            #hard error
            self.logger.log(logging.INFO,"recv() failed, err=%d, errstr=%s"%(err,errstr))
            self.__closeConnection(conn)
            return
        if len(stuff)==0:
            #peer closed connection
            self.logger.log(logging.DEBUG,"Read 0 bytes from peer")
            self.__closeConnection(conn)
            return
        
        conn.appendNetInBuffer(stuff)
        conn.processNetInBuffer()
        self.__processInBuffer(conn)
    
    def __hexDump(self,level,msg,raw):
        if not self.logger.isEnabledFor(level): return
        #todo: there must be a faster way of doing this...
        s=msg+'\n'
        for i in range(0,len(raw),16):
            l = "%04x " % i
            for j in range(i,i+16):
                if (j % 4)==0:
                    l += " "
                if j<len(raw):
                    l += "%02x" % raw[j]
                else:
                    l += '  '
            l += "     "
            for j in range(i,min(i+16,len(raw))):
                b = raw[j]
                if b>=32 and b<127:
                    l += str(chr(raw[j]))
                else:
                    l += '.'
            s += l + '\n'
        self.logger.log(level,s)
    
    def __processInBuffer(self,conn):
        self.logger.log(logging.DEBUG,"Node.__processInBuffer()")
        raw = conn.getAppInBuffer()
        self.logger.log(logging.DEBUG,"len(raw)=%d"%len(raw))
        u = xdrlib.Unpacker(raw)
        while u.get_position()<len(raw):
            msg_start = u.get_position()
            bytes_left = len(raw)-msg_start
            #print "  msg_start=",msg_start," bytes_left=",bytes_left
            if bytes_left<4:
                break
            msg_size = Message.decodeSize(u)
            if bytes_left<msg_size:
                break
            msg = Message()
            status = msg.decode(u,msg_size)
            #print "  state=",status
            if status==Message.decode_status_decoded:
                self.__hexDump(logging.DEBUG,"Got message "+conn.host_id,raw[msg_start:msg_start+msg_size]);
                b = self.__handleMessage(msg,conn)
                if not b:
                    self.logger.log(logging.DEBUG,"handle error")
                    self.__closeConnection(conn)
                    return
            elif status==Message.decode_status_not_enough:
                break #?
            elif status==Message.decode_status_garbage:
                self.__hexDump(logging.WARNING,"Garbage from "+conn.host_id,raw[msg_start:msg_start+msg_size]);
                #self.__hexDump(logging.INFO,"Complete inbuffer: ",raw,0,raw_bytes);
                self.__closeConnection(conn,reset=True)
                return
        conn.consumeAppInBuffer(u.get_position())
    
    
    def __handleWritable(self,conn):
        self.logger.log(logging.DEBUG,"__handleWritable():")
        raw = conn.getNetOutBuffer()
        if len(raw)==0: return
        try:
            bytes_sent = conn.fd.send(raw)
        except socket.error as xxx_todo_changeme2:
            (err,errstr) = xxx_todo_changeme2.args
            if isTransientError(err):
                #Not a real error
                self.logger.log(logging.DEBUG,"send() failed, err=%d, errstr=%s"%(err,errstr))
                return
            #hard error
            self.logger.log(logging.INFO,"send() failed, err=%d, errstr=%s"%(err,errstr))
            self.__closeConnection_unlocked(conn)
            return
            
        conn.consumeNetOutBuffer(bytes_sent)
    
    def __closeConnection_unlocked(self,conn,reset=False):
        if conn.state==Connection.state_closed:
            return
        self.logger.log(logging.INFO,"Closing unlocked connection to " + conn.host_id)
        del self.map_key_conn[conn.key]
        del self.map_fd_conn[conn.fd.fileno()]
        if reset:
            #Set lingertime to zero to force a RST when closing the socket
            #rfc3588, section 2.1
           conn.fd.setsockopt(socket.SOL_SOCKET,socket.SO_LINGER,struct.pack("ii",1,0))
           pass
        conn.fd.close()
        if self.connection_listener:
            self.connection_listener.handle_connection(conn.key,conn.peer,False)
        conn.state = Connection.state_closed
    
    def __closeConnection(self,conn,reset=False):
        self.logger.log(logging.INFO,"Closing connection to " + conn.host_id)
        self.map_key_conn_lock.acquire()
        self.__closeConnection_unlocked(conn,reset)
        self.map_key_conn_lock.release()
        self.logger.log(logging.DEBUG,"Closed connection to " + conn.host_id)
    
    def __initiateConnectionClose(self,conn,why):
        if conn.state!=Connection.state_ready:
            return #Should probably never happen
        self.__sendDPR(conn,why)
        conn.state = Connection.state_closing
    
    def __handleMessage(self,msg,conn):
        if self.logger.isEnabledFor(logging.DEBUG):
            self.logger.log(logging.DEBUG,"command_code=%d application_id=%d connection_state=%d"%(msg.hdr.command_code,msg.hdr.application_id,conn.state))
        conn.timers.markActivity()
        if conn.state==Connection.state_connected_in:
            #only CER allowed
            if (not msg.hdr.isRequest()) or \
               msg.hdr.command_code!=ProtocolConstants.DIAMETER_COMMAND_CAPABILITIES_EXCHANGE or \
               msg.hdr.application_id!=ProtocolConstants.DIAMETER_APPLICATION_COMMON:
                self.logger.log(logging.WARNING,"Got something that wasn't a CER")
                return False
            conn.timers.markRealActivity()
            return self.__handleCER(msg,conn);
        elif conn.state==Connection.state_connected_out:
            #only CEA allowed
            if msg.hdr.isRequest() or \
               msg.hdr.command_code!=ProtocolConstants.DIAMETER_COMMAND_CAPABILITIES_EXCHANGE or \
               msg.hdr.application_id!=ProtocolConstants.DIAMETER_APPLICATION_COMMON:
                self.logger.log(logging.WARNING,"Got something that wasn't a CEA")
                return False
            conn.timers.markRealActivity()
            return self.__handleCEA(msg,conn)
        else:
            if msg.hdr.command_code==ProtocolConstants.DIAMETER_COMMAND_CAPABILITIES_EXCHANGE:
                self.logger.log(logging.WARNING,"Got CER from "+conn.host_id+" after initial capability-exchange")
                #not allowed in this state
                return False
            elif msg.hdr.command_code==ProtocolConstants.DIAMETER_COMMAND_DEVICE_WATCHDOG:
                if msg.hdr.isRequest():
                    return self.__handleDWR(msg,conn);
                else:
                    return self.__handleDWA(msg,conn);
            elif msg.hdr.command_code==ProtocolConstants.DIAMETER_COMMAND_DISCONNECT_PEER:
                if msg.hdr.isRequest():
                    return self.__handleDPR(msg,conn);
                else:
                    return self.__handleDPA(msg,conn)
            else:
                conn.timers.markRealActivity();
                if msg.hdr.isRequest():
                    if self.__isLoopedMessage(msg):
                        self.__rejectLoopedRequest(msg,conn)
                        return True
                    if not self.isAllowedApplication(msg,conn.peer):
                        self.__rejectDisallowedRequest(msg,conn)
                        return True
                if not self.message_dispatcher.handle_message(msg,conn.key,conn.peer):
                    if msg.hdr.isRequest():
                        return self.__handleUnknownRequest(msg,conn)
                    else:
                        return True #unusual, but not impossible
                else:
                    return True
    
    def __isLoopedMessage(self,msg):
        #6.1.3
        for a in msg.subset(ProtocolConstants.DI_ROUTE_RECORD):
            avp = AVP_UTF8String.narrow(a)
            if avp.queryValue() == self.settings.host_id:
                return True
        return False
    
    def __rejectLoopedRequest(self,msg,conn):
        self.logger.log(logging.WARNING,"Rejecting looped request from %s (command=%d)"%(conn.peer.host,msg.hdr.command_code))
        self.__rejectRequest(msg,conn,ProtocolConstants.DIAMETER_RESULT_LOOP_DETECTED)
    
    def isAllowedApplication(self,msg,peer):
        """Determine if a message is supported by a peer.
        The auth-application-id, acct-application-id or
        vendor-specific-application AVP is extracted and tested against the
        peer's capabilities.
          msg   The message
          peer  The peer
        Returns: True if the peer should be able to handle the message.
        """
        try:
            avp = msg.find(ProtocolConstants.DI_AUTH_APPLICATION_ID)
            if avp:
                app = AVP_Unsigned32.narrow(avp).queryValue()
                self.logger.log(logging.DEBUG,"auth-application-id=%d"%app)
                return peer.capabilities.isAllowedAuthApp(app)
            avp = msg.find(ProtocolConstants.DI_ACCT_APPLICATION_ID)
            if avp:
                app = AVP_Unsigned32.narrow(avp).queryValue()
                self.logger.log(logging.DEBUG,"acct-application-id=%d"%app);
                return peer.capabilities.isAllowedAcctApp(app)
            avp = msg.find(ProtocolConstants.DI_VENDOR_SPECIFIC_APPLICATION_ID)
            if avp:
                g = AVP_Grouped.narrow(avp).getAVPs()
                if len(g)==2 and \
                   g[0].code==ProtocolConstants.DI_VENDOR_ID:
                    vendor_id = AVP_Unsigned32.narrow(g[0]).queryValue()
                    app = AVP_Unsigned32.narrow(g[1]).queryValue()
                    self.logger.log(logging.DEBUG,"vendor-id=%d, app=%d"%(vendor_id,app))
                    if g[1].code==ProtocolConstants.DI_AUTH_APPLICATION_ID:
                        return peer.capabilities.isAllowedVendorAuthApp(vendor_id,app)
                    if g[1].code==ProtocolConstants.DI_ACCT_APPLICATION_ID:
                        return peer.capabilities.isAllowedVendorAcctApp(vendor_id,app)
                return False
            self.logger.log(logging.WARNING,"No auth-app-id, acct-app-id nor vendor-app in packet")
        except InvalidAVPLengthError as ex:
            self.logger.log(logging.INFO,"Encountered invalid AVP length while looking at application-id",exc_info=ex);
        return False
    
    def __rejectDisallowedRequest(self,msg,conn):
        self.logger.log(logging.WARNING,"Rejecting request  from " + conn.peer.host + " (command=" + msg.hdr.command_code + ") because it is not allowed.")
        self.__rejectRequest(msg,conn,ProtocolConstants.DIAMETER_RESULT_APPLICATION_UNSUPPORTED)

    def __rejectRequest(self,msg,conn,result_code):
        response = Message()
        response.prepareResponse(msg)
        response.append(AVP_Unsigned32(ProtocolConstants.DI_RESULT_CODE, result_code))
        self.addOurHostAndRealm(response)
        Utils.copyProxyInfo(msg,response)
        Utils.setMandatory_RFC3588(response)
        self.sendMessage(response,conn.key);
    
    def addOurHostAndRealm(self,msg):
        """Add origin-host and origin-realm to a message.
        The configured host and realm is added to the message as origin-host
        and origin-realm AVPs
        """
        msg.append(AVP_UTF8String(ProtocolConstants.DI_ORIGIN_HOST,self.settings.host_id))
        msg.append(AVP_UTF8String(ProtocolConstants.DI_ORIGIN_REALM,self.settings.realm))
    
    def nextEndToEndIdentifier(self):
        """Returns an end-to-end identifier that is unique.
        The initial value is generated as described in RFC 3588 section 3 page 34.
        """
        return self.node_state.nextEndToEndIdentifier()
    
    def __doElection(self,cer_host_id):
        #5.6.4
        c = cmp(self.settings.host_id,cer_host_id)
        if c==0:
            #this is a misconfigured peer or ourselves.
            return False
        
        close_other_connection = c>0
        rc = True
        self.map_key_conn_cv.acquire()
        for connkey,conn in list(self.map_key_conn.items()):
            if conn.host_id and conn.host_id==cer_host_id:
                if close_other_connection:
                    self.__closeConnection(conn)
                    rc = True
                    break
                else:
                    rc = False #close this one
                    break
        self.map_key_conn_cv.release()
        return rc

    def __handleCER(self,msg,conn):
        self.logger.log(logging.DEBUG,"CER received from " + conn.host_id);
        #Handle election
        avp = msg.find(ProtocolConstants.DI_ORIGIN_HOST)
        if not avp:
            #Origin-Host-Id is missing
            error_response = Message()
            error_response.prepareResponse(msg)
            error_response.append(AVP_Unsigned32(ProtocolConstants.DI_RESULT_CODE, ProtocolConstants.DIAMETER_RESULT_MISSING_AVP))
            self.addOurHostAndRealm(error_response);
            error_response.append(AVP_FailedAVP(AVP_UTF8String(ProtocolConstants.DI_ORIGIN_HOST,"")))
            Utils.setMandatory_RFC3588(error_response)
            self.__sendMessage_unlocked(error_response,conn)
            return False
        host_id = AVP_UTF8String.narrow(avp).queryValue()
        self.logger.log(logging.DEBUG,"Peer's origin-host-id is " + host_id)
        if not self.__doElection(host_id):
            error_response = Message()
            error_response.prepareResponse(msg)
            error_response.append(AVP_Unsigned32(ProtocolConstants.DIAMETER_RESULT_ELECTION_LOST, ProtocolConstants.DIAMETER_RESULT_MISSING_AVP))
            self.addOurHostAndRealm(error_response)
            Utils.setMandatory_RFC3588(error_response)
            self.__sendMessage_unlocked(error_response,conn)
            return False
        
        conn.peer = Peer(socket_address=conn.fd.getpeername())
        conn.peer.host = host_id
        conn.host_id = host_id
        
        if self.__handleCEx(msg,conn):
            #todo: check inband-security
            cea = Message()
            cea.prepareResponse(msg)
            #Result-Code
            cea.append(AVP_Unsigned32(ProtocolConstants.DI_RESULT_CODE, ProtocolConstants.DIAMETER_RESULT_SUCCESS))
            self.__addCEStuff(cea,conn.peer.capabilities,conn)
            
            self.logger.log(logging.INFO,"Connection to " +conn.host_id + " is now ready")
            Utils.setMandatory_RFC3588(cea);
            self.__sendMessage_unlocked(cea,conn)
            conn.state=Connection.state_ready;
            
            if self.connection_listener:
                self.connection_listener.handle_connection(conn.key, conn.peer, True)
            self.obj_conn_wait.acquire()
            self.obj_conn_wait.notifyAll()
            self.obj_conn_wait.release()
            return True
        else:
            return False

    def __handleCEA(self,msg,conn):
        self.logger.log(logging.DEBUG,"CEA received from "+conn.host_id)
        avp = msg.find(ProtocolConstants.DI_ORIGIN_HOST)
        if not avp:
            self.logger.log(logging.WARNING,"Peer did not include origin-host-id in CEA")
            return False
        host_id = AVP_UTF8String.narrow(avp).queryValue()
        self.logger.log(logging.DEBUG,"Node:Peer's origin-host-id is '"+host_id+"'")
        
        conn.peer = Peer(socket_address=conn.fd.getpeername())
        conn.peer.host = host_id
        conn.host_id = host_id
        
        rc = self.__handleCEx(msg,conn)
        if rc:
            conn.state=Connection.state_ready;
            self.logger.log(logging.INFO,"Connection to " +conn.host_id + " is now ready")
            if self.connection_listener:
                self.connection_listener.handle_connection(conn.key, conn.peer, True)
            self.obj_conn_wait.acquire()
            self.obj_conn_wait.notifyAll()
            self.obj_conn_wait.release()
            return True
        else:
            return False
    
    def __handleCEx(self,msg,conn):
        self.logger.log(logging.DEBUG,"Processing CER/CEA");
        #calculate capabilities and allowed applications
        try:
            reported_capabilities = Capability()
            for a in msg.subset(ProtocolConstants.DI_SUPPORTED_VENDOR_ID):
                vendor_id = AVP_Unsigned32.narrow(a).queryValue()
                self.logger.log(logging.DEBUG,"peer supports vendor %d"%vendor_id)
                reported_capabilities.addSupportedVendor(vendor_id)
            for a in msg.subset(ProtocolConstants.DI_AUTH_APPLICATION_ID):
                app = AVP_Unsigned32.narrow(a).queryValue()
                self.logger.log(logging.DEBUG,"peer supports auth-app %d"%app)
                if app!=ProtocolConstants.DIAMETER_APPLICATION_COMMON:
                    reported_capabilities.addAuthApp(app)
            for a in msg.subset(ProtocolConstants.DI_ACCT_APPLICATION_ID):
                app = AVP_Unsigned32.narrow(a).queryValue()
                self.logger.log(logging.DEBUG,"peer supports acct-app %d"%app)
                if app!=ProtocolConstants.DIAMETER_APPLICATION_COMMON:
                    reported_capabilities.addAcctApp(app)
            for a in msg.subset(ProtocolConstants.DI_VENDOR_SPECIFIC_APPLICATION_ID):
                ag = AVP_Grouped.narrow(a)
                g = ag.getAVPs()
                if len(g)>=2 and len(g)<=3:
                    #Some non-compliant implementations add both
                    #auth-application-id and acct-application-id,
                    #probably due to a weakly ambiguous 6.11 in rfc3588
                    vendor_id = None
                    auth_app_id = None
                    acct_app_id = None
                    for ga in g:
                        if ga.code==ProtocolConstants.DI_VENDOR_ID:
                            vendor_id = AVP_Unsigned32.narrow(ga).queryValue()
                        elif ga.code==ProtocolConstants.DI_AUTH_APPLICATION_ID:
                            auth_app_id = AVP_Unsigned32.narrow(ga).queryValue()
                        elif ga.code==ProtocolConstants.DI_ACCT_APPLICATION_ID:
                            acct_app_id = AVP_Unsigned32.narrow(ga).queryValue()
                        else:
                            raise InvalidAVPValueError(a)
                    if (not vendor_id) or not (auth_app_id or acct_app_id):
                        raise InvalidAVPValueError(a)
                    if auth_app_id!=None:
                        reported_capabilities.addVendorAuthApp(vendor_id,auth_app_id)
                        self.logger.log(logging.DEBUG,"peer supports auth-app %d"%auth_app_id)
                    if acct_app_id!=None:
                        reported_capabilities.addVendorAcctApp(vendor_id,acct_app_id)
                        self.logger.log(logging.DEBUG,"peer supports acct-app %d"%acct_app_id)
                else:
                    raise InvalidAVPValueError(a)
            
            result_capabilities = Capability.calculateIntersection(self.settings.capabilities, reported_capabilities)
            if self.logger.isEnabledFor(logging.DEBUG):
                s = ""
                for i in result_capabilities.supported_vendor:
                    s += "  supported_vendor %d\n"%i
                for i in result_capabilities.auth_app:
                    s += "  auth_app %d\n"%i
                for i in result_capabilities.acct_app:
                    s += "  acct_app %d\n"%i
                self.logger.log(logging.DEBUG,"Resulting capabilities:\n"+s)
            if result_capabilities.isEmpty():
                self.logger.log(logging.INFO,"No applications in common with %s"%conn.host_id)
                if msg.hdr.isRequest():
                    error_response = Message()
                    error_response.prepareResponse(msg)
                    error_response.append(AVP_Unsigned32(ProtocolConstants.DI_RESULT_CODE, ProtocolConstants.DIAMETER_RESULT_NO_COMMON_APPLICATION))
                    self.addOurHostAndRealm(error_response)
                    Utils.setMandatory_RFC3588(error_response)
                    self.__sendMessage_unlocked(error_response,conn)
                return False
            
            conn.peer.capabilities = result_capabilities
        except InvalidAVPLengthError as ex:
            self.logger.log(logging.WARNING,"Invalid AVP in CER/CEA",exc_info=ex)
            if msg.hdr.isRequest():
                error_response = Message()
                error_response.prepareResponse(msg);
                error_response.append(AVP_Unsigned32(ProtocolConstants.DI_RESULT_CODE, ProtocolConstants.DIAMETER_RESULT_INVALID_AVP_LENGTH))
                self.addOurHostAndRealm(error_response)
                error_response.append(AVP_FailedAVP(ex.avp))
                Utils.setMandatory_RFC3588(error_response)
                self.__sendMessage_unlocked(error_response,conn)
            return False
        except InvalidAVPValueError as ex:
            self.logger.log(logging.WARNING,"Invalid AVP in CER/CEA",exc_info=ex);
            if msg.hdr.isRequest():
                error_response = Message()
                error_response.prepareResponse(msg)
                error_response.append(AVP_Unsigned32(ProtocolConstants.DI_RESULT_CODE, ProtocolConstants.DIAMETER_RESULT_INVALID_AVP_VALUE))
                self.addOurHostAndRealm(error_response)
                error_response.append(AVP_FailedAVP(ex.avp))
                Utils.setMandatory_RFC3588(error_response)
                self.__sendMessage_unlocked(error_response,conn)
            return False
        return True

    def __sendCER(self,conn):
        self.logger.log(logging.DEBUG,"Sending CER to "+conn.host_id)
        cer = Message()
        cer.hdr.setRequest(True)
        cer.hdr.command_code = ProtocolConstants.DIAMETER_COMMAND_CAPABILITIES_EXCHANGE
        cer.hdr.application_id = ProtocolConstants.DIAMETER_APPLICATION_COMMON
        cer.hdr.hop_by_hop_identifier = conn.nextHopByHopIdentifier()
        cer.hdr.end_to_end_identifier = self.node_state.nextEndToEndIdentifier()
        self.__addCEStuff(cer,self.settings.capabilities,conn)
        Utils.setMandatory_RFC3588(cer)
        
        self.__sendMessage_unlocked(cer,conn)

    def __addCEStuff(self,msg,capabilities,conn):
        #Origin-Host, Origin-Realm
        self.addOurHostAndRealm(msg);
        #Host-IP-Address
        #  This is not really that good...
        if conn.peer and conn.peer.use_ericsson_host_ip_address_format:
            #Some servers (ericsson) requires a non-compliant payload in the host-ip-address AVP
            tmp_avp = AVP_Address(ProtocolConstants.DI_HOST_IP_ADDRESS, conn.fd.getsockname()[0])
            msg.append(AVP(ProtocolConstants.DI_HOST_IP_ADDRESS, tmp_avp.payload[2:]))
        else:
            msg.append(AVP_Address(ProtocolConstants.DI_HOST_IP_ADDRESS, conn.fd.getsockname()[0]))
        #Vendor-Id
        msg.append(AVP_Unsigned32(ProtocolConstants.DI_VENDOR_ID, self.settings.vendor_id))
        #Product-Name
        msg.append(AVP_UTF8String(ProtocolConstants.DI_PRODUCT_NAME, self.settings.product_name))
        #Origin-State-Id
        msg.append(AVP_Unsigned32(ProtocolConstants.DI_ORIGIN_STATE_ID, self.node_state.state_id));
        #Error-Message, Failed-AVP: not in success
        #Supported-Vendor-Id
        for i in capabilities.supported_vendor:
            msg.append(AVP_Unsigned32(ProtocolConstants.DI_SUPPORTED_VENDOR_ID,i))
        #Auth-Application-Id
        for i in capabilities.auth_app:
            msg.append(AVP_Unsigned32(ProtocolConstants.DI_AUTH_APPLICATION_ID,i))
        #Inband-Security-Id
        #  todo
        #Acct-Application-Id
        for i in capabilities.acct_app:
            msg.append(AVP_Unsigned32(ProtocolConstants.DI_ACCT_APPLICATION_ID,i))
        #Vendor-Specific-Application-Id
        for va in capabilities.auth_vendor:
            g = []
            g.append(AVP_Unsigned32(ProtocolConstants.DI_VENDOR_ID,va.vendor_id))
            g[-1].setMandatory(True)
            g.append(AVP_Unsigned32(ProtocolConstants.DI_AUTH_APPLICATION_ID,va.application_id))
            g[-1].setMandatory(True)
            msg.append(AVP_Grouped(ProtocolConstants.DI_VENDOR_SPECIFIC_APPLICATION_ID,g))
        for va in capabilities.acct_vendor:
            g = []
            g.append(AVP_Unsigned32(ProtocolConstants.DI_VENDOR_ID,va.vendor_id))
            g[-1].setMandatory(True)
            g.append(AVP_Unsigned32(ProtocolConstants.DI_ACCT_APPLICATION_ID,va.application_id))
            g[-1].setMandatory(True)
            msg.append(AVP_Grouped(ProtocolConstants.DI_VENDOR_SPECIFIC_APPLICATION_ID,g))
        #Firmware-Revision
        if self.settings.firmware_revision!=0:
            msg.append(AVP_Unsigned32(ProtocolConstants.DI_FIRMWARE_REVISION,self.settings.firmware_revision))


    def __handleDWR(self,msg,conn):
        self.logger.log(logging.INFO,"DWR received from "+conn.host_id);
        conn.timers.markDWR()
        dwa = Message()
        dwa.prepareResponse(msg)
        dwa.append(AVP_Unsigned32(ProtocolConstants.DI_RESULT_CODE, ProtocolConstants.DIAMETER_RESULT_SUCCESS))
        self.addOurHostAndRealm(dwa)
        dwa.append(AVP_Unsigned32(ProtocolConstants.DI_ORIGIN_STATE_ID, self.node_state.state_id))
        Utils.setMandatory_RFC3588(dwa)
        
        self.sendMessage(dwa,conn.key)
        return True

    def __handleDWA(self,msg,conn):
        self.logger.log(logging.DEBUG,"DWA received from "+conn.host_id)
        conn.timers.markDWA()
        return True
    
    def __handleDPR(self,msg,conn):
        self.logger.log(logging.DEBUG,"DPR received from "+conn.host_id);
        dpa = Message()
        dpa.prepareResponse(msg)
        dpa.append(AVP_Unsigned32(ProtocolConstants.DI_RESULT_CODE, ProtocolConstants.DIAMETER_RESULT_SUCCESS))
        self.addOurHostAndRealm(dpa)
        Utils.setMandatory_RFC3588(dpa)
        
        self.sendMessage(dpa,conn.key)
        return False
    
    def __handleDPA(self,msg,conn):
        if conn.state==Connection.state_closing:
            self.logger.log(logging.INFO,"Got a DPA from %s"%conn.host_id)
        else:
            self.logger.log(logging.WARNING,"Got a DPA. This is not expected")
        return False #in any case close the connection
    
    def __handleUnknownRequest(self,msg,conn):
        self.logger.log(logging.INFO,"Unknown request received from "+conn.host_id);
        answer = Message()
        answer.prepareResponse(msg)
        answer.append(AVP_Unsigned32(ProtocolConstants.DI_RESULT_CODE, ProtocolConstants.DIAMETER_RESULT_UNABLE_TO_DELIVER))
        self.addOurHostAndRealm(answer)
        Utils.setMandatory_RFC3588(answer)
        
        self.sendMessage(answer,conn.key)
        return True

    def __sendDWR(self,conn):
        self.logger.log(logging.DEBUG,"Sending DWR to "+conn.host_id);
        dwr = Message()
        dwr.hdr.setRequest(True)
        dwr.hdr.command_code = ProtocolConstants.DIAMETER_COMMAND_DEVICE_WATCHDOG
        dwr.hdr.application_id = ProtocolConstants.DIAMETER_APPLICATION_COMMON
        dwr.hdr.hop_by_hop_identifier = conn.nextHopByHopIdentifier()
        dwr.hdr.end_to_end_identifier = self.node_state.nextEndToEndIdentifier()
        self.addOurHostAndRealm(dwr)
        dwr.append(AVP_Unsigned32(ProtocolConstants.DI_ORIGIN_STATE_ID, self.node_state.state_id))
        Utils.setMandatory_RFC3588(dwr)
        
        self.__sendMessage_unlocked(dwr,conn)
        
        conn.timers.markDWR_out()
    
    def __sendDPR(self,conn,why):
        self.logger.log(logging.DEBUG,"Sending DPR to "+conn.host_id);
        dpr = Message()
        dpr.hdr.setRequest(True)
        dpr.hdr.command_code = ProtocolConstants.DIAMETER_COMMAND_DISCONNECT_PEER
        dpr.hdr.application_id = ProtocolConstants.DIAMETER_APPLICATION_COMMON
        dpr.hdr.hop_by_hop_identifier = conn.nextHopByHopIdentifier()
        dpr.hdr.end_to_end_identifier = self.node_state.nextEndToEndIdentifier()
        self.addOurHostAndRealm(dpr)
        dpr.append(AVP_Unsigned32(ProtocolConstants.DI_DISCONNECT_CAUSE, why))
        Utils.setMandatory_RFC3588(dpr)
        
        self.__sendMessage_unlocked(dpr,conn)
    
    def makeNewSessionId(self,optional_part=None):
        """Generate a new session-id
        A Session-Id consists of a mandatory part and an optional part.
        The mandatory part consists of the host-id and two sequencer.
        The optional part can be anything. The caller provide some
        information that will be helpful in debugging in production
        environments, such as user-name or calling-station-id.
        """
        mandatory_part = self.settings.host_id + ";" + self.node_state.nextSessionId_second_part()
        if not optional_part:
            return bytes(mandatory_part, 'utf-8')
        else:
            return bytes(mandatory_part + ";" + optional_part, 'utf-8')

def isTransientError(err):
    return err==errno.EAGAIN or \
           err==errno.EWOULDBLOCK or \
           err==errno.ENOBUFS or \
           err==errno.ENOSR or \
           err==errno.EINTR

