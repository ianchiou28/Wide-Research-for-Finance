# Wide Research for Finance - MVP v1.0

自动化财经新闻分析与每日简报系统

## 功能特性

- ✅ 自动采集5个主流财经RSS源
- ✅ AI驱动的新闻摘要与情感分析
- ✅ 实体识别与事件分类
- ✅ 每日自动生成简报
- ✅ 邮件发送或本地保存

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

复制 `.env.example` 为 `.env` 并填写：

```
DEEPSEEK_API_KEY=sk-xxx                  # 必填
EMAIL_FROM=your_email@gmail.com          # 可选
EMAIL_PASSWORD=your_app_password         # 可选
EMAIL_TO=recipient@email.com             # 可选
```

**注意**: 
- Gmail需要使用应用专用密码（不是账户密码）
- 如不配置邮件，报告将保存到 `data/reports/` 目录

### 3. 运行程序

```bash
python main.py
```

选择运行模式：
- **模式1**: 立即执行一次（测试用）
- **模式2**: 每小时自动执行
- **模式3**: 每天早上8点自动执行

## 数据源

当前配置的RSS源：
- Reuters Business & Markets
- Bloomberg Markets
- CNBC Top News
- Financial Times

可在 `config/sources.yaml` 中自定义添加更多源。

## 报告示例

```
============================================================
财经新闻每日简报 - 2024年01月15日
============================================================

【市场情绪总览】
- 共分析 45 条新闻
- 整体情绪: 中性 (情绪指数: 0.12)

【热点追踪】
今日最受关注的主体：
  • 美联储 (提及12次)
  • 苹果 (提及8次)
  • 特斯拉 (提及6次)

【重大事件提醒】
  [Reuters] 政策
  标题: Fed signals potential rate cuts in 2024
  摘要: 美联储暗示2024年可能降息
  情绪: 积极
  ...
```

## 成本估算

- GPT-4o-mini: 约 $0.30/天（处理100篇文章）
- 月成本: ~$10

## 下一步优化

- [ ] 添加SQLite数据库存储历史数据
- [ ] 生成情绪指数时间序列图表
- [ ] 添加网页爬虫（公司公告等）
- [ ] 实现模式识别与投资建议

## 故障排查

**问题**: RSS源无法访问
- 检查网络连接
- 某些源可能需要VPN

**问题**: DeepSeek API错误
- 确认API密钥正确
- 检查账户余额

**问题**: 邮件发送失败
- Gmail需启用"两步验证"并生成应用专用密码
- 或直接查看 `data/reports/` 目录中的本地报告
