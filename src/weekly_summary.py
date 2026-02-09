import os
import sys
import json
from datetime import datetime
from typing import List, Dict
from openai import OpenAI
from logger import setup_logger

# 导入统一配置
try:
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config'))
    from settings import Config
except ImportError:
    Config = None

logger = setup_logger('weekly_summary')

class WeeklySummary:
    def __init__(self):
        self.api_key = os.getenv('DEEPSEEK_API_KEY')
        self.client = None
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
                    timeout=120.0,
                    max_retries=2
                )
                self._model = "deepseek-chat"
    
    def generate(self, weekly_reports: List[Dict]) -> Dict:
        """生成一周总结和个股预测"""
        if not weekly_reports:
            return {'stocks': [], 'summary': '数据不足'}
        
        # 聚合一周数据
        all_stocks = {}
        all_sentiments = []
        
        for report in weekly_reports:
            all_sentiments.append(report.get('sentiment', {}))
            for stock in report.get('stocks', []):
                key = stock['symbol']
                if key not in all_stocks:
                    all_stocks[key] = {'name': stock['name'], 'up': 0, 'down': 0, 'neutral': 0}
                if stock['direction'] == '上涨':
                    all_stocks[key]['up'] += 1
                elif stock['direction'] == '下跌':
                    all_stocks[key]['down'] += 1
                else:
                    all_stocks[key]['neutral'] += 1
        
        if not all_stocks:
            return {'stocks': [], 'summary': '本周无股票数据'}
        
        # 计算平均情绪
        avg_sentiment = self._calc_avg_sentiment(all_sentiments)
        
        # 构建分析提示
        stocks_summary = "\n".join([
            f"{sym}: {data['name']} (上涨{data['up']}次, 下跌{data['down']}次, 中性{data['neutral']}次)" 
            for sym, data in sorted(all_stocks.items(), key=lambda x: x[1]['up'] + x[1]['down'], reverse=True)[:20]
        ])
        
        prompt = f"""你是资深金融策略分析师。根据过去7天的新闻情绪数据，对活跃个股进行 **逐步推理** 预测。

## 本周数据
【市场情绪指数】
- 整体: {avg_sentiment['overall']:.2f}  (>0.3 乐观 / <-0.3 悲观)
- 中国: {avg_sentiment['cn']:.2f}
- 美国: {avg_sentiment['us']:.2f}

【个股新闻频次】
{stocks_summary}

## 分析要求
对每只股票：
1. 综合情绪方向 + 出现频次判断多空
2. 结合当前市场环境（整体偏多/偏空）修正预测
3. 置信度：高(频次≥4且方向一致) / 中(频次2-3) / 低(频次1或方向矛盾)
4. 给出不超过30字的理由

## Few-shot 示例
{{"symbol": "600519", "name": "贵州茅台", "prediction": "上涨", "confidence": "高", "reason": "Q3超预期+消费政策利好, 机构增持"}}

返回纯JSON:
{{
  "stocks": [
    {{"symbol": "xxx", "name": "xxx", "prediction": "上涨/下跌/震荡", "confidence": "高/中/低", "reason": "xxx"}}
  ],
  "market_outlook": "本周市场总体展望（50字内）",
  "risk_factors": ["风险1", "风险2"],
  "summary": "一周市场综合分析（100字内）"
}}"""
        
        if not self.client:
            return {'stocks': [], 'summary': '未配置 DeepSeek API，暂无周度分析'}

        try:
            response = self.client.chat.completions.create(
                model=self._model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=2000
            )
            content = response.choices[0].message.content if response.choices else None
            if content:
                start = content.find('{')
                end = content.rfind('}')
                if start != -1 and end != -1 and end > start:
                    return json.loads(content[start:end+1])
        except Exception as e:
            logger.error(f"Weekly analysis error: {e}")
            return {'stocks': [], 'summary': '生成周度分析失败'}

        return {'stocks': [], 'summary': 'AI 返回内容为空，暂无数据'}
    
    def _calc_avg_sentiment(self, sentiments: List[Dict]) -> Dict:
        """计算平均情绪"""
        if not sentiments:
            return {'overall': 0, 'cn': 0, 'us': 0}
        
        return {
            'overall': sum(s.get('overall', 0) for s in sentiments) / len(sentiments),
            'cn': sum(s.get('cn', 0) for s in sentiments) / len(sentiments),
            'us': sum(s.get('us', 0) for s in sentiments) / len(sentiments)
        }
    
    def save_analysis(self, analysis: Dict):
        """保存分析结果"""
        if not analysis:
            return ""
        output_dir = os.path.join('data', 'weekly')
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = os.path.join(output_dir, f'analysis_{timestamp}.json')
        payload = {
            **analysis,
            'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        return filename

