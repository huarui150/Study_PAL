"""
RAG文档问答服务
负责文档切片、向量化、检索和问答
"""
import json
import pymysql
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False
    print("[WARNING] numpy未安装，将使用简化的相似度计算")
from typing import Dict, List, Any, Tuple, Optional
from auth import get_db_connection
from smart_ai_service import _get_service
from material_service import MaterialService


class RAGService:
    """RAG问答服务类"""
    
    @staticmethod
    def simple_text_embedding(text: str) -> List[float]:
        """
        简单的文本向量化方法（基于字符频率）
        生产环境建议使用专业的embedding模型
        """
        # 简单的字符频率向量化（128维）
        char_freq = {}
        for char in text:
            if '\u4e00' <= char <= '\u9fff':  # 中文字符
                char_freq[char] = char_freq.get(char, 0) + 1
        
        # 取最常见的128个字符作为特征
        sorted_chars = sorted(char_freq.items(), key=lambda x: x[1], reverse=True)[:128]
        
        vector = [0.0] * 128
        for i, (char, freq) in enumerate(sorted_chars):
            vector[i] = freq / len(text)  # 归一化频率
        
        return vector
    
    @staticmethod
    def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
        """计算余弦相似度"""
        try:
            if HAS_NUMPY:
                a = np.array(vec1)
                b = np.array(vec2)
                
                dot_product = np.dot(a, b)
                norm_a = np.linalg.norm(a)
                norm_b = np.linalg.norm(b)
                
                if norm_a == 0 or norm_b == 0:
                    return 0.0
                
                return dot_product / (norm_a * norm_b)
            else:
                # 简化版本，不使用numpy
                if len(vec1) != len(vec2):
                    return 0.0
                
                dot_product = sum(a * b for a, b in zip(vec1, vec2))
                norm_a = sum(a * a for a in vec1) ** 0.5
                norm_b = sum(b * b for b in vec2) ** 0.5
                
                if norm_a == 0 or norm_b == 0:
                    return 0.0
                
                return dot_product / (norm_a * norm_b)
        except:
            return 0.0
    
    @staticmethod
    def create_embeddings_for_material(material_id: int) -> Tuple[Dict[str, Any], int]:
        """为资料创建文档切片和向量嵌入"""
        try:
            # 获取资料信息
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
                
                # 检查是否已创建嵌入
                cursor.execute(
                    "SELECT COUNT(*) as count FROM embeddings WHERE material_id = %s",
                    (material_id,)
                )
                existing_count = cursor.fetchone()['count']
                if existing_count > 0:
                    connection.close()
                    return {"error": f"该资料已创建了{existing_count}个文档切片"}, 409
            
            # 提取文本内容
            text_content = MaterialService.extract_text_from_file(
                material['url'], material['type']
            )
            
            if not text_content or len(text_content.strip()) < 100:
                return {"error": "文档内容太少，无法创建嵌入"}, 400
            
            # 切分文档
            chunks = MaterialService.chunk_text(text_content, chunk_size=700)
            
            if not chunks:
                return {"error": "文档切分失败"}, 400
            
            # 创建向量嵌入
            embeddings_data = []
            for i, chunk in enumerate(chunks):
                vector = RAGService.simple_text_embedding(chunk)
                embeddings_data.append((material_id, i, chunk, json.dumps(vector)))
            
            # 批量插入数据库
            with connection.cursor() as cursor:
                cursor.executemany("""
                    INSERT INTO embeddings (material_id, chunk_idx, text, vector)
                    VALUES (%s, %s, %s, %s)
                """, embeddings_data)
                
                connection.commit()
                connection.close()
            
            return {
                "material_id": material_id,
                "chunks_created": len(chunks),
                "total_characters": len(text_content),
                "message": "文档嵌入创建成功"
            }, 201
            
        except Exception as e:
            return {"error": f"创建文档嵌入失败: {str(e)}"}, 500
    
    @staticmethod
    def search_similar_chunks(material_id: int, question: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """检索相似的文档块"""
        try:
            # 对问题进行向量化
            question_vector = RAGService.simple_text_embedding(question)
            
            # 获取所有文档块
            connection = get_db_connection()
            with connection.cursor(pymysql.cursors.DictCursor) as cursor:
                cursor.execute("""
                    SELECT chunk_idx, text, vector
                    FROM embeddings
                    WHERE material_id = %s
                    ORDER BY chunk_idx
                """, (material_id,))
                
                chunks = cursor.fetchall()
                connection.close()
            
            if not chunks:
                return []
            
            # 计算相似度
            similarities = []
            for chunk in chunks:
                try:
                    chunk_vector = json.loads(chunk['vector'])
                    similarity = RAGService.cosine_similarity(question_vector, chunk_vector)
                    similarities.append({
                        "chunk_idx": chunk['chunk_idx'],
                        "text": chunk['text'],
                        "similarity": similarity
                    })
                except:
                    continue
            
            # 按相似度排序并返回top_k
            similarities.sort(key=lambda x: x['similarity'], reverse=True)
            return similarities[:top_k]
            
        except Exception as e:
            print(f"[ERROR] 检索文档块失败: {e}")
            return []
    
    @staticmethod
    def ask_document(material_id: int, user_id: int, question: str) -> Tuple[Dict[str, Any], int]:
        """基于文档内容回答问题"""
        try:
            # 验证权限
            connection = get_db_connection()
            with connection.cursor(pymysql.cursors.DictCursor) as cursor:
                cursor.execute("""
                    SELECT m.title
                    FROM materials m
                    JOIN courses c ON m.course_id = c.id
                    WHERE m.id = %s AND c.user_id = %s
                """, (material_id, user_id))
                
                material = cursor.fetchone()
                if not material:
                    connection.close()
                    return {"error": "资料不存在或无权限"}, 404
                
                # 检查是否已创建嵌入
                cursor.execute(
                    "SELECT COUNT(*) as count FROM embeddings WHERE material_id = %s",
                    (material_id,)
                )
                embedding_count = cursor.fetchone()['count']
                if embedding_count == 0:
                    connection.close()
                    return {"error": "请先为该资料创建文档嵌入"}, 400
                
                connection.close()
            
            if not question or not question.strip():
                return {"error": "问题不能为空"}, 400
            
            # 检索相关文档块
            similar_chunks = RAGService.search_similar_chunks(material_id, question, top_k=4)
            
            if not similar_chunks:
                return {"error": "未找到相关内容"}, 404
            
            # 构建上下文
            context_parts = []
            chunk_indices = []
            for i, chunk in enumerate(similar_chunks):
                context_parts.append(f"[文档块{chunk['chunk_idx']}]\n{chunk['text']}")
                chunk_indices.append(chunk['chunk_idx'])
            
            context = "\n\n".join(context_parts)
            
            # 构建RAG提示词
            rag_prompt = f"""请基于提供的文档内容回答用户问题。如果文档中没有相关信息，请明确说明。

文档名称：{material['title']}

相关文档内容：
{context}

用户问题：{question}

回答要求：
1. 答案必须基于提供的文档内容
2. 如果文档中没有相关信息，请说"根据提供的文档内容，我无法找到相关信息来回答这个问题"
3. 在回答结尾请列出参考的文档块编号，格式为"参考文档块：[块号1, 块号2, ...]"
4. 回答要简洁明了，有条理

请回答："""
            
            # 调用AI生成回答
            ai_service = _get_service()
            response, _ = ai_service.get_ai_response(rag_prompt)
            
            answer = response.get('message', '抱歉，无法生成回答')
            
            return {
                "question": question,
                "answer": answer,
                "citations": chunk_indices,
                "material_title": material['title'],
                "context_chunks": len(similar_chunks),
                "relevance_scores": [chunk['similarity'] for chunk in similar_chunks]
            }, 200
            
        except Exception as e:
            return {"error": f"文档问答失败: {str(e)}"}, 500
    
    @staticmethod
    def get_material_chunks(material_id: int, user_id: int) -> Tuple[Dict[str, Any], int]:
        """获取资料的文档切片信息"""
        try:
            # 验证权限
            connection = get_db_connection()
            with connection.cursor(pymysql.cursors.DictCursor) as cursor:
                cursor.execute("""
                    SELECT m.title
                    FROM materials m
                    JOIN courses c ON m.course_id = c.id
                    WHERE m.id = %s AND c.user_id = %s
                """, (material_id, user_id))
                
                material = cursor.fetchone()
                if not material:
                    connection.close()
                    return {"error": "资料不存在或无权限"}, 404
                
                # 获取文档切片
                cursor.execute("""
                    SELECT chunk_idx, text, 
                           CHAR_LENGTH(text) as text_length
                    FROM embeddings
                    WHERE material_id = %s
                    ORDER BY chunk_idx
                """, (material_id,))
                
                chunks = cursor.fetchall()
                connection.close()
                
                return {
                    "material_title": material['title'],
                    "chunks": chunks,
                    "total_chunks": len(chunks),
                    "total_characters": sum(chunk['text_length'] for chunk in chunks)
                }, 200
                
        except Exception as e:
            return {"error": f"获取文档切片失败: {str(e)}"}, 500


# 对外接口函数
def handle_create_embeddings(material_id: int):
    """处理创建文档嵌入请求"""
    return RAGService.create_embeddings_for_material(material_id)

def handle_ask_document(material_id: int, user_id: int, question: str):
    """处理文档问答请求"""
    return RAGService.ask_document(material_id, user_id, question)

def handle_get_chunks(material_id: int, user_id: int):
    """处理获取文档切片请求"""
    return RAGService.get_material_chunks(material_id, user_id)