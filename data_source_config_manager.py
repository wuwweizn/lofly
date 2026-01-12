# -*- coding: utf-8 -*-
"""
数据源配置管理器
负责数据源配置的持久化存储和加载
"""

import json
import os
from typing import Dict, Optional


class DataSourceConfigManager:
    """数据源配置管理器"""
    
    def __init__(self, config_file: str = "data_source_config.json"):
        """
        初始化配置管理器
        
        Args:
            config_file: 配置文件路径
        """
        self.config_file = config_file
        self.config = self._load_config()
    
    def _load_config(self) -> Dict:
        """加载配置"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"加载数据源配置失败: {e}")
                return {}
        return {}
    
    def _save_config(self):
        """保存配置"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存数据源配置失败: {e}")
    
    def get_config(self) -> Dict:
        """获取配置"""
        return self.config.copy()
    
    def update_config(self, config: Dict):
        """
        更新配置
        
        Args:
            config: 新的配置字典
        """
        # 合并配置
        if 'update_interval' in config:
            self.config['update_interval'] = config['update_interval']
        
        # 更新各数据源配置
        for source_type in ['price_sources', 'nav_sources', 'fund_list_sources', 
                           'name_sources', 'purchase_limit_sources']:
            if source_type in config:
                if source_type not in self.config:
                    self.config[source_type] = {}
                for source_name, source_config in config[source_type].items():
                    if source_name not in self.config[source_type]:
                        self.config[source_type][source_name] = {}
                    self.config[source_type][source_name].update(source_config)
        
        # 如果更新了Tushare配置，同步到顶层
        if 'fund_list_sources' in config and 'tushare' in config['fund_list_sources']:
            tushare_config = config['fund_list_sources']['tushare']
            if 'token' in tushare_config:
                self.config['tushare_token'] = tushare_config['token']
            if 'enabled' in tushare_config:
                self.config['use_tushare'] = tushare_config['enabled']
        
        # 保存到文件
        self._save_config()
    
    def get_tushare_token(self) -> Optional[str]:
        """获取Tushare token"""
        # 优先从环境变量获取
        import os
        env_token = os.getenv('TUSHARE_TOKEN')
        if env_token:
            return env_token
        
        # 从配置文件中获取
        if 'fund_list_sources' in self.config and 'tushare' in self.config['fund_list_sources']:
            return self.config['fund_list_sources']['tushare'].get('token')
        
        # 从顶层配置获取（向后兼容）
        return self.config.get('tushare_token')
    
    def merge_with_default(self, default_config: Dict) -> Dict:
        """
        将保存的配置与默认配置合并
        
        Args:
            default_config: 默认配置
            
        Returns:
            合并后的配置
        """
        merged = default_config.copy()
        
        # 合并保存的配置
        if 'update_interval' in self.config:
            merged['update_interval'] = self.config['update_interval']
        
        # 合并各数据源配置
        for source_type in ['price_sources', 'nav_sources', 'fund_list_sources', 
                           'name_sources', 'purchase_limit_sources']:
            if source_type in self.config:
                if source_type not in merged:
                    merged[source_type] = {}
                for source_name, source_config in self.config[source_type].items():
                    if source_name in merged[source_type]:
                        merged[source_type][source_name].update(source_config)
                    else:
                        merged[source_type][source_name] = source_config
        
        # 同步Tushare token到顶层（向后兼容）
        tushare_token = self.get_tushare_token()
        if tushare_token:
            merged['tushare_token'] = tushare_token
            merged['use_tushare'] = True
        
        return merged
