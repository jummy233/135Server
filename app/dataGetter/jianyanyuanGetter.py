import requests
from hashlib import md5, sha1
from typing import NewType, Dict, Optional, Tuple, TypedDict, List
import urllib.parse
from operator import itemgetter
import json
from utils import _currentTimestamp

################
#  auth types  #
################

Token = NewType('Token', str)
Uid = NewType('Uid', str)
AuthToken = NewType('AuthToken', Tuple[Token, Uid])  # Necessary value for authenticion.

AuthData = (
    TypedDict('AuthData',
              {'account': str,
               'password': str,
               'base_url': str,
               'auth_url': str,
               'device_url': str,
               'attr_url': str,
               'datapoint_url': str}))

#######################
#  param type  #
#######################
DeviceParam = (
    TypedDict('DeviceParam',
              {'companyId': str,
               'start': int,
               'size': int,
               'pageNo': int,
               'pageSize': int}))

DataPointParam = (
    TypedDict('DataPointParam',
              {'gid': str,
               'did': str,
               'aid': str,  # list of attrs. string in form "<int>, <int>" where <int> are attr id
               'startTime': str,
               'endTime': str}))  # time format: yyyy-MM-ddTHH:mm:ss


auth: AuthData = AuthData(account='esic_syp',
                          password='a123456',
                          base_url='http://hkzk.esic010.com/',
                          auth_url='v1/businessUser/auth',
                          device_url='/v1/device/devices',
                          attr_url='/v1/history/deviceAttrs/',
                          datapoint_url='/v1/data/datapoints')


#  @pysnooper.snoop()
def _get_token(auth: AuthData) -> Optional[AuthToken]:
    """
    get token
    """
    (account,
     password,
     base_url,
     auth_url) = itemgetter('account', 'password', 'base_url', 'auth_url')(auth)

    # construct request
    url: str = urllib.parse.urljoin(base_url, auth_url)
    timestamp: int = _currentTimestamp(digit=13)

    md5pw: str = md5(password.encode('ascii')).hexdigest()
    sign: str = md5((md5pw + str(timestamp)).encode('ascii')).hexdigest()

    request_data: Dict = {
        'account': account,
        'sign': sign,
        'ts': timestamp,
        'ukey': ''}

    response: requests.Response = requests.post(url, json=request_data)
    if response.status_code == 200:
        rj = response.json()
        return AuthToken((rj['token'], rj['uid']))
    return None


def _get_device_list(auth: AuthData, params: Dict) -> Optional[List]:
    """
    (token + params) return device list as dict by given param
    only return the Array with data.
    """

    method: str = 'POST'
    timestamp: int = _currentTimestamp(13)
    params_json: str = json.dumps(params)
    authtoken = _get_token(auth)
    if authtoken:
        token, uid = authtoken

    # construct request
    base_url, device_url = itemgetter('base_url', 'device_url')(auth)
    url = urllib.parse.urljoin(base_url, device_url)

    sign: str = sha1(
        (method + device_url + params_json + str(timestamp) + token).encode('ascii')).hexdigest()

    headers: Dict = {
        'Content-Type': 'application/json;charset=UTF-8',
        'ts': str(timestamp),
        'uid': uid,
        'sign': sign}

    response = requests.post(url, data=params_json, headers=headers)
    rj: Dict = response.json()

    if response.status_code != 200:
        return None

    if rj['code'] != 0:
        return None
    return rj['data']['devs']


def _get_device_attrs(auth: AuthData, gid: str) -> Optional[List]:
    """
    (token + attrId) return paramter attri table
    only return the Array with data.
    """

    method: str = 'GET'
    timestamp: int = _currentTimestamp(13)

    authtoken = _get_token(auth)
    if authtoken:
        token, uid = authtoken

    # construct request.
    base_url, attr_url = itemgetter('base_url', 'attr_url')(auth)
    attr_url_gid: str = urllib.parse.urljoin(attr_url, gid)
    url: str = urllib.parse.urljoin(base_url, attr_url_gid)

    sign: str = sha1(
        (method + attr_url_gid + str(timestamp) + token).encode('ascii')).hexdigest()

    headers: Dict = {'Content-Type': 'application/json;charset=UTF-8',
                     'ts': str(timestamp),
                     'uid': uid,
                     'sign': sign}

    response: requests.Response = requests.get(url, headers=headers)
    if response.status_code != 200:
        return None

    rj: Dict = response.json()
    if rj['code'] != 0:
        return None
    return rj['data']['jsonArray']


def _get_data_points(auth: AuthData, params: DataPointParam) -> Optional[List]:
    """ return data """
    method: str = 'POST'
    timestamp: int = _currentTimestamp(13)
    param_json = json.dumps(params)

    authtoken = _get_token(auth)
    if authtoken:
        token, uid = authtoken

    # construct request.
    base_url, datapoint_url = itemgetter('base_url', 'datapoint_url')(auth)
    url: str = urllib.parse.urljoin(base_url, datapoint_url)

    sign: str = sha1(
        (method + datapoint_url + param_json + str(timestamp) + token).encode('ascii')).hexdigest()

    headers: Dict = {'Content-Type': 'application/json;charset=UTF-8',
                     'ts': str(timestamp),
                     'uid': uid,
                     'sign': sign}

    response: requests.Response = requests.post(url, data=param_json, headers=headers)
    if response.status_code != 200:
        return None
    rj = response.json()
    if rj['code'] != 0:
        return None
    return rj['data']['asData']




