# 🚀 Wide Research for Finance — 分阶段改进计划

> **目标站点**: http://finai.org.cn/  
> **部署方式**: Docker Compose (3容器: app + collector + nginx)  
> **制定日期**: 2026-02-08  

---

## 📋 改进总览

| 阶段 | 主题 | 耗时估计 | 优先级 |
|------|------|----------|--------|
| **Phase 1** | 🔴 安全加固 & 生产就绪 | 1-2天 | **紧急** |
| **Phase 2** | 🟡 工程化 & 可维护性 | 3-5天 | **重要** |
| **Phase 3** | 🟢 性能优化 & 可扩展 | 3-5天 | **推荐** |
| **Phase 4** | 🔵 金融专业性提升 | 持续 | **长期** |

---

## 🔴 Phase 1: 安全加固 & 生产就绪（1-2天）

### 1.1 ❗ 关闭生产环境 Debug 模式

**现状问题**: `web_app.py` 第1490行 `debug=True` 硬编码，会暴露堆栈信息和开启热重载，**严重安全隐患**。

**改进**:
```python
# web_app.py 末尾
if __name__ == '__main__':
    init_database()
    is_debug = os.getenv('FLASK_DEBUG', 'false').lower() == 'true'
    app.run(
        debug=is_debug,
        host='0.0.0.0',
        port=5000,
        threaded=True
    )
```

**Docker环境变量**: 默认不设置 `FLASK_DEBUG`，仅开发时启用。

---

### 1.2 ❗ 使用 Gunicorn 替代 Flask 内置服务器

**现状问题**: Flask 内置服务器是单线程开发服务器，不适合生产。

**改进**:
```dockerfile
# Dockerfile 中增加
RUN pip install gunicorn

# 启动命令改为
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "--threads", "2", "--timeout", "120", "web_app:app"]
```

```txt
# requirements.txt 增加
gunicorn==21.2.0
```

---

### 1.3 ❗ 配置 HTTPS (Let's Encrypt)

**现状问题**: http://finai.org.cn/ 全站明文传输，用户数据（如果将来有登录）完全裸奔。

**改进方案**: 在 docker-compose.yml 中加入 certbot 容器：

```yaml
# docker-compose.yml 新增
  certbot:
    image: certbot/certbot
    volumes:
      - ./certbot/conf:/etc/letsencrypt
      - ./certbot/www:/var/www/certbot
    entrypoint: "/bin/sh -c 'trap exit TERM; while :; do certbot renew; sleep 12h & wait $${!}; done;'"
```

```nginx
# nginx.conf 更新
server {
    listen 80;
    server_name finai.org.cn www.finai.org.cn;
    
    # ACME 验证
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }
    
    # 强制跳转 HTTPS
    location / {
        return 301 https://$host$request_uri;
    }
}

server {
    listen 443 ssl;
    server_name finai.org.cn www.finai.org.cn;
    
    ssl_certificate /etc/letsencrypt/live/finai.org.cn/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/finai.org.cn/privkey.pem;
    
    # 安全头
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000" always;
    
    location / {
        proxy_pass http://app;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # 静态资源缓存
    location /assets/ {
        proxy_pass http://app;
        expires 7d;
        add_header Cache-Control "public, immutable";
    }
}
```

---

### 1.4 ❗ API 访问控制 & 速率限制

**现状问题**: 所有API无需认证，任何人可以调用 `/api/backtest/run`、`/api/monthly/chat` 等敏感接口消耗LLM额度。

**改进**:
```txt
# requirements.txt 增加
flask-limiter==3.5.0
```

```python
# web_app.py 添加速率限制
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per hour", "50 per minute"]
)

# 对消耗LLM的接口严格限制
@app.route('/api/monthly/chat', methods=['POST'])
@limiter.limit("10 per hour")
def api_monthly_chat():
    ...

@app.route('/api/backtest/run', methods=['POST'])
@limiter.limit("3 per hour")
def run_backtest():
    ...

@app.route('/api/monthly/analysis')
@limiter.limit("5 per hour")  
def api_monthly_analysis():
    ...
```

**可选**: 对管理操作增加 API Key 认证：
```python
from functools import wraps

def require_api_key(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        api_key = request.headers.get('X-API-Key') or request.args.get('api_key')
        if api_key != os.getenv('ADMIN_API_KEY'):
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated

@app.route('/api/backtest/run', methods=['POST'])
@require_api_key
def run_backtest():
    ...
```

---

### 1.5 修复路径遍历风险

**现状问题**: `/api/daily_summary?file=../../.env` 等接口直接拼接文件路径。

**改进**:
```python
import re

def safe_filename(filename):
    """防止路径遍历"""
    if not filename or not re.match(r'^[a-zA-Z0-9_\-\.]+$', filename):
        return None
    return filename

@app.route('/api/daily_summary')
def daily_summary():
    requested_file = request.args.get('file')
    if requested_file:
        requested_file = safe_filename(requested_file)
        if not requested_file:
            return jsonify({'error': '无效的文件名'}), 400
        ...
```

---

### 1.6 Docker 健康检查 & 资源限制

```yaml
# docker-compose.yml 改进
services:
  finance-app:
    build: .
    ports:
      - "8080:5000"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/api/latest"]
      interval: 60s
      timeout: 10s
      retries: 3
      start_period: 30s
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: '1.0'
    environment:
      - TZ=Asia/Shanghai
      - DEEPSEEK_API_KEY=${DEEPSEEK_API_KEY}
      - FLASK_DEBUG=false
    volumes:
      - ./data:/app/data
      - ./.env:/app/.env
    restart: unless-stopped

  finance-collector:
    build: .
    command: python main.py
    healthcheck:
      test: ["CMD", "python", "-c", "import os; exit(0)"]
      interval: 300s
      timeout: 10s
      retries: 3
    deploy:
      resources:
        limits:
          memory: 1G
          cpus: '1.0'
    ...
```

---

## 🟡 Phase 2: 工程化 & 可维护性（3-5天）

### 2.1 引入 Python logging 替代 print

**现状**: 全项目使用 `print()` 输出，无日志级别、无文件保存、无结构化。

**改进**: 创建统一日志模块：

```python
# src/logger.py
import logging
import os
from logging.handlers import RotatingFileHandler

def setup_logger(name='finance', level=None):
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    
    level = level or os.getenv('LOG_LEVEL', 'INFO')
    logger.setLevel(getattr(logging, level))
    
    formatter = logging.Formatter(
        '%(asctime)s [%(name)s] %(levelname)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 控制台
    console = logging.StreamHandler()
    console.setFormatter(formatter)
    logger.addHandler(console)
    
    # 文件（10MB轮转，保留5个）
    os.makedirs('data/logs', exist_ok=True)
    file_handler = RotatingFileHandler(
        'data/logs/app.log', maxBytes=10*1024*1024, backupCount=5, encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    return logger
```

**使用**: 逐步替换所有 `print()`：
```python
from logger import setup_logger
logger = setup_logger('collector')
logger.info(f"成功采集 {len(articles)} 条新闻")
logger.error(f"采集失败: {e}", exc_info=True)
```

---

### 2.2 拆分 web_app.py（1495行 → 多文件）

**当前**: 所有路由、业务逻辑混在一个文件。

**目标结构**:
```
web/
├── __init__.py          # Flask app 工厂函数
├── config.py            # 配置类
├── middleware.py         # 限流、认证、CORS
├── routes/
│   ├── __init__.py
│   ├── report.py        # /api/latest, /api/report/*, /api/summary/*
│   ├── stock.py         # /api/stocks/*, /api/watchlist/*
│   ├── crypto.py        # /api/crypto/*
│   ├── analysis.py      # /api/weekly/*, /api/monthly/*
│   ├── backtest.py      # /api/backtest/*
│   └── hot_search.py    # /api/hot-searches/*
├── services/
│   ├── report_service.py
│   ├── stock_service.py
│   └── cache_service.py
└── utils/
    ├── file_helper.py   # safe_filename, get_latest_file
    └── response.py      # 统一响应格式
```

**实施**: 使用 Flask Blueprint：
```python
# web/routes/report.py
from flask import Blueprint, jsonify
report_bp = Blueprint('report', __name__, url_prefix='/api')

@report_bp.route('/latest')
def api_latest():
    ...

# web/__init__.py
def create_app():
    app = Flask(__name__)
    from web.routes.report import report_bp
    from web.routes.stock import stock_bp
    app.register_blueprint(report_bp)
    app.register_blueprint(stock_bp)
    return app
```

---

### 2.3 统一配置管理

**当前**: API Key、模型名、超时时间分散在各文件中硬编码。

**改进**:
```python
# config/settings.py
import os
from dotenv import load_dotenv
load_dotenv()

class Config:
    # LLM
    LLM_API_KEY = os.getenv('DEEPSEEK_API_KEY')
    LLM_BASE_URL = os.getenv('LLM_BASE_URL', 'https://api.deepseek.com')
    LLM_MODEL = os.getenv('LLM_MODEL', 'deepseek-chat')
    LLM_TIMEOUT = int(os.getenv('LLM_TIMEOUT', '120'))
    
    # 数据采集
    FETCH_TIMEOUT = int(os.getenv('FETCH_TIMEOUT', '15'))
    MAX_PER_SOURCE = int(os.getenv('MAX_PER_SOURCE', '15'))
    
    # 邮件
    EMAIL_FROM = os.getenv('EMAIL_FROM')
    EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')
    EMAIL_TO = os.getenv('EMAIL_TO')
    SMTP_SERVER = os.getenv('SMTP_SERVER')
    SMTP_PORT = int(os.getenv('SMTP_PORT', '465'))
    
    # Web
    FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'false').lower() == 'true'
    SECRET_KEY = os.getenv('SECRET_KEY', 'change-me-in-production')
    ADMIN_API_KEY = os.getenv('ADMIN_API_KEY', '')
```

**更新 .env.example**:
```env
# LLM 配置
DEEPSEEK_API_KEY=sk-your-key
LLM_MODEL=deepseek-chat
LLM_TIMEOUT=120

# 邮件配置
EMAIL_FROM=
EMAIL_PASSWORD=
EMAIL_TO=

# 安全配置
ADMIN_API_KEY=your-random-api-key
SECRET_KEY=your-flask-secret

# 可选
FLASK_DEBUG=false
LOG_LEVEL=INFO
```

---

### 2.4 数据去重

**现状**: `database.py` 定义了 `url_hash` 字段，但 `collector.py` 从未使用。

**改进**:
```python
# src/collector.py 添加去重
import hashlib

class DataCollector:
    def __init__(self, ...):
        ...
        self._seen_hashes = set()
        self._load_recent_hashes()
    
    def _url_hash(self, url: str) -> str:
        return hashlib.md5(url.encode()).hexdigest()
    
    def _load_recent_hashes(self):
        """从数据库加载最近24h的URL hash"""
        try:
            from database import get_recent_news_hashes
            self._seen_hashes = set(get_recent_news_hashes(hours=24))
        except:
            pass
    
    def _is_duplicate(self, url: str) -> bool:
        return self._url_hash(url) in self._seen_hashes
```

**预期效果**: 减少30-50%的LLM分析调用，直接节省API费用。

---

### 2.5 添加单元测试框架

```txt
# requirements-dev.txt
pytest==8.0.0
pytest-mock==3.12.0
pytest-cov==4.1.0
```

**基础测试**:
```
tests/
├── conftest.py                # 公共fixtures
├── test_collector.py          # 采集器测试
├── test_processor.py          # NLP处理测试（mock LLM）
├── test_report_generator.py   # 报告生成测试
├── test_web_app.py            # API端点测试
└── test_backtester.py         # 回测逻辑测试
```

```python
# tests/test_processor.py 示例
def test_extract_json_normal():
    processor = NLPProcessor.__new__(NLPProcessor)
    result = processor._extract_json('[{"index": 1, "summary": "test"}]')
    assert len(result) == 1
    assert result[0]['index'] == 1

def test_extract_json_truncated():
    processor = NLPProcessor.__new__(NLPProcessor)
    # 模拟LLM返回被截断的JSON
    result = processor._extract_json('[{"index": 1, "summary": "test"}, {"index": 2')
    assert result is not None  # 应该能恢复部分数据
```

---

### 2.6 添加 GitHub Actions CI/CD

```yaml
# .github/workflows/deploy.yml
name: Deploy to Server

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.9'
      - run: pip install -r requirements.txt -r requirements-dev.txt
      - run: pytest tests/ --cov=src --cov-report=xml
  
  deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - name: Deploy via SSH
        uses: appleboy/ssh-action@v1
        with:
          host: ${{ secrets.SERVER_HOST }}
          username: ${{ secrets.SERVER_USER }}
          key: ${{ secrets.SSH_KEY }}
          script: |
            cd /opt/finance
            git pull origin main
            docker compose build --no-cache
            docker compose up -d
            docker compose logs --tail=20
```

---

## 🟢 Phase 3: 性能优化 & 可扩展（3-5天）

### 3.1 并发采集（最大收益）

**现状**: 17个RSS源 + 6个网站**串行**请求，耗时可能超过3分钟。

**改进**:
```python
# src/collector.py
from concurrent.futures import ThreadPoolExecutor, as_completed

class DataCollector:
    def fetch_latest(self, hours=24, max_per_source=15) -> List[Dict]:
        articles = []
        
        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = {}
            for source in self.config.get('rss_sources', []):
                future = executor.submit(self._fetch_single_source, source, hours, max_per_source)
                futures[future] = source['name']
            
            for future in as_completed(futures, timeout=60):
                try:
                    result = future.result(timeout=20)
                    articles.extend(result)
                except Exception as e:
                    logger.warning(f"{futures[future]} 采集失败: {e}")
        
        return articles
```

**预期效果**: 采集时间从 3min → 20s。

---

### 3.2 内存缓存层

**现状**: 每次API请求都重新 `glob.glob()` + 读文件 + 解析。

**改进**:
```python
# src/cache.py
from functools import lru_cache
from datetime import datetime, timedelta
import time

class SimpleCache:
    """简单的TTL内存缓存"""
    def __init__(self):
        self._cache = {}
    
    def get(self, key, ttl_seconds=300):
        if key in self._cache:
            value, timestamp = self._cache[key]
            if time.time() - timestamp < ttl_seconds:
                return value
            del self._cache[key]
        return None
    
    def set(self, key, value):
        self._cache[key] = (value, time.time())
    
    def invalidate(self, key=None):
        if key:
            self._cache.pop(key, None)
        else:
            self._cache.clear()

cache = SimpleCache()

# 使用示例
@app.route('/api/latest')
def api_latest():
    cached = cache.get('latest_report', ttl_seconds=300)  # 5分钟缓存
    if cached:
        return jsonify(cached)
    
    data = _build_latest_data()
    cache.set('latest_report', data)
    return jsonify(data)
```

---

### 3.3 Nginx 静态资源优化

```nginx
# nginx.conf 增强
http {
    # 启用 gzip
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css application/json application/javascript text/xml;
    
    # 代理缓存
    proxy_cache_path /tmp/nginx_cache levels=1:2 keys_zone=api_cache:10m max_size=100m inactive=60m;
    
    server {
        ...
        
        # 静态资源 - 长期缓存
        location /assets/ {
            proxy_pass http://app;
            expires 30d;
            add_header Cache-Control "public, immutable";
        }
        
        # API 短期缓存（只读接口）
        location /api/latest {
            proxy_pass http://app;
            proxy_cache api_cache;
            proxy_cache_valid 200 5m;
            proxy_cache_use_stale error timeout;
            add_header X-Cache-Status $upstream_cache_status;
        }
    }
}
```

---

### 3.4 SQLite → SQLite WAL 模式（短期）/ PostgreSQL（长期）

**短期**: 启用 WAL 模式支持并发读写：
```python
# src/database.py
def get_connection():
    conn = sqlite3.connect(get_db_path())
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    conn.row_factory = sqlite3.Row
    ...
```

**长期**: docker-compose 中加入 PostgreSQL：
```yaml
services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: finance
      POSTGRES_USER: finance
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready"]
      interval: 10s

volumes:
  pgdata:
```

---

### 3.5 schedule → APScheduler

**现状**: `schedule` 单线程阻塞，一个任务超时会拖延全部。

**改进**:
```python
# main.py
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.executors.pool import ThreadPoolExecutor

scheduler = BackgroundScheduler(
    executors={'default': ThreadPoolExecutor(4)},
    job_defaults={'coalesce': True, 'max_instances': 1, 'misfire_grace_time': 300}
)

scheduler.add_job(run_daily_report, 'cron', minute=0)                    # 每小时
scheduler.add_job(generate_and_send_summary, 'cron', hour='8,20')        # 日报
scheduler.add_job(run_weekly_report_script, 'cron', hour='8,20')         # 周报
scheduler.add_job(run_monthly_report_script, 'cron', hour=9)             # 月报
scheduler.add_job(run_backtest_verification, 'cron', hour=21)            # 回测
```

```txt
# requirements.txt 替换 schedule
APScheduler==3.10.4
```

---

## 🔵 Phase 4: 金融专业性提升（持续迭代）

### 4.1 情绪评分校准

- 对历史情绪分 vs 实际市场表现做回归分析
- 引入时间衰减：`weight = exp(-0.1 * hours_ago)`
- 不同来源不同权重（Bloomberg > 百度新闻）

### 4.2 量价数据整合

利用已有的 `akshare`/`yfinance`，在 LLM prompt 中加入市场上下文：

```python
prompt = f"""分析以下新闻，并结合市场数据判断影响：

【市场背景】
- 上证指数：今日涨跌 {change}%，成交量 {volume}
- 北向资金：净流入 {north_flow} 亿
- VIX恐慌指数：{vix}

【新闻内容】
{articles_text}
"""
```

### 4.3 回测指标增强

```python
class BacktestMetrics:
    def calculate(self, predictions, actuals):
        return {
            'accuracy': self._accuracy(predictions, actuals),
            'precision': self._precision(predictions, actuals),
            'recall': self._recall(predictions, actuals),
            'sharpe_ratio': self._sharpe_ratio(predictions, actuals),
            'max_drawdown': self._max_drawdown(predictions, actuals),
            'information_coefficient': self._ic(predictions, actuals),
            'benchmark_comparison': self._vs_random(predictions, actuals),
            'sample_size_test': self._statistical_significance(len(predictions)),
        }
```

### 4.4 Prompt Engineering 优化

- 使用 Few-shot 示例提升输出一致性
- 分事件类型使用差异化 prompt（央行决议 / 财报 / 地缘政治）
- 引入 Chain-of-Thought：要求 LLM 先推理过程再给结论
- 定期根据回测结果自动调优 prompt

### 4.5 多模型集成

```python
class EnsembleAnalyzer:
    """多模型投票，提升情绪评分可靠性"""
    
    def analyze(self, article):
        results = []
        # 用不同temperature/prompt获取多个结果
        for temp in [0.1, 0.3, 0.5]:
            result = self._call_llm(article, temperature=temp)
            results.append(result)
        
        # 取中位数作为最终评分
        sentiment = statistics.median([r['sentiment'] for r in results])
        confidence = 1 - statistics.stdev([r['sentiment'] for r in results])
        
        return {'sentiment': sentiment, 'confidence': confidence}
```

---

## 🛠️ 实施优先级路线图

```
Week 1 (Phase 1 - 安全加固)
├── Day 1: 关闭debug + Gunicorn + 速率限制 + 路径校验
├── Day 2: HTTPS配置 + Docker健康检查 + 资源限制
│
Week 2-3 (Phase 2 - 工程化)
├── Day 3: logging模块 + 统一配置管理
├── Day 4-5: web_app.py拆分为Blueprint
├── Day 6: 数据去重 + .env.example完善
├── Day 7: 基础测试框架 + CI/CD
│
Week 3-4 (Phase 3 - 性能优化)
├── Day 8: 并发采集（ThreadPoolExecutor）
├── Day 9: 内存缓存 + Nginx优化
├── Day 10: SQLite WAL + APScheduler
│
Week 5+ (Phase 4 - 持续迭代)
├── 情绪校准 + 量价整合
├── 回测指标增强
├── Prompt 优化
└── 多模型集成
```

---

## 📊 预期改进效果

| 指标 | 当前 | Phase 1后 | Phase 3后 |
|------|------|-----------|-----------|
| **安全评分** | 3/10 | 7/10 | 8/10 |
| **API响应时间** | ~2s | ~1.5s | ~200ms (缓存) |
| **数据采集耗时** | ~3min | ~3min | ~20s |
| **LLM月度开支** | ~$3 | ~$3 | ~$1.5 (去重) |
| **故障可观测性** | 无 | 日志文件 | 结构化日志 |
| **部署流程** | 手动SSH | 手动SSH | Git push自动 |

---

## ⚠️ 注意事项

1. **每个Phase独立可部署**：不要一次性改完，每完成一个阶段就部署验证
2. **数据备份优先**：改动前先备份 `data/` 目录（`tar -czf backup_$(date +%Y%m%d).tar.gz data/`）
3. **灰度发布**：大改动时可以先在 `docker-compose.override.yml` 中测试
4. **监控先行**：Phase 2 的 logging 完成后，后续改动都有迹可循
