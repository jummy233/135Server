import unittest
from app import db, create_app
from app import db_init
from app import modelOperations as mops
from app import models as m
from datetime import datetime


class TestModelOperation(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        self.client = self.app.test_client()
        db_init.create_db()

        db_init.load_climate_area()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def _location(self):
        location = {
            "province": "Province",
            "city": "City",
            "climate_area_name": "A1"
        }

        mops.add_location(location)

    def _project(self):
        project = {
            "location": {"province": "Province", "city": "City"},
            "floor": "4",
            "tech_support_company": {"company_name": "TechSupportCompany"},
            "construction_company": {"company_name": "ConstrutionCompany"},
            "description": "",
            "project_name": "Project",
            "latitude": "31.908271",
            "building_height": 23,  # not necessary for all records to be string.
            "demo_area": "2311.94",
            "longitude": "121.172900",
            "building_type": "House",
            "started_time": "2017-12-18T00:00:00",
            "finished_time": "2018-02-18T00:00:00",
            "project_company": {"company_name": "ProjectCompany"},
            "outdoor_spot": "",
            "district": "Discrict",
            "record_started_from": "2019-04-20T00:00:00",
            "area": "2311.94"
        }
        mops.add_project(project)

    def _spot(self):
        spot = {
            "project": m.Project.query.first().project_id,  # project id or project object.
            "spot_name": "Spot",
            "spot_type": "Bedroom",
            "image": b"asjdlasd"
        }
        mops.add_spot(spot)

    def _device(self):
        device = {
            "device_name": "Device",
            "device_type": "Temperature",
            "spot": m.Spot.query.first().spot_id,
            "create_time": "2019-04-20T00:00:00",
            "modify_time": "2019-04-24T00:00:00"
        }
        mops.add_device(device)

    def _spot_record(self):
        spot_record = {
            "spot_record_time": "2019-09-24T12:30:00",
            "device": m.Device.query.first().device_id,
            "window_opened": "true",
            "temperature": "34",
            "humidity": "89",
            "ac_power": "2000",
            "pm25": "34",
            "co2": "22"
        }
        mops.add_spot_record(spot_record)

    def test_add_location(self):
        self._location()
        query_res = m.Location.query.filter_by(city="City").first()
        self.assertTrue(query_res.province ==
                        "Province" and query_res.city == "City")

    def test_add_project(self):
        # need location to be existed.
        self._location()
        self._project()

        query_res = m.Project.query.filter_by(project_name="Project").first()
        self.assertTrue(query_res.floor == 4 and
                        query_res.area == 2311.94 and
                        query_res.finished_time == datetime(2018, 2, 18))

    def test_add_spot(self):
        self._location()
        self._project()
        self._spot()

        query_res = m.Spot.query.filter_by(spot_name="Spot").first()
        self.assertTrue(query_res.spot_type == "Bedroom" and
                        query_res.project == m.Project.query.first())

    def test_add_device(self):
        self._location()
        self._project()
        self._spot()
        self._device()

        query_res = m.Device.query.filter_by(device_name="Device").first()
        self.assertTrue(query_res.device_type == "Temperature" and
                        query_res.create_time == datetime(2019, 4, 20))

    def test_add_spot_record(self):
        self._location()
        self._project()
        self._spot()
        self._device()
        self._spot_record()

        # query_res = m.SpotRecord.query.filter_by(
        #     spot_record_time=datetime(2019, 4, 24, 12, 30)).first()
        query_res = m.SpotRecord.query.first()
        print(query_res.spot_record_time)
        print(query_res.spot_record_time == datetime(2019, 9, 24, 12, 30))

        self.assertTrue(query_res.window_opened and query_res.humidity == 89)
