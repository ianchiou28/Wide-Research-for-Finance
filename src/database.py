"""
数据库模型和操作
使用 SQLite 作为本地存储，方便开发和部署
如需生产环境可切换到 PostgreSQL
"""

import sqlite3
import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from contextlib import contextmanager

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'finance.db')

def get_db_path():
    """获取数据库路径，确保目录存在"""
    db_dir = os.path.dirname(DB_PATH)
    if not os.path.exists(db_dir):
        os.makedirs(db_dir)
    return DB_PATH

@contextmanager
def get_connection():
    """获取数据库连接的上下文管理器"""
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row  # 使查询结果可以用字段名访问
    try:
        yield conn
    finally:
        conn.close()

def init_database():
    """初始化数据库表结构"""
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # 新闻表 - 存储采集的原始新闻
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS news (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url_hash TEXT UNIQUE,
                title TEXT NOT NULL,
                content TEXT,
                summary TEXT,
                source TEXT,
                category TEXT,
                url TEXT,
                published_at DATETIME,
                collected_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                sentiment_overall REAL DEFAULT 0,
                sentiment_cn REAL DEFAULT 0,
                sentiment_us REAL DEFAULT 0,
                impact_level TEXT,
                event_type TEXT,
                is_processed INTEGER DEFAULT 0,
                related_stocks TEXT
            )
        ''')
        
        # 报告表 - 存储生成的报告
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                report_type TEXT NOT NULL,
                title TEXT,
                content TEXT,
                summary TEXT,
                sentiment_overall REAL DEFAULT 0,
                sentiment_cn REAL DEFAULT 0,
                sentiment_us REAL DEFAULT 0,
                total_news INTEGER DEFAULT 0,
                hot_topics TEXT,
                major_events TEXT,
                stocks TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                file_path TEXT
            )
        ''')
        
        # 自选股表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS watchlist (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL UNIQUE,
                name TEXT,
                market TEXT,
                category TEXT,
                added_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                is_active INTEGER DEFAULT 1
            )
        ''')
        
        # 股票数据表 - 存储行情数据
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS stock_prices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                price REAL,
                change_pct REAL,
                volume INTEGER,
                market_cap REAL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 虚拟货币表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS crypto_prices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                name TEXT,
                price_usd REAL,
                price_cny REAL,
                change_24h REAL,
                volume_24h REAL,
                market_cap REAL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 热搜表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS hot_searches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                platform TEXT NOT NULL,
                rank INTEGER,
                title TEXT NOT NULL,
                url TEXT,
                hot_value INTEGER,
                category TEXT,
                collected_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 预测记录表 - 用于回测
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                prediction_type TEXT,
                predicted_direction TEXT,
                confidence REAL,
                predicted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                target_date DATE,
                actual_direction TEXT,
                actual_change REAL,
                is_correct INTEGER,
                verified_at DATETIME
            )
        ''')
        
        # 创建索引
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_news_url_hash ON news(url_hash)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_news_published ON news(published_at)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_news_source ON news(source)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_reports_type ON reports(report_type)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_reports_created ON reports(created_at)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_watchlist_symbol ON watchlist(symbol)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_hot_platform ON hot_searches(platform, collected_at)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_predictions_symbol ON predictions(symbol)')
        
        conn.commit()
        print("✓ 数据库初始化完成")


# ============== 新闻相关操作 ==============

def get_news_hash(url: str, title: str) -> str:
    """生成新闻的唯一哈希值"""
    import hashlib
    content = f"{url}{title}"
    return hashlib.md5(content.encode()).hexdigest()

def insert_news(news_list: List[Dict]) -> int:
    """批量插入新闻，返回新增数量"""
    inserted = 0
    with get_connection() as conn:
        cursor = conn.cursor()
        for news in news_list:
            url_hash = get_news_hash(news.get('url', ''), news.get('title', ''))
            try:
                cursor.execute('''
                    INSERT OR IGNORE INTO news 
                    (url_hash, title, content, source, category, url, published_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    url_hash,
                    news.get('title', ''),
                    news.get('content', ''),
                    news.get('source', ''),
                    news.get('category', ''),
                    news.get('url', ''),
                    news.get('published_at', datetime.now().isoformat())
                ))
                if cursor.rowcount > 0:
                    inserted += 1
            except Exception as e:
                print(f"插入新闻失败: {e}")
        conn.commit()
    return inserted

def get_unprocessed_news(limit: int = 100) -> List[Dict]:
    """获取未处理的新闻"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM news WHERE is_processed = 0 
            ORDER BY published_at DESC LIMIT ?
        ''', (limit,))
        return [dict(row) for row in cursor.fetchall()]

def update_news_analysis(news_id: int, analysis: Dict):
    """更新新闻的AI分析结果"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE news SET 
                summary = ?,
                sentiment_overall = ?,
                sentiment_cn = ?,
                sentiment_us = ?,
                impact_level = ?,
                event_type = ?,
                related_stocks = ?,
                is_processed = 1
            WHERE id = ?
        ''', (
            analysis.get('summary', ''),
            analysis.get('sentiment_overall', 0),
            analysis.get('sentiment_cn', 0),
            analysis.get('sentiment_us', 0),
            analysis.get('impact_level', ''),
            analysis.get('event_type', ''),
            json.dumps(analysis.get('related_stocks', []), ensure_ascii=False),
            news_id
        ))
        conn.commit()

def get_recent_news(hours: int = 24, source: str = None) -> List[Dict]:
    """获取最近N小时的新闻"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cutoff = (datetime.now() - timedelta(hours=hours)).isoformat()
        
        if source:
            cursor.execute('''
                SELECT * FROM news WHERE published_at > ? AND source = ?
                ORDER BY published_at DESC
            ''', (cutoff, source))
        else:
            cursor.execute('''
                SELECT * FROM news WHERE published_at > ?
                ORDER BY published_at DESC
            ''', (cutoff,))
        
        return [dict(row) for row in cursor.fetchall()]


# ============== 报告相关操作 ==============

def save_report(report_type: str, content: str, parsed_data: Dict, file_path: str = None) -> int:
    """保存报告到数据库"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO reports 
            (report_type, title, content, summary, sentiment_overall, sentiment_cn, 
             sentiment_us, total_news, hot_topics, major_events, stocks, file_path)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            report_type,
            parsed_data.get('title', ''),
            content,
            parsed_data.get('summary', ''),
            parsed_data.get('sentiment', {}).get('overall', 0),
            parsed_data.get('sentiment', {}).get('cn', 0),
            parsed_data.get('sentiment', {}).get('us', 0),
            parsed_data.get('total_news', 0),
            json.dumps(parsed_data.get('hot_topics', []), ensure_ascii=False),
            json.dumps(parsed_data.get('major_events', []), ensure_ascii=False),
            json.dumps(parsed_data.get('stocks', []), ensure_ascii=False),
            file_path
        ))
        conn.commit()
        return cursor.lastrowid

def get_reports(report_type: str = None, limit: int = 20, offset: int = 0) -> List[Dict]:
    """获取报告列表"""
    with get_connection() as conn:
        cursor = conn.cursor()
        
        if report_type:
            cursor.execute('''
                SELECT id, report_type, title, summary, sentiment_overall, sentiment_cn,
                       sentiment_us, total_news, created_at, file_path
                FROM reports WHERE report_type = ?
                ORDER BY created_at DESC LIMIT ? OFFSET ?
            ''', (report_type, limit, offset))
        else:
            cursor.execute('''
                SELECT id, report_type, title, summary, sentiment_overall, sentiment_cn,
                       sentiment_us, total_news, created_at, file_path
                FROM reports ORDER BY created_at DESC LIMIT ? OFFSET ?
            ''', (limit, offset))
        
        results = []
        for row in cursor.fetchall():
            results.append(dict(row))
        return results

def get_report_by_id(report_id: int) -> Optional[Dict]:
    """根据ID获取报告详情"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM reports WHERE id = ?', (report_id,))
        row = cursor.fetchone()
        if row:
            result = dict(row)
            # 解析JSON字段
            for field in ['hot_topics', 'major_events', 'stocks']:
                if result.get(field):
                    try:
                        result[field] = json.loads(result[field])
                    except:
                        pass
            return result
        return None


# ============== 自选股相关操作 ==============

def add_to_watchlist(symbol: str, name: str = None, market: str = None, category: str = 'stock') -> bool:
    """添加到自选股"""
    with get_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO watchlist (symbol, name, market, category)
                VALUES (?, ?, ?, ?)
            ''', (symbol.upper(), name, market, category))
            conn.commit()
            return True
        except Exception as e:
            print(f"添加自选股失败: {e}")
            return False

def remove_from_watchlist(symbol: str) -> bool:
    """从自选股移除"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM watchlist WHERE symbol = ?', (symbol.upper(),))
        conn.commit()
        return cursor.rowcount > 0

def get_watchlist(category: str = None) -> List[Dict]:
    """获取自选股列表"""
    with get_connection() as conn:
        cursor = conn.cursor()
        if category:
            cursor.execute('''
                SELECT * FROM watchlist WHERE is_active = 1 AND category = ?
                ORDER BY added_at DESC
            ''', (category,))
        else:
            cursor.execute('''
                SELECT * FROM watchlist WHERE is_active = 1
                ORDER BY added_at DESC
            ''')
        return [dict(row) for row in cursor.fetchall()]


# ============== 热搜相关操作 ==============

def save_hot_searches(platform: str, items: List[Dict]):
    """保存热搜数据"""
    with get_connection() as conn:
        cursor = conn.cursor()
        for item in items:
            cursor.execute('''
                INSERT INTO hot_searches (platform, rank, title, url, hot_value, category)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                platform,
                item.get('rank', 0),
                item.get('title', ''),
                item.get('url', ''),
                item.get('hot_value', 0),
                item.get('category', '')
            ))
        conn.commit()

def get_latest_hot_searches(platform: str = None, limit: int = 50) -> List[Dict]:
    """获取最新热搜"""
    with get_connection() as conn:
        cursor = conn.cursor()
        if platform:
            cursor.execute('''
                SELECT * FROM hot_searches 
                WHERE platform = ? AND collected_at > datetime('now', '-2 hours')
                ORDER BY collected_at DESC, rank ASC LIMIT ?
            ''', (platform, limit))
        else:
            cursor.execute('''
                SELECT * FROM hot_searches 
                WHERE collected_at > datetime('now', '-2 hours')
                ORDER BY collected_at DESC, rank ASC LIMIT ?
            ''', (limit,))
        return [dict(row) for row in cursor.fetchall()]


# ============== 虚拟货币相关操作 ==============

def save_crypto_prices(prices: List[Dict]):
    """保存加密货币价格"""
    with get_connection() as conn:
        cursor = conn.cursor()
        for price in prices:
            cursor.execute('''
                INSERT INTO crypto_prices 
                (symbol, name, price_usd, price_cny, change_24h, volume_24h, market_cap)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                price.get('symbol', ''),
                price.get('name', ''),
                price.get('price_usd', 0),
                price.get('price_cny', 0),
                price.get('change_24h', 0),
                price.get('volume_24h', 0),
                price.get('market_cap', 0)
            ))
        conn.commit()

def get_crypto_prices(symbols: List[str] = None) -> List[Dict]:
    """获取加密货币最新价格"""
    with get_connection() as conn:
        cursor = conn.cursor()
        if symbols:
            placeholders = ','.join(['?' for _ in symbols])
            cursor.execute(f'''
                SELECT * FROM crypto_prices 
                WHERE symbol IN ({placeholders})
                AND timestamp > datetime('now', '-1 hour')
                ORDER BY timestamp DESC
            ''', symbols)
        else:
            cursor.execute('''
                SELECT DISTINCT symbol, name, price_usd, price_cny, change_24h, 
                       volume_24h, market_cap, MAX(timestamp) as timestamp
                FROM crypto_prices 
                WHERE timestamp > datetime('now', '-1 hour')
                GROUP BY symbol
                ORDER BY market_cap DESC
            ''')
        return [dict(row) for row in cursor.fetchall()]


# ============== 预测记录相关操作（回测用）==============

def save_prediction(symbol: str, direction: str, confidence: float, 
                   target_date: str, prediction_type: str = 'news_based') -> int:
    """保存预测记录"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO predictions 
            (symbol, prediction_type, predicted_direction, confidence, target_date)
            VALUES (?, ?, ?, ?, ?)
        ''', (symbol, prediction_type, direction, confidence, target_date))
        conn.commit()
        return cursor.lastrowid

def verify_prediction(prediction_id: int, actual_direction: str, actual_change: float):
    """验证预测结果"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT predicted_direction FROM predictions WHERE id = ?', (prediction_id,))
        row = cursor.fetchone()
        if row:
            is_correct = 1 if row['predicted_direction'] == actual_direction else 0
            cursor.execute('''
                UPDATE predictions SET 
                    actual_direction = ?,
                    actual_change = ?,
                    is_correct = ?,
                    verified_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (actual_direction, actual_change, is_correct, prediction_id))
            conn.commit()

def get_prediction_accuracy(symbol: str = None, days: int = 30) -> Dict:
    """获取预测准确率统计"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        
        if symbol:
            cursor.execute('''
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN is_correct = 1 THEN 1 ELSE 0 END) as correct,
                    AVG(confidence) as avg_confidence
                FROM predictions 
                WHERE symbol = ? AND verified_at IS NOT NULL AND predicted_at > ?
            ''', (symbol, cutoff))
        else:
            cursor.execute('''
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN is_correct = 1 THEN 1 ELSE 0 END) as correct,
                    AVG(confidence) as avg_confidence
                FROM predictions 
                WHERE verified_at IS NOT NULL AND predicted_at > ?
            ''', (cutoff,))
        
        row = cursor.fetchone()
        if row and row['total'] > 0:
            return {
                'total': row['total'],
                'correct': row['correct'] or 0,
                'accuracy': (row['correct'] or 0) / row['total'] * 100,
                'avg_confidence': row['avg_confidence'] or 0
            }
        return {'total': 0, 'correct': 0, 'accuracy': 0, 'avg_confidence': 0}


# 初始化数据库
if __name__ == '__main__':
    init_database()
