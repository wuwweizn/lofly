# -*- coding: utf-8 -*-
"""
LOF基金数据获取模块
获取场内价格和场外净值
"""

import requests
import json
import time
from typing import Dict, Optional, List
from datetime import datetime, timedelta
from config import DATA_SOURCE

# 尝试导入Tushare
try:
    import tushare as ts
    TUSHARE_AVAILABLE = True
except ImportError:
    TUSHARE_AVAILABLE = False
    print("警告: Tushare未安装，将使用其他数据源")

# 尝试导入akshare
try:
    import akshare as ak
    AKSHARE_AVAILABLE = True
except ImportError:
    AKSHARE_AVAILABLE = False
    print("警告: akshare未安装，将使用其他数据源")

# 尝试导入baostock
try:
    import baostock as bs
    BAOSTOCK_AVAILABLE = True
except ImportError:
    BAOSTOCK_AVAILABLE = False
    print("警告: baostock未安装，将使用其他数据源")


class LOFDataFetcher:
    """LOF基金数据获取器 - 多数据源支持（包括Tushare）"""
    
    def __init__(self, tushare_token: str = None):
        self.session = requests.Session()
        # 禁用代理，避免代理错误
        self.session.proxies = {
            'http': None,
            'https': None
        }
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'http://fund.eastmoney.com/',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8'
        })
        
        # 保存数据源配置（从全局配置导入，支持运行时更新）
        self.data_source_config = DATA_SOURCE
        
        # 初始化Tushare（根据配置决定是否启用）
        self.tushare_pro = None
        fund_list_sources = self.data_source_config.get('fund_list_sources', {})
        tushare_config = fund_list_sources.get('tushare', {})
        use_tushare = tushare_config.get('enabled', True) if fund_list_sources else DATA_SOURCE.get('use_tushare', True)
        
        # #region agent log
        import json
        log_data = {
            'sessionId': 'debug-session',
            'runId': 'run1',
            'hypothesisId': 'C',
            'location': 'data_fetcher.py:__init__:tushare_init_check',
            'message': '检查Tushare初始化条件',
            'data': {
                'tushare_available': TUSHARE_AVAILABLE,
                'use_tushare': use_tushare,
                'has_token': tushare_token is not None,
                'token_length': len(tushare_token) if tushare_token else 0,
                'token_preview': tushare_token[:20] + '...' if tushare_token and len(tushare_token) > 20 else tushare_token
            },
            'timestamp': int(time.time() * 1000)
        }
        try:
            with open('c:\\lof1\\.cursor\\debug.log', 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_data, ensure_ascii=False) + '\n')
        except: pass
        # #endregion
        
        if TUSHARE_AVAILABLE and use_tushare and tushare_token:
            try:
                # #region agent log
                log_data = {
                    'sessionId': 'debug-session',
                    'runId': 'run1',
                    'hypothesisId': 'C',
                    'location': 'data_fetcher.py:__init__:before_set_token',
                    'message': '准备设置Tushare token',
                    'data': {},
                    'timestamp': int(time.time() * 1000)
                }
                try:
                    with open('c:\\lof1\\.cursor\\debug.log', 'a', encoding='utf-8') as f:
                        f.write(json.dumps(log_data, ensure_ascii=False) + '\n')
                except: pass
                # #endregion
                
                ts.set_token(tushare_token)
                self.tushare_pro = ts.pro_api()
                
                # #region agent log
                log_data = {
                    'sessionId': 'debug-session',
                    'runId': 'run1',
                    'hypothesisId': 'C',
                    'location': 'data_fetcher.py:__init__:tushare_init_success',
                    'message': 'Tushare数据源初始化成功',
                    'data': {},
                    'timestamp': int(time.time() * 1000)
                }
                try:
                    with open('c:\\lof1\\.cursor\\debug.log', 'a', encoding='utf-8') as f:
                        f.write(json.dumps(log_data, ensure_ascii=False) + '\n')
                except: pass
                # #endregion
                
                print("Tushare数据源已初始化")
            except Exception as e:
                # #region agent log
                log_data = {
                    'sessionId': 'debug-session',
                    'runId': 'run1',
                    'hypothesisId': 'C',
                    'location': 'data_fetcher.py:__init__:tushare_init_error',
                    'message': 'Tushare初始化失败',
                    'data': {
                        'error_type': type(e).__name__,
                        'error_message': str(e),
                        'error_str': str(e)
                    },
                    'timestamp': int(time.time() * 1000)
                }
                try:
                    with open('c:\\lof1\\.cursor\\debug.log', 'a', encoding='utf-8') as f:
                        f.write(json.dumps(log_data, ensure_ascii=False) + '\n')
                except: pass
                # #endregion
                print(f"Tushare初始化失败: {e}")
                self.tushare_pro = None
        
        # baostock在需要时再登录
        self.baostock_logged_in = False
        
        # 缓存akshare基金申购信息（避免重复下载所有基金数据）
        self._akshare_purchase_cache = None
        self._akshare_purchase_cache_time = None
        
        # 缓存akshare基金申购信息（避免重复下载）
        self._akshare_purchase_cache = None
        self._akshare_purchase_cache_time = None
    
    def _is_source_enabled(self, source_type: str, source_name: str) -> bool:
        """检查数据源是否启用"""
        sources = self.data_source_config.get(source_type, {})
        source_config = sources.get(source_name, {})
        return source_config.get('enabled', True)  # 默认启用（向后兼容）
    
    def _get_enabled_sources(self, source_type: str) -> List[tuple]:
        """获取启用的数据源列表（按优先级排序）"""
        sources = self.data_source_config.get(source_type, {})
        enabled = [(name, config) for name, config in sources.items() if config.get('enabled', True)]
        enabled.sort(key=lambda x: x[1].get('priority', 999))
        return enabled
    
    def get_fund_chinese_name_tushare(self, fund_code: str) -> Optional[str]:
        """
        使用Tushare获取基金中文名称
        
        Args:
            fund_code: 基金代码（6位数字）
            
        Returns:
            基金中文名称，如果失败返回None
        """
        if not self.tushare_pro:
            return None
        
        try:
            # 使用Tushare获取基金基本信息
            # Tushare的基金代码格式：市场代码+基金代码，如 159001.SZ
            # LOF基金通常在深圳(SZ)或上海(SH)
            markets = ['SZ', 'SH']
            
            for market in markets:
                try:
                    # 构建Tushare代码格式
                    ts_code = f"{fund_code}.{market}"
                    
                    # 获取基金基本信息
                    df = self.tushare_pro.fund_basic(
                        ts_code=ts_code,
                        fields='ts_code,name,fund_type,market'
                    )
                    
                    if df is not None and not df.empty:
                        name = df.iloc[0]['name']
                        if name and any('\u4e00' <= char <= '\u9fff' for char in name):
                            return name
                except:
                    continue
            
            # 如果直接查询失败，尝试通过基金代码匹配
            try:
                df = self.tushare_pro.fund_basic(
                    market='E',  # E表示场内基金
                    status='L'   # L表示上市
                )
                
                if df is not None and not df.empty:
                    # 查找匹配的基金代码
                    fund_code_str = str(fund_code)
                    for _, row in df.iterrows():
                        ts_code = str(row.get('ts_code', ''))
                        # 如果ts_code包含基金代码
                        if fund_code_str in ts_code:
                            name = row.get('name', '')
                            if name and any('\u4e00' <= char <= '\u9fff' for char in name):
                                return name
            except:
                pass
                
        except Exception as e:
            print(f"Tushare获取基金名称失败 {fund_code}: {e}")
        
        return None
    
    def get_lof_funds_list_tushare(self) -> List[Dict]:
        """
        使用Tushare获取LOF基金列表（包含基金类型）
        
        Returns:
            基金列表，包含代码、中文名称和类型（index/stock）
        """
        # #region agent log
        import json
        log_data = {
            'sessionId': 'debug-session',
            'runId': 'run1',
            'hypothesisId': 'B',
            'location': 'data_fetcher.py:get_lof_funds_list_tushare:entry',
            'message': '开始从Tushare获取LOF基金列表',
            'data': {'tushare_pro_available': self.tushare_pro is not None},
            'timestamp': int(time.time() * 1000)
        }
        try:
            with open('c:\\lof1\\.cursor\\debug.log', 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_data, ensure_ascii=False) + '\n')
        except: pass
        # #endregion
        
        if not self.tushare_pro:
            # #region agent log
            log_data = {
                'sessionId': 'debug-session',
                'runId': 'run1',
                'hypothesisId': 'B',
                'location': 'data_fetcher.py:get_lof_funds_list_tushare:no_tushare',
                'message': 'Tushare未初始化，无法获取基金列表',
                'data': {},
                'timestamp': int(time.time() * 1000)
            }
            try:
                with open('c:\\lof1\\.cursor\\debug.log', 'a', encoding='utf-8') as f:
                    f.write(json.dumps(log_data, ensure_ascii=False) + '\n')
            except: pass
            # #endregion
            return []
        
        try:
            # #region agent log
            log_data = {
                'sessionId': 'debug-session',
                'runId': 'run1',
                'hypothesisId': 'B',
                'location': 'data_fetcher.py:get_lof_funds_list_tushare:before_api_call',
                'message': '准备调用Tushare API',
                'data': {},
                'timestamp': int(time.time() * 1000)
            }
            try:
                with open('c:\\lof1\\.cursor\\debug.log', 'a', encoding='utf-8') as f:
                    f.write(json.dumps(log_data, ensure_ascii=False) + '\n')
            except: pass
            # #endregion
            
            # 获取场内上市基金
            df = self.tushare_pro.fund_basic(
                market='E',  # E表示场内基金
                status='L'   # L表示上市
            )
            
            # #region agent log
            log_data = {
                'sessionId': 'debug-session',
                'runId': 'run1',
                'hypothesisId': 'B',
                'location': 'data_fetcher.py:get_lof_funds_list_tushare:after_api_call',
                'message': 'Tushare API调用完成',
                'data': {
                    'df_is_none': df is None,
                    'df_empty': df.empty if df is not None else None,
                    'df_shape': list(df.shape) if df is not None else None
                },
                'timestamp': int(time.time() * 1000)
            }
            try:
                with open('c:\\lof1\\.cursor\\debug.log', 'a', encoding='utf-8') as f:
                    f.write(json.dumps(log_data, ensure_ascii=False) + '\n')
            except: pass
            # #endregion
            
            if df is not None and not df.empty:
                lof_funds = []
                for _, row in df.iterrows():
                    ts_code = str(row.get('ts_code', ''))
                    name = str(row.get('name', ''))
                    fund_type = str(row.get('fund_type', ''))
                    
                    # 筛选LOF基金（名称包含LOF或基金类型为LOF）
                    if 'LOF' in name.upper() or 'LOF' in fund_type.upper():
                        # 提取基金代码（从ts_code中提取，如159001.SZ -> 159001）
                        if '.' in ts_code:
                            code = ts_code.split('.')[0]
                            if len(code) == 6 and code.isdigit():
                                # 判断基金类型：指数型或股票型
                                fund_category = self._classify_fund_type(name, fund_type)
                                
                                lof_funds.append({
                                    'code': code,
                                    'name': name,
                                    'type': fund_category  # 'index' 或 'stock'
                                })
                
                # #region agent log
                log_data = {
                    'sessionId': 'debug-session',
                    'runId': 'run1',
                    'hypothesisId': 'B',
                    'location': 'data_fetcher.py:get_lof_funds_list_tushare:success',
                    'message': '成功获取LOF基金列表',
                    'data': {'lof_funds_count': len(lof_funds)},
                    'timestamp': int(time.time() * 1000)
                }
                try:
                    with open('c:\\lof1\\.cursor\\debug.log', 'a', encoding='utf-8') as f:
                        f.write(json.dumps(log_data, ensure_ascii=False) + '\n')
                except: pass
                # #endregion
                
                return lof_funds
        except Exception as e:
            # #region agent log
            log_data = {
                'sessionId': 'debug-session',
                'runId': 'run1',
                'hypothesisId': 'B',
                'location': 'data_fetcher.py:get_lof_funds_list_tushare:error',
                'message': 'Tushare获取LOF基金列表失败',
                'data': {
                    'error_type': type(e).__name__,
                    'error_message': str(e),
                    'error_str': str(e)
                },
                'timestamp': int(time.time() * 1000)
            }
            try:
                with open('c:\\lof1\\.cursor\\debug.log', 'a', encoding='utf-8') as f:
                    f.write(json.dumps(log_data, ensure_ascii=False) + '\n')
            except: pass
            # #endregion
            print(f"Tushare获取LOF基金列表失败: {e}")
        
        return []
    
    def _classify_fund_type(self, name: str, fund_type: str = '') -> str:
        """
        分类基金类型：指数型或股票型
        
        Args:
            name: 基金名称
            fund_type: 基金类型字段
            
        Returns:
            'index' 或 'stock'
        """
        name_lower = name.lower()
        type_lower = fund_type.lower() if fund_type else ''
        
        # 指数型LOF的特征
        index_keywords = [
            '指数', 'index', 'etf', '中证', '国证', '上证', '深证',
            '沪深', '创业板', '中小板', '行业', '主题', '分级'
        ]
        
        # 股票型LOF的特征
        stock_keywords = [
            '混合', '股票', '成长', '价值', '精选', '优选', '灵活',
            '配置', '策略', '主题', '行业精选'
        ]
        
        # 优先判断指数型（特征更明显）
        for keyword in index_keywords:
            if keyword in name_lower or keyword in type_lower:
                return 'index'
        
        # 判断股票型
        for keyword in stock_keywords:
            if keyword in name_lower or keyword in type_lower:
                return 'stock'
        
        # 默认：如果名称包含"指数"相关词汇，归为指数型，否则归为股票型
        if any(kw in name_lower for kw in ['指数', 'index', 'etf']):
            return 'index'
        else:
            return 'stock'
    
    def get_fund_chinese_name(self, fund_code: str) -> Optional[str]:
        """
        获取基金的中文名称
        
        Args:
            fund_code: 基金代码
            
        Returns:
            基金中文名称，如果失败返回None
        """
        # #region agent log
        import json
        log_data = {
            'sessionId': 'debug-session',
            'runId': 'run1',
            'hypothesisId': 'D',
            'location': 'data_fetcher.py:get_fund_chinese_name:entry',
            'message': '开始获取基金中文名称',
            'data': {'fund_code': fund_code, 'tushare_available': self.tushare_pro is not None},
            'timestamp': int(time.time() * 1000)
        }
        try:
            with open('c:\\lof1\\.cursor\\debug.log', 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_data, ensure_ascii=False) + '\n')
        except: pass
        # #endregion
        
        # 优先使用Tushare获取（最准确）
        if self.tushare_pro:
            tushare_name = self.get_fund_chinese_name_tushare(fund_code)
            if tushare_name:
                # #region agent log
                log_data = {
                    'sessionId': 'debug-session',
                    'runId': 'run1',
                    'hypothesisId': 'D',
                    'location': 'data_fetcher.py:get_fund_chinese_name:tushare_success',
                    'message': '从Tushare获取中文名称成功',
                    'data': {'fund_code': fund_code, 'name': tushare_name},
                    'timestamp': int(time.time() * 1000)
                }
                try:
                    with open('c:\\lof1\\.cursor\\debug.log', 'a', encoding='utf-8') as f:
                        f.write(json.dumps(log_data, ensure_ascii=False) + '\n')
                except: pass
                # #endregion
                return tushare_name
        
        # 方法1：从基金基本信息API获取（最可靠）
        if self._is_source_enabled('name_sources', 'eastmoney_api'):
            try:
                url = 'http://api.fund.eastmoney.com/f10/F10FundBasicInfo.aspx'
                params = {
                    'fundCode': fund_code,
                    'callback': 'jQuery'
                }
                response = self.session.get(url, params=params, timeout=5)
                if response.status_code == 200:
                    import re
                    content = response.text
                    json_match = re.search(r'jQuery\((.+)\)', content)
                    if json_match:
                        data = json.loads(json_match.group(1))
                        if data.get('Data'):
                            # 尝试多个可能的字段名
                            name_fields = ['SHORTNAME', 'FULLNAME', 'FundName', 'Name']
                            for field in name_fields:
                                name = data['Data'].get(field, '')
                                if name and any('\u4e00' <= char <= '\u9fff' for char in name):
                                    # #region agent log
                                    log_data = {
                                        'sessionId': 'debug-session',
                                        'runId': 'run1',
                                        'hypothesisId': 'D',
                                        'location': 'data_fetcher.py:get_fund_chinese_name:success_api',
                                        'message': '从API获取中文名称成功',
                                        'data': {'fund_code': fund_code, 'name': name, 'field': field},
                                        'timestamp': int(time.time() * 1000)
                                    }
                                    try:
                                        with open('c:\\lof1\\.cursor\\debug.log', 'a', encoding='utf-8') as f:
                                            f.write(json.dumps(log_data, ensure_ascii=False) + '\n')
                                    except: pass
                                    # #endregion
                                    return name
            except Exception as e:
                pass
        
        # 方法2：从基金JS文件获取
        if self._is_source_enabled('name_sources', 'eastmoney_js'):
            try:
                url2 = f'http://fund.eastmoney.com/js/{fund_code}.js'
                response2 = self.session.get(url2, timeout=5)
                if response2.status_code == 200:
                    import re
                    content = response2.text
                    # 提取中文名称：DWJC:"基金名称"
                    name_match = re.search(r'DWJC:"([^"]+)"', content)
                    if name_match:
                        name = name_match.group(1)
                        if any('\u4e00' <= char <= '\u9fff' for char in name):
                            # #region agent log
                            log_data = {
                                'sessionId': 'debug-session',
                                'runId': 'run1',
                                'hypothesisId': 'D',
                                'location': 'data_fetcher.py:get_fund_chinese_name:success_js',
                                'message': '从JS文件获取中文名称成功',
                                'data': {'fund_code': fund_code, 'name': name},
                                'timestamp': int(time.time() * 1000)
                            }
                            try:
                                with open('c:\\lof1\\.cursor\\debug.log', 'a', encoding='utf-8') as f:
                                    f.write(json.dumps(log_data, ensure_ascii=False) + '\n')
                            except: pass
                            # #endregion
                            return name
            except Exception as e:
                pass
        
        return None
    
    def get_lof_funds_list(self) -> list:
        """
        获取LOF基金列表（优先使用Tushare）
        
        Returns:
            基金列表，包含代码和名称
        """
        # #region agent log
        import json
        log_data = {
            'sessionId': 'debug-session',
            'runId': 'run1',
            'hypothesisId': 'B',
            'location': 'data_fetcher.py:get_lof_funds_list:entry',
            'message': '开始获取LOF基金列表',
            'data': {'tushare_available': self.tushare_pro is not None},
            'timestamp': int(time.time() * 1000)
        }
        try:
            with open('c:\\lof1\\.cursor\\debug.log', 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_data, ensure_ascii=False) + '\n')
        except: pass
        # #endregion
        
        # 优先使用Tushare获取（更准确，包含中文名称）
        if self.tushare_pro:
            tushare_funds = self.get_lof_funds_list_tushare()
            if tushare_funds:
                # #region agent log
                log_data = {
                    'sessionId': 'debug-session',
                    'runId': 'run1',
                    'hypothesisId': 'B',
                    'location': 'data_fetcher.py:get_lof_funds_list:tushare_success',
                    'message': '从Tushare获取LOF基金列表成功',
                    'data': {'count': len(tushare_funds), 'sample': tushare_funds[:3]},
                    'timestamp': int(time.time() * 1000)
                }
                try:
                    with open('c:\\lof1\\.cursor\\debug.log', 'a', encoding='utf-8') as f:
                        f.write(json.dumps(log_data, ensure_ascii=False) + '\n')
                except: pass
                # #endregion
                return tushare_funds
        
        # 备用方案：从东方财富获取
        try:
            # 从东方财富获取LOF基金列表
            url = 'http://fund.eastmoney.com/js/fundcode_search.js'
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                import re
                # 解析JS文件中的基金数据
                content = response.text
                # 提取所有基金数据
                pattern = r'\["(\d{6})","([^"]+)"[^\]]*\]'
                matches = re.findall(pattern, content)
                
                # #region agent log
                log_data = {
                    'sessionId': 'debug-session',
                    'runId': 'run1',
                    'hypothesisId': 'B',
                    'location': 'data_fetcher.py:get_lof_funds_list:after_parse',
                    'message': '解析基金数据完成',
                    'data': {'total_matches': len(matches), 'sample_matches': matches[:3]},
                    'timestamp': int(time.time() * 1000)
                }
                try:
                    with open('c:\\lof1\\.cursor\\debug.log', 'a', encoding='utf-8') as f:
                        f.write(json.dumps(log_data, ensure_ascii=False) + '\n')
                except: pass
                # #endregion
                
                lof_funds = []
                filtered_by_code_16 = 0
                filtered_by_code_50_51 = 0
                filtered_by_name_lof = 0
                filtered_both = 0
                
                for code, name in matches:
                    # 改进的LOF基金筛选逻辑：
                    # 1. LOF基金代码通常以16开头（深圳）或50/51开头（上海）
                    # 2. 名称包含LOF、lof、上市型开放式、上市开放式
                    is_lof_code = (code.startswith('16') or 
                                  code.startswith('50') or 
                                  code.startswith('51'))
                    has_lof_name = ('LOF' in name or 
                                   'lof' in name.lower() or
                                   '上市型开放式' in name or
                                   '上市开放式' in name)
                    
                    if code.startswith('16'):
                        filtered_by_code_16 += 1
                    if code.startswith('50') or code.startswith('51'):
                        filtered_by_code_50_51 += 1
                    if has_lof_name:
                        filtered_by_name_lof += 1
                    
                    # 只要满足代码范围或名称包含LOF即可（放宽条件）
                    if is_lof_code and has_lof_name:
                        filtered_both += 1
                        # 先使用原始名称，中文名称在批量处理时获取（避免太慢）
                        lof_funds.append({
                            'code': code,
                            'name': name
                        })
                
                # #region agent log
                log_data = {
                    'sessionId': 'debug-session',
                    'runId': 'run1',
                    'hypothesisId': 'B',
                    'location': 'data_fetcher.py:get_lof_funds_list:after_filter',
                    'message': '筛选LOF基金完成',
                    'data': {
                        'total_funds': len(matches),
                        'code_16_count': filtered_by_code_16,
                        'code_50_51_count': filtered_by_code_50_51,
                        'name_lof_count': filtered_by_name_lof,
                        'both_match_count': filtered_both,
                        'final_lof_count': len(lof_funds),
                        'sample_lof_funds': lof_funds[:5]
                    },
                    'timestamp': int(time.time() * 1000)
                }
                try:
                    with open('c:\\lof1\\.cursor\\debug.log', 'a', encoding='utf-8') as f:
                        f.write(json.dumps(log_data, ensure_ascii=False) + '\n')
                except: pass
                # #endregion
                
                return lof_funds
        except Exception as e:
            # #region agent log
            log_data = {
                'sessionId': 'debug-session',
                'runId': 'run1',
                'hypothesisId': 'B',
                'location': 'data_fetcher.py:get_lof_funds_list:error',
                'message': '获取LOF基金列表失败',
                'data': {'error': str(e)},
                'timestamp': int(time.time() * 1000)
            }
            try:
                with open('c:\\lof1\\.cursor\\debug.log', 'a', encoding='utf-8') as f:
                    f.write(json.dumps(log_data, ensure_ascii=False) + '\n')
            except: pass
            # #endregion
            print(f"获取LOF基金列表失败: {e}")
        
        return []
    
    def get_fund_price(self, fund_code: str, market: str = 'auto') -> Optional[Dict]:
        """
        获取LOF基金场内实时价格（多数据源交叉验证）
        
        Args:
            fund_code: 基金代码（6位数字）
            market: 市场代码，'sz'=深圳(1), 'sh'=上海(0), 'auto'=自动判断
            
        Returns:
            包含价格信息的字典，如果失败返回None
        """
        # 自动判断市场：16开头通常是深圳，50/51开头通常是上海
        if market == 'auto':
            if fund_code.startswith('16'):
                market = 'sz'
            elif fund_code.startswith('50') or fund_code.startswith('51'):
                market = 'sh'
            else:
                market = 'sz'  # 默认深圳
        
        secid_map = {'sz': '1', 'sh': '0'}
        secid = secid_map.get(market, '1')
        market_code = 'sz' if market == 'sz' else 'sh'
        
        prices = []  # 收集多个数据源的价格
        
        # 方法1：东方财富股票实时行情API（使用完整字段）
        if self._is_source_enabled('price_sources', 'eastmoney_stock'):
            try:
                url = 'http://push2.eastmoney.com/api/qt/stock/get'
                params = {
                    'secid': f'{secid}.{fund_code}',
                    'fields': 'f57,f58,f107,f137,f46,f44,f45,f47,f48,f60,f170,f43,f49,f50,f51,f52,f53,f54,f55,f56',
                    'fltt': 2,
                    'invt': 2
                }
                
                response = self.session.get(url, params=params, timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    if data.get('data'):
                        price_data = data['data']
                        # f43是当前价（单位：分），f44是昨收（单位：分）
                        current_price = price_data.get('f43', 0)
                        if current_price and current_price > 0:
                            price = float(current_price) / 100
                            prev_close = float(price_data.get('f44', current_price)) / 100
                            change_pct = ((price - prev_close) / prev_close * 100) if prev_close > 0 else 0
                            
                            if price > 0:
                                prices.append({
                                    'code': fund_code,
                                    'price': price,
                                    'change_pct': change_pct / 100,
                                    'volume': price_data.get('f47', 0),
                                    'amount': price_data.get('f48', 0),
                                    'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                    'source': 'eastmoney_stock'
                                })
            except Exception as e:
                print(f"东方财富股票API获取失败 {fund_code}: {e}")
        
        # 方法2：东方财富基金套利API（专门用于套利）
        if self._is_source_enabled('price_sources', 'eastmoney_arbitrage'):
            try:
                url2 = 'https://zqhdplus.eastmoney.com/api/fundArbitrage/getFundArbitrageList'
                params2 = {
                    'pageIndex': 1,
                    'pageSize': 100,
                    'fundCode': fund_code
                }
                response2 = self.session.get(url2, params=params2, timeout=5)
                if response2.status_code == 200:
                    data2 = response2.json()
                    if data2.get('Data') and data2['Data'].get('List'):
                        for item in data2['Data']['List']:
                            if item.get('FundCode') == fund_code:
                                price = float(item.get('MarketPrice', 0))
                                if price > 0:
                                    prices.append({
                                        'code': fund_code,
                                        'price': price,
                                        'change_pct': float(item.get('ChangePercent', 0)) / 100,
                                        'volume': item.get('Volume', 0),
                                        'amount': item.get('Amount', 0),
                                        'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                        'source': 'eastmoney_arbitrage'
                                    })
                                break
            except Exception as e:
                print(f"东方财富套利API获取失败 {fund_code}: {e}")
        
        # 方法3：新浪财经实时行情（最常用，数据准确）
        if self._is_source_enabled('price_sources', 'sina'):
            try:
                url3 = f'http://hq.sinajs.cn/list={market_code}{fund_code}'
                headers3 = {
                    'Referer': 'http://finance.sina.com.cn',
                    'User-Agent': 'Mozilla/5.0'
                }
                response3 = self.session.get(url3, headers=headers3, timeout=5)
                if response3.status_code == 200:
                    import re
                    content = response3.text
                    # 解析新浪格式：var hq_str_sz161725="招商中证白酒,1.234,1.235,1.236,1.237,1.238,1.239,1.240,1.241,1.242,1.243,2024-01-01,09:30:00,00"
                    match = re.search(r'="([^"]+)"', content)
                    if match:
                        parts = match.group(1).split(',')
                        if len(parts) >= 3:
                            price = float(parts[3])  # 当前价（parts[3]是现价，parts[1]是名称）
                            if price > 0:
                                prev_close = float(parts[2]) if len(parts) > 2 and parts[2] else price
                                change_pct = ((price - prev_close) / prev_close) if prev_close > 0 else 0
                                
                                prices.append({
                                    'code': fund_code,
                                    'price': price,
                                    'change_pct': change_pct,
                                    'volume': float(parts[8]) if len(parts) > 8 and parts[8] else 0,
                                    'amount': float(parts[9]) if len(parts) > 9 and parts[9] else 0,
                                    'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                    'source': 'sina'
                                })
            except Exception as e:
                print(f"新浪财经API获取失败 {fund_code}: {e}")
        
        # 方法4：腾讯财经实时行情
        if self._is_source_enabled('price_sources', 'tencent'):
            try:
                url4 = f'http://qt.gtimg.cn/q={market_code}{fund_code}'
                headers4 = {
                    'Referer': 'http://qq.com',
                    'User-Agent': 'Mozilla/5.0'
                }
                response4 = self.session.get(url4, headers=headers4, timeout=5)
                if response4.status_code == 200:
                    import re
                    content = response4.text
                    # 解析腾讯格式：v_sz161725="1~招商中证白酒~161725~1.234~1.235~..."
                    match = re.search(r'="([^"]+)"', content)
                    if match:
                        parts = match.group(1).split('~')
                        if len(parts) >= 5:
                            price = float(parts[3])  # 当前价
                            if price > 0:
                                prev_close = float(parts[4]) if len(parts) > 4 and parts[4] else price
                                change_pct = ((price - prev_close) / prev_close) if prev_close > 0 else 0
                                
                                prices.append({
                                    'code': fund_code,
                                    'price': price,
                                    'change_pct': change_pct,
                                    'volume': float(parts[6]) if len(parts) > 6 and parts[6] else 0,
                                    'amount': float(parts[7]) if len(parts) > 7 and parts[7] else 0,
                                    'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                    'source': 'tencent'
                                })
            except Exception as e:
                print(f"腾讯财经API获取失败 {fund_code}: {e}")
        
        # 方法5：网易财经实时行情
        if self._is_source_enabled('price_sources', 'netease'):
            try:
                url5 = f'http://api.money.126.net/data/feed/{market_code}{fund_code}'
                response5 = self.session.get(url5, timeout=5)
                if response5.status_code == 200:
                    import re
                    content = response5.text
                    # 解析网易格式：_ntes_quote_callback({"161725":{"name":"...","price":1.234,...}});
                    match = re.search(r'"price":([\d.]+)', content)
                    if match:
                        price = float(match.group(1))
                        if price > 0:
                            prices.append({
                                'code': fund_code,
                                'price': price,
                                'change_pct': 0,  # 网易可能不提供涨跌幅
                                'volume': 0,
                                'amount': 0,
                                'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                'source': 'netease'
                            })
            except Exception as e:
                print(f"网易财经API获取失败 {fund_code}: {e}")
        
        # 数据验证和选择：多数据源交叉验证
        if prices:
            # 移除异常价格（价格<=0或明显异常）
            valid_prices = [p for p in prices if p['price'] > 0 and 0.01 < p['price'] < 100]
            
            if not valid_prices:
                return None
            
            # 如果只有一个数据源，直接返回
            if len(valid_prices) == 1:
                return {k: v for k, v in valid_prices[0].items() if k != 'source'}
            
            # 多个数据源时，计算价格中位数和平均值
            price_values = [p['price'] for p in valid_prices]
            price_median = sorted(price_values)[len(price_values) // 2]
            price_avg = sum(price_values) / len(price_values)
            
            # 选择最接近中位数的价格（排除异常值）
            best_price = None
            min_diff = float('inf')
            
            for p in valid_prices:
                # 优先选择新浪财经（最常用且准确）
                if p['source'] == 'sina':
                    diff = abs(p['price'] - price_median)
                    if diff < min_diff:
                        min_diff = diff
                        best_price = p
                # 其次选择东方财富股票API
                elif p['source'] == 'eastmoney_stock' and best_price is None:
                    diff = abs(p['price'] - price_median)
                    if diff < min_diff:
                        min_diff = diff
                        best_price = p
                # 再次选择套利API
                elif p['source'] == 'eastmoney_arbitrage' and best_price is None:
                    diff = abs(p['price'] - price_median)
                    if diff < min_diff:
                        min_diff = diff
                        best_price = p
            
            # 如果还没找到，选择最接近中位数的
            if best_price is None:
                for p in valid_prices:
                    diff = abs(p['price'] - price_median)
                    if diff < min_diff:
                        min_diff = diff
                        best_price = p
            
            # 如果价格差异过大（超过5%），发出警告
            price_range_pct = 0
            if len(price_values) > 1:
                price_range = max(price_values) - min(price_values)
                price_range_pct = (price_range / price_avg) * 100 if price_avg > 0 else 0
                if price_range_pct > 5:
                    print(f"警告：基金 {fund_code} 多个数据源价格差异较大 ({price_range_pct:.2f}%)，已选择最接近中位数的价格")
            
            result = {k: v for k, v in best_price.items() if k != 'source'}
            result['price_confidence'] = 'high' if price_range_pct < 1 else 'medium' if price_range_pct < 3 else 'low'
            result['price_sources_count'] = len(valid_prices)
            return result
        
        return None
    
    def get_fund_nav(self, fund_code: str) -> Optional[Dict]:
        """
        获取LOF基金场外净值（多数据源）
        
        Args:
            fund_code: 基金代码（6位数字）
            
        Returns:
            包含净值信息的字典，如果失败返回None
        """
        navs = []  # 收集多个数据源的净值
        
        # 方法1：东方财富基金净值API（最准确）
        if self._is_source_enabled('nav_sources', 'eastmoney_api'):
            try:
                url = 'http://api.fund.eastmoney.com/f10/lsjz'
                params = {
                    'callback': 'jQuery',
                    'fundCode': fund_code,
                    'pageIndex': 1,
                    'pageSize': 1,
                    'startDate': '',
                    'endDate': '',
                    '_': int(time.time() * 1000)
                }
                response = self.session.get(url, params=params, timeout=5)
                if response.status_code == 200:
                    import re
                    content = response.text
                    json_match = re.search(r'jQuery\((.+)\)', content)
                    if json_match:
                        data = json.loads(json_match.group(1))
                        if data.get('Data') and data['Data'].get('LSJZList'):
                            lsjz = data['Data']['LSJZList'][0]
                            nav = float(lsjz.get('DWJZ', 0))
                            if nav > 0:
                                navs.append({
                                    'code': fund_code,
                                    'nav': nav,
                                    'date': lsjz.get('FSRQ', ''),
                                    'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                    'source': 'eastmoney_api'
                                })
            except Exception as e:
                print(f"东方财富净值API获取失败 {fund_code}: {e}")
        
        # 方法2：东方财富基金套利API（包含最新净值）
        if self._is_source_enabled('nav_sources', 'eastmoney_arbitrage'):
            try:
                url2 = 'https://zqhdplus.eastmoney.com/api/fundArbitrage/getFundArbitrageList'
                params2 = {
                    'pageIndex': 1,
                    'pageSize': 100,
                    'fundCode': fund_code
                }
                response2 = self.session.get(url2, params=params2, timeout=5)
                if response2.status_code == 200:
                    data2 = response2.json()
                    if data2.get('Data') and data2['Data'].get('List'):
                        for item in data2['Data']['List']:
                            if item.get('FundCode') == fund_code:
                                nav = float(item.get('NetValue', 0))
                                if nav > 0:
                                    navs.append({
                                        'code': fund_code,
                                        'nav': nav,
                                        'date': item.get('NetValueDate', ''),
                                        'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                        'source': 'eastmoney_arbitrage'
                                    })
                                break
            except Exception as e:
                print(f"东方财富套利API净值获取失败 {fund_code}: {e}")
        
        # 方法3：从基金详情页获取
        if self._is_source_enabled('nav_sources', 'eastmoney_js'):
            try:
                url3 = f'http://fund.eastmoney.com/js/{fund_code}.js'
                response3 = self.session.get(url3, timeout=5)
                if response3.status_code == 200:
                    import re
                    content = response3.text
                    nav_match = re.search(r'DWJZ:"([\d.]+)"', content)
                    date_match = re.search(r'FSRQ:"(\d{4}-\d{2}-\d{2})"', content)
                    
                    if nav_match and date_match:
                        nav = float(nav_match.group(1))
                        if nav > 0:
                            navs.append({
                                'code': fund_code,
                                'nav': nav,
                                'date': date_match.group(1),
                                'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                'source': 'eastmoney_js'
                            })
            except Exception as e:
                print(f"基金详情页获取失败 {fund_code}: {e}")
        
        # 方法4：天天基金网API
        if self._is_source_enabled('nav_sources', '1234567'):
            try:
                url4 = f'http://fundgz.1234567.com.cn/js/{fund_code}.js'
                response4 = self.session.get(url4, timeout=5)
                if response4.status_code == 200:
                    import re
                    content = response4.text
                    # 提取净值
                    nav_match = re.search(r'"dwjz":"([\d.]+)"', content)
                    date_match = re.search(r'"jzrq":"(\d{4}-\d{2}-\d{2})"', content)
                    if nav_match and date_match:
                        nav = float(nav_match.group(1))
                        if nav > 0:
                            navs.append({
                                'code': fund_code,
                                'nav': nav,
                                'date': date_match.group(1),
                                'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                'source': '1234567'
                            })
            except Exception as e:
                print(f"天天基金API获取失败 {fund_code}: {e}")
        
        # 数据验证：选择最新的净值
        if navs:
            # 优先选择日期最新的
            navs.sort(key=lambda x: x['date'], reverse=True)
            return {k: v for k, v in navs[0].items() if k != 'source'}
        
        return None
    
    def get_fund_info(self, fund_code: str) -> Optional[Dict]:
        """
        获取基金完整信息（价格+净值），优先使用套利API，带数据验证
        
        Args:
            fund_code: 基金代码
            
        Returns:
            包含价格和净值的完整信息
        """
        # #region agent log
        import json
        log_data = {
            'sessionId': 'debug-session',
            'runId': 'run1',
            'hypothesisId': 'A',
            'location': 'data_fetcher.py:get_fund_info:entry',
            'message': '开始获取基金信息',
            'data': {'fund_code': fund_code},
            'timestamp': int(time.time() * 1000)
        }
        try:
            with open('c:\\lof1\\.cursor\\debug.log', 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_data, ensure_ascii=False) + '\n')
        except: pass
        # #endregion
        
        # 优先使用套利API（最准确）
        arbitrage_data = self.get_fund_arbitrage_data(fund_code)
        
        # #region agent log
        log_data = {
            'sessionId': 'debug-session',
            'runId': 'run1',
            'hypothesisId': 'A',
            'location': 'data_fetcher.py:get_fund_info:after_arbitrage_api',
            'message': '套利API结果',
            'data': {'fund_code': fund_code, 'has_arbitrage_data': arbitrage_data is not None, 'price': arbitrage_data.get('price', 0) if arbitrage_data else 0, 'nav': arbitrage_data.get('nav', 0) if arbitrage_data else 0},
            'timestamp': int(time.time() * 1000)
        }
        try:
            with open('c:\\lof1\\.cursor\\debug.log', 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_data, ensure_ascii=False) + '\n')
        except: pass
        # #endregion
        
        # 如果套利API返回None，说明基金可能已清盘/退市（套利API只包含正常交易的基金）
        if arbitrage_data is None:
            # #region agent log
            log_data = {
                'sessionId': 'debug-session',
                'runId': 'run1',
                'hypothesisId': 'LIQUIDATED',
                'location': 'data_fetcher.py:get_fund_info:arbitrage_api_none',
                'message': '套利API返回None，基金可能已清盘',
                'data': {'fund_code': fund_code},
                'timestamp': int(time.time() * 1000)
            }
            try:
                with open('c:\\lof1\\.cursor\\debug.log', 'a', encoding='utf-8') as f:
                    f.write(json.dumps(log_data, ensure_ascii=False) + '\n')
            except: pass
            # #endregion
            
            # 尝试获取价格和净值，用于进一步验证
            price_info = self.get_fund_price(fund_code)
            nav_info = self.get_fund_nav(fund_code)
            
            # 如果既没有价格也没有净值，判定为已清盘
            if not price_info and not nav_info:
                # #region agent log
                log_data = {
                    'sessionId': 'debug-session',
                    'runId': 'run1',
                    'hypothesisId': 'LIQUIDATED',
                    'location': 'data_fetcher.py:get_fund_info:no_price_no_nav',
                    'message': '无价格和净值数据，判定为已清盘',
                    'data': {'fund_code': fund_code},
                    'timestamp': int(time.time() * 1000)
                }
                try:
                    with open('c:\\lof1\\.cursor\\debug.log', 'a', encoding='utf-8') as f:
                        f.write(json.dumps(log_data, ensure_ascii=False) + '\n')
                except: pass
                # #endregion
                return None
            
            # 如果同时有价格和净值，检查价差是否异常（超过50%），如果异常则判定为已清盘
            if price_info and nav_info:
                price = price_info.get('price', 0)
                nav = nav_info.get('nav', 0)
                nav_date_str = nav_info.get('date', '')
                
                if price > 0 and nav > 0:
                    diff_pct = abs(price - nav) / nav
                    # 如果价差超过50%，且套利API返回None，判定为已清盘
                    if diff_pct > 0.5:
                        # #region agent log
                        log_data = {
                            'sessionId': 'debug-session',
                            'runId': 'run1',
                            'hypothesisId': 'LIQUIDATED',
                            'location': 'data_fetcher.py:get_fund_info:arbitrage_none_large_diff',
                            'message': '套利API返回None且价差异常，判定为已清盘',
                            'data': {'fund_code': fund_code, 'diff_pct': diff_pct*100, 'price': price, 'nav': nav, 'nav_date': nav_date_str},
                            'timestamp': int(time.time() * 1000)
                        }
                        try:
                            with open('c:\\lof1\\.cursor\\debug.log', 'a', encoding='utf-8') as f:
                                f.write(json.dumps(log_data, ensure_ascii=False) + '\n')
                        except: pass
                        # #endregion
                        return None
            
            # 如果有净值但没有价格，且净值日期过旧（超过30天）或未来日期，判定为已清盘
            if nav_info and not price_info:
                nav_date_str = nav_info.get('date', '')
                if nav_date_str:
                    try:
                        nav_date = datetime.strptime(nav_date_str, '%Y-%m-%d')
                        days_old = (datetime.now() - nav_date).days
                        # 如果净值日期过旧（超过30天）或者是未来日期（数据异常），判定为已清盘
                        if days_old > 30 or days_old < 0:
                            # #region agent log
                            log_data = {
                                'sessionId': 'debug-session',
                                'runId': 'run1',
                                'hypothesisId': 'LIQUIDATED',
                                'location': 'data_fetcher.py:get_fund_info:nav_too_old',
                                'message': '净值日期异常且无价格数据，判定为已清盘',
                                'data': {'fund_code': fund_code, 'nav_date': nav_date_str, 'days_old': days_old},
                                'timestamp': int(time.time() * 1000)
                            }
                            try:
                                with open('c:\\lof1\\.cursor\\debug.log', 'a', encoding='utf-8') as f:
                                    f.write(json.dumps(log_data, ensure_ascii=False) + '\n')
                            except: pass
                            # #endregion
                            return None
                    except:
                        pass
        
        if arbitrage_data:
            # 数据合理性验证
            price = arbitrage_data.get('price', 0)
            nav = arbitrage_data.get('nav', 0)
            
            if price > 0 and nav > 0:
                diff_pct = abs(price - nav) / nav
                if diff_pct > 0.5:
                    print(f"警告：基金 {fund_code} 价差异常 ({diff_pct*100:.2f}%)")
                    arbitrage_data['data_warning'] = True
                    arbitrage_data['price_diff_pct'] = diff_pct * 100
                
                result = {
                    'code': fund_code,
                    'price': price,
                    'nav': nav,
                    'nav_date': arbitrage_data.get('nav_date', ''),
                    'change_pct': arbitrage_data.get('change_pct', 0),
                    'volume': arbitrage_data.get('volume', 0),
                    'amount': arbitrage_data.get('amount', 0),
                    'update_time': arbitrage_data.get('update_time', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                }
                
                # 暂时跳过限购信息获取，避免阻塞批量请求（限购信息可以在后续异步获取）
                # 限购信息获取较慢，会在批量请求时导致超时
                result['purchase_limit'] = {'is_limited': False, 'limit_amount': None, 'limit_desc': '不限购'}
                
                return result
        
        # 备用方案：分别获取价格和净值
        price_info = self.get_fund_price(fund_code)
        nav_info = self.get_fund_nav(fund_code)
        
        # #region agent log
        log_data = {
            'sessionId': 'debug-session',
            'runId': 'run1',
            'hypothesisId': 'A',
            'location': 'data_fetcher.py:get_fund_info:after_fallback',
            'message': '备用方案结果',
            'data': {'fund_code': fund_code, 'has_price_info': price_info is not None, 'has_nav_info': nav_info is not None, 'price': price_info.get('price', 0) if price_info else 0, 'nav': nav_info.get('nav', 0) if nav_info else 0},
            'timestamp': int(time.time() * 1000)
        }
        try:
            with open('c:\\lof1\\.cursor\\debug.log', 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_data, ensure_ascii=False) + '\n')
        except: pass
        # #endregion
        
        if price_info and nav_info:
            # 数据合理性验证
            price = price_info.get('price', 0)
            nav = nav_info.get('nav', 0)
            nav_date_str = nav_info.get('date', '')
            
            # 检查净值日期是否过旧（超过30天没有更新，可能已清盘）或未来日期（数据异常）
            nav_date_too_old = False
            if nav_date_str:
                try:
                    nav_date = datetime.strptime(nav_date_str, '%Y-%m-%d')
                    days_old = (datetime.now() - nav_date).days
                    # 如果净值日期过旧（超过30天）或者是未来日期（数据异常），标记为已清盘
                    if days_old > 30 or days_old < 0:
                        nav_date_too_old = True
                        # #region agent log
                        log_data = {
                            'sessionId': 'debug-session',
                            'runId': 'run1',
                            'hypothesisId': 'LIQUIDATED',
                            'location': 'data_fetcher.py:get_fund_info:nav_date_old',
                            'message': '净值日期异常',
                            'data': {'fund_code': fund_code, 'nav_date': nav_date_str, 'days_old': days_old},
                            'timestamp': int(time.time() * 1000)
                        }
                        try:
                            with open('c:\\lof1\\.cursor\\debug.log', 'a', encoding='utf-8') as f:
                                f.write(json.dumps(log_data, ensure_ascii=False) + '\n')
                        except: pass
                        # #endregion
                except:
                    pass
            
            # 检查价格和净值是否合理（价差不应超过50%）
            if price > 0 and nav > 0:
                diff_pct = abs(price - nav) / nav
                
                # 如果价差超过50%且净值日期过旧，判定为已清盘
                if diff_pct > 0.5 and nav_date_too_old:
                    # #region agent log
                    log_data = {
                        'sessionId': 'debug-session',
                        'runId': 'run1',
                        'hypothesisId': 'LIQUIDATED',
                        'location': 'data_fetcher.py:get_fund_info:large_diff_old_nav',
                        'message': '价差异常且净值日期过旧，判定为已清盘',
                        'data': {'fund_code': fund_code, 'diff_pct': diff_pct*100, 'nav_date': nav_date_str},
                        'timestamp': int(time.time() * 1000)
                    }
                    try:
                        with open('c:\\lof1\\.cursor\\debug.log', 'a', encoding='utf-8') as f:
                            f.write(json.dumps(log_data, ensure_ascii=False) + '\n')
                    except: pass
                    # #endregion
                    return None
                
                if diff_pct > 0.5:  # 价差超过50%可能数据有误
                    print(f"警告：基金 {fund_code} 价差异常 ({diff_pct*100:.2f}%)，价格: {price}, 净值: {nav}")
                    # 仍然返回，但标记为可疑
                    result = {
                        **price_info,
                        'nav': nav_info['nav'],
                        'nav_date': nav_info['date'],
                        'data_warning': True,
                        'price_diff_pct': diff_pct * 100
                    }
                    # 暂时跳过限购信息获取，避免阻塞批量请求（限购信息可以在后续异步获取）
                    result['purchase_limit'] = {'is_limited': False, 'limit_amount': None, 'limit_desc': '不限购'}
                    return result
            
            result = {
                **price_info,
                'nav': nav_info['nav'],
                'nav_date': nav_info['date']
            }
            # 暂时跳过限购信息获取，避免阻塞批量请求（限购信息可以在后续异步获取）
            result['purchase_limit'] = {'is_limited': False, 'limit_amount': None, 'limit_desc': '不限购'}
            return result
        
        # 如果只有价格或只有净值，检查是否可能是已清盘基金
        if price_info and not nav_info:
            # 有价格但没有净值，可能是清盘前的最后价格
            # 检查价格数据是否可信（如果价格数据源数量少，可能不可信）
            price_confidence = price_info.get('price_confidence', 'unknown')
            if price_confidence == 'low':
                # #region agent log
                log_data = {
                    'sessionId': 'debug-session',
                    'runId': 'run1',
                    'hypothesisId': 'LIQUIDATED',
                    'location': 'data_fetcher.py:get_fund_info:price_only_low_confidence',
                    'message': '只有价格数据且置信度低，可能已清盘',
                    'data': {'fund_code': fund_code, 'price': price_info.get('price', 0)},
                    'timestamp': int(time.time() * 1000)
                }
                try:
                    with open('c:\\lof1\\.cursor\\debug.log', 'a', encoding='utf-8') as f:
                        f.write(json.dumps(log_data, ensure_ascii=False) + '\n')
                except: pass
                # #endregion
                return None
        
        if nav_info and not price_info:
            # 有净值但没有价格，检查净值日期
            nav_date_str = nav_info.get('date', '')
            if nav_date_str:
                try:
                    nav_date = datetime.strptime(nav_date_str, '%Y-%m-%d')
                    days_old = (datetime.now() - nav_date).days
                    # 如果净值日期过旧（超过30天）或者是未来日期（数据异常），判定为已清盘
                    if days_old > 30 or days_old < 0:
                        # #region agent log
                        log_data = {
                            'sessionId': 'debug-session',
                            'runId': 'run1',
                            'hypothesisId': 'LIQUIDATED',
                            'location': 'data_fetcher.py:get_fund_info:nav_only_old',
                            'message': '只有净值数据且日期异常，判定为已清盘',
                            'data': {'fund_code': fund_code, 'nav_date': nav_date_str, 'days_old': days_old},
                            'timestamp': int(time.time() * 1000)
                        }
                        try:
                            with open('c:\\lof1\\.cursor\\debug.log', 'a', encoding='utf-8') as f:
                                f.write(json.dumps(log_data, ensure_ascii=False) + '\n')
                        except: pass
                        # #endregion
                        return None
                except:
                    pass
        
        # #region agent log
        log_data = {
            'sessionId': 'debug-session',
            'runId': 'run1',
            'hypothesisId': 'A',
            'location': 'data_fetcher.py:get_fund_info:returning_none',
            'message': 'get_fund_info返回None',
            'data': {'fund_code': fund_code, 'price_info_exists': price_info is not None, 'nav_info_exists': nav_info is not None},
            'timestamp': int(time.time() * 1000)
        }
        try:
            with open('c:\\lof1\\.cursor\\debug.log', 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_data, ensure_ascii=False) + '\n')
        except: pass
        # #endregion
        
        return None
    
    def get_all_funds_arbitrage_data(self, fund_codes: List[str] = None) -> Dict[str, Dict]:
        """
        批量获取所有LOF基金的套利数据（价格+净值+溢价率）
        一次性获取所有基金数据，避免逐个请求
        
        Args:
            fund_codes: 基金代码列表，如果为None则获取所有基金
            
        Returns:
            字典，key为基金代码，value为基金数据
        """
        result = {}
        try:
            url = 'https://zqhdplus.eastmoney.com/api/fundArbitrage/getFundArbitrageList'
            # 尝试不传fundCode，获取所有基金数据
            params = {
                'pageIndex': 1,
                'pageSize': 500,  # 增大pageSize，尝试获取更多数据
            }
            
            # 如果指定了基金代码，只请求一次，然后过滤
            # 否则请求所有数据
            response = self.session.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('Data') and data['Data'].get('List'):
                    fund_set = set(fund_codes) if fund_codes else None
                    
                    for item in data['Data']['List']:
                        fund_code = item.get('FundCode', '')
                        if not fund_code:
                            continue
                            
                        # 如果指定了基金代码列表，只处理列表中的基金
                        if fund_set and fund_code not in fund_set:
                            continue
                            
                        market_price = float(item.get('MarketPrice', 0))
                        net_value = float(item.get('NetValue', 0))
                        nav_date_str = item.get('NetValueDate', '')
                        
                        # 检查净值日期是否过旧（超过30天没有更新，可能已清盘）或未来日期（数据异常）
                        nav_date_too_old = False
                        if nav_date_str:
                            try:
                                nav_date = datetime.strptime(nav_date_str, '%Y-%m-%d')
                                days_old = (datetime.now() - nav_date).days
                                # 如果净值日期过旧（超过30天）或者是未来日期（数据异常），标记为已清盘
                                if days_old > 30 or days_old < 0:
                                    nav_date_too_old = True
                            except:
                                pass
                        
                        # 只处理价格和净值都有效，且净值日期不过旧的基金
                        if market_price > 0 and net_value > 0 and not nav_date_too_old:
                            result[fund_code] = {
                                'code': fund_code,
                                'price': market_price,
                                'nav': net_value,
                                'premium_rate': float(item.get('PremiumRate', 0)),
                                'change_pct': float(item.get('ChangePercent', 0)) / 100,
                                'volume': item.get('Volume', 0),
                                'amount': item.get('Amount', 0),
                                'nav_date': nav_date_str,
                                'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                'source': 'arbitrage_api'
                            }
        except Exception as e:
            print(f"批量套利API获取失败: {e}")
        
        return result
    
    def get_fund_arbitrage_data(self, fund_code: str) -> Optional[Dict]:
        """
        从东方财富套利API获取完整的套利数据（价格+净值+溢价率）
        
        Args:
            fund_code: 基金代码
            
        Returns:
            包含套利相关信息的字典
        """
        try:
            url = 'https://zqhdplus.eastmoney.com/api/fundArbitrage/getFundArbitrageList'
            params = {
                'pageIndex': 1,
                'pageSize': 100,
                'fundCode': fund_code
            }
            response = self.session.get(url, params=params, timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get('Data') and data['Data'].get('List'):
                    for item in data['Data']['List']:
                        if item.get('FundCode') == fund_code:
                            market_price = float(item.get('MarketPrice', 0))
                            net_value = float(item.get('NetValue', 0))
                            premium_rate = float(item.get('PremiumRate', 0))  # 溢价率
                            
                            if market_price > 0 and net_value > 0:
                                return {
                                    'code': fund_code,
                                    'price': market_price,
                                    'nav': net_value,
                                    'premium_rate': premium_rate,
                                    'change_pct': float(item.get('ChangePercent', 0)) / 100,
                                    'volume': item.get('Volume', 0),
                                    'amount': item.get('Amount', 0),
                                    'nav_date': item.get('NetValueDate', ''),
                                    'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                    'source': 'arbitrage_api'
                                }
        except Exception as e:
            print(f"套利API获取失败 {fund_code}: {e}")
        
        return None
    
    def get_fund_purchase_limit(self, fund_code: str) -> Optional[Dict]:
        """
        获取基金申购限购信息
        
        Args:
            fund_code: 基金代码
            
        Returns:
            包含限购信息的字典: {'is_limited': bool, 'limit_amount': float, 'limit_unit': str, 'limit_desc': str}
        """
        # #region agent log
        log_data = {
            'sessionId': 'debug-session',
            'runId': 'run1',
            'hypothesisId': 'E',
            'location': 'data_fetcher.py:get_fund_purchase_limit:entry',
            'message': '开始获取限购信息',
            'data': {'fund_code': fund_code},
            'timestamp': int(time.time() * 1000)
        }
        try:
            with open('c:\\lof1\\.cursor\\debug.log', 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_data, ensure_ascii=False) + '\n')
        except: pass
        # #endregion
        
        try:
            # 方法1：尝试使用akshare获取基金限购信息
            if AKSHARE_AVAILABLE:
                try:
                    # #region agent log
                    log_data = {
                        'sessionId': 'debug-session',
                        'runId': 'run1',
                        'hypothesisId': 'F',
                        'location': 'data_fetcher.py:get_fund_purchase_limit:akshare_try',
                        'message': '尝试使用akshare获取限购信息',
                        'data': {'fund_code': fund_code},
                        'timestamp': int(time.time() * 1000)
                    }
                    try:
                        with open('c:\\lof1\\.cursor\\debug.log', 'a', encoding='utf-8') as f:
                            f.write(json.dumps(log_data, ensure_ascii=False) + '\n')
                    except: pass
                    # #endregion
                    
                    # 尝试使用akshare的基金基本信息接口
                    # 注意：基金代码可能需要添加后缀，如 'of' (场外) 或 'sh'/'sz' (场内)
                    fund_code_full = f"{fund_code}.OF"  # 场外基金
                    
                    # 尝试使用akshare的基金申购赎回信息（包含限购信息）
                    try:
                        # #region agent log
                        log_data = {
                            'sessionId': 'debug-session',
                            'runId': 'run1',
                            'hypothesisId': 'F',
                            'location': 'data_fetcher.py:get_fund_purchase_limit:akshare_purchase_start',
                            'message': '开始使用akshare获取申购信息',
                            'data': {'fund_code': fund_code},
                            'timestamp': int(time.time() * 1000)
                        }
                        try:
                            with open('c:\\lof1\\.cursor\\debug.log', 'a', encoding='utf-8') as f:
                                f.write(json.dumps(log_data, ensure_ascii=False) + '\n')
                        except: pass
                        # #endregion
                        
                        # fund_purchase_em()不接受参数，返回所有基金的申购状态
                        # 使用缓存，避免重复下载（缓存5分钟）
                        import time as time_module
                        current_time = time_module.time()
                        if (self._akshare_purchase_cache is None or 
                            self._akshare_purchase_cache_time is None or 
                            current_time - self._akshare_purchase_cache_time > 300):  # 5分钟缓存
                            # #region agent log
                            log_data = {
                                'sessionId': 'debug-session',
                                'runId': 'run1',
                                'hypothesisId': 'F',
                                'location': 'data_fetcher.py:get_fund_purchase_limit:akshare_cache_miss',
                                'message': 'akshare缓存未命中，开始下载数据',
                                'data': {'fund_code': fund_code, 'cache_exists': self._akshare_purchase_cache is not None},
                                'timestamp': int(time.time() * 1000)
                            }
                            try:
                                with open('c:\\lof1\\.cursor\\debug.log', 'a', encoding='utf-8') as f:
                                    f.write(json.dumps(log_data, ensure_ascii=False) + '\n')
                            except: pass
                            # #endregion
                            
                            try:
                                print(f"正在从akshare下载基金申购数据...")
                                self._akshare_purchase_cache = ak.fund_purchase_em()
                                self._akshare_purchase_cache_time = current_time
                                
                                # #region agent log
                                log_data = {
                                    'sessionId': 'debug-session',
                                    'runId': 'run1',
                                    'hypothesisId': 'F',
                                    'location': 'data_fetcher.py:get_fund_purchase_limit:akshare_cache_loaded',
                                    'message': 'akshare数据下载完成',
                                    'data': {'fund_code': fund_code, 'rows': len(self._akshare_purchase_cache) if self._akshare_purchase_cache is not None else 0, 'columns': list(self._akshare_purchase_cache.columns) if self._akshare_purchase_cache is not None and hasattr(self._akshare_purchase_cache, 'columns') else []},
                                    'timestamp': int(time.time() * 1000)
                                }
                                try:
                                    with open('c:\\lof1\\.cursor\\debug.log', 'a', encoding='utf-8') as f:
                                        f.write(json.dumps(log_data, ensure_ascii=False) + '\n')
                                except: pass
                                # #endregion
                                print(f"akshare数据下载完成，共 {len(self._akshare_purchase_cache)} 条记录")
                            except Exception as e:
                                # #region agent log
                                log_data = {
                                    'sessionId': 'debug-session',
                                    'runId': 'run1',
                                    'hypothesisId': 'F',
                                    'location': 'data_fetcher.py:get_fund_purchase_limit:akshare_download_error',
                                    'message': 'akshare数据下载失败',
                                    'data': {'fund_code': fund_code, 'error': str(e)[:500], 'error_type': type(e).__name__},
                                    'timestamp': int(time.time() * 1000)
                                }
                                try:
                                    with open('c:\\lof1\\.cursor\\debug.log', 'a', encoding='utf-8') as f:
                                        f.write(json.dumps(log_data, ensure_ascii=False) + '\n')
                                except: pass
                                # #endregion
                                print(f"akshare数据下载失败: {e}")
                                # 如果下载失败，缓存设为空，跳过akshare方法
                                self._akshare_purchase_cache = None
                                raise  # 继续使用其他方法获取限购信息
                        else:
                            # #region agent log
                            log_data = {
                                'sessionId': 'debug-session',
                                'runId': 'run1',
                                'hypothesisId': 'F',
                                'location': 'data_fetcher.py:get_fund_purchase_limit:akshare_cache_hit',
                                'message': 'akshare使用缓存数据',
                                'data': {'fund_code': fund_code, 'cache_age_seconds': int(current_time - self._akshare_purchase_cache_time)},
                                'timestamp': int(time.time() * 1000)
                            }
                            try:
                                with open('c:\\lof1\\.cursor\\debug.log', 'a', encoding='utf-8') as f:
                                    f.write(json.dumps(log_data, ensure_ascii=False) + '\n')
                            except: pass
                            # #endregion
                        
                        all_funds_df = self._akshare_purchase_cache
                        if all_funds_df is not None and not all_funds_df.empty:
                            # 从所有基金中筛选出指定基金
                            # 基金代码通常在第二列（索引1）
                            cols = list(all_funds_df.columns)
                            fund_code_col = cols[1]  # 基金代码列
                            fund_record = all_funds_df[all_funds_df[fund_code_col].astype(str).str.contains(fund_code)]
                            
                            if not fund_record.empty:
                                fund_row = fund_record.iloc[0]
                                
                                # #region agent log
                                log_data = {
                                    'sessionId': 'debug-session',
                                    'runId': 'run1',
                                    'hypothesisId': 'F',
                                    'location': 'data_fetcher.py:get_fund_purchase_limit:akshare_purchase_success',
                                    'message': 'akshare申购信息获取到数据',
                                    'data': {
                                        'fund_code': fund_code, 
                                        'columns': cols,
                                        'found': True,
                                        'fund_row': fund_row.to_dict()
                                    },
                                    'timestamp': int(time.time() * 1000)
                                }
                                try:
                                    with open('c:\\lof1\\.cursor\\debug.log', 'a', encoding='utf-8') as f:
                                        f.write(json.dumps(log_data, ensure_ascii=False) + '\n')
                                except: pass
                                # #endregion
                                
                                # 查找限购相关列（akshare返回的列名可能是中文）
                                # 通常"单日累计限额（元）"在倒数第二列
                                cols = list(fund_record.columns)
                                
                                # 方法1：直接查找"单日累计限额"相关列
                                limit_keywords = ['限额', '限购', '单日累计', '单笔限额', '最大申购', 'purchase_limit', 'limit', 'maximum']
                                for col in cols:
                                    col_str = str(col)
                                    # 检查列名中是否包含限购关键词
                                    if any(keyword in col_str for keyword in limit_keywords):
                                        limit_value = fund_row[col]
                                        if limit_value is not None and str(limit_value) != 'nan' and str(limit_value) != '' and str(limit_value) != 'None':
                                            try:
                                                limit_amount = float(limit_value)
                                                if limit_amount > 0:
                                                    # #region agent log
                                                    log_data = {
                                                        'sessionId': 'debug-session',
                                                        'runId': 'run1',
                                                        'hypothesisId': 'F',
                                                        'location': 'data_fetcher.py:get_fund_purchase_limit:akshare_found_limit',
                                                        'message': 'akshare找到限购字段',
                                                        'data': {'fund_code': fund_code, 'column': col, 'value': limit_amount},
                                                        'timestamp': int(time.time() * 1000)
                                                    }
                                                    try:
                                                        with open('c:\\lof1\\.cursor\\debug.log', 'a', encoding='utf-8') as f:
                                                            f.write(json.dumps(log_data, ensure_ascii=False) + '\n')
                                                    except: pass
                                                    # #endregion
                                                    
                                                    return {
                                                        'is_limited': True,
                                                        'limit_amount': limit_amount,
                                                        'limit_unit': '元',
                                                        'limit_desc': f'限购 {limit_amount:.0f} 元' if limit_amount >= 1 else f'限购 {limit_amount:.2f} 元'
                                                    }
                                            except (ValueError, TypeError):
                                                pass
                                
                                # 方法2：如果列名无法识别，尝试倒数第二列（通常是"单日累计限额（元）"）
                                if len(cols) >= 2:
                                    limit_col = cols[-2]  # 倒数第二列
                                    try:
                                        limit_value = fund_row[limit_col]
                                        if limit_value is not None:
                                            limit_amount = float(limit_value)
                                            if limit_amount > 0:
                                                # #region agent log
                                                log_data = {
                                                    'sessionId': 'debug-session',
                                                    'runId': 'run1',
                                                    'hypothesisId': 'F',
                                                    'location': 'data_fetcher.py:get_fund_purchase_limit:akshare_found_limit_col',
                                                    'message': 'akshare从倒数第二列找到限购信息',
                                                    'data': {'fund_code': fund_code, 'column': limit_col, 'value': limit_amount},
                                                    'timestamp': int(time.time() * 1000)
                                                }
                                                try:
                                                    with open('c:\\lof1\\.cursor\\debug.log', 'a', encoding='utf-8') as f:
                                                        f.write(json.dumps(log_data, ensure_ascii=False) + '\n')
                                                except: pass
                                                # #endregion
                                                
                                                return {
                                                    'is_limited': True,
                                                    'limit_amount': limit_amount,
                                                    'limit_unit': '元',
                                                    'limit_desc': f'限购 {limit_amount:.0f} 元' if limit_amount >= 1 else f'限购 {limit_amount:.2f} 元'
                                                }
                                    except (ValueError, TypeError, KeyError):
                                        pass
                                
                                # 方法3：遍历所有列的值，查找包含数字的限购信息
                                for col in cols:
                                    cell_value = fund_row[col]
                                    if cell_value is not None:
                                        try:
                                            limit_amount = float(cell_value)
                                            # 如果金额在合理范围内（1到1000万之间），可能是限购金额
                                            if 1 <= limit_amount <= 10000000:
                                                # 检查列名是否与限购相关
                                                col_str = str(col).lower()
                                                if any(keyword in col_str for keyword in ['限额', '限购', '额', 'limit']):
                                                    # #region agent log
                                                    log_data = {
                                                        'sessionId': 'debug-session',
                                                        'runId': 'run1',
                                                        'hypothesisId': 'F',
                                                        'location': 'data_fetcher.py:get_fund_purchase_limit:akshare_inferred',
                                                        'message': 'akshare推断限购信息',
                                                        'data': {'fund_code': fund_code, 'column': col, 'value': limit_amount},
                                                        'timestamp': int(time.time() * 1000)
                                                    }
                                                    try:
                                                        with open('c:\\lof1\\.cursor\\debug.log', 'a', encoding='utf-8') as f:
                                                            f.write(json.dumps(log_data, ensure_ascii=False) + '\n')
                                                    except: pass
                                                    # #endregion
                                                    
                                                    return {
                                                        'is_limited': True,
                                                        'limit_amount': limit_amount,
                                                        'limit_unit': '元',
                                                        'limit_desc': f'限购 {limit_amount:.0f} 元' if limit_amount >= 1 else f'限购 {limit_amount:.2f} 元'
                                                    }
                                        except (ValueError, TypeError):
                                            pass
                            else:
                                # #region agent log
                                log_data = {
                                    'sessionId': 'debug-session',
                                    'runId': 'run1',
                                    'hypothesisId': 'F',
                                    'location': 'data_fetcher.py:get_fund_purchase_limit:akshare_not_found',
                                    'message': 'akshare未找到指定基金',
                                    'data': {'fund_code': fund_code, 'total_funds': len(all_funds_df)},
                                    'timestamp': int(time.time() * 1000)
                                }
                                try:
                                    with open('c:\\lof1\\.cursor\\debug.log', 'a', encoding='utf-8') as f:
                                        f.write(json.dumps(log_data, ensure_ascii=False) + '\n')
                                except: pass
                                # #endregion
                    except Exception as e:
                        # #region agent log
                        log_data = {
                            'sessionId': 'debug-session',
                            'runId': 'run1',
                            'hypothesisId': 'F',
                            'location': 'data_fetcher.py:get_fund_purchase_limit:akshare_purchase_error',
                            'message': 'akshare申购信息获取失败',
                            'data': {'fund_code': fund_code, 'error': str(e), 'error_type': type(e).__name__},
                            'timestamp': int(time.time() * 1000)
                        }
                        try:
                            with open('c:\\lof1\\.cursor\\debug.log', 'a', encoding='utf-8') as f:
                                f.write(json.dumps(log_data, ensure_ascii=False) + '\n')
                        except: pass
                        # #endregion
                        pass
                except Exception as e:
                    print(f"akshare获取限购信息失败 {fund_code}: {e}")
            
            # 方法2：尝试使用baostock获取（但baostock主要针对股票，可能不支持基金）
            # 暂时跳过，因为baostock主要用于股票数据
            
            # 方法3：从基金基本信息API获取（原有方法）
            url = 'http://api.fund.eastmoney.com/f10/F10FundBasicInfo.aspx'
            params = {
                'fundCode': fund_code,
                'callback': 'jQuery'
            }
            response = self.session.get(url, params=params, timeout=5)
            if response.status_code == 200:
                import re
                content = response.text
                json_match = re.search(r'jQuery\((.+)\)', content)
                if json_match:
                    data = json.loads(json_match.group(1))
                    
                    # #region agent log
                    log_data = {
                        'sessionId': 'debug-session',
                        'runId': 'run1',
                        'hypothesisId': 'E',
                        'location': 'data_fetcher.py:get_fund_purchase_limit:api_response',
                        'message': 'API响应数据',
                        'data': {'fund_code': fund_code, 'data_keys': list(data.keys()) if isinstance(data, dict) else 'not_dict', 'has_data': 'Data' in data if isinstance(data, dict) else False},
                        'timestamp': int(time.time() * 1000)
                    }
                    try:
                        with open('c:\\lof1\\.cursor\\debug.log', 'a', encoding='utf-8') as f:
                            f.write(json.dumps(log_data, ensure_ascii=False) + '\n')
                    except: pass
                    # #endregion
                    
                    if data.get('Data'):
                        data_obj = data['Data']
                        # 尝试多种可能的字段名
                        limit_fields = ['PURCHASELIMIT', 'PurchaseLimit', 'MinPurchaseAmount', 'MaxPurchaseAmount', 
                                       'PURCHASE_LIMIT', 'SUBSCRIBE_LIMIT', '申购限额', '限购', 'LimitAmount']
                        
                        for field in limit_fields:
                            limit_value = data_obj.get(field)
                            if limit_value is not None and limit_value != '':
                                # #region agent log
                                log_data = {
                                    'sessionId': 'debug-session',
                                    'runId': 'run1',
                                    'hypothesisId': 'E',
                                    'location': 'data_fetcher.py:get_fund_purchase_limit:found_field',
                                    'message': '找到限购字段',
                                    'data': {'fund_code': fund_code, 'field': field, 'value': limit_value},
                                    'timestamp': int(time.time() * 1000)
                                }
                                try:
                                    with open('c:\\lof1\\.cursor\\debug.log', 'a', encoding='utf-8') as f:
                                        f.write(json.dumps(log_data, ensure_ascii=False) + '\n')
                                except: pass
                                # #endregion
                                return self._parse_purchase_limit(limit_value, field)
                        
                        # 如果没有找到，记录所有可用字段
                        # #region agent log
                        log_data = {
                            'sessionId': 'debug-session',
                            'runId': 'run1',
                            'hypothesisId': 'E',
                            'location': 'data_fetcher.py:get_fund_purchase_limit:no_limit_field',
                            'message': '未找到限购字段，记录所有字段',
                            'data': {'fund_code': fund_code, 'all_fields': list(data_obj.keys())},
                            'timestamp': int(time.time() * 1000)
                        }
                        try:
                            with open('c:\\lof1\\.cursor\\debug.log', 'a', encoding='utf-8') as f:
                                f.write(json.dumps(log_data, ensure_ascii=False) + '\n')
                        except: pass
                        # #endregion
            
            # 方法4：尝试从基金详情页面获取
            url2 = f'http://fund.eastmoney.com/{fund_code}.html'
            response2 = self.session.get(url2, timeout=5)
            if response2.status_code == 200:
                import re
                content = response2.text
                # 尝试提取限购信息（可能出现在页面中）
                limit_patterns = [
                    r'申购限额[：:]\s*([0-9,.]+)\s*([万元|元|份]*)',
                    r'限购[：:]\s*([0-9,.]+)\s*([万元|元|份]*)',
                    r'单笔申购限额[：:]\s*([0-9,.]+)\s*([万元|元|份]*)',
                    r'最大申购金额[：:]\s*([0-9,.]+)\s*([万元|元|份]*)',
                ]
                
                for pattern in limit_patterns:
                    match = re.search(pattern, content)
                    if match:
                        amount_str = match.group(1).replace(',', '').replace('，', '')
                        unit = match.group(2) if len(match.groups()) > 1 else '元'
                        try:
                            amount = float(amount_str)
                            # #region agent log
                            log_data = {
                                'sessionId': 'debug-session',
                                'runId': 'run1',
                                'hypothesisId': 'E',
                                'location': 'data_fetcher.py:get_fund_purchase_limit:found_in_page',
                                'message': '从页面提取限购信息',
                                'data': {'fund_code': fund_code, 'amount': amount, 'unit': unit, 'pattern': pattern},
                                'timestamp': int(time.time() * 1000)
                            }
                            try:
                                with open('c:\\lof1\\.cursor\\debug.log', 'a', encoding='utf-8') as f:
                                    f.write(json.dumps(log_data, ensure_ascii=False) + '\n')
                            except: pass
                            # #endregion
                            return self._parse_purchase_limit_from_text(amount, unit)
                        except ValueError:
                            continue
            
            # 方法5：尝试基金申购/赎回费率API
            url3 = 'http://api.fund.eastmoney.com/f10/FundTradeInfo.aspx'
            params3 = {
                'fundCode': fund_code,
                'callback': 'jQuery'
            }
            response3 = self.session.get(url3, params=params3, timeout=5)
            if response3.status_code == 200:
                import re
                content = response3.text
                json_match = re.search(r'jQuery\((.+)\)', content)
                if json_match:
                    try:
                        data = json.loads(json_match.group(1))
                        # 记录响应结构
                        # #region agent log
                        log_data = {
                            'sessionId': 'debug-session',
                            'runId': 'run1',
                            'hypothesisId': 'E',
                            'location': 'data_fetcher.py:get_fund_purchase_limit:trade_info',
                            'message': '申购赎回费率API响应',
                            'data': {'fund_code': fund_code, 'data_keys': list(data.keys()) if isinstance(data, dict) else 'not_dict'},
                            'timestamp': int(time.time() * 1000)
                        }
                        try:
                            with open('c:\\lof1\\.cursor\\debug.log', 'a', encoding='utf-8') as f:
                                f.write(json.dumps(log_data, ensure_ascii=False) + '\n')
                        except: pass
                        # #endregion
                    except:
                        pass
                        
        except Exception as e:
            # #region agent log
            log_data = {
                'sessionId': 'debug-session',
                'runId': 'run1',
                'hypothesisId': 'E',
                'location': 'data_fetcher.py:get_fund_purchase_limit:error',
                'message': '获取限购信息失败',
                'data': {'fund_code': fund_code, 'error': str(e)},
                'timestamp': int(time.time() * 1000)
            }
            try:
                with open('c:\\lof1\\.cursor\\debug.log', 'a', encoding='utf-8') as f:
                    f.write(json.dumps(log_data, ensure_ascii=False) + '\n')
            except: pass
            # #endregion
            print(f"获取限购信息失败 {fund_code}: {e}")
        
        # 默认返回不限购
        return {
            'is_limited': False,
            'limit_amount': None,
            'limit_unit': None,
            'limit_desc': '不限购'
        }
    
    def _parse_purchase_limit(self, limit_value, field_name: str) -> Dict:
        """解析限购信息"""
        try:
            if limit_value == 0 or limit_value == '0' or limit_value == '':
                return {
                    'is_limited': False,
                    'limit_amount': None,
                    'limit_unit': None,
                    'limit_desc': '不限购'
                }
            
            # 尝试转换为数值
            if isinstance(limit_value, (int, float)):
                amount = float(limit_value)
                if amount > 0:
                    return {
                        'is_limited': True,
                        'limit_amount': amount,
                        'limit_unit': '元',
                        'limit_desc': f'限购 {amount:,.0f} 元'
                    }
            
            # 如果是字符串，尝试解析
            if isinstance(limit_value, str):
                return self._parse_purchase_limit_from_text(limit_value, '元')
                
        except Exception as e:
            print(f"解析限购信息失败: {e}")
        
        return {
            'is_limited': False,
            'limit_amount': None,
            'limit_unit': None,
            'limit_desc': '不限购'
        }
    
    def _parse_purchase_limit_from_text(self, amount, unit: str) -> Dict:
        """从文本解析限购信息"""
        try:
            # 如果amount是字符串，先尝试转换
            if isinstance(amount, str):
                amount_str = amount.replace(',', '').replace('，', '').strip()
                try:
                    amount = float(amount_str)
                except ValueError:
                    return {
                        'is_limited': False,
                        'limit_amount': None,
                        'limit_unit': None,
                        'limit_desc': '不限购'
                    }
            
            # 转换为浮点数
            amount = float(amount)
            
            # 单位转换
            multiplier = 1
            if '万' in unit or '萬' in unit:
                multiplier = 10000
            elif '千' in unit:
                multiplier = 1000
            
            final_amount = amount * multiplier
            
            if final_amount > 0:
                if final_amount >= 10000:
                    desc = f'限购 {final_amount/10000:.2f} 万元'
                else:
                    desc = f'限购 {final_amount:.2f} 元'
                return {
                    'is_limited': True,
                    'limit_amount': final_amount,
                    'limit_unit': '元',
                    'limit_desc': desc
                }
        except Exception as e:
            print(f"解析限购文本失败: {e}")
        
        return {
            'is_limited': False,
            'limit_amount': None,
            'limit_unit': None,
            'limit_desc': '不限购'
        }


class MockDataFetcher:
    """模拟数据获取器（用于测试）"""
    
    def __init__(self):
        import random
        self.random = random
    
    def get_fund_price(self, fund_code: str) -> Optional[Dict]:
        """模拟价格数据"""
        base_price = 1.0 + self.random.uniform(-0.2, 0.2)
        return {
            'code': fund_code,
            'price': round(base_price, 3),
            'change_pct': round(self.random.uniform(-0.05, 0.05), 4),
            'volume': self.random.randint(1000000, 10000000),
            'amount': self.random.randint(10000000, 100000000),
            'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    
    def get_fund_nav(self, fund_code: str) -> Optional[Dict]:
        """模拟净值数据"""
        base_nav = 1.0 + self.random.uniform(-0.2, 0.2)
        return {
            'code': fund_code,
            'nav': round(base_nav, 3),
            'date': datetime.now().strftime('%Y-%m-%d'),
            'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    
    def get_fund_info(self, fund_code: str) -> Optional[Dict]:
        price_info = self.get_fund_price(fund_code)
        nav_info = self.get_fund_nav(fund_code)
        
        if price_info and nav_info:
            return {
                **price_info,
                'nav': nav_info['nav'],
                'nav_date': nav_info['date']
            }
        return None
