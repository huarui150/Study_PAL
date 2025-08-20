#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建所有必要的数据库表
"""

import pymysql
from datetime import datetime

def get_database_connection():
    return pymysql.connect(
        host='141.11.90.223',
        port=3307,
        user='root',
        password='7539518426',
        database='study_pal',
        charset='utf8mb4',
        autocommit=False
    )

def create_all_tables():
    """创建所有必要的数据库表"""
    connection = get_database_connection()
    
    try:
        with connection.cursor() as cursor:
            # 1. 番茄钟会话表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS pomodoro_sessions (
                    id BIGINT PRIMARY KEY,
                    user_id VARCHAR(50) NOT NULL,
                    plan_id BIGINT,
                    start_at DATETIME NOT NULL,
                    end_at DATETIME,
                    focus_minutes INT DEFAULT 25,
                    actual_minutes INT DEFAULT 0,
                    status ENUM('active', 'completed', 'interrupted') DEFAULT 'active',
                    emotion VARCHAR(10),
                    note TEXT,
                    last_tick DATETIME,
                    remaining_time INT DEFAULT 0,
                    interrupted_reason VARCHAR(100),
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_user_id (user_id),
                    INDEX idx_start_at (start_at)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)
            
            # 2. 成就表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS achievements (
                    id VARCHAR(50) PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    description TEXT,
                    category VARCHAR(50),
                    points INT DEFAULT 0,
                    icon VARCHAR(10),
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)
            
            # 3. 用户成就表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_achievements (
                    id BIGINT AUTO_INCREMENT PRIMARY KEY,
                    user_id VARCHAR(50) NOT NULL,
                    achievement_id VARCHAR(50) NOT NULL,
                    unlocked_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE KEY unique_user_achievement (user_id, achievement_id),
                    INDEX idx_user_id (user_id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)
            
            # 4. StudyCoin记录表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS studycoin_records (
                    id BIGINT AUTO_INCREMENT PRIMARY KEY,
                    user_id VARCHAR(50) NOT NULL,
                    amount INT NOT NULL,
                    reason VARCHAR(200),
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_user_id (user_id),
                    INDEX idx_created_at (created_at)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)
            
            # 5. 用户任务进度表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_task_progress (
                    id BIGINT AUTO_INCREMENT PRIMARY KEY,
                    user_id VARCHAR(50) NOT NULL,
                    task_id VARCHAR(50) NOT NULL,
                    progress INT DEFAULT 0,
                    completed BOOLEAN DEFAULT FALSE,
                    date DATE NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    UNIQUE KEY unique_user_task_date (user_id, task_id, date),
                    INDEX idx_user_id (user_id),
                    INDEX idx_date (date)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)
            
            # 6. 情绪记录表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS emotion_records (
                    id BIGINT AUTO_INCREMENT PRIMARY KEY,
                    user_id VARCHAR(50) NOT NULL,
                    emotion VARCHAR(10) NOT NULL,
                    note TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_user_id (user_id),
                    INDEX idx_created_at (created_at)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)
            
            # 7. 学习计划表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS learning_plans (
                    id BIGINT AUTO_INCREMENT PRIMARY KEY,
                    user_id VARCHAR(50) NOT NULL,
                    title VARCHAR(200) NOT NULL,
                    course_id VARCHAR(50),
                    topic VARCHAR(200),
                    estimate_min INT DEFAULT 25,
                    difficulty INT DEFAULT 3,
                    importance INT DEFAULT 3,
                    deadline DATE,
                    status ENUM('pending', 'in_progress', 'completed', 'overdue') DEFAULT 'pending',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    INDEX idx_user_id (user_id),
                    INDEX idx_deadline (deadline),
                    INDEX idx_status (status)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)
            
            # 8. 用户统计表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_stats (
                    user_id VARCHAR(50) PRIMARY KEY,
                    studycoin_balance INT DEFAULT 0,
                    login_streak INT DEFAULT 0,
                    last_login_date DATE,
                    total_focus_time INT DEFAULT 0,
                    total_pomodoros INT DEFAULT 0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)
            
            # 9. 课程资料表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS course_materials (
                    id BIGINT AUTO_INCREMENT PRIMARY KEY,
                    user_id VARCHAR(50) NOT NULL,
                    course_id VARCHAR(50) NOT NULL,
                    title VARCHAR(200) NOT NULL,
                    file_path VARCHAR(500),
                    file_type VARCHAR(50),
                    file_size BIGINT,
                    upload_status ENUM('uploading', 'completed', 'failed') DEFAULT 'uploading',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_user_id (user_id),
                    INDEX idx_course_id (course_id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)
            
            connection.commit()
            print("✅ 所有数据库表创建成功！")
            
            # 插入默认成就数据
            insert_default_achievements(cursor)
            connection.commit()
            print("✅ 默认成就数据插入成功！")
            
    except Exception as e:
        print(f"❌ 创建表失败: {e}")
        connection.rollback()
    finally:
        connection.close()

def insert_default_achievements(cursor):
    """插入默认成就数据"""
    achievements = [
        ('beginner_1', '初识学伴', '第一次登录完成引导', 'entry', 10, '🎉'),
        ('beginner_2', 'AI小助手', '第一次使用AI辅导提问', 'entry', 10, '🤖'),
        ('study_1', '持之以恒', '连续7天每天≥3番茄', 'study', 50, '💪'),
        ('study_2', '高效达人', '单日有效专注≥120分钟', 'study', 30, '⚡'),
        ('study_3', '稳定输出', '连续14天每天≥2番茄', 'study', 100, '🔥'),
        ('material_1', '资料管家', '上传20份资料并归档', 'material', 30, '📚'),
        ('material_2', '卡片匠人', '生成10张知识卡片', 'material', 25, '🎴'),
        ('quiz_1', '百分勇者', '一次测验满分', 'quiz', 40, '💯'),
        ('plan_1', '规划大师', '连续4周完成周计划', 'plan', 60, '📅'),
        ('economy_1', '理财小能手', '首次在商店消费', 'economy', 15, '💰')
    ]
    
    for achievement in achievements:
        cursor.execute("""
            INSERT IGNORE INTO achievements (id, name, description, category, points, icon)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, achievement)

if __name__ == "__main__":
    create_all_tables()
