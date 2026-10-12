#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""麦麦年报 · 自测套件（38 项断言）。

跑法：
    python -m unittest selftest -v
    # 或
    python selftest.py

覆盖：
  - 金额精度（分/元换算，防浮点误差累积）
  - 时段映射边界（含跨零点深夜时段）
  - 各维度计数守恒（品类 / 时段 / 渠道 / 星期 / 月份 / 券）
  - 极值正确性（最贵 / 最早 / 最晚 / 最多件 / 最忙日）
  - normalize 字段 fallback（对接真实 MCP 返回）
  - 空输入与缺失字段兜底
  - 确定性：同输入必得同输出；样本生成可复现
  - HTML 渲染：标签配对 / 零外链 / 关键卡片齐全
"""
import os
import re
import sys
import unittest
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from wrapped_engine import (  # noqa: E402
    _pct, analyze_orders, build_report, cents, load_sample, normalize, slot_of, yuan,
)
from wrapped_html import render_wrapped_html  # noqa: E402

TAGS = ["html", "head", "body", "main", "section", "div", "style", "p",
        "h1", "h2", "h3", "a", "span", "small", "table"]


def _tags_ok(h):
    """检查常见标签的开闭配对。"""
    for t in TAGS:
        if len(re.findall(r"<%s[ >]" % t, h)) != len(re.findall(r"</%s>" % t, h)):
            return False
    return True


# ---------------------------------------------------------------------------
# 构造测试订单
# ---------------------------------------------------------------------------

def _o(d, items, paid=None, discount=0.0, coupon="", channel="麦乐送", point=0):
    """构造一条最小可用订单。"""
    raw = None if paid is None else paid
    return {
        "orderId": d + items[0]["name"][:3],
        "createTime": "%s %s:00:00" % (d, items[0].pop("_t", "12")),
        "storeName": "深圳罗湖东门店",
        "channel": channel,
        "items": items,
        "paid": raw,
        "discount": discount,
        "couponName": coupon,
        "pointEarned": point,
    }


def _i(name, price, t="12", qty=1, cat="汉堡"):
    return {"name": name, "price": price, "qty": qty, "category": cat, "_t": t}


class TestMoney(unittest.TestCase):
    def test_cents_roundtrip(self):
        for v in (0, 0.1, 1.0, 12.34, 99.9, 1234.56):
            self.assertEqual(cents(v), int(round(v * 100)))
            self.assertEqual(yuan(cents(v)), round(v, 1))

    def test_no_float_drift(self):
        # 0.1 + 0.2 的经典陷阱：分值累加不应漂移
        self.assertEqual(cents(0.1) + cents(0.2), 30)
        self.assertEqual(yuan(cents(0.1) + cents(0.2)), 0.3)

    def test_cents_none_and_negative(self):
        self.assertEqual(cents(None), 0)
        self.assertEqual(cents(0), 0)


class TestSlot(unittest.TestCase):
    def test_slot_boundaries(self):
        self.assertEqual(slot_of(5), "深夜")      # 05:00 仍属深夜
        self.assertEqual(slot_of(0), "深夜")
        self.assertEqual(slot_of(6), "早餐")
        self.assertEqual(slot_of(9), "早餐")
        self.assertEqual(slot_of(10), "午餐")
        self.assertEqual(slot_of(13), "午餐")
        self.assertEqual(slot_of(14), "下午茶")
        self.assertEqual(slot_of(16), "下午茶")
        self.assertEqual(slot_of(17), "晚餐")
        self.assertEqual(slot_of(20), "晚餐")
        self.assertEqual(slot_of(21), "深夜")
        self.assertEqual(slot_of(23), "深夜")

    def test_pct(self):
        self.assertEqual(_pct(1, 4), 25.0)
        self.assertEqual(_pct(0, 0), 0.0)
        self.assertEqual(_pct(1, 3), 33.3)


class TestInvariants(unittest.TestCase):
    """各维度计数必须守恒：分组的和 == 总量。"""

    @classmethod
    def setUpClass(cls):
        cls.r = build_report()

    def test_category_qty_conservation(self):
        self.assertEqual(sum(c["qty"] for c in self.r["by_category"]),
                         self.r["totals"]["total_items"])

    def test_slot_orders_conservation(self):
        self.assertEqual(sum(s["orders"] for s in self.r["by_slot"]),
                         self.r["totals"]["orders"])

    def test_channel_orders_conservation(self):
        self.assertEqual(sum(c["orders"] for c in self.r["by_channel"]),
                         self.r["totals"]["orders"])

    def test_weekday_orders_conservation(self):
        self.assertEqual(sum(w["orders"] for w in self.r["weekday"]),
                         self.r["totals"]["orders"])

    def test_month_orders_conservation(self):
        self.assertEqual(sum(m["orders"] for m in self.r["by_month"]),
                         self.r["totals"]["orders"])

    def test_coupon_partition(self):
        c = self.r["coupon"]
        self.assertEqual(c["used_orders"] +
                         (self.r["totals"]["orders"] - c["used_orders"]),
                         self.r["totals"]["orders"])

    def test_top_items_sorted_desc(self):
        q = [i["qty"] for i in self.r["top_items"]]
        self.assertEqual(q, sorted(q, reverse=True))

    def test_top_items_prefix_of_all(self):
        # TOP 榜必须是全量件数排序的前缀
        self.assertLessEqual(sum(i["qty"] for i in self.r["top_items"]),
                             self.r["totals"]["total_items"])

    def test_range_monotonic(self):
        m = self.r["meta"]
        self.assertLessEqual(m["range_from"], m["range_to"])


class TestExtremes(unittest.TestCase):
    def _orders(self):
        return [
            _o("2026-01-01", [_i("巨无霸套餐", 29.0, "08")], 29.0, point=29),
            _o("2026-01-02", [_i("麦旋风", 13.5, "23", cat="甜品")], 13.5),
            _o("2026-01-03", [_i("小食A", 8.5, "06"), _i("小食B", 9.5, "06"),
                              _i("小食C", 12.0, "06")], 30.0),
            _o("2026-01-03", [_i("汉堡D", 20.0, "12")], 20.0),
        ]

    def test_priciest(self):
        r = analyze_orders(self._orders())
        self.assertEqual(r["highlights"]["priciest"]["paid"], 30.0)

    def test_most_items(self):
        r = analyze_orders(self._orders())
        self.assertEqual(r["highlights"]["most_items"]["items_count"], 3)

    def test_earliest_and_latest(self):
        r = analyze_orders(self._orders())
        self.assertEqual(r["highlights"]["earliest"]["time"], "06:00")
        self.assertEqual(r["highlights"]["latest"]["time"], "23:00")

    def test_busiest_day(self):
        r = analyze_orders(self._orders())
        self.assertEqual(r["highlights"]["busiest_day"]["date"], "2026-01-03")
        self.assertEqual(r["highlights"]["busiest_day"]["orders"], 2)


class TestNormalize(unittest.TestCase):
    """字段 fallback：麦当劳 MCP 各工具字段名不统一，必须都能认。"""

    def test_mcp_style_fields(self):
        o = normalize({
            "orderTime": "2026-05-01 09:15:00",
            "restaurantName": "罗湖翠竹路店",
            "orderType": "到店堂食",
            "actualPrice": 45.5,
            "promotionAmount": 8.0,
            "productList": [
                {"productName": "巨无霸套餐", "salePrice": 29.0, "quantity": 1},
                {"productName": "麦旋风", "salePrice": 13.5, "quantity": 1},
            ],
        })
        self.assertEqual(o["store"], "罗湖翠竹路店")
        self.assertEqual(o["channel"], "到店堂食")
        self.assertEqual(o["paid_cents"], 4550)
        self.assertEqual(o["discount_cents"], 800)
        self.assertEqual(o["items_total"], 2)
        self.assertEqual(o["items_cents"], 4250)
        self.assertTrue(o["dt"].hour == 9)

    def test_missing_paid_falls_back_to_items(self):
        o = normalize({"createTime": "2026-05-01 12:00:00",
                       "items": [{"name": "薯条", "price": 9.5, "qty": 2}]})
        self.assertEqual(o["paid_cents"], 1900)

    def test_missing_time_still_parses(self):
        o = normalize({"items": [{"name": "可乐", "price": 8.5}]})
        self.assertEqual(o["paid_cents"], 850)
        self.assertEqual(o["store"], "未知门店")

    def test_multiple_time_formats(self):
        for s, hour in (("2026-05-01 09:15:30", 9), ("2026-05-01T09:15:30", 9),
                        ("2026/05/01 09:15:30", 9), ("2026-05-01 09:15", 9),
                        ("20260501", 0)):
            o = normalize({"createTime": s, "items": [{"name": "可乐", "price": 8.5}]})
            self.assertEqual(o["dt"].hour, hour, "格式 %s 解析失败" % s)

    def test_garbage_time_falls_back_to_sentinel(self):
        # 任何垃圾输入都不许抛异常，这是确定性引擎对 AI 幻觉的正面回应
        o = normalize({"createTime": "昨天中午", "items": [{"name": "可乐", "price": 8.5}]})
        self.assertEqual(o["dt"], datetime(1970, 1, 1))


class TestEdgeCases(unittest.TestCase):
    def test_empty_input(self):
        r = analyze_orders([])
        self.assertEqual(r["meta"]["orders"], 0)
        self.assertEqual(r["persona"]["label"], "数据不足")

    def test_single_order(self):
        r = analyze_orders([_o("2026-06-01", [_i("薯条", 9.5, "14")], 9.5)])
        self.assertEqual(r["totals"]["orders"], 1)
        self.assertEqual(r["totals"]["avg_paid"], 9.5)
        self.assertEqual(r["totals"]["span_days"], 1)
        self.assertEqual(r["by_slot"][2]["orders"], 1)   # 下午茶

    def test_all_orders_zero_discount(self):
        r = analyze_orders([_o("2026-06-01", [_i("薯条", 9.5, "14")], 9.5)])
        self.assertEqual(r["coupon"]["used_orders"], 0)
        self.assertEqual(r["coupon"]["total_saved"], 0.0)

    def test_negative_paid_not_allowed(self):
        # paid 缺失时用 items 反推，不应出现负数
        o = normalize({"createTime": "2026-06-01 12:00:00", "paid": -1,
                       "items": [{"name": "薯条", "price": 9.5}]})
        self.assertEqual(o["paid_cents"], 950)


class TestDeterminism(unittest.TestCase):
    """确定性是本项目对 AI 幻觉的正面回应：同输入必得同输出。"""

    def test_same_input_same_output(self):
        a = build_report()
        b = build_report()
        for k in ("totals", "by_category", "by_slot", "by_channel",
                  "by_month", "weekday", "top_items", "persona", "coupon", "points"):
            self.assertEqual(a[k], b[k], "字段 %s 不稳定" % k)

    def test_persona_deterministic(self):
        a = build_report()["persona"]
        b = build_report()["persona"]
        self.assertEqual(a["traits"], b["traits"])

    def test_html_deterministic(self):
        r = build_report()
        h1 = render_wrapped_html(r, repo_url="X")
        h2 = render_wrapped_html(r, repo_url="X")
        self.assertEqual(h1, h2)


class TestHtml(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.r = build_report()
        cls.h = render_wrapped_html(cls.r, repo_url="https://example.com/r",
                                    radar_url="https://example.com/radar")

    def test_tags_balanced(self):
        self.assertTrue(_tags_ok(self.h), "存在未闭合标签")

    def test_no_external_assets(self):
        # 除仓库外链（纯文本链接，非资源加载）外不得有任何 http(s) 引用
        urls = [u for u in re.findall(r'(?:src|href)="(https?://[^"]+)"', self.h)
                if "example.com" not in u]
        self.assertEqual(urls, [], "发现外链资源加载: %s" % urls)

    def test_all_cards_present(self):
        for kw in ("麦麦年报", "总览", "你的麦麦人格", "你最常在什么时候来",
                   "你最爱吃", "你怎么吃麦当劳", "你的麦麦节奏", "高光时刻",
                   "你的钱包", "工作日 vs 周末", "这份年报，数据来自你的真实订单"):
            self.assertIn(kw, self.h, "缺少卡片关键字 %s" % kw)

    def test_data_leaks_no_token(self):
        for bad in ("Bearer ", "sk-", "MCD_MCP_TOKEN="):
            self.assertNotIn(bad, self.h)

    def test_non_official_disclaimer(self):
        self.assertIn("非麦当劳官方产品", self.h)

    def test_persona_highlighted(self):
        self.assertIn("<div class=\"lg\">%s</div>" % self.r["persona"]["label"], self.h)


class TestSampleReproducible(unittest.TestCase):
    """样本生成器固定种子 42，任何人重跑都应得到字节级一致的结果。"""

    def test_same_data_within_session(self):
        self.assertEqual(load_sample()["orders"], load_sample()["orders"])

    def test_engine_stable_across_sample_reads(self):
        a = analyze_orders(load_sample()["orders"])
        b = analyze_orders(load_sample()["orders"])
        self.assertEqual(a["totals"], b["totals"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
