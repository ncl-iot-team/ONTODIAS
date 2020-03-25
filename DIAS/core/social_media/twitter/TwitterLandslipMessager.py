import json
import threading
import time
import twitter

from loguru import logger
from twitter import Status


from core.consts.social_media import TWITTER_API_KEY, TWITTER_API_SECRET_KEY, TWITTER_ACCESS_TOKEN, \
    TWITTER_ACCESS_TOKEN_SECRET
from core.consts.database import REDIS_CLIENT
from core.consts.ontology import ONTOLOGY_TRANSFOR
from core.machine_learning.cnn_classification.pred import predict
from core.social_media.twitter.TwitterMessager import TwitterMessager
from core.machine_learning.nlp.WitThirdPatryEngine import WitThirdPatryEngine


class TwitterLandslipMessager(TwitterMessager):

    # 临时demo account 信息

    # 1868495
    # demo_acc_id = 1241754636601544704
    # 166755
    # demo_acc_id = 1238807757450403841
    # 498168789@qq.com
    demo_acc_id = 1242473094603661319
    # ray
    # demo_acc_id = 1112009514

    # demo_acc_id_str = "1241754636601544704"
    # demo_acc_id_str = "1238807757450403841"
    demo_acc_id_str = "1242473094603661319"
    #ray
    # demo_acc_id_str = "1112009514"
    api = twitter.Api(consumer_key=TWITTER_API_KEY,
                      consumer_secret=TWITTER_API_SECRET_KEY,
                      access_token_key=TWITTER_ACCESS_TOKEN,
                      access_token_secret=TWITTER_ACCESS_TOKEN_SECRET)

    # 保存当前需要监控等待回复的messageid
    wait_reply_message_id = 0

    # 存账户信息
    screen_name = ""

    locker = threading.Lock()
    
    def __init__(self):
        super().__init__(locker=self.locker,api=self.api)

    def landslip_search_challenge(self, tweet):

        data = super().ParseAndCheckTwitter(tweet.decode('utf-8'))

        # 格式转化
        tweet_dict = [Status.NewFromJsonDict(x) for x in [data]][0]

        # 判断是否为demo账户
        if tweet_dict.user.id != self.demo_acc_id:
            logger.error("Received not the demo account, the ID: ", tweet_dict.user.id)
            return

        # 清除redis信息  测试用
        REDIS_CLIENT.delete(self.demo_acc_id)

        # 初始化需要回复的tweet id
        self.wait_reply_message_id = tweet_dict.id
        # 初始化需要回复的screen name  目前没用
        self.screen_name = tweet_dict.user.screen_name

        # 匹配demo账户的id
        if tweet_dict.user.id == self.demo_acc_id:
            logger.info(
                "---------------------------------------- New tweet matched From Kafka Start -------------------------------------------")
            logger.info("Tweet ID: {0} , Screen name: {1} Message text : {2}".format(tweet_dict.user.id,
                                                                                     tweet_dict.user.screen_name,
                                                                                     tweet_dict.text))
            logger.info(
                "---------------------------------------- New tweet matched From Kafka End -------------------------------------------")

            self._message_entry(tweet_dict)

            # 启动监控监控回复线程
            self.reply_monitor()
            #
            # if REDIS_CLIENT.hget(self.demo_acc_id, "hazard_chat_status") is not None:
            #     if REDIS_CLIENT.hget(self.demo_acc_id, "hazard_chat_status") == "end":
            #
            #         # 如果有信息需要保留 则需要回滚
            #         TwitterHelper.roll_back(self.demo_acc_id)

    def _message_entry(self, tweet_dict):

        # nlp 解析输入的内容
        wit = WitThirdPatryEngine()
        nlp_res = wit.wit_nlp_process(tweet_dict.text)

        # 检查聊天状态
        if not REDIS_CLIENT.hexists(self.demo_acc_id, "hazard_chat_status"):
            
            self._nlp_question_process(self.demo_acc_id, nlp_res)
            

        if (not REDIS_CLIENT.hexists(self.demo_acc_id, "hazard_chat_status")) or \
                (REDIS_CLIENT.hget(self.demo_acc_id, "hazard_chat_status") is None):
            return

        # 问题处理区域
        self._question_handle(tweet_dict,nlp_res)

    def _question_handle(self, tweet_dict,nlp_res):

        q_status = REDIS_CLIENT.hget(self.demo_acc_id, "hazard_chat_status")
        logger.debug("hazard_chat_status: {0} ".format(q_status, ))

        if q_status == "end":
            return

        # 是否回复过ontology结果
        if not REDIS_CLIENT.hexists(self.demo_acc_id,"ontology_result_reply"):
            all_text = [tweet_dict.text]

            ontology_resp = self.cnn_pred(all_text)

            logger.info(ontology_resp)
            # 回答ontolog 结果
            # super().reply_tweet(screen_name=self.screen_name, text=ontology_resp,
            #                     tweet_id=self.wait_reply_message_id)

            # 已经回复过ontology结果
            REDIS_CLIENT.hset(self.demo_acc_id,"ontology_result_reply","1")

        resp = self._question_match(REDIS_CLIENT.hget(self.demo_acc_id, "question_seq"), tweet_dict=tweet_dict,nlp_res=nlp_res)

        # 回复问题
        if resp is not None:
            self.reply_tweet(screen_name=self.screen_name, text=resp, tweet_id=self.wait_reply_message_id)

    def _question_match(self, seq, tweet_dict,nlp_res):

        logger.debug("Question sequence: {0} ".format(seq, ))

        # 第1个问题 地点
        if seq == "1":

            logger.info("Mached question seq 1")

            # 获取信息中的地点信息
            location_res = self.nlp_location_processing(nlp_res)

            # 没有地点信息
            if location_res is not None:
                logger.debug("location_res is {0}".format(location_res,))

                if not REDIS_CLIENT.hexists(self.demo_acc_id, "location_reply"):
                    REDIS_CLIENT.hset(self.demo_acc_id, "location_reply", "1")
                    
                    return "Where did you observe this event ? "

            REDIS_CLIENT.hset(self.demo_acc_id, "question_seq", "2")

        # 第2个问题 时间
        if REDIS_CLIENT.hget(self.demo_acc_id, "question_seq") == "2":

            logger.info("Mached question seq 2")

            # 获取信息中的地点信息
            date_res = self.nlp_datetime_processing(nlp_res)

            if date_res is not None:
                logger.debug("date_res is {0}".format(date_res, ))
                if not REDIS_CLIENT.hexists(self.demo_acc_id, "date_reply"):
                    REDIS_CLIENT.hset(self.demo_acc_id, "date_reply", "1")

                    return "When did you observe this event?"
                return None
            # 回答完问题 切换下一个问题
            REDIS_CLIENT.hset(self.demo_acc_id, "question_seq", "3")

        elif seq == "3":

            logger.info("Mached question seq 3")

            if not REDIS_CLIENT.hexists(self.demo_acc_id, "Q_2_1_reply"):
                REDIS_CLIENT.hset(self.demo_acc_id, "Q_2_1_reply", "1")
                
                return "Is it ‘raining’ where you observed the ‘leaning pole’?"

            # 收录回复
            if REDIS_CLIENT.hexists(self.demo_acc_id, "Q_2_1_reply"):
                if self.check_Y_N_answer(tweet_dict.text):
                    REDIS_CLIENT.hset(self.demo_acc_id, "Q_2_1_answer", tweet_dict.text)
                    # 回答完问题 切换下一个问题
                    REDIS_CLIENT.hset(self.demo_acc_id, "question_seq", "4")
                    logger.info("Q_2_1 finished")

        elif seq == "4":

            logger.info("Mached question seq 4")

            if not REDIS_CLIENT.hexists(self.demo_acc_id, "Q_2_2_reply"):
                REDIS_CLIENT.hset(self.demo_acc_id, "Q_2_2_reply", "1")
                
                return "Have you noticed any ‘rockfalls’ where you observed the ‘leaning pole’?"

            # 收录回复
            if REDIS_CLIENT.hexists(self.demo_acc_id, "Q_2_2_reply"):
                if self.check_Y_N_answer(tweet_dict.text):
                    REDIS_CLIENT.hset(self.demo_acc_id, "Q_2_2_answer", tweet_dict.text)
                    # 回答完问题 切换下一个问题
                    REDIS_CLIENT.hset(self.demo_acc_id, "question_seq", "5")
                    logger.info("Q_2_2 finished")

        elif seq == "5":

            logger.info("Mached question seq 4")

            if not REDIS_CLIENT.hexists(self.demo_acc_id, "Q_2_3_reply"):
                REDIS_CLIENT.hset(self.demo_acc_id, "Q_2_3_reply", "1")
                
                return "Is there ‘flooding’ in ‘Newcastle upon Tyne’?"

            # 收录回复
            if REDIS_CLIENT.hexists(self.demo_acc_id, "Q_2_3_reply"):
                if self.check_Y_N_answer(tweet_dict.text):
                    REDIS_CLIENT.hset(self.demo_acc_id, "Q_2_3_answer", tweet_dict.text)
                    # 关闭问题
                    REDIS_CLIENT.hset(self.demo_acc_id, "hazard_chat_status", "end")
                    REDIS_CLIENT.hset(self.demo_acc_id, "question_seq", "0")
                    logger.info("Q_2_3 finished")

        return None

    def check_Y_N_answer(self,text):
        logger.debug("text.upper()) bool: {0}".format("YES" in text.upper()))
        logger.debug("text.upper()): {0}".format(text.upper()))
        if ("YES" in text.upper()) or ("NO" in text.upper()):
            return True
        return False

    def nlp_datetime_processing(self,nlp):

        if REDIS_CLIENT.hget(self.demo_acc_id, "hazard_chat_status") is None:
            return
        elif REDIS_CLIENT.hget(self.demo_acc_id, "hazard_chat_status") == "end":
            return

        # 只要开始了对话就必须先提供时间日期
        if 'datetime' not in nlp["entities"].keys() and \
            REDIS_CLIENT.hget(self.demo_acc_id, "hazard_chat_status") == "start":
            logger.debug("datatime not in entities")
            return False

        # 判断类型
        if 'type' in nlp["entities"]["datetime"][0]:

            # 指定日期以及 今天明天昨天关键词
            if nlp["entities"]["datetime"][0]["type"] == "value":

                if 'value' in nlp["entities"]["datetime"][0]:

                    date = nlp["entities"]["datetime"][0]['value'].split('T')[0]

                    if not REDIS_CLIENT.hexists(self.demo_acc_id, "date"):

                        # 如果已经已经有的话更新,没有就创建
                        REDIS_CLIENT.hset(self.demo_acc_id, "date", json.dumps({"value": date, "type": "value"}))
                    else:
                        info = REDIS_CLIENT.hget(self.demo_acc_id, "date")

                        dict = json.loads(info)

                        # 直接更新data
                        dict['value'] = date
                        dict['type'] = "value"

                        REDIS_CLIENT.hset(self.demo_acc_id, "date", json.dumps(dict))

            # 一段时间 目前只支持输入 from 。。。  to ...
            if nlp["entities"]["datetime"][0]["type"] == "interval":

                if 'from' in nlp["entities"]["datetime"][0] and 'to' in nlp["entities"]["datetime"][0]:

                    # 当前只取date
                    date_from = nlp["entities"]["datetime"][0]["from"]["value"].split('T')[0]

                    date_to = nlp["entities"]["datetime"][0]["to"]["value"].split('T')[0]

                    if not REDIS_CLIENT.hexists(self.demo_acc_id, "date"):

                        # 如果已经已经有的话更新,没有就创建
                        REDIS_CLIENT.hset(self.demo_acc_id, "date",
                                          json.dumps({"from": date_from, "to": date_to, "type": "interval"}))
                    else:
                        info = REDIS_CLIENT.hget(self.demo_acc_id, "date")

                        dict = json.loads(info)

                        # 直接更新data
                        dict['from'] = date_from
                        dict['to'] = date_to
                        dict['type'] = "interval"

                        REDIS_CLIENT.hset(self.demo_acc_id, "date", json.dumps(dict))


    def nlp_location_processing(self, nlp):

        logger.debug("location nlp : {0}".format(nlp,))
        if 'entities' not in nlp.keys():
            logger.debug(" entities not in keys")
            return None

        if REDIS_CLIENT.hget(self.demo_acc_id, "hazard_chat_status") is None:
            logger.debug("hazard_char_status is None")
            return None
        elif REDIS_CLIENT.hget(self.demo_acc_id, "hazard_chat_status") == "end":
            logger.debug("hazard_char_status is end")
            return None

        if (('location' not in nlp["entities"].keys()) and
            REDIS_CLIENT.hget(self.demo_acc_id, "hazard_chat_status") == "start"):
                # or ('question_keyword' in nlp["entities"].keys()):
            logger.debug("There is no location info")
            return False

            # 只要开始了对话就必须先提供时间日期

        # 不止一个地区结果
        # 目前默认为1个地区结果
        if len(nlp["entities"]['location']) != 1:
            logger.error( "This system is not support multi-location.")

        if 'resolved' not in nlp["entities"]['location'][0]:

            # 可以拿到准确的位置信息
            if 'suggested' in nlp["entities"]['location'][0].keys():

                if nlp["entities"]['location'][0]['suggested']:
                    location = nlp["entities"]['location'][0]['value']

                    logger.debug("Adding location info")

        elif len(nlp["entities"]['location'][0]['resolved']['values']) != 1:

            # 详细信息可以用下面的进一步取
            all_prob_location = ""

            location = nlp["entities"]['location'][0]["value"]

            for val in nlp["entities"]['location'][0]['resolved']['values']:

                if 'external' in val.keys():
                    if 'wikipedia' in val['external'].keys():
                        all_prob_location = all_prob_location + "\n\t" + val['external']['wikipedia']
                    else:
                        all_prob_location = all_prob_location + "\n\t" + val['name']

            self.add_value_location(location)
        return None

    def add_value_location(self, location):
        logger.debug("Adding location info")
        if not REDIS_CLIENT.hexists(self.demo_acc_id, "location"):

            # 如果已经已经有的话更新,没有就创建
            REDIS_CLIENT.hset(self.demo_acc_id, "location", json.dumps({"title": location}))
        else:
            info = REDIS_CLIENT.hget(self.demo_acc_id, "location")

            dict = json.loads(info)

            # 直接更新data
            dict['title'] = location

            REDIS_CLIENT.hset(self.demo_acc_id, "location", json.dumps(dict))

    def cnn_pred(self, msg):
        pred_result, ontology_result = predict(msg)

        text = []

        if "Other" in ontology_result.keys():
            logger.error("No ontology result !")

        ontology_result_reformat = []
        if ("LeaningTelephonePole" in ontology_result.keys()) or ("IncreaseInWaterLevel" in ontology_result.keys()):
            for k, v in ontology_result.items():
                for val in ontology_result[k]:
                    ontology_result_reformat.append(val)
                    text.append(ONTOLOGY_TRANSFOR[val])

            # 临时答案2个
            text = "From DIAS: Hazards: " + text[0] + " and " + text[1] + " are likely to occur."
        # 目前只能按一句识别 所以else可以这么写
        # else:
        #     for val in ontology_result.items():
        #         for key in val.keys():
        #             text = "I've got the kind of hazard is " + text + key

        # 存入hazard结果  这里只处理了leaningpole  取参数的地方需要判断是否存在key
        REDIS_CLIENT.hset(self.demo_acc_id, "ontology_result_hazards", json.dumps(ontology_result_reformat))

        return text

    '''
        检查nlp的结果
    '''

    def _nlp_question_process(self, recipient_id, nlp):
        '''
            return:
                0 表示没有疑问词 what which
                1 表示成功
                2 表示没有hazard 关键词
        '''

        if 'entities' not in nlp.keys():
            return None

        if 'question_keyword' not in nlp["entities"].keys():
            return 0

        keyword_tag = False

        for keyword in nlp["entities"]['question_keyword']:
            if keyword['value'] == "what" or keyword['value'] == "which":
                keyword_tag = True

        if not keyword_tag:
            return 0

        if 'hazard_keyword' not in nlp["entities"].keys():
            return 2

        # 意味着hazard对话已经开始
        REDIS_CLIENT.hset(recipient_id, "hazard_chat_status", "start")
        REDIS_CLIENT.hset(recipient_id, "question_seq", "1")
        return 1

    def reply_monitor(self):

        while True:

            all_in_reply_ids = []
            all_mention_ids = []
            #  获取所有提及到的信息
            for mentions in self.api.GetMentions():
                all_in_reply_ids.append(mentions.in_reply_to_status_id)
                all_mention_ids.append(mentions.id)

            logger.debug("All mentions : {0}".format(self.api.GetMentions(return_json=True)))

            i = 0
            for id in all_in_reply_ids:
                # 如果提及的和原有的id重合说明有人针对性回复了
                if id == self.wait_reply_message_id:

                    logger.info(
                        "================  Someone replied the message ================")

                    self.wait_reply_message_id = all_mention_ids[i]

                    self._message_entry(self.api.GetStatus(self.wait_reply_message_id))
                    logger.debug("Replied message info :{0}".format(self.api.GetStatus(self.wait_reply_message_id)))
                    continue
                logger.debug("Replied message info :{0}".format(self.api.GetStatus(self.wait_reply_message_id)))
                logger.info("wait_reply_message_id: {0}".format(self.wait_reply_message_id))
                self._message_entry(self.api.GetStatus(self.wait_reply_message_id))
                i += 1

            if REDIS_CLIENT.hexists(self.demo_acc_id,"hazard_chat_status"):
                logger.debug("hazard_chat_status", REDIS_CLIENT.hget(self.demo_acc_id, "hazard_chat_status") == "end")
                if REDIS_CLIENT.hget(self.demo_acc_id, "hazard_chat_status") == "end":
                    break

            # 不存在的话 不用监控
            else:
                break

            logger.debug("Waiting for reply............. waiting msg ID :{0}".format(self.wait_reply_message_id))
            time.sleep(10)