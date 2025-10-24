from enum import Enum
from datetime import datetime
import uuid
import json
import redis
import os

# Redis连接
redis_host = os.getenv('REDIS_HOST', 'localhost')
redis_port = int(os.getenv('REDIS_PORT', 6379))
redis_password = os.getenv('REDIS_PASSWORD', None)
redis_client = redis.Redis(host=redis_host, port=redis_port, password=redis_password, db=0, decode_responses=True)

class TaskStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class BatchTaskManager:
    """批量任务管理器"""
    
    def __init__(self):
        self.redis_client = redis_client
        self.task_prefix = "batch_task:"
    
    def create_task(self, images_data, prompt, api_type="gemini"):
        """创建批量任务"""
        task_id = str(uuid.uuid4())
        
        # 准备任务数据
        task_data = {
            "task_id": task_id,
            "status": TaskStatus.PENDING.value,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "total_images": len(images_data),
            "processed_images": 0,
            "failed_images": 0,
            "progress": 0.0,
            "prompt": prompt,
            "api_type": api_type,
            "images": [],
            "results": {
                "success_count": 0,
                "failed_count": 0,
                "generated_images": []
            }
        }
        
        # 处理图片数据
        for image_data in images_data:
            image_info = {
                "file_id": str(uuid.uuid4()),
                "filename": image_data['filename'],
                "status": TaskStatus.PENDING.value,
                "result_url": None,
                "error": None
            }
            task_data["images"].append(image_info)
        
        # 保存到Redis
        self.redis_client.setex(
            f"{self.task_prefix}{task_id}",
            3600,  # 1小时过期
            json.dumps(task_data)
        )
        
        return task_id, task_data
    
    def get_task(self, task_id):
        """获取任务信息"""
        task_data = self.redis_client.get(f"{self.task_prefix}{task_id}")
        if task_data:
            return json.loads(task_data)
        return None
    
    def update_task_status(self, task_id, status, **kwargs):
        """更新任务状态"""
        task_data = self.get_task(task_id)
        if task_data:
            task_data["status"] = status.value if isinstance(status, TaskStatus) else status
            task_data["updated_at"] = datetime.now().isoformat()
            
            # 更新其他字段
            for key, value in kwargs.items():
                task_data[key] = value
            
            # 保存回Redis
            self.redis_client.setex(
                f"{self.task_prefix}{task_id}",
                3600,
                json.dumps(task_data)
            )
            
            return task_data
        return None
    
    def update_task_progress(self, task_id, progress, current_image=None):
        """更新任务进度"""
        task_data = self.get_task(task_id)
        if task_data:
            task_data["progress"] = progress
            task_data["processed_images"] = int((progress / 100) * task_data["total_images"])
            
            if current_image:
                task_data["current_image"] = current_image
            
            task_data["updated_at"] = datetime.now().isoformat()
            
            self.redis_client.setex(
                f"{self.task_prefix}{task_id}",
                3600,
                json.dumps(task_data)
            )
            
            return task_data
        return None
    
    def add_task_result(self, task_id, image_filename, result):
        """添加任务结果"""
        task_data = self.get_task(task_id)
        if task_data:
            # 更新图片状态
            for image in task_data["images"]:
                if image["filename"] == image_filename:
                    if result["success"]:
                        image["status"] = TaskStatus.COMPLETED.value
                        image["result_url"] = result.get("generated_image_url")
                        task_data["results"]["success_count"] += 1
                        task_data["results"]["generated_images"].append({
                            "filename": image_filename,
                            "generated_url": result.get("generated_image_url"),
                            "generated_filename": result.get("generated_filename")
                        })
                    else:
                        image["status"] = TaskStatus.FAILED.value
                        image["error"] = result.get("error")
                        task_data["results"]["failed_count"] += 1
                    break
            
            # 更新任务状态
            completed_count = task_data["results"]["success_count"] + task_data["results"]["failed_count"]
            if completed_count >= task_data["total_images"]:
                task_data["status"] = TaskStatus.COMPLETED.value
                task_data["progress"] = 100.0
            else:
                task_data["progress"] = (completed_count / task_data["total_images"]) * 100
            
            task_data["updated_at"] = datetime.now().isoformat()
            
            self.redis_client.setex(
                f"{self.task_prefix}{task_id}",
                3600,
                json.dumps(task_data)
            )
            
            return task_data
        return None
    
    def cancel_task(self, task_id):
        """取消任务"""
        return self.update_task_status(task_id, TaskStatus.CANCELLED)
    
    def get_all_tasks(self):
        """获取所有任务"""
        tasks = []
        keys = self.redis_client.keys(f"{self.task_prefix}*")
        for key in keys:
            task_data = self.redis_client.get(key)
            if task_data:
                tasks.append(json.loads(task_data))
        return sorted(tasks, key=lambda x: x["created_at"], reverse=True)
    
    def delete_task(self, task_id):
        """删除任务"""
        return self.redis_client.delete(f"{self.task_prefix}{task_id}")

# 全局任务管理器实例
task_manager = BatchTaskManager()
