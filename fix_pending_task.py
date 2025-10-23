#!/usr/bin/env python3
import sys
import os
sys.path.append('.')
from backend.task_manager import task_manager
from backend.tasks import process_batch_task
import json

# 获取pending任务
tasks = task_manager.get_all_tasks()
pending_task = None
for task in tasks:
    if task['status'] == 'pending':
        pending_task = task
        break

if pending_task:
    print(f"Found pending task: {pending_task['task_id']}")
    
    # 准备任务数据
    images_data = []
    for image in pending_task['images']:
        # 这里需要从文件路径读取数据
        # 由于我们只有文件名，需要找到对应的文件
        print(f"Processing image: {image['filename']}")
    
    # 更新任务状态
    task_manager.update_task_status(pending_task['task_id'], 'processing')
    
    print("Task status updated to processing")
else:
    print("No pending tasks found")
