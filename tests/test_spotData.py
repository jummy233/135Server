import unittest
import app.dataGetter.dataGen as DG
from app import create_app, db
import time
from tests.fake_db import gen_fake


class SpotDataTest(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.j = DG.JianYanYuanData(self.app)
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        gen_fake()

        self.location_attrs = (
            'cityIdLogin',
            'provinceIdLogin',
            'nickname',
            'address',
            'provinceLoginName',
            'cityLoginName',
            'location')

        def tearDown(self):
            self.j.close()

    def test_JianyanyuanConstructor(self):
        token1 = self.j.token
        time.sleep(21)
        token2 = self.j.token
        self.assertTrue(token1 != token2)

    def test_spot_location(self):
        g = self.j.spot_location()
        self.assertTrue(any(g))  # not all None

    def test_filter_attrs(self):
        d = self.j._filter_location_attrs(
            self.j.device_list[5], self.location_attrs)
        self.assertTrue(
            d is not None and len(d.keys()) <= len(self.location_attrs))

    def test_make_datapoint_param(self):
        r = self.j.device_list[8]
        param = self.j._make_datapoint_param(r)
        self.assertTrue(param is not None and 'gid' in param.keys())
