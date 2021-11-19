# coding:utf-8
from numpy import *
import time
import requests
import re
from datetime import datetime

host = "http://api.posthub.top/api/ph"


# from config.index import global_config
# import json


class Timer(object):
    def __init__(self, sleep_interval=0.5):
        # self.buy_time = global_config.getRaw('config', 'buy_time')
        # self.buy_time_start = self.getTimeStamp(self.buy_time)

        self.sleep_interval = sleep_interval

        self.averageOffset = []
        self.diff_time = self.getAverageOffset()

    @staticmethod
    def formatDate():
        return datetime.fromtimestamp(int(time.time()))  # .strftime("%Y-%m-%d %H:%M:%S.%f")

    @staticmethod
    def getTimeStamp(t):
        # 转为时间数组
        timeArray = time.strptime(t, "%Y-%m-%d %H:%M:%S")
        # 转为时间戳
        timeStamp = int(time.mktime(timeArray) * 1e3)
        return timeStamp

    def getNowTime(self):
        localTime = int(time.time() * 1e3)
        return localTime + self.diff_time

    def getAverageOffset(self):
        """
        计算本地与京东服务器时间差平均数
        :return:
        """
        for i in range(5):
            localTime = int(time.time() * 1e3)
            self.averageOffset.append(self.getServerTime() - localTime)
        # 求时间偏移平均数
        return int(mean(self.averageOffset))

    def getServerTime(self):
        """
        从京东服务器获取时间毫秒
        :return:
        """
        url = 'https://api.m.jd.com/client.action?functionId=queryMaterialProducts&client=wh5'
        ret = requests.get(url).text
        res = re.compile(r"\d{10,13}").findall(ret)
        return int(res[0])


class Util(object):
    def __init__(self):
        self.USER_AGENTS = []
        self.getUserAgent()
        self.getJDAccount()

    def get_random_useragent(self):
        """生成随机的UserAgent
        :return: UserAgent字符串
        """
        return random.choice(self.USER_AGENTS)

    @staticmethod
    def remove_redundant_comma(text):
        """
        移除json多余逗号，避免json.loads报错
        https://blog.csdn.net/qq_27540041/article/details/114289038
        """
        rex = r"""(?<=[}\]"'])\s*,\s*(?!\s*[{["'])"""
        return re.sub(rex, "", text, 0)

    @staticmethod
    def reLog(content):
        print("{} {}".format(timer.formatDate(), content))

    def getUserAgent(self):
        """
        获取服务器UA
        :return:
        """
        url = "{}/useragent?pageNo=1&pageSize=99".format(host)
        res = requests.get(url)
        if res.status_code == 200:
            resJson = res.json()["data"]["list"]
            for i in range(len(resJson)):
                self.USER_AGENTS.append(resJson[i]["useragent"])
        else:
            util.reLog("获取UA时报错：{}".format(res.status_code))

    @staticmethod
    def getJDAccount():
        """
        获取JD账号
        :return:
        """
        url = "{}/jdAccount?pageNo=1&pageSize=99".format(host)
        res = requests.get(url)
        if res.status_code == 200:
            resJson = res.json()
            return resJson
        else:
            util.reLog("获取账号时报错：{}".format(res.status_code))
            return {"code": res.status_code}

    @staticmethod
    def getJDGoods():
        url = "{}/jdGoods?pageNo=1&pageSize=99".format(host)
        res = requests.get(url)
        if res.status_code == 200:
            resJson = res.json()
            return resJson
        else:
            util.reLog("获取监控商品时报错：{}".format(res.status_code))
            return {"code": res.status_code}

    @staticmethod
    def updateJDAccount(username, cookie):
        url = "{}/jdAccount/updateData".format(host)
        data = {
            "username": username,
            "cookie": cookie
        }
        res = requests.post(url, json=data)
        if res.status_code == 200:
            return res.json()
        else:
            util.reLog("更新账号状态时报错：{}".format(res.status_code))
            return {"code": res.status_code}


timer = Timer()
util = Util()
