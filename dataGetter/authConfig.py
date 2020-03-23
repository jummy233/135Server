"""
All Authentication information defined here.
each 'auth' corresponds to one data soruce API.
all well typed.
"""

import os.path
import os
from typing import TYPE_CHECKING
import json
if TYPE_CHECKING:  # avoid circular importing.
    # Note cannot use type constructor since it is runtime method
    import dataGetter.apis.jianyanyuanGetter as j
    import dataGetter.apis.xiaomiGetter as x


with open(os.path.join(os.path.realpath(os.path.dirname(__file__)),
                       'static/auth.json'), 'r') as authdata:
    authdict = json.loads(authdata.read())

    ###############
    #  auth data  #
    ###############

    jauth: 'j.AuthData' = authdict['jianyanyuanAuth']
    xauth: 'x.AuthData' = authdict['xiaomiAuth']

    #################
    #  Test params  #
    #################

    jdevice = authdict['jianyanyuanTestDeviceParams']
    jdatapoint = authdict['jianyanyuanTestDataPointParams']

