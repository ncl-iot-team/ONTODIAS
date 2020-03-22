import json

from loguru import logger
import threading

from core.social_media.twitter.Twitter import Twitter
from core.consts.social_media import TWITTER_ACC_ID, TWITTER_ACC_SCREEN_NAME
from core.social_media.twitter.TwitterError import TwitterError


class TwitterMessager(Twitter):

    # 创建内部锁
    locker = None
    api = None

    def __init__(self,locker,api):
        super().__init__()
        self.locker = locker
        self.api = api

    def reply_tweet(self,screen_name,text,tweet_id,media=""):

        logger.info("---------------------------------------- Reply Tweet Start -------------------------------------------")
        logger.info("Tweet ID: {0} , Message text : {1}".format(tweet_id,text))
        logger.info("---------------------------------------- Reply Tweet End -------------------------------------------")

        mentions = "@" + screen_name + " "

        # 判断前一条是不是自己发的
        status = self.api.GetStatus(tweet_id)

        # 自己发的话  需要at2个人
        if status.user.id == TWITTER_ACC_ID:
            mentions = "@" + screen_name + " " + "@" + TWITTER_ACC_SCREEN_NAME + " "

        resp = self.api.PostUpdate(mentions+text+media, in_reply_to_status_id=tweet_id)

        logger.debug("replied resp : {0}".format(resp))
        self.wait_reply_message_id = resp.id

        logger.info("---------------------------------------- Replied information Start -------------------------------------------")
        logger.info("Replied Tweet ID: {0} , Replied message text : {1}".format(resp.id,resp.text))
        logger.info("---------------------------------------- Replied information End -------------------------------------------")

    '''
        This from api: twitter source code
    '''
    def ParseAndCheckTwitter(self,json_data):
        """Try and parse the JSON returned from Twitter and return
        an empty dictionary if there is any error.

        This is a purely defensive check because during some Twitter
        network outages it will return an HTML failwhale page.
        """
        try:
            data = json.loads(json_data)
        except ValueError:
            if "<title>Twitter / Over capacity</title>" in json_data:
                raise TwitterError({'message': "Capacity Error"})
            if "<title>Twitter / Error</title>" in json_data:
                raise TwitterError({'message': "Technical Error"})
            if "Exceeded connection limit for user" in json_data:
                raise TwitterError({'message': "Exceeded connection limit for user"})
            if "Error 401 Unauthorized" in json_data:
                raise TwitterError({'message': "Unauthorized"})
            raise TwitterError({'Unknown error': '{0}'.format(json_data)})
        self.CheckForTwitterError(data)
        return data

    '''
        This from api: twitter source code
    '''
    def CheckForTwitterError(self,data):
        """Raises a TwitterError if twitter returns an error message.

        Args:
            data (dict):
                A python dict created from the Twitter json response

        Raises:
            (twitter.TwitterError): TwitterError wrapping the twitter error
            message if one exists.
        """
        # Twitter errors are relatively unlikely, so it is faster
        # to check first, rather than try and catch the exception
        if 'error' in data:
            raise TwitterError(data['error'])
        if 'errors' in data:
            raise TwitterError(data['errors'])