import json
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import math
from collections import defaultdict

# 模拟数据库存储
plans_db = {}
sessions_db = {}
emotion_daily_db = {}

# 番茄钟模式配置
POMODORO_MODES = {
    "standard": {
        "focus": 25,
        "break": 5,
        "long_break": 15,
        "cycles": 4
    },
    "deep": {
        "focus": 50,
        "break": 10,
        "long_break": 20,
        "cycles": 2
    },
    "sprint": {
        "focus": 35,
        "break": 7,
        "long_break": 0,
        "cycles": 1
    }
}

def create_plan(user_id: int, title: str, course_id: int, topic: str, 
                estimate_min: int, difficulty: int, importance: int, 
                deadline: str) -> Dict[str, Any]:
    """
    创建学习计划
    """
    plan_id = len(plans_db) + 1
    plan = {
        "id": plan_id,
        "user_id": user_id,
        "title": title,
        "course_id": course_id,
        "topic": topic,
        "estimate_min": estimate_min,
        "difficulty": difficulty,  # 1-5
        "importance": importance,  # 1-5
        "deadline": deadline,  # YYYY-MM-DD
        "status": "pending",  # pending, in_progress, completed, overdue
        "created_at": datetime.now().isoformat()
    }
    plans_db[plan_id] = plan
    return plan

def get_user_plans(user_id: int) -> List[Dict[str, Any]]:
    """
    获取用户的所有计划
    """
    return [plan for plan in plans_db.values() if plan["user_id"] == user_id]

def get_plan(plan_id: int) -> Optional[Dict[str, Any]]:
    """
    获取特定计划
    """
    return plans_db.get(plan_id)

def update_plan(plan_id: int, **kwargs) -> Optional[Dict[str, Any]]:
    """
    更新计划信息
    """
    if plan_id in plans_db:
        for key, value in kwargs.items():
            if key in plans_db[plan_id]:
                plans_db[plan_id][key] = value
        return plans_db[plan_id]
    return None

def delete_plan(plan_id: int) -> bool:
    """
    删除计划
    """
    if plan_id in plans_db:
        del plans_db[plan_id]
        return True
    return False

def start_pomodoro_session(user_id: int, plan_id: int, focus_minutes: int = 25) -> Dict[str, Any]:
    """
    开始番茄钟会话 - 保存到数据库
    """
    try:
        from db_service import create_pomodoro_session as db_create_session
        session_id = db_create_session(str(user_id), plan_id, focus_minutes)
        print(f"[DEBUG] Created session {session_id} in database for user {user_id}")
    except Exception as e:
        print(f"[ERROR] Failed to create session in database: {e}")
        # 回退到内存存储
        session_id = len(sessions_db) + 1
        session = {
            "id": session_id,
            "user_id": user_id,
            "plan_id": plan_id,
            "start_at": datetime.now().isoformat(),
            "end_at": None,
            "type": "focus",
            "interrupted": False,
            "reason": None,
            "emotion": None,
            "note": None,
            "focus_minutes": focus_minutes
        }
        sessions_db[session_id] = session
    
    # 更新计划状态
    plan = get_plan(plan_id)
    if plan:
        update_plan(plan_id, status="in_progress")
    
    return {
        "session_id": session_id,
        "focus_min": focus_minutes
    }

def interrupt_pomodoro_session(session_id: int, reason: str) -> Dict[str, Any]:
    """
    中断番茄钟会话
    """
    if session_id in sessions_db:
        session = sessions_db[session_id]
        session["interrupted"] = True
        session["reason"] = reason
        session["end_at"] = datetime.now().isoformat()
        
        # 检查中断时间是否超过90秒
        start_time = datetime.fromisoformat(session["start_at"])
        end_time = datetime.fromisoformat(session["end_at"])
        duration = (end_time - start_time).total_seconds()
        
        is_failed = duration > 90
        
        return {
            "session_id": session_id,
            "failed": is_failed,
            "duration_seconds": duration
        }
    return {"error": "会话未找到"}

def complete_pomodoro_session(session_id: int, emotion: str = None, note: str = None, actual_minutes: int = 25) -> Dict[str, Any]:
    """
    完成番茄钟会话 - 保存到数据库
    """
    try:
        from db_service import complete_pomodoro_session as db_complete_session
        result = db_complete_session(session_id, emotion, note, actual_minutes)
        print(f"[DEBUG] Session {session_id} completed in database with {actual_minutes} minutes")
        return result
    except Exception as e:
        print(f"[ERROR] Failed to complete session in database: {e}")
        # 回退到内存存储
        if session_id in sessions_db:
            session = sessions_db[session_id]
            session["status"] = "completed"
            session["end_at"] = datetime.now().isoformat()
            session["emotion"] = emotion
            session["note"] = note
            session["actual_minutes"] = actual_minutes
            
            print(f"[DEBUG] Session {session_id} completed in memory with {actual_minutes} minutes")
            print(f"[DEBUG] Session data: {session}")
            
            # 记录情绪打卡
            if emotion:
                record_emotion(session["user_id"], emotion)
            
            return {
                "session_id": session_id,
                "completed": True,
                "actual_minutes": actual_minutes
            }
        return {"error": "会话未找到"}

def record_emotion(user_id: int, emotion: str) -> None:
    """
    记录情绪打卡
    """
    today = datetime.now().date().isoformat()
    key = f"{user_id}_{today}"
    
    if key not in emotion_daily_db:
        emotion_daily_db[key] = {
            "id": len(emotion_daily_db) + 1,
            "user_id": user_id,
            "date": today,
            "counts_json": {
                "😄": 0,
                "🙂": 0,
                "😐": 0,
                "😫": 0,
                "😵": 0
            }
        }
    
    emotion_daily_db[key]["counts_json"][emotion] += 1

def get_user_emotions(user_id: int, days: int = 7) -> Dict[str, Any]:
    """
    获取用户最近几天的情绪数据
    """
    emotions = {}
    today = datetime.now().date()
    
    for i in range(days):
        date = (today - timedelta(days=i)).isoformat()
        key = f"{user_id}_{date}"
        if key in emotion_daily_db:
            emotions[date] = emotion_daily_db[key]["counts_json"]
    
    return emotions

def calculate_urgency(deadline: str) -> float:
    """
    计算紧迫度
    """
    try:
        deadline_date = datetime.strptime(deadline, "%Y-%m-%d").date()
        today = datetime.now().date()
        days_to_deadline = (deadline_date - today).days
        return max(0, 1 - days_to_deadline / 7)
    except:
        return 0

def calculate_priority(importance: int, urgency: float) -> float:
    """
    计算优先级
    """
    return 0.5 * (importance / 5) + 0.5 * urgency

def calculate_retention(topic: str, user_id: int) -> float:
    """
    计算记忆维持度（简化实现）
    """
    # 在实际实现中，这里应该基于历史数据计算
    # 简化实现：返回固定值
    return 0.7

def calculate_fatigue(emotions: Dict[str, Any], recent_focus_minutes: int) -> float:
    """
    计算疲劳度
    """
    # 计算最近情绪中的负面情绪比例
    negative_emotions = 0
    total_emotions = 0
    
    for date, emotion_counts in emotions.items():
        for emotion, count in emotion_counts.items():
            if emotion in ["😫", "😵"]:
                negative_emotions += count
            total_emotions += count
    
    emotion_factor = negative_emotions / total_emotions if total_emotions > 0 else 0
    
    # 计算专注时间因子
    time_factor = min(recent_focus_minutes / 120, 1)  # 假设120分钟为高疲劳阈值
    
    # 综合疲劳度
    fatigue = 0.6 * emotion_factor + 0.4 * time_factor
    return max(0, min(1, fatigue))  # 限制在0-1之间

def get_recent_focus_minutes(user_id: int, hours: int = 24) -> int:
    """
    获取最近一段时间的专注时间
    """
    total_minutes = 0
    cutoff_time = datetime.now() - timedelta(hours=hours)
    
    for session in sessions_db.values():
        if session["user_id"] == user_id and session["end_at"]:
            try:
                end_time = datetime.fromisoformat(session["end_at"])
                if end_time > cutoff_time and not session["interrupted"]:
                    total_minutes += session.get("focus_minutes", 25)
            except:
                pass
    
    return total_minutes

def optimize_plans(user_id: int, date: str = None) -> Dict[str, Any]:
    """
    优化学习计划建议
    """
    if date is None:
        date = datetime.now().date().isoformat()
    
    # 获取用户今天的计划
    all_plans = get_user_plans(user_id)
    today_plans = []
    
    for plan in all_plans:
        if plan["status"] in ["pending", "in_progress"]:
            today_plans.append(plan)
    
    # 获取历史数据
    emotions = get_user_emotions(user_id, 3)
    recent_focus_minutes = get_recent_focus_minutes(user_id, 24)
    
    # 计算每个计划的分数
    ranked_plans = []
    for plan in today_plans:
        urgency = calculate_urgency(plan["deadline"])
        priority = calculate_priority(plan["importance"], urgency)
        retention = calculate_retention(plan["topic"], user_id)
        fatigue = calculate_fatigue(emotions, recent_focus_minutes)
        
        # 综合分数
        score = 0.4 * priority + 0.3 * retention + 0.3 * (1 - fatigue)
        
        ranked_plans.append({
            "plan_id": plan["id"],
            "title": plan["title"],
            "score": score,
            "why": f"优先级: {priority:.2f}, 记忆维持: {retention:.2f}, 疲劳度: {fatigue:.2f}"
        })
    
    # 按分数排序
    ranked_plans.sort(key=lambda x: x["score"], reverse=True)
    
    # 确定推荐的番茄钟模式
    mode = "standard"  # 默认模式
    
    # 检查是否需要自适应调整
    # 计算最近的中断率
    recent_sessions = get_recent_sessions(user_id, 3)  # 最近3天的会话
    if recent_sessions:
        interrupted_count = sum(1 for s in recent_sessions if s.get("interrupted", False))
        interruption_rate = interrupted_count / len(recent_sessions)
        
        if interruption_rate > 0.5:  # 中断率高于50%
            mode = "adaptive"  # 缩短时长模式
        elif interruption_rate < 0.2:  # 中断率低于20%
            mode = "deep"  # 深度模式
    
    # 确定目标番茄钟数量
    target_pomodoros = max(3, min(10, len(ranked_plans)))  # 至少3个，最多10个
    
    # 生成时间安排
    schedule = []
    current_time = datetime.now().replace(hour=9, minute=0, second=0, microsecond=0)  # 从早上9点开始
    
    for i, plan in enumerate(ranked_plans[:target_pomodoros]):
        focus_duration = POMODORO_MODES[mode if mode != "adaptive" else "standard"]["focus"]
        
        start_time = current_time.isoformat()
        current_time += timedelta(minutes=focus_duration)
        end_time = current_time.isoformat()
        
        schedule.append({
            "plan_id": plan["plan_id"],
            "title": plan["title"],
            "start": start_time,
            "end": end_time,
            "why": plan["why"]
        })
        
        # 添加休息时间
        break_duration = POMODORO_MODES[mode if mode != "adaptive" else "standard"]["break"]
        current_time += timedelta(minutes=break_duration)
    
    return {
        "mode": mode,
        "target_pomodoros": target_pomodoros,
        "order": schedule
    }

def get_recent_sessions(user_id: int, days: int = 7) -> List[Dict[str, Any]]:
    """
    获取用户最近几天的会话
    """
    cutoff_date = datetime.now() - timedelta(days=days)
    recent_sessions = []
    
    for session in sessions_db.values():
        if session["user_id"] == user_id and session["start_at"]:
            try:
                start_time = datetime.fromisoformat(session["start_at"])
                if start_time > cutoff_date:
                    recent_sessions.append(session)
            except:
                pass
    
    return recent_sessions

def get_session(session_id: int) -> Optional[Dict[str, Any]]:
    """
    获取特定会话
    """
    return sessions_db.get(session_id)

def get_user_pomodoro_stats(user_id: int) -> Dict[str, Any]:
    """获取用户的番茄钟统计数据 - 使用数据库"""
    try:
        from db_service import get_user_pomodoro_stats as db_stats
        return db_stats(str(user_id))
    except Exception as e:
        print(f"[ERROR] Failed to get pomodoro stats from database: {e}")
        # 回退到内存数据
        today = datetime.now().date()
        today_str = today.isoformat()
        
        # 获取用户所有会话
        user_sessions = [s for s in sessions_db.values() if s.get('user_id') == user_id]
        
        # 今日完成的番茄钟
        today_sessions = [s for s in user_sessions 
                         if s.get('start_at', '').startswith(today_str) and s.get('status') == 'completed']
        
        # 总专注时长（包括历史）
        completed_sessions = [s for s in user_sessions if s.get('status') == 'completed']
        total_focus_time = sum(s.get('actual_minutes', 25) for s in completed_sessions)
        
        return {
            "today_pomodoros": len(today_sessions),
            "total_focus_time": total_focus_time,
            "total_sessions": len(completed_sessions),
            "today_focus_time": sum(s.get('actual_minutes', 25) for s in today_sessions)
        }