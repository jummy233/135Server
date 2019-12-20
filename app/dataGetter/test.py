import unittest
import jianyanyuanGetter


class JianyanyuanGetterTest(unittest.TestCase):
    def test_get_token(self):
        token = jianyanyuanGetter._get_token(jianyanyuanGetter.auth)
        # print(token)
        self.assertTrue(isinstance(token, tuple) and len(token) == 2)

    def test_get_device_list(self):
        params: jianyanyuanGetter.DeviceParam = (
            {'companyId': 'HKZ',
             'start': 1,
             'size': 10,
             'pageNo': 1,
             'pageSize': '10'})
        data = jianyanyuanGetter._get_device_list(jianyanyuanGetter.auth, params)
        # print(data['devs'][0]['deviceId'])
        # print(data)
        self.assertTrue(isinstance(data, list))

    def test_get_device_attrs(self):
        data = jianyanyuanGetter._get_device_attrs(jianyanyuanGetter.auth, 'ofskcl')
        self.assertTrue(data[0]['deviceValueId'] == 33)

    def test_get_datapoint(self):
        params: jianyanyuanGetter.DataPointParam = (

            {'gid': 'ofskcl',
             'did': '20227493777269940224',
             'aid': "33,104,121",
             'startTime': '2019-12-16T00:00:00',
             'endTime': '2019-12-17T00:00:00'})
        data = jianyanyuanGetter._get_data_points(jianyanyuanGetter.auth, params)
        print(data)
        self.assertTrue(True)


