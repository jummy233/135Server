from unittest import TestCase
from unittest import skip
from app import db, scheduler
import app.dataGetter.dataloader.Scheduler as S
from app.dataGetter.dataGen import JianYanYuanData
from app.dataGetter.dataGen.dataType import DataSource
from datetime import datetime as dt
from datetime import timedelta
import tempfile
import os
import app
from time import sleep
from threading import enumerate


class TestFetchActor(TestCase):
    """
    To fetch device it must exist in the db first.
    """

    def setUp(self):
        self.app = app.create_app('testing')
        with self.app.app_context():
            # db.drop_all()
            db.create_all()

    @skip('.')
    def test_update_device(self):
        """ should show total 332 devices """
        scheduler.update_device()
        with self.app.app_context():
            from app.models import Device
            self.assertTrue(Device.query.filter(
                Device.device_name.like("%lumi%")).count() > 0)
            self.assertTrue(Device.query.filter(
                Device.device_name.like("%2009%")).count() > 0)
            self.assertTrue(Device.query.count() > 300)

    @skip('.')
    def test_update_record(self):
        """
        send update message directly.
        """
        with self.app.app_context():
            from app.models import Device
            did: int = (
                Device
                .query
                .filter(Device.device_name == "20205754003878404097")
            ).first().device_id

        jmsg = S.UpdateMsg(DataSource.JIANYANYUAN,
                           (did, (dt(2019, 9, 23, 00), dt(2019, 9, 24, 00))))
        scheduler.update_actor.send(jmsg)
        # avoid immediate teardown.
        sleep(20)

    def test_update_all(self):
        scheduler.force_overall_update()
        __import__('pdb').set_trace()

    def tearDown(self):
        # with self.app.app_context():
        #     db.session.remove()
        #     db.drop_all()
        print("test: closing")
        scheduler.close()
