"""
All Authentication information defined here.
each 'auth' corresponds to one data soruce API.
all well typed.
"""

from typing import TYPE_CHECKING
if TYPE_CHECKING:  # avoid circular importing.
    # Note cannot use type constructor since it is runtime method
    import jianyanyuanGetter as j
    import xiaomiGetter as x


#################
#  Jianyanyuan  #
#################

jauth: 'j.AuthData' = dict(account='esic_syp',
                           password='a123456',
                           base_url='http://hkzk.esic010.com/',
                           auth_url='v1/businessUser/auth',
                           device_url='/v1/device/devices',
                           attr_url='/v1/history/deviceAttrs/',
                           datapoint_url='/v1/data/datapoints')


############
#  Xiaomi  #
############

xauth: 'x.AuthData' = dict(account='15123025720',
                           password='lrf123456',
                           appId='576c02d4c43145908749565a',
                           appKey='eztUiDfvxhDNBchhDvfs5LYDrBxC25Qo',
                           state='OwO',
                           redirect_uri='ssw',
                           auth_base_url='https://aiot-oauth2.aqara.cn/',
                           authorize_url='/authorize',
                           token_url='/access_token',
                           grant_type='authorization_code',
                           refresh_token='',

                           api_query_base_url='https://aiot-open-3rd.aqara.cn/3rd/v1.0/',
                           api_query_pos_url='/open/position/query',
                           api_query_dev_url='/open/device/query',
                           api_query_resrouce_url='/open/resource/query')
