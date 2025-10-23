# V2阶段：批量任务数据结构设计

## 任务状态枚举
```python
from enum import Enum

class TaskStatus(Enum):
    PENDING = "pending"      # 等待处理
    PROCESSING = "processing" # 正在处理
    COMPLETED = "completed"   # 已完成
    FAILED = "failed"        # 失败
    CANCELLED = "cancelled"  # 已取消
```

## 批量任务数据结构
```python
{
    "task_id": "uuid4",           # 任务唯一ID
    "status": TaskStatus.PENDING, # 任务状态
    "created_at": "timestamp",    # 创建时间
    "updated_at": "timestamp",    # 更新时间
    "total_images": 5,           # 总图片数量
    "processed_images": 0,        # 已处理图片数量
    "failed_images": 0,          # 失败图片数量
    "progress": 0.0,             # 进度百分比 (0-100)
    "prompt": "用户输入的prompt", # 通用prompt
    "images": [                  # 图片列表
        {
            "file_id": "uuid4",
            "filename": "image1.png",
            "status": TaskStatus.PENDING,
            "result_url": None,
            "error": None
        }
    ],
    "results": {                 # 结果汇总
        "success_count": 0,
        "failed_count": 0,
        "generated_images": []
    }
}
```

## API接口设计
- `POST /api/batch/generate` - 创建批量任务
- `GET /api/batch/tasks` - 获取任务列表
- `GET /api/batch/tasks/{task_id}` - 获取任务详情
- `GET /api/batch/tasks/{task_id}/status` - 获取任务状态
- `DELETE /api/batch/tasks/{task_id}` - 取消任务
- `GET /api/batch/tasks/{task_id}/results` - 下载所有结果
