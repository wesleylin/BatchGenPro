from celery import current_task
from celery_config import celery_app
import sys
import os
from google import genai
from PIL import Image
import io
import uuid
import time

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.api_keys import GEMINI_API_KEY, GEMINI_MODEL, RESULT_FOLDER

@celery_app.task(bind=True)
def generate_single_image(self, file_data, filename, prompt, task_id):
    """
    生成单张图片的Celery任务
    
    Args:
        file_data: 图片文件的二进制数据
        filename: 文件名
        prompt: 生成提示词
        task_id: 任务ID
    
    Returns:
        dict: 包含生成结果的字典
    """
    try:
        # 更新任务状态
        self.update_state(
            state='PROGRESS',
            meta={'status': 'processing', 'filename': filename}
        )
        
        # 初始化Gemini客户端
        client = genai.Client(api_key=GEMINI_API_KEY)
        
        # 将二进制数据转换为PIL Image
        image = Image.open(io.BytesIO(file_data))
        
        # 调用Gemini API生成图片
        full_prompt = f"Create a picture of my image with the following changes: {prompt}"
        
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=[full_prompt, image]
        )
        
        # 处理响应
        if response and hasattr(response, 'candidates') and response.candidates:
            candidate = response.candidates[0]
            if hasattr(candidate, 'content') and candidate.content:
                for part in candidate.content.parts:
                    if hasattr(part, 'inline_data') and part.inline_data:
                        # 保存生成的图片
                        generated_filename = f"generated_{uuid.uuid4()}.png"
                        generated_path = os.path.join(RESULT_FOLDER, generated_filename)
                        
                        with open(generated_path, 'wb') as f:
                            f.write(part.inline_data.data)
                        
                        return {
                            'success': True,
                            'filename': filename,
                            'generated_filename': generated_filename,
                            'generated_url': f"/static/results/{generated_filename}",
                            'description': f"Successfully generated image for {filename}"
                        }
        
        # 如果没有生成图片，返回描述
        return {
            'success': True,
            'filename': filename,
            'generated_filename': None,
            'generated_url': None,
            'description': f"Processed {filename} but no image was generated"
        }
        
    except Exception as e:
        # 记录错误但不抛出异常，避免Celery错误处理问题
        print(f"Error generating image for {filename}: {str(e)}")
        return {
            'success': False,
            'filename': filename,
            'error': str(e)
        }

@celery_app.task(bind=True)
def process_batch_task(self, batch_data):
    """
    处理批量任务的Celery任务
    
    Args:
        batch_data: 批量任务数据
    
    Returns:
        dict: 批量任务结果
    """
    try:
        task_id = batch_data['task_id']
        images = batch_data['images']
        prompt = batch_data['prompt']
        
        results = []
        total_images = len(images)
        
        # 更新任务状态为处理中
        self.update_state(
            state='PROGRESS',
            meta={
                'status': 'processing',
                'progress': 0,
                'current_image': 0,
                'total_images': total_images
            }
        )
        
        for i, image_data in enumerate(images):
            # 更新进度
            progress = (i / total_images) * 100
            self.update_state(
                state='PROGRESS',
                meta={
                    'status': 'processing',
                    'progress': progress,
                    'current_image': i + 1,
                    'total_images': total_images,
                    'filename': image_data['filename']
                }
            )
            
            # 调用单图片生成任务
            result = generate_single_image.delay(
                image_data['file_data'],
                image_data['filename'],
                prompt,
                task_id
            ).get()
            
            results.append(result)
            
            # 短暂延迟，避免API限制
            time.sleep(1)
        
        # 异步更新任务结果
        update_task_results.delay(task_id, results)
        
        return {
            'success': True,
            'task_id': task_id,
            'results': results,
            'total_images': total_images,
            'completed_images': len(results)
        }
        
    except Exception as e:
        print(f"Error processing batch task: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }

@celery_app.task(bind=True)
def update_task_results(self, task_id, results):
    """
    更新任务结果的Celery任务
    
    Args:
        task_id: 任务ID
        results: 任务结果列表
    
    Returns:
        dict: 更新结果
    """
    try:
        from task_manager import task_manager
        
        # 更新任务状态为处理中
        task_manager.update_task_status(task_id, 'processing')
        
        # 处理每个结果
        for result in results:
            if result['success']:
                task_manager.add_task_result(task_id, result['filename'], result)
            else:
                task_manager.add_task_result(task_id, result['filename'], result)
        
        # 更新任务状态为完成
        task_manager.update_task_status(task_id, 'completed')
        
        return {
            'success': True,
            'task_id': task_id,
            'message': 'Task results updated successfully'
        }
        
    except Exception as e:
        print(f"Error updating task results: {str(e)}")
        from task_manager import task_manager
        task_manager.update_task_status(task_id, 'failed')
        return {
            'success': False,
            'error': str(e)
        }

def process_batch_task_sync(task_id, images_data, prompt, api_type="gemini"):
    """
    同步处理批量任务（不使用Celery）
    
    Args:
        task_id: 任务ID
        images_data: 图片数据列表
        prompt: 生成提示词
        api_type: API类型 ("gemini" 或 "doubao")
    
    Returns:
        dict: 批量任务结果
    """
    try:
        from task_manager import task_manager
        
        results = []
        total_images = len(images_data)
        
        for i, image_data in enumerate(images_data):
            # 更新进度
            progress = (i / total_images) * 100
            task_manager.update_task_progress(task_id, progress, i + 1)
            
            # 使用统一的API生成器
            from ai_image_generator import create_image_generator
            generator = create_image_generator(api_type)
            result = generator.generate_image(image_data['file_data'], prompt)
            
            results.append(result)
            
            # 更新任务结果
            task_manager.add_task_result(task_id, image_data['filename'], result)
            
            # 短暂延迟，避免API限制
            time.sleep(1)
        
        return {
            'success': True,
            'task_id': task_id,
            'results': results,
            'total_images': total_images,
            'completed_images': len(results)
        }
        
    except Exception as e:
        print(f"Error processing batch task sync: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }

def generate_single_image_sync(file_data, filename, prompt, task_id):
    """
    同步生成单张图片（不使用Celery）
    
    Args:
        file_data: 图片文件的二进制数据
        filename: 文件名
        prompt: 生成提示词
        task_id: 任务ID
    
    Returns:
        dict: 包含生成结果的字典
    """
    try:
        # 初始化Gemini客户端
        client = genai.Client(api_key=GEMINI_API_KEY)
        
        # 将二进制数据转换为PIL Image
        image = Image.open(io.BytesIO(file_data))
        
        # 调用Gemini API生成图片
        full_prompt = f"Create a picture of my image with the following changes: {prompt}"
        
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=[full_prompt, image]
        )
        
        # 处理响应
        if response and hasattr(response, 'candidates') and response.candidates:
            candidate = response.candidates[0]
            if hasattr(candidate, 'content') and candidate.content:
                for part in candidate.content.parts:
                    if hasattr(part, 'inline_data') and part.inline_data:
                        # 保存生成的图片
                        generated_filename = f"generated_{uuid.uuid4()}.png"
                        generated_path = os.path.join(RESULT_FOLDER, generated_filename)
                        
                        with open(generated_path, 'wb') as f:
                            f.write(part.inline_data.data)
                        
                        return {
                            'success': True,
                            'filename': filename,
                            'generated_filename': generated_filename,
                            'generated_url': f"/static/results/{generated_filename}",
                            'description': f"Successfully generated image for {filename}"
                        }
        
        # 如果没有生成图片，返回描述
        return {
            'success': True,
            'filename': filename,
            'generated_filename': None,
            'generated_url': None,
            'description': f"Processed {filename} but no image was generated"
        }
        
    except Exception as e:
        print(f"Error generating image for {filename}: {str(e)}")
        return {
            'success': False,
            'filename': filename,
            'error': str(e)
        }
