import os
import json
from datetime import datetime, timedelta
from typing import List, Dict
from openai import OpenAI

class WeeklySummary:
    def __init__(self):
        self.api_key = os.getenv('DEEPSEEK_API_KEY')
        self.client = None
        if self.api_key:
            self.client = OpenAI(api_key=self.api_key, base_url="https://api.deepseek.com")

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
        
        prompt = f"""基于过去7天的财经新闻分析数据：

【一周市场情绪】
- 整体: {avg_sentiment['overall']:.2f}
- 中国: {avg_sentiment['cn']:.2f}
- 美国: {avg_sentiment['us']:.2f}

【股票提及统计】
{stocks_summary}

请分析这些股票在未来一周的走势预期。返回JSON（仅JSON，无其他文字）：
{{
  "stocks": [
    {{
      "symbol": "TSLA",
      "name": "特斯拉",
      "prediction": "上涨/下跌/震荡",
      "confidence": "高/中/低",
      "reason": "分析原因"
    }}
  ],
  "summary": "一周市场总体分析"
}}"""
        
        if not self.client:
            return self._mock_analysis(all_stocks, avg_sentiment)
        try:
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=2000
            )
            
            content = response.choices[0].message.content
            if content:
                start = content.find('{')
                end = content.rfind('}')
                if start != -1 and end != -1:
                    return json.loads(content[start:end+1])
        except Exception as e:
            print(f"Weekly analysis error: {e}")
        
        return {'stocks': [], 'summary': '分析失败'}
    
    def _calc_avg_sentiment(self, sentiments: List[Dict]) -> Dict:
        """计算平均情绪"""
        if not sentiments:
            return {'overall': 0, 'cn': 0, 'us': 0}
        
        return {
            'overall': sum(s.get('overall', 0) for s in sentiments) / len(sentiments),
            'cn': sum(s.get('cn', 0) for s in sentiments) / len(sentiments),
            'us': sum(s.get('us', 0) for s in sentiments) / len(sentiments)
        }
    
    def _mock_analysis(self, all_stocks: Dict, avg_sentiment: Dict) -> Dict:
        top = sorted(all_stocks.items(), key=lambda x: x[1]['up'] + x[1]['down'], reverse=True)[:5]
        stocks = []
        for symbol, stats in top:
            direction = '上涨' if stats['up'] >= stats['down'] else '震荡'
            stocks.append({
                'symbol': symbol,
                'name': stats['name'],
                'prediction': direction,
                'confidence': '低',
                'reason': '离线模式占位结果'
            })
        summary = (
            f"离线模式：整体情绪 {avg_sentiment['overall']:.2f}，"
            f"中国 {avg_sentiment['cn']:.2f}，美国 {avg_sentiment['us']:.2f}。"
        )
        return {'stocks': stocks, 'summary': summary}

    def save_analysis(self, analysis: Dict):
        """保存分析结果"""
        os.makedirs('data/weekly', exist_ok=True)
        filename = f"data/weekly/analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(analysis, f, ensure_ascii=False, indent=2)
        return filename
