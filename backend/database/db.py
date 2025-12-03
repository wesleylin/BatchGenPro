# -*- coding: utf-8 -*-
"""
数据库连接管理模块
提供 SQLite 数据库连接和上下文管理器
"""
import sqlite3
import os
from contextlib import contextmanager

# 数据库文件路径
# 使用相对于当前文件的路径
DB_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(DB_DIR, 'batchgen.db')

# 确保数据库目录存在
os.makedirs(DB_DIR, exist_ok=True)


@contextmanager
def get_db():
    """
    获取数据库连接的上下文管理器
    自动处理事务提交和回滚
    
    Usage:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users")
            rows = cursor.fetchall()
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # 返回字典格式的行
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def get_db_connection():
    """
    获取数据库连接（不自动提交）
    用于需要手动控制事务的场景
    
    Returns:
        sqlite3.Connection: 数据库连接对象
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """
    初始化数据库，创建所有表
    如果表已存在则跳过
    """
    from .migrations import create_tables
    create_tables()
    print(f"数据库初始化完成: {DB_PATH}")


if __name__ == '__main__':
    # 直接运行此文件时初始化数据库
    init_db()

