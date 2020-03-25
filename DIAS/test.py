# from core.config_loading.ontology_xml_handler import OntologyXMLResultHandler
# from core.ontology.stardog_helper import metadata_query_hazards
# from core.static.consts import ONTOLOGY_YML_CONFIG_FILE
#
# import json
# if __name__ == '__main__':
#
#     metadata_raw_dict = OntologyXMLResultHandler.xml_to_dict(metadata_query_hazards(["flood_1", "landslide_1"],ONTOLOGY_YML_CONFIG_FILE['prefix']['query']['by_warning_sign']))
#
#     metadata_raw_dict_bindings = metadata_raw_dict["sparql"]["results"]["result"]
import time

import twitter
from kafka import KafkaProducer
import json

from core.consts.social_media import TWITTER_API_KEY, TWITTER_API_SECRET_KEY, TWITTER_ACCESS_TOKEN, \
    TWITTER_ACCESS_TOKEN_SECRET

if __name__ == '__main__':

    time.sleep(15)
    api = twitter.Api(consumer_key=TWITTER_API_KEY,
                      consumer_secret=TWITTER_API_SECRET_KEY,
                      access_token_key=TWITTER_ACCESS_TOKEN,
                      access_token_secret=TWITTER_ACCESS_TOKEN_SECRET)

    re = api.GetSearch(since='2020-03-22', term="leaning pole", result_type="recent", return_json=True)
    for r in re["statuses"]:

        # 1868595
        # if r["user"]["id"] == 1241754636601544704:
        # 498168789@qq.com
        if r["user"]["id"] == 1242473094603661319:
        # 166755
        # if r["user"]["id"] == 1238807757450403841:
        # if r["user"]["id"] == 1112009514:

            print(r)
            kafka_topic = "lews-onto-dias"
            msg_json = json.dumps(r)
            producer = KafkaProducer(bootstrap_servers=["localhost:9092"])
            producer.send(kafka_topic, msg_json.encode('utf-8'))
            producer.close()
            break
