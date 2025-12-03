# -*- coding: utf-8 -*-
"""
积分服务
提供积分查询、扣除、增加、历史记录等功能
"""
from database.db import get_db, get_db_connection


# 积分规则配置
CREDIT_RULES = {
    'gemini-2.5-flash-image': 38,  # Gemini 2.5 每张38积分
    'gemini-3-pro-image-preview': 125,  # Gemini 3 每张125积分
    'doubao-seedream-4-0-250828': 38,  # 豆包 每张38积分
    # 默认值
    'default': 38,  # 默认38积分
}


def calculate_credits_required(model_name, image_count):
    """
    根据模型名称和图片数量计算所需积分
    
    Args:
        model_name: 模型名称
        image_count: 图片数量
    
    Returns:
        int: 所需积分总数
    """
    if not model_name:
        # 如果没有指定模型，使用默认值
        credits_per_image = CREDIT_RULES.get('default', 38)
    else:
        # 根据模型名称查找积分规则
        credits_per_image = CREDIT_RULES.get(model_name, CREDIT_RULES.get('default', 38))
    
    return credits_per_image * image_count


def get_credits_per_image(model_name):
    """
    获取单个模型每张图片所需的积分
    
    Args:
        model_name: 模型名称
    
    Returns:
        int: 每张图片所需的积分
    """
    if not model_name:
        return CREDIT_RULES.get('default', 38)
    return CREDIT_RULES.get(model_name, CREDIT_RULES.get('default', 38))


def get_user_credits(user_id):
    """
    获取用户当前积分余额
    
    Args:
        user_id: 用户ID
    
    Returns:
        int: 用户积分余额，如果用户不存在返回 0
    """
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT credits FROM users WHERE id = ?", (user_id,))
            result = cursor.fetchone()
            if result:
                return result['credits']
            return 0
    except Exception as e:
        print(f"获取用户积分失败: {str(e)}")
        return 0


def check_credits_sufficient(user_id, required_amount):
    """
    检查用户积分是否足够
    
    Args:
        user_id: 用户ID
        required_amount: 需要的积分数量
    
    Returns:
        tuple: (是否足够, 当前积分余额)
    """
    current_credits = get_user_credits(user_id)
    return current_credits >= required_amount, current_credits


def deduct_credits(user_id, amount, task_id=None, image_count=None, description=None):
    """
    扣除用户积分（原子操作）
    
    Args:
        user_id: 用户ID
        amount: 扣除的积分数量（正数）
        task_id: 关联的任务ID（可选）
        image_count: 本次交易的图片数量（可选）
        description: 交易描述（可选）
    
    Returns:
        dict: 包含 success, remaining_credits 的字典，如果失败则包含 error
    """
    if amount <= 0:
        return {'success': False, 'error': '扣除积分数量必须大于0'}
    
    try:
        # 使用事务确保原子性
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            # 检查并扣除积分（使用 WHERE 条件确保积分足够）
            cursor.execute("""
                UPDATE users 
                SET credits = credits - ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND credits >= ?
            """, (amount, user_id, amount))
            
            if cursor.rowcount == 0:
                # 积分不足或用户不存在
                current_credits = get_user_credits(user_id)
                conn.rollback()
                return {
                    'success': False,
                    'error': f'积分不足，当前余额: {current_credits}，需要: {amount}',
                    'current_credits': current_credits
                }
            
            # 获取扣除后的积分余额
            cursor.execute("SELECT credits FROM users WHERE id = ?", (user_id,))
            remaining_credits = cursor.fetchone()['credits']
            
            # 记录交易
            if not description:
                description = f"生成图片扣除积分（{image_count or amount}张）"
            
            cursor.execute("""
                INSERT INTO credit_transactions 
                (user_id, amount, transaction_type, description, task_id, image_count)
                VALUES (?, ?, 'deduct', ?, ?, ?)
            """, (user_id, -amount, description, task_id, image_count))
            
            conn.commit()
            
            return {
                'success': True,
                'deducted_amount': amount,
                'remaining_credits': remaining_credits
            }
            
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
            
    except Exception as e:
        return {'success': False, 'error': f'扣除积分失败: {str(e)}'}


def add_credits(user_id, amount, description=None, transaction_type='recharge'):
    """
    增加用户积分
    
    Args:
        user_id: 用户ID
        amount: 增加的积分数量（正数）
        description: 交易描述（可选）
        transaction_type: 交易类型，'recharge'（充值）或 'reward'（奖励）
    
    Returns:
        dict: 包含 success, new_credits 的字典，如果失败则包含 error
    """
    if amount <= 0:
        return {'success': False, 'error': '增加积分数量必须大于0'}
    
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            
            # 增加积分
            cursor.execute("""
                UPDATE users 
                SET credits = credits + ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (amount, user_id))
            
            if cursor.rowcount == 0:
                return {'success': False, 'error': '用户不存在'}
            
            # 获取增加后的积分余额
            cursor.execute("SELECT credits FROM users WHERE id = ?", (user_id,))
            new_credits = cursor.fetchone()['credits']
            
            # 记录交易
            if not description:
                description = f"{'充值' if transaction_type == 'recharge' else '奖励'}积分"
            
            cursor.execute("""
                INSERT INTO credit_transactions 
                (user_id, amount, transaction_type, description)
                VALUES (?, ?, ?, ?)
            """, (user_id, amount, transaction_type, description))
            
            return {
                'success': True,
                'added_amount': amount,
                'new_credits': new_credits
            }
            
    except Exception as e:
        return {'success': False, 'error': f'增加积分失败: {str(e)}'}


def get_credit_history(user_id, limit=50, offset=0):
    """
    获取用户积分交易历史
    
    Args:
        user_id: 用户ID
        limit: 返回记录数量限制，默认50
        offset: 偏移量，默认0
    
    Returns:
        list: 交易记录列表，每个记录包含 id, amount, transaction_type, description, task_id, image_count, created_at
    """
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, amount, transaction_type, description, task_id, image_count, created_at
                FROM credit_transactions
                WHERE user_id = ?
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
            """, (user_id, limit, offset))
            
            transactions = []
            for row in cursor.fetchall():
                transactions.append({
                    'id': row['id'],
                    'amount': row['amount'],
                    'transaction_type': row['transaction_type'],
                    'description': row['description'],
                    'task_id': row['task_id'],
                    'image_count': row['image_count'],
                    'created_at': row['created_at']
                })
            
            return transactions
            
    except Exception as e:
        print(f"获取积分历史失败: {str(e)}")
        return []


def get_credit_statistics(user_id):
    """
    获取用户积分统计信息
    
    Args:
        user_id: 用户ID
    
    Returns:
        dict: 包含总充值、总消费、当前余额等统计信息
    """
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            
            # 获取当前余额
            current_credits = get_user_credits(user_id)
            
            # 统计总充值
            cursor.execute("""
                SELECT COALESCE(SUM(amount), 0) as total_recharge
                FROM credit_transactions
                WHERE user_id = ? AND transaction_type = 'recharge' AND amount > 0
            """, (user_id,))
            total_recharge = cursor.fetchone()['total_recharge'] or 0
            
            # 统计总消费
            cursor.execute("""
                SELECT COALESCE(ABS(SUM(amount)), 0) as total_deducted
                FROM credit_transactions
                WHERE user_id = ? AND transaction_type = 'deduct' AND amount < 0
            """, (user_id,))
            total_deducted = cursor.fetchone()['total_deducted'] or 0
            
            # 统计总奖励
            cursor.execute("""
                SELECT COALESCE(SUM(amount), 0) as total_reward
                FROM credit_transactions
                WHERE user_id = ? AND transaction_type = 'reward' AND amount > 0
            """, (user_id,))
            total_reward = cursor.fetchone()['total_reward'] or 0
            
            return {
                'current_credits': current_credits,
                'total_recharge': total_recharge,
                'total_deducted': total_deducted,
                'total_reward': total_reward,
                'total_earned': total_recharge + total_reward
            }
            
    except Exception as e:
        print(f"获取积分统计失败: {str(e)}")
        return {
            'current_credits': 0,
            'total_recharge': 0,
            'total_deducted': 0,
            'total_reward': 0,
            'total_earned': 0
        }
