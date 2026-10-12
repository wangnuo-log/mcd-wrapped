#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""麦麦年报 · 命令行入口。

用法
----
    # 用内置脱敏示例数据出 HTML 报告
    python wrapped_cli.py --html -o docs/demo.html

    # 打印统计 JSON（供调试 / 校验）
    python wrapped_cli.py --json

    # 用自己的订单数据（JSON 数组，字段见 wrapped_engine.normalize）
    python wrapped_cli.py --orders my_orders.json --html -o report.html

    # 指定仓库地址，在报告末尾生成 Star 转化位
    python wrapped_cli.py --html -o report.html \\
        --repo https://github.com/wangnuo-log/mcd-wrapped
"""
import argparse
import json
import sys

from wrapped_engine import analyze_orders, build_report
from wrapped_html import render_wrapped_html

DEFAULT_REPO = "https://github.com/wangnuo-log/mcd-wrapped"
DEFAULT_RADAR = "https://github.com/wangnuo-log/mcd-activity-radar"


def build_parser():
    p = argparse.ArgumentParser(
        prog="wrapped_cli",
        description="麦麦年报：把你的麦当劳订单变成一份可分享的年度复盘报告。",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="示例数据由 make_sample_data.py 固定种子 42 生成，可完全复现。")
    p.add_argument("--json", action="store_true",
                   help="打印统计结果 JSON 到 stdout（调试用）")
    p.add_argument("--html", action="store_true",
                   help="生成单文件 HTML 报告")
    p.add_argument("-o", "--out",
                   help="HTML 输出路径；省略则输出到 stdout")
    p.add_argument("--orders", metavar="PATH",
                   help="自定义订单 JSON（数组或含 orders 键的对象）；"
                        "省略则用内置脱敏示例数据")
    p.add_argument("--profile", metavar="JSON",
                   help="用户画像 JSON 字符串，如 '{\"city\":\"深圳\"}'")
    p.add_argument("--generated-at", metavar="YYYY-MM-DD HH:MM",
                   help="报告生成时间戳（默认取当前时间）")
    p.add_argument("--repo", default=DEFAULT_REPO, help="仓库地址，用于 Star 转化位")
    p.add_argument("--radar", default=DEFAULT_RADAR,
                   help="姊妹项目活动雷达地址")
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)

    if args.orders:
        with open(args.orders, "r", encoding="utf-8") as f:
            data = json.load(f)
        orders = data["orders"] if isinstance(data, dict) else data
        profile = json.loads(args.profile) if args.profile else {}
        report = analyze_orders(orders, profile=profile)
    else:
        report = build_report()

    from datetime import datetime
    if args.generated_at:
        report["meta"]["generated_at"] = args.generated_at

    if args.json:
        payload = json.dumps(report, ensure_ascii=False, indent=2)
        if args.out:
            with open(args.out, "w", encoding="utf-8") as f:
                f.write(payload)
            print("wrote %s  (%d bytes, %d orders)"
                  % (args.out, len(payload.encode("utf-8")), report["meta"]["orders"]))
        else:
            sys.stdout.write(payload + "\n")
    if args.html:
        html = render_wrapped_html(report, repo_url=args.repo, radar_url=args.radar)
        if args.out:
            with open(args.out, "w", encoding="utf-8") as f:
                f.write(html)
            print("wrote %s  (%d bytes, %d orders)"
                  % (args.out, len(html.encode("utf-8")), report["meta"]["orders"]))
        else:
            sys.stdout.write(html)

    if not args.json and not args.html:
        t = report["totals"]
        print("麦麦年报 %s" % report["meta"]["range_from"][:4])
        print("  订单 %d 单 · 合计 ¥%s · 笔均 ¥%s"
              % (t["orders"], t["total_paid"], t["avg_paid"]))
        print("  人格 %s（命中 %d/%d 条规则）"
              % (report["persona"]["label"], report["persona"]["rule_hits"],
                 report["persona"]["rule_total"]))
        print("  使用 --html -o out.html 生成完整报告")


if __name__ == "__main__":
    main()
