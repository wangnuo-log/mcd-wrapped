"""麦麦年报 · 麦当劳品牌风格 HTML 渲染器（单文件、零外部依赖）。

产出**单文件 HTML**：样式与脚本全部内联，双击即可打开，可直接部署到
GitHub Pages 作为在线 demo。

设计约定
--------
  - 麦当劳品牌色：主红 #DA291C（McRed） + 金黄 #FFC72C（Golden Arches）+ 白/暖米白底
  - 明亮卡片 + 金色拱门装饰 + 薯条条纹分隔：贴合麦当劳 App 的视觉语言
  - 竖屏卡列（max-width 460px）：手机截图即为一张社交图
  - 所有图形均为 CSS/SVG 自绘，**不使用麦当劳官方 Logo**，仅取配色基因
  - 关键色对比度符合 WCAG AA（正文 #1A1A1A on #FFF）

用法
----
    from wrapped_engine import build_report
    from wrapped_html import render_wrapped_html
    html = render_wrapped_html(build_report())
"""
import html as _html


def esc(s):
    return _html.escape("" if s is None else str(s), quote=True)


def _arcs_svg(size="150", cls="arcs"):
    """自绘金色拱门（双弧），呼应品牌 Golden Arches 意象，纯 SVG。"""
    return (
        '<svg class="%s" viewBox="0 0 100 80" xmlns="http://www.w3.org/2000/svg" '
        'width="%s" height="%s" fill="none" aria-hidden="true">'
        '<path d="M6 76 C 6 14, 42 14, 50 76" stroke="#FFC72C" stroke-width="13" '
        'stroke-linecap="round"/>'
        '<path d="M50 76 C 58 14, 94 14, 94 76" stroke="#FFC72C" stroke-width="13" '
        'stroke-linecap="round"/>'
        '</svg>' % (cls, size, size)
    )


def _fry_divider():
    """薯条条纹分隔线：11 根金色小柱，象征薯条盒。"""
    return ('<div class="fry-divider" aria-hidden="true">' +
            "".join("<i></i>" for _ in range(11)) + "</div>")


def _bar(pct, max_pct, color=None, delay=0):
    """自绘水平条形：pct 为占比，max_pct 用于视觉归一化。"""
    w = 0.0 if max_pct in (0, None) else min(100.0, pct * 100.0 / max_pct)
    col = color or "linear-gradient(90deg,var(--mcgold),#F5B800)"
    return ('<div class="bar"><div class="bar-f" style="width:%.2f%%;background:%s;'
            'animation-delay:%dms"></div></div>' % (w, col, delay))


def _cols(n, label, val):
    """自绘竖向柱：n 为数值，val 为最大值，用于月度趋势。"""
    h = 0.0 if val in (0, None) else max(5.0, n * 100.0 / val)
    return ('<div class="col-f" style="height:%.1f%%"><span>%.0f</span></div>'
            '<div class="col-l">%s</div>' % (h, n, label))


STYLE = """
:root{
  --mcred:#DA291C; --mcred-dark:#A31E14; --mcred-deep:#7A1610;
  --mcgold:#FFC72C; --mcgold-deep:#E0A800; --mcgold-soft:#FFF5D6;
  --ink:#1A1A1A; --ink-soft:#3A3A3A; --ink-mid:#6B6B6B; --ink-dim:#9A9A9A;
  --paper:#FFFFFF; --paper-warm:#FFFDF7; --paper-cool:#F7F5F0;
  --line:#EEEAE0; --line-soft:#F3EFE6;
  --shadow:0 6px 24px rgba(218,41,28,.06), 0 2px 6px rgba(0,0,0,.04);
}
*{box-sizing:border-box;margin:0;padding:0}
html{-webkit-text-size-adjust:100%}
body{
  font-family:"McDonaldland","Segoe UI",system-ui,-apple-system,"PingFang SC",
    "Microsoft YaHei",sans-serif;
  background:var(--paper-warm);color:var(--ink);line-height:1.55;
  -webkit-font-smoothing:antialiased;padding:22px 0 40px;
}
.wrap{max-width:460px;margin:0 auto;padding:0 14px;display:flex;flex-direction:column;gap:14px}
a{color:var(--mcred);text-decoration:none;font-weight:700}
a:hover{text-decoration:underline}

/* ---------- 卡片 ---------- */
.card{background:var(--paper);border:1px solid var(--line);border-radius:20px;
  padding:24px 22px;position:relative;overflow:hidden;box-shadow:var(--shadow)}
.card.tinted-red{background:linear-gradient(165deg,#FFE9E7 0%,#FFFFFF 55%)}
.card.tinted-gold{background:linear-gradient(165deg,#FFF5D6 0%,#FFFFFF 55%)}
.card.fire{background:linear-gradient(160deg,var(--mcred) 0%,#B71F14 60%,var(--mcred-deep) 100%);
  color:#FFF;border-color:transparent}
.kick{font-size:11.5px;letter-spacing:2.5px;color:var(--mcred);font-weight:800;
  margin-bottom:12px;text-transform:uppercase}
.kick.dim{color:var(--ink-mid)}
.tit{font-size:16px;font-weight:800;line-height:1.4;color:var(--ink)}
.sub{font-size:12.5px;color:var(--ink-mid);margin-top:8px;line-height:1.7}

/* ---------- 封面：红底金字 + 金色拱门 ---------- */
.hero{background:linear-gradient(170deg,#DA291C 0%,#B71F14 60%,#7A1610 100%);
  border:1px solid transparent;padding:34px 24px 28px;text-align:center;color:#FFF;
  box-shadow:0 12px 40px rgba(218,41,28,.32);border-radius:20px;
  position:relative;overflow:hidden}
.hero .arcs{position:absolute;top:-38px;right:-38px;width:170px;height:170px;opacity:.14}
.hero .lg{font-size:12px;letter-spacing:6px;color:var(--mcgold);font-weight:800;
  position:relative;z-index:1}
.hero h1{font-size:44px;font-weight:900;letter-spacing:1px;margin:12px 0 4px;line-height:1.1;
  position:relative;z-index:1;text-shadow:0 2px 8px rgba(0,0,0,.18)}
.hero .yr{color:var(--mcgold)}
.hero .tag{font-size:13.5px;color:#FFD9A0;margin-top:12px;position:relative;z-index:1}
.hero .tag b{color:var(--mcgold);font-weight:800}
.hero .rg{margin-top:20px;display:flex;justify-content:space-around;gap:8px;
  border-top:1px solid rgba(255,255,255,.22);padding-top:16px;position:relative;z-index:1}
.hero .rg div{font-size:11.5px;color:#FFD9A0}
.hero .rg b{display:block;font-size:17px;color:#fff;font-weight:800;
  font-variant-numeric:tabular-nums}

/* ---------- Hero 数字 ---------- */
.hero-num{text-align:center}
.hero-num .v{font-size:64px;font-weight:900;color:var(--mcred);letter-spacing:-2px;line-height:1;
  font-variant-numeric:tabular-nums}
.hero-num .v small{font-size:26px;font-weight:800;margin-right:2px;color:var(--mcgold-deep)}
.hero-num .l{font-size:13px;color:var(--ink-mid);margin-top:10px;letter-spacing:.5px}
.triplet{display:flex;justify-content:space-between;gap:8px;margin-top:20px;
  border-top:1px dashed var(--line);padding-top:18px}
.triplet>div{text-align:center;flex:1}
.triplet .n{font-size:24px;font-weight:900;color:var(--mcred);font-variant-numeric:tabular-nums}
.triplet .k{font-size:11px;color:var(--ink-mid);margin-top:4px}

/* ---------- 人格标签 ---------- */
.persona{text-align:center}
.persona .lb{font-size:11.5px;color:var(--ink-mid);letter-spacing:3px;font-weight:700;margin-bottom:10px}
.persona .lg{display:inline-block;background:linear-gradient(135deg,var(--mcgold),#F5B800);
  color:#1A1A1A;font-size:36px;font-weight:900;letter-spacing:2px;padding:16px 32px;
  border-radius:18px;line-height:1.1;box-shadow:0 10px 34px rgba(255,199,44,.36);
  border:3px solid #FFF;outline:2px solid var(--mcgold-deep);outline-offset:-6px}
.traits{display:flex;flex-wrap:wrap;gap:7px;justify-content:center;margin-top:20px}
.tr{background:#FFF;border:1.5px solid var(--mcgold);border-radius:999px;
  padding:7px 13px;font-size:12.5px;font-weight:700;display:flex;align-items:center;gap:6px;
  color:var(--ink-soft)}
.tr i{font-style:normal;font-size:11px;color:var(--mcred);font-variant-numeric:tabular-nums;font-weight:800}
.hint{font-size:11.5px;color:var(--ink-mid);text-align:center;margin-top:16px;line-height:1.7}

/* ---------- 条形 ---------- */
.rows{display:flex;flex-direction:column;gap:12px;margin-top:8px}
.row{display:flex;align-items:center;gap:10px}
.row .nm{width:74px;flex:0 0 74px;font-size:12.5px;font-weight:700;text-align:right;color:var(--ink-soft)}
.row .bar{flex:1;height:24px;background:var(--line-soft);border-radius:8px;overflow:hidden}
.row .bar-f{height:100%;border-radius:8px;animation:grow 1s cubic-bezier(.2,.8,.2,1) both;
  background:linear-gradient(90deg,var(--mcgold),#F5B800)}
.row .vv{width:70px;flex:0 0 70px;font-size:12px;color:var(--ink-mid);
  font-variant-numeric:tabular-nums}
@keyframes grow{from{width:0}}
.row.win .nm{color:var(--mcred);font-weight:800}
.row.win .bar-f{background:linear-gradient(90deg,var(--mcred),#B71F14)}

/* ---------- 柱状 ---------- */
.chart{display:flex;align-items:flex-end;gap:4px;justify-content:space-between;
  height:150px;padding:10px 2px 0}
.col{flex:1;min-width:0;display:flex;flex-direction:column;justify-content:flex-end;height:100%}
.col-f{background:linear-gradient(180deg,var(--mcgold),#E0A800);border-radius:6px 6px 2px 2px;
  position:relative;min-height:6px;animation:rise .8s cubic-bezier(.2,.8,.2,1) both}
.col-f span{position:absolute;left:0;right:0;top:-16px;text-align:center;font-size:10px;
  color:var(--ink-mid);font-variant-numeric:tabular-nums;font-weight:700}
.col-l{text-align:center;font-size:10px;color:var(--ink-mid);margin-top:6px}
.col.peak .col-f{background:linear-gradient(180deg,var(--mcred),#B71F14)}
.col.peak .col-l{color:var(--mcred);font-weight:800}
@keyframes rise{from{height:0}}

/* ---------- 高光卡（红底，白字）---------- */
.hl{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-top:16px}
.hl .it{background:rgba(255,255,255,.1);border:1px solid rgba(255,255,255,.2);
  border-radius:14px;padding:14px 15px;backdrop-filter:blur(4px)}
.hl .k{font-size:11px;color:var(--mcgold);font-weight:800;letter-spacing:1px}
.hl .v{font-size:22px;font-weight:900;margin-top:6px;font-variant-numeric:tabular-nums;line-height:1.2;color:#FFF}
.hl .d{font-size:11.5px;color:#FFD9A0;margin-top:6px;line-height:1.55}

/* ---------- 列表 ---------- */
.list{display:flex;flex-direction:column;gap:9px;margin-top:8px}
.li{display:flex;align-items:baseline;gap:12px;background:var(--paper-warm);
  border:1px solid var(--line);border-radius:12px;padding:12px 14px}
.li .rk{font-size:16px;font-weight:900;color:var(--mcred);width:24px;flex:0 0 24px;
  font-variant-numeric:tabular-nums}
.li .nm{flex:1;font-size:13px;font-weight:700;min-width:0;color:var(--ink)}
.li .vl{font-size:12.5px;color:var(--ink-mid);font-variant-numeric:tabular-nums;flex:0 0 auto;font-weight:600}

/* ---------- 数字网格 ---------- */
.grid4{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-top:8px}
.gc{background:var(--paper-warm);border:1px solid var(--line);border-radius:14px;padding:14px 15px}
.gc .n{font-size:26px;font-weight:900;color:var(--mcred);font-variant-numeric:tabular-nums;
  line-height:1.1}
.gc .k{font-size:11.5px;color:var(--ink-mid);margin-top:5px;line-height:1.5}

/* ---------- 时段环 ---------- */
.slots{display:flex;flex-direction:column;gap:10px;margin-top:8px}
.sl{display:flex;align-items:center;gap:10px}
.sl .hd{width:92px;flex:0 0 92px}
.sl .hd b{font-size:12.5px;font-weight:700;display:block;color:var(--ink)}
.sl .hd span{font-size:10px;color:var(--ink-dim)}
.sl .bar{flex:1;height:18px;background:var(--line-soft);border-radius:6px;overflow:hidden}
.sl .bar-f{height:100%;border-radius:6px;background:linear-gradient(90deg,var(--mcgold),#F5B800);
  animation:grow 1s cubic-bezier(.2,.8,.2,1) both}
.sl .vv{width:54px;flex:0 0 54px;text-align:right;font-size:12px;font-weight:800;
  font-variant-numeric:tabular-nums;color:var(--ink-soft)}

/* ---------- 薯条条纹分隔 ---------- */
.fry-divider{display:flex;gap:3px;justify-content:center;margin:8px 0 4px;opacity:.85}
.fry-divider i{width:5px;height:24px;background:var(--mcgold);border-radius:2px;
  box-shadow:inset 0 -4px 0 var(--mcgold-deep)}

/* ---------- 尾页 CTA（红底）---------- */
.cta{background:linear-gradient(160deg,#DA291C 0%,#B71F14 100%);color:#FFF;text-align:center;
  padding:28px 22px;border-radius:20px;box-shadow:0 12px 36px rgba(218,41,28,.28);
  border:1px solid transparent;position:relative;overflow:hidden}
.cta .arcs2{position:absolute;bottom:-46px;left:-32px;width:150px;height:150px;opacity:.16}
.cta h3{font-size:20px;font-weight:900;letter-spacing:.5px;position:relative;z-index:1}
.cta p{font-size:13px;margin-top:10px;line-height:1.75;color:#FFE9B8;position:relative;z-index:1}
.cta a{color:var(--mcgold);font-weight:800}
.cta .gold-btn{display:inline-block;margin-top:14px;background:var(--mcgold);color:#1A1A1A;
  font-weight:900;font-size:14px;padding:11px 22px;border-radius:999px;
  box-shadow:0 4px 14px rgba(0,0,0,.18);position:relative;z-index:1}
.foot{font-size:11px;color:var(--ink-dim);text-align:center;line-height:1.9;padding:0 14px}
.foot b{color:var(--ink-mid);font-weight:700}
.foot code{background:#EEEAE0;color:var(--ink-soft);padding:2px 7px;border-radius:5px;font-weight:600}
.badge{display:inline-block;font-size:10.5px;font-weight:800;padding:3px 10px;border-radius:999px;
  background:var(--mcgold);color:#1A1A1A;vertical-align:middle;margin-left:6px}
@media (prefers-reduced-motion:reduce){.bar-f,.col-f{animation:none}}
"""


def render_wrapped_html(report, repo_url="", radar_url=""):
    t = report["totals"]
    per = report["persona"]
    hl = report["highlights"]
    cp = report["coupon"]
    meta = report["meta"]
    year = meta["range_from"][:4]
    slot_max = max(s["pct"] for s in report["by_slot"])
    cat_max = max(c["pct"] for c in report["by_category"])
    mon_max = max(m["orders"] for m in report["by_month"])
    ch_max = max(c["pct"] for c in report["by_channel"])
    traits = per.get("traits") or []
    top_slot = max(report["by_slot"], key=lambda s: s["pct"])
    peak_month = max(report["by_month"], key=lambda m: m["orders"])

    L = ["<!DOCTYPE html>", '<html lang="zh-CN">', "<head>", '<meta charset="utf-8">',
         '<meta name="viewport" content="width=device-width,initial-scale=1">',
         "<title>麦麦年报 %s · 你和麦当劳的这一年</title>" % esc(year),
         '<meta name="description" content="麦麦年报：用你的麦当劳真实订单生成一份年度复盘报告，'
         '含消费画像、最爱餐品、高光时刻与人格标签。基于麦当劳 MCP 数据。">',
         "<style>%s</style>" % STYLE, "</head>", '<body>', '<main class="wrap">']

    # ---------------- 封面 ----------------
    L.append('<section class="hero">')
    L.append(_arcs_svg("170", "arcs"))
    L.append('<div class="lg">M C D &nbsp; W R A P P E D</div>')
    L.append('<h1>麦麦年报 <span class="yr">%s</span></h1>' % esc(year))
    L.append('<div class="tag">这一年，你和麦当劳的第 <b>%d</b> 次相遇</div>' % t["orders"])
    L.append('<div class="rg"><div>统计周期<b>%s</b></div>'
             '<div>覆盖门店<b>%d</b></div><div>常吃时段<b>%s</b></div></div>'
             % (esc(meta["range_from"][5:] + " ~ " + meta["range_to"][5:]),
                t["store_count"], esc(top_slot["name"])))
    L.append("</section>")

    # ---------------- 总览 hero ----------------
    L.append('<section class="card tinted-red hero-num">')
    L.append('<div class="kick">%s 总览</div>' % esc(year))
    L.append('<div class="v"><small>¥</small>%s</div>' % esc("%.0f" % t["total_paid"]))
    L.append('<div class="l">%d 天里，你一共为麦当劳花了这么多</div>' % t["span_days"])
    L.append(_fry_divider())
    L.append('<div class="triplet">'
             '<div><div class="n">%d</div><div class="k">笔订单</div></div>'
             '<div><div class="n">%d</div><div class="k">件餐品</div></div>'
             '<div><div class="n">¥%s</div><div class="k">笔均实付</div></div>'
             '</div>' % (t["orders"], t["total_items"], esc(t["avg_paid"])))
    L.append('<div class="sub">%s 起，每周平均 <b>%s</b> 单；最常去 %s。</div>'
             % (esc(t["first_order"]), esc(t["avg_per_week"]), esc(t["busiest_store"])))
    L.append("</section>")

    # ---------------- 人格标签 ----------------
    L.append('<section class="card tinted-gold persona">')
    L.append('<div class="lb">你的麦麦人格</div>')
    L.append('<div class="lg">%s</div>' % esc(per["label"]))
    L.append('<div class="traits">')
    for name, score in traits:
        L.append('<span class="tr">%s<i>%.0f</i></span>' % (esc(name), score))
    L.append("</div>")
    L.append('<div class="hint">人格标签由 <b>%d / %d</b> 条确定性规则判定，'
             '同输入必得同结果，不靠大模型猜测。<br>'
             '得分 = 该维度的真实占比或件数，可逐条核验。</div>' % (per["rule_hits"], per["rule_total"]))
    L.append("</section>")

    # ---------------- 时段 ----------------
    L.append('<section class="card">')
    L.append('<div class="kick">你最常在什么时候来</div>')
    L.append('<div class="tit">%s党，实锤了</div>' % esc(top_slot["name"]))
    L.append('<div class="slots">')
    for i, s in enumerate(report["by_slot"]):
        win = s["name"] == top_slot["name"]
        L.append('<div class="sl"><div class="hd"><b>%s</b><span>%s</span></div>'
                 '<div class="bar"><div class="bar-f" style="width:%.1f%%;animation-delay:%dms'
                 '%s"></div></div><div class="vv">%.1f%%</div></div>'
                 % (esc(s["name"]), esc(s["hours"]), s["pct"], i * 90,
                    ";background:var(--red)" if win else "", s["pct"]))
    L.append("</div>")
    L.append('<div class="sub">%s时段下了 <b>%d</b> 单，占全部订单的 <b>%.1f%%</b>。</div>'
             % (esc(top_slot["name"]), top_slot["orders"], top_slot["pct"]))
    L.append("</section>")

    # ---------------- 最爱餐品 ----------------
    L.append('<section class="card">')
    L.append('<div class="kick">你最爱吃</div>')
    L.append('<div class="tit">TOP %d 餐品</div>' % min(len(report["top_items"]), 6))
    L.append('<div class="list">')
    for i, it in enumerate(report["top_items"][:6]):
        L.append('<div class="li"><span class="rk">%02d</span>'
                 '<span class="nm">%s</span>'
                 '<span class="vl">×%d · ¥%s</span></div>'
                 % (i + 1, esc(it["name"]), it["qty"], esc(it["amount"])))
    L.append("</div>")
    L.append('<div class="sub">全年共 <b>%d</b> 件餐品，品类分布：</div>' % t["total_items"])
    L.append('<div class="rows">')
    for i, c in enumerate(report["by_category"][:6]):
        L.append('<div class="row"><span class="nm">%s</span>'
                 '<div class="bar"><div class="bar-f" style="width:%.1f%%;'
                 'background:var(--yel);animation-delay:%dms"></div></div>'
                 '<span class="vv">%d件 · %.1f%%</span></div>'
                 % (esc(c["name"]), c["pct"], i * 70, c["qty"], c["pct"]))
    L.append("</div></section>")

    # ---------------- 渠道 ----------------
    L.append('<section class="card">')
    L.append('<div class="kick">你怎么吃麦当劳</div>')
    top_ch = report["by_channel"][0]
    L.append('<div class="tit">%s是你的主场</div>' % esc(top_ch["name"]))
    L.append('<div class="rows">')
    for i, c in enumerate(report["by_channel"]):
        L.append('<div class="row"><span class="nm">%s</span>'
                 '<div class="bar"><div class="bar-f" style="width:%.1f%%;animation-delay:%dms'
                 'background:var(--yel);"></div></div>'
                 '<span class="vv">%d单 · ¥%s</span></div>'
                 % (esc(c["name"]), c["pct"], i * 80, c["orders"], esc(c["amount"])))
    L.append("</div></section>")

    # ---------------- 月度趋势 ----------------
    L.append('<section class="card">')
    L.append('<div class="kick">你的麦麦节奏</div>')
    L.append('<div class="tit">%d 月是你的高峰</div>' % peak_month["month"])
    L.append('<div class="chart">')
    for m in report["by_month"]:
        peak = " peak" if m["month"] == peak_month["month"] else ""
        L.append('<div class="col%s">%s</div>' % (peak,
                   _cols(m["orders"], "%d月" % m["month"], mon_max)))
    L.append("</div>")
    L.append('<div class="sub">%d 月下了 <b>%d</b> 单、花了 <b>¥%s</b>；'
             '最淡的是 %d 月，只有 <b>%d</b> 单。</div>'
             % (peak_month["month"], peak_month["orders"], esc(peak_month["amount"]),
                min(report["by_month"], key=lambda m: m["orders"])["month"],
                min(report["by_month"], key=lambda m: m["orders"])["orders"]))
    L.append("</section>")

    # ---------------- 高光时刻 ----------------
    L.append('<section class="card fire">')
    L.append(_arcs_svg("150", "arcs"))
    L.append('<div class="kick" style="color:var(--mcgold)">高光时刻</div>')
    L.append('<div class="tit" style="color:#FFF">这一年最 unforgettable 的几单</div>')
    L.append('<div class="hl">')
    p = hl["priciest"]
    L.append('<div class="it"><div class="k">最贵一单</div><div class="v">¥%s</div>'
             '<div class="d">%s · %s<br>%s</div></div>'
             % (esc(p["paid"]), esc(p["date"]), esc(p["channel"]),
                esc(p["items"][:26] + ("…" if len(p["items"]) > 26 else ""))))
    e = hl["earliest"]
    L.append('<div class="it"><div class="k">最早一单</div><div class="v">%s</div>'
             '<div class="d">%s · %s<br>凌晨的麦当劳，只有你懂</div></div>'
             % (esc(e["time"]), esc(e["date"]), esc(e["channel"])))
    b = hl["busiest_day"]
    L.append('<div class="it"><div class="k">单日连击</div><div class="v">%d 单</div>'
             '<div class="d">%s（%s）<br>当天合计 ¥%s</div></div>'
             % (b["orders"], esc(b["date"]), esc(b["weekday"]), esc(b["amount"])))
    m = hl["most_items"]
    L.append('<div class="it"><div class="k">最多件数</div><div class="v">%d 件</div>'
             '<div class="d">%s · ¥%s<br>这一单撑过了一个下午</div></div>'
             % (m["items_count"], esc(m["date"]), esc(m["paid"])))
    L.append("</div></section>")

    # ---------------- 钱包与积分 ----------------
    L.append('<section class="card tinted-red">')
    L.append('<div class="kick">你的钱包</div>')
    L.append('<div class="tit">用券省下 ¥%s</div>' % esc(cp["total_saved"]))
    L.append('<div class="grid4">')
    L.append('<div class="gc"><div class="n">%.1f%%</div><div class="k">用券率<br>'
             '%d / %d 单用了券</div></div>'
             % (cp["usage_rate"], cp["used_orders"], t["orders"]))
    L.append('<div class="gc"><div class="n">¥%s</div><div class="k">平均每单省<br>'
             '最高单券 ¥%s 级</div></div>' % (esc(cp["avg_saved"]), esc("%.0f" % cp["avg_saved"])))
    L.append('<div class="gc"><div class="n">¥%s</div><div class="k">用券单笔均<br>'
             '未用券单 ¥%s</div></div>' % (esc(cp["avg_paid_used"]), esc(cp["avg_paid_unused"])))
    L.append('<div class="gc"><div class="n">%d</div><div class="k">累计攒积分<br>'
             '平均每单 %s 分</div></div>' % (report["points"]["earned"],
                                            esc(report["points"]["per_order"])))
    L.append("</div>")
    if cp.get("top"):
        L.append('<div class="sub">最常使用：<b>%s</b>（%d 次）。'
                 '注意：用券单笔均 ¥%s 反而高于未用券单 ¥%s——满减券多来自高客单场景。</div>'
                 % (esc(cp["top"]["name"]), cp["top"]["count"],
                    esc(cp["avg_paid_used"]), esc(cp["avg_paid_unused"])))
    L.append("</section>")

    # ---------------- 星期 ----------------
    L.append('<section class="card">')
    L.append('<div class="kick">工作日 vs 周末</div>')
    wd = report["weekday"]
    wk_peak = max(wd, key=lambda x: x["orders"])
    L.append('<div class="tit">%s是你的麦麦日</div>' % esc(wk_peak["name"]))
    L.append('<div class="rows">')
    for i, w in enumerate(wd):
        L.append('<div class="row"><span class="nm">%s</span>'
                 '<div class="bar"><div class="bar-f" style="width:%.1f%%;animation-delay:%dms'
                 'background:var(--yel);"></div></div>'
                 '<span class="vv">%d单 · %.0f%%</span></div>'
                 % (esc(w["name"]), w["pct"], i * 60, w["orders"], w["pct"]))
    L.append("</div></section>")

    # ---------------- 行动号召 ----------------
    extra = []
    if radar_url:
        extra.append('<a href="%s">⚡ 麦麦活动雷达：活动开抢不错过</a>' % esc(radar_url))
    if repo_url:
        extra.append('<a href="%s" style="font-weight:800;text-decoration:underline">'
                     '⭐ %s</a>' % (esc(repo_url), esc(repo_url)))
    L.append('<section class="cta">')
    L.append(_arcs_svg("150", "arcs2"))
    L.append('<h3>这份年报，数据来自你的真实订单</h3>')
    L.append("<p>接入麦当劳 MCP 后，任何人都能生成属于自己的这一份。</p>")
    if extra:
        L.append("<p>" + "<br>".join(extra) + "</p>")
    L.append("<p style='margin-top:10px'>喜欢这份年报？点个 ⭐ Star，"
             "这是麦当劳程序员节创意开发大赛参赛作品。</p>")
    if repo_url:
        L.append('<a class="gold-btn" href="%s">⭐ 点亮这个麦麦年报</a>' % esc(repo_url))
    L.append("</section>")

    # ---------------- 脚注 ----------------
    L.append('<div class="foot">')
    L.append("数据源 <b>麦当劳中国 MCP</b> · <code>order-list</code> / <code>mall-order-list</code> / "
             "<code>query-my-account</code><br>")
    L.append("本页面使用<b>脱敏示例数据</b>（<code>make_sample_data.py</code> 固定种子 42 生成），"
             "非任何真实用户的订单记录。<br>")
    L.append("全部统计由 <code>wrapped_engine.py</code> 确定性计算，纯标准库、零第三方依赖、可单元测试。<br>")
    L.append("麦当劳、McDonald's 及相关标识归其权利人所有，本作品<b>非麦当劳官方产品</b>，"
             "数据仅供参考。<br>")
    L.append("生成于 %s" % esc(meta["generated_at"]))
    L.append("</div>")

    L.append("</main></body></html>")
    return "\n".join(L)
