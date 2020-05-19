import unittest

from diameter import AVP_Time, AVP


class AVP_TimeTestCase(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_time(self):
        when = 1139658264
        a = AVP_Time(1,when)
        assert a.querySecondsSince1970()==when
        
        a.setSecondsSince1970(when+1)
        assert a.querySecondsSince1970()==when+1
        
        a = AVP_Time.narrow(AVP(1,b"\307\230\114\230"))
        assert a.querySecondsSince1970()==1139658264