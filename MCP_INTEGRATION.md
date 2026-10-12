# MCP 集成说明

本作品通过**麦当劳中国 MCP Server** 获取真实订单数据，遵循 MCP 协议的
Streamable HTTP 传输。

- 服务地址：`https://api.mcd.cn/mcp/v1`
- 传输方式：Streamable HTTP（HTTP + JSON-RPC 2.0）
- 认证方式：HTTP Header `Authorization: Bearer ${MCD_MCP_TOKEN}`
- 配置文件：[`mcp-config.example.json`](./mcp-config.example.json)

---

## 1. 用到的 MCP 工具

| 工具 | 用途 | 本作品中如何使用 |
|---|---|---|
| `order-list` | 查询用户历史点餐订单（堂食 / 外带 / 麦乐送） | **主数据源**：订单时间、渠道、商品明细、实付、优惠 |
| `mall-order-list` | 查询麦麦商城订单（联名周边、兑换券） | **补充数据源**：周边类消费，与堂食订单合并复盘 |
| `query-my-account` | 查询麦门会账户信息 | 补充：会员等级、累计消费额（用于与本地统计交叉校验） |

> 本作品**不需要**写操作类工具（下单、取消、领券等），因此 `create-order`、
> `cancel-order`、`add-coupon` 等工具一律不调用——年报是只读的。

---

## 2. 调用流程

```
① initialize                      MCP 握手，协商协议版本
② tools/list                      确认 order-list 等工具可用
③ tools/call  order-list          拉取历史订单（分页）
④ tools/call  mall-order-list     拉取商城订单
⑤ tools/call  query-my-account    拉取账户汇总（校验用）
        │
        ▼  全部为本地 JSON 落盘
⑥ wrapped_cli.py --orders …       本地确定性统计 + 本地渲染
```

所有渲染与计算都在**本地**完成，订单数据不出本机。

---

## 3. 请求示例

### 3.1 握手

```http
POST https://api.mcd.cn/mcp/v1 HTTP/1.1
Authorization: Bearer ${MCD_MCP_TOKEN}
Content-Type: application/json
Accept: application/json, text/event-stream

{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "initialize",
  "params": {
    "protocolVersion": "2025-03-26",
    "clientInfo": {"name": "mcd-wrapped", "version": "1.0.0"},
    "capabilities": {}
  }
}
```

### 3.2 拉取历史订单

```http
POST https://api.mcd.cn/mcp/v1 HTTP/1.1
Authorization: Bearer ${MCD_MCP_TOKEN}
Content-Type: application/json

{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "tools/call",
  "params": {
    "name": "order-list",
    "arguments": {"startTime": "2026-01-01", "endTime": "2026-10-12"}
  }
}
```

响应为 MCP `tool result` 包裹的 JSON，订单数组在
`result.content[0].text` 中（字符串化 JSON，需二次 `json.loads`）。

---

## 4. 字段映射与容错

麦当劳 MCP 各工具的字段命名**不完全统一**，且可能随版本调整。
引擎的 `normalize()` 对每个语义字段做**多路径 fallback**，无需为字段改名改引擎：

| 语义 | 依次尝试的字段名 |
|---|---|
| 订单时间 | `createTime` → `orderTime` → `gmtCreate` → `orderCreateTime` → `placedTime` |
| 门店 | `storeName` → `restaurantName` → `store` → `restaurant` |
| 渠道 | `channel` → `orderType` → `dineType` → `businessType` → `deliveryType` |
| 实付 | `paid` → `actualPrice` → `actualAmount` → `totalPaid` → `payAmount` |
| 优惠 | `discount` → `promotionAmount` → `couponAmount` → `savedAmount` |
| 券名 | `couponName` → `couponDesc` → `couponTitle` → `promotionName` |
| 商品列表 | `items` → `productList` → `goodsList` → `orderItems` → `details` |
| 商品名 | `name` → `productName` → `goodsName` → `spuName` → `itemName` |
| 商品价格 | `price` → `salePrice` → `itemPrice` → `amount` |
| 商品数量 | `qty` → `quantity` → `count` → `num` |
| 积分 | `pointEarned` → `point` → `integral` → `gainPoint` |
| 订单号 | `orderId` → `orderNo` → `id` → `tradeNo` |

**兜底策略**（任何输入都不许抛异常）：

- 时间缺失 → 回落到哨兵时间 `1970-01-01`，并可在统计中识别（月份 1、年份 1970）
- 门店 / 渠道缺失 → 分别用 `未知门店` / `未标注`
- 实付缺失 → 用商品明细求和反推
- 商品数量缺失 → 默认为 1
- 时间格式支持 5 种：`YYYY-MM-DD HH:MM:SS`、`YYYY-MM-DDTHH:MM:SS`、
  `YYYY/MM/DD HH:MM:SS`、`YYYY-MM-DD HH:MM`、`YYYYMMDD`

这些容错路径均由 `selftest.py` 的 `TestNormalize` 与 `TestEdgeCases` 类覆盖。

---

## 5. 错误处理

| HTTP 状态 | 含义 | 处理 |
|---|---|---|
| 200 | 成功 | 解析 `result.content[0].text` |
| 401 | Token 无效 / 过期 | 提示用户重新获取 Token，勿重试 |
| 403 | 无权限 | 检查 Token 是否与该手机号绑定 |
| 404 | 接口不存在 | 降级到本地样本，提示接口变更 |
| 429 | 请求过快 | 指数退避重试，上限 3 次 |
| 5xx | 服务异常 | 指数退避重试，上限 3 次 |

> ⚠️ MCP 服务有**请求速率限制**，年报属低频场景，单次生成通常不超过 5 次调用。
> 不要在循环里逐单调用 `order-list`。

---

## 6. 数据合规

- Token 仅存于环境变量 `MCD_MCP_TOKEN`，**禁止**写入仓库、日志或报告
- `mcp-config.example.json` 中 Token 一律为占位符 `${MCD_MCP_TOKEN}`
- 订单数据本地处理，不上传任何第三方，报告 HTML 无外链回传
- 仓库内示例数据为**程序生成**，不含任何真实用户信息
- 见 [`CONTEST_DECLARATION.md`](./CONTEST_DECLARATION.md) 中的信息安全声明

---

## 7. 本地运行验证

```bash
# 1. 装 MCP 连接器（WorkBuddy / Claude Desktop / Cursor 均可）
#    使用 mcp-config.example.json 作为起点，替换真实 Token

# 2. 通过 MCP 拉取订单并落盘
#    （各 MCP 客户端导出方式不同，最终得到 orders.json）

# 3. 本地渲染
cd src/wrapped_engine
python wrapped_cli.py --orders ../sample_data/orders.json --html -o ../../docs/demo.html

# 4. 自测通过
python -m unittest selftest
```

不配置真实 Token 时，直接运行第 3 步即可看到完整报告——
内置 [`src/sample_data/orders.json`](./src/sample_data/orders.json) 为脱敏示例数据
（82 单、2026-01-05 ~ 2026-10-11，由固定种子 42 生成，可完全复现）。
