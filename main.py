# coding:utf-8
import threading
from utils import util
import time
import json
import random
import copy
import traceback
import ctypes
from src import jd, sm, rgs
from concurrent.futures import ThreadPoolExecutor

Exe = ThreadPoolExecutor(max_workers=int(99))

# 线程时间变量(看门狗监控值)
thread_Time = 0

accountList = []
# 用来比对的账号列表，本地持久保存
localAccList = []

watchList = []
# 用来比对的监控列表，本地持久保存
localWatchList = []

global_collectList = []

lock = threading.Lock()
Thread = threading.Thread


def getAccounts():
    global accountList
    global localAccList
    res = util.getJDAccount()
    if res["code"] == 200:
        resList = res["data"]["list"]
        accTemp = []
        # 提取在线状态的账号
        for i in range(len(resList)):
            if not resList[i]["status"]:
                accTemp.append(resList[i])

        if localAccList != accTemp or not len(localAccList) or not len(accountList):
            lock.acquire()
            localAccList = accTemp
            accountList = copy.deepcopy(accTemp)
            lock.release()

            util.reLog("账号列表更新完成！")
        else:
            util.reLog("账号列表并无差异，无需更新！")


def setIntervalAccount():
    global accountList
    # with open("Cookies.json", "r", encoding="utf-8") as cookies:
    #     accountList = json.load(cookies)
    while True:
        try:
            getAccounts()
        except Exception as e:
            util.reLog(f"获取账号发生异常：{traceback.format_exc()}")
        finally:
            time.sleep(60 * 2)


def getWatchList():
    global watchList
    global localWatchList
    # with open("./productList.json", "r", encoding="utf-8") as products:
    #     watchList = json.load(products)
    res = util.getJDGoods()
    if res["code"] == 200:
        resList = res["data"]["list"]
        watchTemp = []
        # 提取有购买量的商品进行监控购买
        for i in range(len(resList)):
            # 增加提示次数，避免虚假库存时一直提示并下单
            resList[i]["isTip"] = True
            if resList[i]["buyNum"]:
                watchTemp.append(resList[i])
        # 本地数据与远程数据or本地数据为空时进行数据更新

        if localWatchList != watchTemp or not len(localWatchList) or not len(watchList):
            lock.acquire()
            localWatchList = watchTemp
            watchList = copy.deepcopy(watchTemp)
            lock.release()

            util.reLog("监控列表更新完成！")
        else:
            util.reLog("监控列表并无差异，无需更新！")


def setIntervalWatch():
    # with open("./productList.json", "r", encoding="utf-8") as products:
    #     watchList = json.load(products)
    while True:
        try:
            getWatchList()
        except Exception as e:
            util.reLog(f"获取监控数据发生异常：{traceback.format_exc()}")
        time.sleep(30)


def setIntervalCollect():
    global global_collectList
    try:
        while True:
            if len(global_collectList):
                collectList = global_collectList
                collectDiffContrast(collectList)
                time.sleep(30)
            else:
                getCollectList()
                util.reLog("全局收藏列表为空，重新请求中...")
                time.sleep(5)
    except Exception as e:
        util.reLog(f"比对收藏数据发生异常：{traceback.format_exc()}")


def getCollectList():
    """
    获取收藏夹列表赋值到全局变量中
    :return:
    """
    global global_collectList
    while True:
        try:
            acc = accountList[random.randint(0, len(accountList) - 1)]
            jd.setHeaders(acc["cookie"])
            res = jd.watchInventory(acc["areaId"], 0)
            if len(res["data"]):
                lock.acquire()
                global_collectList = res["data"]
                lock.release()
                util.reLog("获取收藏数据完成,赋值成功！")
            else:
                util.reLog("获取收藏数据为空,重新获取中...")
                time.sleep(2)
                getCollectList()
        except Exception as e:
            util.reLog(f"获取收藏数据发生异常：{traceback.format_exc()}")
        finally:
            time.sleep(60 * 10)


def collectDiffContrast(collectList):
    """
    收藏差异比较
    :return:
    """
    watch_temp = []
    collect_temp = []

    for i in range(len(collectList)):
        collect_temp.append(collectList[i]["commId"])
    for x in range(len(watchList)):
        watch_temp.append(watchList[x]["skuId"])

    w_diff_c = list(set(watch_temp).difference(collect_temp))
    c_diff_w = list(set(collect_temp).difference(watch_temp))
    if len(w_diff_c) or len(c_diff_w):
        util.reLog("监控商品与收藏商品之间存在差异,准备校正中...")
        collectDiffCorrection()
    else:
        util.reLog("监控商品与收藏商品之间并无差异，无需更新！")


def collectDiffCorrection():
    """
    收藏差异校正
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

        while True:
            proList = jd.watchInventory(accountList[x]["areaId"], 0)
            if "data" in proList and len(proList["data"]):
                break
            else:
                util.reLog(f"未获取到【{nickname}】收藏数据！重新获取中...")
            time.sleep(2)

        collectData = proList["data"]
        if not len(collectData):
            util.reLog(f"{nickname}获取收藏列表数据失败，为：{collectData}")

        for i in range(len(collectData)):
            collect_temp.append(collectData[i]["commId"])
        # 监控数据相较收藏数据的差异商品，添加收藏
        w_diff_c = list(set(watch_temp).difference(collect_temp))
        if len(w_diff_c):
            for j in range(len(w_diff_c)):
                lock.acquire()
                jd.favCommAdd(w_diff_c[j], cookie)
                util.updateJDAccount(username, cookie)
                lock.release()
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
            lock.acquire()
            jd.favCommBatchDel(",".join(c_diff_w), cookie)
            util.updateJDAccount(username, cookie)
            lock.release()
        else:
            util.reLog("{},未获取到【取消收藏】差异数据".format(nickname))
        time.sleep(2)
    getCollectList()


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
    global thread_Time
    while True:
        # lock.acquire()
        try:
            thread_Time = int(time.time())
            _watchInventory()
        except Exception as e:
            util.reLog(f"比对收藏数据发生异常：{traceback.format_exc()}")
        # lock.release()


def _watchInventory():
    # 轮番使用jd与jx两个接口
    apiType = ["JX", "JD"]
    accTemp = copy.deepcopy(accountList)
    for k in range(len(apiType)):
        for i in range(len(accTemp)):
            cookie = accTemp[i]["cookie"]
            userInfo = accTemp[i]
            # 设置cookie
            nickname = accTemp[i]["nickname"]
            areaId = accTemp[i]["areaId"]
            jd.setHeaders(cookie)
            try:
                # 选择接口进行监控
                if apiType[k] == "JD":
                    proList = jd.watchInventory(areaId)

                    if isRisk("JD", proList, userInfo):
                        continue
                    skuInfo = proList["data"]
                else:
                    # res = jd.setRedis(areaId)
                    #
                    # if isRisk("JX", res, userInfo):
                    #     continue
                    proList = jd.watchInventoryJx()

                    if isRisk("JX", proList, userInfo):
                        continue
                    skuData = proList["data"]["skuInfo"]

                    # jx接口没有筛选功能，自行筛选出有效数据
                    skuInfo = []
                    for item in range(len(skuData)):
                        if skuData[item]["hasStock"] == 1 and skuData[item]["isShelves"] == 1:
                            skuInfo.append(skuData[item])

                # 判断提示过的商品是否下架，如果下架就将提示状态进行修改
                for j in range(len(watchList)):
                    if not watchList[j]["isTip"]:
                        hasStock = True
                        for x in range(len(skuInfo)):
                            skuId_name = "commId" if apiType == "JD" else "skuId"
                            if watchList[j]["skuId"] == skuInfo[x][skuId_name]:
                                hasStock = False
                                break
                        if hasStock:
                            lock.acquire()
                            watchList[j]["isTip"] = True
                            lock.release()

                # 判断是否请求成功
                if proList["iRet"] == "0":
                    if len(skuInfo) != 0:
                        isOrder(skuInfo, apiType[k])
                    else:
                        util.reLog(f"【{apiType[k]}】无有货的商品！来自账号：{nickname}")
                else:
                    util.reLog("【{}】接口返回异常：{}".format(nickname, proList["errMsg"]))
            except Exception as e:
                util.reLog(f"【{nickname}】监控异常报错：{e}")

            time.sleep(2)


def isOrder(proList, apiType):
    """
    是否符合下单条件，符合便开始下单
    commStatus＝1是上架，0是下架          isShelves
    hasStock＝1是有货，0是无货            hasStock
    commOrderStatus＝1是预约状态（抢购预约），0是普通商品（非预约非秒杀）   isYuShou
    :param apiType: 调用的API类型，jd  jx
    :param proList: 监控返回的商品收藏列表数据
    :return:
    """
    for j in range(len(proList)):
        try:
            data = proList[j]
            if apiType == "JD":
                # 下单条件
                IS = data["commStatus"] == "1" and data["hasStock"] == 1 and data["commOrderStatus"] == "0"
                proId = data["commId"]
                proName = data["commTitle"]
                # 商品分类ID
                cat = data["commCategory"].replace(";", ",")
            else:
                IS = data["hasStock"] == 1 and data["isShelves"] == 1 and data["isYuShou"] == 0
                proId = data["skuId"]
                proName = data["goodsName"]
                # 商品分类ID
                cat = data["goodsCategory"].replace(";", ",")

            # 满足上架、有货、普通商品条件
            if IS:
                for y in range(len(watchList)):
                    # 符合监控列表数据的条件
                    if proId == watchList[y]["skuId"]:
                        # 是否提示并下单
                        if watchList[y]["isTip"]:
                            lock.acquire()
                            watchList[y]["isTip"] = False
                            lock.release()
                            # 获取详情页的库存状态
                            detailsStock = rgs(proId, accountList, cat, data["venderId"])
                            if detailsStock != 34:
                                item = f"{proName},有货了啦！库存状态：{detailsStock}\n商品链接：https://item.m.jd.com/product/{proId}.html"
                                Exe.submit(sm.send_ding_msg, item)
                                util.reLog(item)
                                # sm.send_ding_msg(item)
                                commitOrder(watchList[y])
                            else:
                                util.reLog(f"【{apiType}】【{proName}】不符合下单条件！详情库存状态：{detailsStock}")
                        else:
                            util.reLog(f"【{apiType}】【{proName}】已提示并下过一次单,不再重复提示与下单！")
            else:
                util.reLog(f"【{apiType}】【{proName}】不符合下单条件！收藏夹库存状态：{IS}")
        except Exception as e:
            util.reLog(f"确认订单报错：{traceback.format_exc()}")

        time.sleep(1)


def commitOrder(watchData):
    """
    确认下单
    :return:
    """
    for x in range(len(accountList)):
        # jd.setHeaders(accountList[x]["cookie"])
        # jd.orderAction(watchData, accountList[x])
        # 多线程
        # Thread(target=jd.orderAction, args=(watchData, accountList[x])).start()
        Exe.submit(jd.orderAction, watchData, accountList[x])


def terminate_thread(thread):
    """
    强制kill 线程
    :param thread:
    :return:
    """
    if not thread.isAlive():
        return

    exc = ctypes.py_object(SystemExit)
    res = ctypes.pythonapi.PyThreadState_SetAsyncExc(
        ctypes.c_long(thread.ident), exc)
    if res == 0:
        raise ValueError("nonexistent thread id")
    elif res > 1:
        ctypes.pythonapi.PyThreadState_SetAsyncExc(thread.ident, None)
        raise SystemError("PyThreadState_SetAsyncExc failed")


def watchDog():
    """
    看门狗
    :return:
    """
    while True:
        now_time = int(time.time())
        if now_time - thread_Time > 60 * 4:
            threadList = threading.enumerate()
            for i in range(len(threadList)):
                if threadList[i].name == "watchInventory":
                    terminate_thread(threadList[i])
                    time.sleep(5)
                    Thread(target=watchInventory, name="watchInventory").start()
                    sm.send_wx_msg("线程假死，重启成功...")
                    time.sleep(10)
                    break
        # else:
        #     util.reLog(f"看门狗报告:时差{now_time - thread_Time}s")
        time.sleep(10)


if __name__ == "__main__":
    Thread(target=setIntervalAccount).start()
    time.sleep(1)
    Thread(target=setIntervalWatch).start()
    time.sleep(5)
    Thread(target=getCollectList).start()
    time.sleep(5)
    Thread(target=setIntervalCollect).start()
    time.sleep(5)
    Thread(target=watchInventory, name="watchInventory").start()
    watchDog()

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
