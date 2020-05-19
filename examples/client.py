import binascii
from diameter import ProtocolConstants, Message, AVP, AVP_Unsigned32, AVP_UTF8String
from diameter.node import SimpleSyncClient, Capability, NodeSettings, Peer

peer = "localhost"
port = 3868
host_id = "127.0.0.1"
realm = "our.diameter"


cap = Capability()
cap.addAuthApp(ProtocolConstants.DIAMETER_APPLICATION_COMMON)
cap.addAcctApp(ProtocolConstants.DIAMETER_APPLICATION_COMMON)

cap.addAuthApp(ProtocolConstants.DIAMETER_APPLICATION_CREDIT_CONTROL)
cap.addAcctApp(ProtocolConstants.DIAMETER_APPLICATION_CREDIT_CONTROL)
settings = NodeSettings(host_id, realm, 9999, cap, 0, "cc_test_client", 1)

ssc = SimpleSyncClient(settings,[Peer(peer,port)])
ssc.start()
ssc.waitForConnection(timeout=3)

req = Message()
# < Diameter Header: 272, REQ, PXY >
req.hdr.command_code = ProtocolConstants.DIAMETER_COMMAND_CC
req.hdr.application_id = ProtocolConstants.DIAMETER_APPLICATION_CREDIT_CONTROL
req.hdr.setRequest(True)
req.hdr.setProxiable(True)

# < Session-Id >
req.append(AVP(ProtocolConstants.DI_SESSION_ID,ssc.node.makeNewSessionId()))

# { Origin-Host }
# { Origin-Realm }
ssc.node.addOurHostAndRealm(req)

# { Destination-Realm }
req.append(AVP_UTF8String(ProtocolConstants.DI_DESTINATION_REALM,"example.net"))
# { Auth-Application-Id }
req.append(AVP_Unsigned32(ProtocolConstants.DI_AUTH_APPLICATION_ID,ProtocolConstants.DIAMETER_APPLICATION_CREDIT_CONTROL)) # a lie but a minor one
# { Service-Context-Id }
req.append(AVP_UTF8String(ProtocolConstants.DI_SERVICE_CONTEXT_ID,"cc_test@example.net"))
# { CC-Request-Type }
req.append(AVP_Unsigned32(ProtocolConstants.DI_CC_REQUEST_TYPE,ProtocolConstants.DI_CC_REQUEST_TYPE_EVENT_REQUEST))
# { CC-Request-Number }
req.append(AVP_Unsigned32(ProtocolConstants.DI_CC_REQUEST_NUMBER,0))
# [ Destination-Host ]
# [ User-Name ]
req.append(AVP_UTF8String(ProtocolConstants.DI_USER_NAME,"user@example.net"))

#£setMandatory_RFC3588(req)
#setMandatory_RFC4006(req)

res = ssc.sendRequest(req)
    
print("Response data:", str(res))

for avp in res.avp:
    print("avp:", str(avp))

raw_code = res.find(ProtocolConstants.DI_RESULT_CODE).payload
code = int(binascii.b2a_hex(raw_code).decode('utf-8'), 16)
if code == ProtocolConstants.DIAMETER_RESULT_SUCCESS:
    print("SUCCESS")

session_id = res.find(ProtocolConstants.DI_SESSION_ID).payload.decode('utf-8')
origin_host = res.find(ProtocolConstants.DI_ORIGIN_HOST).payload.decode('utf-8')
origin_realm = res.find(ProtocolConstants.DI_ORIGIN_REALM).payload.decode('utf-8')

print("Result Code %s session_id %s origin host %s origin_realm %s" % (code, session_id, origin_host, origin_realm))
