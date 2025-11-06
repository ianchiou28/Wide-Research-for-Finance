# 📊 Wide Research for Finance

> **让AI每小时为你读遍全球财经，抓住每一个市场信号**

一个基于AI的自动化财经情报系统，每小时从17个主流源采集200+条新闻，智能分析情绪、识别热点、提醒重大事件。

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![DeepSeek](https://img.shields.io/badge/AI-DeepSeek-orange.svg)](https://www.deepseek.com/)

---

## ✨ 为什么需要它？

📈 **信息过载时代**：每天有数千条财经新闻，你无法逐一阅读  
🤖 **AI助手**：自动筛选、分析、摘要，只给你最重要的  
🔔 **零延迟**：重大事件第一时间提醒，不错过任何机会  
💰 **极低成本**：每天仅需$0.3，相当于一杯咖啡的价格  

---

## 🚀 核心功能

### 📡 全球数据采集
- **17个主流财经源**：Bloomberg, WSJ, CNBC, Forbes, Financial Times...
- **多维度覆盖**：国际市场 + 专业分析 + 科技/加密货币
- **实时爬取**：每小时自动更新，永不错过突发新闻

### 🧠 AI智能分析
- **情绪识别**：自动判断市场情绪（积极/中性/消极）
- **实体提取**：识别公司、人物、政策、行业等关键信息
- **事件分类**：财报/并购/政策/IPO等类型自动标记
- **影响评估**：智能评估事件对市场的影响程度

### 📊 精美报告
```
【市场情绪总览】
- 共分析 197 条新闻
- 整体情绪: 积极 (情绪指数: 0.46)

【热点追踪】
  • 特朗普 (11次)  • 中国 (5次)  • AI (4次)

【重大事件】
  [Bloomberg] IPO
  Jio估值或达1700亿美元
  情绪: 积极 | 影响: 高
```

---

## ⚡ 快速开始

### 1️⃣ 克隆仓库
```bash
git clone https://github.com/ianchiou28/Wide-Research-for-Finance.git
cd Wide-Research-for-Finance
```

### 2️⃣ 安装依赖
```bash
pip install -r requirements.txt
```

### 3️⃣ 配置 API 密钥
```bash
cp .env.example .env
# 编辑 .env 文件，填入你的 DeepSeek API Key
DEEPSEEK_API_KEY=sk-your-key-here
```

> 🔑 获取 DeepSeek API: [https://platform.deepseek.com](https://platform.deepseek.com)

### 4️⃣ 运行
```bash
python main.py
```

选择运行模式：
- **模式 1**: 立即执行一次（测试）
- **模式 2**: 每小时自动运行 ⭐
- **模式 3**: 每天早上8点运行

---

## 📊 数据源覆盖

| 类别 | 数据源 | 数量 |
|------|------|------|
| 🌎 **国际财经** | Bloomberg, WSJ, CNBC, MarketWatch, Forbes, FT, Yahoo Finance, Investing.com | 9 |
| 📊 **专业分析** | Seeking Alpha, 雪球, Benzinga, The Motley Fool | 4 |
| 🔐 **加密/科技** | CoinDesk, TechCrunch, VentureBeat | 3 |
| 🏦**官方机构** | 美联储, SEC, 央行, 证监会 | 4 |

---

## 💸 成本分析

| 项目 | 每天 | 每月 |
|------|------|------|
| DeepSeek API | $0.20-0.30 | ~$10 |
| 服务器 | 免费（本地） | $0 |
| **总计** | **$0.30** | **$10** |

🎉 **相比Bloomberg Terminal ($2,000/月)，节省 99.5%**

---

## 🛠️ 高级配置

### 邮件推送（可选）
```env
EMAIL_FROM=your_email@gmail.com
EMAIL_PASSWORD=your_app_password  # Gmail应用专用密码
EMAIL_TO=recipient@email.com
```

### 自定义数据源
编辑 `config/sources.yaml` 添加你关注的RSS源：
```yaml
rss_sources:
  - name: "你的源"
    url: "https://example.com/rss"
    category: "custom"
```

---

## 🏗️ 技术架构

```mermaid
graph TB
    A[数据源层] --> B[数据采集层]
    B --> C[信息处理层]
    C --> D[知识整合层]
    D --> E[分析建议层]
    
    A1[17个RSS源<br/>Bloomberg/WSJ/CNBC] --> B
    A2[官方网站<br/>美联储/SEC/央行] --> B
    
    B --> B1[RSS解析器<br/>feedparser]
    B --> B2[网页爬虫<br/>BeautifulSoup]
    
    C --> C1[DeepSeek AI<br/>情感分析]
    C --> C2[实体识别<br/>NER]
    C --> C3[事件分类<br/>财报/并购/政策]
    
    D --> D1[情绪指数计算]
    D --> D2[热点实体统计]
    D --> D3[影响力评分]
    
    E --> E1[每小时报告]
    E --> E2[邮件推送]
    E --> E3[本地存储]
    
    style A fill:#e1f5ff
    style B fill:#fff3e0
    style C fill:#f3e5f5
    style D fill:#e8f5e9
    style E fill:#fce4ec
```

### 核心技术栈

| 层级 | 技术选型 | 说明 |
|------|---------|------|
| **数据采集** | feedparser, requests, BeautifulSoup | RSS订阅 + 网页爬虫 |
| **任务调度** | schedule | 轻量级定时任务 |
| **AI处理** | DeepSeek API | 情感分析、实体提取、事件分类 |
| **数据存储** | 文件系统 (未来: SQLite) | 报告本地保存 |
| **通知推送** | smtplib | Gmail邮件发送 |

### 数据流程

```
[RSS源] → [采集] → [原始文本]
                      ↓
              [DeepSeek AI分析]
                      ↓
        [结构化数据: 情感/实体/事件]
                      ↓
              [指标计算与聚合]
                      ↓
            [生成报告] → [邮件/本地]
```

---

## 📈 开发路线图

### ✅ 已完成 (MVP v1.0)
- [x] 基础RSS采集与分析
- [x] 每小时自动运行
- [x] 官方网站爬虫
- [x] DeepSeek AI集成
- [x] 情感分析与实体识别
- [x] 自动报告生成

### 🚧 进行中 (v1.1)
- [ ] SQLite历史数据存储
- [ ] 情绪指数时间序列图表
- [ ] 数据去重与增量更新

### 🔮 未来计划 (v2.0)
- [ ] 模式识别与投资建议
- [ ] Web仪表盘 (Streamlit)
- [ ] 知识图谱 (Neo4j)
- [ ] 多语言支持
- [ ] 自定义告警规则

---

## 👥 适用人群

✅ **个人投资者** - 每天获取精炼的市场情报  
✅ **量化交易员** - 实时捕捉市场情绪变化  
✅ **财经分析师** - 自动化信息收集与整理  
✅ **创业者** - 关注行业动态与竞争对手  

---

## ❓ 常见问题

<details>
<summary><b>Q: 为什么选择DeepSeek而不是GPT-4？</b></summary>
<br>
DeepSeek性价比极高，成本仅为GPT-4的10%，且在中文财经分析上表现优秀。
</details>

<details>
<summary><b>Q: 需要VPN吗？</b></summary>
<br>
国际源（Bloomberg, WSJ）可能需要，但系统已内置容错机制，单个源失败不影响整体运行。
</details>

<details>
<summary><b>Q: 可以商用吗？</b></summary>
<br>
MIT协议开源，可自由使用和修改。但请注意数据源的版权政策。
</details>

---

## 🎯 性能指标

| 指标 | 数值 |
|------|------|
| 数据源数量 | 17个RSS + 4个网站 |
| 每小时采集量 | 200-300条新闻 |
| AI处理速度 | ~20条/批次 |
| 报告生成时间 | <30秒 |
| API成本 | $0.01-0.02/小时 |
| 内存占用 | <100MB |

---

## 👏 贡献

欢迎 PR! 如果你有好的想法或发现了bug，请提交 Issue。

---

## 📝 许可证

MIT License - 详见 [LICENSE](LICENSE)

---

## ⭐ Star History

如果这个项目对你有帮助，请给个 Star ⭐！

---

<p align="center">
  <b>由 <a href="https://github.com/ianchiou28">@ianchiou28</a> 开发维护</b><br>
  <sub>基于 DeepSeek AI 驱动 | 每天仅需 $0.3</sub>
</p>
