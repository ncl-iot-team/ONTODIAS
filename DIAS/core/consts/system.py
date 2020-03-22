
'''
        LOGGER CONF START
'''
from loguru import logger

# 设置输出日志的格式
logger.add("logs/running.log", format="{time} {level} {message}", filter="my_module", level="INFO",rotation="500 MB", encoding="utf-8")

'''
        LOGGER CONF END
'''