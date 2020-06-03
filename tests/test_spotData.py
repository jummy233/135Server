import unittest
import app.dataGetter.dataGen as DG
from app import create_app, db, scheduler
import time
from datetime import datetime
from tests.fake_db import gen_fake
import threading


class SpotDataTest(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing', with_scheduler=False)
        with self.app.app_context():
            db.drop_all()
            self.j = DG.JianYanYuanData(self.app)
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

    @unittest.skip('.')
    def test_JianyanyuanConstructor(self):
        token1 = self.j.token
        time.sleep(21)
        token2 = self.j.token
        self.assertTrue(token1 != token2)

    @unittest.skip('.')
    def test_device(self):
        devices = list(self.j.device())
        self.assertTrue(len(devices) > 100)
        dname: str = devices[-1].get("device_name")
        self.assertTrue(dname.isdigit())

    def test_sport_record(self):
        time_range = (datetime(2020, 3, 2, 10), datetime(2020, 3, 3, 15))
        records = self.j.spot_record(2, time_range)

    def tearDown(self):
        self.j.close()
