"""
Script to init database.
"""

import sqlalchemy.exc import IntegrityError
from typing import List, Dict
from app import db
from app.models import ClimateArea, Location
from app.modelOperations import add_location
import dataGetter as D
import dataGetter.dataMidware as DM
import json

#########################
#  Record Climate Area  #
#########################


def load_climate_area(self):
    data: Dict = json.loads('app/dataGetter/static/climate_area.json')
    climate_areas: List = data['climate_area']

    if not ClimateArea.query.all():
        return None
    for cl in climate_areas:
        try:
            newcl = ClimateArea(area_name=str(cl))
            db.session.add(cl)
        except IntegrityError:
            db.commit.rollback()


#####################
#  Record Location  #
#####################
def load_location(self):
    data: Dict = json.loads('app/dataGetter/static/locations.json')
    if not Location.query.all():
        return None

    for k, vlist in data:
        city, clid = vlist
        d = {'province': k, 'city': city, 'climate_area_name': clid}
        add_location(d)


####################
#  Record Project  #
####################


#################
#  Record Spot  #
#################

#########################
#  Record Spot Records  #
#########################


####################
#  Record Devices  #
####################




if __name__ == "__main__":
    pass
