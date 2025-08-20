import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from material_service import get_cards_db

def get_quiz(material_id: int) -> Optional[Dict[str, Any]]:
    """
    获取材料的测验题
    """
    cards_db = get_cards_db()
    for card in cards_db.values():
        if card["material_id"] == material_id and "quiz" in card:
            return card["quiz"]
    return None

def get_quiz_question(material_id: int, question_id: int) -> Optional[Dict[str, Any]]:
    """
    获取特定测验题
    """
    quiz = get_quiz(material_id)
    if quiz and "questions" in quiz:
        for question in quiz["questions"]:
            if question.get("id") == question_id:
                return question
    return None

def check_answer(material_id: int, question_id: int, user_answer: str) -> Dict[str, Any]:
    """
    检查用户答案
    """
    question = get_quiz_question(material_id, question_id)
    if not question:
        return {
            "correct": False,
            "error": "题目未找到"
        }
    
    correct_answer = question.get("answer", "")
    is_correct = user_answer.strip().lower() == correct_answer.strip().lower()
    
    return {
        "correct": is_correct,
        "user_answer": user_answer,
        "correct_answer": correct_answer,
        "explanation": question.get("explanation", ""),
        "chunk_indices": question.get("chunk_indices", [])
    }

def format_quiz_response(quiz_data: Dict[str, Any]) -> str:
    """
    格式化测验数据为易于阅读的文本格式
    """
    if not quiz_data or "questions" not in quiz_data:
        return "暂无测验题"
    
    response = ["📝 测验题:\n"]
    
    for i, question in enumerate(quiz_data["questions"], 1):
        response.append(f"{i}. {question.get('question', '')}")
        
        # 如果是选择题，显示选项
        if question.get("type") == "single_choice" and "options" in question:
            for j, option in enumerate(question["options"]):
                letters = ['A', 'B', 'C', 'D', 'E', 'F']
                if j < len(letters):
                    response.append(f"   {letters[j]}. {option}")
        
        response.append(f"   答案: {question.get('answer', '')}")
        response.append(f"   解析: {question.get('explanation', '')}")
        response.append("")
    
    return "\n".join(response)