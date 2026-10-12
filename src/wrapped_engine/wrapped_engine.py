"""麦麦年报 · 确定性统计引擎（纯标准库，零第三方依赖）。

设计原则
--------
1. **确定性**：同样的输入永远得到同样的输出，无任何随机性与浮点误差累积
   （金额一律用 int 分计算，最后再转元）。
2. **不靠大模型算**：分组、计数、占比、极值全部是查表 + 累加，可单元测试。
3. **数据源可替换**：``normalize()`` 做多字段名 fallback，直接对接
   麦当劳 MCP ``order-list`` / ``mall-order-list`` 的真实返回，
   引擎主体不需要改一行。

用法
----
    from wrapped_engine import analyze_orders, load_sample
    report = analyze_orders(load_sample()["orders"])
"""
import json
import os
from collections import Counter, defaultdict
from datetime import datetime

# ---------------------------------------------------------------------------
# 常量：时段 / 品类 / 人格标签规则
# ---------------------------------------------------------------------------

# (名称, 起, 止)；深夜跨零点，起止允许 hour_end < hour_start
SLOTS = [
    ("早餐", 6, 10),
    ("午餐", 10, 14),
    ("下午茶", 14, 17),
    ("晚餐", 17, 21),
    ("深夜", 21, 6),
]
SLOT_DESC = {
    "早餐": "06:00–10:00",
    "午餐": "10:00–14:00",
    "下午茶": "14:00–17:00",
    "晚餐": "17:00–21:00",
    "深夜": "21:00–次日 06:00",
}
CATEGORY_ORDER = ["汉堡", "小食", "甜品", "饮品", "早餐", "套餐", "开心乐园餐"]
WEEKDAY_CN = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
CHANNELS_CN = ["麦乐送", "到店堂食", "到店自取", "得来速"]


def slot_of(hour):
    """把小时映射到时段名。深夜时段跨零点（21:00–05:59）。"""
    for name, start, end in SLOTS:
        if end > start and start <= hour < end:
            return name
        if end < start and (hour >= start or hour < end):
            return name
    return "深夜"


def cents(amount):
    """元 -> 分，用 int 避免浮点误差累积。"""
    if amount is None:
        return 0
    return int(round(float(amount) * 100))


def yuan(cents_):
    """分 -> 元，保留一位小数。"""
    return round(cents_ / 100.0, 1)


def _pct(n, total):
    return round(n * 100.0 / total, 1) if total else 0.0


# ---------------------------------------------------------------------------
# 数据归一化：对接真实 MCP 返回的防御性字段映射
# ---------------------------------------------------------------------------

# MCP 各版本 / 各工具字段名不统一，按优先级逐个尝试
_F_KEYS = {
    "time": ["createTime", "orderTime", "gmtCreate", "orderCreateTime", "placedTime"],
    "store": ["storeName", "restaurantName", "store", "restaurant"],
    "channel": ["channel", "orderType", "dineType", "businessType", "deliveryType"],
    "paid": ["paid", "actualPrice", "actualAmount", "totalPaid", "payAmount"],
    "discount": ["discount", "promotionAmount", "couponAmount", "savedAmount"],
    "coupon": ["couponName", "couponDesc", "couponTitle", "promotionName"],
    "items": ["items", "productList", "goodsList", "orderItems", "details"],
    "item_name": ["name", "productName", "goodsName", "spuName", "itemName"],
    "item_price": ["price", "salePrice", "itemPrice", "amount"],
    "item_qty": ["qty", "quantity", "count", "num"],
    "point": ["pointEarned", "point", "integral", "gainPoint"],
    "order_id": ["orderId", "orderNo", "id", "tradeNo"],
}


def _parse_dt(s):
    """解析订单时间。支持 ISO 与常见中文格式，失败回落到哨兵时间。

    真实 MCP 返回的字段名与格式可能因工具版本不同而变化，引擎必须
    在任何输入下都不崩溃——这是确定性工具与"大模型心算"的分水岭。
    """
    s = str(s).strip().replace("T", " ")
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y/%m/%d %H:%M:%S",
                "%Y-%m-%d", "%Y%m%d"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    return datetime(1970, 1, 1)      # 哨兵：缺失或不可解析，绝不抛异常


def _first(d, keys):
    for k in keys:
        v = d.get(k)
        if v not in (None, ""):
            return v
    return None


def normalize(order):
    """把一条原始订单（MCP 返回或样本）归一化成引擎内部结构。

    返回::

        {
          "order_id": str, "dt": datetime, "store": str, "channel": str,
          "items": [{"name","category","qty","cents"}],
          "paid_cents": int, "discount_cents": int, "coupon": str,
          "point": int, "items_total": int, "items_cents": int
        }
    """
    raw_items = _first(order, _F_KEYS["items"]) or []
    items = []
    for it in raw_items:
        name = _first(it, _F_KEYS["item_name"]) or "未命名餐品"
        qty = int(_first(it, _F_KEYS["item_qty"]) or 1)
        items.append({
            "name": str(name),
            "category": it.get("category") or "其他",
            "qty": qty,
            "cents": cents(_first(it, _F_KEYS["item_price"]) or 0),
        })
    paid_cents = cents(_first(order, _F_KEYS["paid"]))
    if paid_cents <= 0 and items:                     # 兜底：按餐品合计反推
        paid_cents = sum(i["cents"] * i["qty"] for i in items)

    t = str(_first(order, _F_KEYS["time"]) or "")
    dt = _parse_dt(t)

    return {
        "order_id": str(_first(order, _F_KEYS["order_id"]) or t),
        "dt": dt,
        "store": str(_first(order, _F_KEYS["store"]) or "未知门店"),
        "channel": str(_first(order, _F_KEYS["channel"]) or "未标注"),
        "items": items,
        "paid_cents": paid_cents,
        "discount_cents": cents(_first(order, _F_KEYS["discount"])),
        "coupon": str(_first(order, _F_KEYS["coupon"]) or ""),
        "point": int(_first(order, _F_KEYS["point"]) or 0),
        "items_total": sum(i["qty"] for i in items),
        "items_cents": sum(i["cents"] * i["qty"] for i in items),
    }


# ---------------------------------------------------------------------------
# 样本加载
# ---------------------------------------------------------------------------

def load_sample(path=None):
    """读取脱敏示例订单样本（``sample_data/orders.json``）。"""
    if path is None:
        # src/wrapped_engine/ -> src/sample_data/orders.json
        path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                            "sample_data", "orders.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# 统计主入口
# ---------------------------------------------------------------------------

def analyze_orders(raw_orders, profile=None, generated_at=None):
    """把一组原始订单统计成年报字典。"""
    orders = [normalize(o) for o in raw_orders]
    orders.sort(key=lambda o: o["dt"])
    n = len(orders)
    if n == 0:
        return {"meta": {"orders": 0}, "totals": {}, "by_category": [],
                "by_slot": [], "by_channel": [], "by_month": [], "top_items": [],
                "highlights": {}, "coupon": {}, "points": {},
                "persona": {"label": "数据不足", "traits": []}, "weekday": []}

    # ---- 总览 ----
    total_cents = sum(o["paid_cents"] for o in orders)
    total_items = sum(o["items_total"] for o in orders)
    first_dt, last_dt = orders[0]["dt"], orders[-1]["dt"]
    span = max((last_dt.date() - first_dt.date()).days, 1)
    weeks = span / 7.0
    first_store = orders[0]["store"]

    totals = {
        "orders": n,
        "total_paid": yuan(total_cents),
        "total_items": total_items,
        "avg_paid": yuan(round(total_cents / n)),
        "avg_items": round(total_items * 1.0 / n, 1),
        "first_order": first_dt.strftime("%Y-%m-%d"),
        "last_order": last_dt.strftime("%Y-%m-%d"),
        "first_store": first_store,
        "span_days": span,
        "avg_per_week": round(n * 7.0 / span, 2),
        "busiest_store": _top_key(orders, "store")[0],
        "store_count": len(set(o["store"] for o in orders)),
    }

    # ---- 品类分布（按餐品件数与金额）----
    cat_qty, cat_amt = Counter(), defaultdict(int)
    item_qty, item_amt = Counter(), defaultdict(int)
    for o in orders:
        for it in o["items"]:
            cat_qty[it["category"]] += it["qty"]
            cat_amt[it["category"]] += it["cents"] * it["qty"]
            item_qty[it["name"]] += it["qty"]
            item_amt[it["name"]] += it["cents"] * it["qty"]
    item_total_qty = sum(item_qty.values())
    by_category = []
    for c in CATEGORY_ORDER + [x for x in cat_qty if x not in CATEGORY_ORDER]:
        if c not in cat_qty:
            continue
        by_category.append({
            "name": c,
            "qty": cat_qty[c],
            "pct": _pct(cat_qty[c], item_total_qty),
            "amount": yuan(cat_amt[c]),
        })
    by_category.sort(key=lambda x: -x["qty"])

    top_items = [{"name": k, "qty": v, "amount": yuan(item_amt[k])}
                 for k, v in item_qty.most_common(8)]

    # ---- 时段分布 ----
    slot_ct = Counter(slot_of(o["dt"].hour) for o in orders)
    by_slot = [{"name": s[0], "hours": SLOT_DESC[s[0]],
                "orders": slot_ct[s[0]], "pct": _pct(slot_ct[s[0]], n)}
               for s in SLOTS]

    # ---- 渠道 ----
    ch_ct = Counter(o["channel"] for o in orders)
    ch_amt = defaultdict(int)
    for o in orders:
        ch_amt[o["channel"]] += o["paid_cents"]
    by_channel = [{"name": k, "orders": v, "pct": _pct(v, n),
                   "amount": yuan(ch_amt[k])}
                  for k, v in ch_ct.most_common()]

    # ---- 月份趋势 ----
    m_ct, m_amt = Counter(), defaultdict(int)
    for o in orders:
        m_ct[o["dt"].month] += 1
        m_amt[o["dt"].month] += o["paid_cents"]
    by_month = [{"month": m, "orders": m_ct[m], "amount": yuan(m_amt[m])}
                for m in sorted(m_ct)]

    # ---- 星期分布 ----
    w_ct = Counter(o["dt"].weekday() for o in orders)
    w_amt = defaultdict(int)
    for o in orders:
        w_amt[o["dt"].weekday()] += o["paid_cents"]
    weekday = [{"name": WEEKDAY_CN[i], "orders": w_ct[i],
                "amount": yuan(w_amt[i]), "pct": _pct(w_ct[i], n)}
               for i in range(7)]
    weekend_orders = w_ct[5] + w_ct[6]

    # ---- 优惠券 ----
    used = [o for o in orders if o["discount_cents"] > 0]
    saved_cents = sum(o["discount_cents"] for o in used)
    cp_ct = Counter(o["coupon"] for o in used if o["coupon"])
    coupon = {
        "used_orders": len(used),
        "usage_rate": _pct(len(used), n),
        "total_saved": yuan(saved_cents),
        "avg_saved": yuan(round(saved_cents / len(used))) if used else 0.0,
        "top": {"name": cp_ct.most_common(1)[0][0], "count": cp_ct.most_common(1)[0][1]}
              if cp_ct else None,
    }
    # 用券单 vs 未用券单的平均实付对比（衡量"薅羊毛"是否划算）
    unused = [o for o in orders if o["discount_cents"] == 0]
    coupon["avg_paid_used"] = yuan(round(sum(o["paid_cents"] for o in used) / len(used))) \
        if used else 0.0
    coupon["avg_paid_unused"] = yuan(round(sum(o["paid_cents"] for o in unused) / len(unused))) \
        if unused else 0.0

    # ---- 高光时刻 ----
    priciest = max(orders, key=lambda o: o["paid_cents"])
    latest = max(orders, key=lambda o: o["dt"].hour + o["dt"].minute / 60.0)
    early = min(orders, key=lambda o: o["dt"].hour + o["dt"].minute / 60.0)
    most_items = max(orders, key=lambda o: o["items_total"])
    day_ct = Counter(o["dt"].date() for o in orders)
    busiest_day = day_ct.most_common(1)[0]

    def _snap(o):
        return {
            "date": o["dt"].strftime("%Y-%m-%d"),
            "time": o["dt"].strftime("%H:%M"),
            "paid": yuan(o["paid_cents"]),
            "store": o["store"],
            "channel": o["channel"],
            "items": "、".join("%s×%d" % (i["name"], i["qty"]) if i["qty"] > 1
                              else i["name"] for i in o["items"]),
            "items_count": o["items_total"],
        }

    highlights = {
        "priciest": _snap(priciest),
        "latest": _snap(latest),
        "earliest": _snap(early),
        "most_items": _snap(most_items),
        "busiest_day": {"date": busiest_day[0].isoformat(),
                        "orders": busiest_day[1],
                        "amount": yuan(sum(o["paid_cents"] for o in orders
                                           if o["dt"].date() == busiest_day[0])),
                        "weekday": WEEKDAY_CN[busiest_day[0].weekday()]},
    }

    # ---- 积分 ----
    points = {
        "earned": sum(o["point"] for o in orders),
        "per_order": round(sum(o["point"] for o in orders) * 1.0 / n, 1),
    }

    # ---- 人格标签（确定性规则打分）----
    bp = {s["name"]: s["pct"] for s in by_category}
    sp = {s["name"]: s["pct"] for s in by_slot}
    cpp = {c["name"]: c["pct"] for c in by_channel}
    big_orders = sum(1 for o in orders if o["paid_cents"] >= 5000)
    wangbao_count = sum(q for name, q in item_qty.items() if "巨无霸" in name)

    # 阈值调优：让标签更易命中且互相区分，共 12 条确定性规则
    rules = [
        ("早餐信徒", sp.get("早餐", 0) >= 28, sp.get("早餐", 0)),
        ("夜宵麦门", sp.get("深夜", 0) >= 10, sp.get("深夜", 0)),
        ("宅家麦乐送", cpp.get("麦乐送", 0) >= 32, cpp.get("麦乐送", 0)),
        ("现制派", cpp.get("到店堂食", 0) >= 28, cpp.get("到店堂食", 0)),
        ("得来速党", cpp.get("得来速", 0) >= 10, cpp.get("得来速", 0)),
        ("巨无霸死忠", wangbao_count >= 8, wangbao_count),
        ("甜品控", bp.get("甜品", 0) >= 10, bp.get("甜品", 0)),
        ("咖啡党", bp.get("饮品", 0) >= 22, bp.get("饮品", 0)),
        ("薅羊毛大师", coupon["usage_rate"] >= 25, coupon["usage_rate"]),
        ("周末战士", _pct(weekend_orders, n) >= 40, _pct(weekend_orders, n)),
        ("大额玩家", _pct(big_orders, n) >= 12, _pct(big_orders, n)),
        ("高频麦门", totals["avg_per_week"] >= 1.5, totals["avg_per_week"]),
    ]
    traits = [(name, score) for name, hit, score in rules if hit]
    traits.sort(key=lambda x: -x[1])

    persona = {
        "label": traits[0][0] if traits else "均衡麦粉",
        "traits": traits,
        "rule_hits": len(traits),
        "rule_total": len(rules),
    }

    meta = {
        "generated_at": (generated_at or datetime.now()).strftime("%Y-%m-%d %H:%M"),
        "range_from": totals["first_order"],
        "range_to": totals["last_order"],
        "orders": n,
        "profile": profile or {},
    }

    return {
        "meta": meta,
        "totals": totals,
        "by_category": by_category,
        "by_slot": by_slot,
        "by_channel": by_channel,
        "by_month": by_month,
        "weekday": weekday,
        "top_items": top_items,
        "highlights": highlights,
        "coupon": coupon,
        "points": points,
        "persona": persona,
    }


def _top_key(items, field):
    c = Counter(o[field] for o in items)
    return c.most_common(1)[0]


def build_report(path=None, generated_at=None):
    """一步到位：读样本 -> 统计 -> 返回年报字典。"""
    data = load_sample(path)
    return analyze_orders(data["orders"],
                          profile=data.get("profile"),
                          generated_at=generated_at)


if __name__ == "__main__":
    import pprint
    pprint.pprint(build_report(), width=110, sort_dicts=False)
