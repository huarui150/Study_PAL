#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json

def test_api_endpoints():
    """测试API端点返回的数据"""
    base_url = "http://localhost:5000/api"
    user_id = "20242081627"
    
    # 测试成就API
    print("=== 测试成就API ===")
    try:
        response = requests.get(f"{base_url}/achievements/{user_id}")
        if response.status_code == 200:
            data = response.json()
            print("成就数据:")
            print(f"  - 成就数量: {len(data.get('achievements', []))}")
            print(f"  - StudyCoin余额: {data.get('studycoin', 0)}")
            print(f"  - 登录天数: {data.get('stats', {}).get('login_streak', 0)}")
            print(f"  - 总专注时长: {data.get('stats', {}).get('total_focus_time', 0)}")
        else:
            print(f"成就API错误: {response.status_code}")
    except Exception as e:
        print(f"成就API测试失败: {e}")
    
    # 测试番茄钟统计API
    print("\n=== 测试番茄钟统计API ===")
    try:
        response = requests.get(f"{base_url}/pomodoro/stats?user_id={user_id}")
        if response.status_code == 200:
            data = response.json()
            print("番茄钟统计:")
            print(f"  - 今日番茄: {data.get('today_pomodoros', 0)}")
            print(f"  - 今日专注时长: {data.get('today_focus_time', 0)}")
            print(f"  - 总番茄数: {data.get('total_sessions', 0)}")
            print(f"  - 总专注时长: {data.get('total_focus_time', 0)}")
        else:
            print(f"番茄钟API错误: {response.status_code}")
    except Exception as e:
        print(f"番茄钟API测试失败: {e}")
    
    # 测试活动API（使用用户ID参数）
    print("\n=== 测试活动API ===")
    try:
        response = requests.get(f"{base_url}/activities?user_id=1")  # 使用默认用户ID
        if response.status_code == 200:
            data = response.json()
            print("活动数据:")
            print(f"  - 活动数量: {len(data.get('activities', []))}")
            if data.get('activities'):
                for i, activity in enumerate(data['activities'][:3]):
                    print(f"  - 活动{i+1}: {activity.get('title', 'N/A')}")
        else:
            print(f"活动API错误: {response.status_code}")
    except Exception as e:
        print(f"活动API测试失败: {e}")

if __name__ == "__main__":
    test_api_endpoints()
