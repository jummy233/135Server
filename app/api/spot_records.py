from flask import jsonify
from . import api
from ..models import SpotRecord
from datetime import datetime
from datetime import timedelta
import calendar


@api.route('/spot/<spot_id>', methods=['GET'])
def get_spot_records(spot_id):
    spot_records = [r.to_json()
                    for r in
                    SpotRecord.query.filter_by(spot_id=spot_id)]
    return jsonify(spot_records)


@api.route('/spot/<spot_id>/from/<int:year1>/<int:month1>/to/<int:year2>/<int:month2>', methods=['GET'])
def get_spot_records_in_date_range(spot_id, year1, month1, year2, month2):
    date1 = datetime(year1, month1, 1)
    _, day_range_of_month2 = calendar.monthrange(year2, month2)
    date2 = datetime(year2, month2, day_range_of_month2)
    records = (SpotRecord.query.
               filter(SpotRecord.spot_id == spot_id).
               filter(SpotRecord.spot_record_time > date1).
               filter(SpotRecord.spot_record_time < date2).
               order_by(SpotRecord.spot_record_time))
    return jsonify([r.to_json() for r in records])


@api.route('/spot/<spot_id>/date/<int:year>/<int:month>/<int:day>')
def get_spot_records_in_one_day(spot_id, year, month, day):
    date = datetime(year, month, day)
    records = (SpotRecord.query.
               filter(SpotRecord.spot_id == spot_id).
               filter(SpotRecord.spot_record_time >= date).
               filter(SpotRecord.spot_record_time < date + timedelta(days=1)).
               order_by(SpotRecord.spot_record_time))
    return jsonify([r.to_json() for r in records])
