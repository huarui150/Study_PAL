import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict
import time

# 导入其他服务模块以获取统计数据
from pomodoro_service import sessions_db, get_recent_sessions, get_user_emotions, get_recent_focus_minutes
try:
    from material_service import materials_db  # type: ignore
except Exception:
    materials_db = {}
try:
    from card_service import cards_db  # type: ignore
except Exception:
    cards_db = {}
try:
    from quiz_service import quiz_results_db  # type: ignore
except Exception:
    quiz_results_db = {}

# 模拟数据库存储
achievements_db = {}
user_achievements_db = {}
user_studycoin_db = {}
user_login_streak_db = {}
user_coin_history_db: Dict[int, List[Dict[str, Any]]] = {}

# 成就定义
ACHIEVEMENTS = {
    "beginner_1": {
        "id": "beginner_1",
        "name": "初识学伴",
        "category": "入门",
        "description": "第一次登录完成引导",
        "points": 10,
        "condition_type": "first_login"
    },
    "beginner_2": {
        "id": "beginner_2",
        "name": "AI 小助手",
        "category": "入门",
        "description": "第一次使用 AI 辅导提问",
        "points": 10,
        "condition_type": "first_ai_use"
    },
    "study_1": {
        "id": "study_1",
        "name": "持之以恒",
        "category": "学习",
        "description": "连续 7 天每天 ≥3 番茄",
        "points": 50,
        "condition_type": "consecutive_pomodoros",
        "params": {"days": 7, "min_pomodoros_per_day": 3}
    },
    "study_2": {
        "id": "study_2",
        "name": "高效达人",
        "category": "学习",
        "description": "单日有效专注 ≥120 分钟",
        "points": 30,
        "condition_type": "daily_focus_minutes",
        "params": {"minutes": 120}
    },
    "study_3": {
        "id": "study_3",
        "name": "稳定输出",
        "category": "学习",
        "description": "连续 14 天每天 ≥2 番茄",
        "points": 70,
        "condition_type": "consecutive_pomodoros",
        "params": {"days": 14, "min_pomodoros_per_day": 2}
    },
    "study_4": {
        "id": "study_4",
        "name": "冲刺之星",
        "category": "学习",
        "description": "考前冲刺模式完成 6 轮",
        "points": 40,
        "condition_type": "sprint_mode_pomodoros",
        "params": {"count": 6}
    },
    "material_1": {
        "id": "material_1",
        "name": "卡片匠人",
        "category": "资料",
        "description": "生成 10 张知识卡片",
        "points": 30,
        "condition_type": "cards_generated",
        "params": {"count": 10}
    },
    "material_2": {
        "id": "material_2",
        "name": "资料管家",
        "category": "资料",
        "description": "上传 20 份资料并归档",
        "points": 40,
        "condition_type": "materials_uploaded",
        "params": {"count": 20}
    },
    "quiz_1": {
        "id": "quiz_1",
        "name": "百分勇者",
        "category": "测验",
        "description": "一次测验满分",
        "points": 25,
        "condition_type": "perfect_quiz_score"
    },
    "quiz_2": {
        "id": "quiz_2",
        "name": "纠错高手",
        "category": "测验",
        "description": "错题复盘正确率 ≥90%（近 3 次）",
        "points": 35,
        "condition_type": "quiz_accuracy",
        "params": {"accuracy": 90, "recent_count": 3}
    },
    "review_1": {
        "id": "review_1",
        "name": "复盘专家",
        "category": "复盘",
        "description": "连续 7 天完成复盘卡",
        "points": 45,
        "condition_type": "consecutive_reviews",
        "params": {"days": 7}
    },
    "emotion_1": {
        "id": "emotion_1",
        "name": "自我觉察",
        "category": "情绪",
        "description": "连续 5 次提交情绪打卡",
        "points": 20,
        "condition_type": "consecutive_emotions",
        "params": {"count": 5}
    },
    "emotion_2": {
        "id": "emotion_2",
        "name": "能量平衡",
        "category": "情绪",
        "description": "7 天内 😄 占比 ≥50%",
        "points": 30,
        "condition_type": "positive_emotion_ratio",
        "params": {"emoji": "😄", "days": 7, "ratio": 50}
    },
    "plan_1": {
        "id": "plan_1",
        "name": "规划大师",
        "category": "计划",
        "description": "连续 4 周完成周计划",
        "points": 60,
        "condition_type": "consecutive_weekly_plans",
        "params": {"weeks": 4}
    },
    "plan_2": {
        "id": "plan_2",
        "name": "时间估计王",
        "category": "计划",
        "description": "3 次内计划估时误差 <±10%",
        "points": 25,
        "condition_type": "time_estimation_accuracy",
        "params": {"attempts": 3, "accuracy": 10}
    },
    "life_1": {
        "id": "life_1",
        "name": "校园通",
        "category": "生活",
        "description": "触发 5 次图片直返（不同类型）",
        "points": 20,
        "condition_type": "campus_events",
        "params": {"count": 5}
    },
    "economy_1": {
        "id": "economy_1",
        "name": "理财小能手",
        "category": "经济",
        "description": "首次在商店消费",
        "points": 15,
        "condition_type": "first_purchase"
    },
    "honor_1": {
        "id": "honor_1",
        "name": "学习自驱力",
        "category": "荣誉",
        "description": "连续 30 天每天 ≥2 番茄",
        "points": 100,
        "condition_type": "consecutive_pomodoros",
        "params": {"days": 30, "min_pomodoros_per_day": 2}
    }
}

# 任务定义
TASKS = {
    "daily_1": {
        "id": "daily_1",
        "name": "专注任务",
        "type": "daily",
        "description": "完成 ≥4 番茄",
        "target": 4,
        "reward": 10
    },
    "daily_2": {
        "id": "daily_2",
        "name": "测验任务",
        "type": "daily",
        "description": "做 1 次测验",
        "target": 1,
        "reward": 5
    },
    "daily_3": {
        "id": "daily_3",
        "name": "资料任务",
        "type": "daily",
        "description": "上传 1 份资料并生成卡片",
        "target": 1,
        "reward": 5
    },
    "weekly_1": {
        "id": "weekly_1",
        "name": "坚持任务",
        "type": "weekly",
        "description": "7 天中 ≥5 天达标",
        "target": 5,
        "reward": 30
    },
    "weekly_2": {
        "id": "weekly_2",
        "name": "学霸任务",
        "type": "weekly",
        "description": "通过 3 次测验 ≥80 分",
        "target": 3,
        "reward": 25
    }
}

def initialize_user_achievements(user_id: int) -> None:
    """
    初始化用户成就系统
    """
    if user_id not in user_achievements_db:
        user_achievements_db[user_id] = {
            "achievements": [],
            "studycoin": 0,
            "daily_tasks": {},
            "weekly_tasks": {},
            "stats": {
                "pomodoros_completed": 0,
                "cards_generated": 0,
                "materials_uploaded": 0,
                "quizzes_taken": 0,
                "emotions_submitted": 0,
                "login_streak": 0,
                "last_login_date": None
            },
            "daily_rewards": {}
        }
    
    if user_id not in user_studycoin_db:
        user_studycoin_db[user_id] = 0
    if user_id not in user_coin_history_db:
        user_coin_history_db[user_id] = []

def update_login_streak(user_id: int) -> int:
    """
    更新用户登录连续天数
    """
    initialize_user_achievements(user_id)
    
    today = datetime.now().date()
    last_login = user_achievements_db[user_id]["stats"]["last_login_date"]
    
    if last_login is None:
        # 第一次登录
        streak = 1
    else:
        last_login_date = datetime.strptime(last_login, "%Y-%m-%d").date()
        days_diff = (today - last_login_date).days
        
        if days_diff == 1:
            # 连续登录
            streak = user_achievements_db[user_id]["stats"]["login_streak"] + 1
        elif days_diff == 0:
            # 当天重复登录，保持原连续天数
            streak = user_achievements_db[user_id]["stats"]["login_streak"]
        else:
            # 断开连续登录，重新开始
            streak = 1
    
    # 更新记录
    user_achievements_db[user_id]["stats"]["login_streak"] = streak
    user_achievements_db[user_id]["stats"]["last_login_date"] = today.strftime("%Y-%m-%d")
    
    return streak

def check_achievements(user_id: int, event_type: str = None) -> List[Dict[str, Any]]:
    """
    检查用户是否解锁了新成就
    """
    initialize_user_achievements(user_id)
    
    unlocked_achievements = []
    
    for achievement_id, achievement in ACHIEVEMENTS.items():
        # 跳过已解锁的成就
        if achievement_id in user_achievements_db[user_id]["achievements"]:
            continue
            
        # 检查成就条件
        if check_achievement_condition(user_id, achievement):
            # 解锁成就
            unlock_result = unlock_achievement(user_id, achievement_id)
            if unlock_result:
                unlocked_achievements.append(unlock_result)
    
    return unlocked_achievements

def check_achievement_condition(user_id: int, achievement: Dict[str, Any]) -> bool:
    """
    检查特定成就的解锁条件
    """
    condition_type = achievement.get("condition_type")
    params = achievement.get("params", {})
    
    if condition_type == "first_login":
        # 第一次登录，这个条件应该在用户注册时触发
        return False  # 需要在注册时处理
        
    elif condition_type == "consecutive_pomodoros":
        days = params.get("days", 7)
        min_pomodoros = params.get("min_pomodoros_per_day", 3)
        return check_consecutive_pomodoros(user_id, days, min_pomodoros)
        
    elif condition_type == "daily_focus_minutes":
        minutes = params.get("minutes", 120)
        return check_daily_focus_minutes(user_id, minutes)
        
    elif condition_type == "cards_generated":
        count = params.get("count", 10)
        return check_cards_generated(user_id, count)
        
    elif condition_type == "materials_uploaded":
        count = params.get("count", 20)
        return check_materials_uploaded(user_id, count)
        
    elif condition_type == "perfect_quiz_score":
        return check_perfect_quiz_score(user_id)
        
    elif condition_type == "quiz_accuracy":
        accuracy = params.get("accuracy", 90)
        recent_count = params.get("recent_count", 3)
        return check_quiz_accuracy(user_id, accuracy, recent_count)
        
    elif condition_type == "consecutive_emotions":
        count = params.get("count", 5)
        return check_consecutive_emotions(user_id, count)
        
    elif condition_type == "positive_emotion_ratio":
        emoji = params.get("emoji", "😄")
        days = params.get("days", 7)
        ratio = params.get("ratio", 50)
        return check_positive_emotion_ratio(user_id, emoji, days, ratio)
        
    # 其他条件可以继续添加
    
    return False

def check_consecutive_pomodoros(user_id: int, days: int, min_pomodoros: int) -> bool:
    """
    检查连续几天每天完成至少指定数量的番茄钟
    """
    # 获取最近几天的会话
    recent_sessions = get_recent_sessions(user_id, days)
    
    # 按日期分组统计番茄钟数量
    daily_pomodoros = defaultdict(int)
    for session in recent_sessions:
        if session.get("end_at") and not session.get("interrupted", False):
            try:
                date = datetime.fromisoformat(session["end_at"]).date().strftime("%Y-%m-%d")
                daily_pomodoros[date] += 1
            except:
                pass
    
    # 检查最近几天是否都满足条件
    today = datetime.now().date()
    for i in range(days):
        check_date = (today - timedelta(days=i)).strftime("%Y-%m-%d")
        if daily_pomodoros.get(check_date, 0) < min_pomodoros:
            return False
    
    return True

def check_daily_focus_minutes(user_id: int, minutes: int) -> bool:
    """
    检查单日专注时间是否达到指定分钟数
    """
    recent_focus_minutes = get_recent_focus_minutes(user_id, 24)  # 最近24小时
    return recent_focus_minutes >= minutes

def check_cards_generated(user_id: int, count: int) -> bool:
    """
    检查生成的卡片数量是否达到指定数量
    """
    generated_cards = 0
    for card in cards_db.values():
        # 假设卡片与用户关联，这里简化处理
        generated_cards += 1
    
    return generated_cards >= count

def check_materials_uploaded(user_id: int, count: int) -> bool:
    """
    检查上传的资料数量是否达到指定数量
    """
    uploaded_materials = 0
    for material in materials_db.values():
        if material.get("user_id") == user_id:
            uploaded_materials += 1
    
    return uploaded_materials >= count

def check_perfect_quiz_score(user_id: int) -> bool:
    """
    检查是否有测验得分为满分
    """
    for result in quiz_results_db.values():
        if result.get("user_id") == user_id:
            # 假设满分是100分
            if result.get("score", 0) == 100:
                return True
    
    return False

def check_quiz_accuracy(user_id: int, accuracy: int, recent_count: int) -> bool:
    """
    检查最近几次测验的正确率是否达到指定值
    """
    user_results = []
    for result in quiz_results_db.values():
        if result.get("user_id") == user_id:
            user_results.append(result)
    
    # 按时间排序，取最近的几次
    user_results.sort(key=lambda x: x.get("completed_at", ""), reverse=True)
    recent_results = user_results[:recent_count]
    
    if len(recent_results) < recent_count:
        return False
    
    # 计算平均正确率
    total_accuracy = sum(result.get("accuracy", 0) for result in recent_results)
    avg_accuracy = total_accuracy / len(recent_results)
    
    return avg_accuracy >= accuracy

def check_consecutive_emotions(user_id: int, count: int) -> bool:
    """
    检查是否连续提交了指定数量的情绪打卡
    """
    # 这里简化处理，实际应该检查情绪提交的时间序列
    # 从pomodoro_service中获取情绪数据
    emotions = get_user_emotions(user_id, count)
    emotion_count = sum(sum(e.values()) for e in emotions.values())
    
    return emotion_count >= count

def check_positive_emotion_ratio(user_id: int, emoji: str, days: int, ratio: int) -> bool:
    """
    检查指定表情符号在最近几天的情绪中占比是否达到指定比例
    """
    emotions = get_user_emotions(user_id, days)
    
    total_emotions = 0
    positive_emotions = 0
    
    for date_emotions in emotions.values():
        for e, count in date_emotions.items():
            total_emotions += count
            if e == emoji:
                positive_emotions += count
    
    if total_emotions == 0:
        return False
    
    positive_ratio = (positive_emotions / total_emotions) * 100
    return positive_ratio >= ratio

def unlock_achievement(user_id: int, achievement_id: str) -> Optional[Dict[str, Any]]:
    """
    解锁成就
    """
    if achievement_id not in ACHIEVEMENTS:
        return None
    
    initialize_user_achievements(user_id)
    
    # 检查是否已经解锁过该成就
    if achievement_id in user_achievements_db[user_id]["achievements"]:
        return None
    
    # 解锁成就
    user_achievements_db[user_id]["achievements"].append(achievement_id)
    
    # 奖励StudyCoin
    reward_coins(user_id, ACHIEVEMENTS[achievement_id]["points"])
    
    achievement = ACHIEVEMENTS[achievement_id]
    return {
        "event": "achievement.unlocked",
        "user_id": user_id,
        "achievement_id": achievement_id,
        "name": achievement["name"],
        "description": achievement["description"],
        "points": achievement["points"]
    }

def reward_coins(user_id: int, amount: int, is_first_daily: bool = False) -> Optional[Dict[str, Any]]:
    """
    奖励或扣除 StudyCoin（含防刷与日下限）
    - 防刷：5分钟内最多+10
    - 首次完成每日番茄：额外+5（亦计入5分钟上限）
    - 扣分：不低于0
    """
    initialize_user_achievements(user_id)

    # 计算正向奖励的防刷上限（5分钟最多+10）
    adjusted_amount = amount
    if is_first_daily:
        adjusted_amount += 5

    now_ts = time.time()
    # 仅对正向奖励应用防刷，上限每5分钟+10
    if adjusted_amount > 0:
        window_seconds = 300
        # 清理窗口外记录
        recent = []
        total_recent_positive = 0
        for rec in user_coin_history_db.get(user_id, []):
            if now_ts - rec.get("ts", 0) <= window_seconds:
                recent.append(rec)
                if rec.get("amount", 0) > 0:
                    total_recent_positive += rec.get("amount", 0)
        user_coin_history_db[user_id] = recent

        allowed = max(0, 10 - total_recent_positive)
        if adjusted_amount > allowed:
            adjusted_amount = allowed

    # 计算新余额，处理不低于0
    new_total = user_studycoin_db[user_id] + adjusted_amount
    if new_total < 0:
        adjusted_amount = -user_studycoin_db[user_id]
        new_total = 0

    # 若本次奖励经限流为0，直接返回None（不触发事件）
    if adjusted_amount == 0:
        return None

    user_studycoin_db[user_id] = new_total
    user_achievements_db[user_id]["studycoin"] = new_total

    # 记录历史
    user_coin_history_db[user_id].append({"ts": now_ts, "amount": adjusted_amount})

    return {
        "event": "coin.rewarded",
        "user_id": user_id,
        "amount": adjusted_amount,
        "total": new_total
    }

def apply_failure_penalty(user_id: int) -> Optional[Dict[str, Any]]:
    """
    失败扣分：-2（不低于0）
    """
    return reward_coins(user_id, -2, is_first_daily=False)

def complete_pomodoro(user_id: int) -> List[Dict[str, Any]]:
    """
    完成番茄钟，检查相关成就和任务
    """
    initialize_user_achievements(user_id)
    
    # 更新统计信息
    user_achievements_db[user_id]["stats"]["pomodoros_completed"] += 1
    
    events = []
    
    # 检查是否有奖励事件
    # 每日首次完成番茄钟奖励
    today = datetime.now().date().isoformat()
    daily_key = f"pomodoro_{today}"
    
    if daily_key not in user_achievements_db[user_id].get("daily_rewards", {}):
        # 记录每日奖励
        if "daily_rewards" not in user_achievements_db[user_id]:
            user_achievements_db[user_id]["daily_rewards"] = {}
        user_achievements_db[user_id]["daily_rewards"][daily_key] = True
        
        # 奖励金币
        coin_event = reward_coins(user_id, 10, is_first_daily=True)
        if coin_event:
            events.append(coin_event)
    else:
        # 非首次完成，只奖励基础金币
        coin_event = reward_coins(user_id, 10)
        if coin_event:
            events.append(coin_event)
    
    # 检查任务进度
    task_event = update_task_progress(user_id, "daily_1", 1)
    if task_event:
        events.append(task_event)
    
    # 检查成就
    achievement_events = check_achievements(user_id)
    events.extend(achievement_events)
    
    return events

def update_task_progress(user_id: int, task_id: str, progress: int = 1) -> Optional[Dict[str, Any]]:
    """
    更新任务进度
    """
    if task_id not in TASKS:
        return None
    
    initialize_user_achievements(user_id)
    
    task = TASKS[task_id]
    today = datetime.now().date()
    
    # 初始化任务记录
    if task["type"] not in user_achievements_db[user_id]:
        user_achievements_db[user_id][f"{task['type']}_tasks"] = {}
    
    task_key = f"{task_id}_{today.isocalendar()[1]}" if task["type"] == "weekly" else f"{task_id}_{today.isoformat()}"
    
    if task_key not in user_achievements_db[user_id][f"{task['type']}_tasks"]:
        user_achievements_db[user_id][f"{task['type']}_tasks"][task_key] = {
            "progress": 0,
            "completed": False
        }
    
    # 更新进度
    user_achievements_db[user_id][f"{task['type']}_tasks"][task_key]["progress"] += progress
    
    # 调试信息
    print(f"[DEBUG] Task progress update: user_id={user_id}, task_id={task_id}, progress={progress}")
    task_type = task['type']
    print(f"[DEBUG] Current progress: {user_achievements_db[user_id][f'{task_type}_tasks'][task_key]['progress']}/{task['target']}")
    print(f"[DEBUG] User achievements DB for user {user_id}: {user_achievements_db.get(user_id, 'Not found')}")
    
    # 检查是否完成任务
    if (not user_achievements_db[user_id][f"{task_type}_tasks"][task_key]["completed"] and 
        user_achievements_db[user_id][f"{task_type}_tasks"][task_key]["progress"] >= task["target"]):
        
        user_achievements_db[user_id][f"{task_type}_tasks"][task_key]["completed"] = True
        
        # 奖励StudyCoin
        reward_coins(user_id, task["reward"])
        
        print(f"[SUCCESS] Task completed: {task['name']} for user {user_id}")
        
        return {
            "event": "task.completed",
            "user_id": user_id,
            "task_id": task_id,
            "name": task["name"],
            "description": task["description"],
            "reward": task["reward"]
        }
    
    return None

def get_user_achievements(user_id: int) -> Dict[str, Any]:
    """
    获取用户成就信息
    """
    initialize_user_achievements(user_id)
    user_data = user_achievements_db[user_id]
    
    # 获取已解锁的成就详情
    unlocked_achievements = []
    for achievement_id in user_data["achievements"]:
        if achievement_id in ACHIEVEMENTS:
            unlocked_achievements.append(ACHIEVEMENTS[achievement_id])
    
    # 从数据库获取正确的连续登录天数
    try:
        from db_service import get_user_stats_db
        db_stats = get_user_stats_db(str(user_id))
        login_streak = db_stats.get('login_streak', 0)
        user_data["stats"]["login_streak"] = login_streak
    except Exception as e:
        print(f"[ERROR] Failed to get login streak from database: {e}")
    
    return {
        "achievements": unlocked_achievements,
        "studycoin": user_studycoin_db.get(user_id, 0),
        "stats": user_data["stats"]
    }

def get_user_tasks(user_id: int) -> Dict[str, Any]:
    """
    获取用户任务信息
    """
    initialize_user_achievements(user_id)
    user_data = user_achievements_db[user_id]
    
    # 获取今日任务状态
    today = datetime.now().date().isoformat()
    daily_tasks = []
    
    for task_id, task in TASKS.items():
        if task["type"] == "daily":
            task_key = f"{task_id}_{today}"
            task_status = user_data["daily_tasks"].get(task_key, {"progress": 0, "completed": False})
            daily_tasks.append({
                "id": task_id,
                "name": task["name"],
                "description": task["description"],
                "target": task["target"],
                "progress": task_status["progress"],
                "completed": task_status["completed"]
            })
    
    return {
        "daily_tasks": daily_tasks
    }

# 用户注册时调用
def on_user_register(user_id: int) -> List[Dict[str, Any]]:
    """
    用户注册时的处理
    """
    events = []
    
    # 解锁"初识学伴"成就
    achievement_event = unlock_achievement(user_id, "beginner_1")
    if achievement_event:
        events.append(achievement_event)
    
    # 初始化用户时更新登录连续天数（注册即视为首次登录）
    update_login_streak(user_id)
    
    return events

# 用户登录时调用
def on_user_login(user_id: int) -> List[Dict[str, Any]]:
    """
    用户登录时的处理
    """
    events = []
    
    # 更新数据库中的登录连续天数
    try:
        from db_service import update_login_streak_db, record_activity_db
        update_login_streak_db(str(user_id))
        # 记录登录活动
        record_activity_db(str(user_id), 'login', '登录系统', '开始新的学习旅程')
    except Exception as e:
        print(f"[ERROR] Failed to update login streak in database: {e}")
    
    # 同步内存中的登录连续天数
    streak = update_login_streak(user_id)
    
    # 检查成就
    achievement_events = check_achievements(user_id)
    events.extend(achievement_events)
    
    return events