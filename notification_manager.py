# -*- coding: utf-8 -*-
"""
通知管理模块
处理站内信通知的创建、存储和管理
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional


class NotificationType:
    """通知类型"""
    ARBITRAGE_OPPORTUNITY = "arbitrage_opportunity"  # 套利机会
    ARBITRAGE_COMPLETED = "arbitrage_completed"  # 套利完成
    ARBITRAGE_SELL = "arbitrage_sell"  # 套利卖出提醒
    SYSTEM = "system"  # 系统通知
    USER = "user"  # 用户相关通知


class NotificationManager:
    """通知管理器"""
    
    def __init__(self, data_file: str = "notifications.json"):
        """
        初始化通知管理器
        
        Args:
            data_file: 通知数据文件路径
        """
        self.data_file = data_file
        self.notifications = self._load_notifications()
    
    def _load_notifications(self) -> Dict[str, List[Dict]]:
        """加载通知数据（按用户组织）"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"加载通知数据失败: {e}")
                return {}
        return {}
    
    def _save_notifications(self):
        """保存通知数据"""
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.notifications, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存通知数据失败: {e}")
    
    def _get_user_notifications(self, username: str) -> List[Dict]:
        """获取用户的通知列表"""
        if username not in self.notifications:
            self.notifications[username] = []
        return self.notifications[username]
    
    def create_notification(self, username: str, notification_type: str, title: str, 
                           content: str, data: Dict = None) -> str:
        """
        创建通知
        
        Args:
            username: 用户名
            notification_type: 通知类型
            title: 通知标题
            content: 通知内容
            data: 附加数据
            
        Returns:
            通知ID
        """
        import uuid
        notification_id = str(uuid.uuid4())
        
        notification = {
            'id': notification_id,
            'type': notification_type,
            'title': title,
            'content': content,
            'data': data or {},
            'read': False,
            'created_at': datetime.now().isoformat(),
            'read_at': None
        }
        
        user_notifications = self._get_user_notifications(username)
        user_notifications.insert(0, notification)  # 新通知插入到最前面
        
        # 限制每个用户最多保留500条通知
        if len(user_notifications) > 500:
            user_notifications[:] = user_notifications[:500]
        
        self._save_notifications()
        return notification_id
    
    def get_notifications(self, username: str, unread_only: bool = False, 
                         limit: int = None) -> List[Dict]:
        """
        获取用户的通知列表
        
        Args:
            username: 用户名
            unread_only: 是否只获取未读通知
            limit: 限制返回数量
            
        Returns:
            通知列表
        """
        notifications = self._get_user_notifications(username)
        
        if unread_only:
            notifications = [n for n in notifications if not n.get('read', False)]
        
        if limit:
            notifications = notifications[:limit]
        
        return notifications
    
    def get_unread_count(self, username: str) -> int:
        """
        获取未读通知数量
        
        Args:
            username: 用户名
            
        Returns:
            未读通知数量
        """
        notifications = self._get_user_notifications(username)
        return sum(1 for n in notifications if not n.get('read', False))
    
    def mark_as_read(self, username: str, notification_id: str) -> bool:
        """
        标记通知为已读
        
        Args:
            username: 用户名
            notification_id: 通知ID
            
        Returns:
            是否成功
        """
        notifications = self._get_user_notifications(username)
        for notification in notifications:
            if notification['id'] == notification_id:
                notification['read'] = True
                notification['read_at'] = datetime.now().isoformat()
                self._save_notifications()
                return True
        return False
    
    def mark_all_as_read(self, username: str) -> bool:
        """
        标记所有通知为已读
        
        Args:
            username: 用户名
            
        Returns:
            是否成功
        """
        notifications = self._get_user_notifications(username)
        updated = False
        for notification in notifications:
            if not notification.get('read', False):
                notification['read'] = True
                notification['read_at'] = datetime.now().isoformat()
                updated = True
        
        if updated:
            self._save_notifications()
        return updated
    
    def delete_notification(self, username: str, notification_id: str) -> bool:
        """
        删除通知
        
        Args:
            username: 用户名
            notification_id: 通知ID
            
        Returns:
            是否成功
        """
        notifications = self._get_user_notifications(username)
        for i, notification in enumerate(notifications):
            if notification['id'] == notification_id:
                notifications.pop(i)
                self._save_notifications()
                return True
        return False
    
    def delete_all_read(self, username: str) -> int:
        """
        删除所有已读通知
        
        Args:
            username: 用户名
            
        Returns:
            删除的数量
        """
        notifications = self._get_user_notifications(username)
        original_count = len(notifications)
        notifications[:] = [n for n in notifications if not n.get('read', False)]
        deleted_count = original_count - len(notifications)
        
        if deleted_count > 0:
            self._save_notifications()
        
        return deleted_count
