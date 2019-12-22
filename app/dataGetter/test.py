from typing import Optional
import unittest
import jianyanyuanGetter as j
import xiaomiGetter as x
import authConfig
import dataMidware
import time
from sys import argv
jauth = authConfig.jauth
xauth = authConfig.xauth


class JianyanyuanGetterTest(unittest.TestCase):
    def setUp(self):
        self.token = j._get_token(jauth)

    def test_get_token(self):
        token = j._get_token(jauth)
        # print(token)
        self.assertTrue(isinstance(token, tuple) and len(token) == 2)

    def test_get_device_list(self):
        params: j.DeviceParam = (
            {'companyId': 'HKZ',
             'start': 1,
             'size': 10,
             'pageNo': 1,
             'pageSize': '10'})
        data = j._get_device_list(jauth, self.token, params)
        # print(data['devs'][0]['deviceId'])
        # print(data)
        self.assertTrue(isinstance(data, list))

    def test_get_device_attrs(self):
        data = j._get_device_attrs(jauth, self.token, 'ofskcl')
        self.assertTrue(data[0]['deviceValueId'] == 33)

    def test_get_datapoint(self):
        params: j.DataPointParam = (

            {'gid': 'ofskcl',
             'did': '20227493777269940224',
             'aid': "33,104,121",
             'startTime': '2019-12-16T00:00:00',
             'endTime': '2019-12-17T00:00:00'})
        data = j._get_data_points(jauth, self.token, params)
        # print(data)
        self.assertTrue(data is not None)


class XiaomiGetterTest(unittest.TestCase):
    def setUp(self):
        self.token = x._get_token(xauth)

    def test_get_auth_code(self):
        authcode: Optional[str] = x._get_auth_code(xauth)
        self.assertTrue(authcode is not None)

    def test_get_token(self):
        token: Optional[x.TokenResult] = x._get_token(xauth)
        self.assertTrue(token is not None and 'access_token' in token)

    def test_get_token_refresh(self):
        oldtoken = dict(**self.token)
        self.token = x._get_token(xauth, refresh=self.token)

        self.assertTrue(oldtoken['access_token'] != self.token['access_token'])

    def test_gen_sign(self):
        sign: Optional[str] = x._gen_sign(xauth, self.token)
        self.assertTrue(sign is not None)

    def test_get_pos(self):
        pos: Optional[x.PosResult] = x._get_pos(xauth, self.token)
        self.assertTrue(pos is not None)

    def test_get_device(self):
        dev: Optional[x.DeviceResult] = x._get_device(xauth, self.token)
        self.assertTrue(dev is not None)

    def test_get_resource(self):
        params: x.ResourceParam = {
            'data': [{'did': 'lumi.158d0002374da1', 'attrs': ['3', 'humidity_value']}]}
        res: Optional[x.ResourceResult] = x._get_resource(xauth, self.token, params)
        self.assertTrue(res is not None)


class SpotDataTest(unittest.TestCase):
    def setUp(self):
        pass

    def test_JianyanyuanConstructor(self):
        j = dataMidware.JianYanYuanData()
        token1 = j.token
        time.sleep(21)
        token2 = j.token
        self.assertTrue(token1 != token2)
