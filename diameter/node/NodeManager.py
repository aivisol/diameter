from diameter.node.Node import Node
from diameter.node.Error import * #NotRoutableError,NotARequestError
from diameter import *
import logging
import threading

class NodeManager:
    """A Node manager.
    The NodeManager class manages a Node instance and keeps track of
    connections and in-/our-going messages and their end-to-end and
    hop-by-hop identifiers.
    You can build proxies, redirect agents, servers and clients on top of
    it. NodeManager is meant to be subclassed and subclasses should
    override handleRequest() and handleAnswer()
    """
    #If your needs are even simpler then have a look at {@link SimpleSyncClient} and {@link dk.i1.diameter.session.SessionManager}
    
    def __init__(self,settings):
        """
        Constructor for NodeManager.
        A Node instance is constructed using the specified settings, and
        the internal state is initialized.
        """
        self.node = Node(self,self,settings)
        self.settings = settings
        self.req_map = {}
        self.req_map_lock = threading.Lock()
        self.logger = logging.getLogger("dk.i1.diameter.node")
    
    def start(self):
        """
        Starts the embedded Node.
        """
        self.node.start()
    
    def stop(self,grace_time=0):
        """
        Stops the embedded Node and call handleAnswer() with null messages
        for outstanding requests.
        """
        self.node.stop(grace_time)
        self.req_map_lock.acquire()
        for connkey,reqs in list(self.req_map.items()):
            for req in list(reqs.values()):
                handleAnswer(None,connkey,req)
        self.req_map_lock.release()
    
    def waitForConnection(self,timeout=None):
        """
        Waits until at least one connection to a peer has been established
        and capability-exchange has finished.
        """
        self.node.waitForConnection(timeout)
    
    
    def handleRequest(self,request,connkey,peer):
        """
        Handle a request.
        This method is called when a request arrives. It is meant to be
        overridden by a subclass. This implementation rejects all requests.
        
        Please note that the handleRequest() method is called by the
        networking thread and messages from other peers cannot be received
        until the method returns. If the handleRequest() method needs to do
        any lengthy processing then it should implement a message queue,
        put the message into the queue, and return. The requests can then
        be processed by a worker thread pool without stalling the
        networking layer.
          request  The incoming request.
          connkey  The connection from where the request came.
          peer     The peer that sent the request. This is not the
                   originating peer but the peer directly connected to us
                   that sent us the request.
        """
        #incoming requests are not expected by this node
        answer = Message()
        self.logger.log(logging.DEBUG,"Handling incoming request, command_code=%d, end2end=%d, hopbyhop=%d"%(request.hdr.command_code,peer.host,request.hdr.end_to_end_identifier,request.hdr.hop_by_hop_identifier))
        answer.prepareResponse(request)
        answer.add(AVP_Unsigned32(ProtocolConstants.DI_RESULT_CODE, ProtocolConstants.DIAMETER_RESULT_UNABLE_TO_DELIVER))
        self.node.addOurHostAndRealm(answer)
        Utils.copyProxyInfo(request,answer)
        Utils.setMandatory_RFC3588(answer)
        answer(answer,connkey)
    
    def handleAnswer(self,answer,answer_connkey,state):
        """Handle an answer.
        This method is called when an answer arrives. It is meant to
        be overridden in a subclass.
        
        Please note that the handleAnswer() method is called by the
        networking thread and messages from other peers cannot be received
        until the method returns. If the handleAnswer() method needs to do
        any lengthy processing then it should implement a message queue,
        put the message into the queue, and return. The answers can then be
        processed by a worker thread pool without stalling the networking
        layer.
          answer          The answer message. Null if the connection broke.
          answer_connkey  The connection from where the answer came.
          state           The state object passed to sendRequest_*() or
                          forwardRequest()
        """
        #default implementation: silently discard
        self.logger.log(logging.DEBUG,"Handling incoming answer, command_code=%d, end2end=%d, hopbyhop=%d"%(answer.hdr.command_code,answer.hdr.end_to_end_identifier,answer.hdr.hop_by_hop_identifier))
    
    def answer(self,answer,connkey):
        """Answer a request.
        The answer is sent to the connection. If the connection has been
        lost in the meantime it is ignored.
          answer   The answer message.
          connkey  The connection to send the answer to.
        Raises:
          NotARequestError If the answer has the R bit set in the header.
        """
        if answer.hdr.isRequest():
            raise NotARequestError()
        try:
            self.node.sendMessage(answer,connkey)
        except StaleConnectionError as ex:
            pass
    
    def forwardRequest(self,request,connkey,state):
        """
        Forward a request.
        Forward the request to the specified connection. The request will
        automatically get a route-record added if not already present.
        This method is meant to be called from handleRequest().
          request  The request to forward
          connkey  The connection to use
          state    A state object that will be passed to handleAnswer()
                   when the answer arrives. You should remember the ingoing
                   connection and hop-by-hop identifier
        Raises:
          NotARequestError
            If the request does not have the R bit set in the header.
          NotProxiableError
            If the request does not have the P bit set in the header.
          StaleConnectionError
            If the ConnectionKey refers to a lost connection.
        """
        if not request.hdr.isProxiable():
            raise NotProxiableError()
        our_route_record_found = False
        our_host_id = self.settings.host_id
        for a in request.subset(ProtocolConstants.DI_ROUTE_RECORD):
            if AVP_UTF8String.narrow(a).queryValue()==our_host_id:
                our_route_record_found = True
                break
        if not our_route_record_found:
            #add a route-record
            request.add(AVP_UTF8String(ProtocolConstants.DI_ROUTE_RECORD,settings.host_id))
        #send it
        self.sendRequest_1(request,connkey,state)
    
    def forwardAnswer(self,answer,connkey):
        """
        Forward an answer.
        Forward the answer to to the specified connection. The answer will
        automatically get a route-record added. This method is meant to be
        called from handleAnswer().
          answer   The answer to forward
          connkey  The connection to use
        Raises:
          NotAnAnswerError
            If the answer has the R bit set in the header.
          NotProxiableError
            If the answer does not have the P bit set in the header. This
            indicates that there is something completely wrong with either
            the message, the peer or your application.
          StaleConnectionError
            If the ConnectionKey refers to a lost connection.
        """
        if not answer.hdr.isProxiable():
            raise NotProxiableError()
        if answer.hdr.isRequest():
            raise NotAnAnswerError()
        #add a route-record
        answer.add(AVP_UTF8String(ProtocolConstants.DI_ROUTE_RECORD,settings.host_id))
        #send it
        self.answer(answer,connkey)
    
    def sendRequest_1(self, request, connkey, state):
        """
        Initiate a request.
        A request initiated by this node is sent to the specified connection.
          request  The request.
          connkey  The connection to use.
          state    A state object that will be passed to handleAnswer() when
                   the answer arrives.
        Raises:
          NotARequestError
            If the request does not have the R bit set in the header.
          StaleConnectionError
            If the ConnectionKey refers to a lost connection.
        """
        if not request.hdr.isRequest():
            raise NotARequestError()
        request.hdr.hop_by_hop_identifier = self.node.nextHopByHopIdentifier(connkey)
        #remember state
        self.req_map_lock.acquire()
        try:
            reqs = self.req_map[connkey]
            reqs[request.hdr.hop_by_hop_identifier] = state
        except KeyError:
            self.req_map_lock.release()
            raise StaleConnectionError()
        self.req_map_lock.release()
        
        try:
            self.node.sendMessage(request,connkey)
            self.logger.log(logging.DEBUG,"Request sent, command_code=%d hop_by_hop_identifier==%d"%(request.hdr.command_code,request.hdr.hop_by_hop_identifier));
        except StaleConnectionError:
            self.req_map_lock.acquire()
            del self.req_map[request.hdr.hop_by_hop_identifier]
            self.req_map_lock.release()
            raise
    
    def sendRequest_any(self,request,peers,state):
        """
        Sends a request.
        The request is sent to one of the peers and an optional state
        object is remembered. Please note that handleAnswer() for this
        request may get called before this method returns. This can happen
        if the peer is very fast and the OS thread scheduler decides to
        schedule the networking thread.
          request  The request to send.
          peers    The candidate peers
          state    A state object to be remembered. This will be passed to
                   the handleAnswer() method when the answer arrives.
        Raises:
          NotARequestError
            If the request does not have the R bit set in the header.
          NotRoutableError
            If the message could not be sent to any of the peers.
        """
        self.logger.log(logging.DEBUG,"Sending request (command_code=%d) to %d peers"%(request.hdr.command_code,len(peers)))
        request.hdr.end_to_end_identifier = self.node.nextEndToEndIdentifier()
        any_peers = False
        any_capable_peers = False
        for p in peers:
            any_peers = True
            self.logger.log(logging.DEBUG,"Considering sending request to %s"%p.host)
            connkey = self.node.findConnection(p)
            if not connkey: continue
            p2 = self.node.connectionKey2Peer(connkey)
            if not p2: continue;
            if not self.node.isAllowedApplication(request,p2):
                self.logger.log(logging.DEBUG,"peer %s cannot handle request"%p.host)
                continue
            any_capable_peers=True
            try:
                self.sendRequest_1(request,connkey,state)
                return
            except StaleConnectionError as ex:
                pass #ok
            self.logger.log(logging.DEBUG,"Setting retransmit bit")
            request.hdr.setRetransmit(True)
        if any_capable_peers:
            raise NotRoutableError("All capable peer connections went stale")
        elif any_peers:
            raise NotRoutableError("No capable peers")
        else:
            raise NotRoutableError()
    
    #messagedispatcher upcall
    def handle_message(self,msg, connkey, peer):
        """
        Handle an incoming message.
        This implementation calls handleRequest(), or matches an answer to
        an outstanding request and calls handleAnswer().
        Subclasses should not override this method.
        """
        
        if msg.hdr.isRequest():
            self.logger.log(logging.DEBUG,"Handling request")
            self.handleRequest(msg,connkey,peer)
        else:
            self.logger.log(logging.DEBUG,"Handling answer, hop_by_hop_identifier=%d"%msg.hdr.hop_by_hop_identifier)
            #locate state
            state=None
            self.req_map_lock.acquire()
            try:
                reqs = self.req_map[connkey]
                state = reqs[msg.hdr.hop_by_hop_identifier]
                del reqs[msg.hdr.hop_by_hop_identifier]
            except KeyError:
                pass
            self.req_map_lock.release()
            if state:
                self.handleAnswer(msg,connkey,state)
            else:
                self.logger.log(logging.DEBUG,"Answer did not match any outstanding request")
        return True
    
    #connectionlistener upcall
    def handle_connection(self,connkey, peer, updown):
        """
        Handle a a connection state change.
        If the connection has been lost this implementation calls
        handleAnswer(null,...) for outstanding requests on the connection.
        Subclasses should not override this method.
        """
        
        self.req_map_lock.acquire()
        try:
            if updown:
                #register the new connection
                self.req_map[connkey]={}
            else:
                #find outstanding requests, and call handleAnswer with NULL
                if connkey not in self.req_map:
                    return
                reqs = self.req_map[connkey]
                #forget the connection
                del self.req_map[connkey]
                #remove the entries
                for state in list(reqs.values()):
                    self.handleAnswer(None,connkey,state)
        finally:
            self.req_map_lock.release()

