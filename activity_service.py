#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用户活动记录服务
"""

from datetime import datetime, date
from typing import Dict, List, Any
from db_service import get_database_connection

def record_activity(user_id: str, activity_type: str, title: str, description: str = "", metadata: Dict = None):
    """记录用户活动"""
    connection = get_database_connection()
    try:
        with connection.cursor() as cursor:
            # 创建活动记录表（如果不存在）
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_activities (
                    id BIGINT AUTO_INCREMENT PRIMARY KEY,
                    user_id VARCHAR(50) NOT NULL,
                    activity_type VARCHAR(50) NOT NULL,
                    title VARCHAR(200) NOT NULL,
                    description TEXT,
                    metadata JSON,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_user_id (user_id),
                    INDEX idx_created_at (created_at),
                    INDEX idx_activity_type (activity_type)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)
            
            # 插入活动记录
            import json
            metadata_json = json.dumps(metadata) if metadata else None
            cursor.execute("""
                INSERT INTO user_activities (user_id, activity_type, title, description, metadata)
                VALUES (%s, %s, %s, %s, %s)
            """, (user_id, activity_type, title, description, metadata_json))
            
            connection.commit()
            print(f"[ACTIVITY] Recorded: {activity_type} - {title} for user {user_id}")
            
    except Exception as e:
        print(f"[ERROR] Failed to record activity: {e}")
        connection.rollback()
    finally:
        connection.close()

def get_user_activities(user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
    """获取用户最近活动"""
    connection = get_database_connection()
    try:
        with connection.cursor() as cursor:
            # 确保表存在
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_activities (
                    id BIGINT AUTO_INCREMENT PRIMARY KEY,
                    user_id VARCHAR(50) NOT NULL,
                    activity_type VARCHAR(50) NOT NULL,
                    title VARCHAR(200) NOT NULL,
                    description TEXT,
                    metadata JSON,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_user_id (user_id),
                    INDEX idx_created_at (created_at),
                    INDEX idx_activity_type (activity_type)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)
            
            cursor.execute("""
                SELECT activity_type, title, description, metadata, created_at
                FROM user_activities 
                WHERE user_id = %s 
                ORDER BY created_at DESC 
                LIMIT %s
            """, (user_id, limit))
            
            activities = []
            for row in cursor.fetchall():
                activity_type, title, description, metadata, created_at = row
                
                # 根据活动类型设置图标
                icon_map = {
                    'pomodoro': '🍅',
                    'achievement': '🏆',
                    'material_upload': '📄',
                    'ai_chat': '🤖',
                    'plan_create': '📝',
                    'card_generate': '🃏',
                    'login': '🔑',
                    'quiz': '📝'
                }
                
                # 格式化时间
                if created_at:
                    now = datetime.now()
                    time_diff = now - created_at
                    if time_diff.days > 0:
                        time_str = f"{time_diff.days}天前"
                    elif time_diff.seconds > 3600:
                        time_str = f"{time_diff.seconds // 3600}小时前"
                    elif time_diff.seconds > 60:
                        time_str = f"{time_diff.seconds // 60}分钟前"
                    else:
                        time_str = "刚刚"
                else:
                    time_str = "未知时间"
                
                activities.append({
                    'icon': icon_map.get(activity_type, '📌'),
                    'title': title,
                    'description': description or '',
                    'time': time_str,
                    'type': activity_type,
                    'created_at': created_at.isoformat() if created_at else None
                })
            
            return activities
            
    except Exception as e:
        print(f"[ERROR] Failed to get user activities: {e}")
        return []
    finally:
        connection.close()

def get_activity_stats(user_id: str) -> Dict[str, Any]:
    """获取用户活动统计"""
    connection = get_database_connection()
    try:
        with connection.cursor() as cursor:
            today = date.today()
            
            # 今日活动统计
            cursor.execute("""
                SELECT activity_type, COUNT(*) 
                FROM user_activities 
                WHERE user_id = %s AND DATE(created_at) = %s 
                GROUP BY activity_type
            """, (user_id, today))
            
            today_stats = {row[0]: row[1] for row in cursor.fetchall()}
            
            # 总活动统计
            cursor.execute("""
                SELECT activity_type, COUNT(*) 
                FROM user_activities 
                WHERE user_id = %s 
                GROUP BY activity_type
            """, (user_id,))
            
            total_stats = {row[0]: row[1] for row in cursor.fetchall()}
            
            return {
                'today': today_stats,
                'total': total_stats,
                'today_total': sum(today_stats.values()),
                'all_time_total': sum(total_stats.values())
            }
            
    except Exception as e:
        print(f"[ERROR] Failed to get activity stats: {e}")
        return {'today': {}, 'total': {}, 'today_total': 0, 'all_time_total': 0}
    finally:
        connection.close()

# 便捷记录函数
def record_pomodoro_activity(user_id: str, session_id: int, actual_minutes: int):
    """记录番茄钟活动"""
    record_activity(
        user_id=user_id,
        activity_type='pomodoro',
        title='完成专注学习',
        description=f'专注学习{actual_minutes}分钟',
        metadata={'session_id': session_id, 'duration': actual_minutes}
    )

def record_material_upload_activity(user_id: str, filename: str, course_name: str = ""):
    """记录资料上传活动"""
    record_activity(
        user_id=user_id,
        activity_type='material_upload',
        title='上传学习资料',
        description=f'上传了《{filename}》{f" 到{course_name}课程" if course_name else ""}',
        metadata={'filename': filename, 'course': course_name}
    )

def record_ai_chat_activity(user_id: str, message_count: int = 1):
    """记录AI聊天活动"""
    record_activity(
        user_id=user_id,
        activity_type='ai_chat',
        title='AI智能对话',
        description=f'与AI助手进行了学习交流',
        metadata={'message_count': message_count}
    )

def record_plan_create_activity(user_id: str, plan_title: str):
    """记录计划创建活动"""
    record_activity(
        user_id=user_id,
        activity_type='plan_create',
        title='制定学习计划',
        description=f'创建了学习计划：{plan_title}',
        metadata={'plan_title': plan_title}
    )

def record_card_generate_activity(user_id: str, material_name: str, card_count: int = 3):
    """记录卡片生成活动"""
    record_activity(
        user_id=user_id,
        activity_type='card_generate',
        title='生成知识卡片',
        description=f'为《{material_name}》生成了{card_count}张学习卡片',
        metadata={'material': material_name, 'card_count': card_count}
    )

def record_achievement_activity(user_id: str, achievement_name: str):
    """记录成就解锁活动"""
    record_activity(
        user_id=user_id,
        activity_type='achievement',
        title='解锁新成就',
        description=f'获得了"{achievement_name}"成就',
        metadata={'achievement': achievement_name}
    )

def record_login_activity(user_id: str):
    """记录登录活动"""
    record_activity(
        user_id=user_id,
        activity_type='login',
        title='登录系统',
        description='开始新的学习旅程',
        metadata={}
    )
