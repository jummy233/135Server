import unittest
from datetime import datetime
from app import create_app, db
from app import models as m
from app import modelOperations as mops
import db_init


class TestModelToJson(unittest.TestCase):

    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        self.client = self.app.test_client()
        db_init.create_db(name='testing.sqlite')
        m.User.gen_admin()
        db_init.load_climate_area()  # unfull init.

        location = {
            "province": "Province",
            "city": "City",
            "climate_area_name": "A1"
        }
        mops.add_location(location)

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
            "record_started_from": datetime(2019, 4, 20),
            "area": "2311.94"
        }
        mops.add_project(project)

        spot = {
            "project": m.Project.query.first().project_id,
            "spot_name": "Spot",
            "spot_type": "Bedroom",
            "image": b"asjdlasd"
        }
        mops.add_spot(spot)

        device = {
            "device_name": "Device",
            "device_type": "Temperature",
            "spot": m.Spot.query.first().spot_id,
            "online": 1,
            "create_time": "2019-04-20T00:00:00",
            "modify_time": datetime(2019, 4, 24)
        }
        mops.add_device(device)

        spot_record = {
            "spot_record_time": datetime(2019, 9, 24, 12, 30),
            # "spot_record_time": "2019-09-24T12:30:00",
            "device": m.Device.query.first().device_id,
            "window_opened": "true",
            "temperature": "34",
            "humidity": "89",
            "ac_power": "2000",
            "pm25": "34",
            "co2": "22"
        }
        mops.add_spot_record(spot_record)

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_project_to_json(self):
        print('<Project>')
        __import__('pprint').pprint(m.Project.query.first().to_json())
        print()

    def test_spot_to_json(self):
        print('<Spot>')
        __import__('pprint').pprint(m.Spot.query.first().to_json())
        print()

    def test_device_to_json(self):
        print('<Device>')
        __import__('pprint').pprint(m.Device.query.first().to_json())
        print()

    def test_user_to_json(self):
        print('<User>')
        __import__('pprint').pprint(m.User.query.first().to_json())
        print()

    def test_location_to_json(self):
        print('<Location>')
        __import__('pprint').pprint(m.Location.query.first().to_json())
        print()

    def test_spot_record_to_json(self):
        print('<SpotRecord>')
        __import__('pprint').pprint(m.SpotRecord.query.first().to_json())
        print()



