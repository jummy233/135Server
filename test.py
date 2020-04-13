import dataGetter.apis.xiaomiGetter as X
import dataGetter.dataMidware as M
from dataGetter.authConfig import xauth
from dataGetter.dataGen.xiaomiData import mkResouceParam
from datetime import datetime as dt


# t = X._get_token(xauth)
# pos = X._get_pos(xauth, t)
# device = X._get_device(xauth, t)
# authcode = X._get_auth_code(xauth)
# print(authcode)

x = M.XiaoMiData()
__import__('pdb').set_trace()
p = mkResouceParam(x.device_list[0], dt(2019, 11, 1), dt(2019, 11, 2))
res = X._get_resource(xauth, x.token, p)

print("end")
