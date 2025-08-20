"""
知识卡片生成服务
负责生成学习卡片、测验题和复习计划
"""
import json
import pymysql
from typing import Dict, List, Any, Tuple, Optional
from auth import get_db_connection
from smart_ai_service import _get_service
from material_service import MaterialService


class CardService:
    """知识卡片服务类"""
    
    @staticmethod
    def generate_card_prompt(text_content: str, title: str) -> str:
        """生成知识卡片的提示词"""
        # 限制文本长度，避免Token超限
        content_preview = text_content[:2000] if len(text_content) > 2000 else text_content
        
        return f"""你是专业的学习内容提炼助手。请基于文档内容生成学习卡片，必须严格按照JSON格式返回。

文档：{title}
内容：{content_preview}

请返回以下JSON格式（不要任何其他文字）：
{{
    "summary": "核心内容摘要（150字内）",
    "key_points": [
        "要点1",
        "要点2",
        "要点3",
        "要点4"
    ],
    "terms": [
        {{"term": "术语1", "definition": "定义1"}},
        {{"term": "术语2", "definition": "定义2"}}
    ],
    "examples": [
        {{"title": "例题1", "content": "题目", "solution": "解答"}}
    ],
    "study_plan": {{
        "difficulty": "中等",
        "review_frequency": "每周复习1次",
        "time_estimate": "30分钟",
        "tips": "重点理解概念"
    }}
}}

要求：关键点4-6个，术语2-5个，例题1-2个。只返回JSON，不要其他内容。"""

    @staticmethod
    def generate_quiz_prompt(text_content: str, title: str) -> str:
        """生成测验题的提示词"""
        return f"""基于给定文档内容生成测验题。

文档标题：{title}
文档内容：
{text_content[:3000]}...

请生成5道题：单选题3道、填空题2道。严格按照JSON格式返回：

{{
    "questions": [
        {{
            "type": "choice",
            "question": "题目内容",
            "options": ["A. 选项1", "B. 选项2", "C. 选项3", "D. 选项4"],
            "answer": "A",
            "explanation": "答案解析",
            "chunk_idx": [0, 1]
        }},
        {{
            "type": "fill",
            "question": "填空题内容，用______表示空白",
            "answer": "正确答案",
            "explanation": "答案解析", 
            "chunk_idx": [2]
        }}
    ]
}}

要求：
1. 题目要有一定难度，考查理解而非记忆
2. 选择题4个选项，只有1个正确答案
3. 填空题空白部分要合理
4. 每题都要有详细解析
5. chunk_idx表示题目依据的文档段落索引
6. 必须返回有效的JSON格式"""

    @staticmethod
    def parse_ai_response(response_text: str) -> Optional[Dict]:
        """解析AI返回的JSON响应"""
        try:
            if not response_text or not response_text.strip():
                return None

            # 多种方式尝试解析JSON
            response_text = response_text.strip()
            
            # 1. 直接解析
            try:
                return json.loads(response_text)
            except:
                pass
            
            # 2. 查找JSON块
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}')
            
            if start_idx >= 0 and end_idx > start_idx:
                json_str = response_text[start_idx:end_idx + 1]
                try:
                    return json.loads(json_str)
                except:
                    pass
            
            # 3. 创建默认结构
            print(f"[WARNING] JSON解析失败，使用默认结构。原文: {response_text[:200]}...")
            return {
                "summary": "AI生成内容解析失败，请重新生成",
                "key_points": ["内容解析失败", "请重新尝试生成"],
                "terms": [{"term": "解析错误", "definition": "AI返回格式不正确"}],
                "examples": [{"title": "示例", "content": "解析失败", "solution": "请重新生成"}],
                "study_plan": {
                    "difficulty": "中等",
                    "review_frequency": "待重新生成",
                    "time_estimate": "未知",
                    "tips": "请重新生成卡片"
                }
            }
            
        except Exception as e:
            print(f"[ERROR] JSON解析异常: {e}")
            return None
    
    @staticmethod
    def generate_cards_for_material(material_id: int) -> Tuple[Dict[str, Any], int]:
        """为资料生成知识卡片和测验"""
        try:
            # 获取资料信息和文本内容
            connection = get_db_connection()
            with connection.cursor(pymysql.cursors.DictCursor) as cursor:
                cursor.execute("""
                    SELECT m.*, c.user_id 
                    FROM materials m
                    JOIN courses c ON m.course_id = c.id
                    WHERE m.id = %s
                """, (material_id,))
                
                material = cursor.fetchone()
                if not material:
                    connection.close()
                    return {"error": "资料不存在"}, 404
                
                # 检查是否已生成卡片
                cursor.execute(
                    "SELECT id FROM cards WHERE material_id = %s",
                    (material_id,)
                )
                if cursor.fetchone():
                    connection.close()
                    return {"error": "该资料已生成知识卡片"}, 409
            
            # 提取文本内容
            text_content = MaterialService.extract_text_from_file(
                material['url'], material['type']
            )
            
            if not text_content or len(text_content.strip()) < 100:
                return {"error": "文档内容太少，无法生成卡片"}, 400
            
            # 使用AI生成卡片内容
            try:
                ai_service = _get_service()
                print(f"[DEBUG] 开始AI生成卡片，文本长度: {len(text_content)}")
                
                # 生成知识卡片
                card_prompt = CardService.generate_card_prompt(text_content, material['title'])
                print(f"[DEBUG] 发送卡片生成请求...")
                card_response, card_status = ai_service.get_ai_response(card_prompt)
                
                if card_status != 200:
                    print(f"[ERROR] AI卡片生成失败，状态码: {card_status}")
                    return {"error": "AI服务暂时不可用，请稍后重试"}, 503
                
                card_data = CardService.parse_ai_response(card_response.get('message', ''))
                print(f"[DEBUG] 卡片数据解析结果: {'成功' if card_data else '失败'}")
                
                # 生成测验题（可选，失败不影响主流程）
                quiz_data = {"questions": []}
                try:
                    quiz_prompt = CardService.generate_quiz_prompt(text_content, material['title'])
                    quiz_response, quiz_status = ai_service.get_ai_response(quiz_prompt)
                    if quiz_status == 200:
                        quiz_data = CardService.parse_ai_response(quiz_response.get('message', '')) or {"questions": []}
                except Exception as quiz_error:
                    print(f"[WARNING] 测验生成失败: {quiz_error}")
                
            except Exception as ai_error:
                print(f"[ERROR] AI服务调用失败: {ai_error}")
                return {"error": f"AI生成失败: {str(ai_error)}"}, 500
            
            if not card_data:
                return {"error": "AI生成卡片内容失败，请检查文档内容或重试"}, 500
            
            # 确保必要字段存在
            card_content = {
                "summary": card_data.get("summary", ""),
                "key_points": card_data.get("key_points", [])[:8],
                "terms": card_data.get("terms", [])[:10],
                "examples": card_data.get("examples", [])[:3],
                "study_plan": card_data.get("study_plan", {})
            }
            
            quiz_content = quiz_data if quiz_data else {"questions": []}
            
            # 保存到数据库
            with connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO cards (material_id, summary, key_points, terms, examples, quiz)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                    material_id,
                    card_content["summary"],
                    json.dumps(card_content["key_points"], ensure_ascii=False),
                    json.dumps(card_content["terms"], ensure_ascii=False),
                    json.dumps(card_content["examples"], ensure_ascii=False),
                    json.dumps(quiz_content, ensure_ascii=False)
                ))
                
                card_id = cursor.lastrowid
                connection.commit()
                connection.close()
            
            return {
                "card_id": card_id,
                "material_id": material_id,
                "summary": card_content["summary"],
                "key_points_count": len(card_content["key_points"]),
                "terms_count": len(card_content["terms"]),
                "examples_count": len(card_content["examples"]),
                "quiz_count": len(quiz_content.get("questions", [])),
                "message": "知识卡片生成成功"
            }, 201
            
        except Exception as e:
            return {"error": f"生成知识卡片失败: {str(e)}"}, 500
    
    @staticmethod
    def get_material_cards(material_id: int, user_id: int) -> Tuple[Dict[str, Any], int]:
        """获取资料的知识卡片"""
        try:
            connection = get_db_connection()
            with connection.cursor(pymysql.cursors.DictCursor) as cursor:
                # 验证权限并获取卡片
                cursor.execute("""
                    SELECT cards.*, materials.title as material_title
                    FROM cards
                    JOIN materials ON cards.material_id = materials.id
                    JOIN courses ON materials.course_id = courses.id
                    WHERE cards.material_id = %s AND courses.user_id = %s
                """, (material_id, user_id))
                
                card = cursor.fetchone()
                if not card:
                    connection.close()
                    return {"error": "知识卡片不存在或无权限"}, 404
                
                connection.close()
                
                # 解析JSON字段
                try:
                    card['key_points'] = json.loads(card['key_points']) if card['key_points'] else []
                    card['terms'] = json.loads(card['terms']) if card['terms'] else []
                    card['examples'] = json.loads(card['examples']) if card['examples'] else []
                    card['quiz'] = json.loads(card['quiz']) if card['quiz'] else {}
                except:
                    pass
                
                # 格式化时间
                if card['created_at']:
                    card['created_at'] = card['created_at'].isoformat()
                
                return {"card": card}, 200
                
        except Exception as e:
            return {"error": f"获取知识卡片失败: {str(e)}"}, 500
    
    @staticmethod
    def regenerate_quiz(material_id: int, user_id: int) -> Tuple[Dict[str, Any], int]:
        """重新生成测验题"""
        try:
            connection = get_db_connection()
            with connection.cursor(pymysql.cursors.DictCursor) as cursor:
                # 验证权限并获取资料信息
                cursor.execute("""
                    SELECT m.* FROM materials m
                    JOIN courses c ON m.course_id = c.id
                    WHERE m.id = %s AND c.user_id = %s
                """, (material_id, user_id))
                
                material = cursor.fetchone()
                if not material:
                    connection.close()
                    return {"error": "资料不存在或无权限"}, 404
                
                # 检查卡片是否存在
                cursor.execute(
                    "SELECT id FROM cards WHERE material_id = %s",
                    (material_id,)
                )
                card = cursor.fetchone()
                if not card:
                    connection.close()
                    return {"error": "请先生成知识卡片"}, 404
            
            # 提取文本内容
            text_content = MaterialService.extract_text_from_file(
                material['url'], material['type']
            )
            
            # 使用AI重新生成测验
            ai_service = _get_service()
            quiz_prompt = CardService.generate_quiz_prompt(text_content, material['title'])
            quiz_response, _ = ai_service.get_ai_response(quiz_prompt)
            quiz_data = CardService.parse_ai_response(quiz_response.get('message', ''))
            
            if not quiz_data:
                return {"error": "AI生成测验失败，请重试"}, 500
            
            # 更新数据库
            with connection.cursor() as cursor:
                cursor.execute("""
                    UPDATE cards SET quiz = %s WHERE material_id = %s
                """, (json.dumps(quiz_data, ensure_ascii=False), material_id))
                
                connection.commit()
                connection.close()
            
            return {
                "material_id": material_id,
                "quiz_count": len(quiz_data.get("questions", [])),
                "quiz": quiz_data,
                "message": "测验题重新生成成功"
            }, 200
            
        except Exception as e:
            return {"error": f"重新生成测验失败: {str(e)}"}, 500


# 对外接口函数
def handle_generate_cards(material_id: int):
    """处理生成知识卡片请求"""
    return CardService.generate_cards_for_material(material_id)

def handle_get_cards(material_id: int, user_id: int):
    """处理获取知识卡片请求"""
    return CardService.get_material_cards(material_id, user_id)

def handle_regenerate_quiz(material_id: int, user_id: int):
    """处理重新生成测验请求"""
    return CardService.regenerate_quiz(material_id, user_id)