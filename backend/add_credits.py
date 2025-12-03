#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
给用户增加积分的脚本
"""
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from auth.credit_service import add_credits, get_user_credits
from database.db import get_db

def add_credits_to_user(user_id, amount):
    """给指定用户增加积分"""
    result = add_credits(user_id, amount, description="测试充值", transaction_type='recharge')
    if result['success']:
        print(f"✅ 成功给用户 {user_id} 增加 {amount} 积分")
        print(f"   新积分余额: {result['new_credits']}")
        return True
    else:
        print(f"❌ 失败: {result.get('error')}")
        return False

def list_users():
    """列出所有用户"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT id, email, username, credits FROM users ORDER BY id DESC')
        users = cursor.fetchall()
        return users

if __name__ == '__main__':
    print("=" * 50)
    print("用户列表:")
    print("=" * 50)
    users = list_users()
    for user in users:
        print(f"ID: {user['id']:3d} | Email: {user['email']:30s} | Username: {user['username']:15s} | Credits: {user['credits']:3d}")
    
    if len(sys.argv) > 1:
        user_id = int(sys.argv[1])
        amount = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    else:
        print("\n" + "=" * 50)
        print("给最近注册的用户增加5积分...")
        if users:
            user_id = users[0]['id']
            amount = 5
        else:
            print("❌ 没有找到用户")
            sys.exit(1)
    
    print(f"\n给用户 ID {user_id} 增加 {amount} 积分...")
    add_credits_to_user(user_id, amount)
    
    # 显示更新后的积分
    current_credits = get_user_credits(user_id)
    print(f"\n当前积分余额: {current_credits}")


