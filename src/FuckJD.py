import requests
from utils import util
from urllib import parse
import json
from operator import methodcaller
import random


class FuckJD(object):
    def __init__(self):
        self.session = requests.session()
        self.header = {
            "User-Agent": "",
            "cookie": ""
        }

    def setHeaders(self, cookie):
        self.header["User-Agent"] = util.get_random_useragent()
        self.header["cookie"] = cookie

    def favCommAdd(self, skuId, cookie):
        """
        添加商品到收藏
        :param cookie:
        :param skuId:
        :return:
        """
        url = "https://wq.jd.com/fav/comm/FavCommAdd?commId={}&sceneval=2".format(skuId)
        header = {
            "User-Agent": util.get_random_useragent(),
            "cookie": cookie,
            "referer": "https://item.m.jd.com/"
        }
        res = self.session.get(url, headers=header)
        if res.status_code == 200:
            resJson = res.json()
            if resJson["iRet"] == 0:
                util.reLog(f"将{skuId}加入收藏成功！")
            else:
                util.reLog("错误：{}".format(resJson["errMsg"]))

    def favCommDel(self, skuId, cookie):
        """
        取消收藏商品
        :param cookie:
        :param skuId:
        :return:
        """
        url = "https://wq.jd.com/fav/comm/FavCommDel?commId={}&sceneval=2".format(skuId)
        header = {
            "User-Agent": util.get_random_useragent(),
            "cookie": cookie,
            "referer": "https://item.m.jd.com/"
        }
        res = self.session.get(url, headers=header)

        if res.status_code == 200:
            resJson = res.json()
            if int(resJson["iRet"]) == 0:
                util.reLog("取消收藏成功".format(resJson["errMsg"]))
            else:
                util.reLog("错误：{}".format(resJson["errMsg"]))

    def favCommBatchDel(self, skuIds, cookie):
        """
        批量取消收藏商品
        :param cookie:
        :param skuIds:
        :return:
        """
        url = "https://wq.jd.com/fav/comm/FavCommBatchDel?commId={}&sceneval=2".format(skuIds)
        header = {
            "User-Agent": util.get_random_useragent(),
            "cookie": cookie,
            "referer": "https://wqs.jd.com/"
        }
        res = self.session.get(url, headers=header)

        if res.status_code == 200:
            resJson = res.json()
            if resJson["iRet"] == "0":
                util.reLog("批量取消收藏成功".format(resJson["errMsg"]))
            else:
                util.reLog("错误：{}".format(resJson["errMsg"]))

    def orderAction(self, proInfo, accInfo):
        """
        打开直链，相当于创建订单
        :param accInfo:
        :param proInfo:
        :return:
        """
        url = "https://p.m.jd.com/norder/order.action?wareId={}&wareNum={}&enterOrder=true".format(proInfo["skuId"],
                                                                                                   proInfo["buyNum"])
        ua = util.get_random_useragent()
        header = {
            "User-Agent": ua,
            "cookie": accInfo["cookie"]
        }
        res = self.session.get(url, headers=header)
        if res.status_code == 200:
            util.reLog("{} 正在生成订单...".format(accInfo["username"]))
            self.orderConfirm(proInfo, accInfo, header)

    def orderConfirm(self, proInfo, accInfo, header):
        """
        确认订单
        :param header:
        :param accInfo: 账号
        :param proInfo: 商品ID
        :return:
        """
        username = accInfo["username"]
        goodName = proInfo["goodName"]
        url = "https://wq.jd.com/deal/msubmit/confirm?skulist={}".format(proInfo["skuId"])
        header["referer"] = "https://p.m.jd.com/"
        try:
            res = self.session.get(url, headers=header)
            if res.status_code == 200:
                # 有时候返回的json数据会在"fatherType"字段后多一个逗号，导致抛出异常。
                jsonStr = util.remove_redundant_comma(res.text)
                resJson = json.loads(jsonStr)

                if resJson["errId"] == "0":
                    msg = f"【{username}】下单成功！商品名称：{goodName}订单编号：{resJson['dealId']},订单金额：{int(resJson['totalPrice']) / 100},耗时：{res.elapsed.total_seconds()}"
                    util.reLog(msg)
                    sm.send_sql_msg(username, msg)
                    sm.send_wx_msg(msg)
                else:
                    content = f"【{username}】下单接口异常：{resJson['errMsg']},耗时：{res.elapsed.total_seconds()}"
                    util.reLog(content)
                    sm.send_sql_log(content)
            else:
                util.reLog("【】确认订单接口状态异常：".format(res.status_code))
        except Exception as e:
            util.reLog("确认订单异常：{}".format(e))

    def watchInventory(self, areaId, stock=1):
        url = "https://wq.jd.com/fav/comm/FavCommQueryFilter"
        data = {
            "cp": 1,
            "pageSize": 20,
            "category": 0,
            "promote": 0,
            "cutPrice": 0,
            "coupon": 0,
            "stock": stock,  # 筛选有库存的 1有
            "areaNo": areaId,
            "sceneval": 2,
            "g_login_type": 1,
            "callback": "jsonpCBKD",
            "g_ty": "ls"
        }
        self.header["referer"] = "https://wqs.jd.com/my/fav/goods_fav.shtml"
        params = parse.urlencode(data)
        res = requests.get(url, params, headers=self.header, timeout=5)
        if res.status_code == 200:
            resJson = json.loads(res.text[14:-13])
            return resJson

    def watchInventoryJx(self, stock=1):
        """
        惊喜收藏夹接口
        :return:
        """
        url = "https://m.jingxi.com/fav/comm/QueryUserFavSkuInfo"
        data = {
            "cp": 1,
            "pageSize": 20,
            "offlineDown": 1,
            "noStockDown": stock,
            "category": 0,
            "skuName": "",
            "promote": 0,
            "orderReduce": 0,
            "buy": 0,
            "sceneval": 2,
            "g_login_type": 1,
            "callback": "jsonpCBKD",
            "g_ty": "ls"
        }
        self.header["Referer"] = "https://st.jingxi.com/my/fav.shtml"
        params = parse.urlencode(data)
        res = requests.get(url, params, headers=self.header, timeout=5)
        if res.status_code == 200:
            resJson = res.text
            return json.loads(resJson[14:-13])

    def setRedis(self, areaId):
        """
        jx接口设置地区
        :return:
        """
        url = "https://wq.jd.com/deal/recvaddr/SetRedis"
        data = {
            "key": "wq_addr",
            "value": "0|{}|_||".format(areaId),
            "callersource": "h5commom_addr",
            "sceneval": 2,
            "g_login_type": 1,
            "g_ty": "ajax"
        }
        self.header["referer"] = "https://item.m.jd.com/"
        params = parse.urlencode(data)
        res = requests.get(url, params, headers=self.header)
        if res.status_code == 200:
            return res.json()


class Stock:
    """
    获取库存状态的接口合集
    """

    def __init__(self):
        self.header = {
            "user-agent": ""
        }

    def setHeader(self):
        self.header["user-agent"] = util.get_random_useragent()

    def getStock_getWareBusiness(self, skuId, areaId):
        url = f"https://item-soa.jd.com/getWareBusiness?callback=stockCallbackA&skuId={skuId}&area={areaId}"
        header = self.header
        header["referer"] = "https://item-soa.jd.com/getWareBusiness"
        res = requests.get(url, headers=header).text
        resJson = json.loads(res[15:-1])
        return resJson["stockInfo"]["stockState"]

    def getStock_mview2(self, skuId, areaId):
        url = f"https://item.m.jd.com/item/mview2?datatype=1&callback=stockCallbackA&cgi_source=mitem&sku={skuId}&_fd=jdm"
        header = self.header
        header["referer"] = f"https://item.m.jd.com/product/{skuId}.html"
        header["cookie"] = f"wq_addr=0%7C{areaId}%7C_%7C%7C;"
        res = requests.get(url, headers=header).text
        # print(res)
        # 替换掉特殊字符
        res = res.replace('\\x', '')

        resJson = json.loads(res[15:-2])
        return resJson["stock"]["StockState"]

    def getStock_waview(self, skuId, areaId):
        area = areaId.replace("_", "-")
        url = f"https://wqitem.jd.com/item/waview?sku={skuId}&areaid={area}&callback=stockCallbackA"
        res = requests.get(url, headers=self.header).text
        # 替换掉特殊字符
        res = res.replace('\\x', '')
        resJson = json.loads(res[15:-2])
        return resJson["stock"]["StockState"]

    def getStock_skuDescribe(self, skuId, areaId):
        url = f"https://wq.jd.com/commodity/skudescribe/get?command=3&source=wqm_cpsearch&priceinfo=1&buynums=1&skus={skuId}&area={areaId}&callback=stockCallbackA"
        res = requests.get(url, headers=self.header).text
        resJson = json.loads(res[15:-3])
        return int(resJson["stockstate"]["data"][skuId]["a"])

    def getStock_stock(self, skuId, areaId, cat, vId):
        url = f"https://cd.jd.com/stock?callback=stockCallbackA&buyNum=1&ch=2&sceneval=2&skuId={skuId}&venderId={vId}&cat={cat}&area={areaId}"
        header = self.header
        header["referer"] = f"https://item.m.jd.com/product/{skuId}.html"
        res = requests.get(url, headers=header).text
        resJson = json.loads(res[15:-1])
        # print(f"接口：stock,内容：{resJson}")
        return resJson["stock"]["StockState"]

    def getStock_c3stock(self, skuId, areaId, cat, vId):
        url = f"https://c.3.cn/stock?skuId={skuId}&venderId={vId}&cat={cat}&area={areaId}&buyNum=1&callback=stockCallbackA"
        header = self.header
        header["referer"] = f"https://item.m.jd.com/product/{skuId}.html"
        res = requests.get(url, headers=header).text
        resJson = json.loads(res[15:-1])
        # print(f"接口：c3,内容：{resJson}")
        return resJson["stock"]["StockState"]

    def getStock_c03stock(self, skuId, areaId, cat, vId):
        url = f"https://c0.3.cn/stock?skuId={skuId}&venderId={vId}&cat={cat}&area={areaId}&buyNum=1&callback=stockCallbackA"
        header = self.header
        header["referer"] = f"https://item.m.jd.com/product/{skuId}.html"
        res = requests.get(url, headers=header).text
        resJson = json.loads(res[15:-1])
        # print(f"接口：c03,内容：{resJson}")
        return resJson["stock"]["StockState"]

    def getStock_h5draw(self, skuId, cookie):
        url = f"https://wq.jd.com/itemv3/h5draw?sku={skuId}&isJson=1&source=h5v3&g_login_type=1&g_ty=ajax"
        header = self.header
        header["cookie"] = cookie
        try:
            res = requests.get(url, headers=self.header).json()
            return res["domain"]["data"]["skuInfo"]["stockState"]
        except Exception as e:
            util.reLog(f"通过cookie获取详情库存报错：{e}")


class SendMessage(object):
    def __init__(self):
        pass

    @staticmethod
    def send_wx_msg(msg):
        url = "http://wxpusher.zjiecode.com/api/send/message"
        header = {
            "content-type": "application/json;charset=UTF-8"
        }
        data = {
            "appToken": "AT_bqId9U6YS5QDtNqKbTlmbvUxeMm1G5H7",
            "content": msg,
            # "summary": "消息摘要",   消息摘要，显示在微信聊天页面或者模版消息卡片上，限制长度100，可以不传，不传默认截取content前面的内容。
            "contentType": 1,  # 内容类型 1表示文字  2表示html(只发送body标签内部的数据即可，不包括body标签) 3表示markdown
            # "topicIds": [123],  # 发送目标的topicId，是一个数组！！！，也就是群发，使用uids单发的时候， 可以不传。
            "uids": [
                "UID_EpR7ha6Wwc1bn71ktiUPze0BIMEw"
            ],  # 发送目标的UID，是一个数组。注意uids和topicIds可以同时填写，也可以只填写一个。
            # "url": "http://wxpusher.zjiecode.com"  # 原文链接，可选参数
        }

        requests.post(url, json=data, headers=header).json()

    def send_sql_msg(self, username, content):
        url = "http://api.posthub.top/api/addMessage"
        data = {
            "AppName": "FuckJD",
            "username": username,
            "phone": username,
            "ip": self.getIp(),
            "content": content
        }
        requests.post(url, json=data).json()

    @staticmethod
    def send_sql_log(content):
        url = "http://api.posthub.top/api/ph/jdErrLog"
        data = {
            "content": content
        }
        requests.post(url, json=data).json()

    @staticmethod
    def getIp():
        import re
        url = "http://pv.sohu.com/cityjson"
        res = requests.get(url).text

        p = r'(?:(?:[0-1]?\d?\d|2[0-4]\d|25[0-5])\.){3}(?:(?:[0,1]?\d?\d|2[0-4]\d|25[0-5]))'
        ip = re.findall(p, res)

        return ip[0]

    @staticmethod
    def send_ding_msg(msg):
        url = "http://api.posthub.top/api/ding/msgPush"
        header = {"content-type": "application/json;charset=utf-8"}
        data = {"content": msg}
        requests.post(url, json=data, headers=header)


stock = Stock()


def randomGetStock(skuId, accont, cat, vId):
    """
    从库存接口合集中任意获取一个库存
    # 40 配货
    # 34 无货
    # 33 有货
    :param skuId:
    :param areaId:
    :param cat:
    :param vId:
    :return: 返回库存状态ID，如33
    """
    index = random.randint(0, len(accont) - 1)
    areaId = accont[index]["areaId"]
    cookie = accont[index]["cookie"]
    funcList = [
        methodcaller('getStock_getWareBusiness', skuId, areaId),
        methodcaller('getStock_mview2', skuId, areaId),
        methodcaller('getStock_waview', skuId, areaId),
        methodcaller('getStock_skuDescribe', skuId, areaId),
        methodcaller('getStock_stock', skuId, areaId, cat, vId),
        methodcaller('getStock_c3stock', skuId, areaId, cat, vId),
        methodcaller('getStock_c03stock', skuId, areaId, cat, vId),
    ]
    # 调用一个
    stock.setHeader()
    f = random.choice(funcList)
    try:
        state = f(stock)
    except Exception as e:
        state = stock.getStock_h5draw(skuId, cookie)
        util.reLog(f"查询详情页库存报错：{e}，错误接口：{f},重新请求后状态：{state}")
    return state


jd = FuckJD()
sm = SendMessage()
