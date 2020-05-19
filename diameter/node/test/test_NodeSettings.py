import unittest

from diameter import ProtocolConstants
from diameter.node import NodeSettings, Capability
from diameter.node.Error import InvalidSettingError


class NodeSettingsTestCase(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_NodeSettings(self):
        cap = Capability()
        cap.addAuthApp(117)
        try:
            ns = NodeSettings("example.net","example.net",-1,cap,3868,"PythonDiameter",1)
            assert False
        except InvalidSettingError:
            pass
        try:
            ns = NodeSettings("somehost.example.net","net",-1,cap,3868,"PythonDiameter",1)
            assert False
        except InvalidSettingError:
            pass
        try:
            ns = NodeSettings("somehost.example.net","example.net",0,cap,3868,"PythonDiameter",1)
            assert False
        except InvalidSettingError:
            pass
        try:
            empty_cap = Capability()
            ns = NodeSettings("somehost.example.net","example.net",0,empty_cap,3868,"PythonDiameter",1)
            assert False
        except InvalidSettingError:
            pass
        try:
            ns = NodeSettings("somehost.example.net","example.net",-1,cap,-4,"PythonDiameter",1)
            assert False
        except InvalidSettingError:
            pass
        try:
            ns = NodeSettings("somehost.example.net","example.net",-1,cap,65536,"PythonDiameter",1)
            assert False
        except InvalidSettingError:
            pass
        try:
            ns = NodeSettings("somehost.example.net","example.net",-1,cap,3868,None,1)
            assert False
        except InvalidSettingError:
            pass
            
        try:
            ns = NodeSettings("somehost.example.net","example.net",-1,cap,3868,"PythonDiameter",1)
        except InvalidSettingError:
            assert False
