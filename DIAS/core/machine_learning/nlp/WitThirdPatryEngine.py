from wit import Wit

from core.consts.social_media import WIT_ACCESS_TOKEN

class WitThirdPatryEngine:

    def wit_nlp_process(self,msg):
        client = Wit(access_token=WIT_ACCESS_TOKEN)
        return client.message(msg)