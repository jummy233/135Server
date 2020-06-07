from typing import Optional, List, Dict
import unittest
from app.dataGetter.apis import xiaomiGetter as x
from app.dataGetter import authConfig
import time
xauth = authConfig.xauth


class XiaomiGetterTest(unittest.TestCase):
    def setUp(self):
        self.token = x.get_token(xauth)

    @unittest.skip('.')
    def test_get_auth_code(self):
        authcode: Optional[str] = x._get_auth_code(xauth)
        print("authcode ---->", authcode)
        self.assertTrue(authcode is not None)

    @unittest.skip('.')
    def test_get_token(self):
        token: Optional[x.TokenResult] = x.get_token(xauth)
        self.assertTrue(token is not None and 'access_token' in token)

    @unittest.skip('.')
    def test_get_token_refresh(self):
        oldtoken = dict(**self.token)
        self.token = x.get_token(xauth, refresh=self.token)

        self.assertTrue(oldtoken['access_token'] != self.token['access_token'])

    @unittest.skip('.')
    def test_gen_sign(self):
        sign: Optional[str] = x._gen_sign(xauth, self.token)
        # print("----> ", sign)
        self.assertTrue(sign is not None)

    @unittest.skip('.')
    def test_get_pos(self):
        params: x.PosParam = {'positionId': 'real2.557305651542360064'}
        pos: Optional[x.PosResult] = x.get_pos(xauth, self.token, params)
        print("----> ", pos)
        self.assertTrue(pos is not None)

    @unittest.skip('.')
    def test_get_device(self):
        dev: Optional[x.DeviceResult] = x.get_device(xauth, self.token)
        print("----> ", dev)
        self.assertTrue(dev.get('data') is not None)

    def test_get_hist_resource(self):
        params: x.ResourceParam = {
            "did": "lumi.158d0001fd5c50",
            'attrs': ['humidity_value', 'temperature_value'],
            "startTime": 1591340400000,
            "endTime": 1591491708869,
            "pageNum": 1,
            "pageSize": 100
        }
        # {
        #     'did':       'lumi.158d00020267ec',
        #     'attrs':     ['humidity_value', 'temperature_value'],
        #     'startTime': 1591319880000,
        #     'endTime':   1591339880000,
        #     'pageNum':   1,
        #     'pageSize':  100  # maxium 300
        # }

        res: Optional[x.ResourceResult] = x.get_hist_resource(
            xauth, self.token, params)
        print("----> ", res)
        self.assertTrue(res is not None and res != '')

    @unittest.skip('.')
    def test_get_resource(self):
        print(self.token)
        params: Dict[List[x.ResourceParam_light]] = {
            'data': [{
                'did': 'lumi.158d0001fd5c50',  # zzh" old"
                # 'did': 'lumi.158d00020267ec',  # new
                'attrs': ['humidity_value', 'temperature_value']
            }]
        }
        res: Optional[x.ResourceResult] = x.get_resource(
            xauth, self.token, params)
        print("----> ", res)
        self.assertTrue(res is not None and res != '')
