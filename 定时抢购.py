from utils import timer, util
from src import jd
from concurrent.futures import ThreadPoolExecutor
import time

Exe = ThreadPoolExecutor(max_workers=int(99))

proInfo = {
    "skuId": "10026188020628",
    "goodName": "耐克 男子 NIKE DUNK LOW RETRO 运动鞋 DD1391 DD1391-103 42",
    "buyNum": "1"
}


def startRun(accInfo):
    number = 0
    while True:
        now = timer.getNowTime()
        if now >= startTimeStamp:
            jd.orderAction(proInfo, accInfo)
            number += 1
            if number >= 3:
                break
        time.sleep(.001)


if __name__ == "__main__":
    account = util.getJDAccount()
    accountList = account["data"]["list"]
    # 定时抢
    av = timer.getAverageOffset()
    # 开始时间 2010-10-01 20:00:00
    startTime = "2021-11-27 10:00:00"

    startTimeStamp = timer.getTimeStamp(startTime)
    print("{} 【时差：{} ms】开始购买,请等待...".format(startTime, av))

    for i in range(len(accountList)):
        print(f"{accountList[i]['nickname']},等待下单中...")
        Exe.submit(startRun, accountList[i])
