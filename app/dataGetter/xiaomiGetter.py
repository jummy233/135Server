import requests
from hashlib import md5, sha1
from typing import NewType, Dict, Optional, Tuple, TypedDict, List, Callable
from operator import itemgetter
import urllib.parse
from datetime import datetime as dt
import json

Token = NewType('Token', str)

AuthData = (
    TypedDict('AuthData',
              {'account': str,
               'password': str,
               'appId': str,  # called client_id in json request.
               'appKey': str,  # called client_secret in json request.

               'state': str,  # arbitrary string.
               'redirect_uri': str,  # callback uri, see document.

               'auth_base_url': str,
               'authorize_url': str,
               'token_url': str,

               'refresh_token': str,

               'api_query_base_url': str,
               'api_query_pos_url': str,
               'api_query_dev_url': str,
               'api_query_resrouce_url': str}, total=False))


def _auth_refresh_token(auth: AuthData, token: str) -> AuthData:
    """ return auth data for refreshing token """
    newauth: AuthData = auth.copy()
    newauth['refresh_token'] = token
    return newauth



PosParam = (  # Method: Get
    TypedDict('PosParam',
              {'positionId': str,
               'pageNum': int,
               'pageSize': int}))

DeviceParam = (
    TypedDict('DeviceParam',
              {'did': str,
               'positionId': str,
               'pageNum': int,
               'pageSize': int}))

###########################################
# Nested type declaration
OneResourceParam = (
    TypedDict('OneResourceParam',
              {'did': str,
               'attrs': List[str]}))


class ResourceParam(TypedDict):
    data: List[OneResourceParam]
###########################################


auth: AuthData = AuthData(account='15123025720',
                          password='lrf123456',
                          appId='576c02d4c43145908749565a',
                          appKey='',
                          state='OwO',
                          redirect_uri='ssw',
                          auth_base_url='https://aiot-oauth2.aqara.cn/',
                          authorize_url='/authorize',
                          token_url='/access_token',
                          api_query_base_url='https://aiot-open-3rd.aqara.cn/3rd/v1.0/',
                          api_query_pos_url='/open/position/query',
                          api_query_dev_url='/open/device/query',
                          api_query_resrouce_url='/open/resource/query')


def _get_auth_code(auth: AuthData) -> Optional[str]:
    """ return auth code """
    (client_id,
     auth_base_url,
     authorize_url,
     redirect_uri,
     state,
     account,
     password) = itemgetter('appId', 'auth_base_url', 'authorize_url', 'redirect_uri', 'state',
                            'account', 'password')(auth)

    # First get to the login page
    url: str = urllib.parse.urljoin(auth_base_url, authorize_url)
    getparam: Dict = {'client_id': client_id,
                      'response_type': 'code',
                      'redirect_uri': redirect_uri,
                      'state': state}
    login_url: str = url + '?' + urllib.parse.urlencode(getparam)

    # Second step is to login with account and password to get auth code.
    postparam: Dict = dict({'account': account, 'password': password})

    response: requests.Response = requests.post(login_url, data=postparam)
    response_url: str = response.url

    # get auth code from parameters in returned url.
    if 'code' not in response_url:
        return None

    returned_params: str = urllib.parse.urlsplit(response_url).query
    query: Dict = {k: v[0] for k, v in urllib.parse.parse_qs(returned_params).items()}
    return query['code']


def _get_token(auth: AuthData):
    """ return token with given auth code """
    (client_id,
     client_secret,
     redirect_uri,
     auth_base_url,
     token_url,
     state,
     )


def _get_device():
    pass


def _get_pos():
    pass


def _get_resource():
    pass




