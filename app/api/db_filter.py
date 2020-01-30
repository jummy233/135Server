from typing import Optional, NewType
from flask import jsonify, request
from flask import json as FlaskJson
from sqlalchemy.exc import IntegrityError
from . import api
from ..api_types import ApiResponse, ReturnCode, ApiRequest
from ..modelOperations import ModelOperations
from ..modelOperations import commit_db_operation
from ..modelOperations import commit
from ..models import User, Location, Project, ProjectDetail
from ..models import ClimateArea, Company, Permission
from ..models import OutdoorSpot, OutdoorRecord
from ..models import Spot, SpotRecord, Device
from ..models import Data


Json = NewType('Json', str)


@api.route('/project/filter/', methods=["POST"])
def filter_project_paged(keyword: str) -> Json:
    pass


@api.route('/device/filter/', methods=["POST"])
def filter_device_paged(keyword: str) -> Json:
    pass


@api.route('/spot/filter/', methods=["POST"])
def filter_spot_paged(keyword: str) -> Json:
    pass


@api.route('/spotRecord/filter/', methods=["POST"])
def filter_spotRecord_paged(keyword: str) -> Json:
    pass


@api.route('/project/filter/', methods=["POST"])
def filter_project_paged(keyword: str) -> Json:
    pass


