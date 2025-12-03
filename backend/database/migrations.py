# -*- coding: utf-8 -*-
"""
数据库迁移脚本
创建所有必要的表结构
"""
from .db import get_db_connection


def create_tables():
    """
    创建所有数据库表
    如果表已存在则跳过（使用 IF NOT EXISTS）
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # 1. 用户表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email VARCHAR(255) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                username VARCHAR(100),
                credits INTEGER DEFAULT 0 NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 2. 积分交易记录表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS credit_transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                amount INTEGER NOT NULL,
                transaction_type VARCHAR(50) NOT NULL,
                description TEXT,
                task_id VARCHAR(255),
                image_count INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        
        # 3. 用户会话表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                session_token VARCHAR(255) UNIQUE NOT NULL,
                expires_at TIMESTAMP NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        
        # 创建索引
        # 用户表索引
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)
        """)
        
        # 积分交易记录表索引
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_credit_transactions_user_id 
            ON credit_transactions(user_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_credit_transactions_created_at 
            ON credit_transactions(created_at)
        """)
        
        # 用户会话表索引
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_user_sessions_token 
            ON user_sessions(session_token)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_user_sessions_user_id 
            ON user_sessions(user_id)
        """)
        
        conn.commit()
        print("数据库表创建成功")
        
    except Exception as e:
        conn.rollback()
        print(f"创建数据库表失败: {str(e)}")
        raise
    finally:
        conn.close()


if __name__ == '__main__':
    # 直接运行此文件时创建表
    create_tables()

