"""
课程管理服务
负责课程的增删改查和事件管理
"""
import pymysql
from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime
from auth import get_db_connection


class CourseService:
    """课程管理服务类"""
    
    @staticmethod
    def create_course(user_id: int, course_data: Dict[str, Any]) -> Tuple[Dict[str, Any], int]:
        """创建新课程"""
        try:
            print(f"[DEBUG] 创建课程 - user_id: {user_id}, course_data: {course_data}")
            
            name = course_data.get('name', '').strip()
            weight = float(course_data.get('weight', 1.0))
            color = course_data.get('color', '#3498db')
            exam_ratio = float(course_data.get('exam_ratio', 0.6))
            
            if not name:
                return {"error": "课程名称不能为空"}, 400
                
            if not (0 < weight <= 5.0):
                return {"error": "课程权重必须在0-5之间"}, 400
                
            if not (0 <= exam_ratio <= 1.0):
                return {"error": "考试权重必须在0-1之间"}, 400
                
            print(f"[DEBUG] 准备连接数据库...")
            connection = get_db_connection()
            print(f"[DEBUG] 数据库连接成功")
            
            with connection.cursor(pymysql.cursors.DictCursor) as cursor:
                # 检查同名课程
                cursor.execute(
                    "SELECT id FROM courses WHERE user_id = %s AND name = %s",
                    (user_id, name)
                )
                if cursor.fetchone():
                    connection.close()
                    return {"error": "课程名称已存在"}, 409
                
                # 插入新课程
                cursor.execute("""
                    INSERT INTO courses (user_id, name, weight, color, exam_ratio) 
                    VALUES (%s, %s, %s, %s, %s)
                """, (user_id, name, weight, color, exam_ratio))
                
                course_id = cursor.lastrowid
                connection.commit()
                connection.close()
                
                return {
                    "course_id": course_id,
                    "name": name,
                    "weight": weight,
                    "color": color,
                    "exam_ratio": exam_ratio,
                    "message": "课程创建成功"
                }, 201
                
        except Exception as e:
            return {"error": f"创建课程失败: {str(e)}"}, 500
    
    @staticmethod
    def get_user_courses(user_id: int) -> Tuple[Dict[str, Any], int]:
        """获取用户的所有课程"""
        try:
            connection = get_db_connection()
            with connection.cursor(pymysql.cursors.DictCursor) as cursor:
                # 使用子查询避免JOIN放大导致的COUNT开销，并增加LIMIT以避免一次性返回过多数据
                cursor.execute("""
                    SELECT 
                        c.*, 
                        (SELECT COUNT(*) FROM materials m WHERE m.course_id = c.id) AS material_count,
                        (SELECT COUNT(*) FROM events e WHERE e.course_id = c.id) AS event_count
                    FROM courses c
                    WHERE c.user_id = %s
                    ORDER BY c.created_at DESC
                    LIMIT 200
                """, (user_id,))
                
                courses = cursor.fetchall()
                connection.close()
                
                return {
                    "courses": courses,
                    "total": len(courses)
                }, 200
                
        except Exception as e:
            return {"error": f"获取课程列表失败: {str(e)}"}, 500
    
    @staticmethod
    def update_course(user_id: int, course_id: int, course_data: Dict[str, Any]) -> Tuple[Dict[str, Any], int]:
        """更新课程信息"""
        try:
            connection = get_db_connection()
            with connection.cursor(pymysql.cursors.DictCursor) as cursor:
                # 验证课程归属
                cursor.execute(
                    "SELECT id FROM courses WHERE id = %s AND user_id = %s",
                    (course_id, user_id)
                )
                if not cursor.fetchone():
                    connection.close()
                    return {"error": "课程不存在或无权限"}, 404
                
                # 构建更新字段
                update_fields = []
                params = []
                
                if 'name' in course_data:
                    name = course_data['name'].strip()
                    if not name:
                        return {"error": "课程名称不能为空"}, 400
                    update_fields.append("name = %s")
                    params.append(name)
                
                if 'weight' in course_data:
                    weight = float(course_data['weight'])
                    if not (0 < weight <= 5.0):
                        return {"error": "课程权重必须在0-5之间"}, 400
                    update_fields.append("weight = %s")
                    params.append(weight)
                
                if 'color' in course_data:
                    update_fields.append("color = %s")
                    params.append(course_data['color'])
                
                if 'exam_ratio' in course_data:
                    exam_ratio = float(course_data['exam_ratio'])
                    if not (0 <= exam_ratio <= 1.0):
                        return {"error": "考试权重必须在0-1之间"}, 400
                    update_fields.append("exam_ratio = %s")
                    params.append(exam_ratio)
                
                if not update_fields:
                    return {"error": "没有可更新的字段"}, 400
                
                # 执行更新
                params.extend([course_id, user_id])
                cursor.execute(f"""
                    UPDATE courses SET {', '.join(update_fields)}
                    WHERE id = %s AND user_id = %s
                """, params)
                
                connection.commit()
                connection.close()
                
                return {"message": "课程更新成功"}, 200
                
        except Exception as e:
            return {"error": f"更新课程失败: {str(e)}"}, 500
    
    @staticmethod
    def delete_course(user_id: int, course_id: int) -> Tuple[Dict[str, Any], int]:
        """删除课程"""
        try:
            connection = get_db_connection()
            with connection.cursor() as cursor:
                # 验证课程归属并删除
                cursor.execute(
                    "DELETE FROM courses WHERE id = %s AND user_id = %s",
                    (course_id, user_id)
                )
                
                if cursor.rowcount == 0:
                    connection.close()
                    return {"error": "课程不存在或无权限"}, 404
                
                connection.commit()
                connection.close()
                
                return {"message": "课程删除成功"}, 200
                
        except Exception as e:
            return {"error": f"删除课程失败: {str(e)}"}, 500
    
    @staticmethod
    def create_event(user_id: int, event_data: Dict[str, Any]) -> Tuple[Dict[str, Any], int]:
        """创建学习事件"""
        try:
            course_id = event_data.get('course_id')
            title = event_data.get('title', '').strip()
            due = event_data.get('due')
            event_type = event_data.get('type', 'study')
            priority = int(event_data.get('priority', 1))
            
            if not title:
                return {"error": "事件标题不能为空"}, 400
            
            if event_type not in ['exam', 'ddl', 'study']:
                return {"error": "事件类型无效"}, 400
            
            if not due:
                return {"error": "截止时间不能为空"}, 400
            
            # 解析时间
            try:
                due_datetime = datetime.fromisoformat(due.replace('Z', '+00:00'))
            except:
                return {"error": "时间格式无效"}, 400
            
            connection = get_db_connection()
            with connection.cursor() as cursor:
                # 如果指定了课程，验证课程归属
                if course_id:
                    cursor.execute(
                        "SELECT id FROM courses WHERE id = %s AND user_id = %s",
                        (course_id, user_id)
                    )
                    if not cursor.fetchone():
                        connection.close()
                        return {"error": "指定的课程不存在"}, 404
                
                # 插入事件
                cursor.execute("""
                    INSERT INTO events (user_id, course_id, title, due, type, priority)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (user_id, course_id, title, due_datetime, event_type, priority))
                
                event_id = cursor.lastrowid
                connection.commit()
                connection.close()
                
                return {
                    "event_id": event_id,
                    "message": "事件创建成功"
                }, 201
                
        except Exception as e:
            return {"error": f"创建事件失败: {str(e)}"}, 500
    
    @staticmethod
    def get_user_events(user_id: int, start_date: Optional[str] = None, end_date: Optional[str] = None) -> Tuple[Dict[str, Any], int]:
        """获取用户的学习事件"""
        try:
            connection = get_db_connection()
            with connection.cursor(pymysql.cursors.DictCursor) as cursor:
                query = """
                    SELECT e.*, c.name as course_name, c.color as course_color
                    FROM events e
                    LEFT JOIN courses c ON e.course_id = c.id
                    WHERE e.user_id = %s
                """
                params = [user_id]
                
                # 添加时间范围过滤
                if start_date:
                    query += " AND e.due >= %s"
                    params.append(start_date)
                
                if end_date:
                    query += " AND e.due <= %s"
                    params.append(end_date)
                
                query += " ORDER BY e.due ASC"
                
                cursor.execute(query, params)
                events = cursor.fetchall()
                connection.close()
                
                # 格式化时间
                for event in events:
                    if event['due']:
                        event['due'] = event['due'].isoformat()
                
                return {
                    "events": events,
                    "total": len(events)
                }, 200
                
        except Exception as e:
            return {"error": f"获取事件列表失败: {str(e)}"}, 500


# 对外接口函数
def handle_create_course(user_id: int, course_data: Dict[str, Any]):
    """处理创建课程请求"""
    return CourseService.create_course(user_id, course_data)

def handle_get_courses(user_id: int):
    """处理获取课程列表请求"""
    return CourseService.get_user_courses(user_id)

def handle_update_course(user_id: int, course_id: int, course_data: Dict[str, Any]):
    """处理更新课程请求"""
    return CourseService.update_course(user_id, course_id, course_data)

def handle_delete_course(user_id: int, course_id: int):
    """处理删除课程请求"""
    return CourseService.delete_course(user_id, course_id)

def handle_create_event(user_id: int, event_data: Dict[str, Any]):
    """处理创建事件请求"""
    return CourseService.create_event(user_id, event_data)

def handle_get_events(user_id: int, start_date: Optional[str] = None, end_date: Optional[str] = None):
    """处理获取事件列表请求"""
    return CourseService.get_user_events(user_id, start_date, end_date)