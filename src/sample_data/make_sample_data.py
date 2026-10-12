#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成脱敏示例订单样本（纯示例数据，非真实用户数据）。

设计原则：
  - 固定随机种子 42，**完全可复现**：任何人重跑都得到字节级一致的 orders.json
  - 餐品名、门店名、时段节奏均为公开可见的麦当劳常规信息，不含任何用户标识
  - 生成结果固化到 sample_data/orders.json，运行时不再执行本脚本

用法：
    python make_sample_data.py
"""
import json
import os
import random
from datetime import date, datetime, timedelta

SEED = 42
YEAR = 2026
START = date(YEAR, 1, 1)
END = date(2026, 10, 12)          # 数据截止日（与报告生成日一致）

# 用户画像：深圳罗湖的程序员，早餐 + 深夜麦乐送重度用户
RND = random.Random(SEED)

STORES = [
    ("4403001", "深圳罗湖东门店", "东门步行街"),
    ("4403002", "深圳罗湖翠竹路店", "翠竹路"),
    ("4403003", "深圳罗湖莲塘村店", "莲塘"),
    ("4403004", "深圳罗湖水贝店", "水贝"),
    ("4403005", "深圳罗湖笋岗店", "笋岗"),
]

# 餐品池：name, category, price
MENU = [
    ("巨无霸套餐", "汉堡", 29.0),
    ("巨无霸", "汉堡", 13.5),
    ("麦辣鸡腿堡套餐", "汉堡", 30.5),
    ("麦辣鸡腿堡", "汉堡", 14.5),
    ("板烧鸡腿堡套餐", "汉堡", 28.5),
    ("板烧鸡腿堡", "汉堡", 13.0),
    ("麦香鸡", "汉堡", 11.5),
    ("吉士汉堡套餐", "汉堡", 21.5),
    ("双层吉士堡", "汉堡", 15.5),
    ("麦香鱼", "汉堡", 13.5),
    ("猪扒包", "汉堡", 8.5),
    ("大薯条", "小食", 12.0),
    ("中薯条", "小食", 9.5),
    ("薯饼（6块）", "小食", 8.5),
    ("麦辣鸡翅（3只）", "小食", 25.0),
    ("麦乐鸡（6块）", "小食", 16.5),
    ("麦乐鸡（4块）", "小食", 12.5),
    ("麦旋风（原味）", "甜品", 13.5),
    ("麦旋风（华夫筒）", "甜品", 17.0),
    ("麦旋风（奥利奥）", "甜品", 18.0),
    ("麦旋风（抹茶）", "甜品", 18.0),
    ("新地（草莓）", "甜品", 11.5),
    ("可口可乐中杯", "饮品", 8.5),
    ("可口可乐零度", "饮品", 9.5),
    ("橙汁", "饮品", 10.5),
    ("柠檬茶", "饮品", 12.0),
    ("卡布奇诺", "饮品", 18.5),
    ("拿铁", "饮品", 19.5),
    ("燕麦拿铁", "饮品", 23.0),
    ("冰美式", "饮品", 16.5),
    ("吉士蛋麦满分套餐", "早餐", 18.5),
    ("猪柳蛋麦满分套餐", "早餐", 20.5),
    ("猪柳蛋麦满分", "早餐", 11.0),
    ("吉士蛋麦满分", "早餐", 9.5),
    ("双层猪柳蛋麦满分", "早餐", 12.5),
    ("麦满分套餐（吉士蛋）", "早餐", 19.5),
    ("麦香鱼早餐套餐", "早餐", 22.5),
    ("热豆浆", "饮品", 7.5),
    ("开心乐园餐（麦乐鸡4块）", "套餐", 32.5),
    ("巨无霸双层套餐", "汉堡", 35.5),
    ("麦辣鸡腿堡+麦旋风套餐", "套餐", 38.5),
]

CHANNELS = [("麦乐送", 45), ("到店堂食", 27), ("到店自取", 16), ("得来速", 12)]
CH_NAMES = [c for c, _ in CHANNELS]
CH_W = [w for _, w in CHANNELS]

# 券类型：(名称, 折扣, 使用概率)
COUPONS = [
    ("周一会员日 9.9 超值早餐", 9.9, 0.85),
    ("满 30 减 8 元券", 8.0, 0.55),
    ("麦辣鸡腿堡 立减 6 元", 6.0, 0.45),
    ("新品尝鲜 5 折券", 10.5, 0.30),
    ("麦乐送免配送费券", 6.0, 0.70),
    ("麦旋风立减 5 元", 5.0, 0.50),
]


def _anchor(d, hour, minute, items, coupon=("", 0.0), channel="麦乐送"):
    """锚点订单：精确指定餐品，用于制造报告里的高光时刻。"""
    raw = sum(p[2] for p in items)
    discount = round(min(coupon[1], raw * 0.5), 1)
    paid = round(raw - discount, 1)
    store = RND.choice(STORES)
    return {
        "orderId": "%s%s" % (YEAR, d.strftime("%m%d%H%M%S"))[-16:],
        "createTime": "%04d-%02d-%02d %02d:%02d:00" % (d.year, d.month, d.day, hour, minute),
        "storeCode": store[0],
        "storeName": store[1],
        "channel": channel,
        "items": [{"name": p[0], "category": p[1], "qty": 1, "price": p[2]} for p in items],
        "couponName": coupon[0],
        "discount": discount,
        "paid": paid,
        "pointEarned": int(paid),
    }


def _order_for(d, tag=None):
    """按日期与画像节奏造一单。tag 用于强制指定场景。"""
    store = RND.choice(STORES)

    hour, minute, pool, channel = None, None, None, None
    if tag == "深夜":
        hour = RND.randint(21, 23) + (1 if RND.random() < 0.4 else 0)
        hour = hour - 24 if hour >= 24 else hour
        minute = RND.randint(0, 59)
        channel = "麦乐送"
        pool = [m for m in MENU if m[1] in ("汉堡", "小食", "套餐", "饮品", "甜品")]
    elif tag == "早餐":
        hour = 6 + RND.randint(0, 1)
        minute = RND.randint(20, 55)
        channel = RND.choice(["麦乐送", "到店堂食", "得来速"])
        pool = [m for m in MENU if m[1] == "早餐"]
    elif tag == "下午茶":
        hour = RND.randint(14, 16)
        minute = RND.randint(0, 59)
        channel = RND.choice(["麦乐送", "到店堂食"])
        pool = [m for m in MENU if m[1] in ("甜品", "饮品", "小食")]
    else:
        r = RND.random()
        if r < 0.36:                                              # 早餐（用户主场景）
            hour, minute = 7 + RND.randint(0, 1), RND.randint(15, 55)
            pool = [m for m in MENU if m[1] == "早餐"] + \
                   [m for m in MENU if m[1] == "饮品"
                    and "咖啡" not in m[0] and "拿铁" not in m[0]]
            channel = RND.choice(["麦乐送", "到店堂食", "得来速"])
        elif r < 0.66:                                            # 午餐
            hour, minute = 11 + RND.randint(0, 2), RND.randint(0, 59)
            pool = [m for m in MENU if m[1] in ("汉堡", "小食", "套餐", "饮品")]
        elif r < 0.82:                                            # 下午茶
            hour, minute = 14 + RND.randint(0, 2), RND.randint(0, 59)
            pool = [m for m in MENU if m[1] in ("甜品", "饮品", "小食")]
            channel = RND.choice(["麦乐送", "到店堂食"])
        else:                                                     # 晚餐 / 夜宵
            hour, minute = 17 + RND.randint(0, 4), RND.randint(0, 59)
            pool = [m for m in MENU if m[1] in ("汉堡", "小食", "套餐", "饮品", "甜品")]

    if channel is None:
        channel = RND.choices(CH_NAMES, weights=CH_W, k=1)[0]

    # 一单 1-4 件
    n = RND.choice([1, 1, 2, 2, 2, 3, 3, 4])
    picked = []
    seen = set()
    for _ in range(n):
        m = RND.choice(pool)
        if m[0] in seen:
            continue
        seen.add(m[0])
        picked.append(m)
    if not picked:
        picked = [pool[0]]

    raw = sum(p[2] for p in picked)

    # 用券（约 42% 订单用券）
    coupon_name, discount = "", 0.0
    if RND.random() < 0.42:
        c = RND.choice(COUPONS)
        # 只在该券语义匹配时生效：早餐券仅早餐，麦旋风券仅甜品
        name_join = "".join(p[0] for p in picked)
        ok = True
        if "早餐" in c[0] and "早餐" not in name_join:
            ok = False
        if "麦旋风" in c[0] and "麦旋风" not in name_join:
            ok = False
        if "满 30" in c[0] and raw < 30:
            ok = False
        if "配送费" in c[0] and channel != "麦乐送":
            ok = False
        if ok:
            coupon_name, discount = c[0], min(c[1], round(raw * 0.45, 1))

    paid = round(raw - discount, 1)
    # 麦当劳积分：1 元 ≈ 1 积分（部分商品 1.2 倍），向下取整
    point = int(paid)

    ts = datetime(d.year, d.month, d.day, hour, minute)
    return {
        "orderId": "%s%s" % (YEAR, d.strftime("%m%d%H%M%S"))[-16:],
        "createTime": ts.strftime("%Y-%m-%d %H:%M:%S"),
        "storeCode": store[0],
        "storeName": store[1],
        "channel": channel,
        "items": [{"name": p[0], "category": p[1], "qty": RND.choice([1, 1, 1, 2]),
                   "price": p[2]} for p in picked],
        "couponName": coupon_name,
        "discount": discount,
        "paid": paid,
        "pointEarned": point,
    }


def main():
    # 主波次：1-10 月，平均每 3-4 天一单；春节前后稀疏，暑期加密
    ANCHOR_DAYS = {date(2026, 3, 2), date(2026, 5, 16), date(2026, 7, 19), date(2026, 8, 15)}
    orders, d = [], START
    while d <= END:
        if d in ANCHOR_DAYS:                     # 锚点日期由下方单独编排，避免同日重复
            d += timedelta(days=1)
            continue
        # 下单概率：暑期(7/8月)与开学季(3/9月)更密，春节(2月)与长假稀疏
        if d.month in (7, 8):
            p = 0.74
        elif d.month in (3, 9):
            p = 0.64
        elif d.month == 2:
            p = 0.32
        else:
            p = 0.58
        if RND.random() < p:
            orders.append(_order_for(d))
            d += timedelta(days=RND.randint(1, 3))
        else:
            d += timedelta(days=RND.randint(2, 4))

    # 高光锚点：保证报告有戏剧性数据点（最贵一单 / 最深夜宵 / 单日连击）
    FEAST = [
        ("巨无霸套餐", "汉堡", 29.0),
        ("巨无霸双层套餐", "汉堡", 35.5),
        ("麦辣鸡腿堡+麦旋风套餐", "套餐", 38.5),
        ("开心乐园餐（麦乐鸡4块）", "套餐", 32.5),
        ("麦旋风（华夫筒）", "甜品", 17.0),
        ("大薯条", "小食", 12.0),
    ]
    orders.append(_anchor(date(2026, 8, 15), 12, 30, FEAST,
                          ("满 30 减 8 元券", 8.0), "到店堂食"))   # 暑期亲子聚餐（年度最贵）
    orders.append(_order_for(date(2026, 3, 2), "深夜"))             # 加班凌晨单
    orders.append(_order_for(date(2026, 5, 16), "深夜"))             # 加班夜宵
    orders.append(_order_for(date(2026, 8, 15), "早餐"))            # 8/15 一天三单
    orders.append(_order_for(date(2026, 8, 15), "下午茶"))
    orders.append(_order_for(date(2026, 7, 19), "下午茶"))          # 暑期周末连击
    orders.append(_order_for(date(2026, 7, 19), "深夜"))

    # 保证数据末尾不断更：最后一单距截止日超过 7 天则补一单
    if orders:
        last = date.fromisoformat(sorted(o["createTime"] for o in orders)[-1][:10])
        if (END - last).days > 7:
            orders.append(_order_for(END - timedelta(days=RND.randint(1, 4)), "下午茶"))

    orders.sort(key=lambda o: o["createTime"])

    out = {
        "schema": "mcd-wrapped-sample/v1",
        "note": "示例数据，非任何真实用户的订单。由 make_sample_data.py 固定种子 42 生成，可完全复现。",
        "profile": {"city": "深圳", "cityCode": "4403", "persona": "程序员 · 早餐+夜宵重度用户"},
        "generatedAt": datetime(2026, 10, 12, 15, 0).strftime("%Y-%m-%d %H:%M"),
        "range": {"from": START.strftime("%Y-%m-%d"), "to": END.strftime("%Y-%m-%d")},
        "orders": orders,
    }
    dst = os.path.join(os.path.dirname(os.path.abspath(__file__)), "orders.json")
    with open(dst, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print("wrote %s  (%d orders)" % (dst, len(orders)))


if __name__ == "__main__":
    main()
