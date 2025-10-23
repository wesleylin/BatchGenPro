from celery import Celery
import os

# Redis配置
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

# 创建Celery应用
celery_app = Celery('batchgen_pro')

# Celery配置
celery_app.conf.update(
    broker_url=REDIS_URL,
    result_backend=REDIS_URL,
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,  # 5分钟超时
    task_soft_time_limit=240,  # 4分钟软超时
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

# 任务路由 - 暂时使用默认队列
# celery_app.conf.task_routes = {
#     'batchgen_pro.tasks.generate_single_image': {'queue': 'image_generation'},
#     'batchgen_pro.tasks.process_batch_task': {'queue': 'batch_processing'},
# }
