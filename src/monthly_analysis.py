"""
月度深度分析模块
功能：
1. 自动获取/抓取月度重大事件（央行会议、经济数据发布等）
2. 深度分析事件对市场的影响
3. 生成加减仓建议
4. 支持对话式交互追问
5. 每日更新，持续修正预测
"""

import os
import json
import re
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from openai import OpenAI
import glob
from logger import setup_logger

# 导入统一配置
import sys as _sys
_sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config'))
try:
    from settings import Config
except ImportError:
    Config = None

logger = setup_logger('monthly_analysis')


class MonthlyAnalysis:
    """月度深度分析器"""
    
    # 预设的重大事件日历（可扩展为自动抓取）
    MAJOR_EVENTS_TEMPLATE = {
        "us_fed": {
            "name": "美联储FOMC议息会议",
            "name_en": "Fed FOMC Meeting",
            "frequency": "monthly",
            "importance": "critical",
            "affects": ["us_stocks", "global_stocks", "bonds", "forex", "crypto"],
            "keywords": ["FOMC", "美联储", "利率决议", "鲍威尔", "Powell", "Fed"]
        },
        "us_cpi": {
            "name": "美国CPI数据",
            "name_en": "US CPI Data",
            "frequency": "monthly",
            "importance": "high",
            "affects": ["us_stocks", "bonds", "forex"],
            "keywords": ["CPI", "通胀", "inflation", "物价"]
        },
        "us_employment": {
            "name": "美国非农就业数据",
            "name_en": "US Non-Farm Payrolls",
            "frequency": "monthly",
            "importance": "high",
            "affects": ["us_stocks", "forex"],
            "keywords": ["非农", "就业", "NFP", "employment", "payroll"]
        },
        "china_pboc": {
            "name": "中国人民银行利率决议",
            "name_en": "PBOC Interest Rate Decision",
            "frequency": "monthly",
            "importance": "critical",
            "affects": ["cn_stocks", "hk_stocks", "forex"],
            "keywords": ["央行", "LPR", "降息", "降准", "货币政策"]
        },
        "china_pmi": {
            "name": "中国PMI数据",
            "name_en": "China PMI Data",
            "frequency": "monthly",
            "importance": "high",
            "affects": ["cn_stocks", "commodities"],
            "keywords": ["PMI", "制造业", "采购经理"]
        },
        "china_cewc": {
            "name": "中央经济工作会议",
            "name_en": "Central Economic Work Conference",
            "frequency": "yearly",  # 每年12月
            "importance": "critical",
            "affects": ["cn_stocks", "hk_stocks", "commodities"],
            "keywords": ["中央经济工作会议", "经济工作会议", "政策定调"]
        },
        "japan_boj": {
            "name": "日本央行利率决议",
            "name_en": "BOJ Interest Rate Decision",
            "frequency": "monthly",
            "importance": "high",
            "affects": ["jp_stocks", "forex", "us_stocks"],
            "keywords": ["日本央行", "BOJ", "日元", "加息", "YCC"]
        },
        "ecb_meeting": {
            "name": "欧洲央行利率决议",
            "name_en": "ECB Interest Rate Decision",
            "frequency": "monthly",
            "importance": "high",
            "affects": ["eu_stocks", "forex"],
            "keywords": ["欧洲央行", "ECB", "欧元", "拉加德"]
        },
        "us_gdp": {
            "name": "美国GDP数据",
            "name_en": "US GDP Data",
            "frequency": "quarterly",
            "importance": "high",
            "affects": ["us_stocks", "global_stocks"],
            "keywords": ["GDP", "经济增长", "economic growth"]
        },
        "earnings_season": {
            "name": "财报季",
            "name_en": "Earnings Season",
            "frequency": "quarterly",
            "importance": "high",
            "affects": ["us_stocks", "cn_stocks"],
            "keywords": ["财报", "earnings", "业绩", "季报"]
        }
    }
    
    # 预设事件日历作为备用（自动抓取失败时使用）
    FALLBACK_CALENDAR = {
        "2025-01": [
            {"event_id": "us_employment", "date": "2025-01-10", "note": "12月非农"},
            {"event_id": "us_cpi", "date": "2025-01-15", "note": "12月CPI"},
            {"event_id": "japan_boj", "date": "2025-01-24", "note": ""},
            {"event_id": "us_fed", "date": "2025-01-29", "note": "1月FOMC"}
        ],
        "2025-02": [
            {"event_id": "us_employment", "date": "2025-02-07", "note": "1月非农"},
            {"event_id": "us_cpi", "date": "2025-02-12", "note": "1月CPI"},
            {"event_id": "china_pmi", "date": "2025-02-01", "note": "1月PMI"}
        ],
        "2025-03": [
            {"event_id": "us_employment", "date": "2025-03-07", "note": "2月非农"},
            {"event_id": "us_cpi", "date": "2025-03-12", "note": "2月CPI"},
            {"event_id": "us_fed", "date": "2025-03-19", "note": "3月FOMC"},
            {"event_id": "japan_boj", "date": "2025-03-14", "note": ""}
        ],
        "2025-12": [
            {"event_id": "us_employment", "date": "2025-12-05", "note": "11月非农"},
            {"event_id": "us_cpi", "date": "2025-12-11", "note": "11月CPI"},
            {"event_id": "us_fed", "date": "2025-12-17", "note": "12月FOMC，可能降息"},
            {"event_id": "japan_boj", "date": "2025-12-19", "note": "关注是否加息"},
            {"event_id": "china_cewc", "date": "2025-12-11", "note": "中央经济工作会议，约12月中旬"},
            {"event_id": "ecb_meeting", "date": "2025-12-12", "note": ""}
        ]
    }
    
    # 经济日历数据来源配置
    CALENDAR_SOURCES = [
        {
            "name": "Investing.com Economic Calendar",
            "url": "https://www.investing.com/economic-calendar/",
            "type": "web_scrape"
        },
        {
            "name": "Trading Economics",
            "url": "https://tradingeconomics.com/calendar",
            "type": "web_scrape"  
        }
    ]
    
    def __init__(self):
        self.api_key = os.getenv('DEEPSEEK_API_KEY')
        self.client = None
        self._model = "deepseek-chat"
        if self.api_key:
            if Config:
                client_kwargs = Config.get_llm_client_kwargs()
                client_kwargs['api_key'] = self.api_key
                self.client = OpenAI(**client_kwargs)
                self._model = Config.LLM_MODEL
            else:
                self.client = OpenAI(
                    api_key=self.api_key, 
                    base_url="https://api.deepseek.com",
                    timeout=120.0  # 增加超时时间到120秒
                )
        
        # 对话历史（用于追问）
        self.conversation_history: List[Dict] = []
        self.current_analysis: Optional[Dict] = None
        
        # 缓存的动态事件
        self._cached_events: Dict[str, List[Dict]] = {}
        self._cache_time: Optional[datetime] = None
        
    def get_month_key(self, date: datetime = None) -> str:
        """获取月份键值"""
        if date is None:
            date = datetime.now()
        return date.strftime("%Y-%m")
    
    def _fetch_events_from_news(self, year: int, month: int) -> List[Dict]:
        """通过分析新闻自动识别重大事件"""
        events = []
        
        # 从历史报告中提取与事件相关的新闻
        json_reports = glob.glob('data/reports_json/report_*.json')
        json_reports.sort(key=os.path.getctime, reverse=True)
        
        # 收集最近的新闻
        recent_news = []
        for report_path in json_reports[:30]:  # 最近30份报告
            try:
                with open(report_path, 'r', encoding='utf-8') as f:
                    report = json.load(f)
                
                for event_type in ['high_impact', 'other']:
                    for news in report.get('events', {}).get(event_type, []):
                        title = news.get('title', '')
                        summary = news.get('summary', '')
                        if title:
                            recent_news.append(f"{title}: {summary[:100]}")
            except:
                continue
        
        # 如果没有足够的新闻数据，跳过自动识别
        if len(recent_news) < 5 or not self.client:
            logger.info("新闻数据不足，跳过自动识别")
            return events
        
        # 用AI分析新闻中提到的即将发生的重大事件
        prompt = f"""分析以下新闻，提取{year}年{month}月将要发生的重大经济/金融事件。

【最近新闻摘要】
{chr(10).join(recent_news[:30])}

请找出新闻中明确提到的{year}年{month}月的事件：
1. 央行会议/利率决议
2. 重要经济数据发布
3. 重大政策会议
4. 其他影响市场的事件

只返回有明确日期的事件，返回JSON数组：
[{{"date": "YYYY-MM-DD", "name": "事件名", "importance": "critical/high/medium", "note": "说明"}}]

如果没找到，返回 []"""

        try:
            response = self.client.chat.completions.create(
                model=self._model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=1500
            )
            
            content = response.choices[0].message.content if response.choices else None
            if content:
                # 提取JSON数组
                start = content.find('[')
                end = content.rfind(']')
                if start != -1 and end != -1 and end > start:
                    events = json.loads(content[start:end+1])
                    logger.info(f"自动识别到 {len(events)} 个事件")
        except Exception as e:
            logger.warning(f"自动抓取事件失败: {e}")
        
        return events
    
    def _identify_high_impact_events(self, events: List[Dict]) -> List[Dict]:
        """用AI判断哪些事件会对股市产生重大影响"""
        if not events or not self.client or len(events) < 2:
            return events
        
        events_desc = "\n".join([f"- {e.get('date', '')}: {e.get('name', '')} ({e.get('importance', 'medium')})" for e in events[:15]])
        
        prompt = f"""评估以下事件对股市的影响：

{events_desc}

对每个事件评估影响程度(1-10)和方向。返回JSON数组：
[{{"date": "日期", "name": "名称", "impact_score": 8, "expected_direction": "bullish/bearish/neutral", "analysis": "简短分析"}}]"""

        try:
            response = self.client.chat.completions.create(
                model=self._model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=1500
            )
            
            content = response.choices[0].message.content if response.choices else None
            if content:
                start = content.find('[')
                end = content.rfind(']')
                if start != -1 and end != -1:
                    impact_analysis = json.loads(content[start:end+1])
                    
                    # 合并影响分析到事件中
                    impact_map = {(a.get('date', ''), a.get('name', '')): a for a in impact_analysis}
                    for event in events:
                        key = (event.get('date', ''), event.get('name', ''))
                        if key in impact_map:
                            event.update(impact_map[key])
                    
                    # 按影响分数排序
                    events.sort(key=lambda x: x.get('impact_score', 0), reverse=True)
                    logger.info(f"已评估 {len(impact_analysis)} 个事件的影响")
        except Exception as e:
            logger.warning(f"影响评估失败: {e}")
        
        return events
    
    def _fix_json_with_ai(self, broken_json: str, events: List[Dict]) -> Optional[Dict]:
        """使用AI修复格式错误的JSON"""
        if not self.client:
            return None
        
        try:
            response = self.client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": "你是一个JSON修复专家。用户会给你一个格式有问题的JSON字符串，请修复它并返回有效的JSON。只返回修复后的JSON，不要有任何其他文字。"},
                    {"role": "user", "content": f"请修复这个JSON:\n{broken_json[:4000]}"}
                ],
                temperature=0.1,
                max_tokens=6000
            )
            
            content = response.choices[0].message.content if response.choices else None
            if content:
                content = content.strip()
                if content.startswith('```json'):
                    content = content[7:]
                elif content.startswith('```'):
                    content = content[3:]
                if content.endswith('```'):
                    content = content[:-3]
                
                start = content.find('{')
                end = content.rfind('}')
                if start != -1 and end != -1:
                    return json.loads(content[start:end+1])
        except Exception as e:
            logger.warning(f"AI修复JSON失败: {e}")
        
        return None
    
    def get_monthly_events(self, year: int = None, month: int = None, force_refresh: bool = False) -> List[Dict]:
        """获取指定月份的重大事件 - 支持自动抓取和动态更新"""
        if year is None:
            year = datetime.now().year
        if month is None:
            month = datetime.now().month
        
        month_key = f"{year}-{month:02d}"
        
        # 检查缓存是否有效（24小时内）
        cache_valid = (
            not force_refresh and 
            self._cache_time and 
            datetime.now() - self._cache_time < timedelta(hours=24) and
            month_key in self._cached_events
        )
        
        if cache_valid:
            return self._cached_events[month_key]
        
        # 1. 首先尝试从新闻中自动识别事件
        logger.info(f"正在自动识别 {year}年{month}月 的重大事件...")
        auto_events = self._fetch_events_from_news(year, month)
        
        # 2. 获取预设的事件日历
        preset_events = self.FALLBACK_CALENDAR.get(month_key, [])
        preset_enriched = []
        for event in preset_events:
            event_info = self.MAJOR_EVENTS_TEMPLATE.get(event["event_id"], {})
            preset_enriched.append({
                "id": event["event_id"],
                "date": event["date"],
                "name": event_info.get("name", event["event_id"]),
                "name_en": event_info.get("name_en", ""),
                "importance": event_info.get("importance", "medium"),
                "affects": event_info.get("affects", []),
                "note": event.get("note", ""),
                "keywords": event_info.get("keywords", []),
                "source": "preset"
            })
        
        # 3. 合并自动抓取和预设事件（去重，但允许同一天多个事件）
        all_events = []
        seen_keys = set()
        
        # 优先使用自动抓取的事件
        for event in auto_events:
            key = (event.get('date', ''), event.get('name', ''))
            if key not in seen_keys:
                event['source'] = 'auto_detected'
                all_events.append(event)
                seen_keys.add(key)
        
        # 补充预设事件（允许同一天有多个不同事件）
        for event in preset_enriched:
            key = (event.get('date', ''), event.get('name', ''))
            if key not in seen_keys:
                all_events.append(event)
                seen_keys.add(key)
        
        # 4. 评估事件影响程度并排序
        if all_events and self.client:
            logger.info("正在评估事件对市场的影响...")
            all_events = self._identify_high_impact_events(all_events)
        
        # 按日期排序
        all_events.sort(key=lambda x: x.get("date", ""))
        
        # 更新缓存
        self._cached_events[month_key] = all_events
        self._cache_time = datetime.now()
        
        return all_events
    
    def collect_related_news(self, events: List[Dict], days_back: int = 30) -> Dict[str, List[Dict]]:
        """从历史报告中收集与事件相关的新闻"""
        # 使用事件名称作为key（因为自动抓取的事件可能没有id）
        news_by_event = {}
        for e in events:
            key = e.get("id") or e.get("name", "")
            news_by_event[key] = []
        
        # 获取过去N天的JSON报告
        json_reports = glob.glob('data/reports_json/report_*.json')
        cutoff = datetime.now() - timedelta(days=days_back)
        
        for report_path in json_reports:
            try:
                mtime = datetime.fromtimestamp(os.path.getctime(report_path))
                if mtime < cutoff:
                    continue
                
                with open(report_path, 'r', encoding='utf-8') as f:
                    report = json.load(f)
                
                # 检查每个事件的关键词
                all_news = []
                for event_type in ['high_impact', 'other', 'stock_specific']:
                    all_news.extend(report.get('events', {}).get(event_type, []))
                
                for news in all_news:
                    title = news.get('title', '') + ' ' + news.get('summary', '')
                    title_lower = title.lower()
                    
                    for event in events:
                        keywords = event.get('keywords', [])
                        # 对于自动抓取的事件，用名称作为关键词
                        if not keywords:
                            keywords = [event.get('name', ''), event.get('name_en', '')]
                        
                        for keyword in keywords:
                            if keyword and keyword.lower() in title_lower:
                                key = event.get("id") or event.get("name", "")
                                if key in news_by_event:
                                    news_by_event[key].append({
                                        "title": news.get("title", ""),
                                        "summary": news.get("summary", ""),
                                        "sentiment": news.get("sentiment", {}),
                                        "date": report.get("meta", {}).get("generated_at", "")
                                    })
                                break
            except Exception as e:
                continue
        
        return news_by_event
    
    def aggregate_weekly_data(self, days: int = 30) -> Dict:
        """聚合过去N天的周报数据"""
        weekly_files = glob.glob('data/weekly/analysis_*.json')
        weekly_files.sort(key=os.path.getctime, reverse=True)
        
        cutoff = datetime.now() - timedelta(days=days)
        
        all_stocks = {}
        summaries = []
        
        for filepath in weekly_files[:8]:  # 最近8份周报（约2个月）
            try:
                mtime = datetime.fromtimestamp(os.path.getctime(filepath))
                if mtime < cutoff:
                    continue
                    
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                summaries.append(data.get('summary', ''))
                
                for stock in data.get('stocks', []):
                    symbol = stock.get('symbol', '')
                    if symbol not in all_stocks:
                        all_stocks[symbol] = {
                            'name': stock.get('name', ''),
                            'predictions': [],
                            'reasons': []
                        }
                    all_stocks[symbol]['predictions'].append(stock.get('prediction', ''))
                    all_stocks[symbol]['reasons'].append(stock.get('reason', ''))
            except:
                continue
        
        return {
            'stocks': all_stocks,
            'summaries': summaries
        }
    
    def generate_monthly_analysis(self, year: int = None, month: int = None) -> Dict:
        """生成月度深度分析（支持每日更新）"""
        if year is None:
            year = datetime.now().year
        if month is None:
            month = datetime.now().month
        
        # 1. 获取本月重大事件
        events = self.get_monthly_events(year, month)
        
        # 2. 标记已发生的事件，收集实际结果
        today = datetime.now().strftime('%Y-%m-%d')
        past_events = []
        upcoming_events = []
        for e in events:
            event_date = e.get('date', '9999-12-31')
            if event_date <= today:
                e['status'] = 'completed'
                past_events.append(e)
            else:
                e['status'] = 'upcoming'
                upcoming_events.append(e)
        
        # 3. 收集相关新闻（用于分析已发生事件的实际影响）
        related_news = self.collect_related_news(events)
        
        # 4. 聚合历史周报数据
        weekly_data = self.aggregate_weekly_data()
        
        # 5. 获取上一次分析（用于对比和修正）
        previous_analysis = self.get_latest_analysis()
        
        # 6. 构建分析提示
        month_name = f"{year}年{month}月"
        current_date = datetime.now().strftime('%Y年%m月%d日')
        
        # 已发生事件及其实际影响
        past_events_desc = ""
        if past_events:
            past_events_desc = "\n【已发生事件回顾】"
            for e in past_events:
                key = e.get("id") or e.get("name", "")
                news = related_news.get(key, [])
                past_events_desc += f"\n- {e.get('date')} {e.get('name')} [已发生]"
                if news:
                    # 分析实际市场反应
                    sentiments = [n.get('sentiment', {}).get('label', '') for n in news[-5:]]
                    past_events_desc += f"\n  相关新闻{len(news)}条，近期情绪: {', '.join(set(sentiments))}"
        
        # 即将发生的事件
        upcoming_events_desc = ""
        if upcoming_events:
            upcoming_events_desc = "\n【即将发生事件】"
            for e in upcoming_events:
                key = e.get("id") or e.get("name", "")
                news_count = len(related_news.get(key, []))
                importance = e.get('importance', 'medium')
                source_tag = "[自动识别]" if e.get('source') == 'auto_detected' else ""
                
                upcoming_events_desc += f"\n- {e.get('date', '待定')} {e.get('name', '')}（重要性：{importance}）{source_tag}"
                
                if e.get('impact_score'):
                    upcoming_events_desc += f" [影响评分: {e['impact_score']}/10]"
                if e.get('expected_direction'):
                    direction_map = {'bullish': '利多', 'bearish': '利空', 'neutral': '中性'}
                    upcoming_events_desc += f" [预期: {direction_map.get(e['expected_direction'], e['expected_direction'])}]"
                
                if e.get('note'):
                    upcoming_events_desc += f" - {e['note']}"
                upcoming_events_desc += f" [相关新闻{news_count}条]"
        
        events_desc = past_events_desc + upcoming_events_desc
        
        # 汇总周报中的高频股票
        top_stocks = sorted(
            weekly_data['stocks'].items(),
            key=lambda x: len(x[1]['predictions']),
            reverse=True
        )[:15]
        
        stocks_desc = ""
        for symbol, data in top_stocks:
            pred_counts = {}
            for p in data['predictions']:
                pred_counts[p] = pred_counts.get(p, 0) + 1
            main_pred = max(pred_counts.items(), key=lambda x: x[1])[0] if pred_counts else "未知"
            stocks_desc += f"\n- {symbol} ({data['name']}): 主要预测={main_pred}, 出现{len(data['predictions'])}次"
        
        # 最近的市场总结
        recent_summaries = "\n".join(weekly_data['summaries'][:3]) if weekly_data['summaries'] else "暂无近期周报"
        
        # 上次预测回顾（用于修正）
        previous_summary = ""
        if previous_analysis and not previous_analysis.get('error'):
            prev_date = previous_analysis.get('generated_at', '')[:10]
            prev_summary = previous_analysis.get('summary', '')[:200]
            previous_summary = f"\n【上次分析回顾】({prev_date})\n{prev_summary}..."
        
        prompt = f"""你是一位资深金融分析师。今天是{current_date}，请基于以下信息，生成{month_name}的深度月度市场分析报告。

【重要】这是每日更新的月度分析，请特别注意：
1. 对已发生事件，分析其实际市场影响，修正之前的预测
2. 对即将发生事件，结合最新信息更新预期
3. 根据市场变化及时调整加减仓建议

{events_desc}
{previous_summary}

【近期周报市场观点】
{recent_summaries}

【近期高关注度股票】
{stocks_desc}

请提供详尽的分析报告，必须包含：

1. **本月宏观环境概览**（结合今日最新情况）
   - 全球经济形势
   - 主要央行政策预期
   - 地缘政治风险

2. **重大事件深度分析**
   已发生事件：
   - 实际结果与预期对比
   - 市场反应分析
   - 后续影响评估
   
   即将发生事件：
   - 最新市场预期
   - 情景分析（乐观/基准/悲观）
   - 对各类资产的影响预判

3. **行业轮动建议**（根据最新情况调整）
   - 本月看好的行业及原因
   - 本月需回避的行业及原因
   - 边际变化值得关注的行业

4. **个股加减仓建议**（今日建议）
   给出具体的操作建议：
   - 建议加仓的股票（附理由和目标位）
   - 建议减仓的股票（附理由和止损位）
   - 观望的股票（需要等待的信号）

5. **关键时间节点提醒**（未来待发生的）
   - 重点关注日期
   - 需要提前布局的时机
   - 风险释放的可能时间窗口

6. **预测修正**（如有上次分析）
   - 哪些预测准确/偏差
   - 需要调整的观点
   - 新的风险点

7. **风险提示**
   - 主要不确定性
   - 黑天鹅事件预警
   - 仓位管理建议

请返回JSON格式（仅返回JSON，无其他文字）：
{{
  "month": "{month_name}",
  "update_date": "{current_date}",
  "generated_at": "{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
  "is_daily_update": true,
  "macro_overview": {{
    "global_economy": "全球经济概述",
    "central_banks": "央行政策预期",
    "geopolitics": "地缘政治风险"
  }},
  "event_analysis": [
    {{
      "event": "事件名称",
      "date": "日期",
      "status": "completed/upcoming",
      "market_expectation": "预期或实际结果",
      "actual_result": "已发生事件的实际结果（如适用）",
      "scenarios": {{
        "bullish": "乐观情景及概率",
        "base": "基准情景及概率",
        "bearish": "悲观情景及概率"
      }},
      "impact": {{
        "stocks": "对股市影响",
        "bonds": "对债市影响",
        "forex": "对汇市影响",
        "commodities": "对大宗商品影响"
      }},
      "key_indicators": ["需关注的指标1", "指标2"]
    }}
  ],
  "prediction_review": {{
    "accurate": ["准确的预测1"],
    "adjusted": ["需调整的观点1"],
    "new_risks": ["新发现的风险1"]
  }},
  "sector_rotation": {{
    "overweight": [
      {{"sector": "行业名", "reason": "看好原因", "top_picks": ["代表股1", "代表股2"]}}
    ],
    "underweight": [
      {{"sector": "行业名", "reason": "回避原因"}}
    ],
    "watch": [
      {{"sector": "行业名", "catalyst": "需关注的催化剂"}}
    ]
  }},
  "stock_recommendations": {{
    "buy": [
      {{
        "symbol": "股票代码",
        "name": "股票名称",
        "current_price": "当前价格区间",
        "target_price": "目标价",
        "stop_loss": "止损位",
        "reason": "推荐理由",
        "timing": "建仓时机"
      }}
    ],
    "sell": [
      {{
        "symbol": "股票代码",
        "name": "股票名称",
        "reason": "减仓理由",
        "timing": "减仓时机"
      }}
    ],
    "hold": [
      {{
        "symbol": "股票代码",
        "name": "股票名称",
        "wait_for": "等待的信号"
      }}
    ]
  }},
  "key_dates": [
    {{
      "date": "日期",
      "event": "事件",
      "action": "建议操作",
      "priority": "high/medium/low"
    }}
  ],
  "risk_warnings": {{
    "main_uncertainties": ["不确定性1", "不确定性2"],
    "black_swan_alerts": ["潜在黑天鹅1"],
    "position_management": "仓位管理建议"
  }},
  "summary": "月度总结（一段话概括）"
}}"""
        
        if not self.client:
            return {
                "error": True,
                "message": "未配置 DeepSeek API",
                "events": events
            }
        
        try:
            response = self.client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": "你是一位资深金融分析师，擅长宏观分析和投资策略制定。请提供专业、客观、可操作的分析建议。请严格返回有效的JSON格式，不要包含任何注释或额外文字。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=8000
            )
            
            content = response.choices[0].message.content if response.choices else None
            if content:
                # 清理可能的markdown代码块标记
                content = content.strip()
                if content.startswith('```json'):
                    content = content[7:]
                elif content.startswith('```'):
                    content = content[3:]
                if content.endswith('```'):
                    content = content[:-3]
                content = content.strip()
                
                # 提取JSON
                start = content.find('{')
                end = content.rfind('}')
                if start != -1 and end != -1 and end > start:
                    json_str = content[start:end+1]
                    
                    # 尝试修复常见的JSON问题
                    try:
                        analysis = json.loads(json_str)
                    except json.JSONDecodeError as je:
                        # 尝试修复：移除尾部逗号
                        fixed_json = re.sub(r',\s*([}\]])', r'\1', json_str)
                        try:
                            analysis = json.loads(fixed_json)
                        except:
                            # 如果仍然失败，用AI修复
                            logger.warning("JSON解析失败，尝试AI修复...")
                            analysis = self._fix_json_with_ai(json_str, events)
                            if not analysis:
                                return {
                                    "error": True,
                                    "message": f"JSON解析失败: {str(je)}",
                                    "events": events,
                                    "raw_content": json_str[:1000]
                                }
                    
                    # 保存分析结果
                    self.current_analysis = analysis
                    
                    # 初始化对话历史
                    self.conversation_history = [
                        {"role": "system", "content": "你是一位资深金融分析师。你刚刚生成了月度分析报告，用户可能会追问细节。请基于已有分析内容回答问题，如需补充可以提供更深入的见解。"},
                        {"role": "assistant", "content": f"我已完成{month_name}的月度分析报告。您可以就任何感兴趣的部分追问，比如：\n- 某个具体事件的更详细分析\n- 某只股票的深度研究\n- 特定行业的投资逻辑\n- 仓位配置的具体建议"}
                    ]
                    
                    return analysis
                    
        except Exception as e:
            return {
                "error": True,
                "message": f"生成分析失败: {str(e)}",
                "events": events
            }
        
        return {
            "error": True,
            "message": "AI返回内容解析失败",
            "events": events
        }
    
    def chat(self, user_message: str) -> str:
        """对话式追问"""
        if not self.client:
            return "未配置 DeepSeek API，无法进行对话"
        
        if not self.current_analysis:
            return "请先生成月度分析报告，再进行追问"
        
        # 添加当前分析的上下文
        context = f"【当前月度分析报告摘要】\n{json.dumps(self.current_analysis, ensure_ascii=False, indent=2)[:3000]}..."
        
        # 构建消息
        messages = self.conversation_history.copy()
        messages.append({
            "role": "user", 
            "content": f"{context}\n\n用户问题: {user_message}"
        })
        
        try:
            response = self.client.chat.completions.create(
                model=self._model,
                messages=messages,
                temperature=0.4,
                max_tokens=2000
            )
            
            assistant_reply = response.choices[0].message.content if response.choices else "抱歉，无法生成回复"
            
            # 更新对话历史
            self.conversation_history.append({"role": "user", "content": user_message})
            self.conversation_history.append({"role": "assistant", "content": assistant_reply})
            
            # 保持历史长度
            if len(self.conversation_history) > 20:
                self.conversation_history = self.conversation_history[:2] + self.conversation_history[-16:]
            
            return assistant_reply
            
        except Exception as e:
            return f"对话出错: {str(e)}"
    
    def save_analysis(self, analysis: Dict) -> str:
        """保存分析结果"""
        if not analysis or analysis.get('error'):
            return ""
        
        output_dir = os.path.join('data', 'monthly')
        os.makedirs(output_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = os.path.join(output_dir, f'analysis_{timestamp}.json')
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(analysis, f, ensure_ascii=False, indent=2)
        
        return filename
    
    def get_latest_analysis(self) -> Optional[Dict]:
        """获取最新的月度分析"""
        files = glob.glob('data/monthly/analysis_*.json')
        if not files:
            return None
        
        latest = max(files, key=os.path.getctime)
        try:
            with open(latest, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return None
    
    def update_event_result(self, event_id: str, actual_result: str, market_reaction: str) -> Dict:
        """更新事件结果，用于回测和修正预测"""
        if not self.current_analysis:
            return {"error": "无当前分析"}
        
        update_prompt = f"""基于以下实际结果，请更新和修正之前的预测：

【原事件预测】
事件ID: {event_id}

【实际结果】
{actual_result}

【市场反应】
{market_reaction}

请提供：
1. 预测准确度评估
2. 偏差原因分析
3. 后续影响修正
4. 新的投资建议调整

返回JSON格式。"""
        
        if not self.client:
            return {"error": "未配置API"}
        
        try:
            response = self.client.chat.completions.create(
                model=self._model,
                messages=[{"role": "user", "content": update_prompt}],
                temperature=0.3,
                max_tokens=1500
            )
            
            content = response.choices[0].message.content if response.choices else None
            if content:
                start = content.find('{')
                end = content.rfind('}')
                if start != -1 and end != -1:
                    return json.loads(content[start:end+1])
        except Exception as e:
            return {"error": str(e)}
        
        return {"error": "解析失败"}


# 便捷函数
def generate_monthly_report(year: int = None, month: int = None) -> Dict:
    """生成月度报告的便捷函数"""
    analyzer = MonthlyAnalysis()
    analysis = analyzer.generate_monthly_analysis(year, month)
    if not analysis.get('error'):
        analyzer.save_analysis(analysis)
    return analysis


if __name__ == '__main__':
    # 测试
    analyzer = MonthlyAnalysis()
    
    # 获取12月事件（支持自动抓取）
    logger.info("=" * 60)
    logger.info("正在获取2025年12月重大事件（自动识别 + 预设）...")
    logger.info("=" * 60)
    
    events = analyzer.get_monthly_events(2025, 12)
    
    logger.info(f"共发现 {len(events)} 个重大事件")
    for e in events:
        source_tag = "[自动]" if e.get('source') == 'auto_detected' else "[预设]"
        impact = f"影响:{e.get('impact_score', '-')}/10" if e.get('impact_score') else ""
        direction = e.get('expected_direction', '')
        
        logger.info(f"📅 {e.get('date', '待定')} - {e.get('name', '')} ({e.get('importance', 'medium')}) {source_tag}")
        if impact or direction:
            logger.info(f"   {impact} {direction}")
        if e.get('analysis'):
            logger.info(f"   💡 {e['analysis'][:80]}...")
    
    logger.info("=" * 60)
    logger.info("正在生成月度深度分析...")
    logger.info("=" * 60)
    
    analysis = analyzer.generate_monthly_analysis(2025, 12)
    
    if not analysis.get('error'):
        filename = analyzer.save_analysis(analysis)
        logger.info(f"✅ 分析已保存: {filename}")
        logger.info(f"📝 月度总结:")
        logger.info("-" * 40)
        logger.info(analysis.get('summary', '无总结'))
        
        # 显示关键建议
        if analysis.get('stock_recommendations'):
            recs = analysis['stock_recommendations']
            if recs.get('buy'):
                logger.info(f"📈 建议加仓 ({len(recs['buy'])}只):")
                for stock in recs['buy'][:3]:
                    logger.info(f"  - {stock.get('symbol', '')} {stock.get('name', '')}: {stock.get('reason', '')[:50]}")
            if recs.get('sell'):
                logger.info(f"📉 建议减仓 ({len(recs['sell'])}只):")
                for stock in recs['sell'][:3]:
                    logger.info(f"  - {stock.get('symbol', '')} {stock.get('name', '')}: {stock.get('reason', '')[:50]}")
    else:
        logger.error(f"❌ 错误: {analysis.get('message')}")
        if analysis.get('raw_content'):
            logger.debug(f"原始内容预览: {analysis['raw_content'][:500]}...")
