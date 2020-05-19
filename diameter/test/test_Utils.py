import unittest

from diameter import Utils, MessageHeader, AVP, AVP_OctetString, Message, ProtocolConstants


class UtilsTestCase(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_Utils(self):        
        #Test setMandatory
        avps = []
        avps.append(AVP(1,"user@example.net"))
        avps.append(AVP(2,"user@example.net"))
        avps.append(AVP(999,"user@example.net"))
        avps.append(AVP(1,"vendor@example.net",-1))
        Utils.setMandatory(avps,[1,2])
        assert avps[0].isMandatory()
        assert avps[1].isMandatory()
        assert not avps[2].isMandatory()
        assert not avps[3].isMandatory()
        
        msg = Message()
        msg.append(AVP(1,"user@example.net"))
        msg.append(AVP(2,"user@example.net"))
        msg.append(AVP(999,"user@example.net"))
        msg.append(AVP(1,"vendor@example.net",-1))
        Utils.setMandatory(msg,[1,2])
        assert msg[0].isMandatory()
        assert msg[1].isMandatory()
        assert not msg[2].isMandatory()
        assert not msg[3].isMandatory()
        
        avps = []
        avps.append(AVP(ProtocolConstants.DI_ORIGIN_HOST,"user@example.net"))
        avps.append(AVP(999,"user@example.net"))
        Utils.setMandatory_RFC3588(avps)
        assert avps[0].isMandatory()
        assert not avps[1].isMandatory()
        
        #test copyProxyInfo
        src_msg = Message()
        src_msg.append(AVP(1,"user@example.net"))
        src_msg.append(AVP_OctetString(ProtocolConstants.DI_PROXY_INFO,"fnox"))
        src_msg.append(AVP(999,"vendor@example.net",-1))
        src_msg.append(AVP_OctetString(ProtocolConstants.DI_PROXY_INFO,"mox"))
        dst_msg = Message()
        Utils.copyProxyInfo(src_msg,dst_msg)
        assert len(dst_msg)==2
        assert src_msg[1].code==dst_msg[0].code
        assert src_msg[1].payload==dst_msg[0].payload
        assert src_msg[3].code==dst_msg[1].code
        assert src_msg[3].payload==dst_msg[1].payload
        
        #Test the ABNF checker
        #create a conforming DPR
        msg = Message()
        msg.append(AVP(ProtocolConstants.DI_ORIGIN_HOST,"A value"))
        msg.append(AVP(ProtocolConstants.DI_ORIGIN_REALM,"A value"))
        msg.append(AVP(ProtocolConstants.DI_DISCONNECT_CAUSE,"abcd"))
        rc = Utils.checkABNF(msg,Utils.abnf_dpr)
        assert not rc
        #create a DPR with a missing AVP
        msg = Message()
        msg.append(AVP(ProtocolConstants.DI_ORIGIN_HOST,"A value"))
        msg.append(AVP(ProtocolConstants.DI_ORIGIN_REALM,"A value"))
        #msg.append(AVP(ProtocolConstants.DI_DISCONNECT_CAUSE,"abcd"))
        rc = Utils.checkABNF(msg,Utils.abnf_dpr)
        assert rc
        assert rc[1]==ProtocolConstants.DIAMETER_RESULT_MISSING_AVP
        #create a DPR with a duplicated AVP
        msg = Message()
        msg.append(AVP(ProtocolConstants.DI_ORIGIN_HOST,"A value"))
        msg.append(AVP(ProtocolConstants.DI_ORIGIN_REALM,"A value"))
        msg.append(AVP(ProtocolConstants.DI_ORIGIN_REALM,"A value"))
        msg.append(AVP(ProtocolConstants.DI_DISCONNECT_CAUSE,"abcd"))
        rc = Utils.checkABNF(msg,Utils.abnf_dpr)
        assert rc
        assert rc[1]==ProtocolConstants.DIAMETER_RESULT_AVP_OCCURS_TOO_MANY_TIMES
        assert rc[0]
        #create a DPR with a an extra AVP
        msg = Message()
        msg.append(AVP(ProtocolConstants.DI_ORIGIN_HOST,"A value"))
        msg.append(AVP(ProtocolConstants.DI_ORIGIN_REALM,"A value"))
        msg.append(AVP(ProtocolConstants.DI_DISCONNECT_CAUSE,"abcd"))
        msg.append(AVP(999,"A value"))
        rc = Utils.checkABNF(msg,Utils.abnf_dpr)
        assert rc
        assert rc[1]==ProtocolConstants.DIAMETER_RESULT_AVP_NOT_ALLOWED
        assert rc[0]
        #create a conforming ASR 
        msg = Message()
        msg.append(AVP(ProtocolConstants.DI_SESSION_ID,"A value"))
        msg.append(AVP(ProtocolConstants.DI_ORIGIN_HOST,"A value"))
        msg.append(AVP(ProtocolConstants.DI_ORIGIN_REALM,"A value"))
        msg.append(AVP(ProtocolConstants.DI_DESTINATION_REALM,"A value"))
        msg.append(AVP(ProtocolConstants.DI_DESTINATION_HOST,"A value"))
        msg.append(AVP(ProtocolConstants.DI_AUTH_APPLICATION_ID,"A value"))
        rc = Utils.checkABNF(msg,Utils.abnf_asr)
        assert not rc
        #create a ASR with session-id the wrong palce
        msg = Message()
        msg.append(AVP(ProtocolConstants.DI_ORIGIN_HOST,"A value"))
        msg.append(AVP(ProtocolConstants.DI_SESSION_ID,"A value"))
        msg.append(AVP(ProtocolConstants.DI_ORIGIN_REALM,"A value"))
        msg.append(AVP(ProtocolConstants.DI_DESTINATION_REALM,"A value"))
        msg.append(AVP(ProtocolConstants.DI_DESTINATION_HOST,"A value"))
        msg.append(AVP(ProtocolConstants.DI_AUTH_APPLICATION_ID,"A value"))
        rc = Utils.checkABNF(msg,Utils.abnf_asr)
        assert rc
        assert rc[0]
