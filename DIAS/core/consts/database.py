
'''
        REDIS DATABASE START
'''
import redis
from core.consts.configure import SYSTEM_CONFIG_FILE

#创建连接池
REDIS_POOL = redis.ConnectionPool(host=SYSTEM_CONFIG_FILE["redis"]["host"],port=SYSTEM_CONFIG_FILE["redis"]["port"],decode_responses=True)

#创建链接对象
REDIS_CLIENT = redis.Redis(connection_pool=REDIS_POOL)

'''
        REDIS DATABASE END
'''


'''
        STARDOG DATABASE START
'''

from core.consts.configure import DATASOURCE_YML_CONFIG_FILE

# 配置Stardog连接变量
STARDOG_CONN_DETAILS = {
    'endpoint': 'http://'+DATASOURCE_YML_CONFIG_FILE["database"]["stardog"]["host"]+':'+str(DATASOURCE_YML_CONFIG_FILE["database"]["stardog"]["port"]),
    'username': DATASOURCE_YML_CONFIG_FILE["database"]["stardog"]["username"],
    'password': DATASOURCE_YML_CONFIG_FILE["database"]["stardog"]["password"]
}


'''
        STARDOG DATABASE END
'''