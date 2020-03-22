import threading

from loguru import logger

from core.data_collector.data_collector import dataCollector
from core.social_media.twitter.TwitterLandslipMessager import TwitterLandslipMessager


def reply_thread(tweet):

    t = TwitterLandslipMessager()

    t.landslip_search_challenge(tweet)


if __name__ == '__main__':

    # 启动一个监控回复的进程

    dc = dataCollector()
    consumer = dc.kafka_consumer()

    for tweet in consumer:
        logger.info(
            "---------------------------------------- Consume a message from Kafka -------------------------------------------")
        t = threading.Thread(target=reply_thread, args=(tweet.value,))
        t.start()