# 项目改进计划 & API文档

## 一、项目架构升级概述

### 新增后端模块

| 模块 | 文件 | 功能 |
|------|------|------|
| 数据库 | `src/database.py` | SQLite存储，支持新闻/报告/自选股/预测记录 |
| 实时采集 | `src/realtime_collector.py` | 同花顺、东方财富、新浪、金十实时快讯 |
| 热搜采集 | `src/hot_search.py` | 微博/头条/知乎/百度/抖音热搜聚合 |
| 个股追踪 | `src/stock_tracker.py` | A股/港股/美股行情、新闻、公告 |
| 虚拟货币 | `src/crypto_collector.py` | CoinGecko/币安行情、恐惧贪婪指数 |
| 回测系统 | `src/backtester.py` | 基于新闻的预测验证和策略回测 |

---

## 二、新增API接口文档

### 2.1 历史报告

#### 获取历史报告列表
```
GET /api/reports/history?page=1&per_page=20&type=all
```
- `type`: `all` | `hourly` | `daily` | `weekly`

响应示例:
```json
{
  "total": 100,
  "page": 1,
  "per_page": 20,
  "pages": 5,
  "data": [
    {
      "id": "20251127_120000",
      "type": "hourly",
      "title": "每小时简报",
      "timestamp": "2025-11-27T12:00:00"
    }
  ]
}
```

#### 获取报告详情
```
GET /api/reports/{report_id}?type=hourly
```

---

### 2.2 热搜功能

#### 获取聚合财经热搜
```
GET /api/hot-searches?finance_only=true
```

#### 获取指定平台热搜
```
GET /api/hot-searches?platform=weibo&finance_only=true
```
- `platform`: `weibo` | `toutiao` | `zhihu` | `baidu` | `douyin`

#### 获取所有平台热搜
```
GET /api/hot-searches/all?finance_only=true
```

响应示例:
```json
{
  "weibo": [{"rank": 1, "title": "A股大涨", "hot_value": 5000000}],
  "toutiao": [...],
  "zhihu": [...]
}
```

---

### 2.3 个股追踪

#### 搜索股票
```
GET /api/stocks/search?q=茅台
```

#### 获取实时行情
```
GET /api/stocks/{symbol}/quote
```
- `symbol`: 股票代码，如 `600519`(A股), `AAPL`(美股), `00700`(港股)

响应示例:
```json
{
  "symbol": "600519",
  "name": "贵州茅台",
  "market": "sh",
  "price": 1800.50,
  "change_pct": 2.35,
  "volume": 1234567,
  "timestamp": "2025-11-27T14:30:00"
}
```

#### 获取个股新闻
```
GET /api/stocks/{symbol}/news?name=茅台&limit=20
```

#### 获取公司公告
```
GET /api/stocks/{symbol}/announcements?limit=10
```

---

### 2.4 自选股管理

#### 获取自选股列表
```
GET /api/watchlist?category=stock
```
- `category`: `stock` | `crypto` | 不传则返回全部

#### 添加自选股
```
POST /api/watchlist
Content-Type: application/json

{
  "symbol": "600519",
  "name": "贵州茅台",
  "market": "sh",
  "category": "stock"
}
```

#### 移除自选股
```
DELETE /api/watchlist/{symbol}
```

---

### 2.5 虚拟货币

#### 获取行情数据
```
GET /api/crypto/market?symbols=BTC,ETH,SOL,DOGE
```

响应示例:
```json
{
  "data": [
    {
      "symbol": "BTC",
      "name": "Bitcoin",
      "price_usd": 95000,
      "change_24h": 2.5,
      "market_cap": 1800000000000
    }
  ]
}
```

#### 获取全球市场数据
```
GET /api/crypto/global
```

#### 获取热门币种
```
GET /api/crypto/trending
```

#### 获取恐惧贪婪指数
```
GET /api/crypto/fear-greed
```

响应示例:
```json
{
  "value": 75,
  "classification": "Greed",
  "timestamp": "2025-11-27T00:00:00"
}
```

#### 获取币种详情
```
GET /api/crypto/{coin_id}
```
- `coin_id`: CoinGecko ID，如 `bitcoin`, `ethereum`

---

### 2.6 实时快讯

#### 获取实时数据
```
GET /api/realtime
```

响应示例:
```json
{
  "data": [
    {
      "title": "央行宣布降准0.25个百分点",
      "source": "同花顺7x24",
      "is_realtime": true,
      "published_at": "2025-11-27T14:30:00"
    }
  ],
  "timestamp": "2025-11-27T14:35:00"
}
```

---

### 2.7 回测系统

#### 获取回测报告
```
GET /api/backtest/report
```

#### 回测情绪策略
```
GET /api/backtest/strategy
```

响应示例:
```json
{
  "strategy_name": "情绪驱动策略",
  "total_signals": 100,
  "buy_signals": 30,
  "sell_signals": 25,
  "hold_signals": 45,
  "signals": [...]
}
```

---

## 三、前端页面规划

### 建议新增页面

| 页面 | 路由 | 功能 |
|------|------|------|
| 历史报告 | `/history` | 查看历史报告，支持日历选择 |
| 热搜 | `/hot` | 展示各平台财经热搜 |
| 自选股 | `/watchlist` | 管理自选股，查看行情和新闻 |
| 个股详情 | `/stock/:symbol` | 个股行情、新闻、公告 |
| 虚拟货币 | `/crypto` | 加密货币行情和市场数据 |
| 回测 | `/backtest` | 策略回测结果展示 |
| 设置 | `/settings` | 系统配置 |

### 首页组件增强建议

1. **实时快讯滚动条** - 顶部或侧边滚动显示最新快讯
2. **热搜标签云** - 展示当前财经热点
3. **自选股卡片** - 快速查看关注的股票行情
4. **加密货币迷你面板** - 显示BTC/ETH等主流币价格

---

## 四、数据库表结构

```sql
-- 新闻表
news (id, url_hash, title, content, source, sentiment_*, published_at, ...)

-- 报告表  
reports (id, report_type, content, sentiment_*, created_at, ...)

-- 自选股表
watchlist (id, symbol, name, market, category, added_at)

-- 热搜表
hot_searches (id, platform, rank, title, hot_value, collected_at)

-- 加密货币价格
crypto_prices (id, symbol, price_usd, change_24h, timestamp)

-- 预测记录（回测用）
predictions (id, symbol, predicted_direction, actual_direction, is_correct)
```

---

## 五、启动说明

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 初始化数据库（首次运行自动执行）
python src/database.py

# 3. 启动Web服务
python web_app.py

# 4. 测试新模块
python src/realtime_collector.py  # 测试实时采集
python src/hot_search.py          # 测试热搜采集
python src/stock_tracker.py       # 测试个股追踪
python src/crypto_collector.py    # 测试虚拟货币
python src/backtester.py          # 测试回测系统
```

---

## 六、解决九阳豆浆案例的问题

针对"九阳出新产品导致股价大涨但项目未及时捕获"的问题，新架构提供以下解决方案：

1. **公司公告监控** - `stock_tracker.get_company_announcements()` 可获取新产品发布等官方公告

2. **实时快讯** - `realtime_collector` 接入同花顺/东方财富7x24快讯，延迟降至分钟级

3. **自选股追踪** - 将关注的股票加入自选股，系统自动聚合其相关新闻和公告

4. **热搜监控** - 通过热搜发现市场热点，关联到具体股票

使用示例:
```python
# 1. 添加九阳到自选股
POST /api/watchlist
{"symbol": "002242", "name": "九阳股份", "market": "sz"}

# 2. 获取九阳相关公告
GET /api/stocks/002242/announcements

# 3. 获取九阳相关新闻
GET /api/stocks/002242/news?name=九阳

# 4. 通过热搜发现热点
GET /api/hot-searches?finance_only=true
```
