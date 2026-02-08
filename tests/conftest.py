"""
共享测试 fixtures
"""
import os
import sys
import pytest

# 把 src 目录加入 Python 路径
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT_DIR, 'src'))
sys.path.insert(0, ROOT_DIR)


@pytest.fixture
def sample_articles():
    """模拟的新闻列表"""
    return [
        {
            'title': '美联储宣布维持利率不变',
            'content': '美联储在最新议息会议上决定维持联邦基金利率不变...',
            'source': 'Reuters',
            'category': 'us_official',
            'url': 'https://example.com/fed-rate',
            'published_at': '2025-01-01T10:00:00',
        },
        {
            'title': '特斯拉Q4财报超预期',
            'content': '特斯拉公布2024年Q4财报，营收同比增长20%...',
            'source': 'Bloomberg',
            'category': 'earnings',
            'url': 'https://example.com/tsla-q4',
            'published_at': '2025-01-02T08:00:00',
        },
        {
            'title': '中国央行下调LPR利率',
            'content': '中国人民银行宣布下调1年期LPR利率10个基点...',
            'source': '新华社',
            'category': 'china_official',
            'url': 'https://example.com/pboc-lpr',
            'published_at': '2025-01-03T09:00:00',
        },
    ]


@pytest.fixture
def sample_processed_articles(sample_articles):
    """模拟经过 NLP 处理后的新闻"""
    enrichments = [
        {
            'summary': '美联储维持利率',
            'sentiment': 0.1,
            'sentiment_cn': 0.05,
            'sentiment_us': 0.2,
            'entities': ['美联储', 'FOMC'],
            'event_type': '政策',
            'impact_level': '高',
            'stock_impact': [],
        },
        {
            'summary': '特斯拉Q4超预期',
            'sentiment': 0.8,
            'sentiment_cn': 0.3,
            'sentiment_us': 0.9,
            'entities': ['特斯拉', 'TSLA'],
            'event_type': '财报',
            'impact_level': '高',
            'stock_impact': [{'symbol': 'TSLA', 'direction': '上涨'}],
        },
        {
            'summary': '央行降息',
            'sentiment': 0.4,
            'sentiment_cn': 0.6,
            'sentiment_us': 0.1,
            'entities': ['央行', 'LPR'],
            'event_type': '政策',
            'impact_level': '高',
            'stock_impact': [],
        },
    ]
    return [{**a, **e} for a, e in zip(sample_articles, enrichments)]


@pytest.fixture
def temp_db(tmp_path):
    """在临时目录创建测试数据库"""
    import database
    old_path = database.DB_PATH
    database.DB_PATH = str(tmp_path / 'test.db')
    database.init_database()
    yield database.DB_PATH
    database.DB_PATH = old_path
