import threading
from utils import util
import time
import json
from src import jd, sm, rgs
from concurrent.futures import ThreadPoolExecutor

Exe = ThreadPoolExecutor(max_workers=int(99))

accountList = []
watchList = []

lock = threading.Lock()


def getWatchList():
    global watchList
    # with open("./productList.json", "r", encoding="utf-8") as products:
    #     watchList = json.load(products)
    try:
        res = util.getJDGoods()
        if res["code"] == 200:
            item = res["data"]["list"]
            temp = []
            # 提取有购买量的商品进行监控购买
            for i in range(len(item)):
                if item[i]["buyNum"]:
                    temp.append(item[i])
            watchList = temp
            util.reLog("监控列表更新完成！")
            return False
        else:
            return True
    except Exception as e:
        util.reLog("获取监控列表请求报错：{}".format(e))
        return True


def getAccounts():
    global accountList
    try:
        res = util.getJDAccount()
        if res["code"] == 200:
            item = res["data"]["list"]
            temp = []
            # 提取在线状态的账号
            for i in range(len(item)):
                if not item[i]["status"]:
                    temp.append(item[i])
            accountList = temp
            if len(accountList) == 0:
                sm.send_wx_msg(f"accountList={len(accountList)} 賬號有異常！")
            util.reLog("账号列表更新完成！")
            return False
        else:
            return True
    except Exception as e:
        util.reLog("获取账号列表请求报错：{}".format(e))
        return True


def setIntervalAccount():
    global accountList
    # with open("Cookies.json", "r", encoding="utf-8") as cookies:
    #     accountList = json.load(cookies)
    while True:
        lock.acquire()
        ok = getAccounts()
        lock.release()
        if ok:
            continue
        time.sleep(60 * 5)


def setIntervalWatch():
    global watchList
    # with open("./productList.json", "r", encoding="utf-8") as products:
    #     watchList = json.load(products)
    while True:
        if getWatchList():
            continue
        time.sleep(60 * 10)


def setIntervalCollect():
    while True:
        diffCollect()
        time.sleep(60 * 8)


def diffCollect():
    """
    比较收藏夹与监控数据的差异并添加差异到收藏夹
    :return:
    """
    watch_temp = []
    for x in range(len(watchList)):
        watch_temp.append(watchList[x]["skuId"])

    # 循环拿到每个账号的收藏商品ID
    for x in range(len(accountList)):
        nickname = accountList[x]["nickname"]
        username = accountList[x]["username"]
        cookie = accountList[x]["cookie"]

        jd.setHeaders(cookie)
        collect_temp = []
        proList = jd.watchInventory(accountList[x]["areaId"], 0)

        if "data" in proList:
            d = proList["data"]
            if not len(d):
                util.reLog(f"{nickname}获取收藏列表数据失败，为：{d}")

            for i in range(len(d)):
                collect_temp.append(d[i]["commId"])
            # 监控数据相较收藏数据的差异商品，添加收藏
            w_diff_c = list(set(watch_temp).difference(collect_temp))
            if len(w_diff_c):
                for j in range(len(w_diff_c)):
                    jd.favCommAdd(w_diff_c[j], cookie)
                    util.updateJDAccount(username, cookie)
                    time.sleep(2)
            else:
                util.reLog("{},未获取到【添加收藏】差异数据".format(nickname))

            # 收藏数据相较监控数据的差异商品，取消收藏
            c_diff_w = list(set(collect_temp).difference(watch_temp))
            if len(c_diff_w):
                # 逐个取消收藏
                # for j in range(len(c_diff_w)):
                #     jd.favCommDel(c_diff_w[j], cookie)
                #     time.sleep(2)
                # 批量取消收藏
                jd.favCommBatchDel(",".join(c_diff_w), cookie)
                util.updateJDAccount(username, cookie)
            else:
                util.reLog("{},未获取到【取消收藏】差异数据".format(nickname))
        else:
            util.reLog("未获取到【{}】收藏数据！".format(nickname))
        time.sleep(2)


def addCollect():
    """
    将监控列表数据添加到收藏
    :return:
    """
    for x in range(len(accountList)):
        for index in range(len(watchList)):
            util.reLog("{}: 正在将【{}】加入收藏夹...".format(accountList[x]["nickname"], watchList[index]["name"]))
            jd.favCommAdd(watchList[index]["id"], accountList[x]["cookie"])
            time.sleep(2)
        time.sleep(2)


def batchDelCollect():
    """
    批量取消收藏
    :return:
    """
    for i in range(len(accountList)):
        cookie = accountList[i]["cookie"]
        # 设置cookie
        jd.setHeaders(cookie)

        proList = jd.watchInventory(accountList[i]["areaId"], 0)
        ls = proList["data"]
        if len(ls) != 0:
            temp = []
            for z in range(len(ls)):
                temp.append(ls[z]["commId"])
            skuIds = ",".join(temp)
            jd.favCommBatchDel(skuIds)
        else:
            util.reLog("{} 没有收藏商品！".format(accountList[i]["nickname"]))
        time.sleep(5)


def isRisk(api, data, userInfo):
    noLogin = False
    # 判断是否风控，为None则被风控
    if not isinstance(data, dict):
        util.reLog("【{}】 监控返回的错误数据：{}".format(api, data))
        sm.send_wx_msg("{} 疑似被风控！{}".format(api, userInfo["nickname"]))
        noLogin = True
    else:
        #  判断登录是否失效
        if "iRet" in data:
            if int(data["iRet"]):
                noLogin = True
        elif "retCode" in data:
            if int(data["retCode"]):
                noLogin = True
        if noLogin:
            util.reLog("{} 疑似登录失效！".format(userInfo["nickname"]))
            sm.send_wx_msg("{} 疑似登录失效！".format(userInfo["nickname"]))
            sm.send_sql_log("{} 疑似登录失效,{}".format(userInfo["nickname"], json.dumps(data)))
            util.updateJDAccount(userInfo["username"], userInfo["cookie"])
            # 尝试更新账号列表
            getAccounts()
    return noLogin


def watchInventory():
    runCount = 0
    while True:
        # lock.acquire()
        _watchInventory()
        runCount += 1
        if runCount % 100 == 0:
            util.reLog(f"runCount = {runCount}")
        # lock.release()


def _watchInventory():
    # 轮番使用jd与jx两个接口
    try:
        for k in range(2):
            for i in range(len(accountList)):
                cookie = accountList[i]["cookie"]
                userInfo = accountList[i]
                # 设置cookie
                nickname = accountList[i]["nickname"]
                areaId = accountList[i]["areaId"]
                jd.setHeaders(cookie)
                # 用来打印错误源
                proList = None
                try:
                    # 选择接口进行监控 1为jd 0为jx
                    apiType = k
                    if apiType:
                        proList = jd.watchInventory(areaId)

                        if isRisk("JD", proList, userInfo):
                            continue
                        skuInfo = proList["data"]
                        isBuy = True
                    else:
                        res = jd.setRedis(areaId)

                        if isRisk("JX", res, userInfo):
                            continue
                        proList = jd.watchInventoryJx()

                        if isRisk("JX", proList, userInfo):
                            continue
                        skuInfo = proList["data"]["skuInfo"]
                        # jx接口没有筛选功能，根据顶置特性，来进行判断
                        isBuy = skuInfo[0]["hasStock"] == 1 and skuInfo[0]["isShelves"] == 1 and skuInfo[0][
                            "isYuShou"] == 0

                    api_type = "JD" if apiType else "JX"
                    # 判断是否请求成功
                    if proList["iRet"] == "0":
                        if len(skuInfo) != 0 and isBuy:
                            isOrder(skuInfo, apiType)
                        else:
                            util.reLog("【{}】无有货的商品！来自账号：{}".format(api_type, nickname))
                    else:
                        util.reLog("【{}】接口返回异常：{}".format(nickname, proList["errMsg"]))
                except Exception as e:
                    print(proList)
                    util.reLog(f"【{nickname}】监控异常报错：{e}")

                time.sleep(2)
            # else:
            #     # 如果没有执行for的主程序，則會跑到這裏來
            #     util.reLog(f"No Account, Please Check. AccountList={len(accountList)}")
    except Exception as e:
        print(e)


def isOrder(proList, apiType):
    """
    是否符合下单条件，符合便开始下单
    commStatus＝1是上架，0是下架          isShelves
    hasStock＝1是有货，0是无货            hasStock
    commOrderStatus＝1是预约状态（抢购预约），0是普通商品（非预约非秒杀）   isYuShou
    :param apiType: 调用的API类型，1 为jd 0 为jx
    :param proList: 监控返回的商品收藏列表数据
    :return:
    """
    for j in range(len(proList)):
        try:
            data = proList[j]
            if apiType:
                # 下单条件
                IS = data["commStatus"] == "1" and data["hasStock"] == 1 and data["commOrderStatus"] == "0"
                proId = data["commId"]
                proName = data["commTitle"]
                # 获取详情页的库存状态
                cat = data["commCategory"].replace(";", ",")
            else:
                IS = data["hasStock"] == 1 and data["isShelves"] == 1 and data["isYuShou"] == 0
                proId = data["skuId"]
                proName = data["goodsName"]

                cat = data["goodsCategory"].replace(";", ",")

            api_type = "JD" if apiType else "JX"
            # 满足上架、有货、普通商品条件
            if IS:
                # 获取详情页的库存状态
                detailsStock = rgs(proId, accountList[0]["areaId"], cat, data["venderId"])
                if int(detailsStock) != 34:
                    for y in range(len(watchList)):
                        # 符合监控列表数据的条件
                        if proId == watchList[y]["skuId"] and watchList[y]["buyNum"] != 0:
                            # 这里发送信息之前是用了Exe.submit(sm.send_ding_msg)
                            item = f"{proName},有货了啦！库存状态：{detailsStock}\n商品链接：https://item.m.jd.com/product/{proId}.html"
                            # Exe.submit(sm.send_ding_msg, item)
                            sm.send_ding_msg(item)
                            commitOrder(watchList[y])
                else:
                    util.reLog(f"【{api_type}】【{proName}】不符合下单条件！详情库存：{detailsStock}")
            else:

                util.reLog(f"【{api_type}】【{proName}】不符合下单条件！收藏夹库存：{IS}")
        except Exception as e:
            util.reLog(f"确认订单报错：{e}")
        time.sleep(1)


def commitOrder(watchData):
    """
    确认下单
    :return:
    """
    for x in range(len(accountList)):
        # jd.setHeaders(accountList[x]["cookie"])
        jd.orderAction(watchData, accountList[x])
        # 多线程
        # Exe.submit(jd.orderAction, watchData, accountList[x])


if __name__ == "__main__":
    Exe.submit(setIntervalAccount)
    Exe.submit(setIntervalWatch)
    time.sleep(5)
    Exe.submit(setIntervalCollect)
    time.sleep(5)
    watchInventory()

    # 测试下单
    # jd.setHeaders("pt_key=AAJhWCPhADDehv0WYWD7Jb3ZaZS-87ptA_Xb2KHTeda3BxS-MWp8MKlLw-l8kYtowQWkfJDpBMs;")
    # jd.setRedis(accountList[5]["areaId"])
    # print(jd.watchInventoryJx())
    # jd.orderAction("11454116841", 1, accountList[5]["username"])
    # 添加收藏
    # addCollect()
    # jx 测试接口
    # jd.setHeaders(accountList[0]["cookie"])
    # jd.setRedis()
    # print(jd.watchInventoryJx())
