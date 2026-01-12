# -*- coding: utf-8 -*-
"""
套利记录模块
记录和管理套利交易流程
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional
from enum import Enum


class ArbitrageStatus(Enum):
    """套利状态"""
    PENDING = "pending"  # 待执行（已记录初始操作，等待完成）
    IN_PROGRESS = "in_progress"  # 进行中（已执行初始操作，等待最终操作）
    COMPLETED = "completed"  # 已完成
    CANCELLED = "cancelled"  # 已取消


class ArbitrageType(Enum):
    """套利类型"""
    PREMIUM = "premium"  # 溢价套利：场外申购 → 场内卖出
    DISCOUNT = "discount"  # 折价套利：场内买入 → 场外赎回


class ArbitrageRecorder:
    """套利记录器"""
    
    def __init__(self, data_file: str = "arbitrage_records.json"):
        """
        初始化套利记录器
        
        Args:
            data_file: 记录文件路径
        """
        self.data_file = data_file
        self.records = self._load_records()
    
    def _load_records(self) -> Dict[str, List[Dict]]:
        """加载记录（按用户ID组织）"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # 兼容旧格式（列表格式）
                    if isinstance(data, list):
                        # 转换为新格式：按用户ID组织
                        return {}
                    return data
            except Exception as e:
                print(f"加载套利记录失败: {e}")
                return {}
        return {}
    
    def _save_records(self):
        """保存记录"""
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.records, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存套利记录失败: {e}")
    
    def _get_user_records(self, username: str) -> List[Dict]:
        """获取用户的记录列表"""
        if username not in self.records:
            self.records[username] = []
        return self.records[username]
    
    def create_record(self, fund_code: str, fund_name: str, arbitrage_type: str, 
                     initial_price: float, initial_shares: float, initial_amount: float,
                     initial_date: str = None, username: str = None) -> str:
        """
        创建套利记录（记录初始操作）
        
        Args:
            fund_code: 基金代码
            fund_name: 基金名称
            arbitrage_type: 套利类型（'premium' 或 'discount'）
            initial_price: 初始价格（申购时的净值或买入时的价格）
            initial_shares: 初始份额
            initial_amount: 初始金额
            initial_date: 初始日期（格式：YYYY-MM-DD），默认为今天
            
        Returns:
            记录ID
        """
        record_id = f"{fund_code}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        if initial_date is None:
            initial_date = datetime.now().strftime('%Y-%m-%d')
        
        record = {
            'id': record_id,
            'username': username,  # 添加用户名
            'fund_code': fund_code,
            'fund_name': fund_name,
            'arbitrage_type': arbitrage_type,
            'status': ArbitrageStatus.IN_PROGRESS.value,
            'initial_operation': {
                'type': 'subscribe' if arbitrage_type == 'premium' else 'buy',
                'price': initial_price,
                'shares': initial_shares,
                'amount': initial_amount,
                'date': initial_date,
                'timestamp': datetime.now().isoformat()
            },
            'final_operation': None,
            'profit': None,
            'profit_rate': None,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        user_records = self._get_user_records(username)
        user_records.append(record)
        self._save_records()
        return record_id
    
    def complete_record(self, record_id: str, final_price: float, final_shares: float = None,
                       final_amount: float = None, final_date: str = None, username: str = None) -> bool:
        """
        完成套利记录（记录最终操作）
        
        Args:
            record_id: 记录ID
            final_price: 最终价格（赎回时的净值或卖出时的价格）
            final_shares: 最终份额（如果与初始份额不同）
            final_amount: 最终金额（如果提供，将使用此值计算）
            final_date: 最终日期（格式：YYYY-MM-DD），默认为今天
            
        Returns:
            是否成功
        """
        record = self.get_record(record_id, username)
        if not record:
            return False
        
        if record['status'] != ArbitrageStatus.IN_PROGRESS.value:
            return False
        
        if final_date is None:
            final_date = datetime.now().strftime('%Y-%m-%d')
        
        initial = record['initial_operation']
        if final_shares is None:
            final_shares = initial['shares']
        
        # 计算最终金额
        if final_amount is None:
            if record['arbitrage_type'] == 'premium':
                # 溢价套利：场内卖出
                final_amount = final_shares * final_price
            else:
                # 折价套利：场外赎回
                final_amount = final_shares * final_price
        
        record['final_operation'] = {
            'type': 'sell' if record['arbitrage_type'] == 'premium' else 'redeem',
            'price': final_price,
            'shares': final_shares,
            'amount': final_amount,
            'date': final_date,
            'timestamp': datetime.now().isoformat()
        }
        
        # 计算盈亏
        initial_amount = initial['amount']
        record['profit'] = final_amount - initial_amount
        record['profit_rate'] = (record['profit'] / initial_amount) * 100 if initial_amount > 0 else 0
        record['status'] = ArbitrageStatus.COMPLETED.value
        record['updated_at'] = datetime.now().isoformat()
        
        self._save_records()
        return True
    
    def cancel_record(self, record_id: str, username: str = None) -> bool:
        """
        取消套利记录
        
        Args:
            record_id: 记录ID
            username: 用户名（如果提供，只在该用户的记录中查找）
            
        Returns:
            是否成功
        """
        record = self.get_record(record_id, username)
        if not record:
            return False
        
        if record['status'] == ArbitrageStatus.IN_PROGRESS.value:
            record['status'] = ArbitrageStatus.CANCELLED.value
            record['updated_at'] = datetime.now().isoformat()
            self._save_records()
            return True
        return False
    
    def get_record(self, record_id: str, username: str = None) -> Optional[Dict]:
        """
        获取单条记录
        
        Args:
            record_id: 记录ID
            username: 用户名（如果提供，只在该用户的记录中查找）
            
        Returns:
            记录字典，如果不存在返回None
        """
        if username:
            user_records = self._get_user_records(username)
            for record in user_records:
                if record['id'] == record_id:
                    return record
        else:
            # 在所有用户的记录中查找
            for user_records in self.records.values():
                for record in user_records:
                    if record['id'] == record_id:
                        return record
        return None
    
    def get_all_records(self, fund_code: str = None, status: str = None, username: str = None) -> List[Dict]:
        """
        获取所有记录
        
        Args:
            fund_code: 基金代码（可选，用于筛选）
            status: 状态（可选，用于筛选）
            username: 用户名（如果提供，只返回该用户的记录）
            
        Returns:
            记录列表
        """
        if username:
            records = self._get_user_records(username)
        else:
            # 合并所有用户的记录
            records = []
            for user_records in self.records.values():
                records.extend(user_records)
        
        if fund_code:
            records = [r for r in records if r['fund_code'] == fund_code]
        if status:
            records = [r for r in records if r['status'] == status]
        # 按创建时间倒序排列
        records.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        return records
    
    def get_all_users_statistics(self) -> Dict:
        """
        获取所有用户的统计信息（管理员功能）
        
        Returns:
            统计信息字典
        """
        all_records = self.get_all_records()
        
        total_records = len(all_records)
        total_completed = sum(1 for r in all_records if r['status'] == 'completed')
        total_in_progress = sum(1 for r in all_records if r['status'] == 'in_progress')
        total_cancelled = sum(1 for r in all_records if r['status'] == 'cancelled')
        total_pending = sum(1 for r in all_records if r['status'] == 'pending')
        
        # 计算总盈亏
        total_profit = sum(
            (r.get('profit') or 0) for r in all_records 
            if r.get('profit') is not None
        )
        
        # 计算总金额
        total_amount = sum(
            (r.get('initial_operation', {}).get('amount') or 0) for r in all_records
        )
        
        # 计算整体盈亏率
        overall_profit_rate = (total_profit / total_amount * 100) if total_amount > 0 else 0
        
        # 按用户统计
        user_statistics = {}
        for record in all_records:
            username = record.get('username', 'unknown')
            if username not in user_statistics:
                user_statistics[username] = {
                    'total_records': 0,
                    'completed': 0,
                    'in_progress': 0,
                    'cancelled': 0,
                    'pending': 0,
                    'total_profit': 0,
                    'total_amount': 0,
                    'profit_rate': 0
                }
            
            user_stats = user_statistics[username]
            user_stats['total_records'] += 1
            user_stats[record['status']] = user_stats.get(record['status'], 0) + 1
            
            if record.get('profit') is not None:
                user_stats['total_profit'] += record.get('profit', 0)
            
            initial_amount = record.get('initial_operation', {}).get('amount', 0)
            user_stats['total_amount'] += initial_amount
        
        # 计算每个用户的盈亏率
        for username, user_stats in user_statistics.items():
            if user_stats['total_amount'] > 0:
                user_stats['profit_rate'] = (user_stats['total_profit'] / user_stats['total_amount']) * 100
        
        return {
            'total_records': total_records,
            'total_completed': total_completed,
            'total_in_progress': total_in_progress,
            'total_cancelled': total_cancelled,
            'total_pending': total_pending,
            'total_profit': total_profit,
            'total_amount': total_amount,
            'overall_profit_rate': overall_profit_rate,
            'user_statistics': user_statistics
        }
    
    def get_statistics(self, username: str = None) -> Dict:
        """
        获取统计信息
        
        Args:
            username: 用户名（如果提供，只统计该用户的记录）
            
        Returns:
            统计信息字典
        """
        if username:
            records = self._get_user_records(username)
        else:
            # 合并所有用户的记录
            records = []
            for user_records in self.records.values():
                records.extend(user_records)
        
        completed = [r for r in records if r['status'] == ArbitrageStatus.COMPLETED.value]
        
        total_count = len(completed)
        total_profit = sum(r.get('profit', 0) or 0 for r in completed)
        total_investment = sum(r['initial_operation']['amount'] for r in completed)
        
        profitable_count = len([r for r in completed if r.get('profit', 0) and r['profit'] > 0])
        loss_count = len([r for r in completed if r.get('profit', 0) and r['profit'] < 0])
        
        avg_profit_rate = 0
        if total_count > 0:
            profit_rates = [r.get('profit_rate', 0) or 0 for r in completed]
            avg_profit_rate = sum(profit_rates) / len(profit_rates) if profit_rates else 0
        
        return {
            'total_count': total_count,
            'total_profit': round(total_profit, 2),
            'total_investment': round(total_investment, 2),
            'total_return_rate': round((total_profit / total_investment * 100) if total_investment > 0 else 0, 2),
            'profitable_count': profitable_count,
            'loss_count': loss_count,
            'win_rate': round((profitable_count / total_count * 100) if total_count > 0 else 0, 2),
            'avg_profit_rate': round(avg_profit_rate, 2),
            'in_progress_count': len([r for r in records if r['status'] == ArbitrageStatus.IN_PROGRESS.value])
        }
    
    def get_daily_purchase_amount(self, username: str, fund_code: str, date: str = None) -> float:
        """
        获取用户指定日期对指定基金的累计申购金额
        
        Args:
            username: 用户名
            fund_code: 基金代码
            date: 日期（格式：YYYY-MM-DD），默认为今天
            
        Returns:
            累计申购金额（元）
        """
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        
        user_records = self._get_user_records(username)
        total_amount = 0.0
        
        for record in user_records:
            # 只统计同一基金、同一日期、且是溢价套利（申购）的记录
            if (record.get('fund_code') == fund_code and 
                record.get('arbitrage_type') == 'premium' and
                record.get('initial_operation', {}).get('date') == date):
                # 只统计进行中或已完成的记录（不包括已取消的）
                if record.get('status') in ['in_progress', 'completed']:
                    amount = record.get('initial_operation', {}).get('amount', 0)
                    if amount:
                        total_amount += float(amount)
        
        return total_amount
    
    def delete_record(self, record_id: str) -> bool:
        """
        删除记录
        
        Args:
            record_id: 记录ID
            
        Returns:
            是否成功
        """
        for i, record in enumerate(self.records):
            if record['id'] == record_id:
                self.records.pop(i)
                self._save_records()
                return True
        return False
