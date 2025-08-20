"""
JWT认证工具函数
从请求中提取用户信息
"""
try:
    import jwt
except ImportError:
    print("WARNING: PyJWT not installed, using fallback authentication")
    jwt = None
from flask import request
from typing import Optional, Dict, Any


def get_user_from_token() -> Optional[int]:
    """
    从JWT token中获取用户ID
    返回: user_id 或 None
    """
    if jwt is None:
        return None
        
    try:
        # 从Authorization header获取token
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return None
        
        token = auth_header.split(' ')[1]
        
        # 解码JWT token
        payload = jwt.decode(token, 'studypal_secret_key', algorithms=['HS256'])
        student_id = payload.get('student_id')
        
        if not student_id:
            return None
        
        # 根据student_id查询用户ID
        from auth import get_db_connection
        try:
            connection = get_db_connection()
            with connection.cursor() as cursor:
                cursor.execute("SELECT id FROM users WHERE student_id = %s", (student_id,))
                result = cursor.fetchone()
                connection.close()
                
                if result:
                    return result[0]
        except Exception as db_error:
            print(f"数据库查询失败: {db_error}")
            return None
        
        return None
        
    except Exception as e:
        print(f"JWT解析失败: {e}")
        return None


def get_user_id_from_request() -> int:
    """
    从请求中获取用户ID，支持多种方式：
    1. JWT token (推荐)
    2. 请求参数中的user_id (测试用)
    
    返回: user_id，如果获取失败返回1（默认用户）
    """
    # 1. 尝试从JWT token获取
    user_id = get_user_from_token()
    if user_id:
        return user_id
    
    # 2. 从请求参数获取（测试用）
    if request.method == 'POST':
        # 先尝试表单数据（文件上传）
        user_id = request.form.get('user_id', type=int)
        if user_id:
            return user_id
        
        # 再尝试JSON数据
        try:
            data = request.get_json() or {}
            user_id = data.get('user_id')
        except:
            pass
    else:
        user_id = request.args.get('user_id', type=int)
    
    # 3. 默认返回用户ID 1（测试用）
    return user_id if user_id else 1


def require_auth(f):
    """
    装饰器：要求用户认证
    """
    from functools import wraps
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = get_user_from_token()
        if not user_id:
            from flask import jsonify
            return jsonify({"error": "需要登录"}), 401
        
        # 将user_id作为参数传递给被装饰的函数
        return f(user_id=user_id, *args, **kwargs)
    
    return decorated_function

