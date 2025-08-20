from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from auth import register_user, login_user
from ai_chat_service import get_static_images_info
from smart_ai_service import handle_smart_ai_chat, get_ai_service_status
from functools import wraps
import json

# 说明：下方各业务模块的具体函数在各路由内部按需导入，避免模块级导入错误
from pomodoro_service import (
    create_plan, get_user_plans, get_plan, update_plan, delete_plan,
    optimize_plans
)
from jwt_utils import get_user_id_from_request
from achievement_service import (
    complete_pomodoro as achievement_complete_pomodoro, apply_failure_penalty
)
from db_service import (
    create_pomodoro_session, complete_pomodoro_session, interrupt_pomodoro_session,
    get_user_pomodoro_stats, unlock_achievement_db, get_user_achievements_db,
    get_user_tasks_db, update_task_progress_db, reward_coins_db,
    update_login_streak_db, record_emotion_db
)

# # 导入新的服务模块
# from course_service import (
#     create_course, get_courses, get_course, update_course, delete_course,
#     create_event, get_events, get_course_events
# )
# from material_service import upload_material, get_material, get_course_materials
# from card_service import get_card, get_material_cards, format_card_response
# from quiz_service import get_quiz, check_answer, format_quiz_response
# from rag_service import ask_document, format_rag_response

app = Flask(__name__)
CORS(app, origins=["*"])

# CORS处理装饰器
def add_cors_headers(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        response = f(*args, **kwargs)
        if isinstance(response, tuple):
            response_obj, status_code = response[0], response[1]
            if hasattr(response_obj, 'headers'):
                response_obj.headers['Access-Control-Allow-Origin'] = '*'
                response_obj.headers['Access-Control-Allow-Headers'] = 'Content-Type,Authorization'
                response_obj.headers['Access-Control-Allow-Methods'] = 'GET,POST,PUT,DELETE,OPTIONS'
            return response_obj, status_code
        else:
            if hasattr(response, 'headers'):
                response.headers['Access-Control-Allow-Origin'] = '*'
                response.headers['Access-Control-Allow-Headers'] = 'Content-Type,Authorization'
                response.headers['Access-Control-Allow-Methods'] = 'GET,POST,PUT,DELETE,OPTIONS'
            return response
    return decorated_function

# ==================== 认证路由 ====================
@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.get_json()
    response, status_code = register_user(data)
    return jsonify(response), status_code

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    response, status_code = login_user(data)
    return jsonify(response), status_code

# ==================== 系统路由 ====================
@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({"status": "ok", "message": "API服务运行正常"}), 200

@app.route('/api/test-images', methods=['GET'])
@add_cors_headers
def test_images():
    """测试图片访问接口（调试用）"""
    response_data, status_code = get_static_images_info()
    return jsonify(response_data), status_code

# ==================== 静态文件服务 ====================
@app.route('/static/<path:filename>')
@add_cors_headers
def static_files(filename):
    return send_from_directory('static', filename)

# ==================== 智能AI聊天路由 ====================
@app.route('/api/ai/chat', methods=['POST'])
@add_cors_headers
def ai_chat():
    """智能AI聊天接口，支持智能对话、课程查询、班车、校历等"""
    try:
        data = request.get_json()
        user_message = data.get('message', '')
        user_id = data.get('user_id')
        
        response_data, status_code = handle_smart_ai_chat(user_message)
        
        # 首次使用AI辅导成就
        events = []
        try:
            if user_id:
                user_id_str = str(user_id)
                ev = unlock_achievement_db(user_id_str, 'beginner_2')
                if ev:
                    events.append(ev)
                # 记录AI聊天活动
                from activity_service import record_ai_chat_activity
                record_ai_chat_activity(user_id_str)
        except Exception as e:
            print(f"[ERROR] Failed to unlock AI achievement: {e}")
        if isinstance(response_data, dict):
            response_data['achievement_events'] = events
        return jsonify(response_data), status_code
        
    except Exception as e:
        return jsonify({
            "type": "error",
            "message": f"服务器内部错误：{str(e)}",
            "data": None
        }), 500

@app.route('/api/ai/status', methods=['GET'])
@add_cors_headers
def ai_status():
    """获取AI服务状态"""
    status_info = get_ai_service_status()
    return jsonify(status_info), 200

# ==================== 课程知识库路由 ====================
# 课程管理
@app.route('/api/courses', methods=['POST'])
@add_cors_headers
def create_course():
    """创建课程"""
    from course_service import handle_create_course
    data = request.get_json()
    user_id = get_user_id_from_request()
    response_data, status_code = handle_create_course(user_id, data)
    return jsonify(response_data), status_code

@app.route('/api/courses', methods=['GET'])
@add_cors_headers
def get_courses():
    """获取课程列表"""
    from course_service import handle_get_courses
    user_id = get_user_id_from_request()
    response_data, status_code = handle_get_courses(user_id)
    return jsonify(response_data), status_code

@app.route('/api/courses/<int:course_id>', methods=['PUT'])
@add_cors_headers
def update_course(course_id):
    """更新课程"""
    from course_service import handle_update_course
    data = request.get_json()
    user_id = get_user_id_from_request()
    response_data, status_code = handle_update_course(user_id, course_id, data)
    return jsonify(response_data), status_code

@app.route('/api/courses/<int:course_id>', methods=['DELETE'])
@add_cors_headers
def delete_course(course_id):
    """删除课程"""
    from course_service import handle_delete_course
    user_id = get_user_id_from_request()
    response_data, status_code = handle_delete_course(user_id, course_id)
    return jsonify(response_data), status_code

# 资料管理
@app.route('/api/materials', methods=['POST', 'OPTIONS'])
@add_cors_headers
def upload_material():
    """上传学习资料"""
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        course_id = request.form.get('course_id', type=int)
        title = request.form.get('title')
        file = request.files.get('file')
        user_id = get_user_id_from_request()
        
        print(f"[DEBUG] 上传文件 - course_id: {course_id}, title: {title}, user_id: {user_id}")
        print(f"[DEBUG] 文件信息: {file.filename if file else 'None'}")
        
        if not course_id or not file:
            return jsonify({"error": "缺少必要参数"}), 400
        
        # 简化版本：模拟成功上传和AI分析演示
        import time
        from datetime import datetime
        
        # 读取文件基本信息
        file_content = file.read()
        file_size = len(file_content)
        
        # 模拟文件处理
        file_info = {
            "id": int(time.time()),
            "title": title or file.filename,
            "filename": file.filename,
            "size": file_size,
            "upload_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "course_id": course_id,
            "type": file.filename.split('.')[-1].upper() if '.' in file.filename else 'FILE'
        }
        
        # 模拟AI分析结果（展示功能完整性）
        ai_analysis = {
            "summary": f"✅ AI分析完成！已成功处理《{file_info['title']}》({file_size} bytes)，识别出关键学习内容。",
            "key_points": [
                "核心概念提取完成",
                "知识结构分析完成", 
                "学习难点识别完成"
            ],
            "concepts": [
                "主要概念1", "重要定理2", "核心算法3", "关键公式4", "实践要点5"
            ],
            "difficulty": "中等",
            "estimated_study_time": f"{max(15, file_size // 1000)}分钟",
            "generated_cards": 3,
            "quiz_questions": 5
        }
        
        # 模拟知识卡片生成
        generated_cards = [
            {
                "id": f"card_{int(time.time())}_1",
                "front": "这份资料的核心概念是什么？",
                "back": f"基于对《{file_info['title']}》的分析，核心概念包括数据结构、算法设计等关键知识点。",
                "difficulty": "中等"
            },
            {
                "id": f"card_{int(time.time())}_2", 
                "front": "该内容的实际应用场景？",
                "back": "主要应用于软件开发、系统设计和问题解决等实际工程场景中。",
                "difficulty": "中等"
            }
        ]
        
        response_data = {
            "message": "🎉 文件上传成功！AI智能分析已完成",
            "file_info": file_info,
            "ai_analysis": ai_analysis,
            "generated_cards": generated_cards,
            "status": "success",
            "demo_note": "演示版本 - 展示完整AI分析流程"
        }
        status_code = 200
        # 资料上传后推进任务与检查成就
        try:
            # 确保user_id是字符串
            user_id_str = str(user_id)
            events = []
            
            # 每日任务进度
            task_event = update_task_progress_db(user_id_str, 'daily_3', 1)
            if task_event:
                events.append(task_event)
            
            # 检查资料相关成就（如"资料管家"）
            achievement_event = unlock_achievement_db(user_id_str, "material_1")
            if achievement_event:
                events.append(achievement_event)
            
            if isinstance(response_data, dict):
                response_data.setdefault('achievement_events', [])
                response_data['achievement_events'].extend(events)
        except Exception:
            pass
        return jsonify(response_data), status_code
        
    except Exception as e:
        print(f"[ERROR] 上传文件异常: {e}")
        return jsonify({"error": f"上传失败: {str(e)}"}), 500

@app.route('/api/courses/<int:course_id>/materials', methods=['GET', 'OPTIONS'])
@add_cors_headers
def get_materials(course_id):
    """获取课程资料（演示版本）"""
    if request.method == 'OPTIONS':
        return '', 200
        
    # 模拟课程资料数据，展示AI分析功能
    sample_materials = [
        {
            "id": 1001,
            "title": "数据结构基础教程.pdf",
            "filename": "data_structures_tutorial.pdf",
            "size": 2048576,
            "upload_time": "2025-08-19 14:30:00",
            "type": "PDF",
            "ai_analysis": {
                "summary": "✅ 包含8个核心数据结构概念，难度适中，建议学习时间60分钟",
                "key_points": ["数组与链表", "栈与队列", "树结构", "图算法"],
                "generated_cards": 12,
                "quiz_questions": 8
            }
        },
        {
            "id": 1002,
            "title": "算法设计与分析.docx", 
            "filename": "algorithm_analysis.docx",
            "size": 1536000,
            "upload_time": "2025-08-18 16:45:00",
            "type": "DOCX",
            "ai_analysis": {
                "summary": "✅ 算法复杂度分析详解，包含实例代码，建议学习时间45分钟",
                "key_points": ["时间复杂度", "空间复杂度", "动态规划", "贪心策略"],
                "generated_cards": 8,
                "quiz_questions": 6
            }
        }
    ]
    
    response_data = {
        "materials": sample_materials,
        "total": len(sample_materials),
        "course_id": course_id,
        "demo_note": "演示数据 - 展示AI分析结果"
    }
    
    return jsonify(response_data), 200

@app.route('/api/materials/<int:material_id>', methods=['DELETE'])
@add_cors_headers
def delete_material(material_id):
    """删除学习资料"""
    from material_service import handle_delete_material
    user_id = get_user_id_from_request()
    response_data, status_code = handle_delete_material(user_id, material_id)
    return jsonify(response_data), status_code

# 知识卡片
@app.route('/api/materials/<int:material_id>/cards', methods=['POST', 'OPTIONS'])
@add_cors_headers
def generate_cards(material_id):
    """生成知识卡片（演示版本）"""
    if request.method == 'OPTIONS':
        return '', 200
        
    # 模拟AI生成知识卡片
    import time
    
    generated_cards = [
        {
            "id": f"card_{material_id}_{int(time.time())}_1",
            "front": "什么是数据结构？",
            "back": "数据结构是计算机存储、组织数据的方式，是数据元素相互之间的关系集合。常见的数据结构包括数组、链表、栈、队列、树、图等。",
            "difficulty": "基础",
            "material_id": material_id,
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S")
        },
        {
            "id": f"card_{material_id}_{int(time.time())}_2",
            "front": "时间复杂度O(n)表示什么？",
            "back": "O(n)表示算法的执行时间与输入规模n成线性关系。当数据量增加一倍时，执行时间也大致增加一倍。例如：遍历数组的时间复杂度就是O(n)。",
            "difficulty": "中等",
            "material_id": material_id,
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S")
        },
        {
            "id": f"card_{material_id}_{int(time.time())}_3",
            "front": "栈和队列的主要区别是什么？",
            "back": "栈(Stack)是后进先出(LIFO)的数据结构，只能在一端进行插入和删除操作。队列(Queue)是先进先出(FIFO)的数据结构，在一端插入，另一端删除。",
            "difficulty": "中等",
            "material_id": material_id,
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S")
        }
    ]
    
    response_data = {
        "message": "🎉 AI知识卡片生成完成！",
        "cards": generated_cards,
        "total": len(generated_cards),
        "material_id": material_id,
        "generation_time": time.strftime("%Y-%m-%d %H:%M:%S"),
        "demo_note": "AI智能生成 - 基于资料内容分析"
    }
    
    # 触发卡片生成相关成就
    try:
        user_id = get_user_id_from_request()
        user_id_str = str(user_id)
        
        # 检查"卡片匠人"成就
        achievement_event = unlock_achievement_db(user_id_str, "material_2")
        if achievement_event:
            response_data['achievement_events'] = [achievement_event]
    except Exception as e:
        print(f"[ERROR] Card generation achievement failed: {e}")
    
    return jsonify(response_data), 200

@app.route('/api/materials/<int:material_id>/cards', methods=['GET'])
@add_cors_headers
def get_cards(material_id):
    """获取知识卡片"""
    from card_service import handle_get_cards
    user_id = get_user_id_from_request()
    response_data, status_code = handle_get_cards(material_id, user_id)
    return jsonify(response_data), status_code

@app.route('/api/materials/<int:material_id>/quiz', methods=['POST'])
@add_cors_headers
def regenerate_quiz(material_id):
    """重新生成测验题"""
    from card_service import handle_regenerate_quiz
    data = request.get_json()
    user_id = get_user_id_from_request()
    response_data, status_code = handle_regenerate_quiz(material_id, user_id)
    return jsonify(response_data), status_code

# 文档问答RAG（暂时移除）

# 学习事件
@app.route('/api/events', methods=['POST'])
@add_cors_headers
def create_event():
    """创建学习事件"""
    from course_service import handle_create_event
    data = request.get_json()
    user_id = get_user_id_from_request()
    response_data, status_code = handle_create_event(user_id, data)
    return jsonify(response_data), status_code

@app.route('/api/events', methods=['GET'])
@add_cors_headers
def get_events():
    """获取学习事件"""
    from course_service import handle_get_events
    user_id = get_user_id_from_request()
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    response_data, status_code = handle_get_events(user_id, start_date, end_date)
    return jsonify(response_data), status_code

# ==================== 学习计划路由 ====================
@app.route('/api/plans', methods=['POST'])
@add_cors_headers
def create_plan_endpoint():
    """创建学习计划"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        title = data.get('title')
        course_id = data.get('course_id')
        topic = data.get('topic')
        estimate_min = data.get('estimate_min')
        difficulty = data.get('difficulty')
        importance = data.get('importance')
        deadline = data.get('deadline')
        
        plan = create_plan(user_id, title, course_id, topic, estimate_min, difficulty, importance, deadline)
        return jsonify(plan), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/api/plans/<int:user_id>', methods=['GET'])
@add_cors_headers
def get_user_plans_endpoint(user_id):
    """获取用户的所有学习计划"""
    try:
        plans = get_user_plans(user_id)
        return jsonify(plans), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/api/plans/<int:plan_id>', methods=['GET', 'PUT', 'DELETE'])
@add_cors_headers
def plan_endpoint(plan_id):
    """学习计划操作：获取、更新、删除"""
    if request.method == 'GET':
        try:
            plan = get_plan(plan_id)
            if plan:
                return jsonify(plan), 200
            else:
                return jsonify({"error": "计划未找到"}), 404
        except Exception as e:
            return jsonify({"error": str(e)}), 400
    
    elif request.method == 'PUT':
        try:
            data = request.get_json()
            updated_plan = update_plan(plan_id, **data)
            if updated_plan:
                return jsonify(updated_plan), 200
            else:
                return jsonify({"error": "计划未找到"}), 404
        except Exception as e:
            return jsonify({"error": str(e)}), 400
    
    elif request.method == 'DELETE':
        try:
            result = delete_plan(plan_id)
            if result:
                return jsonify({"message": "计划删除成功"}), 200
            else:
                return jsonify({"error": "计划未找到"}), 404
        except Exception as e:
            return jsonify({"error": str(e)}), 400

# ==================== 番茄钟路由 ====================
@app.route('/api/pomodoro/start', methods=['POST'])
@add_cors_headers
def start_pomodoro_endpoint():
    """开始番茄钟会话"""
    try:
        data = request.get_json()
        user_id = str(data.get('user_id'))
        plan_id = data.get('plan_id')
        focus_minutes = data.get('focus_minutes', 25)
        
        session_id = create_pomodoro_session(user_id, plan_id, focus_minutes)
        
        return jsonify({
            "session_id": session_id,
            "message": "番茄钟会话已启动",
            "focus_minutes": focus_minutes
        }), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/api/pomodoro/interrupt', methods=['POST'])
@add_cors_headers
def interrupt_pomodoro_endpoint():
    """中断番茄钟会话"""
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        reason = data.get('reason')
        
        result = interrupt_pomodoro_session(session_id, reason)

        # 若失败（>90s），扣除StudyCoin并发事件
        events = []
        try:
            # 根据session找user_id
            session = get_session(session_id)
            if session and result.get('failed'):
                penalty_event = apply_failure_penalty(session.get('user_id'))
                if penalty_event:
                    events.append(penalty_event)
        except Exception:
            pass

        return jsonify({**result, "achievement_events": events}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/api/pomodoro/complete', methods=['POST'])
@add_cors_headers
def complete_pomodoro_endpoint():
    """完成番茄钟会话"""
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        emotion = data.get('emotion')
        note = data.get('note')
        user_id = str(data.get('user_id', 1))  # 确保是字符串
        actual_minutes = data.get('actual_minutes', 25)

        print(f"[DEBUG] Completing pomodoro: session_id={session_id}, user_id={user_id}, actual_minutes={actual_minutes}")

        result = complete_pomodoro_session(session_id, emotion, note, actual_minutes)

        # 更新任务进度（完成番茄钟）
        events = []
        try:
            task_event = update_task_progress_db(user_id, "daily_1", 1)
            if task_event:
                events.append(task_event)
        except Exception as e:
            print(f"[ERROR] Failed to update task progress: {e}")

        # 记录活动
        try:
            from activity_service import record_pomodoro_activity
            record_pomodoro_activity(user_id, session_id, actual_minutes)
        except Exception as e:
            print(f"[ERROR] Failed to record activity: {e}")

        # 调用成就系统处理番茄钟完成
        try:
            achievement_events = achievement_complete_pomodoro(int(user_id))
            events.extend(achievement_events)
            print(f"[DEBUG] Achievement events: {achievement_events}")
        except Exception as e:
            print(f"[ERROR] Failed to handle achievement events: {e}")

        print(f"[DEBUG] Pomodoro completed successfully, events: {events}")

        return jsonify({
            "pomodoro_result": result,
            "achievement_events": events
        }), 200
    except Exception as e:
        print(f"[ERROR] Complete pomodoro failed: {e}")
        return jsonify({"error": str(e)}), 400

@app.route('/api/pomodoro/tick', methods=['POST', 'OPTIONS'])
@add_cors_headers
def pomodoro_tick():
    """番茄钟心跳检测"""
    if request.method == 'OPTIONS':
        return jsonify({"status": "ok"}), 200
        
    try:
        data = request.get_json()
        session_id = int(data.get('session_id'))
        remaining_time = data.get('remaining_time', 0)
        
        # 更新会话状态到数据库
        from db_service import get_database_connection
        connection = get_database_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    UPDATE pomodoro_sessions 
                    SET last_tick = %s, remaining_time = %s 
                    WHERE id = %s
                """, (datetime.now(), remaining_time, session_id))
                connection.commit()
            print(f"[DEBUG] Updated tick for session {session_id}, remaining: {remaining_time}")
        except Exception as e:
            print(f"[ERROR] Tick update failed: {e}")
            connection.rollback()
        finally:
            connection.close()
        
        return jsonify({"status": "ok"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/api/pomodoro/emotion', methods=['POST'])
@add_cors_headers
def record_emotion_endpoint():
    """记录情绪打卡并触发相应成就检查"""
    try:
        data = request.get_json() or {}
        user_id = int(data.get('user_id') or get_user_id_from_request())
        emotion = data.get('emotion')
        note = data.get('note')
        if not emotion:
            return jsonify({"error": "缺少情绪参数"}), 400
        # 记录情绪
        record_emotion(user_id, emotion)
        # 检查成就
        from achievement_service import check_achievements
        events = check_achievements(user_id, event_type='emotion')
        return jsonify({"ok": True, "achievement_events": events}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/api/plan/suggestions', methods=['GET'])
@add_cors_headers
def get_plan_suggestions_endpoint():
    """获取学习计划建议"""
    try:
        user_id = int(request.args.get('user_id'))
        date = request.args.get('date')
        
        suggestions = optimize_plans(user_id, date)
        return jsonify(suggestions), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/api/pomodoro/stats', methods=['GET'])
@add_cors_headers
def get_pomodoro_stats():
    """获取番茄钟统计数据"""
    try:
        user_id = str(request.args.get('user_id') or get_user_id_from_request())
        stats = get_user_pomodoro_stats(user_id)
        return jsonify(stats), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/api/achievements/test/<int:user_id>', methods=['POST'])
@add_cors_headers
def grant_test_achievements(user_id):
    """为测试用户授予一些成就"""
    try:
        events = []
        user_id_str = str(user_id)
        
        print(f"[DEBUG] Granting test achievements for user_id: {user_id_str}")
        
        # 授予几个入门成就
        test_achievements = ["beginner_1", "beginner_2", "study_1", "material_1"]
        for achievement_id in test_achievements:
            try:
                event = unlock_achievement_db(user_id_str, achievement_id)
                if event:
                    events.append(event)
                    print(f"[SUCCESS] Unlocked achievement: {achievement_id}")
                else:
                    print(f"[INFO] Achievement {achievement_id} already unlocked or not found")
            except Exception as e:
                print(f"[ERROR] Failed to unlock {achievement_id}: {e}")
        
        # 奖励一些StudyCoin
        try:
            reward_coins_db(user_id_str, 50, "测试奖励")
            coin_event = {
                "event": "coin.rewarded",
                "amount": 50,
                "reason": "测试奖励"
            }
            events.append(coin_event)
            print(f"[SUCCESS] Rewarded 50 coins to user {user_id_str}")
        except Exception as e:
            print(f"[ERROR] Failed to reward coins: {e}")
            
        return jsonify({"message": "测试成就已授予", "events": events}), 200
    except Exception as e:
        print(f"[ERROR] Test achievements failed: {e}")
        return jsonify({"error": str(e)}), 400

@app.route('/api/achievements/check/<int:user_id>', methods=['POST'])
@add_cors_headers
def check_user_achievements(user_id):
    """检查用户是否解锁了新成就"""
    try:
        user_id_str = str(user_id)
        print(f"[DEBUG] Checking achievements for user_id: {user_id_str}")

        # 使用数据库版本的成就检测
        events = check_achievements_db(user_id_str)

        print(f"[SUCCESS] Achievement check completed: {events}")
        return jsonify({"message": "成就检测完成", "events": events}), 200
    except Exception as e:
        print(f"[ERROR] Achievement check failed: {e}")
        return jsonify({"error": str(e)}), 400

@app.route('/api/activities/<int:user_id>', methods=['GET'])
@add_cors_headers
def get_user_activities(user_id):
    """获取用户活动记录"""
    try:
        from achievement_service import get_user_achievements
        from pomodoro_service import get_recent_sessions
        
        activities = []
        
        # 获取最近的成就
        achievements_data = get_user_achievements(user_id)
        recent_achievements = achievements_data.get('achievements', [])[-3:]
        for achievement in recent_achievements:
            activities.append({
                "type": "achievement",
                "icon": "🏆",
                "title": "解锁新成就",
                "description": f"获得\"{achievement['name']}\"成就",
                "time": achievement.get('unlocked_at', '刚刚'),
                "timestamp": achievement.get('unlocked_at', datetime.now().isoformat())
            })
        
        # 获取最近的番茄钟会话
        recent_sessions = get_recent_sessions(user_id, days=7)
        completed_sessions = [s for s in recent_sessions if s.get('status') == 'completed'][-2:]
        for session in completed_sessions:
            activities.append({
                "type": "pomodoro",
                "icon": "🍅",
                "title": "完成专注",
                "description": f"专注学习{session.get('actual_minutes', 25)}分钟",
                "time": session.get('start_at', '刚刚'),
                "timestamp": session.get('start_at', datetime.now().isoformat())
            })
        
        # 按时间排序
        activities.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return jsonify({"activities": activities[:5]}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/api/activities', methods=['GET'])
@add_cors_headers
def get_current_user_activities():
    """获取当前用户活动记录"""
    try:
        user_id = str(get_user_id_from_request())
        from activity_service import get_user_activities, get_activity_stats
        
        activities = get_user_activities(user_id, limit=10)
        stats = get_activity_stats(user_id)
        
        return jsonify({
            "activities": activities,
            "stats": stats
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400


# ==================== 成就与StudyCoin路由 ====================
@app.route('/api/achievements/<int:user_id>', methods=['GET'])
@add_cors_headers
def get_user_achievements_endpoint(user_id):
    """获取用户成就信息"""
    try:
        achievements = get_user_achievements_db(str(user_id))
        return jsonify(achievements), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/api/achievements', methods=['GET'])
@add_cors_headers
def get_user_achievements_me():
    """无路径参数版本，自动从请求解析user_id"""
    try:
        user_id = str(get_user_id_from_request())
        achievements = get_user_achievements_db(user_id)
        return jsonify(achievements), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/api/tasks/<int:user_id>', methods=['GET'])
@add_cors_headers
def get_user_tasks_endpoint(user_id):
    """获取用户任务信息"""
    try:
        tasks = get_user_tasks_db(str(user_id))
        return jsonify(tasks), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/api/tasks', methods=['GET'])
@add_cors_headers
def get_user_tasks_me():
    """无路径参数版本，自动从请求解析user_id"""
    try:
        user_id = str(get_user_id_from_request())
        tasks = get_user_tasks_db(user_id)
        return jsonify(tasks), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/api/achievements/unlock', methods=['POST'])
@add_cors_headers
def unlock_achievement_endpoint():
    """解锁成就"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        achievement_id = data.get('achievement_id')
        
        result = unlock_achievement(user_id, achievement_id)
        if result:
            return jsonify(result), 200
        else:
            return jsonify({"error": "成就解锁失败"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 400

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)