import jwt
import datetime
import pymysql
from werkzeug.security import generate_password_hash, check_password_hash
import hashlib
import os
from dotenv import load_dotenv
from typing import Dict, Any, Tuple
from achievement_service import on_user_register, on_user_login

# 加载.env配置
load_dotenv()

# 数据库配置
DB_CONFIG = {
    'host': os.getenv('DB_HOST'),
    'port': int(os.getenv('DB_PORT', 3306)),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'database': os.getenv('DB_NAME'),
    'charset': os.getenv('DB_CHARSET', 'utf8mb4')
}

def get_db_connection():
    """获取数据库连接"""
    return pymysql.connect(**DB_CONFIG)

def register_user(data):
    """
    用户注册功能
    """
    student_id = data.get('student_id')
    password = data.get('password')
    name = data.get('name')
    major = data.get('major')
    
    # 检查必填字段
    if not all([student_id, password, name, major]):
        return {"error": "缺少必要字段"}, 400
    
    try:
        # 连接数据库
        connection = get_db_connection()
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            # 检查用户是否已存在
            check_query = "SELECT id FROM users WHERE username = %s OR student_id = %s"
            cursor.execute(check_query, (student_id, student_id))
            if cursor.fetchone():
                connection.close()
                return {"error": "用户已存在"}, 409
            
            # 插入新用户
            insert_query = """
                INSERT INTO users (username, password_hash, student_id, major, name) 
                VALUES (%s, %s, %s, %s, %s)
            """
            password_hash = generate_password_hash(password)
            cursor.execute(insert_query, (student_id, password_hash, student_id, major, name))
            new_id = cursor.lastrowid
        
        # 提交事务
        connection.commit()
        connection.close()
        
        # 触发注册事件，解锁相关成就
        try:
            from db_service import unlock_achievement_db, update_login_streak_db, record_activity_db
            events = []
            # 解锁"初识学伴"成就
            event = unlock_achievement_db(student_id, "beginner_1")
            if event:
                events.append(event)
            # 更新登录统计
            update_login_streak_db(student_id)
            # 记录注册活动
            record_activity_db(student_id, 'register', '用户注册', '加入StudyPAL+学习平台')
            print(f"[SUCCESS] Registration events handled for user {student_id}: {events}")
        except Exception as e:
            print(f"[ERROR] Failed to handle registration events: {e}")
            events = []
        
        # 生成JWT token
        token = jwt.encode({
            'student_id': student_id,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24),
            'iat': datetime.datetime.utcnow()
        }, 'studypal_secret_key', algorithm='HS256')
        
        # 返回token和用户信息
        return {
            "token": token,
            "user_info": {
                "id": new_id,
                "student_id": student_id,
                "name": name,
                "major": major
            },
            "events": events
        }, 201
        
    except Exception as e:
        return {"error": f"注册失败: {str(e)}"}, 500

def login_user(data):
    """
    用户登录功能
    """
    student_id = data.get('student_id')
    password = data.get('password')
    
    # 检查必填字段
    if not all([student_id, password]):
        return {"error": "学号和密码不能为空"}, 400
    
    try:
        # 连接数据库
        connection = get_db_connection()
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            # 查询用户信息
            query = "SELECT * FROM users WHERE username = %s OR student_id = %s"
            cursor.execute(query, (student_id, student_id))
            user = cursor.fetchone()
            
            # 检查用户是否存在
            if not user:
                connection.close()
                return {"error": "用户不存在"}, 404
            
            # 验证密码
            if not check_password_hash(user['password_hash'], password):
                connection.close()
                return {"error": "密码错误"}, 401
        
        connection.close()
        
        # 更新登录连续天数并检查成就
        events = on_user_login(user['id'])
        print(f"[SUCCESS] Login events handled for user {user['id']}: {events}")
        
        # 生成JWT token
        token = jwt.encode({
            'student_id': user['student_id'],
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24),
            'iat': datetime.datetime.utcnow()
        }, 'studypal_secret_key', algorithm='HS256')
        
        # 返回token和用户信息
        return {
            "token": token,
            "user_info": {
                "id": user['id'],
                "student_id": user['student_id'],
                "name": user['name'],
                "major": user['major']
            },
            "events": events
        }, 200
        
    except Exception as e:
        return {"error": f"登录失败: {str(e)}"}, 500