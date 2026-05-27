# A 股数据源架构文档

> 文件位置: `tradingagents/dataflows/a_stock.py`
>
> 零第三方数据依赖（不依赖 akshare），所有数据均通过直接 HTTP API 或 TCP 协议获取。

---

## 目录

- [六大数据源总览](#六大数据源总览)
- [数据缓存机制](#数据缓存机制)
- [Ticker 格式处理](#ticker-格式处理)
- [17 个数据接口详解](#17-个数据接口详解)
- [接口与数据源映射总表](#接口与数据源映射总表)
- [获取限制与注意事项](#获取限制与注意事项)
- [Vendor 路由机制](#vendor-路由机制)

---

## 限制标记说明

文档中使用以下标记来标注各类限制：

| 标记 | 含义 |
|------|------|
| 🔴 **严重** | 接口已停更/下线/不可用，有功能缺失 |
| 🟠 **高危** | 非公开API，随时可能变更或被封；依赖特定网络环境 |
| 🟡 **中等** | 有数据量/时间范围/频率限制，但不影响基本使用 |
| 🟢 **低风险** | 公开稳定接口，限制较少 |
| ⚠️ | 需要特别注意的事项 |

---

## 六大数据源总览

| # | 数据源 | 协议 | 基础 URL | 主要用途 | 认证 | 限制等级 | 限制详情 |
|---|--------|------|----------|----------|------|----------|----------|
| 1 | **mootdx** (通达信) | TCP 7709 | `std` 标准行情服务器 | K线OHLCV、财务快照、F10 | 无 | 🟠 | TCP端口可能被防火墙拦截；单次最多800根K线；连接不稳定时超时 |
| 2 | **腾讯财经** | HTTP/GBK | `https://qt.gtimg.cn/q=` | 实时行情（PE/PB/市值/换手率/涨跌停） | 无 | 🟡 | GBK编码需解码；字段索引硬编码(vals[1]~vals[52])，格式变更会解析失败；高频请求可能触发限速 |
| 3 | **东方财富** | HTTP | `push2.eastmoney.com` / `datacenter-web.eastmoney.com` | 股票信息、龙虎榜、解禁、行业排名、资金流向 | 无 | 🟡 | secid格式要求严格(1.代码/0.代码)；非交易时段部分接口返回空；datacenter的reportName需精确匹配 |
| 4 | **新浪财经** | HTTP | `quotes.sina.cn` / `money.finance.sina.com.cn` | K线备用源、三大财务报表 | 无 | 🟠 | 非公开API，随时可能变更；财务报表最多8条记录；K线备用源无明确频率限制但高频可能封IP |
| 5 | **同花顺** | HTTP | `basic.10jqka.com.cn` / `data.hexin.cn` / `zx.10jqka.com.cn` | 一致预期EPS、涨停热点、北向资金 | 无 | 🟠 | HTML页面解析，改版即失效；hsgtApi需特定Host/Referer；🔴北向历史API已于2024-08停更；涨停接口需GBK参数 |
| 6 | **百度股市通** | HTTP | `finance.pae.baidu.com` | 概念板块/行业/地域归属 | 无 | 🟡 | 需特定Accept/Origin/Referer请求头；ResultCode非零即错误；V0.2.7已替换其fundflow接口(下线) |
| 7 | **财联社** | HTTP | `www.cls.cn/nodeapi/telegraphList` | 全球财经快讯 | 无 | 🟢 | 仅返回最新快讯，无历史回溯；ctime为unix时间戳 |

> **关键特征**: 所有数据源均**无需 API Key**，通过模拟浏览器 User-Agent 即可直接访问。

---

## 数据缓存机制

| 缓存类型 | 路径 | 策略 | 说明 |
|----------|------|------|------|
| K线 CSV | `~/.tradingagents/cache/{code}-astock-daily.csv` | 按日缓存 | 同一天内重复请求直接读缓存，不重新请求 |
| 北向资金 CSV | `~/.tradingagents/cache/northbound_daily.csv` | 增量追加 | 每次调用自动追加当日收盘快照，按日期去重 |

缓存目录可通过环境变量 `TRADINGAGENTS_CACHE_DIR` 或配置项 `data_cache_dir` 自定义。

---

## Ticker 格式处理

系统支持多种 A 股代码输入格式，统一转换为纯 6 位数字：

| 输入格式 | 示例 | 转换结果 |
|----------|------|----------|
| 纯数字 | `688017` | `688017` |
| 交易所前缀 | `SH688017` / `sz000001` | `688017` / `000001` |
| 交易所后缀 | `688017.SH` / `000001.SZ` | `688017` / `000001` |
| 中文名称 | `宝光股份` | 通过 mootdx 股票列表反查 → `600379` |

市场前缀规则：
- `6` / `9` 开头 → `sh`（沪市）
- `0` / `3` 开头 → `sz`（深市）
- `8` 开头 → `bj`（北交所）

---

## 17 个数据接口详解

### 1. get_stock_data — K线行情

**函数签名**:
```python
def get_stock_data(
    symbol: str,       # A股代码，如 688017, SH688017
    start_date: str,   # 起始日期 yyyy-mm-dd
    end_date: str,     # 结束日期 yyyy-mm-dd
) -> str
```

**数据源映射**:

| 优先级 | 数据源 | 接口 | 返回字段 | 限制 |
|--------|--------|------|----------|------|
| 主源 | mootdx TCP 🟠 | `client.bars(symbol, category=4, offset=800)` | Date, Open, High, Low, Close, Volume, Amount | TCP 7709端口可能被防火墙拦截；单次最多800根K线 |
| 备用 | 新浪 HTTP 🟠 | `CN_MarketData.getKLineData?scale=240&datalen=800` | Date, Open, High, Low, Close, Volume | 非公开API，随时可能变更；高频请求可能封IP |

**数据流**:
1. 尝试 mootdx TCP 获取 800 根日K线（约3年交易日）
2. mootdx 失败 → 新浪 HTTP API 兜底
3. 两个源均失败 → 返回错误提示

**获取限制**:
- 🟠 mootdx: 单次最多 800 根K线；依赖 TCP 7709 端口连通性，部分网络环境可能被防火墙拦截
- 🟠 新浪: 非公开API，接口随时可能变更；高频请求可能触发 IP 封禁
- 🟢 返回数据按 `start_date` / `end_date` 过滤，无额外限制

---

### 2. get_indicators — 技术指标

**函数签名**:
```python
def get_indicators(
    symbol: str,           # A股代码
    indicator: str,        # 指标名称，如 rsi, macd, close_50_sma
    curr_date: str,        # 当前交易日 YYYY-mm-dd
    look_back_days: int,   # 回溯天数
) -> str
```

**数据源映射**:

| 步骤 | 数据源 | 说明 | 限制 |
|------|--------|------|------|
| 1 | mootdx 🟠 / 新浪 🟠 | 调用 `_load_ohlcv_astock()` 获取K线数据 | 同 get_stock_data 的K线获取限制 |
| 2 | stockstats 库 🟢 | 在K线上计算技术指标 | 纯本地计算，无网络限制 |

**支持的指标**:

| 指标键 | 含义 |
|--------|------|
| `close_50_sma` | 50日简单移动平均线 |
| `close_200_sma` | 200日简单移动平均线 |
| `close_10_ema` | 10日指数移动平均线 |
| `macd` / `macds` / `macdh` | MACD线 / 信号线 / 柱状图 |
| `rsi` | 相对强弱指标 |
| `boll` / `boll_ub` / `boll_lb` | 布林带中轨 / 上轨 / 下轨 |
| `atr` | 平均真实波幅 |
| `vwma` | 成交量加权移动平均 |
| `mfi` | 资金流量指标 |

**获取限制**:
- 🟠 底层受 `_load_ohlcv_astock()` 的K线获取限制约束
- 🟢 `curr_date` 用于防止前瞻偏差，只返回该日期之前的指标值
- 🟡 非交易日返回 "N/A: Not a trading day"，look_back_days 跨越非交易日时会有空缺

---

### 3. get_fundamentals — 公司基本面

**函数签名**:
```python
def get_fundamentals(
    ticker: str,       # A股代码
    curr_date: str,    # 当前日期（未使用，接口兼容）
) -> str
```

**数据源映射**（多源聚合）:

| 数据源 | 接口 | 返回字段 | 限制 |
|--------|------|----------|------|
| 腾讯财经 🟡 | `qt.gtimg.cn/q={prefix}{code}` | name, price, pe_ttm, pe_static, pb, mcap_yi, float_mcap_yi, turnover_pct, change_pct, limit_up, limit_down | GBK编码；字段索引硬编码(vals[1]~vals[52])，API格式变更会解析失败 |
| mootdx TCP 🟠 | `client.finance(symbol=code)` | eps, bvps, roe, profit, income, liutongguben, zongguben | 仅返回最近一期季度快照，历史不可查；TCP连接不稳定时超时 |
| 东方财富 push2 🟡 | `push2.eastmoney.com/api/qt/stock/get` | 行业(f127), 总股本(f84), 流通股本(f85), 总市值(f116), 流通市值(f117), 上市日期(f189) | secid格式要求 `市场编号.代码`（沪=1，深=0） |
| 同花顺 🟠 | `basic.10jqka.com.cn/new/{code}/worth.html` | 一致预期EPS、Forward PE、PEG、PE消化年数 | HTML表格解析，页面改版即失效；低覆盖度(<3家机构)标注Warning |

**获取限制**:
- 🟡 腾讯财经: 批量查询，单次可请求多只股票；GBK 编码需解码；字段索引固定，API 格式变更可能导致解析失败
- 🟠 mootdx finance: 返回最近一期季度快照，历史数据不可查
- 🟡 东方财富 push2: `secid` 格式要求 `市场编号.代码`（沪市=1，深市=0）
- 🟠 同花顺: HTML 表格解析，页面改版会导致解析失败；低覆盖度（<3家机构）会标注 Warning
- ⚠️ 四个数据源中任一失败不影响其他源，结果为成功源的聚合

---

### 4. get_balance_sheet — 资产负债表

**函数签名**:
```python
def get_balance_sheet(
    ticker: str,       # A股代码
    freq: str,         # 'annual' 或 'quarterly'
    curr_date: str,    # 当前日期 YYYY-MM-DD
) -> str
```

**数据源映射**:

| 数据源 | 接口 | 参数 | 限制 |
|--------|------|------|------|
| 新浪财经 🟠 | `quotes.sina.cn/.../CompanyFinanceService.getFinanceReport2022` | `paperCode=sh600379, source=fzb, type=0, page=1, num=20` | 非公开API；最多8条记录；无备用源 |

**获取限制**:
- 🟠 新浪 API 为非公开接口，可能随时变更或下线
- 🟡 最多返回 8 条记录（`df.head(8)`）
- 🟡 `freq=annual` 仅筛选 12 月报告
- 🟢 `curr_date` 过滤防止前瞻偏差
- 🔴 **无备用数据源**，新浪不可用时直接返回错误

---

### 5. get_cashflow — 现金流量表

**函数签名**:
```python
def get_cashflow(
    ticker: str,
    freq: str,         # 'annual' 或 'quarterly'
    curr_date: str,
) -> str
```

**数据源映射**: 与资产负债表共用 `_get_financial_report_sina()`，`source=llb`

**获取限制**: 同资产负债表（🟠非公开API / 🟡最多8条 / 🔴无备用源）

---

### 6. get_income_statement — 利润表

**函数签名**:
```python
def get_income_statement(
    ticker: str,
    freq: str,         # 'annual' 或 'quarterly'
    curr_date: str,
) -> str
```

**数据源映射**: 与资产负债表共用 `_get_financial_report_sina()`，`source=lrb`

**获取限制**: 同资产负债表（🟠非公开API / 🟡最多8条 / 🔴无备用源）

---

### 7. get_news — 个股新闻

**函数签名**:
```python
def get_news(
    ticker: str,       # A股代码
    start_date: str,   # 起始日期 yyyy-mm-dd
    end_date: str,     # 结束日期 yyyy-mm-dd
) -> str
```

**数据源映射**:

| 优先级 | 数据源 | 接口 | 返回字段 | 限制 |
|--------|--------|------|----------|------|
| 主源 | 东方财富搜索 🟡 | `search-api-web.eastmoney.com/search/jsonp` | title, content, date, mediaName, url | JSONP格式需手动去括号；默认page_size=20 |
| 备用 | 新浪财经 🟠 | `vip.stock.finance.sina.com.cn/corp/view/vCB_AllNewsStock.php` | title, time, url（正则解析HTML） | GB2312编码；正则提取，无正文；页面结构变更会解析失败 |

**获取限制**:
- 🟡 东方财富: JSONP 格式需手动去括号解析；默认 `page_size=20`，无法翻页
- 🟠 新浪: GB2312 编码；通过正则提取新闻列表，无正文内容；页面结构变更会导致解析失败
- 🟢 新闻按 `start_date` / `end_date` 过滤
- ⚠️ 东方财富搜索API以股票代码为关键词，可能返回不相关新闻

---

### 8. get_global_news — 全球财经新闻

**函数签名**:
```python
def get_global_news(
    curr_date: str,        # 当前日期 yyyy-mm-dd
    look_back_days: int,   # 回溯天数，默认 7
    limit: int,            # 最大文章数，默认 10
) -> str
```

**数据源映射**:

| 数据源 | 接口 | 返回字段 | 限制 |
|--------|------|----------|------|
| 财联社 🟢 | `www.cls.cn/nodeapi/telegraphList?rn={limit}&page=1` | title/brief, content, ctime(unix时间戳) | 仅返回最新快讯，无历史回溯 |
| 东方财富7x24 🟡 | `np-weblist.eastmoney.com/comm/web/getFastNewsList` | title, summary, showTime | 需biz=web_724和fastColumn=102参数；summary截断200字 |

**获取限制**:
- 🔴 两个源均为**实时快讯，无历史回溯能力**（只能获取最近发布的新闻）
- 🟢 财联社: `ctime` 为 unix 时间戳，需自行转换
- 🟡 东方财富: 需要 `biz=web_724` 和 `fastColumn=102` 参数
- 🟢 结果按标题去重
- ⚠️ `look_back_days` 参数实际无法控制回溯范围，因为两个API都只返回最新数据

---

### 9. get_insider_transactions — 股东研究

**函数签名**:
```python
def get_insider_transactions(
    ticker: str,       # A股代码
) -> str
```

**数据源映射**:

| 数据源 | 接口 | 说明 | 限制 |
|--------|------|------|------|
| mootdx TCP 🟠 | `client.F10(symbol=code, name="股东研究")` | 返回 F10 文本，提取【4.股东变化】段落 | TCP连接不稳定时超时；文本超2000字符截断；🔴无备用源 |

**获取限制**:
- 🟡 A 股无美式 insider transactions 概念，此处返回的是"股东研究"文本，语义不同
- 🟡 文本可能很长，超过 2000 字符会被截断（旧数据省略）
- 🟠 依赖 mootdx TCP 连接稳定性
- 🔴 **无备用数据源**，mootdx 不可用时直接返回错误
- ⚠️ 不支持 `curr_date` 过滤，可能存在前瞻偏差

---

### 10. get_profit_forecast — 盈利预测

**函数签名**:
```python
def get_profit_forecast(
    ticker: str,
    curr_date: str,    # 当前日期（未使用，接口兼容）
) -> str
```

**数据源映射**:

| 数据源 | 接口 | 返回字段 | 限制 |
|--------|------|----------|------|
| 同花顺 🟠 | `basic.10jqka.com.cn/new/{code}/worth.html` | 年度, 预测机构数, 最小值, 均值, 最大值 | HTML表格解析，页面改版即失效；🔴无备用源 |
| 腾讯财经 🟡 | `qt.gtimg.cn/q={prefix}{code}` | 当前价格、PE(TTM)，用于计算 Forward PE / PEG | GBK编码；字段硬编码 |

**计算逻辑**:
- Forward PE = 当前价格 / 当年一致预期 EPS
- PEG = Forward PE / (EPS CAGR × 100)
- PE 消化年数 = log(Forward PE / 30) / log(1 + CAGR)（仅 Forward PE > 30x 时计算）

**获取限制**:
- 🟠 同花顺页面为 HTML 表格，解析依赖页面结构不变
- 🟡 低覆盖度（<3 家机构）会标注 Warning
- 🟡 EPS 为负或下降时，PEG 不适用
- 🔴 同花顺EPS数据**无备用源**
- ⚠️ 不支持 `curr_date` 过滤，始终返回最新预测，回测时可能存在前瞻偏差

---

### 11. get_hot_stocks — 涨停热点

**函数签名**:
```python
def get_hot_stocks(
    curr_date: str,    # 日期 YYYY-MM-DD，空字符串表示今天
) -> str
```

**数据源映射**:

| 数据源 | 接口 | 返回字段 | 限制 |
|--------|------|----------|------|
| 同花顺 🟠 | `zx.10jqka.com.cn/event/api/getharden/date/{date}/...` | code, name, reason(人工标注), zhangfu, huanshou, chengjiaoe, ddejingliang | 需GBK charset参数；🔴非交易日无数据；🔴无备用源 |

**获取限制**:
- 🔴 **仅返回当日涨停股**，非交易日无数据
- 🟠 同花顺非公开API，需 `charset/GBK/` 参数
- 🟡 `reason` 字段为同花顺编辑团队人工标注的涨停原因标签（如"算力租赁+AI政务"），质量高但可能延迟
- 🟢 底部附带主题频率统计（Top 15）
- 🟡 API 返回 `errocode != 0` 时表示错误
- 🔴 **无备用数据源**

---

### 12. get_northbound_flow — 北向资金

**函数签名**:
```python
def get_northbound_flow(
    curr_date: str,           # 日期 YYYY-MM-DD
    include_history: bool,    # 是否包含历史数据，默认 False
) -> str
```

**数据源映射**:

| 数据类型 | 数据源 | 接口 | 返回字段 | 限制 |
|----------|--------|------|----------|------|
| 实时分钟流 | 同花顺 hsgtApi 🟠 | `data.hexin.cn/market/hsgtApi/method/dayChart/` | time[], hgt[], sgt[] | 需特定Host/Referer头；🔴仅交易时段有数据 |
| 历史日收盘 | 本地 CSV 缓存 🟢 | `~/.tradingagents/cache/northbound_daily.csv` | date, hgt, sgt | 🔴依赖持续调用积累，首次使用无历史 |

**获取限制**:
- 🔴 **上游历史 API 已于 2024-08 停止更新**，历史数据完全依赖本地缓存
- 🔴 实时数据**仅在交易时段可用**，非交易时段返回空
- 🟡 每次 `include_history=True` 调用会自动将当日收盘数据追加到本地 CSV
- 🔴 历史数据需要**持续调用才能积累**，首次使用时无历史数据
- 🟠 同花顺 hsgtApi 需要 `Host: data.hexin.cn` 和 `Referer: https://data.hexin.cn/` 请求头
- ⚠️ 历史数据精度取决于过去调用时的实时数据快照，非官方历史数据

---

### 13. get_concept_blocks — 概念板块

**函数签名**:
```python
def get_concept_blocks(
    ticker: str,       # A股代码
) -> str
```

**数据源映射**:

| 数据源 | 接口 | 返回字段 | 限制 |
|--------|------|----------|------|
| 百度股市通 🟡 | `finance.pae.baidu.com/api/getrelatedblock?stock=[{code,market,type}]` | 分类名称, 板块名称, 涨跌幅(ratio), 描述(describe) | 需特定Accept/Origin/Referer请求头；🔴无备用源 |

**获取限制**:
- 🟡 需要特定请求头：`Accept: application/vnd.finance-web.v1+json`、`Origin: https://gushitong.baidu.com`、`Referer: https://gushitong.baidu.com/`
- 🟡 `ResultCode=0` 表示成功，非 0 为错误
- 🟢 返回三类板块：申万行业、概念主题、地域
- 🔴 **无备用数据源**，百度API不可用时直接返回错误
- ⚠️ 不支持 `curr_date` 过滤，始终返回最新板块归属

---

### 14. get_fund_flow — 个股资金流向

**函数签名**:
```python
def get_fund_flow(
    ticker: str,            # A股代码
    curr_date: str,         # 日期 YYYY-MM-DD
    include_history: bool,  # 是否包含历史，默认 True
) -> str
```

**数据源映射**:

| 数据类型 | 数据源 | 接口 | 返回字段 | 限制 |
|----------|--------|------|----------|------|
| 实时分钟流 | 东方财富 push2 🟡 | `push2.eastmoney.com/api/qt/stock/fflow/kline/get` | 时间, 主力/小单/中单/大单/超大单净流入 | 🔴仅交易时段有数据；🟡仅显示最近10个分钟点 |
| 历史日K | 东方财富 push2his 🟡 | `push2his.eastmoney.com/api/qt/stock/fflow/daykline/get` | 日期, 主力/大单/中单/小单/超大单净流入 | 🟡最多20个交易日(lmt=20) |

**获取限制**:
- 🟡 `secid` 格式：沪市 `1.{code}`，深市 `0.{code}`
- 🟡 实时数据仅显示最近 10 个分钟点
- 🟡 历史数据最多 20 个交易日（`lmt=20`）
- 🔴 非交易时段**无实时数据**
- ⚠️ V0.2.7 版本替换了已下线的百度 PAE fundflow 接口

---

### 15. get_dragon_tiger_board — 龙虎榜

**函数签名**:
```python
def get_dragon_tiger_board(
    ticker: str,           # A股代码
    trade_date: str,       # 交易日期 YYYY-MM-DD
    look_back_days: int,   # 回溯天数，默认 30
) -> str
```

**数据源映射**:

| 数据类型 | 数据源 | 接口(reportName) | 返回字段 | 限制 |
|----------|--------|------------------|----------|------|
| 上榜记录 | 东方财富 datacenter 🟡 | `RPT_DAILYBILLBOARD_DETAILSNEW` | TRADE_DATE, EXPLANATION, BILLBOARD_NET_AMT, TURNOVERRATE | 🟡page_size=50；🟡filter格式要求严格 |
| 买入席位 | 东方财富 datacenter 🟡 | `RPT_BILLBOARD_DAILYDETAILSBUY` | OPERATEDEPT_NAME, BUY, SELL, NET, OPERATEDEPT_CODE | 🟡仅TOP5 |
| 卖出席位 | 东方财富 datacenter 🟡 | `RPT_BILLBOARD_DAILYDETAILSSELL` | 同上 | 🟡仅TOP5 |
| 机构动向 | 从买卖席位中筛选 🟢 | `OPERATEDEPT_CODE="0"` | 机构专用席位的买入/卖出汇总 | 🟢纯逻辑筛选，无额外限制 |

**获取限制**:
- 🟡 统一通过 `_eastmoney_datacenter()` 辅助函数查询，`reportName` 需精确匹配
- 🟡 上榜记录按 `look_back_days` 时间范围过滤，最多50条
- 🟡 席位明细仅显示最近一次上榜的 TOP5
- 🟢 机构动向通过 `OPERATEDEPT_CODE="0"` 识别机构专用席位
- 🔴 **无备用数据源**

---

### 16. get_lockup_expiry — 限售解禁

**函数签名**:
```python
def get_lockup_expiry(
    ticker: str,        # A股代码
    trade_date: str,    # 交易日期 YYYY-MM-DD
    forward_days: int,  # 向前查看天数，默认 90
) -> str
```

**数据源映射**:

| 数据类型 | 数据源 | 接口(reportName) | 返回字段 | 限制 |
|----------|--------|------------------|----------|------|
| 历史解禁 | 东方财富 datacenter 🟡 | `RPT_LIFT_STAGE` | FREE_DATE, LIMITED_STOCK_TYPE, FREE_SHARES_NUM, FREE_RATIO | 🟡最多15批(page_size=15) |
| 未来待解禁 | 东方财富 datacenter 🟡 | `RPT_LIFT_STAGE`（带日期过滤） | 同上 | 🟡最多20条(page_size=20) |

**获取限制**:
- 🟡 历史记录最多 15 批（`page_size=15`）
- 🟡 未来待解禁按 `trade_date` ~ `trade_date + forward_days` 范围查询，最多 20 条
- 🔴 **无备用数据源**

---

### 17. get_industry_comparison — 行业横向对比

**函数签名**:
```python
def get_industry_comparison(
    ticker: str,    # A股代码（用于识别所属行业）
    trade_date: str, # 交易日期
    top_n: int,     # 显示排名数，默认 20
) -> str
```

**数据源映射**:

| 数据源 | 接口 | 参数 | 返回字段 | 限制 |
|--------|------|------|----------|------|
| 东方财富 push2 🟡 | `push2.eastmoney.com/api/qt/clist/get` | `fs=m:90+t:2`（行业板块） | 行业名(f14), 涨跌幅(f3), 上涨数(f104), 下跌数(f105), 领涨股(f140) | 🟡显示top_n*2行；⚠️不按个股所属行业筛选 |

**获取限制**:
- 🟡 一次返回全部行业（约100个），代码中限制最多显示 `top_n * 2` 行
- ⚠️ 原同花顺行业接口已返回 401，已替换为东方财富
- ⚠️ **不按个股所属行业筛选**，返回全行业排名，需用户自行定位
- 🔴 **无备用数据源**

---

## 接口与数据源映射总表

| # | 接口 | 分类 | mootdx | 腾讯财经 | 东方财富 | 新浪财经 | 同花顺 | 百度股市通 | 财联社 | 有备用源 |
|---|------|------|--------|----------|----------|----------|--------|-----------|--------|----------|
| 1 | get_stock_data | core_stock | ★主 🟠 | | | ★备 🟠 | | | | ✅ |
| 2 | get_indicators | technical | ★(K线) 🟠 | | | ★备(K线) 🟠 | | | | ✅ |
| 3 | get_fundamentals | fundamental | ★(快照) 🟠 | ★(估值) 🟡 | ★(信息) 🟡 | | ★(EPS) 🟠 | | | ✅(多源聚合) |
| 4 | get_balance_sheet | fundamental | | | | ★ 🟠 | | | | ❌ |
| 5 | get_cashflow | fundamental | | | | ★ 🟠 | | | | ❌ |
| 6 | get_income_statement | fundamental | | | | ★ 🟠 | | | | ❌ |
| 7 | get_news | news | | | ★主 🟡 | ★备 🟠 | | | | ✅ |
| 8 | get_global_news | news | | | ★ 🟡 | | | | ★ 🟢 | ✅(双源合并) |
| 9 | get_insider_transactions | news | ★ 🟠 | | | | | | | ❌ |
| 10 | get_profit_forecast | signal | | ★(价格) 🟡 | | | ★(EPS) 🟠 | | | ❌(EPS部分) |
| 11 | get_hot_stocks | signal | | | | | ★ 🟠 | | | ❌ |
| 12 | get_northbound_flow | signal | | | | | ★(实时) 🟠 | | | ❌ |
| 13 | get_concept_blocks | signal | | | | | | ★ 🟡 | | ❌ |
| 14 | get_fund_flow | signal | | | ★ 🟡 | | | | | ❌ |
| 15 | get_dragon_tiger_board | signal | | | ★ 🟡 | | | | | ❌ |
| 16 | get_lockup_expiry | signal | | | ★ 🟡 | | | | | ❌ |
| 17 | get_industry_comparison | signal | | | ★ 🟡 | | | | | ❌ |

> ★主 = 主数据源，★备 = 备用数据源，★ = 数据源之一
>
> 🟢低风险 🟡中等 🟠高危 🔴严重

---

## 获取限制与注意事项

### 通用限制

| 限制类型 | 等级 | 说明 |
|----------|------|------|
| **无需 API Key** | 🟢 | 所有数据源均免费、匿名访问，通过 User-Agent 模拟浏览器 |
| **频率限制** | 🟡 | 无明确 QPS 限制，但高频请求可能触发 IP 封禁或限速 |
| **网络依赖** | 🟠 | mootdx 依赖 TCP 7709 端口，部分企业网络/防火墙可能拦截 |
| **编码问题** | 🟡 | 腾讯财经返回 GBK，新浪返回 GB2312，需显式解码 |
| **前瞻偏差防护** | 🟢 | K线、财务报表、技术指标均通过 `curr_date` 参数过滤，防止回测时泄露未来数据 |
| **非公开API** | 🟠 | 大部分HTTP接口为非公开API，无稳定性保证，随时可能变更格式或下线 |

### 各数据源特定限制

| 数据源 | 限制等级 | 限制详情 |
|--------|----------|----------|
| **mootdx** | 🟠 | TCP 长连接，网络不稳定时可能超时；单次最多 800 根K线；F10 文本可能很长需截断；部分券商服务器可能限制连接频率 |
| **腾讯财经** | 🟡 | 字段索引硬编码（vals[1]~vals[52]），API 格式变更会导致解析失败；批量查询时用逗号分隔；GBK编码 |
| **东方财富 push2** | 🟡 | `secid` 格式必须为 `市场编号.代码`（1=沪, 0=深）；部分接口非交易时段返回空；字段编号(f57,f58等)含义非自文档化 |
| **东方财富 datacenter** | 🟡 | `reportName` 为固定枚举值，需精确匹配；`filter` 字符串格式有严格要求；分页参数需正确设置 |
| **新浪财经** | 🟠 | 财务报表接口为非公开 API，可能随时变更；最多返回 8 条记录；K线备用源无明确限制但高频可能封IP |
| **同花顺** | 🟠🔴 | EPS 页面为 HTML 解析，页面改版会导致失败；hsgtApi 需特定 Host/Referer 头；**🔴北向历史 API 已于 2024-08 停更**；涨停热点 API 需 GBK charset 参数 |
| **百度股市通** | 🟡 | 需特定 Accept/Origin/Referer 请求头；`ResultCode` 非零表示错误；fundflow接口已下线(V0.2.7替换) |
| **财联社** | 🟢 | 仅返回最新快讯，无历史回溯；`ctime` 为 unix 时间戳 |

### 已下线/停更接口

| 接口 | 原数据源 | 状态 | 替代方案 |
|------|----------|------|----------|
| 北向资金历史 | 同花顺 hsgtApi | 🔴 2024-08 停更 | 本地 CSV 缓存逐步积累 |
| 百度 PAE fundflow/fundsortlist | 百度股市通 | 🔴 2026-05 下线 | 东方财富 push2 资金流向 |
| 同花顺行业排名 | 同花顺 | 🔴 返回 401 | 东方财富 push2 行业板块 |

### 无备用源接口清单

以下接口在唯一数据源不可用时**直接失败**，无容灾能力：

| 接口 | 唯一数据源 | 失败影响 |
|------|-----------|----------|
| get_balance_sheet | 新浪财经 | 无法获取资产负债表 |
| get_cashflow | 新浪财经 | 无法获取现金流量表 |
| get_income_statement | 新浪财经 | 无法获取利润表 |
| get_insider_transactions | mootdx | 无法获取股东研究 |
| get_profit_forecast (EPS部分) | 同花顺 | 无法获取一致预期EPS |
| get_hot_stocks | 同花顺 | 无法获取涨停热点 |
| get_northbound_flow (实时) | 同花顺 | 无法获取北向资金实时流 |
| get_concept_blocks | 百度股市通 | 无法获取概念板块 |
| get_fund_flow | 东方财富 | 无法获取资金流向 |
| get_dragon_tiger_board | 东方财富 | 无法获取龙虎榜 |
| get_lockup_expiry | 东方财富 | 无法获取解禁日历 |
| get_industry_comparison | 东方财富 | 无法获取行业对比 |

### 前瞻偏差风险

| 接口 | curr_date 过滤 | 风险 |
|------|---------------|------|
| get_stock_data | ✅ 按 end_date 过滤 | 低 |
| get_indicators | ✅ 按 curr_date 过滤 | 低 |
| get_fundamentals | ❌ 未使用 curr_date | 🟡 实时行情无历史快照 |
| get_balance_sheet | ✅ 按 curr_date 过滤 | 低 |
| get_cashflow | ✅ 按 curr_date 过滤 | 低 |
| get_income_statement | ✅ 按 curr_date 过滤 | 低 |
| get_news | ✅ 按日期范围过滤 | 低 |
| get_insider_transactions | ❌ 不支持 curr_date | 🟠 可能包含最新股东数据 |
| get_profit_forecast | ❌ 未使用 curr_date | 🟠 始终返回最新预测 |
| get_hot_stocks | ✅ 按 curr_date 查询 | 低 |
| get_northbound_flow | ✅ 实时数据 | 低 |
| get_concept_blocks | ❌ 不支持 curr_date | 🟡 板块归属变化较慢 |
| get_fund_flow | ✅ 实时+历史 | 低 |
| get_dragon_tiger_board | ✅ 按 trade_date 查询 | 低 |
| get_lockup_expiry | ✅ 按 trade_date 查询 | 低 |
| get_industry_comparison | ✅ 实时数据 | 低 |

---

## Vendor 路由机制

数据接口通过 `interface.py` 的 `route_to_vendor()` 函数进行路由分发：

```
用户调用 → route_to_vendor(method, *args, **kwargs)
         → 读取配置 get_vendor(category, method)
         → 按优先级尝试 vendor 实现
         → 失败时自动 fallback 到下一个可用 vendor
```

**默认配置**（`default_config.py`）:

```python
"data_vendors": {
    "core_stock_apis": "a_stock",
    "technical_indicators": "a_stock",
    "fundamental_data": "a_stock",
    "news_data": "a_stock",
    "signal_data": "a_stock",
}
```

**配置优先级**:
1. `tool_vendors[method]` — 工具级别配置（最高优先级）
2. `data_vendors[category]` — 分类级别配置
3. 默认值 `"a_stock"`

**Fallback 链**: 主 vendor 失败后，自动尝试该 method 的其他可用 vendor（如 `a_stock` → `yfinance` → `alpha_vantage`），仅 AlphaVantage 限速错误触发 fallback。

**A 股专属接口**（signal_data 类别下的 8 个接口）仅 `a_stock` vendor 可用，无 fallback。
