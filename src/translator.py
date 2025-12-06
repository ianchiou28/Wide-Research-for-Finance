"""
后端数据国际化翻译服务
用于将中文数据内容翻译为英文，或提供双语支持
"""

import os
import json
import hashlib
from typing import Dict, List, Optional, Any
from datetime import datetime
import re

# 尝试导入 DeepSeek API
try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False


class TranslationCache:
    """翻译缓存，避免重复翻译相同内容"""
    
    def __init__(self, cache_file: str = 'data/translation_cache.json'):
        self.cache_file = cache_file
        self.cache: Dict[str, str] = {}
        self._load_cache()
    
    def _load_cache(self):
        """加载缓存"""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    self.cache = json.load(f)
        except Exception:
            self.cache = {}
    
    def _save_cache(self):
        """保存缓存"""
        try:
            os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, ensure_ascii=False, indent=2)
        except Exception:
            pass
    
    def get(self, text: str) -> Optional[str]:
        """获取缓存的翻译"""
        key = hashlib.md5(text.encode()).hexdigest()
        return self.cache.get(key)
    
    def set(self, text: str, translation: str):
        """设置翻译缓存"""
        key = hashlib.md5(text.encode()).hexdigest()
        self.cache[key] = translation
        # 定期保存（每100条保存一次）
        if len(self.cache) % 100 == 0:
            self._save_cache()
    
    def save(self):
        """手动保存缓存"""
        self._save_cache()


class Translator:
    """翻译服务"""
    
    # 常用财经术语词典（中->英）
    FINANCE_DICT = {
        # 市场情绪
        '积极': 'Positive',
        '消极': 'Negative', 
        '中性': 'Neutral',
        '看涨': 'Bullish',
        '看跌': 'Bearish',
        '震荡': 'Sideways',
        '上涨': 'Up',
        '下跌': 'Down',
        
        # 市场
        'A股': 'A-Share',
        '美股': 'US Stock',
        '港股': 'HK Stock',
        '中国市场': 'China Market',
        '美国市场': 'US Market',
        '全球市场': 'Global Market',
        
        # 报告类型
        '每日总结': 'Daily Summary',
        '深度报告': 'Deep Report',
        '每小时简报': 'Hourly Brief',
        '周度分析': 'Weekly Analysis',
        '每日摘要': 'Daily Digest',
        
        # 事件类型
        '重大事件': 'Major Event',
        '政策变动': 'Policy Change',
        '财报发布': 'Earnings Release',
        '并购重组': 'M&A',
        '高管变动': 'Executive Change',
        
        # 机构
        '美联储': 'Federal Reserve',
        '央行': 'Central Bank',
        '证监会': 'CSRC',
        '财政部': 'Ministry of Finance',
        
        # 常见股票名（美股）
        '特斯拉': 'Tesla',
        '苹果': 'Apple',
        '谷歌': 'Google',
        '亚马逊': 'Amazon',
        '微软': 'Microsoft',
        '英伟达': 'NVIDIA',
        '台积电': 'TSMC',
        '阿里巴巴': 'Alibaba',
        '腾讯': 'Tencent',
        '百度': 'Baidu',
        '京东': 'JD.com',
        '小米': 'Xiaomi',
        '小米集团': 'Xiaomi Group',
        '小米集团-W': 'Xiaomi-W',
        '华为': 'Huawei',
        '比亚迪': 'BYD',
        '宁德时代': 'CATL',
        '贵州茅台': 'Kweichow Moutai',
        '中国平安': 'Ping An',
        
        # A股常见股票
        '九阳股份': 'Joyoung',
        '格力电器': 'Gree Electric',
        '美的集团': 'Midea Group',
        '海尔智家': 'Haier Smart Home',
        '伊利股份': 'Yili Group',
        '蒙牛乳业': 'Mengniu Dairy',
        '五粮液': 'Wuliangye',
        '中信证券': 'CITIC Securities',
        '海康威视': 'Hikvision',
        '立讯精密': 'Luxshare',
        '恒瑞医药': 'Hengrui Medicine',
        '药明康德': 'WuXi AppTec',
        '迈瑞医疗': 'Mindray',
        '万科A': 'Vanke-A',
        '保利发展': 'Poly Developments',
        '招商银行': 'CMB',
        '工商银行': 'ICBC',
        '建设银行': 'CCB',
        '农业银行': 'ABC',
        '中国银行': 'BOC',
        '平安银行': 'PAB',
        '兴业银行': 'CIB',
        '浦发银行': 'SPDB',
        '招商银行': 'CMB',
        '工商银行': 'ICBC',
        '建设银行': 'CCB',
        
        # 单位
        '万': '0K',
        '亿': '00M',
        '条': '',
        '个': '',
        '次': 'times',
    }
    
    def __init__(self, use_api: bool = True):
        """
        初始化翻译器
        
        Args:
            use_api: 是否使用 DeepSeek API 进行翻译，False 则仅使用词典
        """
        self.use_api = use_api and HAS_OPENAI
        self.cache = TranslationCache()
        self.client = None
        
        if self.use_api:
            api_key = os.getenv('DEEPSEEK_API_KEY')
            if api_key:
                self.client = OpenAI(
                    api_key=api_key,
                    base_url="https://api.deepseek.com",
                    timeout=60.0,   # 设置60秒超时
                    max_retries=2   # 自动重试2次
                )
            else:
                self.use_api = False
    
    def translate_text(self, text: str, use_api: bool = None) -> str:
        """
        翻译文本
        
        Args:
            text: 要翻译的中文文本
            use_api: 是否使用 API（覆盖默认设置）
            
        Returns:
            翻译后的英文文本
        """
        if not text or not text.strip():
            return text
        
        # 检查缓存
        cached = self.cache.get(text)
        if cached:
            return cached
        
        # 先尝试词典翻译
        result = self._dict_translate(text)
        
        # 如果词典翻译后仍有大量中文，且启用了 API，则使用 API 翻译
        should_use_api = use_api if use_api is not None else self.use_api
        if should_use_api and self._has_chinese(result):
            api_result = self._api_translate(text)
            if api_result:
                result = api_result
        
        # 缓存结果
        self.cache.set(text, result)
        return result
    
    def _dict_translate(self, text: str) -> str:
        """使用词典进行翻译"""
        result = text
        for cn, en in self.FINANCE_DICT.items():
            result = result.replace(cn, en)
        return result
    
    def _has_chinese(self, text: str) -> bool:
        """检查文本是否包含中文"""
        return bool(re.search(r'[\u4e00-\u9fff]', text))
    
    def _api_translate(self, text: str) -> Optional[str]:
        """使用 DeepSeek API 翻译"""
        if not self.client:
            return None
        
        try:
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {
                        "role": "system",
                        "content": """You are a professional financial translator. 
Translate the following Chinese text to English. 
Keep stock symbols, numbers, and technical terms accurate.
Only return the translation, no explanations."""
                    },
                    {
                        "role": "user",
                        "content": text
                    }
                ],
                max_tokens=500,
                temperature=0.3
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Translation API error: {e}")
            return None
    
    def translate_dict(self, data: Dict[str, Any], fields: List[str] = None) -> Dict[str, Any]:
        """
        翻译字典中的指定字段
        
        Args:
            data: 要翻译的字典
            fields: 要翻译的字段名列表，None 则翻译所有字符串字段
            
        Returns:
            翻译后的字典（新对象）
        """
        result = data.copy()
        
        for key, value in result.items():
            if fields and key not in fields:
                continue
            
            if isinstance(value, str) and self._has_chinese(value):
                result[key] = self.translate_text(value)
            elif isinstance(value, dict):
                result[key] = self.translate_dict(value, fields)
            elif isinstance(value, list):
                result[key] = self.translate_list(value, fields)
        
        return result
    
    def translate_list(self, data: List[Any], fields: List[str] = None) -> List[Any]:
        """
        翻译列表中的内容
        
        Args:
            data: 要翻译的列表
            fields: 如果列表元素是字典，指定要翻译的字段
            
        Returns:
            翻译后的列表（新对象）
        """
        result = []
        for item in data:
            if isinstance(item, str) and self._has_chinese(item):
                result.append(self.translate_text(item))
            elif isinstance(item, dict):
                result.append(self.translate_dict(item, fields))
            elif isinstance(item, list):
                result.append(self.translate_list(item, fields))
            else:
                result.append(item)
        return result
    
    def save_cache(self):
        """保存翻译缓存"""
        self.cache.save()


# 创建全局翻译器实例
_translator: Optional[Translator] = None

def get_translator() -> Translator:
    """获取全局翻译器实例"""
    global _translator
    if _translator is None:
        _translator = Translator()
    return _translator


def translate_response(data: Any, lang: str = 'zh') -> Any:
    """
    根据语言参数翻译 API 响应数据
    
    Args:
        data: API 响应数据
        lang: 语言代码 'zh' 或 'en'
        
    Returns:
        处理后的数据
    """
    if lang == 'zh':
        return data
    
    translator = get_translator()
    
    if isinstance(data, dict):
        return translator.translate_dict(data)
    elif isinstance(data, list):
        return translator.translate_list(data)
    elif isinstance(data, str):
        return translator.translate_text(data)
    
    return data


def translate_text(text: str, lang: str = 'zh') -> str:
    """
    翻译单个文本字符串
    
    Args:
        text: 要翻译的文本
        lang: 语言代码 'zh' 或 'en'
        
    Returns:
        翻译后的文本
    """
    if lang == 'zh' or not text:
        return text
    
    translator = get_translator()
    return translator.translate_text(text)


# 特定数据结构的翻译函数
def translate_report_data(data: Dict, lang: str = 'zh') -> Dict:
    """翻译报告数据结构"""
    if lang == 'zh':
        return data
    
    translator = get_translator()
    result = data.copy()
    
    # 翻译情绪标签
    if 'sentiment' in result:
        sentiment = result['sentiment']
        for key in ['overall', 'cn', 'us']:
            if key in sentiment and 'label' in sentiment[key]:
                sentiment[key]['label'] = translator.translate_text(sentiment[key]['label'])
    
    # 翻译实体名称
    if 'entities' in result:
        for entity in result['entities']:
            if 'name' in entity:
                entity['name'] = translator.translate_text(entity['name'])
    
    # 翻译事件
    if 'events' in result:
        for event_type in ['high_impact', 'hot_search', 'stock_specific', 'other']:
            if event_type in result['events']:
                for event in result['events'][event_type]:
                    if 'title' in event:
                        event['title'] = translator.translate_text(event['title'])
                    if 'summary' in event:
                        event['summary'] = translator.translate_text(event['summary'])
                    if 'event_type' in event:
                        event['event_type'] = translator.translate_text(event['event_type'])
    
    # 翻译股票影响
    if 'stock_impacts' in result:
        for stock in result['stock_impacts']:
            if 'name' in stock:
                stock['name'] = translator.translate_text(stock['name'])
            if 'prediction' in stock:
                stock['prediction'] = translator.translate_text(stock['prediction'])
    
    return result


def translate_hot_search_data(data: Dict, lang: str = 'zh') -> Dict:
    """翻译热搜数据"""
    if lang == 'zh':
        return data
    
    translator = get_translator()
    result = data.copy()
    
    if 'data' in result:
        for item in result['data']:
            if 'title' in item:
                item['title'] = translator.translate_text(item['title'])
            if 'content' in item:
                item['content'] = translator.translate_text(item['content'])
    
    return result


def translate_stock_data(data: Dict, lang: str = 'zh') -> Dict:
    """翻译股票数据"""
    if lang == 'zh':
        return data
    
    translator = get_translator()
    result = data.copy()
    
    if 'name' in result:
        result['name'] = translator.translate_text(result['name'])
    
    if 'data' in result and isinstance(result['data'], list):
        for item in result['data']:
            if 'name' in item:
                item['name'] = translator.translate_text(item['name'])
    
    return result
