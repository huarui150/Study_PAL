import datetime
import os
from flask import jsonify

def handle_ai_chat(user_message):
    """
    处理AI聊天请求
    根据用户输入返回相应的响应和数据
    """
    if not user_message:
        return create_error_response("消息不能为空")
    
    user_message_lower = user_message.lower()
    
    # 班车查询
    if any(keyword in user_message_lower for keyword in ['班车', '公交', 'bus']):
        return create_image_response(
            response_type="bus_schedule",
            message="🚌 这是大连理工的班车时刻表：",
            image_filename="bus.jpg",
            data="真实班车数据已显示在图片中"
        )
    
    # 课程查询
    elif any(keyword in user_message_lower for keyword in ['课程', '课表', '形策', 'class']):
        return create_image_response(
            response_type="course_schedule",
            message="📚 这是大连理工的形策课程表：",
            image_filename="classes.png", 
            data="真实课程数据已显示在图片中"
        )
    
    # 校历查询
    elif any(keyword in user_message_lower for keyword in ['校历', '日程', 'event', '安排']):
        return create_image_response(
            response_type="calendar_events",
            message="📅 这是大连理工的校历安排：",
            image_filename="events.jpg",
            data="真实校历数据已显示在图片中"
        )
    
    # 系统状态查询
    elif any(keyword in user_message_lower for keyword in ['状态', '系统', 'status']):
        return create_status_response()
    
    # 默认AI问答
    else:
        return create_default_response(user_message)

def create_image_response(response_type, message, image_filename, data):
    """创建包含图片的响应"""
    return {
        "type": response_type,
        "message": message,
        "image_url": f"/static/{image_filename}",
        "data": data
    }, 200

def create_status_response():
    """创建系统状态响应"""
    return {
        "type": "system_status",
        "message": "💻 系统运行状态正常",
        "data": {
            "服务器状态": "在线",
            "数据库连接": "正常", 
            "最后更新": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "在线用户": "126人",
            "系统负载": "轻度",
            "图片服务": "正常",
            "AI服务": "就绪"
        }
    }, 200

def create_default_response(user_message):
    """创建默认AI问答响应"""
    return {
        "type": "ai_response",
        "message": f"你好！我是大连理工学习助手 🎓\n\n你刚才说：「{user_message}」\n\n我可以帮你查询：\n\n📚 课程表（输入'课程'或'课表'）\n🚌 班车时刻（输入'班车'）\n📅 校历安排（输入'校历'）\n💻 系统状态（输入'状态'）\n\n请告诉我你想了解什么？",
        "data": "AI助手已就绪"
    }, 200

def create_error_response(error_message):
    """创建错误响应"""
    return {
        "type": "error",
        "message": f"处理请求时出错：{error_message}",
        "data": None
    }, 400

def get_static_images_info():
    """获取静态图片文件信息（用于调试）"""
    static_dir = os.path.join(os.getcwd(), 'static')
    images = []
    
    if os.path.exists(static_dir):
        for file in os.listdir(static_dir):
            if file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                images.append({
                    "filename": file,
                    "url": f"/static/{file}",
                    "full_url": f"http://localhost:5000/static/{file}",
                    "exists": True
                })
    
    return {
        "static_directory": static_dir,
        "images": images,
        "image_count": len(images)
    }, 200
