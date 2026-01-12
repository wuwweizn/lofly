# -*- coding: utf-8 -*-
"""
LOF基金套利计算模块
计算套利机会和收益
"""

from typing import Dict, Optional
from config import TRADE_FEES, ARBITRAGE_THRESHOLD


class ArbitrageCalculator:
    """LOF基金套利计算器"""
    
    def __init__(self):
        self.fees = TRADE_FEES
        self.threshold = ARBITRAGE_THRESHOLD
    
    def calculate_arbitrage(self, fund_info: Dict) -> Optional[Dict]:
        """
        计算套利机会
        
        Args:
            fund_info: 包含price和nav的基金信息
            
        Returns:
            套利分析结果，如果没有套利机会返回None
        """
        if not fund_info or 'price' not in fund_info or 'nav' not in fund_info:
            return None
        
        price = fund_info['price']
        nav = fund_info['nav']
        
        if price <= 0 or nav <= 0:
            return None
        
        # 计算价差
        price_diff = price - nav
        price_diff_pct = (price_diff / nav) * 100
        
        # 判断套利方向
        is_premium = price > nav  # 溢价：场内价格 > 净值
        
        # 计算套利成本和收益
        if is_premium:
            # 溢价套利：场外申购（按净值）→ 场内卖出（按价格）
            # 操作顺序：1. 在场外申购基金份额（净值nav），2. 转到场内卖出（价格price）
            subscribe_cost = self.fees['subscribe_fee']
            sell_cost = self.fees['sell_commission'] + self.fees['stamp_tax']
            total_cost = subscribe_cost + sell_cost
            
            # 假设投入10000元计算
            investment = 10000
            # 1. 在场外申购：投入investment，扣除申购费后，按净值申购得份额
            subscribe_shares = investment * (1 - subscribe_cost) / nav
            # 2. 在场内卖出：持有份额，按价格卖出，扣除卖出费用
            final_value = subscribe_shares * price * (1 - sell_cost)
            # 净收益
            net_profit = final_value - investment
            profit_rate = (net_profit / investment) * 100
            
            # #region agent log
            import json
            import time
            log_data = {
                'sessionId': 'debug-session',
                'runId': 'run1',
                'hypothesisId': 'A',
                'location': 'arbitrage_calculator.py:calculate_arbitrage:premium',
                'message': '溢价套利计算',
                'data': {
                    'fund_code': fund_info.get('code', ''),
                    'price': price,
                    'nav': nav,
                    'investment': investment,
                    'subscribe_shares': subscribe_shares,
                    'final_value': final_value,
                    'net_profit': net_profit,
                    'profit_rate': profit_rate
                },
                'timestamp': int(time.time() * 1000)
            }
            try:
                with open('c:\\lof1\\.cursor\\debug.log', 'a', encoding='utf-8') as f:
                    f.write(json.dumps(log_data, ensure_ascii=False) + '\n')
            except: pass
            # #endregion
            
            arbitrage_type = '溢价套利'
            operation = '场外申购 → 场内卖出'
        else:
            # 折价套利：场内买入（按价格）→ 场外赎回（按净值）
            # 操作顺序：1. 在场内买入基金份额（价格price），2. 转到场外赎回（净值nav）
            redeem_cost = self.fees['redeem_fee']
            buy_cost = self.fees['buy_commission']
            total_cost = redeem_cost + buy_cost
            
            # 假设投入10000元计算
            investment = 10000
            # 1. 在场内买入：投入investment，扣除买入费用后，按价格买入得份额
            buy_shares = investment * (1 - buy_cost) / price
            # 2. 在场外赎回：持有份额，按净值赎回，扣除赎回费用
            final_value = buy_shares * nav * (1 - redeem_cost)
            # 净收益
            net_profit = final_value - investment
            profit_rate = (net_profit / investment) * 100
            
            # #region agent log
            import json
            import time
            log_data = {
                'sessionId': 'debug-session',
                'runId': 'run1',
                'hypothesisId': 'B',
                'location': 'arbitrage_calculator.py:calculate_arbitrage:discount',
                'message': '折价套利计算',
                'data': {
                    'fund_code': fund_info.get('code', ''),
                    'price': price,
                    'nav': nav,
                    'investment': investment,
                    'buy_shares': buy_shares,
                    'final_value': final_value,
                    'net_profit': net_profit,
                    'profit_rate': profit_rate
                },
                'timestamp': int(time.time() * 1000)
            }
            try:
                with open('c:\\lof1\\.cursor\\debug.log', 'a', encoding='utf-8') as f:
                    f.write(json.dumps(log_data, ensure_ascii=False) + '\n')
            except: pass
            # #endregion
            
            arbitrage_type = '折价套利'
            operation = '场内买入 → 场外赎回'
        
        # 判断是否有套利机会
        has_opportunity = (
            abs(price_diff) >= self.threshold['min_price_diff'] and
            profit_rate >= self.threshold['min_profit_rate'] * 100
        )
        
        return {
            'fund_code': fund_info.get('code', ''),
            'price': price,
            'nav': nav,
            'price_diff': round(price_diff, 4),
            'price_diff_pct': round(price_diff_pct, 2),
            'arbitrage_type': arbitrage_type,
            'operation': operation,
            'total_cost_rate': round(total_cost * 100, 2),
            'profit_rate': round(profit_rate, 2),
            'net_profit_10k': round(net_profit, 2),  # 投入1万元的净收益
            'has_opportunity': has_opportunity,
            'update_time': fund_info.get('update_time', ''),
        }
    
    def calculate_batch(self, funds_info: list) -> list:
        """
        批量计算套利机会
        
        Args:
            funds_info: 基金信息列表
            
        Returns:
            套利分析结果列表
        """
        results = []
        for fund_info in funds_info:
            result = self.calculate_arbitrage(fund_info)
            if result:
                results.append(result)
        return results
    
    def filter_opportunities(self, results: list) -> list:
        """
        过滤出有套利机会的结果
        
        Args:
            results: 套利分析结果列表
            
        Returns:
            有套利机会的结果列表
        """
        return [r for r in results if r.get('has_opportunity', False)]
    
    def sort_by_profit(self, results: list, reverse: bool = True) -> list:
        """
        按收益率排序
        
        Args:
            results: 套利分析结果列表
            reverse: 是否降序排列
            
        Returns:
            排序后的结果列表
        """
        return sorted(results, key=lambda x: x.get('profit_rate', 0), reverse=reverse)
