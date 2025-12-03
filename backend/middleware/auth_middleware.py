# -*- coding: utf-8 -*-
"""
认证中间件
提供装饰器用于API接口的身份验证
"""
from functools import wraps
from flask import request, jsonify
from auth.auth_service import verify_token, get_user_by_token


def get_token_from_request():
    """
    从请求头中提取 token
    支持 Authorization: Bearer <token> 格式
    
    Returns:
        str: token 字符串，如果不存在返回 None
    """
    # 优先从 Authorization header 获取
    auth_header = request.headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        return auth_header[7:]  # 移除 'Bearer ' 前缀
    
    # 兼容从 X-Auth-Token header 获取
    return request.headers.get('X-Auth-Token')


def require_auth(f):
    """
    装饰器：要求用户必须登录才能访问
    
    Usage:
        @app.route('/api/protected')
        @require_auth
        def protected_route(user):
            # user 是当前登录用户的信息字典
            return jsonify({'message': f'Hello {user["username"]}'})
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = get_token_from_request()
        
        if not token:
            return jsonify({
                'success': False,
                'error': '未提供认证token，请先登录'
            }), 401
        
        # 验证 token
        user_info = verify_token(token)
        if not user_info:
            return jsonify({
                'success': False,
                'error': 'token无效或已过期，请重新登录'
            }), 401
        
        # 获取完整用户信息
        user = get_user_by_token(token)
        if not user:
            return jsonify({
                'success': False,
                'error': '用户不存在'
            }), 401
        
        # 将用户信息作为参数传递给被装饰的函数
        kwargs['user'] = user
        return f(*args, **kwargs)
    
    return decorated_function


def optional_auth(f):
    """
    装饰器：可选认证，如果提供了token则验证，否则继续执行
    
    Usage:
        @app.route('/api/public')
        @optional_auth
        def public_route(user=None):
            if user:
                return jsonify({'message': f'Hello {user["username"]}'})
            else:
                return jsonify({'message': 'Hello anonymous'})
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = get_token_from_request()
        user = None
        
        if token:
            user_info = verify_token(token)
            if user_info:
                user = get_user_by_token(token)
        
        # 将用户信息作为参数传递（可能为None）
        kwargs['user'] = user
        return f(*args, **kwargs)
    
    return decorated_function


def get_current_user():
    """
    获取当前请求的用户信息（不抛出异常）
    用于在非装饰器场景下获取用户信息
    
    Returns:
        dict: 用户信息字典，如果未登录返回 None
    """
    token = get_token_from_request()
    if not token:
        return None
    
    user_info = verify_token(token)
    if not user_info:
        return None
    
    return get_user_by_token(token)


