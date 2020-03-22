import json

from kafka import KafkaConsumer

from core.consts.configure import SYSTEM_CONFIG_FILE


class dataCollector:
    kafka_conf = {}

    def __init__(self):
        self.kafka_conf = SYSTEM_CONFIG_FILE["kafka"]

    def kafka_consumer(self):
        consumer_client = KafkaConsumer(
            bootstrap_servers=[self.kafka_conf["host"] + ":" + str(self.kafka_conf["port"])])

        consumer_client.subscribe([self.kafka_conf["topic_lews"]])

        return consumer_client
