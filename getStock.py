import requests
import random
import json
from operator import methodcaller


# 调用函数的九种方法
# https://zhuanlan.zhihu.com/p/359505439
# https://blog.csdn.net/lly1122334/article/details/115971862

class Stock:
    def __init__(self):
        self.header = {
            "user-agent": "Mozilla/5.0 (Linux; Android 10; HarmonyOS; WLZ-AL10; HMSCore 6.2.0.302) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.105 HuaweiBrowser/12.0.0.301 Mobile Safari/537.36",
            "referer": "https://item.m.jd.com/product/100021318944.html"
        }

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
        return resJson["stockstate"]["data"][skuId]["a"]

    def getStock_stock(self, skuId, areaId, cat, vId):
        url = f"https://cd.jd.com/stock?callback=stockCallbackA&buyNum=1&ch=2&sceneval=2&skuId={skuId}&venderId={vId}&cat={cat}&area={areaId}"

        res = requests.get(url, headers=self.header).text
        resJson = json.loads(res[15:-1])
        return resJson["stock"]["StockState"]

    def getStock_c3stock(self, skuId, areaId, cat, vId):
        url = f"https://c.3.cn/stock?skuId={skuId}&venderId={vId}&cat={cat}&area={areaId}&buyNum=1&callback=stockCallbackA"
        res = requests.get(url, headers=self.header).text
        resJson = json.loads(res[15:-1])
        return resJson["stock"]["StockState"]

    def getStock_c03stock(self, skuId, areaId, cat, vId):
        url = f"https://c0.3.cn/stock?skuId={skuId}&venderId={vId}&cat={cat}&area={areaId}&buyNum=1&callback=stockCallbackA"
        res = requests.get(url, headers=self.header).text
        resJson = json.loads(res[15:-1])
        return resJson["stock"]["StockState"]

    def getStock_h5draw(self, skuId, cookie):
        url = f"https://wq.jd.com/itemv3/h5draw?sku={skuId}&isJson=1&source=h5v3&g_login_type=1&g_ty=ajax"
        header = self.header
        header["cookie"] = cookie
        res = requests.get(url, headers=self.header).json()
        return res["domain"]["data"]["skuInfo"]["stockState"]


# 40 配货
# 34 无货
# 33 有货
skuId = "100006843633"
areaId = "18_1482_48936_53640"
cat = "9987,653,655"
vId = "1000003443"
cookie = "pt_key=AAJhieSyADB2kEClnYoAybp7sxxPQteMcBQUcMqBz1qC5e5xJd0A6Gdj9d63vl7TtE-ZqfUUAmU;cid=9;"
s = Stock()
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
# print(random.choice(funcList)(s))

# print(s.getStock_getWareBusiness(skuId, areaId))
# print(s.getStock_mview2(skuId, areaId))
# print(s.getStock_waview(skuId, areaId))
# print(s.getStock_skuDescribe(skuId, areaId))
# print(s.getStock_stock(skuId, areaId, cat, vId))
# print(s.getStock_c3stock(skuId, areaId, cat, vId))
# print(s.getStock_c03stock(skuId, areaId, cat, vId))
# s.getStock_h5draw(skuId, cookie)
