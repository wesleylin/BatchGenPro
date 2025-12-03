# -*- coding: utf-8 -*-
"""
用户认证服务
提供注册、登录、token管理等功能
"""
import os
import uuid
import jwt
import datetime
from database.db import get_db
from utils.password_utils import hash_password, check_password

# JWT 配置
JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'batchgen-pro-secret-key-change-in-production')
JWT_EXPIRATION_DAYS = int(os.getenv('JWT_EXPIRATION_DAYS', '30'))


def generate_token(user_id, email):
    """
    生成 JWT token
    
    Args:
        user_id: 用户ID
        email: 用户邮箱
    
    Returns:
        str: JWT token 字符串
    """
    payload = {
        'user_id': user_id,
        'email': email,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(days=JWT_EXPIRATION_DAYS),
        'iat': datetime.datetime.utcnow()
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm='HS256')


def verify_token(token):
    """
    验证 JWT token 并返回用户信息
    
    Args:
        token: JWT token 字符串
    
    Returns:
        dict: 包含 user_id 和 email 的字典，如果验证失败返回 None
    """
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=['HS256'])
        return {
            'user_id': payload['user_id'],
            'email': payload['email']
        }
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def register_user(email, password, username=None):
    """
    注册新用户
    
    Args:
        email: 用户邮箱
        password: 用户密码
        username: 用户名（可选）
    
    Returns:
        dict: 包含 success, user_id, token 的字典，如果失败则包含 error
    """
    if not email or not password:
        return {'success': False, 'error': '邮箱和密码不能为空'}
    
    if len(password) < 6:
        return {'success': False, 'error': '密码长度至少6位'}
    
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            
            # 检查邮箱是否已存在
            cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
            if cursor.fetchone():
                return {'success': False, 'error': '该邮箱已被注册'}
            
            # 加密密码
            password_hash = hash_password(password)
            
            # 如果没有提供用户名，使用邮箱前缀作为默认用户名
            if not username:
                username = email.split('@')[0]
            
            # 插入新用户
            cursor.execute("""
                INSERT INTO users (email, password_hash, username, credits)
                VALUES (?, ?, ?, ?)
            """, (email, password_hash, username, 0))
            
            user_id = cursor.lastrowid
            
            # 生成 token
            token = generate_token(user_id, email)
            
            # 创建会话记录
            expires_at = datetime.datetime.utcnow() + datetime.timedelta(days=JWT_EXPIRATION_DAYS)
            session_token = str(uuid.uuid4())
            cursor.execute("""
                INSERT INTO user_sessions (user_id, session_token, expires_at)
                VALUES (?, ?, ?)
            """, (user_id, session_token, expires_at))
            
            return {
                'success': True,
                'user_id': user_id,
                'email': email,
                'username': username,
                'token': token,
                'credits': 0
            }
            
    except Exception as e:
        return {'success': False, 'error': f'注册失败: {str(e)}'}


def login_user(email, password):
    """
    用户登录
    
    Args:
        email: 用户邮箱
        password: 用户密码
    
    Returns:
        dict: 包含 success, user_id, token 的字典，如果失败则包含 error
    """
    if not email or not password:
        return {'success': False, 'error': '邮箱和密码不能为空'}
    
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            
            # 查询用户
            cursor.execute("""
                SELECT id, email, password_hash, username, credits
                FROM users WHERE email = ?
            """, (email,))
            
            user = cursor.fetchone()
            
            if not user:
                return {'success': False, 'error': '邮箱或密码错误'}
            
            # 验证密码
            if not check_password(password, user['password_hash']):
                return {'success': False, 'error': '邮箱或密码错误'}
            
            user_id = user['id']
            
            # 生成 token
            token = generate_token(user_id, user['email'])
            
            # 创建会话记录
            expires_at = datetime.datetime.utcnow() + datetime.timedelta(days=JWT_EXPIRATION_DAYS)
            session_token = str(uuid.uuid4())
            cursor.execute("""
                INSERT INTO user_sessions (user_id, session_token, expires_at)
                VALUES (?, ?, ?)
            """, (user_id, session_token, expires_at))
            
            return {
                'success': True,
                'user_id': user_id,
                'email': user['email'],
                'username': user['username'],
                'token': token,
                'credits': user['credits']
            }
            
    except Exception as e:
        return {'success': False, 'error': f'登录失败: {str(e)}'}


def logout_user(token):
    """
    用户登出（删除会话记录）
    
    Args:
        token: JWT token
    
    Returns:
        dict: 包含 success 的字典
    """
    try:
        user_info = verify_token(token)
        if not user_info:
            return {'success': False, 'error': '无效的 token'}
        
        # 这里可以选择删除所有会话，或者只删除当前会话
        # 为了简化，我们只标记 token 无效（实际应用中可以在 Redis 中维护黑名单）
        # 或者删除数据库中的会话记录
        
        with get_db() as conn:
            cursor = conn.cursor()
            # 删除过期的会话记录（清理）
            cursor.execute("""
                DELETE FROM user_sessions 
                WHERE expires_at < ?
            """, (datetime.datetime.utcnow(),))
        
        return {'success': True}
        
    except Exception as e:
        return {'success': False, 'error': f'登出失败: {str(e)}'}


def get_user_by_token(token):
    """
    通过 token 获取用户信息
    
    Args:
        token: JWT token
    
    Returns:
        dict: 包含用户信息的字典，如果失败返回 None
    """
    user_info = verify_token(token)
    if not user_info:
        return None
    
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, email, username, credits, created_at
                FROM users WHERE id = ?
            """, (user_info['user_id'],))
            
            user = cursor.fetchone()
            if not user:
                return None
            
            return {
                'id': user['id'],
                'email': user['email'],
                'username': user['username'],
                'credits': user['credits'],
                'created_at': user['created_at']
            }
    except Exception as e:
        return None


def get_user_by_id(user_id):
    """
    通过用户ID获取用户信息
    
    Args:
        user_id: 用户ID
    
    Returns:
        dict: 包含用户信息的字典，如果失败返回 None
    """
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, email, username, credits, created_at
                FROM users WHERE id = ?
            """, (user_id,))
            
            user = cursor.fetchone()
            if not user:
                return None
            
            return {
                'id': user['id'],
                'email': user['email'],
                'username': user['username'],
                'credits': user['credits'],
                'created_at': user['created_at']
            }
    except Exception as e:
        return None


