# -*- coding: utf-8 -*-
"""
LOF基金套利工具 - Web界面
"""

from flask import Flask, render_template, jsonify, request, session
from functools import wraps
from data_fetcher import LOFDataFetcher, MockDataFetcher
from arbitrage_calculator import ArbitrageCalculator
from arbitrage_recorder import ArbitrageRecorder
from user_manager import UserManager
from notification_manager import NotificationManager, NotificationType
from data_source_config_manager import DataSourceConfigManager
from config import LOF_FUNDS, DATA_SOURCE, TRADE_FEES, ARBITRAGE_THRESHOLD
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import time
import secrets
import os

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False
app.config['SECRET_KEY'] = secrets.token_hex(16)  # 用于session加密

# 全局变量
use_mock_data = False
data_fetcher = None
calculator = None
arbitrage_recorder = ArbitrageRecorder()
user_manager = UserManager()
notification_manager = NotificationManager()
data_source_config_manager = DataSourceConfigManager()


# 登录验证装饰器
def login_required(f):
    """需要登录的装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session or not session.get('logged_in'):
            return jsonify({
                'success': False,
                'message': '请先登录',
                'requires_login': True
            }), 401
        return f(*args, **kwargs)
    return decorated_function


# 管理员权限装饰器
def admin_required(f):
    """需要管理员权限的装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session or not session.get('logged_in'):
            return jsonify({
                'success': False,
                'message': '请先登录',
                'requires_login': True
            }), 401
        
        username = session.get('username')
        user = user_manager.get_user(username)
        if not user or user.get('role') != 'admin':
            return jsonify({
                'success': False,
                'message': '需要管理员权限',
                'requires_admin': True
            }), 403
        
        return f(*args, **kwargs)
    return decorated_function


def init_fetcher(mock=False):
    """初始化数据获取器"""
    global data_fetcher, calculator, use_mock_data, DATA_SOURCE
    use_mock_data = mock
    if mock:
        data_fetcher = MockDataFetcher()
    else:
        # 合并保存的配置和默认配置
        merged_config = data_source_config_manager.merge_with_default(DATA_SOURCE)
        DATA_SOURCE.update(merged_config)
        
        # 从配置获取Tushare token（优先环境变量，其次UI配置）
        tushare_token = None
        # 1. 优先从环境变量获取
        env_token = os.getenv('TUSHARE_TOKEN')
        if env_token:
            tushare_token = env_token
        # 2. 从配置管理器获取
        elif data_source_config_manager.get_tushare_token():
            tushare_token = data_source_config_manager.get_tushare_token()
        # 3. 从DATA_SOURCE获取（向后兼容）
        elif DATA_SOURCE.get('tushare_token'):
            tushare_token = DATA_SOURCE.get('tushare_token')
        
        data_fetcher = LOFDataFetcher(tushare_token=tushare_token)
        data_fetcher.data_source_config = DATA_SOURCE
    calculator = ArbitrageCalculator()


# 初始化
init_fetcher()

# 启动时自动发现所有LOF基金
def auto_discover_funds():
    """启动时自动发现所有LOF基金"""
    global LOF_FUNDS
    
    # #region agent log
    import json
    log_data = {
        'sessionId': 'debug-session',
        'runId': 'run1',
        'hypothesisId': 'A',
        'location': 'app.py:auto_discover_funds:entry',
        'message': '开始自动发现LOF基金',
        'data': {'initial_funds_count': len(LOF_FUNDS)},
        'timestamp': int(time.time() * 1000)
    }
    try:
        with open('c:\\lof1\\.cursor\\debug.log', 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_data, ensure_ascii=False) + '\n')
    except: pass
    # #endregion
    
    if not use_mock_data:
        try:
            funds_list = data_fetcher.get_lof_funds_list()
            if funds_list:
                funds_dict = {fund['code']: fund['name'] for fund in funds_list}
                LOF_FUNDS.update(funds_dict)
                
                # #region agent log
                log_data = {
                    'sessionId': 'debug-session',
                    'runId': 'run1',
                    'hypothesisId': 'A',
                    'location': 'app.py:auto_discover_funds:success',
                    'message': '自动发现LOF基金完成',
                    'data': {'discovered_count': len(funds_dict), 'total_count': len(LOF_FUNDS)},
                    'timestamp': int(time.time() * 1000)
                }
                try:
                    with open('c:\\lof1\\.cursor\\debug.log', 'a', encoding='utf-8') as f:
                        f.write(json.dumps(log_data, ensure_ascii=False) + '\n')
                except: pass
                # #endregion
                
                print(f"自动发现 {len(funds_dict)} 只LOF基金，总计 {len(LOF_FUNDS)} 只")
        except Exception as e:
            # #region agent log
            log_data = {
                'sessionId': 'debug-session',
                'runId': 'run1',
                'hypothesisId': 'A',
                'location': 'app.py:auto_discover_funds:error',
                'message': '自动发现LOF基金失败',
                'data': {'error': str(e)},
                'timestamp': int(time.time() * 1000)
            }
            try:
                with open('c:\\lof1\\.cursor\\debug.log', 'a', encoding='utf-8') as f:
                    f.write(json.dumps(log_data, ensure_ascii=False) + '\n')
            except: pass
            # #endregion
            print(f"自动发现LOF基金失败: {e}")

# 启动时自动发现
auto_discover_funds()


@app.route('/')
def index():
    """主页"""
    return render_template('index.html')


@app.route('/api/funds')
def get_funds():
    """获取基金列表"""
    # #region agent log
    import json
    log_data = {
        'sessionId': 'debug-session',
        'runId': 'run1',
        'hypothesisId': 'A',
        'location': 'app.py:get_funds',
        'message': 'API返回基金列表',
        'data': {'funds_count': len(LOF_FUNDS), 'funds_keys': list(LOF_FUNDS.keys())[:5]},
        'timestamp': int(time.time() * 1000)
    }
    try:
        with open('c:\\lof1\\.cursor\\debug.log', 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_data, ensure_ascii=False) + '\n')
    except: pass
    # #endregion
    
    return jsonify({
        'funds': LOF_FUNDS,
        'success': True
    })


@app.route('/api/funds/discover', methods=['GET'])
def discover_funds():
    """动态发现LOF基金列表"""
    try:
        if use_mock_data:
            return jsonify({
                'success': True,
                'message': '模拟数据模式不支持动态发现',
                'funds': {}
            })
        
        funds_list = data_fetcher.get_lof_funds_list()
        if funds_list:
            funds_dict = {fund['code']: fund['name'] for fund in funds_list}
            # 更新全局基金列表（合并，不覆盖）
            global LOF_FUNDS
            LOF_FUNDS.update(funds_dict)
            
            return jsonify({
                'success': True,
                'funds': funds_dict,
                'count': len(funds_dict),
                'total_count': len(LOF_FUNDS)
            })
        else:
            return jsonify({
                'success': True,
                'message': '未发现新的LOF基金',
                'funds': {},
                'count': 0
            })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@app.route('/api/fund/<fund_code>')
def get_fund_info(fund_code):
    """获取单个基金信息"""
    try:
        fund_info = data_fetcher.get_fund_info(fund_code)
        if not fund_info:
            return jsonify({
                'success': False,
                'message': f'无法获取基金 {fund_code} 的数据'
            }), 404
        
        result = calculator.calculate_arbitrage(fund_info)
        if result:
            result['fund_name'] = LOF_FUNDS.get(fund_code, '')
            return jsonify({
                'success': True,
                'data': result
            })
        else:
            return jsonify({
                'success': False,
                'message': '无法计算套利机会'
            }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@app.route('/api/funds/batch', methods=['POST'])
def get_funds_batch():
    """批量获取基金信息"""
    # #region agent log
    import json
    log_data = {
        'sessionId': 'debug-session',
        'runId': 'run1',
        'hypothesisId': 'C',
        'location': 'app.py:get_funds_batch:entry',
        'message': '开始批量获取基金信息',
        'data': {},
        'timestamp': int(time.time() * 1000)
    }
    try:
        with open('c:\\lof1\\.cursor\\debug.log', 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_data, ensure_ascii=False) + '\n')
    except: pass
    # #endregion
    
    try:
        data = request.get_json()
        fund_codes = data.get('codes', list(LOF_FUNDS.keys()))
        
        # #region agent log
        log_data = {
            'sessionId': 'debug-session',
            'runId': 'run1',
            'hypothesisId': 'C',
            'location': 'app.py:get_funds_batch:received',
            'message': '收到批量请求',
            'data': {'fund_codes_count': len(fund_codes), 'sample_codes': fund_codes[:5]},
            'timestamp': int(time.time() * 1000)
        }
        try:
            with open('c:\\lof1\\.cursor\\debug.log', 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_data, ensure_ascii=False) + '\n')
        except: pass
        # #endregion
        
        # 优化方案2：并行请求处理（使用多线程，显著提升速度）
        results = []
        processed = 0
        errors = 0
        
        def process_single_fund(fund_code: str):
            """处理单个基金的函数（用于并行执行）"""
            try:
                fund_info = data_fetcher.get_fund_info(fund_code)
                if fund_info:
                    result = calculator.calculate_arbitrage(fund_info)
                    if result:
                        # 暂时不获取限购信息，避免批量请求超时
                        result['purchase_limit'] = {'is_limited': False, 'limit_amount': None, 'limit_desc': '不限购'}
                        
                        # 获取基金名称，确保是中文
                        fund_name = LOF_FUNDS.get(fund_code, '')
                        is_chinese = fund_name and any('\u4e00' <= char <= '\u9fff' for char in fund_name)
                        
                        # 如果名称不是中文，尝试获取中文名称（但不在并行中获取，避免过多请求）
                        # 可以后续异步更新
                        result['fund_name'] = fund_name if fund_name else fund_code
                        return {'success': True, 'result': result, 'fund_code': fund_code}
                return {'success': False, 'fund_code': fund_code, 'reason': 'no_data'}
            except Exception as e:
                return {'success': False, 'fund_code': fund_code, 'reason': str(e)}
        
        # 使用线程池并行处理（并发数：30，平衡速度和API限制）
        max_workers = 30
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交所有任务
            future_to_fund = {executor.submit(process_single_fund, fund_code): fund_code 
                            for fund_code in fund_codes}
            
            # 收集结果
            for future in as_completed(future_to_fund):
                fund_code = future_to_fund[future]
                try:
                    result_data = future.result()
                    if result_data['success']:
                        result = result_data['result']
                        results.append(result)
                        processed += 1
                        
                        # 检测套利机会并发送通知（仅对已登录用户）
                        if result.get('has_opportunity') and 'logged_in' in session and session.get('logged_in'):
                            username = session.get('username')
                            if username:
                                try:
                                    fund_code = result.get('fund_code', '')
                                    fund_name = result.get('fund_name', fund_code)
                                    arbitrage_type = result.get('arbitrage_type', '')
                                    profit_rate = result.get('profit_rate', 0)
                                    
                                    # 检查是否已经通知过（避免重复通知）
                                    # 可以通过检查最近的通知来判断
                                    recent_notifications = notification_manager.get_notifications(
                                        username, unread_only=True, limit=10
                                    )
                                    already_notified = any(
                                        n.get('type') == NotificationType.ARBITRAGE_OPPORTUNITY and
                                        n.get('data', {}).get('fund_code') == fund_code and
                                        # 检查是否是最近5分钟内的通知
                                        (datetime.now() - datetime.fromisoformat(n.get('created_at', ''))).total_seconds() < 300
                                        for n in recent_notifications
                                    )
                                    
                                    # 只通知收益率高于5%的套利机会
                                    if not already_notified and profit_rate > 5:
                                        notification_manager.create_notification(
                                            username=username,
                                            notification_type=NotificationType.ARBITRAGE_OPPORTUNITY,
                                            title=f'发现套利机会：{fund_name} ({fund_code})',
                                            content=f'{arbitrage_type}，预期收益率 {profit_rate:.2f}%',
                                            data={
                                                'fund_code': fund_code,
                                                'fund_name': fund_name,
                                                'arbitrage_type': arbitrage_type,
                                                'profit_rate': profit_rate,
                                                'price': result.get('price'),
                                                'nav': result.get('nav'),
                                                'price_diff_pct': result.get('price_diff_pct')
                                            }
                                        )
                                except Exception as e:
                                    print(f"发送套利机会通知失败: {e}")
                    else:
                        errors += 1
                except Exception as e:
                    errors += 1
                    print(f"获取基金 {fund_code} 失败: {e}")
        
        # #region agent log
        log_data = {
            'sessionId': 'debug-session',
            'runId': 'run1',
            'hypothesisId': 'C',
            'location': 'app.py:get_funds_batch:completed',
            'message': '批量处理完成',
            'data': {'total': len(fund_codes), 'processed': processed, 'errors': errors, 'results_count': len(results)},
            'timestamp': int(time.time() * 1000)
        }
        try:
            with open('c:\\lof1\\.cursor\\debug.log', 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_data, ensure_ascii=False) + '\n')
        except: pass
        # #endregion
        
        # 按收益率排序
        sorted_results = calculator.sort_by_profit(results)
        
        # 分类基金：指数型和股票型
        index_funds = [r for r in sorted_results if LOF_FUNDS.get(r['fund_code'], '').endswith('指数') or '指数' in r.get('fund_name', '')]
        stock_funds = [r for r in sorted_results if r not in index_funds]
        
        return jsonify({
            'success': True,
            'data': sorted_results,
            'count': len(sorted_results),
            'index_funds': index_funds,
            'stock_funds': stock_funds,
            'index_count': len(index_funds),
            'stock_count': len(stock_funds)
        })
    except Exception as e:
        # #region agent log
        log_data = {
            'sessionId': 'debug-session',
            'runId': 'run1',
            'hypothesisId': 'C',
            'location': 'app.py:get_funds_batch:error',
            'message': '批量处理出错',
            'data': {'error': str(e)},
            'timestamp': int(time.time() * 1000)
        }
        try:
            with open('c:\\lof1\\.cursor\\debug.log', 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_data, ensure_ascii=False) + '\n')
        except: pass
        # #endregion
        
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@app.route('/api/funds/purchase-limits', methods=['POST'])
def get_purchase_limits():
    """批量获取基金限购信息（异步调用，不阻塞主流程）"""
    # #region agent log
    import json
    log_data = {
        'sessionId': 'debug-session',
        'runId': 'run1',
        'hypothesisId': 'H',
        'location': 'app.py:get_purchase_limits:entry',
        'message': '开始批量获取限购信息',
        'data': {},
        'timestamp': int(time.time() * 1000)
    }
    try:
        with open('c:\\lof1\\.cursor\\debug.log', 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_data, ensure_ascii=False) + '\n')
    except: pass
    # #endregion
    
    try:
        data = request.get_json()
        fund_codes = data.get('codes', [])
        
        limits = {}
        for fund_code in fund_codes:
            try:
                purchase_limit = data_fetcher.get_fund_purchase_limit(fund_code)
                limits[fund_code] = purchase_limit
            except Exception as e:
                limits[fund_code] = {'is_limited': False, 'limit_amount': None, 'limit_desc': '不限购'}
        
        return jsonify({
            'success': True,
            'limits': limits,
            'count': len(limits)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@app.route('/api/arbitrage/check-purchase-limit', methods=['POST'])
@login_required
def check_purchase_limit():
    """检查申购金额是否超过限购（用于实时验证）"""
    # #region agent log
    import json
    log_data = {
        'sessionId': 'debug-session',
        'runId': 'run1',
        'hypothesisId': 'J',
        'location': 'app.py:check_purchase_limit:entry',
        'message': '开始检查申购限购',
        'data': {},
        'timestamp': int(time.time() * 1000)
    }
    try:
        with open('c:\\lof1\\.cursor\\debug.log', 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_data, ensure_ascii=False) + '\n')
    except: pass
    # #endregion
    
    try:
        data = request.get_json()
        fund_code = data.get('fund_code')
        amount = float(data.get('amount', 0))
        date = data.get('date')
        
        # #region agent log
        log_data = {
            'sessionId': 'debug-session',
            'runId': 'run1',
            'hypothesisId': 'K',
            'location': 'app.py:check_purchase_limit:params',
            'message': '接收到的参数',
            'data': {'fund_code': fund_code, 'amount': amount, 'date': date},
            'timestamp': int(time.time() * 1000)
        }
        try:
            with open('c:\\lof1\\.cursor\\debug.log', 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_data, ensure_ascii=False) + '\n')
        except: pass
        # #endregion
        
        if not fund_code or amount <= 0:
            return jsonify({
                'success': True,
                'is_valid': True,
                'message': ''
            })
        
        username = session.get('username')
        
        # 获取基金限购信息
        try:
            purchase_limit = data_fetcher.get_fund_purchase_limit(fund_code)
            # #region agent log
            log_data = {
                'sessionId': 'debug-session',
                'runId': 'run1',
                'hypothesisId': 'L',
                'location': 'app.py:check_purchase_limit:purchase_limit',
                'message': '获取限购信息',
                'data': {'purchase_limit': purchase_limit},
                'timestamp': int(time.time() * 1000)
            }
            try:
                with open('c:\\lof1\\.cursor\\debug.log', 'a', encoding='utf-8') as f:
                    f.write(json.dumps(log_data, ensure_ascii=False) + '\n')
            except: pass
            # #endregion
        except Exception as e:
            purchase_limit = {'is_limited': False, 'limit_amount': None, 'limit_desc': '不限购'}
        
        # 如果基金不限购，直接返回有效
        if not purchase_limit or not purchase_limit.get('is_limited') or not purchase_limit.get('limit_amount'):
            return jsonify({
                'success': True,
                'is_valid': True,
                'message': '',
                'purchase_limit': purchase_limit
            })
        
        limit_amount = float(purchase_limit.get('limit_amount', 0))
        
        # 检查单次申购金额
        if amount > limit_amount:
            limit_display = limit_amount / 10000 if limit_amount >= 10000 else limit_amount
            limit_unit = '万元' if limit_amount >= 10000 else '元'
            return jsonify({
                'success': True,
                'is_valid': False,
                'message': f'单次申购金额超过限购 {limit_display:.2f} {limit_unit}',
                'purchase_limit': purchase_limit,
                'limit_amount': limit_amount
            })
        
        # 获取当天累计申购金额
        if date is None:
            from datetime import datetime
            date = datetime.now().strftime('%Y-%m-%d')
        
        daily_amount = arbitrage_recorder.get_daily_purchase_amount(
            username=username,
            fund_code=fund_code,
            date=date
        )
        
        # #region agent log
        log_data = {
            'sessionId': 'debug-session',
            'runId': 'run1',
            'hypothesisId': 'M',
            'location': 'app.py:check_purchase_limit:daily_amount',
            'message': '获取当天累计申购金额',
            'data': {
                'daily_amount': daily_amount,
                'new_amount': amount,
                'total_after': daily_amount + amount,
                'limit_amount': limit_amount
            },
            'timestamp': int(time.time() * 1000)
        }
        try:
            with open('c:\\lof1\\.cursor\\debug.log', 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_data, ensure_ascii=False) + '\n')
        except: pass
        # #endregion
        
        # 检查累计申购金额
        total_amount = daily_amount + amount
        if total_amount > limit_amount:
            remaining = limit_amount - daily_amount
            remaining_display = remaining / 10000 if remaining >= 10000 else remaining
            remaining_unit = '万元' if remaining >= 10000 else '元'
            limit_display = limit_amount / 10000 if limit_amount >= 10000 else limit_amount
            limit_unit = '万元' if limit_amount >= 10000 else '元'
            return jsonify({
                'success': True,
                'is_valid': False,
                'message': f'当天累计申购金额将超过限购 {limit_display:.2f} {limit_unit}，剩余可申购 {remaining_display:.2f} {remaining_unit}',
                'purchase_limit': purchase_limit,
                'limit_amount': limit_amount,
                'daily_amount': daily_amount,
                'remaining': remaining
            })
        
        # 金额有效
        remaining = limit_amount - total_amount
        remaining_display = remaining / 10000 if remaining >= 10000 else remaining
        remaining_unit = '万元' if remaining >= 10000 else '元'
        return jsonify({
            'success': True,
            'is_valid': True,
            'message': f'剩余可申购额度：{remaining_display:.2f} {remaining_unit}',
            'purchase_limit': purchase_limit,
            'limit_amount': limit_amount,
            'daily_amount': daily_amount,
            'remaining': remaining
        })
        
    except Exception as e:
        # #region agent log
        log_data = {
            'sessionId': 'debug-session',
            'runId': 'run1',
            'hypothesisId': 'N',
            'location': 'app.py:check_purchase_limit:error',
            'message': '检查限购失败',
            'data': {'error': str(e)},
            'timestamp': int(time.time() * 1000)
        }
        try:
            with open('c:\\lof1\\.cursor\\debug.log', 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_data, ensure_ascii=False) + '\n')
        except: pass
        # #endregion
        
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@app.route('/api/config')
def get_config():
    """获取配置信息"""
    # 如果用户已登录，返回用户设置，否则返回默认配置
    if 'logged_in' in session and session.get('logged_in'):
        username = session.get('username')
        user_settings = user_manager.get_user_settings(username)
        
        # 合并用户设置和默认配置（数据源配置始终使用全局配置）
        config = {
            'trade_fees': user_settings.get('trade_fees', TRADE_FEES),
            'arbitrage_threshold': user_settings.get('arbitrage_threshold', ARBITRAGE_THRESHOLD),
            'update_interval': user_settings.get('update_interval', DATA_SOURCE['update_interval']),
            'data_sources': DATA_SOURCE,  # 数据源配置始终使用全局配置
            'use_mock_data': use_mock_data
        }
    else:
        # 未登录用户返回默认配置
        config = {
            'trade_fees': TRADE_FEES,
            'arbitrage_threshold': ARBITRAGE_THRESHOLD,
            'update_interval': DATA_SOURCE['update_interval'],
            'data_sources': DATA_SOURCE,
            'use_mock_data': use_mock_data
        }
    
    return jsonify({
        'success': True,
        'data': config
    })


@app.route('/api/config', methods=['POST'])
@login_required
def update_config():
    """更新配置（保存到用户设置）"""
    try:
        username = session.get('username')
        data = request.get_json()
        
        # 准备用户设置
        user_settings = {}
        
        # 保存交易费用
        if 'trade_fees' in data:
            user_settings['trade_fees'] = data['trade_fees']
        
        # 保存套利阈值
        if 'arbitrage_threshold' in data:
            user_settings['arbitrage_threshold'] = data['arbitrage_threshold']
        
        # 保存更新间隔（用户个人设置）
        if 'data_sources' in data:
            data_sources = data['data_sources']
            if 'update_interval' in data_sources:
                user_settings['update_interval'] = data_sources['update_interval']
        
        # 保存到用户设置
        user_manager.set_user_settings(username, user_settings)
        
        # 更新计算器
        global calculator
        calculator = ArbitrageCalculator()
        
        return jsonify({
            'success': True,
            'message': '配置更新成功'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@app.route('/api/mode', methods=['POST'])
def toggle_mode():
    """切换数据模式（真实/模拟）"""
    try:
        data = request.get_json()
        mock = data.get('mock', False)
        init_fetcher(mock)
        
        return jsonify({
            'success': True,
            'message': f'已切换到{"模拟数据" if mock else "真实数据"}模式'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


# 套利记录相关API
@app.route('/api/arbitrage/records', methods=['POST'])
@login_required
def create_arbitrage_record():
    """创建套利记录"""
    # #region agent log
    import json
    log_data = {
        'sessionId': 'debug-session',
        'runId': 'run1',
        'hypothesisId': 'A',
        'location': 'app.py:create_arbitrage_record:entry',
        'message': '开始创建套利记录',
        'data': {},
        'timestamp': int(time.time() * 1000)
    }
    try:
        with open('c:\\lof1\\.cursor\\debug.log', 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_data, ensure_ascii=False) + '\n')
    except: pass
    # #endregion
    
    try:
        data = request.get_json()
        fund_code = data.get('fund_code')
        fund_name = data.get('fund_name', '')
        arbitrage_type = data.get('arbitrage_type')  # 'premium' or 'discount'
        initial_price = float(data.get('initial_price', 0))
        initial_shares = float(data.get('initial_shares', 0))
        initial_amount = float(data.get('initial_amount', 0))
        initial_date = data.get('initial_date')
        
        # #region agent log
        log_data = {
            'sessionId': 'debug-session',
            'runId': 'run1',
            'hypothesisId': 'B',
            'location': 'app.py:create_arbitrage_record:params',
            'message': '接收到的参数',
            'data': {
                'fund_code': fund_code,
                'arbitrage_type': arbitrage_type,
                'initial_amount': initial_amount,
                'initial_date': initial_date
            },
            'timestamp': int(time.time() * 1000)
        }
        try:
            with open('c:\\lof1\\.cursor\\debug.log', 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_data, ensure_ascii=False) + '\n')
        except: pass
        # #endregion
        
        if not fund_code or not arbitrage_type or initial_price <= 0 or initial_amount <= 0:
            return jsonify({
                'success': False,
                'message': '参数不完整'
            }), 400
        
        username = session.get('username')
        
        # 只对溢价套利（申购）进行限购验证
        if arbitrage_type == 'premium':
            # #region agent log
            log_data = {
                'sessionId': 'debug-session',
                'runId': 'run1',
                'hypothesisId': 'C',
                'location': 'app.py:create_arbitrage_record:check_limit_start',
                'message': '开始检查限购',
                'data': {'fund_code': fund_code, 'initial_amount': initial_amount},
                'timestamp': int(time.time() * 1000)
            }
            try:
                with open('c:\\lof1\\.cursor\\debug.log', 'a', encoding='utf-8') as f:
                    f.write(json.dumps(log_data, ensure_ascii=False) + '\n')
            except: pass
            # #endregion
            
            # 获取基金限购信息
            try:
                purchase_limit = data_fetcher.get_fund_purchase_limit(fund_code)
                # #region agent log
                log_data = {
                    'sessionId': 'debug-session',
                    'runId': 'run1',
                    'hypothesisId': 'D',
                    'location': 'app.py:create_arbitrage_record:purchase_limit',
                    'message': '获取限购信息',
                    'data': {'purchase_limit': purchase_limit},
                    'timestamp': int(time.time() * 1000)
                }
                try:
                    with open('c:\\lof1\\.cursor\\debug.log', 'a', encoding='utf-8') as f:
                        f.write(json.dumps(log_data, ensure_ascii=False) + '\n')
                except: pass
                # #endregion
            except Exception as e:
                # 如果获取限购信息失败，默认不限购
                purchase_limit = {'is_limited': False, 'limit_amount': None, 'limit_desc': '不限购'}
                # #region agent log
                log_data = {
                    'sessionId': 'debug-session',
                    'runId': 'run1',
                    'hypothesisId': 'E',
                    'location': 'app.py:create_arbitrage_record:purchase_limit_error',
                    'message': '获取限购信息失败，使用默认值',
                    'data': {'error': str(e), 'purchase_limit': purchase_limit},
                    'timestamp': int(time.time() * 1000)
                }
                try:
                    with open('c:\\lof1\\.cursor\\debug.log', 'a', encoding='utf-8') as f:
                        f.write(json.dumps(log_data, ensure_ascii=False) + '\n')
                except: pass
                # #endregion
            
            # 如果基金有限购，进行验证
            if purchase_limit and purchase_limit.get('is_limited') and purchase_limit.get('limit_amount'):
                limit_amount = float(purchase_limit.get('limit_amount', 0))
                
                # #region agent log
                log_data = {
                    'sessionId': 'debug-session',
                    'runId': 'run1',
                    'hypothesisId': 'F',
                    'location': 'app.py:create_arbitrage_record:limit_check',
                    'message': '基金有限购，开始验证',
                    'data': {'limit_amount': limit_amount, 'initial_amount': initial_amount},
                    'timestamp': int(time.time() * 1000)
                }
                try:
                    with open('c:\\lof1\\.cursor\\debug.log', 'a', encoding='utf-8') as f:
                        f.write(json.dumps(log_data, ensure_ascii=False) + '\n')
                except: pass
                # #endregion
                
                # 检查单次申购金额是否超过限购
                if initial_amount > limit_amount:
                    limit_display = limit_amount / 10000 if limit_amount >= 10000 else limit_amount
                    limit_unit = '万元' if limit_amount >= 10000 else '元'
                    return jsonify({
                        'success': False,
                        'message': f'单次申购金额 {initial_amount:.2f} 元超过限购金额 {limit_display:.2f} {limit_unit}'
                    }), 400
                
                # 获取当天累计申购金额
                if initial_date is None:
                    from datetime import datetime
                    initial_date = datetime.now().strftime('%Y-%m-%d')
                
                daily_amount = arbitrage_recorder.get_daily_purchase_amount(
                    username=username,
                    fund_code=fund_code,
                    date=initial_date
                )
                
                # #region agent log
                log_data = {
                    'sessionId': 'debug-session',
                    'runId': 'run1',
                    'hypothesisId': 'G',
                    'location': 'app.py:create_arbitrage_record:daily_amount',
                    'message': '获取当天累计申购金额',
                    'data': {
                        'daily_amount': daily_amount,
                        'initial_date': initial_date,
                        'new_amount': initial_amount,
                        'total_after': daily_amount + initial_amount,
                        'limit_amount': limit_amount
                    },
                    'timestamp': int(time.time() * 1000)
                }
                try:
                    with open('c:\\lof1\\.cursor\\debug.log', 'a', encoding='utf-8') as f:
                        f.write(json.dumps(log_data, ensure_ascii=False) + '\n')
                except: pass
                # #endregion
                
                # 检查累计申购金额是否超过限购
                total_amount = daily_amount + initial_amount
                if total_amount > limit_amount:
                    remaining = limit_amount - daily_amount
                    remaining_display = remaining / 10000 if remaining >= 10000 else remaining
                    remaining_unit = '万元' if remaining >= 10000 else '元'
                    limit_display = limit_amount / 10000 if limit_amount >= 10000 else limit_amount
                    limit_unit = '万元' if limit_amount >= 10000 else '元'
                    return jsonify({
                        'success': False,
                        'message': f'当天累计申购金额 {total_amount:.2f} 元超过限购金额 {limit_display:.2f} {limit_unit}，剩余可申购 {remaining_display:.2f} {remaining_unit}'
                    }), 400
        
        record_id = arbitrage_recorder.create_record(
            fund_code=fund_code,
            fund_name=fund_name,
            arbitrage_type=arbitrage_type,
            initial_price=initial_price,
            initial_shares=initial_shares,
            initial_amount=initial_amount,
            initial_date=initial_date,
            username=username
        )
        
        # #region agent log
        log_data = {
            'sessionId': 'debug-session',
            'runId': 'run1',
            'hypothesisId': 'H',
            'location': 'app.py:create_arbitrage_record:success',
            'message': '套利记录创建成功',
            'data': {'record_id': record_id},
            'timestamp': int(time.time() * 1000)
        }
        try:
            with open('c:\\lof1\\.cursor\\debug.log', 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_data, ensure_ascii=False) + '\n')
        except: pass
        # #endregion
        
        return jsonify({
            'success': True,
            'record_id': record_id,
            'message': '套利记录创建成功'
        })
    except Exception as e:
        # #region agent log
        log_data = {
            'sessionId': 'debug-session',
            'runId': 'run1',
            'hypothesisId': 'I',
            'location': 'app.py:create_arbitrage_record:error',
            'message': '创建套利记录失败',
            'data': {'error': str(e)},
            'timestamp': int(time.time() * 1000)
        }
        try:
            with open('c:\\lof1\\.cursor\\debug.log', 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_data, ensure_ascii=False) + '\n')
        except: pass
        # #endregion
        
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@app.route('/api/arbitrage/records/<record_id>/complete', methods=['POST'])
@login_required
def complete_arbitrage_record(record_id):
    """完成套利记录"""
    try:
        data = request.get_json()
        final_price = float(data.get('final_price', 0))
        final_shares = data.get('final_shares')
        final_amount = data.get('final_amount')
        final_date = data.get('final_date')
        
        if final_price <= 0:
            return jsonify({
                'success': False,
                'message': '最终价格必须大于0'
            }), 400
        
        if final_shares is not None:
            final_shares = float(final_shares)
        if final_amount is not None:
            final_amount = float(final_amount)
        
        username = session.get('username')
        success = arbitrage_recorder.complete_record(
            record_id=record_id,
            final_price=final_price,
            username=username,
            final_shares=final_shares,
            final_amount=final_amount,
            final_date=final_date
        )
        
        if success:
            username = session.get('username')
            record = arbitrage_recorder.get_record(record_id, username)
            
            # 发送套利完成通知
            if record:
                try:
                    fund_code = record.get('fund_code', '')
                    fund_name = record.get('fund_name', fund_code)
                    arbitrage_type = record.get('arbitrage_type', '')
                    profit = record.get('profit', 0)
                    profit_rate = record.get('profit_rate', 0)
                    
                    # 判断是溢价套利还是折价套利
                    if arbitrage_type == 'premium' or '溢价' in str(arbitrage_type):
                        # 溢价套利：场外申购 → 场内卖出，卖出时通知
                        notification_manager.create_notification(
                            username=username,
                            notification_type=NotificationType.ARBITRAGE_SELL,
                            title=f'套利卖出提醒：{fund_name} ({fund_code})',
                            content=f'溢价套利已完成，可进行场内卖出操作。预期收益 {profit:.2f} 元（{profit_rate:.2f}%）',
                            data={
                                'fund_code': fund_code,
                                'fund_name': fund_name,
                                'arbitrage_type': 'premium',
                                'profit': profit,
                                'profit_rate': profit_rate,
                                'record_id': record_id
                            }
                        )
                    
                    # 发送套利完成通知
                    notification_manager.create_notification(
                        username=username,
                        notification_type=NotificationType.ARBITRAGE_COMPLETED,
                        title=f'套利交易完成：{fund_name} ({fund_code})',
                        content=f'套利交易已完成，最终收益 {profit:.2f} 元（{profit_rate:.2f}%）',
                        data={
                            'fund_code': fund_code,
                            'fund_name': fund_name,
                            'arbitrage_type': arbitrage_type,
                            'profit': profit,
                            'profit_rate': profit_rate,
                            'record_id': record_id
                        }
                    )
                except Exception as e:
                    print(f"发送套利完成通知失败: {e}")
            
            return jsonify({
                'success': True,
                'record': record,
                'message': '套利记录完成'
            })
        else:
            return jsonify({
                'success': False,
                'message': '完成记录失败，记录不存在或状态不正确'
            }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@app.route('/api/arbitrage/records', methods=['GET'])
@login_required
def get_arbitrage_records():
    """获取套利记录列表"""
    try:
        username = session.get('username')
        fund_code = request.args.get('fund_code')
        status = request.args.get('status')
        
        records = arbitrage_recorder.get_all_records(fund_code=fund_code, status=status, username=username)
        
        return jsonify({
            'success': True,
            'records': records,
            'count': len(records)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@app.route('/api/arbitrage/records/<record_id>', methods=['GET'])
@login_required
def get_arbitrage_record(record_id):
    """获取单条套利记录"""
    try:
        record = arbitrage_recorder.get_record(record_id)
        if record:
            return jsonify({
                'success': True,
                'record': record
            })
        else:
            return jsonify({
                'success': False,
                'message': '记录不存在'
            }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@app.route('/api/arbitrage/records/<record_id>', methods=['DELETE'])
@login_required
def delete_arbitrage_record(record_id):
    """删除套利记录"""
    try:
        success = arbitrage_recorder.delete_record(record_id)
        if success:
            return jsonify({
                'success': True,
                'message': '记录已删除'
            })
        else:
            return jsonify({
                'success': False,
                'message': '记录不存在'
            }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@app.route('/api/arbitrage/records/<record_id>/cancel', methods=['POST'])
@login_required
def cancel_arbitrage_record(record_id):
    """取消套利记录"""
    try:
        success = arbitrage_recorder.cancel_record(record_id)
        if success:
            return jsonify({
                'success': True,
                'message': '记录已取消'
            })
        else:
            return jsonify({
                'success': False,
                'message': '记录不存在'
            }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@app.route('/api/arbitrage/statistics', methods=['GET'])
@login_required
def get_arbitrage_statistics():
    """获取套利统计信息"""
    try:
        username = session.get('username')
        stats = arbitrage_recorder.get_statistics(username)
        return jsonify({
            'success': True,
            'statistics': stats
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


# ==================== 管理员套利记录管理API ====================

@app.route('/api/admin/arbitrage/records', methods=['GET'])
@admin_required
def get_all_arbitrage_records():
    """获取所有用户的套利记录（仅管理员）"""
    try:
        fund_code = request.args.get('fund_code')
        status = request.args.get('status')
        
        records = arbitrage_recorder.get_all_records(
            fund_code=fund_code,
            status=status
        )
        
        return jsonify({
            'success': True,
            'records': records,
            'count': len(records)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@app.route('/api/admin/arbitrage/statistics', methods=['GET'])
@admin_required
def get_all_arbitrage_statistics():
    """获取所有用户的套利统计信息（仅管理员）"""
    try:
        statistics = arbitrage_recorder.get_all_users_statistics()
        return jsonify({
            'success': True,
            'statistics': statistics
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


# ==================== 用户认证相关API ====================

# 初始化防护模块
from captcha import CaptchaManager
from rate_limiter import RateLimiter
from datetime import datetime

captcha_manager = CaptchaManager()
rate_limiter = RateLimiter()

@app.route('/api/auth/captcha', methods=['GET'])
def get_captcha():
    """获取验证码"""
    try:
        session_id = session.get('id', str(time.time()))
        if 'id' not in session:
            session['id'] = session_id
        
        captcha_data = captcha_manager.generate_captcha(session_id)
        # 不返回答案给客户端
        return jsonify({
            'success': True,
            'question': captcha_data['question']
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/api/auth/register', methods=['POST'])
def register():
    """用户注册"""
    try:
        data = request.get_json()
        username = (data.get('username') or '').strip()
        password = data.get('password') or ''
        email = (data.get('email') or '').strip() or None
        captcha_answer = data.get('captcha_answer', '').strip()
        
        # #region agent log
        with open('c:\\lof1\\.cursor\\debug.log', 'a', encoding='utf-8') as f:
            import json
            f.write(json.dumps({'location':'app.py:register:entry','message':'开始注册','data':{'username':username,'passwordLength':len(password) if password else 0,'hasEmail':bool(email),'hasCaptcha':bool(captcha_answer)},'timestamp':int(time.time()*1000),'sessionId':'debug-session','hypothesisId':'1,2'})+'\n')
        # #endregion
        
        # 获取客户端IP
        client_ip = request.remote_addr or request.environ.get('HTTP_X_FORWARDED_FOR', '').split(',')[0] or 'unknown'
        
        # 检查频率限制
        rate_ok, rate_message = rate_limiter.check_rate_limit(client_ip, username)
        if not rate_ok:
            # #region agent log
            with open('c:\\lof1\\.cursor\\debug.log', 'a', encoding='utf-8') as f:
                import json
                f.write(json.dumps({'location':'app.py:register:rate_limit','message':'频率限制','data':{'ip':client_ip,'username':username,'message':rate_message},'timestamp':int(time.time()*1000),'sessionId':'debug-session','hypothesisId':'6'})+'\n')
            # #endregion
            rate_limiter.record_attempt(client_ip, username, success=False)
            return jsonify({
                'success': False,
                'message': rate_message
            }), 429  # Too Many Requests
        
        if not username or not password:
            # #region agent log
            with open('c:\\lof1\\.cursor\\debug.log', 'a', encoding='utf-8') as f:
                import json
                f.write(json.dumps({'location':'app.py:register:validation_failed','message':'用户名或密码为空','data':{'hasUsername':bool(username),'hasPassword':bool(password)},'timestamp':int(time.time()*1000),'sessionId':'debug-session','hypothesisId':'2'})+'\n')
            # #endregion
            rate_limiter.record_attempt(client_ip, username, success=False)
            return jsonify({
                'success': False,
                'message': '用户名和密码不能为空'
            }), 400
        
        # 验证验证码
        session_id = session.get('id', str(time.time()))
        if 'id' not in session:
            session['id'] = session_id
        
        captcha_ok, captcha_message = captcha_manager.verify_captcha(session_id, captcha_answer)
        if not captcha_ok:
            # #region agent log
            with open('c:\\lof1\\.cursor\\debug.log', 'a', encoding='utf-8') as f:
                import json
                f.write(json.dumps({'location':'app.py:register:captcha_failed','message':'验证码验证失败','data':{'message':captcha_message},'timestamp':int(time.time()*1000),'sessionId':'debug-session','hypothesisId':'7'})+'\n')
            # #endregion
            rate_limiter.record_attempt(client_ip, username, success=False)
            return jsonify({
                'success': False,
                'message': captcha_message
            }), 400
        
        # #region agent log
        with open('c:\\lof1\\.cursor\\debug.log', 'a', encoding='utf-8') as f:
            import json
            f.write(json.dumps({'location':'app.py:register:before_register','message':'调用user_manager.register前','data':{'username':username,'usernameLength':len(username),'passwordLength':len(password)},'timestamp':int(time.time()*1000),'sessionId':'debug-session','hypothesisId':'1,2'})+'\n')
        # #endregion
        
        success, message = user_manager.register(username, password, email)
        
        # #region agent log
        with open('c:\\lof1\\.cursor\\debug.log', 'a', encoding='utf-8') as f:
            import json
            f.write(json.dumps({'location':'app.py:register:after_register','message':'调用user_manager.register后','data':{'success':success,'message':message},'timestamp':int(time.time()*1000),'sessionId':'debug-session','hypothesisId':'1,2,5'})+'\n')
        # #endregion
        
        if success:
            # 记录成功的注册
            rate_limiter.record_attempt(client_ip, username, success=True)
            return jsonify({
                'success': True,
                'message': message
            })
        else:
            # 记录失败的注册尝试
            rate_limiter.record_attempt(client_ip, username, success=False)
            return jsonify({
                'success': False,
                'message': message
            }), 400
    except Exception as e:
        # #region agent log
        with open('c:\\lof1\\.cursor\\debug.log', 'a', encoding='utf-8') as f:
            import json
            f.write(json.dumps({'location':'app.py:register:exception','message':'注册异常','data':{'error':str(e),'type':type(e).__name__},'timestamp':int(time.time()*1000),'sessionId':'debug-session','hypothesisId':'3,4'})+'\n')
        # #endregion
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@app.route('/api/auth/login', methods=['POST'])
def login():
    """用户登录"""
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '')
        
        if not username or not password:
            return jsonify({
                'success': False,
                'message': '用户名和密码不能为空'
            }), 400
        
        success, message, user_info = user_manager.login(username, password)
        
        if success:
            # 设置session
            session['username'] = username
            session['logged_in'] = True
            
            return jsonify({
                'success': True,
                'message': message,
                'user': user_info
            })
        else:
            return jsonify({
                'success': False,
                'message': message
            }), 401
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@app.route('/api/auth/logout', methods=['POST'])
def logout():
    """用户登出"""
    try:
        session.clear()
        return jsonify({
            'success': True,
            'message': '登出成功'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@app.route('/api/auth/current', methods=['GET'])
def get_current_user():
    """获取当前登录用户信息"""
    try:
        if 'logged_in' in session and session.get('logged_in'):
            username = session.get('username')
            user_info = user_manager.get_user(username)
            if user_info:
                return jsonify({
                    'success': True,
                    'user': user_info
                })
        
        return jsonify({
            'success': False,
            'message': '未登录'
        }), 401
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


# ==================== 用户数据相关API ====================

@app.route('/api/user/favorites', methods=['GET'])
@login_required
def get_user_favorites():
    """获取用户的自选基金列表"""
    username = session.get('username')
    favorites = user_manager.get_user_favorites(username)
    return jsonify({
        'success': True,
        'favorites': favorites
    })


@app.route('/api/user/favorites', methods=['POST'])
@login_required
def update_user_favorites():
    """更新用户的自选基金列表"""
    try:
        username = session.get('username')
        data = request.get_json()
        fund_codes = data.get('favorites', [])
        
        success = user_manager.set_user_favorites(username, fund_codes)
        if success:
            return jsonify({
                'success': True,
                'message': '自选基金已更新'
            })
        else:
            return jsonify({
                'success': False,
                'message': '更新失败'
            }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@app.route('/api/user/favorites/<fund_code>', methods=['POST'])
@login_required
def add_user_favorite(fund_code):
    """添加自选基金"""
    try:
        username = session.get('username')
        success = user_manager.add_user_favorite(username, fund_code)
        if success:
            return jsonify({
                'success': True,
                'message': '已添加到自选'
            })
        else:
            return jsonify({
                'success': False,
                'message': '添加失败'
            }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@app.route('/api/user/favorites/<fund_code>', methods=['DELETE'])
@login_required
def remove_user_favorite(fund_code):
    """移除自选基金"""
    try:
        username = session.get('username')
        success = user_manager.remove_user_favorite(username, fund_code)
        if success:
            return jsonify({
                'success': True,
                'message': '已从自选移除'
            })
        else:
            return jsonify({
                'success': False,
                'message': '移除失败'
            }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@app.route('/api/user/settings', methods=['GET'])
@login_required
def get_user_settings():
    """获取用户的设置"""
    username = session.get('username')
    settings = user_manager.get_user_settings(username)
    return jsonify({
        'success': True,
        'settings': settings
    })


@app.route('/api/user/settings', methods=['POST'])
@login_required
def update_user_settings():
    """更新用户的设置"""
    try:
        username = session.get('username')
        data = request.get_json()
        settings = data.get('settings', {})
        
        success = user_manager.set_user_settings(username, settings)
        if success:
            return jsonify({
                'success': True,
                'message': '设置已保存'
            })
        else:
            return jsonify({
                'success': False,
                'message': '保存失败'
            }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


# ==================== 数据源配置相关API（仅管理员） ====================

@app.route('/api/data-sources/config', methods=['GET'])
@admin_required
def get_data_source_config():
    """获取数据源配置（仅管理员）"""
    # 合并保存的配置和默认配置
    merged_config = data_source_config_manager.merge_with_default(DATA_SOURCE)
    
    return jsonify({
        'success': True,
        'data': {
            'update_interval': merged_config['update_interval'],
            'data_sources': merged_config
        }
    })


@app.route('/api/data-sources/config', methods=['POST'])
@admin_required
def update_data_source_config():
    """更新数据源配置（仅管理员）"""
    try:
        data = request.get_json()
        data_sources = data.get('data_sources', {})
        
        # 保存配置到文件
        data_source_config_manager.update_config(data_sources)
        
        # 更新全局数据源配置（运行时使用）
        global DATA_SOURCE
        merged_config = data_source_config_manager.merge_with_default(DATA_SOURCE)
        DATA_SOURCE.update(merged_config)
        
        # 如果更新了Tushare配置，重新初始化fetcher
        if 'fund_list_sources' in data_sources and 'tushare' in data_sources['fund_list_sources']:
            tushare_config = data_sources['fund_list_sources']['tushare']
            
            # 重新初始化数据获取器
            global data_fetcher
            # 优先使用环境变量，其次使用UI配置
            tushare_token = None
            env_token = os.getenv('TUSHARE_TOKEN')
            if env_token:
                tushare_token = env_token
            elif tushare_config.get('token'):
                tushare_token = tushare_config.get('token')
            elif DATA_SOURCE.get('tushare_token'):
                tushare_token = DATA_SOURCE.get('tushare_token')
            
            if not use_mock_data and tushare_token:
                data_fetcher = LOFDataFetcher(tushare_token=tushare_token)
                data_fetcher.data_source_config = DATA_SOURCE
        
        return jsonify({
            'success': True,
            'message': '数据源配置已更新并保存'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


# ==================== 用户管理相关API（仅管理员） ====================

@app.route('/api/users', methods=['GET'])
@admin_required
def list_users():
    """获取所有用户列表（仅管理员）"""
    try:
        users = user_manager.list_all_users()
        return jsonify({
            'success': True,
            'users': users,
            'count': len(users)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@app.route('/api/users/<username>', methods=['PUT'])
@admin_required
def update_user(username):
    """更新用户信息（仅管理员）"""
    try:
        data = request.get_json()
        
        # 更新邮箱
        if 'email' in data:
            success = user_manager.update_user_email(username, data['email'])
            if not success:
                return jsonify({
                    'success': False,
                    'message': '用户不存在'
                }), 404
        
        # 更新角色
        if 'role' in data:
            success = user_manager.update_user_role(username, data['role'])
            if not success:
                return jsonify({
                    'success': False,
                    'message': '用户不存在或角色无效'
                }), 400
        
        # 重置密码
        if 'password' in data and data['password']:
            success = user_manager.reset_user_password(username, data['password'])
            if not success:
                return jsonify({
                    'success': False,
                    'message': '用户不存在或密码不符合要求'
                }), 400
        
        return jsonify({
            'success': True,
            'message': '用户信息已更新'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@app.route('/api/users/<username>', methods=['DELETE'])
@admin_required
def delete_user(username):
    """删除用户（仅管理员）"""
    try:
        # 不能删除自己
        current_username = session.get('username')
        if username == current_username:
            return jsonify({
                'success': False,
                'message': '不能删除自己的账户'
            }), 400
        
        success = user_manager.delete_user(username)
        if success:
            return jsonify({
                'success': True,
                'message': '用户已删除'
            })
        else:
            return jsonify({
                'success': False,
                'message': '用户不存在'
            }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


# ==================== 通知相关API ====================

@app.route('/api/notifications', methods=['GET'])
@login_required
def get_notifications():
    """获取用户通知列表"""
    try:
        username = session.get('username')
        unread_only = request.args.get('unread_only', 'false').lower() == 'true'
        limit = request.args.get('limit', type=int)
        
        notifications = notification_manager.get_notifications(
            username, unread_only=unread_only, limit=limit
        )
        
        return jsonify({
            'success': True,
            'notifications': notifications,
            'count': len(notifications)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@app.route('/api/notifications/unread-count', methods=['GET'])
@login_required
def get_unread_count():
    """获取未读通知数量"""
    try:
        username = session.get('username')
        count = notification_manager.get_unread_count(username)
        return jsonify({
            'success': True,
            'count': count
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@app.route('/api/notifications/<notification_id>/read', methods=['POST'])
@login_required
def mark_notification_read(notification_id):
    """标记通知为已读"""
    try:
        username = session.get('username')
        success = notification_manager.mark_as_read(username, notification_id)
        if success:
            return jsonify({
                'success': True,
                'message': '已标记为已读'
            })
        else:
            return jsonify({
                'success': False,
                'message': '通知不存在'
            }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@app.route('/api/notifications/read-all', methods=['POST'])
@login_required
def mark_all_notifications_read():
    """标记所有通知为已读"""
    try:
        username = session.get('username')
        count = notification_manager.mark_all_as_read(username)
        return jsonify({
            'success': True,
            'message': f'已标记 {count} 条通知为已读',
            'count': count
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@app.route('/api/notifications/<notification_id>', methods=['DELETE'])
@login_required
def delete_notification(notification_id):
    """删除通知"""
    try:
        username = session.get('username')
        success = notification_manager.delete_notification(username, notification_id)
        if success:
            return jsonify({
                'success': True,
                'message': '通知已删除'
            })
        else:
            return jsonify({
                'success': False,
                'message': '通知不存在'
            }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@app.route('/api/notifications/delete-read', methods=['POST'])
@login_required
def delete_read_notifications():
    """删除所有已读通知"""
    try:
        username = session.get('username')
        count = notification_manager.delete_all_read(username)
        return jsonify({
            'success': True,
            'message': f'已删除 {count} 条已读通知',
            'count': count
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


if __name__ == '__main__':
    import sys
    use_mock = '--mock' in sys.argv
    if use_mock:
        init_fetcher(True)
        print("使用模拟数据模式")
    
    app.run(debug=True, host='0.0.0.0', port=8505)
