import unittest
from app import db, create_app, models, utils
from app.api import db_views
import json
from datetime import datetime, timedelta


def cheap_gen_fake():
    models.ClimateArea.gen_fake()
    models.OutdoorSpot.gen_fake(5)
    models.Location.gen_fake(5)
    models.Company.gen_fake(5)
    models.Project.gen_fake(5)
    models.Spot.gen_fake(5)


class DBViewTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        self.client = self.app.test_client()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_db_view_api_ping(self):
        # check the avaliablity of apis.
        models.gen_fake_db()
        responses = [self.client.get('/view/project/generic'),
                     self.client.get('/view/project/detailed'),
                     self.client.get('/view/spots'),
                     self.client.get('/view/spot/1')]
        self.assertTrue(all(filter(lambda r: r.status_code == 200, responses)))

    def test_spot_detailed_view_outdoor_data_integrity(self):
        dday = timedelta(days=1)
        dhour = timedelta(hours=1)
        days_in_test_month = [datetime(2019, 5, 1, 0) + i * dday + h * dhour
                              for h in range(0, 24)
                              for i in range(0, 31)]

        cheap_gen_fake()
        # generate test outdoor data
        for day in days_in_test_month:
            odr = models.OutdoorRecord(outdoor_record_time=day)
            db.session.add(odr)
            db.session.commit()

        models.rand_date = utils.rand_date_in(datetime(2019, 5, 1),
                                              datetime(2019, 6, 1))
        models.SpotRecord.gen_fake(500)

        response = self.client.get('/view/spot/1')
        response_data = json.loads(response.get_data(as_text=True))

        # if outdoor data exists in the corresponding records.
        has_outdoor = any(filter(lambda data: data['outdoor_record'] != {}, response_data))
        self.assertTrue(has_outdoor)

        # if outdoor data hour is correct.
        def is_in_same_hour(d1, d2) -> bool:
            _, day1, mon1, year1, time1, _ = d1.split()
            _, day2, mon2, year2, time2, _ = d2.split()
            hour1 = time1.split(":")[0]
            hour2 = time2.split(":")[0]
            d1_str = day1 + mon1 + year1 + hour1
            d2_str = day2 + mon2 + year2 + hour2
            return d1_str == d2_str

        same_hour = False
        for data in response_data:
            od_time: str = data["outdoor_record"]["outdoor_record_time"]
            rec_time: str = data["spot_record_time"]
            if is_in_same_hour(od_time, rec_time):
                same_hour = True
        self.assertTrue(same_hour)
