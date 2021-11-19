# 优惠券领取
from utils import util
import time
import json
import requests


def startRun(accInfo):
    skuId = "100021318944"
    url = "https://wq.jd.com/bases/yuyue/item?callback=subscribeItemCBA&dataType=1&skuId={}&sceneval=2".format(skuId)
    header = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36",
        "cookie": accInfo["cookie"],
        "content-type": "application/x-www-form-urlencoded",
        "referer": "https://wqs.jd.com/"
    }
    res = requests.get(url, headers=header)
    resJson = json.loads(res.text[17:-3])
    print("【{}】----{}".format(accInfo["nickname"], resJson["list"][0]["replyMsg"]))


if __name__ == "__main__":
    account = util.getJDAccount()
    accountList = account["data"]["list"]
    for i in range(len(accountList)):
        startRun(accountList[i])
        time.sleep(3)
