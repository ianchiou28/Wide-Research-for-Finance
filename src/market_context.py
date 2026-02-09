"""
市场上下文数据获取器
在 LLM 分析前注入实时 / 当日的量价数据，提升情绪判断的准确性。
"""

import os
from datetime import datetime, timedelta
from typing import Dict, Optional
from logger import setup_logger

logger = setup_logger('market_context')

# 尝试导入数据源
try:
    import akshare as ak
    HAS_AKSHARE = True
except ImportError:
    HAS_AKSHARE = False

try:
    import yfinance as yf
    HAS_YFINANCE = True
except ImportError:
    HAS_YFINANCE = False


class MarketContext:
    """获取当前市场背景数据，用于增强 LLM prompt"""

    def __init__(self):
        self._cache: Dict[str, dict] = {}
        self._cache_ts: Dict[str, datetime] = {}
        self._cache_ttl = 1800  # 缓存 30 分钟

    def get_context_text(self) -> str:
        """
        生成可嵌入 LLM prompt 的市场背景文本。
        若数据不可获取，返回空字符串（不影响主流程）。
        """
        sections = []

        cn = self._get_cn_market()
        if cn:
            sections.append(self._format_cn(cn))

        us = self._get_us_market()
        if us:
            sections.append(self._format_us(us))

        if not sections:
            return ""

        header = "【当前市场背景（仅供参考）】"
        return header + "\n" + "\n".join(sections) + "\n"

    # ----------------------------------------------------------------
    # A 股数据
    # ----------------------------------------------------------------

    def _get_cn_market(self) -> Optional[Dict]:
        cached = self._from_cache('cn_market')
        if cached:
            return cached

        if not HAS_AKSHARE:
            return None

        try:
            data: Dict = {}

            # 上证指数实时行情
            try:
                df = ak.stock_zh_index_spot_em()
                sh = df[df['代码'] == '000001']
                if not sh.empty:
                    row = sh.iloc[0]
                    data['sh_index'] = {
                        'name': '上证指数',
                        'price': float(row.get('最新价', 0)),
                        'change_pct': float(row.get('涨跌幅', 0)),
                        'volume': float(row.get('成交量', 0)),
                        'amount': float(row.get('成交额', 0)),
                    }
            except Exception as e:
                logger.debug(f"获取上证指数失败: {e}")

            # 北向资金
            try:
                north_df = ak.stock_hsgt_north_net_flow_in_em(symbol="北向")
                if not north_df.empty:
                    latest = north_df.iloc[-1]
                    data['north_flow'] = round(float(latest.get('当日净流入', latest.iloc[-1])) / 1e8, 2)  # 亿
            except Exception as e:
                logger.debug(f"获取北向资金失败: {e}")

            if data:
                self._to_cache('cn_market', data)
            return data if data else None

        except Exception as e:
            logger.debug(f"获取A股市场数据失败: {e}")
            return None

    def _format_cn(self, data: Dict) -> str:
        lines = ["- A股市场:"]
        sh = data.get('sh_index')
        if sh:
            sign = '+' if sh['change_pct'] >= 0 else ''
            lines.append(
                f"  上证指数 {sh['price']:.2f} ({sign}{sh['change_pct']:.2f}%)"
                f"  成交额 {sh['amount']/1e8:.0f}亿"
            )
        north = data.get('north_flow')
        if north is not None:
            sign = '+' if north >= 0 else ''
            lines.append(f"  北向资金: {sign}{north}亿")
        return "\n".join(lines)

    # ----------------------------------------------------------------
    # 美股数据
    # ----------------------------------------------------------------

    def _get_us_market(self) -> Optional[Dict]:
        cached = self._from_cache('us_market')
        if cached:
            return cached

        if not HAS_YFINANCE:
            return None

        try:
            data: Dict = {}

            # 三大指数
            for symbol, name in [
                ('^GSPC', '标普500'),
                ('^DJI', '道琼斯'),
                ('^IXIC', '纳斯达克'),
            ]:
                try:
                    t = yf.Ticker(symbol)
                    info = t.fast_info
                    prev_close = float(getattr(info, 'previous_close', 0) or 0)
                    last = float(getattr(info, 'last_price', 0) or 0)
                    change_pct = ((last - prev_close) / prev_close * 100) if prev_close else 0
                    data[symbol] = {
                        'name': name,
                        'price': last,
                        'change_pct': round(change_pct, 2),
                    }
                except Exception:
                    pass

            # VIX 恐慌指数
            try:
                vix = yf.Ticker('^VIX')
                vix_info = vix.fast_info
                data['vix'] = round(float(getattr(vix_info, 'last_price', 0) or 0), 2)
            except Exception:
                pass

            if data:
                self._to_cache('us_market', data)
            return data if data else None

        except Exception as e:
            logger.debug(f"获取美股市场数据失败: {e}")
            return None

    def _format_us(self, data: Dict) -> str:
        lines = ["- 美股市场:"]
        for key in ['^GSPC', '^DJI', '^IXIC']:
            idx = data.get(key)
            if idx:
                sign = '+' if idx['change_pct'] >= 0 else ''
                lines.append(
                    f"  {idx['name']} {idx['price']:.2f} ({sign}{idx['change_pct']:.2f}%)"
                )
        vix = data.get('vix')
        if vix:
            level = '恐慌' if vix > 25 else '警惕' if vix > 20 else '平稳'
            lines.append(f"  VIX恐慌指数: {vix} ({level})")
        return "\n".join(lines)

    # ----------------------------------------------------------------
    # 缓存
    # ----------------------------------------------------------------

    def _from_cache(self, key: str) -> Optional[Dict]:
        ts = self._cache_ts.get(key)
        if ts and (datetime.now() - ts).total_seconds() < self._cache_ttl:
            return self._cache.get(key)
        return None

    def _to_cache(self, key: str, value: Dict):
        self._cache[key] = value
        self._cache_ts[key] = datetime.now()
