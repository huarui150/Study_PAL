#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库服务模块 - 替换所有内存存储为数据库存储
"""

import pymysql
from datetime import datetime, date
from typing import Dict, Any, List, Optional
import json

# 数据库配置
DB_CONFIG = {
    'host': '141.11.90.223',
    'port': 3307,
    'user': 'root',
    'password': '7539518426',
    'database': 'study_pal',
    'charset': 'utf8mb4',
    'autocommit': False
}

def get_database_connection():
    """获取数据库连接"""
    return pymysql.connect(**DB_CONFIG)

# ==================== 番茄钟会话相关 ====================

def create_pomodoro_session(user_id: str, plan_id: int = None, focus_minutes: int = 25) -> int:
    """创建番茄钟会话"""
    connection = get_database_connection()
    try:
        with connection.cursor() as cursor:
            session_id = int(datetime.now().timestamp() * 1000)  # 使用时间戳作为ID
            cursor.execute("""
                INSERT INTO pomodoro_sessions (id, user_id, plan_id, start_at, focus_minutes, status)
                VALUES (%s, %s, %s, %s, %s, 'active')
            """, (session_id, user_id, plan_id, datetime.now(), focus_minutes))
            connection.commit()
            print(f"[DB] Created pomodoro session {session_id} for user {user_id}")
            return session_id
    except Exception as e:
        print(f"[DB ERROR] Failed to create session: {e}")
        connection.rollback()
        raise e
    finally:
        connection.close()

def complete_pomodoro_session(session_id: int, emotion: str = None, note: str = None, actual_minutes: int = 25) -> Dict[str, Any]:
    """完成番茄钟会话"""
    connection = get_database_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                UPDATE pomodoro_sessions 
                SET status = 'completed', end_at = %s, emotion = %s, note = %s, actual_minutes = %s
                WHERE id = %s
            """, (datetime.now(), emotion, note, actual_minutes, session_id))
            
            if cursor.rowcount > 0:
                connection.commit()
                print(f"[DB] Completed pomodoro session {session_id} with {actual_minutes} minutes")
                
                # 记录情绪到专门的表
                if emotion:
                    cursor.execute("SELECT user_id FROM pomodoro_sessions WHERE id = %s", (session_id,))
                    result = cursor.fetchone()
                    if result:
                        record_emotion_db(result[0], emotion, note)
                
                return {
                    "session_id": session_id,
                    "completed": True,
                    "actual_minutes": actual_minutes
                }
            else:
                return {"error": "会话未找到"}
    except Exception as e:
        print(f"[DB ERROR] Failed to complete session: {e}")
        connection.rollback()
        raise e
    finally:
        connection.close()

def interrupt_pomodoro_session(session_id: int, reason: str = None) -> Dict[str, Any]:
    """中断番茄钟会话"""
    connection = get_database_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                UPDATE pomodoro_sessions 
                SET status = 'interrupted', end_at = %s, interrupted_reason = %s
                WHERE id = %s
            """, (datetime.now(), reason, session_id))
            
            if cursor.rowcount > 0:
                connection.commit()
                print(f"[DB] Interrupted pomodoro session {session_id}, reason: {reason}")
                return {"session_id": session_id, "interrupted": True}
            else:
                return {"error": "会话未找到"}
    except Exception as e:
        print(f"[DB ERROR] Failed to interrupt session: {e}")
        connection.rollback()
        raise e
    finally:
        connection.close()

def get_user_pomodoro_stats(user_id: str) -> Dict[str, Any]:
    """获取用户番茄钟统计"""
    connection = get_database_connection()
    try:
        with connection.cursor() as cursor:
            today = date.today()
            
            # 今日完成的番茄钟
            cursor.execute("""
                SELECT COUNT(*), COALESCE(SUM(actual_minutes), 0)
                FROM pomodoro_sessions 
                WHERE user_id = %s AND DATE(start_at) = %s AND status = 'completed'
            """, (user_id, today))
            today_result = cursor.fetchone()
            today_pomodoros = int(today_result[0]) if today_result else 0
            today_focus_time = int(today_result[1]) if today_result else 0
            
            # 总的完成统计
            cursor.execute("""
                SELECT COUNT(*), COALESCE(SUM(actual_minutes), 0)
                FROM pomodoro_sessions 
                WHERE user_id = %s AND status = 'completed'
            """, (user_id,))
            total_result = cursor.fetchone()
            total_sessions = int(total_result[0]) if total_result else 0
            total_focus_time = int(total_result[1]) if total_result else 0
            
            return {
                "today_pomodoros": today_pomodoros,
                "today_focus_time": today_focus_time,
                "total_sessions": total_sessions,
                "total_focus_time": total_focus_time
            }
    except Exception as e:
        print(f"[DB ERROR] Failed to get pomodoro stats: {e}")
        return {"today_pomodoros": 0, "today_focus_time": 0, "total_sessions": 0, "total_focus_time": 0}
    finally:
        connection.close()

# ==================== 成就相关 ====================

def unlock_achievement_db(user_id: str, achievement_id: str) -> Optional[Dict[str, Any]]:
    """解锁成就"""
    connection = get_database_connection()
    try:
        with connection.cursor() as cursor:
            # 检查是否已经解锁
            cursor.execute("""
                SELECT id FROM user_achievements 
                WHERE user_id = %s AND achievement_id = %s
            """, (user_id, achievement_id))
            
            if cursor.fetchone():
                print(f"[DB] Achievement {achievement_id} already unlocked for user {user_id}")
                return None
            
            # 获取成就信息
            cursor.execute("SELECT name, description, points FROM achievements WHERE id = %s", (achievement_id,))
            achievement = cursor.fetchone()
            
            if not achievement:
                print(f"[DB] Achievement {achievement_id} not found")
                return None
            
            # 解锁成就
            cursor.execute("""
                INSERT INTO user_achievements (user_id, achievement_id, unlocked_at)
                VALUES (%s, %s, %s)
            """, (user_id, achievement_id, datetime.now()))
            
            # 奖励StudyCoin
            reward_coins_db(user_id, achievement[2], f"解锁成就: {achievement[0]}")
            
            connection.commit()
            print(f"[DB] Unlocked achievement {achievement_id} for user {user_id}")
            
            return {
                "event": "achievement.unlocked",
                "achievement": {
                    "id": achievement_id,
                    "name": achievement[0],
                    "description": achievement[1],
                    "points": achievement[2]
                }
            }
    except Exception as e:
        print(f"[DB ERROR] Failed to unlock achievement: {e}")
        connection.rollback()
        return None
    finally:
        connection.close()

def get_user_achievements_db(user_id: str) -> Dict[str, Any]:
    """获取用户成就"""
    connection = get_database_connection()
    try:
        with connection.cursor() as cursor:
            # 获取已解锁的成就
            cursor.execute("""
                SELECT a.id, a.name, a.description, a.category, a.points, a.icon, ua.unlocked_at
                FROM user_achievements ua
                JOIN achievements a ON ua.achievement_id = a.id
                WHERE ua.user_id = %s
                ORDER BY ua.unlocked_at DESC
            """, (user_id,))
            
            achievements = []
            for row in cursor.fetchall():
                achievements.append({
                    "id": row[0],
                    "name": row[1],
                    "description": row[2],
                    "category": row[3],
                    "points": row[4],
                    "icon": row[5],
                    "unlocked_at": row[6].isoformat() if row[6] else None
                })
            
            # 获取用户统计
            stats = get_user_stats_db(user_id)
            
            return {
                "achievements": achievements,
                "stats": stats,
                "studycoin": stats.get("studycoin_balance", 0)
            }
    except Exception as e:
        print(f"[DB ERROR] Failed to get user achievements: {e}")
        return {"achievements": [], "stats": {}, "studycoin": 0}
    finally:
        connection.close()

def check_achievements_db(user_id: str) -> List[Dict[str, Any]]:
    """
    基于数据库的成就检测
    检查用户是否满足成就解锁条件
    """
    connection = get_database_connection()
    try:
        with connection.cursor() as cursor:
            events = []

            # 获取所有成就定义
            cursor.execute("SELECT id, name, condition_type, condition_params FROM achievements")
            achievements = cursor.fetchall()

            for achievement_row in achievements:
                achievement_id, name, condition_type, condition_params = achievement_row

                # 检查是否已经解锁
                cursor.execute("""
                    SELECT id FROM user_achievements
                    WHERE user_id = %s AND achievement_id = %s
                """, (user_id, achievement_id))

                if cursor.fetchone():
                    continue  # 已经解锁，跳过

                # 根据条件类型检查是否满足解锁条件
                should_unlock = check_achievement_condition_db(cursor, user_id, condition_type, condition_params)

                if should_unlock:
                    # 解锁成就
                    unlock_event = unlock_achievement_db(user_id, achievement_id)
                    if unlock_event:
                        events.append(unlock_event)

            connection.commit()
            return events

    except Exception as e:
        print(f"[DB ERROR] Failed to check achievements: {e}")
        connection.rollback()
        return []
    finally:
        connection.close()

def check_achievement_condition_db(cursor, user_id: str, condition_type: str, condition_params: str) -> bool:
    """
    检查成就解锁条件（数据库版本）
    """
    try:
        params = json.loads(condition_params) if condition_params else {}
    except:
        params = {}

    if condition_type == "first_login":
        # 首次登录 - 简化处理，假设注册用户都满足
        return True

    elif condition_type == "consecutive_pomodoros":
        days = params.get("days", 7)
        min_pomodoros = params.get("min_pomodoros_per_day", 3)
        return check_consecutive_pomodoros_db(cursor, user_id, days, min_pomodoros)

    elif condition_type == "daily_focus_minutes":
        minutes = params.get("minutes", 120)
        return check_daily_focus_minutes_db(cursor, user_id, minutes)

    elif condition_type == "cards_generated":
        count = params.get("count", 10)
        return check_cards_generated_db(cursor, user_id, count)

    elif condition_type == "materials_uploaded":
        count = params.get("count", 20)
        return check_materials_uploaded_db(cursor, user_id, count)

    elif condition_type == "perfect_quiz_score":
        return check_perfect_quiz_score_db(cursor, user_id)

    elif condition_type == "quiz_accuracy":
        accuracy = params.get("accuracy", 90)
        recent_count = params.get("recent_count", 3)
        return check_quiz_accuracy_db(cursor, user_id, accuracy, recent_count)

    elif condition_type == "consecutive_reviews":
        days = params.get("days", 7)
        return check_consecutive_reviews_db(cursor, user_id, days)

    elif condition_type == "consecutive_emotions":
        count = params.get("count", 5)
        return check_consecutive_emotions_db(cursor, user_id, count)

    elif condition_type == "positive_emotion_ratio":
        emoji = params.get("emoji", "😄")
        days = params.get("days", 7)
        ratio = params.get("ratio", 50)
        return check_positive_emotion_ratio_db(cursor, user_id, emoji, days, ratio)

    return False

def check_consecutive_pomodoros_db(cursor, user_id: str, days: int, min_pomodoros: int) -> bool:
    """检查连续天数完成番茄钟（数据库版本）"""
    try:
        # 获取最近几天的会话数据
        cursor.execute("""
            SELECT DATE(end_at), COUNT(*) as count
            FROM pomodoro_sessions
            WHERE user_id = %s AND end_at IS NOT NULL AND interrupted = FALSE
            AND end_at >= DATE_SUB(NOW(), INTERVAL %s DAY)
            GROUP BY DATE(end_at)
            ORDER BY DATE(end_at) DESC
        """, (user_id, days))

        daily_sessions = {row[0]: row[1] for row in cursor.fetchall()}

        # 检查最近几天是否都满足条件
        today = datetime.now().date()
        for i in range(days):
            check_date = (today - timedelta(days=i)).isoformat()
            if daily_sessions.get(check_date, 0) < min_pomodoros:
                return False
        return True
    except:
        return False

def check_daily_focus_minutes_db(cursor, user_id: str, minutes: int) -> bool:
    """检查单日专注时间（数据库版本）"""
    try:
        cursor.execute("""
            SELECT SUM(duration_minutes) as total_minutes
            FROM pomodoro_sessions
            WHERE user_id = %s AND DATE(end_at) = CURDATE()
            AND end_at IS NOT NULL AND interrupted = FALSE
        """, (user_id,))

        result = cursor.fetchone()
        return result and result[0] and result[0] >= minutes
    except:
        return False

def check_cards_generated_db(cursor, user_id: str, count: int) -> bool:
    """检查生成的卡片数量（数据库版本）"""
    try:
        cursor.execute("""
            SELECT COUNT(*) as card_count
            FROM cards
            WHERE user_id = %s
        """, (user_id,))

        result = cursor.fetchone()
        return result and result[0] and result[0] >= count
    except:
        return False

def check_materials_uploaded_db(cursor, user_id: str, count: int) -> bool:
    """检查上传的资料数量（数据库版本）"""
    try:
        cursor.execute("""
            SELECT COUNT(*) as material_count
            FROM materials
            WHERE user_id = %s
        """, (user_id,))

        result = cursor.fetchone()
        return result and result[0] and result[0] >= count
    except:
        return False

def check_perfect_quiz_score_db(cursor, user_id: str) -> bool:
    """检查是否有满分测验（数据库版本）"""
    try:
        cursor.execute("""
            SELECT COUNT(*) as perfect_count
            FROM quiz_results
            WHERE user_id = %s AND score = 100
        """, (user_id,))

        result = cursor.fetchone()
        return result and result[0] and result[0] > 0
    except:
        return False

def check_quiz_accuracy_db(cursor, user_id: str, accuracy: int, recent_count: int) -> bool:
    """检查测验正确率（数据库版本）"""
    try:
        cursor.execute("""
            SELECT accuracy
            FROM quiz_results
            WHERE user_id = %s
            ORDER BY completed_at DESC
            LIMIT %s
        """, (user_id, recent_count))

        results = cursor.fetchall()
        if len(results) < recent_count:
            return False

        avg_accuracy = sum(row[0] for row in results) / len(results)
        return avg_accuracy >= accuracy
    except:
        return False

def check_consecutive_reviews_db(cursor, user_id: str, days: int) -> bool:
    """检查连续复盘天数（数据库版本）"""
    try:
        # 这里需要根据实际的复盘记录表来实现
        # 暂时使用简化逻辑
        cursor.execute("""
            SELECT COUNT(DISTINCT DATE(created_at)) as review_days
            FROM activity_logs
            WHERE user_id = %s AND activity_type = 'review'
            AND created_at >= DATE_SUB(NOW(), INTERVAL %s DAY)
        """, (user_id, days))

        result = cursor.fetchone()
        return result and result[0] and result[0] >= days
    except:
        return False

def check_consecutive_emotions_db(cursor, user_id: str, count: int) -> bool:
    """检查连续情绪打卡（数据库版本）"""
    try:
        cursor.execute("""
            SELECT COUNT(*) as emotion_count
            FROM emotions
            WHERE user_id = %s
            AND created_at >= DATE_SUB(NOW(), INTERVAL %s DAY)
        """, (user_id, count))

        result = cursor.fetchone()
        return result and result[0] and result[0] >= count
    except:
        return False

def check_positive_emotion_ratio_db(cursor, user_id: str, emoji: str, days: int, ratio: int) -> bool:
    """检查积极情绪比例（数据库版本）"""
    try:
        cursor.execute("""
            SELECT emotion, COUNT(*) as count
            FROM emotions
            WHERE user_id = %s
            AND created_at >= DATE_SUB(NOW(), INTERVAL %s DAY)
            GROUP BY emotion
        """, (user_id, days))

        emotion_counts = {row[0]: row[1] for row in cursor.fetchall()}
        total_emotions = sum(emotion_counts.values())

        if total_emotions == 0:
            return False

        positive_count = emotion_counts.get(emoji, 0)
        positive_ratio = (positive_count / total_emotions) * 100

        return positive_ratio >= ratio
    except:
        return False

def reward_coins_db(user_id: str, amount: int, reason: str = ""):
    """奖励StudyCoin"""
    connection = get_database_connection()
    try:
        with connection.cursor() as cursor:
            # 记录StudyCoin变化
            cursor.execute("""
                INSERT INTO studycoin_records (user_id, amount, reason)
                VALUES (%s, %s, %s)
            """, (user_id, amount, reason))
            
            # 更新用户余额
            cursor.execute("""
                INSERT INTO user_stats (user_id, studycoin_balance) 
                VALUES (%s, %s)
                ON DUPLICATE KEY UPDATE studycoin_balance = studycoin_balance + %s
            """, (user_id, amount, amount))
            
            connection.commit()
            print(f"[DB] Rewarded {amount} coins to user {user_id}, reason: {reason}")
    except Exception as e:
        print(f"[DB ERROR] Failed to reward coins: {e}")
        connection.rollback()
    finally:
        connection.close()

# ==================== 任务相关 ====================

def update_task_progress_db(user_id: str, task_id: str, progress: int = 1) -> Optional[Dict[str, Any]]:
    """更新任务进度"""
    connection = get_database_connection()
    try:
        with connection.cursor() as cursor:
            today = date.today()
            
            # 获取或创建任务进度
            cursor.execute("""
                INSERT INTO user_task_progress (user_id, task_id, progress, date)
                VALUES (%s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE progress = progress + %s
            """, (user_id, task_id, progress, today, progress))
            
            # 检查任务是否完成
            cursor.execute("""
                SELECT progress FROM user_task_progress 
                WHERE user_id = %s AND task_id = %s AND date = %s
            """, (user_id, task_id, today))
            
            result = cursor.fetchone()
            current_progress = result[0] if result else 0
            
            # 任务目标（这里简化为固定值，实际应该从任务配置中获取）
            task_targets = {
                "daily_1": 4,    # 每日完成4个番茄
                "daily_2": 1,    # 每日做1次测验
                "daily_3": 1     # 每日上传1份资料
            }
            
            target = task_targets.get(task_id, 1)
            
            if current_progress >= target:
                # 标记为完成
                cursor.execute("""
                    UPDATE user_task_progress 
                    SET completed = TRUE 
                    WHERE user_id = %s AND task_id = %s AND date = %s AND completed = FALSE
                """, (user_id, task_id, today))
                
                if cursor.rowcount > 0:  # 首次完成
                    reward_amount = 10  # 任务奖励
                    reward_coins_db(user_id, reward_amount, f"完成每日任务: {task_id}")
                    
                    connection.commit()
                    print(f"[DB] Task {task_id} completed for user {user_id}")
                    
                    return {
                        "event": "task.completed",
                        "task_id": task_id,
                        "reward": reward_amount
                    }
            
            connection.commit()
            return None
    except Exception as e:
        print(f"[DB ERROR] Failed to update task progress: {e}")
        connection.rollback()
        return None
    finally:
        connection.close()

def get_user_tasks_db(user_id: str) -> Dict[str, Any]:
    """获取用户任务"""
    connection = get_database_connection()
    try:
        with connection.cursor() as cursor:
            today = date.today()
            
            # 获取今日任务进度
            cursor.execute("""
                SELECT task_id, progress, completed
                FROM user_task_progress 
                WHERE user_id = %s AND date = %s
            """, (user_id, today))
            
            task_progress = {row[0]: {"progress": row[1], "completed": row[2]} for row in cursor.fetchall()}
            
            # 构建任务列表
            tasks = [
                {
                    "id": "daily_1",
                    "name": "完成4个番茄钟",
                    "description": "今日完成至少4个番茄钟专注",
                    "type": "daily",
                    "target": 4,
                    "progress": task_progress.get("daily_1", {}).get("progress", 0),
                    "completed": task_progress.get("daily_1", {}).get("completed", False),
                    "reward": 10
                },
                {
                    "id": "daily_2", 
                    "name": "完成1次测验",
                    "description": "今日完成至少1次学习测验",
                    "type": "daily",
                    "target": 1,
                    "progress": task_progress.get("daily_2", {}).get("progress", 0),
                    "completed": task_progress.get("daily_2", {}).get("completed", False),
                    "reward": 10
                },
                {
                    "id": "daily_3",
                    "name": "上传1份资料",
                    "description": "今日上传至少1份学习资料",
                    "type": "daily",
                    "target": 1,
                    "progress": task_progress.get("daily_3", {}).get("progress", 0),
                    "completed": task_progress.get("daily_3", {}).get("completed", False),
                    "reward": 10
                }
            ]
            
            return {"daily_tasks": tasks}
    except Exception as e:
        print(f"[DB ERROR] Failed to get user tasks: {e}")
        return {"daily_tasks": []}
    finally:
        connection.close()

# ==================== 用户统计相关 ====================

def get_user_stats_db(user_id: str) -> Dict[str, Any]:
    """获取用户统计"""
    connection = get_database_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT studycoin_balance, login_streak, last_login_date, total_focus_time, total_pomodoros
                FROM user_stats WHERE user_id = %s
            """, (user_id,))
            
            result = cursor.fetchone()
            if result:
                return {
                    "studycoin_balance": result[0],
                    "login_streak": result[1],
                    "last_login_date": result[2].isoformat() if result[2] else None,
                    "total_focus_time": result[3],
                    "total_pomodoros": result[4]
                }
            else:
                return {
                    "studycoin_balance": 0,
                    "login_streak": 0,
                    "last_login_date": None,
                    "total_focus_time": 0,
                    "total_pomodoros": 0
                }
    except Exception as e:
        print(f"[DB ERROR] Failed to get user stats: {e}")
        return {}
    finally:
        connection.close()

def update_login_streak_db(user_id: str):
    """更新登录连续天数"""
    connection = get_database_connection()
    try:
        with connection.cursor() as cursor:
            today = date.today()
            
            cursor.execute("""
                SELECT last_login_date, login_streak FROM user_stats WHERE user_id = %s
            """, (user_id,))
            
            result = cursor.fetchone()
            
            if result:
                last_login = result[0]
                current_streak = result[1]
                
                if last_login == today:
                    return  # 今天已经登录过
                
                if last_login and (today - last_login).days == 1:
                    # 连续登录
                    new_streak = current_streak + 1
                else:
                    # 重新开始
                    new_streak = 1
                
                cursor.execute("""
                    UPDATE user_stats 
                    SET last_login_date = %s, login_streak = %s
                    WHERE user_id = %s
                """, (today, new_streak, user_id))
            else:
                # 首次登录
                cursor.execute("""
                    INSERT INTO user_stats (user_id, last_login_date, login_streak)
                    VALUES (%s, %s, 1)
                """, (user_id, today))
            
            connection.commit()
            print(f"[DB] Updated login streak for user {user_id}")
    except Exception as e:
        print(f"[DB ERROR] Failed to update login streak: {e}")
        connection.rollback()
    finally:
        connection.close()

# ==================== 情绪记录相关 ====================

def record_emotion_db(user_id: str, emotion: str, note: str = None):
    """记录情绪"""
    connection = get_database_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO emotion_records (user_id, emotion, note)
                VALUES (%s, %s, %s)
            """, (user_id, emotion, note))
            connection.commit()
            print(f"[DB] Recorded emotion {emotion} for user {user_id}")
    except Exception as e:
        print(f"[DB ERROR] Failed to record emotion: {e}")
        connection.rollback()
    finally:
        connection.close()

# ==================== 学习计划相关 ====================

def create_learning_plan_db(user_id: str, title: str, course_id: str, topic: str, 
                           estimate_min: int, difficulty: int, importance: int, deadline: str) -> int:
    """创建学习计划"""
    connection = get_database_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO learning_plans (user_id, title, course_id, topic, estimate_min, difficulty, importance, deadline)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (user_id, title, course_id, topic, estimate_min, difficulty, importance, deadline))
            
            plan_id = cursor.lastrowid
            connection.commit()
            print(f"[DB] Created learning plan {plan_id} for user {user_id}")
            return plan_id
    except Exception as e:
        print(f"[DB ERROR] Failed to create learning plan: {e}")
        connection.rollback()
        raise e
    finally:
        connection.close()

def get_user_plans_db(user_id: str) -> List[Dict[str, Any]]:
    """获取用户学习计划"""
    connection = get_database_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT id, title, course_id, topic, estimate_min, difficulty, importance, deadline, status, created_at
                FROM learning_plans 
                WHERE user_id = %s 
                ORDER BY created_at DESC
            """, (user_id,))
            
            plans = []
            for row in cursor.fetchall():
                plans.append({
                    "id": row[0],
                    "title": row[1],
                    "course_id": row[2],
                    "topic": row[3],
                    "estimate_min": row[4],
                    "difficulty": row[5],
                    "importance": row[6],
                    "deadline": row[7].isoformat() if row[7] else None,
                    "status": row[8],
                    "created_at": row[9].isoformat() if row[9] else None
                })
            
            return plans
    except Exception as e:
        print(f"[DB ERROR] Failed to get user plans: {e}")
        return []
    finally:
        connection.close()

def record_activity_db(user_id: str, activity_type: str, title: str, description: str = "", metadata: Dict = None):
    """记录用户活动到数据库"""
    connection = get_database_connection()
    try:
        with connection.cursor() as cursor:
            # 确保活动表存在
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
            print(f"[DB] Recorded activity: {activity_type} - {title} for user {user_id}")
            
    except Exception as e:
        print(f"[DB ERROR] Failed to record activity: {e}")
        connection.rollback()
    finally:
        connection.close()
