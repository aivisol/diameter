"""A mishmash of handy methods"""
from diameter import ProtocolConstants
from diameter.AVP import AVP

def setMandatory(avps,codes):
    """Sets the M-bit on the avps with the specified codes.
    Vendor-specific AVPs are not modified.
    AVPs not listed are not modified.
      avps   The AVPs to examine and possibly set the M-bit on.
      codes  Array of codes
    """
    for a in avps:
        if a.vendor_id==0 and (a.code in codes):
            a.setMandatory(True)

rfc3588_mandatory_codes = frozenset([
    ProtocolConstants.DI_ACCOUNTING_RECORD_NUMBER,
    ProtocolConstants.DI_ACCOUNTING_RECORD_TYPE,
    ProtocolConstants.DI_ACCOUNTING_SESSION_ID,
    ProtocolConstants.DI_ACCOUNTING_SUB_SESSION_ID,
    ProtocolConstants.DI_ACCT_APPLICATION_ID,
    ProtocolConstants.DI_ACCT_INTERIM_INTERVAL,
    ProtocolConstants.DI_ACCT_MULTI_SESSION_ID,
    ProtocolConstants.DI_AUTHORIZATION_LIFETIME,
    ProtocolConstants.DI_AUTH_APPLICATION_ID,
    ProtocolConstants.DI_AUTH_GRACE_PERIOD,
    ProtocolConstants.DI_AUTH_REQUEST_TYPE,
    ProtocolConstants.DI_AUTH_SESSION_STATE,
    ProtocolConstants.DI_CLASS,
    ProtocolConstants.DI_DESTINATION_HOST,
    ProtocolConstants.DI_DESTINATION_REALM,
    ProtocolConstants.DI_DISCONNECT_CAUSE,
    ProtocolConstants.DI_E2E_SEQUENCE_AVP,
    ProtocolConstants.DI_EVENT_TIMESTAMP,
    ProtocolConstants.DI_EXPERIMENTAL_RESULT,
    ProtocolConstants.DI_EXPERIMENTAL_RESULT_CODE,
    ProtocolConstants.DI_FAILED_AVP,
    ProtocolConstants.DI_HOST_IP_ADDRESS,
    ProtocolConstants.DI_INBAND_SECURITY_ID,
    ProtocolConstants.DI_MULTI_ROUND_TIME_OUT,
    ProtocolConstants.DI_ORIGIN_HOST,
    ProtocolConstants.DI_ORIGIN_REALM,
    ProtocolConstants.DI_ORIGIN_STATE_ID,
    ProtocolConstants.DI_PROXY_HOST,
    ProtocolConstants.DI_PROXY_INFO,
    ProtocolConstants.DI_PROXY_STATE,
    ProtocolConstants.DI_REDIRECT_HOST,
    ProtocolConstants.DI_REDIRECT_HOST_USAGE,
    ProtocolConstants.DI_REDIRECT_MAX_CACHE_TIME,
    ProtocolConstants.DI_RESULT_CODE,
    ProtocolConstants.DI_RE_AUTH_REQUEST_TYPE,
    ProtocolConstants.DI_ROUTE_RECORD,
    ProtocolConstants.DI_SESSION_BINDING,
    ProtocolConstants.DI_SESSION_ID,
    ProtocolConstants.DI_SESSION_SERVER_FAILOVER,
    ProtocolConstants.DI_SESSION_TIMEOUT,
    ProtocolConstants.DI_SUPPORTED_VENDOR_ID,
    ProtocolConstants.DI_TERMINATION_CAUSE,
    ProtocolConstants.DI_USER_NAME,
    ProtocolConstants.DI_VENDOR_ID,
    ProtocolConstants.DI_VENDOR_SPECIFIC_APPLICATION_ID
])


def setMandatory_RFC3588(avps):
    """Sets the M-bit on the AVPs that should have the M bit set according to RFC3588"""
    setMandatory(avps,rfc3588_mandatory_codes)

def copyProxyInfo(source,destination):
    """Copies any Proxy-Info AVPs from one message to another.
         from  The source message.
         to   The destination message.
    """
    for a in source.subset(ProtocolConstants.DI_PROXY_INFO):
        destination.append(AVP(a.code,a.payload,a.vendor_id))


rfc4006_mandatory_codes = frozenset([
    ProtocolConstants.DI_CC_INPUT_OCTETS,
    ProtocolConstants.DI_CC_MONEY,
    ProtocolConstants.DI_CC_OUTPUT_OCTETS,
    ProtocolConstants.DI_CC_REQUEST_NUMBER,
    ProtocolConstants.DI_CC_REQUEST_TYPE,
    ProtocolConstants.DI_CC_SERVICE_SPECIFIC_UNITS,
    ProtocolConstants.DI_CC_SESSION_FAILOVER,
    ProtocolConstants.DI_CC_SUB_SESSION_ID,
    ProtocolConstants.DI_CC_TIME,
    ProtocolConstants.DI_CC_TOTAL_OCTETS,
    ProtocolConstants.DI_CC_UNIT_TYPE,
    ProtocolConstants.DI_CHECK_BALANCE_RESULT,
    ProtocolConstants.DI_COST_INFORMATION,
    ProtocolConstants.DI_COST_UNIT,
    ProtocolConstants.DI_CREDIT_CONTROL,
    ProtocolConstants.DI_CREDIT_CONTROL_FAILURE_HANDLING,
    ProtocolConstants.DI_CURRENCY_CODE,
    ProtocolConstants.DI_DIRECT_DEBITING_FAILURE_HANDLING,
    ProtocolConstants.DI_EXPONENT,
    ProtocolConstants.DI_FINAL_UNIT_ACTION,
    ProtocolConstants.DI_FINAL_UNIT_INDICATION,
    ProtocolConstants.DI_GRANTED_SERVICE_UNIT,
    ProtocolConstants.DI_G_S_U_POOL_IDENTIFIER,
    ProtocolConstants.DI_G_S_U_POOL_REFERENCE,
    ProtocolConstants.DI_MULTIPLE_SERVICES_CREDIT_CONTROL,
    ProtocolConstants.DI_MULTIPLE_SERVICES_INDICATOR,
    ProtocolConstants.DI_RATING_GROUP,
    ProtocolConstants.DI_REDIRECT_ADDRESS_TYPE,
    ProtocolConstants.DI_REDIRECT_SERVER,
    ProtocolConstants.DI_REDIRECT_SERVER_ADDRESS,
    ProtocolConstants.DI_REQUESTED_ACTION,
    ProtocolConstants.DI_REQUESTED_SERVICE_UNIT,
    ProtocolConstants.DI_RESTRICTION_FILTER_RULE,
    ProtocolConstants.DI_SERVICE_CONTEXT_ID,
    ProtocolConstants.DI_SERVICE_IDENTIFIER,
    ProtocolConstants.DI_SUBSCRIPTION_ID,
    ProtocolConstants.DI_SUBSCRIPTION_ID_DATA,
    ProtocolConstants.DI_SUBSCRIPTION_ID_TYPE,
    ProtocolConstants.DI_TARIFF_CHANGE_USAGE,
    ProtocolConstants.DI_TARIFF_TIME_CHANGE,
    ProtocolConstants.DI_UNIT_VALUE,
    ProtocolConstants.DI_USED_SERVICE_UNIT,
    ProtocolConstants.DI_VALUE_DIGITS,
    ProtocolConstants.DI_VALIDITY_TIME,
])


def setMandatory_RFC4006(avps):
    """Sets the M-bit on the AVPs that must have the M bit set according to RFCC4006"""
    setMandatory(avps,rfc4006_mandatory_codes)



#ABNF for CER (section 5.3.1)
abnf_cer = [
    (False,  1,    1, ProtocolConstants.DI_ORIGIN_HOST),
    (False,  1,    1, ProtocolConstants.DI_ORIGIN_REALM),
    (False,  1, None, ProtocolConstants.DI_HOST_IP_ADDRESS),
    (False,  1,    1, ProtocolConstants.DI_VENDOR_ID),
    (False,  1,    1, ProtocolConstants.DI_PRODUCT_NAME),
    (False,  0,    1, ProtocolConstants.DI_ORIGIN_STATE_ID),
    (False,  0, None, ProtocolConstants.DI_SUPPORTED_VENDOR_ID),
    (False,  0, None, ProtocolConstants.DI_AUTH_APPLICATION_ID),
    (False,  0, None, ProtocolConstants.DI_INBAND_SECURITY_ID),
    (False,  0, None, ProtocolConstants.DI_ACCT_APPLICATION_ID),
    (False,  0, None, ProtocolConstants.DI_VENDOR_SPECIFIC_APPLICATION_ID),
    (False,  0,    1, ProtocolConstants.DI_FIRMWARE_REVISION),
    (False,  0, None, None),
]
#ABNF for CEA (section 5.3.2)
abnf_cea = [
    (False,  1,    1, ProtocolConstants.DI_RESULT_CODE),
    (False,  1,    1, ProtocolConstants.DI_ORIGIN_HOST),
    (False,  1,    1, ProtocolConstants.DI_ORIGIN_REALM),
    (False,  1, None, ProtocolConstants.DI_HOST_IP_ADDRESS),
    (False,  1,    1, ProtocolConstants.DI_VENDOR_ID),
    (False,  1,    1, ProtocolConstants.DI_PRODUCT_NAME),
    (False,  0,    1, ProtocolConstants.DI_ORIGIN_STATE_ID),
    (False,  0,    1, ProtocolConstants.DI_ERROR_MESSAGE),
    (False,  0,    1, ProtocolConstants.DI_FAILED_AVP),
    (False,  0, None, ProtocolConstants.DI_SUPPORTED_VENDOR_ID),
    (False,  0, None, ProtocolConstants.DI_AUTH_APPLICATION_ID),
    (False,  0, None, ProtocolConstants.DI_INBAND_SECURITY_ID),
    (False,  0, None, ProtocolConstants.DI_ACCT_APPLICATION_ID),
    (False,  0, None, ProtocolConstants.DI_VENDOR_SPECIFIC_APPLICATION_ID),
    (False,  0,    1, ProtocolConstants.DI_FIRMWARE_REVISION),
    (False,  0, None, None),
]
#ABNF for DPR (section 5.4.1)
abnf_dpr = [
    (False,  1,    1, ProtocolConstants.DI_ORIGIN_HOST),
    (False,  1,    1, ProtocolConstants.DI_ORIGIN_REALM),
    (False,  1,    1, ProtocolConstants.DI_DISCONNECT_CAUSE),
]
#ABNF for DPA (section 5.4.2)
abnf_dpa = [
    (False,  1,    1, ProtocolConstants.DI_RESULT_CODE),
    (False,  1,    1, ProtocolConstants.DI_ORIGIN_HOST),
    (False,  1,    1, ProtocolConstants.DI_ORIGIN_REALM),
    (False,  0,    1, ProtocolConstants.DI_ERROR_MESSAGE),
    (False,  0,    1, ProtocolConstants.DI_FAILED_AVP),
]
#ABNF for DWR (section 5.5.1)
abnf_dwr = [
    (False,  1,    1, ProtocolConstants.DI_ORIGIN_HOST),
    (False,  1,    1, ProtocolConstants.DI_ORIGIN_REALM),
    (False,  0,    1, ProtocolConstants.DI_ORIGIN_STATE_ID),
]
#ABNF for DWA (section 5.5.2)
abnf_dwa = [
    (False,  1,    1, ProtocolConstants.DI_RESULT_CODE),
    (False,  1,    1, ProtocolConstants.DI_ORIGIN_HOST),
    (False,  1,    1, ProtocolConstants.DI_ORIGIN_REALM),
    (False,  0,    1, ProtocolConstants.DI_ERROR_MESSAGE),
    (False,  0,    1, ProtocolConstants.DI_FAILED_AVP),
    (False,  0,    1, ProtocolConstants.DI_ORIGIN_STATE_ID),
]
#todo: 7.2
#ABNF for RAR (section 8.3.1)
abnf_rar = [
    (True,   1,    1, ProtocolConstants.DI_SESSION_ID),
    (False,  1,    1, ProtocolConstants.DI_ORIGIN_HOST),
    (False,  1,    1, ProtocolConstants.DI_ORIGIN_REALM),
    (False,  1,    1, ProtocolConstants.DI_DESTINATION_REALM),
    (False,  1,    1, ProtocolConstants.DI_DESTINATION_HOST),
    (False,  0,    1, ProtocolConstants.DI_AUTH_APPLICATION_ID),
    (False,  0,    1, ProtocolConstants.DI_RE_AUTH_REQUEST_TYPE),
    (False,  0, None, None),
]
#ABNF for RAA (section 8.3.2)
abnf_raa = [
    (True,   1,    1, ProtocolConstants.DI_SESSION_ID),
    (False,  1,    1, ProtocolConstants.DI_RESULT_CODE),
    (False,  1,    1, ProtocolConstants.DI_ORIGIN_HOST),
    (False,  1,    1, ProtocolConstants.DI_ORIGIN_REALM),
    ##more optional attributes, but no point in listing them because there can also be arbitrary AVPs
    (False,  0, None, None),
]
#ABNF for STR (section 8.4.1)
abnf_str = [
    (True,   1,    1, ProtocolConstants.DI_SESSION_ID),
    (False,  1,    1, ProtocolConstants.DI_ORIGIN_HOST),
    (False,  1,    1, ProtocolConstants.DI_ORIGIN_REALM),
    (False,  1,    1, ProtocolConstants.DI_DESTINATION_REALM),
    (False,  1,    1, ProtocolConstants.DI_AUTH_APPLICATION_ID),
    (False,  1,    1, ProtocolConstants.DI_TERMINATION_CAUSE),
    (False,  0,    1, ProtocolConstants.DI_USER_NAME),
    (False,  0,    1, ProtocolConstants.DI_DESTINATION_HOST),
    (False,  0, None, ProtocolConstants.DI_CLASS),
    (False,  0,    1, ProtocolConstants.DI_ORIGIN_STATE_ID),
    (False,  0, None, ProtocolConstants.DI_PROXY_INFO),
    (False,  0, None, ProtocolConstants.DI_ROUTE_RECORD),
    (False,  0, None, None),
]
#ABNF for STA (section 8.4.1)
abnf_sta = [
    (True,   1,    1, ProtocolConstants.DI_SESSION_ID),
    (False,  1,    1, ProtocolConstants.DI_RESULT_CODE),
    (False,  1,    1, ProtocolConstants.DI_ORIGIN_HOST),
    (False,  1,    1, ProtocolConstants.DI_ORIGIN_REALM),
    (False,  0,    1, ProtocolConstants.DI_USER_NAME),
    (False,  0, None, ProtocolConstants.DI_CLASS),
    (False,  0,    1, ProtocolConstants.DI_ERROR_MESSAGE),
    (False,  0,    1, ProtocolConstants.DI_ERROR_REPORTING_HOST),
    (False,  0, None, ProtocolConstants.DI_FAILED_AVP),
    (False,  0,    1, ProtocolConstants.DI_ORIGIN_STATE_ID),
    (False,  0, None, ProtocolConstants.DI_REDIRECT_HOST),
    (False,  0,    1, ProtocolConstants.DI_REDIRECT_HOST_USAGE),
    (False,  0,    1, ProtocolConstants.DI_REDIRECT_MAX_CACHE_TIME),
    (False,  0, None, ProtocolConstants.DI_PROXY_INFO),
    (False,  0, None, None),
]
#ABNF for ASR (section 8.5.1)
abnf_asr = [
    (True,   1,    1, ProtocolConstants.DI_SESSION_ID),
    (False,  1,    1, ProtocolConstants.DI_ORIGIN_HOST),
    (False,  1,    1, ProtocolConstants.DI_ORIGIN_REALM),
    (False,  1,    1, ProtocolConstants.DI_DESTINATION_REALM),
    (False,  1,    1, ProtocolConstants.DI_DESTINATION_HOST),
    (False,  1,    1, ProtocolConstants.DI_AUTH_APPLICATION_ID),
    (False,  0,    1, ProtocolConstants.DI_USER_NAME),
    (False,  0,    1, ProtocolConstants.DI_ORIGIN_STATE_ID),
    (False,  0, None, ProtocolConstants.DI_PROXY_INFO),
    (False,  0, None, ProtocolConstants.DI_ROUTE_RECORD),
    (False,  0, None, None),
]
#ABNF for ASA (section 8.5.2)
abnf_asa = [
    (True,   1,    1, ProtocolConstants.DI_SESSION_ID),
    (False,  1,    1, ProtocolConstants.DI_RESULT_CODE),
    (False,  1,    1, ProtocolConstants.DI_ORIGIN_HOST),
    (False,  1,    1, ProtocolConstants.DI_ORIGIN_REALM),
    (False,  0,    1, ProtocolConstants.DI_USER_NAME),
    (False,  0,    1, ProtocolConstants.DI_ORIGIN_STATE_ID),
    (False,  0,    1, ProtocolConstants.DI_ERROR_MESSAGE),
    (False,  0,    1, ProtocolConstants.DI_ERROR_REPORTING_HOST),
    (False,  0, None, ProtocolConstants.DI_FAILED_AVP),
    (False,  0, None, ProtocolConstants.DI_REDIRECT_HOST),
    (False,  0,    1, ProtocolConstants.DI_REDIRECT_HOST_USAGE),
    (False,  0,    1, ProtocolConstants.DI_REDIRECT_MAX_CACHE_TIME),
    (False,  0, None, ProtocolConstants.DI_PROXY_INFO),
    (False,  0, None, None),
]


def checkABNF(msg, abnf):
    """
    Check that a message conforms to an ABNF.
    The message is checked if it conforms to the ABNF specification.
    You can use it like this:
    
    abnf_my_message = [
        (True,   1,  1, ProtocolConstants.DI_SESSION_ID),
        (False,  1,  1, ProtocolConstants.DI_ORIGIN_HOST),
        (False,  1,  1, ProtocolConstants.DI_ORIGIN_REALM),
        (False,  1,  1, ProtocolConstants.DI_USER_NAME),
        ...
        (False,  0, None, None),  #special marker for arbitrary AVPs
    ]
    caf = Utils.checkABNF(msg,abnf_my_message)
    if caf:
        #The message did not conform to the ABNF
        response = Message()
        response.prepareResponse(msg)
        ...
        if caf[0]:
            msg.add(caf[0])
        msg.add(AVP_Unsigned32(ProtocolConstants.DI_RESULT_CODE,caf[1]))
        if caf.[2]:
            msg.add(AVP_UTF8String(ProtocolConstants.DI_ERROR_MESSAGE,caf[2]))
        ...
    
    Parameters:
      msg  The message to be checked.
      abnf  An list of ABNFComponents. You can use on of the predefined ones or your own. It is supposed to be a list of tuples (fixed_position,min_count,max_count,code)
    Returns:
      None on success. A tuple (failed_avp,result_code,error_message) on failure. The failed_avp can be None. The error_message item can be None.
    """
    
    arbitrary_avps_allowed=False
    for a in abnf:
        if not a[3]:
            arbitrary_avps_allowed = True
            break
    
    i=-1
    for fixed_position,min_count,max_count,code in abnf:
        i+=1
        if not code: continue #no checks on arbitrary AVPs
        if min_count==0 and not max_count:
            continue #no real limits.
        count = msg.count(code)
        if count<min_count:
            ##not present or too few occurrences
            if min_count==1:
                error_message=None
            else:
                error_message="AVP must occur at least %d times"%min_count
            return (None,
                    ProtocolConstants.DIAMETER_RESULT_MISSING_AVP,
                    error_message
                   )
        elif max_count and count>max_count:
            #locate the first violation
            violating_avp=None
            j=0
            for avp in msg.subset(code):
                j+=1
                if j>max_count:
                    violating_avp = avp
                    break
            return (violating_avp,
                    ProtocolConstants.DIAMETER_RESULT_AVP_OCCURS_TOO_MANY_TIMES,
                    None
                   )
        
        if fixed_position:
            #check position
            #assumption: previous AVPs are also fixed-position (otherwise this doesn't make much sense)
            #assumption: arbitrary AVPs are not allowed before this
            #todo: support previous AVP non-1 occurences
            
            #find postion
            pos=0
            while msg[pos].code!=code:
                pos += 1
            if pos!=i:
                #No really good result-code for this...
                return (msg[pos],
                        ProtocolConstants.DIAMETER_RESULT_INVALID_AVP_VALUE,
                        "AVP occurs at wrong position"
                       )
    
    if not arbitrary_avps_allowed:
        #check that there aren't any
        for avp in msg:
            allowed=False
            for a in abnf:
                if avp.code==a[3]:
                    allowed=True
                    break
            if not allowed:
                return (avp,
                        ProtocolConstants.DIAMETER_RESULT_AVP_NOT_ALLOWED,
                        "hov" #None
                       )
    
    return None #message passed checks
