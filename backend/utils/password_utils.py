# -*- coding: utf-8 -*-
"""
密码加密和验证工具
使用 bcrypt 进行密码哈希
"""
import bcrypt


def hash_password(password):
    """
    对密码进行哈希加密
    
    Args:
        password: 原始密码字符串
    
    Returns:
        str: 加密后的密码哈希值（字符串格式）
    """
    if not password:
        raise ValueError("密码不能为空")
    
    # 生成盐并加密密码
    salt = bcrypt.gensalt()
    password_hash = bcrypt.hashpw(password.encode('utf-8'), salt)
    return password_hash.decode('utf-8')


def check_password(password, password_hash):
    """
    验证密码是否匹配
    
    Args:
        password: 原始密码字符串
        password_hash: 存储的密码哈希值
    
    Returns:
        bool: 密码匹配返回 True，否则返回 False
    """
    if not password or not password_hash:
        return False
    
    try:
        return bcrypt.checkpw(
            password.encode('utf-8'),
            password_hash.encode('utf-8')
        )
    except Exception:
        return False


