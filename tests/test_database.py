"""
database 模块的单元测试
"""
import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))

import database


class TestDatabaseOperations:
    """数据库基础操作测试"""

    def test_init_database(self, temp_db):
        """测试数据库初始化"""
        assert os.path.exists(temp_db)

    def test_wal_mode(self, temp_db):
        """测试 WAL 模式已启用"""
        with database.get_connection() as conn:
            result = conn.execute('PRAGMA journal_mode').fetchone()
            assert result[0] == 'wal'

    def test_insert_and_get_news(self, temp_db):
        """测试新闻插入和查询"""
        news_list = [
            {
                'title': '测试新闻1',
                'content': '这是测试内容',
                'source': 'test',
                'category': 'test',
                'url': 'https://example.com/1',
                'published_at': '2025-01-01T00:00:00',
            },
        ]
        inserted = database.insert_news(news_list)
        assert inserted == 1

    def test_dedup_on_insert(self, temp_db):
        """测试重复插入去重"""
        news = [
            {
                'title': '同一条新闻',
                'content': '内容',
                'source': 'test',
                'category': 'test',
                'url': 'https://example.com/dup',
                'published_at': '2025-01-01T00:00:00',
            },
        ]
        first = database.insert_news(news)
        second = database.insert_news(news)
        assert first == 1
        assert second == 0  # 重复不会插入

    def test_get_recent_news_hashes(self, temp_db):
        """测试获取最近新闻 hash"""
        news = [
            {
                'title': f'测试{i}',
                'content': f'内容{i}',
                'source': 'test',
                'category': 'test',
                'url': f'https://example.com/{i}',
                'published_at': '2025-01-01T00:00:00',
            }
            for i in range(5)
        ]
        database.insert_news(news)
        hashes = database.get_recent_news_hashes(hours=24)
        assert len(hashes) == 5

    def test_news_hash_consistency(self, temp_db):
        """测试 hash 生成一致性"""
        h1 = database.get_news_hash('https://example.com/a', '标题A')
        h2 = database.get_news_hash('https://example.com/a', '标题A')
        h3 = database.get_news_hash('https://example.com/b', '标题B')
        assert h1 == h2
        assert h1 != h3


class TestWatchlist:
    """自选股测试"""

    def test_add_to_watchlist(self, temp_db):
        result = database.add_to_watchlist('AAPL', '苹果', 'US')
        assert result is True

    def test_get_watchlist(self, temp_db):
        database.add_to_watchlist('AAPL', '苹果', 'US')
        database.add_to_watchlist('TSLA', '特斯拉', 'US')
        watchlist = database.get_watchlist()
        assert len(watchlist) >= 2
