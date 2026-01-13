# -*- coding: utf-8 -*-
"""
用户管理模块
处理用户注册、登录、密码加密等
"""

import json
import os
from datetime import datetime
from typing import Dict, Optional, List
from werkzeug.security import generate_password_hash, check_password_hash

def _get_log_path():
    """获取日志文件路径（跨平台）"""
    try:
        # 尝试获取项目根目录
        current_dir = os.path.dirname(os.path.abspath(__file__))
        log_dir = os.path.join(current_dir, '.cursor')
        if not os.path.exists(log_dir):
            return None
        return os.path.join(log_dir, 'debug.log')
    except:
        return None


class UserManager:
    """用户管理器"""
    
    def __init__(self, data_file: str = "users.json"):
        """
        初始化用户管理器
        
        Args:
            data_file: 用户数据文件路径
        """
        self.data_file = data_file
        self.users = self._load_users()
        # 初始化默认管理员账户（如果不存在）
        self._init_default_admin()
    
    def _load_users(self) -> Dict:
        """加载用户数据"""
        # #region agent log
        import json
        log_path = _get_log_path()
        if log_path:
            try:
                with open(log_path, 'a', encoding='utf-8') as f:
                    f.write(json.dumps({'location':'user_manager.py:_load_users:entry','message':'开始加载用户数据','data':{'data_file':self.data_file,'file_exists':os.path.exists(self.data_file)},'timestamp':int(datetime.now().timestamp()*1000),'sessionId':'debug-session','hypothesisId':'A'})+'\n')
            except: pass
        # #endregion
        
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    users = json.load(f)
                    # #region agent log
                    log_path = _get_log_path()
                    if log_path:
                        try:
                            with open(log_path, 'a', encoding='utf-8') as f:
                                f.write(json.dumps({'location':'user_manager.py:_load_users:loaded','message':'用户数据加载成功','data':{'usersCount':len(users),'usernames':list(users.keys())},'timestamp':int(datetime.now().timestamp()*1000),'sessionId':'debug-session','hypothesisId':'A'})+'\n')
                        except: pass
                    # #endregion
                    
                    # 为旧用户数据添加缺失的字段
                    updated = False
                    for username, user_data in users.items():
                        if 'role' not in user_data:
                            user_data['role'] = 'user'
                            updated = True
                        if 'favorites' not in user_data:
                            user_data['favorites'] = []
                            updated = True
                        if 'settings' not in user_data:
                            user_data['settings'] = {}
                            updated = True
                    # 如果有更新，保存回去
                    if updated:
                        with open(self.data_file, 'w', encoding='utf-8') as f:
                            json.dump(users, f, ensure_ascii=False, indent=2)
                    return users
            except Exception as e:
                # #region agent log
                log_path = _get_log_path()
                if log_path:
                    try:
                        with open(log_path, 'a', encoding='utf-8') as f:
                            f.write(json.dumps({'location':'user_manager.py:_load_users:error','message':'加载用户数据失败','data':{'error':str(e)},'timestamp':int(datetime.now().timestamp()*1000),'sessionId':'debug-session','hypothesisId':'A'})+'\n')
                    except: pass
                # #endregion
                print(f"加载用户数据失败: {e}")
                return {}
        
        # #region agent log
        log_path = _get_log_path()
        if log_path:
            try:
                with open(log_path, 'a', encoding='utf-8') as f:
                    f.write(json.dumps({'location':'user_manager.py:_load_users:empty','message':'用户数据文件不存在，返回空字典','data':{'data_file':self.data_file},'timestamp':int(datetime.now().timestamp()*1000),'sessionId':'debug-session','hypothesisId':'A'})+'\n')
            except: pass
        # #endregion
        return {}
    
    def _init_default_admin(self):
        """初始化默认管理员账户（如果不存在）"""
        # #region agent log
        import json
        log_path = _get_log_path()
        if log_path:
            try:
                with open(log_path, 'a', encoding='utf-8') as f:
                    f.write(json.dumps({'location':'user_manager.py:_init_default_admin:entry','message':'检查默认管理员账户','data':{'admin_exists':'admin' in self.users},'timestamp':int(datetime.now().timestamp()*1000),'sessionId':'debug-session','hypothesisId':'A'})+'\n')
            except: pass
        # #endregion
        
        default_admin_username = 'admin'
        default_admin_password = 'admin123'
        
        if default_admin_username not in self.users:
            # #region agent log
            log_path = _get_log_path()
            if log_path:
                try:
                    with open(log_path, 'a', encoding='utf-8') as f:
                        f.write(json.dumps({'location':'user_manager.py:_init_default_admin:creating','message':'创建默认管理员账户','data':{'username':default_admin_username},'timestamp':int(datetime.now().timestamp()*1000),'sessionId':'debug-session','hypothesisId':'A'})+'\n')
                except: pass
            # #endregion
            
            self.users[default_admin_username] = {
                'username': default_admin_username,
                'password_hash': generate_password_hash(default_admin_password),
                'email': None,
                'created_at': datetime.now().isoformat(),
                'last_login': None,
                'role': 'admin',  # 管理员角色
                'favorites': [],
                'settings': {}
            }
            self._save_users()
            
            # #region agent log
            log_path = _get_log_path()
            if log_path:
                try:
                    with open(log_path, 'a', encoding='utf-8') as f:
                        f.write(json.dumps({'location':'user_manager.py:_init_default_admin:created','message':'默认管理员账户创建成功','data':{'username':default_admin_username,'usersCount':len(self.users)},'timestamp':int(datetime.now().timestamp()*1000),'sessionId':'debug-session','hypothesisId':'A'})+'\n')
                except: pass
            # #endregion
            print(f"[初始化] 已创建默认管理员账户: {default_admin_username} / {default_admin_password}")
        else:
            # #region agent log
            log_path = _get_log_path()
            if log_path:
                try:
                    with open(log_path, 'a', encoding='utf-8') as f:
                        f.write(json.dumps({'location':'user_manager.py:_init_default_admin:exists','message':'默认管理员账户已存在','data':{'username':default_admin_username,'role':self.users[default_admin_username].get('role')},'timestamp':int(datetime.now().timestamp()*1000),'sessionId':'debug-session','hypothesisId':'A'})+'\n')
                except: pass
            # #endregion
    
    def _save_users(self):
        """保存用户数据"""
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.users, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存用户数据失败: {e}")
    
    def register(self, username: str, password: str, email: str = None) -> tuple[bool, str]:
        """
        注册新用户
        
        Args:
            username: 用户名
            password: 密码
            email: 邮箱（可选）
            
        Returns:
            (是否成功, 消息)
        """
        # #region agent log
        with open('c:\\lof1\\.cursor\\debug.log', 'a', encoding='utf-8') as f:
            import json
            f.write(json.dumps({'location':'user_manager.py:register:entry','message':'开始注册验证','data':{'username':username,'usernameLength':len(username) if username else 0,'passwordLength':len(password) if password else 0},'timestamp':int(datetime.now().timestamp()*1000),'sessionId':'debug-session','hypothesisId':'1,2'})+'\n')
        # #endregion
        
        # 验证用户名（确保username不是None）
        if not username:
            # #region agent log
            with open('c:\\lof1\\.cursor\\debug.log', 'a', encoding='utf-8') as f:
                import json
                f.write(json.dumps({'location':'user_manager.py:register:username_empty','message':'用户名为空','data':{'username':username},'timestamp':int(datetime.now().timestamp()*1000),'sessionId':'debug-session','hypothesisId':'1'})+'\n')
            # #endregion
            return False, "用户名不能为空"
        
        username_stripped = username.strip() if username else ''
        if len(username_stripped) < 3:
            # #region agent log
            with open('c:\\lof1\\.cursor\\debug.log', 'a', encoding='utf-8') as f:
                import json
                f.write(json.dumps({'location':'user_manager.py:register:username_too_short','message':'用户名太短','data':{'username':username,'length':len(username_stripped)},'timestamp':int(datetime.now().timestamp()*1000),'sessionId':'debug-session','hypothesisId':'1'})+'\n')
            # #endregion
            return False, "用户名至少需要3个字符"
        
        if not username_stripped.isalnum():
            # #region agent log
            with open('c:\\lof1\\.cursor\\debug.log', 'a', encoding='utf-8') as f:
                import json
                f.write(json.dumps({'location':'user_manager.py:register:username_invalid','message':'用户名包含非法字符','data':{'username':username,'isalnum':username_stripped.isalnum()},'timestamp':int(datetime.now().timestamp()*1000),'sessionId':'debug-session','hypothesisId':'1'})+'\n')
            # #endregion
            return False, "用户名只能包含字母和数字"
        
        # 验证密码
        if not password or len(password) < 6:
            # #region agent log
            with open('c:\\lof1\\.cursor\\debug.log', 'a', encoding='utf-8') as f:
                import json
                f.write(json.dumps({'location':'user_manager.py:register:password_too_short','message':'密码太短','data':{'passwordLength':len(password) if password else 0},'timestamp':int(datetime.now().timestamp()*1000),'sessionId':'debug-session','hypothesisId':'2'})+'\n')
            # #endregion
            return False, "密码至少需要6个字符"
        
        # 增强密码强度验证
        if len(password) > 50:
            return False, "密码长度不能超过50个字符"
        
        # 检查密码是否过于简单（全为相同字符）
        if len(set(password)) == 1:
            return False, "密码不能全为相同字符"
        
        # 检查常见弱密码
        weak_passwords = ['123456', 'password', '12345678', 'qwerty', 'abc123', 'password123']
        if password.lower() in weak_passwords:
            return False, "密码过于简单，请使用更复杂的密码"
        
        # 检查用户名是否已存在
        if username in self.users:
            # #region agent log
            with open('c:\\lof1\\.cursor\\debug.log', 'a', encoding='utf-8') as f:
                import json
                f.write(json.dumps({'location':'user_manager.py:register:username_exists','message':'用户名已存在','data':{'username':username},'timestamp':int(datetime.now().timestamp()*1000),'sessionId':'debug-session','hypothesisId':'5'})+'\n')
            # #endregion
            return False, "用户名已存在"
        
        # #region agent log
        with open('c:\\lof1\\.cursor\\debug.log', 'a', encoding='utf-8') as f:
            import json
            f.write(json.dumps({'location':'user_manager.py:register:before_create','message':'创建用户前','data':{'username':username},'timestamp':int(datetime.now().timestamp()*1000),'sessionId':'debug-session'})+'\n')
        # #endregion
        
        # 创建用户
        self.users[username] = {
            'username': username,
            'password_hash': generate_password_hash(password),
            'email': email,
            'created_at': datetime.now().isoformat(),
            'last_login': None,
            'role': 'user',  # 默认为普通用户
            'favorites': [],
            'settings': {}
        }
        
        # #region agent log
        with open('c:\\lof1\\.cursor\\debug.log', 'a', encoding='utf-8') as f:
            import json
            f.write(json.dumps({'location':'user_manager.py:register:before_save','message':'保存用户前','data':{'username':username,'usersCount':len(self.users)},'timestamp':int(datetime.now().timestamp()*1000),'sessionId':'debug-session'})+'\n')
        # #endregion
        
        self._save_users()
        
        # #region agent log
        with open('c:\\lof1\\.cursor\\debug.log', 'a', encoding='utf-8') as f:
            import json
            f.write(json.dumps({'location':'user_manager.py:register:success','message':'注册成功','data':{'username':username},'timestamp':int(datetime.now().timestamp()*1000),'sessionId':'debug-session'})+'\n')
        # #endregion
        
        return True, "注册成功"
    
    def login(self, username: str, password: str) -> tuple[bool, str, Optional[Dict]]:
        """
        用户登录
        
        Args:
            username: 用户名
            password: 密码
            
        Returns:
            (是否成功, 消息, 用户信息)
        """
        # #region agent log
        import json
        log_path = _get_log_path()
        if log_path:
            try:
                with open(log_path, 'a', encoding='utf-8') as f:
                    f.write(json.dumps({'location':'user_manager.py:login:entry','message':'开始登录验证','data':{'username':username,'passwordLength':len(password) if password else 0,'usersCount':len(self.users),'userExists':username in self.users},'timestamp':int(datetime.now().timestamp()*1000),'sessionId':'debug-session','hypothesisId':'B,C,D'})+'\n')
            except: pass
        # #endregion
        
        if username not in self.users:
            # #region agent log
            log_path = _get_log_path()
            if log_path:
                try:
                    with open(log_path, 'a', encoding='utf-8') as f:
                        f.write(json.dumps({'location':'user_manager.py:login:user_not_found','message':'用户不存在','data':{'username':username,'availableUsers':list(self.users.keys())},'timestamp':int(datetime.now().timestamp()*1000),'sessionId':'debug-session','hypothesisId':'B'})+'\n')
                except: pass
            # #endregion
            return False, "用户名或密码错误", None
        
        user = self.users[username]
        
        # #region agent log
        log_path = _get_log_path()
        if log_path:
            try:
                with open(log_path, 'a', encoding='utf-8') as f:
                    f.write(json.dumps({'location':'user_manager.py:login:before_password_check','message':'开始验证密码','data':{'username':username,'hasPasswordHash':bool(user.get('password_hash')),'role':user.get('role')},'timestamp':int(datetime.now().timestamp()*1000),'sessionId':'debug-session','hypothesisId':'C'})+'\n')
            except: pass
        # #endregion
        
        # 验证密码
        password_valid = check_password_hash(user['password_hash'], password)
        
        # #region agent log
        log_path = _get_log_path()
        if log_path:
            try:
                with open(log_path, 'a', encoding='utf-8') as f:
                    f.write(json.dumps({'location':'user_manager.py:login:password_check_result','message':'密码验证结果','data':{'username':username,'passwordValid':password_valid},'timestamp':int(datetime.now().timestamp()*1000),'sessionId':'debug-session','hypothesisId':'C'})+'\n')
            except: pass
        # #endregion
        
        if not password_valid:
            # #region agent log
            log_path = _get_log_path()
            if log_path:
                try:
                    with open(log_path, 'a', encoding='utf-8') as f:
                        f.write(json.dumps({'location':'user_manager.py:login:password_invalid','message':'密码验证失败','data':{'username':username},'timestamp':int(datetime.now().timestamp()*1000),'sessionId':'debug-session','hypothesisId':'C'})+'\n')
                except: pass
            # #endregion
            return False, "用户名或密码错误", None
        
        # 更新最后登录时间
        user['last_login'] = datetime.now().isoformat()
        self._save_users()
        
        # 返回用户信息（不包含密码）
        user_info = {
            'username': user['username'],
            'email': user.get('email'),
            'created_at': user.get('created_at'),
            'last_login': user['last_login'],
            'role': user.get('role', 'user')  # 默认为普通用户
        }
        
        return True, "登录成功", user_info
    
    def get_user(self, username: str) -> Optional[Dict]:
        """
        获取用户信息
        
        Args:
            username: 用户名
            
        Returns:
            用户信息（不包含密码），如果用户不存在返回None
        """
        if username not in self.users:
            return None
        
        user = self.users[username]
        return {
            'username': user['username'],
            'email': user.get('email'),
            'created_at': user.get('created_at'),
            'last_login': user.get('last_login'),
            'role': user.get('role', 'user')  # 默认为普通用户
        }
    
    def user_exists(self, username: str) -> bool:
        """
        检查用户是否存在
        
        Args:
            username: 用户名
            
        Returns:
            是否存在
        """
        return username in self.users
    
    def get_user_favorites(self, username: str) -> List[str]:
        """
        获取用户的自选基金列表
        
        Args:
            username: 用户名
            
        Returns:
            自选基金代码列表
        """
        if username not in self.users:
            return []
        return self.users[username].get('favorites', [])
    
    def set_user_favorites(self, username: str, fund_codes: List[str]) -> bool:
        """
        设置用户的自选基金列表
        
        Args:
            username: 用户名
            fund_codes: 基金代码列表
            
        Returns:
            是否成功
        """
        if username not in self.users:
            return False
        if 'favorites' not in self.users[username]:
            self.users[username]['favorites'] = []
        self.users[username]['favorites'] = fund_codes
        self._save_users()
        return True
    
    def add_user_favorite(self, username: str, fund_code: str) -> bool:
        """
        添加自选基金
        
        Args:
            username: 用户名
            fund_code: 基金代码
            
        Returns:
            是否成功
        """
        if username not in self.users:
            return False
        if 'favorites' not in self.users[username]:
            self.users[username]['favorites'] = []
        if fund_code not in self.users[username]['favorites']:
            self.users[username]['favorites'].append(fund_code)
            self._save_users()
        return True
    
    def remove_user_favorite(self, username: str, fund_code: str) -> bool:
        """
        移除自选基金
        
        Args:
            username: 用户名
            fund_code: 基金代码
            
        Returns:
            是否成功
        """
        if username not in self.users:
            return False
        if 'favorites' not in self.users[username]:
            return True
        if fund_code in self.users[username]['favorites']:
            self.users[username]['favorites'].remove(fund_code)
            self._save_users()
        return True
    
    def get_user_settings(self, username: str) -> Dict:
        """
        获取用户的设置
        
        Args:
            username: 用户名
            
        Returns:
            用户设置字典
        """
        if username not in self.users:
            return {}
        return self.users[username].get('settings', {})
    
    def set_user_settings(self, username: str, settings: Dict) -> bool:
        """
        设置用户的设置
        
        Args:
            username: 用户名
            settings: 设置字典
            
        Returns:
            是否成功
        """
        if username not in self.users:
            return False
        if 'settings' not in self.users[username]:
            self.users[username]['settings'] = {}
        self.users[username]['settings'].update(settings)
        self._save_users()
        return True
    
    def list_all_users(self) -> List[Dict]:
        """
        获取所有用户列表（不包含密码）
        
        Returns:
            用户列表
        """
        users_list = []
        for username, user_data in self.users.items():
            users_list.append({
                'username': username,
                'email': user_data.get('email'),
                'role': user_data.get('role', 'user'),
                'created_at': user_data.get('created_at'),
                'last_login': user_data.get('last_login')
            })
        return users_list
    
    def update_user_role(self, username: str, role: str) -> bool:
        """
        更新用户角色
        
        Args:
            username: 用户名
            role: 角色（'admin' 或 'user'）
            
        Returns:
            是否成功
        """
        if username not in self.users:
            return False
        if role not in ['admin', 'user']:
            return False
        self.users[username]['role'] = role
        self._save_users()
        return True
    
    def update_user_email(self, username: str, email: str) -> bool:
        """
        更新用户邮箱
        
        Args:
            username: 用户名
            email: 邮箱
            
        Returns:
            是否成功
        """
        if username not in self.users:
            return False
        self.users[username]['email'] = email
        self._save_users()
        return True
    
    def reset_user_password(self, username: str, new_password: str) -> bool:
        """
        重置用户密码（管理员功能）
        
        Args:
            username: 用户名
            new_password: 新密码
            
        Returns:
            是否成功
        """
        if username not in self.users:
            return False
        if len(new_password) < 6:
            return False
        self.users[username]['password_hash'] = generate_password_hash(new_password)
        self._save_users()
        return True
    
    def delete_user(self, username: str) -> bool:
        """
        删除用户（管理员功能）
        
        Args:
            username: 用户名
            
        Returns:
            是否成功
        """
        if username not in self.users:
            return False
        del self.users[username]
        self._save_users()
        return True
