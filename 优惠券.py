# 优惠券领取
from utils import timer, util
from concurrent.futures import ThreadPoolExecutor
import time
import requests

Exe = ThreadPoolExecutor(max_workers=int(99))


def startRun(accInfo):
    url = "https://api.m.jd.com/client.action?functionId=newBabelAwardCollection"
    header = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36",
        "cookie": accInfo["cookie"],
        "content-type": "application/x-www-form-urlencoded",
        "referer": "https://prodev.m.jd.com/"
    }
    data = "body=%7B%22activityId%22%3A%2231QzsgSooWDuebS3u31MxcSqZ7c2%22%2C%22scene%22%3A%221%22%2C%22args%22%3A%22key%3D9B646C57E3D8E13F5E0F6FF4DEA134B5F9D0C336A50511D9B4B742F57C65FDFA81FB90ACF4CE85BBF36BF88FE51310AF_babel%2CroleId%3D2E9535F97C6A57EF8EEA1C85008E821D_babel%2CstrengthenKey%3D1924E19FBD3218025C6BA355ED04C937EF1FFBA0FB0094D621B096FB350E9818C5C252534939AD97A7E71D034121F78A_babel%22%2C%22platform%22%3A%221%22%2C%22orgType%22%3A%222%22%2C%22openId%22%3A%22-1%22%2C%22pageClickKey%22%3A%22-1%22%2C%22eid%22%3A%22WDA2JLABBG7RQUELITAYT532ZQWNLOLCP4FSUH2VWVAKS6A2JS6SFTQRB76GJ5YMWI5GYFTZNK623WVLZDUL7RLQ2Y%22%2C%22fp%22%3A%2229f2e6057ae8d4ddf45734aaa453f69f%22%2C%22shshshfp%22%3A%22bbde9c4b6c37cd738e88abddb0d5b706%22%2C%22shshshfpa%22%3A%22c94408d9-3fc6-73d6-1084-e9314f44ac8f-1617873698%22%2C%22shshshfpb%22%3A%22ieFk8yy%2FeVXTPEYf2RMtGow%3D%3D%22%2C%22childActivityUrl%22%3A%22https%253A%252F%252Fprodev.m.jd.com%252Fmall%252Factive%252F31QzsgSooWDuebS3u31MxcSqZ7c2%252Findex.html%253FbabelChannel%253Dttt3%22%2C%22userArea%22%3A%22-1%22%2C%22client%22%3A%22-1%22%2C%22clientVersion%22%3A%22-1%22%2C%22uuid%22%3A%22-1%22%2C%22osVersion%22%3A%22-1%22%2C%22brand%22%3A%22-1%22%2C%22model%22%3A%22-1%22%2C%22networkType%22%3A%22-1%22%2C%22jda%22%3A%22122270672.16333648460421882130288.1633364846.1636553982.1636595769.56%22%2C%22pageClick%22%3A%22Babel_Coupon%22%2C%22couponSource%22%3A%22manual%22%2C%22couponSourceDetail%22%3A%22-100%22%2C%22channel%22%3A%22%E9%80%9A%E5%A4%A9%E5%A1%94%E4%BC%9A%E5%9C%BA%22%2C%22headArea%22%3A%22605715ec560d6508f7403b91b677d79c%22%2C%22mitemAddrId%22%3A%22%22%2C%22geo%22%3A%7B%22lng%22%3A%22%22%2C%22lat%22%3A%22%22%7D%2C%22addressId%22%3A%22%22%2C%22posLng%22%3A%22%22%2C%22posLat%22%3A%22%22%2C%22focus%22%3A%22%22%2C%22innerAnchor%22%3A%22%22%2C%22cv%22%3A%222.0%22%7D&screen=750*1334&client=wh5&clientVersion=1.0.0&sid=&uuid=16333648460421882130288&area=18_1482_48936_53640"
    res = requests.post(url, data, headers=header).json()
    print("{} 【{}】{}".format(timer.formatDate(), accInfo["nickname"], res["subCodeMsg"]))


if __name__ == "__main__":
    account = util.getJDAccount()
    accountList = account["data"]["list"]
    # 定时抢优惠券
    av = timer.getAverageOffset()
    # 开始时间 2010-10-01 20:00:00
    startTime = "2021-11-11 10:00:00"

    startTimeStamp = timer.getTimeStamp(startTime)
    print("{} 【时差：{} ms】开始购买,请等待...".format(startTime, av))
    while True:
        now = timer.getNowTime()
        if now >= startTimeStamp:
            for i in range(len(accountList)):
                Exe.submit(startRun, accountList[i])
            break
        time.sleep(.001)
    # ==================================================
    # 批量领取优惠券
    # for i in range(len(accountList)):
    #     startRun(accountList[i])
    #     time.sleep(3)
