# 麦麦年报 · MCD Wrapped

> **一句话：把你的麦当劳订单变成一份可以截图发给朋友的年报。**
>
> Spotify 有 Wrapped，网易云有年报。**麦当劳 36 个 MCP 工具里，只有 3 个工具的历史订单链路，整个榜单 100 个项目里 0 个人碰它。** 我们做了。

![status](https://img.shields.io/badge/status-参赛中-DA291C) ![deps](https://img.shields.io/badge/dependency-0-FFC72C) ![tests](https://img.shields.io/badge/tests-38%20passing-4ADE80) ![py](https://img.shields.io/badge/python-3.8%2B-40B39F)

**麦当劳程序员节创意开发大赛参赛作品** · 非麦当劳官方产品

**🔴 在线体验：[wangnuo-log.github.io/mcd-wrapped/demo.html](https://wangnuo-log.github.io/mcd-wrapped/demo.html)**（脱敏示例数据渲染，即开即看）

---

## 🚫 先看一眼这个榜单的空白

大赛开赛 3 天，官方排行榜快照显示约 130 个项目报名、100 个上榜。我们把它们按赛道数了一遍：

| 赛道 | 上榜项目数 | 饱和状态 |
|---|---:|---|
| 优惠券 / 省钱 / 预算 | ~30 | 🔴 严重拥挤 |
| 卡路里 / 营养 | ~15 | 🔴 严重拥挤 |
| 点餐助手 / 推荐 | ~15 | 🟡 较拥挤 |
| 活动雷达 / 日历 | ~5 | 🟡 有跟随者 |
| 派对预约 / 门店 | ~8 | 🟡 有跟随者 |
| **历史订单复盘 / 年度报告** | **0** | 🟢 **完全空白** |

**洞察**：现有 100 个项目 **100% 面向未来**——帮你省钱、帮你推荐、帮你提醒。
**没有一个项目面向过去**——你没在问"我怎么省"，你在问"**我这一年到底吃了什么**"。

年度报告是这个赛道的唯一形式，而且它是**社交传播型内容**：Spotify Wrapped 的病毒式传播不靠推荐算法，靠"我想把这张图发给朋友"。

---

## 🎬 效果预览

[`docs/demo.html`](./docs/demo.html) · 单文件 19.8 KB · 零外部依赖 · 双击即开 · 移动端竖屏即为社交图

82 单 · ¥2,650 · 219 件 · 279 天 · 5 家门店，渲染成 **11 张竖屏叙事卡片**：

| # | 卡片 | 内容 |
|---:|---|---|
| 1 | 封面 | 年度主题 + 统计周期 + 主场景 |
| 2 | 总览 | 总消费（62px 巨字）/ 订单数 / 件数 / 笔均 |
| 3 | **麦麦人格** | 大字标签 + 徽章组（社交传播核心） |
| 4 | 时段分布 | 早餐/午餐/下午茶/晚餐/深夜 横向条 |
| 5 | 最爱 TOP 6 | 排名 + 件数 + 金额 |
| 6 | 渠道 | 麦乐送 / 堂食 / 得来速 / 自取 |
| 7 | 月度节奏 | 10 柱柱状图 + 高峰/低谷月份 |
| 8 | 高光时刻 | 最贵一单 / 最早一单 / 单日连击 / 最多件数 |
| 9 | 钱包 | 用券率 / 省下金额 / 累计积分 |
| 10 | 工作日 vs 周末 | 7 日分布 |
| 11 | CTA | 姊妹项目入口 + Star 转化位 |

深色底 + 荧光黄高亮，是刻意照抄 Spotify Wrapped 的视觉语言——**为截图而设计**，不是为"看起来专业"。

---

## 🧠 技术立场：不靠大模型算

这是本项目和榜单上绝大多数项目的分水岭。大部分"AI 技能"让大模型直接读 JSON 然后"总结一下"——**不可复现，也不可验证**。

我们的架构：

```
麦当劳 MCP (order-list / mall-order-list / query-my-account)
        │
        ▼
  normalize()            ← 字段名 fallback，适配 MCP 版本差异
        │
        ▼
  analyze_orders()       ← 纯标准库、确定性计算、int 分运算防浮点误差
        │
        ▼
  render_wrapped_html()  ← 单文件 HTML，CSS 自绘图，零外部资源
```

### 三个具体的可靠性设计

**1. 金额一律用 int 分计算**

```python
def cents(amount):
    return int(round(float(amount) * 100))   # 元 → 分

def yuan(cents_):
    return round(cents_ / 100.0, 1)          # 分 → 元
```

`0.1 + 0.2` 在 float 下是 `0.30000000000000004`。分是 int，累加零漂移。82 单、214 件餐品、¥2,650，逐项守恒可验。

**2. 任何输入都不许崩**

真实 MCP 返回的字段名因工具版本而异。`normalize()` 对每个字段做多路径 fallback：

| 语义 | 尝试的字段名 |
|---|---|
| 时间 | `createTime` / `orderTime` / `gmtCreate` / `orderCreateTime` / `placedTime` |
| 商品 | `items` / `productList` / `goodsList` / `orderItems` / `details` |
| 实付 | `paid` / `actualPrice` / `actualAmount` / `totalPaid` / `payAmount` |

时间解析支持 5 种格式，**解析失败回落到哨兵时间而不是抛异常**——这是"确定性工具"和"AI 碰运气"的区别。

**3. 38 项自测，跑通即证明**

```bash
$ python -m unittest selftest
......................................
Ran 38 tests in 0.078s

OK
```

覆盖五类断言：

- **精度**：元/分往返、浮点漂移、负值与 None
- **边界**：时段映射 12 个边界点（含跨零点深夜时段）、百分比容差
- **守恒**：品类 / 时段 / 渠道 / 星期 / 月份 / 券 六个维度的分组之和 == 总量
- **健壮性**：MCP 风格字段、缺失字段、垃圾时间字符串、空列表、单笔订单
- **确定性**：同输入两次运行结果逐字段相等（含人格标签排序）、HTML 逐字节相等

---

## 🏷️ 麦麦人格：确定性的判据，不是一句 AI 评语

10 条规则，全部是**可逐条核验的数学判据**：

| 标签 | 判定条件 |
|---|---|
| 早餐信徒 | 早餐时段订单占比 ≥ 30% |
| 夜宵麦门 | 深夜时段（21:00–06:00）占比 ≥ 12% |
| 宅家麦乐送 | 麦乐送渠道占比 ≥ 35% |
| 现制派 | 到店堂食占比 ≥ 30% |
| 得来速党 | 得来速渠道占比 ≥ 12% |
| 巨无霸死忠 | 巨无霸类餐品件数 ≥ 10 |
| 甜品控 | 甜品品类件数占比 ≥ 12% |
| 薅羊毛大师 | 用券率 ≥ 30% |
| 周末战士 | 周末订单占比 ≥ 42% |
| 大额玩家 | 单笔 ≥ ¥50 订单占比 ≥ 15% |

命中越多标签越立体，主标签取得分最高者。**同数据必得同标签**，不靠"感觉"。

示例数据上命中 5/10：`宅家麦乐送 42.7`、`早餐信徒 36.6`、`得来速党 24.4`、`大额玩家 15.9`、`巨无霸死忠 12`。

---

## 🚀 快速开始

### 方式一：本地离线（推荐，零依赖零 Token）

```bash
cd src/wrapped_engine
python -m pip install nothing    # 真的什么都不用装

# 生成报告
python wrapped_cli.py --html -o ../../docs/demo.html

# 跑自测
python -m unittest selftest -v

# 直接看结果
start ../../docs/demo.html       # Windows
open  ../../docs/demo.html       # macOS
```

内置 [脱敏示例数据](./src/sample_data/orders.json)（82 单、1–10 月），无需 Token、无需联网。

### 方式二：接你的真实订单（麦当劳 MCP）

```bash
# 1. 配置 MCP Token
export MCD_MCP_TOKEN="你的Token"

# 2. 通过 MCP 调用 order-list 拿到订单 JSON，落盘
python wrapped_cli.py --orders my_orders.json --html -o report.html

# 3. 带上仓库链接，报告尾部自动生成 Star 入口
python wrapped_cli.py --orders my_orders.json --html -o report.html \
    --repo https://github.com/wangnuo-log/mcd-wrapped
```

`--orders` 接受 JSON 数组，或含 `orders` 键的对象；字段名不匹配时无需改引擎，`normalize()` 会自动适配。

### 方式三：在 WorkBuddy 里当技能用

把 [`skills/mcd-wrapped`](./skills/mcd-wrapped) 目录放进 `~/.workbuddy/skills/`，配置 mcd-mcp 连接器（见 [`mcp-config.example.json`](./mcp-config.example.json)），然后说：

> 「生成我的麦麦年报」

---

## 📁 目录结构

```
mcd-wrapped/
├── README.md                     ← 本文件
├── CONTEST_DECLARATION.md        官方参赛声明（原文复制，一字未改）
├── MCP_INTEGRATION.md            MCP 集成说明
├── LICENSE                       MIT
├── mcp-config.example.json       脱敏 MCP 配置示例
├── .gitignore
├── docs/
│   ├── demo.html                 ← 单文件年报（19.8 KB，零外链）
│   └── demo.json                 统计基准输出（供校验）
├── skills/
│   └── mcd-wrapped/SKILL.md      WorkBuddy 技能入口
└── src/
    ├── sample_data/
    │   ├── make_sample_data.py   样本生成器（种子 42，可复现）
    │   └── orders.json           脱敏示例订单（82 单）
    └── wrapped_engine/
        ├── wrapped_engine.py     统计引擎（纯标准库）
        ├── wrapped_html.py       Wrapped 风格渲染器
        ├── wrapped_cli.py        命令行入口
        └── selftest.py           38 项自测
```

---

## 🔒 数据与隐私

- **仓库中不含任何真实 Token、密钥、账号或真实用户订单**
- 示例数据由 [`make_sample_data.py`](./src/sample_data/make_sample_data.py) 用**固定随机种子 42** 生成，任何人重跑都得到字节级一致的结果——可复现、可核验、可审计
- 示例餐品名、门店名取自公开菜单与门店列表，不含个人信息
- 接真实数据时，订单 JSON 由你本地生成、本地渲染、**不上传任何第三方**
- HTML 报告为单文件、零外链、零脚本回传，断网可看

---

## 🔗 姊妹项目

| 项目 | 定位 | 状态 |
|---|---|---|
| [mcd-wrapped](.) | **面向过去**：年度复盘、社交传播 | 本项目 · [Issue #533](https://github.com/M-China/mcd-developer-innovation-challenge/issues/533) |
| [mcd-activity-radar](https://github.com/wangnuo-log/mcd-activity-radar) | **面向未来**：活动聚合、开抢倒计时 | 已参赛 · [Issue #37](https://github.com/M-China/mcd-developer-innovation-challenge/issues/37) |

两个项目共用同一套 MCP Token、同一个 mcd-mcp 连接器配置，报告中互相留了入口。

---

## 📄 许可

[MIT License](./LICENSE)

**麦当劳、McDonald's、巨无霸及相关标识归其权利人所有。** 本作品为独立开发的技术演示，**非麦当劳官方产品**，与麦当劳无隶属或合作关系。
