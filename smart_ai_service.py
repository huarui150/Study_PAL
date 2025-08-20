import os
from dotenv import load_dotenv
import datetime
from typing import Dict, Any, Tuple, Optional
from openai import OpenAI

# 加载.env配置
load_dotenv()

class SmartAIService:
    """
    智能AI对话服务
    - 支持通义千问（DashScope OpenAI 兼容接口）
    - 内置班车/课程/校历/系统状态等快捷查询
    - 无法调用在线API时，回退到本地简单回复
    """

    def __init__(self) -> None:
        # 直接使用你的API密钥
        self.api_key = os.getenv("QWEN_API_KEY")
        self.model: str = "qwen-plus"
        self.client: Optional[OpenAI] = None
        
        try:
            self.client = OpenAI(
                api_key=self.api_key,
                base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
            )
            print("[SUCCESS] 通义千问API初始化成功")
        except Exception as e:
            print(f"[ERROR] 通义千问API初始化失败: {e}")
            self.client = None

    def get_ai_response(self, user_message: str, conversation_history: list = None) -> Tuple[Dict[str, Any], int]:
        """
        获取AI响应
        1) 特定功能查询 → 返回图片或状态
        2) 通义千问 → 智能问答
        3) 本地回退 → 简单提示
        """

        if not user_message or not user_message.strip():
            return self._create_error_response("消息不能为空")

        # 1. 特定功能查询
        special_response = self._check_special_queries(user_message)
        if special_response:
            return special_response

        # 2. 在线AI（通义千问）
        if self.client is not None:
            try:
                print(f"[DEBUG] 开始调用通义千问API: {user_message[:20]}...")
                reply_text = self._call_qwen_api(user_message)
                print(f"[DEBUG] 通义千问回复: {reply_text[:50]}...")
                return {
                    "type": "ai_response", 
                    "message": reply_text,
                    "data": reply_text,
                }, 200
            except Exception as e:
                print(f"[ERROR] 通义千问调用失败: {str(e)}")
                print(f"[ERROR] 错误类型: {type(e).__name__}")
        else:
            print("[DEBUG] client 为 None，跳过API调用")

        # 3. 本地回退
        return self._create_default_response(user_message)

    # ========= 私有方法 =========

    def _call_qwen_api(self, user_message: str) -> str:
        if self.client is None:
            raise RuntimeError("通义千问客户端未初始化")

        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system", 
                        "content": "你是大连理工大学的智能学习助手，名字叫StudyPAL+。你很友善、专业，擅长回答学习相关问题。请用中文回答，语言简洁明了。"
                    },
                    {"role": "user", "content": user_message},
                ],
                temperature=0.7,
                max_tokens=1500,
            )

            if (
                completion
                and completion.choices
                and completion.choices[0].message
                and completion.choices[0].message.content
            ):
                reply = completion.choices[0].message.content.strip()
                # 确保返回的文本是UTF-8编码
                return reply.encode('utf-8', errors='ignore').decode('utf-8')
            
            return "抱歉，我暂时无法生成合适的回答。"
            
        except Exception as e:
            print(f"[ERROR] API调用详细错误: {e}")
            raise e

    def _check_special_queries(self, user_message: str) -> Optional[Tuple[Dict[str, Any], int]]:
        text = user_message.lower()

        # 班车查询
        if any(k in text for k in ["班车", "公交", "bus"]):
            return self._create_image_response(
                response_type="bus_schedule",
                message="🚌 这是大连理工的班车时刻表：",
                image_filename="bus.jpg",
                data="真实班车数据已显示在图片中",
            )

        # 课程查询
        if any(k in text for k in ["课程", "课表", "形策", "class"]):
            return self._create_image_response(
                response_type="course_schedule",
                message="📚 这是大连理工的形策课程表：",
                image_filename="classes.png",
                data="真实课程数据已显示在图片中",
            )

        # 校历查询
        if any(k in text for k in ["校历", "日程", "event", "安排"]):
            return self._create_image_response(
                response_type="calendar_events",
                message="📅 这是大连理工的校历安排：",
                image_filename="events.jpg",
                data="真实校历数据已显示在图片中",
            )

        # 系统状态
        if any(k in text for k in ["状态", "系统", "status"]):
            return self._create_status_response()

        return None

    # ========= 响应构造 =========

    def _create_image_response(
        self, response_type: str, message: str, image_filename: str, data: Any
    ) -> Tuple[Dict[str, Any], int]:
        return {
            "type": response_type,
            "message": message,
            "image_url": f"/static/{image_filename}",
            "data": data,
        }, 200

    def _create_status_response(self) -> Tuple[Dict[str, Any], int]:
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
                "AI服务": "就绪",
            },
        }, 200

    def _create_default_response(self, user_message: str) -> Tuple[Dict[str, Any], int]:
        return {
            "type": "ai_response",
            "message": (
                "你好！我是大连理工学习助手 🎓\n\n"
                f"你刚才说：「{user_message}」\n\n"
                "我可以帮你查询：\n\n"
                "📚 课程表（输入'课程'或'课表'）\n"
                "🚌 班车时刻（输入'班车'）\n"
                "📅 校历安排（输入'校历'）\n"
                "💻 系统状态（输入'状态'）\n\n"
                "也可以直接问我学习相关问题，我会用AI来帮你解答。"
            ),
            "data": "AI助手已就绪",
        }, 200

    def _create_error_response(self, error_message: str) -> Tuple[Dict[str, Any], int]:
        return {
            "type": "error",
            "message": f"处理请求时出错：{error_message}",
            "data": None,
        }, 400


# ========= 模块级别的服务实例与对外方法 =========
_service_instance: Optional[SmartAIService] = None


def _get_service() -> SmartAIService:
    global _service_instance
    if _service_instance is None:
        _service_instance = SmartAIService()
    return _service_instance


def handle_smart_ai_chat(user_message: str):
    service = _get_service()
    return service.get_ai_response(user_message)


def get_ai_service_status() -> Dict[str, Any]:
    service = _get_service()
    status = "在线" if service.client is not None else "未配置（使用本地回退）"
    return {
        "service_name": "Smart AI Service",
        "status": status,
        "model": service.model,
        "provider": "Tongyi Qianwen (DashScope)",
        "configured": service.client is not None,
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }