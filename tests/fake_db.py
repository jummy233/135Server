"""
NOTE: deprecated test
All framework test are based on jianyanyuan data.
"""

from datetime import datetime


def gen_fake():
    """ avoid circular import """
    from app import modelOperations as mops
    from app.modelOperations import commit
    from app import models as m
    import db_init

    db_init.load_climate_area()
    location = {
        "province": "Province",
        "city": "City",
        "climate_area_name": "A1"
    }
    mops.ModelOperations.Add.add_location(location)

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
    mops.ModelOperations.Add.add_project(project)

    spot = {
        "project": m.Project.query.first().project_id,
        "spot_name": "Spot",
        "spot_type": "Bedroom",
        "image": b"asjdlasd"
    }
    mops.ModelOperations.Add.add_spot(spot)

    device = {
        "device_name": "Device",
        "device_type": "Temperature",
        "spot": m.Spot.query.first().spot_id,
        "online": 1,
        "create_time": "2019-04-20T00:00:00",
        "modify_time": datetime(2019, 4, 24)
    }
    mops.ModelOperations.Add.add_device(device)

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
    mops.ModelOperations.Add.add_spot_record(spot_record)
    commit()
